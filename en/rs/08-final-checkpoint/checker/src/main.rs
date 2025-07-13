use anyhow::Result;
use futures::StreamExt;
use libp2p::identity;
use libp2p::{
    gossipsub, identify, kad, ping,
    swarm::{NetworkBehaviour, SwarmEvent},
};
use libp2p::{noise, tcp, yamux, Multiaddr, StreamProtocol, SwarmBuilder};
use prost::Message;
use std::env;
use std::time::Duration;

// Universal Connectivity Message structure for chat
#[derive(Clone, PartialEq, prost::Message)]
pub struct UniversalConnectivityMessage {
    #[prost(oneof = "universal_connectivity_message::Message", tags = "1, 2, 3, 4")]
    pub message: Option<universal_connectivity_message::Message>,
}

pub mod universal_connectivity_message {
    #[derive(Clone, PartialEq, prost::Oneof)]
    pub enum Message {
        #[prost(message, tag = "1")]
        Chat(super::ChatMessage),
        #[prost(message, tag = "2")]
        File(super::FileMessage),
        #[prost(message, tag = "3")]
        Webrtc(super::WebrtcMessage),
        #[prost(message, tag = "4")]
        BrowserPeerDiscovery(super::BrowserPeerDiscoveryMessage),
    }
}

#[derive(Clone, PartialEq, prost::Message)]
pub struct ChatMessage {
    #[prost(string, tag = "1")]
    pub message: String,
}

#[derive(Clone, PartialEq, prost::Message)]
pub struct FileMessage {
    #[prost(string, tag = "1")]
    pub name: String,
    #[prost(uint64, tag = "2")]
    pub size: u64,
    #[prost(bytes = "vec", tag = "3")]
    pub data: Vec<u8>,
}

#[derive(Clone, PartialEq, prost::Message)]
pub struct WebrtcMessage {
    #[prost(string, tag = "1")]
    pub data: String,
}

#[derive(Clone, PartialEq, prost::Message)]
pub struct BrowserPeerDiscoveryMessage {
    #[prost(string, tag = "1")]
    pub peer_id: String,
    #[prost(string, repeated, tag = "2")]
    pub multiaddrs: Vec<String>,
}

// Define a custom network behaviour that includes all protocols
#[derive(NetworkBehaviour)]
struct Behaviour {
    ping: ping::Behaviour,
    identify: identify::Behaviour,
    gossipsub: gossipsub::Behaviour,
    kademlia: kad::Behaviour<kad::store::MemoryStore>,
}

