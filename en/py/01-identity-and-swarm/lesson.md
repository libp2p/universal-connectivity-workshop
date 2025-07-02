# Lesson 1: Identity and Basic Host

Welcome to your first step into peer-to-peer networking with libp2p! In this lesson, you'll create your very first libp2p peer and understand the fundamental concept of peer identity.

## Learning Objectives

By the end of this lesson, you will:
- Understand what a PeerId is and why it's important
- Create cryptographic keypairs for peer identification
- Initialize a basic libp2p Host
- Run your first libp2p application

## Background: Peer Identity in libp2p

In traditional client-server applications, servers have known addresses (like domain names), but clients are anonymous. In peer-to-peer networks, every participant is both a client and a server, so each peer needs a stable, verifiable identity.

libp2p uses **cryptographic keypairs** for peer identity:
- **Private Key**: Kept secret, used to sign messages and prove identity
- **Public Key**: Shared with others, used to verify signatures  
- **PeerId**: A hash of the public key, used as a short identifier

This design ensures that:
1. Peers can prove they control their identity (via signatures)
2. Others can verify that proof (via public key cryptography)
3. Identities are compact and easy to share (via PeerId hash)

## Your Task

Create a Python application that:
1. Generates an Ed25519 keypair for peer identity
2. Creates a basic libp2p Host
3. Prints the peer's ID when the application starts
4. Runs a simple event loop (even though it won't handle events yet)

## Step-by-Step Instructions

### Step 1: Set Up Your Main Function

Create `app/main.py` with the basic structure:

```python
#!/usr/bin/env python3
"""
Lesson 1: Identity and Basic Host
Creates a basic libp2p host with cryptographic identity.
"""

import trio
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import hashlib
import base58

async def main():
    print("Starting Universal Connectivity Application...")
    
    # Your code will go here
    
    # Keep the application running
    try:
        while True:
            await trio.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == "__main__":
    trio.run(main())
```

### Step 2: Generate Cryptographic Identity

Add identity generation to your `main()` function:

```python
# Generate Ed25519 keypair for peer identity
private_key = ed25519.Ed25519PrivateKey.generate()
public_key = private_key.public_key()

# Extract public key bytes for PeerId generation
public_key_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw
)

print(f"Generated Ed25519 keypair")
print(f"Public key: {public_key_bytes.hex()}")
```

### Step 3: Create PeerId

A PeerId is a multihash of the public key. For simplicity, we'll create a basic version:

```python
# Create PeerId by hashing the public key
# In real libp2p, this uses multihash format, but we'll simplify
peer_id_hash = hashlib.sha256(public_key_bytes).digest()
peer_id = base58.b58encode(peer_id_hash).decode('ascii')

print(f"Local peer id: {peer_id}")
```

### Step 4: Create Basic Host Class

Before your `main()` function, create a simple Host class:

```python
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
```

### Step 5: Use the Host in Main

Update your `main()` function to use the Host:

```python
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
```

## Complete Solution Structure

Your complete `app/main.py` should look like this:

```python
#!/usr/bin/env python3
"""
Lesson 1: Identity and Basic Host
Creates a basic libp2p host with cryptographic identity.
"""

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
```

## Testing Your Solution

Run your application with:
```bash
cd app
python main.py
```

You should see output similar to:
```
Starting Universal Connectivity Application...
Local peer id: 8QmatENdmjQQqwGqkAdTyKMjwTtJJdqCfZ6jAFkchTw9bKS4
Host started with PeerId: 8QmatENdmjQQqwGqkAdTyKMjwTtJJdqCfZ6jAFkchTw9bKS4
```

Press Ctrl+C to stop the application.

## Hint Blocks

### 🔑 Understanding Cryptographic Keys

**Ed25519** is a modern elliptic curve signature scheme that provides:
- Fast key generation and signing
- Small key sizes (32 bytes for public keys)
- Strong security guarantees
- Deterministic signatures

The private key stays secret and is used to prove identity, while the public key can be shared freely.

### 🆔 PeerId Format

In real libp2p implementations, PeerIds follow the multihash format:
- They start with a prefix indicating the hash algorithm
- They encode the length of the hash
- They contain the actual hash of the public key

Our simplified version just uses SHA256 + Base58 encoding for readability.

### ⚡ Async/Await Pattern

Python's trio is perfect for network programming because:
- It handles many connections concurrently
- It's non-blocking (doesn't freeze your program)
- It integrates well with networking libraries

The `while host.is_running` loop keeps our program alive to handle future network events.

### 🔧 Troubleshooting

**Import Error**: If you get import errors, make sure you've installed the dependencies:
```bash
pip install cryptography base58
```

**Key Generation Fails**: The cryptography library requires system-level crypto libraries. On some systems you might need:
```bash
# Ubuntu/Debian
sudo apt-get install build-essential libssl-dev libffi-dev

# macOS (with Homebrew)
brew install openssl libffi
```

## What You've Learned

Congratulations! You've created your first libp2p node with:

- **Cryptographic Identity**: Your node has a unique, verifiable identity
- **PeerId**: A compact identifier that other peers can use to reference your node
- **Basic Host**: The foundation that will handle all network operations
- **Async Structure**: Ready to handle network events efficiently

## What's Next?

In the next lesson, you'll learn about:
- **Multiaddresses**: How peers specify where they can be reached
- **Transport Layers**: Adding TCP networking to your host
- **Connection Establishment**: Actually connecting to other peers

Your identity is just the beginning - now let's make your peer reachable on the network!