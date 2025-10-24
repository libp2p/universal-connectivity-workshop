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
2. **Handle Bootstrap Process**: Initiate and monitor DHT bootstrap
3. **Process Kademlia Events**: Handle peer discovery and routing events

## Step-by-Step Instructions

### Step 1: Update Dependencies

Add the `kademlia` feature to your Cargo.toml features:

```toml
[dependencies]
libp2p = { version = "0.56", features = ["ed25519", "gossipsub", "identify", "kad", "macros", "noise", "ping", "quic", "tcp", "tokio", "yamux"] }
```

Note the addition of the "kad" feature.

### Step 2: Add Kademlia Import

Add the kademlia import to your existing imports:

```rust
use anyhow::Result;
use futures::StreamExt;
use libp2p::{
    gossipsub, identify, identity, kad, 
    multiaddr::Protocol,
    noise, ping, 
    swarm::{NetworkBehaviour, SwarmEvent},
    tcp, yamux, Multiaddr, PeerId, StreamProtocol, SwarmBuilder,
};
use prost::Message;
use std::{
    collections::hash_map::DefaultHasher,
    env,
    hash::{Hash, Hasher},
    str::FromStr,
    time::{Duration, SystemTime, UNIX_EPOCH},
};
```

### Step 3: Add Kademlia Protocol Name

Add the constant for the kademlia protocol name:

```rust
const KADEMLIA_PROTOCOL_NAME: StreamProtocol = StreamProtocol::new("/ipfs/kad/1.0.0");
const KADEMLIA_QUERY_TIMEOUT: u64 = 60;
const KADEMLIA_BOOTSTRAP_INTERVAL: u64 = 300;
```

### Step 4: Update Your NetworkBehaviour

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

### Step 5: Parse the Bootstrap Peer Addresses

In this lesson, the Multiaddr's for the bootstrap peers are passed in the environment variable named 'BOOSTRAP_PEERS'. You must add code, similar to the code for parsing the 'REMOTE_PEERS' environment variable, to parse the bootstrap peers.

```rust
// parse the bootstrap peer addresses from the environment variable
let mut bootstrap_addrs: Vec<Multiaddr> = Vec::default();
if let Ok(bootstrap_peers) = env::var("BOOTSTRAP_PEERS") {
    bootstrap_addrs = bootstrap_peers
        .split(',')                         // Split the string at ','
        .map(str::trim)                     // Trim whitespace of each string
        .filter(|s| !s.is_empty())          // Filter out empty strings
        .map(Multiaddr::from_str)           // Parse each string into Multiaddr
        .collect::<Result<Vec<_>, _>>()?;   // Collect into Result and unwrap it
}
```

These bootstrap peers are used to initialize the Kademlia DHT and help your node find other peers in the network.

### Step 6: Configure Kademlia

Create and configure the Kademlia behavior.

```rust

// ... existing code to configure gossipsub ...

// Create Kademlia configuration
let mut kad_config = kad::Config::new(KADEMLIA_PROTOCOL_NAME.to_string());
kad_config.set_query_timeout(Duration::from_secs(KADEMLIA_QUERY_TIMEOUT));
kad_config.set_bootstrap_interval(Some(Duration::from_secs(KADEMLIA_BOOTSTRAP_INTERVAL)));

// Create Kademlia behavior with memory store
let store = kad::store::MemoryStore::new(local_peer_id);
let kademlia = kad::Behaviour::with_config(local_peer_id, store, kad_config);
```

Now that the kademlia behaviour is created, we must add the bootstrapper peers. We use the bootstrap Multiaddr's we parsed earlier but we must split off the PeerId's from the Multiaddr's using a new function called `split_address`. Add this to your file near the function for creating gossipsub messages that you added in lesson 6:

```rust
fn split_address(addr: Multiaddr) -> Option<(PeerId, Multiaddr)> {
    let mut base_addr = Multiaddr::empty();
    let mut peer_id = None;

    for protocol in addr.into_iter() {
        match protocol {
            Multiaddr::P2p(id) => {
                peer_id = Some(id);
                break;
            }
            _ => {
                base_addr.push(protocol);
            }
        }
    }

    peer_id.map(|id| (id, base_addr))
}
```

