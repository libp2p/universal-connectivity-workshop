# Lesson 6: Gossipsub Checkpoint 🏆

Welcome to your third checkpoint! In this lesson, you'll implement Gossipsub, libp2p's publish-subscribe protocol that enables topic-based messaging across peer-to-peer networks. You'll also work with protobuf serialization for structured message formats.

## Learning Objectives

By the end of this lesson, you will:
- Understand publish-subscribe messaging patterns
- Implement Gossipsub for topic-based communication
- Work with protobuf serialization for structured messages
- Subscribe to and publish messages on specific topics

## Background: Gossipsub Protocol

Gossipsub is libp2p's scalable publish-subscribe protocol that enables:

- **Topic-Based Messaging**: Peers can subscribe to specific topics of interest
- **Efficient Distribution**: Messages are efficiently routed through the network
- **Scalability**: Works well with large numbers of peers and topics
- **Fault Tolerance**: Resilient to peer failures and network partitions

It's used by major blockchain networks like Ethereum 2.0 for consensus communication.

## Your Task

Building on your identify implementation from Lesson 5, you need to:

1. **Add Gossipsub Behavior**: Include `gossipsub::Behaviour` in your `NetworkBehaviour` struct
2. **Configure Topics**: Subscribe to Universal Connectivity topics
3. **Implement Protobuf Messages**: Define and serialize `UniversalConnectivityMessage`
4. **Handle Gossipsub Events**: Process incoming messages and subscription events

## Step-by-Step Instructions

### Step 1: Update Dependencies

Add gossipsub and protobuf support to your Cargo.toml:

```toml
[dependencies]
libp2p = { version = "0.55", features = ["ed25519", "gossipsub", "identify", "macros", "noise", "ping", "quic", "tcp", "tokio", "yamux"] }
prost = "0.13"
prost-types = "0.13"
```

### Step 2: Add Imports

Add the necessary imports:

```rust
use libp2p::{gossipsub, identify, noise, tcp, quic, yamux, Multiaddr, SwarmBuilder, PeerId};
use prost::Message;
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
```

### Step 3: Define the UniversalConnectivityMessage

Create the protobuf message structure:

```rust
#[derive(Clone, PartialEq, prost::Message)]
pub struct UniversalConnectivityMessage {
    #[prost(string, tag = "1")]
    pub from: String,
    #[prost(string, tag = "2")]
    pub message: String,
    #[prost(int64, tag = "3")]
    pub timestamp: i64,
    #[prost(enumeration = "MessageType", tag = "4")]
    pub message_type: i32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, PartialOrd, Ord, prost::Enumeration)]
#[repr(i32)]
pub enum MessageType {
    Chat = 0,
    File = 1,
    BrowserPeerDiscovery = 2,
}
```

### Step 4: Update Your NetworkBehaviour

Add gossipsub to your behavior struct:

```rust
#[derive(NetworkBehaviour)]
struct Behaviour {
    ping: ping::Behaviour,
    identify: identify::Behaviour,
    gossipsub: gossipsub::Behaviour,
}
```

### Step 5: Configure Gossipsub

Configure gossipsub with message authentication and topics:

```rust
// Create a Gossipsub configuration
let gossipsub_config = gossipsub::ConfigBuilder::default()
    .heartbeat_interval(Duration::from_secs(10))
    .validation_mode(gossipsub::ValidationMode::Strict)
    .build()
    .expect("Valid config");

// Create a gossipsub instance
let mut gossipsub = gossipsub::Behaviour::new(
    gossipsub::MessageAuthenticity::Signed(local_key.clone()),
    gossipsub_config,
).expect("Correct configuration");

// Subscribe to topics
let topics = vec![
    "universal-connectivity",
    "universal-connectivity-file",
    "universal-connectivity-browser-peer-discovery"
];

for topic_str in topics {
    let topic = gossipsub::IdentTopic::new(topic_str);
    gossipsub.subscribe(&topic)?;
    println!("Subscribed to topic: {}", topic_str);
}
```

### Step 6: Handle Gossipsub Events

Add gossipsub event handling to your event loop:

```rust
BehaviourEvent::Gossipsub(gossipsub_event) => {
    match gossipsub_event {
        gossipsub::Event::Message {
            propagation_source: _,
            message_id: _,
            message,
        } => {
            let topic = message.topic.clone();
            if let Ok(uc_message) = UniversalConnectivityMessage::decode(&message.data[..]) {
                println!("Received message on topic '{}': {} from {} (type: {:?})", 
                    topic, uc_message.message, uc_message.from, uc_message.message_type);
            } else {
                println!("Received non-UC message on topic '{}': {} bytes", 
                    topic, message.data.len());
            }
        }
        gossipsub::Event::Subscribed { peer_id, topic } => {
            println!("Peer {} subscribed to topic: {}", peer_id, topic);
        }
        gossipsub::Event::Unsubscribed { peer_id, topic } => {
            println!("Peer {} unsubscribed from topic: {}", peer_id, topic);
        }
        _ => {}
    }
}
```

## Testing Your Implementation

