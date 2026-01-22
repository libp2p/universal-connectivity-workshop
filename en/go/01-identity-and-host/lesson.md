# Lesson 1: Identity and Basic Host

Welcome to your first step into peer-to-peer networking with go-libp2p! In this lesson, you'll create your very first libp2p peer and understand the fundamental concept of peer identity.

## Learning Objectives

By the end of this lesson, you will:
- Understand what a PeerId is and why it's important
- Create a cryptographic keypair for peer identification
- Initialize a basic libp2p Host
- Run your first libp2p application

## Background: Peer Identity in libp2p

In traditional client-server applications, servers have known addresses (like domain names), but clients are anonymous. In peer-to-peer networks, every participant is both a client and a server, so each peer needs a stable, verifiable identity.

libp2p uses **cryptographic keypairs** for peer identity:
- **Private Key**: Kept secret, used to sign messages and prove identity
- **Public Key**: Shared with others, used to verify signatures
- **PeerId**: A hash of the public key, used as a short identifier

This design ensures that:
1. Peers can prove they control their identity (via signatures)
2. Others can verify that proof (via public key cryptography)
3. Identities are compact and easy to share (via PeerId hash)

## Your Task

Create a Go application that:
1. Generates an Ed25519 keypair for peer identity
2. Creates a basic libp2p Host
3. Prints the peer's ID when the application starts
4. Keeps the host running until interrupted

## Step-by-Step Instructions

### Step 1: Set Up Your Main Package

Create `app/main.go` with the basic package structure and imports:

```go
package main

import (
    "context"
    "fmt"
    "log"
    "os"
    "os/signal"
    "syscall"

    "github.com/libp2p/go-libp2p"
    "github.com/libp2p/go-libp2p/core/crypto"
    "github.com/libp2p/go-libp2p/core/host"
)

func main() {
    fmt.Println("Starting Universal Connectivity Application...")

    // Your code will go here
}
```

**What's happening here?**

- `package main`: Declares this as an executable program (not a library)
- `context`: Provides cancellation and timeout mechanisms for goroutines
- `fmt` and `log`: For printing output and logging
- `os/signal`, `syscall`: For handling OS signals like Ctrl+C
- `github.com/libp2p/go-libp2p`: The main libp2p package
- `github.com/libp2p/go-libp2p/core/crypto`: Cryptographic primitives for key generation
- `github.com/libp2p/go-libp2p/core/host`: The Host interface definition

**Why?** These imports provide all the building blocks needed to create a libp2p node with proper identity and lifecycle management.

### Step 2: Generate an Ed25519 Keypair

Add keypair generation to your `main()` function:

```go
func main() {
    fmt.Println("Starting Universal Connectivity Application...")

    // Generate an Ed25519 keypair for our peer identity
    priv, _, err := crypto.GenerateKeyPair(crypto.Ed25519, -1)
    if err != nil {
        log.Fatalf("Failed to generate keypair: %v", err)
    }

    // Your next code will go here
}
```

**What's happening here?**

- `crypto.GenerateKeyPair(crypto.Ed25519, -1)`: Generates a new Ed25519 keypair
  - First parameter: The key type (Ed25519 is modern and fast)
  - Second parameter: Key size (-1 means use default, which is 256 bits for Ed25519)
  - Returns: private key, public key, and error
- We only keep the private key (`priv`) because the public key can be derived from it
- Error checking ensures we don't proceed with invalid keys

**Why Ed25519?** It's a modern elliptic curve algorithm that provides:
- Fast key generation and signing
- Small key sizes (32 bytes)
- Strong security guarantees
- Deterministic signatures

### Step 3: Create the libp2p Host

Now create the host using the generated keypair:

