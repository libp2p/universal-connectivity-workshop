# Lesson 3: Ping Protocol Checkpoint

Congratulations on reaching your first checkpoint! In this lesson, you'll implement the ping protocol to verify connectivity and measure round-trip time (RTT) to remote peers. This is your first real libp2p protocol in action!

## Learning Objectives

By the end of this lesson, you will:
- Understand libp2p's protocol abstraction
- Implement the ping protocol to measure connectivity
- Connect to the instructor's checkpoint server
- Measure and display round-trip times
- Debug connection and protocol issues

## Background: The Ping Protocol

The **ping protocol** is one of libp2p's simplest and most useful protocols. It works similarly to ICMP ping but operates at the libp2p protocol layer:

1. **Initiator** sends a 32-byte random payload over a stream
2. **Responder** echoes the exact payload back
3. **Initiator** measures the round-trip time (RTT)

### Why Ping?

- **Connectivity Verification**: Confirms end-to-end connectivity
- **Latency Measurement**: Measures network round-trip time
- **Keep-Alive**: Can maintain NAT mappings and connections
- **Protocol Testing**: Validates your libp2p stack is working

### Protocol Flow

```
Peer A (Initiator)         Peer B (Responder)
    |                              |
    |------- Open Stream --------->|
    |   Protocol: /ipfs/ping/1.0.0 |
    |                              |
    |------ 32 Random Bytes ------>|
    |                              |
    |<----- Same 32 Bytes ---------|
    |                              |
    |------ Close Stream --------->|
    |                              |
    Calculate RTT
```

### jvm-libp2p Ping Service

jvm-libp2p provides a built-in ping protocol that handles all the protocol details:

```kotlin
import io.libp2p.protocol.Ping

// Add Ping protocol to host
val node: Host = host {
    identity { random(KeyType.ED25519) }
    transports { +::TcpTransport }
    secureChannels { +::NoiseXXSecureChannel }
    muxers { +StreamMuxerProtocol.Mplex }
    protocols { +Ping() }  // Add ping protocol
    network { listen("/ip4/0.0.0.0/tcp/0") }
}

// Dial and ping a remote peer
val ping = Ping()
val stream = node.network.connect(remoteAddr).stream
val controller = ping.dial(node, remotePeer, stream).controller.get()
val latency = controller.ping().get()
println("RTT: ${latency}ms")
```

## Your Task

Extend your application to:
1. Add the Ping protocol to your host
2. Connect to the instructor's checkpoint server
3. Ping the server and display the RTT
4. Handle ping failures gracefully

## Checkpoint Server

The instructor provides a checkpoint server at:
```
/ip4/147.75.77.187/tcp/4001/p2p/QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN
```

This is a public libp2p bootstrap node that responds to ping requests.

## Step-by-Step Instructions

### Step 1: Update Imports

Add the ping protocol import to your `app/src/main/kotlin/Main.kt`:

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

- `io.libp2p.protocol.Ping`: The ping protocol implementation

### Step 2: Add Ping Protocol to Host

Modify your host creation to include the Ping protocol:

```kotlin
fun main() {
    println("Starting Universal Connectivity Application...")

    // Create a libp2p host with TCP transport, security, multiplexing, and ping
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
            +Ping()  // Add ping protocol
        }
        network {
            listen("/ip4/0.0.0.0/tcp/0")
        }
    }

    // Set up connection event handler
    node.network.connectionsManager.addConnectionHandler { conn ->
        println("New connection established: ${conn.secureSession().remoteId}")
        conn.closeFuture().thenAccept {
            println("Connection closed: ${conn.secureSession().remoteId}")
        }
    }

    // Start the host
    node.start().get()

    // Print the peer ID
    println("Local peer id: ${node.peerId}")

    // Print listening addresses
    println("Listening on:")
    for (addr in node.listenAddresses()) {
        println("  $addr/p2p/${node.peerId}")
    }

    println("Ping protocol initialized")

    // More code will go here...
}
```

**What's happening here?**

- `protocols { +Ping() }`: Adds the ping protocol to the host
  - Automatically registers the `/ipfs/ping/1.0.0` protocol handler
  - Handles both sending pings (client) and responding to pings (server)
  - Your node can now act as both ping initiator and responder

