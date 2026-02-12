# Lesson 05: Identify Checkpoint

## Introduction

Welcome to your second checkpoint! In this lesson, you'll learn about the Identify protocol, which allows libp2p peers to exchange information about their capabilities, supported protocols, and network details.

The good news is that nim-libp2p's SwitchBuilder automatically handles the Identify protocol for you! In this lesson, you'll learn how to access the peer information that's exchanged during connections.

## Learning Objectives

By the end of this lesson, you will:

- Understand the purpose of the Identify protocol in libp2p
- Learn how nim-libp2p automatically handles Identify
- Access peer information from the PeerStore
- Display peer capabilities including protocols, agent version, and addresses

## Background: The Identify Protocol

The Identify protocol (`/ipfs/id/1.0.0`) is fundamental to libp2p's peer discovery and capability negotiation. It serves several important purposes:

- **Capability Discovery**: Learn what protocols a peer supports
- **Version Information**: Exchange software version and agent strings
- **Address Discovery**: Learn how peers see your external addresses
- **Protocol Negotiation**: Establish common protocols for communication

When peers connect, they automatically exchange identification information, allowing the network to be self-describing and adaptive.

## How nim-libp2p Handles Identify

Unlike some other libp2p implementations where you need to manually configure Identify, nim-libp2p's `SwitchBuilder` automatically:

1. **Creates the Identify protocol** with your peer's information
2. **Mounts it on the Switch** to handle incoming identify requests
3. **Runs Identify automatically** when connections are established
4. **Stores the results** in the PeerStore for easy access

This means you get Identify functionality "for free" when using SwitchBuilder!

## Your Task

Building on your QUIC transport and ping implementation, you need to:

1. **Understand the PeerStore**: Learn how peer information is stored
2. **Access Peer Information**: Retrieve identify data after connections
3. **Display Peer Details**: Show protocol version, agent, and supported protocols

## Step-by-Step Instructions

### Step 1: Update Imports

Add the PeerStore-related imports:

```nim
import chronos
import libp2p
import libp2p/protocols/ping
import libp2p/peerstore  # For accessing peer information
import std/[os, strutils]
```

### Step 2: Understanding the PeerStore

The PeerStore contains several "books" that store different types of peer information:

- `AddressBook` - Peer's listening addresses
- `ProtoBook` - Protocols the peer supports
- `AgentBook` - Agent version string (e.g., "nim-libp2p/0.0.1")
- `ProtoVersionBook` - Protocol version (e.g., "ipfs/0.1.0")
- `KeyBook` - Peer's public key

You access these using the bracket syntax:

```nim
# Get peer's supported protocols
let protocols = switch.peerStore[ProtoBook][peerId]

# Get peer's agent version
let agentVersion = switch.peerStore[AgentBook][peerId]

# Get peer's protocol version
let protoVersion = switch.peerStore[ProtoVersionBook][peerId]

# Get peer's addresses
let addresses = switch.peerStore[AddressBook][peerId]
```

### Step 3: Display Identify Information After Connection

Create a procedure to display peer information:

```nim
proc displayPeerInfo(switch: Switch, peerId: PeerId) =
  ## Display identify information for a connected peer
  echo "=== Identify Information for ", peerId, " ==="

  # Get agent version
  let agentVersion = switch.peerStore[AgentBook][peerId]
  if agentVersion.len > 0:
    echo "  Agent: ", agentVersion

  # Get protocol version
  let protoVersion = switch.peerStore[ProtoVersionBook][peerId]
  if protoVersion.len > 0:
    echo "  Protocol Version: ", protoVersion

  # Get supported protocols
  let protocols = switch.peerStore[ProtoBook][peerId]
  if protocols.len > 0:
    echo "  Supported Protocols (", protocols.len, "):"
    for proto in protocols:
      echo "    - ", proto

  # Get addresses
  let addresses = switch.peerStore[AddressBook][peerId]
  if addresses.len > 0:
    echo "  Listen Addresses:"
    for addr in addresses:
      echo "    - ", addr

  echo "=== End Identify Information ==="
```

### Step 4: Call displayPeerInfo After Connection

After connecting to a peer and before starting the ping loop, display their identify info:

```nim
for fullAddr in remoteAddrs:
  try:
    let parsed = parseFullAddress(fullAddr)
    if parsed.isOk:
      let (peerId, wireAddr) = parsed.get()
      echo "Dialing ", peerId, " at ", wireAddr

      # Dial with PingCodec
      let conn = await switch.dial(peerId, @[wireAddr], PingCodec)

      echo "Connected to: ", peerId

      # Give identify a moment to complete
      await sleepAsync(100.milliseconds)

      # Display identify information
      displayPeerInfo(switch, peerId)

      # Start ping loop
      asyncSpawn pingLoop(pingProtocol, conn, peerId)
  except CatchableError as e:
    echo "Failed to connect: ", e.msg
```

### Step 5: Handle Identify in Connection Events (Optional)

You can also display identify info in your connection handler:

```nim
proc onConnect(peerId: PeerId, event: ConnEvent) {.async: (raises: [CancelledError]).} =
  echo "Connected to: ", peerId
  # Note: Identify may not be complete yet at this point
  # For best results, add a small delay or check in main loop
```

## Solution

Here's the complete working solution:

