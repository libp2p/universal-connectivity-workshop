# Lesson 5: Identify Checkpoint 🏆

Welcome to your second checkpoint! In this lesson, you'll implement the Identify protocol, which allows libp2p peers to exchange information about their capabilities, supported protocols, and network details.

## Learning Objectives

By the end of this lesson, you will:
- Understand the purpose of the Identify protocol in libp2p
- Add Identify service to your libp2p node
- Handle identify events and extract peer information
- Exchange protocol capabilities with remote peers

## Background: The Identify Protocol

The Identify protocol is fundamental to libp2p's peer discovery and capability negotiation. It serves several important purposes:

- **Capability Discovery**: Learn what protocols a peer supports
- **Version Information**: Exchange software version and agent strings
- **Address Discovery**: Learn how peers see your external addresses
- **Protocol Negotiation**: Establish common protocols for communication

When peers connect, they automatically exchange identification information, allowing the network to be self-describing and adaptive.

## Your Task

In this lesson, you'll implement a two-node setup where Node1 listens and Node2 dials it. After connection, both nodes will:

1. **Add Identify Service**: Include `identify()` service in your libp2p configuration
2. **Configure Identify Settings**: Set up identify with the IPFS protocol and Universal Connectivity agent string
3. **Handle Identify Events**: Process identification events and display peer information
4. **Dynamic Address Discovery**: Use the Identify protocol to discover each other's listening addresses dynamically
5. **Bidirectional Ping**: Both nodes ping each other after identify exchange completes

## Architecture: Two-Node Setup

This lesson uses a two-node architecture:
- **Node1 (Listener)**: Starts first, listens on a fixed port (9092), and waits for connections
- **Node2 (Dialer)**: Starts after Node1, dials Node1 using a configurable address (default: `127.0.0.1:9092` locally, `172.16.16.16:9092` in Docker)

After connection, both nodes automatically:
1. Exchange identify information via the Identify protocol
2. Discover each other's listening addresses dynamically
3. Learn about each other's supported protocols and capabilities
4. Ping each other to verify connectivity

## Step-by-Step Instructions

### Step 1: Update Dependencies

Ensure your `package.json` includes the identify package:

```json
{
  "dependencies": {
    "@libp2p/identify": "^4.0.7",
    "libp2p": "^3.1.0"
  }
}
```

### Step 2: Add Identify Import

Add the `identify` import to your existing imports:

```javascript
import { identify } from '@libp2p/identify';
```

### Step 3: Set Up Identify String Constants

When you use identify there are two strings you must configure it with. One is the protocol version and the other is the agent identification string. It is typically a good idea to setup constant values for these so that you can reference them in multiple places and be certain that the values are the same everywhere. Let's define the constants at the top of your file:

```javascript
const IDENTIFY_PROTOCOL_VERSION = '/ipfs/id/1.0.0';
const AGENT_VERSION = 'universal-connectivity/0.1.0';
```

### Step 4: Configure Identify in Your libp2p Node

When creating your libp2p node, add the identify service:

```javascript
const node = await createLibp2p({
  // ... other configuration ...
  services: {
    ping: ping({
      protocolPrefix: 'ipfs',
      pingInterval: 1000,
      timeout: 5000
    }),
    identify: identify({
      protocolPrefix: 'ipfs',
      agentVersion: AGENT_VERSION
    })
  }
});
```

### Step 5: Handle Identify Events

The Identify protocol automatically runs when peers connect. Add event handlers to process the identify exchange:

```javascript
// Handle peer connection events
node.addEventListener('peer:connect', (event) => {
  const peerId = event.detail.toString();
  console.log(`[IDENTIFY] Node: Incoming connection from ${peerId}`);
});

// Handle identify events - this fires automatically after connection
node.addEventListener('peer:identify', async (event) => {
  const { detail } = event;
  const peerId = detail.peerId.toString();
  const protocols = detail.protocols || [];
  const listenAddrs = detail.listenAddrs || [];
  
  console.log(`[IDENTIFY] Node: Identified peer ${peerId}`);
  console.log(`[IDENTIFY] Node: Peer agent: ${detail.agentVersion || AGENT_VERSION}`);
  console.log(`[IDENTIFY] Node: Peer supports ${protocols.length} protocols`);
  console.log(`[IDENTIFY] Node: Protocols: ${protocols.join(', ')}`);
  
  // Dynamically discovered listening addresses
  console.log(`[IDENTIFY] Node: Peer's dynamically discovered listening addresses (${listenAddrs.length}):`);
  listenAddrs.forEach((addr, i) => {
    console.log(`[IDENTIFY] Node:   ${i + 1}. ${addr.toString()}`);
  });
  
  // Ping the peer after identify exchange
  console.log(`[PING] Node: Pinging ${peerId}...`);
  try {
    const rtt = await node.services.ping.ping(detail.peerId);
    console.log(`[PING] Node: Ping to ${peerId} successful, RTT: ${rtt} ms`);
  } catch (err) {
    console.log(`[PING] Node: Ping to ${peerId} failed: ${err.message}`);
  }
});

