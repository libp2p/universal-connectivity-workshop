# Lesson 7: Kademlia DHT

Welcome to Checkpoint 4! In this lesson, you'll implement Kademlia DHT, libp2p's distributed hash table protocol that enables decentralized peer discovery, content routing, and distributed storage in js-libp2p.

## Learning Objectives

By the end of this lesson, you will:
- Understand how Distributed Hash Tables (DHTs) work
- Implement Kademlia DHT for decentralized peer discovery
- Use peer routing to find peers without centralized servers
- Use content routing to announce and discover content providers
- Store and retrieve values in a distributed key-value store
- Understand client vs server DHT modes

---

## Background: Kademlia DHT Protocol

Kademlia is a peer-to-peer distributed hash table protocol that provides three essential capabilities:

### 1. **Peer Routing**
Find the network location (multiaddrs) of any peer using only their Peer ID, enabling decentralized peer discovery without DNS or central servers.

### 2. **Content Routing**
Announce that you provide specific content (using CIDs) and discover which peers in the network provide that content. This is how IPFS enables content-addressed file sharing.

### 3. **Value Storage**
Store and retrieve arbitrary key-value pairs distributed across the network, creating a decentralized database that no single peer controls.

### How Kademlia DHT Works

**Key Concepts:**

1. **XOR Distance Metric**: Kademlia uses XOR to measure "distance" between node IDs and keys, creating a structured network topology.

2. **K-Buckets**: Each node maintains routing tables called k-buckets organized by distance ranges, enabling logarithmic lookup complexity.

3. **Recursive Lookups**: Finding peers or content involves querying progressively closer nodes until the target is found (similar to binary search).

4. **Replication**: Values are stored on multiple nodes (default: 20) for redundancy and availability.

5. **Client vs Server Mode**:
   - **Server Mode**: Node answers DHT queries and stores values (becomes part of the DHT infrastructure)
   - **Client Mode**: Node only queries the DHT but doesn't store values (lightweight participant)

**Real-World Usage:**
- **IPFS**: Uses Kademlia for content routing and peer discovery
- **Ethereum**: Uses modified Kademlia for node discovery
- **BitTorrent**: Uses Kademlia for trackerless peer discovery
- **Blockchain Networks**: Many use DHT for decentralized node discovery

---

## Your Task

Building on your GossipSub implementation from Lesson 6, you need to:

1. **Add Kademlia DHT Service**: Configure libp2p nodes with DHT capabilities
2. **Implement Peer Routing**: Find peers by their Peer ID
3. **Implement Content Routing**: Announce and discover content providers
4. **Implement Value Storage**: Store and retrieve distributed key-value pairs
5. **Understand DHT Modes**: Learn when to use client vs server mode

## Step-by-Step Instructions

### Step 1: Review the Implementation

The implementation is provided for you in `app/index.js`. It demonstrates a complete DHT network with three nodes:

- **Bootstrap Node**: Server mode - accepts connections and DHT queries
- **Provider Node**: Server mode - provides content and stores values
- **Consumer Node**: Client mode - queries the DHT for peers, content, and values

### Step 2: Understanding Kademlia DHT Configuration

```javascript
import { kadDHT } from '@libp2p/kad-dht'

const node = await createLibp2p({
  // ... transports, encryption, muxing
  services: {
    dht: kadDHT({
      clientMode: false,  // Server mode: can answer queries and store values
      protocol: '/universal-connectivity-workshop/kad/1.0.0',
      peerInfoMapper: (peer) => peer,
      validators: {},  // Custom validators for stored values
      selectors: {}    // Custom selectors for choosing between multiple values
    }),
    identify: identify(), //required
    ping: ping()  // Required for DHT to work properly
  }
})
```

**Key Configuration Options:**

- `clientMode: false` - Server mode (default): participates in storing DHT data
- `clientMode: true` - Client mode: only queries, doesn't store data
- `protocol` - Custom DHT protocol identifier (must match across network)
- `validators` - Functions to validate values before storing
- `selectors` - Functions to choose between multiple values for same key

### Step 3: Peer Routing - Finding Peers

Peer routing lets you discover where a peer is located in the network:

```javascript
// Find peer by ID
const foundPeer = await node.peerRouting.findPeer(targetPeerId)
console.log(`Found peer at: ${foundPeer.multiaddrs[0].toString()}`)
```

**Use Cases:**
- Establishing connections to specific peers
- Building peer lists for application protocols
- Discovering network topology

