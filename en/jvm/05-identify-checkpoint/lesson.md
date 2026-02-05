# Lesson 5: Identify Protocol Checkpoint

Welcome to another checkpoint! In this lesson, you'll use the Identify protocol to discover detailed information about connected peers. This protocol is fundamental to libp2p's capability negotiation and peer discovery.

## Learning Objectives

By the end of this lesson, you will:
- Understand the Identify protocol and its role in libp2p
- Access peer metadata through the peerstore
- Query supported protocols and agent versions
- Inspect observed addresses (NAT detection)
- Customize your node's identity information

## Background: The Identify Protocol

The **Identify protocol** (`/ipfs/id/1.0.0`) is automatically enabled in jvm-libp2p when you add it to your protocols. It exchanges metadata between peers immediately after connection:

### What Identify Shares

| Information | Description | Example |
|-------------|-------------|---------|
| **Peer ID** | Unique cryptographic identifier | `12D3KooW...` |
| **Agent Version** | Software name and version | `jvm-libp2p/1.1.1` |
| **Protocol Version** | libp2p protocol version | `ipfs/0.1.0` |
| **Supported Protocols** | List of protocols peer supports | `/ipfs/ping/1.0.0`, `/ipfs/id/1.0.0` |
| **Listen Addresses** | Addresses peer listens on | `/ip4/192.168.1.1/tcp/4001` |
| **Observed Address** | How peer sees you (NAT detection) | `/ip4/203.0.113.1/tcp/54321` |

### Why Identify Matters

1. **Protocol Negotiation**: Know what protocols peer supports before attempting to use them
2. **NAT Detection**: Discover your public address via observed addresses
3. **Version Compatibility**: Check if peer runs compatible software
4. **Debugging**: Identify what software and version peer is running
5. **Metrics**: Track network composition (agent versions, protocols)

### The Identify Flow

```
Peer A                           Peer B
  |                                 |
  |----------- Connect -----------→|
  |                                 |
  |← Open /ipfs/id/1.0.0 stream ---|
  |                                 |
  |-- Send Identify Message ------→|
  |                                 |
  |←- Send Identify Message -------|
  |                                 |
  Both peers now know about each other
```

Both peers initiate the identify exchange. The protocol is:
- **Bidirectional**: Both peers send their info
- **Automatic**: Happens immediately after connection
- **Cached**: Information stored in peerstore

## The Peerstore

The **peerstore** is libp2p's database of peer information. It stores:

- **Addresses**: Known multiaddresses for each peer
- **Protocols**: Supported protocols per peer
- **Keys**: Public keys (derived from peer IDs)
- **Metadata**: Custom key-value pairs
- **Agent Version**: Software identification

Accessing the peerstore:

```kotlin
node.peerstore  // Returns Peerstore interface
```

## Your Task

Extend your application to:
1. Add the Identify protocol
2. Set a custom agent version
3. Connect to a remote peer and exchange identify information
4. Query the peerstore for peer metadata
5. Display supported protocols
6. Show agent version information

## Step-by-Step Instructions

### Step 1: Add Required Imports

Update your imports in `app/src/main/kotlin/Main.kt`:

```kotlin
import io.libp2p.core.Host
import io.libp2p.core.crypto.KeyType
import io.libp2p.core.dsl.host
import io.libp2p.core.multiformats.Multiaddr
import io.libp2p.core.mux.StreamMuxerProtocol
import io.libp2p.etc.types.toVoidCompletableFuture
import io.libp2p.protocol.Identify
import io.libp2p.protocol.Ping
import io.libp2p.security.noise.NoiseXXSecureChannel
import io.libp2p.transport.tcp.TcpTransport
import java.util.concurrent.CompletableFuture
import java.util.concurrent.TimeUnit
```

**What's new?**

- `io.libp2p.protocol.Identify`: Identify protocol implementation
- `io.libp2p.protocol.Ping`: Ping protocol for connectivity testing

### Step 2: Configure Identify Protocol and Custom Agent Version

Add the Identify and Ping protocols to your host:

```kotlin
fun main() {
    println("Starting Universal Connectivity Application...")

    // Create a libp2p host with identify protocol
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
        }
        network {
            listen("/ip4/0.0.0.0/tcp/0")
        }
    }

    // Rest of code...
}
```

**What's happening here?**

- `protocols { }`: Block to configure application protocols
- `+Ping()`: Adds ping protocol for connectivity testing
- `+Identify()`: Adds identify protocol for peer discovery and capability exchange
  - Automatically advertises supported protocols
  - Shares listening addresses with peers
  - Uses default agent version `jvm/0.1`
- **Auto-negotiation**: Protocol exchange happens automatically on connection

**Why Identify?** Essential for peer discovery - lets other peers know what protocols you support and how to reach you!

### Step 3: Add Connection Event Handler

Add a connection handler to monitor when peers connect:

```kotlin
fun main() {
    // ... (after host creation) ...

    // Set up connection event handler
    node.network.connectionsManager.addConnectionHandler { conn ->
        println("New connection established: ${conn.secureSession().remoteId}")
        conn.closeFuture().thenAccept {
            println("Connection closed: ${conn.secureSession().remoteId}")
        }
    }

    // Start the host
    node.start().get()

    // Rest of code...
}
```

### Step 4: Query Peer Information After Connection

Add a function to display peer information:

```kotlin
fun displayPeerInfo(node: Host) {
    println("\n=== Peer Information ===")

    // Get all connected peers
    val peers = node.network.getPeers()

    if (peers.isEmpty()) {
        println("No connected peers")
        return
    }

    for (peerId in peers) {
        println("\nPeer ID: $peerId")

        // Get supported protocols
        val protocols = node.peerstore.getProtocols(peerId).get()
        if (protocols.isNotEmpty()) {
            println("Supported protocols (${protocols.size}):")
            for (protocol in protocols) {
                println("  - $protocol")
            }
        }

        // Get known addresses
        val addrs = node.peerstore.get(peerId).get()?.addresses ?: emptyList()
        if (addrs.isNotEmpty()) {
            println("Known addresses (${addrs.size}):")
            for (addr in addrs) {
                println("  - $addr")
            }
        }
    }

    println("\n=== End Peer Information ===")
}
```

**What's happening here?**

- `node.network.getPeers()`: Returns list of currently connected peer IDs
- `node.peerstore.getProtocols(peerId)`: Returns CompletableFuture of protocols peer supports
  - Example: `[/ipfs/ping/1.0.0, /ipfs/id/1.0.0]`
  - `.get()` blocks until result is available
- `node.peerstore.get(peerId)`: Returns peer information including addresses
  - Access via `.addresses` property

**Note**: In jvm-libp2p, the peerstore automatically stores information from the identify protocol exchange.

### Step 5: Connect to Remote Peer

Add code to connect to a remote peer (using a default checkpoint server if none specified):

```kotlin
fun main() {
    // ... (after printing listening addresses) ...

    // Parse remote peer addresses from environment variable
    val remotePeersStr = System.getenv("REMOTE_PEERS")
        ?: "/ip4/147.75.77.187/tcp/4001/p2p/QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN"

    if (remotePeersStr.isEmpty()) {
        println("No REMOTE_PEERS specified, using checkpoint server")
    }

    val connectionFutures = mutableListOf<CompletableFuture<Void>>()
    val connectedPeers = mutableListOf<String>()

    val peerAddrs = remotePeersStr.split(",")
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
                connectedPeers.add(peerId.toString())
            }.exceptionally { err ->
                println("Failed to connect to $peerId: ${err.message}")
                null
            }
        } catch (e: Exception) {
            println("Invalid multiaddr $trimmed: ${e.message}")
        }
    }

    // Wait for connections to complete
    try {
        CompletableFuture.allOf(*connectionFutures.toTypedArray())
            .get(30, TimeUnit.SECONDS)
    } catch (e: Exception) {
        println("Connection timeout or error: ${e.message}")
    }

    if (connectedPeers.isEmpty()) {
        println("Failed to connect to any peers")
        node.stop().get()
        return
    }

    // Rest of code...
}
```

