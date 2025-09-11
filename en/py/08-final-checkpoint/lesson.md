# Lesson 8: Final Checkpoint - Complete Universal Connectivity

🏆 **Final Checkpoint** - Congratulations on reaching the final lesson! You'll now bring together everything you've learned to create a complete universal connectivity application with chat messaging capabilities using py-libp2p.

## Learning Objectives

By the end of this lesson, you will:
- Integrate all py-libp2p protocols learned throughout the workshop
- Implement a complete peer-to-peer communication system in Python
- Add chat messaging functionality using Gossipsub
- Handle multiple protocols working together seamlessly
- Create a production-ready py-libp2p application

## Background: Universal Connectivity

Universal connectivity means enabling seamless communication between any two peers, regardless of their network environment, platform, or implementation. This includes:

- **Multiple Transport Support**: TCP for reliable connections
- **Peer Discovery**: Finding other peers using Kademlia DHT
- **Protocol Negotiation**: Using Identify to exchange capabilities
- **Health Monitoring**: Ping to ensure connections remain active
- **Message Passing**: Gossipsub for reliable pub/sub communication
- **Application Logic**: Chat messaging as a practical use case

## System Architecture

Your final Python application will implement this complete stack:

```
┌─────────────────────────────────────┐
│           Chat Application          │
├─────────────────────────────────────┤
│              Gossipsub              │  ← Pub/Sub messaging
├─────────────────────────────────────┤
│     Kademlia │ Identify │ Ping      │  ← Discovery, Info, Health
├─────────────────────────────────────┤
│       Noise Security + Yamux        │  ← Encryption + Multiplexing
├─────────────────────────────────────┤
│            TCP Transport            │  ← Network layer
└─────────────────────────────────────┘
```

## Your Challenge

Implement a complete py-libp2p application that:

1. **Configures Multi-Protocol Stack**: Set up TCP transport with all protocols
2. **Integrates All Protocols**: Combine Ping, Identify, Gossipsub, and Kademlia
3. **Handles Connections**: Connect to remote peers and manage connection lifecycle
4. **Implements Messaging**: Send and receive chat messages via Gossipsub
5. **Provides User Feedback**: Print meaningful status messages for all events

### Requirements Checklist

Your implementation must:
- ✅ Print "Starting Universal Connectivity Application..." on startup
- ✅ Display the local peer ID
- ✅ Connect to remote peers using the `REMOTE_PEER` environment variable or `--connect` flag
- ✅ Handle ping events with round-trip time measurement
- ✅ Process identify protocol information exchanges
- ✅ Subscribe to the "universal-connectivity" Gossipsub topic
- ✅ Send an introductory chat message when connecting to peers
- ✅ Receive and display chat messages from other peers
- ✅ Initialize Kademlia DHT for peer discovery (if bootstrap peers provided)

## Implementation Hints: chatroom.py

<details>

### 🔍 Getting Started: Module Docstring (Click to expand)
 
```python
"""
ChatRoom module for Universal Connectivity Python Peer

This module handles chat room functionality including message handling,
pubsub subscriptions, and peer discovery.
"""
```
<summary>This is the module-level docstring. It provides a high-level overview of what the module does: it manages chat room features in a peer-to-peer (P2P) system called "Universal Connectivity Python Peer." Key responsibilities include processing messages, managing subscriptions to Pub/Sub (publish-subscribe) topics, and discovering other peers on the network.</summary>

</details>

<details>

### Imports

```python
import base58
import json
import logging
import time
import trio
from dataclasses import dataclass
from typing import Set, Optional, AsyncIterator

from libp2p.host.basic_host import BasicHost
from libp2p.pubsub.pb.rpc_pb2 import Message
from libp2p.pubsub.pubsub import Pubsub
```
<summary>

