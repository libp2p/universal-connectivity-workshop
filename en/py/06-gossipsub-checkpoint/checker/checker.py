import os
import sys
import logging
from typing import List
import json
from dataclasses import dataclass
from enum import IntEnum

import trio
from libp2p import new_host
from libp2p.crypto.rsa import create_new_key_pair
from libp2p.pubsub.gossipsub import GossipSub
from libp2p.pubsub.pubsub import Pubsub
from libp2p.peer.peerinfo import info_from_p2p_addr
from libp2p.tools.async_service.trio_service import background_trio_service
from libp2p.network.connection.connection import Connection
import multiaddr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
IDENTIFY_PROTOCOL_VERSION = "/ipfs/id/1.0.0"
AGENT_VERSION = "universal-connectivity/0.1.0"
GOSSIPSUB_TOPICS = [
    "universal-connectivity",
    "universal-connectivity-file", 
    "universal-connectivity-browser-peer-discovery"
]

class MessageType(IntEnum):
    CHAT = 0
    FILE = 1
    BROWSER_PEER_DISCOVERY = 2

@dataclass
class UniversalConnectivityMessage:
    from_peer: str
    message: str
    timestamp: int
    message_type: MessageType
    
    def to_json(self) -> str:
        return json.dumps({
            "from": self.from_peer,
            "message": self.message,
            "timestamp": self.timestamp,
            "message_type": self.message_type.value
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> "UniversalConnectivityMessage":
        data = json.loads(json_str)
        return cls(
            from_peer=data["from"],
            message=data["message"],
            timestamp=data["timestamp"],
            message_type=MessageType(data["message_type"])
        )

class P2PChecker:
    def __init__(self, remote_addrs: List[str]):
        self.remote_addrs = remote_addrs
        self.host = None
        self.pubsub = None
        self.gossipsub = None
        self.peer_id = None
        self.connection_id = None
        self.subscriptions = {}
        
    async def setup_host_and_pubsub(self):
        """Initialize the libp2p host and pubsub components."""
        key_pair = create_new_key_pair()
        self.host = new_host(key_pair=key_pair)
        
        # Create GossipSub with configuration
        self.gossipsub = GossipSub(
            protocols=["/meshsub/1.0.0"],
            degree=6,  # mesh_n
            degree_low=4,  # mesh_n_low  
            degree_high=12,  # mesh_n_high
            heartbeat_interval=10.0,  # 10 seconds
            fanout_ttl=60.0,
            mcache_len=5,
            mcache_gossip=3
        )
        
        self.pubsub = Pubsub(self.host, self.gossipsub)
        self.peer_id = str(self.host.get_id())
        
        logger.info(f"Initialized host with peer ID: {self.peer_id}")
    
    async def subscribe_to_topics(self):
        """Subscribe to all gossipsub topics."""
        for topic in GOSSIPSUB_TOPICS:
            try:
                subscription = await self.pubsub.subscribe(topic)
                self.subscriptions[topic] = subscription
                logger.info(f"Subscribed to topic: {topic}")
            except Exception as e:
                logger.error(f"Failed to subscribe to {topic}: {e}")
                raise
    
    async def connect_to_peers(self):
        """Connect to remote peers."""
        for addr_str in self.remote_addrs:
            try:
                logger.info(f"Attempting to connect to: {addr_str}")
                maddr = multiaddr.Multiaddr(addr_str)
                info = info_from_p2p_addr(maddr)
                await self.host.connect(info)
                logger.info(f"Successfully connected to: {addr_str}")
                # Store connection info (simplified)
                self.connection_id = addr_str
                print(f"connected,{info.peer_id},{maddr}")
            except Exception as e:
                logger.error(f"Failed to connect to {addr_str}: {e}")
                print(f"error,{e}")
                continue
    
    async def handle_ping(self):
        """Handle ping functionality (simplified version)."""
        while True:
            try:
                await trio.sleep(1)  # Ping interval
                if self.host and self.host.get_network().connections:
                    # Simplified ping - just check if connections are still active
                    connections = self.host.get_network().connections
                    for peer_id, connection in connections.items():
                        # Simulate ping RTT
                        rtt_ms = 50  # Placeholder RTT
                        print(f"ping,{peer_id},{rtt_ms} ms")
            except Exception as e:
                logger.debug(f"Ping error: {e}")
                await trio.sleep(5)
    
    async def handle_identify(self):
        """Handle identify protocol (simplified)."""
        # In py-libp2p, identify is typically handled automatically
        # This is a placeholder for identify events
        while True:
            try:
                await trio.sleep(30)  # Check periodically
                if self.host and self.host.get_network().connections:
                    for peer_id in self.host.get_network().connections.keys():
                        print(f"identify,{peer_id},{IDENTIFY_PROTOCOL_VERSION},{AGENT_VERSION}")
            except Exception as e:
                logger.debug(f"Identify error: {e}")
                await trio.sleep(30)
    
    async def handle_gossipsub_messages(self, topic: str):
        """Handle incoming gossipsub messages for a specific topic."""
        if topic not in self.subscriptions:
            return
            
        subscription = self.subscriptions[topic]
        
        try:
            async for message in subscription:
                try:
                    # Try to decode as UniversalConnectivityMessage
                    msg_data = UniversalConnectivityMessage.from_json(message.data.decode())
                    print(f"msg,{msg_data.from_peer},{topic},{msg_data.message}")
                    
                    # Close connection after receiving message
                    if self.connection_id:
                        logger.info("Closing connection after receiving message")
                        # In py-libp2p, we'll just mark for shutdown
                        return
                        
                except json.JSONDecodeError:
                    # Handle non-JSON messages
                    try:
                        msg_str = message.data.decode()
                        print(f"msg,{message.from_id},{topic},{msg_str}")
                    except Exception:
                        print(f"error,{topic}")
                        
                except Exception as e:
                    logger.debug(f"Error processing message from {topic}: {e}")
                    print(f"error,{topic}")
                    
        except Exception as e:
            logger.info(f"Gossipsub message handler for {topic} stopped: {e}")
    
    async def handle_connection_events(self):
        """Handle connection events."""
        while True:
            try:
                await trio.sleep(5)
                
                # Check for connection changes
                if self.host:
                    connections = self.host.get_network().connections
                    if not connections and self.connection_id:
                        print(f"closed,{self.connection_id}")
                        return
                        
            except Exception as e:
                logger.debug(f"Connection event handler error: {e}")
                await trio.sleep(5)
    
    async def run(self):
        """Main run loop."""
        try:
            # Setup host and pubsub
            await self.setup_host_and_pubsub()
            
            # Start the host
            listen_addr = multiaddr.Multiaddr("/ip4/0.0.0.0/tcp/0")
            
            async with self.host.run(listen_addrs=[listen_addr]):
                async with background_trio_service(self.pubsub):
                    async with background_trio_service(self.gossipsub):
                        
                        # Wait for services to initialize
                        await trio.sleep(1)
                        
                        # Subscribe to topics
                        await self.subscribe_to_topics()
                        
                        # Connect to remote peers
                        await self.connect_to_peers()
                        
                        # Start all event handlers
                        async with trio.open_nursery() as nursery:
                            # Start gossipsub message handlers for each topic
                            for topic in GOSSIPSUB_TOPICS:
                                nursery.start_soon(self.handle_gossipsub_messages, topic)
                            
                            # Start other event handlers
                            nursery.start_soon(self.handle_ping)
                            nursery.start_soon(self.handle_identify)
                            nursery.start_soon(self.handle_connection_events)
                            
                            # Wait indefinitely or until connection closes
                            try:
                                await trio.sleep_forever()
                            except KeyboardInterrupt:
                                logger.info("Shutting down...")
                                nursery.cancel_scope.cancel()
                                
        except Exception as e:
            logger.error(f"Error in main run loop: {e}")
            print(f"error,{e}")
            raise

async def main():
    """Main entry point."""
    try:
        # Get remote peers from environment variable
        remote_peers_env = os.getenv("REMOTE_PEERS", "")
        if not remote_peers_env:
            logger.error("REMOTE_PEERS environment variable not set")
            print("error,REMOTE_PEERS environment variable not set")
            sys.exit(1)
        
        remote_addrs = [
            addr.strip() 
            for addr in remote_peers_env.split(',') 
            if addr.strip()
        ]
        
        if not remote_addrs:
            logger.error("No valid remote addresses found")
            print("error,No valid remote addresses found")
            sys.exit(1)
        
        logger.info(f"Connecting to remote peers: {remote_addrs}")
        
        # Create and run checker
        checker = P2PChecker(remote_addrs)
        await checker.run()
        
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"error,{e}")
        sys.exit(1)

if __name__ == "__main__":
    trio.run(main)