# Lesson 4: Circuit Relay v2

Welcome to Lesson 4! In this lesson, you'll learn how Circuit Relay v2 enables NAT traversal, allowing peers behind firewalls to communicate through a relay node.

## Learning Objectives

By the end of this lesson, you will:

- Understand why Circuit Relay v2 is essential for NAT traversal
- Set up a relay node that forwards traffic between peers
- Configure a listener node to reserve a slot on the relay
- Connect a dialer node to the listener through the relay
- Understand the three-node architecture and traffic flow

## Background: Why Circuit Relay v2?

**The Problem**: Many peers are behind NATs or firewalls that block incoming connections. Direct peer-to-peer connections fail.

**The Solution**: Circuit Relay v2 uses an intermediary relay node to forward traffic:
- **Relay Node**: Publicly accessible, forwards traffic
- **Listener Node**: Behind NAT, reserves a slot on relay
- **Dialer Node**: Connects to listener through relay

**Key Insight**: The relay address `/ip4/.../tcp/.../p2p/<relay-id>/p2p-circuit/p2p/<listener-id>` tells the dialer to route through the relay to reach the listener.

## Architecture

```
Dialer Node                    Relay Node                    Listener Node
    |                              |                             |
    |--[1] Connect to relay-------->|                             |
    |                              |--[2] Reserve slot----------->|
    |                              |<--[3] Reservation confirmed--|
    |                              |                             |
    |--[4] Dial via relay address-->|--[5] Forward to listener-->|
    |                              |                             |
    |<--[6] Traffic flows---------|<--[7] Traffic flows----------|
```

**Traffic Flow**: All data between dialer and listener flows through the relay.

## Your Task

Create three Node.js applications:
1. **Relay Node** (`relay.js`) - Public relay that forwards traffic
2. **Listener Node** (`listener.js`) - Private node that reserves a slot on relay
3. **Dialer Node** (`dialer.js`) - Connects to listener via relay

## Step-by-Step Instructions

### 1. Relay Node (`relay.js`)

The relay listens on public addresses and forwards traffic between peers:

```javascript
import { createLibp2p } from 'libp2p';
import { tcp } from '@libp2p/tcp';
import { noise } from '@chainsafe/libp2p-noise';
import { yamux } from '@chainsafe/libp2p-yamux';
import { circuitRelayServer } from '@libp2p/circuit-relay-v2';
import { identify } from '@libp2p/identify';
import { createFromJSON } from '@libp2p/peer-id-factory';
import fs from 'fs';

async function main() {
  // Load persistent peer ID (relay identity should be stable)
  const peerIdJson = JSON.parse(fs.readFileSync('./peer-id.json', 'utf-8'));
  const peerId = await createFromJSON(peerIdJson);

  const node = await createLibp2p({
    peerId,
    addresses: {
      listen: ['/ip4/0.0.0.0/tcp/0']  // Listen on any available port
    },
    transports: [tcp()],
    connectionEncrypters: [noise()],
    streamMuxers: [yamux()],
    services: {
      identify: identify(),
      relay: circuitRelayServer({
        reservations: {
          maxReservations: 15  // Allow up to 15 peers to reserve slots
        }
      })
    }
  });

  await node.start();
  console.log(`Node started with id ${node.peerId.toString()}`);
  console.log('Listening on:');
  node.getMultiaddrs().forEach(addr => console.log(`  ${addr.toString()}`));
}

main().catch(console.error);
```

**Key Points**:
- `circuitRelayServer()` enables relay functionality
- `maxReservations` limits concurrent reservations (prevents relay abuse)
- Relay must be publicly accessible (listening on public IP)

### 2. Listener Node (`listener.js`)

The listener connects to the relay and reserves a slot, then advertises its relay address:

```javascript
import { createLibp2p } from 'libp2p';
import { tcp } from '@libp2p/tcp';
import { noise } from '@chainsafe/libp2p-noise';
import { yamux } from '@chainsafe/libp2p-yamux';
import { circuitRelayTransport } from '@libp2p/circuit-relay-v2';
import { identify } from '@libp2p/identify';
import { multiaddr } from '@multiformats/multiaddr';

async function main() {
  const relayAddrStr = process.env.RELAY_ADDR || process.argv[2];
  const relayAddr = multiaddr(relayAddrStr);

  const node = await createLibp2p({
    addresses: {
      listen: []  // No direct listening - behind NAT
    },
    transports: [
      tcp(),
      circuitRelayTransport()  // Enable circuit relay transport
    ],
    connectionEncrypters: [noise()],
    streamMuxers: [yamux()],
    services: {
      identify: identify()
    }
  });

  await node.start();
  console.log(`Node started with id ${node.peerId.toString()}`);

  // Connect to relay
  const relayConn = await node.dial(relayAddr);
  const relayPeerId = relayConn.remotePeer.toString();
  console.log(`Connected to the relay ${relayPeerId}`);

  // Listen on circuit relay address - this creates a reservation
  const circuitListenAddrStr = `${relayAddr.toString()}/p2p-circuit`;
  const circuitListenAddr = multiaddr(circuitListenAddrStr);
  await node.components.transportManager.listen([circuitListenAddr]);

  // Wait for reservation to be confirmed and relay address to be advertised
  let relayMultiaddr = null;
  for (let i = 0; i < 30; i++) {
    const addrs = node.getMultiaddrs();
    relayMultiaddr = addrs.find(addr => {
      const addrStr = addr.toString();
      return addrStr.includes('/p2p-circuit') && 
             addrStr.includes(relayPeerId) &&
             addrStr.includes(node.peerId.toString());
    });
    
    if (relayMultiaddr) {
      console.log(`Advertising with a relay address of ${relayMultiaddr.toString()}`);
      break;
    }
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  // Keep running
  await new Promise(() => {});
}

main().catch(console.error);
```

