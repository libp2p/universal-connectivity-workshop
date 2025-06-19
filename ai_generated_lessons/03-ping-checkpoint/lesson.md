# Lesson 3: Protocol Basics - Ping Checkpoint ⭐

Congratulations on reaching your first checkpoint! In this lesson, you'll implement the ping protocol and connect to the instructor's server to demonstrate that your libp2p node can communicate with other peers.

## Learning Objectives

By the end of this lesson, you will:
- Understand the concept of NetworkBehaviour in libp2p
- Implement the ping protocol for basic peer communication
- Handle libp2p events in the event loop
- Successfully connect to a remote peer and exchange ping/pong messages

## Background: NetworkBehaviour and Protocols

In libp2p, **protocols** define how peers communicate. The **ping protocol** is the simplest protocol - it sends a ping message and expects a pong response, similar to ICMP ping but at the application layer.

**NetworkBehaviour** is a trait that defines how your node behaves on the network. You can compose multiple behaviors together to create complex networking applications. Each behavior handles specific protocols and events.

The ping protocol is useful for:
- Testing basic connectivity between peers
- Keeping connections alive
- Measuring round-trip time
- Validating that the networking stack is working

## 🏆 Checkpoint Challenge

Your goal is to create a libp2p application that:
1. Connects to the instructor's ping server
2. Sends ping messages and receives pong responses
3. Prints confirmation of successful ping exchanges

## Your Task

