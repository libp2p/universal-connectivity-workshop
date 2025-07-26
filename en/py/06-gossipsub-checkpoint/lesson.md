# Lesson 6: Gossipsub Checkpoint 🏆

Welcome to your third checkpoint! In this lesson, you'll implement Gossipsub, py-libp2p's publish-subscribe protocol for topic-based messaging in peer-to-peer networks. You'll also work with JSON serialization for structured message formats.

## Learning Objectives

By the end of this lesson, you will:
- Understand publish-subscribe messaging patterns
- Implement Gossipsub for topic-based communication
- Work with JSON serialization for structured messages
- Subscribe to and publish messages on specific topics

## Background: Gossipsub Protocol

Gossipsub is py-libp2p's scalable publish-subscribe protocol that enables:

- **Topic-Based Messaging**: Peers subscribe to topics of interest
- **Efficient Distribution**: Messages are routed efficiently through the network
- **Scalability**: Supports large numbers of peers and topics
- **Fault Tolerance**: Resilient to peer failures and network partitions

It's used in decentralized applications for efficient message dissemination, such as chat systems or blockchain networks.

## Your Task

Building on your previous py-libp2p implementation (e.g., identify protocol from Lesson 5), you need to:

1. **Add Gossipsub Support**: Integrate `GossipSub` and `Pubsub` into your libp2p host
2. **Configure Topics**: Subscribe to Universal Connectivity topics
3. **Implement JSON Messages**: Define and serialize `ChatMessage` using JSON
4. **Handle Gossipsub Events**: Process incoming messages and subscription events

## Step-by-Step Instructions

### Step 1: Set Up Dependencies

Ensure your project includes the necessary dependencies. Your `requirements.txt` should include:

```text
libp2p
trio
trio-asyncio
janus
base58
```

Install them using:

```bash
pip install -r requirements.txt
```

### Step 2: Add Imports

In your main script, include the necessary imports:

```python
import argparse
import logging
import sys
import time
import trio
from dataclasses import dataclass
from typing import Optional
import json
import base58
from libp2p import new_host
from libp2p.crypto.rsa import create_new_key_pair
from libp2p.pubsub.gossipsub import GossipSub
from libp2p.pubsub.pubsub import Pubsub
from libp2p.peer.peerinfo import info_from_p2p_addr
from libp2p.tools.async_service.trio_service import background_trio_service
import multiaddr
```

### Step 3: Define the ChatMessage Structure

Define a `ChatMessage` dataclass for JSON-serialized messages:

```python
@dataclass
class ChatMessage:
    """Represents a chat message."""
    message: str
    sender_id: str
    sender_nick: str
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps({
            "message": self.message,
            "sender_id": self.sender_id,
            "sender_nick": self.sender_nick,
            "timestamp": self.timestamp
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> "ChatMessage":
        """Create ChatMessage from JSON string."""
        data = json.loads(json_str)
        return cls(
            message=data["message"],
            sender_id=data["sender_id"],
            sender_nick=data["sender_nick"],
            timestamp=data.get("timestamp")
        )
```

### Step 4: Configure Gossipsub

Set up the `GossipSub` and `Pubsub` components:

```python
# Constants
GOSSIPSUB_PROTOCOL_ID = "/meshsub/1.0.0"
CHAT_TOPIC = "universal-connectivity"
PUBSUB_DISCOVERY_TOPIC = "universal-connectivity-browser-peer-discovery"
```

### Step 5: Subscribe to Topics

Subscribe to the necessary topics:

```python
async def subscribe_to_topics(pubsub):
    """Subscribe to all necessary topics."""
    try:
        chat_subscription = await pubsub.subscribe(CHAT_TOPIC)
        discovery_subscription = await pubsub.subscribe(PUBSUB_DISCOVERY_TOPIC)
        logger.info(f"Subscribed to topics: {CHAT_TOPIC}, {PUBSUB_DISCOVERY_TOPIC}")
        return chat_subscription, discovery_subscription
    except Exception as e:
        logger.error(f"Failed to subscribe to topics: {e}")
        raise
```

