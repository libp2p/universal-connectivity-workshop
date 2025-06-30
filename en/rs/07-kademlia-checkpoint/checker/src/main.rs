use anyhow::Result;
use futures::StreamExt;
use libp2p::{
    gossipsub, identify, identity, kad,
    multiaddr::Protocol,
    ping,
    swarm::{ConnectionId, NetworkBehaviour, SwarmEvent},
    Multiaddr, PeerId, StreamProtocol, SwarmBuilder,
};
use prost::Message;
use std::{
    collections::hash_map::DefaultHasher,
    env,
    fmt::Write,
    hash::{Hash, Hasher},
    path::PathBuf,
    str::FromStr,
    time::{Duration, SystemTime, UNIX_EPOCH},
};
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
    Ok(identity::Keypair::from_protobuf_encoding(&bytes)?)
}

fn message_id(msg: &gossipsub::Message) -> gossipsub::MessageId {
    let mut s = DefaultHasher::new();
    msg.data.hash(&mut s);
    gossipsub::MessageId::from(s.finish().to_string())
}

fn create_test_message(
    peer_id: &PeerId,
) -> Result<(gossipsub::IdentTopic, UniversalConnectivityMessage)> {
    // Send a test message on the universal-connectivity topic
    let topic = gossipsub::IdentTopic::new("universal-connectivity");
    let message = UniversalConnectivityMessage {
        from: peer_id.to_string(),
        message: "Hello from {peer_id}!".to_string(),
        timestamp: SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs() as i64,
        message_type: MessageType::Chat as i32,
    };
    Ok((topic, message))
}

fn split_address(addr: Multiaddr) -> Option<(PeerId, Multiaddr)> {
    let mut base_addr = Multiaddr::empty();
    let mut peer_id = None;

    for protocol in addr.into_iter() {
        match protocol {
            Protocol::P2p(id) => {
                peer_id = Some(id);
                break;
            }
            _ => {
                base_addr.push(protocol);
            }
        }
    }

    peer_id.map(|id| (id, base_addr))
}

#[tokio::main]
async fn main() -> Result<()> {
    // parse the remote peer addresses from the environment variable
    let remote_peers = env::var("REMOTE_PEERS")?;
    let remote_addrs: Vec<Multiaddr> = remote_peers
        .split(',') // Split at ','
        .map(str::trim) // Trim whitespace
        .filter(|s| !s.is_empty()) // Filter out empty strings
        .map(Multiaddr::from_str) // Parse each string into Multiaddr
        .collect::<Result<Vec<_>, _>>()?; // Collect into Result and unwrap it

    // parse the bootstrap peer addresses from the environment variable
    let bootstrap_peers = env::var("BOOTSTRAP_PEERS")?;
    let bootstrap_addrs: Vec<Multiaddr> = bootstrap_peers
        .split(',') // Split at ','
        .map(str::trim) // Trim whitespace
        .filter(|s| !s.is_empty()) // Filter out empty strings
        .map(Multiaddr::from_str) // Parse each string into Multiaddr
        .collect::<Result<Vec<_>, _>>()?; // Collect into Result and unwrap it

    let local_key = read_identity().await?;
    let local_peer_id = local_key.public().to_peer_id();

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

    // Create Kademlia configuration
    let mut kad_config = kad::Config::new(KADEMLIA_PROTOCOL_NAME);
    kad_config.set_query_timeout(Duration::from_secs(KADEMLIA_QUERY_TIMEOUT));
    kad_config
        .set_periodic_bootstrap_interval(Some(Duration::from_secs(KADEMLIA_BOOTSTRAP_INTERVAL)));

    // Create Kademlia behavior with memory store
    let store = kad::store::MemoryStore::new(local_peer_id);
    let mut kademlia = kad::Behaviour::with_config(local_peer_id, store, kad_config);
    kademlia.set_mode(Some(kad::Mode::Server));

    // Add the bootstrap peer addresses to the kademlia behaviour
    for addr in bootstrap_addrs.into_iter() {
        if let Some((peer_id, peer_addr)) = split_address(addr) {
            println!("Adding bootstrap peer: {peer_id} with multiaddr: {peer_addr}");
            kademlia.add_address(&peer_id, peer_addr);
        }
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
            kademlia,
        })?
        .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
        .build();

    // listen on all addresses
    for addr in remote_addrs.into_iter() {
        swarm.listen_on(addr)?;
    }

    // Start the Kademlia bootstrap process
    swarm.behaviour_mut().kademlia.bootstrap()?;

    loop {
        tokio::select! {
            Some(event) = swarm.next() => match event {
                SwarmEvent::ConnectionEstablished { peer_id, connection_id, endpoint, .. } => {
                    println!("connected,{peer_id},{}", endpoint.get_remote_address());
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
                                        num_remaining, ..
                                    })) => {
                                        if num_remaining == 0 {
                                            println!("bootstrap");
                                        }
                                    }
                                    kad::QueryResult::Bootstrap(Err(kad::BootstrapError::Timeout { .. })) => {
                                        println!("error,bootstrap timed out");
                                    }
                                    kad::QueryResult::GetClosestPeers(Ok(kad::GetClosestPeersOk { peers, .. })) => {
                                        let mut out = String::from("closestpeers,");
                                        for (i, peer) in peers.iter().enumerate() {
                                            if i > 0 {
                                                out.push(',');
                                            }
                                            write!(&mut out, "{}", peer.peer_id)?;
                                            for addr in &peer.addrs {
                                                write!(&mut out, "-{addr}")?;
                                            }
                                        }
                                    }
                                    kad::QueryResult::GetClosestPeers(Err(kad::GetClosestPeersError::Timeout { .. })) => {
                                        println!("error,get closest peers timed out");
                                    }
                                    _ => {}
                                }
                            }
                            kad::Event::RoutingUpdated { peer, is_new_peer, addresses, old_peer, .. } => {
                                if is_new_peer {
                                    println!("New peer added to routing table: {peer} with {} addresses", addresses.len());
                                }
                                if let Some(old) = old_peer {
                                    println!("Peer {peer} replaced {old} in routing table");
                                }
                            }
                            kad::Event::UnroutablePeer { peer } => {
                                println!("Peer {peer} is unroutable");
                            }
                            kad::Event::RoutablePeer { peer, address } => {
                                println!("Peer {peer} is routable at {address}");
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
