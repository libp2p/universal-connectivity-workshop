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

### go-libp2p Ping Service

go-libp2p provides a built-in ping service that handles all the protocol details:

```go
import "github.com/libp2p/go-libp2p/p2p/protocol/ping"

// Create ping service
pingService := ping.NewPingService(host)

// Ping a peer (returns a channel)
resultChan := pingService.Ping(ctx, peerID)

// Wait for result
result := <-resultChan
if result.Error != nil {
    log.Printf("Ping failed: %v", result.Error)
} else {
    log.Printf("Ping RTT: %s", result.RTT)
}
```

## Your Task

Extend your application to:
1. Create a ping service
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

Add the ping protocol import to your `app/main.go`:

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
    "github.com/libp2p/go-libp2p/core/event"
    "github.com/libp2p/go-libp2p/core/host"
    "github.com/libp2p/go-libp2p/core/network"
    "github.com/libp2p/go-libp2p/core/peer"
    "github.com/libp2p/go-libp2p/p2p/protocol/ping"
    "github.com/multiformats/go-multiaddr"
)
```

**What's new?**

- `time`: For timeout handling and RTT display
- `github.com/libp2p/go-libp2p/core/peer`: Peer ID types
- `github.com/libp2p/go-libp2p/p2p/protocol/ping`: The ping protocol

### Step 2: Create Ping Service

After creating your host, add the ping service:

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

    // Create host with TCP listener
    h, err := libp2p.New(
        libp2p.Identity(priv),
        libp2p.ListenAddrStrings(
            "/ip4/0.0.0.0/tcp/0",
        ),
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

    // Create ping service
    pingService := ping.NewPingService(h)
    fmt.Println("Ping service created")

    // More code will go here...
}
```

**What's happening here?**

- `ping.NewPingService(h)`: Creates a ping service attached to your host
  - Automatically registers the `/ipfs/ping/1.0.0` protocol handler
  - Handles both sending pings (client) and responding to pings (server)
  - Your node can now act as both ping initiator and responder

**Why automatic?** The ping service registers itself with your host's stream handlers. When a peer opens a ping stream to you, it's automatically handled.

### Step 3: Parse and Connect to Checkpoint Server

Add code to connect to remote peers with error handling:

```go
func main() {
    // ... previous code (ping service creation) ...

    // Parse remote peer addresses
    remotePeersStr := os.Getenv("REMOTE_PEERS")
    if remotePeersStr == "" {
        // Default to checkpoint server if no peers specified
        remotePeersStr = "/ip4/147.75.77.187/tcp/4001/p2p/QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN"
        fmt.Println("No REMOTE_PEERS specified, using checkpoint server")
    }

    var connectedPeers []peer.ID

    peerAddrs := strings.Split(remotePeersStr, ",")
    for _, addrStr := range peerAddrs {
        addrStr = strings.TrimSpace(addrStr)
        if addrStr == "" {
            continue
        }

        // Parse multiaddr
        addr, err := multiaddr.NewMultiaddr(addrStr)
        if err != nil {
            log.Printf("Invalid multiaddr %s: %v", addrStr, err)
            continue
        }

        // Extract peer info
        peerInfo, err := peer.AddrInfoFromP2pAddr(addr)
        if err != nil {
            log.Printf("Invalid peer address %s: %v", addr, err)
            continue
        }

        fmt.Printf("Dialing peer %s...\n", peerInfo.ID)

        // Connect with timeout
        connCtx, connCancel := context.WithTimeout(ctx, 30*time.Second)
        err = h.Connect(connCtx, *peerInfo)
        connCancel()

        if err != nil {
            log.Printf("Failed to connect to %s: %v", peerInfo.ID, err)
            continue
        }

        fmt.Printf("Connected to: %s\n", peerInfo.ID)
        connectedPeers = append(connectedPeers, peerInfo.ID)
    }

    if len(connectedPeers) == 0 {
        log.Fatal("Failed to connect to any peers")
    }

    // More code will go here...
}
```

**What's happening here?**

- **Default Checkpoint Server**: If `REMOTE_PEERS` is empty, we use the instructor's server
- **Timeout Context**: `context.WithTimeout(ctx, 30*time.Second)` ensures connections don't hang
  - If connection takes longer than 30 seconds, it's cancelled
  - Essential for unreliable networks
- **connCancel()**: Releases timeout context resources
  - Called immediately after Connect returns (success or failure)
  - Prevents context leaks
- **Track Connected Peers**: Store peer IDs in `connectedPeers` slice for pinging
- **Fail Fast**: Exit if no connections succeed

**Why 30 seconds?** TCP handshake + TLS/Noise negotiation + protocol negotiation can take time on slow networks.

### Step 4: Ping Connected Peers

Add code to ping each connected peer:

