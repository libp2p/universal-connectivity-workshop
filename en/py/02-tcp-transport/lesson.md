# Lesson 2: Transport Layer - TCP Connection

Building on your basic py-libp2p node, in this lesson you'll learn about transport layers and establish your first peer-to-peer connections using TCP with security and multiplexing.

## Learning Objectives

By the end of this lesson, you will:
- Understand py-libp2p's transport abstraction
- Configure TCP transport with security and multiplexing
- Set up a TCP listener to accept incoming connections
- Establish connections to remote peers
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

Create an application that:
1. **Sets up a TCP listener** to accept incoming connections (crucial for checker)
2. Parse remote peer addresses from environment variables
3. Establish connections to remote peers if specified
4. Print connection events for verification
5. Keep the listener running to maintain connections

## Key Implementation Points

### 1. Setting Up the TCP Listener

The most important part is creating a listener that accepts incoming connections:

```python
# Set up listening address
listen_addr = Multiaddr("/ip4/0.0.0.0/tcp/0")  # Let system choose port

# Create host
host = new_host()

# Start listening (this creates the TCP listener)
async with host.run(listen_addrs=[listen_addr]):
    # Your application logic here
    pass
```

### 2. Why the Listener is Critical

The checker needs to **connect TO your application**. Without a listener:
- ✗ Your app can only dial out to other peers
- ✗ No incoming connections are accepted
- ✗ Checker times out trying to connect

With a listener:
- ✅ Your app accepts incoming connections
- ✅ Checker can successfully connect
- ✅ Connection events are properly handled

### 3. Complete Working Implementation

```python
import trio
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
    
    # Set up listening address - this is crucial for accepting incoming connections
    listen_addr = Multiaddr("/ip4/0.0.0.0/tcp/0")  # Let system choose port
    
    # Create the libp2p host
    host = new_host()
    
    print(f"Local peer id: {host.get_id()}")
    
    # Start the host and begin listening for connections
    async with host.run(listen_addrs=[listen_addr]):
        # Print our listening addresses so checker can find us
        addrs = host.get_addrs()
        for addr in addrs:
            print(f"Listening on: {addr}")
        
        # Connect to all remote peers if any specified
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
        
        # Keep the program running to maintain connections and accept new ones
        try:
            print("Waiting for incoming connections...")
            while True:
                await trio.sleep(1)
                
                # Check connection status for outbound connections
                if connected_peers:
                    current_peers = list(host.get_network().connections.keys())
                    disconnected = [p for p in connected_peers if p not in current_peers]
                    
                    for peer_id in disconnected:
                        print(f"Connection to {peer_id} closed gracefully")
                        connected_peers.remove(peer_id)
        
        except KeyboardInterrupt:
            print("Shutting down...")

if __name__ == "__main__":
    trio.run(main)
```

## Testing Your Implementation

### With Docker Compose

```bash
docker compose --project-name workshop up --build --remove-orphans
```

### Manual Testing

```bash
python main.py
```

You should see output like:
```
Starting Universal Connectivity application...
Local peer id: 12D3KooW...
Listening on: /ip4/127.0.0.1/tcp/54321/p2p/12D3KooW...
Listening on: /ip4/192.168.1.100/tcp/54321/p2p/12D3KooW...
Waiting for incoming connections...
```

### Check Your Solution

```bash
python check.py
```

## Success Criteria

Your implementation should:
- ✅ Display the startup message and local peer ID
- ✅ Set up TCP listener on available port
- ✅ Print listening addresses
- ✅ Accept incoming connections (what the checker tests)
- ✅ Parse and connect to remote peers if specified
- ✅ Handle connection lifecycle properly
- ✅ Keep running to maintain connections

## Common Issues and Solutions

### "No incoming connection listener setup detected"
**Problem**: Your app isn't listening for incoming connections
**Solution**: Use `host.run(listen_addrs=[listen_addr])` to start the TCP listener

### "Connection refused" 
**Problem**: The listener isn't properly configured
**Solution**: Ensure you're using `0.0.0.0` to listen on all interfaces

### "Program exits immediately"
**Problem**: No event loop to keep the program running
**Solution**: Add the `while True: await trio.sleep(1)` loop

### TypeError about listen_addrs
**Problem**: Passing `listen_addrs` to `new_host()` instead of `host.run()`
**Solution**: Pass `listen_addrs` only to the `host.run()` method

## Key Concepts Learned

- **TCP Transport**: How py-libp2p handles network communication
- **Listeners vs Dialers**: Accepting incoming vs making outgoing connections
- **Multiaddresses**: libp2p's standardized addressing format
- **Async Context Managers**: Using `async with` for resource management
- **Connection Lifecycle**: Establishment, maintenance, and cleanup
- **Event-Driven Programming**: Responding to network events

## What's Next?

Excellent! You've successfully configured TCP transport and can both accept incoming connections and establish outgoing connections. You now understand the fundamental networking layer of libp2p.

In the next lesson, you'll add your first application protocol (ping) and learn about stream handling and protocol negotiation!