### Step 4: Content Routing - Announcing and Finding Content

Content routing enables content-addressed systems like IPFS:

```javascript
import { CID } from 'multiformats/cid'
import * as raw from 'multiformats/codecs/raw'
import { sha256 } from 'multiformats/hashes/sha2'

// Create a Content ID (CID)
const content = 'Hello World'
const contentBytes = uint8ArrayFromString(content)
const hash = await sha256.digest(contentBytes)
const cid = CID.create(1, raw.code, hash)

// Announce that you provide this content
await node.contentRouting.provide(cid)

// Find who provides this content
for await (const provider of node.contentRouting.findProviders(cid)) {
  console.log(`Provider: ${provider.id.toString()}`)
}
```

**Use Cases:**
- IPFS-style content distribution
- Decentralized file sharing
- Distributed content delivery networks (CDNs)

### Step 5: Value Storage - Distributed Key-Value Store

DHT value storage creates a distributed database:

```javascript
// Store a value
const key = uint8ArrayFromString('/my-app/my-key')
const value = uint8ArrayFromString(JSON.stringify({ data: 'my value' }))
await node.services.dht.put(key, value)

// Retrieve a value
const retrievedValue = await node.services.dht.get(key)
const data = JSON.parse(uint8ArrayToString(retrievedValue))
console.log(data)  // { data: 'my value' }
```

**Key Format:**
- Use path-like keys: `/namespace/key-name`
- Keys are namespace-aware
- Values are replicated across ~20 nodes

**Use Cases:**
- Distributed configuration storage
- Decentralized naming systems (like ENS)
- Peer reputation systems
- Application state synchronization

### Step 6: Running and Testing the Lesson

## Prerequisites

- Node.js 22+ installed
- Basic understanding of peer-to-peer networks
- Completed lessons 1-6 of this workshop

## Three Ways to Run

### Option 1: Direct Node Execution (Recommended for Learning)

```bash
cd app
npm install
node index.js
```

### **What you'll see:**

```
Starting Kademlia DHT Universal Connectivity Lesson...

=== STEP 1: BOOTSTRAP NODE SETUP ===
[BOOTSTRAP] Started with Peer ID: 12D3KooW...
[BOOTSTRAP] DHT Mode: Server (can answer queries and store values)

=== STEP 2: PROVIDER NODE SETUP ===
[PROVIDER] Started with Peer ID: 12D3KooW...
[PROVIDER] DHT Mode: Server (can answer queries and store values)

=== STEP 3: CONSUMER NODE SETUP ===
[CONSUMER] Started with Peer ID: 12D3KooW...
[CONSUMER] DHT Mode: Client (queries only, doesn't store values)

=== STEP 4: NETWORK FORMATION ===
[PROVIDER] Successfully connected to bootstrap node
[CONSUMER] Successfully connected to bootstrap node

=== STEP 5: PEER ROUTING DEMONSTRATION ===
[CONSUMER] Successfully found peer via DHT!
+ Peer routing successful: DHT enabled decentralized peer discovery

=== STEP 6: CONTENT ROUTING DEMONSTRATION ===
[PROVIDER] Announcing as content provider to DHT...
[CONSUMER] Found content provider via DHT!
+ Content routing successful: DHT enabled decentralized content discovery

=== STEP 7: DISTRIBUTED VALUE STORAGE ===
[PROVIDER] Successfully stored value in distributed hash table
[CONSUMER] Successfully retrieved value from DHT!
+ DHT GET operation successful: Retrieved value from distributed storage

=== STEP 8: DHT NETWORK TOPOLOGY ===
+ DHT routing tables populated: Network topology established
```

### Option 2: Docker Compose (Workshop Tool)

```bash
docker-compose up --build
```

Check results:
```bash
python3 check.py
```

### Option 3: Interactive Exploration

Modify `app/index.js` to experiment with:
- Different DHT configurations
- Custom content IDs
- Your own key-value pairs
- Multiple bootstrap nodes

## Understanding the Output

### Step 1-3: Node Startup
```
[BOOTSTRAP] Started with Peer ID: 12D3KooW...
[PROVIDER] Started with Peer ID: 12D3KooW...
[CONSUMER] Started with Peer ID: 12D3KooW...
```
**What's happening**: Three nodes with different roles are created

### Step 4: Network Formation
```
[PROVIDER] Successfully connected to bootstrap node
[CONSUMER] Successfully connected to bootstrap node
```
**What's happening**: Nodes are joining the DHT network

