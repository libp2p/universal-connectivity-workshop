# Lesson 2: Transport Layer - TCP Connection

Building on your basic libp2p node, you'll now learn about transport layers and establish your first peer-to-peer connections using TCP with security protocols.

## Learning Objectives

By the end of this lesson, you will:
- Understand libp2p's transport abstraction
- Configure TCP transport with security and multiplexing
- Establish connections between two libp2p nodes
- Understand the role of Noise encryption and Yamux multiplexing

## Background: Transport Layers in libp2p

In libp2p, **transports** handle the low-level network communication. A transport defines how data travels between peers. libp2p supports multiple transports:

- **TCP**: Reliable, ordered, connection-oriented (like HTTP)
- **QUIC**: Modern UDP-based with built-in encryption
- **WebRTC**: For browser connectivity
- **Memory**: For testing and local communication

Each transport can be enhanced with:
- **Security protocols**: Encrypt communication (Noise, TLS)
- **Multiplexers**: Share one connection for multiple streams (Yamux, Mplex)

## Transport Stack

A typical libp2p connection stack looks like:
```
Application protocols (ping, gossipsub, etc.)
        ↕
    Multiplexer (Yamux)
        ↕
   Security (Noise/TLS)
        ↕
    Transport (TCP/QUIC)
        ↕
      Network (IP)
```

## Your Task

Extend your application to:
1. Add listening capability so other peers can connect to you
2. Test connection establishment between two instances
3. Print connection events for verification
4. Run two instances and connect them together

## Step-by-Step Instructions

### Step 1: Update Your Event Loop

Modify your event loop to handle more connection events and add listening:

```rust
// Start listening on a local port
swarm.listen_on("/ip4/0.0.0.0/tcp/0".parse()?)?;

loop {
    match swarm.select_next_some().await {
        SwarmEvent::NewListenAddr { address, .. } => {
            println!("Listening on: {}", address);
        }
        SwarmEvent::ConnectionEstablished { peer_id, endpoint, .. } => {
            println!("Connected to: {} via {}", peer_id, endpoint.get_remote_address());
        }
        SwarmEvent::ConnectionClosed { peer_id, endpoint, cause, .. } => {
            println!("Disconnected from {}: {:?}", peer_id, cause);
        }
        SwarmEvent::IncomingConnection { local_addr, send_back_addr } => {
            println!("Incoming connection from {} to {}", send_back_addr, local_addr);
        }
        SwarmEvent::OutgoingConnectionError { peer_id, error, .. } => {
            println!("Failed to connect to {:?}: {}", peer_id, error);
        }
        SwarmEvent::IncomingConnectionError { local_addr, send_back_addr, error } => {
            println!("Incoming connection failed from {} to {}: {}", send_back_addr, local_addr, error);
        }
        _ => {}
    }
}
```

### Step 2: Add Connection Command Line Arguments

Add command line argument support to optionally connect to another peer:

```rust
use std::env;

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = env::args().collect();
    
    // ... existing setup code ...
    
    // Check if a target address was provided
    if args.len() > 1 {
        let target_addr = &args[1];
        println!("Attempting to connect to: {}", target_addr);
        
        match target_addr.parse::<Multiaddr>() {
            Ok(addr) => {
                swarm.dial(addr)?;
            }
            Err(e) => {
                println!("Invalid multiaddr '{}': {}", target_addr, e);
            }
        }
    }
    
    // ... event loop ...
}
```

### Step 3: Test Your Transport Configuration

Your transport configuration should already include:
- **TCP**: For network connectivity
- **Noise**: For encryption
- **Yamux**: For multiplexing

The configuration from Lesson 1 already sets this up:
```rust
.with_tcp(
    tcp::Config::default(),
    noise::Config::new,
    yamux::Config::default,
)?
```

### Step 4: Add Better Error Handling

Improve your connection handling:

```rust
SwarmEvent::OutgoingConnectionError { peer_id, error, .. } => {
    match peer_id {
        Some(peer) => println!("Failed to connect to {}: {}", peer, error),
        None => println!("Failed to connect: {}", error),
    }
}
```

## Complete Solution Structure

Your updated `src/main.rs` should follow this structure:

```rust
// Imports (same as Lesson 1 plus Multiaddr)
use anyhow::Result;
use futures::StreamExt;
use libp2p::identity;
use libp2p::swarm::{NetworkBehaviour, SwarmEvent};
use libp2p::{noise, tcp, yamux, Multiaddr};
use std::env;
use std::error::Error;
use std::time::Duration;

// Empty behavior (same as Lesson 1)
#[derive(NetworkBehaviour)]
struct Behaviour {}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    // Parse command line arguments
    // Generate identity and create swarm
    // Start listening
    // Optionally connect to target
    // Run event loop with connection handling
    Ok(())
}
```

## Testing Your Solution

### Test 1: Single Instance
Run your application and verify it starts listening:
```bash
cargo run
```

You should see:
```
Starting Universal Connectivity application...
Local peer id: 12D3KooWGrCaG7G8eB3VV4z3h8Rj1r1j1j1j1j1j1j1j1j1j1j
Listening on: /ip4/127.0.0.1/tcp/54321
Listening on: /ip4/192.168.1.100/tcp/54321
```

### Test 2: Two Instances Connected
1. Start the first instance and note its listening address:
```bash
cargo run
# Note the port number, e.g., 54321
```

2. In another terminal, start a second instance and connect to the first:
```bash
cargo run /ip4/127.0.0.1/tcp/54321
```

You should see connection establishment on both sides.

## Expected Output

