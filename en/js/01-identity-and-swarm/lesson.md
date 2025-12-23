# Lesson 1: Identity & Swarm Basics

Welcome to your first step in building a universal connectivity app with js-libp2p!

## Learning Objectives

By the end of this lesson, you will:

- Understand what a PeerId is and why it's important
- Create a libp2p node with identity
- Generate and display a valid peer ID

## Background: Peer Identity in libp2p

In peer-to-peer networks, every participant needs a stable, verifiable identity. libp2p uses cryptographic keypairs:

- **Private Key**: Kept secret, used to sign messages
- **Public Key**: Shared with others, used to verify signatures
- **PeerId**: A hash of the public key (starts with `12D3KooW`)

When you create a libp2p node, a keypair is automatically generated, giving you a unique peer identity.

## Your Task

Create a JavaScript application that:

1. Creates a libp2p node with essential protocols
2. Prints the startup message: `Starting Universal Connectivity Application`
3. Prints the peer ID: `Local peer id: <your-peer-id>`

## Step-by-Step Instructions

### 1. Set Up the Project

Ensure you have:
- Docker and Docker Compose installed
- Python 3 (for validation script)

### 2. Navigate to the Lesson Directory

```bash
cd en/js/01-identity-and-swarm
```

### 3. Create Your Application

Edit `app/index.js`:

```javascript
import { createLibp2p } from 'libp2p';
import { tcp } from '@libp2p/tcp';
import { noise } from '@chainsafe/libp2p-noise';
import { yamux } from '@chainsafe/libp2p-yamux';
import { ping } from '@libp2p/ping';

async function main() {
  console.log('Starting Universal Connectivity Application');

  const node = await createLibp2p({
    addresses: {
      listen: []
    },
    transports: [tcp()],
    connectionEncryption: [noise()],
    streamMuxers: [yamux()],
    services: {
      ping: ping()
    }
  });

  console.log(`Local peer id: ${node.peerId.toString()}`);
  
  // Keep the process alive briefly
  const keepAliveMs = Number(process.env.KEEPALIVE_MS || '10000');
  await new Promise((resolve) => setTimeout(resolve, keepAliveMs));

  await node.stop();
}

main().catch((err) => {
  console.error(err?.message ?? err);
  process.exit(1);
});
```

### 4. Run and Test

```bash
# Set environment variables
export PROJECT_ROOT="$(pwd)/../.."
export LESSON_PATH="en/js/01-identity-and-swarm"

# Ensure stdout.log exists as a file
touch stdout.log

# Build and run
docker compose up -d --build

# Wait a few seconds for the app to run, then check
sleep 5
python3 check.py

# Clean up
docker compose down -v
```

## Expected Output

Your `stdout.log` should contain:

```
Starting Universal Connectivity Application
Local peer id: 12D3KooW...
```

The peer ID will be different each time (unless you configure a persistent identity).

## Key Concepts

- **PeerId**: Unique identifier for your node (automatically generated)
- **Transports**: TCP enables network connections
- **Connection Encryption**: Noise protocol secures communications
- **Stream Muxers**: Yamux allows multiple streams over one connection
- **Services**: Ping protocol enables basic connectivity testing

## What's Next?

Excellent work! You've created your first libp2p node with a stable identity. In the next lesson, you'll learn how to connect to other peers and establish TCP connections.
