# Lesson 2: Transport Layer - TCP Connection (JavaScript)

Building on your basic libp2p node, in this lesson you'll now learn about transport layers and establish your first peer-to-peer connections using TCP with Noise and Yamux.

# Learning Objectives

By the end of this lesson, you will:

- Understand libp2p's transport abstraction in JavaScript
- Configure TCP transport with security and multiplexing
- Establish a connection to a remote peer

## Background: Transport Layers in libp2p
In libp2p, transports handle the low-level network communication. A transport defines how data travels between peers. libp2p supports multiple transports:

- TCP: Reliable, ordered, connection-oriented (like HTTP)
- WebSockets: For browser and server connectivity
- WebRTC: For browser-to-browser connectivity
- Memory: For testing and local communication

Each transport can be enhanced with:

- Security protocols: Encrypt communication (e.g. Noise, TLS)
- Multiplexers: Share one connection for multiple streams (Yamux, Mplex)

## Transport Stack

The libp2p stack looks like the following when using TCP, Noise, and Yamux:
```
Application protocols (ping, gossipsub, etc.)
    ↕
Multiplexer (Yamux)
    ↕
Security (Noise)
    ↕
Transport (TCP)
    ↕
Network (IP)
```
# Your Task

Extend your application to:

- Parse remote peer addresses from an environment variable
- Establish a connection to a remote peer
- Print connection events for verification

# Step-by-Step Instructions

Step 1: **Install Required Dependencies**
First, make sure you have the necessary libp2p packages installed:

```javascript
npm install @libp2p/tcp @chainsafe/libp2p-noise @chainsafe/libp2p-yamux @multiformats/multiaddr @libp2p/identify
```
Step 2: **Add Imports**
In your `app/index.js`, ensure you have the necessary imports:

```
import { createLibp2p } from 'libp2p'
import { tcp } from '@libp2p/tcp'
import { noise } from '@libp2p/noise'
import { yamux } from '@libp2p/yamux'
import { ping } from '@libp2p/ping'
import { identify } from '@libp2p/identify'
import { multiaddr } from '@multiformats/multiaddr'
import { generateKeyPair } from '@libp2p/crypto/keys'
```

Step 3: **Parse the Multiaddr from Environment Variable**
In this workshop, one or more Multiaddr strings for remote peers is passed in the environment variable REMOTE_PEERS. It is important to note that the values in REMOTE_PEERS are not IP addresses but rather Multiaddr strings. A Multiaddr string looks like: /ip4/172.16.16.17/tcp/9092.
To parse the list of Multiaddr strings, add the following code to your main function:

```javascript
async function main() {
    console.log('Starting Universal Connectivity application...')

    // Parse the remote peer addresses from the environment variable
    let remoteAddrs = []
    if (process.env.REMOTE_PEERS) {
        remoteAddrs = process.env.REMOTE_PEERS
            .split(',')                     
            .map(addr => addr.trim())       
            .filter(addr => addr !== '')    
            .map(addr => multiaddr(addr))
    }

    // ... existing code ...
}
```

Step 4: **Configure Your libp2p Node**
Update your node configuration to include the transport stack. Replace your existing libp2p configuration with:

```javascript
    
    // Create the libp2p node
    const node = await createLibp2p({
        addresses: {
            listen: ['/ip4/0.0.0.0/tcp/0'] // Listen on any available port
        },
        transports: [
            tcp()
        ],
        connectionEncrypters: [
            noise()
        ],
        streamMuxers: [
            yamux()
        ],
        services: {
            ping: ping(),
            identify: identify()
        },
        connectionManager: {
            idleTimeout: 60000 // 60 seconds
        }
    })

    console.log('Local peer id:', node.peerId.toString())

}
```

Step 5: **Add Code to Dial the Remote Peer**
Right after you create your node and before you start it, add the code to dial the remote peer addresses:

```javascript
async function main() {

    // Start the node
    await node.start()
    console.log('Node started successfully')

    // Dial all of the remote peer Multiaddrs
    for (const addr of remoteAddrs) {
        try {
            console.log('Dialing:', addr.toString())
            await node.dial(addr)
        } catch (error) {
            console.error('Failed to dial', addr.toString(), ':', error.message)
        }
    }

}
```

Step 6: **Set Up Event Handling**
Add event listeners to handle connection events. In libp2p JavaScript, you listen for events on the node object:
```javascript
async function main() {

    // Set up event handlers
    node.addEventListener('connection:open', (event) => {
        const connection = event.detail
        console.log('Connection opened to:', connection.remotePeer.toString(), 'via', connection.remoteAddr.toString())
    })

    node.addEventListener('connection:close', (event) => {
        const connection = event.detail
        console.log('Connection closed to:', connection.remotePeer.toString())
    })

    // Keep the process running
    process.on('SIGINT', async () => {
        console.log('Shutting down...')
        await node.stop()
        process.exit(0)
    })

    console.log('Node is running. Press Ctrl+C to stop.')
}

main().catch(console.error)
```

