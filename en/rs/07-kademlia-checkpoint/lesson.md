# Lesson 7: Kademlia Checkpoint 🏆

Welcome to your fourth checkpoint! In this lesson, you'll implement Kademlia, a distributed hash table (DHT) protocol that enables decentralized peer discovery and content routing in libp2p networks.

## Learning Objectives

By the end of this lesson, you will:
- Understand distributed hash tables and the Kademlia protocol
- Implement Kademlia DHT for peer discovery
- Handle bootstrap processes and peer routing
- Work with bootstrap nodes and network initialization

## Background: Kademlia DHT

Kademlia is a distributed hash table protocol that provides:

- **Decentralized Peer Discovery**: Find peers without central servers
- **Content Routing**: Locate data distributed across the network
- **Self-Organizing**: Networks automatically adapt to peer joins/leaves
- **Scalability**: Efficient routing with logarithmic lookup complexity

It's used by IPFS, BitTorrent, and many other P2P systems for peer and content discovery.

## Your Task

Building on your gossipsub implementation from Lesson 6, you need to:

1. **Add Kademlia Behavior**: Include `kad::Behaviour` in your `NetworkBehaviour` struct
2. **Configure Bootstrap Nodes**: Set up initial peers for network entry
3. **Handle Bootstrap Process**: Initiate and monitor DHT bootstrap
4. **Process Kademlia Events**: Handle peer discovery and routing events

## Step-by-Step Instructions

### Step 1: Update Dependencies

Add kademlia support to your Cargo.toml features:

```toml
[dependencies]
libp2p = { version = "0.55", features = ["ed25519", "gossipsub", "identify", "kad", "macros", "noise", "ping", "quic", "tcp", "tokio", "yamux"] }
```

Note the addition of the "kad" feature.

### Step 2: Add Kademlia Import

Add the kademlia import to your existing imports:

```rust
use libp2p::{gossipsub, identify, kad, noise, tcp, quic, yamux, Multiaddr, SwarmBuilder, PeerId};
```

### Step 3: Update Your NetworkBehaviour

Add kademlia to your behavior struct:

```rust
#[derive(NetworkBehaviour)]
struct Behaviour {
    ping: ping::Behaviour,
    identify: identify::Behaviour,
    gossipsub: gossipsub::Behaviour,
    kademlia: kad::Behaviour<kad::store::MemoryStore>,
}
```

### Step 4: Configure Kademlia

Create and configure the Kademlia behavior:

```rust
// Create Kademlia configuration
let mut kad_config = kad::Config::new(local_peer_id);
kad_config.set_query_timeout(Duration::from_secs(60));
kad_config.set_bootstrap_interval(Some(Duration::from_secs(300)));

// Create Kademlia behavior with memory store
let store = kad::store::MemoryStore::new(local_peer_id);
let mut kademlia = kad::Behaviour::with_config(local_peer_id, store, kad_config);

// Set protocol name
kademlia.set_mode(Some(kad::Mode::Server));
```

### Step 5: Handle Bootstrap Nodes

Parse and add bootstrap nodes from environment variable:

```rust
// Parse bootstrap peers from environment variable
if let Ok(bootstrap_peers) = env::var("BOOTSTRAP_PEERS") {
    for addr_str in bootstrap_peers.split(',') {
        if let Ok(addr) = addr_str.trim().parse::<Multiaddr>() {
            if let Some(peer_id) = addr.iter().find_map(|p| match p {
                libp2p::multiaddr::Protocol::P2p(hash) => Some(PeerId::from_multihash(hash).ok()?),
                _ => None,
            }) {
                kademlia.add_address(&peer_id, addr.clone());
                println!("Added bootstrap peer: {} at {}", peer_id, addr);
            }
        }
    }
    
    // Start bootstrap process
    if let Err(e) = kademlia.bootstrap() {
        println!("Failed to start bootstrap: {:?}", e);
    } else {
        println!("Started Kademlia bootstrap process");
    }
}
```