And add the kademlia behaviour into the SwarmBuilder code in your peer:

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
            identify::Config::new(IDENTIFY_PROTOCOL_VERSION.to_string(), key.public())
                .with_agent_version(AGENT_VERSION.to_string())
        ),
        gossipsub,
        kademlia,
    })?
    .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
    .build();
```

### Step 7: Initiate Bootstrapping

Since you are joining a Kademlia network using one or more bootstrap peers, you no longer need to dial any peers directly. You may remove the code for dialing remote peers and instead add code to trigger the kademlia bootstrap process:

```rust
// ~~~ snip ~~~
// Dial all of the remote peer Multiaddrs
for addr in remote_addrs.into_iter() {
    swarm.dial(addr)?;
}
// ~~~ snip ~~~

// Start the Kademlia bootstrap process
if !bootstrap_addrs.is_empty() {
    // Add the bootstrap peer addresses to the kademlia behaviour
    for addr in bootstrap_addrs.into_iter() {
        if let Some((peer_id, peer_addr)) = split_address(addr) {
            println!("Adding bootstrap peer: {peer_id} with multiaddr: {peer_addr}");
            swarm.behaviour_mut().kademlia.add_address(&peer_id, peer_addr);
        }
    }

    // Start the Kademlia bootstrap process
    swarm.behaviour_mut().kademlia.bootstrap()?;
}

```

### Step 8: Handle Kademlia Events

Add kademlia event handling to your event loop:

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

                            // now that the remote peer is subscribed, publish a message
                            if topic == gossipsub::IdentTopic::new("universal-connectivity").into() {
                                let (topic, msg) = create_test_message(&local_peer_id)?;

                                let mut buf = Vec::new();
                                msg.encode(&mut buf)?;

                                if let Err(e) = swarm.behaviour_mut().gossipsub.publish(topic.clone(), buf) {
                                    println!("Failed to publish message: {:?}", e);
                                } else {
                                    println!("Published test message to '{topic}' topic");
                                }
                            }
                        }
                        gossipsub::Event::Unsubscribed { peer_id, topic } => {
                            println!("Peer {peer_id} unsubscribed from '{topic}'");
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
                                    println!("Bootstrap progress: contacted {peer}, {num_remaining} remaining");
                                    if num_remaining == 0 {
                                        println!("Kademlia bootstrap completed successfully");
                                    }
                                }
                                kad::QueryResult::Bootstrap(Err(kad::BootstrapError::Timeout { .. })) => {
                                    println!("Kademlia bootstrap timed out");
                                }
                                kad::QueryResult::GetClosestPeers(Ok(kad::GetClosestPeersOk { key: _, peers })) => {
                                    println!("Found {} closest peers", peers.len());
                                    for peer in peers {
                                        println!("Closest peer: {peer:?}");
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
                                println!("New peer added to routing table: {peer} with {} addresses", addresses.len());
                            }
                            if let Some(old) = old_peer {
                                println!("Peer {peer} replaced {old} in routing table");
                            }
                        }
                        kad::Event::UnroutablePeer { peer } => {
                            println!("Peer {peer} is unroutable");
                        }
                        kad::Event::RoutablePeer { peer, address } => {
                            println!("Peer {peer} is routable at {address}");
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
   export LESSON_PATH=en/rs/07-kademlia-checkpoint
   ```

2. Change into the lesson directory:
    ```bash
    cd $PROJECT_ROOT/$LESSON_PATH
    ```