#[tokio::main]
async fn main() -> Result<()> {
    println!("Starting Universal Connectivity Application...");

    let remote_peer = env::var("REMOTE_PEER")?;
    let remote_addr: Multiaddr = remote_peer.parse()?;

    let local_key = identity::Keypair::generate_ed25519();
    let local_peer_id = identity::PeerId::from(local_key.public());
    println!("Local peer id: {local_peer_id}");

    // Configure Gossipsub
    let gossipsub_config = gossipsub::ConfigBuilder::default()
        .heartbeat_interval(Duration::from_secs(10))
        .validation_mode(gossipsub::ValidationMode::Strict)
        .build()
        .expect("Valid config");

    let mut gossipsub = gossipsub::Behaviour::new(
        gossipsub::MessageAuthenticity::Signed(local_key.clone()),
        gossipsub_config,
    )
    .expect("Correct configuration");

    // Subscribe to topics
    let chat_topic = gossipsub::IdentTopic::new("universal-connectivity");
    let file_topic = gossipsub::IdentTopic::new("universal-connectivity-file");
    let browser_topic = gossipsub::IdentTopic::new("universal-connectivity-browser-peer-discovery");

    gossipsub.subscribe(&chat_topic)?;
    gossipsub.subscribe(&file_topic)?;
    gossipsub.subscribe(&browser_topic)?;

    // Configure Kademlia
    let store = kad::store::MemoryStore::new(local_peer_id);
    let mut kad_config = kad::Config::new(StreamProtocol::new("/ipfs/kad/1.0.0"));
    kad_config.set_query_timeout(Duration::from_secs(60));
    let kademlia = kad::Behaviour::with_config(local_peer_id, store, kad_config);

    let mut swarm = SwarmBuilder::with_existing_identity(local_key.clone())
        .with_tokio()
        .with_tcp(
            tcp::Config::default(),
            noise::Config::new,
            yamux::Config::default,
        )?
        .with_quic()
        .with_behaviour(|_| Behaviour {
            ping: ping::Behaviour::new(ping::Config::new().with_interval(Duration::from_secs(1))),
            identify: identify::Behaviour::new(
                identify::Config::new("/ipfs/id/1.0.0".into(), local_key.public())
                    .with_agent_version("universal-connectivity/0.1.0".into()),
            ),
            gossipsub,
            kademlia,
        })?
        .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
        .build();

    swarm.listen_on(remote_addr)?;

    // Send a welcome chat message after connecting
    let mut sent_welcome = false;

    loop {
        tokio::select! {
            Some(event) = swarm.next() => match event {
                SwarmEvent::NewListenAddr { address, .. } => {
                    println!("Listening on: {address}");
                }
                SwarmEvent::ConnectionEstablished { peer_id, endpoint, .. } => {
                    println!("Connected to: {peer_id} via {}", endpoint.get_remote_address());

                    // Send welcome message once when first peer connects
                    if !sent_welcome {
                        let welcome_msg = UniversalConnectivityMessage {
                            message: Some(universal_connectivity_message::Message::Chat(ChatMessage {
                                message: "Hello from the Universal Connectivity checker!".to_string(),
                            })),
                        };

                        let mut buf = Vec::new();
                        prost::Message::encode(&welcome_msg, &mut buf)?;

                        if let Err(e) = swarm.behaviour_mut().gossipsub.publish(chat_topic.clone(), buf) {
                            println!("Failed to publish welcome message: {e}");
                        } else {
                            println!("Sent welcome chat message to connected peers");
                        }
                        sent_welcome = true;
                    }
                }
                SwarmEvent::ConnectionClosed { peer_id, cause, .. } => {
                    if let Some(err) = cause {
                        println!("Connection to {peer_id} closed with error: {err}");
                    } else {
                        println!("Connection to {peer_id} closed gracefully");
                    }
                }
                SwarmEvent::Behaviour(event) => match event {
                    BehaviourEvent::Ping(ping_event) => {
                        match ping_event {
                            ping::Event { peer, result: Ok(rtt), .. } => {
                                println!("Received a ping from {peer}, round trip time: {} ms", rtt.as_millis());
                            }
                            ping::Event { peer, result: Err(failure), .. } => {
                                println!("Ping failed to {peer}: {failure:?}");
                            }
                        }
                    }
                    BehaviourEvent::Identify(identify_event) => {
                        match identify_event {
                            identify::Event::Received { peer_id, info, .. } => {
                                println!("Identified peer: {} with protocol version: {}", peer_id, info.protocol_version);
                                println!("Peer agent: {}", info.agent_version);
                                println!("Peer supports {} protocols", info.protocols.len());
                            }
                            identify::Event::Sent { peer_id, .. } => {
                                println!("Sent identify info to: {peer_id}");
                            }
                            identify::Event::Error { peer_id, error, .. } => {
                                println!("Identify error with {peer_id}: {error:?}");
                            }
                            _ => {}
                        }
                    }
                    BehaviourEvent::Gossipsub(gossipsub_event) => match gossipsub_event {
                        gossipsub::Event::Message {
                            message,
                            propagation_source: peer_id,
                            ..
                        } => {
                            // Try to decode as UniversalConnectivityMessage
                            match UniversalConnectivityMessage::decode(&message.data[..]) {
                                Ok(uc_msg) => {
                                    match uc_msg.message {
                                        Some(universal_connectivity_message::Message::Chat(chat)) => {
                                            println!("Received chat message from {peer_id}: {}", chat.message);
                                        }
                                        Some(universal_connectivity_message::Message::File(file)) => {
                                            println!("Received file message from {peer_id}: {} ({} bytes)", file.name, file.size);
                                        }
                                        _ => {
                                            println!("Received other gossipsub message from {peer_id}");
                                        }
                                    }
                                }
                                Err(_) => {
                                    // Fallback to raw message display
                                    if let Ok(text) = String::from_utf8(message.data.clone()) {
                                        println!("Received raw gossipsub message from {peer_id}: {text}");
                                    } else {
                                        println!("Received binary gossipsub message from {peer_id}");
                                    }
                                }
                            }
                        }
                        gossipsub::Event::Subscribed { peer_id, topic } => {
                            println!("Peer {peer_id} subscribed to topic: {topic}");
                        }
                        gossipsub::Event::Unsubscribed { peer_id, topic } => {
                            println!("Peer {peer_id} unsubscribed from topic: {topic}");
                        }
                        _ => {}
                    }
                    BehaviourEvent::Kademlia(kad_event) => {
                        println!("Kademlia event: {kad_event:?}");
                    }
                }
                _ => {}
            }
        }
    }
}
