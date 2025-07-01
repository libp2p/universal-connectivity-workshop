# Lesson 2: Transport Layer - TCP Connection

Building on your basic py-libp2p node, in this lesson you'll learn about transport layers and establish your first peer-to-peer connections using TCP with Noise and Yamux multiplexing.

## Learning Objectives

By the end of this lesson, you will:
- Understand py-libp2p's transport abstraction
- Configure TCP transport with security and multiplexing
- Establish a connection to a remote peer
- Handle connection events properly

## Background: Transport Layers in py-libp2p

In py-libp2p, **transports** handle the low-level network communication. A transport defines how data travels between peers. py-libp2p supports multiple transports:

- **TCP**: Reliable, ordered, connection-oriented (like HTTP)
- **Memory**: For testing and local communication

Each transport can be enhanced with:
- **Security protocols**: Encrypt communication (e.g. Noise, SecIO)
- **Multiplexers**: Share one connection for multiple streams (Yamux, Mplex)

## Transport Stack

The py-libp2p stack looks like the following when using TCP, Noise, and Yamux:

```
Application protocols (ping, pubsub, etc.)
    ↕
Multiplexer (Yamux)
    ↕
Security (Noise)
    ↕
Transport (TCP)
    ↕
Network (IP)
```

## Your Task

Extend your application to:
1. Parse remote peer addresses from an environment variable
2. Establish a connection to a remote peer
3. Print connection events for verification
4. Handle connection lifecycle properly

## Step-by-Step Instructions

### Step 1: Add Required Imports

In your `main.py`, ensure you have the necessary imports. You must import `Multiaddr` for handling addresses and connection event handling capabilities:

```python
import asyncio
import logging
import os
from typing import List

from libp2p import new_host
from libp2p.network.connection.swarm_connection import SwarmConnection
from libp2p.peer.peerinfo import info_from_p2p_addr
from multiaddr import Multiaddr

# Set up logging to see connection events
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### Step 2: Parse Multiaddrs from Environment Variable

In this workshop, one or more `Multiaddr` strings for remote peers is passed in the environment variable `REMOTE_PEERS`. A `Multiaddr` string looks like: `/ip4/172.16.16.17/tcp/9092`.

Add the following code to your `main` function to parse the remote peer addresses:

```python
async def main():
    print("Starting Universal Connectivity application...")
    
    # Parse remote peer addresses from environment variable
    remote_addrs: List[Multiaddr] = []
    remote_peers_env = os.getenv("REMOTE_PEERS", "")
    
    if remote_peers_env:
        remote_addrs = [
            Multiaddr(addr.strip()) 
            for addr in remote_peers_env.split(',') 
            if addr.strip()
        ]
    
    # ... rest of the code will go here ...
```

### Step 3: Create the Host and Set Up Connection Handling

Create your py-libp2p host and set up connection event handlers:

```python
async def main():
    print("Starting Universal Connectivity application...")
    
    # Parse remote peer addresses from environment variable
    remote_addrs: List[Multiaddr] = []
    remote_peers_env = os.getenv("REMOTE_PEERS", "")
    
    if remote_peers_env:
        remote_addrs = [
            Multiaddr(addr.strip()) 
            for addr in remote_peers_env.split(',') 
            if addr.strip()
        ]
    
    # Create the libp2p host
    host = new_host()
    
    print(f"Local peer id: {host.get_id()}")
    
    # Set up connection event handlers
    def connection_handler(connection: SwarmConnection) -> None:
        """Handle new connections"""
        peer_id = connection.muxed_conn.peer_id
        remote_addr = connection.muxed_conn.conn.writer.get_extra_info('peername')
        print(f"Connected to: {peer_id} via {remote_addr}")
    
    def disconnection_handler(peer_id) -> None:
        """Handle disconnections"""
        print(f"Connection to {peer_id} closed gracefully")
    
    # Register the handlers
    host.get_network().set_new_connection_handler(connection_handler)
    # Note: py-libp2p doesn't have a direct disconnection handler, 
    # we'll handle this in our connection loop
```

### Step 4: Connect to Remote Peers

Add code to dial the remote peer addresses:

```python
async def main():
    print("Starting Universal Connectivity application...")
    
    # Parse remote peer addresses from environment variable  
    remote_addrs: List[Multiaddr] = []
    remote_peers_env = os.getenv("REMOTE_PEERS", "")
    
    if remote_addrs_env:
        remote_addrs = [
            Multiaddr(addr.strip()) 
            for addr in remote_peers_env.split(',') 
            if addr.strip()
        ]
    
    # Create the libp2p host
    host = new_host()
    
    print(f"Local peer id: {host.get_id()}")
    
    # Connect to all remote peers
    for addr in remote_addrs:
        try:
            # Extract peer info from multiaddr
            peer_info = info_from_p2p_addr(addr)
            
            # Connect to the peer
            await host.connect(peer_info)
            print(f"Successfully connected to peer at {addr}")
            
        except Exception as e:
            print(f"Failed to connect to {addr}: {e}")
    
    # Keep the program running to maintain connections
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        await host.close()
```

### Step 5: Enhanced Connection Management

For better connection lifecycle management, let's improve our implementation:

```python
import asyncio
import logging
import os
from typing import List, Dict

from libp2p import new_host
from libp2p.peer.peerinfo import info_from_p2p_addr
from libp2p.peer.id import ID
from multiaddr import Multiaddr

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[ID, bool] = {}
    
    def on_connection_established(self, peer_id: ID, remote_addr: str):
        """Handle new connection establishment"""
        self.active_connections[peer_id] = True
        print(f"Connected to: {peer_id} via {remote_addr}")
    
    def on_connection_closed(self, peer_id: ID):
        """Handle connection closure"""
        if peer_id in self.active_connections:
            del self.active_connections[peer_id]
        print(f"Connection to {peer_id} closed gracefully")

