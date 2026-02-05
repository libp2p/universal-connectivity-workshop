# Lesson 4: QUIC Transport

In this lesson, you'll learn about QUIC transport and multi-transport architecture in libp2p. While QUIC is a powerful modern transport protocol, **QUIC support in jvm-libp2p is currently in BETA status** and not yet production-ready. This lesson focuses on understanding multi-transport architecture and preparing for when QUIC becomes fully available.

## Learning Objectives

By the end of this lesson, you will:
- Understand QUIC and its advantages over TCP
- Learn about multi-transport architecture in libp2p
- Understand QUIC's beta status in jvm-libp2p
- Configure transport layers with proper patterns
- Prepare code for future QUIC support
- Compare QUIC and TCP multiaddresses

## Background: QUIC Transport

**QUIC** (Quick UDP Internet Connections) is a modern transport protocol developed by Google, now standardized as RFC 9000. It combines features from TCP, TLS, and HTTP/2 into a single, efficient protocol.

### Key QUIC Advantages

| Feature | TCP + TLS | QUIC |
|---------|-----------|------|
| **Connection Establishment** | 3-way handshake + TLS handshake (2-3 RTTs) | Combined handshake (1 RTT) |
| **Encryption** | Optional (TLS layer) | Built-in (always encrypted) |
| **Head-of-Line Blocking** | Yes (stream-level) | No (per-stream ordering) |
| **Connection Migration** | No (breaks on IP change) | Yes (survives IP/port changes) |
| **Transport** | TCP (reliable, ordered) | UDP-based (custom reliability) |
| **NAT Traversal** | Good | Better (UDP hole-punching) |

### When QUIC Shines

1. **Mobile Networks**: Connection migration handles network switches (WiFi ↔ Cellular)
2. **Lossy Networks**: Better performance with packet loss
3. **Long-Distance**: Reduced latency from 1-RTT handshake
4. **Firewall Traversal**: UDP-based helps with certain NAT types
5. **Modern Infrastructure**: Optimized for current internet conditions

### QUIC in libp2p

libp2p supports QUIC with:
- Protocol ID: `/quic` or `/quic-v1`
- Built-in security (no separate security layer needed)
- Automatic transport selection
- Multiplexing built-in (no separate muxer needed)

## QUIC Status in jvm-libp2p

**IMPORTANT: Current Status**