// Handle peer disconnect events
node.addEventListener('peer:disconnect', (event) => {
  const peerId = event.detail.toString();
  console.log(`[IDENTIFY] Node: Connection to ${peerId} closed`);
});
```

### Step 6: Implement Node2 (Dialer)

For Node2, dial Node1 using a configurable address. The address can be set via the `NODE1_ADDR` environment variable:

```javascript
// Dial Node1 using configurable address
const node1NetworkAddr = process.env.NODE1_ADDR || '/ip4/127.0.0.1/tcp/9092';
const node1Addr = multiaddr(node1NetworkAddr);

console.log(`[IDENTIFY] Node2: Dialing Node1 at ${node1Addr.toString()}...`);
const conn = await node.dial(node1Addr);
const node1Peer = conn.remotePeer;
console.log(`[IDENTIFY] Node2: Connected to Node1 (Peer ID: ${node1Peer.toString()})`);

// Identify protocol runs automatically on connection open
// Wait for identify exchange to complete
console.log('[IDENTIFY] Node2: Waiting for identify exchange...');
// The peer:identify event handler above will process the exchange
```

## Testing Your Implementation

1. Set the environment variables:
   ```bash
   export PROJECT_ROOT=/path/to/workshop
   export LESSON_PATH=en/js/05-identify-protocol
   export CHECKER_KEY_PATH=/path/to/checker.key
   ```

2. Change into the lesson directory:
   ```bash
   cd $PROJECT_ROOT/$LESSON_PATH
   ```

3. Run with Docker Compose:
   ```bash
   docker compose up --build
   ```

4. Check your output:
   ```bash
   python3 check.py
   ```

## Success Criteria

Your implementation should:
- ✅ Node1 starts and listens on port 9092
- ✅ Node2 starts and dials Node1 using configurable address
- ✅ Both nodes establish connection successfully
- ✅ Identify protocol exchange completes automatically (bidirectional)
- ✅ Both nodes discover each other's listening addresses dynamically via Identify
- ✅ Both nodes learn about each other's supported protocols and capabilities
- ✅ Both nodes ping each other successfully after identify exchange
- ✅ Display peer protocol version, agent string, and discovered addresses

## Key Implementation Details

### Dynamic Address Discovery

One of the key features demonstrated in this lesson is **dynamic address discovery via the Identify protocol**. Instead of hardcoding addresses or using files, peers exchange their listening addresses automatically:

- When Node2 connects to Node1, both nodes automatically exchange identify information
- The Identify protocol includes each node's listening addresses in `detail.listenAddrs`
- Both nodes learn about each other's full set of addresses dynamically
- This is how real libp2p networks work - addresses are discovered through the protocol itself

### Configurable Connection Address

Node2 uses the `NODE1_ADDR` environment variable to dial Node1:
- **Locally**: Defaults to `/ip4/127.0.0.1/tcp/9092`
- **In Docker**: Set via docker-compose to `/ip4/172.16.16.16/tcp/9092`

This allows the same code to work in both local development and Docker environments.

### Bidirectional Identify Exchange

The Identify protocol runs automatically when peers connect, and it's bidirectional:
1. Node2 dials Node1 → Connection opens
2. Identify protocol runs automatically on both sides
3. Node1 learns Node2's capabilities and addresses
4. Node2 learns Node1's capabilities and addresses
5. Both nodes can then use this information for further communication

See `app/node1.js` and `app/node2.js` for the complete implementation.

## What's Next?

Congratulations! You've reached your second checkpoint 🎉

You now have a libp2p node that can:
- Support multiple transports (TCP)
- Measure connectivity with ping
- Exchange peer capabilities with identify

Key concepts you've learned:
- **Identify Protocol**: Exchanging peer capabilities and metadata
- **Protocol Negotiation**: How peers learn about each other's supported protocols
- **Agent Strings**: Identifying software versions in the network
- **Capability Discovery**: Building adaptive peer-to-peer networks

In the next lesson, you'll implement Gossipsub for publish-subscribe messaging, allowing peers to communicate through topic-based channels!