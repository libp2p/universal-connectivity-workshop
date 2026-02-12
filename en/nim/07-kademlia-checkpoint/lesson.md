# Lesson 07: Kademlia Checkpoint

## Introduction

Welcome to your fourth checkpoint! In this lesson, you'll implement Kademlia, a distributed hash table (DHT) protocol that enables decentralized peer discovery and content routing in libp2p networks using nim-libp2p.

## Learning Objectives

By the end of this lesson, you will:

- Understand distributed hash tables and the Kademlia protocol
- Implement Kademlia DHT for peer discovery in Nim
- Handle bootstrap processes and peer routing
- Store and retrieve values in the distributed hash table
- Work with providers (content advertisement and discovery)

## Background: Kademlia DHT

### What is a Distributed Hash Table?

A Distributed Hash Table (DHT) is a decentralized key-value store spread across multiple nodes. Unlike a centralized database, no single node stores all data. Instead, data is distributed based on the hash of keys.

```
              ┌────────────────────────────────────────────────────┐
              │            Distributed Hash Table                  │
              │                                                    │
              │   Node A        Node B        Node C        Node D │
              │   ┌────┐        ┌────┐        ┌────┐        ┌────┐│
              │   │K1:V│        │K4:V│        │K2:V│        │K3:V││
              │   │K5:V│        │K8:V│        │K6:V│        │K7:V││
              │   └────┘        └────┘        └────┘        └────┘│
              │                                                    │
              │  Keys distributed based on XOR distance to NodeID  │
              └────────────────────────────────────────────────────┘
```

### Kademlia's Key Innovations

Kademlia provides several advantages over simpler DHT designs:

1. **XOR Distance Metric**: Distance between nodes is calculated using XOR, which is symmetric and satisfies the triangle inequality
2. **Logarithmic Lookups**: O(log n) hops to find any key in a network of n nodes
3. **Self-Organizing**: The routing table automatically adapts as peers join/leave
4. **Parallel Queries**: Multiple nodes are queried simultaneously (alpha parameter)
5. **Redundancy**: Data is replicated across multiple closest nodes

### Kademlia Parameters

| Parameter | Description | nim-libp2p Default |
|-----------|-------------|-------------------|
| k (replication) | Bucket size, number of peers to store/query | 20 |
| alpha | Number of parallel queries | 10 |
| quorum | Responses needed for consensus | 5 |
| timeout | Query timeout | 5 seconds |

### Use Cases

- **IPFS**: Content-addressable storage and peer discovery
- **BitTorrent**: DHT-based tracker
- **Ethereum**: Node discovery in devp2p
- **libp2p**: Peer routing and content routing

## Your Task

Building on your Gossipsub implementation from Lesson 6, you need to:

1. **Create KadDHT Instance**: Initialize Kademlia with bootstrap nodes
2. **Mount the Protocol**: Register it on the switch
3. **Store Values**: Put key-value pairs in the DHT
4. **Retrieve Values**: Get values by key
5. **Handle Providers**: Advertise and discover content providers

## Step-by-Step Instructions

### Step 1: Update Imports

Add the Kademlia-related imports:

```nim
import chronos
import libp2p
import libp2p/protocols/kademlia
import stew/byteutils
import std/[os, strutils]
```

### Step 2: Define Constants and Helpers

```nim
const
  DHTKey = "nim-libp2p-workshop-key"

proc toKey(s: string): seq[byte] =
  ## Convert a string to a DHT key
  s.toBytes()
```

### Step 3: Create and Configure KadDHT

Create the Kademlia DHT instance with bootstrap nodes:

```nim
proc createKadDHT(switch: Switch, bootstrapNodes: seq[(PeerId, seq[MultiAddress])]): KadDHT =
  ## Create a KadDHT instance with configuration
  let config = KadDHTConfig.new(
    timeout = 10.seconds,       # Query timeout
    quorum = 2,                 # Responses needed for consensus
    replication = 10,           # k-parameter
    alpha = 5,                  # Parallel queries
  )

  KadDHT.new(
    switch,
    bootstrapNodes = bootstrapNodes,
    config = config,
  )
```

### Step 4: Store and Retrieve Values

```nim
proc storeValue(kad: KadDHT, key: string, value: string) {.async.} =
  ## Store a value in the DHT
  let keyBytes = key.toKey()
  let valueBytes = value.toBytes()

  let res = await kad.putValue(keyBytes, valueBytes).wait(10.seconds)
  if res.isErr():
    echo "Failed to store value: ", res.error
  else:
    echo "Stored value '", value, "' with key: ", key

proc retrieveValue(kad: KadDHT, key: string): Future[Option[string]] {.async.} =
  ## Retrieve a value from the DHT
  let keyBytes = key.toKey()

  let res = await kad.getValue(keyBytes).wait(10.seconds)
  if res.isErr():
    echo "Failed to retrieve value: ", res.error
    return none(string)
  else:
    let record = res.get()
    return some(string.fromBytes(record.value))
```

### Step 5: Work with Providers