**Why automatic?** The ping protocol registers itself with your host's protocol handlers. When a peer opens a ping stream to you, it's automatically handled.

### Step 3: Parse and Connect to Checkpoint Server

Add code to connect to remote peers with error handling:

```kotlin
fun main() {
    // ... previous code (host creation and startup) ...

    // Parse remote peer addresses
    val remotePeersStr = System.getenv("REMOTE_PEERS") ?: ""
    val remotePeers = mutableListOf<Multiaddr>()

    if (remotePeersStr.isNotEmpty()) {
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
    } else {
        // Default to checkpoint server if no peers specified
        val checkpointAddr = "/ip4/147.75.77.187/tcp/4001/p2p/QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN"
        println("No REMOTE_PEERS specified, using checkpoint server")
        remotePeers.add(Multiaddr(checkpointAddr))
    }

    // Dial remote peers
    val connectionFutures = mutableListOf<CompletableFuture<Unit>>()

    for (addr in remotePeers) {
        // Extract peer ID from multiaddr
        val peerId = addr.getPeerId()
        if (peerId == null) {
            println("Multiaddress $addr does not contain peer ID, skipping")
            continue
        }

        println("Dialing peer $peerId at $addr")

        // Connect to the peer
        try {
            val connFuture = node.network.connect(addr).thenApply { }
            connectionFutures.add(connFuture)

            connFuture.thenAccept {
                println("Connected to: $peerId")
            }.exceptionally { err ->
                println("Failed to connect to $peerId: ${err.message}")
                null
            }
        } catch (e: Exception) {
            println("Error dialing $peerId: ${e.message}")
        }
    }

    // Wait for all connections to complete (with timeout)
    try {
        CompletableFuture.allOf(*connectionFutures.toTypedArray())
            .get(30, TimeUnit.SECONDS)
    } catch (e: Exception) {
        println("Some connection attempts timed out or failed")
    }

    // More code will go here...
}
```

**What's happening here?**

- **Default Checkpoint Server**: If `REMOTE_PEERS` is empty, we use the instructor's server
- **Timeout**: Wait up to 30 seconds for connections to establish
  - If connection takes longer, we continue anyway
  - Essential for unreliable networks
- **Error Handling**: Continue if some connections fail

**Why 30 seconds?** TCP handshake + TLS/Noise negotiation + protocol negotiation can take time on slow networks.

### Step 4: Ping Connected Peers

Add code to ping each connected peer:

```kotlin
fun main() {
    // ... previous code (connecting to peers) ...

    // Get connected peers
    val connectedPeers = node.network.connections
        .map { it.secureSession().remoteId.toString() }
        .distinct()

    if (connectedPeers.isEmpty()) {
        println("No peers connected, exiting")
        node.stop().get()
        return
    }

    // Ping each connected peer
    println("\nPinging connected peers...")

    val ping = Ping()

    for (addr in remotePeers) {
        val peerId = addr.getPeerId() ?: continue

        // Skip if not connected
        if (!connectedPeers.contains(peerId.toString())) {
            continue
        }

        try {
            println("Pinging $peerId...")

            // Use Ping.dial() to create a ping controller
            val pinger = ping.dial(node, addr).controller.get(10, TimeUnit.SECONDS)

            // Perform 3 pings to measure latency
            for (i in 1..3) {
                val rtt = pinger.ping().get(10, TimeUnit.SECONDS)
                println("Ping $i to $peerId: RTT = ${rtt}ms")
            }
        } catch (e: Exception) {
            println("Error pinging $peerId: ${e.message}")
        }
    }

    // Keep the application running
    println("\nApplication running. Press Ctrl+C to exit.")
    Thread.sleep(TimeUnit.SECONDS.toMillis(30))

    // Shut down gracefully
    node.stop().get()
    println("Shutting down...")
}
```

**What's happening here?**

- **Get Connected Peers**: Extract peer IDs from active connections
  - Use `node.network.connections` to access current connections
  - Map to peer ID strings for comparison
- **Ping.dial()**: Creates a ping controller for a specific peer
  - Takes the host and target multiaddr
  - Returns `CompletableFuture<DialController>` with controller property
  - Handles protocol negotiation automatically