**Key Points**:
- `circuitRelayTransport()` enables using relays
- `node.components.transportManager.listen([circuitListenAddr])` creates the reservation
- Format: `/ip4/.../tcp/.../p2p/<relay-id>/p2p-circuit` tells the node to reserve on that specific relay
- After reservation, the node advertises `/ip4/.../tcp/.../p2p/<relay-id>/p2p-circuit/p2p/<listener-id>`

### 3. Dialer Node (`dialer.js`)

The dialer connects to the listener using the relay address:

```javascript
import { createLibp2p } from 'libp2p';
import { tcp } from '@libp2p/tcp';
import { noise } from '@chainsafe/libp2p-noise';
import { yamux } from '@chainsafe/libp2p-yamux';
import { circuitRelayTransport } from '@libp2p/circuit-relay-v2';
import { multiaddr } from '@multiformats/multiaddr';

async function main() {
  const listenerRelayAddrStr = process.env.LISTENER_RELAY_ADDR || process.argv[2];
  const listenerRelayAddr = multiaddr(listenerRelayAddrStr);

  const node = await createLibp2p({
    transports: [
      tcp(),
      circuitRelayTransport()  // Enable circuit relay transport
    ],
    connectionEncrypters: [noise()],
    streamMuxers: [yamux()]
  });

  await node.start();
  console.log(`Node started with id ${node.peerId.toString()}`);

  // Dial through relay - circuit relay transport handles routing
  const conn = await node.dial(listenerRelayAddr);
  console.log(`Connected to the listener node via ${conn.remoteAddr.toString()}`);

  await node.stop();
}

main().catch(console.error);
```

**Key Points**:
- Dialer must include `circuitRelayTransport()` to support circuit addresses
- `node.dial(listenerRelayAddr)` automatically routes through the relay
- Traffic flows: Dialer → Relay → Listener (transparent to application)

## Running the Lesson

```bash
# 1. Start relay (in one terminal)
cd app
node relay.js
# Note the relay's multiaddr (e.g., /ip4/127.0.0.1/tcp/56775/p2p/12D3KooW...)

# 2. Start listener (in another terminal)
node listener.js /ip4/127.0.0.1/tcp/56775/p2p/12D3KooW...
# Note the advertised relay address

# 3. Start dialer (in another terminal)
node dialer.js /ip4/127.0.0.1/tcp/56775/p2p/12D3KooW.../p2p-circuit/p2p/12D3KooW...
# Should see: "Connected to the listener node via ..."
```

## Important Concepts

### Circuit Relay Address Format

```
/ip4/<relay-ip>/tcp/<relay-port>/p2p/<relay-peer-id>/p2p-circuit/p2p/<listener-peer-id>
```

- `/p2p-circuit`: Indicates this is a circuit relay address
- The dialer connects to the relay, which forwards to the listener
- All traffic is encrypted end-to-end (relay can't read it)

### Reservation Mechanism

- Listener "reserves" a slot on the relay
- Reservation prevents relay exhaustion (limited slots)
- Reservation expires after a timeout
- Only one reservation per listener per relay

### Performance Implications

- **Latency**: Traffic goes through relay, adding one hop
- **Bandwidth**: Relay forwards all traffic (potential bottleneck)
- **Cost**: Relay consumes resources forwarding traffic
- **Trust**: Relay sees traffic (but can't decrypt it due to end-to-end encryption)

## Success Criteria

Your implementation should:
- ✅ Relay node starts and listens on public addresses
- ✅ Listener connects to relay and reserves a slot
- ✅ Listener advertises relay address with `/p2p-circuit`
- ✅ Dialer connects to listener through relay
- ✅ Connection message shows relay address

## What's Next?

Excellent work! You've mastered Circuit Relay v2 and NAT traversal. You now understand:
- **NAT Traversal**: How to connect peers behind firewalls
- **Relay Architecture**: Three-node setup (relay, listener, dialer)
- **Reservation System**: How listeners reserve slots on relays
- **Circuit Addresses**: How multiaddrs encode relay paths
- **End-to-End Security**: Traffic is encrypted, relay can't read it

Next up: The Identify Protocol - learning how peers discover each other's capabilities and addresses!