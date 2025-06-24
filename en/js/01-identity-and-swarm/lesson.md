# Lesson 1: Identity & Swarm Basics

Welcome to your first step in building a universal connectivity app with js-libp2p!

## Objective
- Generate a PeerId
- Set up a minimal js-libp2p node with TCP transport
- Print your PeerId and listening addresses
- Observe basic node events

---

## Step-by-Step Instructions

1. **Install Dependencies**
   ```sh
   npm install libp2p @libp2p/tcp @chainsafe/libp2p-noise @chainsafe/libp2p-yamux
   ```

2. **Generate a PeerId and Set Up Node**
   - Create `index.js` in your `app/` directory.
   - Use the following template to get started:

   ```js
   import { createLibp2p } from 'libp2p';
   import { tcp } from '@libp2p/tcp';
   import { noise } from '@chainsafe/libp2p-noise';
   import { yamux } from '@chainsafe/libp2p-yamux';

   const main = async () => {
     const node = await createLibp2p({
       addresses: {
         listen: ['/ip4/0.0.0.0/tcp/0']
       },
       transports: [tcp()],
       connectionEncrypters: [noise()],
       streamMuxers: [yamux()]
     });

     await node.start();
     console.log('PeerId:', node.peerId.toString());
     console.log('Listening on:');
     node.getMultiaddrs().forEach((addr) => {
       console.log(addr.toString());
     });
   };

   main().catch(console.error);
   ```

3. **Run Your Node**
   ```sh
   node app/index.js
   ```
   - You should see your PeerId and at least one listening address printed.

---

## Hints

<details>
<summary>Hint 1: How do I generate a PeerId?</summary>
PeerId is generated automatically when you create a libp2p node with `createLibp2p`.
</details>

<details>
<summary>Hint 2: What should I print?</summary>
Print your PeerId using `node.peerId.toString()` and each address from `node.getMultiaddrs()`.
</details>

<details>
<summary>Hint 3: Full Solution</summary>
See the code template above. Make sure to install all dependencies and run the script from the correct directory.
</details>

---

## Resources
- [js-libp2p Getting Started Guide](https://docs.libp2p.io/guides/getting-started/javascript)
- [js-libp2p API Docs](https://libp2p.github.io/js-libp2p/)