- **PingController**: The controller manages ping operations
  - `pinger.ping()` sends a ping and measures RTT
  - Returns `CompletableFuture<Long>` with RTT in milliseconds
- **Multiple Pings**: Perform 3 pings to measure average latency
  - Each ping is independent
  - Helps identify network jitter
- **Timeout**: Wait up to 10 seconds for each operation
  - `.get(10, TimeUnit.SECONDS)` blocks with timeout
  - Prevents hanging on unresponsive peers

**Why use multiaddr?** The Ping.dial() method needs the full multiaddr (not just PeerId) to establish the connection path.

## Understanding the Complete Flow

Here's what happens when you run your application:

1. **Initialization**:
   - Generate keypair and create host
   - Register TCP transport, Noise security, Mplex muxer
   - Add Ping protocol to supported protocols
   - Start listening on TCP

2. **Connection Phase**:
   - Parse peer addresses (default to checkpoint server)
   - Dial each peer with timeout
   - Wait for connection establishment
   - Track successfully connected peers

3. **Ping Phase**:
   - For each connected peer:
     - Open new stream with `/ipfs/ping/1.0.0` protocol
     - Initialize ping controller
     - Send ping request (32 random bytes)
     - Wait for echo response
     - Calculate RTT
     - Display result

4. **Maintenance Phase**:
   - Monitor connection events
   - Keep connections alive
   - Wait for user interrupt

## Testing Your Implementation

### Local Testing

```bash
cd en/jvm/03-ping-checkpoint/app

# Build your application
./gradlew build

# Run with default checkpoint server
./gradlew run

# Or specify custom peers
export REMOTE_PEERS="/ip4/147.75.77.187/tcp/4001/p2p/QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN"
./gradlew run
```

Expected output:
```
Starting Universal Connectivity Application...
Local peer id: 12D3KooW...
Listening on:
  /ip4/127.0.0.1/tcp/54321/p2p/12D3KooW...
Ping protocol initialized
No REMOTE_PEERS specified, using checkpoint server
Dialing peer QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN...
Connected to: QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN

Pinging connected peers...
Pinging QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN...
Ping to QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN successful: RTT = 45ms

Application running. Press Ctrl+C to exit.
```

### Automated Testing

```bash
# Run the checker
cd ..  # Back to lesson directory
python check.py
```

### Docker Testing

```bash
cd en/jvm/03-ping-checkpoint
export PROJECT_ROOT=$(pwd)/../../..
export LESSON_PATH=en/jvm/03-ping-checkpoint

# Build and run
docker compose up --build

# Check results
python check.py
```

## Success Criteria

Your implementation should:
- ✅ Create and start the host with Ping protocol
- ✅ Connect to the checkpoint server (or custom peers)
- ✅ Successfully ping connected peers
- ✅ Display RTT measurements in milliseconds
- ✅ Handle connection and ping failures gracefully
- ✅ Keep running until interrupted

## Troubleshooting

### Common Issues

<details>
<summary>Connection Timeout</summary>

**Symptom**: "Failed to connect to peer: timeout"

**Causes**:
1. Network unreachable (firewall, no internet)
2. Peer is offline or unreachable
3. Wrong multiaddress format
4. Timeout too short

**Solutions**:
- Check internet connectivity: `ping 147.75.77.187`
- Verify firewall allows outbound TCP
- Try increasing connection timeout to 60 seconds
- Verify multiaddress is correct
</details>

<details>
<summary>Ping Timeout</summary>

**Symptom**: "Ping failed: timeout"

**Causes**:
1. Connection dropped after establishment
2. Peer doesn't support ping protocol
3. Network latency too high
4. Stream negotiation failed

**Solutions**:
- Increase ping timeout to 30 seconds
- Check if peer is still connected
- Try pinging multiple times
- Check for connection events in logs
</details>

<details>
<summary>Protocol Negotiation Failed</summary>

**Symptom**: "protocol not supported"

**Causes**:
1. Peer doesn't support `/ipfs/ping/1.0.0`
2. libp2p versions incompatible
3. Protocol registration failed

**Solutions**:
- Verify ping protocol was added: check for "Ping protocol initialized"
- Ensure peer is a proper libp2p node
- Try the official checkpoint server (should always work)
- Check jvm-libp2p version compatibility
</details>