async def main():
    print("Starting Universal Connectivity application...")
    
    # Parse remote peer addresses
    remote_addrs: List[Multiaddr] = []
    remote_peers_env = os.getenv("REMOTE_PEERS", "")
    
    if remote_peers_env:
        remote_addrs = [
            Multiaddr(addr.strip()) 
            for addr in remote_peers_env.split(',') 
            if addr.strip()
        ]
    
    # Create host and connection manager
    host = new_host()
    conn_manager = ConnectionManager()
    
    print(f"Local peer id: {host.get_id()}")
    
    # Connect to remote peers
    connected_peers = []
    for addr in remote_addrs:
        try:
            peer_info = info_from_p2p_addr(addr)
            await host.connect(peer_info)
            conn_manager.on_connection_established(peer_info.peer_id, str(addr))
            connected_peers.append(peer_info.peer_id)
            
        except Exception as e:
            print(f"Failed to connect to {addr}: {e}")
    
    # Monitor connections
    try:
        while connected_peers:
            await asyncio.sleep(1)
            
            # Check if connections are still active
            current_peers = list(host.get_network().connections.keys())
            disconnected = [p for p in connected_peers if p not in current_peers]
            
            for peer_id in disconnected:
                conn_manager.on_connection_closed(peer_id)
                connected_peers.remove(peer_id)
                
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        await host.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Testing Your Implementation

If you are using the workshop tool, hit the `c` key to check your solution. The checker will validate that your peer successfully connects to a remote peer and handles connection events properly.

For manual testing:

1. Set environment variables:
   ```bash
   export PROJECT_ROOT=/path/to/workshop
   export LESSON_PATH=py/02-tcp-transport
   ```

   For windowa
   ```cmd
   $env:LESSON_PATH = "py/02-tcp-transport"
   $env:PROJECT_ROOT = "."
   ```

2. Run with Docker Compose:
   ```bash
   docker rm -f workshop-lesson ucw-checker-02-tcp-transport
   docker network rm -f workshop-net
   docker network create --driver bridge --subnet 172.16.16.0/24 workshop-net
   docker compose --project-name workshop up --build --remove-orphans
   ```

3. Check your output:
   ```bash
   python check.py
   ```

## Success Criteria

Your implementation should:
- ✅ Display the startup message and local peer ID
- ✅ Successfully parse remote peer addresses from the environment variable
- ✅ Successfully connect to the remote peer
- ✅ Print connection establishment messages
- ✅ Handle connection closure gracefully

## Hints

### Hint - Common Issues

**Problem**: "ModuleNotFoundError: No module named 'libp2p'"
**Solution**: Make sure py-libp2p is installed: `pip install libp2p`

**Problem**: Connection fails with "Connection refused"
**Solution**: Ensure the remote peer is running and the address is correct.

**Problem**: Program exits immediately
**Solution**: Add the event loop to keep the program running after connections.

### Hint - Complete Solution

Here's the complete working solution:

```python
import asyncio
import logging
import os
from typing import List

from libp2p import new_host
from libp2p.peer.peerinfo import info_from_p2p_addr
from multiaddr import Multiaddr

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    print("Starting Universal Connectivity application...")
    
    # Parse remote peer addresses from environment variable
    remote_addrs: List[Multiaddr] = []
    remote_peers_env = os.getenv("REMOTE_PEERS", "")
    
    if remote_peers_env:
        remote_addrs = [
            Multiaddr(addr.strip()) 
            for addr in remote_peers_env.split(',') 
            if addr.strip()
        ]
    
    # Create the libp2p host
    host = new_host()
    
    print(f"Local peer id: {host.get_id()}")
    
    # Connect to all remote peers
    connected_peers = []
    for addr in remote_addrs:
        try:
            # Extract peer info from multiaddr
            peer_info = info_from_p2p_addr(addr)
            
            # Connect to the peer
            await host.connect(peer_info)
            print(f"Connected to: {peer_info.peer_id} via {addr}")
            connected_peers.append(peer_info.peer_id)
            
        except Exception as e:
            print(f"Failed to connect to {addr}: {e}")
    
    # Monitor connections and handle closures
    try:
        while connected_peers:
            await asyncio.sleep(1)
            
            # Check connection status
            current_peers = list(host.get_network().connections.keys())
            disconnected = [p for p in connected_peers if p not in current_peers]
            
            for peer_id in disconnected:
                print(f"Connection to {peer_id} closed gracefully")
                connected_peers.remove(peer_id)
                
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        await host.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## What's Next?

Excellent! You've successfully configured TCP transport and established peer-to-peer connections using py-libp2p. You now understand:

- **Transport Layer**: How py-libp2p handles network communication
- **Security**: Noise protocol for encrypted connections  
- **Connection Management**: Establishing and monitoring connections
- **Event-Driven Programming**: Responding to network events
- **Async Programming**: Managing asynchronous operations in Python

In the next lesson, you'll add your first protocol (ping) and connect to the instructor's server for your first checkpoint!

Key concepts you've learned:
- **py-libp2p Host Creation**: Setting up the networking stack
- **Connection Events**: Establishment and closure handling
- **Multiaddresses**: libp2p's addressing format
- **Async Patterns**: Python async/await for network operations

Next up: Adding the ping protocol and achieving your first checkpoint!