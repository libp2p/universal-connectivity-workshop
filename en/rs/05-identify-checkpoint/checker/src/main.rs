use anyhow::Result;
use futures::StreamExt;
use libp2p::identity;
use libp2p::{identify, noise, tcp, yamux, Multiaddr, SwarmBuilder};
use libp2p::{
    ping,
    swarm::{NetworkBehaviour, SwarmEvent},
};
use std::env;
use std::time::Duration;

// Define a custom network behaviour that includes ping and identify functionality
#[derive(NetworkBehaviour)]
struct Behaviour {
    ping: ping::Behaviour,
    identify: identify::Behaviour,
}

#[tokio::main]
async fn main() -> Result<()> {
    println!("Starting Universal Connectivity Application...");

    let remote_peer = env::var("REMOTE_PEER")?;
    let remote_addr: Multiaddr = remote_peer.parse()?;

    let local_key = identity::Keypair::generate_ed25519();
    let local_peer_id = identity::PeerId::from(local_key.public());
    println!("Local peer id: {local_peer_id}");

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
                identify::Config::new("/ipfs/id/1.0.0".to_string(), key.public())
                    .with_agent_version("universal-connectivity/0.1.0".to_string()),
            ),
        })?
        .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
        .build();

    swarm.listen_on(remote_addr)?;

    loop {
        tokio::select! {
            Some(event) = swarm.next() => match event {
                SwarmEvent::NewListenAddr { address, .. } => {
                    println!("Listening on: {address}");
                }
                SwarmEvent::ConnectionEstablished { peer_id, endpoint, .. } => {
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
                }
                SwarmEvent::OutgoingConnectionError { peer_id, error, .. } => {
                    println!("Failed to connect to {peer_id:?}: {error}");
                }
                _ => {}
            }
        }
    }
}
