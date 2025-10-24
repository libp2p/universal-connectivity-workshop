# Lesson 5: Identify Checkpoint 🏆

Welcome to your second checkpoint! In this lesson, you'll implement the Identify protocol, which allows libp2p peers to exchange information about their capabilities, supported protocols, and network details.

## Learning Objectives

By the end of this lesson, you will:
- Understand the purpose of the Identify protocol in libp2p
- Add Identify behavior to your NetworkBehaviour
- Handle identify events and extract peer information
- Exchange protocol capabilities with remote peers

## Background: The Identify Protocol

The Identify protocol is fundamental to libp2p's peer discovery and capability negotiation. It serves several important purposes:

- **Capability Discovery**: Learn what protocols a peer supports
- **Version Information**: Exchange software version and agent strings
- **Address Discovery**: Learn how peers see your external addresses
- **Protocol Negotiation**: Establish common protocols for communication

When peers connect, they automatically exchange identification information, allowing the network to be self-describing and adaptive.

## Your Task

Building on your QUIC transport implementation from Lesson 4, you need to:

1. **Add Identify Behavior**: Include `identify::Behaviour` in your `NetworkBehaviour` struct
2. **Configure Identify Settings**: Set up identify with the IPFS protocol and Universal Connectivity agent string
3. **Handle Identify Events**: Process identification events and display peer information

## Step-by-Step Instructions

### Step 1: Update Dependencies

Add the `identify` feature to your Cargo.toml features:

```toml
[dependencies]
libp2p = { version = "0.56", features = ["ed25519", "identify", "macros", "noise", "ping", "quic", "tcp", "tokio", "yamux"] }
```

### Step 2: Add Identify Import

Add the `identify` import to your existing imports:

```rust
use anyhow::Result;
use futures::StreamExt;
use libp2p::{
    identify, identity, noise, ping, tcp, yamux,
    Multiaddr, SwarmBuilder,
    swarm::{NetworkBehaviour, SwarmEvent}
};
use std::{env, str::FromStr, time::Duration};
```

### Step 3: Update Your NetworkBehaviour

Add the `identify` behavior to your existing behavior struct:

```rust
#[derive(NetworkBehaviour)]
struct Behaviour {
    ping: ping::Behaviour,
    identify: identify::Behaviour,
}
```

### Step 4: Set Up Identify String Constants

When you use identify there are two strings you must configure it with. One is the protocol version and the other is the agent identification string. It is typically a good idea to setup constant values for these so that you can reference them in multiple places and be certain that the values are the same everywhere. Let's define the constants at the top of your file:

```rust
const IDENTIFY_PROTOCOL_VERSION: &str = "/ipfs/id/1.0.0";
const AGENT_VERSION: &str = "universal-connectivity/0.1.0";
```

### Step 5: Configure Identify in the Swarm Builder

When creating your behavior, configure the identify protocol:

```rust
// Build the Swarm
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
            identify::Config::new(IDENTIFY_PROTOCOL_VERSION.to_string(), key.public())
                .with_agent_version(AGENT_VERSION.to_string())
        ),
    })?
    .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
    .build();
```

Note that we now use the `key` parameter the the closure to configure `identify` with your peer's public key.

### Step 6: Handle Identify Events

Just like in previous lessons, we need to add the identify protocol event handlers. In your event loop, add handling for identify events alongside your existing ping events:

```rust
loop {
    tokio::select! {
        Some(event) = swarm.next() => match event {
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
            SwarmEvent::OutgoingConnectionError { peer_id, error, .. } => {
                println!("Failed to connect to {peer_id:?}: {error}");
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
                            println!("Identified peer: {peer_id} with protocol version: {}", info.protocol_version);
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
            _ => {}
        }
    }
}
```

## Testing Your Implementation

1. Set the environment variables:
   ```bash
   export PROJECT_ROOT=/path/to/workshop
   export LESSON_PATH=en/rs/05-identify-checkpoint
   ```

2. Change into the lesson directory:
    ```bash
    cd $PROJECT_ROOT/$LESSON_PATH
    ```

3. Run with Docker Compose:
   ```bash
   docker rm -f workshop-lesson ucw-checker-en
   docker network rm -f workshop-net
   docker network create --driver bridge --subnet 172.16.16.0/24 workshop-net
   docker compose --project-name workshop up --build --remove-orphans
   ```

4. Check your output:
   ```bash
   python check.py
   ```

## Success Criteria

Your implementation should:
- ✅ Display the startup message and local peer ID
- ✅ Successfully dial the remote peer
- ✅ Establish a connection
- ✅ Send and receive ping messages
- ✅ Exchange identify information
- ✅ Display peer protocol version and agent string

## Hints

## Hint - Complete Solution

Here's the complete working solution:

```rust
use anyhow::Result;
use futures::StreamExt;
use libp2p::{
    identify, identity, noise, ping, tcp, yamux,
    Multiaddr, SwarmBuilder,
    swarm::{NetworkBehaviour, SwarmEvent}
};
use std::{env, str::FromStr, time::Duration};

const IDENTIFY_PROTOCOL_VERSION: &str = "/ipfs/id/1.0.0";
const AGENT_VERSION: &str = "universal-connectivity/0.1.0";

#[derive(NetworkBehaviour)]
struct Behaviour {
    ping: ping::Behaviour,
    identify: identify::Behaviour,
}

#[tokio::main]
async fn main() -> Result<()> {
    println!("Starting Universal Connectivity Application...");

    // parse the remote peer addresses from the environment variable
    let mut remote_addrs: Vec<Multiaddr> = Vec::default();
    if let Ok(remote_peers) = env::var("REMOTE_PEERS") {
        remote_addrs = remote_peers
            .split(',')                         // Split the string at ','
            .map(str::trim)                     // Trim whitespace of each string
            .filter(|s| !s.is_empty())          // Filter out empty strings
            .map(Multiaddr::from_str)           // Parse each string into Multiaddr
            .collect::<Result<Vec<_>, _>>()?;   // Collect into Result and unwrap it
    }

    // Generate a random Ed25519 keypair for our local peer
    let local_key = identity::Keypair::generate_ed25519();
    let local_peer_id = identity::PeerId::from(local_key.public());

    println!("Local peer id: {local_peer_id}");

    // Build the swarm
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
                identify::Config::new(IDENTIFY_PROTOCOL_VERSION.to_string(), key.public())
                    .with_agent_version(AGENT_VERSION.to_string())
            ),
        })?
        .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
        .build();

    // Dial all of the remote peer Multiaddrs
    for addr in remote_addrs.into_iter() {
        swarm.dial(addr)?;
    }

    loop {
        tokio::select! {
            Some(event) = swarm.next() => match event {
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
                SwarmEvent::OutgoingConnectionError { peer_id, error, .. } => {
                    println!("Failed to connect to {peer_id:?}: {error}");
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
                                println!("Identified peer: {peer_id} with protocol version: {}", info.protocol_version);
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
                _ => {}
            }
        }
    }
}
```

## What's Next?

Congratulations! You've reached your second checkpoint 🎉

You now have a libp2p node that can:
- Support multiple transports (TCP and QUIC)
- Measure connectivity with ping
- Exchange peer capabilities with identify

Key concepts you've learned:
- **Identify Protocol**: Exchanging peer capabilities and metadata
- **Protocol Negotiation**: How peers learn about each other's supported protocols
- **Agent Strings**: Identifying software versions in the network
- **Capability Discovery**: Building adaptive peer-to-peer networks

In the next lesson, you'll implement Gossipsub for publish-subscribe messaging, allowing peers to communicate through topic-based channels!
