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

### Step 1: Add Required Dependencies

First, update `app/build.gradle.kts` to ensure you have the gossip protocol:

```kotlin
dependencies {
    // jvm-libp2p core library includes gossip
    implementation("io.libp2p:jvm-libp2p:1.1.1-RELEASE")

    // Logging
    implementation("org.slf4j:slf4j-api:2.0.9")
    implementation("org.apache.logging.log4j:log4j-slf4j2-impl:2.20.0")
    implementation("org.apache.logging.log4j:log4j-core:2.20.0")
}
```

### Step 2: Add Required Imports

Update your imports in `app/src/main/kotlin/Main.kt`:

```kotlin
import io.libp2p.core.Host
import io.libp2p.core.PeerId
import io.libp2p.core.crypto.KeyType
import io.libp2p.core.dsl.host
import io.libp2p.core.multiformats.Multiaddr
import io.libp2p.core.mux.StreamMuxerProtocol
import io.libp2p.etc.types.toVoidCompletableFuture
import io.libp2p.protocol.Identify
import io.libp2p.protocol.Ping
import io.libp2p.pubsub.gossip.Gossip
import io.libp2p.security.noise.NoiseXXSecureChannel
import io.libp2p.transport.tcp.TcpTransport
import java.util.concurrent.CompletableFuture
import java.util.concurrent.TimeUnit
import kotlin.concurrent.thread
```

**What's new?**

- `io.libp2p.pubsub.gossip.Gossip`: GossipSub protocol implementation
- `io.libp2p.protocol.Identify`: Identify protocol for peer information
- `io.libp2p.protocol.Ping`: Ping protocol for keepalive
- `kotlin.concurrent.thread`: For concurrent publishing/receiving

### Step 3: Create GossipSub Instance

Create a Gossip protocol instance and add it to your host:

```kotlin
fun main() {
    println("Starting Universal Connectivity Application...")

    // Create Gossip instance
    val gossip = Gossip()

    // Create a libp2p host with TCP transport, security, multiplexing, and gossip
    val node: Host = host {
        identity {
            random(KeyType.ED25519)
        }
        transports {
            +::TcpTransport
        }
        secureChannels {
            +::NoiseXXSecureChannel
        }
        muxers {
            +StreamMuxerProtocol.Mplex
        }
        protocols {
            +Ping()
            +Identify()
            +gossip
        }
        network {
            listen("/ip4/0.0.0.0/tcp/0")
        }
    }

    // Start the host
    node.start().get()

    println("Local peer id: ${node.peerId}")

    // Print listening addresses
    println("Listening on:")
    for (addr in node.listenAddresses()) {
        println("  $addr/p2p/${node.peerId}")
    }

    println("GossipSub service created")

    // Rest of code...
}
```

**What's happening here?**

- `val gossip = Gossip()`: Creates GossipSub instance
- `protocols { +gossip }`: Registers GossipSub with the host
- The host automatically handles GossipSub protocol negotiations
- Gossip starts its background mesh maintenance automatically

### Step 4: Connect to Peers

Add connection code (similar to previous lessons):

```kotlin
fun main() {
    // ... (previous code) ...

    // Parse remote peer addresses from environment variable
    val remotePeersStr = System.getenv("REMOTE_PEERS") ?: ""

    if (remotePeersStr.isEmpty()) {
        println("No REMOTE_PEERS specified. Running in standalone mode.")
        println("Export REMOTE_PEERS to connect to other peers.")
    }

    if (remotePeersStr.isNotEmpty()) {
        val peerAddrs = remotePeersStr.split(",")
        val connectionFutures = mutableListOf<CompletableFuture<Void>>()

        for (addrStr in peerAddrs) {
            val trimmed = addrStr.trim()
            if (trimmed.isEmpty()) continue

            try {
                val addr = Multiaddr(trimmed)
                val peerId = addr.peerId

                if (peerId == null) {
                    println("Multiaddress $addr does not contain peer ID, skipping")
                    continue
                }

                println("Dialing peer $peerId...")

                val connFuture = node.network.connect(addr).toVoidCompletableFuture()
                connectionFutures.add(connFuture)

                connFuture.thenAccept {
                    println("Connected to: $peerId")
                }.exceptionally { err ->
                    println("Failed to connect to $peerId: ${err.message}")
                    null
                }
            } catch (e: Exception) {
                println("Invalid multiaddr $trimmed: ${e.message}")
            }
        }

        // Wait for connections with timeout
        try {
            CompletableFuture.allOf(*connectionFutures.toTypedArray())
                .get(30, TimeUnit.SECONDS)
        } catch (e: Exception) {
            // Connection attempts timed out or failed
        }
    }

    // Continue even if no peers connected (can still publish locally)

    // Rest of code...
}
```

