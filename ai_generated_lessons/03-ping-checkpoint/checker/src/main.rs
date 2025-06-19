use anyhow::Result;
use futures::StreamExt;
use libp2p::identity;
use libp2p::ping::{self, Event as PingEvent};
use libp2p::swarm::{NetworkBehaviour, SwarmEvent};
use libp2p::{noise, tcp, yamux, Multiaddr};
use std::env;
use std::error::Error;
use std::time::Duration;

#[derive(NetworkBehaviour)]
struct Behaviour {
    ping: ping::Behaviour,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    println!("r Starting ping checker server...");
    
    // Generate a random Ed25519 keypair for the checker
    let local_key = identity::Keypair::generate_ed25519();
    let local_peer_id = local_key.public().to_peer_id();
    
    println!("i Checker peer id: {}", local_peer_id);
    
    // Create behavior with ping
    let behaviour = Behaviour {
        ping: ping::Behaviour::new(ping::Config::new()),
    };
    
    // Build the Swarm
    let mut swarm = libp2p::SwarmBuilder::with_existing_identity(local_key)
        .with_tokio()
        .with_tcp(
            tcp::Config::default(),
            noise::Config::new,
            yamux::Config::default,
        )?
        .with_behaviour(|_key| behaviour)?
        .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
        .build();
    
    // Get configuration from environment
    let checker_ip = env::var("CHECKER_IP").unwrap_or_else(|_| "0.0.0.0".to_string());
    let checker_port = env::var("CHECKER_PORT").unwrap_or_else(|_| "9000".to_string());
    
    // Create listen address
    let listen_addr: Multiaddr = format!("/ip4/{}/tcp/{}", checker_ip, checker_port).parse()?;
    
    // Start listening
    swarm.listen_on(listen_addr.clone())?;
    println!("i Checker listening on: {}", listen_addr);
    
    let mut student_connected = false;
    let mut ping_exchanges = 0;
    
    // Run the network event loop
    loop {
        match swarm.select_next_some().await {
            SwarmEvent::NewListenAddr { address, .. } => {
                println!("i Checker listening on: {}", address);
            }
            SwarmEvent::Behaviour(BehaviourEvent::Ping(ping_event)) => {
                match ping_event {
                    PingEvent::Pong { peer, rtt } => {
                        ping_exchanges += 1;
                        println!("v Ping response sent to {}: RTT = {:?} (exchange #{})", peer, rtt, ping_exchanges);
                        
                        if ping_exchanges >= 3 {
                            println!("y Checkpoint completed! Student successfully exchanged {} pings", ping_exchanges);
                            break;
                        }
                    }
                    PingEvent::Failure { peer, error } => {
                        println!("x Ping failed with {}: {}", peer, error);
                    }
                }
            }
            SwarmEvent::ConnectionEstablished { peer_id, .. } => {
                student_connected = true;
                println!("v Student connected: {}", peer_id);
            }
            SwarmEvent::ConnectionClosed { peer_id, cause, .. } => {
                println!("i Student disconnected {}: {:?}", peer_id, cause);
                if student_connected && ping_exchanges < 3 {
                    println!("x Student disconnected before completing checkpoint");
                    break;
                }
            }
            SwarmEvent::IncomingConnection { local_addr, send_back_addr } => {
                println!("i Incoming connection from {} to {}", send_back_addr, local_addr);
            }
            SwarmEvent::IncomingConnectionError { local_addr, send_back_addr, error } => {
                println!("x Incoming connection error from {} to {}: {}", send_back_addr, local_addr, error);
            }
            _ => {}
        }
    }
    
    if ping_exchanges >= 3 {
        println!("y SUCCESS: Ping checkpoint completed with {} exchanges", ping_exchanges);
    } else {
        println!("x FAILURE: Only {} ping exchanges completed, expected at least 3", ping_exchanges);
    }
    
    Ok(())
}