These are the module's imports:
- `base58`: Used for encoding/decoding peer IDs (common in P2P systems for compact, human-readable representations).
- `json`: For serializing/deserializing messages to/from JSON format.
- `logging`: For logging events, errors, and info.
- `time`: To handle timestamps for messages.
- `trio`: An async library for concurrent I/O operations (used for asynchronous tasks like message handling).
- `dataclasses`: To define simple data classes (e.g., for messages).
- `typing`: For type hints like `Set`, `Optional`, and `AsyncIterator`.
- From `libp2p`: Imports specific classes for P2P networking. `BasicHost` represents the local peer host, `Message` is a protobuf message type for Pub/Sub, and `Pubsub` handles the publish-subscribe system.
</summary>
</details>

<details>

### Logger Setup

```python
logger = logging.getLogger("chatroom")
```
<summary>Creates a logger named "chatroom" for general logging in this module.</summary>

</details>

<details>

### System Logger Setup 

```python
# Create a separate logger for system messages
system_logger = logging.getLogger("system_messages")
system_handler = logging.FileHandler("system_messages.txt", mode='a')
system_handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S"))
system_logger.addHandler(system_handler)
system_logger.setLevel(logging.INFO)
system_logger.propagate = False
```
<summary>

This sets up a specialized logger for "system messages" (e.g., status updates, errors visible to the user). It logs to a file `system_messages.txt` in append mode (`'a'`). The formatter adds a timestamp in HH:MM:SS format. The level is set to INFO, and `propagate=False` prevents these logs from bubbling up to higher-level loggers. </summary>

</details>

<details>

### Constants 

```python
# Chat room buffer size for incoming messages
CHAT_ROOM_BUF_SIZE = 128

# Topics used in the chat system
PUBSUB_DISCOVERY_TOPIC = "universal-connectivity-browser-peer-discovery"
CHAT_TOPIC = "universal-connectivity"
```
<summary>

- `CHAT_ROOM_BUF_SIZE`: Defines a buffer size of 128 for handling incoming messages (likely for queues or streams).
- `PUBSUB_DISCOVERY_TOPIC` and `CHAT_TOPIC`: These are string constants for Pub/Sub topics. The discovery topic is for finding other peers (possibly browser-based), and the chat topic is for actual chat messages.
</summary>

</details>

<details>

### ChatMessage Dataclass 

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
<summary>

This defines a data class for chat messages:
- Fields: `message` (the text), `sender_id` (peer ID of sender), `sender_nick` (nickname), `timestamp` (optional, defaults to current time via `__post_init__`).
- `to_json`: Serializes the message to a JSON string.
- `from_json`: Class method to deserialize a JSON string back into a `ChatMessage` object.
This class is used to structure and handle messages in a consistent way, though the code also supports raw string messages for compatibility with a Go implementation.
</summary>
</details>
<details>

### ChatRoom Class Docstring and __init__

```python
class ChatRoom:
    """
    Represents a subscription to PubSub topics for chat functionality.
    Messages can be published to topics and received messages are handled
    through callback functions.
    """
    
    def __init__(self, host: BasicHost, pubsub: Pubsub, nickname: str, multiaddr: str = None):
        self.host = host
        self.pubsub = pubsub
        self.nickname = nickname
        self.peer_id = str(host.get_id())
        self.multiaddr = multiaddr or f"unknown/{self.peer_id}"
        
        # Subscriptions
        self.chat_subscription = None
        self.discovery_subscription = None
        
        # Message handlers
        self.message_handlers = []
        self.system_message_handlers = []
        
        # Running state
        self.running = False
        
        logger.info(f"ChatRoom initialized for peer {self.peer_id[:8]}... with nickname '{nickname}'")
        self._log_system_message("Universal Connectivity Chat Started")
        self._log_system_message(f"Nickname: {nickname}")
        self._log_system_message(f"Multiaddr: {self.multiaddr}")
        self._log_system_message("Commands: /quit, /peers, /status, /multiaddr")
```

<summary>