```nim
proc advertiseContent(kad: KadDHT, contentKey: seq[byte]) {.async.} =
  ## Advertise that we're providing content
  await kad.startProviding(contentKey)
  echo "Started providing content: ", contentKey.toHex()[0..15], "..."

proc findProviders(kad: KadDHT, contentKey: seq[byte]): Future[seq[PeerId]] {.async.} =
  ## Find providers for content
  let providers = await kad.getProviders(contentKey)
  echo "Found ", providers.len, " providers for content"
  return providers
```

### Step 6: Parse Bootstrap Peers

```nim
proc parseBootstrapPeers(peersEnv: string): seq[(PeerId, seq[MultiAddress])] =
  ## Parse REMOTE_PEERS environment variable into bootstrap peer list
  result = @[]
  if peersEnv.len == 0:
    return

  for addrStr in peersEnv.split(','):
    let trimmed = addrStr.strip()
    if trimmed.len > 0:
      let fullAddr = MultiAddress.init(trimmed).tryGet()
      let parsed = parseFullAddress(fullAddr)
      if parsed.isOk:
        let (peerId, wireAddr) = parsed.get()
        result.add((peerId, @[wireAddr]))
```

### Step 7: Mount KadDHT on Switch

```nim
# After creating switch and KadDHT
switch.mount(kad)
```

### Step 8: Main Application Flow

```nim
proc main() {.async.} =
  echo "Starting Kademlia DHT application..."

  # Parse bootstrap peers from environment
  let remotePeersEnv = getEnv("REMOTE_PEERS", "")
  let bootstrapPeers = parseBootstrapPeers(remotePeersEnv)

  # Create switch
  let rng = newRng()
  let localAddress = MultiAddress.init("/ip4/0.0.0.0/tcp/0").tryGet()

  let switch = SwitchBuilder
    .new()
    .withRng(rng)
    .withAddress(localAddress)
    .withTcpTransport()
    .withMplex()
    .withNoise()
    .build()

  # Create KadDHT
  let kad = createKadDHT(switch, bootstrapPeers)
  switch.mount(kad)

  # Start switch
  await switch.start()

  echo "Local peer id: ", switch.peerInfo.peerId
  for addr in switch.peerInfo.addrs:
    echo "Listening on: ", addr

  # Store a value
  await storeValue(kad, DHTKey, "Hello from nim-libp2p!")

  # Wait for replication
  await sleepAsync(2.seconds)

  # Retrieve the value
  let value = await retrieveValue(kad, DHTKey)
  if value.isSome:
    echo "Retrieved: ", value.get()

  # Keep running
  echo "DHT node running..."
  while true:
    await sleepAsync(10.seconds)

waitFor(main())
```

## Solution

Here's the complete working solution:

```nim
import chronos
import libp2p
import libp2p/protocols/kademlia
import stew/byteutils
import std/[os, strutils, options]

const
  DHTKey = "nim-libp2p-workshop-key"
  DHTValue = "Hello from nim-libp2p Kademlia!"

proc toKey(s: string): seq[byte] =
  ## Convert a string to a DHT key
  s.toBytes()

proc parseBootstrapPeers(peersEnv: string): seq[(PeerId, seq[MultiAddress])] =
  ## Parse REMOTE_PEERS environment variable into bootstrap peer list
  result = @[]
  if peersEnv.len == 0:
    return

  for addrStr in peersEnv.split(','):
    let trimmed = addrStr.strip()
    if trimmed.len > 0:
      let fullAddr = MultiAddress.init(trimmed).tryGet()
      let parsed = parseFullAddress(fullAddr)
      if parsed.isOk:
        let (peerId, wireAddr) = parsed.get()
        result.add((peerId, @[wireAddr]))

proc main() {.async.} =
  echo "Starting Kademlia DHT application..."

  # Parse bootstrap peers from environment
  let remotePeersEnv = getEnv("REMOTE_PEERS", "")
  let bootstrapPeers = parseBootstrapPeers(remotePeersEnv)

  echo "Bootstrap peers: ", bootstrapPeers.len

  # Create random number generator
  let rng = newRng()

  # Use TCP address
  let localAddress = MultiAddress.init("/ip4/0.0.0.0/tcp/0").tryGet()

  # Create a Switch
  let switch = SwitchBuilder
    .new()
    .withRng(rng)
    .withAddress(localAddress)
    .withTcpTransport()
    .withMplex()
    .withNoise()
    .build()

  # Create KadDHT with configuration
  let config = KadDHTConfig.new(
    timeout = 10.seconds,
    quorum = 2,
    replication = 10,
    alpha = 5,
  )

  let kad = KadDHT.new(
    switch,
    bootstrapNodes = bootstrapPeers,
    config = config,
  )

  # Mount KadDHT on the switch
  switch.mount(kad)

  # Connection event handlers
  proc onConnect(peerId: PeerId, event: ConnEvent) {.async: (raises: [CancelledError]).} =
    echo "Connected to: ", peerId

  proc onDisconnect(peerId: PeerId, event: ConnEvent) {.async: (raises: [CancelledError]).} =
    echo "Disconnected from: ", peerId

  switch.addConnEventHandler(onConnect, ConnEventKind.Connected)
  switch.addConnEventHandler(onDisconnect, ConnEventKind.Disconnected)

  # Start the switch
  await switch.start()

  # Print local peer information
  echo "Local peer id: ", switch.peerInfo.peerId

  # Print listening addresses
  for addr in switch.peerInfo.addrs:
    echo "Listening on: ", addr

  # Connect to bootstrap peers manually
  for (peerId, addrs) in bootstrapPeers:
    try:
      echo "Connecting to bootstrap peer: ", peerId
      await switch.connect(peerId, addrs)
      echo "Connected to bootstrap peer: ", peerId
    except CatchableError as e:
      echo "Failed to connect to bootstrap peer: ", e.msg

  # Wait for connections to stabilize
  await sleepAsync(2.seconds)

  # Store a value in the DHT
  echo "Storing value in DHT..."
  let keyBytes = DHTKey.toKey()
  let valueBytes = DHTValue.toBytes()

  let putRes = await kad.putValue(keyBytes, valueBytes).wait(15.seconds)
  if putRes.isErr():
    echo "Failed to store value: ", putRes.error
  else:
    echo "Stored value '", DHTValue, "' with key: ", DHTKey

  # Wait for replication
  await sleepAsync(3.seconds)

  # Retrieve the value
  echo "Retrieving value from DHT..."
  let getRes = await kad.getValue(keyBytes).wait(15.seconds)
  if getRes.isErr():
    echo "Failed to retrieve value: ", getRes.error
  else:
    let record = getRes.get()
    let retrievedValue = string.fromBytes(record.value)
    echo "Retrieved value: ", retrievedValue

  # Keep running
  echo "DHT node running. Waiting for messages..."
  while true:
    await sleepAsync(5.seconds)

waitFor(main())
```