```go
func main() {
    // ... previous code (connecting to peers) ...

    // Subscribe to connection events
    sub, err := h.EventBus().Subscribe(new(event.EvtPeerConnectednessChanged))
    if err != nil {
        log.Fatalf("Failed to subscribe to events: %v", err)
    }
    defer sub.Close()

    // Handle events
    go func() {
        for e := range sub.Out() {
            evt := e.(event.EvtPeerConnectednessChanged)
            switch evt.Connectedness {
            case network.Connected:
                fmt.Printf("Connected to: %s\n", evt.Peer)
            case network.NotConnected:
                fmt.Printf("Disconnected from: %s\n", evt.Peer)
            }
        }
    }()

    // Ping each connected peer
    fmt.Println("\nPinging connected peers...")
    for _, peerID := range connectedPeers {
        // Create timeout context for ping
        pingCtx, pingCancel := context.WithTimeout(ctx, 10*time.Second)

        fmt.Printf("Pinging %s...\n", peerID)

        // Ping returns a channel that receives the result
        resultChan := pingService.Ping(pingCtx, peerID)

        // Wait for result
        result := <-resultChan
        pingCancel()

        if result.Error != nil {
            log.Printf("Ping to %s failed: %v", peerID, result.Error)
        } else {
            fmt.Printf("Ping to %s successful: RTT = %s\n", peerID, result.RTT)
        }
    }

    // Keep running
    fmt.Println("\nApplication running. Press Ctrl+C to exit.")
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

    <-sigCh
    fmt.Println("\nShutting down...")
}
```

**What's happening here?**

- **Ping Context**: Separate timeout for each ping (10 seconds)
  - Independent of connection timeout
  - Allows ping to fail without killing the connection
- **Result Channel**: `pingService.Ping()` returns a channel
  - Ping runs asynchronously
  - Result delivered via channel when complete
- **Blocking Receive**: `<-resultChan` waits for the ping result
  - Blocks current goroutine until result arrives or timeout
- **Result Handling**: Check `result.Error` first, then display `result.RTT`
  - RTT is a `time.Duration` (e.g., "15ms", "120ms")
- **Keep Running**: Wait for Ctrl+C to maintain connections

**Why channels?** Go's idiomatic way to handle asynchronous operations. The ping runs in the background, and you get the result when ready.

## Understanding the Complete Flow

Here's what happens when you run your application:

1. **Initialization**:
   - Generate keypair and create host
   - Register TCP transport
   - Create ping service (registers protocol handler)

2. **Connection Phase**:
   - Parse peer addresses (default to checkpoint server)
   - Dial each peer with timeout
   - Wait for connection establishment
   - Track successfully connected peers

3. **Ping Phase**:
   - For each connected peer:
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
cd en/go/03-ping-checkpoint

# Run with default checkpoint server
go run app/main.go

# Or specify custom peers
export REMOTE_PEERS="/ip4/147.75.77.187/tcp/4001/p2p/QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN"
go run app/main.go
```

Expected output:
```
Starting Universal Connectivity Application...
Local peer id: 12D3KooW...
Listening on:
  /ip4/127.0.0.1/tcp/54321/p2p/12D3KooW...
Ping service created
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
python check.py
```

### Docker Testing

```bash
cd en/go/03-ping-checkpoint
export PROJECT_ROOT=$(pwd)/../../..
export LESSON_PATH=en/go/03-ping-checkpoint

# Build and run
docker compose up --build

