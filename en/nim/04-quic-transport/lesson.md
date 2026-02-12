# Lesson 04: QUIC Transport

> **Note:** QUIC support in nim-libp2p is currently in the stabilization phase. The core implementation is complete and functional for this workshop, but you may encounter minor API changes in future releases.

## Introduction

Now that you understand TCP transport and have implemented the ping protocol, let's explore QUIC - a modern UDP-based transport protocol that provides built-in encryption and multiplexing. You'll learn about nim-libp2p's multi-transport capabilities by adding QUIC support to your application.

## Learning Objectives

By the end of this lesson, you will:

- Understand the advantages of QUIC over TCP
- Configure multi-transport nim-libp2p nodes
- Handle connections over different transport protocols
- Connect to remote peers using QUIC multiaddresses

## Background: QUIC Transport

QUIC (Quick UDP Internet Connections) is a modern transport protocol that offers several advantages over TCP:

- **Built-in Security**: Encryption is integrated into the protocol (no separate TLS/Noise layer needed)
- **Reduced Latency**: Fewer round-trips for connection establishment
- **Better Multiplexing**: Streams don't block each other (no head-of-line blocking)
- **Connection Migration**: Connections can survive network changes
- **UDP-based**: Can traverse NATs more easily than TCP

## Transport Comparison

Remember back in Lesson 2, you learned that the libp2p stack looks like the following when using TCP, Noise, and Mplex:

```
Application protocols (ping, gossipsub, etc.)
    |
Multiplexer (Mplex/Yamux)
    |
Security (Noise)
    |
Transport (TCP)
    |
Network (IP)
```

In this lesson you will add the ability to connect to remote peers using the QUIC transport. Because it has integrated encryption and multiplexing, the libp2p stack looks like the following when using QUIC:

```
Application protocols (ping, gossipsub, etc.)
    |
--------------+
Multiplexer   |
Security    (QUIC)
Transport     |
--------------+
    |
Network (IP)
```

## Your Task

Extend your ping application to support QUIC transport:

1. **Add QUIC Transport**: Configure QUIC alongside your existing TCP transport
2. **Multi-Transport Configuration**: Create a Switch that can handle both protocols
3. **Connect via QUIC**: Use a QUIC multiaddress to connect to the remote peer
4. **Handle Transport Events**: Display connection information for QUIC connections

## Step-by-Step Instructions

### Step 1: Update Imports

Your imports remain similar to the previous lesson:

```nim
import chronos
import libp2p
import libp2p/protocols/ping
import std/[os, strutils]
```

The QUIC transport is built into nim-libp2p and uses the same high-level API.

### Step 2: Configure Multi-Transport Switch

The key change is adding `.withQuicTransport()` to your SwitchBuilder. Note that QUIC has built-in encryption, so it doesn't use the Noise security layer you configured for TCP:

```nim
  # Create a Switch with both TCP and QUIC transports
  let switch = SwitchBuilder
    .new()
    .withRng(rng)
    .withAddress(localAddress)
    .withTcpTransport()       # TCP still uses Noise + Mplex
    .withQuicTransport()      # QUIC has built-in encryption + multiplexing
    .withMplex()              # For TCP streams
    .withNoise()              # For TCP security
    .build()
```

### Step 3: Listen on QUIC Address

For QUIC, you need a UDP multiaddress instead of TCP:

```nim
  # For TCP: /ip4/0.0.0.0/tcp/0
  # For QUIC: /ip4/0.0.0.0/udp/0/quic-v1

  let localAddress = MultiAddress.init("/ip4/0.0.0.0/udp/0/quic-v1").tryGet()
```

### Step 4: Connect Using QUIC

You will use the same dialing code from Lesson 3, but the `REMOTE_PEERS` environment variable will be initialized with a QUIC multiaddr. Without any other code changes, your peer will dial the remote peer with QUIC.

QUIC Multiaddrs look like: `/ip4/172.16.16.17/udp/9091/quic-v1`

