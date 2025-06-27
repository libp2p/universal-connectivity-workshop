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

### Step 0: Add Dependencies

First, add the required dependencies either by editing your `Cargo.toml` or by using `cargo add`.

Edit your `Cargo.toml` to include the following dependencies:
```toml
[dependencies]
anyhow = "1.0"
futures = "0.3"
libp2p = { version = "0.55", features = ["ed25519", "macros", "noise", "ping", "tcp", "tokio", "yamux"] }
tokio = { version = "1.45", features = ["full"] }
```

Or use the command line:
```bash
cargo add anyhow
cargo add futures
cargo add libp2p --features ed25519,macros,noise,ping,tcp,tokio,yamux
cargo add tokio --features full
```

### Step 1: Set Up Your Main Function and Print Startup Message

Create the basic structure in `src/main.rs` and import the dependencies:

```rust
use anyhow::Result;

#[tokio::main]
async fn main() -> Result<()> {
    println!("Starting Universal Connectivity Application...");
    
    // Step 3 code goes here
    
    Ok(())
}
```

The `anyhow::Result` type is used for error handling, allowing you to return errors easily without needing to define custom error types.

### Step 2: Generate Identity and Print PeerId

Generate an Ed25519 keypair and extract the PeerId:

```rust
use libp2p::identity;

// Generate a random Ed25519 keypair for our local peer
let local_key = identity::Keypair::generate_ed25519();
let local_peer_id = local_key.public().to_peer_id();

println!("Local peer id: {}", local_peer_id);
```

### Step 3: Create a Basic Behaviour

For now, create a network behavior with just the ping behaiour.

```rust
use libp2p::{swarm::NetworkBehaviour, ping};

#[derive(NetworkBehaviour)]
struct Behaviour {
    ping: ping::Behaviour,
}
```

### Step 4: Build the Swarm

Create a Swarm with minimal transport configuration:

```rust
use libp2p::{noise, tcp, yamux, SwarmBuilder};
use std::time::Duration;

let swarm = SwarmBuilder::with_existing_identity(local_key)
    .with_tokio()
    .with_tcp(
        tcp::Config::default(),
        noise::Config::new,
        yamux::Config::default,
    )?
    .with_behaviour(|_| Behaviour { ping: ping::Behaviour::default() })?
    .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
    .build();
```

### Step 5: Run the Event Loop

Add a basic event loop that will run indefinitely:

```rust
use futures::StreamExt;

loop {
    tokio::select! {
        Some(event) = swarm.next() => match event {
            // Handle events here in the future
            _ => {}
        }
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
use libp2p::{noise, tcp, yamux, SwarmBuilder};
use libp2p::{ping, swarm::NetworkBehaviour};
use std::time::Duration;

// Step 3: Create a Basic Behaviour
#[derive(NetworkBehaviour)]
struct Behaviour {
    ping: ping::Behaviour,
}

// Main function
#[tokio::main]
async fn main() -> Result<()> {
    // Step 1: Set Up Your Main Function and Print Startup Message

    // Step 2: Generate identity and Print PeerId

    // Step 4: Build the Swarm

    // Step 5: Run the Event Loop

    Ok(())
}
```

## Testing Your Implementation

If you are using the workshop tool to take this workshop, you only have to hit the `c` key to check your solutionto see if it is correct. However if you would like to test your solution manually, you can follow these steps. The `PROJECT_ROOT` environment variable is the path to your Rust project. The `LESSON_PATH` for this lesson is most likely `.workshop/universal-conectivity-workshop/en/rs/01-identity-and-swarm`.

1. Set the environment variables:
   ```bash
   export PROJECT_ROOT=/path/to/workshop
   export LESSON_PATH=en/rs/03-ping-checkpoint
   ```

2. Change into the lesson directory:
    ```bash
    cd $PROJECT_ROOT/$LESSON_PATH
    ```

3. Run with Docker Compose:
   ```bash
   docker compose up --build
   ```

4. Run the Python script to check your output:
   ```bash
   python check.py
   ```

## Success Criteria

Your implementation should:
- ✅ Display the startup message and local peer ID

## Hints

## Hint - Complete Solution

Here's the complete working solution:

```rust
use anyhow::Result;
use futures::StreamExt;
use libp2p::identity;
use libp2p::{noise, tcp, yamux, SwarmBuilder};
use libp2p::{ping, swarm::NetworkBehaviour};
use std::time::Duration;

#[derive(NetworkBehaviour)]
struct Behaviour {
    ping: ping::Behaviour,
}

#[tokio::main]
async fn main() -> Result<()> {
    println!("Starting Universal Connectivity Application...");
    
    // Generate a random Ed25519 keypair for our local peer
    let local_key = identity::Keypair::generate_ed25519();
    let local_peer_id = local_key.public().to_peer_id();
    
    println!("Local peer id: {}", local_peer_id);
    
    // Build the Swarm, connecting the lower transport logic with the
    // higher-level Network Behaviour logic
    let mut swarm = SwarmBuilder::with_existing_identity(local_key)
        .with_tokio()
        .with_tcp(
            tcp::Config::default(),
            noise::Config::new,
            yamux::Config::default,
        )?
        .with_behaviour(|_| Behaviour { ping: ping::Behaviour::default() })?
        .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
        .build();
    
    // Run the network event loop
    loop {
        tokio::select! {
            Some(event) = swarm.next() => match event {
                // Handle events here in the future
                _ => {}
            }
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