### Step 6: Handle Kademlia Events

Add kademlia event handling to your event loop:

```rust
BehaviourEvent::Kademlia(kad_event) => {
    match kad_event {
        kad::Event::OutboundQueryProgressed { result, .. } => {
            match result {
                kad::QueryResult::Bootstrap(Ok(kad::BootstrapOk {
                    peer,
                    num_remaining,
                })) => {
                    println!("Bootstrap progress: contacted {}, {} remaining", peer, num_remaining);
                    if num_remaining == 0 {
                        println!("Kademlia bootstrap completed successfully");
                    }
                }
                kad::QueryResult::Bootstrap(Err(kad::BootstrapError::Timeout)) => {
                    println!("Kademlia bootstrap timed out");
                }
                kad::QueryResult::GetClosestPeers(Ok(kad::GetClosestPeersOk { key: _, peers })) => {
                    println!("Found {} closest peers", peers.len());
                    for peer in peers {
                        println!("Closest peer: {}", peer);
                    }
                }
                kad::QueryResult::GetClosestPeers(Err(kad::GetClosestPeersError::Timeout { key: _, peers })) => {
                    println!("Get closest peers timed out, found {} peers", peers.len());
                }
                _ => {}
            }
        }
        kad::Event::RoutingUpdated { peer, is_new_peer, addresses, bucket_range: _, old_peer } => {
            if is_new_peer {
                println!("New peer added to routing table: {} with {} addresses", peer, addresses.len());
            }
            if let Some(old) = old_peer {
                println!("Peer {} replaced {} in routing table", peer, old);
            }
        }
        kad::Event::UnroutablePeer { peer } => {
            println!("Peer {} is unroutable", peer);
        }
        kad::Event::RoutablePeer { peer, address } => {
            println!("Peer {} is routable at {}", peer, address);
        }
        _ => {}
    }
}
```

## Testing Your Implementation

1. Set the environment variables:
   ```bash
   export PROJECT_ROOT=/path/to/workshop
   export LESSON_PATH=en/rs/07-kademlia-checkpoint
   export BOOTSTRAP_PEERS="/ip4/172.16.16.17/tcp/9092/p2p/12D3KooWExample"
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
- ✅ Subscribe to gossipsub topics
- ✅ Add bootstrap peers to Kademlia
- ✅ Start the bootstrap process
- ✅ Handle Kademlia routing events

## Hints

## Hint - Bootstrap Node Format

Bootstrap nodes need to include peer IDs in the multiaddr:
```
/ip4/172.16.16.17/tcp/9092/p2p/12D3KooWExample
```

## Hint - Kademlia Memory Store

Use the memory store for this lesson:
```rust
let store = kad::store::MemoryStore::new(local_peer_id);
let kademlia = kad::Behaviour::with_config(local_peer_id, store, kad_config);
```

## Hint - Complete Solution

Here's the complete working solution:

```rust
use anyhow::Result;
use futures::StreamExt;
use libp2p::identity;
use libp2p::{gossipsub, identify, kad, noise, tcp, quic, yamux, Multiaddr, SwarmBuilder, PeerId};
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
    kademlia: kad::Behaviour<kad::store::MemoryStore>,
}

