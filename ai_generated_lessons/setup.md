# Rust Setup Instructions

Welcome to the Universal Connectivity Workshop! Follow these steps to set up your development environment.

## Prerequisites

Before starting this workshop, ensure you have the following installed:

### 1. Rust Toolchain

Install Rust using rustup (recommended):

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
```

Verify your installation:
```bash
rustc --version
cargo --version
```

You should have Rust 1.70 or later for full libp2p compatibility.

### 2. Required System Dependencies

**On Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install build-essential pkg-config libssl-dev
```

**On macOS:**
```bash
# Install Xcode command line tools
xcode-select --install

# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required packages
brew install pkg-config openssl
```

**On Windows:**
- Install Visual Studio Build Tools or Visual Studio Community
- Ensure you have the C++ build tools installed

### 3. Docker (for lesson validation)

Install Docker Desktop from https://www.docker.com/products/docker-desktop/

Verify Docker installation:
```bash
docker --version
docker-compose --version
```

## Project Setup

1. **Create a new Rust project:**
   ```bash
   cargo new uc-app
   cd uc-app
   ```

2. **Initialize the workshop in your project directory:**
   ```bash
   # Run the workshop tool from your project directory
   workshop
   ```

3. **Select your preferences:**
   - Choose "English" for spoken language
   - Choose "Rust" for programming language
   - Select "Building Universal Connectivity with rust-libp2p"

## Development Environment

### Recommended IDE Setup

**VS Code with Rust extensions:**
- Install rust-analyzer extension
- Install CodeLLDB for debugging
- Install Even Better TOML for Cargo.toml syntax highlighting

**Other IDEs:**
- CLion with Rust plugin
- Vim/Neovim with rust-analyzer
- Emacs with rust-mode

### Useful Development Commands

During the workshop, you'll frequently use these commands:

```bash
# Check your code compiles
cargo check

# Build your project
cargo build

# Run your application
cargo run

# Run with debug logging
RUST_LOG=debug cargo run

# Format your code
cargo fmt

# Run linter
cargo clippy
```

## Network Configuration

Some lessons require connecting to instructor servers. Ensure:

1. **Firewall settings** allow outbound connections on various ports
2. **Corporate networks** may require proxy configuration
3. **NAT/Router settings** - some lessons will help you understand and work with NAT

## Workshop Structure

Once setup is complete, you'll work through:

1. **Foundation lessons** (1-4): Basic libp2p concepts
2. **Discovery and messaging** (5-8): Peer discovery and communication
3. **Advanced features** (9-11): NAT traversal and file sharing
4. **Final integration** (12): Complete application

## Getting Help

During the workshop:
- Ask the instructor for help with setup issues
- Check with neighboring participants
- Use the hint system in each lesson
- Reference the official libp2p documentation: https://docs.libp2p.io/

## Ready to Begin!

Once you've completed these setup steps:

1. Return to the workshop tool in your project directory
2. Start with Lesson 1: "First Steps - Identity and Basic Swarm"
3. Follow the step-by-step instructions in each lesson

Good luck, and welcome to the world of peer-to-peer networking with rust-libp2p!