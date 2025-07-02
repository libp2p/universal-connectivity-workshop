import trio
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import hashlib
import base58

class LibP2PHost:
    """Basic libp2p Host implementation"""
    
    def __init__(self, private_key, peer_id):
        self.private_key = private_key
        self.peer_id = peer_id
        self.is_running = False
    
    async def start(self):
        """Start the host"""
        self.is_running = True
        print(f"Host started with PeerId: {self.peer_id}")
    
    async def stop(self):
        """Stop the host"""
        self.is_running = False
        print("Host stopped")
    
    def get_peer_id(self):
        """Get the peer ID"""
        return self.peer_id

async def main():
    print("Starting Universal Connectivity Application...")
    
    # Generate Ed25519 keypair for peer identity
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    # Extract public key bytes for PeerId generation
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    
    # Create PeerId by hashing the public key
    peer_id_hash = hashlib.sha256(public_key_bytes).digest()
    peer_id = base58.b58encode(peer_id_hash).decode('ascii')
    
    print(f"Local peer id: {peer_id}")
    
    # Create and start the libp2p host
    host = LibP2PHost(private_key, peer_id)
    await host.start()
    
    # Keep the application running
    try:
        while host.is_running:
            await trio.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        await host.stop()

if __name__ == "__main__":
    trio.run(main)