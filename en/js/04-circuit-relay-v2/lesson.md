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
  "@chainsafe/libp2p-noise": "^16.1.4",
  "@chainsafe/libp2p-yamux": "^7.0.4",
  "@libp2p/circuit-relay-v2": "^3.2.24",
  "@libp2p/crypto": "^5.1.8",
  "@libp2p/identify": "^3.0.39",
  "@libp2p/mplex": "^11.0.47",
  "@libp2p/peer-id": "^5.1.9",
  "@libp2p/tcp": "^10.1.19",
  "@libp2p/websockets": "^9.2.19",
  "@multiformats/multiaddr": "^12.5.1",
  "libp2p": "^2.10.0"
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
import { noise } from "@chainsafe/libp2p-noise";
import { yamux } from "@chainsafe/libp2p-yamux";
import { circuitRelayServer } from "@libp2p/circuit-relay-v2";
import { identify } from "@libp2p/identify";
import { webSockets } from "@libp2p/websockets";
import { tcp } from "@libp2p/tcp";
import { createLibp2p } from "libp2p";
import { peerIdFromPrivateKey } from "@libp2p/peer-id";
import { keys } from "@libp2p/crypto";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function createNode() {
  const peerIdPath = path.join(__dirname, "peer-id.json");
  const peerIdJson = JSON.parse(fs.readFileSync(peerIdPath, "utf8"));
  const privateKeyBytes = Buffer.from(peerIdJson.privKey, "base64");
  const privateKey = keys.privateKeyFromProtobuf(privateKeyBytes);
  // Generate peer ID from the private key
  const peerId = peerIdFromPrivateKey(privateKey);
  console.log("PeerId:", peerId.toString());

  const node = await createLibp2p({
    privateKey,
    addresses: {
      listen: ["/ip4/0.0.0.0/tcp/4001", "/ip4/0.0.0.0/tcp/4002/ws"],
    },
    transports: [tcp(), webSockets()],
    connectionEncrypters: [noise()],
    streamMuxers: [yamux()],
    services: {
      identify: identify(),
      relay: circuitRelayServer({ reservations: 15 }),
    },
  });
  return node;
}

async function main() {
  const node = await createNode();

  await node.start();
  node.addEventListener("error", (evt) => {
    console.error("Node error:", evt.detail);
  });

  console.log(`PeerId: ${node.peerId.toString()}`);
  console.log(`Node started with id ${node.peerId.toString()}`);
  console.log("Listening on:");
  const multiaddrs = node.getMultiaddrs();
  multiaddrs.forEach((ma) => console.log(ma.toString()));

  // Keep the node running
  process.on("SIGTERM", async () => {
    console.log("Shutting down relay node...");
    await node.stop();
  });
}

main().catch(console.error);


```

#### **listener.js**

```js
import { noise } from "@chainsafe/libp2p-noise";
import { yamux } from "@chainsafe/libp2p-yamux";
import { circuitRelayTransport } from "@libp2p/circuit-relay-v2";
import { identify } from "@libp2p/identify";
import { webSockets } from "@libp2p/websockets";
import { createLibp2p } from "libp2p";
import { multiaddr } from "@multiformats/multiaddr";
import { tcp } from "@libp2p/tcp";

const relayAddr = process.argv[2];
if (!relayAddr) {
  throw new Error("Relay address must be provided as command line argument");
}

const node = await createLibp2p({
  addresses: {
    listen: ["/p2p-circuit"],
  },
  transports: [webSockets(), circuitRelayTransport(), tcp()],
  connectionEncrypters: [noise()],
  streamMuxers: [yamux()],
  services: {
    identify: identify(),
  },
});

console.log(`Node started with id ${node.peerId.toString()}`);
const conn = await node.dial(multiaddr(relayAddr));
console.log(`Connected to the relay ${conn.remotePeer.toString()}`);

node.addEventListener("self:peer:update", (evt) => {
  const relayAddresses = node
    .getMultiaddrs()
    .filter((ma) => ma.toString().includes("/p2p-circuit/"));
  if (relayAddresses.length > 0) {
    console.log(
      `Advertising with a relay address of ${relayAddresses[0].toString()}`
    );
  }
});

// Keep the node running
process.on("SIGTERM", async () => {
  console.log("Shutting down listener node...");
  await node.stop();
});

```

#### **dialer.js**

```js
import { createLibp2p } from "libp2p";
import { tcp } from "@libp2p/tcp";
import { noise } from "@chainsafe/libp2p-noise";
import { yamux } from "@chainsafe/libp2p-yamux";
import { multiaddr } from "@multiformats/multiaddr";
import { webSockets } from "@libp2p/websockets";
import { circuitRelayTransport } from "@libp2p/circuit-relay-v2";
import { identify } from "@libp2p/identify";

const LISTENER_RELAY_ADDR = process.argv[2];
if (!LISTENER_RELAY_ADDR) {
  throw new Error(
    "Listener relay address must be provided as command line argument"
  );
}

