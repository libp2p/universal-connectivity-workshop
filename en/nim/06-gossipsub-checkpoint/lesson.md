# Lesson 06: Gossipsub Checkpoint

## Introduction

Welcome to your third checkpoint! In this lesson, you'll implement Gossipsub, libp2p's publish-subscribe protocol that enables topic-based messaging across peer-to-peer networks. You'll learn how Gossipsub efficiently distributes messages while protecting against malicious peers.

## Learning Objectives

By the end of this lesson, you will:

- Understand publish-subscribe messaging patterns and why Gossipsub exists
- Learn the difference between mesh members and gossip peers
- Implement Gossipsub for topic-based communication
- Subscribe to topics and handle incoming messages
- Publish messages to connected peers
- Understand Gossipsub's Byzantine fault tolerance mechanisms

## Background: Why Gossipsub?

### The Problem with Naive Flooding (FloodSub)

The simplest pub/sub approach is **FloodSub**: when you receive a message, forward it to all peers subscribed to that topic. While simple, this has serious problems:

- **Bandwidth Explosion**: Each message is sent O(n) times where n = number of peers
- **No Protection Against Spam**: Malicious peers can flood the network
- **Poor Scalability**: Network load grows quadratically with peer count

### Gossipsub: A Better Approach

Gossipsub solves these problems through two key mechanisms:

1. **Mesh Network**: Each peer maintains a small, stable set of peers (the "mesh") for direct message forwarding
2. **Gossip Protocol**: Peers periodically share metadata about messages they've seen, allowing others to request missing messages

This provides:
- **Efficient Distribution**: O(D) message sends where D = mesh degree (typically 6-12)
- **Redundancy**: Multiple paths ensure message delivery even with peer failures
- **Byzantine Resistance**: Peer scoring detects and penalizes misbehaving peers

## Gossipsub Architecture

### Mesh vs Gossip Peers

```
                    ┌─────────────────────────────────────┐
                    │           Your Node                 │
                    │                                     │
                    │  ┌─────────────────────────────┐   │
                    │  │      Mesh Peers (D=6)       │   │
                    │  │  - Direct message relay     │   │
                    │  │  - Bidirectional            │   │
                    │  │  - Stable connections       │   │
                    │  └─────────────────────────────┘   │
                    │                                     │
                    │  ┌─────────────────────────────┐   │
                    │  │     Gossip Peers (lazy)     │   │
                    │  │  - Metadata exchange only   │   │
                    │  │  - IHAVE/IWANT protocol     │   │
                    │  │  - Backup message source    │   │
                    │  └─────────────────────────────┘   │
                    └─────────────────────────────────────┘
```

**Mesh Peers**: Full message forwarding partners (typically D=6 peers per topic)
**Gossip Peers**: Share message IDs; can request full messages if needed

### Gossipsub Parameters

nim-libp2p's Gossipsub has configurable parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `d` | 6 | Target mesh degree |
| `dLow` | 4 | Minimum mesh peers before grafting |
| `dHigh` | 12 | Maximum mesh peers before pruning |
| `heartbeatInterval` | 1s | How often to maintain mesh |
| `gossipFactor` | 0.25 | Fraction of peers to gossip to |

### Byzantine Fault Tolerance: Peer Scoring

Gossipsub tracks peer behavior and assigns scores:

```nim
# Peer scoring parameters (simplified)
type GossipSubParams = object
  gossipThreshold: float64      # Below this: no gossip to peer
  publishThreshold: float64     # Below this: no publish to peer
  graylistThreshold: float64    # Below this: ignore peer entirely
```

Peers are penalized for:
- Sending invalid messages
- Excessive message spam
- Failing to forward messages
- IP address collocation (potential Sybil attack)

## Your Task

Building on your identify implementation from Lesson 5, you need to:

1. **Create GossipSub Instance**: Initialize with a Switch
2. **Mount the Protocol**: Register it on the switch
3. **Subscribe to Topics**: Handle incoming messages with a TopicHandler
4. **Publish Messages**: Send data to subscribed peers
5. **Handle Message Events**: Process and display received messages

## Step-by-Step Instructions

### Step 1: Update Imports

Add the Gossipsub-related imports:

```nim
import chronos
import libp2p
import libp2p/protocols/pubsub/gossipsub
import libp2p/protocols/pubsub/pubsub
import stew/byteutils  # For string.fromBytes and toBytes
import std/[os, strutils, json, times]
```

### Step 2: Define Constants and Message Types

Define your topic and message structure:

```nim
const
  ChatTopic = "universal-connectivity"
  DiscoveryTopic = "universal-connectivity-browser-peer-discovery"

type
  ChatMessage = object
    sender: string
    message: string
    timestamp: int64
```

### Step 3: Create a Topic Handler

The TopicHandler processes incoming messages:

```nim
proc createTopicHandler(localPeerId: PeerId): TopicHandler =
  ## Create a handler for incoming pubsub messages
  proc handler(topic: string, data: seq[byte]) {.async.} =
    try:
      let msgStr = string.fromBytes(data)
      let jsonNode = parseJson(msgStr)

      let sender = jsonNode["sender"].getStr()
      let message = jsonNode["message"].getStr()

      # Don't display our own messages
      if sender != $localPeerId:
        echo "Received message on '", topic, "': ", message, " from ", sender[0..7], "..."
    except CatchableError as e:
      echo "Failed to parse message: ", e.msg

  return handler
```

### Step 4: Create and Configure GossipSub

Create the GossipSub instance with appropriate parameters:

```nim
proc createGossipSub(switch: Switch): GossipSub =
  ## Create a GossipSub instance with reasonable defaults
  let params = GossipSubParams.init(
    d = 6,                              # Target mesh degree
    dLow = 4,                           # Min peers before grafting
    dHigh = 12,                         # Max peers before pruning
    heartbeatInterval = 1.seconds,      # Mesh maintenance interval
    gossipFactor = 0.25,                # Fraction of peers to gossip to
    floodPublish = true,                # Publish to all peers initially
  )

  GossipSub.init(
    switch = switch,
    params = params,
  )
```

### Step 5: Subscribe to Topics

Subscribe to the chat topic with your handler:

```nim
proc setupSubscriptions(gossip: GossipSub, handler: TopicHandler) =
  ## Subscribe to chat topic
  gossip.subscribe(ChatTopic, handler)
  echo "Subscribed to topic: ", ChatTopic

  # Optionally subscribe to discovery topic
  gossip.subscribe(DiscoveryTopic, handler)
  echo "Subscribed to topic: ", DiscoveryTopic
```

### Step 6: Publish Messages

Create a procedure to publish messages:

```nim
proc publishMessage(gossip: GossipSub, peerId: PeerId, message: string) {.async.} =
  ## Publish a chat message to the network
  let chatMsg = ChatMessage(
    sender: $peerId,
    message: message,
    timestamp: getTime().toUnix()
  )

  let data = $(%*chatMsg)  # Convert to JSON bytes

  let peers = await gossip.publish(ChatTopic, data.toBytes())
  echo "Published message to ", peers, " peers"
```

### Step 7: Mount GossipSub on Switch

Mount the protocol so it handles incoming connections:

```nim
# After creating switch and gossipsub
switch.mount(gossip)
```

### Step 8: Periodic Publishing Loop

Create a loop to send test messages:

```nim
proc publishLoop(gossip: GossipSub, peerId: PeerId) {.async.} =
  ## Periodically publish test messages
  var counter = 0
  while true:
    await sleepAsync(5.seconds)
    counter.inc()
    let msg = "Hello from nim-libp2p! Message #" & $counter
    await publishMessage(gossip, peerId, msg)
```

## Solution

Here's the complete working solution:

```nim
import chronos
import libp2p
import libp2p/protocols/pubsub/gossipsub
import libp2p/protocols/pubsub/pubsub
import stew/byteutils
import std/[os, strutils, json, times]

const
  ChatTopic = "universal-connectivity"
  DiscoveryTopic = "universal-connectivity-browser-peer-discovery"

type
  ChatMessage = object
    sender: string
    message: string
    timestamp: int64

proc createTopicHandler(localPeerId: PeerId): TopicHandler =
  ## Create a handler for incoming pubsub messages
  proc handler(topic: string, data: seq[byte]) {.async.} =
    try:
      let msgStr = string.fromBytes(data)
      let jsonNode = parseJson(msgStr)

      let sender = jsonNode["sender"].getStr()
      let message = jsonNode["message"].getStr()

      # Don't display our own messages
      if sender != $localPeerId:
        echo "Received on '", topic, "': ", message, " from ", sender[0..min(7, sender.len-1)], "..."
    except CatchableError as e:
      echo "Failed to parse message: ", e.msg

  return handler

proc publishMessage(gossip: GossipSub, peerId: PeerId, message: string) {.async.} =
  ## Publish a chat message to the network
  let chatMsg = %*{
    "sender": $peerId,
    "message": message,
    "timestamp": getTime().toUnix()
  }

  let data = $chatMsg
  let peers = await gossip.publish(ChatTopic, data.toBytes())
  echo "Published message to ", peers, " peers"

proc publishLoop(gossip: GossipSub, peerId: PeerId) {.async.} =
  ## Periodically publish test messages
  var counter = 0
  while true:
    await sleepAsync(5.seconds)
    counter.inc()
    let msg = "Hello from nim-libp2p! Message #" & $counter
    await publishMessage(gossip, peerId, msg)

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

  # Use TCP address
  let localAddress = MultiAddress.init("/ip4/0.0.0.0/tcp/0").tryGet()

  # Create a Switch
  let switch = SwitchBuilder
    .new()
    .withRng(rng)
    .withAddress(localAddress)
    .withTcpTransport()
    .withMplex()
    .withNoise()
    .build()

  # Create GossipSub with parameters
  let params = GossipSubParams.init(
    d = 6,
    dLow = 4,
    dHigh = 12,
    heartbeatInterval = 1.seconds,
    gossipFactor = 0.25,
    floodPublish = true,
  )

  let gossip = GossipSub.init(
    switch = switch,
    parameters = params,
  )

  # Mount GossipSub on the switch
  switch.mount(gossip)

  # Create topic handler
  let handler = createTopicHandler(switch.peerInfo.peerId)

  # Subscribe to topics
  gossip.subscribe(ChatTopic, handler)
  echo "Subscribed to topic: ", ChatTopic

  gossip.subscribe(DiscoveryTopic, handler)
  echo "Subscribed to topic: ", DiscoveryTopic

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
        await switch.connect(peerId, @[wireAddr])
        echo "Connected to: ", peerId
      else:
        echo "Failed to parse address: ", fullAddr
    except CatchableError as e:
      echo "Failed to connect to ", fullAddr, ": ", e.msg

  # Start the publish loop in the background
  asyncSpawn publishLoop(gossip, switch.peerInfo.peerId)

  # Keep running
  echo "Waiting for messages..."
  while true:
    await sleepAsync(1.seconds)

waitFor(main())
```

