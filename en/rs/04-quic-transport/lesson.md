# Lesson 4: QUIC Transport

Now that you understand TCP transport, let's explore QUIC - a modern UDP-based transport protocol that provides built-in encryption and multiplexing. You'll learn about libp2p's multi-transport capabilities by running both TCP and QUIC simultaneously.

## Learning Objectives

By the end of this lesson, you will:
- Understand the advantages of QUIC over TCP
- Configure multi-transport libp2p nodes
- Handle connections over different transport protocols
- Connect to remote peers using QUIC multiaddresses

## Background: QUIC Transport

QUIC (Quick UDP Internet Connections) is a modern transport protocol that offers several advantages over TCP:

- **Built-in Security**: Encryption is integrated into the protocol (no separate TLS layer needed)
- **Reduced Latency**: Fewer round-trips for connection establishment
- **Better Multiplexing**: Streams don't block each other (no head-of-line blocking)
- **Connection Migration**: Connections can survive network changes
- **UDP-based**: Can traverse NATs more easily than TCP

## Transport Comparison

**TCP Stack:**
```
Application protocols (ping, gossipsub, etc.)
                    ↕
            Multiplexer (Yamux)
                    ↕
            Security (Noise)
                    ↕
              Transport (TCP)
                    ↕
                Network (IP)
```

**QUIC Stack:**
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

Extend your ping application to support both TCP and QUIC transports:

1. **Add QUIC Transport**: Configure QUIC alongside your existing TCP transport
2. **Multi-Transport Configuration**: Create a swarm that can handle both protocols
3. **Connect via QUIC**: Use a QUIC multiaddress to connect to the remote peer
4. **Handle Transport Events**: Display connection information for both transports

## Step-by-Step Instructions

### Step 1: Update Dependencies

Add QUIC support to your Cargo.toml features:

```toml
[dependencies]
libp2p = { version = "0.55", features = ["ed25519", "macros", "noise", "ping", "quic", "tcp", "tokio", "yamux"] }
```

Note the addition of the "quic" feature.

### Step 2: Add QUIC Import

Add the QUIC import to your existing imports:

```rust
use libp2p::{noise, tcp, quic, yamux, Multiaddr, SwarmBuilder};
```

### Step 3: Configure Multi-Transport Swarm

Replace your TCP-only transport configuration with a multi-transport setup:

```rust
let mut swarm = SwarmBuilder::with_existing_identity(local_key)
    .with_tokio()
    .with_quic()
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

### Step 4: Connect Using QUIC

The remote peer address will be a QUIC multiaddress (e.g., `/ip4/172.16.16.17/udp/9092/quic-v1`). Use the same dialing code:

```rust
let remote_peer = env::var("REMOTE_PEER")?;
let remote_addr: Multiaddr = remote_peer.parse()?;
println!("Dialing: {}", remote_addr);
swarm.dial(remote_addr)?;
```

### Step 5: Handle Connection Events

Your existing event handling code will work for both TCP and QUIC connections. The multiaddress in the connection events will show which transport was used.

## Testing Your Implementation

1. Set the environment variables:
   ```bash
   export PROJECT_ROOT=/path/to/workshop
   export LESSON_PATH=en/rs/04-quic-transport
   ```

2. Run with Docker Compose:
   ```bash
   docker compose up --build
   ```

3. Check your output:
   ```bash
   python check.py
   ```

## Success Criteria

Your implementation should:
- ✅ Display the startup message and local peer ID
- ✅ Successfully dial the remote peer using QUIC
- ✅ Establish a QUIC connection
- ✅ Send and receive ping messages over QUIC
- ✅ Display round-trip times in milliseconds

## Hints

## Hint - Transport Configuration Order

The order of transport configuration in the SwarmBuilder matters. QUIC should be configured before TCP:

```rust
.with_quic()
.with_tcp(
    tcp::Config::default(),
    noise::Config::new,
    yamux::Config::default,
)?
```

## Hint - QUIC Multiaddress Format

QUIC multiaddresses use UDP instead of TCP and include the QUIC version:
- TCP: `/ip4/127.0.0.1/tcp/9092`
- QUIC: `/ip4/127.0.0.1/udp/9092/quic-v1`

## Hint - Complete Solution

Here's the complete working solution:

```rust
use anyhow::Result;
use futures::StreamExt;
use libp2p::identity;
use libp2p::{noise, tcp, quic, yamux, Multiaddr, SwarmBuilder};
use libp2p::{
    ping,
    swarm::{NetworkBehaviour, SwarmEvent},
};
use std::env;
use std::time::Duration;

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
        .with_quic()
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

    println!("Dialing: {}", remote_addr);
    swarm.dial(remote_addr)?;

    loop {
        tokio::select! {
            Some(event) = swarm.next() => match event {
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
                SwarmEvent::Behaviour(behaviour_event) => match behaviour_event {
                    BehaviourEvent::Ping(ping_event) => {
                        match ping_event {
                            ping::Event {
                                peer,
                                result: Ok(ping::Success::Ping { rtt }),
                            } => {
                                println!("Received a ping from {}, round trip time: {} ms", peer, rtt.as_millis());
                            }
                            ping::Event {
                                peer,
                                result: Err(failure),
                            } => {
                                println!("Ping failed to {}: {:?}", peer, failure);
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
```

## What's Next?

Great work! You've successfully implemented multi-transport support with QUIC. You now understand:

- **QUIC Advantages**: Built-in security, reduced latency, better multiplexing
- **Multi-Transport Configuration**: Running multiple transports simultaneously
- **Transport Flexibility**: libp2p's ability to adapt to different network conditions
- **Modern Protocols**: How libp2p embraces cutting-edge networking technology

Key concepts you've learned:
- **QUIC Protocol**: Modern UDP-based transport with integrated security
- **Multi-Transport**: Supporting multiple protocols simultaneously
- **Transport Abstraction**: How libp2p handles different transports uniformly
- **Connection Flexibility**: Choosing the best transport for each connection

In the next lesson, you'll reach your second checkpoint by implementing the Identify protocol, which allows peers to exchange information about their capabilities and supported protocols!