const main = async () => {
  try {
    const node = await createLibp2p({
      addresses: { listen: [] },
      transports: [tcp(), webSockets(), circuitRelayTransport()],
      connectionEncrypters: [noise()],
      streamMuxers: [yamux()],
      services: {
        identify: identify(),
      },
    });

    await node.start();
    console.log(`Node started with id ${node.peerId.toString()}`);

    try {
      await node.dial(multiaddr(LISTENER_RELAY_ADDR));
      console.log(`Connected to the listener node via ${LISTENER_RELAY_ADDR}`);
      console.log("DIAL SUCCESS");
    } catch (err) {
      console.error("Dial failed:", err);
      process.exit(1);
    }

    // Keep node running briefly to maintain connection
    setTimeout(async () => {
      console.log("Shutting down dialer node...");
      await node.stop();
    }, 5000);
  } catch (err) {
    console.error("Dialer setup failed:", err);
    process.exit(1);
  }
};

main().catch(console.error);
```

---

### 3. Run the Nodes

1. **Generate a relay PeerId file (creates `app/peer-id.json`)**:

   ```sh
   cd app
   node generate_peer_id.js
   ```

2. **Start the relay node:**

   ```sh
   node relay.js
   ```

   - Copy the relay's multiaddr and PeerId from the output.

3. **Start the listener node:**

   - Replace `<RELAY_MULTIADDR>` in `listener.js` with the relay's multiaddr (from above).

   ```sh
   node listener.js
   ```

   - Copy the relay address for the dialer from the output.

4. **Start the dialer node:**
   - Replace `<REPLACE_WITH_LISTENER_RELAY_ADDR>` in `dialer.js` with the relay address printed by the listener.
   ```sh
   node dialer.js
   ```
   - On success, you should see `DIAL SUCCESS`.

---

### 4. Docker Compose Usage

You can use Docker Compose to run all three nodes in isolated containers. Update `docker-compose.yaml` to define three services: relay, listener, and dialer. Example:

```yaml
version: "3.8"
services:
  lesson:
    build:
      context: ./app
      dockerfile: Dockerfile
    container_name: ucw-lesson-04-circuit-relay-v2-js
    stop_grace_period: 1m
    volumes:
      - ./relay.log:/app/relay.log
    networks:
      workshop-net:
        ipv4_address: 172.16.16.16

  checker:
    build:
      context: .
      dockerfile: ./checker/Dockerfile
    container_name: ucw-checker-04-circuit-relay-v2-js
    depends_on:
      - lesson
    stop_grace_period: 1m
    environment:
      - TIMEOUT_DURATION=${TIMEOUT_DURATION:-30s}
    volumes:
      - ./checker.log:/app/checker.log
      - ./relay.log:/app/relay.log
      - ./listener.log:/app/listener.log
      - ./dialer.log:/app/dialer.log
    networks:
      workshop-net:
        ipv4_address: 172.16.16.17

networks:
  workshop-net:
    name: workshop-net
    external: false
    driver: bridge
    ipam:
      config:
        - subnet: 172.16.16.0/24 
```

### 5. Check using check.py

Follow these steps to validate your setup using the provided checker. Run all commands from the `en/js/04-circuit-relay-v2/` directory unless stated otherwise.

1. Save logs of relay.js in relay.log:

- Copy the printed console logs after you run relay.js and paste them in relay.log. The output looks like:
  ```
  PeerId: <RelayPeerId>
  Node started with id <RelayPeerId>
  Listening on:
  /ip4/127.0.0.1/tcp/<PORT_1>/p2p/<RelayPeerId>
  /ip4/172.21.249.132/tcp/<PORT_1>/p2p/<RelayPeerId>
  /ip4/127.0.0.1/tcp/<PORT_2>/ws/p2p/<RelayPeerId>
  /ip4/172.21.249.132/tcp/<PORT_2>/ws/p2p/<RelayPeerId>
  ```

2. Save logs of listener.js in listener.log:

- Copy the listener output to listener.log. The output looks like:
  ```
  Node started with id <ListenerPeerId>
  Connected to the relay <RelayPeerId>
  Advertising with a relay address of /ip4/127.0.0.1/tcp/<PORT>/p2p/<RelayPeerId>/p2p-circuit/p2p/<ListenerPeerId>
  ```

3. Save logs of dialer.js in dialer.log:

- Copy the dialer logs from the console to dialer.log file. The output looks like:
  ```
  Node started with id <DialerPeerId>
  Connected to the listener node via /ip4/127.0.0.1/tcp/<PORT>/p2p/<RelayPeerId>/p2p-circuit/p2p/<ListenerPeerId>
  DIAL SUCCESS
  ```

4. Run the checker from the lesson directory:

In a separate tab in the terminal, run from outside the /app directory:

```sh
python3 check.py \
  --relay-log app/relay.log \
  --listener-log app/listener.log \
  --dialer-log app/dialer.log \
  --relay-peerid-json app/peer-id.json
```
You should see: 
`✓ All nodes validated successfully! Your circuit relay v2 setup is correct.`
Note:

- The relay must use the `peer-id.json` generated in step 1 (already wired in `relay.js`).

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
