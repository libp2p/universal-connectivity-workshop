# Lesson 3: Ping Protocol (Checkpoint 1)

Welcome to your first checkpoint! In this lesson, you'll implement the ping protocol using js-libp2p and connect to a remote peer to exchange ping messages.

## Objective
- Add ping protocol to your libp2p node
- Connect to a remote peer using a multiaddr
- Exchange ping messages and print latency

---

## Step-by-Step Instructions

1. **Install Dependencies**
   (If you haven't already, run:)
   ```sh
   cd 03-ping-protocol/app
   npm i @libp2p/ping @libp2p/identify @multiformats/multiaddr @libp2p/tcp @chainsafe/libp2p-noise @chainsafe/libp2p-yamux libp2p @libp2p/interface it-protobuf-stream protons-runtime
   ```

2. **Run Your Node**
   - Start one instance with no arguments:

     ```sh
     cd 02-tcp-transport/app

     node peer1.js 

     libp2p has started
     listening on: /ip4/192.168.0.7/tcp/57375/p2p/  12D3KooWGQZENtJNpBvcRVaYNYD1ZX9UwnZfR1DbNFtFY1q3hvak
     listening on: /ip4/127.0.0.1/tcp/57375/p2p/    12D3KooWGQZENtJNpBvcRVaYNYD1ZX9UwnZfR1DbNFtFY1q3hvak
     listening on: /ip4/172.27.192.1/tcp/57375/p2p/12D3KooWGQZENtJNpBvcRVaYNYD1ZX9UwnZfR1DbNFtFY1q3hvak     
     ```

     - Copy the `/ip4/...` maddr printed.

   - In a new terminal, run:
     ```sh
     cd 03-ping-protocol/app

     node peer2.js /ip4/127.0.0.1/tcp/57375/p2p/12D3KooWGQZENtJNpBvcRVaYNYD1ZX9UwnZfR1DbNFtFY1q3hvak

     libp2p has started
     listening on: /ip4/192.168.0.7/tcp/57379/p2p/12D3KooWGBqHs54L7tYgMBpjYXMmiFhkvAEck81MfJ5rYm7cSL7K
     listening on: /ip4/127.0.0.1/tcp/57379/p2p/12D3KooWGBqHs54L7tYgMBpjYXMmiFhkvAEck81MfJ5rYm7cSL7K
     listening on: /ip4/172.27.192.1/tcp/57379/p2p/     12D3KooWGBqHs54L7tYgMBpjYXMmiFhkvAEck81MfJ5rYm7cSL7K
     ```
     (Replace with the maddr from the first instance.)
   - You should see a successful ping and latency printed.

   ```
   pinging remote peer at /ip4/127.0.0.1/tcp/57375/p2p/12D3KooWGQZENtJNpBvcRVaYNYD1ZX9UwnZfR1DbNFtFY1q3hvak
   
   pinged /ip4/127.0.0.1/tcp/57375/p2p/12D3KooWGQZENtJNpBvcRVaYNYD1ZX9UwnZfR1DbNFtFY1q3hvak in 253ms
   ```

---

## Hints

<details>
<summary>Hint 1: How do I use the ping service?</summary>
Add `ping: ping()` to the `services` property in your libp2p config.
</details>

<details>
<summary>Hint 2: How do I connect to a remote peer?</summary>
Use the `@multformats/multiaddr` module to parse the address, then call `node.services.ping.ping(ma)`.
</details>

<details>
<summary>Hint 3: Full Solution</summary>
See the code template above. Make sure to handle errors and print the latency.
</details>

---

# Direct Message Protocol: Insights and Implementation

## What is the Direct Message Protocol?
The Direct Message (DM) protocol allows peers to send and receive custom messages (such as chat or commands) over libp2p streams. It uses protobuf for message encoding, supports metadata, and robustly handles connection, stream, and error management. This protocol is a real-world example of how to extend libp2p with your own protocols.

## How is it Implemented?
- **Protocol Registration:** The DM service registers the `/universal-connectivity/dm/1.0.0` protocol with libp2p, handling connect/disconnect and incoming streams.
- **Protobuf Usage:** Messages are encoded/decoded using protobuf definitions (mocked in this lesson for simplicity).
- **Event-Driven:** The service emits a `message` event when a DM is received.
- **Error Handling:** Handles timeouts, missing data, and protocol errors robustly.

## How to Use in Your Node
1. **Register the Service:**
   ```js
   import { directMessage } from './direct-message.js';
   // ...
   services: {
     // ...
     directMessage: directMessage(),
   }
   ```
2. **Send a Direct Message:**
   ```js
   await node.services.directMessage.send(peerId, 'Hello, world!');
   ```
3. **Listen for Incoming DMs:**
   ```js
   node.services.directMessage.addEventListener('message', (event) => {
     const { content, type, connection } = event.detail;
     console.log(`Received DM: ${content} (type: ${type}) from ${connection.remotePeer.toString()}`);
   });
   ```

## Why is this Important?
- Teaches how to extend libp2p with custom protocols
- Demonstrates robust event-driven and error-handling patterns
- Prepares you for building real-world P2P messaging and command systems

## Summary Table
| Concept                | What to Learn/Do                                      |
|------------------------|------------------------------------------------------|
| Protocol Registration  | How to register a custom protocol with libp2p        |
| Protobuf Usage         | How to encode/decode messages                        |
| Event Handling         | How to listen for and emit events                    |
| Error Handling         | How to handle timeouts, missing data, protocol errors|
| Sending/Receiving DMs  | How to send and receive direct messages              |

---

## Resources
- [js-libp2p Getting Started Guide](https://docs.libp2p.io/guides/getting-started/javascript)
- [js-libp2p API Docs](https://libp2p.github.io/js-libp2p/)
- [js-libp2p Ping Service](https://libp2p.github.io/js-libp2p/modules/_libp2p_ping.html)