**Note**: Unlike previous lessons, we don't require peer connections. GossipSub works standalone too!

### Step 5: Join a Topic and Subscribe

Add topic joining and subscription:

```kotlin
fun main() {
    // ... (previous code: GossipSub creation and peer connections) ...

    // Get the GossipSub API
    val api = gossip.router

    // Join a topic
    val topicName = "universal-connectivity-chat"
    api.subscribe(topicName)
    println("Joined topic: $topicName")

    // Rest of code...
}
```

**What's happening here?**

- `gossip.router`: Gets the GossipSub API for operations
- `api.subscribe(topicName)`: Joins and subscribes to a topic
  - Creates or joins existing topic
  - Begins mesh formation with other topic members
  - Starts receiving messages from the topic
- **Topic Names**: Can be any string. Peers must use exact same name to communicate.

### Step 6: Publish Messages

Add a thread to publish messages periodically:

```kotlin
fun main() {
    // ... (previous code: topic subscription) ...

    // Start publishing messages in background thread
    val publishThread = thread(start = true) {
        var msgCount = 0

        while (true) {
            try {
                Thread.sleep(5000) // Publish every 5 seconds

                msgCount++
                val msg = "Hello from ${node.peerId.toShortString()} - Message #$msgCount at ${System.currentTimeMillis()}"

                api.publish(topicName, msg.toByteArray())
                println("[SENT] $msg")

            } catch (e: InterruptedException) {
                println("Publishing thread interrupted")
                break
            } catch (e: Exception) {
                println("Failed to publish: ${e.message}")
            }
        }
    }

    // Rest of code...
}
```

**What's happening here?**

- **Thread**: Publishing runs concurrently with receiving
- `Thread.sleep(5000)`: Publishes every 5 seconds
- `api.publish(topicName, data)`: Publishes message to topic
  - Message is a byte array
  - Gets flooded to mesh neighbors
  - Propagates across the network
- **Message Format**: GossipSub transmits raw bytes. You can use JSON, protobuf, or any serialization format.

### Step 7: Receive Messages

Add message receiving with a subscription handler:

```kotlin
fun main() {
    // ... (previous code: publishing thread) ...

    // Subscribe to receive messages
    api.subscribe { msg ->
        // Skip our own messages
        if (msg.from == node.peerId) {
            return@subscribe
        }

        val sender = msg.from.toShortString()
        val text = String(msg.data)
        println("[RECEIVED] From $sender: $text")
    }

    println()
    println("Application running. Messages will be published every 5 seconds.")
    println("Press Ctrl+C to exit.")
    println()

    // Keep running
    Thread.sleep(Long.MAX_VALUE)
}
```

**What's happening here?**

- `api.subscribe { msg -> }`: Sets message handler callback
  - Called for each received message
  - Runs on GossipSub's internal thread pool
