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

In libp2p, **transports** handle the low-level network communication. A transport defines how data travels between peers. go-libp2p supports multiple transports out of the box:

- **TCP**: Reliable, ordered, connection-oriented (like HTTP)
- **QUIC**: Modern UDP-based with built-in encryption
- **WebTransport**: Browser-compatible modern transport
- **WebSocket**: HTTP-based upgrade for firewall traversal

By default, `libp2p.New()` automatically configures TCP, QUIC, and WebSocket transports with appropriate security (Noise/TLS) and multiplexing (Yamux).

## Transport Stack

The libp2p stack looks like this when using TCP:

```
Application protocols (ping, identify, etc.)
    ↕
Multiplexer (Yamux)
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
1. Listen on a TCP address for incoming connections
2. Parse remote peer addresses from an environment variable
3. Dial remote peers
4. Handle and log connection events

## Step-by-Step Instructions

### Step 1: Add Required Imports

Update your imports in `app/main.go`:

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

    "github.com/libp2p/go-libp2p"
    "github.com/libp2p/go-libp2p/core/crypto"
    "github.com/libp2p/go-libp2p/core/event"
    "github.com/libp2p/go-libp2p/core/host"
    "github.com/libp2p/go-libp2p/core/network"
    "github.com/multiformats/go-multiaddr"
)
```

**What's new?**

- `strings`: For parsing environment variables
- `github.com/libp2p/go-libp2p/core/event`: For subscribing to network events
- `github.com/libp2p/go-libp2p/core/network`: Network types and interfaces
- `github.com/multiformats/go-multiaddr`: Multiaddress parsing and manipulation

### Step 2: Configure Listening Addresses

Modify your host creation to listen on specific addresses:

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
            "/ip4/0.0.0.0/tcp/0",  // Listen on all IPv4 interfaces, random port
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

    // More code will go here...
}
```

**What's happening here?**

- `libp2p.ListenAddrStrings(...)`: Configures which addresses the host listens on
  - `/ip4/0.0.0.0/tcp/0`: Listen on all IPv4 interfaces
  - Port `0` means the OS assigns a random available port
- `h.Addrs()`: Returns all multiaddresses the host is listening on
- We print full addresses including the peer ID (`/p2p/<peer-id>`) so others can dial us

**Why 0.0.0.0?** This binds to all network interfaces, making your peer reachable on any of your machine's IP addresses (localhost, LAN IP, etc.).

**Why port 0?** Random port assignment prevents conflicts when running multiple instances.

### Step 3: Parse Remote Peer Addresses

Add code to parse peer addresses from an environment variable:

```go
func main() {
    // ... previous code (host creation) ...

    fmt.Printf("Local peer id: %s\n", h.ID())

    // Print listening addresses
    fmt.Println("Listening on:")
    for _, addr := range h.Addrs() {
        fmt.Printf("  %s/p2p/%s\n", addr, h.ID())
    }

    // Parse remote peer addresses from environment variable
    remotePeersStr := os.Getenv("REMOTE_PEERS")
    var remotePeers []multiaddr.Multiaddr

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
            remotePeers = append(remotePeers, addr)
        }
    }

    // More code will go here...
}
```

**What's happening here?**

- `os.Getenv("REMOTE_PEERS")`: Reads environment variable containing peer addresses
- Expected format: comma-separated multiaddresses
  - Example: `/ip4/192.168.1.1/tcp/4001/p2p/12D3KooW...,/ip4/10.0.0.1/tcp/4001/p2p/12D3KooW...`
- `strings.Split(...)`: Separates addresses by commas
- `multiaddr.NewMultiaddr(addrStr)`: Parses each string into a multiaddress
- We skip invalid addresses and log errors, but don't fail (graceful degradation)

### Step 4: Dial Remote Peers

Add code to connect to the parsed remote peers:

```go
func main() {
    // ... previous code (parsing remote peers) ...

    // Dial remote peers
    for _, addr := range remotePeers {
        // Extract peer ID from multiaddr
        peerInfo, err := host.InfoFromP2pAddr(addr)
        if err != nil {
            log.Printf("Invalid peer address %s: %v", addr, err)
            continue
        }

        fmt.Printf("Dialing peer %s at %s\n", peerInfo.ID, addr)

        // Connect to the peer
        if err := h.Connect(ctx, *peerInfo); err != nil {
            log.Printf("Failed to connect to %s: %v", peerInfo.ID, err)
        }
    }

    // More code will go here...
}
```

**What's happening here?**

- `host.InfoFromP2pAddr(addr)`: Extracts peer ID and addresses from multiaddr
  - Returns `AddrInfo` containing peer ID and list of addresses
- `h.Connect(ctx, *peerInfo)`: Initiates connection to the peer
  - Uses the context for cancellation/timeout
  - libp2p automatically tries all provided addresses
  - Connection happens asynchronously; errors are logged but don't stop the program

**Why asynchronous?** Connection establishment involves network I/O (TCP handshake, TLS/Noise negotiation, etc.). Running synchronously would block the program.

### Step 5: Subscribe to Connection Events

Add event handling to monitor connections:

```go
func main() {
    // ... previous code (dialing peers) ...

    // Subscribe to connection events
    sub, err := h.EventBus().Subscribe(new(event.EvtPeerConnectednessChanged))
    if err != nil {
        log.Fatalf("Failed to subscribe to events: %v", err)
    }
    defer sub.Close()

    // Handle events in a separate goroutine
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

    // Signal handling
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

    <-sigCh
    fmt.Println("\nShutting down...")
}
```

**What's happening here?**

- `h.EventBus().Subscribe(...)`: Subscribe to peer connectivity events
  - `event.EvtPeerConnectednessChanged`: Fired when connections establish or close
- `sub.Out()`: Returns a channel that receives events
- `goroutine`: Handles events concurrently without blocking main thread
- `evt.Connectedness`: Connection state
  - `network.Connected`: Connection established
  - `network.NotConnected`: Connection closed
- We print connection state changes to track network activity

**Why a goroutine?** Event handling needs to run continuously without blocking the main thread. Goroutines are Go's lightweight threads, perfect for concurrent tasks.

## Understanding the Flow

Here's what happens when you run your program:

1. **Host Creation**: libp2p initializes with TCP transport
2. **Listening**: Binds to OS-assigned ports on all interfaces
3. **Address Display**: Shows where peers can reach you
4. **Parsing**: Reads and validates remote peer addresses
5. **Dialing**: Initiates connections to remote peers
6. **Event Handling**: Monitors connection state changes
7. **Waiting**: Blocks until Ctrl+C
8. **Cleanup**: Closes connections and releases resources

## Testing Your Implementation

### Manual Testing - Two Nodes

#### Terminal 1 (Listener):
```bash
cd en/go/02-tcp-transport
go run app/main.go
```

Note the output - you'll see something like:
```
Starting Universal Connectivity Application...
Local peer id: 12D3KooWJ7GFE...
Listening on:
  /ip4/127.0.0.1/tcp/54321/p2p/12D3KooWJ7GFE...
  /ip4/192.168.1.100/tcp/54321/p2p/12D3KooWJ7GFE...
