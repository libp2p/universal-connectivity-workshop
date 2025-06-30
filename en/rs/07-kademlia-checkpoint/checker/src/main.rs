use anyhow::Result;
use futures::StreamExt;
use libp2p::{
    gossipsub, identify, identity, kad, ping,
    swarm::{ConnectionId, NetworkBehaviour, SwarmEvent},
    Multiaddr, StreamProtocol, SwarmBuilder,
};
use prost::Message;
use std::{env, hash::Hash, path::PathBuf, str::FromStr, time::Duration};
use tokio::fs;

const IDENTIFY_PROTOCOL_VERSION: &str = "/ipfs/id/1.0.0";
const AGENT_VERSION: &str = "universal-connectivity/0.1.0";
const GOSSIPSUB_TOPICS: &[&str] = &[
    "universal-connectivity",
    "universal-connectivity-file",
    "universal-connectivity-browser-peer-discovery",
];
const KADEMLIA_PROTOCOL_NAME: StreamProtocol = StreamProtocol::new("/ipfs/kad/1.0.0");
const KADEMLIA_QUERY_TIMEOUT: u64 = 10;
const KADEMLIA_BOOTSTRAP_INTERVAL: u64 = 300;

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
    kademlia: kad::Behaviour<kad::store::MemoryStore>,
}

async fn read_identity() -> Result<identity::Keypair> {
    let key_path = PathBuf::from("/app/key");
    let bytes = fs::read(&key_path).await?;
    return Ok(identity::Keypair::from_protobuf_encoding(&bytes)?);
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

    let local_key = read_identity().await?;
    let local_peer_id = local_key.public().to_peer_id();

    // Create a Gossipsub configuration
    let gossipsub_config = gossipsub::ConfigBuilder::default()
        .heartbeat_interval(Duration::from_secs(10))
        .validation_mode(gossipsub::ValidationMode::Strict)
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

    let mut kad_config = kad::Config::new(KADEMLIA_PROTOCOL_NAME);
    kad_config.set_query_timeout(Duration::from_secs(KADEMLIA_QUERY_TIMEOUT));
    kad_config.set_periodic_bootstrap_interval(None);
    let kad_store = kad::store::MemoryStore::new(local_peer_id.clone());
    let kademlia = kad::Behaviour::with_config(local_peer_id, kad_store, kad_config);

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
            kademlia,
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
                    BehaviourEvent::Kademlia(kad_event) => {
                        match kad_event {
                            kad::Event::OutboundQueryProgressed { result, .. } => {
                                match result {
                                    kad::QueryResult::Bootstrap(Ok(kad::BootstrapOk {
                                        peer,
                                        num_remaining,
                                    })) => {
                                        println!("Bootstrap progress: contacted {}, {} remaining", peer, num_remaining);
                                        if num_remaining == 0 {
                                            println!("Kademlia bootstrap completed successfully");
                                        }
                                    }
                                    kad::QueryResult::Bootstrap(Err(kad::BootstrapError::Timeout)) => {
                                        println!("Kademlia bootstrap timed out");
                                    }
                                    kad::QueryResult::GetClosestPeers(Ok(kad::GetClosestPeersOk { key: _, peers })) => {
                                        println!("Found {} closest peers", peers.len());
                                        for peer in peers {
                                            println!("Closest peer: {}", peer);
                                        }
                                    }
                                    kad::QueryResult::GetClosestPeers(Err(kad::GetClosestPeersError::Timeout { key: _, peers })) => {
                                        println!("Get closest peers timed out, found {} peers", peers.len());
                                    }
                                    _ => {}
                                }
                            }
                            kad::Event::RoutingUpdated { peer, is_new_peer, addresses, bucket_range: _, old_peer } => {
                                if is_new_peer {
                                    println!("New peer added to routing table: {} with {} addresses", peer, addresses.len());
                                }
                                if let Some(old) = old_peer {
                                    println!("Peer {} replaced {} in routing table", peer, old);
                                }
                            }
                            kad::Event::UnroutablePeer { peer } => {
                                println!("Peer {} is unroutable", peer);
                            }
                            kad::Event::RoutablePeer { peer, address } => {
                                println!("Peer {} is routable at {}", peer, address);
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