- `msg.from`: Peer ID of the sender
  - We skip our own messages (they're echoed back)
- `msg.data`: The actual message payload (bytes)
- **Concurrent Processing**: Handler is called asynchronously

## Complete Solution

Here's the full implementation:

```kotlin
import io.libp2p.core.Host
import io.libp2p.core.crypto.KeyType
import io.libp2p.core.dsl.host
import io.libp2p.core.multiformats.Multiaddr
import io.libp2p.core.mux.StreamMuxerProtocol
import io.libp2p.etc.types.toVoidCompletableFuture
import io.libp2p.protocol.Identify
import io.libp2p.protocol.Ping
import io.libp2p.pubsub.gossip.Gossip
import io.libp2p.security.noise.NoiseXXSecureChannel
import io.libp2p.transport.tcp.TcpTransport
import java.util.concurrent.CompletableFuture
import java.util.concurrent.TimeUnit
import kotlin.concurrent.thread

fun main() {
    println("Starting Universal Connectivity Application...")

    // Create Gossip instance
    val gossip = Gossip()

    // Create a libp2p host
    val node: Host = host {
        identity {
            random(KeyType.ED25519)
        }
        transports {
            +::TcpTransport
        }
        secureChannels {
            +::NoiseXXSecureChannel
        }
        muxers {
            +StreamMuxerProtocol.Mplex
        }
        protocols {
            +Ping()
            +Identify()
            +gossip
        }
        network {
            listen("/ip4/0.0.0.0/tcp/0")
        }
    }

    // Start the host
    node.start().get()

    println("Local peer id: ${node.peerId}")

    // Print listening addresses
    println("Listening on:")
    for (addr in node.listenAddresses()) {
        println("  $addr/p2p/${node.peerId}")
    }

    println("GossipSub service created")

    // Parse and connect to remote peers
    val remotePeersStr = System.getenv("REMOTE_PEERS") ?: ""
    if (remotePeersStr.isEmpty()) {
        println("No REMOTE_PEERS specified. Running in standalone mode.")
    }

    if (remotePeersStr.isNotEmpty()) {
        val peerAddrs = remotePeersStr.split(",")
        val connectionFutures = mutableListOf<CompletableFuture<Void>>()

        for (addrStr in peerAddrs) {
            val trimmed = addrStr.trim()
            if (trimmed.isEmpty()) continue

            try {
                val addr = Multiaddr(trimmed)
                val peerId = addr.peerId

                if (peerId == null) {
                    println("Multiaddress $addr does not contain peer ID, skipping")
                    continue
                }

                println("Dialing peer $peerId...")

                val connFuture = node.network.connect(addr).toVoidCompletableFuture()
                connectionFutures.add(connFuture)

                connFuture.thenAccept {
                    println("Connected to: $peerId")
                }.exceptionally { err ->
                    println("Failed to connect to $peerId: ${err.message}")
                    null
                }
            } catch (e: Exception) {
                println("Invalid multiaddr $trimmed: ${e.message}")
            }
        }

        // Wait for connections with timeout
        try {
            CompletableFuture.allOf(*connectionFutures.toTypedArray())
                .get(30, TimeUnit.SECONDS)
        } catch (e: Exception) {
            // Connection attempts timed out or failed
        }
    }

    // Get GossipSub API
    val api = gossip.router

    // Join topic
    val topicName = "universal-connectivity-chat"
    api.subscribe(topicName)
    println("Joined topic: $topicName")

    // Subscribe to receive messages
    api.subscribe { msg ->
        // Skip our own messages
        if (msg.from == node.peerId) {
            return@subscribe
        }

        val sender = msg.from.toShortString()
        val text = String(msg.data)
        println("[RECEIVED] From $sender: $text")
    }

    // Start publishing messages
    val publishThread = thread(start = true) {
        var msgCount = 0

        while (true) {
            try {
                Thread.sleep(5000)

                msgCount++
                val msg = "Hello from ${node.peerId.toShortString()} - Message #$msgCount at ${System.currentTimeMillis()}"

                api.publish(topicName, msg.toByteArray())
                println("[SENT] $msg")

            } catch (e: InterruptedException) {
                println("Publishing thread interrupted")
                break
            } catch (e: Exception) {
                println("Failed to publish: ${e.message}")
            }
        }
    }

    println()
    println("Application running. Messages will be published every 5 seconds.")
    println("Press Ctrl+C to exit.")
    println()

    // Keep running
    Thread.sleep(Long.MAX_VALUE)
}
```

## Testing Your Implementation

### Single Instance Test

```bash
cd en/jvm/06-gossipsub-checkpoint
gradle run
```

Expected output:
```
Starting Universal Connectivity Application...
Local peer id: 12D3KooW...
Listening on:
  /ip4/127.0.0.1/tcp/54321/p2p/12D3KooW...
GossipSub service created
No REMOTE_PEERS specified. Running in standalone mode.
Joined topic: universal-connectivity-chat

Application running. Messages will be published every 5 seconds.
Press Ctrl+C to exit.

[SENT] Hello from 12D3KooW... - Message #1 at 1706094000000
[SENT] Hello from 12D3KooW... - Message #2 at 1706094005000
```

### Multi-Instance Test (Real P2P Chat!)

#### Terminal 1:
```bash
gradle run
```

Note one of the listening addresses.

#### Terminal 2:
```bash
export REMOTE_PEERS="<address from Terminal 1>"
gradle run
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
cd en/jvm/06-gossipsub-checkpoint
export PROJECT_ROOT=$(pwd)/../../..
export LESSON_PATH=en/jvm/06-gossipsub-checkpoint

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
- Add check: `if (msg.from == node.peerId) return@subscribe`
- Verify peer ID comparison is correct
- This is normal GossipSub behavior (you receive your own messages)
</details>

<details>
<summary>Compilation Errors</summary>

**Symptom**: Gradle build fails with missing imports

**Causes**:
1. Missing jvm-libp2p dependency
2. Wrong version
3. JitPack not configured

**Solutions**:
- Ensure `io.libp2p:jvm-libp2p:1.1.1-RELEASE` in dependencies
- Add `maven("https://jitpack.io")` to repositories
- Run `gradle clean build`
</details>

<details>
<summary>Thread Interrupted Exceptions</summary>

**Symptom**: "Publishing thread interrupted" in logs

**Causes**:
1. Application shutdown
2. Host stopped

**Solutions**:
- This is normal during shutdown
- Ensure proper cleanup with try-finally
- Use daemon threads if needed
</details>

## Hints

<details>
<summary>Hint: Message Validation</summary>

Add custom message validation in jvm-libp2p by filtering in your subscription handler:

```kotlin
api.subscribe { msg ->
    // Skip own messages
    if (msg.from == node.peerId) return@subscribe

    // Reject messages over 1KB
    if (msg.data.size > 1024) {
        println("Rejected large message from ${msg.from.toShortString()}")
        return@subscribe
    }

    // Process valid message
    println("[RECEIVED] ${String(msg.data)}")
}
```

Validation prevents spam and invalid messages from being processed!
</details>

<details>
<summary>Hint: Multiple Topics</summary>

Subscribe to multiple topics:

```kotlin
val topics = listOf("chat", "announcements", "alerts")

for (topic in topics) {
    api.subscribe(topic)
    println("Subscribed to: $topic")
}

// Handle messages from all topics
api.subscribe { msg ->
    if (msg.from == node.peerId) return@subscribe

    // msg.topic contains the topic name
    println("[${msg.topics.firstOrNull()}] ${String(msg.data)}")
}
```

Useful for organizing different types of messages!
</details>

<details>
<summary>Hint: Structured Messages</summary>

Use structured messages with simple serialization:

```kotlin
data class ChatMessage(
    val sender: String,
    val text: String,
    val timestamp: Long
)

// Publishing
val msg = ChatMessage(
    sender = node.peerId.toShortString(),
    text = "Hello, world!",
    timestamp = System.currentTimeMillis()
)
val json = """{"sender":"${msg.sender}","text":"${msg.text}","timestamp":${msg.timestamp}}"""
api.publish(topicName, json.toByteArray())

// Receiving
api.subscribe { msg ->
    if (msg.from == node.peerId) return@subscribe

    val text = String(msg.data)
    // Parse JSON or use a library
    println("Message: $text")
}
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

You've completed the GossipSub checkpoint! This powerful pub/sub system enables:
- Decentralized messaging at scale
- Topic-based content distribution
- Resilient peer-to-peer communication
- Foundation for complex P2P applications

Next, you can explore:
- Kademlia DHT for peer discovery
- Custom protocols for your use case
- Advanced GossipSub configurations
- Production deployment strategies

## Additional Resources

- [GossipSub specification](https://github.com/libp2p/specs/blob/master/pubsub/gossipsub/README.md)
- [jvm-libp2p documentation](https://github.com/libp2p/jvm-libp2p)
- [PubSub interface spec](https://github.com/libp2p/specs/tree/master/pubsub)
- [Mesh networks explained](https://docs.libp2p.io/concepts/pubsub/overview/)