3. Run with Docker Compose:
   ```bash
   docker rm -f workshop-lesson ucw-checker-en ucw-checker-en-01 ucw-checker-en-02
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
- ✅ Subscribe to gossipsub topics
- ✅ Add bootstrap peers to Kademlia
- ✅ Start the bootstrap process
- ✅ Handle Kademlia routing events

## Hints

## Hint - Bootstrap Node Format

Bootstrap nodes need to include peer IDs in the multiaddr:
```
```
## Hint - Kademlia Bootstrapper Multiaddr Format

QUIC multiaddresses use UDP instead of TCP and include the QUIC protocol after the port number.
- TCP: `/ip4/127.0.0.1/tcp/9092`
- QUIC: `/ip4/127.0.0.1/udp/9092/quic-v1`
- Kademlia Bootstrapper: `/ip4/172.16.16.17/udp/9091/quic-v1/p2p/12D3KooWDj4uNjMpUtESkyJa2ZB6DtXg5PKC4pTUptJixE7zo9gB`

## Hint - Complete Solution

Here's the complete working solution:

```rust
use anyhow::Result;
use futures::StreamExt;
use libp2p::{
    gossipsub, identify, identity, kad, 
    multiaddr::Protocol,
    noise, ping, 
    swarm::{NetworkBehaviour, SwarmEvent},
    tcp, yamux, Multiaddr, PeerId, StreamProtocol, SwarmBuilder,
};
use prost::Message;
use std::{
    collections::hash_map::DefaultHasher,
    env,
    hash::{Hash, Hasher},
    str::FromStr,
    time::{Duration, SystemTime, UNIX_EPOCH},
};

const IDENTIFY_PROTOCOL_VERSION: &str = "/ipfs/id/1.0.0";
const AGENT_VERSION: &str = "universal-connectivity/0.1.0";
const GOSSIPSUB_TOPICS: &[&str] = &[
    "universal-connectivity",
    "universal-connectivity-file",
    "universal-connectivity-browser-peer-discovery"
];
const KADEMLIA_PROTOCOL_NAME: StreamProtocol = StreamProtocol::new("/ipfs/kad/1.0.0");
const KADEMLIA_QUERY_TIMEOUT: u64 = 60;
const KADEMLIA_BOOTSTRAP_INTERVAL: u64 = 300;

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

fn message_id(msg: &gossipsub::Message) -> gossipsub::MessageId {
    let mut s = DefaultHasher::new();
    msg.data.hash(&mut s);
    gossipsub::MessageId::from(s.finish().to_string())
}

fn create_test_message(peer_id: &PeerId) -> Result<(gossipsub::IdentTopic, UniversalConnectivityMessage)> {
    // Send a test message on the universal-connectivity topic
    let topic = gossipsub::IdentTopic::new("universal-connectivity");
    let message = UniversalConnectivityMessage {
        from: peer_id.to_string(),
        message: format!("Hello from {peer_id}!"),
        timestamp: SystemTime::now()
            .duration_since(UNIX_EPOCH)?
            .as_secs() as i64,
        message_type: MessageType::Chat as i32,
    };
    Ok((topic, message))
}

fn split_address(addr: Multiaddr) -> Option<(PeerId, Multiaddr)> {
    let mut base_addr = Multiaddr::empty();
    let mut peer_id = None;

    for protocol in addr.into_iter() {
        match protocol {
            Protocol::P2p(id) => {
                peer_id = Some(id);
                break;
            }
            _ => {
                base_addr.push(protocol);
            }
        }
    }

    peer_id.map(|id| (id, base_addr))
}