- Class docstring: Describes the class as managing Pub/Sub subscriptions for chat, with publishing and callback-based handling.
- `__init__`: Initializes the chat room with a `host` (local P2P host), `pubsub` (Pub/Sub system), `nickname`, and optional `multiaddr` (multiaddress for connecting to this peer; defaults to a placeholder).
  - Sets `peer_id` from the host.
  - Initializes subscriptions to None, empty lists for handlers, and `running=False`.
  - Logs initialization and system messages (e.g., startup info and available commands).

</summary>
</details>
<details>

### _log_system_message Method

```python
    def _log_system_message(self, message: str):
        """Log system message to file."""
        system_logger.info(message)
```
<summary>
Private method to log a system message using the specialized logger.
</summary>
</details>
<details>

### join_chat_room Class Method

```python
    @classmethod
    async def join_chat_room(cls, host: BasicHost, pubsub: Pubsub, nickname: str, multiaddr: str = None) -> "ChatRoom":
        """Create and join a chat room."""
        chat_room = cls(host, pubsub, nickname, multiaddr)
        await chat_room._subscribe_to_topics()
        chat_room._log_system_message(f"Joined chat room as '{nickname}'")
        return chat_room
```

<summary>

Async class method to create a `ChatRoom` instance, subscribe to topics, log the join, and return the instance. This is a convenience factory method for joining a chat room.
</summary>
</details>
<details>

### _subscribe_to_topics Method

```python
    async def _subscribe_to_topics(self):
        """Subscribe to all necessary topics."""
        try:
            # Subscribe to chat topic
            self.chat_subscription = await self.pubsub.subscribe(CHAT_TOPIC)
            logger.info(f"Subscribed to chat topic: {CHAT_TOPIC}")
            
            # Subscribe to discovery topic
            self.discovery_subscription = await self.pubsub.subscribe(PUBSUB_DISCOVERY_TOPIC)
            logger.info(f"Subscribed to discovery topic: {PUBSUB_DISCOVERY_TOPIC}")
            
        except Exception as e:
            logger.error(f"Failed to subscribe to topics: {e}")
            self._log_system_message(f"ERROR: Failed to subscribe to topics: {e}")
            raise
```
<summary>
Async private method to subscribe to the chat and discovery topics using the Pub/Sub system. Stores the subscriptions and logs success or failure (raising the exception after logging).
</summary>
</details>
<details>

### publish_message Method

```python
    async def publish_message(self, message: str):
        """Publish a chat message in Go-compatible format (raw string)."""
        try:
            # Check if we have any peers connected
            peer_count = len(self.pubsub.peers)
            logger.info(f"📤 Publishing message to {peer_count} peers: {message}")
            logger.info(f"Total pubsub peers: {list(self.pubsub.peers.keys())}")
            
            # Send raw message string like Go peer (compatible format)
            await self.pubsub.publish(CHAT_TOPIC, message.encode())
            logger.info(f"✅ Message published successfully to topic '{CHAT_TOPIC}'")
            
            if peer_count == 0:
                print(f"⚠️  No peers connected - message sent to topic but no one will receive it")
            else:
                print(f"✓ Message sent to {peer_count} peer(s)")
                
        except Exception as e:
            logger.error(f"❌ Failed to publish message: {e}")
            print(f"❌ Error sending message: {e}")
                
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            self._log_system_message(f"ERROR: Failed to publish message: {e}")
```
<summary>

Async method to publish a message to the chat topic. It logs the peer count, publishes the message as a raw encoded string (for compatibility with a Go version), and provides user feedback via print. Handles errors with logging and printing. Note: There's a duplicate `except` block, which might be a typo.
</summary>
</details>
<details>

### _handle_chat_messages Method

