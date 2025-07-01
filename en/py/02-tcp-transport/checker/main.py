import asyncio
import os
import sys
from typing import List

from libp2p import new_host
from multiaddr import Multiaddr


async def main():
    """
    Minimal checker application for libp2p connections.
    """
    # Get environment variable
    remote_peers_env = os.getenv("REMOTE_PEERS", "")
    if not remote_peers_env:
        print("error,No REMOTE_PEERS environment variable set")
        return

    # Parse addresses
    listen_addrs: List[Multiaddr] = []
    for addr_str in remote_peers_env.split(','):
        addr_str = addr_str.strip()
        if addr_str:
            try:
                listen_addrs.append(Multiaddr(addr_str))
            except Exception as e:
                print(f"error,Invalid multiaddr {addr_str}: {e}")
                continue

    if not listen_addrs:
        print("error,No valid addresses")
        return

    # Create host
    try:
        host = new_host()
    except Exception as e:
        print(f"error,Host creation failed: {e}")
        return

    # Try to listen on each address one by one
    for addr in listen_addrs:
        try:
            print(f"Trying to listen on {addr}")
            
            # Create a task for listening to handle potential blocking
            listen_task = asyncio.create_task(host.get_network().listen(addr))
            
            # Wait for the listen operation with a timeout
            await asyncio.wait_for(listen_task, timeout=10.0)
            
            print(f"incoming,{addr},listening")
            
        except asyncio.TimeoutError:
            print(f"error,Timeout listening on {addr}")
            continue
        except Exception as e:
            print(f"error,Listen failed on {addr}: {e}")
            print(f"Exception details: {type(e).__name__}: {str(e)}")
            continue

    # Simple wait loop
    try:
        print("Waiting for connections (30 seconds max)...")
        
        for i in range(300):  # 30 seconds
            await asyncio.sleep(0.1)
            
            # Try to access connections safely
            try:
                network = host.get_network()
                if hasattr(network, 'connections'):
                    connections = network.connections
                    if connections:
                        print(f"Found {len(connections)} connections")
                        for peer_id in connections:
                            print(f"connected,{peer_id},basic")
                        # Exit after finding connections
                        await asyncio.sleep(2)  # Wait a bit more
                        break
            except Exception as e:
                print(f"error,Connection check failed: {e}")
                break
                
    except Exception as e:
        print(f"error,Main loop error: {e}")
    
    # Cleanup
    try:
        await host.close()
    except Exception as e:
        print(f"error,Cleanup error: {e}")


if __name__ == "__main__":
    # Set environment variable for testing if not set
    if not os.getenv("REMOTE_PEERS"):
        print("Warning: REMOTE_PEERS not set, using default")
        os.environ["REMOTE_PEERS"] = "/ip4/127.0.0.1/tcp/9092"
    
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"error,Top level error: {e}")
        sys.exit(1)