```nim
  for fullAddr in remoteAddrs:
    try:
      let parsed = parseFullAddress(fullAddr)
      if parsed.isOk:
        let (peerId, wireAddr) = parsed.get()
        echo "Dialing ", peerId, " at ", wireAddr

        # This works for both TCP and QUIC - libp2p handles the transport
        let conn = await switch.dial(peerId, @[wireAddr], PingCodec)
        asyncSpawn pingLoop(pingProtocol, conn, peerId)
    except CatchableError as e:
      echo "Failed to connect: ", e.msg
```

### Step 5: Handle Connection Events

Your existing event handling code will work for both TCP and QUIC connections. The multiaddress in the connection events will show which transport was used:

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
  while true:
    try:
      # Send ping and measure round-trip time
      let rtt = await p.ping(conn)

      # Display the RTT in milliseconds
      echo "Received a ping from ", peerId, ", round trip time: ", rtt.milliseconds, " ms"

    except CatchableError as e:
      echo "Ping failed to ", peerId, ": ", e.msg
      break

    # Wait 1 second before next ping
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

  # Use QUIC address (UDP-based)
  let localAddress = MultiAddress.init("/ip4/0.0.0.0/udp/0/quic-v1").tryGet()

  # Create the ping protocol
  let pingProtocol = Ping.new(rng = rng)

  # Create a Switch with QUIC transport
  # Note: QUIC has built-in encryption and multiplexing, so we don't need
  # separate Noise or Mplex configuration for QUIC connections
  let switch = SwitchBuilder
    .new()
    .withRng(rng)
    .withAddress(localAddress)
    .withQuicTransport()
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

### QUIC Transport Configuration

The key difference from TCP is the transport configuration:

```nim
let switch = SwitchBuilder
  .new()
  .withRng(rng)
  .withAddress(localAddress)
  .withQuicTransport()  # Built-in encryption + multiplexing
  .build()
```

Notice that we don't need `.withNoise()` or `.withMplex()` for QUIC - the protocol handles encryption and multiplexing internally.

### QUIC Multiaddress Format

QUIC uses UDP instead of TCP:

- **TCP**: `/ip4/127.0.0.1/tcp/9092`
- **QUIC**: `/ip4/127.0.0.1/udp/9091/quic-v1`

The `/quic-v1` component indicates QUIC version 1.

### Transport Abstraction

One of the powerful features of libp2p is transport abstraction. The same dialing and protocol code works regardless of whether you're using TCP or QUIC:

```nim
# This works for both TCP and QUIC connections
let conn = await switch.dial(peerId, @[wireAddr], PingCodec)
```

The switch automatically selects the appropriate transport based on the multiaddress.

## Testing Your Implementation

The workshop checker will:
1. Listen for incoming QUIC connections
2. Accept your peer's connection
3. Respond to ping requests over QUIC
4. Verify that RTT is being measured and displayed

## Success Criteria

Your implementation should:

- Display the startup message and local peer ID
- Successfully dial the remote peer using QUIC
- Establish a QUIC connection
- Send and receive ping messages over QUIC
- Display round-trip times in milliseconds
- Handle connection events properly

## Common Mistakes

1. **Using TCP multiaddr format**: Make sure to use `/udp/.../quic-v1` not `/tcp/...`
2. **Adding Noise/Mplex for QUIC**: QUIC has built-in security and multiplexing
3. **Not handling connection errors**: QUIC connections can fail differently than TCP

## What's Next?

Great work! You've successfully implemented QUIC transport support. You now understand:

- **QUIC Advantages**: Built-in security, reduced latency, better multiplexing
- **Multi-Transport Configuration**: How to configure different transports
- **Transport Abstraction**: libp2p's ability to handle different transports uniformly
- **Modern Protocols**: How libp2p embraces cutting-edge networking technology

Key concepts you've learned:
- **QUIC Protocol**: Modern UDP-based transport with integrated security
- **Multi-Transport**: Supporting multiple protocols in the same application
- **Transport Abstraction**: How libp2p handles different transports uniformly
- **Connection Flexibility**: Choosing the best transport for each connection

In the next lesson, you'll reach your second checkpoint by implementing the Identify protocol, which allows peers to exchange information about their capabilities and supported protocols!