```go
func main() {
    fmt.Println("Starting Universal Connectivity Application...")

    // Generate keypair (from Step 2)
    priv, _, err := crypto.GenerateKeyPair(crypto.Ed25519, -1)
    if err != nil {
        log.Fatalf("Failed to generate keypair: %v", err)
    }

    // Create a context for lifecycle management
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    // Create a libp2p host with the generated identity
    h, err := libp2p.New(
        libp2p.Identity(priv),
    )
    if err != nil {
        log.Fatalf("Failed to create host: %v", err)
    }
    defer h.Close()

    // Print the peer ID
    fmt.Printf("Local peer id: %s\n", h.ID())

    // Your next code will go here
}
```

**What's happening here?**

- `context.WithCancel(context.Background())`: Creates a cancellable context
  - `context.Background()`: The root context for the application
  - `cancel`: A function to cancel the context (called with `defer`)
- `libp2p.New(...)`: Creates a new libp2p host with options
  - `libp2p.Identity(priv)`: Sets the host's identity from our private key
  - Returns a `host.Host` interface and an error
- `defer h.Close()`: Ensures the host is properly closed when main() exits
- `h.ID()`: Gets the PeerId derived from the public key

**Why use context?** Contexts in Go are the standard way to:
- Signal cancellation to goroutines
- Set deadlines and timeouts
- Pass request-scoped values
- Coordinate graceful shutdown

**Why defer?** The `defer` keyword ensures cleanup code runs even if there's a panic or early return. It's Go's RAII-like pattern for resource management.

### Step 4: Keep the Host Running

Add code to keep the application running until interrupted:

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

    // Create host
    h, err := libp2p.New(
        libp2p.Identity(priv),
    )
    if err != nil {
        log.Fatalf("Failed to create host: %v", err)
    }
    defer h.Close()

    fmt.Printf("Local peer id: %s\n", h.ID())

    // Set up signal handling for graceful shutdown
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

    // Block until we receive a signal
    <-sigCh
    fmt.Println("\nShutting down...")
}
```

**What's happening here?**

- `make(chan os.Signal, 1)`: Creates a buffered channel to receive OS signals
  - Buffer size of 1 prevents missing signals if we're not ready to receive
- `signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)`: Registers the channel to receive:
  - `SIGINT`: Sent by Ctrl+C
  - `SIGTERM`: Sent by process managers for graceful shutdown
- `<-sigCh`: Blocks execution until a signal is received
  - The `<-` operator receives from the channel
  - This keeps the program running until interrupted

**Why this pattern?**
- Prevents the program from exiting immediately
- Allows for graceful shutdown when you press Ctrl+C
- Gives time for cleanup code (deferred `h.Close()`) to run
- Standard pattern in Go servers and daemons

### Step 5: Understanding the Complete Flow

Here's how your program executes:

1. **Startup**: Prints startup message
2. **Key Generation**: Creates Ed25519 keypair
3. **Host Creation**: Initializes libp2p host with identity
4. **PeerId Display**: Shows the peer's unique identifier
5. **Wait**: Blocks until Ctrl+C is pressed
6. **Shutdown**:
   - Prints shutdown message
   - Deferred `cancel()` cancels the context
   - Deferred `h.Close()` closes the host cleanly

This pattern ensures proper resource cleanup even if errors occur.

## Testing Your Implementation

### Running Your Code

1. Navigate to the lesson directory:
   ```bash
   cd en/go/01-identity-and-host
   ```

2. Run your application:
   ```bash
   go run app/main.go
   ```

3. You should see output similar to:
   ```
   Starting Universal Connectivity Application...
   Local peer id: 12D3KooWJ7GFEPLWbpxPyWkfPvFCbR7BwNb6Nwvn8Nrw9J8JZLQP
   ```

4. Press Ctrl+C to stop:
   ```
   ^C
   Shutting down...
   ```

### Automated Checking

If you're using the workshop tool, press the `c` key to check your solution.

For manual testing:
```bash
python check.py
```

## Success Criteria

Your implementation should:
- ✅ Display the startup message
- ✅ Generate a valid Ed25519 keypair
- ✅ Create a libp2p host successfully
- ✅ Display a valid peer ID (starts with "12D3KooW")
- ✅ Run until interrupted by Ctrl+C
- ✅ Shut down gracefully

## Hints

<details>
<summary>Hint: Common Import Errors</summary>

If you see import errors, make sure you've downloaded the dependencies:

```bash
go mod tidy
```

This command:
- Downloads missing dependencies
- Removes unused dependencies
- Updates go.mod and go.sum files
</details>

<details>
<summary>Hint: PeerId Format</summary>

Valid libp2p PeerIds (using Ed25519):
- Start with "12D3KooW" (base58btc multibase prefix + Ed25519 indicator)
- Are 52-55 characters long
- Only contain base58 characters (no 0, O, I, l)

Example: `12D3KooWJ7GFEPLWbpxPyWkfPvFCbR7BwNb6Nwvn8Nrw9J8JZLQP`
</details>

<details>
<summary>Hint: Understanding Context</summary>

Contexts in Go are powerful but can be confusing at first:

```go
// Create a root context
ctx := context.Background()

