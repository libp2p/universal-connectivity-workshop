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

The **Identify protocol** (`/ipfs/id/1.0.0`) is automatically enabled in go-libp2p. It exchanges metadata between peers immediately after connection:

### What Identify Shares

| Information | Description | Example |
|-------------|-------------|---------|
| **Peer ID** | Unique cryptographic identifier | `12D3KooW...` |
| **Agent Version** | Software name and version | `go-libp2p/0.36.0` |
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

```go
h.Peerstore()  // Returns peerstore.Peerstore interface
```

## Your Task

Extend your application to:
1. Set a custom agent version
2. Connect to peers and exchange identify information
3. Query the peerstore for peer metadata
4. Display supported protocols
5. Show observed addresses (NAT detection)

## Step-by-Step Instructions

### Step 1: Configure Custom Agent Version

Add a custom agent version when creating your host:

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

    // Create host with custom agent version
    h, err := libp2p.New(
        libp2p.Identity(priv),
        libp2p.ListenAddrStrings(
            "/ip4/0.0.0.0/tcp/0",
            "/ip4/0.0.0.0/udp/0/quic-v1",
        ),
        libp2p.UserAgent("universal-connectivity-app/1.0.0"),  // NEW!
    )
    if err != nil {
        log.Fatalf("Failed to create host: %v", err)
    }
    defer h.Close()

    fmt.Printf("Local peer id: %s\n", h.ID())
    fmt.Printf("Agent version: universal-connectivity-app/1.0.0\n")

    // Print listening addresses
    fmt.Println("Listening on:")
    for _, addr := range h.Addrs() {
        fmt.Printf("  %s/p2p/%s\n", addr, h.ID())
    }

    // Rest of code...
}
```

**What's happening here?**

- `libp2p.UserAgent("...")`: Sets custom agent version string
  - Format: `software-name/version`
  - Appears in identify messages
  - Helps peers identify what software you're running
- **Default**: Without this, uses `go-libp2p/VERSION`

**Why customize?** Makes your application identifiable in network metrics and logs. Essential for production applications!

### Step 2: Query Peer Information After Connection

Add a function to display peer information:

```go
func displayPeerInfo(h host.Host, peerID peer.ID) {
    fmt.Printf("\n=== Peer Information: %s ===\n", peerID)

    peerStore := h.Peerstore()

    // Get supported protocols
    protocols, err := peerStore.GetProtocols(peerID)
    if err != nil {
        log.Printf("Failed to get protocols: %v", err)
    } else {
        fmt.Printf("Supported protocols (%d):\n", len(protocols))
        for _, protocol := range protocols {
            fmt.Printf("  - %s\n", protocol)
        }
    }

    // Get agent version
    if agentVersion, err := peerStore.Get(peerID, "AgentVersion"); err == nil {
        if av, ok := agentVersion.(string); ok {
            fmt.Printf("Agent version: %s\n", av)
        }
    }

    // Get protocol version
    if protoVersion, err := peerStore.Get(peerID, "ProtocolVersion"); err == nil {
        if pv, ok := protoVersion.(string); ok {
            fmt.Printf("Protocol version: %s\n", pv)
        }
    }

    // Get known addresses
    addrs := peerStore.Addrs(peerID)
    if len(addrs) > 0 {
        fmt.Printf("Known addresses (%d):\n", len(addrs))
        for _, addr := range addrs {
            fmt.Printf("  - %s\n", addr)
        }
    }

    fmt.Println("=== End Peer Information ===\n")
}
```

**What's happening here?**

- `h.Peerstore()`: Accesses the peerstore
- `GetProtocols(peerID)`: Returns list of protocols peer supports
  - Example: `["/ipfs/ping/1.0.0", "/ipfs/id/1.0.0"]`
- `Get(peerID, "AgentVersion")`: Retrieves agent version from metadata
  - Stored as interface{}, needs type assertion
- `Addrs(peerID)`: Returns all known addresses for peer
  - Includes both advertised and discovered addresses

### Step 3: Display Observed Address (NAT Detection)

Add code to show your observed address:

```go
func displayObservedAddrs(h host.Host) {
    // Get the identify service
    ids := h.EventBus()

    // Subscribe to identify events
    sub, err := ids.Subscribe(new(event.EvtPeerIdentificationCompleted))
    if err != nil {
        log.Printf("Failed to subscribe to identify events: %v", err)
        return
    }
    defer sub.Close()

    // Wait a bit for identify to complete
    time.Sleep(2 * time.Second)

    // Check observed addresses
    observedAddrs := h.Peerstore().Addrs(h.ID())
    if len(observedAddrs) > 0 {
        fmt.Println("\nObserved addresses (how others see us):")
        for _, addr := range observedAddrs {
            fmt.Printf("  - %s\n", addr)
        }
    }
}
```

**What's happening here?**

- **Observed Address**: The address remote peers report seeing us from
  - Critical for NAT traversal
  - Shows your public IP if behind NAT
  - May differ from listening addresses
- **EvtPeerIdentificationCompleted**: Event fired when identify completes
- **Sleep**: Give time for identify protocol to run
  - In production, use event subscription properly

**NAT Detection Example**:
- You listen on: `/ip4/192.168.1.100/tcp/4001` (private)
- Peer observes: `/ip4/203.0.113.50/tcp/54321` (public)
- This tells you you're behind NAT!

### Step 4: Integrate Into Main Function

Update your main function to use the peer info display:

```go
func main() {
    fmt.Println("Starting Universal Connectivity Application...")

    // ... (keypair and host creation) ...

    // Create ping service
    pingService := ping.NewPingService(h)
    fmt.Println("Ping service created")

    // Parse and connect to peers
    // ... (connection code) ...

    if len(connectedPeers) == 0 {
        log.Fatal("Failed to connect to any peers")
    }

    // Give identify protocol time to complete
    fmt.Println("\nWaiting for identify protocol to complete...")
    time.Sleep(2 * time.Second)

    // Display peer information
    for _, peerID := range connectedPeers {
        displayPeerInfo(h, peerID)
    }

    // Display observed addresses
    displayObservedAddrs(h)

    // Ping peers
    fmt.Println("Pinging connected peers...")
    // ... (ping code) ...

    // Keep running
    fmt.Println("\nApplication running. Press Ctrl+C to exit.")
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

    <-sigCh
    fmt.Println("\nShutting down...")
}
```

### Step 5: Add Required Import

Don't forget to import peerstore types:

```go
import (
    // ... existing imports ...
    "github.com/libp2p/go-libp2p/core/peerstore"
)
```

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
    "github.com/libp2p/go-libp2p/core/event"
    "github.com/libp2p/go-libp2p/core/host"
    "github.com/libp2p/go-libp2p/core/network"
    "github.com/libp2p/go-libp2p/core/peer"
    "github.com/libp2p/go-libp2p/p2p/protocol/ping"
    "github.com/multiformats/go-multiaddr"
)

func displayPeerInfo(h host.Host, peerID peer.ID) {
    fmt.Printf("\n=== Peer Information: %s ===\n", peerID)

    peerStore := h.Peerstore()

    // Get supported protocols
    protocols, err := peerStore.GetProtocols(peerID)
    if err != nil {
        log.Printf("Failed to get protocols: %v", err)
    } else {
        fmt.Printf("Supported protocols (%d):\n", len(protocols))
        for _, protocol := range protocols {
            fmt.Printf("  - %s\n", protocol)
        }
    }

    // Get agent version
    if agentVersion, err := peerStore.Get(peerID, "AgentVersion"); err == nil {
        if av, ok := agentVersion.(string); ok {
            fmt.Printf("Agent version: %s\n", av)
        }
    }

    // Get protocol version
    if protoVersion, err := peerStore.Get(peerID, "ProtocolVersion"); err == nil {
        if pv, ok := protoVersion.(string); ok {
            fmt.Printf("Protocol version: %s\n", pv)
        }
    }

    // Get known addresses
    addrs := peerStore.Addrs(peerID)
    if len(addrs) > 0 {
        fmt.Printf("Known addresses (%d):\n", len(addrs))
        for _, addr := range addrs {
            fmt.Printf("  - %s\n", addr)
        }
    }

    fmt.Println("=== End Peer Information ===\n")
}

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

    // Create host with custom agent version
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
    fmt.Printf("Agent version: universal-connectivity-app/1.0.0\n")

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

    // Wait for identify to complete
    fmt.Println("\nWaiting for identify protocol to complete...")
    time.Sleep(2 * time.Second)

    // Display peer information
    for _, peerID := range connectedPeers {
        displayPeerInfo(h, peerID)
    }

    // Ping peers
    fmt.Println("Pinging connected peers...")
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

## Testing Your Implementation

### Local Testing

```bash
cd en/go/05-identify-checkpoint
go run app/main.go
```

Expected output:
```
Starting Universal Connectivity Application...
Local peer id: 12D3KooW...
Agent version: universal-connectivity-app/1.0.0
Listening on:
  /ip4/127.0.0.1/tcp/54321/p2p/12D3KooW...
  /ip4/127.0.0.1/udp/54322/quic-v1/p2p/12D3KooW...
