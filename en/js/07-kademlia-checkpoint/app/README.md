# Lesson 7: Kademlia DHT (Distributed Hash Table)

## Overview

This lesson provides a comprehensive, beginner-friendly introduction to **Kademlia Distributed Hash Table (DHT)** in JavaScript using libp2p. Students will learn how to build decentralized peer discovery, content routing, and distributed storage systems - the same technologies that power IPFS, Ethereum, and BitTorrent.

## Quick Start

```bash
# Run the lesson locally
cd app
npm install
node index.js

# OR run with Docker (from lesson directory)
docker-compose up --build

# Validate results (from lesson directory)
python3 check.py
```

## What You'll Learn

This lesson demonstrates three core DHT capabilities:

### 1. 🔍 Peer Routing
Find any peer in the network using only their Peer ID - no centralized directory needed!

### 2. 📦 Content Routing  
Announce content you provide and discover who has content you need - just like IPFS!

### 3. 💾 Distributed Value Storage
Store and retrieve key-value pairs across a distributed network - decentralized database in action!

## Architecture

The lesson uses a realistic 3-node architecture:

```
┌─────────────┐
│  BOOTSTRAP  │ ← Network entry point (Server Mode)
│    NODE     │   • Accepts connections
└──────┬──────┘   • Stores DHT data
       │          • Routes queries
       ├──────────────────────┐
       │                      │
┌──────▼──────┐      ┌───────▼──────┐
│  PROVIDER   │      │   CONSUMER   │
│    NODE     │      │     NODE     │
│(Server Mode)│      │ (Client Mode)│
└─────────────┘      └──────────────┘
• Provides content   • Queries DHT
• Stores values      • Lightweight
• Routes queries     • No storage
```

## Learning Path

### For Students

1. **Deep Dive**: [lesson.md](./lesson.md) - Comprehensive tutorial
2. **Experiment**: Modify `app/index.js` to test your understanding
3. **Build**: Create your own DHT-powered application

## Learning Objectives

By completing this lesson, students will:

- [ ] Understand how Distributed Hash Tables work
- [ ] Configure Kademlia DHT in libp2p
- [ ] Implement peer routing for decentralized discovery
- [ ] Use content routing for provider discovery
- [ ] Store and retrieve values in distributed storage
- [ ] Understand client vs server DHT modes
- [ ] Build multi-node DHT networks
- [ ] Apply DHT concepts to real-world applications

## Real-World Applications

### IPFS (InterPlanetary File System)
```javascript
// Find who has a file
for await (const provider of node.contentRouting.findProviders(fileCID)) {
  // Connect and download from provider
}
```

### Ethereum Node Discovery
```javascript
// Find Ethereum nodes
const peer = await node.peerRouting.findPeer(targetNodeId)
await node.dial(peer.multiaddrs[0])
```

### Distributed Configuration
```javascript
// Store app config
await node.services.dht.put(
  uint8ArrayFromString('/myapp/config'),
  uint8ArrayFromString(JSON.stringify(config))
)
```

## Validation Coverage

The `check.py` script validates:

- ✅ All 3 nodes start successfully
- ✅ Peer IDs are valid (base58, proper length)
- ✅ DHT modes configured correctly (2 server, 1 client)
- ✅ Network formation and connections
- ✅ Peer routing queries
- ✅ Content routing with CIDs
- ✅ Value storage PUT/GET operations
- ✅ Routing table population
- ✅ Comprehensive demonstration summary

Success rate in testing: **100%**

## Code Highlights

### Creating a DHT-Enabled Node
```javascript
const node = await createLibp2p({
  // ... transports, encryption, muxing
  services: {
    dht: kadDHT({
      clientMode: false,  // Server mode
      protocol: '/universal-connectivity-workshop/kad/1.0.0'
    }),
    identify: identify()
  }
})
```

### Peer Routing
```javascript
const foundPeer = await node.peerRouting.findPeer(targetPeerId)
console.log(`Found at: ${foundPeer.multiaddrs[0]}`)
```

### Content Routing
```javascript
// Announce
await node.contentRouting.provide(contentCID)

// Discover
for await (const provider of node.contentRouting.findProviders(contentCID)) {
  console.log(`Provider: ${provider.id}`)
}
```

### Value Storage
```javascript
// Store
await node.services.dht.put(key, value)

// Retrieve
const data = await node.services.dht.get(key)
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Peer not found | Routing tables not populated | Wait 3+ seconds after connecting |
| Value not retrieved | Replication incomplete | Add 2-3 second delay after PUT |
| Content provider not found | Provider record not propagated | Wait 2-3 seconds after provide() |
| Connection failures | Incorrect bootstrap address | Verify multiaddr format |


## Testing

### Local Testing
```bash
cd app
npm install
node index.js
```

### Workshop Tool Testing
```bash
# From the lesson directory
docker-compose up --build

# In a new terminal
python3 check.py
```

### Expected Output
```
i Checking Lesson 7: Kademlia DHT
i ==================================================
i Found stdout.log from Docker container
i Checking Kademlia DHT functionality...
+ BOOTSTRAP node started with Peer ID: 12D3KooWJ133XEgvjxggd4JcjXqKhip2gcoYvs7m4yFFANx4KW42
+ PROVIDER node started with Peer ID: 12D3KooWNVtAKewJHVtx2mA8NwDr7ZLT2GcLxu8jrP2BZr4eV49E
+ CONSUMER node started with Peer ID: 12D3KooWCCt6T6pfZzMhSZwrGfzECBsZ5tx6jwdboiA6hi1m9wzS
+ Multi-node DHT network detected: 3 nodes
+ DHT modes correctly configured: 2 server nodes, 1 client node
+ All nodes listening: 6 address(es) total
.......
......
```

## Docker Architecture

### Simplified Design (Current):

```
┌─────────────────────────────────────┐
│   Docker Container (lesson)         │
│   - Runs app/index.js               │
│   - Outputs to stdout.log           │
│   - 3 nodes: Bootstrap/Provider/    │
│     Consumer                         │
└─────────────────────────────────────┘
           │
           │ writes
           ▼
    stdout.log (volume mount)
           │
           │ reads
           ▼
    check.py (runs on host)
           │
           │ validates
           ▼
    ✅ Pass / ❌ Fail
```

## Prerequisites

Before starting this lesson, complete:
1. ✅ Lesson 1: Identity and Swarm
2. ✅ Lesson 2: TCP Transport
3. ✅ Lesson 3: Ping Protocol
4. ✅ Lesson 4: Circuit Relay
5. ✅ Lesson 5: Identify Protocol
6. ✅ Lesson 6: GossipSub Pub/Sub

## What's Next?

After completing this lesson:
- Build a decentralized file sharing app
- Create a distributed database
- Implement a peer discovery service
- Contribute to libp2p projects
- Explore advanced protocols (AutoNAT, hole punching)

## Resources

- [Kademlia Paper (Original)](https://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf)
- [libp2p DHT Specification](https://github.com/libp2p/specs/tree/master/kad-dht)
- [js-libp2p-kad-dht](https://github.com/libp2p/js-libp2p/tree/main/packages/kad-dht)
- [IPFS DHT Documentation](https://docs.ipfs.tech/concepts/dht/)
- [libp2p Documentation](https://docs.libp2p.io/)

## 🤝 Contributing

Found an issue or want to improve this lesson?
- Report bugs on GitHub
- Suggest improvements
- Add more examples
- Improve documentation

---
