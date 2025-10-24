# Lesson 7: Kademlia Checkpoint 🏆

Welcome to your fourth checkpoint! In this lesson, you'll implement Kademlia, a distributed hash table (DHT) protocol that enables decentralized peer discovery and content routing in libp2p networks using py-libp2p.

## Learning Objectives

By the end of this lesson, you will:
- Understand distributed hash tables and the Kademlia protocol
- Implement Kademlia DHT for peer discovery in Python
- Handle bootstrap processes and peer routing
- Work with bootstrap nodes and network initialization

## Background: Kademlia DHT

Kademlia is a distributed hash table protocol that provides:

- **Decentralized Peer Discovery**: Find peers without central servers
- **Content Routing**: Locate data distributed across the network
- **Self-Organizing**: Networks automatically adapt to peer joins/leaves
- **Scalability**: Efficient routing with logarithmic lookup complexity

It's used by IPFS, BitTorrent, and many other P2P systems for peer and content discovery.

## Your Task

Building on your gossipsub implementation from Lesson 6, you need to:

1. **Add Kademlia DHT**: Include KadDHT in your application
2. **Handle Bootstrap Process**: Initiate and monitor DHT bootstrap
3. **Process Kademlia Events**: Handle peer discovery and routing events

## Step-by-Step Instructions

### Step 1: Update Dependencies

Ensure your requirements.txt includes the necessary py-libp2p dependencies:

```txt
libp2p>=0.2.0
trio>=0.20.0
multiaddr>=0.0.9
base58>=2.1.0
protobuf>=4.21.0
```

### Step 2: Import Required Modules

Add the necessary imports to your main.py:

```python
import argparse
import logging
import os
import random
import secrets
import sys

import base58
from multiaddr import (
    Multiaddr,
)
import trio

from libp2p import (
    new_host,
)
from libp2p.abc import (
    IHost,
)
from libp2p.crypto.secp256k1 import (
    create_new_key_pair,
)
from libp2p.kad_dht.kad_dht import (
    DHTMode,
    KadDHT,
)
from libp2p.kad_dht.utils import (
    create_key_from_binary,
)
from libp2p.tools.async_service import (
    background_trio_service,
)
from libp2p.tools.utils import (
    info_from_p2p_addr,
)

```

### Step 3: Configure Logging and Constants

Set up logging and define constants:

```python
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("kademlia-example")

# Configure DHT module loggers to inherit from the parent logger
# This ensures all kademlia-example.* loggers use the same configuration
# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_ADDR_LOG = os.path.join(SCRIPT_DIR, "server_node_addr.txt")

# Set the level for all child loggers
for module in [
    "kad_dht",
    "value_store",
    "peer_routing",
    "routing_table",
    "provider_store",
]:
    child_logger = logging.getLogger(f"kademlia-example.{module}")
    child_logger.setLevel(logging.INFO)
    child_logger.propagate = True  # Allow propagation to parent

# File to store node information
bootstrap_nodes = []
```

### Step 4: Connect to Bootstrap Nodes

Create a function to connect to bootstrap nodes:

```python
async def connect_to_bootstrap_nodes(host: IHost, bootstrap_addrs: list[str]) -> None:
    """
    Connect to the bootstrap nodes provided in the list.

    params: host: The host instance to connect to
            bootstrap_addrs: List of bootstrap node addresses

    Returns
    -------
        None

    """
    for addr in bootstrap_addrs:
        try:
            peerInfo = info_from_p2p_addr(Multiaddr(addr))
            host.get_peerstore().add_addrs(peerInfo.peer_id, peerInfo.addrs, 3600)
            await host.connect(peerInfo)
        except Exception as e:
            logger.error(f"Failed to connect to bootstrap node {addr}: {e}")

def save_server_addr(addr: str) -> None:
    """Append the server's multiaddress to the log file."""
    try:
        with open(SERVER_ADDR_LOG, "w") as f:
            f.write(addr + "\n")
        logger.info(f"Saved server address to log: {addr}")
    except Exception as e:
        logger.error(f"Failed to save server address: {e}")


def load_server_addrs() -> list[str]:
    """Load all server multiaddresses from the log file."""
    if not os.path.exists(SERVER_ADDR_LOG):
        return []
    try:
        with open(SERVER_ADDR_LOG) as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Failed to load server addresses: {e}")
        return []
```

