# Lesson 6: Gossipsub Pub/Sub

Welcome to Lesson 6! In this lesson, you'll implement a real-time group chat using libp2p's Gossipsub pub/sub protocol. This is a powerful feature that enables decentralized messaging and broadcasting.

---

## Objective
- Set up libp2p nodes with Gossipsub pub/sub service
- Join a topic and subscribe to messages
- Send and receive messages in real-time
- Handle pub/sub events and message broadcasting

---

## Background: What is Gossipsub?

Gossipsub is a pub/sub protocol that allows peers to:
- **Publish** messages to topics
- **Subscribe** to topics to receive messages
- **Broadcast** messages to all subscribers in a topic
- **Scale** efficiently with network size

Think of it like a decentralized chat room where anyone can join, send messages, and receive messages from all other participants.

---

## Step-by-Step Instructions

### 1. Install Dependencies

In the `app/` directory, ensure you have the following dependencies:

```json
{
  "dependencies": {
    "libp2p": "^0.46.7",
    "@chainsafe/libp2p-gossipsub": "^14.1.1",
    "@libp2p/tcp": "^8.0.6",
    "@libp2p/websockets": "^9.2.17",
    "@chainsafe/libp2p-noise": "^10.0.0",
    "@chainsafe/libp2p-yamux": "^7.0.0",
    "@libp2p/identify": "^3.0.37",
    "uint8arrays": "^5.1.0"
  }
}
```

Install them with:
```sh
npm install
```

---

### 2. Create Your Gossipsub Chat Node

The `chat-node.js` file is already created in the `app/` directory with the following features:

- **Interactive chat interface** with commands
- **Automatic topic subscription** to `gossipsub-chat`
- **Message broadcasting** to all connected peers
- **Peer connection management**
- **Helpful error messages** and instructions

---

### 3. Run Multiple Chat Nodes (Required!)

**Important:** Gossipsub requires at least 2 nodes to exchange messages. A single node cannot send messages to itself.

#### **Step 1: Start the first chat node**
```sh
node chat-node.js
```

You'll see output like:
```
Chat node started with Peer ID: 12D3KooWMCGQB7LABcJgRRaFdfyR5FhdPDR7Zs6XKggoVaT5vKya
Listening on: /ip4/127.0.0.1/tcp/49401/p2p/12D3KooWMCGQB7LABcJgRRaFdfyR5FhdPDR7Zs6XKggoVaT5vKya
Subscribed to topic: gossipsub-chat

💡 To connect to another chat node, run:
   node chat-node.js <multiaddr>
   Example: node chat-node.js /ip4/127.0.0.1/tcp/49401/p2p/12D3KooW...

=== Gossipsub Chat ===
Type your message and press Enter to send:
(Type "quit" to exit)
(Type "peers" to see connected peers)
(Type "help" for instructions)
```

#### **Step 2: Start a second chat node**
In a **new terminal**, run:
```sh
node chat-node.js /ip4/127.0.0.1/tcp/49401/p2p/12D3KooWMCGQB7LABcJgRRaFdfyR5FhdPDR7Zs6XKggoVaT5vKya
```

Replace the multiaddr with the one from your first node.

#### **Step 3: Test the chat**
- Type messages in either terminal
- See them appear in the other terminal
- Use `peers` command to see connected peers
- Use `help` command for instructions

---

### 4. Chat Commands

The chat interface supports several commands:

- **Any message**: Sends the message to all connected peers
- **`peers`**: Shows all connected peer IDs
- **`help`**: Displays help and instructions
- **`quit`**: Exits the chat node

---

### 5. Expected Output

**Node 1:**
```
Chat node started with Peer ID: 12D3KooW...
Listening on: /ip4/127.0.0.1/tcp/49401/p2p/12D3KooW...
Subscribed to topic: gossipsub-chat

=== Gossipsub Chat ===
Type your message and press Enter to send:
(Type "quit" to exit)
(Type "peers" to see connected peers)
(Type "help" for instructions)

Hello from Node 1!
Message sent: "Hello from Node 1!"
MESSAGE RECEIVED from 12D3KooW...: "Hello from Node 2!" on topic gossipsub-chat
```

