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
use libp2p::{gossipsub, identify, noise, tcp, yamux, Multiaddr, SwarmBuilder, PeerId};
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

Configure gossipsub with message authentication and topics. The first step is to define the Gossipsub topics as constant values at the top of your file along with the other constants:

```rust
const IDENTIFY_PROTOCOL_NAME: &str = "/ipfs/id/1.0.0";
const AGENT_VERSION: &str = "universal-connectivity/0.1.0";
const GOSSIPSUB_TOPICS: &[&str] = &[
    "universal-connectivity",
    "universal-connectivity-file",
    "universal-connectivity-browser-peer-discovery"
];
```

The next step is to create a Gossipsub configuration with the correct heartbeat interval and validation mode. The heartbeat interval determines how often the Gossipsub protocol checks for new messages and propagates them, while the validation mode ensures that messages are properly authenticated and validated before being processed. The strict validation mode requires that each message is signed by the sender using the secret key that is associated with their peer id public key.

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
).map_err(|e| anyhow::anyhow!(e))?;

// Subscribe to the gossipsub topics
for topic_str in GOSSIPSUB_TOPICS {
    let topic = gossipsub::IdentTopic::new(topic_str);
    gossipsub.subscribe(&topic)?;
    println!("Subscribed to Gossipsub topic: {}", topic_str);
}
```

The last step is to add the gossipsub behavior to your NetworkBehaviour:

```rust
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
            identify::Config::new(IDENTIFY_PROTOCOL_NAME.to_string(), key.public())
                .with_agent_version(AGENT_VERSION.to_string())
        ),
        gossipsub,
    })?
    .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
    .build();
```

### Step 6: Handle Gossipsub Events

Add gossipsub event handling to your event loop:

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
                        gossipsub::Event::Message { message, .. } => {
                            if let Ok(msg) = UniversalConnectivityMessage::decode(&message.data[..]) {
                                println!("Received message on topic '{}': {} from {} (type: {:?})", 
                                    message.topic,
                                    msg.message,
                                    msg.from,
                                    msg.message_type);
                            } else {
                                println!("Received invalid message on topic '{}'", message.topic);
                            }
                        }
                        gossipsub::Event::Subscribed { peer_id, topic } => {
                            println!("Peer {peer_id} subscribed to '{topic}'");
                        }
                        gossipsub::Event::Unsubscribed { peer_id, topic } => {
                            println!("Peer {peer_id} unsubscribed from '{topic}'");
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

### Step 7: Send a Message on a Gossipsub Topic

Now that you've subscribed to the Gossipsub topics and set up the event handling, you can send messages on these topics. Let's do that by adding a function that constructs a `UniversalConnectivityMessage` that we can publish. We will then add code to publish this message after we have established a connection to the remote peer.

First, add a function to create a `UniversalConnectivityMessage`:

```rust
fn create_test_message(peer_id: &PeerId) -> Result<(gossipsub::IdentTopic, UniversalConnectivityMessage)> {
    // Send a test message on the universal-connectivity topic
    let topic = gossipsub::IdentTopic::new("universal-connectivity");
    let message = UniversalConnectivityMessage {
        from: peer_id.to_string(),
        message: "Hello from {peer_id}!".to_string(),
        timestamp: SystemTime::now()
            .duration_since(UNIX_EPOCH)?
            .as_secs() as i64,
        message_type: MessageType::Chat as i32,
    };
    Ok((topic, message))
}
```

Next, add code to send this message after establishing a connection to the remote peer:

```rust
loop {
    tokio::select! {
        Some(event) = swarm.next() => match event {
            SwarmEvent::ConnectionEstablished { peer_id, endpoint, .. } => {
                println!("Connected to: {peer_id} via {}", endpoint.get_remote_address());
                let (topic, msg) = create_test_message(local_peer_id);

                let mut buf = Vec::new();
                msg.encode(&mut buf)?;

                if let Err(e) = swarm.behaviour_mut().gossipsub.publish(topic, buf) {
                    println!("Failed to publish message: {:?}", e);
                } else {
                    println!("Published test message to 'universal-connectivity' topic");
                }
            }
            // ...
        }
    }
}
```

## Testing Your Implementation

1. Set the environment variables:
   ```bash
   export PROJECT_ROOT=/path/to/workshop
   export LESSON_PATH=en/rs/06-gossipsub-checkpoint
   ```

2. Change into the lesson directory:
    ```bash
    cd $PROJECT_ROOT/$LESSON_PATH
    ```

3. Run with Docker Compose:
   ```bash
   docker rm -f ucw-checker-06-gossipsub-checkpoint
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
).map_err(|e| anyhow::anyhow!(e))?;
```

## Hint - Topic Subscription

Subscribe to topics before adding the behavior to the swarm:

```rust
for topic in GOSSIPSUB_TOPICS {
    let topic = gossipsub::IdentTopic::new(topic);
    gossipsub.subscribe(&topic)?;
    println!("Subscribed to Gossipsub topic: {}", topic);
}
```

## Hint - Complete Solution

Here's the complete working solution:

```rust
use anyhow::Result;
use futures::StreamExt;
use libp2p::identity;
use libp2p::{gossipsub, identify, noise, tcp, yamux, Multiaddr, SwarmBuilder};
use libp2p::{
    ping,
    swarm::{NetworkBehaviour, SwarmEvent},
};
use prost::Message;
use std::env;
use std::hash::Hash;
use std::str::FromStr;
use std::time::Duration;