// Add cancellation capability
ctx, cancel := context.WithCancel(ctx)
defer cancel()  // Always defer cancel to prevent context leaks

// Add a timeout
ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
defer cancel()

// Pass context to functions that might need cancellation
doSomething(ctx)
```

For now, we create a context even though we don't use it much. Future lessons will show why it's important.
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
    "syscall"

    "github.com/libp2p/go-libp2p"
    "github.com/libp2p/go-libp2p/core/crypto"
)

func main() {
    fmt.Println("Starting Universal Connectivity Application...")

    // Generate an Ed25519 keypair for our peer identity
    priv, _, err := crypto.GenerateKeyPair(crypto.Ed25519, -1)
    if err != nil {
        log.Fatalf("Failed to generate keypair: %v", err)
    }

    // Create a context for lifecycle management
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    // Create a libp2p host with the generated identity
    h, err := libp2p.New(
        libp2p.Identity(priv),
    )
    if err != nil {
        log.Fatalf("Failed to create host: %v", err)
    }
    defer h.Close()

    // Print the peer ID
    fmt.Printf("Local peer id: %s\n", h.ID())

    // Set up signal handling for graceful shutdown
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

    // Block until we receive a signal
    <-sigCh
    fmt.Println("\nShutting down...")
}
```

## What You've Learned

Congratulations! You've created your first libp2p node with:

- **Cryptographic Identity**: Your node has a unique, verifiable identity using Ed25519
- **PeerId**: A compact identifier that other peers can use to reference your node
- **Basic Host**: The foundation that will handle all network operations
- **Graceful Shutdown**: Proper resource cleanup and signal handling
- **Go Patterns**: Context usage, defer for cleanup, and channel-based signaling

## Key Concepts

### Peer Identity
Every libp2p node has a cryptographic identity based on public-key cryptography. The PeerId is derived from the public key and serves as the node's unique identifier in the network.

### Host Interface
The `host.Host` interface is the core of go-libp2p. It provides:
- Identity management
- Network connection handling
- Protocol stream management
- Address listening and dialing

### Context Pattern
Go's `context.Context` is used throughout libp2p for:
- Cancellation signals
- Deadline propagation
- Request-scoped values
- Coordinating goroutine cleanup

## What's Next?

In the next lesson, you'll learn about:
- **Multiaddresses**: How peers specify where they can be reached
- **Transport Layers**: Adding TCP networking to your host
- **Listening**: Making your peer discoverable on the network
- **Dialing**: Connecting to other peers

Your identity is just the beginning - now let's make your peer reachable on the network!

## Additional Resources

- [go-libp2p documentation](https://pkg.go.dev/github.com/libp2p/go-libp2p)
- [PeerId specification](https://github.com/libp2p/specs/blob/master/peer-ids/peer-ids.md)
- [libp2p connectivity](https://docs.libp2p.io/concepts/fundamentals/peers/)
- [Go context package](https://pkg.go.dev/context)
