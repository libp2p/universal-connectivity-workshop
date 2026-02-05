# Lesson 2: Transport Layer - TCP Connection

Building on your basic libp2p host, in this lesson you'll learn about transport layers and establish your first peer-to-peer connections using TCP.

## Learning Objectives

By the end of this lesson, you will:
- Understand libp2p's transport abstraction
- Configure TCP transport with listening addresses
- Parse and use multiaddresses for peer connections
- Dial remote peers and handle connection events
- Monitor connection lifecycle

## Background: Transport Layers in libp2p

In libp2p, **transports** handle the low-level network communication. A transport defines how data travels between peers. jvm-libp2p supports multiple transports:

- **TCP**: Reliable, ordered, connection-oriented (like HTTP)
- **QUIC**: Modern UDP-based with built-in encryption
- **WebSocket**: HTTP-based upgrade for firewall traversal

The transport layer is just one part of the complete libp2p networking stack.

## Transport Stack

The libp2p stack looks like this when using TCP:

```
Application protocols (ping, identify, etc.)
    ↕
Multiplexer (Yamux/Mplex)
    ↕
Security (Noise/TLS)
    ↕
Transport (TCP)
    ↕
Network (IP)
```

Each layer serves a specific purpose:
- **Transport**: Establishes connections between network endpoints
- **Security**: Encrypts data and authenticates peers
- **Multiplexer**: Allows multiple independent streams over one connection
- **Application**: Your protocols and data

## Multiaddresses

libp2p uses **multiaddresses** to specify network endpoints. Unlike traditional addresses (like `192.168.1.1:8080`), multiaddresses are self-describing and composable.

Examples:
```
/ip4/127.0.0.1/tcp/4001
/ip6/::1/tcp/4001
/ip4/192.168.1.1/tcp/4001/p2p/12D3KooWJ7GFE...
```

Format breakdown:
- `/ip4/127.0.0.1`: IPv4 address
- `/tcp/4001`: TCP port
- `/p2p/12D3KooW...`: Peer ID (optional but useful for dialing)

## Your Task

Extend your application to:
1. Configure TCP transport on your host
2. Listen on a TCP address for incoming connections
3. Parse remote peer addresses from an environment variable
4. Dial remote peers
5. Handle and log connection events

## Step-by-Step Instructions

### Step 1: Add Required Imports

Update your imports in `app/src/main/kotlin/Main.kt`:

```kotlin
import io.libp2p.core.Host
import io.libp2p.core.PeerId
import io.libp2p.core.crypto.KeyType
import io.libp2p.core.dsl.host
import io.libp2p.core.multiformats.Multiaddr
import io.libp2p.core.mux.StreamMuxerProtocol
import io.libp2p.etc.types.toVoidCompletableFuture
import io.libp2p.security.noise.NoiseXXSecureChannel
import io.libp2p.transport.tcp.TcpTransport
import java.util.concurrent.CompletableFuture
import java.util.concurrent.TimeUnit
```

**What's new?**

- `io.libp2p.transport.tcp.TcpTransport`: TCP transport implementation
- `io.libp2p.security.noise.NoiseXXSecureChannel`: Noise protocol for secure channels
- `io.libp2p.core.mux.StreamMuxerProtocol`: Multiplexing protocols (Mplex/Yamux)
- `io.libp2p.core.multiformats.Multiaddr`: Multiaddress parsing and manipulation
- `CompletableFuture`: For handling async connection operations

### Step 2: Configure Transport and Security

Modify your host creation to include transport, security, and multiplexing:

```kotlin
fun main() {
    println("Starting Universal Connectivity Application...")

    // Create a libp2p host with TCP transport, security, and multiplexing
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
        network {
            listen("/ip4/0.0.0.0/tcp/0")
        }
    }

    // More code will go here...
}
```

**What's happening here?**

- `transports { +::TcpTransport }`: Adds TCP transport to the host
  - Uses Kotlin's function reference syntax (`::`)
  - The `+` operator adds the transport to the builder
- `secureChannels { +::NoiseXXSecureChannel }`: Adds Noise encryption
  - Required for secure communication between peers
  - Noise is a modern cryptographic framework
