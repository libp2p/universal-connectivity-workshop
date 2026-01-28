# Lesson 6: Gossipsub Checkpoint

In this lesson, you'll implement **Gossipsub**, a scalable publish-subscribe protocol for peer-to-peer messaging. Gossipsub is the backbone of decentralized communication in libp2p, powering everything from chat applications to blockchain block propagation.

## Learning Objectives

By the end of this lesson, you will:

- Understand why Gossipsub exists and how it improves on naive flooding
- Know the difference between mesh peers and gossip peers
- Configure Gossipsub parameters (`D_min`, `D_max`, heartbeat interval)
- Subscribe to topics and handle incoming messages
- Publish messages to topic subscribers
- Understand how Gossipsub handles misbehaving peers

## Background: Why Gossipsub?

### The Problem with Naive Flooding

The simplest pub/sub approach is **flooding**: when a peer receives a message, it forwards it to every other peer it knows. This has serious problems:

- **Bandwidth waste**: Every peer sends `N-1` copies of every message (where N = connected peers)
- **No scalability**: Network traffic grows as O(N²) with the number of peers
- **Amplification attacks**: A malicious peer can flood the network with messages

### How Gossipsub Solves This

Gossipsub (`/meshsub/1.0.0`) uses a **hybrid mesh + gossip** approach:

1. **Mesh layer**: Each peer maintains a small, stable set of peers (the "mesh") for each topic. Messages are forwarded **only** through the mesh, keeping bandwidth bounded.

