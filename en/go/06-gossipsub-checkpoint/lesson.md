# Lesson 6: GossipSub Pub/Sub Checkpoint

Welcome to one of libp2p's most powerful features! In this lesson, you'll implement GossipSub, a publish-subscribe messaging system that enables efficient topic-based communication across peer-to-peer networks.

## Learning Objectives

By the end of this lesson, you will:
- Understand pub/sub messaging patterns
- Implement GossipSub for topic-based communication
- Join topics and manage subscriptions
- Publish and receive messages
- Handle message routing and validation
- Build a simple chat application over P2P

## Background: Publish-Subscribe Pattern

**Pub/Sub** is a messaging pattern where:
- **Publishers** send messages to **topics**
- **Subscribers** receive messages from topics they're interested in
- Publishers and subscribers are decoupled (don't know about each other)

### Traditional vs P2P Pub/Sub

| Traditional (Centralized) | P2P (GossipSub) |
|---------------------------|-----------------|
| Central message broker | Distributed routing |
| Single point of failure | No single point of failure |
| Limited scalability | Scales with network |
| Broker owns data | End-to-end encryption possible |
| Simple routing | Complex but resilient |

## GossipSub Overview

**GossipSub** is libp2p's flagship pub/sub protocol. It combines:
- **Mesh Networks**: Small, well-connected groups per topic
- **Gossip Protocol**: Efficient message propagation
- **Flood Publishing**: Reliable delivery within mesh
- **Peer Exchange**: Dynamic mesh maintenance

### How GossipSub Works

```
Topic: "chat"

Peer A ←→ Peer B ←→ Peer C
  ↕         ↕         ↕
Peer D ←→ Peer E ←→ Peer F

1. Peers join topic, form mesh
2. Publisher floods message to mesh neighbors
3. Mesh peers relay to their neighbors
4. All subscribers receive message
5. Gossip metadata keeps mesh healthy
```

### Key Concepts

**Topic**: Named channel for messages
- Example: `"chat"`, `"blockchain-blocks"`, `"sensor-data"`

**Mesh**: Set of peers you maintain full connections with
- Typical size: 6-12 peers per topic
- Trade-off: bandwidth vs redundancy

**Fanout**: Temporary connections for publishing without subscribing

**Gossip**: Metadata exchanges to maintain mesh health
- "I have these messages"
- "I want these messages"
- "Join my mesh"

## Your Task

Build a simple P2P chat application:
1. Create GossipSub instance
2. Join a chat topic
3. Subscribe to receive messages
4. Publish messages periodically
5. Display received messages
6. Handle concurrent publishing and receiving

## Step-by-Step Instructions

### Step 1: Add GossipSub Import

Update your imports in `app/main.go`:

```go
package main

import (
    "bufio"
    "context"
    "fmt"
    "log"
    "os"
    "os/signal"
    "strings"
    "syscall"
    "time"

    "github.com/libp2p/go-libp2p"
    "github.com/libp2p/go-libp2p/core/crypto"
    "github.com/libp2p/go-libp2p/core/host"
    "github.com/libp2p/go-libp2p/core/peer"
    pubsub "github.com/libp2p/go-libp2p-pubsub"
    "github.com/multiformats/go-multiaddr"
)
```

**What's new?**

- `pubsub "github.com/libp2p/go-libp2p-pubsub"`: GossipSub implementation
  - Aliased as `pubsub` for convenience
- `bufio`: For reading user input (optional, for interactive chat)

### Step 2: Create GossipSub Instance

After creating your host, initialize GossipSub:

```go
func main() {
    fmt.Println("Starting Universal Connectivity Application...")

    // Generate keypair
    priv, _, err := crypto.GenerateKeyPair(crypto.Ed25519, -1)
    if err != nil {
        log.Fatalf("Failed to generate keypair: %v", err)
    }

    // Create context
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    // Create host
    h, err := libp2p.New(
        libp2p.Identity(priv),
        libp2p.ListenAddrStrings(
            "/ip4/0.0.0.0/tcp/0",
            "/ip4/0.0.0.0/udp/0/quic-v1",
        ),
        libp2p.UserAgent("universal-connectivity-app/1.0.0"),
    )
    if err != nil {
        log.Fatalf("Failed to create host: %v", err)
    }
    defer h.Close()

    fmt.Printf("Local peer id: %s\n", h.ID())

    // Print listening addresses
    fmt.Println("Listening on:")
    for _, addr := range h.Addrs() {
        fmt.Printf("  %s/p2p/%s\n", addr, h.ID())
    }

    // Create GossipSub instance
    ps, err := pubsub.NewGossipSub(ctx, h)
    if err != nil {
        log.Fatalf("Failed to create GossipSub: %v", err)
    }
    fmt.Println("GossipSub service created")

    // Rest of code...
}
```

**What's happening here?**

- `pubsub.NewGossipSub(ctx, h)`: Creates GossipSub instance
  - Requires context for lifecycle management
  - Attaches to your host
  - Registers GossipSub protocol handlers
  - Starts background mesh maintenance
- **Default Configuration**: Uses sensible defaults
  - Mesh size: 6-12 peers
  - Heartbeat interval: 1 second
  - Message caching: enabled

### Step 3: Connect to Peers

Add connection code (similar to previous lessons):

```go
func main() {
    // ... (previous code) ...

    // Parse remote peers
    remotePeersStr := os.Getenv("REMOTE_PEERS")
    if remotePeersStr == "" {
        fmt.Println("No REMOTE_PEERS specified. Running in standalone mode.")
        fmt.Println("Export REMOTE_PEERS to connect to other peers.")
    }

    if remotePeersStr != "" {
        peerAddrs := strings.Split(remotePeersStr, ",")
        for _, addrStr := range peerAddrs {
            addrStr = strings.TrimSpace(addrStr)
            if addrStr == "" {
                continue
            }

            addr, err := multiaddr.NewMultiaddr(addrStr)
            if err != nil {
                log.Printf("Invalid multiaddr %s: %v", addrStr, err)
                continue
            }

            peerInfo, err := peer.AddrInfoFromP2pAddr(addr)
            if err != nil {
                log.Printf("Invalid peer address %s: %v", addr, err)
                continue
            }

            fmt.Printf("Dialing peer %s...\n", peerInfo.ID)

            connCtx, connCancel := context.WithTimeout(ctx, 30*time.Second)
            err = h.Connect(connCtx, *peerInfo)
            connCancel()

            if err != nil {
                log.Printf("Failed to connect to %s: %v", peerInfo.ID, err)
            } else {
                fmt.Printf("Connected to: %s\n", peerInfo.ID)
            }
        }
    }

    // Continue even if no peers connected (can still publish locally)

    // Rest of code...
}
```

**Note**: Unlike previous lessons, we don't require peer connections. GossipSub works standalone too!

### Step 4: Join a Topic and Subscribe

Add topic joining and subscription:

```go
func main() {
    // ... (previous code: GossipSub creation and peer connections) ...

    // Join a topic
    topicName := "universal-connectivity-chat"
    topic, err := ps.Join(topicName)
    if err != nil {
        log.Fatalf("Failed to join topic: %v", err)
    }
    defer topic.Close()
    fmt.Printf("Joined topic: %s\n", topicName)

    // Subscribe to the topic
    sub, err := topic.Subscribe()
    if err != nil {
        log.Fatalf("Failed to subscribe to topic: %v", err)
    }
    defer sub.Cancel()
    fmt.Println("Subscribed to topic")

    // Rest of code...
}
```

**What's happening here?**

- `ps.Join(topicName)`: Joins a topic
  - Creates or joins existing topic
  - Returns a `Topic` handle for operations
  - Begins mesh formation with other topic members
- `topic.Subscribe()`: Creates subscription to receive messages
  - Returns a `Subscription` handle
  - Starts receiving messages from the topic
  - You can have multiple subscriptions per topic
- **defer Close/Cancel**: Proper cleanup when done

**Topic Names**: Can be any string. Peers must use exact same name to communicate.

### Step 5: Publish Messages

Add a goroutine to publish messages periodically:

```go
func main() {
    // ... (previous code: topic subscription) ...

    // Start publishing messages
    go func() {
        ticker := time.NewTicker(5 * time.Second)
        defer ticker.Stop()

        msgCount := 0
        for {
            select {
            case <-ticker.C:
                msgCount++
                msg := fmt.Sprintf("Hello from %s - Message #%d at %s",
                    h.ID().ShortString(),
                    msgCount,
                    time.Now().Format(time.RFC3339),
                )

                if err := topic.Publish(ctx, []byte(msg)); err != nil {
                    log.Printf("Failed to publish: %v", err)
                } else {
                    fmt.Printf("[SENT] %s\n", msg)
                }

            case <-ctx.Done():
                return
            }
        }
    }()

    // Rest of code...
}
```

**What's happening here?**

- **Goroutine**: Publishing runs concurrently with receiving
- `time.NewTicker(5 * time.Second)`: Publishes every 5 seconds
- `topic.Publish(ctx, []byte(msg))`: Publishes message to topic
  - Message is a byte slice
  - Gets flooded to mesh neighbors
  - Propagates across the network
- `select` with `ctx.Done()`: Graceful shutdown

**Message Format**: GossipSub transmits raw bytes. You can use JSON, protobuf, or any serialization format.

### Step 6: Receive Messages

Add a goroutine to receive and display messages:

```go
func main() {
    // ... (previous code: publishing goroutine) ...

    // Start receiving messages
    go func() {
        for {
            msg, err := sub.Next(ctx)
            if err != nil {
                if ctx.Err() != nil {
                    // Context cancelled, normal shutdown
                    return
                }
                log.Printf("Subscription error: %v", err)
                return
            }

            // Skip our own messages
            if msg.ReceivedFrom == h.ID() {
                continue
            }

            fmt.Printf("[RECEIVED] From %s: %s\n",
                msg.ReceivedFrom.ShortString(),
                string(msg.Data),
            )
        }
    }()

    // Keep running
    fmt.Println("\nApplication running. Messages will be published every 5 seconds.")
    fmt.Println("Press Ctrl+C to exit.\n")

    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

    <-sigCh
    fmt.Println("\nShutting down...")
}
```

**What's happening here?**

- `sub.Next(ctx)`: Blocking call that waits for next message
  - Returns `*pubsub.Message` when available
  - Blocks until message arrives or context cancelled
- `msg.ReceivedFrom`: Peer ID of the sender
  - We skip our own messages (they're echoed back)
- `msg.Data`: The actual message payload (bytes)
- **Error Handling**: Check if error is due to shutdown or actual problem

## Complete Solution

Here's the full implementation:

```go
package main

import (
    "context"
    "fmt"
    "log"
    "os"
    "os/signal"
    "strings"
    "syscall"
    "time"

    "github.com/libp2p/go-libp2p"
    "github.com/libp2p/go-libp2p/core/crypto"
    "github.com/libp2p/go-libp2p/core/peer"
    pubsub "github.com/libp2p/go-libp2p-pubsub"
    "github.com/multiformats/go-multiaddr"
)

func main() {
    fmt.Println("Starting Universal Connectivity Application...")

    // Generate keypair
    priv, _, err := crypto.GenerateKeyPair(crypto.Ed25519, -1)
    if err != nil {
        log.Fatalf("Failed to generate keypair: %v", err)
    }

    // Create context
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    // Create host
    h, err := libp2p.New(
        libp2p.Identity(priv),
        libp2p.ListenAddrStrings(
            "/ip4/0.0.0.0/tcp/0",
            "/ip4/0.0.0.0/udp/0/quic-v1",
        ),
        libp2p.UserAgent("universal-connectivity-app/1.0.0"),
    )
    if err != nil {
        log.Fatalf("Failed to create host: %v", err)
    }
    defer h.Close()

    fmt.Printf("Local peer id: %s\n", h.ID())

    // Print listening addresses
    fmt.Println("Listening on:")
    for _, addr := range h.Addrs() {
        fmt.Printf("  %s/p2p/%s\n", addr, h.ID())
    }

    // Create GossipSub
    ps, err := pubsub.NewGossipSub(ctx, h)
    if err != nil {
        log.Fatalf("Failed to create GossipSub: %v", err)
    }
    fmt.Println("GossipSub service created")

    // Parse and connect to remote peers
    remotePeersStr := os.Getenv("REMOTE_PEERS")
    if remotePeersStr == "" {
        fmt.Println("No REMOTE_PEERS specified. Running in standalone mode.")
    }

    if remotePeersStr != "" {
        peerAddrs := strings.Split(remotePeersStr, ",")
        for _, addrStr := range peerAddrs {
            addrStr = strings.TrimSpace(addrStr)
            if addrStr == "" {
                continue
            }

            addr, err := multiaddr.NewMultiaddr(addrStr)
            if err != nil {
                log.Printf("Invalid multiaddr %s: %v", addrStr, err)
                continue
            }

            peerInfo, err := peer.AddrInfoFromP2pAddr(addr)
            if err != nil {
                log.Printf("Invalid peer address %s: %v", addr, err)
                continue
            }

            fmt.Printf("Dialing peer %s...\n", peerInfo.ID)

            connCtx, connCancel := context.WithTimeout(ctx, 30*time.Second)
            err = h.Connect(connCtx, *peerInfo)
            connCancel()

            if err != nil {
                log.Printf("Failed to connect to %s: %v", peerInfo.ID, err)
            } else {
                fmt.Printf("Connected to: %s\n", peerInfo.ID)
            }
        }
    }

    // Join topic
    topicName := "universal-connectivity-chat"
    topic, err := ps.Join(topicName)
    if err != nil {
        log.Fatalf("Failed to join topic: %v", err)
    }
    defer topic.Close()
    fmt.Printf("Joined topic: %s\n", topicName)

    // Subscribe
    sub, err := topic.Subscribe()
    if err != nil {
        log.Fatalf("Failed to subscribe to topic: %v", err)
    }
    defer sub.Cancel()
    fmt.Println("Subscribed to topic")

    // Publish messages
    go func() {
        ticker := time.NewTicker(5 * time.Second)
        defer ticker.Stop()

        msgCount := 0
        for {
            select {
            case <-ticker.C:
                msgCount++
                msg := fmt.Sprintf("Hello from %s - Message #%d at %s",
                    h.ID().ShortString(),
                    msgCount,
                    time.Now().Format(time.RFC3339),
                )

                if err := topic.Publish(ctx, []byte(msg)); err != nil {
                    log.Printf("Failed to publish: %v", err)
                } else {
                    fmt.Printf("[SENT] %s\n", msg)
                }

            case <-ctx.Done():
                return
            }
        }
    }()

    // Receive messages
    go func() {
        for {
            msg, err := sub.Next(ctx)
            if err != nil {
                if ctx.Err() != nil {
                    return
                }
                log.Printf("Subscription error: %v", err)
                return
            }

            // Skip our own messages
            if msg.ReceivedFrom == h.ID() {
                continue
            }

            fmt.Printf("[RECEIVED] From %s: %s\n",
                msg.ReceivedFrom.ShortString(),
                string(msg.Data),
            )
        }
    }()

    // Keep running
    fmt.Println("\nApplication running. Messages will be published every 5 seconds.")
    fmt.Println("Press Ctrl+C to exit.\n")

    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

    <-sigCh
    fmt.Println("\nShutting down...")
}
```

## Testing Your Implementation

### Single Instance Test

```bash
cd en/go/06-gossipsub-checkpoint
go run app/main.go
```

Expected output:
```
Starting Universal Connectivity Application...
Local peer id: 12D3KooW...
Listening on:
  /ip4/127.0.0.1/tcp/54321/p2p/12D3KooW...
  /ip4/127.0.0.1/udp/54322/quic-v1/p2p/12D3KooW...
GossipSub service created
No REMOTE_PEERS specified. Running in standalone mode.
Joined topic: universal-connectivity-chat
Subscribed to topic

Application running. Messages will be published every 5 seconds.
Press Ctrl+C to exit.

[SENT] Hello from 12D3KooW... - Message #1 at 2026-01-14T10:30:00Z
[SENT] Hello from 12D3KooW... - Message #2 at 2026-01-14T10:30:05Z
```

### Multi-Instance Test (Real P2P Chat!)

#### Terminal 1:
```bash
go run app/main.go
```

Note one of the listening addresses.

#### Terminal 2:
```bash
export REMOTE_PEERS="<address from Terminal 1>"
go run app/main.go
```

Both terminals should show:
- Their own sent messages: `[SENT] ...`
- Received messages from the other peer: `[RECEIVED] From ... ...`

**This is real P2P chat!**

### Three+ Instances

Try running 3-5 instances! Each can connect to any other, and messages propagate across the mesh.

### Automated Testing

```bash
python check.py
```

### Docker Testing

```bash
cd en/go/06-gossipsub-checkpoint
export PROJECT_ROOT=$(pwd)/../../..
export LESSON_PATH=en/go/06-gossipsub-checkpoint

docker compose up --build
python check.py
```

## Success Criteria

Your implementation should:
- ✅ Create GossipSub instance
- ✅ Join a topic successfully
- ✅ Subscribe to receive messages
- ✅ Publish messages periodically
- ✅ Receive and display messages from peers
- ✅ Handle concurrent publishing/receiving

## Troubleshooting

<details>
<summary>Messages Not Reaching Peers</summary>

**Symptom**: Publishing works, but other peers don't receive messages

**Causes**:
1. Not connected to any peers
2. Peers joined different topics (typo in name)
3. Network partition
4. Firewall blocking connections

**Solutions**:
- Verify peers are connected: check "Connected to:" messages
- Ensure exact same topic name (case-sensitive!)
- Test locally first (localhost addresses)
- Check both peers joined same topic
- Wait a few seconds after connection for mesh to form
</details>

<details>
<summary>Receiving Own Messages</summary>

**Symptom**: See "[RECEIVED]" for your own sent messages

**Causes**:
1. Forgot to filter own messages
2. Logic error in filter

**Solutions**:
- Add check: `if msg.ReceivedFrom == h.ID() { continue }`
- Verify peer ID comparison is correct
- This is normal GossipSub behavior (you receive your own messages)
</details>

<details>
<summary>Subscription Error</summary>

**Symptom**: "Subscription error" logged

**Causes**:
1. Topic closed before subscription
2. Context cancelled
3. Subscription cancelled

**Solutions**:
- Ensure topic.Subscribe() called before topic.Close()
- Check context isn't cancelled prematurely
- Don't defer sub.Cancel() if you need long-running subscription
- Proper error checking in receive loop
</details>

<details>
<summary>High Memory Usage</summary>

**Symptom**: Memory grows over time

**Causes**:
1. Message cache not bounded
2. Too many subscriptions
3. Large messages published frequently

**Solutions**:
- Configure cache size: use GossipSub options
- Cancel unused subscriptions
- Limit message size and frequency
- Monitor with `ps.GetTopics()` and `topic.ListPeers()`
</details>

## Hints

<details>
<summary>Hint: GossipSub Configuration</summary>

Customize GossipSub behavior with options:

```go
ps, err := pubsub.NewGossipSub(
    ctx,
    h,
    pubsub.WithMessageSigning(true),      // Sign messages with peer key
    pubsub.WithStrictSignatureVerification(true),  // Verify signatures
    pubsub.WithMaxMessageSize(1024 * 1024),  // Max 1MB messages
    pubsub.WithHeartbeatInterval(time.Second),  // Heartbeat frequency
)
```

**Useful options**:
- `WithMessageSigning`: Add cryptographic signatures
- `WithMessageIdFn`: Custom message ID function (deduplication)
- `WithPeerExchange`: Enable peer discovery in topic
- `WithFloodPublish`: Flood to all peers (more redundancy)
</details>

<details>
<summary>Hint: Message Validation</summary>

Add custom message validation:

```go
validator := func(ctx context.Context, peerID peer.ID, msg *pubsub.Message) bool {
    // Example: Reject messages over 1KB
    if len(msg.Data) > 1024 {
        return false
    }

    // Example: Only accept messages from known peers
    if h.Network().Connectedness(peerID) != network.Connected {
        return false
    }

    // Accept message
    return true
}

// Register validator for topic
err := ps.RegisterTopicValidator(topicName, validator)
```

Validators prevent spam and invalid messages from propagating!
</details>

<details>
<summary>Hint: Topic Mesh Inspection</summary>

Inspect the topic mesh:

```go
// Get list of peers in topic
peers := topic.ListPeers()
fmt.Printf("Topic has %d peers:\n", len(peers))
for _, p := range peers {
    fmt.Printf("  - %s\n", p.ShortString())
}

// Get all topics
topics := ps.GetTopics()
fmt.Printf("Subscribed to %d topics: %v\n", len(topics), topics)
```

Useful for debugging mesh formation and peer discovery!
</details>

<details>
<summary>Hint: JSON Messages</summary>

Use structured messages with JSON:

```go
type ChatMessage struct {
    Sender    string    `json:"sender"`
    Text      string    `json:"text"`
    Timestamp time.Time `json:"timestamp"`
}

// Publishing
msg := ChatMessage{
    Sender:    h.ID().ShortString(),
    Text:      "Hello, world!",
    Timestamp: time.Now(),
}
data, _ := json.Marshal(msg)
topic.Publish(ctx, data)

// Receiving
var msg ChatMessage
json.Unmarshal(receivedMsg.Data, &msg)
fmt.Printf("%s: %s\n", msg.Sender, msg.Text)
```

Structured messages are easier to work with!
</details>

## What You've Learned

Congratulations! You've successfully:

- **Implemented GossipSub** pub/sub messaging
- **Created topic-based communication** channels
- **Published messages** to distributed network
- **Received messages** from peers
- **Built a P2P chat application** from scratch
- **Understood mesh networks** and gossip protocols

## Key Concepts

### Pub/Sub Pattern
- **Decoupling**: Publishers don't know subscribers
- **Topic-Based**: Messages organized by topics
- **Scalable**: Add subscribers without changing publishers
- **Flexible**: Multiple topics per application

### GossipSub Mechanics
- **Mesh Formation**: Small, well-connected groups
- **Flood Publishing**: Reliable within mesh
- **Gossip Metadata**: Efficient beyond mesh
- **Peer Exchange**: Dynamic peer discovery

### Message Propagation
- **Immediate**: Messages flood through mesh
- **Efficient**: Gossip prevents redundant sends
- **Reliable**: Multiple paths ensure delivery
- **Fast**: Low latency within mesh

### Use Cases
- **Chat Applications**: Real-time messaging
- **Blockchain**: Block/transaction propagation
- **IoT**: Sensor data distribution
- **Gaming**: Game state synchronization
- **CDN**: Content distribution

## What's Next?

In the final lesson, you'll implement the **Kademlia DHT** (Distributed Hash Table):
- Peer discovery at scale
- Content routing and addressing
- Distributed key-value storage
- Network-wide queries

The DHT is the foundation for truly decentralized applications!

Next up: Lesson 7 - Kademlia DHT Checkpoint (Final Lesson!)

## Additional Resources

- [GossipSub specification](https://github.com/libp2p/specs/blob/master/pubsub/gossipsub/README.md)
- [go-libp2p-pubsub documentation](https://pkg.go.dev/github.com/libp2p/go-libp2p-pubsub)
- [PubSub interface spec](https://github.com/libp2p/specs/tree/master/pubsub)
- [Mesh networks explained](https://docs.libp2p.io/concepts/pubsub/overview/)
