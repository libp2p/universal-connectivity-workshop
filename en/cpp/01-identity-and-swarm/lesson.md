# Lesson 1: Identity and Basic Host

Welcome to your first step into peer-to-peer networking with cpp-libp2p! In this lesson, you'll create your very first libp2p peer and understand the fundamental concept of peer identity.

## Learning Objectives

By the end of this lesson, you will:
- Understand what a PeerId is and why it's important
- Create a libp2p Host with automatic keypair generation
- Initialize and run the Boost.Asio event loop
- Run your first libp2p application with C++

## Background: Peer Identity in libp2p

In traditional client-server applications, servers have known addresses (like domain names), but clients are anonymous. In peer-to-peer networks, every participant is both a client and a server, so each peer needs a stable, verifiable identity.

libp2p uses **cryptographic keypairs** for peer identity:
- **Private Key**: Kept secret, used to sign messages and prove identity
- **Public Key**: Shared with others, used to verify signatures
- **PeerId**: A hash of the public key, used as a short identifier

This design ensures that:
1. Peers can prove they control their identity (via signatures)
2. Others can verify that proof (via public key cryptography)
3. Identities are compact and easy to share (via PeerId hash)

## cpp-libp2p Architecture Overview

Before we start coding, let's understand some key concepts in cpp-libp2p:

### Dependency Injection with Boost.DI

cpp-libp2p uses **Boost.DI** for dependency injection. This pattern allows you to configure components (like hosts, transports, and protocols) in a flexible way. The best part? The injector **automatically generates an Ed25519 keypair** for you!

```cpp
// Create a fully configured host with auto-generated identity
auto injector = libp2p::injector::makeHostInjector();
auto host = injector.create<std::shared_ptr<libp2p::Host>>();
```

### What makeHostInjector() Provides Automatically

When you call `makeHostInjector()`, it sets up:
- **Ed25519 Keypair**: Auto-generated cryptographic identity
- **TCP Transport**: Network communication over TCP
- **QUIC Transport**: Modern UDP-based transport
- **Noise Security**: Encrypted connections
- **Yamux Multiplexer**: Multiple streams over one connection
- **And more!**

### Async I/O with Boost.Asio

cpp-libp2p is built on **Boost.Asio** for asynchronous I/O operations. All network operations are non-blocking and event-driven:

```cpp
auto io_context = injector.create<std::shared_ptr<boost::asio::io_context>>();
io_context->run();  // This runs the event loop
```

## Your Task

Create a C++ application that:
1. Creates a libp2p Host (with auto-generated Ed25519 identity)
2. Prints the peer's ID when the application starts
3. Runs the Boost.Asio event loop
4. Handles graceful shutdown on Ctrl+C

## Step-by-Step Instructions

### Step 1: Set Up Your Main File

Create `app/main.cpp` with the basic includes:

```cpp
/**
 * Lesson 1: Identity and Basic Host
 * Creates a basic libp2p host with cryptographic identity.
 */

#include <iostream>
#include <memory>
#include <csignal>

#include <boost/asio/io_context.hpp>
#include <boost/asio/post.hpp>
#include <boost/asio/signal_set.hpp>

#include <libp2p/host/host.hpp>
#include <libp2p/injector/host_injector.hpp>
#include <libp2p/log/configurator.hpp>
#include <libp2p/log/logger.hpp>
```

**What's happening here?**

- We include Boost.Asio for async I/O and signal handling
- We include `libp2p/host/host.hpp` for the Host interface
- We include `libp2p/injector/host_injector.hpp` for dependency injection
- The logging headers help us configure output

### Step 2: Configure Logging

