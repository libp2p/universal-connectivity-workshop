# Lesson 03: Ping Checkpoint

## Introduction

Welcome to your first checkpoint! In this lesson, you'll implement the ping protocol using nim-libp2p to establish bidirectional connectivity with a remote peer and measure round-trip times (RTT).

The ping protocol is one of the fundamental protocols in libp2p, allowing peers to verify connectivity and measure network latency.

## Learning Objectives

By the end of this lesson, you will:

- Understand the purpose and mechanics of the ping protocol
- Mount the Ping protocol on a Switch to handle incoming pings
- Dial remote peers using the PingCodec
- Measure and display round-trip times (RTT)
- Implement a ping loop with configurable intervals

## Background: The Ping Protocol

The ping protocol in libp2p (`/ipfs/ping/1.0.0`) serves several important purposes:

- **Connectivity Testing**: Verifies that connections are working bidirectionally
- **Latency Measurement**: Measures round-trip time (RTT) between peers
- **Keep-Alive**: Helps maintain connections by sending periodic traffic
- **Network Quality**: Provides insights into connection stability

Unlike ICMP ping, libp2p's ping protocol works over any transport and respects the encryption and multiplexing layers. It exchanges 32-byte random payloads, with the receiver echoing the data back.

## Your Task

Building on your TCP transport implementation from Lesson 2, you need to:

1. **Create a Ping Protocol Instance**: Use `Ping.new()` to create the protocol
2. **Mount the Protocol**: Register it on your Switch to handle incoming pings
3. **Dial with PingCodec**: Connect to remote peers using the ping protocol
4. **Measure RTT**: Send pings and display round-trip times
5. **Implement Ping Loop**: Ping the remote peer every second

## Step-by-Step Instructions

### Step 1: Update Imports

Add the ping protocol import to your existing imports:

```nim
import chronos
import libp2p
import libp2p/protocols/ping
import std/[os, strutils]
```

The `libp2p/protocols/ping` module provides:
- `Ping` - The ping protocol type
- `PingCodec` - The protocol identifier (`/ipfs/ping/1.0.0`)
- `ping()` - Method to send a ping and measure RTT

### Step 2: Create the Ping Protocol Instance

Create a Ping instance using the shared RNG. You can optionally provide a handler for incoming pings.

```nim
  # Create the ping protocol
  let pingProtocol = Ping.new(rng = rng)
```

### Step 3: Mount the Protocol on Your Switch

Mount the ping protocol on your switch so it can handle incoming ping requests:

```nim
  # Mount the ping protocol to handle incoming pings
  switch.mount(pingProtocol)
```

When another peer sends a ping to your node, the protocol will automatically echo the payload back.

### Step 4: Dial Remote Peers with PingCodec

When connecting to remote peers, dial using the `PingCodec` to get a connection suitable for pinging:

```nim
  # Connect to remote peer with ping protocol
  for fullAddr in remoteAddrs:
    try:
      let parsed = parseFullAddress(fullAddr)
      if parsed.isOk:
        let (peerId, wireAddr) = parsed.get()
        echo "Dialing ", peerId, " at ", wireAddr

        # Dial with PingCodec to get a ping-ready connection
        let conn = await switch.dial(peerId, @[wireAddr], PingCodec)

        # Start pinging in the background
        asyncSpawn pingLoop(pingProtocol, conn, peerId)
    except CatchableError as e:
      echo "Failed to connect: ", e.msg
```

### Step 5: Implement the Ping Loop with RTT Display

Create an async procedure that continuously pings the remote peer and displays RTT:

```nim
proc pingLoop(p: Ping, conn: Connection, peerId: PeerId) {.async.} =
  ## Continuously ping a peer every second and display RTT
  while true:
    try:
      # Send ping and measure round-trip time
      let rtt = await p.ping(conn)

      # CRITICAL: Display the RTT - this is required for the checkpoint!
      echo "Received a ping from ", peerId, ", round trip time: ", rtt.milliseconds, " ms"

    except CatchableError as e:
      echo "Ping failed to ", peerId, ": ", e.msg
      break

    # Wait 1 second before next ping
    await sleepAsync(1.seconds)
```

**Important**: The `ping()` method returns a `Duration`. Use `.milliseconds` to convert it to milliseconds for display.

### Step 6: Handle Connection Events

Keep your connection event handlers from Lesson 2 to track connection state:

```nim
  proc onConnect(peerId: PeerId, event: ConnEvent) {.async: (raises: [CancelledError]).} =
    echo "Connected to: ", peerId

  proc onDisconnect(peerId: PeerId, event: ConnEvent) {.async: (raises: [CancelledError]).} =
    echo "Connection to ", peerId, " closed gracefully"

  switch.addConnEventHandler(onConnect, ConnEventKind.Connected)
  switch.addConnEventHandler(onDisconnect, ConnEventKind.Disconnected)
```

## Solution

Here's the complete working solution:

```nim
import chronos
import libp2p
import libp2p/protocols/ping
import std/[os, strutils]

proc pingLoop(p: Ping, conn: Connection, peerId: PeerId) {.async.} =
  ## Continuously ping a peer every second and display RTT
  ## CRITICAL: This must display RTT for the checkpoint to pass!
  while true:
    try:
      # Send ping and measure round-trip time
      let rtt = await p.ping(conn)

      # Display the RTT in milliseconds
      echo "Received a ping from ", peerId, ", round trip time: ", rtt.milliseconds, " ms"

    except CatchableError as e:
      echo "Ping failed to ", peerId, ": ", e.msg
      break

    # Wait 1 second before next ping (configurable interval)
    await sleepAsync(1.seconds)

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

  # Create the ping protocol
  let pingProtocol = Ping.new(rng = rng)

  # Create a Switch using the builder pattern
  let switch = SwitchBuilder
    .new()
    .withRng(rng)
    .withAddress(localAddress)
    .withTcpTransport()
    .withMplex()
    .withNoise()
    .build()

  # Mount the ping protocol to handle incoming pings
  switch.mount(pingProtocol)

  # Connection event handlers
  proc onConnect(peerId: PeerId, event: ConnEvent) {.async: (raises: [CancelledError]).} =
    echo "Connected to: ", peerId

  proc onDisconnect(peerId: PeerId, event: ConnEvent) {.async: (raises: [CancelledError]).} =
    echo "Connection to ", peerId, " closed gracefully"

  switch.addConnEventHandler(onConnect, ConnEventKind.Connected)
  switch.addConnEventHandler(onDisconnect, ConnEventKind.Disconnected)

  # Start the switch
  await switch.start()

  # Print local peer information
  echo "Local peer id: ", switch.peerInfo.peerId

  # Print listening addresses
  for addr in switch.peerInfo.addrs:
    echo "Listening on: ", addr

  # Connect to remote peers and start pinging
  for fullAddr in remoteAddrs:
    try:
      let parsed = parseFullAddress(fullAddr)
      if parsed.isOk:
        let (peerId, wireAddr) = parsed.get()
        echo "Dialing ", peerId, " at ", wireAddr

        # Dial with PingCodec to establish a ping connection
        let conn = await switch.dial(peerId, @[wireAddr], PingCodec)

        echo "Ping session started with: ", peerId

        # Start the ping loop in the background
        asyncSpawn pingLoop(pingProtocol, conn, peerId)
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

### The Ping Protocol

nim-libp2p provides a built-in `Ping` protocol that implements `/ipfs/ping/1.0.0`:

```nim
let pingProtocol = Ping.new(rng = rng)
```

The protocol:
- Generates 32 random bytes
- Sends them to the remote peer
- Waits for the echo response
- Measures the round-trip time

### Mounting Protocols

To handle incoming protocol requests, you must **mount** the protocol on your switch:

```nim
switch.mount(pingProtocol)
```

This registers the protocol handler. When a remote peer opens a stream with `/ipfs/ping/1.0.0`, your switch will route it to the ping protocol handler.

### Dialing with Protocol Codecs

When you dial a peer, you can specify which protocol you want to use:

```nim
let conn = await switch.dial(peerId, @[wireAddr], PingCodec)
```

This:
1. Establishes a connection to the peer
2. Performs the multistream-select negotiation for the ping protocol
3. Returns a connection ready for ping operations

### Measuring RTT

The `ping()` method sends a ping and returns the round-trip time as a `Duration`:

```nim
let rtt = await pingProtocol.ping(conn)
echo "RTT: ", rtt.milliseconds, " ms"
```

## Testing Your Implementation

The workshop checker will:
1. Start listening for incoming connections
2. Accept your peer's connection
3. Respond to ping requests
4. Verify that RTT is being measured and displayed

## Success Criteria

Your implementation should:

- Display the startup message and local peer ID
- Successfully dial the remote peer
- Mount the ping protocol for incoming pings
- Send ping requests every second
- **Display round-trip times (RTT) in milliseconds** - This is critical!
- Handle connection events properly

## Common Mistakes

1. **Not displaying RTT**: The checkpoint requires RTT output. Make sure to print the round-trip time!
2. **Using wrong codec**: Use `PingCodec` when dialing, not just `connect()`
3. **Not mounting protocol**: Without `switch.mount(pingProtocol)`, incoming pings won't be handled
4. **Forgetting async spawn**: The ping loop must run concurrently using `asyncSpawn`

## What's Next?

Congratulations! You've reached your first checkpoint!

You now have a libp2p node that can:
- Generate a stable identity
- Create encrypted, multiplexed connections
- Measure connection quality with pings
- Display network latency metrics

Key concepts you've learned:
- **Ping Protocol**: Testing connectivity and measuring latency
- **Protocol Mounting**: Registering handlers for incoming protocol requests
- **Protocol Dialing**: Connecting with specific protocol codecs
- **RTT Measurement**: Calculating round-trip times

In the next lesson, you'll explore QUIC transport as an alternative to TCP, learning about libp2p's multi-transport capabilities.