**First instance:**
```
Starting Universal Connectivity application...
Local peer id: 12D3KooWFirst...
Listening on: /ip4/127.0.0.1/tcp/54321
Incoming connection from /ip4/127.0.0.1/tcp/54322 to /ip4/127.0.0.1/tcp/54321
Connected to: 12D3KooWSecond... via /ip4/127.0.0.1/tcp/54322
```

**Second instance:**
```
Starting Universal Connectivity application...
Local peer id: 12D3KooWSecond...
Attempting to connect to: /ip4/127.0.0.1/tcp/54321
Listening on: /ip4/127.0.0.1/tcp/54322
Connected to: 12D3KooWFirst... via /ip4/127.0.0.1/tcp/54321
```

## Hints

## Hint - Missing imports
Make sure you import Multiaddr:

```rust
use libp2p::{noise, tcp, yamux, Multiaddr};
use std::env;
```

## Hint - Listening setup
To start listening on all interfaces with a random port:

```rust
swarm.listen_on("/ip4/0.0.0.0/tcp/0".parse()?)?;
```

The port `0` means "assign any available port".

## Hint - Command line argument parsing
Basic argument parsing:

```rust
let args: Vec<String> = env::args().collect();
if args.len() > 1 {
    let target_addr = &args[1];
    // Use target_addr
}
```

## Hint - Event pattern matching
Complete event handling pattern:

```rust
match swarm.select_next_some().await {
    SwarmEvent::NewListenAddr { address, .. } => {
        println!("Listening on: {}", address);
    }
    SwarmEvent::ConnectionEstablished { peer_id, endpoint, .. } => {
        println!("Connected to: {} via {}", peer_id, endpoint.get_remote_address());
    }
    SwarmEvent::ConnectionClosed { peer_id, cause, .. } => {
        println!("Disconnected from {}: {:?}", peer_id, cause);
    }
    SwarmEvent::IncomingConnection { local_addr, send_back_addr } => {
        println!("Incoming connection from {} to {}", send_back_addr, local_addr);
    }
    SwarmEvent::OutgoingConnectionError { peer_id, error, .. } => {
        match peer_id {
            Some(peer) => println!("Failed to connect to {}: {}", peer, error),
            None => println!("Failed to connect: {}", error),
        }
    }
    _ => {}
}
```

## Hint - Complete Solution

Here's the complete working solution:

```rust
use anyhow::Result;
use futures::StreamExt;
use libp2p::identity;
use libp2p::swarm::{NetworkBehaviour, SwarmEvent};
use libp2p::{noise, tcp, yamux, Multiaddr};
use std::env;
use std::error::Error;
use std::time::Duration;

#[derive(NetworkBehaviour)]
struct Behaviour {}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    println!("Starting Universal Connectivity application...");
    
    let args: Vec<String> = env::args().collect();
    
    // Generate a random Ed25519 keypair for our local peer
    let local_key = identity::Keypair::generate_ed25519();
    let local_peer_id = local_key.public().to_peer_id();
    
    println!("Local peer id: {}", local_peer_id);
    
    // Build the Swarm
    let mut swarm = libp2p::SwarmBuilder::with_existing_identity(local_key)
        .with_tokio()
        .with_tcp(
            tcp::Config::default(),
            noise::Config::new,
            yamux::Config::default,
        )?
        .with_behaviour(|_key| Behaviour {})?
        .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
        .build();
    
    // Start listening
    swarm.listen_on("/ip4/0.0.0.0/tcp/0".parse()?)?;
    
    // Check if a target address was provided
    if args.len() > 1 {
        let target_addr = &args[1];
        println!("Attempting to connect to: {}", target_addr);
        
        match target_addr.parse::<Multiaddr>() {
            Ok(addr) => {
                swarm.dial(addr)?;
            }
            Err(e) => {
                println!("Invalid multiaddr '{}': {}", target_addr, e);
            }
        }
    }
    
    // Run the network event loop
    loop {
        match swarm.select_next_some().await {
            SwarmEvent::NewListenAddr { address, .. } => {
                println!("Listening on: {}", address);
            }
            SwarmEvent::ConnectionEstablished { peer_id, endpoint, .. } => {
                println!("Connected to: {} via {}", peer_id, endpoint.get_remote_address());
            }
            SwarmEvent::ConnectionClosed { peer_id, cause, .. } => {
                println!("Disconnected from {}: {:?}", peer_id, cause);
            }
            SwarmEvent::IncomingConnection { local_addr, send_back_addr } => {
                println!("Incoming connection from {} to {}", send_back_addr, local_addr);
            }
            SwarmEvent::OutgoingConnectionError { peer_id, error, .. } => {
                match peer_id {
                    Some(peer) => println!("Failed to connect to {}: {}", peer, error),
                    None => println!("Failed to connect: {}", error),
                }
            }
            SwarmEvent::IncomingConnectionError { local_addr, send_back_addr, error } => {
                println!("Incoming connection failed from {} to {}: {}", send_back_addr, local_addr, error);
            }
            _ => {}
        }
    }
}
```

## What's Next?

Excellent! You've successfully configured TCP transport and established peer-to-peer connections. You now understand:

- **Transport Layer**: How libp2p handles network communication
- **Security**: Noise protocol for encrypted connections  
- **Multiplexing**: Yamux for sharing connections
- **Connection Management**: Handling incoming and outgoing connections
- **Event-Driven Programming**: Responding to network events

In the next lesson, you'll add your first protocol (ping) and connect to the instructor's server for your first checkpoint!

Key concepts you've learned:
- **libp2p Transport Stack**: TCP + Noise + Yamux
- **Connection Events**: Establishment, closing, and errors
- **Listening and Dialing**: Acting as both client and server
- **Multiaddresses**: libp2p's addressing format

Next up: Adding the ping protocol and achieving your first checkpoint!