<details>
<summary>No Peers Connected</summary>

**Symptom**: "No peers connected, exiting"

**Causes**:
1. Invalid multiaddress format
2. All peers unreachable
3. Network connectivity issues

**Solutions**:
- Test with checkpoint server first (known good peer)
- Verify multiaddress format: `/ip4/IP/tcp/PORT/p2p/PEER_ID`
- Check DNS resolution
- Try local testing with two instances first
</details>

## Hints

<details>
<summary>Hint: Understanding RTT</summary>

**Round-Trip Time (RTT)** measures the time for data to travel from your peer to the remote peer and back.

Factors affecting RTT:
- **Geographic Distance**: Further peers = higher RTT
  - Same city: 1-10ms
  - Same country: 10-50ms
  - Different continents: 100-300ms
- **Network Quality**: WiFi vs Ethernet, congestion
- **Routing**: Number of hops, ISP routing policies
- **Peer Load**: CPU and network load on remote peer

**Good RTT values**:
- < 50ms: Excellent (local or nearby)
- 50-100ms: Good (regional)
- 100-200ms: Acceptable (long distance)
- > 200ms: High (intercontinental or slow network)

The checkpoint server (US-based) typically shows 10-150ms RTT depending on your location.
</details>

<details>
<summary>Hint: Ping Protocol Details</summary>

The ping protocol in jvm-libp2p:

**As Initiator (Client)**:
```kotlin
val ping = Ping()
val stream = node.network.newStream("/ipfs/ping/1.0.0", peerId).get()
val controller = ping.initChannel(stream).controller.get()
val rtt = controller.ping().get()
```

**As Responder (Server)**:
- Automatically handled by the ping protocol
- No code needed!
- Protocol is added via `protocols { +Ping() }`

**Protocol ID**: `/ipfs/ping/1.0.0`

**How it works**:
1. Opens stream with protocol negotiation
2. Sends 32 random bytes
3. Waits for exact echo
4. Calculates time difference (in milliseconds)
5. Returns RTT via CompletableFuture
6. Stream can be reused for multiple pings

**Error cases**:
- Stream open fails → Exception thrown
- Echo mismatch → Exception thrown
- Timeout → Exception thrown
- Success → RTT returned in milliseconds
</details>

<details>
<summary>Hint: CompletableFuture Chaining</summary>

jvm-libp2p uses CompletableFuture for async operations:

**Chaining Operations**:
```kotlin
node.network.newStream("/ipfs/ping/1.0.0", peerId)
    .thenCompose { stream -> ping.initChannel(stream).controller }
    .thenCompose { controller -> controller.ping() }
    .thenAccept { rtt -> println("RTT: ${rtt}ms") }
    .exceptionally { err ->
        println("Error: ${err.message}")
        null
    }
```

**Why chain?**
- Keeps code readable and sequential
- Proper error propagation
- Non-blocking by default
- Can add timeouts at any stage

**Blocking when needed**:
```kotlin
val rtt = future.get(10, TimeUnit.SECONDS)
```

Use `.get()` only when you need to wait for results synchronously.
</details>

## Complete Solution