## Code Walkthrough

### KadDHT Initialization

```nim
let config = KadDHTConfig.new(
  timeout = 10.seconds,   # How long to wait for queries
  quorum = 2,             # Minimum responses for consensus
  replication = 10,       # Number of closest peers to query
  alpha = 5,              # Parallel query count
)

let kad = KadDHT.new(
  switch,
  bootstrapNodes = bootstrapPeers,  # Initial peers to connect to
  config = config,
)
```

### Value Storage and Retrieval

```nim
# putValue returns Result[void, cstring]
let putRes = await kad.putValue(key, value).wait(timeout)

# getValue returns Result[EntryRecord, cstring]
let getRes = await kad.getValue(key).wait(timeout)
if getRes.isOk:
  let record = getRes.get()
  echo "Value: ", string.fromBytes(record.value)
```

### Bootstrap Process

When a KadDHT node starts:
1. It connects to bootstrap nodes
2. Queries them for nodes close to itself
3. Populates its routing table
4. Periodically refreshes buckets

## Testing Your Implementation

The workshop checker will:
1. Start a DHT server node
2. Connect to your peer
3. Verify DHT operations (put/get)
4. Check value storage and retrieval

## Success Criteria

Your implementation should:

- Display the startup message and local peer ID
- Connect to bootstrap peers
- Store values in the DHT
- Retrieve values from the DHT
- Handle peer connection events
- Maintain DHT routing table

## Common Mistakes

1. **Not mounting KadDHT**: `switch.mount(kad)` is required
2. **Short timeouts**: DHT operations need time for network propagation
3. **Missing bootstrap peers**: Without initial peers, DHT can't function
4. **Not waiting for replication**: Values need time to propagate
5. **Key encoding issues**: Ensure consistent key encoding (use `.toBytes()`)

## Advanced: Understanding Kademlia Routing

### XOR Distance

Kademlia uses XOR to calculate distance between node IDs:

```
Distance(A, B) = A XOR B

Example:
Node A: 1010
Node B: 1100
Distance: 0110 = 6
```

### Routing Table Structure

```
┌─────────────────────────────────────────────────┐
│                  Routing Table                   │
├─────────────────────────────────────────────────┤
│ Bucket 0: Peers with distance 2^0 (closest)     │
│ Bucket 1: Peers with distance 2^1               │
│ Bucket 2: Peers with distance 2^2               │
│ ...                                              │
│ Bucket 255: Peers with distance 2^255 (farthest)│
└─────────────────────────────────────────────────┘
```

Each bucket stores up to k peers. When a bucket is full, the oldest peer is pinged - if it responds, the new peer is discarded (favoring long-lived peers).

## What's Next?

Congratulations! You've reached your fourth checkpoint!

You now have a libp2p node that can:
- Communicate over TCP with encryption
- Exchange peer identification
- Participate in publish-subscribe messaging (Gossipsub)
- Discover peers through Kademlia DHT
- Store and retrieve data in a distributed hash table

Key concepts you've learned:
- **Distributed Hash Tables**: Decentralized key-value storage
- **XOR Distance Metric**: How Kademlia organizes peers
- **Bootstrap Process**: Joining existing P2P networks
- **Routing Tables**: Efficient peer organization and lookup
- **Quorum and Replication**: Ensuring data availability

In the next lesson, you'll complete the Universal Connectivity application by putting everything together!