```python
    async def _handle_chat_messages(self):
        """Handle incoming chat messages in Go-compatible format."""
        logger.debug("📨 Starting chat message handler")
        
        try:
            async for message in self._message_stream(self.chat_subscription):
                try:
                    # Handle raw string messages like Go peer
                    raw_message = message.data.decode()
                    sender_id = str(message.from_id) if message.from_id else "unknown"
                    
                    logger.info(f"📨 Received message from {sender_id}: {raw_message}")
                    
                    # Skip our own messages
                    if message.from_id and str(message.from_id) == self.peer_id:
                        logger.info("📨 Ignoring own message")
                        continue
                    
                    # Create ChatMessage object for handlers
                    chat_msg = ChatMessage(
                        message=raw_message,
                        sender_id=sender_id,
                        sender_nick=sender_id[-8:] if len(sender_id) > 8 else sender_id  # Use last 8 chars like Go
                    )
                    
                    # Call message handlers
                    for handler in self.message_handlers:
                        try:
                            await handler(chat_msg)
                        except Exception as e:
                            logger.error(f"❌ Error in message handler: {e}")
                    
                    # Default console output if no handlers
                    if not self.message_handlers:
                        print(f"[{chat_msg.sender_nick}]: {chat_msg.message}")
                
                except Exception as e:
                    logger.error(f"❌ Error processing chat message: {e}")
        
        except Exception as e:
            logger.error(f"❌ Error in chat message handler: {e}")
```
<summary>

Async private method to process incoming chat messages from the subscription stream. Decodes raw messages, skips self-sent ones, creates a `ChatMessage` object (using last 8 chars of sender ID as nick for brevity, mimicking Go), calls registered handlers, and falls back to printing if no handlers are set. Logs errors at each level.
</summary>
</details>
<details>

### _handle_discovery_messages Method

```python
    async def _handle_discovery_messages(self):
        """Handle incoming discovery messages."""
        logger.debug("Starting discovery message handler")
        
        try:
            async for message in self._message_stream(self.discovery_subscription):
                try:
                    # Skip our own messages
                    if str(message.from_id) == self.peer_id:
                        continue
                    
                    # Handle discovery message (simplified - just log for now)
                    sender_id = base58.b58encode(message.from_id).decode()
                    logger.info(f"Discovery message from peer: {sender_id}")
                
                except Exception as e:
                    logger.error(f"Error processing discovery message: {e}")
        
        except Exception as e:
            logger.error(f"Error in discovery message handler: {e}")
```

<summary>

Async private method similar to `_handle_chat_messages` but for discovery topic. Skips self-messages, encodes sender ID in base58, and logs the discovery event (handling is minimal/simplified here). </summary>

</details>
<details>

### _message_stream Method

```Python
    async def _message_stream(self, subscription) -> AsyncIterator[Message]:
        """Create an async iterator for subscription messages."""
        while self.running:
            try:
                message = await subscription.get()
                yield message
            except Exception as e:
                logger.error(f"Error getting message from subscription: {e}")
                await trio.sleep(1)  # Avoid tight loop on error
```

<summary>

Async private generator to yield messages from a subscription. Loops while `running` is True, fetches messages, yields them, and handles errors with a 1-second sleep to prevent CPU spin.
</summary>
</details>
<details>

### start_message_handlers Method

```python
    async def start_message_handlers(self):
        """Start all message handler tasks."""
        self.running = True
        
        async with trio.open_nursery() as nursery:
            nursery.start_soon(self._handle_chat_messages)
            nursery.start_soon(self._handle_discovery_messages)
```
<summary>

Async method to start the chat room's message processing. Sets `running=True` and uses Trio's nursery to concurrently run the chat and discovery handlers.
</summary>
</details>
<details>

### add_message_handler and add_system_message_handler Methods 

```python
    def add_message_handler(self, handler):
        """Add a custom message handler."""
        self.message_handlers.append(handler)
    
    def add_system_message_handler(self, handler):
        """Add a custom system message handler."""
        self.system_message_handlers.append(handler)
```
<summary>
Methods to register custom async callbacks for handling chat messages or system messages. These allow extending the behavior (e.g., for UI integration).
</summary>
</details>
<details>

### run_interactive Method