```nim
import chronos
import libp2p
import libp2p/protocols/ping
import libp2p/peerstore
import std/[os, strutils]

proc displayPeerInfo(switch: Switch, peerId: PeerId) =
  ## Display identify information for a connected peer
  echo ""
  echo "=== Identify Information for ", peerId, " ==="

  # Get agent version
  let agentVersion = switch.peerStore[AgentBook][peerId]
  if agentVersion.len > 0:
    echo "  Agent: ", agentVersion
  else:
    echo "  Agent: (not available)"

  # Get protocol version
  let protoVersion = switch.peerStore[ProtoVersionBook][peerId]
  if protoVersion.len > 0:
    echo "  Protocol Version: ", protoVersion
  else:
    echo "  Protocol Version: (not available)"

  # Get supported protocols
  let protocols = switch.peerStore[ProtoBook][peerId]
  if protocols.len > 0:
    echo "  Supported Protocols (", protocols.len, "):"
    for proto in protocols:
      echo "    - ", proto
  else:
    echo "  Supported Protocols: (none)"

  # Get addresses
  let addresses = switch.peerStore[AddressBook][peerId]
  if addresses.len > 0:
    echo "  Listen Addresses:"
    for addr in addresses:
      echo "    - ", addr
  else:
    echo "  Listen Addresses: (none)"

  echo "=== End Identify Information ==="
  echo ""

proc pingLoop(p: Ping, conn: Connection, peerId: PeerId) {.async.} =
  ## Continuously ping a peer every second and display RTT
  while true:
    try:
      let rtt = await p.ping(conn)
      echo "Received a ping from ", peerId, ", round trip time: ", rtt.milliseconds, " ms"
    except CatchableError as e:
      echo "Ping failed to ", peerId, ": ", e.msg
      break
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

  # Create random number generator
  let rng = newRng()

  # Use TCP address for this lesson
  let localAddress = MultiAddress.init("/ip4/0.0.0.0/tcp/0").tryGet()

  # Create the ping protocol
  let pingProtocol = Ping.new(rng = rng)

  # Create a Switch - Identify is automatically included!
  let switch = SwitchBuilder
    .new()
    .withRng(rng)
    .withAddress(localAddress)
    .withTcpTransport()
    .withMplex()
    .withNoise()
    .build()

  # Mount the ping protocol
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

  # Connect to remote peers
  for fullAddr in remoteAddrs:
    try:
      let parsed = parseFullAddress(fullAddr)
      if parsed.isOk:
        let (peerId, wireAddr) = parsed.get()
        echo "Dialing ", peerId, " at ", wireAddr

        # Dial with PingCodec
        let conn = await switch.dial(peerId, @[wireAddr], PingCodec)

        echo "Ping session started with: ", peerId

        # Wait a moment for identify to complete
        await sleepAsync(500.milliseconds)

        # Display identify information from PeerStore
        displayPeerInfo(switch, peerId)

        # Start ping loop
        asyncSpawn pingLoop(pingProtocol, conn, peerId)
      else:
        echo "Failed to parse address: ", fullAddr
    except CatchableError as e:
      echo "Failed to connect to ", fullAddr, ": ", e.msg

  # Keep running
  echo "Waiting for connections..."
  while true:
    await sleepAsync(1.seconds)

waitFor(main())
```

## Code Walkthrough

### Automatic Identify

When you use `SwitchBuilder.build()`, it automatically:

1. Creates an `Identify` protocol instance with your peer's info
2. Mounts it on the switch via `switch.mount(identify)`
3. Configures the PeerStore to store identify results

This happens in the builder's `build()` method - you don't need to do anything!

### PeerStore Books

The PeerStore uses a "book" pattern to organize peer data:

```nim
# Each book is a typed container for specific data
switch.peerStore[AgentBook][peerId]      # Returns string
switch.peerStore[ProtoBook][peerId]      # Returns seq[string]
switch.peerStore[AddressBook][peerId]    # Returns seq[MultiAddress]
switch.peerStore[ProtoVersionBook][peerId]  # Returns string
```

### Timing Considerations

Identify runs asynchronously after connection establishment. If you try to read PeerStore data immediately after connecting, it might not be populated yet. A small delay (100-500ms) ensures identify has completed.

## Testing Your Implementation

The workshop checker will:
1. Accept your peer's connection
2. Exchange identify information
3. Respond to ping requests
4. Verify that identify exchange completed successfully

## Success Criteria

Your implementation should:

- Display the startup message and local peer ID
- Successfully dial the remote peer
- Exchange identify information (automatic)
- Display peer's agent version and protocol version
- Display peer's supported protocols
- Continue sending pings with RTT display
- Handle connection events properly

## Common Mistakes

1. **Checking PeerStore too early**: Identify runs asynchronously; add a small delay
2. **Forgetting imports**: Make sure to import `libp2p/peerstore`
3. **Empty results**: If PeerStore returns empty data, the peer may not support Identify

## What's Next?

Congratulations! You've reached your second checkpoint!

You now have a libp2p node that can:
- Support TCP transport with Noise encryption
- Measure connectivity with ping and RTT
- Exchange peer capabilities via Identify
- Access peer metadata from the PeerStore

Key concepts you've learned:
- **Identify Protocol**: Automatic peer capability exchange
- **PeerStore**: Centralized storage for peer metadata
- **Book Pattern**: Type-safe access to different peer data types
- **Automatic Protocol Handling**: How nim-libp2p simplifies common patterns

In the next lesson, you'll implement Gossipsub for publish-subscribe messaging, allowing peers to communicate through topic-based channels!
