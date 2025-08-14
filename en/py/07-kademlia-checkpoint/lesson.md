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
import secrets
import sys
import time
from typing import List, Optional

import trio
from multiaddr import Multiaddr

from libp2p import new_host
from libp2p.abc import IHost
from libp2p.crypto.secp256k1 import create_new_key_pair
from libp2p.kad_dht.kad_dht import DHTMode, KadDHT
from libp2p.peer.id import ID as PeerID
from libp2p.pubsub.gossipsub import GossipSub
from libp2p.tools.async_service import background_trio_service
from libp2p.tools.utils import info_from_p2p_addr

# Message protocol
from your_message_protocol import UniversalConnectivityMessage, MessageType
```

### Step 3: Configure Logging and Constants

Set up logging and define constants:

```python
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("kademlia-checkpoint")

# Protocol constants
GOSSIPSUB_TOPICS = [
    "universal-connectivity",
    "universal-connectivity-file", 
    "universal-connectivity-browser-peer-discovery"
]
```

### Step 4: Parse Environment Variables

Add functions to parse bootstrap and remote peers from environment variables:

```python
def parse_multiaddrs_from_env(env_var: str) -> List[str]:
    """Parse multiaddresses from environment variable."""
    addrs_str = os.environ.get(env_var, "")
    if not addrs_str:
        return []
    
    return [
        addr.strip() 
        for addr in addrs_str.split(",") 
        if addr.strip()
    ]

def get_bootstrap_peers() -> List[str]:
    """Get bootstrap peer addresses from BOOTSTRAP_PEERS env var."""
    return parse_multiaddrs_from_env("BOOTSTRAP_PEERS")

def get_remote_peers() -> List[str]:
    """Get remote peer addresses from REMOTE_PEERS env var."""  
    return parse_multiaddrs_from_env("REMOTE_PEERS")
```

### Step 5: Connect to Bootstrap Nodes

Create a function to connect to bootstrap nodes:

```python
async def connect_to_bootstrap_nodes(host: IHost, bootstrap_addrs: List[str]) -> None:
    """Connect to the bootstrap nodes provided in the list."""
    for addr in bootstrap_addrs:
        try:
            logger.info(f"Adding bootstrap peer: {addr}")
            peer_info = info_from_p2p_addr(Multiaddr(addr))
            host.get_peerstore().add_addrs(peer_info.peer_id, peer_info.addrs, 3600)
            await host.connect(peer_info)
        except Exception as e:
            logger.warning(f"Failed to connect to bootstrap node {addr}: {e}")
```

### Step 6: Create Message Handler

Implement the gossipsub message handler:

```python
async def handle_gossipsub_message(msg_data: bytes, topic: str, sender: PeerID) -> None:
    """Handle incoming gossipsub messages."""
    try:
        # Decode the protobuf message
        message = UniversalConnectivityMessage()
        message.ParseFromString(msg_data)
        
        logger.info(f"msg,{message.from_peer},{topic},{message.message}")
    except Exception as e:
        logger.warning(f"error,Failed to decode message: {e}")

def create_test_message(peer_id: PeerID) -> UniversalConnectivityMessage:
    """Create a test message for gossipsub."""
    message = UniversalConnectivityMessage()
    message.from_peer = str(peer_id)
    message.message = f"Hello from {peer_id}!"
    message.timestamp = int(time.time())
    message.message_type = MessageType.CHAT
    return message
