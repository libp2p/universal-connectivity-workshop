#!/usr/bin/env python3
"""
Checker for Kademlia DHT Implementation
This checker connects to the student's DHT nodes and validates functionality
"""

import logging
import os
import secrets
import sys
import time
from typing import List

import trio
from multiaddr import Multiaddr
import base58

from libp2p import new_host
from libp2p.abc import IHost
from libp2p.crypto.secp256k1 import create_new_key_pair
from libp2p.kad_dht.kad_dht import DHTMode, KadDHT
from libp2p.kad_dht.utils import create_key_from_binary
from libp2p.peer.id import ID as PeerID
from libp2p.tools.async_service import background_trio_service
from libp2p.tools.utils import info_from_p2p_addr

# Configure logging to match expected output format
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("kademlia-checker")


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
    """Get remote peer addresses from REMOTE_PEERS env var or server_node_addr.txt."""
    # First try environment variable
    env_peers = parse_multiaddrs_from_env("REMOTE_PEERS")
    if env_peers:
        return env_peers
    
    # Try to read from server_node_addr.txt (created by the main app)
    server_addr_file = "server_node_addr.txt"
    if os.path.exists(server_addr_file):
        try:
            with open(server_addr_file, 'r') as f:
                addr = f.read().strip()
                if addr:
                    return [addr]
        except Exception as e:
            logger.warning(f"error,Failed to read {server_addr_file}: {e}")
    
    # Try to read from app/server_node_addr.txt
    app_server_addr_file = "app/server_node_addr.txt"
    if os.path.exists(app_server_addr_file):
        try:
            with open(app_server_addr_file, 'r') as f:
                addr = f.read().strip()
                if addr:
                    return [addr]
        except Exception as e:
            logger.warning(f"error,Failed to read {app_server_addr_file}: {e}")
    
    return []


async def connect_to_remote_peers(host: IHost, remote_addrs: List[str]) -> None:
    """Connect to the remote peers (student's DHT nodes)."""
    for addr in remote_addrs:
        try:
            peerInfo = info_from_p2p_addr(Multiaddr(addr))
            host.get_peerstore().add_addrs(peerInfo.peer_id, peerInfo.addrs, 3600)
            await host.connect(peerInfo)
            logger.info(f"connected,{peerInfo.peer_id},{addr}")
        except Exception as e:
            logger.warning(f"error,Failed to connect to {addr}: {e}")


async def test_dht_functionality(host: IHost, dht: KadDHT) -> None:
    """Test DHT functionality by storing and retrieving values."""
    # Test value storage and retrieval
    test_key = create_key_from_binary(b"test-key-from-checker")
    test_value = b"Test value from checker"
    
    try:
        # Try to store a value
        await dht.put_value(test_key, test_value)
        logger.info(f"dht-put,{base58.b58encode(test_key).decode()},{test_value.decode()}")
        
        # Wait a moment for propagation
        await trio.sleep(1)
        
        # Try to retrieve the value
        retrieved_value = await dht.get_value(test_key)
        if retrieved_value:
            logger.info(f"dht-get,{base58.b58encode(test_key).decode()},{retrieved_value.decode()}")
        else:
            logger.warning("error,Failed to retrieve stored value")
            
    except Exception as e:
        logger.error(f"error,DHT operation failed: {e}")


async def test_content_provider(host: IHost, dht: KadDHT) -> None:
    """Test content provider functionality."""
    content_key = create_key_from_binary(b"test-content-from-checker")
    
    try:
        # Advertise as a content provider
        success = await dht.provider_store.provide(content_key)
        if success:
            logger.info(f"provider-advertise,{content_key.hex()}")
        else:
            logger.warning("error,Failed to advertise as content provider")
        
        # Wait a moment for propagation
        await trio.sleep(1)
        
        # Try to find providers for the content
        providers = await dht.provider_store.find_providers(content_key)
        if providers:
            provider_ids = [p.peer_id.pretty() for p in providers]
            logger.info(f"provider-found,{content_key.hex()},{len(providers)},{','.join(provider_ids)}")
        else:
            logger.warning(f"error,No providers found for content {content_key.hex()}")
            
    except Exception as e:
        logger.error(f"error,Content provider operation failed: {e}")