```

#### Terminal 2 (Dialer):
```bash
# Use the full multiaddr from Terminal 1
export REMOTE_PEERS="/ip4/127.0.0.1/tcp/54321/p2p/12D3KooWJ7GFE..."
go run app/main.go
```

You should see:
- Terminal 2: "Dialing peer 12D3KooWJ7GFE..."
- Both terminals: "Connected to: 12D3KooW..."

### Automated Checking

If using the workshop tool, press `c` to check your solution.

For manual testing:
```bash
python check.py
```

## Success Criteria

Your implementation should:
- ✅ Display startup message and peer ID
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
- Wrong protocol: `/tcp/` for TCP, `/udp/` for UDP
- Invalid peer ID: Must start with "12D3KooW" for Ed25519
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
- "no addresses": Multiaddress missing `/p2p/` component
- "connection refused": Peer not listening or firewall blocking
- "context deadline exceeded": Network unreachable or slow
</details>

<details>
<summary>Hint: Event Subscription</summary>

go-libp2p uses an event bus for notifications. Key events:

- `EvtPeerConnectednessChanged`: Connection state changes
- `EvtLocalAddressesUpdated`: Listening addresses changed
- `EvtPeerIdentificationCompleted`: Peer identification finished

Subscribe before you need events:
```go
sub, err := h.EventBus().Subscribe(new(event.EvtPeerConnectednessChanged))
if err != nil {
    log.Fatal(err)
}
defer sub.Close()  // Always close subscription
```

Handle in a goroutine to avoid blocking:
```go
go func() {
    for e := range sub.Out() {
        // Process event
    }
}()
```
</details>

## Hint - Complete Solution

Here's the complete working solution:

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

    "github.com/libp2p/go-libp2p"
    "github.com/libp2p/go-libp2p/core/crypto"
    "github.com/libp2p/go-libp2p/core/event"
    "github.com/libp2p/go-libp2p/core/host"
    "github.com/libp2p/go-libp2p/core/network"
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

    // Parse remote peer addresses
    remotePeersStr := os.Getenv("REMOTE_PEERS")
    var remotePeers []multiaddr.Multiaddr

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
            remotePeers = append(remotePeers, addr)
        }
    }

    // Dial remote peers
    for _, addr := range remotePeers {
        peerInfo, err := host.InfoFromP2pAddr(addr)
        if err != nil {
            log.Printf("Invalid peer address %s: %v", addr, err)
            continue
        }

        fmt.Printf("Dialing peer %s at %s\n", peerInfo.ID, addr)

        if err := h.Connect(ctx, *peerInfo); err != nil {
            log.Printf("Failed to connect to %s: %v", peerInfo.ID, err)
        }
    }

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

    // Signal handling
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

    <-sigCh
    fmt.Println("\nShutting down...")
}
```

## What's Next?

Excellent! You've successfully configured TCP transport and established peer-to-peer connections. You now understand:

- **Transport Layer**: How libp2p handles network communication
- **Multiaddresses**: Self-describing, composable network addresses
- **Listening and Dialing**: Acting as both server and client
- **Connection Events**: Monitoring network activity
- **Async Operations**: Handling concurrent tasks with goroutines

## Key Concepts

### Transport Abstraction
libp2p abstracts transport details, letting you focus on application logic. The same code works with TCP, QUIC, WebSocket, etc.

### Multiaddresses
Unlike traditional "IP:port", multiaddresses describe the full path to a peer:
- Self-describing protocols
- Composable (can chain multiple protocols)
- Future-proof (new protocols can be added)

### Connection Management
go-libp2p automatically handles:
- Connection pooling
- Keep-alive
- Reconnection attempts
- Resource limits

### Event-Driven Architecture
Events decouple components:
- Subscribe to what you need
- Handle asynchronously
- No tight coupling between layers

In the next lesson, you'll add your first protocol (ping) and connect to the instructor's server for your first checkpoint!

Next up: Adding the ping protocol and achieving your first checkpoint!

## Additional Resources

- [Multiaddr specification](https://github.com/multiformats/multiaddr)
- [libp2p transports](https://docs.libp2p.io/concepts/transports/overview/)
- [go-libp2p host documentation](https://pkg.go.dev/github.com/libp2p/go-libp2p/core/host)
- [Network package documentation](https://pkg.go.dev/github.com/libp2p/go-libp2p/core/network)