### Step 6: Handle Gossipsub Events

Handle incoming messages and subscription events:

```python
async def handle_chat_messages(subscription, nickname, peer_id):
    """Handle incoming chat messages."""
    try:
        async for message in subscription:
            try:
                # Skip our own messages
                if str(message.from_id) == peer_id:
                    continue
                    
                chat_msg = ChatMessage.from_json(message.data.decode())
                sender_short = chat_msg.sender_id[:8] if len(chat_msg.sender_id) > 8 else chat_msg.sender_id
                print(f"[{chat_msg.sender_nick}({sender_short})]: {chat_msg.message}")
            except Exception as e:
                logger.debug(f"Error processing chat message: {e}")
    except Exception as e:
        logger.info(f"Chat message handler stopped: {e}")

async def handle_discovery_messages(subscription, peer_id):
    """Handle incoming discovery messages."""
    try:
        async for message in subscription:
            try:
                if str(message.from_id) == peer_id:
                    continue
                sender_id = base58.b58encode(message.from_id).decode()
                logger.info(f"Discovery message from peer: {sender_id}")
            except Exception as e:
                logger.debug(f"Error processing discovery message: {e}")
    except Exception as e:
        logger.info(f"Discovery message handler stopped: {e}")
```

### Step 7: Publish Messages

Implement message publishing:

```python
async def publish_message(pubsub, message, nickname, peer_id):
    """Publish a chat message."""
    chat_msg = ChatMessage(
        message=message,
        sender_id=peer_id,
        sender_nick=nickname
    )
    
    try:
        # Get connected peers count from the router's mesh
        peer_count = 0
        if hasattr(pubsub.router, 'mesh') and CHAT_TOPIC in pubsub.router.mesh:
            peer_count = len(pubsub.router.mesh[CHAT_TOPIC])
        
        logger.debug(f"Publishing message to {peer_count} peers: {message}")
        await pubsub.publish(CHAT_TOPIC, chat_msg.to_json().encode())
        print(f"✓ Message sent to {peer_count} peer(s)")
    except Exception as e:
        logger.error(f"Failed to publish message: {e}")
```

### Step 8: Integrate with Main Application

Integrate everything in your main application:

```python
async def run_interactive(pubsub, nickname, peer_id, host):
    """Run interactive chat mode."""
    print(f"\n=== Universal Connectivity Chat ===")
    print(f"Nickname: {nickname}")
    print(f"Peer ID: {peer_id}")
    print(f"Type messages and press Enter to send. Type 'quit' to exit.")
    print(f"Commands: /peers, /status, /multiaddr")
    print()
    
    try:
        while True:
            try:
                message = await trio.to_thread.run_sync(input)
                if message.lower() in ["quit", "exit", "q"]:
                    print("Goodbye!")
                    break
                elif message.strip() == "/peers":
                    # Get peers from both host and pubsub
                    try:
                        host_peers = set(str(peer_id) for peer_id in host.get_network().connections.keys())
                        
                        # Get pubsub mesh peers
                        mesh_peers = set()
                        if hasattr(pubsub.router, 'mesh'):
                            for topic, peers in pubsub.router.mesh.items():
                                mesh_peers.update(str(p) for p in peers)
                        
                        all_peers = host_peers.union(mesh_peers)
                        
                        if all_peers:
                            print(f"📡 Connected peers ({len(all_peers)}):")
                            for peer in all_peers:
                                short_id = peer[:8] if len(peer) > 8 else peer
                                print(f"  - {short_id}...")
                        else:
                            print("📡 No peers connected")
                    except Exception as e:
                        logger.debug(f"Error getting peer info: {e}")
                        print("📡 Error retrieving peer information")
                    continue
                elif message.strip() == "/status":
                    try:
                        host_peers = len(host.get_network().connections)
                        
                        # Count pubsub mesh peers
                        mesh_peer_count = 0
                        if hasattr(pubsub.router, 'mesh'):
                            for topic, peers in pubsub.router.mesh.items():
                                mesh_peer_count += len(peers)
                        
                        print(f"📊 Status:")
                        print(f"  - Nickname: {nickname}")
                        print(f"  - Host connections: {host_peers}")
                        print(f"  - Pubsub mesh peers: {mesh_peer_count}")
                        print(f"  - Subscribed topics: chat, discovery")
                    except Exception as e:
                        logger.debug(f"Error getting status: {e}")
                        print("📊 Error retrieving status information")
                    continue
                elif message.strip() == "/multiaddr":
                    listen_addrs = host.get_addrs()
                    print(f"🌐 Multiaddresses:")
                    for addr in listen_addrs:
                        full_addr = f"{addr}/p2p/{peer_id}"
                        print(f"  - {full_addr}")
                    continue
                
                if message.strip():
                    await publish_message(pubsub, message, nickname, peer_id)
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break
    except Exception as e:
        logger.info(f"Interactive session ended: {e}")
        print("Session ended.")

async def connect_to_peers(host, connect_addrs):
    """Connect to specified peer addresses with retry logic."""
    for addr_str in connect_addrs:
        try:
            logger.info(f"Attempting to connect to: {addr_str}")
            maddr = multiaddr.Multiaddr(addr_str)
            info = info_from_p2p_addr(maddr)
            
            # Add some retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await host.connect(info)
                    logger.info(f"Successfully connected to: {addr_str}")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Connection attempt {attempt + 1} failed, retrying in 2s: {e}")
                        await trio.sleep(2)
                    else:
                        logger.error(f"Failed to connect after {max_retries} attempts: {e}")
                        raise
        except Exception as e:
            logger.error(f"Failed to connect to {addr_str}: {e}")
            # Don't exit, continue with other addresses
            continue

async def main_async(args):
    logger.info("Starting Universal Connectivity Python Peer...")
    
    nickname = args.nick or f"peer-{time.time():.0f}"
    port = args.port or 0
    connect_addrs = args.connect or []
    
    # Create host and pubsub components
    key_pair = create_new_key_pair()
    listen_addr = multiaddr.Multiaddr(f"/ip4/0.0.0.0/tcp/{port}")
    host = new_host(key_pair=key_pair)
    
    gossipsub = GossipSub(
        protocols=[GOSSIPSUB_PROTOCOL_ID],
        degree=3,
        degree_low=2,
        degree_high=4,
    )
    
    pubsub = Pubsub(host, gossipsub)
    peer_id = str(host.get_id())
    
    # Start the host and services
    async with host.run(listen_addrs=[listen_addr]):
        async with background_trio_service(pubsub):
            async with background_trio_service(gossipsub):
                logger.info(f"Host started, listening on: {listen_addr}")
                logger.info(f"Peer ID: {peer_id}")
                
                # Wait a moment for services to initialize
                await trio.sleep(1)
                
                # Subscribe to topics
                chat_subscription, discovery_subscription = await subscribe_to_topics(pubsub)
                
                # Connect to specified peers
                if connect_addrs:
                    await connect_to_peers(host, connect_addrs)
                    # Give some time for connections to establish
                    await trio.sleep(2)
                
                # Start all concurrent tasks
                async with trio.open_nursery() as nursery:
                    nursery.start_soon(handle_chat_messages, chat_subscription, nickname, peer_id)
                    nursery.start_soon(handle_discovery_messages, discovery_subscription, peer_id)
                    nursery.start_soon(run_interactive, pubsub, nickname, peer_id, host)
                    
                    # Handle nursery exceptions gracefully
                    try:
                        await trio.sleep_forever()
                    except KeyboardInterrupt:
                        logger.info("Received keyboard interrupt, shutting down...")
                        nursery.cancel_scope.cancel()

def main():
    parser = argparse.ArgumentParser(description="Universal Connectivity Python Peer")
    parser.add_argument("--nick", type=str, help="Nickname to use for the chat")
    parser.add_argument("-c", "--connect", action="append", help="Address to connect to", default=[])
    parser.add_argument("-p", "--port", type=int, help="Port to listen on", default=0)
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logging.getLogger("libp2p").setLevel(logging.DEBUG)
    
    try:
        trio.run(main_async, args)
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Testing Your Implementation

1. Set environment variables:

```bash
export PROJECT_ROOT=/path/to/workshop
export LESSON_PATH=py/06-gossipsub-checkpoint
```

2. Change into the lesson directory:

```bash
cd $PROJECT_ROOT/$LESSON_PATH
```

3. Run the application:

```bash
python main.py --nick testuser --port 9095
```

4. Test with a second instance in another terminal:

```bash
python main.py --nick testuser2 --port 9096 --connect /ip4/127.0.0.1/tcp/9095/p2p/<peer_id_from_first_instance>
```

5. Verify output:

- Check that both instances subscribe to `universal-connectivity` and `universal-connectivity-browser-peer-discovery`
- Send messages and confirm they are received by the other peer
- Use commands like `/peers`, `/status`, and `/multiaddr` to verify connectivity

## Success Criteria

Your implementation should:
- ✅ Display startup message and local peer ID
- ✅ Successfully connect to remote peers
- ✅ Subscribe to Universal Connectivity topics
- ✅ Send and receive JSON-serialized chat messages
- ✅ Handle peer subscription and discovery events

## Hints

- Ensure your `ChatMessage` serialization/deserialization is robust
- Use the logging system to debug subscription and message handling issues
- Check that `trio` and `trio-asyncio` are properly handling async operations
- Verify peer connections using the `/peers` command

## Hint - Complete Solution

Below is the complete working solution:

```python
import argparse
import logging
import sys
import time
import trio
from dataclasses import dataclass
from typing import Optional
import json
import base58
from libp2p import new_host
from libp2p.crypto.rsa import create_new_key_pair
from libp2p.pubsub.gossipsub import GossipSub
from libp2p.pubsub.pubsub import Pubsub
from libp2p.peer.peerinfo import info_from_p2p_addr
from libp2p.tools.async_service.trio_service import background_trio_service
import multiaddr

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("main")