### Step 5: Cleanup Task

Add a cleanup task for peer store management:

```python
async def cleanup_task(host: IHost, interval: int = 60) -> None:
    """Manual cleanup task for the peer store if the built-in one doesn't exist."""
    while True:
        try:
            await trio.sleep(interval)
            # Simple cleanup: remove peers that haven't been seen recently
            peerstore = host.get_peerstore()
            peer_ids = list(peerstore.peer_ids())
            logger.debug(f"Cleanup task: checking {len(peer_ids)} peers")
            
            # Note: This is a basic implementation. In a real scenario,
            # you might want to implement more sophisticated cleanup logic
            
        except Exception as e:
            logger.warning(f"Cleanup task error: {e}")
```

### Step 6: Main Application Logic

Implement the main application:

```python
async def run_node(
    port: int, mode: str, bootstrap_addrs: list[str] | None = None
) -> None:
    """Run a node that serves content in the DHT with setup inlined."""
    try:
        if port <= 0:
            port = random.randint(10000, 60000)
        logger.debug(f"Using port: {port}")

        # Convert string mode to DHTMode enum
        if mode is None or mode.upper() == "CLIENT":
            dht_mode = DHTMode.CLIENT
        elif mode.upper() == "SERVER":
            dht_mode = DHTMode.SERVER
        else:
            logger.error(f"Invalid mode: {mode}. Must be 'client' or 'server'")
            sys.exit(1)

        # Load server addresses for client mode
        if dht_mode == DHTMode.CLIENT:
            server_addrs = load_server_addrs()
            if server_addrs:
                logger.info(f"Loaded {len(server_addrs)} server addresses from log")
                bootstrap_nodes.append(server_addrs[0])  # Use the first server address
            else:
                logger.warning("No server addresses found in log file")

        if bootstrap_addrs:
            for addr in bootstrap_addrs:
                bootstrap_nodes.append(addr)

        key_pair = create_new_key_pair(secrets.token_bytes(32))
        host = new_host(key_pair=key_pair)
        listen_addr = Multiaddr(f"/ip4/127.0.0.1/tcp/{port}")

        async with host.run(listen_addrs=[listen_addr]), trio.open_nursery() as nursery:
            # Start the peer-store cleanup task - check if method exists first
            peerstore = host.get_peerstore()
            if hasattr(peerstore, 'start_cleanup_task'):
                nursery.start_soon(peerstore.start_cleanup_task, 60)
                logger.debug("Started built-in peer store cleanup task")
            else:
                nursery.start_soon(cleanup_task, host, 60)
                logger.debug("Started manual peer store cleanup task")

            peer_id = host.get_id().pretty()
            addr_str = f"/ip4/127.0.0.1/tcp/{port}/p2p/{peer_id}"
            
            # Connect to bootstrap nodes
            if bootstrap_nodes:
                await connect_to_bootstrap_nodes(host, bootstrap_nodes)
                logger.info(f"Connected to bootstrap nodes: {list(host.get_connected_peers())}")
            
            dht = KadDHT(host, dht_mode)
            
            # Add all peer ids from the host to the dht routing table
            for peer_id_obj in host.get_peerstore().peer_ids():
                try:
                    await dht.routing_table.add_peer(peer_id_obj)
                except Exception as e:
                    logger.warning(f"Failed to add peer {peer_id_obj} to routing table: {e}")
            
            bootstrap_cmd = f"--bootstrap {addr_str}"
            logger.info("To connect to this node, use: %s", bootstrap_cmd)

            # Save server address in server mode
            if dht_mode == DHTMode.SERVER:
                save_server_addr(addr_str)

            # Start the DHT service
            async with background_trio_service(dht):
                logger.info(f"DHT service started in {dht_mode.value} mode")
                val_key = create_key_from_binary(b"py-libp2p kademlia example value")
                content = b"Hello from python node "
                content_key = create_key_from_binary(content)

                if dht_mode == DHTMode.SERVER:
                    # Store a value in the DHT
                    msg = "Hello message from Sumanjeet"
                    val_data = msg.encode()
                    try:
                        await dht.put_value(val_key, val_data)
                        logger.info(
                            f"Stored value '{val_data.decode()}' "
                            f"with key: {base58.b58encode(val_key).decode()}"
                        )
                    except Exception as e:
                        logger.error(f"Failed to store value: {e}")

                    # Advertise as content server
                    try:
                        success = await dht.provider_store.provide(content_key)
                        if success:
                            logger.info(
                                "Successfully advertised as server "
                                f"for content: {content_key.hex()}"
                            )
                        else:
                            logger.warning("Failed to advertise as content server")
                    except Exception as e:
                        logger.error(f"Failed to advertise as content server: {e}")

                else:
                    # Retrieve the value (client mode)
                    try:
                        logger.info(
                            "Looking up key: %s", base58.b58encode(val_key).decode()
                        )
                        val_data = await dht.get_value(val_key)
                        if val_data:
                            try:
                                logger.info(f"Retrieved value: {val_data.decode()}")
                            except UnicodeDecodeError:
                                logger.info(f"Retrieved value (bytes): {val_data!r}")
                        else:
                            logger.warning("Failed to retrieve value")
                    except Exception as e:
                        logger.error(f"Failed to retrieve value: {e}")

                    # Also check if we can find servers for our own content
                    try:
                        logger.info("Looking for servers of content: %s", content_key.hex())
                        providers = await dht.provider_store.find_providers(content_key)
                        if providers:
                            logger.info(
                                "Found %d servers for content: %s",
                                len(providers),
                                [p.peer_id.pretty() for p in providers],
                            )
                        else:
                            logger.warning(
                                "No servers found for content %s", content_key.hex()
                            )
                    except Exception as e:
                        logger.error(f"Failed to find providers: {e}")

                # Keep the node running
                logger.info("Node is now running. Press Ctrl+C to stop.")
                try:
                    while True:
                        logger.debug(
                            "Status - Connected peers: %d, "
                            "Peers in store: %d, Values in store: %d",
                            len(dht.host.get_connected_peers()),
                            len(dht.host.get_peerstore().peer_ids()),
                            len(dht.value_store.store),
                        )
                        await trio.sleep(10)
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal, shutting down...")
                    return

    except Exception as e:
        logger.error(f"Server node error: {e}", exc_info=True)
        sys.exit(1)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Kademlia DHT example with content server functionality"
    )
    parser.add_argument(
        "--mode",
        default="server",
        help="Run as a server or client node",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Port to listen on (0 for random)",
    )
    parser.add_argument(
        "--bootstrap",
        type=str,
        nargs="*",
        help=(
            "Multiaddrs of bootstrap nodes. "
            "Provide a space-separated list of addresses. "
            "This is required for client mode."
        ),
    )
    # add option to use verbose logging
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()
    # Set logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    return args


def main():
    """Main entry point for the kademlia demo."""
    try:
        args = parse_args()
        logger.info(
            "Running in %s mode on port %d",
            args.mode,
            args.port,
        )
        trio.run(run_node, args.port, args.mode, args.bootstrap)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.critical(f"Script failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

## Key Changes from Previous Implementation

The updated implementation includes several important improvements:

1. **Proper DHT Initialization**: The DHT is now properly initialized with the correct mode and peer routing table setup
2. **Server Address Persistence**: Server addresses are saved to a file and can be loaded by client nodes
3. **Better Bootstrap Logic**: Improved bootstrap node connection and DHT routing table population
4. **Enhanced Error Handling**: More robust error handling throughout the application
5. **Proper Cleanup**: Automatic peer store cleanup with fallback manual implementation
6. **Command Line Arguments**: Support for runtime configuration via command line arguments
7. **Environment Variable Integration**: Seamless integration with Docker Compose environment variables

## Testing Your Implementation

1. Set the environment variables:
   ```bash
   export PROJECT_ROOT=/path/to/workshop
   export LESSON_PATH=en/py/07-kademlia-checkpoint
   ```

2. Change into the lesson directory:
    ```bash
    cd $PROJECT_ROOT/$LESSON_PATH
    ```

3. Run with Docker Compose:
   ```bash
   docker rm -f workshop-lesson ucw-checker-07-kademlia-checkpoint
   docker network rm -f workshop-net
   docker network create --driver bridge --subnet 172.16.16.0/24 workshop-net
   docker compose --project-name workshop up --build --remove-orphans
   ```

4. Check your output:
   ```bash
   python run_test.py
   ```

You can also test manually with command line arguments:

```bash
# Run a server node
python main.py --mode server --port 8000

