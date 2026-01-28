# Lesson 5: Identify Checkpoint

In this lesson, you'll implement the **Identify protocol**, which allows peers to exchange information about their capabilities, supported protocols, and network details.

## Learning Objectives

- Understand the purpose and role of the Identify protocol
- Implement identify protocol handling
- Handle identify events and extract peer information
- Exchange protocol capabilities with remote peers

## What is the Identify Protocol?

The Identify protocol (`/ipfs/id/1.0.0`) is like a "business card" exchange between peers. When two peers connect, they automatically share:

1. **Peer ID** - Unique identifier derived from public key
2. **Agent Version** - Software name and version (e.g., "universal-connectivity/0.1.0")
3. **Protocol Version** - Protocol compatibility version
4. **Supported Protocols** - List of protocols the peer speaks (ping, identify, etc.)
5. **Listen Addresses** - How to reach this peer

## Four Core Purposes

| Purpose | Description |
|---------|-------------|
| **Capability Discovery** | Learn what protocols a peer supports |
| **Version Information** | Exchange software version and agent strings |
| **Address Discovery** | Learn how peers see your external addresses |
| **Protocol Negotiation** | Establish common protocols for communication |

## Key Changes from Lesson 4

1. **Add Identify protocol** alongside Ping
2. **Subscribe to identify events** to receive peer information
3. **Display peer capabilities** when identify is received

## Code Walkthrough

### Create Identify Components

```cpp
#include <libp2p/protocol/identify/identify.hpp>
#include <libp2p/protocol/identify/identify_msg_processor.hpp>

// Get required components from injector
auto conn_manager = injector.create<std::shared_ptr<libp2p::network::ConnectionManager>>();
auto identity_manager = injector.create<std::shared_ptr<libp2p::peer::IdentityManager>>();
auto key_marshaller = injector.create<std::shared_ptr<libp2p::crypto::marshaller::KeyMarshaller>>();

// Create Identify message processor
auto identify_msg_processor = std::make_shared<libp2p::protocol::IdentifyMessageProcessor>(
    *host, *conn_manager, *identity_manager, key_marshaller);

// Create Identify protocol
libp2p::protocol::IdentifyConfig identify_config;
auto identify = std::make_shared<libp2p::protocol::Identify>(
    identify_config, *host, identify_msg_processor, *bus);
```

### Subscribe to Identify Events

```cpp
auto identify_connection = identify->onIdentifyReceived(
    [](const libp2p::peer::PeerId& peer_id) {
        std::cout << "Identify received from: " << peer_id.toBase58() << std::endl;
    });
```

### Register Protocol Handler and Start

```cpp
// Set up identify protocol handler
host->setProtocolHandler(
    {identify->getProtocolId()},
    [identify](libp2p::StreamAndProtocol stream) {
        identify->handle(std::move(stream));
    });

// Start identify protocol (watches for new connections)
identify->start();
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LISTEN_PORT` | 9000 | TCP listening port |
| `QUIC_PORT` | 9001 | QUIC listening port |
| `REMOTE_PEERS` | (empty) | Comma-separated peer multiaddresses |

## Building and Running

```bash
# Build
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build .

# Run
./lesson

# With remote peer
REMOTE_PEERS="/ip4/192.168.1.100/tcp/9000/p2p/12D3KooW..." ./lesson
```

## Expected Output

```
Starting Universal Connectivity Application...
Local peer id: 12D3KooWxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Agent version: universal-connectivity/0.1.0
Protocol version: /ipfs/0.1.0
Listening on TCP: /ip4/0.0.0.0/tcp/9000
Listening on QUIC: /ip4/0.0.0.0/udp/9001/quic-v1
Protocols:
  - Ping: /ipfs/ping/1.0.0
  - Identify: /ipfs/id/1.0.0
Transports: TCP + QUIC
Waiting for connections...
Identify received from: 12D3KooWyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
```

## Observed Addresses

The Identify protocol also helps with NAT traversal by telling you how other peers see your address:

```cpp
// Get addresses observed by other peers
auto observed = identify->getAllObservedAddresses();
for (const auto& addr : observed) {
    std::cout << "Observed address: " << addr.getStringAddress() << std::endl;
}
```

## Next Steps

In Lesson 6, you'll learn about the DHT (Distributed Hash Table) for decentralized peer discovery.
