# Lesson 4: QUIC Transport

In this lesson, you'll add QUIC transport alongside TCP, giving your application multiple transport options for improved connectivity and performance. QUIC is a modern, UDP-based transport with built-in encryption and improved performance characteristics.

## Learning Objectives

By the end of this lesson, you will:
- Understand QUIC and its advantages over TCP
- Configure multiple transports in libp2p
- Listen on both TCP and QUIC simultaneously
- Understand transport selection and fallback
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

Extend your application to:
1. Add QUIC transport alongside TCP
2. Listen on both TCP and QUIC ports
3. Display both types of listening addresses
4. Connect to peers using either or both transports
5. Ping peers to verify connectivity

## Step-by-Step Instructions

### Step 1: Update Host Configuration

The good news: QUIC is enabled by default in go-libp2p! You just need to add a UDP listening address.

Update your host creation in `app/main.go`:

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

    // Create host with TCP and QUIC listeners
    h, err := libp2p.New(
        libp2p.Identity(priv),
        libp2p.ListenAddrStrings(
            "/ip4/0.0.0.0/tcp/0",          // TCP transport
            "/ip4/0.0.0.0/udp/0/quic-v1",  // QUIC transport
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

    // Rest of your code...
}
```

**What's happening here?**

- `"/ip4/0.0.0.0/tcp/0"`: TCP listener (from previous lesson)
- `"/ip4/0.0.0.0/udp/0/quic-v1"`: **NEW** - QUIC listener
  - Uses UDP instead of TCP
  - Port `0` for OS-assigned random port
  - `/quic-v1` indicates QUIC protocol version 1
- Both transports use the same private key and peer ID
- libp2p automatically handles both simultaneously

**Why "quic-v1"?** This is the multiaddress component for QUIC version 1 (RFC 9000). Earlier versions used `/quic`, but `quic-v1` is the current standard.

### Step 2: Understand the Multiaddress Format

Your application will now show addresses like:

```
Listening on:
  /ip4/127.0.0.1/tcp/54321/p2p/12D3KooW...       ← TCP
  /ip4/192.168.1.100/tcp/54321/p2p/12D3KooW...   ← TCP (LAN)
  /ip4/127.0.0.1/udp/54322/quic-v1/p2p/12D3KooW... ← QUIC
  /ip4/192.168.1.100/udp/54322/quic-v1/p2p/12D3KooW... ← QUIC (LAN)
```

Notice:
- **TCP addresses**: `/tcp/PORT`
- **QUIC addresses**: `/udp/PORT/quic-v1`
- Both share the same peer ID
- Ports may differ (OS assigns independently)

### Step 3: No Changes Needed for Connection Code!

Here's the beautiful part: **your connection code doesn't change**. When you dial a peer with multiple transports:

```go
// This peer has both TCP and QUIC addresses
addr, _ := multiaddr.NewMultiaddr(
    "/ip4/147.75.77.187/tcp/4001/p2p/QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN"
)
peerInfo, _ := peer.AddrInfoFromP2pAddr(addr)

// h.Connect automatically tries all available transports
h.Connect(ctx, *peerInfo)
```

libp2p will:
1. Look up all known addresses for the peer
2. Try TCP and QUIC in parallel
3. Use whichever succeeds first
4. Cache the working connection

### Step 4: Complete Implementation

Here's your complete `app/main.go` with QUIC support:

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

    // Create host with TCP and QUIC
    h, err := libp2p.New(
        libp2p.Identity(priv),
        libp2p.ListenAddrStrings(
            "/ip4/0.0.0.0/tcp/0",
            "/ip4/0.0.0.0/udp/0/quic-v1",
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

**That's it!** The only change from Lesson 3 is adding the QUIC listening address. Everything else works automatically!

## Understanding Transport Selection

### Scenario 1: Single Transport Connection

If a peer only advertises TCP:
```
/ip4/192.168.1.100/tcp/4001/p2p/12D3KooW...
```

libp2p will use TCP (no choice).

### Scenario 2: Multi-Transport Connection

If a peer advertises both:
```
/ip4/192.168.1.100/tcp/4001/p2p/12D3KooW...
/ip4/192.168.1.100/udp/4001/quic-v1/p2p/12D3KooW...
```

libp2p will:
1. Start both TCP and QUIC dial attempts
2. Use whichever succeeds first
3. Cancel the other attempt
4. Remember which transport worked for future connections

This is called "Happy Eyeballs" - racing connections for best performance!

### Scenario 3: Firewall Blocking

If TCP is blocked but UDP is allowed:
- TCP dial fails
- QUIC dial succeeds
- Connection established via QUIC
- Future dials prefer QUIC

## Testing Your Implementation

### Local Testing

```bash
cd en/go/04-quic-transport

# Build and run
go run app/main.go
```

Expected output:
```
Starting Universal Connectivity Application...
Local peer id: 12D3KooW...
Listening on:
  /ip4/127.0.0.1/tcp/54321/p2p/12D3KooW...
  /ip4/127.0.0.1/udp/54322/quic-v1/p2p/12D3KooW...
Ping service created
No REMOTE_PEERS specified, using checkpoint server
Dialing peer QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN...
Connected to: QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN

Pinging connected peers...
Pinging QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN...
Ping to QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN successful: RTT = 42ms

Application running. Press Ctrl+C to exit.
```

### Two-Instance Test (QUIC Connection)

#### Terminal 1:
```bash
cd en/go/04-quic-transport
go run app/main.go
```

Note the QUIC address from output:
```
/ip4/127.0.0.1/udp/54322/quic-v1/p2p/12D3KooWABC...
```

#### Terminal 2:
```bash
# Use the QUIC address from Terminal 1
export REMOTE_PEERS="/ip4/127.0.0.1/udp/54322/quic-v1/p2p/12D3KooWABC..."
go run app/main.go
```

Both terminals should show successful connection and ping via QUIC!

### Automated Checking

```bash
python check.py
```

### Docker Testing

```bash
cd en/go/04-quic-transport
export PROJECT_ROOT=$(pwd)/../../..
export LESSON_PATH=en/go/04-quic-transport

docker compose up --build
python check.py
```

## Success Criteria

Your implementation should:
- ✅ Listen on both TCP and QUIC transports
- ✅ Display both TCP and QUIC listening addresses
- ✅ Connect to remote peers (transport auto-selected)
- ✅ Successfully ping via either transport
- ✅ Handle both address types correctly

## Troubleshooting

<details>
<summary>Missing QUIC Addresses</summary>

**Symptom**: Only TCP addresses shown, no QUIC/UDP addresses

**Causes**:
1. Forgot to add QUIC listen address
2. UDP port binding failed
3. System doesn't support UDP

**Solutions**:
- Verify you added: `"/ip4/0.0.0.0/udp/0/quic-v1"`
- Check if another process is using UDP ports
- Run as administrator/root if permission denied
- Check for UDP firewall rules
</details>

<details>
<summary>QUIC Connection Failures</summary>

**Symptom**: "Failed to connect" when using QUIC address

**Causes**:
1. UDP blocked by firewall
2. NAT doesn't support UDP hole-punching
3. Peer's UDP port not reachable
4. QUIC version mismatch

**Solutions**:
- Test locally first (127.0.0.1)
- Check firewall allows UDP
- Verify QUIC address format: `/udp/PORT/quic-v1`
- Fall back to TCP address if QUIC fails
- Try updating go-libp2p to latest version
</details>

<details>
<summary>Slow QUIC Performance</summary>

**Symptom**: QUIC RTT higher than TCP

**Causes**:
1. Network prefers TCP routing
2. UDP rate limiting by ISP
3. Lossy network with UDP
4. CPU overhead of QUIC encryption

**Solutions**:
- This is normal in some networks
- TCP may be more optimized in your environment
- QUIC shines on mobile/lossy networks
- Performance depends on network conditions
- Both transports are valid, libp2p will choose best
</details>

## Hints

<details>
<summary>Hint: Transport Comparison</summary>

### TCP Transport
**Pros**:
- Universally supported
- Well-optimized by networks
- Predictable behavior
- Mature debugging tools

**Cons**:
- Slower connection establishment (2-3 RTTs)
- Head-of-line blocking
- Can't survive IP changes
- Requires separate encryption layer

### QUIC Transport
**Pros**:
- Faster connection (1 RTT)
- No head-of-line blocking
- Connection migration
- Built-in encryption
- Better loss recovery

**Cons**:
- Some networks block/throttle UDP
- Higher CPU usage
- Less debugging tools
- Newer (fewer optimizations)

**Best Practice**: Support both, let libp2p choose!
</details>

<details>
<summary>Hint: Inspecting Active Connections</summary>

You can inspect which transport is actually being used:

```go
// Get connections to a peer
conns := h.Network().ConnsToPeer(peerID)

for _, conn := range conns {
    // Get remote multiaddress
    remoteAddr := conn.RemoteMultiaddr()
    fmt.Printf("Connection using: %s\n", remoteAddr)

    // Check transport
    if strings.Contains(remoteAddr.String(), "/tcp/") {
        fmt.Println("  Transport: TCP")
    } else if strings.Contains(remoteAddr.String(), "/quic-v1") {
        fmt.Println("  Transport: QUIC")
    }
}
```

This helps verify which transport libp2p selected!
</details>

<details>
<summary>Hint: Adding More Transports</summary>

go-libp2p supports additional transports:

**WebSocket** (good for browser compatibility):
```go
libp2p.ListenAddrStrings(
    "/ip4/0.0.0.0/tcp/0",
    "/ip4/0.0.0.0/udp/0/quic-v1",
    "/ip4/0.0.0.0/tcp/0/ws",  // WebSocket
)
```

**WebTransport** (modern browser transport):
```go
libp2p.ListenAddrStrings(
    "/ip4/0.0.0.0/tcp/0",
    "/ip4/0.0.0.0/udp/0/quic-v1",
    "/ip4/0.0.0.0/udp/0/quic-v1/webtransport",  // WebTransport
)
```

More transports = better connectivity!
</details>

## What You've Learned

Congratulations! You've successfully:

- **Added QUIC transport** to your libp2p node
- **Configured multi-transport** listening
- **Understood transport selection** and Happy Eyeballs
- **Compared TCP and QUIC** characteristics
- **Tested multi-transport connectivity**

## Key Concepts

### Multi-Transport Architecture
- **Flexibility**: Support multiple network technologies
- **Resilience**: Fallback if one transport fails
- **Performance**: Use fastest available option
- **Future-Proof**: Easy to add new transports

### QUIC Benefits
- **0-RTT Resumption**: Even faster reconnections
- **Congestion Control**: Better than TCP in some cases
- **Stream Multiplexing**: No head-of-line blocking
- **Connection Migration**: Survives network changes

### Happy Eyeballs
- **Parallel Racing**: Try all transports simultaneously
- **First Win**: Use whichever succeeds first
- **Caching**: Remember what worked
- **User Experience**: Minimize connection time

### Transport Abstraction
- **Application-Agnostic**: Same code for all transports
- **Protocol Independence**: Transports handle low-level details
- **Automatic Selection**: libp2p chooses best option
- **Graceful Fallback**: Degrade gracefully if transport fails

## What's Next?

In the next lesson, you'll explore the **Identify protocol** to discover peer information:
- Agent version and protocol versions
- Supported protocols
- Public and observed addresses
- Peer metadata

This is another checkpoint lesson where you'll verify your implementation against the instructor's server!

Next up: Lesson 5 - Identify Protocol Checkpoint!

## Additional Resources

- [QUIC RFC 9000](https://www.rfc-editor.org/rfc/rfc9000.html)
- [libp2p transports](https://docs.libp2p.io/concepts/transports/overview/)
- [QUIC in libp2p](https://github.com/libp2p/specs/blob/master/quic/README.md)
- [Happy Eyeballs RFC 8305](https://www.rfc-editor.org/rfc/rfc8305.html)
- [go-libp2p QUIC transport](https://pkg.go.dev/github.com/libp2p/go-libp2p/p2p/transport/quic)