**Node 2:**
```
Chat node started with Peer ID: 12D3KooW...
Listening on: /ip4/127.0.0.1/tcp/49402/p2p/12D3KooW...
Subscribed to topic: gossipsub-chat
Connected to remote peer: /ip4/127.0.0.1/tcp/49401/p2p/12D3KooW...

=== Gossipsub Chat ===
Type your message and press Enter to send:
(Type "quit" to exit)
(Type "peers" to see connected peers)
(Type "help" for instructions)

MESSAGE RECEIVED from 12D3KooW...: "Hello from Node 1!" on topic gossipsub-chat
Hello from Node 2!
Message sent: "Hello from Node 2!"
```

---

## How It Works

### **1. Gossipsub Service**
- `gossipsub()` creates a pub/sub service that handles message routing
- Messages are automatically broadcast to all subscribers of a topic

### **2. Topic Subscription**
- `node.services.pubsub.subscribe(TOPIC)` joins the chat topic
- All nodes subscribing to the same topic form a chat room

### **3. Message Publishing**
- `node.services.pubsub.publish(TOPIC, data)` sends a message to all subscribers
- Messages are automatically encoded/decoded using `uint8arrays`

### **4. Message Reception**
- The `message` event fires when a message is received
- `evt.detail.data` contains the message content
- `evt.detail.from` contains the sender's Peer ID

---

## Troubleshooting & Common Issues

### **"NoPeersSubscribedToTopic" Error**
This error occurs when you try to send a message but no other peers are subscribed to the topic.

**Solution:**
1. Start a second chat node
2. Connect it to the first node using the multiaddr
3. Both nodes must be subscribed to the same topic

### **Messages Not Appearing**
- Ensure both nodes are connected (use `peers` command)
- Verify both nodes are subscribed to `gossipsub-chat` topic
- Check that the multiaddr is correct when connecting

### **Connection Issues**
- Use the exact multiaddr format: `/ip4/127.0.0.1/tcp/PORT/p2p/PEERID`
- Make sure the first node is running before starting the second
- Try using `127.0.0.1` instead of other IP addresses for local testing

---

## Advanced Features

### **Multiple Topics**
```js
// Subscribe to multiple topics
await node.services.pubsub.subscribe('general-chat')
await node.services.pubsub.subscribe('tech-discussion')

// Publish to specific topics
await node.services.pubsub.publish('general-chat', uint8ArrayFromString('Hello!'))
await node.services.pubsub.publish('tech-discussion', uint8ArrayFromString('libp2p is awesome!'))
```

### **Message Filtering**
```js
node.services.pubsub.addEventListener('message', (evt) => {
  if (evt.detail.topic === 'important-announcements') {
    console.log('IMPORTANT:', uint8ArrayToString(evt.detail.data))
  }
})
```

---

## Hints

<details>
<summary>Hint 1: How do I add Gossipsub to my node?</summary>
Add `pubsub: gossipsub()` to the `services` property in your libp2p config.
</details>

<details>
<summary>Hint 2: How do I subscribe to a topic?</summary>
Use `await node.services.pubsub.subscribe('topic-name')` to join a topic.
</details>

<details>
<summary>Hint 3: How do I send a message?</summary>
Use `await node.services.pubsub.publish('topic-name', uint8ArrayFromString('message'))`.
</details>

<details>
<summary>Hint 4: How do I receive messages?</summary>
Listen for the `message` event on `node.services.pubsub` and extract data from `evt.detail`.
</details>

<details>
<summary>Hint 5: Why do I get "NoPeersSubscribedToTopic"?</summary>
You need at least 2 nodes connected and subscribed to the same topic. Start another chat node and connect them!
</details>

---

## Resources
- [js-libp2p Gossipsub Documentation](https://libp2p.github.io/js-libp2p/modules/_chainsafe_libp2p_gossipsub.html)
- [Gossipsub Protocol Specification](https://github.com/libp2p/specs/blob/master/pubsub/gossipsub/README.md)
- [js-libp2p Getting Started](https://docs.libp2p.io/guides/getting-started/javascript)

---

## Next Steps
- Try running multiple nodes to test scalability
- Experiment with different topics and message types
- Explore Gossipsub configuration options for performance tuning 