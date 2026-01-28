# Lesson 2: Transport Layer - TCP Connection

Building on your basic cpp-libp2p node, in this lesson you'll learn about transport layers and establish your first peer-to-peer connections using TCP with Noise security and Yamux multiplexing.

## Learning Objectives

By the end of this lesson, you will:
- Understand cpp-libp2p's transport abstraction
- Configure TCP transport with security and multiplexing
- Parse multiaddresses from environment variables
- Listen for incoming connections
- Dial remote peers and handle connection events

## Background: Transport Layers in libp2p

In libp2p, **transports** handle the low-level network communication. A transport defines how data travels between peers. cpp-libp2p supports multiple transports:

- **TCP**: Reliable, ordered, connection-oriented (like HTTP)
- **QUIC**: Modern UDP-based with built-in encryption
- **WebRTC**: For browser connectivity

Each transport can be enhanced with:
- **Security protocols**: Encrypt communication (e.g., Noise)
- **Multiplexers**: Share one connection for multiple streams (e.g., Yamux)

## Transport Stack

The cpp-libp2p stack looks like this when using TCP, Noise, and Yamux:

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

The good news: `makeHostInjector()` automatically configures all of this for you!

## Your Task

Extend your application to:
1. Parse remote peer addresses from the `REMOTE_PEERS` environment variable
2. Listen on a configurable TCP port
3. Dial remote peers
4. Handle connection events (established, closed, errors)

## Step-by-Step Instructions

### Step 1: Add Required Headers

Add the multiaddress and peer info headers to your includes:

```cpp
#include <libp2p/multi/multiaddress.hpp>
#include <libp2p/peer/peer_info.hpp>

#include <cstdlib>  // for getenv
#include <sstream>  // for string splitting
#include <vector>
```

### Step 2: Create Helper Functions

Add helper functions to parse environment variables and split strings:

```cpp
namespace {
  // Helper function to split string by delimiter
  std::vector<std::string> split(const std::string& str, char delimiter) {
    std::vector<std::string> tokens;
    std::istringstream stream(str);
    std::string token;
    while (std::getline(stream, token, delimiter)) {
      // Trim whitespace
      size_t start = token.find_first_not_of(" \t\n\r");
      size_t end = token.find_last_not_of(" \t\n\r");
      if (start != std::string::npos && end != std::string::npos) {
        tokens.push_back(token.substr(start, end - start + 1));
      }
    }
    return tokens;
  }

  // Helper function to get environment variable with default
  std::string getEnv(const std::string& name, const std::string& defaultValue = "") {
    const char* value = std::getenv(name.c_str());
    return value ? std::string(value) : defaultValue;
  }
}  // namespace
```

**What's happening here?**
- `split()` breaks a comma-separated string into individual addresses
- `getEnv()` safely reads environment variables with fallback defaults

### Step 3: Parse Remote Peer Addresses

In your main function, parse the `REMOTE_PEERS` environment variable:

```cpp
// Parse remote peer addresses from environment variable
std::vector<libp2p::multi::Multiaddress> remote_addrs;
std::string remote_peers_env = getEnv("REMOTE_PEERS", "");

if (!remote_peers_env.empty()) {
    auto addr_strings = split(remote_peers_env, ',');
    for (const auto& addr_str : addr_strings) {
        auto addr_result = libp2p::multi::Multiaddress::create(addr_str);
        if (addr_result.has_value()) {
            remote_addrs.push_back(addr_result.value());
            log->info("Parsed remote address: {}", addr_str);
        } else {
            log->error("Failed to parse multiaddress: {}", addr_str);
        }
    }
}
```

**What's happening here?**
- We read `REMOTE_PEERS` which contains comma-separated multiaddresses
- Each address like `/ip4/172.16.16.17/tcp/9092/p2p/12D3KooW...` is parsed
- Invalid addresses are logged but don't crash the application

### Step 4: Configure Listening Port

Get the listening port from environment:

```cpp
// Get listening port from environment
std::string listen_port = getEnv("LISTEN_PORT", "9000");
std::string listen_addr_str = "/ip4/0.0.0.0/tcp/" + listen_port;
```

The multiaddress `/ip4/0.0.0.0/tcp/9000` means:
- `/ip4/0.0.0.0` - Listen on all IPv4 interfaces
- `/tcp/9000` - Use TCP on port 9000

