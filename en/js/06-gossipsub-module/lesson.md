# Lesson 6: GossipSub Pub/Sub (Checkpoint 3)

Welcome to Checkpoint 3! In this lesson, you'll implement GossipSub, libp2p's publish-subscribe protocol that enables topic-based messaging across peer-to-peer networks. You'll learn how to create decentralized messaging systems that can scale to thousands of peers.

## Learning Objectives

By the end of this lesson, you will:
- Understand publish-subscribe messaging patterns
- Implement GossipSub for topic-based communication  
- Subscribe to and publish messages on specific topics
- Handle peer discovery and mesh formation in GossipSub networks
- Build both programmatic and interactive chat applications

---

## Background: GossipSub Protocol

GossipSub is libp2p's scalable publish-subscribe protocol that enables:

- **Topic-Based Messaging**: Peers can subscribe to specific topics of interest
- **Efficient Distribution**: Messages are efficiently routed through the network using a mesh overlay
- **Scalability**: Works well with large numbers of peers and topics (used by Ethereum 2.0)
- **Fault Tolerance**: Resilient to peer failures and network partitions
- **Gossip Propagation**: Uses gossip protocol for reliable message delivery

### How GossipSub Works

1. **Mesh Formation**: Peers form a mesh topology for each topic they're subscribed to
2. **Message Publishing**: When a peer publishes a message, it sends it to all mesh peers for that topic
3. **Message Forwarding**: Mesh peers forward the message to their mesh peers, creating redundancy
4. **Gossip Layer**: Peers also maintain a gossip layer for additional message propagation
5. **Pruning/Grafting**: The mesh topology adapts dynamically as peers join/leave

This creates a robust, scalable system for decentralized messaging.

---

## Your Task

Building on your identify implementation from Lesson 5, you need to:

1. **Add GossipSub Service**: Include GossipSub in your libp2p node configuration
2. **Configure Topics**: Subscribe to Universal Connectivity topics
3. **Implement Message Publishing**: Send messages to topics
4. **Handle GossipSub Events**: Process incoming messages and subscription events

## Step-by-Step Instructions

### Step 1: Review the Implementation

The implementation is provided for you in `app/index.js`. It demonstrates:

- Setting up a libp2p node with GossipSub service
- Subscribing to a topic (`universal-connectivity`)
- Publishing a message to the topic
- Handling incoming messages and subscription events

### Step 2: Understanding GossipSub Configuration

```javascript
import { gossipsub } from '@chainsafe/libp2p-gossipsub'

const node = await createLibp2p({
  // ... other config
  services: {
    pubsub: gossipsub({
      emitSelf: false,  // Don't receive our own messages
      allowPublishToZeroPeers: true,  // Allow publishing when no peers
      messageProcessingConcurrency: 10  // Process up to 10 messages concurrently
    }),
    identify: identify()  // Still need identify for peer discovery
  }
})
```

Key configuration options:
- `emitSelf: false` - Prevents receiving your own published messages
- `allowPublishToZeroPeers: true` - Allows publishing even when no peers are subscribed
- `messageProcessingConcurrency` - Controls concurrent message processing

### Step 3: Topic Subscription and Event Handling

```javascript
const TOPIC = 'universal-connectivity'

// Set up message listener
node.services.pubsub.addEventListener('message', (evt) => {
  const message = uint8ArrayToString(evt.detail.data)
  const fromPeer = evt.detail.from.toString()
  console.log(`Received message from ${fromPeer}: "${message}" on topic ${evt.detail.topic}`)
})

// Subscribe to topic
await node.services.pubsub.subscribe(TOPIC)
console.log(`Subscribed to topic: ${TOPIC}`)
```

### Step 4: Publishing Messages

```javascript
import { fromString as uint8ArrayFromString } from 'uint8arrays/from-string'

const message = `Hello from ${node.peerId.toString()}`
await node.services.pubsub.publish(TOPIC, uint8ArrayFromString(message))
```

### Step 5: Testing the Implementation

**Run the basic implementation:**
```bash
cd app
npm install
node index.js
```

**Test interactive chat (optional):**
```bash
node chat-node.js
```

**To test with Workshop Tool**: Press `c` to check your solution.

---

## Expected Output

When you run the application, you should see:

```
Starting GossipSub Universal Connectivity Lesson...
Node started with Peer ID: 12D3KooW...
Listening on: /ip4/0.0.0.0/tcp/...
No remote peer specified - running in standalone mode
Setting up GossipSub messaging...
Subscribed to topic: universal-connectivity
Published message: "Hello from 12D3KooW... at 2024-..."
GossipSub demonstration complete!
Key achievements:
✓ Created libp2p node with GossipSub service
✓ Subscribed to pub/sub topic
✓ Published message to topic
✓ Set up message and subscription event handling
```

---

## Interactive Chat Testing

You can also test the interactive chat application:

```bash
node chat-node.js
```

This provides a real-time chat interface where you can:
- Type messages to send to the topic
- See messages from other connected peers
- Use `peers` to see connected peers
- Use `quit` to exit

**Connecting multiple nodes:**
```bash
# Terminal 1 - Start first node
node chat-node.js

# Terminal 2 - Connect second node to first
node chat-node.js /ip4/127.0.0.1/tcp/PORT/p2p/PEER_ID
```

---

## Key Concepts Learned

1. **Publish-Subscribe Pattern**: Topic-based messaging where publishers send to topics and subscribers receive from topics they're interested in

2. **GossipSub Mesh**: Peers form efficient mesh topologies for reliable message distribution

3. **Event-Driven Architecture**: Handle messages and subscription changes through event listeners

4. **Peer Discovery**: GossipSub works with the identify protocol for peer capability discovery

5. **Decentralized Communication**: No central server needed - peers communicate directly

---

## Troubleshooting

**Issue**: "NoPeersSubscribedToTopic" error
- **Solution**: This is normal when running standalone. The message is still published to the network.

**Issue**: No messages received
- **Solution**: Ensure multiple nodes are connected and subscribed to the same topic.

**Issue**: Connection failures
- **Solution**: Check that multiaddresses are correct and peers are reachable.

---

## Advanced Concepts

- **Topic Mesh Management**: GossipSub maintains optimal mesh connections per topic
- **Message Validation**: Custom message validators for secure applications
- **Peer Scoring**: GossipSub includes peer reputation systems
- **Flood Protection**: Built-in protection against message flooding attacks

---

## Hints

💡 **Multiple Peers**: For interesting behavior, run multiple instances and connect them
💡 **Real-time Chat**: The chat-node.js demonstrates interactive GossipSub usage
💡 **Topic Design**: In production, use meaningful topic names like "chat-room-general"
💡 **Message Format**: Consider JSON for structured messages in real applications

---

## Resources

- [libp2p GossipSub Specification](https://github.com/libp2p/specs/blob/master/pubsub/gossipsub/README.md)
- [GossipSub in Ethereum 2.0](https://eth2.news/2020/01/24/gossipsub-scaling-p2p-messaging-for-eth-20/)
- [js-libp2p-gossipsub Documentation](https://github.com/ChainSafe/js-libp2p-gossipsub)
- [libp2p Examples Repository](https://github.com/libp2p/js-libp2p-examples)

---

This lesson is part of the JavaScript libp2p workshop series.