# Lesson 02: Transport Layer - TCP Connection

## Introduction

Building on your basic nim-libp2p node from Lesson 1, in this lesson you'll learn about transport layers and establish your first peer-to-peer connections using TCP with Noise encryption and Mplex multiplexing.

## Learning Objectives

By the end of this lesson, you will:

- Understand nim-libp2p's transport abstraction
- Configure TCP transport with security and multiplexing
- Parse remote peer addresses from environment variables
- Establish a connection to a remote peer
- Handle connection events properly

## Background: Transport Layers in nim-libp2p

In nim-libp2p, **transports** handle the low-level network communication. A transport defines how data travels between peers. nim-libp2p supports multiple transports:

- **TCP**: Reliable, ordered, connection-oriented (like HTTP)
- **QUIC**: Modern UDP-based with built-in encryption
- **WebSocket**: For browser connectivity
- **Memory**: For testing and local communication

Each transport can be enhanced with:

- **Security protocols**: Encrypt communication (e.g., Noise, TLS)
- **Multiplexers**: Share one connection for multiple streams (e.g., Mplex, Yamux)

## Transport Stack

The nim-libp2p stack looks like the following when using TCP, Noise, and Mplex:

```
Application protocols (ping, gossipsub, etc.)
    ↕
Multiplexer (Mplex)
    ↕
Security (Noise)
    ↕
Transport (TCP)
    ↕
Network (IP)
```

## Your Task

Extend your application from Lesson 1 to:

1. Parse remote peer addresses from the `REMOTE_PEERS` environment variable
2. Add connection event handlers to track connections
3. Establish a connection to a remote peer
4. Print connection events for verification
5. Keep the application running to maintain connections

## Step-by-Step Instructions

### Step 1: Set Up Imports

Start with the necessary imports. We need `chronos` for async operations, `libp2p` for networking, and standard library modules for environment variables and string handling.

```nim
import chronos
import libp2p
import std/[os, strutils]
```

### Step 2: Create the Main Async Procedure

Define your main procedure with the `{.async.}` pragma. Print a startup message to confirm the application is running.

```nim
proc main() {.async.} =
  echo "Starting Universal Connectivity application..."
```

### Step 3: Parse Remote Peer Addresses

Read the `REMOTE_PEERS` environment variable, which contains comma-separated multiaddresses. Parse each address into a `MultiAddress` object.

```nim
  # Parse remote peer addresses from environment variable
  let remotePeersEnv = getEnv("REMOTE_PEERS", "")
  var remoteAddrs: seq[MultiAddress] = @[]

  if remotePeersEnv.len > 0:
    for addrStr in remotePeersEnv.split(','):
      let trimmed = addrStr.strip()
      if trimmed.len > 0:
        remoteAddrs.add(MultiAddress.init(trimmed).tryGet())
```

### Step 4: Create the Switch

Build your Switch with TCP transport, Noise security, and Mplex multiplexing - the same as Lesson 1.

```nim
  # Create random number generator for cryptographic operations
  let rng = newRng()

  # Define a local address (port 0 means "pick any available port")
  let localAddress = MultiAddress.init("/ip4/0.0.0.0/tcp/0").tryGet()

  # Create a Switch using the builder pattern
  let switch = SwitchBuilder
    .new()
    .withRng(rng)
    .withAddress(localAddress)
    .withTcpTransport()
    .withMplex()
    .withNoise()
    .build()
```

### Step 5: Add Connection Event Handlers

nim-libp2p uses callback-based event handlers. Register handlers for `Connected` and `Disconnected` events to track connection state changes.

```nim
  # Connection event handler for when a peer connects
  # Note: Must use {.async: (raises: [CancelledError]).} for ConnEventHandler
  proc onConnect(peerId: PeerId, event: ConnEvent) {.async: (raises: [CancelledError]).} =
    echo "Connected to: ", peerId

  # Connection event handler for when a peer disconnects
  proc onDisconnect(peerId: PeerId, event: ConnEvent) {.async: (raises: [CancelledError]).} =
    echo "Connection to ", peerId, " closed gracefully"

  # Register the event handlers
  switch.addConnEventHandler(onConnect, ConnEventKind.Connected)
  switch.addConnEventHandler(onDisconnect, ConnEventKind.Disconnected)
```

**Important**: The `{.async: (raises: [CancelledError]).}` pragma is required for `ConnEventHandler`. This tells the compiler that the async procedure only raises `CancelledError` (for cancellation), matching nim-libp2p's type expectations.

The `ConnEvent` object contains additional information:
- `event.kind`: Either `ConnEventKind.Connected` or `ConnEventKind.Disconnected`
- For `Connected` events: `event.incoming` indicates if the connection was inbound

### Step 6: Start the Switch and Print PeerId

Start the Switch to begin listening for connections and print the local peer ID.

```nim
  # Start the switch
  await switch.start()

  # Print local peer information
  echo "Local peer id: ", switch.peerInfo.peerId

  # Print listening addresses
  for addr in switch.peerInfo.addrs:
    echo "Listening on: ", addr
```

### Step 7: Connect to Remote Peers

For each remote address, parse out the PeerId and wire address, then establish a connection using `switch.connect()`.

```nim
  # Connect to all remote peers
  for fullAddr in remoteAddrs:
    try:
      # parseFullAddress extracts (PeerId, wireAddress) from a full multiaddress
      # e.g., /ip4/172.16.16.17/tcp/9092/p2p/12D3KooW... -> (peerId, /ip4/172.16.16.17/tcp/9092)
      let parsed = parseFullAddress(fullAddr)
      if parsed.isOk:
        let (peerId, wireAddr) = parsed.get()
        echo "Attempting to connect to ", peerId, " at ", wireAddr
        await switch.connect(peerId, @[wireAddr])
      else:
        echo "Failed to parse address: ", fullAddr
    except CatchableError as e:
      echo "Failed to connect to ", fullAddr, ": ", e.msg
```

