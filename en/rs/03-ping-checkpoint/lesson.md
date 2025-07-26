# Lesson 3: Ping Checkpoint 🏆

Welcome to your first checkpoint! In this lesson, you'll implement the ping protocol, one of the fundamental protocols in libp2p that allows peers to measure connectivity and round-trip times.

## Learning Objectives

By the end of this lesson, you will:
- Understand the purpose and mechanics of the ping protocol
- Add ping behavior to your NetworkBehaviour
- Handle ping events and display connection quality metrics  
- Successfully establish bidirectional connectivity with a remote peer

## Background: The Ping Protocol

The ping protocol in libp2p serves several important purposes:
- **Connectivity Testing**: Verifies that connections are working bidirectionally
- **Latency Measurement**: Measures round-trip time between peers
- **Keep-Alive**: Helps maintain connections by sending periodic traffic
- **Network Quality**: Provides insights into connection stability

Unlike ICMP ping, libp2p's ping protocol works over any transport and respects the encryption and multiplexing layers.

## Your Task

Building on your TCP transport implementation from Lesson 2, you need to:

1. **Configure Ping Settings**: Set up ping with a 1-second interval and 5-second timeout
2. **Handle Ping Events**: Process `ping::Event` and display round-trip times

## Step-by-Step Instructions

### Step 1: Update Your NetworkBehaviour

Your existing NetworkBehaviour already includes the `ping` behavior from Lesson 1, but now you need to configure it properly. Your NetworkBehaviour should already look like the following:

```rust
#[derive(NetworkBehaviour)]
struct Behaviour {
    ping: ping::Behaviour,
}
```

### Step 2: Configure Ping in the Swarm Builder

When creating your behavior, instead of using a `ping::Behaviour::default()`, we want to use the `ping::Behaviour::new()` function and provide it with a `ping::Config` that is configured with the correct 1 second interval and 5 second timeout. The default settings for interval and timeout are 15 seconds and 20 seconds respectively. We are making those values shorter so that when we test this solution we'll send and receive pings immediately after establishing a connection to the remote peer. This is just for convenience. In normal networking situations, the defaults are more appropriate. When programming for mobile or other battery powered devices, you should make the interval and timeout much longer, such as 30 and 45 seconds so that the radio in the device can spend less time in the high power active state.

Modify your code that builds the swarm so that the ping behaviour is configured like this:

```rust
// Build the Swarm
let mut swarm = libp2p::SwarmBuilder::with_existing_identity(local_key)
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
```

### Step 3: Handle Ping Events

In your event loop, add handling for ping events alongside your existing connection events:

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
            }
            _ => {}
        }
    }
}
```

## Testing Your Implementation

If you are using the workshop tool to take this workshop, you only have to hit the `c` key to check your solutionto see if it is correct. However if you would like to test your solution manually, you can follow these steps. The `PROJECT_ROOT` environment variable is the path to your Rust project. The `LESSON_PATH` for this lesson is most likely `.workshop/universal-conectivity-workshop/en/rs/03-ping-checkpoint`.

1. Set the environment variables:
   ```bash
   export PROJECT_ROOT=/path/to/workshop
   export LESSON_PATH=en/rs/03-ping-checkpoint
   ```

2. Change into the lesson directory:
    ```bash
    cd $PROJECT_ROOT/$LESSON_PATH
    ```

3. Run with Docker Compose:
   ```bash
   docker rm -f workshop-lesson ucw-checker-03-ping-checkpoint
   docker network rm -f workshop-net
   docker network create --driver bridge --subnet 172.16.16.0/24 workshop-net
   docker compose --project-name workshop up --build --remove-orphans
   ```

4. Run the Python script to check your output:
   ```bash
   python check.py
   ```

## Success Criteria

Your implementation should:
- ✅ Display the startup message and local peer ID
- ✅ Successfully dial the remote peer
- ✅ Establish a connection
- ✅ Send and receive ping messages
- ✅ Display round-trip times in milliseconds

## Hints

## Hint - Complete Solution

Here's the complete working solution:

```rust
use anyhow::Result;
use futures::StreamExt;
use libp2p::{
    identity, noise, ping, tcp, yamux,
    Multiaddr, SwarmBuilder,
    swarm::{NetworkBehaviour, SwarmEvent}
};
use std::{env, str::FromStr, time::Duration};

#[derive(NetworkBehaviour)]
struct Behaviour {
    ping: ping::Behaviour,
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

    // Build the Swarm
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
                }
                _ => {}
            }
        }
    }
}
```

## What's Next?

Congratulations! You've reached your first checkpoint 🎉

You now have a libp2p node that can:
- Generate a stable identity
- Create encrypted, multiplexed connections  
- Measure connection quality with pings

Key concepts you've learned:
- **Ping Protocol**: Testing connectivity and measuring latency
- **NetworkBehaviour Events**: Handling protocol-specific events
- **Configuration**: Customizing protocol behavior
- **Bidirectional Communication**: Both sending and receiving messages

In the next lesson, you'll explore QUIC transport as an alternative to TCP, learning about libp2p's multi-transport capabilities.