## Code Walkthrough

### GossipSub Initialization

```nim
let params = GossipSubParams.init(
  d = 6,                           # Target 6 mesh peers per topic
  dLow = 4,                        # Graft more peers if below 4
  dHigh = 12,                      # Prune peers if above 12
  heartbeatInterval = 1.seconds,   # Check mesh every second
  floodPublish = true,             # Flood first publish for reliability
)

let gossip = GossipSub.init(switch = switch, params = params)
```

### Topic Subscription

```nim
# TopicHandler signature: proc(topic: string, data: seq[byte]): Future[void]
gossip.subscribe(ChatTopic, handler)
```

When you subscribe:
1. GossipSub adds you to the topic
2. Sends subscription announcements to peers
3. Begins mesh building for that topic

### Publishing Messages

```nim
let peers = await gossip.publish(ChatTopic, data.toBytes())
```

Publishing:
1. Signs the message with your peer's key (if configured)
2. Sends to all mesh peers for that topic
3. Returns the number of peers the message was sent to

### How Mesh Maintenance Works

Every `heartbeatInterval`, GossipSub:

1. **Checks mesh size**: Grafts or prunes peers to maintain D peers
2. **Sends IHAVE messages**: Tells gossip peers about recent message IDs
3. **Processes IWANT requests**: Sends requested messages to peers
4. **Updates peer scores**: Adjusts scores based on behavior

## Testing Your Implementation

The workshop checker will:
1. Connect to your peer
2. Subscribe to the same topics
3. Send test messages
4. Verify you receive and can publish messages

## Success Criteria

Your implementation should:

- Display the startup message and local peer ID
- Successfully dial the remote peer
- Subscribe to Universal Connectivity topics
- Receive messages from the remote peer
- Publish messages that the remote peer receives
- Handle peer connection events properly

## Common Mistakes

1. **Forgetting to mount**: `switch.mount(gossip)` is required
2. **Not starting switch first**: Start switch before publishing
3. **Wrong data format**: Messages are `seq[byte]`, use `.toBytes()` for strings
4. **Missing peer connections**: No messages without connected peers
5. **Not waiting for mesh**: Mesh building takes time; initial publishes may fail

## Advanced: Understanding Peer Scoring

GossipSub protects against Byzantine peers through scoring:

```nim
# Score thresholds in GossipSubParams
gossipThreshold = -100.0      # Below: stop gossiping to this peer
publishThreshold = -1000.0    # Below: stop publishing to this peer
graylistThreshold = -10000.0  # Below: completely ignore this peer
```

Peers lose points for:
- **Invalid messages**: -100 per invalid message
- **Spam**: Excessive duplicate messages
- **Ignoring messages**: Not forwarding to mesh
- **Sybil attacks**: Multiple peers from same IP

This scoring system is why Gossipsub is used in production systems like Ethereum 2.0!

## What's Next?

Congratulations! You've reached your third checkpoint!

You now have a libp2p node that can:
- Communicate over TCP with encryption
- Exchange peer identification
- Participate in publish-subscribe messaging
- Efficiently distribute messages through mesh networking

Key concepts you've learned:
- **Publish-Subscribe**: Topic-based messaging patterns
- **Gossipsub Protocol**: Efficient, Byzantine-resistant message distribution
- **Mesh vs Gossip**: Direct forwarding vs lazy propagation
- **Peer Scoring**: Protecting against malicious peers
- **Topic Management**: Subscribing to and handling topic events

In the next lesson, you'll implement Kademlia DHT for distributed peer discovery and content routing!
