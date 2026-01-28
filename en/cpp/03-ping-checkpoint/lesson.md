# Lesson 3: Ping Checkpoint

Welcome to your first checkpoint! In this lesson, you'll implement the ping protocol using `cpp-libp2p` to establish bidirectional connectivity with a remote peer and measure round-trip times. This lesson builds on basic libp2p concepts and introduces protocol handling and event-driven networking.

## Learning Objectives

By the end of this lesson, you will:
- Understand the purpose and mechanics of the ping protocol in libp2p.
- Implement a working ping protocol using `cpp-libp2p`.
- Handle ping requests and responses to measure network performance.
- Successfully connect to remote peers and validate your solution.

## Background: The Ping Protocol

The ping protocol in libp2p serves several purposes:
- **Connectivity Testing**: Verifies bidirectional communication between peers.
- **Latency Measurement**: Measures round-trip time (RTT) to assess network performance.
- **Keep-Alive**: Sends periodic messages to maintain active connections.
- **Network Quality**: Provides insights into connection stability and reliability.

The libp2p ping protocol (`/ipfs/ping/1.0.0`) exchanges 32-byte payloads between peers, with the receiver echoing the data back to measure round-trip time.

## Your Task

Building on your TCP transport implementation from Lesson 2, you need to:

1. **Configure Ping Settings**: Set up ping with a 1-second interval and 5-second timeout
2. **Handle Ping Events**: Set up ping protocol handlers and process ping responses
3. **Monitor Peer Health**: Subscribe to peer dead events for connection monitoring

## Step-by-Step Instructions

### Step 1: Add Ping Protocol Includes

Include the necessary headers for the ping protocol, event bus, scheduler, and random generator:

```cpp
#include <libp2p/protocol/ping.hpp>
#include <libp2p/event/bus.hpp>
#include <libp2p/basic/scheduler/scheduler_impl.hpp>
#include <libp2p/crypto/random_generator/boost_generator.hpp>
```

### Step 2: Create Event Bus and Scheduler

The ping protocol requires an event bus for communication and a scheduler for timing:

```cpp
// Create host using dependency injection
auto injector = libp2p::injector::makeHostInjector();
auto host = injector.create<std::shared_ptr<libp2p::Host>>();
auto io_context = injector.create<std::shared_ptr<boost::asio::io_context>>();
auto bus = injector.create<std::shared_ptr<libp2p::event::Bus>>();

// Create scheduler for ping protocol timing
auto scheduler = std::make_shared<libp2p::basic::SchedulerImpl>(
    io_context,
    libp2p::basic::Scheduler::Config{});

// Create random generator for ping payload
auto random_gen = std::make_shared<libp2p::crypto::random::BoostRandomGenerator>();
```

### Step 3: Configure Ping Settings

Configure the ping protocol with appropriate interval, timeout, and message size:

```cpp
// Configure ping with 1-second interval and 5-second timeout
libp2p::protocol::PingConfig ping_config;
ping_config.interval = std::chrono::seconds(1);
ping_config.timeout = std::chrono::seconds(5);
ping_config.message_size = 32;
```

The configuration parameters:
- **interval**: How often to send ping messages (1 second)
- **timeout**: How long to wait for a response before considering peer dead (5 seconds)
- **message_size**: Size of the ping payload in bytes (32 bytes, standard)

### Step 4: Create Ping Protocol Instance

Create the ping protocol instance with all required dependencies:

```cpp
// Create ping protocol
auto ping = std::make_shared<libp2p::protocol::Ping>(
    *host, *bus, scheduler, random_gen, ping_config);
```

### Step 5: Set Up Ping Protocol Handler

Register a protocol handler so incoming connections can use ping:

```cpp
// Set up ping protocol handler for incoming connections
host->setProtocolHandler(
    ping->getProtocolId(),
    [ping](libp2p::protocol::BaseProtocol::StreamAndProtocol stream) {
        ping->handle(std::move(stream));
    });

std::cout << "Ping protocol: " << ping->getProtocolId() << std::endl;
```

### Step 6: Start Pinging After Connection and Measure RTT

When connecting to a remote peer, start the ping session and measure the round-trip time (RTT). The RTT tells us how long it takes for a ping message to travel to the peer and back:

```cpp
host->connect(
    peer_info,
    [&, addr, remote_peer_id, ping, log](auto&& conn_result) {
        if (!conn_result.has_value()) {
            std::cout << "Failed to connect: " << conn_result.error().message() << std::endl;
            return;
        }

        std::cout << "Connected to: " << remote_peer_id.toBase58() << std::endl;

        // Start pinging and measure RTT
        // Record the start time before initiating the ping session
        auto ping_start = std::make_shared<std::chrono::steady_clock::time_point>(
            std::chrono::steady_clock::now());

        auto conn = conn_result.value();
        ping->startPinging(
            conn,
            [remote_peer_id, log, ping_start](auto&& ping_result) {
                if (ping_result.has_value()) {
                    // Calculate round-trip time
                    auto elapsed = std::chrono::steady_clock::now() - *ping_start;
                    auto rtt_us = std::chrono::duration_cast<
                        std::chrono::microseconds>(elapsed).count();
                    double rtt_ms = rtt_us / 1000.0;

                    std::cout << "Ping RTT to " << remote_peer_id.toBase58()
                              << ": " << rtt_ms << "ms" << std::endl;
                } else {
                    std::cout << "Failed to start ping: "
                              << ping_result.error().message() << std::endl;
                }
            });
    });
```

