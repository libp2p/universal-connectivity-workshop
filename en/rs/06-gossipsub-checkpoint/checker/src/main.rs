use anyhow::Result;
use futures::StreamExt;
use libp2p::identity;
use libp2p::{gossipsub, identify, noise, tcp, yamux, Multiaddr, SwarmBuilder};
use libp2p::{
    ping,
    swarm::{NetworkBehaviour, SwarmEvent},
};
use prost::Message;
use std::env;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

#[derive(Clone, PartialEq, prost::Message)]
pub struct UniversalConnectivityMessage {
    #[prost(string, tag = "1")]
    pub from: String,
    #[prost(string, tag = "2")]
    pub message: String,
    #[prost(int64, tag = "3")]
    pub timestamp: i64,
    #[prost(enumeration = "MessageType", tag = "4")]
    pub message_type: i32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, PartialOrd, Ord, prost::Enumeration)]
#[repr(i32)]
pub enum MessageType {
    Chat = 0,
    File = 1,
    BrowserPeerDiscovery = 2,
}

// Define a custom network behaviour that includes ping, identify, and gossipsub functionality
#[derive(NetworkBehaviour)]
struct Behaviour {
    ping: ping::Behaviour,
    identify: identify::Behaviour,
    gossipsub: gossipsub::Behaviour,
}

#[tokio::main]
async fn main() -> Result<()> {
    println!("Starting Universal Connectivity Application...");

    let remote_peer = env::var("REMOTE_PEER")?;
    let remote_addr: Multiaddr = remote_peer.parse()?;

    let local_key = identity::Keypair::generate_ed25519();
    let local_peer_id = identity::PeerId::from(local_key.public());
    println!("Local peer id: {local_peer_id}");

    // Create a Gossipsub configuration
    let gossipsub_config = gossipsub::ConfigBuilder::default()
        .heartbeat_interval(Duration::from_secs(10))
        .validation_mode(gossipsub::ValidationMode::Strict)
        .build()
        .expect("Valid config");

    // Create a gossipsub instance
    let mut gossipsub = gossipsub::Behaviour::new(
        gossipsub::MessageAuthenticity::Signed(local_key.clone()),
        gossipsub_config,
    ).expect("Correct configuration");

    // Subscribe to topics
    let topics = vec![
        "universal-connectivity",
        "universal-connectivity-file",
        "universal-connectivity-browser-peer-discovery"
    ];

    for topic_str in topics {
        let topic = gossipsub::IdentTopic::new(topic_str);
        gossipsub.subscribe(&topic)?;
        println!("Subscribed to topic: {}", topic_str);
    }

    let mut swarm = SwarmBuilder::with_existing_identity(local_key)
        .with_tokio()
        .with_tcp(
            tcp::Config::default(),
            noise::Config::new,
            yamux::Config::default,
        )?
        .with_quic()
        .with_behaviour(|key| Behaviour {
            ping: ping::Behaviour::new(
                ping::Config::new()
                    .with_interval(Duration::from_secs(1))
                    .with_timeout(Duration::from_secs(5))
            ),
            identify: identify::Behaviour::new(
                identify::Config::new("/ipfs/id/1.0.0".to_string(), key.public())
                    .with_agent_version("universal-connectivity/0.1.0".to_string())
            ),
            gossipsub,
        })?
        .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
        .build();

    swarm.listen_on(remote_addr)?;

    // Send a test message after a short delay
    let mut message_sent = false;
    let mut message_timer = tokio::time::interval(Duration::from_secs(5));

    loop {
        tokio::select! {
            _ = message_timer.tick() => {
                if !message_sent {
                    // Send a test message on the universal-connectivity topic
                    let topic = gossipsub::IdentTopic::new("universal-connectivity");
                    let test_message = UniversalConnectivityMessage {
                        from: local_peer_id.to_string(),
                        message: "Hello from checker!".to_string(),
                        timestamp: SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs() as i64,
                        message_type: MessageType::Chat as i32,
                    };
                    
                    let mut buf = Vec::new();
                    test_message.encode(&mut buf)?;
                    
                    if let Err(e) = swarm.behaviour_mut().gossipsub.publish(topic, buf) {
                        println!("Failed to publish message: {:?}", e);
                    } else {
                        println!("Published test message to universal-connectivity topic");
                    }
                    message_sent = true;
                }
            }
            Some(event) = swarm.next() => match event {
                SwarmEvent::NewListenAddr { address, .. } => {
                    println!("Listening on: {address}");
                }
                SwarmEvent::ConnectionEstablished { peer_id, connection_id, endpoint, .. } => {
                    println!("Connected to: {peer_id} via {}", endpoint.get_remote_address());
                }
                SwarmEvent::ConnectionClosed { peer_id, cause, .. } => {
                    if let Some(err) = cause {
                        println!("Connection to {peer_id} closed with error: {err}");
                    } else {
                        println!("Connection to {peer_id} closed gracefully");
                    }
                }
                SwarmEvent::IncomingConnection { local_addr, send_back_addr, .. } => {
                    println!("Incoming connection to: {local_addr}, from: {send_back_addr}");
                }
                SwarmEvent::Behaviour(behaviour_event) => match behaviour_event {
                    BehaviourEvent::Ping(ping_event) => {
                        match ping_event {
                            ping::Event {
                                peer,
                                connection,
                                result: Ok(rtt),
                            } => {
                                println!("Received a ping from {} (connection {:?}), round trip time: {} ms", peer, connection, rtt.as_millis());
                            }
                            ping::Event {
                                peer,
                                connection,
                                result: Err(failure),
                            } => {
                                println!("Ping failed to {} (connection {:?}): {:?}", peer, connection, failure);
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
                                println!("Sent identify info to: {}", peer_id);
                            }
                            identify::Event::Error { peer_id, error, .. } => {
                                println!("Identify error with {}: {:?}", peer_id, error);
                            }
                            _ => {}
                        }
                    }
                    BehaviourEvent::Gossipsub(gossipsub_event) => {
                        match gossipsub_event {
                            gossipsub::Event::Message {
                                propagation_source: _,
                                message_id: _,
                                message,
                            } => {
                                let topic = message.topic.clone();
                                if let Ok(uc_message) = UniversalConnectivityMessage::decode(&message.data[..]) {
                                    println!("Received message on topic '{}': {} from {} (type: {:?})", 
                                        topic, uc_message.message, uc_message.from, uc_message.message_type);
                                } else {
                                    println!("Received non-UC message on topic '{}': {} bytes", 
                                        topic, message.data.len());
                                }
                            }
                            gossipsub::Event::Subscribed { peer_id, topic } => {
                                println!("Peer {} subscribed to topic: {}", peer_id, topic);
                            }
                            gossipsub::Event::Unsubscribed { peer_id, topic } => {
                                println!("Peer {} unsubscribed from topic: {}", peer_id, topic);
                            }
                            _ => {}
                        }
                    }
                }
                SwarmEvent::OutgoingConnectionError { peer_id, error, .. } => {
                    println!("Failed to connect to {peer_id:?}: {error}");
                }
                _ => {}
            }
        }
    }
}