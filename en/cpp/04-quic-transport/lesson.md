# Lesson 4: QUIC Transport

In this lesson, you'll extend your libp2p application to support **QUIC transport** alongside TCP. QUIC is a modern, UDP-based transport protocol that offers several advantages over TCP.

## Learning Objectives

- Understand QUIC advantages over TCP
- Configure multi-transport libp2p hosts
- Connect to peers using QUIC multiaddresses
- Handle connections transparently across different transports

## QUIC vs TCP

| Feature | TCP | QUIC |
|---------|-----|------|
| Protocol | TCP | UDP |
| Encryption | Separate TLS handshake | Built-in |
| Connection latency | 2-3 RTT | 1 RTT (0-RTT resumption) |
| Multiplexing | Head-of-line blocking | Stream-level multiplexing |
| NAT traversal | Limited | Better (UDP-based) |
| Connection migration | Not supported | Supported |

## Protocol Stack Comparison

**TCP Stack:**
```
Application → Multiplexer (Yamux) → Security (Noise) → Transport (TCP) → Network
```

**QUIC Stack:**
```
Application → Multiplexer/Security/Transport (integrated in QUIC) → Network
```

## Multiaddress Format

- **TCP**: `/ip4/127.0.0.1/tcp/9000`
- **QUIC**: `/ip4/127.0.0.1/udp/9001/quic-v1`

## Key Changes from Lesson 3

1. **Add QUIC listening address** alongside TCP
2. **Detect transport type** from multiaddress for logging
3. **Handle both transports** transparently

## Code Walkthrough

### Listen on Both Transports

```cpp
// Get listening ports
std::string tcp_port = getEnv("LISTEN_PORT", "9000");
std::string quic_port = getEnv("QUIC_PORT", "9001");

// Build multiaddresses for both transports
std::string tcp_addr_str = "/ip4/0.0.0.0/tcp/" + tcp_port;
std::string quic_addr_str = "/ip4/0.0.0.0/udp/" + quic_port + "/quic-v1";

// Listen on TCP
auto tcp_addr = libp2p::multi::Multiaddress::create(tcp_addr_str).value();
host->listen(tcp_addr);

// Listen on QUIC
auto quic_addr = libp2p::multi::Multiaddress::create(quic_addr_str).value();
host->listen(quic_addr);
```

### Detect Transport Type

```cpp
std::string getTransportType(const libp2p::multi::Multiaddress& addr) {
    std::string addr_str = addr.getStringAddress();
    if (addr_str.find("/quic") != std::string::npos) {
        return "QUIC";
    } else if (addr_str.find("/tcp/") != std::string::npos) {
        return "TCP";
    }
    return "Unknown";
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LISTEN_PORT` | 9000 | TCP listening port |
| `QUIC_PORT` | 9001 | QUIC listening port |
| `REMOTE_PEERS` | (empty) | Comma-separated peer multiaddresses |

## Building and Running

```bash
# Build
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build .

# Run (listening on both TCP and QUIC)
./lesson

# Connect to a peer via QUIC
REMOTE_PEERS="/ip4/192.168.1.100/udp/9001/quic-v1/p2p/12D3KooW..." ./lesson

# Connect to a peer via TCP
REMOTE_PEERS="/ip4/192.168.1.100/tcp/9000/p2p/12D3KooW..." ./lesson
```

## Expected Output

```
Starting Universal Connectivity Application...
Local peer id: 12D3KooWxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Listening on TCP: /ip4/0.0.0.0/tcp/9000
Listening on QUIC: /ip4/0.0.0.0/udp/9001/quic-v1
Ping protocol: /ipfs/ping/1.0.0
Transports: TCP + QUIC
Waiting for connections and pings...
```

## Next Steps

In Lesson 5, you'll learn about mDNS for automatic peer discovery on local networks.