GOSSIPSUB_PROTOCOL_ID = "/meshsub/1.0.0"
CHAT_TOPIC = "universal-connectivity"
PUBSUB_DISCOVERY_TOPIC = "universal-connectivity-browser-peer-discovery"

@dataclass
class ChatMessage:
    """Represents a chat message."""
    message: str
    sender_id: str
    sender_nick: str
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps({
            "message": self.message,
            "sender_id": self.sender_id,
            "sender_nick": self.sender_nick,
            "timestamp": self.timestamp
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> "ChatMessage":
        """Create ChatMessage from JSON string."""
        data = json.loads(json_str)
        return cls(
            message=data["message"],
            sender_id=data["sender_id"],
            sender_nick=data["sender_nick"],
            timestamp=data.get("timestamp")
        )

async def subscribe_to_topics(pubsub):
    """Subscribe to all necessary topics."""
    try:
        chat_subscription = await pubsub.subscribe(CHAT_TOPIC)
        discovery_subscription = await pubsub.subscribe(PUBSUB_DISCOVERY_TOPIC)
        logger.info(f"Subscribed to topics: {CHAT_TOPIC}, {PUBSUB_DISCOVERY_TOPIC}")
        return chat_subscription, discovery_subscription
    except Exception as e:
        logger.error(f"Failed to subscribe to topics: {e}")
        raise

async def publish_message(pubsub, message, nickname, peer_id):
    """Publish a chat message."""
    chat_msg = ChatMessage(
        message=message,
        sender_id=peer_id,
        sender_nick=nickname
    )
    
    try:
        # Get connected peers count from the router's mesh
        peer_count = 0
        if hasattr(pubsub.router, 'mesh') and CHAT_TOPIC in pubsub.router.mesh:
            peer_count = len(pubsub.router.mesh[CHAT_TOPIC])
        
        logger.debug(f"Publishing message to {peer_count} peers: {message}")
        await pubsub.publish(CHAT_TOPIC, chat_msg.to_json().encode())
        print(f"✓ Message sent to {peer_count} peer(s)")
    except Exception as e:
        logger.error(f"Failed to publish message: {e}")

async def handle_chat_messages(subscription, nickname, peer_id):
    """Handle incoming chat messages."""
    try:
        async for message in subscription:
            try:
                # Skip our own messages
                if str(message.from_id) == peer_id:
                    continue
                    
                chat_msg = ChatMessage.from_json(message.data.decode())
                sender_short = chat_msg.sender_id[:8] if len(chat_msg.sender_id) > 8 else chat_msg.sender_id
                print(f"[{chat_msg.sender_nick}({sender_short})]: {chat_msg.message}")
            except Exception as e:
                logger.debug(f"Error processing chat message: {e}")
    except Exception as e:
        logger.info(f"Chat message handler stopped: {e}")

async def handle_discovery_messages(subscription, peer_id):
    """Handle incoming discovery messages."""
    try:
        async for message in subscription:
            try:
                if str(message.from_id) == peer_id:
                    continue
                sender_id = base58.b58encode(message.from_id).decode()
                logger.info(f"Discovery message from peer: {sender_id}")
            except Exception as e:
                logger.debug(f"Error processing discovery message: {e}")
    except Exception as e:
        logger.info(f"Discovery message handler stopped: {e}")

async def run_interactive(pubsub, nickname, peer_id, host):
    """Run interactive chat mode."""
    print(f"\n=== Universal Connectivity Chat ===")
    print(f"Nickname: {nickname}")
    print(f"Peer ID: {peer_id}")
    print(f"Type messages and press Enter to send. Type 'quit' to exit.")
    print(f"Commands: /peers, /status, /multiaddr")
    print()
    
    try:
        while True:
            try:
                message = await trio.to_thread.run_sync(input)
                if message.lower() in ["quit", "exit", "q"]:
                    print("Goodbye!")
                    break
                elif message.strip() == "/peers":
                    # Get peers from both host and pubsub
                    try:
                        host_peers = set(str(peer_id) for peer_id in host.get_network().connections.keys())
                        
                        # Get pubsub mesh peers
                        mesh_peers = set()
                        if hasattr(pubsub.router, 'mesh'):
                            for topic, peers in pubsub.router.mesh.items():
                                mesh_peers.update(str(p) for p in peers)
                        
                        all_peers = host_peers.union(mesh_peers)
                        
                        if all_peers:
                            print(f"📡 Connected peers ({len(all_peers)}):")
                            for peer in all_peers:
                                short_id = peer[:8] if len(peer) > 8 else peer
                                print(f"  - {short_id}...")
                        else:
                            print("📡 No peers connected")
                    except Exception as e:
                        logger.debug(f"Error getting peer info: {e}")
                        print("📡 Error retrieving peer information")
                    continue
                elif message.strip() == "/status":
                    try:
                        host_peers = len(host.get_network().connections)
                        
                        # Count pubsub mesh peers
                        mesh_peer_count = 0
                        if hasattr(pubsub.router, 'mesh'):
                            for topic, peers in pubsub.router.mesh.items():
                                mesh_peer_count += len(peers)
                        
                        print(f"📊 Status:")
                        print(f"  - Nickname: {nickname}")
                        print(f"  - Host connections: {host_peers}")
                        print(f"  - Pubsub mesh peers: {mesh_peer_count}")
                        print(f"  - Subscribed topics: chat, discovery")
                    except Exception as e:
                        logger.debug(f"Error getting status: {e}")
                        print("📊 Error retrieving status information")
                    continue
                elif message.strip() == "/multiaddr":
                    listen_addrs = host.get_addrs()
                    print(f"🌐 Multiaddresses:")
                    for addr in listen_addrs:
                        full_addr = f"{addr}/p2p/{peer_id}"
                        print(f"  - {full_addr}")
                    continue
                
                if message.strip():
                    await publish_message(pubsub, message, nickname, peer_id)
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break
    except Exception as e:
        logger.info(f"Interactive session ended: {e}")
        print("Session ended.")

async def connect_to_peers(host, connect_addrs):
    """Connect to specified peer addresses with retry logic."""
    for addr_str in connect_addrs:
        try:
            logger.info(f"Attempting to connect to: {addr_str}")
            maddr = multiaddr.Multiaddr(addr_str)
            info = info_from_p2p_addr(maddr)
            
            # Add some retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await host.connect(info)
                    logger.info(f"Successfully connected to: {addr_str}")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Connection attempt {attempt + 1} failed, retrying in 2s: {e}")
                        await trio.sleep(2)
                    else:
                        logger.error(f"Failed to connect after {max_retries} attempts: {e}")
                        raise
        except Exception as e:
            logger.error(f"Failed to connect to {addr_str}: {e}")
            # Don't exit, continue with other addresses
            continue

async def main_async(args):
    logger.info("Starting Universal Connectivity Python Peer...")
    
    nickname = args.nick or f"peer-{time.time():.0f}"
    port = args.port or 0
    connect_addrs = args.connect or []
    
    # Create host and pubsub components
    key_pair = create_new_key_pair()
    listen_addr = multiaddr.Multiaddr(f"/ip4/0.0.0.0/tcp/{port}")
    host = new_host(key_pair=key_pair)
    
    gossipsub = GossipSub(
        protocols=[GOSSIPSUB_PROTOCOL_ID],
        degree=3,
        degree_low=2,
        degree_high=4,
    )
    
    pubsub = Pubsub(host, gossipsub)
    peer_id = str(host.get_id())
    
    # Start the host and services
    async with host.run(listen_addrs=[listen_addr]):
        async with background_trio_service(pubsub):
            async with background_trio_service(gossipsub):
                logger.info(f"Host started, listening on: {listen_addr}")
                logger.info(f"Peer ID: {peer_id}")
                
                # Wait a moment for services to initialize
                await trio.sleep(1)
                
                # Subscribe to topics
                chat_subscription, discovery_subscription = await subscribe_to_topics(pubsub)
                
                # Connect to specified peers
                if connect_addrs:
                    await connect_to_peers(host, connect_addrs)
                    # Give some time for connections to establish
                    await trio.sleep(2)
                
                # Start all concurrent tasks
                async with trio.open_nursery() as nursery:
                    nursery.start_soon(handle_chat_messages, chat_subscription, nickname, peer_id)
                    nursery.start_soon(handle_discovery_messages, discovery_subscription, peer_id)
                    nursery.start_soon(run_interactive, pubsub, nickname, peer_id, host)
                    
                    # Handle nursery exceptions gracefully
                    try:
                        await trio.sleep_forever()
                    except KeyboardInterrupt:
                        logger.info("Received keyboard interrupt, shutting down...")
                        nursery.cancel_scope.cancel()

def main():
    parser = argparse.ArgumentParser(description="Universal Connectivity Python Peer")
    parser.add_argument("--nick", type=str, help="Nickname to use for the chat")
    parser.add_argument("-c", "--connect", action="append", help="Address to connect to", default=[])
    parser.add_argument("-p", "--port", type=int, help="Port to listen on", default=0)
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logging.getLogger("libp2p").setLevel(logging.DEBUG)
    
    try:
        trio.run(main_async, args)
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## What's Next?

Congratulations! You've reached your third checkpoint 🎉

You now have a py-libp2p node that can:
- Communicate over multiple transports
- Exchange peer identification
- Participate in publish-subscribe messaging
- Handle JSON-serialized messages

Key concepts you've learned:
- **Publish-Subscribe**: Topic-based messaging patterns
- **Gossipsub Protocol**: Efficient message distribution in P2P networks
- **JSON Serialization**: Structured message formats
- **Topic Management**: Subscribing to and handling topic events

In the next lesson, you'll implement Kademlia DHT for distributed peer discovery and routing!