```

### Step 7: Main Application Logic

Implement the main application:

```python
async def run_node() -> None:
    """Run the kademlia checkpoint node."""
    try:
        # Parse environment variables
        remote_addrs = get_remote_peers() 
        bootstrap_addrs = get_bootstrap_peers()
        
        # Create host with generated key pair
        key_pair = create_new_key_pair(secrets.token_bytes(32))
        host = new_host(key_pair=key_pair)
        
        # Determine listen addresses
        listen_addrs = []
        if remote_addrs:
            # Use remote addresses as listen addresses
            listen_addrs = [Multiaddr(addr) for addr in remote_addrs]
        else:
            # Default listen address
            listen_addrs = [Multiaddr("/ip4/127.0.0.1/tcp/0")]
        
        # Start the host
        async with host.run(listen_addrs=listen_addrs), trio.open_nursery() as nursery:
            peer_id = host.get_id()
            
            # Start peer store cleanup
            nursery.start_soon(host.get_peerstore().start_cleanup_task, 60)
            
            # Connect to bootstrap nodes if provided
            if bootstrap_addrs:
                await connect_to_bootstrap_nodes(host, bootstrap_addrs)
            
            # Initialize Kademlia DHT
            dht = KadDHT(host, DHTMode.SERVER)
            
            # Add connected peers to DHT routing table
            for connected_peer in host.get_connected_peers():
                await dht.routing_table.add_peer(connected_peer)
            
            # Initialize GossipSub
            gossipsub = GossipSub(
                protocols=["/meshsub/1.0.0", "/gossipsub/1.0"],
                degree=6,
                degree_low=4,
                degree_high=12,
                heartbeat_interval=1.0,
            )
            
            # Set up gossipsub in host
            host.get_mux().set_handler("/meshsub/1.0.0", gossipsub.get_handler())
            host.get_mux().set_handler("/gossipsub/1.0", gossipsub.get_handler())
            
            # Subscribe to topics
            for topic in GOSSIPSUB_TOPICS:
                await gossipsub.subscribe(topic)
                logger.info(f"Subscribed to topic: {topic}")
            
            # Start DHT service
            async with background_trio_service(dht):
                logger.info("Kademlia DHT service started")
                
                # Bootstrap the DHT if we have bootstrap peers
                if bootstrap_addrs and host.get_connected_peers():
                    logger.info("Starting Kademlia bootstrap process")
                    try:
                        # Perform bootstrap - this will populate the routing table
                        await dht.bootstrap()
                        logger.info("bootstrap")
                    except Exception as e:
                        logger.warning(f"error,Bootstrap failed: {e}")
                
                # Handle events and keep running
                while True:
                    await trio.sleep(1)
                    
                    # Handle gossipsub messages
                    try:
                        async for msg in gossipsub.subscribe_messages():
                            await handle_gossipsub_message(
                                msg.data, 
                                msg.topic, 
                                msg.from_id
                            )
                    except Exception:
                        # No messages available
                        pass
                    
    except Exception as e:
        logger.error(f"error,{e}")
        sys.exit(1)

def main():
    """Main entry point."""
    try:
        trio.run(run_node)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"error,{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Step 8: Create the Message Protocol

Create a separate file `message_protocol.py` for your protobuf messages:

```python
"""Universal Connectivity Message Protocol."""

from enum import IntEnum

class MessageType(IntEnum):
    CHAT = 0
    FILE = 1
    BROWSER_PEER_DISCOVERY = 2

class UniversalConnectivityMessage:
    """Simple message class that mimics protobuf structure."""
    
    def __init__(self):
        self.from_peer = ""
        self.message = ""
        self.timestamp = 0
        self.message_type = MessageType.CHAT
    
    def SerializeToString(self) -> bytes:
        """Serialize message to bytes (simplified implementation)."""
        # This is a simplified serialization - in practice you'd use protobuf
        data = f"{self.from_peer}|{self.message}|{self.timestamp}|{self.message_type}"
        return data.encode('utf-8')
    
    def ParseFromString(self, data: bytes) -> None:
        """Parse message from bytes (simplified implementation)."""
        # This is a simplified deserialization - in practice you'd use protobuf
        parts = data.decode('utf-8').split('|')
        if len(parts) >= 4:
            self.from_peer = parts[0]
            self.message = parts[1]
            self.timestamp = int(parts[2])
            self.message_type = MessageType(int(parts[3]))
```

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
   python check.py
   ```

## Success Criteria

Your implementation should:
- ✅ Display connection establishment messages
- ✅ Subscribe to gossipsub topics  
- ✅ Add bootstrap peers to Kademlia
- ✅ Start the bootstrap process
- ✅ Handle peer discovery and routing events

## What's Next?

Congratulations! You've reached your fourth checkpoint 🎉

You now have a fully-featured libp2p node that can:
- Connect over multiple transports
- Exchange peer identification  
- Participate in gossipsub messaging
- Discover peers through Kademlia DHT

Key concepts you've learned:
- **Distributed Hash Tables**: Decentralized data and peer storage
- **Bootstrap Process**: Joining existing P2P networks  
- **Peer Discovery**: Finding other nodes without central coordination
- **Routing Tables**: Efficient peer organization and lookup

In the final lesson, you'll complete the Universal Connectivity application by implementing chat messaging and connecting to the real network!