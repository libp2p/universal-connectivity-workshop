# go-libp2p Universal Connectivity Workshop Setup

Welcome to the go-libp2p Universal Connectivity Workshop! This guide will help you set up your development environment.

## Prerequisites

- Go 1.21 or higher (recommended: Go 1.23+)
- Basic knowledge of Go programming
- Familiarity with Go modules and goroutines
- Understanding of networking concepts (optional but helpful)
- Text editor or IDE of your choice (VS Code with Go extension, GoLand, etc.)

## Environment Setup

### Step 1: Install Go

If you haven't installed Go yet, download and install it from [https://go.dev/dl/](https://go.dev/dl/)

Verify your Go installation:

```bash
go version  # Should be 1.21 or higher
```

### Step 2: Create a Workshop Directory

Create a new directory for your workshop projects:

```bash
mkdir go-libp2p-workshop
cd go-libp2p-workshop
```

### Step 3: Initialize Go Module

Initialize a new Go module for the workshop:

```bash
go mod init workshop
```

This creates a `go.mod` file that tracks your dependencies.

### Step 4: Install Core Dependencies

Install the required go-libp2p packages. We'll add dependencies as we progress through the lessons, but here are the core ones:

```bash
go get github.com/libp2p/go-libp2p@latest
go get github.com/multiformats/go-multiaddr@latest
```

For additional utilities:

```bash
go get github.com/libp2p/go-libp2p/p2p/protocol/ping@latest
go get github.com/libp2p/go-libp2p/p2p/security/noise@latest
```

### Step 5: Verify Your Setup

Create a simple test file to verify your setup:

```bash
cat > test.go << 'EOF'
package main

import (
    "fmt"
    "github.com/libp2p/go-libp2p"
)

func main() {
    fmt.Println("go-libp2p version check...")
    // Just importing successfully means the setup works
    _ = libp2p.New
    fmt.Println("✓ Setup verified successfully!")
}
EOF

go run test.go
rm test.go
```

You should see:
```
go-libp2p version check...
✓ Setup verified successfully!
```

### Step 6: Run Dependency Checker

Run the dependency checker to ensure all required tools are available:

```bash
python deps.py
```

You should see all green checkmarks (✓) for required dependencies.

## Workshop Structure

Each lesson in this workshop follows this structure:

```
01-identity-and-host/
├── app/                    # Your application code goes here
│   ├── main.go            # Main application file
│   └── Dockerfile         # For containerized testing
├── lesson.md              # Lesson instructions and explanations
├── lesson.yaml            # Lesson metadata
├── check.py               # Automated checker for your solution
├── docker-compose.yaml    # Docker configuration
└── stdout.log             # Output log (created when you run your code)
```

## Go-libp2p Architecture Overview

go-libp2p is structured around several core components:

### Host
The **Host** is the main entry point for libp2p functionality. It manages:
- Peer identity (PeerId derived from cryptographic keys)
- Network connections
- Protocol handlers
- Stream multiplexing

### Transports
Transport layers handle low-level network communication:
- **TCP**: Traditional reliable transport
- **QUIC**: Modern UDP-based transport with built-in encryption
- **WebTransport**: Browser-compatible transport

### Security
Security protocols encrypt connections:
- **Noise**: Modern cryptographic handshake protocol
- **TLS**: Traditional TLS 1.3 support

### Multiplexing
Stream multiplexers allow multiple logical streams over a single connection:
- **Yamux**: Primary multiplexer used in production
- **Mplex**: Alternative multiplexer

### Protocols
Application-level protocols built on top of streams:
- **Ping**: Connectivity testing and latency measurement
- **Identify**: Peer information exchange
- **Kad-DHT**: Distributed hash table for peer discovery
- **GossipSub**: Pub/sub messaging system

## Getting Help

During the workshop:

1. **Read the lesson.md file carefully** - it contains detailed instructions and explanations
2. **Use the hint blocks** - they provide additional context for tricky parts
3. **Check your solution** - run `python check.py` to validate your implementation
4. **Consult the documentation** - [https://pkg.go.dev/github.com/libp2p/go-libp2p](https://pkg.go.dev/github.com/libp2p/go-libp2p)
5. **Ask for help** - don't hesitate to ask the instructor or fellow participants

## Workshop Objectives

By the end of this workshop, you will:

- Understand peer-to-peer networking fundamentals
- Know how to create libp2p hosts with cryptographic identities
- Implement transport layers and connection management
- Build custom protocols for peer communication
- Use built-in protocols (ping, identify, GossipSub, Kademlia)
- Connect to the Universal Connectivity network
- Handle NAT traversal and connectivity challenges

## Go-Specific Best Practices

Throughout this workshop, we'll follow Go best practices:

### Error Handling
Always check and handle errors explicitly:
```go
host, err := libp2p.New()
if err != nil {
    return fmt.Errorf("failed to create host: %w", err)
}
```

### Context Usage
Use `context.Context` for cancellation and timeouts:
```go
ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
defer cancel()
```

### Resource Cleanup
Always defer cleanup operations:
```go
host, err := libp2p.New()
if err != nil {
    return err
}
defer host.Close()
```

### Structured Logging
Use structured logging for better observability:
```go
log.Printf("Connected to peer %s", peerID)
```

## Next Steps

Once your environment is set up:

1. Navigate to the first lesson: `01-identity-and-host/`
2. Read the `lesson.md` file
3. Start coding in the `app/` directory
4. Test your solution with `python check.py`

Let's begin building the future of peer-to-peer applications with Go! 🚀

## Troubleshooting

### Common Issues

**Go version too old:**
```bash
go version  # Should be 1.21+
```
If your version is too old, download the latest from [https://go.dev/dl/](https://go.dev/dl/)

**Module initialization issues:**
```bash
# Remove existing module files and reinitialize
rm go.mod go.sum
go mod init workshop
```

**Dependency download failures:**
```bash
# Clean module cache and retry
go clean -modcache
go get github.com/libp2p/go-libp2p@latest
```

**Import errors during lessons:**
Make sure you're running `go mod tidy` after adding new imports to download dependencies.

**Build errors:**
```bash
# Ensure all dependencies are downloaded
go mod download
go mod tidy

# Try building
go build -o app ./app/main.go
```

**Port already in use:**
If you see "bind: address already in use" errors, another process is using the port. Either:
- Stop the other process
- Change the listen port in your code
- Use `lsof -i :PORT` (Mac/Linux) or `netstat -ano | findstr :PORT` (Windows) to find the process

Need more help? Ask your instructor! 👨‍🏫

## Additional Resources

- **Official go-libp2p documentation**: [https://docs.libp2p.io/](https://docs.libp2p.io/)
- **go-libp2p GitHub repository**: [https://github.com/libp2p/go-libp2p](https://github.com/libp2p/go-libp2p)
- **Go package documentation**: [https://pkg.go.dev/github.com/libp2p/go-libp2p](https://pkg.go.dev/github.com/libp2p/go-libp2p)
- **Examples directory**: [https://github.com/libp2p/go-libp2p/tree/master/examples](https://github.com/libp2p/go-libp2p/tree/master/examples)
- **libp2p specifications**: [https://github.com/libp2p/specs](https://github.com/libp2p/specs)
