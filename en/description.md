# Universal Connectivity

Welcome to the Universal Connectivity Workshop! This hands-on workshop teaches you how to build peer-to-peer applications using rust-libp2p, the powerful networking stack for decentralized applications.

## What You'll Learn

Throughout this workshop, you'll build a complete universal connectivity application from scratch, learning:

- **libp2p Fundamentals**: Peer identity, key generation, and swarm management
- **Transport Layers**: TCP and QUIC transports with Noise encryption and Yamux multiplexing
- **Protocol Integration**: Ping for connectivity testing and health monitoring
- **Peer Discovery**: Using Kademlia DHT for decentralized peer discovery
- **Peer Information**: Identify protocol for exchanging peer capabilities and metadata
- **Group Communication**: Implementing chat functionality with gossipsub pub/sub messaging
- **Protocol Composition**: Building applications that combine multiple libp2p protocols
- **Real-world Architecture**: Creating production-ready peer-to-peer applications

## Workshop Structure

The workshop consists of 8 progressive lessons with 5 interactive checkpoints where you'll connect to the instructor's server to demonstrate your progress. Each checkpoint includes prizes for the fastest participants!

### Lesson Overview

1. **Identity and Basic Swarm** (Lesson 1): Generate keypairs, create PeerIDs, and set up a basic libp2p swarm
2. **TCP Transport and Dialing** (Lesson 2): Implement TCP transport with Noise encryption and Yamux multiplexing
3. **Ping Checkpoint** (Lesson 3): 🏆 First checkpoint - implement ping protocol for connectivity testing
4. **QUIC Transport** (Lesson 4): Add QUIC transport for modern UDP-based communication
5. **Identify Checkpoint** (Lesson 5): 🏆 Second checkpoint - exchange peer information using identify protocol
6. **Gossipsub Checkpoint** (Lesson 6): 🏆 Third checkpoint - implement pub/sub messaging with gossipsub
7. **Kademlia Checkpoint** (Lesson 7): 🏆 Fourth checkpoint - peer discovery using Kademlia DHT
8. **Final Checkpoint** (Lesson 8): 🏆 Final checkpoint - complete universal connectivity with chat messaging

## Prerequisites

- **Rust Knowledge**: Familiarity with Rust syntax and basic async/await concepts
- **Networking Basics**: Understanding of IP addresses, ports, and basic networking
- **Development Environment**: Rust toolchain (rustc, cargo) installed and working

## Workshop Format

This is an interactive, instructor-led workshop designed for classroom settings. You'll work through exercises step-by-step, with:

- **Clear Learning Objectives**: Each lesson focuses on specific concepts and skills
- **Hands-on Exercises**: Practical coding challenges that build real functionality
- **Progressive Hints**: Multiple levels of help, from gentle nudges to complete solutions
- **Competitive Elements**: Timed checkpoints with prizes to maintain engagement
- **Collaborative Learning**: Opportunities to help peers and learn from each other

## Final Application

By the end of this workshop, you'll have built a complete universal connectivity application featuring:

- **Multi-transport connectivity**: TCP and QUIC transports for different network conditions
- **Security and multiplexing**: Noise encryption and Yamux stream multiplexing
- **Health monitoring**: Ping protocol for connection health and latency measurement
- **Peer discovery**: Kademlia DHT for finding and connecting to other peers
- **Peer information exchange**: Identify protocol for sharing capabilities and metadata
- **Real-time messaging**: Gossipsub pub/sub for chat and group communication
- **Protocol integration**: All libp2p protocols working together seamlessly
- **Production-ready architecture**: Proper error handling and event-driven design

Get ready to dive deep into the world of peer-to-peer networking with rust-libp2p!