# Check results
python check.py
```

## Success Criteria

Your implementation should:
- ✅ Create a ping service successfully
- ✅ Connect to the checkpoint server (or custom peers)
- ✅ Successfully ping connected peers
- ✅ Display RTT measurements
- ✅ Handle connection and ping failures gracefully
- ✅ Keep running until interrupted

## Troubleshooting

### Common Issues

<details>
<summary>Connection Timeout</summary>

**Symptom**: "Failed to connect to peer: context deadline exceeded"

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

**Symptom**: "Ping failed: context deadline exceeded"

**Causes**:
1. Connection dropped after establishment
2. Peer doesn't support ping protocol
3. Network latency too high
4. Firewall blocking after initial connection

**Solutions**:
- Increase ping timeout to 30 seconds
- Check if peer is still connected: `h.Network().Connectedness(peerID)`
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
- Verify ping service was created: check logs for "Ping service created"
- Ensure peer is a proper libp2p node
- Try the official checkpoint server (should always work)
- Check libp2p version compatibility
</details>

<details>
<summary>No Peers Connected</summary>

**Symptom**: "Failed to connect to any peers"

**Causes**:
1. Invalid multiaddress format
2. All peers unreachable
3. Network connectivity issues

**Solutions**:
- Test with checkpoint server first (known good peer)
- Verify multiaddress format: `/ip4/IP/tcp/PORT/p2p/PEER_ID`
- Check DNS resolution: `nslookup bootstrap.libp2p.io`
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
<summary>Hint: Ping Service Details</summary>

The ping service in go-libp2p:

**As Initiator (Client)**:
```go
pingService := ping.NewPingService(host)
resultChan := pingService.Ping(ctx, peerID)
result := <-resultChan
```

**As Responder (Server)**:
- Automatically handled by the ping service
- No code needed!
- Service registers handler on creation

**Protocol ID**: `/ipfs/ping/1.0.0`

**How it works**:
1. Opens stream with protocol negotiation
2. Sends 32 random bytes
3. Waits for exact echo
4. Calculates time difference
5. Closes stream
6. Returns result via channel

**Error cases**:
- Stream open fails → `result.Error` set
- Echo mismatch → `result.Error` set
- Timeout → `result.Error` set
- Success → `result.RTT` contains duration
</details>

<details>
<summary>Hint: Context and Timeouts</summary>

Contexts in Go manage cancellation and timeouts:

**Connection Timeout**:
```go
connCtx, connCancel := context.WithTimeout(ctx, 30*time.Second)
defer connCancel()
err := h.Connect(connCtx, peerInfo)
```

**Ping Timeout**:
```go
pingCtx, pingCancel := context.WithTimeout(ctx, 10*time.Second)
defer pingCancel()
resultChan := pingService.Ping(pingCtx, peerID)
result := <-resultChan
```

**Best Practices**:
- Always call `cancel()` to release resources
- Use `defer cancel()` for automatic cleanup
- Separate timeouts for different operations
- Longer timeout for connection (30s) than ping (10s)

**Why separate contexts?**
- Connection can be slow (TCP handshake, encryption negotiation)
- Ping should be fast (just echo)
- Different failure modes need different timeouts
</details>

## Complete Solution

Here's the full working implementation:

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
    "github.com/libp2p/go-libp2p/core/event"
    "github.com/libp2p/go-libp2p/core/host"
    "github.com/libp2p/go-libp2p/core/network"
    "github.com/libp2p/go-libp2p/core/peer"
    "github.com/libp2p/go-libp2p/p2p/protocol/ping"
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
        ),
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

    // Create ping service
    pingService := ping.NewPingService(h)
    fmt.Println("Ping service created")

    // Parse remote peers
    remotePeersStr := os.Getenv("REMOTE_PEERS")
    if remotePeersStr == "" {
        remotePeersStr = "/ip4/147.75.77.187/tcp/4001/p2p/QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN"
        fmt.Println("No REMOTE_PEERS specified, using checkpoint server")
    }

    var connectedPeers []peer.ID

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
            continue
        }

        fmt.Printf("Connected to: %s\n", peerInfo.ID)
        connectedPeers = append(connectedPeers, peerInfo.ID)
    }

    if len(connectedPeers) == 0 {
        log.Fatal("Failed to connect to any peers")
    }

    // Subscribe to events
    sub, err := h.EventBus().Subscribe(new(event.EvtPeerConnectednessChanged))
    if err != nil {
        log.Fatalf("Failed to subscribe to events: %v", err)
    }
    defer sub.Close()

    go func() {
        for e := range sub.Out() {
            evt := e.(event.EvtPeerConnectednessChanged)
            switch evt.Connectedness {
            case network.Connected:
                fmt.Printf("Event: Connected to %s\n", evt.Peer)
            case network.NotConnected:
                fmt.Printf("Event: Disconnected from %s\n", evt.Peer)
            }
        }
    }()

    // Ping peers
    fmt.Println("\nPinging connected peers...")
    for _, peerID := range connectedPeers {
        pingCtx, pingCancel := context.WithTimeout(ctx, 10*time.Second)

        fmt.Printf("Pinging %s...\n", peerID)

        resultChan := pingService.Ping(pingCtx, peerID)
        result := <-resultChan
        pingCancel()

        if result.Error != nil {
            log.Printf("Ping to %s failed: %v", peerID, result.Error)
        } else {
            fmt.Printf("Ping to %s successful: RTT = %s\n", peerID, result.RTT)
        }
    }

    // Keep running
    fmt.Println("\nApplication running. Press Ctrl+C to exit.")
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

    <-sigCh
    fmt.Println("\nShutting down...")
}
```

## What You've Learned

Congratulations! You've successfully:

- **Implemented your first libp2p protocol** (ping)
- **Connected to a public checkpoint server**
- **Measured network latency** using RTT
- **Handled timeouts and errors** gracefully
- **Worked with Go channels** for async operations

## Key Concepts

### Protocol Abstraction
libp2p protocols are application-layer agreements on top of connections:
- Protocol ID (e.g., `/ipfs/ping/1.0.0`)
- Request/response pattern
- Stream-based communication
- Automatic negotiation

### Ping Service Architecture
- **Dual Role**: Acts as both client and server
- **Auto-Registration**: Registers handler on creation
- **Stream-Based**: Each ping uses its own stream
- **Async Results**: Channel-based result delivery

### Timeout Management
- **Connection Timeouts**: For establishing connections (30s)
- **Operation Timeouts**: For individual operations (10s)
- **Context Cancellation**: Proper resource cleanup
- **Failure Handling**: Graceful degradation

### RTT Measurement
- **Round-Trip Time**: Total time for request + response
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
- [go-libp2p ping protocol](https://pkg.go.dev/github.com/libp2p/go-libp2p/p2p/protocol/ping)
- [Context package](https://pkg.go.dev/context)
- [libp2p protocols overview](https://docs.libp2p.io/concepts/protocols/)