Step 7: Complete Implementation
Here's how your complete src/index.js should look:
```javascript
import { createLibp2p } from 'libp2p'
import { tcp } from '@libp2p/tcp'
import { noise } from '@chainsafe/libp2p-noise'
import { yamux } from '@chainsafe/libp2p-yamux'
import { ping } from '@libp2p/ping'
import { identify } from '@libp2p/identify'
import { multiaddr } from '@multiformats/multiaddr'

async function main() {
    console.log('Starting Universal Connectivity application...')

    // Parse the remote peer addresses from the environment variable
    let remoteAddrs = []
    if (process.env.REMOTE_PEERS) {
        remoteAddrs = process.env.REMOTE_PEERS
            .split(',')                     // Split the string at ','
            .map(addr => addr.trim())       // Trim whitespace of each string
            .filter(addr => addr !== '')    // Filter out empty strings
            .map(addr => multiaddr(addr))   // Parse each string into Multiaddr
    }
    
    // Create the libp2p node
    const node = await createLibp2p({
        addresses: {
            listen: ['/ip4/0.0.0.0/tcp/0']
        },
        transports: [
            tcp()
        ],
        connectionEncryption: [
            noise()
        ],
        streamMuxers: [
            yamux()
        ],
        services: {
            ping: ping(),
            identify: identify()
        },
        connectionManager: {
            idleTimeout: 60000
        }
    })

    console.log('Local peer id:', node.peerId.toString())

    // Set up event handlers

    node.addEventListener('connection:open', (event) => {
        const connection = event.detail
        console.log('Connection opened to:', connection.remotePeer.toString(), 'via', connection.remoteAddr.toString())
    })

    node.addEventListener('connection:close', (event) => {
        const connection = event.detail
        console.log('Connection closed to:', connection.remotePeer.toString())
    })

    // Start the node
    await node.start()
    console.log("Listening on:")
    node.getMultiaddrs().forEach(addr => {
        console.log('  •', addr.toString())
    })

    // Dial all of the remote peer Multiaddrs
    for (const addr of remoteAddrs) {
        try {
            console.log('Dialing:', addr.toString())
            await node.dial(addr)
        } catch (error) {
            console.error('Failed to dial', addr.toString(), ':', error.message)
        }
    }

    // Keep the process running
    process.on('SIGINT', async () => {
        console.log('Shutting down...')
        await node.stop()
        process.exit(0)
    })

    console.log('Node is running. Press Ctrl+C to stop.')
}

main().catch(console.error)
```

## Testing Your Implementation
To test your implementation manually:

Set the environment variables:

```bash
export REMOTE_PEERS="/ip4/127.0.0.1/tcp/9092"
```

Run your application:
```bash
node app/index.js
```

You should see output similar to:

```bash
Starting Universal Connectivity application...
Local peer id: 12D3KooWJUxSjn1A9iYckqj3HNywfJiqF1J6VihqTCfRgko5u7h2
Listening on:
  • /ip4/127.0.0.1/tcp/59116/p2p/12D3KooWJUxSjn1A9iYckqj3HNywfJiqF1J6VihqTCfRgko5u7h2
  • /ip4/192.168.0.29/tcp/59116/p2p/12D3KooWJUxSjn1A9iYckqj3HNywfJiqF1J6VihqTCfRgko5u7h2
```

Success Criteria
Your implementation should:

✅ Display the startup message and local peer ID
✅ Successfully parse remote peer addresses from the environment variable
✅ Successfully dial the remote peer
✅ Establish a connection and print connection messages
✅ Handle graceful shutdown with Ctrl+C

What's Next?
Excellent! You've successfully configured TCP transport and established peer-to-peer connections in JavaScript. You now understand:

Transport Layer: How libp2p handles network communication in Node.js
Security: Noise protocol for encrypted connections
Multiplexing: Yamux for sharing connections
Connection Management: Handling incoming and outgoing connections
Event-Driven Programming: Responding to network events with event listeners

In the next lesson, you'll explore the ping protocol in more detail and connect to the instructor's server for your first checkpoint!
Key concepts you've learned:

libp2p Transport Stack: TCP + Noise + Yamux in JavaScript
Connection Events: Using event listeners for connection lifecycle
Listening and Dialing: Acting as both client and server
Multiaddresses: libp2p's addressing format in JavaScript

Next up: Deep diving into the ping protocol and achieving your first checkpoint!