Extend your previous application to:
1. Add the ping behavior to your NetworkBehaviour
2. Handle ping events in the event loop
3. Connect to a specified multiaddr (instructor's server)
4. Print ping results for verification

## Step-by-Step Instructions

### Step 1: Update Dependencies

Add the ping feature to your `Cargo.toml`:

```toml
[dependencies]
libp2p = { version = "0.55", features = ["ed25519", "tokio", "macros", "ping", "tcp", "noise", "yamux"] }
tokio = { version = "1.0", features = ["full"] }
anyhow = "1.0"
```

### Step 2: Import Required Types

Add the ping-related imports to your `src/main.rs`:

```rust
use libp2p::ping::{self, Event as PingEvent};
use libp2p::swarm::SwarmEvent;
use std::env;
```

### Step 3: Update Your NetworkBehaviour

Replace your empty behavior with one that includes ping:

```rust
use libp2p::swarm::derive_prelude::*;

#[derive(NetworkBehaviour)]
struct Behaviour {
    ping: ping::Behaviour,
}
```

### Step 4: Create the Behaviour Instance

Update your swarm creation to include the ping behavior:

```rust
let behaviour = Behaviour {
    ping: ping::Behaviour::new(ping::Config::new()),
};

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
```

### Step 5: Connect to the Target Peer

Add code to connect to the instructor's server using the multiaddr from environment variables:

```rust
// Get the target multiaddr from environment variable
let target_multiaddr = env::var("CHECKER_MULTIADDR")
    .unwrap_or_else(|_| "/ip4/127.0.0.1/tcp/9000".to_string());

println!("Connecting to: {}", target_multiaddr);

// Parse and dial the multiaddr
let multiaddr: Multiaddr = target_multiaddr.parse()?;
swarm.dial(multiaddr)?;
```

### Step 6: Handle Events in the Event Loop

Update your event loop to handle ping events:

```rust
use futures::StreamExt;

loop {
    match swarm.select_next_some().await {
        SwarmEvent::NewListenAddr { address, .. } => {
            println!("Listening on: {}", address);
        }
        SwarmEvent::Behaviour(BehaviourEvent::Ping(ping_event)) => {
            match ping_event {
                PingEvent::Pong { peer, rtt } => {
                    println!("Ping successful to {}: RTT = {:?}", peer, rtt);
                }
                PingEvent::Failure { peer, error } => {
                    println!("Ping failed to {}: {}", peer, error);
                }
            }
        }
        SwarmEvent::ConnectionEstablished { peer_id, .. } => {
            println!("Connected to: {}", peer_id);
        }
        SwarmEvent::ConnectionClosed { peer_id, cause, .. } => {
            println!("Disconnected from {}: {:?}", peer_id, cause);
        }
        SwarmEvent::OutgoingConnectionError { error, .. } => {
            println!("Failed to connect: {}", error);
        }
        _ => {}
    }
}
```

Don't forget to import the required types:

```rust
use libp2p::{Multiaddr, swarm::SwarmEvent};
```

## Complete Solution Structure

Your complete `src/main.rs` should follow this structure:

```rust
// Imports
use anyhow::Result;
use futures::StreamExt;
use libp2p::identity;
use libp2p::ping::{self, Event as PingEvent};
use libp2p::swarm::{NetworkBehaviour, SwarmEvent};
use libp2p::{noise, tcp, yamux, Multiaddr};
use std::env;
use std::error::Error;
use std::time::Duration;

// Network behavior with ping
#[derive(NetworkBehaviour)]
struct Behaviour {
    ping: ping::Behaviour,
}

// Event type for pattern matching
#[allow(clippy::large_enum_variant)]
enum BehaviourEvent {
    Ping(PingEvent),
}

// Main function
#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    // Setup identity and swarm
    // Connect to target
    // Handle events
    Ok(())
}
```

## Testing Your Solution

When you run your application, you should see output like:

```
Starting Universal Connectivity application...
Local peer id: 12D3KooWGrCaG7G8eB3VV4z3h8Rj1r1j1j1j1j1j1j1j1j1j1j
Connecting to: /ip4/172.27.1.10/tcp/9000
Connected to: 12D3KooWInstructorPeerID
Ping successful to 12D3KooWInstructorPeerID: RTT = 5ms
Ping successful to 12D3KooWInstructorPeerID: RTT = 3ms
```

## Hints

## Hint - Import errors
Make sure you have all the necessary imports:

```rust
use anyhow::Result;
use futures::StreamExt;
use libp2p::identity;
use libp2p::ping::{self, Event as PingEvent};
use libp2p::swarm::{NetworkBehaviour, SwarmEvent};
use libp2p::{noise, tcp, yamux, Multiaddr};
use std::env;
use std::error::Error;
use std::time::Duration;
```

## Hint - NetworkBehaviour derive issues
If you get errors with the NetworkBehaviour derive, make sure you have the "macros" feature enabled in Cargo.toml and that your behaviour struct looks like:

```rust
#[derive(NetworkBehaviour)]
struct Behaviour {
    ping: ping::Behaviour,
}
```

## Hint - Event handling pattern
The event loop should handle multiple event types. Make sure you're matching on the correct patterns:

```rust
match swarm.select_next_some().await {
    SwarmEvent::Behaviour(BehaviourEvent::Ping(ping_event)) => {
        // Handle ping events
    }
    SwarmEvent::ConnectionEstablished { peer_id, .. } => {
        // Handle new connections
    }
    _ => {}
}
```

## Hint - Connection issues
If you can't connect to the target, check:
1. The CHECKER_MULTIADDR environment variable is set correctly
2. The target peer is running and accessible
3. Your multiaddr parsing is correct: `target_multiaddr.parse()?`

## Hint - Complete Solution

Here's the complete working solution:

```rust
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
    println!("Starting Universal Connectivity application...");
    
    // Generate a random Ed25519 keypair for our local peer
    let local_key = identity::Keypair::generate_ed25519();
    let local_peer_id = local_key.public().to_peer_id();
    
    println!("Local peer id: {}", local_peer_id);
    
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
    
    // Get the target multiaddr from environment variable
    let target_multiaddr = env::var("CHECKER_MULTIADDR")
        .unwrap_or_else(|_| "/ip4/127.0.0.1/tcp/9000".to_string());
    
    println!("Connecting to: {}", target_multiaddr);
    
    // Parse and dial the multiaddr
    let multiaddr: Multiaddr = target_multiaddr.parse()?;
    swarm.dial(multiaddr)?;
    
    // Run the network event loop
    loop {
        match swarm.select_next_some().await {
            SwarmEvent::NewListenAddr { address, .. } => {
                println!("Listening on: {}", address);
            }
            SwarmEvent::Behaviour(BehaviourEvent::Ping(ping_event)) => {
                match ping_event {
                    PingEvent::Pong { peer, rtt } => {
                        println!("Ping successful to {}: RTT = {:?}", peer, rtt);
                    }
                    PingEvent::Failure { peer, error } => {
                        println!("Ping failed to {}: {}", peer, error);
                    }
                }
            }
            SwarmEvent::ConnectionEstablished { peer_id, .. } => {
                println!("Connected to: {}", peer_id);
            }
            SwarmEvent::ConnectionClosed { peer_id, cause, .. } => {
                println!("Disconnected from {}: {:?}", peer_id, cause);
            }
            SwarmEvent::OutgoingConnectionError { error, .. } => {
                println!("Failed to connect: {}", error);
            }
            _ => {}
        }
    }
}
```

## 🏆 Checkpoint Success!

When your solution works correctly, you'll see ping/pong exchanges with the instructor's server. This proves that:

- Your libp2p node can establish connections
- Protocol negotiation is working
- You can communicate with other libp2p peers
- Your networking stack is properly configured

## What's Next?

Excellent work! You've successfully implemented your first libp2p protocol and connected to a remote peer. In the next lesson, you'll learn about modern transport protocols by adding QUIC support alongside TCP.

Key concepts you've learned:
- **NetworkBehaviour**: Composable protocol behaviors
- **Ping Protocol**: Simple request-response communication
- **Event Handling**: Processing network events in async loops
- **Remote Connections**: Dialing and connecting to other peers
- **Protocol Negotiation**: libp2p automatically handles protocol selection

Next up: Adding QUIC transport for faster, more efficient connections!