2. **Gossip layer**: Peers periodically share **metadata** (message IDs they've seen) with non-mesh peers. This ensures messages eventually reach all subscribers even if the mesh is imperfect.

This design achieves:

- **Bounded bandwidth**: Each peer forwards to at most `D_max` mesh peers, not all peers
- **Reliability**: The gossip layer catches any messages missed by the mesh
- **Scalability**: Performance stays stable as the network grows

### Mesh vs Gossip Peers

| | Mesh Peers | Gossip Peers |
|---|---|---|
| **What they receive** | Full messages | Only message IDs (metadata) |
| **Count per topic** | `D_min` to `D_max` | Remaining connected peers |
| **Purpose** | Primary message delivery | Redundancy and discovery |
| **Selection** | Maintained by heartbeat | All other topic subscribers |

### Gossipsub Parameters Explained

| Parameter | Description | Our Setting |
|-----------|-------------|-------------|
| `D` | Target number of mesh peers per topic | (auto, between D_min and D_max) |
| `D_min` | Minimum mesh peers before grafting more | 2 |
| `D_max` | Maximum mesh peers before pruning | 4 |
| `heartbeat_interval` | How often to maintain mesh health | 1000ms |
| `sign_messages` | Cryptographically sign each message | true |

### How Gossipsub Handles Misbehaving Peers

Gossipsub includes built-in defenses against Byzantine (malicious) peers:

- **Message signing**: Each message is signed with the sender's private key, preventing impersonation
- **Message deduplication**: Messages are tracked by ID, so duplicates are dropped
- **Mesh maintenance**: The heartbeat periodically checks mesh health and replaces unresponsive peers
- **GRAFT/PRUNE protocol**: Peers can request to join or leave another peer's mesh in a controlled way

## Your Task

Building on your Identify implementation from Lesson 5, you need to:

1. **Configure Gossipsub**: Set mesh parameters and create the protocol
2. **Subscribe to Topics**: Register handlers for chat and discovery topics
3. **Publish Messages**: Send periodic heartbeat messages
4. **Bootstrap**: Add known peers to the gossip network

## Step-by-Step Instructions

### Step 1: Add Gossipsub Includes

Add the Gossipsub header and additional dependencies it requires:

```cpp
#include <libp2p/protocol/gossip/gossip.hpp>
#include <libp2p/crypto/key_marshaller/key_marshaller_impl.hpp>
#include <libp2p/crypto/crypto_provider/crypto_provider_impl.hpp>
#include <libp2p/network/connection_manager.hpp>
#include <libp2p/peer/identity_manager.hpp>
```

Gossipsub needs the crypto provider and key marshaller for message signing, and the identity manager for peer identification.

### Step 2: Extract Additional Dependencies from the Injector

Gossipsub requires several components beyond what we've used so far:

```cpp
auto identity_manager = injector.create<std::shared_ptr<libp2p::peer::IdentityManager>>();
auto key_marshaller = injector.create<std::shared_ptr<libp2p::crypto::marshaller::KeyMarshaller>>();
auto crypto_provider = injector.create<std::shared_ptr<libp2p::crypto::CryptoProvider>>();
```

**Why these are needed:**

- **IdentityManager**: Provides our peer's identity for message signing
- **KeyMarshaller**: Serializes/deserializes cryptographic keys
- **CryptoProvider**: Performs the actual cryptographic operations (signing, verification)

### Step 3: Configure Gossipsub Parameters

Configure the mesh parameters that control how Gossipsub manages peer connections:

```cpp
// Configure Gossipsub
libp2p::protocol::gossip::Config gossip_config;
gossip_config.D_min = 2;        // Minimum mesh peers per topic
gossip_config.D_max = 4;        // Maximum mesh peers per topic
gossip_config.heartbeat_interval_msec = std::chrono::milliseconds(1000);
gossip_config.protocol_version = "/meshsub/1.0.0";
gossip_config.sign_messages = true;
```

**What each parameter means:**

- **D_min = 2**: If we have fewer than 2 mesh peers for a topic, the heartbeat will GRAFT (add) new peers
- **D_max = 4**: If we have more than 4 mesh peers, the heartbeat will PRUNE (remove) excess peers
- **heartbeat_interval = 1000ms**: Every second, check mesh health and perform maintenance
- **sign_messages = true**: Sign every message with our Ed25519 key to prevent spoofing

### Step 4: Create the Gossipsub Instance

```cpp
auto gossip = libp2p::protocol::gossip::create(
    scheduler, host, identity_manager, crypto_provider, key_marshaller, gossip_config);
```

The `create()` factory function wires together all the dependencies. The scheduler handles the periodic heartbeat, and the crypto components handle message signing.

### Step 5: Define Topics and Subscribe

Subscribe to the two topics used in Universal Connectivity:

```cpp
const std::string CHAT_TOPIC = "universal-connectivity";
const std::string DISCOVERY_TOPIC = "universal-connectivity-browser-peer-discovery";

// Subscribe to chat topic
auto chat_sub = gossip->subscribe(
    {CHAT_TOPIC},
    [peer_id_str](libp2p::protocol::gossip::Gossip::SubscriptionData data) {
        if (data) {
            std::string msg(data->data.begin(), data->data.end());
            std::cout << "Chat message on topic '" << data->topic << "': " << msg << std::endl;
        }
    });

// Subscribe to discovery topic
auto discovery_sub = gossip->subscribe(
    {DISCOVERY_TOPIC},
    [](libp2p::protocol::gossip::Gossip::SubscriptionData data) {
        if (data) {
            std::string msg(data->data.begin(), data->data.end());
            std::cout << "Discovery message: " << msg << std::endl;
        }
    });
```

**What's happening here:**

- `subscribe()` registers a callback for each message received on the topic
- The `SubscriptionData` contains the raw message bytes and the topic name
- We subscribe to **two** topics: one for chat messages and one for peer discovery
- The returned subscription object must be kept alive (stored in a variable) for the duration of the program

### Step 6: Start Gossipsub and Add Bootstrap Peers

```cpp
// Start the gossipsub protocol
gossip->start();

// Add bootstrap peers so gossipsub can build its mesh
for (const auto& addr : remote_addrs) {
    auto peer_id_opt = addr.getPeerId();
    if (!peer_id_opt) continue;

    auto remote_peer_id = libp2p::peer::PeerId::fromBase58(peer_id_opt.value()).value();
    gossip->addBootstrapPeer(remote_peer_id, addr);
}
```

Bootstrap peers are the initial nodes that Gossipsub connects to for building its mesh. Without bootstrap peers, a node cannot discover the existing topic mesh.

### Step 7: Publish Messages Periodically

Create a timer to publish heartbeat messages, demonstrating the publish side of pub/sub:

```cpp
// Helper: create a JSON chat message
std::string createChatMessage(const std::string& sender_id, const std::string& message) {
    auto now = std::chrono::system_clock::now();
    auto timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()).count();

    std::ostringstream json;
    json << "{\"sender\":\"" << sender_id << "\","
         << "\"message\":\"" << message << "\","
         << "\"timestamp\":" << timestamp << "}";
    return json.str();
}

// Periodic heartbeat publisher (every 10 seconds)
auto publish_timer = std::make_shared<boost::asio::steady_timer>(*io_context);
std::function<void(const boost::system::error_code&)> publish_handler;
publish_handler = [&, publish_timer, peer_id_str](const boost::system::error_code& ec) {
    if (ec) return;

    std::string msg = createChatMessage(peer_id_str, "heartbeat");
    libp2p::Bytes data(msg.begin(), msg.end());
    if (gossip->publish(CHAT_TOPIC, data)) {
        std::cout << "Published heartbeat to " << CHAT_TOPIC << std::endl;
    }

    publish_timer->expires_after(std::chrono::seconds(10));
    publish_timer->async_wait(publish_handler);
};

publish_timer->expires_after(std::chrono::seconds(5));
publish_timer->async_wait(publish_handler);
```

**What's happening here:**

- We create a JSON-formatted message with our peer ID, a message body, and a timestamp
- `gossip->publish()` sends the message to all mesh peers for the topic
- Mesh peers forward the message to their own mesh peers, propagating it through the network
- The timer fires every 10 seconds (with an initial 5-second delay)

## Complete Implementation

Here's the complete `app/main.cpp` for this lesson:

```cpp
/**
 * Lesson 6: Gossipsub Checkpoint
 * Implements the Gossipsub protocol for publish-subscribe messaging.
 */

#include <iostream>
#include <memory>
#include <string>
#include <vector>
#include <cstdlib>
#include <sstream>
#include <chrono>
#include <ctime>

#include <boost/asio/io_context.hpp>
#include <boost/asio/post.hpp>
#include <boost/asio/signal_set.hpp>
#include <boost/asio/steady_timer.hpp>

#include <libp2p/host/host.hpp>
#include <libp2p/injector/host_injector.hpp>
#include <libp2p/log/configurator.hpp>
#include <libp2p/log/logger.hpp>
#include <libp2p/multi/multiaddress.hpp>
#include <libp2p/peer/peer_info.hpp>
#include <libp2p/protocol/ping.hpp>
#include <libp2p/protocol/identify/identify.hpp>
#include <libp2p/protocol/identify/identify_msg_processor.hpp>
#include <libp2p/protocol/gossip/gossip.hpp>
#include <libp2p/event/bus.hpp>
#include <libp2p/basic/scheduler/scheduler_impl.hpp>
#include <libp2p/basic/scheduler/asio_scheduler_backend.hpp>
#include <libp2p/crypto/random_generator/boost_generator.hpp>
#include <libp2p/crypto/key_marshaller/key_marshaller_impl.hpp>
#include <libp2p/crypto/crypto_provider/crypto_provider_impl.hpp>
#include <libp2p/network/connection_manager.hpp>
#include <libp2p/peer/identity_manager.hpp>

namespace {
  const std::string logger_config(R"(
sinks:
  - name: console
    type: console
    color: true
groups:
  - name: main
    sink: console
    level: info
    children:
      - name: libp2p
  )");

  // Topics for Universal Connectivity
  const std::string CHAT_TOPIC = "universal-connectivity";
  const std::string DISCOVERY_TOPIC = "universal-connectivity-browser-peer-discovery";

  std::vector<std::string> split(const std::string& str, char delimiter) {
    std::vector<std::string> tokens;
    std::istringstream stream(str);
    std::string token;
    while (std::getline(stream, token, delimiter)) {
      size_t start = token.find_first_not_of(" \t\n\r");
      size_t end = token.find_last_not_of(" \t\n\r");
      if (start != std::string::npos && end != std::string::npos) {
        tokens.push_back(token.substr(start, end - start + 1));
      }
    }
    return tokens;
  }

  std::string getEnv(const std::string& name, const std::string& defaultValue = "") {
    const char* value = std::getenv(name.c_str());
    return value ? std::string(value) : defaultValue;
  }

  std::string getTransportType(const libp2p::multi::Multiaddress& addr) {
    std::string addr_str(addr.getStringAddress());
    if (addr_str.find("/quic") != std::string::npos) {
      return "QUIC";
    } else if (addr_str.find("/tcp/") != std::string::npos) {
      return "TCP";
    }
    return "Unknown";
  }

  std::string createChatMessage(const std::string& sender_id, const std::string& message) {
    auto now = std::chrono::system_clock::now();
    auto timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()).count();

    std::ostringstream json;
    json << "{\"sender\":\"" << sender_id << "\","
         << "\"message\":\"" << message << "\","
         << "\"timestamp\":" << timestamp << "}";
    return json.str();
  }
}  // namespace

int main(int argc, char** argv) {
    std::cout << "Starting Universal Connectivity Application..." << std::endl;

    // Initialize logging
    auto logging_system = std::make_shared<soralog::LoggingSystem>(
        std::make_shared<soralog::ConfiguratorFromYAML>(
            std::make_shared<libp2p::log::Configurator>(),
            logger_config));
    auto r = logging_system->configure();
    if (r.has_error) {
        std::cerr << r.message << std::endl;
        return EXIT_FAILURE;
    }
    libp2p::log::setLoggingSystem(logging_system);
    libp2p::log::setLevelOfGroup("main", soralog::Level::INFO);
    auto log = libp2p::log::createLogger("Lesson6");

    // Parse remote peer addresses
    std::vector<libp2p::multi::Multiaddress> remote_addrs;
    std::string remote_peers_env = getEnv("REMOTE_PEERS", "");
    if (!remote_peers_env.empty()) {
        for (const auto& addr_str : split(remote_peers_env, ',')) {
            auto addr_result = libp2p::multi::Multiaddress::create(addr_str);
            if (addr_result.has_value()) {
                remote_addrs.push_back(addr_result.value());
                log->info("Parsed remote address: {} ({})", addr_str,
                         getTransportType(addr_result.value()));
            }
        }
    }

    // Get listening ports
    std::string tcp_port = getEnv("LISTEN_PORT", "9000");
    std::string quic_port = getEnv("QUIC_PORT", "9001");
    std::string tcp_addr_str = "/ip4/0.0.0.0/tcp/" + tcp_port;
    std::string quic_addr_str = "/ip4/0.0.0.0/udp/" + quic_port + "/quic-v1";

    // Create host using dependency injection
    auto injector = libp2p::injector::makeHostInjector();
    auto host = injector.create<std::shared_ptr<libp2p::Host>>();
    auto io_context = injector.create<std::shared_ptr<boost::asio::io_context>>();
    auto bus = injector.create<std::shared_ptr<libp2p::event::Bus>>();
    auto conn_manager = injector.create<std::shared_ptr<libp2p::network::ConnectionManager>>();
    auto identity_manager = injector.create<std::shared_ptr<libp2p::peer::IdentityManager>>();
    auto key_marshaller = injector.create<std::shared_ptr<libp2p::crypto::marshaller::KeyMarshaller>>();
    auto crypto_provider = injector.create<std::shared_ptr<libp2p::crypto::CryptoProvider>>();

    // Create scheduler
    auto scheduler_backend = std::make_shared<libp2p::basic::AsioSchedulerBackend>(io_context);
    auto scheduler = std::make_shared<libp2p::basic::SchedulerImpl>(
        scheduler_backend,
        libp2p::basic::Scheduler::Config{});

    // Create random generator
    auto random_gen = std::make_shared<libp2p::crypto::random::BoostRandomGenerator>();

    // Configure ping
    libp2p::protocol::PingConfig ping_config;
    ping_config.interval = std::chrono::seconds(1);
    ping_config.timeout = std::chrono::seconds(5);
    ping_config.message_size = 32;
    auto ping = std::make_shared<libp2p::protocol::Ping>(
        *host, *bus, scheduler, random_gen, ping_config);

    // Create Identify
    auto identify_msg_processor = std::make_shared<libp2p::protocol::IdentifyMessageProcessor>(
        *host, *conn_manager, *identity_manager, key_marshaller);
    libp2p::protocol::IdentifyConfig identify_config;
    auto identify = std::make_shared<libp2p::protocol::Identify>(
        identify_config, *host, identify_msg_processor, *bus);

    // Configure Gossipsub
    libp2p::protocol::gossip::Config gossip_config;
    gossip_config.D_min = 2;
    gossip_config.D_max = 4;
    gossip_config.heartbeat_interval_msec = std::chrono::milliseconds(1000);
    gossip_config.protocol_version = "/meshsub/1.0.0";
    gossip_config.sign_messages = true;

    // Create Gossipsub
    auto gossip = libp2p::protocol::gossip::create(
        scheduler, host, identity_manager, crypto_provider, key_marshaller, gossip_config);

    auto peer_id = host->getId();
    std::string peer_id_str = peer_id.toBase58();
    std::cout << "Local peer id: " << peer_id_str << std::endl;
    std::cout << "Agent version: universal-connectivity/0.1.0" << std::endl;

    // Signal handling
    boost::asio::signal_set signals(*io_context, SIGINT, SIGTERM);
    signals.async_wait([&](const boost::system::error_code&, int) {
        std::cout << "Shutting down..." << std::endl;
        gossip->stop();
        io_context->stop();
    });

    // Subscribe to gossip topics
    libp2p::protocol::Subscription chat_sub;
    libp2p::protocol::Subscription discovery_sub;

    // Start host and protocols
    boost::asio::post(*io_context, [&] {
        // Listen on TCP
        auto tcp_addr = libp2p::multi::Multiaddress::create(tcp_addr_str).value();
        auto tcp_result = host->listen(tcp_addr);
        if (!tcp_result) {
            log->error("Failed to listen on TCP: {}", tcp_result.error().message());
            io_context->stop();
            return;
        }
        std::cout << "Listening on TCP: " << tcp_addr.getStringAddress() << std::endl;

        // Listen on QUIC
        auto quic_addr = libp2p::multi::Multiaddress::create(quic_addr_str).value();
        auto quic_result = host->listen(quic_addr);
        if (!quic_result) {
            log->warn("Failed to listen on QUIC: {}", quic_result.error().message());
        } else {
            std::cout << "Listening on QUIC: " << quic_addr.getStringAddress() << std::endl;
        }

        // Set up protocol handlers
        host->setProtocolHandler(
            {ping->getProtocolId()},
            [ping](libp2p::StreamAndProtocol stream) {
                ping->handle(std::move(stream));
            });

        host->setProtocolHandler(
            {identify->getProtocolId()},
            [identify](libp2p::StreamAndProtocol stream) {
                identify->handle(std::move(stream));
            });

        identify->start();

        // Subscribe to chat topic
        chat_sub = gossip->subscribe(
            {CHAT_TOPIC},
            [peer_id_str](libp2p::protocol::gossip::Gossip::SubscriptionData data) {
                if (data) {
                    std::string msg(data->data.begin(), data->data.end());
                    std::cout << "Chat message on topic '" << data->topic << "': " << msg << std::endl;
                }
            });

        // Subscribe to discovery topic
        discovery_sub = gossip->subscribe(
            {DISCOVERY_TOPIC},
            [](libp2p::protocol::gossip::Gossip::SubscriptionData data) {
                if (data) {
                    std::string msg(data->data.begin(), data->data.end());
                    std::cout << "Discovery message: " << msg << std::endl;
                }
            });

        // Start gossipsub
        gossip->start();

        std::cout << "Protocols:" << std::endl;
        std::cout << "  - Ping: " << ping->getProtocolId() << std::endl;
        std::cout << "  - Identify: /ipfs/id/1.0.0" << std::endl;
        std::cout << "  - Gossipsub: /meshsub/1.0.0" << std::endl;
        std::cout << "Topics:" << std::endl;
        std::cout << "  - " << CHAT_TOPIC << std::endl;
        std::cout << "  - " << DISCOVERY_TOPIC << std::endl;
        std::cout << "Transports: TCP + QUIC" << std::endl;

        // Add bootstrap peers and connect
        for (const auto& addr : remote_addrs) {
            auto peer_id_opt = addr.getPeerId();
            if (!peer_id_opt) {
                std::cout << "Invalid address (missing peer ID): " << addr.getStringAddress() << std::endl;
                continue;
            }

            auto remote_peer_id = libp2p::peer::PeerId::fromBase58(peer_id_opt.value()).value();

            gossip->addBootstrapPeer(remote_peer_id, addr);

            libp2p::peer::PeerInfo peer_info{remote_peer_id, {addr}};
            std::string transport = getTransportType(addr);

            std::cout << "Connecting via " << transport << " to: " << addr.getStringAddress() << std::endl;

            host->connect(
                peer_info,
                [&, addr, remote_peer_id, ping, log, transport](auto&& conn_result) {
                    if (!conn_result.has_value()) {
                        std::cout << "Failed to connect: " << conn_result.error().message() << std::endl;
                        return;
                    }
                    std::cout << "Connected via " << transport << " to: "
                              << remote_peer_id.toBase58() << std::endl;

                    auto conn = conn_result.value();
                    ping->startPinging(conn, [remote_peer_id](auto&&) {});
                });
        }

        std::cout << "Waiting for connections and messages..." << std::endl;
    });

    // Periodic message publishing (every 10 seconds)
    auto publish_timer = std::make_shared<boost::asio::steady_timer>(*io_context);
    std::function<void(const boost::system::error_code&)> publish_handler;
    publish_handler = [&, publish_timer, peer_id_str](const boost::system::error_code& ec) {
        if (ec) return;

        std::string msg = createChatMessage(peer_id_str, "heartbeat");
        libp2p::Bytes data(msg.begin(), msg.end());
        if (gossip->publish(CHAT_TOPIC, data)) {
            std::cout << "Published heartbeat to " << CHAT_TOPIC << std::endl;
        }

        publish_timer->expires_after(std::chrono::seconds(10));
        publish_timer->async_wait(publish_handler);
    };

    publish_timer->expires_after(std::chrono::seconds(5));
    publish_timer->async_wait(publish_handler);

    // Subscribe to identify events
    auto identify_connection = identify->onIdentifyReceived(
        [](const libp2p::peer::PeerId& peer_id) {
            std::cout << "Identify received from: " << peer_id.toBase58() << std::endl;
        });

    // Subscribe to ping events
    auto& ping_channel = bus->getChannel<libp2p::event::protocol::PeerIsDeadChannel>();
    auto ping_sub = ping_channel.subscribe([](const libp2p::peer::PeerId& peer) {
        std::cout << "Ping timeout - peer is dead: " << peer.toBase58() << std::endl;
    });

    // Run the event loop
    try {
        io_context->run();
    } catch (const std::exception& e) {
        log->error("Error: {}", e.what());
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
```

## Testing Your Implementation

### Build and Run with Docker:

```bash
# Navigate to lesson directory
cd en/cpp/06-gossipsub-checkpoint

# Build and run
docker compose up --build

# Check results in another terminal
python3 check.py
```

### Testing with Two Peers:

To test pub/sub messaging, run two instances:

```bash
# Terminal 1: First peer
docker compose up --build

# Terminal 2: Second peer connected to first
LISTEN_PORT=9002 QUIC_PORT=9003 \
REMOTE_PEERS="/ip4/127.0.0.1/tcp/9000/p2p/12D3KooW..." docker compose up --build
```

### Expected Output:

```
Starting Universal Connectivity Application...
Local peer id: 12D3KooWxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Agent version: universal-connectivity/0.1.0
Listening on TCP: /ip4/0.0.0.0/tcp/9000
Listening on QUIC: /ip4/0.0.0.0/udp/9001/quic-v1
Protocols:
  - Ping: /ipfs/ping/1.0.0
  - Identify: /ipfs/id/1.0.0
  - Gossipsub: /meshsub/1.0.0
Topics:
  - universal-connectivity
  - universal-connectivity-browser-peer-discovery
Transports: TCP + QUIC
Waiting for connections and messages...
Published heartbeat to universal-connectivity
```

## Key Concepts Summary

| Concept | cpp-libp2p Implementation |
|---------|---------------------------|
| Create Gossipsub | `gossip::create(scheduler, host, identity_manager, crypto_provider, key_marshaller, config)` |
| Subscribe | `gossip->subscribe({topic}, callback)` |
| Publish | `gossip->publish(topic, bytes)` |
| Bootstrap | `gossip->addBootstrapPeer(peer_id, addr)` |
| Mesh control | `D_min` / `D_max` in config |
| Message signing | `config.sign_messages = true` |

## Troubleshooting

**Common Issues:**

1. **"Group 'Gossip' not found" warning**: This is harmless — soralog doesn't have a pre-configured group for Gossipsub, so it falls back to the default
2. **Messages not received**: Ensure both peers are subscribed to the same topic before publishing
3. **Gossipsub not starting**: Call `gossip->start()` after subscribing to topics
4. **Bootstrap peer not connecting**: Verify the multiaddress includes the `/p2p/<peer_id>` suffix

## What's Next?

In Lesson 7, you'll add **Kademlia DHT** — a distributed hash table for decentralized peer discovery. Combined with Gossipsub, this enables fully decentralized communication where peers can discover each other without a central server.