**What's happening here?**

- `std::chrono::steady_clock` provides a monotonic clock ideal for measuring elapsed time
- We record the time before `startPinging`, which initiates the ping stream and first data exchange
- The callback fires after the stream is opened and the first ping round-trip completes
- We compute the difference in microseconds and convert to milliseconds for display
- This gives us the **round-trip time (RTT)** — the time for a message to travel to the peer and back

### Step 7: Subscribe to Peer Dead Events

Monitor for ping timeouts by subscribing to the PeerIsDeadChannel:

```cpp
// Subscribe to ping events
auto ping_channel = bus->getChannel<libp2p::event::protocol::PeerIsDeadChannel>();
auto ping_sub = ping_channel.subscribe([](const libp2p::peer::PeerId& peer) {
    std::cout << "Ping timeout - peer is dead: " << peer.toBase58() << std::endl;
});
```

## Complete Implementation

Here's the complete `main.cpp` with ping protocol:

```cpp
/**
 * Lesson 3: Ping Checkpoint
 * Implements the ping protocol to measure connectivity and round-trip times.
 */

#include <iostream>
#include <memory>
#include <string>
#include <vector>
#include <cstdlib>
#include <sstream>
#include <chrono>

#include <boost/asio/io_context.hpp>
#include <boost/asio/post.hpp>
#include <boost/asio/signal_set.hpp>

#include <libp2p/host/host.hpp>
#include <libp2p/injector/host_injector.hpp>
#include <libp2p/log/configurator.hpp>
#include <libp2p/log/logger.hpp>
#include <libp2p/multi/multiaddress.hpp>
#include <libp2p/peer/peer_info.hpp>
#include <libp2p/protocol/ping.hpp>
#include <libp2p/event/bus.hpp>
#include <libp2p/basic/scheduler/scheduler_impl.hpp>
#include <libp2p/crypto/random_generator/boost_generator.hpp>

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
    auto log = libp2p::log::createLogger("Lesson3");

    // Parse remote peer addresses
    std::vector<libp2p::multi::Multiaddress> remote_addrs;
    std::string remote_peers_env = getEnv("REMOTE_PEERS", "");
    if (!remote_peers_env.empty()) {
        for (const auto& addr_str : split(remote_peers_env, ',')) {
            auto addr_result = libp2p::multi::Multiaddress::create(addr_str);
            if (addr_result.has_value()) {
                remote_addrs.push_back(addr_result.value());
                log->info("Parsed remote address: {}", addr_str);
            }
        }
    }

    // Get listening port
    std::string listen_port = getEnv("LISTEN_PORT", "9000");
    std::string listen_addr_str = "/ip4/0.0.0.0/tcp/" + listen_port;

    // Create host using dependency injection
    auto injector = libp2p::injector::makeHostInjector();
    auto host = injector.create<std::shared_ptr<libp2p::Host>>();
    auto io_context = injector.create<std::shared_ptr<boost::asio::io_context>>();
    auto bus = injector.create<std::shared_ptr<libp2p::event::Bus>>();

    // Create scheduler for ping protocol
    auto scheduler = std::make_shared<libp2p::basic::SchedulerImpl>(
        io_context,
        libp2p::basic::Scheduler::Config{});

    // Create random generator for ping
    auto random_gen = std::make_shared<libp2p::crypto::random::BoostRandomGenerator>();

    // Configure ping with 1-second interval and 5-second timeout
    libp2p::protocol::PingConfig ping_config;
    ping_config.interval = std::chrono::seconds(1);
    ping_config.timeout = std::chrono::seconds(5);
    ping_config.message_size = 32;

    // Create ping protocol
    auto ping = std::make_shared<libp2p::protocol::Ping>(
        *host, *bus, scheduler, random_gen, ping_config);

    auto peer_id = host->getId();
    std::cout << "Local peer id: " << peer_id.toBase58() << std::endl;

    // Signal handling
    boost::asio::signal_set signals(*io_context, SIGINT, SIGTERM);
    signals.async_wait([&](const boost::system::error_code&, int) {
        std::cout << "Shutting down..." << std::endl;
        io_context->stop();
    });

    // Start host and set up ping
    boost::asio::post(*io_context, [&] {
        // Parse and listen on address
        auto listen_addr = libp2p::multi::Multiaddress::create(listen_addr_str).value();
        auto listen_result = host->listen(listen_addr);
        if (!listen_result) {
            log->error("Failed to listen: {}", listen_result.error().message());
            io_context->stop();
            return;
        }

        std::cout << "Listening on: " << listen_addr.getStringAddress() << std::endl;

        // Set up ping protocol handler for incoming connections
        host->setProtocolHandler(
            ping->getProtocolId(),
            [ping](libp2p::protocol::BaseProtocol::StreamAndProtocol stream) {
                ping->handle(std::move(stream));
            });

        std::cout << "Ping protocol: " << ping->getProtocolId() << std::endl;

        // Connect to remote peers and start pinging
        for (const auto& addr : remote_addrs) {
            auto peer_id_str = addr.getPeerId();
            if (!peer_id_str) {
                std::cout << "Invalid address (missing peer ID): " << addr.getStringAddress() << std::endl;
                continue;
            }

            auto remote_peer_id = libp2p::peer::PeerId::fromBase58(peer_id_str.value()).value();
            libp2p::peer::PeerInfo peer_info{remote_peer_id, {addr}};

            std::cout << "Connecting to: " << addr.getStringAddress() << std::endl;

            host->connect(
                peer_info,
                [&, addr, remote_peer_id, ping, log](auto&& conn_result) {
                    if (!conn_result.has_value()) {
                        std::cout << "Failed to connect: " << conn_result.error().message() << std::endl;
                        return;
                    }

                    std::cout << "Connected to: " << remote_peer_id.toBase58() << std::endl;

                    // Start pinging and measure RTT
                    auto ping_start = std::make_shared<std::chrono::steady_clock::time_point>(
                        std::chrono::steady_clock::now());

                    auto conn = conn_result.value();
                    ping->startPinging(
                        conn,
                        [remote_peer_id, log, ping_start](auto&& ping_result) {
                            if (ping_result.has_value()) {
                                auto elapsed = std::chrono::steady_clock::now() - *ping_start;
                                auto rtt_us = std::chrono::duration_cast<
                                    std::chrono::microseconds>(elapsed).count();
                                double rtt_ms = rtt_us / 1000.0;

                                std::cout << "Ping RTT to " << remote_peer_id.toBase58()
                                          << ": " << rtt_ms << "ms" << std::endl;
                            } else {
                                std::cout << "Failed to start ping: "
                                          << ping_result.error().message() << std::endl;
                            }
                        });
                });
        }

        std::cout << "Waiting for connections and pings..." << std::endl;
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
cd en/cpp/03-ping-checkpoint

# Build and run
docker compose up --build

# Check results in another terminal
python3 check.py
```