1. Set the environment variables:
   ```bash
   export PROJECT_ROOT=/path/to/workshop
   export LESSON_PATH=en/rs/06-gossipsub-checkpoint
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
- ✅ Successfully dial the remote peer
- ✅ Subscribe to Universal Connectivity topics
- ✅ Receive and decode gossipsub messages
- ✅ Handle peer subscription events

## Hints

## Hint - Message Authentication

Gossipsub requires message authentication. Use the same keypair for both the swarm and gossipsub:

```rust
let mut gossipsub = gossipsub::Behaviour::new(
    gossipsub::MessageAuthenticity::Signed(local_key.clone()),
    gossipsub_config,
).expect("Correct configuration");
```

## Hint - Topic Subscription

Subscribe to topics before adding the behavior to the swarm:

```rust
let topic = gossipsub::IdentTopic::new("universal-connectivity");
gossipsub.subscribe(&topic)?;
```

## Hint - Complete Solution

Here's the complete working solution:

```rust
use anyhow::Result;
use futures::StreamExt;
use libp2p::identity;
use libp2p::{gossipsub, identify, noise, tcp, quic, yamux, Multiaddr, SwarmBuilder, PeerId};
use libp2p::{
    ping,
    swarm::{NetworkBehaviour, SwarmEvent},
};
use prost::Message;
use std::env;
use std::time::Duration;

#[derive(Clone, PartialEq, prost::Message)]
pub struct UniversalConnectivityMessage {
    #[prost(string, tag = "1")]
    pub from: String,
    #[prost(string, tag = "2")]
    pub message: String,
    #[prost(int64, tag = "3")]
    pub timestamp: i64,
    #[prost(enumeration = "MessageType", tag = "4")]
    pub message_type: i32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, PartialOrd, Ord, prost::Enumeration)]
#[repr(i32)]
pub enum MessageType {
    Chat = 0,
    File = 1,
    BrowserPeerDiscovery = 2,
}

#[derive(NetworkBehaviour)]
struct Behaviour {
    ping: ping::Behaviour,
    identify: identify::Behaviour,
    gossipsub: gossipsub::Behaviour,
}

#[tokio::main]
async fn main() -> Result<()> {
    println!("Starting Universal Connectivity Application...");

    let remote_peer = env::var("REMOTE_PEER")?;
    let remote_addr: Multiaddr = remote_peer.parse()?;

    let local_key = identity::Keypair::generate_ed25519();
    let local_peer_id = identity::PeerId::from(local_key.public());
    println!("Local peer id: {local_peer_id}");

    // Create a Gossipsub configuration
    let gossipsub_config = gossipsub::ConfigBuilder::default()
        .heartbeat_interval(Duration::from_secs(10))
        .validation_mode(gossipsub::ValidationMode::Strict)
        .build()
        .expect("Valid config");

    // Create a gossipsub instance
    let mut gossipsub = gossipsub::Behaviour::new(
        gossipsub::MessageAuthenticity::Signed(local_key.clone()),
        gossipsub_config,
    ).expect("Correct configuration");

    // Subscribe to topics
    let topics = vec![
        "universal-connectivity",
        "universal-connectivity-file",
        "universal-connectivity-browser-peer-discovery"
    ];

    for topic_str in topics {
        let topic = gossipsub::IdentTopic::new(topic_str);
        gossipsub.subscribe(&topic)?;
        println!("Subscribed to topic: {}", topic_str);
    }

    let mut swarm = SwarmBuilder::with_existing_identity(local_key)
        .with_tokio()
        .with_quic()
        .with_tcp(
            tcp::Config::default(),
            noise::Config::new,
            yamux::Config::default,
        )?
        .with_behaviour(|key| Behaviour {
            ping: ping::Behaviour::new(
                ping::Config::new()
                    .with_interval(Duration::from_secs(1))
                    .with_timeout(Duration::from_secs(5))
            ),
            identify: identify::Behaviour::new(
                identify::Config::new("/ipfs/id/1.0.0".to_string(), key.public())
                    .with_agent_version("universal-connectivity/0.1.0".to_string())
            ),
            gossipsub,
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
                    BehaviourEvent::Identify(identify_event) => {
                        match identify_event {
                            identify::Event::Received { peer_id, info } => {
                                println!("Identified peer: {} with protocol version: {}", peer_id, info.protocol_version);
                                println!("Peer agent: {}", info.agent_version);
                                println!("Peer supports {} protocols", info.protocols.len());
                            }
                            identify::Event::Sent { peer_id } => {
                                println!("Sent identify info to: {}", peer_id);
                            }
                            identify::Event::Error { peer_id, error } => {
                                println!("Identify error with {}: {:?}", peer_id, error);
                            }
                            _ => {}
                        }
                    }
                    BehaviourEvent::Gossipsub(gossipsub_event) => {
                        match gossipsub_event {
                            gossipsub::Event::Message {
                                propagation_source: _,
                                message_id: _,
                                message,
                            } => {
                                let topic = message.topic.clone();
                                if let Ok(uc_message) = UniversalConnectivityMessage::decode(&message.data[..]) {
                                    println!("Received message on topic '{}': {} from {} (type: {:?})", 
                                        topic, uc_message.message, uc_message.from, uc_message.message_type);
                                } else {
                                    println!("Received non-UC message on topic '{}': {} bytes", 
                                        topic, message.data.len());
                                }
                            }
                            gossipsub::Event::Subscribed { peer_id, topic } => {
                                println!("Peer {} subscribed to topic: {}", peer_id, topic);
                            }
                            gossipsub::Event::Unsubscribed { peer_id, topic } => {
                                println!("Peer {} unsubscribed from topic: {}", peer_id, topic);
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

Congratulations! You've reached your third checkpoint 🎉

You now have a libp2p node that can:
- Communicate over multiple transports
- Exchange peer identification
- Participate in publish-subscribe messaging
- Handle structured protobuf messages

Key concepts you've learned:
- **Publish-Subscribe**: Topic-based messaging patterns
- **Gossipsub Protocol**: Efficient message distribution in P2P networks  
- **Protobuf Serialization**: Structured message formats
- **Topic Management**: Subscribing to and handling topic events

In the next lesson, you'll implement Kademlia DHT for distributed peer discovery and routing!