Add a logging configuration using soralog (cpp-libp2p's logging system):

```cpp
namespace {
  const std::string logger_config(R"(
# ----------------
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
# ----------------
  )");
}  // namespace
```

This YAML configuration sets up console logging with colors enabled.

### Step 3: Set Up the Main Function with Logging

Create the main function and initialize logging:

```cpp
int main(int argc, char** argv) {
    std::cout << "Starting Universal Connectivity Application..." << std::endl;

    // Initialize logging system
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

    auto log = libp2p::log::createLogger("Lesson1");
```

### Step 4: Create the Host Using Dependency Injection

This is the magic of cpp-libp2p - one line creates a fully configured host:

```cpp
    // Create host using dependency injection
    // The injector automatically generates an Ed25519 keypair!
    auto injector = libp2p::injector::makeHostInjector();

    // Extract the host and io_context from the injector
    auto host = injector.create<std::shared_ptr<libp2p::Host>>();
    auto io_context =
        injector.create<std::shared_ptr<boost::asio::io_context>>();
```

**What's happening here?**

- `makeHostInjector()` creates a dependency injector with all default configurations
- Internally, it generates an Ed25519 keypair automatically
- We extract the `Host` and `io_context` from the injector

### Step 5: Get and Print the Peer ID

```cpp
    // Get and print the peer ID
    auto peer_id = host->getId();
    std::cout << "Local peer id: " << peer_id.toBase58() << std::endl;
```

The `toBase58()` method converts the peer ID to a human-readable Base58 string format, which starts with `12D3KooW` for Ed25519 keys.

### Step 6: Set Up Signal Handling and Run the Event Loop

```cpp
    // Set up signal handling for graceful shutdown (Ctrl+C)
    boost::asio::signal_set signals(*io_context, SIGINT, SIGTERM);
    signals.async_wait([&](const boost::system::error_code&, int) {
        std::cout << "Shutting down..." << std::endl;
        io_context->stop();
    });

    // Start the host
    boost::asio::post(*io_context, [&] {
        host->start();
        log->info("Host started with PeerId: {}", peer_id.toBase58());
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

**What's happening here?**

- `signal_set` handles Ctrl+C gracefully
- `boost::asio::post` schedules work on the io_context
- `host->start()` starts the host's network listeners
- `io_context->run()` runs the event loop until stopped

## Complete Solution

Here's the complete `app/main.cpp`:

```cpp
/**
 * Lesson 1: Identity and Basic Host
 * Creates a basic libp2p host with cryptographic identity.
 */

#include <iostream>
#include <memory>
#include <csignal>

#include <boost/asio/io_context.hpp>
#include <boost/asio/post.hpp>
#include <boost/asio/signal_set.hpp>

#include <libp2p/host/host.hpp>
#include <libp2p/injector/host_injector.hpp>
#include <libp2p/log/configurator.hpp>
#include <libp2p/log/logger.hpp>

namespace {
  const std::string logger_config(R"(
# ----------------
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
# ----------------
  )");
}  // namespace

int main(int argc, char** argv) {
    std::cout << "Starting Universal Connectivity Application..." << std::endl;

    // Initialize logging system
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

    auto log = libp2p::log::createLogger("Lesson1");

    // Create host using dependency injection
    // The injector automatically generates an Ed25519 keypair!
    auto injector = libp2p::injector::makeHostInjector();

    // Extract the host and io_context from the injector
    auto host = injector.create<std::shared_ptr<libp2p::Host>>();
    auto io_context =
        injector.create<std::shared_ptr<boost::asio::io_context>>();

    // Get and print the peer ID
    auto peer_id = host->getId();
    std::cout << "Local peer id: " << peer_id.toBase58() << std::endl;

    // Set up signal handling for graceful shutdown (Ctrl+C)
    boost::asio::signal_set signals(*io_context, SIGINT, SIGTERM);
    signals.async_wait([&](const boost::system::error_code&, int) {
        std::cout << "Shutting down..." << std::endl;
        io_context->stop();
    });

    // Start the host
    boost::asio::post(*io_context, [&] {
        host->start();
        log->info("Host started with PeerId: {}", peer_id.toBase58());
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

## Testing Your Solution

### Using Docker (Recommended)

Docker provides a consistent build environment with all dependencies pre-configured:

```bash
cd en/cpp/01-identity-and-swarm
docker compose up --build
python3 check.py
```

**Note**: The first Docker build takes 15-20 minutes as it compiles cpp-libp2p and all dependencies. Subsequent builds are much faster due to caching.

### Building Locally

To build locally, you first need to build and install cpp-libp2p (see `setup.md` for details):

```bash
# Clone and build cpp-libp2p (uses Hunter for dependency management)
git clone https://github.com/libp2p/cpp-libp2p.git
cd cpp-libp2p
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DTESTING=OFF -DEXAMPLES=OFF \
    -DCMAKE_INSTALL_PREFIX=$HOME/libp2p
cmake --build . -j$(nproc)
cmake --install .
```

Then build the lesson:

```bash
# Set paths
export LIBP2P_INSTALL_DIR=$HOME/libp2p
export HUNTER_INSTALL_DIR=$(find ~/.hunter -type d -name "Install" | head -1)

# Build
cd en/cpp/01-identity-and-swarm/app
mkdir -p build
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH="$LIBP2P_INSTALL_DIR;$HUNTER_INSTALL_DIR"
cmake --build build

# Run and save output
timeout 5 ./build/lesson > ../stdout.log 2>&1
cat ../stdout.log
```

You should see output similar to:
```
Starting Universal Connectivity Application...
Local peer id: 12D3KooWEgUjBV5FJAuBSoNMRYFRHjV7PjZwRQ7b43EKX9g7D6xV
```

Press Ctrl+C to stop the application.

## Understanding the PeerId Format

In libp2p, PeerIds follow a specific format:
- **12D3KooW...**: Indicates an Ed25519 key (most common, what we use)
- **Qm...**: Indicates an RSA key (legacy format)
- **16Uiu2HAm...**: Indicates a secp256k1 key

The PeerId is derived from the public key using a multihash format, making it:
- Compact (easy to share)
- Verifiable (can be checked against the public key)
- Self-certifying (no central authority needed)

## What You've Learned

Congratulations! You've created your first cpp-libp2p node with:

- **Automatic Identity**: The injector generated an Ed25519 keypair for you
- **PeerId**: A compact identifier derived from the public key
- **Basic Host**: The foundation that will handle all network operations
- **Async Structure**: Ready to handle network events with Boost.Asio

## Key Concepts Summary

| Concept | cpp-libp2p Implementation |
|---------|---------------------------|
| Host Creation | `makeHostInjector()` + `injector.create<Host>()` |
| Auto Keypair | Injector generates Ed25519 automatically |
| PeerId Access | `host->getId().toBase58()` |
| Event Loop | `io_context->run()` |
| Signal Handling | `boost::asio::signal_set` |

## Advanced: Custom Keypair (Optional)

If you want to use a specific keypair instead of auto-generated:

```cpp
#include <libp2p/crypto/key.hpp>

// Create a keypair manually
libp2p::crypto::KeyPair keypair{
    libp2p::crypto::PublicKey{{libp2p::crypto::Key::Type::Ed25519, public_bytes}},
    libp2p::crypto::PrivateKey{{libp2p::crypto::Key::Type::Ed25519, private_bytes}}
};

// Use it with the injector
auto injector = libp2p::injector::makeHostInjector(
    libp2p::injector::useKeyPair(keypair)
);
```

## What's Next?

In the next lesson, you'll learn about:
- **Multiaddresses**: How peers specify where they can be reached
- **Transport Layers**: Configuring TCP to listen on specific addresses
- **Connection Establishment**: Actually connecting to other peers

Your identity is just the beginning - now let's make your peer reachable on the network!
