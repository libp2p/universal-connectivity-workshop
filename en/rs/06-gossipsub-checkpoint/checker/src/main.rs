use anyhow::Result;
use futures::StreamExt;
use libp2p::{
    gossipsub, identify, identity, ping,
    swarm::{ConnectionId, NetworkBehaviour, SwarmEvent},
    Multiaddr, SwarmBuilder,
};
use prost::Message;
use std::{
    collections::hash_map::DefaultHasher,
    env,
    hash::{Hash, Hasher},
    str::FromStr,
    time::Duration,
};

const IDENTIFY_PROTOCOL_VERSION: &str = "/ipfs/id/1.0.0";
const AGENT_VERSION: &str = "universal-connectivity/0.1.0";
const GOSSIPSUB_TOPICS: &[&str] = &[
    "universal-connectivity",
    "universal-connectivity-file",
    "universal-connectivity-browser-peer-discovery",
];

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

fn message_id(msg: &gossipsub::Message) -> gossipsub::MessageId {
    let mut s = DefaultHasher::new();
    msg.data.hash(&mut s);
    gossipsub::MessageId::from(s.finish().to_string())
}

#[tokio::main]
async fn main() -> Result<()> {
    let remote_peers = env::var("REMOTE_PEERS")?;
    let remote_addrs: Vec<Multiaddr> = remote_peers
        .split(',')
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .map(Multiaddr::from_str)
        .collect::<Result<_, _>>()?;

    let local_key = identity::Keypair::generate_ed25519();

    // Create a Gossipsub configuration
    let gossipsub_config = gossipsub::ConfigBuilder::default()
        .heartbeat_interval(Duration::from_secs(10))
        .validation_mode(gossipsub::ValidationMode::Permissive)
        .message_id_fn(message_id)
        .mesh_outbound_min(1)
        .mesh_n_low(1)
        .flood_publish(true)
        .build()?;

    // Create a gossipsub instance
    let mut gossipsub = gossipsub::Behaviour::new(
        gossipsub::MessageAuthenticity::Signed(local_key.clone()),
        gossipsub_config,
    )
    .map_err(|e| anyhow::anyhow!(e))?;

    // Subscribe to topics
    for topic in GOSSIPSUB_TOPICS {
        let topic = gossipsub::IdentTopic::new(*topic);
        gossipsub.subscribe(&topic)?;
    }

    let mut swarm = SwarmBuilder::with_existing_identity(local_key)
        .with_tokio()
        .with_quic()
        .with_behaviour(|key| Behaviour {
            ping: ping::Behaviour::new(
                ping::Config::new()
                    .with_interval(Duration::from_secs(1))
                    .with_timeout(Duration::from_secs(5)),
            ),
            identify: identify::Behaviour::new(
                identify::Config::new(IDENTIFY_PROTOCOL_VERSION.to_string(), key.public())
                    .with_agent_version(AGENT_VERSION.to_string()),
            ),
            gossipsub,
        })?
        .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
        .build();

    // listen on all addresses
    for addr in remote_addrs.into_iter() {
        swarm.listen_on(addr)?;
    }

    let mut cid: Option<ConnectionId> = None;

    loop {
        tokio::select! {
            Some(event) = swarm.next() => match event {
                SwarmEvent::ConnectionEstablished { peer_id, connection_id, endpoint, .. } => {
                    println!("connected,{peer_id},{}", endpoint.get_remote_address());
                    cid = Some(connection_id);
                }
                SwarmEvent::ConnectionClosed { peer_id, cause, .. } => {
                    if let Some(error) = cause {
                        println!("error,{error}");
                    } else {
                        println!("closed,{peer_id}");
                    }
                    return Ok(())
                }
                SwarmEvent::IncomingConnection { local_addr, send_back_addr, .. } => {
                    println!("incoming,{local_addr},{send_back_addr}");
                }
                SwarmEvent::OutgoingConnectionError { error, .. } => {
                    println!("error,{error}");
                }
                SwarmEvent::Behaviour(behaviour_event) => match behaviour_event {
                    BehaviourEvent::Ping(ping::Event { peer, result, .. }) => {
                        match result {
                            Ok(rtt) => {
                                println!("ping,{peer},{} ms", rtt.as_millis());
                            }
                            Err(failure) => {
                                println!("error,{failure}");
                            }
                        }
                    }
                    BehaviourEvent::Identify(identify_event) => {
                        match identify_event {
                            identify::Event::Received { peer_id, info, .. } => {
                                println!("identify,{peer_id},{},{}", info.protocol_version, info.agent_version);
                            }
                            identify::Event::Error { error, .. } => {
                                println!("error,{error}");
                            }
                            _ => {}
                        }
                    }
                    BehaviourEvent::Gossipsub(gossipsub_event) => {
                        match gossipsub_event {
                            gossipsub::Event::Message { message, .. } => {
                                if let Ok(msg) = UniversalConnectivityMessage::decode(&message.data[..]) {
                                    println!("msg,{},{},{}",
                                        msg.from,
                                        message.topic,
                                        msg.message);
                                    if let Some(connection_id) = cid {
                                        swarm.close_connection(connection_id);
                                    }
                                } else {
                                    println!("error,{}", message.topic);
                                }
                            }
                            gossipsub::Event::Subscribed { peer_id, topic } => {
                                println!("subscribe,{peer_id},{topic}");
                            }
                            gossipsub::Event::Unsubscribed { peer_id, topic } => {
                                println!("unsubscribe,{peer_id},{topic}");
                            }
                            _ => {}
                        }
                    }
                }
                _ => {}
            }
        }
    }
}
