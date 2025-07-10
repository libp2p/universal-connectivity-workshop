# Lesson 1: Identity & Swarm Basics

Welcome to your first step in building a universal connectivity app with js-libp2p!

## Learning Objectives

By the end of this lesson, you will:

- Understand what a PeerId is and why it's important
- Create cryptographic keypairs for peer identification
- Initialize a basic libp2p node
- Listen for and handle basic network events
- Run your first libp2p application

## Background: Peer Identity in libp2p

In traditional client-server applications, servers have known addresses (like domain names), but clients are anonymous. In peer-to-peer networks, every participant is both a client and a server, so each peer needs a stable, verifiable identity.
libp2p uses cryptographic keypairs for peer identity:

- Private Key: Kept secret, used to sign messages and prove identity
- Public Key: Shared with others, used to verify signatures
- PeerId: A hash of the public key, used as a short identifier

This design ensures that:

- Peers can prove they control their identity (via signatures)
- Others can verify that proof (via public key cryptography)
- Identities are compact and easy to share (via PeerId hash)

## Your Task

Create a JavaScript/TypeScript application that:

- Generates a keypair for peer identity (or uses auto-generated one)
- Creates a basic libp2p node with essential protocols
- Prints the peer's ID and listening addresses when the application starts
- Handles basic network events
- Runs the event loop and responds to network activity

## Step-by-Step Instructions

0. **Prerequisites**

| Tool                  | Recommended version |
| ----------------------| ------------------- | 
| Node                  | ≥ 18 LTS            | 
| npm                   | ≥ 9                 |
| TypeScript (optional) | ≥ 5.4               |


1. **Install Dependencies**
First, initialize your project and add the required dependencies:

```bash
npm init -y
npm install libp2p @libp2p/tcp @libp2p/ping @chainsafe/libp2p-noise @chainsafe/libp2p-yamux @libp2p/ping
```

For TypeScript support (optional):

```bash
npm install -D typescript @types/node
npx tsc --init
```

2. **Set Up Your Main Function and Print Startup Message``

```javascript
// index.js
import { createLibp2p } from 'libp2p';
import { tcp } from '@libp2p/tcp';
import { noise } from '@chainsafe/libp2p-noise';
import { yamux } from '@chainsafe/libp2p-yamux';
import { ping } from '@libp2p/ping';

const main = async () => {
  console.log('Starting Universal Connectivity Application...');
  
  // Step 2 code goes here
  
};

main().catch((error) => {
  console.error('Error:', error);
  process.exit(1);
});

```
3. **Create the libp2p Node**

Configure and create your libp2p node with essential protocols:

```
const node = await createLibp2p({
  addresses: {
    listen: ['/ip4/0.0.0.0/tcp/0'] // Listen on any available port
  },
  transports: [tcp()],
  connectionEncrypters: [noise()],
  streamMuxers: [yamux()],
  services: {
    ping: ping({
      protocolPrefix: 'ipfs', // default
    })
  }
});
```

4. **Print Identity and Network Information**
Add logging to show your peer's identity and network details:

```javascript
await node.start();

console.log('Local peer id:', node.peerId.toString());
console.log('Listening on:');
node.getMultiaddrs().forEach((addr) => {
  console.log(' ', addr.toString());
});
```

5. **Handle Network Events**

Add event listeners to observe network activity:

```javascript
// Listen for peer connections
node.addEventListener('peer:connect', (evt) => {
  console.log('Connected to:', evt.detail.toString());
});

// Listen for peer disconnections
node.addEventListener('peer:disconnect', (evt) => {
  console.log('Disconnected from:', evt.detail.toString());
});

console.log('Node is running. Press Ctrl+C to stop.');
```

6. **Keep the Application Running**

Add a way to keep the application running and handle graceful shutdown:

```javascript
// Keep the process running
const cleanup = async () => {
  console.log('\nShutting down...');
  await node.stop();
  process.exit(0);
};

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);

// Keep the process alive
process.stdin.resume();
```

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

## Complete Solution Structure
Your complete index.js should look like this:

```javascript
import { createLibp2p } from 'libp2p';
import { tcp } from '@libp2p/tcp';
import { noise } from '@chainsafe/libp2p-noise';
import { yamux } from '@chainsafe/libp2p-yamux';
import { ping } from '@libp2p/ping';

const main = async () => {
  console.log('Starting Universal Connectivity Application...');
  
  // Create the libp2p node
  const node = await createLibp2p({
    addresses: {
      listen: ['/ip4/0.0.0.0/tcp/0']
    },
    transports: [tcp()],
    connectionEncrypters: [noise()],
    streamMuxers: [yamux()],
    services: {
      ping: ping({
        protocolPrefix: 'ipfs',
      })
    }
  });

  // Start the node
  await node.start();

  // Print identity and network information
  console.log('Local peer id:', node.peerId.toString());
  console.log('Listening on:');
  node.getMultiaddrs().forEach((addr) => {
    console.log(' ', addr.toString());
  });

  // Handle network events
  node.addEventListener('peer:connect', (evt) => {
    console.log('Connected to:', evt.detail.toString());
  });

  node.addEventListener('peer:disconnect', (evt) => {
    console.log('Disconnected from:', evt.detail.toString());
  });

  console.log('Node is running. Press Ctrl+C to stop.');

  // Graceful shutdown
  const cleanup = async () => {
    console.log('\nShutting down...');
    await node.stop();
    process.exit(0);
  };

  process.on('SIGINT', cleanup);
  process.on('SIGTERM', cleanup);

  // Keep the process alive
  process.stdin.resume();
};

main().catch((error) => {
  console.error('Error:', error);
  process.exit(1);
});
```

## Testing Your Solution
Run your application with:

```bash
node index.js
```

You should see output similar to:
```
Starting Universal Connectivity Application...
Local peer id: 12D3KooWQ6ERu4LGLQFZMkWzdjNcUbxE2UqLQWX5bXBkYU2jcySd
Listening on:
  /ip4/127.0.0.1/tcp/54321
  /ip4/192.168.1.100/tcp/54321
Node is running. Press Ctrl+C to stop.
```
The PeerId and port numbers will be different each time you run the application.

## Hints

</details>
<details>
<summary>Hint: ES Modules</summary>
Make sure your package.json includes:

```json
{
  "type": "module"
}
```

Or use .mjs extension for your files to enable ES module imports.
</details>

## Advanced: Custom Identity
If you want to create a persistent identity (like the Rust version does explicitly), you can generate a keypair:

```javascript
import { generateKeyPair } from '@libp2p/crypto/keys';

// Generate an Ed25519 keypair
const privateKey = await generateKeyPair('Ed25519');
const peerId = await createFromPrivKey(privateKey);

const node = await createLibp2p({
  peerId: peerId, // Use your custom identity
  // ... rest of config
});
```

## Resources
- [js-libp2p Getting Started Guide](https://docs.libp2p.io/guides/getting-started/javascript)
- [js-libp2p API Docs](https://libp2p.github.io/js-libp2p/)


## What's Next?

Excellent work! You've created your first libp2p node with a stable identity and basic networking capabilities. In the next lesson, you'll learn how to connect to other peers and exchange data.
Key concepts you've learned:

- Peer Identity: Every libp2p node has a cryptographic identity (PeerId)
- Transports: TCP transport enables network connections
- Security: Noise protocol encrypts all communications
- Multiplexing: Yamux allows multiple streams over one connection
- Services: Ping protocol enables basic connectivity testing
- Event System: libp2p uses events to notify about network activity

Next up: Connecting to other peers and sending your first ping messages!