### Step 6: Wait for Identify and Display Information

Add code to wait for the identify protocol to complete and display peer information:

```kotlin
fun main() {
    // ... (after connection code) ...

    // Give identify protocol time to complete
    println("\nWaiting for identify protocol to complete...")
    Thread.sleep(TimeUnit.SECONDS.toMillis(3))

    // Display peer information
    displayPeerInfo(node)

    // Test ping
    println("\nTesting ping...")
    for (peerId in node.network.getPeers()) {
        try {
            val pingProtocol = node.protocols.find { it is Ping } as? Ping
            if (pingProtocol != null) {
                val latency = pingProtocol.ping(peerId).get(10, TimeUnit.SECONDS)
                println("Ping to $peerId successful: RTT = ${latency.toMillis()}ms")
            }
        } catch (e: Exception) {
            println("Ping to $peerId failed: ${e.message}")
        }
    }

    // Keep running
    println("\nApplication running. Press Ctrl+C to exit.")
    Thread.sleep(TimeUnit.SECONDS.toMillis(30))

    // Shut down gracefully
    node.stop().get()
    println("Shutting down...")
}
```

**What's happening here?**

- `Thread.sleep(3000)`: Give time for identify protocol to complete
  - Identify runs automatically after connection
  - We need to wait for it to finish before querying peerstore
- `displayPeerInfo(node)`: Display all peer information
- **Ping test**: Use Ping protocol to verify connectivity
  - `pingProtocol.ping(peerId)`: Sends ping and returns CompletableFuture with latency
  - Confirms that peer is responsive

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
import io.libp2p.security.noise.NoiseXXSecureChannel
import io.libp2p.transport.tcp.TcpTransport
import java.util.concurrent.CompletableFuture
import java.util.concurrent.TimeUnit

fun displayPeerInfo(node: Host) {
    println("\n=== Peer Information ===")

    val peers = node.network.getPeers()

    if (peers.isEmpty()) {
        println("No connected peers")
        return
    }

    for (peerId in peers) {
        println("\nPeer ID: $peerId")

        try {
            val protocols = node.peerstore.getProtocols(peerId).get(2, TimeUnit.SECONDS)
            if (protocols.isNotEmpty()) {
                println("Supported protocols (${protocols.size}):")
                for (protocol in protocols) {
                    println("  - $protocol")
                }
            }
        } catch (e: Exception) {
            println("Could not get protocols: ${e.message}")
        }

        try {
            val peerInfo = node.peerstore.get(peerId).get(2, TimeUnit.SECONDS)
            val addrs = peerInfo?.addresses ?: emptyList()
            if (addrs.isNotEmpty()) {
                println("Known addresses (${addrs.size}):")
                for (addr in addrs) {
                    println("  - $addr")
                }
            }
        } catch (e: Exception) {
            println("Could not get addresses: ${e.message}")
        }
    }

    println("\n=== End Peer Information ===")
}

