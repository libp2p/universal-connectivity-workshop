use anyhow::Result;
use futures::StreamExt;
use libp2p::{
    core::transport::ListenerId,
    gossipsub, identify, identity, kad,
    multiaddr::Protocol,
    noise, ping, tcp,
    swarm::{NetworkBehaviour, SwarmEvent}, yamux,
    Multiaddr, PeerId, StreamProtocol, SwarmBuilder,
};
use prost::Message;
use std::{
    collections::hash_map::DefaultHasher,
    env,
    hash::{Hash, Hasher},
    path::PathBuf,
    str::FromStr,
    time::{Duration, SystemTime, UNIX_EPOCH},
};

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
const TICK_INTERVAL: tokio::time::Duration = tokio::time::Duration::from_secs(5);

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
    let bytes = tokio::fs::read(&key_path).await?;
    Ok(identity::Keypair::from_protobuf_encoding(&bytes)?)
}

fn message_id(msg: &gossipsub::Message) -> gossipsub::MessageId {
    let mut s = DefaultHasher::new();
    msg.data.hash(&mut s);
    gossipsub::MessageId::from(s.finish().to_string())
}

fn create_test_message(
    peer_id: &PeerId,
    counter: usize,
) -> Result<(gossipsub::IdentTopic, UniversalConnectivityMessage)> {
    // Send a test message on the universal-connectivity topic
    let topic = gossipsub::IdentTopic::new("universal-connectivity");
    let message = UniversalConnectivityMessage {
        from: peer_id.to_string(),
        message: format!("Hello from {peer_id}! ({counter})"),
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
    let mut listen_on: Vec<Multiaddr> = Vec::default();
    if let Ok(listen_addrs) = env::var("LISTEN_ADDRS") {
        listen_on = listen_addrs
            .split(',') // Split the string at ','
            .map(str::trim) // Trim whitespace of each string
            .filter(|s| !s.is_empty()) // Filter out empty strings
            .map(Multiaddr::from_str) // Parse each string into Multiaddr
            .collect::<Result<Vec<_>, _>>()?; // Collect into Result and unwrap it
    }

    // parse the bootstrap peer addresses from the environment variable
    let mut bootstrap_addrs: Vec<Multiaddr> = Vec::default();
    if let Ok(bootstrap_peers) = env::var("BOOTSTRAP_PEERS") {
        bootstrap_addrs = bootstrap_peers
            .split(',') // Split the string at ','
            .map(str::trim) // Trim whitespace of each string
            .filter(|s| !s.is_empty()) // Filter out empty strings
            .map(Multiaddr::from_str) // Parse each string into Multiaddr
            .collect::<Result<Vec<_>, _>>()?; // Collect into Result and unwrap it
    }

    // parse environment flags
    let close_after_connected: bool = env::var("CLOSE_AFTER_CONNECTED").is_ok();
    let close_after_ping: bool = env::var("CLOSE_AFTER_PING").is_ok();
    let close_after_identify: bool = env::var("CLOSE_AFTER_IDENTIFY").is_ok();
    let close_after_gossip_msg: bool = env::var("CLOSE_AFTER_GOSSIP_MSG").is_ok();
    let close_after_kademlia_bootstrap: bool = env::var("CLOSE_AFTER_KADEMLIA_BOOTSTRAP").is_ok();
    let chatty: bool = env::var("CHATTY").is_ok();

    // get our identity
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

    // listen on all addresses, remember listener ids
    let mut listeners: Vec<ListenerId> = Vec::with_capacity(listen_on.len());
    for addr in listen_on.into_iter() {
        if let Ok(listener_id) = swarm.listen_on(addr) {
            listeners.push(listener_id);
        }
    }

    if !bootstrap_addrs.is_empty() {
        // Add the bootstrap peer addresses to the kademlia behaviour
        for addr in bootstrap_addrs.into_iter() {
            if let Some((peer_id, peer_addr)) = split_address(addr) {
                swarm
                    .behaviour_mut()
                    .kademlia
                    .add_address(&peer_id, peer_addr);
            }
        }

        // Start the Kademlia bootstrap process
        swarm.behaviour_mut().kademlia.bootstrap()?;
    }

    // set up ticking timer
    let mut timer = tokio::time::interval(TICK_INTERVAL);
    let mut counter = 0;

    // hook into termination signals
    let mut sig_term = tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())?;
    let mut sig_quit = tokio::signal::unix::signal(tokio::signal::unix::SignalKind::quit())?;

    let mut shutdown = false;

    'run: loop {
        tokio::select! {
            event = swarm.select_next_some() => match event {
                SwarmEvent::ConnectionEstablished { peer_id, connection_id, endpoint, .. } => {
                    println!("connected,{peer_id},{}", endpoint.get_remote_address());
                    if close_after_connected {
                        swarm.close_connection(connection_id);
                    }
                }
                SwarmEvent::ConnectionClosed { peer_id, cause, .. } => {
                    if let Some(error) = cause {
                        println!("error,{error}");
                    } else {
                        println!("closed,{peer_id}");
                    }
                    if shutdown && swarm.network_info().num_peers() == 0 {
                        println!("nomorepeers");
                        break 'run Ok(());
                    }
                }
                SwarmEvent::IncomingConnection { local_addr, send_back_addr, .. } => {
                    println!("incoming,{local_addr},{send_back_addr}");
                }
                SwarmEvent::OutgoingConnectionError { error, .. } => {
                    println!("error,{error}");
                }
                SwarmEvent::Behaviour(behaviour_event) => match behaviour_event {
                    BehaviourEvent::Ping(ping::Event { peer, connection, result}) => {
                        match result {
                            Ok(rtt) => {
                                println!("ping,{peer},{} ms", rtt.as_millis());
                                if close_after_ping {
                                    swarm.close_connection(connection);
                                }
                            }
                            Err(error) => {
                                println!("error,{error}");
                            }
                        }
                    }
                    BehaviourEvent::Identify(identify_event) => {
                        match identify_event {
                            identify::Event::Received { peer_id, connection_id, info, .. } => {
                                println!("identify,{peer_id},{}", info.agent_version);
                                if close_after_identify {
                                    swarm.close_connection(connection_id);
                                }
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

                                    if close_after_gossip_msg {
                                        if let Ok(peer_id) = PeerId::from_str(&msg.from) {
                                            let _ = swarm.disconnect_peer_id(peer_id);
                                        }
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
                    BehaviourEvent::Kademlia(kad_event) => {
                        match kad_event {
                            kad::Event::OutboundQueryProgressed { result, .. } => {
                                match result {
                                    kad::QueryResult::Bootstrap(Ok(kad::BootstrapOk {
                                        num_remaining, ..
                                    })) => {
                                        if num_remaining == 0 {
                                            println!("kademlia,bootstrap");
                                            if close_after_kademlia_bootstrap {
                                                break 'run Ok(());
                                            }
                                        }
                                    }
                                    kad::QueryResult::Bootstrap(Err(kad::BootstrapError::Timeout { .. })) => {
                                        println!("error,bootstrap timed out");
                                    }
                                    kad::QueryResult::GetClosestPeers(Ok(kad::GetClosestPeersOk { peers, .. })) => {
                                        println!("kademlia,closestpeers,{}", peers.len());
                                        for peer in &peers {
                                            let mut out = format!("closestpeer,{}", peer.peer_id);
                                            for addr in &peer.addrs {
                                                out = format!("{out},{addr}");
                                            }
                                            println!("{out}");
                                        }
                                    }
                                    kad::QueryResult::GetClosestPeers(Err(kad::GetClosestPeersError::Timeout { .. })) => {
                                        println!("error,get closest peers timed out");
                                    }
                                    _ => {}
                                }
                            }
                            kad::Event::RoutingUpdated { peer, is_new_peer, old_peer, .. } => {
                                let mut out = "kademlia,routing_update".to_string();
                                if is_new_peer {
                                    out = format!("{out},new {peer}");
                                }
                                if let Some(old) = old_peer {
                                    out = format!("{out},replaced {old}")
                                }
                                println!("{out}");
                            }
                            kad::Event::UnroutablePeer { peer } => {
                                println!("kademlia,unroutable {peer}");
                            }
                            kad::Event::RoutablePeer { peer, address } => {
                                println!("kademlia,routable,{peer},{address}");
                            }
                            _ => {}
                        }
                    }
                }
                _ => {}
            },
            _ = timer.tick() => {
                if chatty {
                    counter += 1;
                    let (topic, msg) = create_test_message(&local_peer_id, counter)?;
                    let mut buf = Vec::new();
                    msg.encode(&mut buf)?;
                    if let Err(error) = swarm.behaviour_mut().gossipsub.publish(topic, buf) {
                        println!("error,{error}");
                    }
                }
            },
            _ = sig_term.recv() => {
                // turn off our listeners
                for listener_id in &listeners {
                    let _ = swarm.remove_listener(*listener_id);
                }

                // disconnect from all connected peers
                let connected: Vec<PeerId> = swarm.connected_peers().cloned().collect();
                for peer_id in &connected {
                    let _ = swarm.disconnect_peer_id(*peer_id);
                }

                shutdown = true;
            },
            _ = sig_quit.recv() => {
                // received SIG_QUIT
                println!("sigquit");
                break 'run Ok(());
            },
        }
    }

    // fin
}
