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
              Transport (TCP)
                    ↕
                Network (IP)
```

Note that QUIC is a modern alternative to TCP, providing built-in encryption and multiplexing. When using QUIC as your transport the libp2p connection stack looks like:

```
Application protocols (ping, gossipsub, etc.)
                   ↕
            Multiplexer ───┐
            Security     (QUIC)
            Transport   ───┘
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

### Step 1: Add Imports

In your `src/main.rs`, ensure you have the necessary imports. You will need to import `Multiaddr` for handling addresses and `SwarmEvent` for handling connection events. Add the following imports at the top of your file:

```rust
use std::{env, str::FromStr}; // <- Add this whole line
use libp2p::{noise, tcp, yamux, SwarmBuilder, Multiaddr}; // <- Add Multiaddr
use libp2p::{ping, swarm::{NetworkBehaviour, SwarmEvent}}; // <- Add SwarmEvent
```

### Step 2: Parse the Multiaddr from Environment Variable

In this workshop, one or more `Multiaddr` strings for remote peers is always set in the environment variable `REMOTE_PEERS`. It is important to note that the value of `REMOTE_PEERS` is not an IP address but rather one or more `Multiaddr` strings separated by commas. `Multiaddr` strings looks something like: `/ip4/172.16.16.17/tcp/9092`.

To parse the list of `Multiaddr` strings, add the following code to your `main` function:

```rust
#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    println!("Starting Universal Connectivity application...");

    let remote_peers = env::var("REMOTE_PEERS")?;
    let remote_addrs: Vec<Multiaddr> = remote_peers
        .split(',') // Split at ','
        .map(str::trim) // Trim whitespace
        .filter(|s| !s.is_empty()) // Filter out empty strings
        .map(Multiaddr::from_str) // Parse each string into Multiaddr
        .collect<Result<Multiaddr, _>>()?; // Collect into Result and unwrap it
    
    // ... existing code ...
}
```

### Step 3: Add Code to Dial the Remote Peer

Right after you build your `swarm` and right before you enter the event loop, add the code to dial the remote peer:
    
```rust
#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    println!("Starting Universal Connectivity application...");

    // ... existing code initialize and build the swarm ...

    // Dial all of the remote peer Multiaddrs
    for addr in remote_addrs.into_iter() {
        swarm.dial(addr)?;
    }

    // ... existing event loop code ...
}
```

If you run your peer now, nothing happens because even though you dialed the remote peer, you haven't set up any event handling to see the connection events.

### Step 4: Update Your Event Loop

By default, a libp2p swarm will emit events when it starts listening, connects to peers, or encounters errors. You need to handle these events in your event loop. The connection related swarm events are all documented here in [enum SwarmEvent](https://docs.rs/libp2p/0.55.0/libp2p/swarm/enum.SwarmEvent.html).

For now, we only care about the `ConnectionEstablished`, `ConnectionClosed`, and `OutgoingConnectionError` events because they will tell us if our dial succeeded or failed and when a connection has been closed. In this lesson, you only have to dial the remote peer, so you don't need to handle incoming connections yet. If you successfully dial the remote peer, it will gracefully close the connection. You do not need to do anything other than what is shown below.

Add the following code to your event loop to handle connection events caused by dialing a remote peer:

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
            _ => {}
        }
    }
}
```

After making these changes to your peer, hit the `c` key to check your solution. If you did everything correctly, your peer will dial the remote peer and print connection events when it connects or disconnects.

## Testing Your Implementation

If you are using the workshop tool to take this workshop, you only have to hit the `c` key to check your solutionto see if it is correct. However if you would like to test your solution manually, you can follow these steps. The `PROJECT_ROOT` environment variable is the path to your Rust project. The `LESSON_PATH` for this lesson is most likely `.workshop/universal-conectivity-workshop/en/rs/02-tcp-transport`.

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
   docker compose up --build
   ```

4. Run the Python script to check your output:
   ```bash
   python check.py
   ```

## Success Criteria

Your implementation should:
- ✅ Display the startup message and local peer ID
- ✅ Successfully dial the remote peer
- ✅ Establish a connection and print connection messages

## Hints

## Hint - Complete Solution

Here's the complete working solution:

```rust
use anyhow::Result;
use futures::StreamExt;
use libp2p::identity;
use libp2p::{noise, tcp, yamux, Multiaddr, SwarmBuilder};
use libp2p::{ping, swarm::{NetworkBehaviour, SwarmEvent}};
use std::env;
use std::time::Duration;

#[derive(NetworkBehaviour)]
struct Behaviour {
    ping: ping::Behaviour,
}

#[tokio::main]
async fn main() -> Result<()> {
    println!("Starting Universal Connectivity Application...");

    // Parse the remote peer addresses from the environment variable
    let remote_peers = env::var("REMOTE_PEERS")?;
    let remote_addrs: Vec<Multiaddr> = remote_peers
        .split(',') // Split at ','
        .map(str::trim) // Trim whitespace
        .filter(|s| !s.is_empty()) // Filter out empty strings
        .map(Multiaddr::from_str) // Parse each string into Multiaddr
        .collect<Result<Multiaddr, _>>()?; // Collect into Result and unwrap it
     
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
        .with_behaviour(|_| Behaviour { ping: ping::Behaviour::default() })?
        .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
        .build();

    // Dial all of the remote peer Multiaddrs
    for addr in remote_addrs.into_iter() {
        swarm.dial(addr)?;
    }
    
    // Run the network event loop
    loop {
        match swarm.select_next_some().await {
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