```python
    async def run_interactive(self):
        """Run interactive chat mode."""
        print(f"\n=== Universal Connectivity Chat ===")
        print(f"Nickname: {self.nickname}")
        print(f"Peer ID: {self.peer_id}")
        print(f"Type messages and press Enter to send. Type 'quit' to exit.")
        print(f"Commands: /peers, /status, /multiaddr")
        print()
        
        async with trio.open_nursery() as nursery:
            # Start message handlers
            nursery.start_soon(self.start_message_handlers)
            
            # Start input handler
            nursery.start_soon(self._input_handler)
```
<summary>
Async method for an interactive console-based chat. Prints welcome/info, then uses a Trio nursery to run message handlers and an input handler concurrently.
</summary>
</details>
<details>

### _input_handler Method

```python
    async def _input_handler(self):
        """Handle user input in interactive mode."""
        try:
            while self.running:
                try:
                    # Use trio's to_thread to avoid blocking the event loop
                    message = await trio.to_thread.run_sync(input)
                    
                    if message.lower() in ["quit", "exit", "q"]:
                        print("Goodbye!")
                        self.running = False
                        break
                    
                    # Handle special commands
                    elif message.strip() == "/peers":
                        peers = self.get_connected_peers()
                        if peers:
                            print(f"📡 Connected peers ({len(peers)}):")
                            for peer in peers:
                                print(f"  - {peer[:8]}...")
                        else:
                            print("📡 No peers connected")
                        continue
                    
                    elif message.strip() == "/multiaddr":
                        print(f"\n📋 Copy this multiaddress:")
                        print(f"{self.multiaddr}")
                        print()
                        continue
                    
                    elif message.strip() == "/status":
                        peer_count = self.get_peer_count()
                        print(f"📊 Status:")
                        print(f"  - Multiaddr: {self.multiaddr}")
                        print(f"  - Nickname: {self.nickname}")
                        print(f"  - Connected peers: {peer_count}")
                        print(f"  - Subscribed topics: chat, discovery")
                        continue
                    
                    if message.strip():
                        await self.publish_message(message)
                
                except EOFError:
                    print("\nGoodbye!")
                    self.running = False
                    break
                except Exception as e:
                    logger.error(f"Error in input handler: {e}")
                    await trio.sleep(0.1)
        
        except Exception as e:
            logger.error(f"Fatal error in input handler: {e}")
            self.running = False
```
<summary>

Async private method for handling user input in interactive mode. Uses `trio.to_thread.run_sync` to run blocking `input()` without freezing the async loop. Processes commands like `/quit` (exits), `/peers` (lists peers), `/multiaddr` (shows address), `/status` (shows info). For regular messages, publishes them. Handles EOF (e.g., Ctrl+D) and errors gracefully.
<summary>
</details>
<details>

### stop Method

```python
    async def stop(self):
        """Stop the chat room."""
        self.running = False
        logger.info("ChatRoom stopped")
```
<summary> 

Async method to stop the chat room by setting `running=False` and logging the stop.

</summary>
</details>
<details>

### get_connected_peers Method
```python
    def get_connected_peers(self) -> Set[str]:
        """Get list of connected peer IDs."""
        return set(str(peer_id) for peer_id in self.pubsub.peers.keys())
```
<summary> Returns a set of connected peer IDs as strings from the Pub/Sub peers.</summary>

</details>
<details>

### get_peer_count Method
```python
    def get_peer_count(self) -> int:
        """Get number of connected peers."""
        return len(self.pubsub.peers)
```
<summary> Returns the count of connected peers from the Pub/Sub system.</summary>
</details>

<details>
<summary>🔍 Complete Solution (Click to expand if stuck)</summary>