According to the [jvm-libp2p repository](https://github.com/libp2p/jvm-libp2p), QUIC transport is currently marked as 🍋 (prototype/beta, not tested in production). This means:

- **Not Production Ready**: QUIC support exists but is not fully stable
- **Beta Quality**: Implementation may have bugs or incomplete features
- **Under Development**: API may change in future releases
- **Future Support**: Will become production-ready in future versions

### Why Learn About QUIC Now?

Even though QUIC is in beta:
1. **Architecture Understanding**: Learn multi-transport patterns
2. **Future Preparation**: Be ready when QUIC goes production
3. **Design Patterns**: Understand how transports work in libp2p
4. **Industry Knowledge**: QUIC is widely used in other libp2p implementations

## Transport Selection in libp2p

When multiple transports are available, libp2p automatically:

1. **Advertisement**: Announces all transports in multiaddresses
2. **Parallel Dialing**: Tries multiple transports simultaneously (Happy Eyeballs)
3. **First Success**: Uses whichever connects first
4. **Fallback**: Retries other transports if one fails

Example: Peer has TCP and QUIC addresses:
```
/ip4/192.168.1.100/tcp/4001/p2p/12D3KooW...
/ip4/192.168.1.100/udp/4001/quic-v1/p2p/12D3KooW...
```

libp2p will dial both simultaneously, using whichever succeeds first!

## Your Task

In this lesson, you'll:
1. Understand multi-transport architecture
2. Learn the QUIC transport pattern (for future use)
3. Document QUIC's beta status in your code
4. Keep TCP transport as the production-ready option
5. Add ping protocol to test connectivity

## Step-by-Step Instructions

### Step 1: Review Transport Architecture

The jvm-libp2p transport stack supports multiple transports:

```kotlin
val node = host {
    identity { random(KeyType.ED25519) }

    // Transports - multiple can be added
    transports {
        +::TcpTransport  // Production-ready
        // Future: QUIC transport when available
    }

    secureChannels { +::NoiseXXSecureChannel }
    muxers { +StreamMuxerProtocol.Mplex }

    network {
        listen("/ip4/0.0.0.0/tcp/0")
        // Future: listen("/ip4/0.0.0.0/udp/0/quic-v1")
    }
}
```

**Key Points**:
- Multiple transports can be configured
- Each transport has its own listening address
- Security and multiplexing work across all transports
- Same code handles all transport types

### Step 2: Add Required Imports

Update your imports in `app/src/main/kotlin/Main.kt`:

```kotlin
import io.libp2p.core.Host
import io.libp2p.core.crypto.KeyType
import io.libp2p.core.dsl.host
import io.libp2p.core.multiformats.Multiaddr
import io.libp2p.core.mux.StreamMuxerProtocol
import io.libp2p.etc.types.toVoidCompletableFuture
import io.libp2p.protocol.Ping
import io.libp2p.security.noise.NoiseXXSecureChannel
import io.libp2p.transport.tcp.TcpTransport
import java.util.concurrent.CompletableFuture
import java.util.concurrent.TimeUnit
```

**What's new?**

- `io.libp2p.protocol.Ping`: Ping protocol for connectivity testing
- Other imports carry over from previous lessons

### Step 3: Configure Host with Ping Protocol

Create your host with TCP transport and ping support:

```kotlin
fun main() {
    println("Starting Universal Connectivity Application...")

    // Note: QUIC transport in jvm-libp2p is currently BETA status
    // This lesson uses TCP as the production-ready transport

    val node: Host = host {
        identity {
            random(KeyType.ED25519)
        }
        transports {
            +::TcpTransport
            // QUIC transport when production-ready:
            // Requires additional dependencies and configuration
            // Pattern: +::QuicTransport (future)
        }
        secureChannels {
            +::NoiseXXSecureChannel
        }
        muxers {
            +StreamMuxerProtocol.Mplex
        }
        network {
            listen("/ip4/0.0.0.0/tcp/0")
            // QUIC listen address pattern (future):
            // listen("/ip4/0.0.0.0/udp/0/quic-v1")
        }
        protocols {
            +Ping()  // Add ping protocol
        }
    }

    // More code will go here...
}
```

**What's happening here?**

- `protocols { +Ping() }`: Adds ping protocol support
  - Ping tests connectivity between peers
  - Measures round-trip time (RTT)
  - Standard libp2p protocol
- Comments show future QUIC pattern
- TCP remains the production transport

### Step 4: Set Up Connection Handler and Start Host

Add connection monitoring and start the host:

```kotlin
fun main() {
    // ... previous code (host creation) ...

    // Set up connection event handler
    node.network.connectionsManager.addConnectionHandler { conn ->
        val remotePeer = conn.secureSession().remoteId
        println("Event: Connected to $remotePeer")
        conn.closeFuture().thenAccept {
            println("Event: Disconnected from $remotePeer")
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

    // More code will go here...
}
```

**What's happening here?**

- Connection handler monitors peer connections
- Start and print addresses as in previous lessons
- Same pattern works for any transport type

### Step 5: Parse Remote Peers

Add code to parse peer addresses from environment variable:

```kotlin
fun main() {
    // ... previous code (printing addresses) ...

    // Parse remote peer addresses
    val remotePeersStr = System.getenv("REMOTE_PEERS")
        ?: "/ip4/147.75.77.187/tcp/4001/p2p/QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN"

    if (remotePeersStr.isEmpty() || remotePeersStr == "/ip4/147.75.77.187/tcp/4001/p2p/QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN") {
        println("No REMOTE_PEERS specified, using checkpoint server")
    }

    val remotePeers = mutableListOf<Multiaddr>()
    val peerAddrs = remotePeersStr.split(",")

    for (addrStr in peerAddrs) {
        val trimmed = addrStr.trim()
        if (trimmed.isEmpty()) continue

        try {
            val addr = Multiaddr(trimmed)
            remotePeers.add(addr)
        } catch (e: Exception) {
            println("Invalid multiaddr $trimmed: ${e.message}")
        }
    }

    // More code will go here...
}
```

**What's happening here?**

- Default to checkpoint server if no REMOTE_PEERS set
- Parse comma-separated multiaddresses
- Transport type (TCP/QUIC) determined by multiaddress format

### Step 6: Connect to Remote Peers

Add code to dial remote peers:

```kotlin
fun main() {
    // ... previous code (parsing remote peers) ...

    // Dial remote peers
    val connectionFutures = mutableListOf<CompletableFuture<Void>>()
    val connectedPeers = mutableListOf<String>()

    for (addr in remotePeers) {
        val peerId = addr.peerId
        if (peerId == null) {
            println("Multiaddress $addr does not contain peer ID, skipping")
            continue
        }

        println("Dialing peer $peerId...")

        try {
            val connFuture = node.network.connect(addr).toVoidCompletableFuture()
            connectionFutures.add(connFuture)

            connFuture.thenAccept {
                println("Connected to: $peerId")
                connectedPeers.add(peerId.toString())
            }.exceptionally { err ->
                println("Failed to connect to $peerId: ${err.message}")
                null
            }
        } catch (e: Exception) {
            println("Error dialing $peerId: ${e.message}")
        }
    }

    // Wait for connections
    try {
        CompletableFuture.allOf(*connectionFutures.toTypedArray())
            .get(30, TimeUnit.SECONDS)
    } catch (e: Exception) {
        println("Some connection attempts timed out or failed")
    }

    // More code will go here...
}
```

### Step 7: Ping Connected Peers

Add ping functionality to test connectivity:

```kotlin
fun main() {
    // ... previous code (connecting to peers) ...

    if (connectedPeers.isEmpty()) {
        println("Failed to connect to any peers")
        node.stop().get()
        return
    }

    // Get ping protocol
    val ping = node.protocols.find { it is Ping } as? Ping
    if (ping == null) {
        println("Ping protocol not found")
        node.stop().get()
        return
    }

    // Ping each connected peer
    println("\nPinging connected peers...")
    for (peerIdStr in connectedPeers) {
        try {
            println("Pinging $peerIdStr...")

            val startTime = System.nanoTime()
            val pingFuture = ping.ping(node.network, Multiaddr("/p2p/$peerIdStr"))
            pingFuture.get(10, TimeUnit.SECONDS)
            val endTime = System.nanoTime()

            val rttMs = (endTime - startTime) / 1_000_000.0
            println("Ping to $peerIdStr successful: RTT = ${rttMs.toInt()}ms")
        } catch (e: Exception) {
            println("Ping to $peerIdStr failed: ${e.message}")
        }
    }

    // More code will go here...
}
```

**What's happening here?**

- Get Ping protocol instance from host
- Ping each successfully connected peer
- Measure round-trip time manually
- Use timeout to prevent hanging

### Step 8: Keep Running and Clean Shutdown

Add code to keep the application running:

```kotlin
fun main() {
    // ... all previous code ...

    // Keep the application running
    println("\nApplication running. Press Ctrl+C to exit.")
    Thread.sleep(TimeUnit.SECONDS.toMillis(30))

    // Shut down gracefully
    println("Shutting down...")
    node.stop().get()
}
```

## Complete Implementation

Here's your complete `app/src/main/kotlin/Main.kt`:

```kotlin
import io.libp2p.core.Host
import io.libp2p.core.crypto.KeyType
import io.libp2p.core.dsl.host
import io.libp2p.core.multiformats.Multiaddr
import io.libp2p.core.mux.StreamMuxerProtocol
import io.libp2p.etc.types.toVoidCompletableFuture
import io.libp2p.protocol.Ping
import io.libp2p.security.noise.NoiseXXSecureChannel
import io.libp2p.transport.tcp.TcpTransport
import java.util.concurrent.CompletableFuture
import java.util.concurrent.TimeUnit

fun main() {
    println("Starting Universal Connectivity Application...")

    // Note: QUIC transport in jvm-libp2p is currently BETA status
    // This lesson uses TCP as the production-ready transport

    val node: Host = host {
        identity {
            random(KeyType.ED25519)
        }
        transports {
            +::TcpTransport
            // QUIC transport when production-ready:
            // Requires additional dependencies and configuration
            // Pattern: +::QuicTransport (future)
        }
        secureChannels {
            +::NoiseXXSecureChannel
        }
        muxers {
            +StreamMuxerProtocol.Mplex
        }
        network {
            listen("/ip4/0.0.0.0/tcp/0")
            // QUIC listen address pattern (future):
            // listen("/ip4/0.0.0.0/udp/0/quic-v1")
        }
        protocols {
            +Ping()
        }
    }

    // Set up connection event handler
    node.network.connectionsManager.addConnectionHandler { conn ->
        val remotePeer = conn.secureSession().remoteId
        println("Event: Connected to $remotePeer")
        conn.closeFuture().thenAccept {
            println("Event: Disconnected from $remotePeer")
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

    // Parse remote peer addresses
    val remotePeersStr = System.getenv("REMOTE_PEERS")
        ?: "/ip4/147.75.77.187/tcp/4001/p2p/QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN"

    if (remotePeersStr.isEmpty() || remotePeersStr == "/ip4/147.75.77.187/tcp/4001/p2p/QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN") {
        println("No REMOTE_PEERS specified, using checkpoint server")
    }

    val remotePeers = mutableListOf<Multiaddr>()
    val peerAddrs = remotePeersStr.split(",")

    for (addrStr in peerAddrs) {
        val trimmed = addrStr.trim()
        if (trimmed.isEmpty()) continue

        try {
            val addr = Multiaddr(trimmed)
            remotePeers.add(addr)
        } catch (e: Exception) {
            println("Invalid multiaddr $trimmed: ${e.message}")
        }
    }

    // Dial remote peers
    val connectionFutures = mutableListOf<CompletableFuture<Void>>()
    val connectedPeers = mutableListOf<String>()

    for (addr in remotePeers) {
        val peerId = addr.peerId
        if (peerId == null) {
            println("Multiaddress $addr does not contain peer ID, skipping")
            continue
        }

        println("Dialing peer $peerId...")

        try {
            val connFuture = node.network.connect(addr).toVoidCompletableFuture()
            connectionFutures.add(connFuture)

            connFuture.thenAccept {
                println("Connected to: $peerId")
                connectedPeers.add(peerId.toString())
            }.exceptionally { err ->
                println("Failed to connect to $peerId: ${err.message}")
                null
            }
        } catch (e: Exception) {
            println("Error dialing $peerId: ${e.message}")
        }
    }

    // Wait for connections
    try {
        CompletableFuture.allOf(*connectionFutures.toTypedArray())
            .get(30, TimeUnit.SECONDS)
    } catch (e: Exception) {
        println("Some connection attempts timed out or failed")
    }

    if (connectedPeers.isEmpty()) {
        println("Failed to connect to any peers")
        node.stop().get()
        return
    }

    // Get ping protocol
    val ping = node.protocols.find { it is Ping } as? Ping
    if (ping == null) {
        println("Ping protocol not found")
        node.stop().get()
        return
    }

    // Ping each connected peer
    println("\nPinging connected peers...")
    for (peerIdStr in connectedPeers) {
        try {
            println("Pinging $peerIdStr...")

            val startTime = System.nanoTime()
            val pingFuture = ping.ping(node.network, Multiaddr("/p2p/$peerIdStr"))
            pingFuture.get(10, TimeUnit.SECONDS)
            val endTime = System.nanoTime()

            val rttMs = (endTime - startTime) / 1_000_000.0
            println("Ping to $peerIdStr successful: RTT = ${rttMs.toInt()}ms")
        } catch (e: Exception) {
            println("Ping to $peerIdStr failed: ${e.message}")
        }
    }

    // Keep the application running
    println("\nApplication running. Press Ctrl+C to exit.")
    Thread.sleep(TimeUnit.SECONDS.toMillis(30))

    // Shut down gracefully
    println("Shutting down...")
    node.stop().get()
}
```

## Understanding Multi-Transport Architecture

### Transport Abstraction

libp2p's power comes from transport abstraction:

```
Application Layer (Your code)
        ↕
  Protocol Layer (Ping, Identify, etc.)
        ↕
   Stream Multiplexing (Mplex)
        ↕
   Security Layer (Noise)
        ↕
  Transport Layer (TCP, QUIC, WebSocket)
        ↕
    Network (IP/UDP)
```

**Key Benefits**:
- Application code works with any transport
- Easy to add new transports
- Automatic transport selection
- Graceful fallback

### QUIC Multiaddress Format

When QUIC becomes available, addresses will look like:

```
TCP:  /ip4/192.168.1.100/tcp/4001/p2p/12D3KooW...
QUIC: /ip4/192.168.1.100/udp/4001/quic-v1/p2p/12D3KooW...
```

**Notice**:
- QUIC uses `/udp/` not `/tcp/`
- Includes `/quic-v1` protocol component
- Same peer ID for both transports
- Ports may differ

## Testing Your Implementation

### Manual Testing

```bash
cd en/jvm/04-quic-transport/app
./gradlew run
```

Expected output:
```
Starting Universal Connectivity Application...
Local peer id: 12D3KooW...
Listening on:
  /ip4/127.0.0.1/tcp/54321/p2p/12D3KooW...
  /ip4/192.168.1.100/tcp/54321/p2p/12D3KooW...
No REMOTE_PEERS specified, using checkpoint server
Dialing peer QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN...
Event: Connected to QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN
Connected to: QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN

Pinging connected peers...
Pinging QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN...
Ping to QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN successful: RTT = 42ms

Application running. Press Ctrl+C to exit.
```

### Two-Instance Test

#### Terminal 1:
```bash
cd en/jvm/04-quic-transport/app
./gradlew run
```

Note the TCP address from output.

#### Terminal 2:
```bash
# Windows
set REMOTE_PEERS=/ip4/127.0.0.1/tcp/54321/p2p/12D3KooWABC...
./gradlew run

# Linux/Mac
export REMOTE_PEERS="/ip4/127.0.0.1/tcp/54321/p2p/12D3KooWABC..."
./gradlew run
```

Both terminals should show successful connection and ping!

### Automated Checking

```bash
cd ..  # Back to lesson directory
python check.py
```

## Success Criteria

Your implementation should:
- ✅ Display startup message and peer ID
- ✅ Configure TCP transport with security and multiplexing
- ✅ Add Ping protocol
- ✅ Listen on TCP addresses
- ✅ Connect to remote peers successfully
- ✅ Ping peers and measure RTT
- ✅ Document QUIC beta status
- ✅ Show multi-transport architecture pattern

## Troubleshooting

<details>
<summary>Connection Failures</summary>

**Symptom**: "Failed to connect to" messages

**Causes**:
1. Invalid multiaddress format
2. Network unreachable
3. Firewall blocking
4. Peer not listening

**Solutions**:
- Verify multiaddress includes `/p2p/<peer-id>`
- Test with localhost first: `/ip4/127.0.0.1/tcp/...`
- Check firewall settings
- Ensure remote peer is running
</details>

<details>
<summary>Ping Failures</summary>

**Symptom**: "Ping to ... failed"

**Causes**:
1. Connection not established
2. Peer doesn't support ping
3. Timeout too short
4. Network issues

**Solutions**:
- Verify "Connected to" message appears first
- Ensure peer supports ping protocol
- Increase timeout if network is slow
- Check for error messages in output
</details>

<details>
<summary>QUIC Not Available</summary>

**Symptom**: Want to use QUIC but it's not available

**Status**: QUIC is currently in BETA in jvm-libp2p

**Future Steps**:
1. Monitor [jvm-libp2p releases](https://github.com/libp2p/jvm-libp2p/releases)
2. Check for production-ready QUIC status
3. Add necessary dependencies when available
4. Update transport configuration
5. Add UDP listening addresses

**Current Solution**: Use TCP transport (production-ready)
</details>

## Hints

<details>
<summary>Hint: Transport Selection</summary>

When multiple transports are configured, libp2p uses "Happy Eyeballs":

```kotlin
// Host with multiple transports
transports {
    +::TcpTransport
    // Future: +::QuicTransport
}

// When dialing, libp2p will:
// 1. Try all available transports in parallel
// 2. Use whichever connects first
// 3. Cancel other attempts
// 4. Cache the working transport
```

This provides:
- Faster connections (parallel attempts)
- Better reliability (fallback options)
- Optimal performance (fastest wins)
</details>

<details>
<summary>Hint: Multiaddress Components</summary>

Understanding multiaddress format:

```
/ip4/192.168.1.100/tcp/4001/p2p/12D3KooW...
 │    │             │    │    │   │
 │    IP address    │    Port │   Peer ID
 Protocol           Protocol  Protocol
```

For QUIC (future):
```
/ip4/192.168.1.100/udp/4001/quic-v1/p2p/12D3KooW...
 │    │             │    │    │       │   │
 │    IP address    │    Port │       │   Peer ID
 Protocol           Protocol  QUIC    Protocol
                              version
```

Key differences:
- TCP uses `/tcp/`
- QUIC uses `/udp/` + `/quic-v1`
</details>

<details>
<summary>Hint: Future QUIC Configuration</summary>

When QUIC becomes production-ready, the pattern will be:

```kotlin
// Add QUIC dependencies to build.gradle.kts
dependencies {
    implementation("io.libp2p:jvm-libp2p:1.x.x-RELEASE")
    // Additional QUIC dependencies may be required
    // implementation("io.netty:netty-transport-native-quic:...")
}

// Configure QUIC transport
val node = host {
    transports {
        +::TcpTransport
        +::QuicTransport  // When available
    }
    network {
        listen("/ip4/0.0.0.0/tcp/0")
        listen("/ip4/0.0.0.0/udp/0/quic-v1")
    }
    // Security and muxing still needed for TCP
    // QUIC has built-in security and muxing
}
```

Monitor jvm-libp2p repository for updates!
</details>

## What You've Learned

Congratulations! You've successfully:

- **Understood QUIC transport** and its advantages
- **Learned multi-transport architecture** in libp2p
- **Recognized QUIC beta status** in jvm-libp2p
- **Added Ping protocol** for connectivity testing
- **Prepared for future QUIC support**
- **Built production-ready TCP transport**

## Key Concepts

### Multi-Transport Architecture
- **Flexibility**: Support multiple network technologies
- **Resilience**: Fallback if one transport fails
- **Performance**: Use fastest available option
- **Future-Proof**: Easy to add new transports

### QUIC Benefits (Future)
- **Faster Connections**: 1-RTT handshake
- **Better Recovery**: Improved packet loss handling
- **Connection Migration**: Survives network changes
- **Built-in Security**: No separate security layer needed

### Production vs Beta
- **TCP**: Production-ready, widely tested
- **QUIC**: Beta status, under development
- **Strategy**: Use TCP now, add QUIC when ready
- **Architecture**: Code ready for multiple transports

### Transport Abstraction
- **Application-Agnostic**: Same code for all transports
- **Protocol Independence**: Transports handle low-level details
- **Automatic Selection**: libp2p chooses best option
- **Graceful Fallback**: Degrade gracefully if transport fails

## What's Next?

In future lessons, you'll explore more libp2p protocols and features:
- Peer discovery mechanisms
- Content routing with DHT
- Pub/sub messaging
- NAT traversal strategies

The multi-transport architecture you learned here will support all these advanced features!

## Additional Resources

- [QUIC RFC 9000](https://www.rfc-editor.org/rfc/rfc9000.html)
- [libp2p transports](https://docs.libp2p.io/concepts/transports/overview/)
- [QUIC in libp2p](https://docs.libp2p.io/concepts/transports/quic/)
- [jvm-libp2p repository](https://github.com/libp2p/jvm-libp2p)
- [jvm-libp2p releases](https://github.com/libp2p/jvm-libp2p/releases)
- [Happy Eyeballs RFC 8305](https://www.rfc-editor.org/rfc/rfc8305.html)

**Sources for QUIC Status**:
- [GitHub - libp2p/jvm-libp2p](https://github.com/libp2p/jvm-libp2p)
- [QUIC - libp2p](https://docs.libp2p.io/concepts/transports/quic/)
