# Gossipsub Pub/Sub Chat Example

This example demonstrates a simple group chat using libp2p with Gossipsub pub/sub protocol.

## Setup

1. Install dependencies:
   ```sh
   npm install libp2p @libp2p/tcp @libp2p/websockets @chainsafe/libp2p-noise @chainsafe/libp2p-yamux @chainsafe/libp2p-gossipsub @libp2p/peer-id-factory
   ```

2. Run one or more chat nodes:
   ```sh
   node chat-node.js
   ```

3. Copy a multiaddr from one node and connect from another:
   ```sh
   node chat-node.js <multiaddr>
   ```

4. Type messages in any terminal to broadcast to all peers.

## How it works

- Each node uses libp2p with Gossipsub for pub/sub messaging.
- Nodes join the same topic and broadcast messages.
- You can connect nodes using their multiaddrs.

## References
- [js-libp2p pubsub example](https://github.com/libp2p/js-libp2p-examples/blob/main/examples/js-libp2p-example-pubsub/README.md) 