```python
"""
ChatRoom module for Universal Connectivity Python Peer

This module handles chat room functionality including message handling,
pubsub subscriptions, and peer discovery.
"""

import base58
import json
import logging
import time
import trio
from dataclasses import dataclass
from typing import Set, Optional, AsyncIterator

from libp2p.host.basic_host import BasicHost
from libp2p.pubsub.pb.rpc_pb2 import Message
from libp2p.pubsub.pubsub import Pubsub

logger = logging.getLogger("chatroom")

# Create a separate logger for system messages
system_logger = logging.getLogger("system_messages")
system_handler = logging.FileHandler("system_messages.txt", mode='a')
system_handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S"))
system_logger.addHandler(system_handler)
system_logger.setLevel(logging.INFO)
system_logger.propagate = False  # Don't send to parent loggers

# Chat room buffer size for incoming messages
CHAT_ROOM_BUF_SIZE = 128

# Topics used in the chat system
PUBSUB_DISCOVERY_TOPIC = "universal-connectivity-browser-peer-discovery"
CHAT_TOPIC = "universal-connectivity"


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


class ChatRoom:
    """
    Represents a subscription to PubSub topics for chat functionality.
    Messages can be published to topics and received messages are handled
    through callback functions.
    """
    
    def __init__(self, host: BasicHost, pubsub: Pubsub, nickname: str, multiaddr: str = None):
        self.host = host
        self.pubsub = pubsub
        self.nickname = nickname
        self.peer_id = str(host.get_id())
        self.multiaddr = multiaddr or f"unknown/{self.peer_id}"
        
        # Subscriptions
        self.chat_subscription = None
        self.discovery_subscription = None
        
        # Message handlers
        self.message_handlers = []
        self.system_message_handlers = []
        
        # Running state
        self.running = False
        
        logger.info(f"ChatRoom initialized for peer {self.peer_id[:8]}... with nickname '{nickname}'")
        self._log_system_message("Universal Connectivity Chat Started")
        self._log_system_message(f"Nickname: {nickname}")
        self._log_system_message(f"Multiaddr: {self.multiaddr}")
        self._log_system_message("Commands: /quit, /peers, /status, /multiaddr")
    
    def _log_system_message(self, message: str):
        """Log system message to file."""
        system_logger.info(message)
    
    @classmethod
    async def join_chat_room(cls, host: BasicHost, pubsub: Pubsub, nickname: str, multiaddr: str = None) -> "ChatRoom":
        """Create and join a chat room."""
        chat_room = cls(host, pubsub, nickname, multiaddr)
        await chat_room._subscribe_to_topics()
        chat_room._log_system_message(f"Joined chat room as '{nickname}'")
        return chat_room
    
    async def _subscribe_to_topics(self):
        """Subscribe to all necessary topics."""
        try:
            # Subscribe to chat topic
            self.chat_subscription = await self.pubsub.subscribe(CHAT_TOPIC)
            logger.info(f"Subscribed to chat topic: {CHAT_TOPIC}")
            
            # Subscribe to discovery topic
            self.discovery_subscription = await self.pubsub.subscribe(PUBSUB_DISCOVERY_TOPIC)
            logger.info(f"Subscribed to discovery topic: {PUBSUB_DISCOVERY_TOPIC}")
            
        except Exception as e:
            logger.error(f"Failed to subscribe to topics: {e}")
            self._log_system_message(f"ERROR: Failed to subscribe to topics: {e}")
            raise
    
    async def publish_message(self, message: str):
        """Publish a chat message in Go-compatible format (raw string)."""
        try:
            # Check if we have any peers connected
            peer_count = len(self.pubsub.peers)
            logger.info(f"📤 Publishing message to {peer_count} peers: {message}")
            logger.info(f"Total pubsub peers: {list(self.pubsub.peers.keys())}")
            
            # Send raw message string like Go peer (compatible format)
            await self.pubsub.publish(CHAT_TOPIC, message.encode())
            logger.info(f"✅ Message published successfully to topic '{CHAT_TOPIC}'")
            
            if peer_count == 0:
                print(f"⚠️  No peers connected - message sent to topic but no one will receive it")
            else:
                print(f"✓ Message sent to {peer_count} peer(s)")
                
        except Exception as e:
            logger.error(f"❌ Failed to publish message: {e}")
            print(f"❌ Error sending message: {e}")
                
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            self._log_system_message(f"ERROR: Failed to publish message: {e}")
    
    async def _handle_chat_messages(self):
        """Handle incoming chat messages in Go-compatible format."""
        logger.debug("📨 Starting chat message handler")
        
        try:
            async for message in self._message_stream(self.chat_subscription):
                try:
                    # Handle raw string messages like Go peer
                    raw_message = message.data.decode()
                    sender_id = str(message.from_id) if message.from_id else "unknown"
                    
                    logger.info(f"📨 Received message from {sender_id}: {raw_message}")
                    
                    # Skip our own messages
                    if message.from_id and str(message.from_id) == self.peer_id:
                        logger.info("📨 Ignoring own message")
                        continue
                    
                    # Create ChatMessage object for handlers
                    chat_msg = ChatMessage(
                        message=raw_message,
                        sender_id=sender_id,
                        sender_nick=sender_id[-8:] if len(sender_id) > 8 else sender_id  # Use last 8 chars like Go
                    )
                    
                    # Call message handlers
                    for handler in self.message_handlers:
                        try:
                            await handler(chat_msg)
                        except Exception as e:
                            logger.error(f"❌ Error in message handler: {e}")
                    
                    # Default console output if no handlers
                    if not self.message_handlers:
                        print(f"[{chat_msg.sender_nick}]: {chat_msg.message}")
                
                except Exception as e:
                    logger.error(f"❌ Error processing chat message: {e}")
        
        except Exception as e:
            logger.error(f"❌ Error in chat message handler: {e}")
    
    async def _handle_discovery_messages(self):
        """Handle incoming discovery messages."""
        logger.debug("Starting discovery message handler")
        
        try:
            async for message in self._message_stream(self.discovery_subscription):
                try:
                    # Skip our own messages
                    if str(message.from_id) == self.peer_id:
                        continue
                    
                    # Handle discovery message (simplified - just log for now)
                    sender_id = base58.b58encode(message.from_id).decode()
                    logger.info(f"Discovery message from peer: {sender_id}")
                
                except Exception as e:
                    logger.error(f"Error processing discovery message: {e}")
        
        except Exception as e:
            logger.error(f"Error in discovery message handler: {e}")
    
    async def _message_stream(self, subscription) -> AsyncIterator[Message]:
        """Create an async iterator for subscription messages."""
        while self.running:
            try:
                message = await subscription.get()
                yield message
            except Exception as e:
                logger.error(f"Error getting message from subscription: {e}")
                await trio.sleep(1)  # Avoid tight loop on error
    
    async def start_message_handlers(self):
        """Start all message handler tasks."""
        self.running = True
        
        async with trio.open_nursery() as nursery:
            nursery.start_soon(self._handle_chat_messages)
            nursery.start_soon(self._handle_discovery_messages)
    
    def add_message_handler(self, handler):
        """Add a custom message handler."""
        self.message_handlers.append(handler)
    
    def add_system_message_handler(self, handler):
        """Add a custom system message handler."""
        self.system_message_handlers.append(handler)
    
    async def run_interactive(self):
        """Run interactive chat mode."""
        print(f"\n=== Universal Connectivity Chat ===")
        print(f"Nickname: {self.nickname}")
        print(f"Peer ID: {self.peer_id}")
        print(f"Type messages and press Enter to send. Type 'quit' to exit.")
        print(f"Commands: /peers, /status, /multiaddr")
        print()
        
        async with trio.open_nursery() as nursery:
            # Start message handlers
            nursery.start_soon(self.start_message_handlers)
            
            # Start input handler
            nursery.start_soon(self._input_handler)
    
    async def _input_handler(self):
        """Handle user input in interactive mode."""
        try:
            while self.running:
                try:
                    # Use trio's to_thread to avoid blocking the event loop
                    message = await trio.to_thread.run_sync(input)
                    
                    if message.lower() in ["quit", "exit", "q"]:
                        print("Goodbye!")
                        self.running = False
                        break
                    
                    # Handle special commands
                    elif message.strip() == "/peers":
                        peers = self.get_connected_peers()
                        if peers:
                            print(f"📡 Connected peers ({len(peers)}):")
                            for peer in peers:
                                print(f"  - {peer[:8]}...")
                        else:
                            print("📡 No peers connected")
                        continue
                    
                    elif message.strip() == "/multiaddr":
                        print(f"\n📋 Copy this multiaddress:")
                        print(f"{self.multiaddr}")
                        print()
                        continue
                    
                    elif message.strip() == "/status":
                        peer_count = self.get_peer_count()
                        print(f"📊 Status:")
                        print(f"  - Multiaddr: {self.multiaddr}")
                        print(f"  - Nickname: {self.nickname}")
                        print(f"  - Connected peers: {peer_count}")
                        print(f"  - Subscribed topics: chat, discovery")
                        continue
                    
                    if message.strip():
                        await self.publish_message(message)
                
                except EOFError:
                    print("\nGoodbye!")
                    self.running = False
                    break
                except Exception as e:
                    logger.error(f"Error in input handler: {e}")
                    await trio.sleep(0.1)
        
        except Exception as e:
            logger.error(f"Fatal error in input handler: {e}")
            self.running = False
    
    async def stop(self):
        """Stop the chat room."""
        self.running = False
        logger.info("ChatRoom stopped")
    
    def get_connected_peers(self) -> Set[str]:
        """Get list of connected peer IDs."""
        return set(str(peer_id) for peer_id in self.pubsub.peers.keys())
    
    def get_peer_count(self) -> int:
        """Get number of connected peers."""
        return len(self.pubsub.peers)
```