### Step 8: Keep the Application Running

Use an infinite loop with `sleepAsync` to keep the application running and maintain connections.

```nim
  # Keep the application running
  echo "Waiting for connections..."
  while true:
    await sleepAsync(1.seconds)

# Entry point
waitFor(main())
```

## Solution

Here's the complete working solution:

```nim
import chronos
import libp2p
import std/[os, strutils]

proc main() {.async.} =
  echo "Starting Universal Connectivity application..."

  # Parse remote peer addresses from environment variable
  let remotePeersEnv = getEnv("REMOTE_PEERS", "")
  var remoteAddrs: seq[MultiAddress] = @[]

  if remotePeersEnv.len > 0:
    for addrStr in remotePeersEnv.split(','):
      let trimmed = addrStr.strip()
      if trimmed.len > 0:
        remoteAddrs.add(MultiAddress.init(trimmed).tryGet())

  # Create random number generator for cryptographic operations
  let rng = newRng()

  # Define a local address (port 0 means "pick any available port")
  let localAddress = MultiAddress.init("/ip4/0.0.0.0/tcp/0").tryGet()

  # Create a Switch using the builder pattern
  let switch = SwitchBuilder
    .new()
    .withRng(rng)
    .withAddress(localAddress)
    .withTcpTransport()
    .withMplex()
    .withNoise()
    .build()

  # Connection event handler for when a peer connects
  # Note: Must use {.async: (raises: [CancelledError]).} for ConnEventHandler
  proc onConnect(peerId: PeerId, event: ConnEvent) {.async: (raises: [CancelledError]).} =
    echo "Connected to: ", peerId

  # Connection event handler for when a peer disconnects
  proc onDisconnect(peerId: PeerId, event: ConnEvent) {.async: (raises: [CancelledError]).} =
    echo "Connection to ", peerId, " closed gracefully"

  # Register the event handlers
  switch.addConnEventHandler(onConnect, ConnEventKind.Connected)
  switch.addConnEventHandler(onDisconnect, ConnEventKind.Disconnected)

  # Start the switch
  await switch.start()

  # Print local peer information
  echo "Local peer id: ", switch.peerInfo.peerId

  # Print listening addresses
  for addr in switch.peerInfo.addrs:
    echo "Listening on: ", addr

  # Connect to all remote peers
  for fullAddr in remoteAddrs:
    try:
      # parseFullAddress extracts (PeerId, wireAddress) from a full multiaddress
      let parsed = parseFullAddress(fullAddr)
      if parsed.isOk:
        let (peerId, wireAddr) = parsed.get()
        echo "Attempting to connect to ", peerId, " at ", wireAddr
        await switch.connect(peerId, @[wireAddr])
      else:
        echo "Failed to parse address: ", fullAddr
    except CatchableError as e:
      echo "Failed to connect to ", fullAddr, ": ", e.msg

  # Keep the application running
  echo "Waiting for connections..."
  while true:
    await sleepAsync(1.seconds)

waitFor(main())
```

## Code Walkthrough

### Connection Event Handlers

nim-libp2p uses a callback-based system for connection events:

```nim
proc onConnect(peerId: PeerId, event: ConnEvent) {.async: (raises: [CancelledError]).} =
  echo "Connected to: ", peerId

switch.addConnEventHandler(onConnect, ConnEventKind.Connected)
```

The handler receives:
- `peerId`: The remote peer's identifier
- `event`: Contains `kind` (Connected/Disconnected) and additional metadata

You must register separate handlers for each event kind you want to handle.

### Parsing Full Multiaddresses

A full multiaddress includes both the network address and peer ID:
```
/ip4/172.16.16.17/tcp/9092/p2p/12D3KooWXyz...
```

The `parseFullAddress` function splits this into:
- **PeerId**: `12D3KooWXyz...`
- **Wire Address**: `/ip4/172.16.16.17/tcp/9092`

```nim
let parsed = parseFullAddress(fullAddr)
if parsed.isOk:
  let (peerId, wireAddr) = parsed.get()
```

### Connect vs Dial

nim-libp2p provides two methods:
- `connect(peerId, addrs)`: Establishes a connection without opening a protocol stream
- `dial(peerId, addrs, protocols)`: Connects AND opens a stream for specific protocols

In this lesson, we use `connect()` since we're just establishing connectivity.

## Testing Your Implementation

The workshop checker will:
1. Start listening on `172.16.16.17:9092`
2. Wait for your peer to connect
3. Close the connection gracefully
4. Verify the connection was established and closed properly

## Success Criteria

Your implementation should:

- Display the startup message and local peer ID
- Successfully parse remote peer addresses from the environment variable
- Establish a connection to the remote peer
- Print connection establishment messages via event handlers
- Handle connection closure gracefully

## What's Next?

Excellent! You've successfully configured TCP transport and established peer-to-peer connections. You now understand:

- **Transport Layer**: How nim-libp2p handles network communication
- **Security**: Noise protocol for encrypted connections
- **Multiplexing**: Mplex for sharing connections
- **Connection Management**: Handling incoming and outgoing connections
- **Event-Driven Programming**: Responding to network events with callbacks

In the next lesson, you'll add your first protocol (ping) and connect to the instructor's server for your first checkpoint!

Key concepts you've learned:

- **nim-libp2p Transport Stack**: TCP + Noise + Mplex
- **Connection Events**: Connected and Disconnected handlers
- **Multiaddresses**: Parsing full addresses with peer IDs
- **Async Programming**: Using Chronos for concurrent operations

Next up: Adding the ping protocol and achieving your first checkpoint!