Ping service created
No REMOTE_PEERS specified, using checkpoint server
Dialing peer QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN...
Connected to: QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN

Waiting for identify protocol to complete...

=== Peer Information: QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN ===
Supported protocols (15):
  - /ipfs/ping/1.0.0
  - /ipfs/id/1.0.0
  - /ipfs/id/push/1.0.0
  - /libp2p/circuit/relay/0.2.0/hop
  - /ipfs/kad/1.0.0
  ... (more protocols)
Agent version: go-ipfs/0.13.0
Protocol version: ipfs/0.1.0
Known addresses (4):
  - /ip4/147.75.77.187/tcp/4001
  - /ip4/147.75.77.187/udp/4001/quic
  ... (more addresses)
=== End Peer Information ===

Pinging connected peers...
Pinging QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN...
Ping to QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN successful: RTT = 45ms

Application running. Press Ctrl+C to exit.
```

### Two-Instance Test

Test identify between your own instances:

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

Both should display each other's information, including your custom agent version!

### Automated Testing

```bash
python check.py
```

### Docker Testing

```bash
cd en/go/05-identify-checkpoint
export PROJECT_ROOT=$(pwd)/../../..
export LESSON_PATH=en/go/05-identify-checkpoint

docker compose up --build
python check.py
```

## Success Criteria

Your implementation should:
- ✅ Set custom agent version
- ✅ Connect to remote peers
- ✅ Display supported protocols for peers
- ✅ Show agent and protocol versions
- ✅ List known peer addresses
- ✅ Successfully ping connected peers

## Troubleshooting

<details>
<summary>Empty Protocol List</summary>

**Symptom**: `GetProtocols()` returns empty list or error

**Causes**:
1. Identify not yet completed
2. Connection closed before identify
3. Peer doesn't support identify

**Solutions**:
- Add `time.Sleep(2 * time.Second)` after connection
- Subscribe to `EvtPeerIdentificationCompleted` event
- Check connection still active
- Try with known-good peer (checkpoint server)
</details>

<details>
<summary>Missing Agent Version</summary>

**Symptom**: Can't retrieve "AgentVersion" from peerstore

**Causes**:
1. Identify not completed
2. Peer doesn't advertise agent version
3. Wrong metadata key

**Solutions**:
- Wait longer for identify to complete
- Check for error from `peerStore.Get()`
- Try "ProtocolVersion" instead
- Verify peer is running libp2p software
</details>

<details>
<summary>Custom Agent Version Not Appearing</summary>

**Symptom**: Your agent version not shown to other peers

**Causes**:
1. Forgot `libp2p.UserAgent()` option
2. Option placed after `libp2p.New()`
3. Other peer not checking agent version

**Solutions**:
- Verify `libp2p.UserAgent()` is in option list
- Must be passed to `libp2p.New()`
- Test with two of your own instances
- Check other peer's logs for your version
</details>

## Hints

<details>
<summary>Hint: Peerstore Operations</summary>

Common peerstore operations:

**Store Address**:
```go
h.Peerstore().AddAddrs(peerID, addrs, peerstore.PermanentAddrTTL)
```

**Get Protocols**:
```go
protocols, err := h.Peerstore().GetProtocols(peerID)
```

**Set Metadata**:
```go
err := h.Peerstore().Put(peerID, "key", "value")
```

**Get Metadata**:
```go
value, err := h.Peerstore().Get(peerID, "key")
if v, ok := value.(string); ok {
    fmt.Println(v)
}
```

**Check if Peer Supports Protocol**:
```go
protocols, _ := h.Peerstore().GetProtocols(peerID)
for _, p := range protocols {
    if p == "/my-protocol/1.0.0" {
        // Peer supports it!
    }
}
```
</details>

<details>
<summary>Hint: Identify Events</summary>

Subscribe to identify events for better synchronization:

```go
sub, err := h.EventBus().Subscribe(new(event.EvtPeerIdentificationCompleted))
if err != nil {
    log.Fatal(err)
}
defer sub.Close()

