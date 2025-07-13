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
```

**What’s happening here?**
- The `#!/usr/bin/env python3` line is like a note to your computer saying, “Run this script with Python 3.” It’s a standard way to make the script executable on Unix-like systems (e.g., Linux or macOS).
- The docstring (`"""..."""`) is a quick summary of what the script does: it’s Lesson 1 in learning how to build a `libp2p` host (a node in a P2P network) and give it a unique identity using cryptography.

**Why?** The shebang ensures the script runs with the right Python version, and the docstring is like a label on a jar, telling you what’s inside.

### 2. Imports
```python
import trio
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import hashlib
import base58
```

**What’s happening here?**
This is like grabbing the ingredients for your recipe. The script pulls in:
- `trio`: A library for handling asynchronous tasks, like juggling multiple phone calls without dropping any. It’s used here to manage the host’s lifecycle.
- `cryptography.hazmat.primitives`: Tools for secure cryptography:
  - `hashes`: For creating cryptographic hashes (though not directly used here, imported for completeness).
  - `ed25519`: A fast and secure algorithm for generating keypairs (private and public keys) to identify your node.
  - `serialization`: Helps convert keys into a format you can use (like raw bytes).
- `hashlib`: A Python library for hashing data, used here to create a unique ID from the public key.
- `base58`: A library for encoding data in a compact, human-readable format (like Bitcoin addresses), used to make the peer ID look nice.

**Why?** These libraries provide the tools to create a secure identity, manage async operations, and format the peer ID.

### 3. LibP2PHost Class
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

**What’s happening here?**
This is like building a little control center for your P2P node, called `LibP2PHost`. Here’s what it does:
- **Initialization (`__init__`)**: When you create a host, you give it a private key (your secret) and a peer ID (your public name). It also sets a flag (`is_running`) to `False`, meaning the host isn’t active yet.
- **Start (`start`)**: Flips the `is_running` flag to `True` and prints a message saying the host is up with its peer ID. It’s marked `async` because it might do network stuff later (though here it’s simple).
- **Stop (`stop`)**: Sets `is_running` to `False` and prints that the host is stopped. Also `async` for future-proofing.
- **Get Peer ID (`get_peer_id`)**: Just returns the peer ID so others can see who you are.

**Why?** This class is like the blueprint for your P2P node. It’s basic for now (just starting, stopping, and storing an ID), but it’s a foundation you can build on to add networking features.

### 4. Main Async Function
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

**What’s happening here?**
This is the heart of the program, where everything comes together. It’s marked `async` because it uses `trio` for asynchronous operations. Here’s the step-by-step:
1. **Print a startup message**: Just a friendly “Hey, we’re starting!”
2. **Generate a keypair**: Uses Ed25519 to create a private key (your secret) and a public key (what you share). Think of it like creating a lock and key: the private key is yours, and the public key is what others use to verify you.
3. **Get public key bytes**: Converts the public key into raw bytes (a format suitable for hashing).
4. **Create a peer ID**: Takes the public key bytes, hashes them with SHA-256 (a secure way to create a unique fingerprint), and encodes the result in Base58 (a compact, readable format). This becomes your node’s unique ID, like a username.
5. **Print the peer ID**: Shows you the ID so you know who you are in the network.
6. **Create and start the host**: Makes a new `LibP2PHost` with the private key and peer ID, then starts it (which just sets `is_running` to `True` and prints a message).
7. **Keep running**: Loops indefinitely, checking every second if the host is still running. If you hit `Ctrl+C`, it catches the `KeyboardInterrupt`, prints “Shutting down...”, and stops the host.

**Why?** This sets up your node’s identity and starts a basic host that just sits there (for now). It’s like registering for a social network and logging in, but not chatting yet.


### 5. Entry Point
```python
if __name__ == "__main__":
    trio.run(main)
```

**What’s happening here?**
This is the standard way to say, “If this script is run directly (not imported as a module), start the `main` function.” The `trio.run(main)` part tells `trio` to handle the asynchronous `main` function, kicking off the whole program.

**Why?** It’s the “on” switch for the app, ensuring everything starts properly.

### Big Picture
This script is like a “Hello, World!” for P2P networking with `libp2p`. It:
- Creates a unique identity for your node using Ed25519 cryptography (a private-public keypair).
- Turns the public key into a compact, unique peer ID using SHA-256 and Base58.
- Sets up a basic `LibP2PHost` that can start and stop, though it doesn’t do much networking yet (it’s Lesson 1, after all!).
- Uses `trio` to manage the async flow, keeping the app running until you stop it with `Ctrl+C`.

Think of it as setting up a profile for your computer in a decentralized network. It’s not connecting to other peers or sending messages yet, but it’s got the basics: a secure ID and a way to say “I’m here!” This is a starting point you could build on to add features like connecting to other nodes or sending data, as seen in the more complex code you shared earlier.

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