### Step 5: Start Listening

Inside your `boost::asio::post` block, add listening:

```cpp
boost::asio::post(*io_context, [&] {
    // Parse listen address
    auto listen_addr_result = libp2p::multi::Multiaddress::create(listen_addr_str);
    if (!listen_addr_result.has_value()) {
        log->error("Failed to parse listen address: {}", listen_addr_str);
        io_context->stop();
        return;
    }
    auto listen_addr = listen_addr_result.value();

    // Start listening
    auto listen_result = host->listen(listen_addr);
    if (!listen_result) {
        log->error("Failed to listen on {}: {}", listen_addr_str,
                   listen_result.error().message());
        io_context->stop();
        return;
    }

    std::cout << "Listening on: " << listen_addr.getStringAddress() << std::endl;

    // Print all listening addresses
    for (const auto& addr : host->getAddresses()) {
        std::cout << "Address: " << addr.getStringAddress() << std::endl;
    }
});
```

### Step 6: Dial Remote Peers

Add connection logic for each remote peer:

```cpp
// Connect to remote peers
for (const auto& addr : remote_addrs) {
    std::cout << "Attempting to connect to: " << addr.getStringAddress() << std::endl;

    // Extract peer ID from multiaddress
    auto peer_id_str = addr.getPeerId();
    if (!peer_id_str.has_value()) {
        std::cout << "Invalid multiaddress " << addr.getStringAddress()
                  << ": Missing /p2p/<peer_id>" << std::endl;
        continue;
    }

    auto remote_peer_id_result = libp2p::peer::PeerId::fromBase58(peer_id_str.value());
    if (!remote_peer_id_result.has_value()) {
        std::cout << "Failed to parse peer ID" << std::endl;
        continue;
    }

    auto remote_peer_id = remote_peer_id_result.value();
    libp2p::peer::PeerInfo peer_info{remote_peer_id, {addr}};

    // Asynchronous connect with callback
    host->connect(
        peer_info,
        [&, addr, remote_peer_id](auto&& conn_result) {
            if (conn_result.has_value()) {
                std::cout << "Connected to: " << remote_peer_id.toBase58()
                          << " via " << addr.getStringAddress() << std::endl;
            } else {
                std::cout << "Failed to connect to " << addr.getStringAddress()
                          << ": " << conn_result.error().message() << std::endl;
            }
        }
    );
}

std::cout << "Waiting for connections..." << std::endl;
```

**What's happening here?**
- We extract the peer ID from the multiaddress (the `/p2p/12D3KooW...` part)
- We create a `PeerInfo` with the peer ID and address
- `host->connect()` is asynchronous - we provide a callback for the result
- The callback handles both success and failure cases

## Complete Solution

Here's the complete `app/main.cpp`:

