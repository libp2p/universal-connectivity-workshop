# Lesson 1: First Steps - Identity and Basic Swarm

Welcome to your journey into peer-to-peer networking with rust-libp2p! In this first lesson, you'll create your very first libp2p peer and understand the fundamental concept of peer identity.

## Learning Objectives

By the end of this lesson, you will:
- Understand what a PeerId is and why it's important
- Create cryptographic keypairs for peer identification
- Initialize a basic libp2p Swarm
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

Create a Rust application that:
1. Generates an Ed25519 keypair for peer identity
2. Creates a basic libp2p Swarm
3. Prints the peer's ID when the application starts
4. Runs the event loop (even though it won't handle events yet)

## Step-by-Step Instructions

### Step 1: Add Dependencies

First, add the required dependencies to your `Cargo.toml`:

```toml
[dependencies]
libp2p = { version = "0.55", features = ["ed25519", "tokio", "macros"] }
tokio = { version = "1.0", features = ["full"] }
anyhow = "1.0"
```

### Step 2: Set Up Your Main Function

Create the basic structure in `src/main.rs`:

```rust
use anyhow::Result;
use libp2p::identity;
use libp2p::swarm::{NetworkBehaviour, Swarm};
use std::error::Error;

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    println!("Starting Universal Connectivity application...");
    
    // Your code will go here
    
    Ok(())
}
```

### Step 3: Generate Identity

Generate an Ed25519 keypair and extract the PeerId:

```rust
// Generate a random Ed25519 keypair for our local peer
let local_key = identity::Keypair::generate_ed25519();
let local_peer_id = local_key.public().to_peer_id();

println!("Local peer id: {}", local_peer_id);
```

### Step 4: Create a Basic Behaviour

For now, create an empty network behavior (we'll add protocols in later lessons):

```rust
use libp2p::swarm::derive_prelude::*;

#[derive(NetworkBehaviour)]
struct Behaviour {}
```

### Step 5: Build the Swarm

Create a Swarm with minimal transport configuration:

```rust
use libp2p::{noise, tcp, yamux, Transport};

let swarm = libp2p::SwarmBuilder::with_existing_identity(local_key)
    .with_tokio()
    .with_tcp(
        tcp::Config::default(),
        noise::Config::new,
        yamux::Config::default,
    )?
    .with_behaviour(|_key| Behaviour {})?
    .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
    .build();
```

### Step 6: Run the Event Loop

Add a basic event loop that will run indefinitely:

```rust
use futures::StreamExt;

loop {
    match swarm.select_next_some().await {
        // We're not handling any events yet, just keep running
        _ => {}
    }
}
```

## Complete Solution Structure

Your complete `src/main.rs` should look something like this structure:

```rust
// Imports
use anyhow::Result;
use futures::StreamExt;
use libp2p::identity;
use libp2p::swarm::{NetworkBehaviour, Swarm};
use libp2p::{noise, tcp, yamux};
use std::error::Error;
use std::time::Duration;

// Network behavior
#[derive(NetworkBehaviour)]
struct Behaviour {}

// Main function
#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    // Print startup message
    // Generate keypair
    // Create swarm
    // Print peer ID
    // Run event loop
    Ok(())
}
```

## Testing Your Solution

Run your application with:
```bash
cargo run
```

You should see output similar to:
```
Starting Universal Connectivity application...
Local peer id: 12D3KooWGrCaG7G8eB3VV4z3h8Rj1r1j1j1j1j1j1j1j1j1j1j
```

The PeerId will be different each time you run the application since we're generating a new keypair each time.

## Hints

## Hint - Missing imports
If you get compilation errors about missing types, make sure you have all the necessary imports:

```rust
use anyhow::Result;
use futures::StreamExt;
use libp2p::identity;
use libp2p::swarm::{NetworkBehaviour, Swarm};
use libp2p::{noise, tcp, yamux};
use std::error::Error;
use std::time::Duration;
```

## Hint - Swarm builder issues
If you're having trouble with the SwarmBuilder, remember that you need to:
1. Start with an existing identity: `SwarmBuilder::with_existing_identity(local_key)`
2. Choose an executor: `.with_tokio()`
3. Configure transport: `.with_tcp(...)`
4. Add behavior: `.with_behaviour(|_key| Behaviour {})`
5. Configure swarm: `.with_swarm_config(...)`
6. Build it: `.build()`

## Hint - Event loop not working
Make sure your event loop is properly structured:

```rust
loop {
    match swarm.select_next_some().await {
        _ => {}
    }
}
```

You need to import `StreamExt` from futures for this to work.

## Hint - Cargo.toml dependencies
Double-check your dependencies in Cargo.toml:

```toml
[dependencies]
libp2p = { version = "0.55", features = ["ed25519", "tokio", "macros"] }
tokio = { version = "1.0", features = ["full"] }
anyhow = "1.0"
```

## Hint - Complete Solution

Here's the complete working solution:

```rust
use anyhow::Result;
use futures::StreamExt;
use libp2p::identity;
use libp2p::swarm::{NetworkBehaviour, Swarm};
use libp2p::{noise, tcp, yamux};
use std::error::Error;
use std::time::Duration;

#[derive(NetworkBehaviour)]
struct Behaviour {}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    println!("Starting Universal Connectivity application...");
    
    // Generate a random Ed25519 keypair for our local peer
    let local_key = identity::Keypair::generate_ed25519();
    let local_peer_id = local_key.public().to_peer_id();
    
    println!("Local peer id: {}", local_peer_id);
    
    // Build the Swarm, connecting the lower transport logic with the
    // higher-level Network Behaviour logic
    let mut swarm = libp2p::SwarmBuilder::with_existing_identity(local_key)
        .with_tokio()
        .with_tcp(
            tcp::Config::default(),
            noise::Config::new,
            yamux::Config::default,
        )?
        .with_behaviour(|_key| Behaviour {})?
        .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
        .build();
    
    // Run the network event loop
    loop {
        match swarm.select_next_some().await {
            _ => {}
        }
    }
}
```

## What's Next?

Great job! You've created your first libp2p node with a stable identity. In the next lesson, you'll learn how to add transport layers so your node can actually connect to other peers over the network.

Key concepts you've learned:
- **Peer Identity**: Every libp2p node has a cryptographic identity
- **Keypairs**: Ed25519 keypairs provide both identity and security
- **PeerId**: A compact identifier derived from the public key
- **Swarm**: The main coordination point for libp2p networking
- **Event Loop**: libp2p uses async events to handle network activity

Next up: Adding TCP transport so peers can actually communicate!
