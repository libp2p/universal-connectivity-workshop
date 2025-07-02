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