fun main() {
    println("Starting Universal Connectivity Application...")

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
            +Identify(agentVersion = "universal-connectivity-app/1.0.0")
        }
        network {
            listen("/ip4/0.0.0.0/tcp/0")
        }
    }

    node.network.connectionsManager.addConnectionHandler { conn ->
        println("New connection established: ${conn.secureSession().remoteId}")
        conn.closeFuture().thenAccept {
            println("Connection closed: ${conn.secureSession().remoteId}")
        }
    }

    node.start().get()

    println("Local peer id: ${node.peerId}")
    println("Agent version: universal-connectivity-app/1.0.0")

    println("Listening on:")
    for (addr in node.listenAddresses()) {
        println("  $addr/p2p/${node.peerId}")
    }

    val remotePeersStr = System.getenv("REMOTE_PEERS")
        ?: "/ip4/147.75.77.187/tcp/4001/p2p/QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN"

    if (System.getenv("REMOTE_PEERS") == null) {
        println("No REMOTE_PEERS specified, using checkpoint server")
    }

    val connectionFutures = mutableListOf<CompletableFuture<Void>>()
    val connectedPeers = mutableListOf<String>()

    val peerAddrs = remotePeersStr.split(",")
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
                connectedPeers.add(peerId.toString())
            }.exceptionally { err ->
                println("Failed to connect to $peerId: ${err.message}")
                null
            }
        } catch (e: Exception) {
            println("Invalid multiaddr $trimmed: ${e.message}")
        }
    }

    try {
        CompletableFuture.allOf(*connectionFutures.toTypedArray())
            .get(30, TimeUnit.SECONDS)
    } catch (e: Exception) {
        println("Connection timeout or error: ${e.message}")
    }

    if (connectedPeers.isEmpty()) {
        println("Failed to connect to any peers")
        node.stop().get()
        return
    }

    println("\nWaiting for identify protocol to complete...")
    Thread.sleep(TimeUnit.SECONDS.toMillis(3))

    displayPeerInfo(node)

    println("\nTesting ping...")
    for (peerId in node.network.getPeers()) {
        try {
            val pingProtocol = node.protocols.find { it is Ping } as? Ping
            if (pingProtocol != null) {
                val latency = pingProtocol.ping(peerId).get(10, TimeUnit.SECONDS)
                println("Ping to $peerId successful: RTT = ${latency.toMillis()}ms")
            }
        } catch (e: Exception) {
            println("Ping to $peerId failed: ${e.message}")
        }
    }

    println("\nApplication running. Press Ctrl+C to exit.")
    Thread.sleep(TimeUnit.SECONDS.toMillis(30))

    node.stop().get()
    println("Shutting down...")
}
```

## Testing Your Implementation

### Local Testing

```bash
cd en/jvm/05-identify-checkpoint/app
./gradlew run
```

Expected output:
```
Starting Universal Connectivity Application...
Local peer id: 12D3KooW...
Agent version: universal-connectivity-app/1.0.0
Listening on:
  /ip4/127.0.0.1/tcp/54321/p2p/12D3KooW...
No REMOTE_PEERS specified, using checkpoint server
Dialing peer QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN...
Connected to: QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN

Waiting for identify protocol to complete...

=== Peer Information ===

Peer ID: QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN
Supported protocols (15):
  - /ipfs/ping/1.0.0
  - /ipfs/id/1.0.0
  - /ipfs/id/push/1.0.0
  ... (more protocols)
Known addresses (4):
  - /ip4/147.75.77.187/tcp/4001
  ... (more addresses)

=== End Peer Information ===

Testing ping...
Ping to QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN successful: RTT = 45ms

Application running. Press Ctrl+C to exit.
```

### Two-Instance Test

Test identify between your own instances:

#### Terminal 1:
```bash
cd en/jvm/05-identify-checkpoint/app
./gradlew run
```

Note one of the listening addresses.

#### Terminal 2:
```bash
export REMOTE_PEERS="<address from Terminal 1>"
./gradlew run
```

Both should display each other's information, including your custom agent version!

### Automated Testing

```bash
cd en/jvm/05-identify-checkpoint
python check.py
```

### Docker Testing

```bash
cd en/jvm/05-identify-checkpoint
docker compose up --build
python check.py
```

## Success Criteria

Your implementation should:
- ✅ Set custom agent version
- ✅ Add Identify protocol
- ✅ Connect to remote peers
- ✅ Display supported protocols for peers
- ✅ Show known peer addresses
- ✅ Successfully ping connected peers

## Troubleshooting

<details>
<summary>Empty Protocol List</summary>

**Symptom**: `getProtocols()` returns empty list or timeout

**Causes**:
1. Identify not yet completed
2. Connection closed before identify
3. Peer doesn't support identify

**Solutions**:
- Add `Thread.sleep(3000)` after connection
- Check connection still active
- Try with known-good peer (checkpoint server)
- Verify Identify protocol is added to host
</details>

<details>
<summary>Missing Identify Protocol</summary>

**Symptom**: No peer information available

**Causes**:
1. Forgot to add Identify to protocols block
2. Identify not configured properly

**Solutions**:
- Verify `+Identify(...)` is in protocols block
- Must be inside host { protocols { } } builder
- Check that both peers have Identify enabled
</details>

<details>
<summary>Custom Agent Version Not Appearing</summary>

**Symptom**: Your agent version not shown to other peers

**Causes**:
1. Forgot `agentVersion` parameter
2. Parameter not passed to Identify
3. Other peer not checking agent version

**Solutions**:
- Verify: `+Identify(agentVersion = "...")`
- Test with two of your own instances
- Check other peer's logs for your version
</details>

## Hints

<details>
<summary>Hint: Peerstore Operations</summary>

Common peerstore operations in jvm-libp2p:

**Get Protocols**:
```kotlin
val protocols = node.peerstore.getProtocols(peerId).get()
```

**Get Peer Info**:
```kotlin
val peerInfo = node.peerstore.get(peerId).get()
val addresses = peerInfo?.addresses ?: emptyList()
```

**Get Connected Peers**:
```kotlin
val peers = node.network.getPeers()
```

**Check if Peer Supports Protocol**:
```kotlin
val protocols = node.peerstore.getProtocols(peerId).get()
if ("/ipfs/ping/1.0.0" in protocols) {
    // Peer supports ping!
}
```
</details>

<details>
<summary>Hint: Accessing Protocols</summary>

To use a protocol after adding it to the host:

```kotlin
// Find Ping protocol
val pingProtocol = node.protocols.find { it is Ping } as? Ping
if (pingProtocol != null) {
    val latency = pingProtocol.ping(peerId).get()
    println("Latency: ${latency.toMillis()}ms")
}

