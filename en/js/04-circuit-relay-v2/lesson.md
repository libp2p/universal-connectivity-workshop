# Lesson 4: Circuit Relay v2

Welcome to Lesson 4! In this lesson, you'll learn how to use Circuit Relay v2 in js-libp2p to connect a private peer (behind NAT/firewall) to a public peer via a relay node. This is a critical skill for enabling universal connectivity in real-world networks.

---

## Objective
- Set up a relay node with circuit-relay-v2
- Configure a listener node (behind NAT) to reserve a slot on the relay
- Connect a dialer node to the listener via the relay
- Print a success message on connection

---

## Background: What is Circuit Relay v2?

Circuit Relay v2 is a protocol in libp2p that allows peers to connect even if one or both are behind NATs or firewalls. A relay node acts as an intermediary, forwarding traffic between peers that cannot connect directly.

---

## Step-by-Step Instructions

### 1. Install Dependencies

In the `app/` directory, ensure you have the following dependencies in your `package.json`:

```json
"dependencies": {
  "libp2p": "^0.46.7",
  "@libp2p/circuit-relay-v2": "^0.1.7",
  "@libp2p/tcp": "^8.0.6",
  "@chainsafe/libp2p-noise": "^10.0.0",
  "@libp2p/mplex": "^11.0.2",
  "@libp2p/peer-id-factory": "^4.2.4"
}
```

Install them with:
```sh
npm install
```

---

### 2. Create Three Node Scripts

You will create three scripts in the `app/` directory:
- `relay.js` — the relay node
- `listener.js` — the private/listener node (behind NAT)
- `dialer.js` — the dialer node (connects to listener via relay)

#### **relay.js**
```js
import { createLibp2p } from 'libp2p';
import { tcp } from '@libp2p/tcp';
import { noise } from '@chainsafe/libp2p-noise';
import { mplex } from '@libp2p/mplex';
import { circuitRelayServer } from '@libp2p/circuit-relay-v2';

const main = async () => {
  const node = await createLibp2p({
    addresses: { listen: ['/ip4/0.0.0.0/tcp/15003'] },
    transports: [tcp()],
    connectionEncryption: [noise()],
    streamMuxers: [mplex()],
    services: {
      relay: circuitRelayServer({ reservations: { maxReservations: 10 } })
    }
  });
  await node.start();
  console.log('Relay node started with id:', node.peerId.toString());
  node.getMultiaddrs().forEach(addr => console.log(addr.toString()));
};
main();
```

#### **listener.js**
```js
import { createLibp2p } from 'libp2p';
import { tcp } from '@libp2p/tcp';
import { noise } from '@chainsafe/libp2p-noise';
import { mplex } from '@libp2p/mplex';
import { circuitRelayClient } from '@libp2p/circuit-relay-v2';
import { createFromJSON } from '@libp2p/peer-id-factory';
import fs from 'fs';

const RELAY_MULTIADDR = '<REPLACE_WITH_RELAY_MULTIADDR>'; // e.g. /ip4/127.0.0.1/tcp/15003/p2p/<RelayPeerId>

const main = async () => {
  // Optionally load a persistent PeerId
  let peerId;
  if (fs.existsSync('./peer-id.json')) {
    const peerIdJson = JSON.parse(fs.readFileSync('./peer-id.json'));
    peerId = await createFromJSON(peerIdJson);
  }
  const node = await createLibp2p({
    peerId,
    addresses: { listen: [] },
    transports: [tcp()],
    connectionEncryption: [noise()],
    streamMuxers: [mplex()],
    services: {
      relay: circuitRelayClient()
    }
  });
  await node.start();
  // Reserve a slot on the relay
  const relayConn = await node.dial(RELAY_MULTIADDR);
  console.log('Listener node started with id:', node.peerId.toString());
  node.getMultiaddrs().forEach(addr => console.log(addr.toString()));
  // Print relay address for dialer
  const relayAddr = `${RELAY_MULTIADDR}/p2p-circuit/p2p/${node.peerId.toString()}`;
  console.log('Relay address for dialer:', relayAddr);
};
main();
```

#### **dialer.js**
```js
import { createLibp2p } from 'libp2p';
import { tcp } from '@libp2p/tcp';
import { noise } from '@chainsafe/libp2p-noise';
import { mplex } from '@libp2p/mplex';

const LISTENER_RELAY_ADDR = '<REPLACE_WITH_LISTENER_RELAY_ADDR>'; // e.g. /ip4/127.0.0.1/tcp/15003/p2p/<RelayPeerId>/p2p-circuit/p2p/<ListenerPeerId>

const main = async () => {
  const node = await createLibp2p({
    addresses: { listen: [] },
    transports: [tcp()],
    connectionEncryption: [noise()],
    streamMuxers: [mplex()]
  });
  await node.start();
  try {
    await node.dial(LISTENER_RELAY_ADDR);
    console.log('DIAL SUCCESS');
  } catch (err) {
    console.error('Dial failed:', err);
  }
};
main();
```

---

### 3. Run the Nodes

1. **Start the relay node:**
   ```sh
   node relay.js
   ```
   - Copy the relay's multiaddr and PeerId from the output.

2. **Start the listener node:**
   - Replace `<RELAY_MULTIADDR>` in `listener.js` with the relay's multiaddr (from above).
   ```sh
   node listener.js
   ```
   - Copy the relay address for the dialer from the output.

3. **Start the dialer node:**
   - Replace `<REPLACE_WITH_LISTENER_RELAY_ADDR>` in `dialer.js` with the relay address printed by the listener.
   ```sh
   node dialer.js
   ```
   - On success, you should see `DIAL SUCCESS`.

---

### 4. Docker Compose Usage

You can use Docker Compose to run all three nodes in isolated containers. Update `docker-compose.yaml` to define three services: relay, listener, and dialer. Example:

```yaml
version: '3.8'
services:
  relay:
    build: ./app
    command: node relay.js
    stdin_open: true
    tty: true
  listener:
    build: ./app
    command: node listener.js
    stdin_open: true
    tty: true
  dialer:
    build: ./app
    command: node dialer.js
    stdin_open: true
    tty: true
```

---

## Troubleshooting & Hints
- Ensure all multiaddrs are correct and up-to-date between steps.
- If you see connection errors, check firewall/NAT settings and that the relay is running.
- Use `console.log` to print all addresses and PeerIds for debugging.
- For more, see the [js-libp2p circuit relay example](https://github.com/libp2p/js-libp2p-examples/tree/main/examples/js-libp2p-example-circuit-relay).

---

## Resources
- [js-libp2p circuit relay example](https://github.com/libp2p/js-libp2p-examples/tree/main/examples/js-libp2p-example-circuit-relay)
- [js-libp2p documentation](https://libp2p.io/) 