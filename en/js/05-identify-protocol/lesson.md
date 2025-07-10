# Lesson 5: Identify Protocol (Checkpoint 2)

Welcome to Checkpoint 2! In this lesson, you'll implement the identify protocol in js-libp2p, connect to a remote peer, and extract its PeerId and supported protocols.

## Objective
- Implement the identify protocol for peer capability discovery
- Connect to a remote peer and extract its PeerId and supported protocols

---

## Step-by-Step Instructions

1. **Install Dependencies**
   (If you haven't already, run:)
   ```sh
   npm install
   ```

2. **Generate Your PeerId**
   Run the following command in your app directory:
   ```sh
   node generate-peer-id.js
   ```
   This will create a `peer-id.json` file required for your node.

3. **Update Your Node Setup**
   - In your `app/` directory, update or create `index.js` as follows:

   ```js
   import fs from 'fs';
   import { createLibp2p } from 'libp2p';
   import { tcp } from '@libp2p/tcp';
   import { quic } from '@chainsafe/libp2p-quic';
   import { noise } from '@chainsafe/libp2p-noise';
   import { yamux } from '@chainsafe/libp2p-yamux';
   import { identify } from '@libp2p/identify';
   import { createFromJSON } from '@libp2p/peer-id-factory';
   import { multiaddr } from '@multiformats/multiaddr';

   const main = async () => {
     const peerIdJson = JSON.parse(fs.readFileSync('./peer-id.json'));
     const peerId = await createFromJSON(peerIdJson);

     const node = await createLibp2p({
       peerId,
       addresses: {
         listen: [
           '/ip4/0.0.0.0/tcp/0',
           '/ip4/0.0.0.0/udp/0/quic-v1'
         ]
       },
       transports: [tcp(), quic()],
       connectionEncrypters: [noise()],
       streamMuxers: [yamux()],
       services: {
         identify: identify()
       }
     });

     await node.start();
     console.log(`Node Peer ID: ${node.peerId.toString()}`);
     console.log('Listening on:');
     node.getMultiaddrs().forEach(addr => {
       console.log(addr.toString());
     });

     if (process.argv.length > 2) {
       const remoteAddr = process.argv[2];
       try {
         const ma = multiaddr(remoteAddr);
         const conn = await node.dial(ma);
         const remotePeer = conn.remotePeer;
         const protocols = await node.services.identify.getProtocols(remotePeer);
         console.log(`Remote PeerId: ${remotePeer.toString()}`);
         console.log('Protocols:', protocols);
       } catch (err) {
         console.error('Failed to connect or identify remote peer:', err);
       }
     }
   };

   main();
   ```

4. **Run Your Node**
   - Start your node:
     ```sh
     node app/index.js
     ```
   - In a new terminal, run another instance and connect to the first node:
     ```sh
     node app/index.js <multiaddr-of-first-node>
     ```
   - You should see the remote PeerId and supported protocols printed.

---

## Hints

<details>
<summary>Hint 1: How do I use the identify service?</summary>
Add `identify: identify()` to the `services` property in your libp2p config.
</details>

<details>
<summary>Hint 2: How do I connect to a remote peer?</summary>
Use the `@multiformats/multiaddr` module to parse the address, then call `node.dial(ma)`.
</details>

<details>
<summary>Hint 3: How do I get the remote peer's protocols?</summary>
Use `node.services.identify.getProtocols(remotePeer)` after dialing.
</details>

<details>
<summary>Hint 4: Full Solution</summary>
See the code template above. Ensure you handle errors and print the required information.
</details>

---

## Resources
- [js-libp2p Getting Started Guide](https://docs.libp2p.io/guides/getting-started/javascript)
- [js-libp2p API Docs](https://libp2p.github.io/js-libp2p/)
- [js-libp2p Identify Service](https://libp2p.github.io/js-libp2p/modules/_libp2p_identify.html)