- `muxers { +StreamMuxerProtocol.Mplex }`: Adds Mplex multiplexing
  - Allows multiple streams over a single connection
  - Mplex is lightweight and efficient
- `network { listen("/ip4/0.0.0.0/tcp/0") }`: Configures listening
  - `0.0.0.0`: Binds to all network interfaces
  - Port `0`: OS assigns a random available port

**Why these components?** TCP provides reliable transport, Noise ensures security, and Mplex enables efficient multiplexing. Together they form a complete networking stack.

### Step 3: Start Host and Print Listening Addresses

Add code to start the host and display its listening addresses:

```kotlin
fun main() {
    // ... previous code (host creation) ...

    // Start the host
    node.start().get()

    // Print the peer ID
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

- `node.start().get()`: Starts the host and blocks until ready
- `node.listenAddresses()`: Returns list of multiaddresses the host is listening on
- We append `/p2p/${node.peerId}` to create full dialable addresses
- Full addresses let other peers know both where and who to connect to

**Why print full addresses?** Other peers need the complete address including peer ID to establish authenticated connections.

### Step 4: Parse Remote Peer Addresses

Add code to parse peer addresses from an environment variable:

```kotlin
fun main() {
    // ... previous code (printing addresses) ...

    // Parse remote peer addresses from environment variable
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
    }

    // More code will go here...
}
```

**What's happening here?**

- `System.getenv("REMOTE_PEERS")`: Reads environment variable
- Expected format: comma-separated multiaddresses
  - Example: `/ip4/192.168.1.1/tcp/4001/p2p/12D3KooW...,/ip4/10.0.0.1/tcp/4001/p2p/12D3KooW...`
- `Multiaddr(trimmed)`: Parses string into Multiaddr object
- We catch exceptions for invalid addresses but continue (graceful degradation)

### Step 5: Dial Remote Peers

Add code to connect to the parsed remote peers:

```kotlin
fun main() {
    // ... previous code (parsing remote peers) ...

    // Dial remote peers
    val connectionFutures = mutableListOf<CompletableFuture<Void>>()

    for (addr in remotePeers) {
        // Extract peer ID from multiaddr
        val peerId = addr.peerId
        if (peerId == null) {
            println("Multiaddress $addr does not contain peer ID, skipping")
            continue
        }

        println("Dialing peer $peerId at $addr")

        // Connect to the peer
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

    // More code will go here...
}
```

**What's happening here?**

- `addr.peerId`: Extracts PeerId from the multiaddress
  - Returns `null` if the address doesn't contain a peer ID component
- `node.network.connect(addr)`: Initiates connection to the peer
  - Returns a `CompletableFuture` for async handling
  - Connection happens in the background
- `toVoidCompletableFuture()`: Converts result to Void future
- `.thenAccept { }`: Success callback when connection establishes
- `.exceptionally { }`: Error handler for connection failures

**Why CompletableFuture?** jvm-libp2p is async-first. CompletableFuture allows non-blocking operations with proper error handling.

### Step 6: Add Connection Event Handling

Add a connection handler to monitor peer connections:

```kotlin
fun main() {
    // ... at the beginning after host creation ...

    // Set up connection event handler
    node.network.connectionsManager.addConnectionHandler { conn ->
        println("New connection established: ${conn.secureSession().remoteId}")
        conn.closeFuture().thenAccept {
            println("Connection closed: ${conn.secureSession().remoteId}")
        }
    }

    // ... rest of the code ...
}
```

**What's happening here?**

- `node.network.connectionsManager`: Manages all network connections
- `addConnectionHandler { }`: Registers callback for new connections
  - Called whenever a connection is established (incoming or outgoing)
- `conn.secureSession().remoteId`: Gets the remote peer's ID
- `conn.closeFuture()`: Future that completes when connection closes
  - Allows us to detect disconnections

**Why connection handlers?** They provide visibility into network activity and allow you to react to peer connections/disconnections.

### Step 7: Keep Running and Clean Shutdown

Add code to keep the application running:

```kotlin
fun main() {
    // ... all previous code ...

    // Wait for all connections to complete (with timeout)
    try {
        CompletableFuture.allOf(*connectionFutures.toTypedArray())
            .get(5, TimeUnit.SECONDS)
    } catch (e: Exception) {
        // Connection attempts timed out or failed
    }

    // Keep the application running
    println("Host running. Press Ctrl+C to exit.")
    Thread.sleep(TimeUnit.SECONDS.toMillis(30))

    // Shut down gracefully
    node.stop().get()
    println("Shutting down...")
}
```

**What's happening here?**

- `CompletableFuture.allOf(...)`: Waits for all connection attempts
  - Takes array of futures and combines them
  - `.get(5, TimeUnit.SECONDS)`: Waits up to 5 seconds
- `Thread.sleep(...)`: Keeps host alive for 30 seconds
  - In production, use signal handlers instead
- `node.stop().get()`: Stops host and waits for cleanup
  - Ensures all resources are released properly

## Understanding the Flow

Here's what happens when you run your program:

1. **Host Creation**: libp2p initializes with TCP, Noise, and Mplex
2. **Start**: Network stack activates and starts listening
3. **Address Display**: Shows where peers can reach you
4. **Parsing**: Reads and validates remote peer addresses
5. **Dialing**: Initiates connections to remote peers asynchronously
6. **Connection Events**: Monitors connection establishment/closure
7. **Waiting**: Keeps host running
8. **Cleanup**: Closes connections and releases resources

## Testing Your Implementation

### Manual Testing - Two Nodes

#### Terminal 1 (Listener):
```bash
cd en/jvm/02-tcp-transport/app
./gradlew run
```

Note the output - you'll see something like:
```
Starting Universal Connectivity Application...
Local peer id: 12D3KooWJ7GFE...
Listening on:
  /ip4/127.0.0.1/tcp/54321/p2p/12D3KooWJ7GFE...
  /ip4/192.168.1.100/tcp/54321/p2p/12D3KooWJ7GFE...
Host running. Press Ctrl+C to exit.
```

#### Terminal 2 (Dialer):
```bash
# Use the full multiaddr from Terminal 1
export REMOTE_PEERS="/ip4/127.0.0.1/tcp/54321/p2p/12D3KooWJ7GFE..."
./gradlew run
```

You should see:
- Terminal 2: "Dialing peer 12D3KooWJ7GFE..."
- Terminal 2: "Connected to: 12D3KooW..."
- Terminal 1: "New connection established: 12D3KooW..."

### Automated Checking

If using the workshop tool, press `c` to check your solution.

For manual testing:
```bash
cd ..  # Back to lesson directory
python check.py
```

## Success Criteria

Your implementation should:
- ✅ Display startup message and peer ID
- ✅ Configure TCP transport with Noise and Mplex
- ✅ Listen on TCP port (shown in output)
- ✅ Parse REMOTE_PEERS environment variable
- ✅ Dial remote peers successfully
- ✅ Log connection establishment
- ✅ Log connection closure

## Hints

<details>
<summary>Hint: Multiaddress Format</summary>

Valid multiaddresses have this structure:
```
/ip4/192.168.1.1/tcp/4001/p2p/12D3KooWJ7GFE...
 │    │            │    │    │   │
 │    └─ IP addr   │    │    │   └─ Peer ID
 │                 │    │    └─ Protocol component
 │                 │    └─ Port
 │                 └─ Protocol component
 └─ Protocol component
```

Common mistakes:
- Missing `/p2p/` component: Need peer ID to dial
- Wrong protocol: `/tcp/` for TCP
- Invalid peer ID: Must start with "12D3KooW" for Ed25519

In Kotlin:
```kotlin
val addr = Multiaddr("/ip4/127.0.0.1/tcp/4001/p2p/12D3KooW...")
val peerId = addr.peerId  // Extracts PeerId component
```
</details>

<details>
<summary>Hint: Connection Failures</summary>

If connections fail:

1. **Check the multiaddress format**: Must include `/p2p/<peer-id>`
2. **Verify network reachability**: Can you ping the IP?
3. **Check firewalls**: Port may be blocked
4. **Confirm peer is listening**: Is the other peer running?
5. **Try localhost first**: Use `/ip4/127.0.0.1/...` for testing

Common errors:
- "no peer ID in multiaddr": Missing `/p2p/` component
- Connection refused: Peer not listening or firewall blocking
- Timeout: Network unreachable or slow connection
</details>

<details>
<summary>Hint: Connection Handlers</summary>

jvm-libp2p uses connection handlers for notifications:

```kotlin
// Add handler for new connections
node.network.connectionsManager.addConnectionHandler { conn ->
    val remotePeer = conn.secureSession().remoteId
    println("Connected to: $remotePeer")

    // Handle disconnection
    conn.closeFuture().thenAccept {
        println("Disconnected from: $remotePeer")
    }
}
```

Handlers are called for both incoming and outgoing connections.
</details>

<details>
<summary>Hint: Kotlin DSL Syntax</summary>

The jvm-libp2p DSL uses Kotlin's type-safe builders:

```kotlin
val host = host {
    // Identity configuration
    identity {
        random(KeyType.ED25519)
    }

    // Add transports (:: is function reference)
    transports {
        +::TcpTransport  // + operator adds transport
    }

    // Add secure channels
    secureChannels {
        +::NoiseXXSecureChannel
    }

    // Add multiplexers
    muxers {
        +StreamMuxerProtocol.Mplex
    }

    // Network configuration
    network {
        listen("/ip4/0.0.0.0/tcp/0")
    }
}
```

The `+` operator is shorthand for adding components to the builder.
</details>

## Hint - Complete Solution

Here's the complete working solution:

```kotlin
import io.libp2p.core.Host
import io.libp2p.core.crypto.KeyType
import io.libp2p.core.dsl.host
import io.libp2p.core.multiformats.Multiaddr
import io.libp2p.core.mux.StreamMuxerProtocol
import io.libp2p.etc.types.toVoidCompletableFuture
import io.libp2p.security.noise.NoiseXXSecureChannel
import io.libp2p.transport.tcp.TcpTransport
import java.util.concurrent.CompletableFuture
import java.util.concurrent.TimeUnit

fun main() {
    println("Starting Universal Connectivity Application...")

    // Create a libp2p host with TCP transport, security, and multiplexing
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

    // Parse remote peer addresses from environment variable
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
    }

    // Dial remote peers
    val connectionFutures = mutableListOf<CompletableFuture<Void>>()

    for (addr in remotePeers) {
        // Extract peer ID from multiaddr
        val peerId = addr.peerId
        if (peerId == null) {
            println("Multiaddress $addr does not contain peer ID, skipping")
            continue
        }

        println("Dialing peer $peerId at $addr")

        // Connect to the peer
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
            .get(5, TimeUnit.SECONDS)
    } catch (e: Exception) {
        // Connection attempts timed out or failed
    }

    // Keep the application running
    println("Host running. Press Ctrl+C to exit.")
    Thread.sleep(TimeUnit.SECONDS.toMillis(30))

    // Shut down gracefully
    node.stop().get()
    println("Shutting down...")
}
```

## What's Next?

Excellent! You've successfully configured TCP transport and established peer-to-peer connections. You now understand:

- **Transport Layer**: How libp2p handles network communication
- **Multiaddresses**: Self-describing, composable network addresses
- **Listening and Dialing**: Acting as both server and client
- **Connection Events**: Monitoring network activity
- **Security and Multiplexing**: Building a complete network stack

## Key Concepts

### Transport Abstraction
libp2p abstracts transport details, letting you focus on application logic. The same code works with TCP, QUIC, WebSocket, etc.

### Multiaddresses
Unlike traditional "IP:port", multiaddresses describe the full path to a peer:
- Self-describing protocols
- Composable (can chain multiple protocols)
- Future-proof (new protocols can be added)

### Security First
jvm-libp2p requires security channels (like Noise) for all connections:
- Encrypts all traffic
- Authenticates peer identities
- Prevents tampering

### Multiplexing
Multiplexers like Mplex allow:
- Multiple streams over one connection
- Efficient resource usage
- Reduced connection overhead

In the next lesson, you'll add your first protocol (ping) and connect to the instructor's server for your first checkpoint!

## Additional Resources

- [Multiaddr specification](https://github.com/multiformats/multiaddr)
- [libp2p transports](https://docs.libp2p.io/concepts/transports/overview/)
- [Noise protocol](https://noiseprotocol.org/)
- [jvm-libp2p examples](https://github.com/libp2p/jvm-libp2p/tree/develop/examples)