**Requirements (requirements.txt):**
```txt
libp2p>=0.4.0
trio>=0.20.0
multiaddr>=0.0.9
base58>=2.1.0
janus>=2.0.0
trio_asyncio>=0.15.0
textual>=0.79.1
```
</details>

## Testing Your Implementation

Run your application and verify it:

### Terminal 1 (Server/Bootstrap node):
```bash
python app/main.py --nick alice --ui -p 4001
```

### Terminal 2 (Client connecting to server):
```bash
python app/main.py --nick bob --ui -c /ip4/127.0.0.1/tcp/4001/p2p/<peer id>
```

Your application should:
1. Connect to the remote peer
2. Exchange ping, identify, and gossipsub messages  
3. Send and receive chat messages
4. Handle all protocols simultaneously

## Key Differences from Rust Implementation

- **Trio instead of Tokio**: py-libp2p uses trio for async concurrency
- **Service Management**: Uses `background_trio_service` for protocol lifecycle
- **Protocol APIs**: Slightly different APIs but same functionality
- **Error Handling**: Python-style exception handling vs Rust's Result types
- **Type System**: Uses dataclasses and type hints for structure

## Next Steps

🎉 **Congratulations!** You've built a complete universal connectivity application using py-libp2p!

You now understand:
- Multi-protocol networking with py-libp2p
- Async service management with trio
- Peer discovery with Kademlia DHT
- Protocol negotiation with Identify
- Health monitoring with Ping  
- Pub/sub messaging with Gossipsub
- Real-world Python libp2p integration

Consider exploring:
- **Interactive Chat**: Adding user input for real-time messaging
- **File Sharing**: Implementing file transfer protocols
- **Custom Protocols**: Building your own py-libp2p protocols  
- **Network Optimization**: Tuning performance for your use case
- **Browser Integration**: Connecting with browser-based peers
- **Production Deployment**: Scaling to handle many peers

The Universal Connectivity Workshop has given you the foundation to build any peer-to-peer application in Python that you can imagine!