async def run_checker() -> None:
    """Run the checker that validates the student's kademlia implementation."""
    try:
        # Parse environment variables or look for server address file
        remote_addrs = get_remote_peers()
        if not remote_addrs:
            logger.error("error,No REMOTE_PEERS specified and no server_node_addr.txt found")
            logger.info("info,Please either:")
            logger.info("info,1. Set REMOTE_PEERS environment variable with server address")
            logger.info("info,2. Run 'python app/main.py --mode server' first to create server_node_addr.txt")
            sys.exit(1)
        
        # Create host with generated key pair
        key_pair = create_new_key_pair(secrets.token_bytes(32))
        host = new_host(key_pair=key_pair)
        
        # Listen on a port (this makes us a bootstrapper)
        listen_addrs = [Multiaddr("/ip4/127.0.0.1/tcp/0")]  # Use port 0 for automatic assignment
        
        # Start the host
        async with host.run(listen_addrs=listen_addrs), trio.open_nursery() as nursery:
            peer_id = host.get_id()
            
            # Get the actual listening address
            actual_addrs = host.get_addrs()
            if actual_addrs:
                listen_addr = actual_addrs[0]
                logger.info(f"checker-listening,{listen_addr}/p2p/{peer_id}")
            
            # Start peer store cleanup if available
            peerstore = host.get_peerstore()
            if hasattr(peerstore, 'start_cleanup_task'):
                nursery.start_soon(peerstore.start_cleanup_task, 60)
            
            # Initialize Kademlia DHT in server mode (we're acting as a peer)
            dht = KadDHT(host, DHTMode.SERVER)
            
            # Start DHT service
            async with background_trio_service(dht):
                logger.info("checker-dht-started,server")
                
                # Connect to the student's nodes
                await connect_to_remote_peers(host, remote_addrs)
                
                # Wait for connections to establish
                connection_timeout = 10  # seconds
                check_interval = 0.5
                elapsed = 0
                
                while elapsed < connection_timeout:
                    connected_peers = list(host.get_connected_peers())
                    if connected_peers:
                        break
                    await trio.sleep(check_interval)
                    elapsed += check_interval
                
                connected_peers = list(host.get_connected_peers())
                if not connected_peers:
                    logger.error("error,No connections established with student nodes")
                    return
                
                logger.info(f"connections-established,{len(connected_peers)}")
                
                # Log each connected peer
                for peer in connected_peers:
                    peer_addrs = host.get_peerstore().addrs(peer)
                    if peer_addrs:
                        logger.info(f"peer-connected,{peer},{peer_addrs[0]}")
                    else:
                        logger.info(f"peer-connected,{peer},unknown-addr")
                
                # Wait for DHT to bootstrap
                await trio.sleep(2)
                
                # Test DHT functionality
                await test_dht_functionality(host, dht)
                
                # Test content provider functionality
                await test_content_provider(host, dht)
                
                # Check routing table status
                routing_table_size = len(dht.routing_table.get_all_peers())
                logger.info(f"routing-table-size,{routing_table_size}")
                
                # Final status check
                final_connected_peers = list(host.get_connected_peers())
                logger.info(f"final-status,{len(final_connected_peers)}")
                
                # Log disconnections
                for peer in final_connected_peers:
                    logger.info(f"peer-disconnect,{peer}")
                
                return
                    
    except Exception as e:
        logger.error(f"error,{e}")
        sys.exit(1)


def main():
    """Main entry point."""
    try:
        trio.run(run_checker)
    except KeyboardInterrupt:
        logger.info("checker-shutdown,interrupted")
    except Exception as e:
        logger.error(f"error,{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()