### Step 5: Peer Routing
```
[CONSUMER] Successfully found peer via DHT!
+ Peer routing successful
```
**What's happening**: Consumer found Provider without knowing its address beforehand

### Step 6: Content Routing
```
[PROVIDER] Announcing as content provider to DHT...
[CONSUMER] Found content provider via DHT!
```
**What's happening**: Like IPFS - announcing you have content and others finding it

### Step 7: Value Storage
```
[PROVIDER] Successfully stored value in distributed hash table
[CONSUMER] Successfully retrieved value from DHT!
```
**What's happening**: Distributed database in action - data stored across multiple nodes

## Key Concepts Explained Simply

### 1. Peer Routing
**Like**: Phone book for peer-to-peer networks
**Without DHT**: Need centralized server to find peers
**With DHT**: Ask the network itself

### 2. Content Routing
**Like**: Google for peer-to-peer content
**Without DHT**: Need to know who has what
**With DHT**: Search by content hash (CID)

### 3. Value Storage
**Like**: Dropbox, but decentralized
**Without DHT**: Need central database
**With DHT**: Data distributed across network

## Real-World Applications

### IPFS (InterPlanetary File System)
Uses Kademlia DHT to:
- Find who has files you want
- Announce files you're sharing
- Discover peer addresses

### Ethereum
Uses modified Kademlia to:
- Discover other Ethereum nodes
- Find peers for specific blockchain shards
- Maintain network health

### BitTorrent
Uses Mainline DHT (Kademlia-based) to:
- Find peers without trackers
- Decentralized torrent discovery

## Experiment Ideas

### 1. Store Your Own Data
```javascript
const key = uint8ArrayFromString('/myapp/username')
const value = uint8ArrayFromString('Alice')
await node.services.dht.put(key, value)
```

### 2. Create Multiple Bootstrap Nodes
Run the app twice on different ports to create a larger network

### 3. Monitor Routing Tables
```javascript
const peers = await node.peerStore.all()
console.log(`DHT knows about ${peers.length} peers`)
```

### 4. Custom Content IDs
```javascript
const myContent = 'Hello World'
const hash = await sha256.digest(uint8ArrayFromString(myContent))
const cid = CID.create(1, raw.code, hash)
await node.contentRouting.provide(cid)
```

## Common Questions

### Q: Why wait between operations?
**A**: DHT is distributed - data needs time to propagate across nodes (2-3 seconds)

### Q: What's the difference between client and server mode?
**A**: 
- **Server mode**: Stores DHT data, answers queries (more resources, helps network)
- **Client mode**: Only queries, doesn't store (lightweight, mobile-friendly)

### Q: How does it find peers without a central server?
**A**: Uses XOR distance metric and k-bucket routing - peers recursively forward queries to closer nodes

### Q: How many nodes store each value?
**A**: Default is ~20 nodes for redundancy (configurable)

### Q: Is this secure?
**A**: Basic DHT has vulnerabilities (Sybil attacks, eclipse attacks). Production systems add:
- Validators (verify data before storing)
- Selectors (choose best value when multiple exist)
- Peer reputation systems

## Next Steps

### Build Something Cool
- **Decentralized Chat**: Use DHT to find chat participants
- **File Sharing App**: Store file metadata in DHT
- **Peer Discovery Service**: Help apps find each other
- **Distributed Database**: Build on DHT value storage

### Explore Advanced Topics
- Custom validators and selectors
- Private DHTs with allow-lists
- Performance optimization
- Security best practices

### Contribute
- Report issues on GitHub
- Improve documentation
- Add more examples
- Help other learners

## Troubleshooting

### "Peer not found"
```
✓ Normal if queried immediately
✗ Issue if after 3+ seconds
Solution: Increase wait time between connection and query
```

### "Value not retrieved"
```
✓ Normal for very small networks (< 4 nodes)
✗ Issue in larger networks after waiting
Solution: Ensure PUT succeeded, check key format
```

### Port conflicts
```
Solution: App uses random ports (0) - no conflicts
If seeing errors, check firewall settings
```

### Connection refused
```
Solution: Ensure bootstrap node started first
Verify multiaddr format correct
```

---

## Key Concepts Learned

1. **Distributed Hash Tables**: Data structure distributed across multiple nodes using consistent hashing

2. **XOR Distance Metric**: Mathematical way to measure closeness between node IDs and keys