# Run a client node (in another terminal)
python main.py --mode client --port 8000
```

## Success Criteria

Your implementation should:
- ✅ Display connection establishment messages
- ✅ Subscribe to gossipsub topics  
- ✅ Add bootstrap peers to Kademlia
- ✅ Initialize DHT in proper mode (SERVER/CLIENT)
- ✅ Store and retrieve values in the DHT
- ✅ Advertise and discover content providers
- ✅ Handle peer discovery and routing events
- ✅ Maintain persistent server address information

## Hint - Complete Solution

Below is the complete working solution:

```python
#!/usr/bin/env python

"""
A basic example of using the Kademlia DHT implementation, with all setup logic inlined.
This example demonstrates both value storage/retrieval and content server
advertisement/discovery.
"""

import argparse
import logging
import os
import random
import secrets
import sys

import base58
from multiaddr import (
    Multiaddr,
)
import trio

from libp2p import (
    new_host,
)
from libp2p.abc import (
    IHost,
)
from libp2p.crypto.secp256k1 import (
    create_new_key_pair,
)
from libp2p.kad_dht.kad_dht import (
    DHTMode,
    KadDHT,
)
from libp2p.kad_dht.utils import (
    create_key_from_binary,
)
from libp2p.tools.async_service import (
    background_trio_service,
)
from libp2p.tools.utils import (
    info_from_p2p_addr,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("kademlia-example")

# Configure DHT module loggers to inherit from the parent logger
# This ensures all kademlia-example.* loggers use the same configuration
# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_ADDR_LOG = os.path.join(SCRIPT_DIR, "server_node_addr.txt")

# Set the level for all child loggers
for module in [
    "kad_dht",
    "value_store",
    "peer_routing",
    "routing_table",
    "provider_store",
]:
    child_logger = logging.getLogger(f"kademlia-example.{module}")
    child_logger.setLevel(logging.INFO)
    child_logger.propagate = True  # Allow propagation to parent

# File to store node information
bootstrap_nodes = []


# function to take bootstrap_nodes as input and connects to them
async def connect_to_bootstrap_nodes(host: IHost, bootstrap_addrs: list[str]) -> None:
    """
    Connect to the bootstrap nodes provided in the list.

    params: host: The host instance to connect to
            bootstrap_addrs: List of bootstrap node addresses

    Returns
    -------
        None

    """
    for addr in bootstrap_addrs:
        try:
            peerInfo = info_from_p2p_addr(Multiaddr(addr))
            host.get_peerstore().add_addrs(peerInfo.peer_id, peerInfo.addrs, 3600)
            await host.connect(peerInfo)
        except Exception as e:
            logger.error(f"Failed to connect to bootstrap node {addr}: {e}")


def save_server_addr(addr: str) -> None:
    """Append the server's multiaddress to the log file."""
    try:
        with open(SERVER_ADDR_LOG, "w") as f:
            f.write(addr + "\n")
        logger.info(f"Saved server address to log: {addr}")
    except Exception as e:
        logger.error(f"Failed to save server address: {e}")


def load_server_addrs() -> list[str]:
    """Load all server multiaddresses from the log file."""
    if not os.path.exists(SERVER_ADDR_LOG):
        return []
    try:
        with open(SERVER_ADDR_LOG) as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Failed to load server addresses: {e}")
        return []


async def cleanup_task(host: IHost, interval: int = 60) -> None:
    """Manual cleanup task for the peer store if the built-in one doesn't exist."""
    while True:
        try:
            await trio.sleep(interval)
            # Simple cleanup: remove peers that haven't been seen recently
            peerstore = host.get_peerstore()
            peer_ids = list(peerstore.peer_ids())
            logger.debug(f"Cleanup task: checking {len(peer_ids)} peers")
            
            # Note: This is a basic implementation. In a real scenario,
            # you might want to implement more sophisticated cleanup logic
            
        except Exception as e:
            logger.warning(f"Cleanup task error: {e}")


async def run_node(
    port: int, mode: str, bootstrap_addrs: list[str] | None = None
) -> None:
    """Run a node that serves content in the DHT with setup inlined."""
    try:
        if port <= 0:
            port = random.randint(10000, 60000)
        logger.debug(f"Using port: {port}")

        # Convert string mode to DHTMode enum
        if mode is None or mode.upper() == "CLIENT":
            dht_mode = DHTMode.CLIENT
        elif mode.upper() == "SERVER":
            dht_mode = DHTMode.SERVER
        else:
            logger.error(f"Invalid mode: {mode}. Must be 'client' or 'server'")
            sys.exit(1)

        # Load server addresses for client mode
        if dht_mode == DHTMode.CLIENT:
            server_addrs = load_server_addrs()
            if server_addrs:
                logger.info(f"Loaded {len(server_addrs)} server addresses from log")
                bootstrap_nodes.append(server_addrs[0])  # Use the first server address
            else:
                logger.warning("No server addresses found in log file")

        if bootstrap_addrs:
            for addr in bootstrap_addrs:
                bootstrap_nodes.append(addr)

        key_pair = create_new_key_pair(secrets.token_bytes(32))
        host = new_host(key_pair=key_pair)
        listen_addr = Multiaddr(f"/ip4/127.0.0.1/tcp/{port}")

        async with host.run(listen_addrs=[listen_addr]), trio.open_nursery() as nursery:
            # Start the peer-store cleanup task - check if method exists first
            peerstore = host.get_peerstore()
            if hasattr(peerstore, 'start_cleanup_task'):
                nursery.start_soon(peerstore.start_cleanup_task, 60)
                logger.debug("Started built-in peer store cleanup task")
            else:
                nursery.start_soon(cleanup_task, host, 60)
                logger.debug("Started manual peer store cleanup task")

            peer_id = host.get_id().pretty()
            addr_str = f"/ip4/127.0.0.1/tcp/{port}/p2p/{peer_id}"
            
            # Connect to bootstrap nodes
            if bootstrap_nodes:
                await connect_to_bootstrap_nodes(host, bootstrap_nodes)
                logger.info(f"Connected to bootstrap nodes: {list(host.get_connected_peers())}")
            
            dht = KadDHT(host, dht_mode)
            
            # Add all peer ids from the host to the dht routing table
            for peer_id_obj in host.get_peerstore().peer_ids():
                try:
                    await dht.routing_table.add_peer(peer_id_obj)
                except Exception as e:
                    logger.warning(f"Failed to add peer {peer_id_obj} to routing table: {e}")
            
            bootstrap_cmd = f"--bootstrap {addr_str}"
            logger.info("To connect to this node, use: %s", bootstrap_cmd)

            # Save server address in server mode
            if dht_mode == DHTMode.SERVER:
                save_server_addr(addr_str)

            # Start the DHT service
            async with background_trio_service(dht):
                logger.info(f"DHT service started in {dht_mode.value} mode")
                val_key = create_key_from_binary(b"py-libp2p kademlia example value")
                content = b"Hello from python node "
                content_key = create_key_from_binary(content)

                if dht_mode == DHTMode.SERVER:
                    # Store a value in the DHT
                    msg = "Hello message from Sumanjeet"
                    val_data = msg.encode()
                    try:
                        await dht.put_value(val_key, val_data)
                        logger.info(
                            f"Stored value '{val_data.decode()}' "
                            f"with key: {base58.b58encode(val_key).decode()}"
                        )
                    except Exception as e:
                        logger.error(f"Failed to store value: {e}")

                    # Advertise as content server
                    try:
                        success = await dht.provider_store.provide(content_key)
                        if success:
                            logger.info(
                                "Successfully advertised as server "
                                f"for content: {content_key.hex()}"
                            )
                        else:
                            logger.warning("Failed to advertise as content server")
                    except Exception as e:
                        logger.error(f"Failed to advertise as content server: {e}")

                else:
                    # Retrieve the value (client mode)
                    try:
                        logger.info(
                            "Looking up key: %s", base58.b58encode(val_key).decode()
                        )
                        val_data = await dht.get_value(val_key)
                        if val_data:
                            try:
                                logger.info(f"Retrieved value: {val_data.decode()}")
                            except UnicodeDecodeError:
                                logger.info(f"Retrieved value (bytes): {val_data!r}")
                        else:
                            logger.warning("Failed to retrieve value")
                    except Exception as e:
                        logger.error(f"Failed to retrieve value: {e}")

                    # Also check if we can find servers for our own content
                    try:
                        logger.info("Looking for servers of content: %s", content_key.hex())
                        providers = await dht.provider_store.find_providers(content_key)
                        if providers:
                            logger.info(
                                "Found %d servers for content: %s",
                                len(providers),
                                [p.peer_id.pretty() for p in providers],
                            )
                        else:
                            logger.warning(
                                "No servers found for content %s", content_key.hex()
                            )
                    except Exception as e:
                        logger.error(f"Failed to find providers: {e}")

                # Keep the node running
                logger.info("Node is now running. Press Ctrl+C to stop.")
                try:
                    while True:
                        logger.debug(
                            "Status - Connected peers: %d, "
                            "Peers in store: %d, Values in store: %d",
                            len(dht.host.get_connected_peers()),
                            len(dht.host.get_peerstore().peer_ids()),
                            len(dht.value_store.store),
                        )
                        await trio.sleep(10)
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal, shutting down...")
                    return

    except Exception as e:
        logger.error(f"Server node error: {e}", exc_info=True)
        sys.exit(1)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Kademlia DHT example with content server functionality"
    )
    parser.add_argument(
        "--mode",
        default="server",
        help="Run as a server or client node",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Port to listen on (0 for random)",
    )
    parser.add_argument(
        "--bootstrap",
        type=str,
        nargs="*",
        help=(
            "Multiaddrs of bootstrap nodes. "
            "Provide a space-separated list of addresses. "
            "This is required for client mode."
        ),
    )
    # add option to use verbose logging
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()
    # Set logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    return args


def main():
    """Main entry point for the kademlia demo."""
    try:
        args = parse_args()
        logger.info(
            "Running in %s mode on port %d",
            args.mode,
            args.port,
        )
        trio.run(run_node, args.port, args.mode, args.bootstrap)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.critical(f"Script failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

## What's Next?

Congratulations! You've reached your fourth checkpoint 🎉

You now have a fully-featured libp2p node that can:
- Connect over multiple transports
- Exchange peer identification  
- Participate in gossipsub messaging
- Discover peers through Kademlia DHT
- Store and retrieve data in a distributed hash table
- Advertise and discover content providers

Key concepts you've learned:
- **Distributed Hash Tables**: Decentralized data and peer storage
- **Bootstrap Process**: Joining existing P2P networks  
- **Peer Discovery**: Finding other nodes without central coordination
- **Routing Tables**: Efficient peer organization and lookup
- **Content Provision**: Advertising and discovering content in the network

In the final lesson, you'll complete the Universal Connectivity application by implementing chat messaging and connecting to the real network!