Here's the full working implementation:

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

    // Create a libp2p host with TCP transport, security, multiplexing, and ping
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
        }
        network {
            listen("/ip4/0.0.0.0/tcp/0")
        }
    }

    // Set up connection event handler
    node.network.connectionsManager.addConnectionHandler { conn ->
        println("New connection established: ${conn.secureSession().remoteId}")
        conn.closeFuture().thenAccept {
            println("Connection closed: ${conn.secureSession().remoteId}")
        }
    }

    // Start the host
    node.start().get()

    // Print the peer ID
    println("Local peer id: ${node.peerId}")

    // Print listening addresses
    println("Listening on:")
    for (addr in node.listenAddresses()) {
        println("  $addr/p2p/${node.peerId}")
    }

    println("Ping protocol initialized")

    // Parse remote peer addresses
    val remotePeersStr = System.getenv("REMOTE_PEERS") ?: ""
    val remotePeers = mutableListOf<Multiaddr>()

    if (remotePeersStr.isNotEmpty()) {
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
    } else {
        val checkpointAddr = "/ip4/147.75.77.187/tcp/4001/p2p/QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN"
        println("No REMOTE_PEERS specified, using checkpoint server")
        remotePeers.add(Multiaddr(checkpointAddr))
    }

    // Dial remote peers
    val connectionFutures = mutableListOf<CompletableFuture<Void>>()

    for (addr in remotePeers) {
        val peerId = addr.peerId
        if (peerId == null) {
            println("Multiaddress $addr does not contain peer ID, skipping")
            continue
        }

        println("Dialing peer $peerId at $addr")

        try {
            val connFuture = node.network.connect(addr).toVoidCompletableFuture()
            connectionFutures.add(connFuture)

            connFuture.thenAccept {
                println("Connected to: $peerId")
            }.exceptionally { err ->
                println("Failed to connect to $peerId: ${err.message}")
                null
            }
        } catch (e: Exception) {
            println("Error dialing $peerId: ${e.message}")
        }
    }

    // Wait for all connections to complete (with timeout)
    try {
        CompletableFuture.allOf(*connectionFutures.toTypedArray())
            .get(30, TimeUnit.SECONDS)
    } catch (e: Exception) {
        println("Some connection attempts timed out or failed")
    }

    // Get connected peers
    val connectedPeers = node.network.connectionsManager.connections
        .map { it.secureSession().remoteId }
        .distinct()

    if (connectedPeers.isEmpty()) {
        println("No peers connected, exiting")
        node.stop().get()
        return
    }

    // Ping each connected peer
    println("\nPinging connected peers...")

    val ping = Ping()

    for (peerId in connectedPeers) {
        println("Pinging $peerId...")

        try {
            node.network.newStream("/ipfs/ping/1.0.0", peerId)
                .thenCompose { stream ->
                    ping.initChannel(stream).controller
                }.thenCompose { controller ->
                    controller.ping()
                }.thenAccept { rtt ->
                    println("Ping to $peerId successful: RTT = ${rtt}ms")
                }.exceptionally { err ->
                    println("Ping to $peerId failed: ${err.message}")
                    null
                }.get(10, TimeUnit.SECONDS)
        } catch (e: Exception) {
            println("Error pinging $peerId: ${e.message}")
        }
    }

    // Keep the application running
    println("\nApplication running. Press Ctrl+C to exit.")
    Thread.sleep(TimeUnit.SECONDS.toMillis(30))

    // Shut down gracefully
    node.stop().get()
    println("Shutting down...")
}
```

## What You've Learned

Congratulations! You've successfully:

- **Implemented your first libp2p protocol** (ping)
- **Connected to a public checkpoint server**
- **Measured network latency** using RTT
- **Handled timeouts and errors** gracefully
- **Worked with CompletableFuture chaining** for async operations

## Key Concepts

### Protocol Abstraction
libp2p protocols are application-layer agreements on top of connections:
- Protocol ID (e.g., `/ipfs/ping/1.0.0`)
- Request/response pattern
- Stream-based communication
- Automatic negotiation

### Ping Protocol Architecture
- **Dual Role**: Acts as both client and server
- **Auto-Registration**: Registers handler when added to host
- **Stream-Based**: Each ping uses its own stream
- **Async Results**: CompletableFuture-based result delivery

### Timeout Management
- **Connection Timeouts**: For establishing connections (30s)
- **Operation Timeouts**: For individual operations (10s)
- **Future Timeouts**: Proper resource cleanup with `.get(timeout)`
- **Failure Handling**: Graceful degradation

### RTT Measurement
- **Round-Trip Time**: Total time for request + response in milliseconds
- **Network Indicator**: Measures connection quality
- **Use Cases**: Connection health, peer selection, diagnostics

## What's Next?

In the next lesson, you'll add QUIC transport alongside TCP. QUIC provides:
- Built-in encryption (no separate security layer)
- Faster connection establishment
- Better handling of packet loss
- UDP-based (better NAT traversal in some cases)

Next up: Lesson 4 - QUIC Transport!

## Additional Resources

- [libp2p ping specification](https://github.com/libp2p/specs/blob/master/ping/ping.md)
- [jvm-libp2p repository](https://github.com/libp2p/jvm-libp2p)
- [CompletableFuture guide](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/CompletableFuture.html)
- [libp2p protocols overview](https://docs.libp2p.io/concepts/protocols/)