3. **Logarithmic Lookup**: Finding data requires only log(N) hops for N nodes (extremely efficient)

4. **Peer Routing**: Decentralized peer discovery without DNS or central directories

5. **Content Routing**: Content-addressed networking where data is found by its hash, not location

6. **Distributed Storage**: Key-value pairs replicated across multiple nodes for redundancy

7. **Client vs Server Modes**: Balance between resource contribution and lightweight participation

---

## Troubleshooting

**Issue**: "Peer not found" errors
- **Solution**: Ensure nodes are connected and DHT routing tables have populated (wait 2-3 seconds)

**Issue**: Values not found with `get()`
- **Solution**: DHT replication takes time. Allow 2-3 seconds for values to propagate across nodes

**Issue**: No content providers found
- **Solution**: Ensure provider node called `provide()` and consumer waited for propagation

**Issue**: Connection failures
- **Solution**: Verify bootstrap addresses are correct and nodes are in server mode (not client mode only)

---

## Advanced Concepts

### DHT Security Considerations

- **Sybil Attacks**: Malicious peers creating many identities to control DHT
- **Eclipse Attacks**: Isolating target nodes from honest network
- **Value Poisoning**: Storing malicious values in the DHT

**Mitigations:**
- Validators: Verify values before accepting them
- Selectors: Choose best value when multiple exist
- Peer reputation systems
- Private DHTs with allow-lists

### Performance Optimization

- **Bootstrap Nodes**: Well-known stable nodes for network entry
- **K-Bucket Configuration**: Tune bucket sizes for network scale
- **Query Parallelization**: Query multiple peers simultaneously
- **Caching**: Cache frequently accessed values locally

### Production Best Practices

1. **Use Bootstrap Lists**: Maintain list of stable bootstrap nodes
2. **Enable Server Mode**: Run server mode nodes for healthy DHT
3. **Implement Validators**: Validate data before storing
4. **Monitor Routing Tables**: Track DHT health and connectivity
5. **Graceful Degradation**: Handle DHT failures in application logic

---

## Real-World Applications

### IPFS (InterPlanetary File System)
Uses Kademlia DHT for:
- Finding peers who have specific content (CIDs)
- Discovering peer addresses for direct connections
- Maintaining network topology and peer lists

### Ethereum
Modified Kademlia (Discv4/Discv5) for:
- Discovering Ethereum nodes
- Finding peers for specific shards (in Eth2)
- Maintaining healthy peer connections

### BitTorrent
Uses Mainline DHT (based on Kademlia) for:
- Trackerless torrent peer discovery
- Storing metadata about torrents
- Finding seeders for content

---

## Hints

💡 **Network Scale**: DHT efficiency improves with more nodes - consider running multiple instances

💡 **Client Mode**: Use client mode for lightweight applications that don't want to store DHT data

💡 **Namespacing**: Use clear key namespaces like `/app-name/category/key` for organization

💡 **CID Format**: Content IDs (CIDs) are self-describing hashes - include codec and hash type

💡 **Replication**: Values are automatically replicated to ~20 nodes for redundancy

---

## Resources

- [libp2p Docs](https://docs.libp2p.io/)
- [DHT Explained Video](https://www.youtube.com/watch?v=kXyVqk3EbwE)
- [Kademlia Paper (Original)](https://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf)
- [libp2p Kademlia DHT Specification](https://github.com/libp2p/specs/tree/master/kad-dht)
- [js-libp2p-kad-dht Documentation](https://github.com/libp2p/js-libp2p/tree/main/packages/kad-dht)
- [IPFS DHT Documentation](https://docs.ipfs.tech/concepts/dht/)
- [Understanding DHTs in P2P Networks](https://en.wikipedia.org/wiki/Distributed_hash_table)

---

## What's Next?

Congratulations! You've now mastered the core libp2p protocols in javascript version:

1. ✅ Identity and peer IDs
2. ✅ Transport (TCP)
3. ✅ Ping protocol
4. ✅ Circuit relay
5. ✅ Identify protocol
6. ✅ GossipSub pub/sub
7. ✅ **Kademlia DHT** (Current lesson)

You now have the foundation to build production-ready decentralized applications with:
- Secure peer-to-peer networking
- Efficient content distribution
- Decentralized peer discovery
- Topic-based messaging
- Distributed storage

**Next Steps:**
- Lesson-08 : Final Showdown
- Build a complete decentralized application utilising js-libp2p modules
- Contribute to the libp2p ecosystem

Happy learning! 🚀