go func() {
    for e := range sub.Out() {
        evt := e.(event.EvtPeerIdentificationCompleted)
        fmt.Printf("Identified peer: %s\n", evt.Peer)
        displayPeerInfo(h, evt.Peer)
    }
}()
```

This ensures you only query peerstore after identify completes!
</details>

<details>
<summary>Hint: Protocol Capabilities Check</summary>

Before using a protocol, verify peer supports it:

```go
func supportsPing(h host.Host, peerID peer.ID) bool {
    protocols, err := h.Peerstore().GetProtocols(peerID)
    if err != nil {
        return false
    }

    for _, p := range protocols {
        if p == "/ipfs/ping/1.0.0" {
            return true
        }
    }
    return false
}

// Usage
if supportsPing(h, peerID) {
    // Safe to ping
    pingService.Ping(ctx, peerID)
} else {
    fmt.Println("Peer doesn't support ping")
}
```

This prevents errors when trying protocols peer doesn't support!
</details>

## What You've Learned

Congratulations! You've successfully:

- **Used the Identify protocol** to discover peer information
- **Queried the peerstore** for protocols and metadata
- **Set custom agent version** for your application
- **Understood NAT detection** via observed addresses
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
- **Extensible**: Store custom metadata

### Agent Version
- **Identification**: What software is running
- **Debugging**: Track down version-specific issues
- **Metrics**: Network composition analysis
- **Production**: Essential for operational visibility

### Observed Addresses
- **NAT Detection**: Discover public address
- **Connectivity**: How others reach you
- **Relay Selection**: Choose relay strategy
- **Network Topology**: Understand position in network

## What's Next?

In the next lesson, you'll implement **GossipSub**, libp2p's pub/sub protocol:
- Topic-based messaging
- Peer discovery in topics
- Message propagation
- Efficient broadcast communication

This is a significant step toward building distributed applications!

Next up: Lesson 6 - GossipSub Pub/Sub Checkpoint!

## Additional Resources

- [Identify protocol specification](https://github.com/libp2p/specs/blob/master/identify/README.md)
- [Peerstore documentation](https://pkg.go.dev/github.com/libp2p/go-libp2p/core/peerstore)
- [NAT traversal in libp2p](https://docs.libp2p.io/concepts/nat/)
- [libp2p addressing](https://docs.libp2p.io/concepts/fundamentals/addressing/)