### Expected Output:

```
Starting Universal Connectivity Application...
Local peer id: 12D3KooW...
Listening on: /ip4/0.0.0.0/tcp/9000
Ping protocol: /ipfs/ping/1.0.0
Connecting to: /ip4/127.0.0.1/tcp/9000/p2p/12D3KooW...
Connected to: 12D3KooW...
Ping RTT to 12D3KooW...: 2.45ms
Waiting for connections and pings...
```

The **Ping RTT** value shows the round-trip time in milliseconds. Lower values indicate better connectivity. Typical values:
- **Local (same machine)**: < 1ms
- **Same network (LAN)**: 1-5ms
- **Internet**: 10-200ms+

## Success Criteria

Your implementation should:
- Display the startup message and local peer ID
- Successfully listen on the configured port
- Register the ping protocol handler (`/ipfs/ping/1.0.0`)
- Handle incoming ping requests automatically
- **Measure and display round-trip time (RTT)** when pinging peers
- Start pinging connected peers with configured interval
- Monitor peer health through event subscriptions

## Key Concepts

### PingConfig Structure

```cpp
struct PingConfig {
    std::chrono::milliseconds interval;   // Time between pings
    std::chrono::milliseconds timeout;    // Max wait for response
    size_t message_size;                  // Ping payload size (default: 32)
};
```

### Ping Protocol Flow

1. **Server Mode**: Receives ping, echoes payload back
2. **Client Mode**: Sends ping, waits for echo, measures RTT
3. **Health Monitoring**: Triggers PeerIsDeadChannel if timeout occurs

### Event Bus

The event bus enables decoupled communication between components:
- Subscribe to channels for specific events
- PeerIsDeadChannel notifies when a peer stops responding

## Troubleshooting

**Common Issues:**

1. **Build Errors with Ping Include**: Ensure you're including `<libp2p/protocol/ping.hpp>`
2. **Scheduler Creation Fails**: Make sure io_context is valid before creating scheduler
3. **No Ping Messages**: Verify protocol handler is set before connections
4. **Subscription Not Working**: Keep ping_sub variable alive for duration of program

**Debug Tips:**
- Check if ping protocol ID is `/ipfs/ping/1.0.0`
- Verify the event bus is properly injected
- Ensure scheduler is running (io_context must be active)

## What's Next?

Congratulations! You've successfully implemented the libp2p ping protocol.

You've learned:
- **Protocol Implementation**: How to configure and use built-in protocols
- **Event System**: Subscribing to protocol events for health monitoring
- **Dependency Injection**: Using cpp-libp2p's injector for component creation
- **Async Patterns**: Callbacks and event-driven programming with Boost.Asio

In Lesson 4, you'll add QUIC transport for modern, multiplexed connections!
