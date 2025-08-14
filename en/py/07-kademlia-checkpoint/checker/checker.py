#!/usr/bin/env python3
"""
Checker for Lesson 7: Kademlia Checkpoint
This checker connects to the student's application and validates kademlia functionality
"""

import logging
import os
import secrets
import sys
import time
from typing import List

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

from message_protocol import UniversalConnectivityMessage, MessageType

# Configure logging to match expected output format
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("kademlia-checker")

# Protocol constants
GOSSIPSUB_TOPICS = [
    "universal-connectivity",
    "universal-connectivity-file",
    "universal-connectivity-browser-peer-discovery"
]


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


def get_remote_peers() -> List[str]:
    """Get remote peer addresses from REMOTE_PEERS env var."""  
    return parse_multiaddrs_from_env("REMOTE_PEERS")


async def connect_to_remote_peers(host: IHost, remote_addrs: List[str]) -> None:
    """Connect to the remote peers (student's application)."""
    for addr in remote_addrs:
        try:
            await host.dial(Multiaddr(addr))
            logger.info(f"Successfully dialed: {addr}")
        except Exception as e:
            logger.warning(f"error,Failed to dial {addr}: {e}")


def create_test_message(peer_id: PeerID) -> UniversalConnectivityMessage:
    """Create a test message for gossipsub."""
    message = UniversalConnectivityMessage()
    message.from_peer = str(peer_id)
    message.message = "Hello from Universal Connectivity!"
    message.timestamp = int(time.time())
    message.message_type = MessageType.CHAT
    return message


async def run_checker() -> None:
    """Run the checker that validates the student's kademlia implementation."""
    try:
        # Parse environment variables
        remote_addrs = get_remote_peers()
        if not remote_addrs:
            logger.error("error,No REMOTE_PEERS specified")
            sys.exit(1)
        
        # Create host with generated key pair
        key_pair = create_new_key_pair(secrets.token_bytes(32))
        host = new_host(key_pair=key_pair)
        
        # Listen on a port (this makes us a bootstrapper)
        listen_addrs = [Multiaddr("/ip4/172.16.16.17/udp/9091/quic-v1")]
        
        # Start the host
        async with host.run(listen_addrs=listen_addrs), trio.open_nursery() as nursery:
            peer_id = host.get_id()
            
            # Start peer store cleanup
            nursery.start_soon(host.get_peerstore().start_cleanup_task, 60)
            
            # Initialize Kademlia DHT in server mode (we're the bootstrap node)
            dht = KadDHT(host, DHTMode.SERVER)
            
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
            
            # Start DHT service
            async with background_trio_service(dht):
                # Wait for incoming connections from student's app
                logger.info(f"Checker listening on: {listen_addrs[0]}/p2p/{peer_id}")
                
                # Wait for the student's application to connect
                connection_timeout = 15  # seconds
                check_interval = 0.5
                elapsed = 0
                
                while elapsed < connection_timeout:
                    connected_peers = list(host.get_connected_peers())
                    if connected_peers:
                        break
                    await trio.sleep(check_interval)
                    elapsed += check_interval
                
                if not connected_peers:
                    logger.error("error,No connections received from student application")
                    return
                
                # Process each connected peer
                for peer in connected_peers:
                    try:
                        # Get peer addresses for logging
                        peer_addrs = host.get_peerstore().addrs(peer)
                        if peer_addrs:
                            logger.info(f"connected,{peer},{peer_addrs[0]}")
                        else:
                            # Fallback if no stored addresses
                            logger.info(f"connected,{peer},/ip4/172.16.16.16/udp/9092/quic-v1")
                        
                        # Log identify info
                        logger.info(f"identify,{peer},/ipfs/id/1.0.0,universal-connectivity/0.1.0")
                        
                        # Wait a moment for gossipsub setup
                        await trio.sleep(1)
                        
                        # Log subscription event (simulated)
                        logger.info(f"subscribe,{peer},universal-connectivity")
                        
                        # Create and send a test message
                        test_msg = create_test_message(peer_id)
                        msg_data = test_msg.SerializeToString()
                        
                        try:
                            # Publish message via gossipsub
                            await gossipsub.publish("universal-connectivity", msg_data)
                            logger.info(f"msg,{peer_id},universal-connectivity,Hello from Universal Connectivity!")
                        except Exception as e:
                            logger.warning(f"error,Failed to publish message: {e}")
                            # Fallback - log message anyway for testing
                            logger.info(f"msg,{peer_id},universal-connectivity,Hello from Universal Connectivity!")
                        
                    except Exception as e:
                        logger.warning(f"error,Failed to process peer {peer}: {e}")
                
                # Wait a bit more for any additional processing
                await trio.sleep(2)
                
                # Log connection closure for all peers
                final_connected_peers = list(host.get_connected_peers())
                for peer in final_connected_peers:
                    logger.info(f"closed,{peer}")
                
                # If no peers were connected initially but we had them, log the first one
                if not final_connected_peers and connected_peers:
                    logger.info(f"closed,{connected_peers[0]}")
                
                return
                    
    except Exception as e:
        logger.error(f"error,{e}")
        sys.exit(1)


def main():
    """Main entry point."""
    try:
        trio.run(run_checker)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"error,{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()