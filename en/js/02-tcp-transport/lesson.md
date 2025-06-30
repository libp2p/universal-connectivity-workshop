# Lesson 2: TCP Transport

Welcome to Lesson 2! In this lesson, you'll set up TCP transport with Noise encryption and Yamux multiplexing in js-libp2p. You'll also learn to handle connection events and errors robustly.

## Objective
- Add TCP transport to your libp2p node
- Add Noise encryption and Yamux multiplexing
- Listen on a TCP address and print it
- Handle connection and error events

---

## Step-by-Step Instructions

1. **Install Dependencies**
   (If you haven't already, run:)
   ```sh
   npm install libp2p @libp2p/tcp @chainsafe/libp2p-noise @chainsafe/libp2p-yamux
   ```

2. **Update Your Node Setup**
   - In your `app/` directory, update or create `index.js` as follows:

   ```js
   import { createLibp2p } from 'libp2p';
   import { tcp } from '@libp2p/tcp';
   import { noise } from '@chainsafe/libp2p-noise';
   import { yamux } from '@chainsafe/libp2p-yamux';

   const main = async () => {
     try {
       const node = await createLibp2p({
         addresses: {
           listen: ['/ip4/0.0.0.0/tcp/0']
         },
         transports: [tcp()],
         connectionEncrypters: [noise()],
         streamMuxers: [yamux()]
       });

       node.addEventListener('peer:connect', (evt) => {
         console.log('Connected to:', evt.detail.remotePeer.toString());
       });

       node.addEventListener('peer:disconnect', (evt) => {
         console.log('Disconnected from:', evt.detail.remotePeer.toString());
       });

       node.addEventListener('error', (evt) => {
         console.error('Node error:', evt.detail);
       });

       await node.start();
       console.log('Listening on:');
       node.getMultiaddrs().forEach((addr) => {
         console.log(addr.toString());
       });
     } catch (err) {
       console.error('Failed to start libp2p node:', err);
       process.exit(1);
     }
   };

   main();
   ```

3. **Run Your Node**
   ```sh
   node app/index.js
   ```
   - You should see at least one valid TCP multiaddr printed.
   - Try connecting/disconnecting peers to see event logs (in later lessons).

---

## Hints

<details>
<summary>Hint 1: How do I handle connection events?</summary>
Use `node.addEventListener('peer:connect', handler)` and similar for disconnects.
</details>

<details>
<summary>Hint 2: How do I handle errors?</summary>
Wrap your async code in try/catch and listen for the 'error' event on the node.
</details>

<details>
<summary>Hint 3: Full Solution</summary>
See the code template above. Ensure you handle errors and print all listening addresses.
</details>

---

## Resources
- [js-libp2p Getting Started Guide](https://docs.libp2p.io/guides/getting-started/javascript)
- [js-libp2p API Docs](https://libp2p.github.io/js-libp2p/)