#[tokio::main]
async fn main() -> Result<()> {
    println!("Starting Universal Connectivity Application...");

    let remote_peer = env::var("REMOTE_PEER")?;
    let remote_addr: Multiaddr = remote_peer.parse()?;

    let local_key = identity::Keypair::generate_ed25519();
    let local_peer_id = identity::PeerId::from(local_key.public());
    println!("Local peer id: {local_peer_id}");

    // Create Kademlia configuration
    let mut kad_config = kad::Config::new(local_peer_id);
    kad_config.set_query_timeout(Duration::from_secs(60));
    kad_config.set_bootstrap_interval(Some(Duration::from_secs(300)));

    // Create Kademlia behavior with memory store
    let store = kad::store::MemoryStore::new(local_peer_id);
    let mut kademlia = kad::Behaviour::with_config(local_peer_id, store, kad_config);
    kademlia.set_mode(Some(kad::Mode::Server));

    // Parse bootstrap peers from environment variable
    if let Ok(bootstrap_peers) = env::var("BOOTSTRAP_PEERS") {
        for addr_str in bootstrap_peers.split(',') {
            if let Ok(addr) = addr_str.trim().parse::<Multiaddr>() {
                if let Some(peer_id) = addr.iter().find_map(|p| match p {
                    libp2p::multiaddr::Protocol::P2p(hash) => PeerId::from_multihash(hash).ok(),
                    _ => None,
                }) {
                    kademlia.add_address(&peer_id, addr.clone());
                    println!("Added bootstrap peer: {} at {}", peer_id, addr);
                }
            }
        }
        
        // Start bootstrap process
        if let Err(e) = kademlia.bootstrap() {
            println!("Failed to start bootstrap: {:?}", e);
        } else {
            println!("Started Kademlia bootstrap process");
        }
    }

    // Create Gossipsub configuration
    let gossipsub_config = gossipsub::ConfigBuilder::default()
        .heartbeat_interval(Duration::from_secs(10))
        .validation_mode(gossipsub::ValidationMode::Strict)
        .build()
        .expect("Valid config");

    // Create gossipsub instance
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
            kademlia,
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
                    BehaviourEvent::Kademlia(kad_event) => {
                        match kad_event {
                            kad::Event::OutboundQueryProgressed { result, .. } => {
                                match result {
                                    kad::QueryResult::Bootstrap(Ok(kad::BootstrapOk {
                                        peer,
                                        num_remaining,
                                    })) => {
                                        println!("Bootstrap progress: contacted {}, {} remaining", peer, num_remaining);
                                        if num_remaining == 0 {
                                            println!("Kademlia bootstrap completed successfully");
                                        }
                                    }
                                    kad::QueryResult::Bootstrap(Err(kad::BootstrapError::Timeout)) => {
                                        println!("Kademlia bootstrap timed out");
                                    }
                                    kad::QueryResult::GetClosestPeers(Ok(kad::GetClosestPeersOk { key: _, peers })) => {
                                        println!("Found {} closest peers", peers.len());
                                        for peer in peers {
                                            println!("Closest peer: {}", peer);
                                        }
                                    }
                                    kad::QueryResult::GetClosestPeers(Err(kad::GetClosestPeersError::Timeout { key: _, peers })) => {
                                        println!("Get closest peers timed out, found {} peers", peers.len());
                                    }
                                    _ => {}
                                }
                            }
                            kad::Event::RoutingUpdated { peer, is_new_peer, addresses, bucket_range: _, old_peer } => {
                                if is_new_peer {
                                    println!("New peer added to routing table: {} with {} addresses", peer, addresses.len());
                                }
                                if let Some(old) = old_peer {
                                    println!("Peer {} replaced {} in routing table", peer, old);
                                }
                            }
                            kad::Event::UnroutablePeer { peer } => {
                                println!("Peer {} is unroutable", peer);
                            }
                            kad::Event::RoutablePeer { peer, address } => {
                                println!("Peer {} is routable at {}", peer, address);
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

Congratulations! You've reached your fourth checkpoint 🎉

You now have a fully-featured libp2p node that can:
- Connect over multiple transports
- Exchange peer identification
- Participate in gossipsub messaging
- Discover peers through Kademlia DHT

Key concepts you've learned:
- **Distributed Hash Tables**: Decentralized data and peer storage
- **Bootstrap Process**: Joining existing P2P networks  
- **Peer Discovery**: Finding other nodes without central coordination
- **Routing Tables**: Efficient peer organization and lookup

In the final lesson, you'll complete the Universal Connectivity application by implementing chat messaging and connecting to the real network!