// Find Identify protocol
val identifyProtocol = node.protocols.find { it is Identify } as? Identify
```

Protocols added in the builder are accessible via `node.protocols` list.
</details>

<details>
<summary>Hint: Async Operations</summary>

jvm-libp2p uses CompletableFuture for async operations:

```kotlin
// Wait for result with timeout
val result = future.get(5, TimeUnit.SECONDS)

// Non-blocking callback
future.thenAccept { result ->
    println("Got result: $result")
}.exceptionally { error ->
    println("Error: ${error.message}")
    null
}

// Combine multiple futures
CompletableFuture.allOf(*futures.toTypedArray()).get()
```
</details>

## What You've Learned

Congratulations! You've successfully:

- **Used the Identify protocol** to discover peer information
- **Queried the peerstore** for protocols and metadata
- **Set custom agent version** for your application
- **Understood peer discovery** through automatic information exchange
- **Completed another checkpoint** with real-world connectivity

## Key Concepts

### Identify Protocol
- **Automatic Exchange**: Runs immediately after connection
- **Bidirectional**: Both peers learn about each other
- **Essential Metadata**: Protocols, versions, addresses
- **Foundation**: Basis for capability negotiation

### Peerstore
- **Central Database**: All peer information in one place
- **Persistent**: Information survives across connections
- **Queryable**: Easy access to peer capabilities
- **Automatic**: Populated by identify protocol

### Agent Version
- **Identification**: What software is running
- **Debugging**: Track down version-specific issues
- **Metrics**: Network composition analysis
- **Production**: Essential for operational visibility

### Protocol Discovery
- **Capability Negotiation**: Know what peer can do
- **Graceful Degradation**: Handle missing protocols
- **Version Compatibility**: Check protocol support
- **Future-Proof**: Add new protocols dynamically

## What's Next?

You've now mastered the fundamentals of jvm-libp2p:
- Identity and peer ID generation
- TCP transport and connection handling
- Identify protocol for peer discovery
- Ping protocol for connectivity testing

These building blocks form the foundation for more advanced libp2p features like:
- DHT (Distributed Hash Table)
- PubSub (Publish-Subscribe messaging)
- Relay and NAT traversal
- Custom protocols

Next up: Building custom protocols and advanced connectivity patterns!

## Additional Resources

- [Identify protocol specification](https://github.com/libp2p/specs/blob/master/identify/README.md)
- [jvm-libp2p documentation](https://github.com/libp2p/jvm-libp2p)
- [libp2p concepts](https://docs.libp2p.io/concepts/)
- [Peerstore design](https://docs.libp2p.io/concepts/fundamentals/peers/)