const IDENTIFY_PROTOCOL_VERSION: &str = "/ipfs/id/1.0.0";
const AGENT_VERSION: &str = "universal-connectivity/0.1.0";
const GOSSIPSUB_TOPICS: &[&str] = &[
    "universal-connectivity",
    "universal-connectivity-file",
    "universal-connectivity-browser-peer-discovery"
];

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

fn create_test_message(peer_id: &PeerId) -> Result<(gossipsub::IdentTopic, UniversalConnectivityMessage)> {
    // Send a test message on the universal-connectivity topic
    let topic = gossipsub::IdentTopic::new("universal-connectivity");
    let message = UniversalConnectivityMessage {
        from: peer_id.to_string(),
        message: "Hello from {peer_id}!".to_string(),
        timestamp: SystemTime::now()
            .duration_since(UNIX_EPOCH)?
            .as_secs() as i64,
        message_type: MessageType::Chat as i32,
    };
    Ok((topic, message))
}

#[tokio::main]
async fn main() -> Result<()> {
    println!("Starting Universal Connectivity Application...");

    let remote_peers = env::var("REMOTE_PEERS")?;
    let remote_addrs: Vec<Multiaddr> = remote_peers
        .split(',') // Split at ','
        .map(str::trim) // Trim whitespace
        .filter(|s| !s.is_empty()) // Filter out empty strings
        .map(Multiaddr::from_str) // Parse each string into Multiaddr
        .collect<Result<Multiaddr, _>>()?; // Collect into Result and unwrap it

    let local_key = identity::Keypair::generate_ed25519();
    let local_peer_id = identity::PeerId::from(local_key.public());
    println!("Local peer id: {local_peer_id}");

    // Create a Gossipsub configuration
    let gossipsub_config = gossipsub::ConfigBuilder::default()
        .heartbeat_interval(Duration::from_secs(10))
        .validation_mode(gossipsub::ValidationMode::Strict)
        .build()?;

    // Create a gossipsub instance
    let mut gossipsub = gossipsub::Behaviour::new(
        gossipsub::MessageAuthenticity::Signed(local_key.clone()),
        gossipsub_config,
    ).map_err(|e| anyhow::anyhow!(e))?;

    // Subscribe to topics
    let topics = vec![
        "universal-connectivity",
        "universal-connectivity-file",
        "universal-connectivity-browser-peer-discovery"
    ];

    for topic in GOSSIPSUB_TOPICS {
        let topic = gossipsub::IdentTopic::new(*topic);
        gossipsub.subscribe(&topic)?;
        println!("Subscribed to topic: {topic}");
    }

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
                identify::Config::new("/ipfs/id/1.0.0".to_string(), key.public())
                    .with_agent_version("universal-connectivity/0.1.0".to_string())
            ),
            gossipsub,
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
                SwarmEvent::ConnectionEstablished { peer_id, connection_id, endpoint, .. } => {
                    println!("Connected to: {peer_id} via {}", endpoint.get_remote_address());
                    let (topic, msg) = create_test_message(local_peer_id)?;

                    let mut buf = Vec::new();
                    msg.encode(&mut buf)?;

                    if let Err(e) = swarm.behaviour_mut().gossipsub.publish(topic.clone(), buf) {
                        println!("Failed to publish message: {:?}", e);
                    } else {
                        println!("Published test message to '{topic}' topic");
                    }
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
                            gossipsub::Event::Message { message, .. } => {
                                if let Ok(msg) = UniversalConnectivityMessage::decode(&message.data[..]) {
                                    println!("Received message on topic '{}': {} from {} (type: {:?})", 
                                        message.topic,
                                        msg.message,
                                        msg.from,
                                        msg.message_type);
                                } else {
                                    println!("Received invalid message on topic '{topic}');
                                }
                            }
                            gossipsub::Event::Subscribed { peer_id, topic } => {
                                println!("Peer {peer_id} subscribed to '{topic}'");
                            }
                            gossipsub::Event::Unsubscribed { peer_id, topic } => {
                                println!("Peer {peer_id} unsubscribed from '{topic}'");
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