#[tokio::main]
async fn main() -> Result<()> {
    println!("Starting Universal Connectivity Application...");

    // parse the remote peer addresses from the environment variable
    let mut _remote_addrs: Vec<Multiaddr> = Vec::default();
    if let Ok(remote_peers) = env::var("REMOTE_PEERS") {
        _remote_addrs = remote_peers
            .split(',')                         // Split the string at ','
            .map(str::trim)                     // Trim whitespace of each string
            .filter(|s| !s.is_empty())          // Filter out empty strings
            .map(Multiaddr::from_str)           // Parse each string into Multiaddr
            .collect::<Result<Vec<_>, _>>()?;   // Collect into Result and unwrap it
    }

    // parse the bootstrap peer addresses from the environment variable
    let mut bootstrap_addrs: Vec<Multiaddr> = Vec::default();
    if let Ok(bootstrap_peers) = env::var("BOOTSTRAP_PEERS") {
        bootstrap_addrs = bootstrap_peers
            .split(',')                         // Split the string at ','
            .map(str::trim)                     // Trim whitespace of each string
            .filter(|s| !s.is_empty())          // Filter out empty strings
            .map(Multiaddr::from_str)           // Parse each string into Multiaddr
            .collect::<Result<Vec<_>, _>>()?;   // Collect into Result and unwrap it
    }

    let local_key = identity::Keypair::generate_ed25519();
    let local_peer_id = identity::PeerId::from(local_key.public());
    println!("Local peer id: {local_peer_id}");

    // Create Gossipsub configuration
    let gossipsub_config = gossipsub::ConfigBuilder::default()
        .heartbeat_interval(Duration::from_secs(10))
        .validation_mode(gossipsub::ValidationMode::Permissive)
        .message_id_fn(message_id)
        .mesh_outbound_min(1)
        .mesh_n_low(1)
        .flood_publish(true)
        .build()?;

    // Create gossipsub instance
    let mut gossipsub = gossipsub::Behaviour::new(
        gossipsub::MessageAuthenticity::Signed(local_key.clone()),
        gossipsub_config,
    ).expect("Correct configuration");

    // Subscribe to topics
    for topic in GOSSIPSUB_TOPICS {
        let topic = gossipsub::IdentTopic::new(*topic);
        gossipsub.subscribe(&topic)?;
        println!("Subscribed to topic: {topic}");
    }

    // Create Kademlia configuration
    let mut kad_config = kad::Config::new(KADEMLIA_PROTOCOL_NAME);
    kad_config.set_query_timeout(Duration::from_secs(KADEMLIA_QUERY_TIMEOUT));
    kad_config.set_periodic_bootstrap_interval(Some(Duration::from_secs(KADEMLIA_BOOTSTRAP_INTERVAL)));

    // Create Kademlia behavior with memory store
    let store = kad::store::MemoryStore::new(local_peer_id);
    let mut kademlia = kad::Behaviour::with_config(local_peer_id, store, kad_config);
    kademlia.set_mode(Some(kad::Mode::Server));

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
            gossipsub,
            kademlia,
        })?
        .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
        .build();

    if !bootstrap_addrs.is_empty() {
        // Add the bootstrap peer addresses to the kademlia behaviour
        for addr in bootstrap_addrs.into_iter() {
            if let Some((peer_id, peer_addr)) = split_address(addr) {
                println!("Adding bootstrap peer: {peer_id} with multiaddr: {peer_addr}");
                swarm.behaviour_mut().kademlia.add_address(&peer_id, peer_addr);
            }
        }

        // Start the Kademlia bootstrap process
        swarm.behaviour_mut().kademlia.bootstrap()?;
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

                                // now that the remote peer is subscribed, publish a message
                                if topic == gossipsub::IdentTopic::new("universal-connectivity").into() {
                                    let (topic, msg) = create_test_message(&local_peer_id)?;

                                    let mut buf = Vec::new();
                                    msg.encode(&mut buf)?;

                                    if let Err(e) = swarm.behaviour_mut().gossipsub.publish(topic.clone(), buf) {
                                        println!("Failed to publish message: {e:?}");
                                    } else {
                                        println!("Published test message to '{topic}' topic");
                                    }
                                }
                            }
                            gossipsub::Event::Unsubscribed { peer_id, topic } => {
                                println!("Peer {peer_id} unsubscribed from '{topic}'");
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
                                        println!("Bootstrap progress: contacted {peer}, {num_remaining} remaining");
                                        if num_remaining == 0 {
                                            println!("Kademlia bootstrap completed successfully");
                                        }
                                    }
                                    kad::QueryResult::Bootstrap(Err(kad::BootstrapError::Timeout { .. })) => {
                                        println!("Kademlia bootstrap timed out");
                                    }
                                    kad::QueryResult::GetClosestPeers(Ok(kad::GetClosestPeersOk { key: _, peers })) => {
                                        println!("Found {} closest peers", peers.len());
                                        for peer in peers {
                                            println!("Closest peer: {peer:?}");
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
                                    println!("New peer added to routing table: {peer} with {} addresses", addresses.len());
                                }
                                if let Some(old) = old_peer {
                                    println!("Peer {peer} replaced {old} in routing table");
                                }
                            }
                            kad::Event::UnroutablePeer { peer } => {
                                println!("Peer {peer} is unroutable");
                            }
                            kad::Event::RoutablePeer { peer, address } => {
                                println!("Peer {peer} is routable at {address}");
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
