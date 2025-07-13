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

- **Security protocols**: Encrypt communication (e.g., Noise)
- **Multiplexers**: Share one connection for multiple streams (e.g., Yamux)

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
2. Set up a listener for incoming connections
3. Establish a connection to a remote peer
4. Print connection events for verification
5. Handle connection lifecycle properly

## Step-by-Step Instructions

### Step 1: Set Up Your Environment

Ensure you have **py-libp2p** installed:

```bash
pip install libp2p
```

### Step 2: Create the Main Application

Create a file named `main.py` in app folder with the following code to set up a libp2p host, listen for incoming connections, and connect to remote peers.

```python
import trio
import logging
import os
from typing import List

from libp2p import new_host
from libp2p.peer.peerinfo import info_from_p2p_addr
from multiaddr import Multiaddr

# Set up logging
logging.basicConfig(level=logging.DEBUG)
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
    
    # Set up listening address with configurable port
    listen_port = os.getenv("LISTEN_PORT", "9000")
    listen_addr = Multiaddr(f"/ip4/0.0.0.0/tcp/{listen_port}")
    
    # Create the libp2p host
    host = new_host()
    
    print(f"Local peer id: {host.get_id()}")
    
    # Start the host and begin listening for connections
    async with host.run(listen_addrs=[listen_addr]):
        # Print our listening addresses
        addrs = host.get_addrs()
        for addr in addrs:
            print(f"Listening on: {addr}")
        
        # Connect to all remote peers if any specified
        connected_peers = []
        for addr in remote_addrs:
            try:
                # Validate that the multiaddress contains /p2p
                if not addr.get("p2p"):
                    print(f"Invalid multiaddress {addr}: Missing /p2p/<peer_id>")
                    continue
                
                # Extract peer info from multiaddr
                peer_info = info_from_p2p_addr(addr)
                
                # Connect to the peer
                print(f"Attempting to connect to {peer_info.peer_id} at {addr}")
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

### Script explanation

This Python script is like a friendly greeter setting up a simple peer-to-peer (P2P) network node using the `libp2p` library. It’s designed to start a host, listen for connections, connect to other peers if you tell it to, and keep an eye on those connections, all while logging what’s going on. Think of it as your computer opening a lemonade stand, ready to chat with other stands in the neighborhood and keep the conversation going until you say stop.

The script kicks off with a cheerful “Starting Universal Connectivity application...” message, letting you know it’s ready to roll. It first checks if you’ve provided any remote peers to connect to by looking at the REMOTE_PEERS environment variable (like a list of friends’ addresses). If you’ve given it some addresses (in a special format called multiaddresses), it cleans them up and stores them in a list. For example, these addresses might look like `/ip4/127.0.0.1/tcp/8000/p2p/QmPeer...,` and it makes sure they’re valid by stripping out any extra spaces.

Next, it sets up where your node will listen for incoming connections. It grabs a port number from the LISTEN_PORT environment variable (defaulting to 9000 if you don’t specify one) and creates a multiaddress like `/ip4/0.0.0.0/tcp/9000,` which means “listen on all network interfaces at this port.” Then it creates a libp2p host, which is like your node’s control center, and prints out its unique ID (like a name tag) so you know who you are in the network.

The host starts running and begins listening on the specified address. It shows you all the addresses it’s listening on (there might be a few, depending on your network setup). If you provided any remote peers, it tries to connect to each one. For each address, it checks if it includes a peer ID (the /p2p part), and if not, it skips it with a warning. If the address is good, it extracts the peer’s info, attempts to connect, and if successful, adds the peer’s ID to a list of connected peers and prints a happy “Connected!” message. If something goes wrong (like the peer’s offline), it just prints an error and moves on.

Once all connections are set up, the script enters a loop where it waits for new incoming connections and keeps the app running. Every second, it checks if any of your connected peers have dropped off (like if they closed their lemonade stand). If a peer disconnects, it lets you know and removes them from the list. The app keeps humming along until you hit `Ctrl+C`, at which point it says “Shutting down...” and gracefully exits. The whole thing is like a friendly network hub that stays online, chats with peers, and keeps you posted on who’s around, all while being ready to shut down when you’re done.

### Step 3: Test Your Implementation

#### Manual Testing

1. **Run Node 1 (Server)**:

   - In the first terminal, set the listening port and run the program without `REMOTE_PEERS` to act as the server:

     ```powershell
     $env:LISTEN_PORT = "9000"
     $env:REMOTE_PEERS = $null
     python app/main.py
     ```

   - Note the peer ID and listening address, e.g., `/ip4/0.0.0.0/tcp/9000/p2p/QmRBWnrT7wP2w8JGe3YprMxjPxMvgXFtT1LLNE5JbGFNn9`.

2. **Run Node 2 (Client)**:

   - In the second terminal, set the listening port to a different value (to avoid conflicts) and set `REMOTE_PEERS` to connect to Node 1:

     ```powershell
     $env:LISTEN_PORT = "9001"
     $env:REMOTE_PEERS = "/ip4/127.0.0.1/tcp/9000/p2p/QmRBWnrT7wP2w8JGe3YprMxjPxMvgXFtT1LLNE5JbGFNn9"
     python app/main.py
     ```

   - Replace the peer ID with the actual peer ID from Node 1’s output.

3. **Verify Output**:

   - Node 1 should print its peer ID, listening address, and indicate it’s waiting for connections.
   - Node 2 should print its peer ID, listening address, and confirm a successful connection to Node 1, e.g., `Connected to: QmRBWnrT7wP2w8JGe3YprMxjPxMvgXFtT1LLNE5JbGFNn9 via /ip4/127.0.0.1/tcp/9000/p2p/QmRBWnrT7wP2w8JGe3YprMxjPxMvgXFtT1LLNE5JbGFNn9`.

#### Testing with Docker

To test your solution using Docker, you need to set up a network and run both the student’s application and the checker. The checker (`check.py`) expects specific output in `checker.log`, which is generated by `checker/main.py`.

1. **Create a Docker Network**:

   - Create a bridge network with a specific subnet to match the checker’s expected IP range:

     ```bash
     docker network rm workshop-net
     docker network create --driver bridge --subnet 172.16.16.0/24 workshop-net
     ```

2. **Run Docker Compose**:

   - Ensure the `REMOTE_PEERS` environment variable in `docker-compose.yaml` includes the correct peer ID of the `lesson` container. You can find this by running the `lesson` service first and noting its peer ID from the output.

   - Remove any existing containers and network to avoid conflicts:

    ```bash
    docker rm -f workshop-lesson workshop-checker
    docker network rm workshop-net
    ```

   - Run the containers:

     ```bash
     docker compose --project-name workshop up --build --remove-orphans
     ```

   - Note: You may need to update the `REMOTE_PEERS` peer ID in `docker-compose.yml` after the `lesson` container starts. Alternatively, use a dynamic peer ID retrieval script (advanced) or run the checker manually after noting the peer ID.

3. **Check the Output**:

   - After running, check the `checker.log` file for output and run:

     ```bash
     python check.py
     ```

   - The checker validates that:

     - The application starts and displays the peer ID.
     - It listens on a valid multiaddress (e.g., `/ip4/0.0.0.0/tcp/9000/p2p/<peer_id>`).
     - It connects to the remote peer (`/ip4/172.16.16.17/tcp/9092/p2p/<checker_peer_id>`).
     - It prints connection establishment and closure messages.

### Step 4: Success Criteria

Your implementation should:

- ✅ Display the startup message and local peer ID
- ✅ Successfully parse remote peer addresses from the environment variable
- ✅ Listen on a TCP port (e.g., 9000)
- ✅ Successfully connect to the remote peer
- ✅ Print connection establishment messages
- ✅ Handle connection closure gracefully

### Step 5: Hints

#### Common Issues

**Problem**: "ModuleNotFoundError: No module named 'libp2p'" **Solution**: Ensure py-libp2p is installed:

```bash
pip install libp2p
```

**Problem**: Connection fails with "Connection refused" **Solution**: Ensure the remote peer is running, the address is correct (includes `/p2p/<peer_id>`), and the port is open (e.g., check firewall settings).

**Problem**: Port conflict when running multiple nodes **Solution**: Use different `LISTEN_PORT` values for each node (e.g., `9000` for Node 1, `9001` for Node 2).

**Problem**: Program exits immediately **Solution**: The code includes an event loop (`while True: await trio.sleep(1)`) to keep the program running.

**Problem**: Checker fails with "No connection established" **Solution**: Ensure the `REMOTE_PEERS` multiaddress includes the correct peer ID and uses `127.0.0.1` for local testing or the correct IP for Docker/network testing.

## What's Next?

Excellent! You've successfully configured TCP transport and established peer-to-peer connections using py-libp2p. You now understand:

- **Transport Layer**: How py-libp2p handles network communication
- **Security**: Noise protocol for encrypted connections
- **Multiplexing**: Yamux for stream multiplexing
- **Connection Management**: Establishing and monitoring connections
- **Async Programming**: Managing asynchronous operations in Python

In the next lesson, you'll add your first protocol (ping) and connect to the instructor's server for your first checkpoint!

Key concepts you've learned:

- **py-libp2p Host Creation**: Setting up the networking stack
- **Listening and Connecting**: Managing incoming and outgoing connections
- **Multiaddresses**: libp2p's addressing format
- **Connection Events**: Handling establishment and closure

Next up: Adding the ping protocol and achieving your first checkpoint!