```cpp
/**
 * Lesson 2: TCP Transport
 * Establishes TCP connections and handles connection events.
 */

#include <iostream>
#include <memory>
#include <string>
#include <vector>
#include <cstdlib>
#include <sstream>

#include <boost/asio/io_context.hpp>
#include <boost/asio/post.hpp>
#include <boost/asio/signal_set.hpp>

#include <libp2p/host/host.hpp>
#include <libp2p/injector/host_injector.hpp>
#include <libp2p/log/configurator.hpp>
#include <libp2p/log/logger.hpp>
#include <libp2p/multi/multiaddress.hpp>
#include <libp2p/peer/peer_info.hpp>

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
    logging_system->configure();
    libp2p::log::setLoggingSystem(logging_system);
    libp2p::log::setLevelOfGroup("main", soralog::Level::INFO);
    auto log = libp2p::log::createLogger("Lesson2");

    // Parse remote peer addresses
    std::vector<libp2p::multi::Multiaddress> remote_addrs;
    std::string remote_peers_env = getEnv("REMOTE_PEERS", "");
    if (!remote_peers_env.empty()) {
        for (const auto& addr_str : split(remote_peers_env, ',')) {
            auto addr_result = libp2p::multi::Multiaddress::create(addr_str);
            if (addr_result.has_value()) {
                remote_addrs.push_back(addr_result.value());
            }
        }
    }

    // Get listening port
    std::string listen_port = getEnv("LISTEN_PORT", "9000");
    std::string listen_addr_str = "/ip4/0.0.0.0/tcp/" + listen_port;

    // Create host
    auto injector = libp2p::injector::makeHostInjector();
    auto host = injector.create<std::shared_ptr<libp2p::Host>>();
    auto io_context = injector.create<std::shared_ptr<boost::asio::io_context>>();

    auto peer_id = host->getId();
    std::cout << "Local peer id: " << peer_id.toBase58() << std::endl;

    // Signal handling
    boost::asio::signal_set signals(*io_context, SIGINT, SIGTERM);
    signals.async_wait([&](const boost::system::error_code&, int) {
        std::cout << "Shutting down..." << std::endl;
        io_context->stop();
    });

    // Start host
    boost::asio::post(*io_context, [&] {
        auto listen_addr = libp2p::multi::Multiaddress::create(listen_addr_str).value();
        host->listen(listen_addr);
        std::cout << "Listening on: " << listen_addr.getStringAddress() << std::endl;

        // Connect to remote peers
        for (const auto& addr : remote_addrs) {
            auto peer_id_str = addr.getPeerId();
            if (!peer_id_str) continue;

            auto remote_peer_id = libp2p::peer::PeerId::fromBase58(peer_id_str.value()).value();
            libp2p::peer::PeerInfo peer_info{remote_peer_id, {addr}};

            host->connect(peer_info, [addr, remote_peer_id](auto&& result) {
                if (result) {
                    std::cout << "Connected to: " << remote_peer_id.toBase58() << std::endl;
                } else {
                    std::cout << "Failed to connect to " << addr.getStringAddress() << std::endl;
                }
            });
        }

        std::cout << "Waiting for connections..." << std::endl;
    });

    io_context->run();
    return EXIT_SUCCESS;
}
```

## Testing Your Solution

### Using Docker (Recommended)

```bash
cd en/cpp/02-tcp-transport
docker compose up --build
python3 check.py
```

### Building Locally

```bash
export LIBP2P_INSTALL_DIR=$HOME/libp2p
export HUNTER_INSTALL_DIR=$(find ~/.hunter -type d -name "Install" | head -1)

cd en/cpp/02-tcp-transport/app
mkdir -p build
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH="$LIBP2P_INSTALL_DIR;$HUNTER_INSTALL_DIR"
cmake --build build

# Run without remote peers (just listen)
./build/lesson

# Run with a remote peer
REMOTE_PEERS="/ip4/127.0.0.1/tcp/9001/p2p/12D3KooW..." ./build/lesson
```

You should see output like:
```
Starting Universal Connectivity Application...
Local peer id: 12D3KooWEgUjBV5FJAuBSoNMRYFRHjV7PjZwRQ7b43EKX9g7D6xV
Listening on: /ip4/0.0.0.0/tcp/9000
Waiting for connections...
```

## Understanding Multiaddresses

Multiaddresses are libp2p's flexible addressing format:

| Example | Meaning |
|---------|---------|
| `/ip4/127.0.0.1/tcp/9000` | IPv4 localhost, TCP port 9000 |
| `/ip4/0.0.0.0/tcp/9000` | All IPv4 interfaces, port 9000 |
| `/ip4/1.2.3.4/tcp/9000/p2p/12D3KooW...` | Full peer address with ID |

The `/p2p/<peer_id>` suffix is required when dialing to verify you're connecting to the right peer.

## What You've Learned

Congratulations! You've extended your cpp-libp2p node with:

- **TCP Transport**: Network communication over TCP
- **Listening**: Accepting incoming connections
- **Dialing**: Connecting to remote peers
- **Multiaddresses**: libp2p's flexible addressing
- **Async Callbacks**: Handling connection results

## Key Concepts Summary

| Concept | cpp-libp2p Implementation |
|---------|---------------------------|
| Listen | `host->listen(multiaddr)` |
| Dial/Connect | `host->connect(peer_info, callback)` |
| Parse Address | `Multiaddress::create(string)` |
| Get Peer ID | `multiaddr.getPeerId()` |
| Environment Vars | `std::getenv("REMOTE_PEERS")` |

## What's Next?

In the next lesson, you'll:
- Add the **ping protocol** to test connections
- Learn about **protocol handlers**
- Connect to a **checkpoint server** for verification

Your transport layer is ready - now let's add some protocols!
