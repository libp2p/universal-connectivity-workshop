# Lesson 01: Identity and Basic Switch

## Introduction

Welcome to the first lesson in the nim-libp2p workshop! In this lesson, you'll learn the fundamental concept of **peer identity** in libp2p networks and create your first libp2p Switch using Nim.

Every peer in a libp2p network has a unique cryptographic identity. This identity is derived from a public/private keypair and is used to:
- Uniquely identify peers across the network
- Authenticate connections between peers
- Sign and verify messages

## Key Concepts

### PeerId
A `PeerId` is a cryptographic hash of a peer's public key. It serves as the unique identifier for a peer in the network. In nim-libp2p, the PeerId is automatically generated when you create a Switch.

### Switch
In nim-libp2p, a `Switch` is the main entry point for all networking operations. It's equivalent to what other libp2p implementations call a "Host". The Switch manages:
- Transport protocols (TCP, QUIC, etc.)
- Stream multiplexing (mplex, yamux)
- Security protocols (Noise, TLS)
- Protocol handlers

### SwitchBuilder
nim-libp2p uses a fluent builder pattern called `SwitchBuilder` to construct Switch instances. This allows you to configure transports, multiplexers, and security protocols in a clean, chainable way.

### Chronos
nim-libp2p is built on top of [Chronos](https://github.com/status-im/nim-chronos), an efficient asynchronous programming framework for Nim. All network operations are async and use the `{.async.}` pragma.

## Your Task

Create a basic nim-libp2p Switch that:
1. Initializes a random number generator (RNG)
2. Creates a Switch using SwitchBuilder with TCP transport
3. Starts the Switch
4. Prints the peer's PeerId
5. Properly shuts down the Switch

The output should display the PeerId in the format:
```
PeerId: 12D3KooW...
```

## Solution

```nim
import chronos
import libp2p

proc main() {.async.} =
  # Create random number generator for cryptographic operations
  let rng = newRng()

  # Define a local address (port 0 means "pick any available port")
  let localAddress = MultiAddress.init("/ip4/0.0.0.0/tcp/0").tryGet()

  # Create a Switch using the builder pattern
  let switch = SwitchBuilder
    .new()
    .withRng(rng)              # Provide RNG for key generation
    .withAddress(localAddress) # Set listening address
    .withTcpTransport()        # Use TCP as transport
    .withMplex()               # Use Mplex for stream multiplexing
    .withNoise()               # Use Noise protocol for encryption
    .build()

  # Start the switch - this begins listening on the configured address
  await switch.start()

  # Print the PeerId
  echo "PeerId: ", switch.peerInfo.peerId

  # Clean shutdown
  await switch.stop()

# Run the async main procedure
waitFor(main())
```

## Code Walkthrough

### 1. Imports
```nim
import chronos
import libp2p
```
- `chronos`: The async framework providing `{.async.}` and `waitFor`
- `libp2p`: The main libp2p module that exports all necessary types

### 2. Random Number Generator
```nim
let rng = newRng()
```
The RNG is essential for cryptographic operations including:
- Generating the Ed25519 keypair for peer identity
- Cryptographic handshakes in the Noise protocol
- Any randomness needed during network operations

### 3. MultiAddress
```nim
let localAddress = MultiAddress.init("/ip4/0.0.0.0/tcp/0").tryGet()
```
A `MultiAddress` is a self-describing network address format used in libp2p. The format `/ip4/0.0.0.0/tcp/0` means:
- `/ip4/0.0.0.0`: Listen on all IPv4 interfaces
- `/tcp/0`: Use TCP transport with an automatically assigned port

The `.tryGet()` extracts the value or throws an exception if parsing failed.

### 4. SwitchBuilder
```nim
let switch = SwitchBuilder
  .new()
  .withRng(rng)
  .withAddress(localAddress)
  .withTcpTransport()
  .withMplex()
  .withNoise()
  .build()
```
This fluent builder pattern configures:
- **withRng**: Provides cryptographic randomness
- **withAddress**: Sets the listening address
- **withTcpTransport**: Enables TCP connections
- **withMplex**: Enables stream multiplexing over a single connection
- **withNoise**: Enables encrypted communication using the Noise protocol

### 5. Starting and Accessing PeerInfo
```nim
await switch.start()
echo "PeerId: ", switch.peerInfo.peerId
```
After starting, the Switch's `peerInfo` contains:
- `peerId`: The unique identifier for this peer
- `addrs`: The actual addresses the switch is listening on

### 6. Async Execution
```nim
waitFor(main())
```
`waitFor` runs the async procedure and blocks until completion. This is the bridge between sync and async code in Chronos.

## What's Next?

In the next lesson, we'll add TCP transport to enable actual network connections between peers. You'll learn how to dial other peers and establish connections.
