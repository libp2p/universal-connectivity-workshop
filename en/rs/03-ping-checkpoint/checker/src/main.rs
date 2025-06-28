use anyhow::Result;
use futures::StreamExt;
use libp2p::{
    identity, noise, ping,
    swarm::{NetworkBehaviour, SwarmEvent},
    tcp, yamux, Multiaddr, SwarmBuilder,
};
use std::{env, str::FromStr, time::Duration};

// Define a custom network behaviour that includes ping functionality
#[derive(NetworkBehaviour)]
struct Behaviour {
    ping: ping::Behaviour,
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
                    .with_timeout(Duration::from_secs(5)),
            ),
        })?
        .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
        .build();

    // listen on all addresses
    for addr in remote_addrs.into_iter() {
        swarm.listen_on(addr)?;
    }

    loop {
        tokio::select! {
            Some(event) = swarm.next() => match event {
                SwarmEvent::ConnectionEstablished { peer_id, endpoint, .. } => {
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
                SwarmEvent::Behaviour(behaviour_event) => match behaviour_event {
                    BehaviourEvent::Ping(ping::Event { peer, connection, result }) => {
                        match result {
                            Ok(rtt) => {
                                println!("ping,{peer},{} ms", rtt.as_millis());
                            }
                            Err(failure) => {
                                println!("error,{failure}");
                            }
                        }
                        swarm.close_connection(connection);
                    }
                }
                SwarmEvent::OutgoingConnectionError { error, .. } => {
                    println!("error,{error}");
                }
                _ => {}
            }
        }
    }
}
