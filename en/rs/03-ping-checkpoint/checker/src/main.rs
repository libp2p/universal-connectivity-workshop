use anyhow::Result;
use futures::StreamExt;
use libp2p::identity;
use libp2p::{noise, tcp, yamux, Multiaddr, SwarmBuilder};
use libp2p::{
    ping,
    swarm::{NetworkBehaviour, SwarmEvent},
};
use std::env;
use std::time::Duration;

// Define a custom network behaviour that includes ping functionality
#[derive(NetworkBehaviour)]
struct Behaviour {
    ping: ping::Behaviour,
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
        .with_behaviour(|_| Behaviour {
            ping: ping::Behaviour::new(
                ping::Config::new()
                    .with_interval(Duration::from_secs(1))
                    .with_timeout(Duration::from_secs(5))
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
                }
                SwarmEvent::OutgoingConnectionError { peer_id, error, .. } => {
                    println!("Failed to connect to {peer_id:?}: {error}");
                }
                _ => {}
            }
        }
    }
}