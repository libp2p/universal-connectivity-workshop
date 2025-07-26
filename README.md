![libp2p](https://raw.githubusercontent.com/libp2p/universal-connectivity-workshop/main/libp2p.png)

# Universal Connectivity Workshop

Welcome to the Universal Connectivity Workshop! This hands-on workshop teaches you how to build peer-to-peer applications using libp2p, the powerful networking stack for decentralized applications.

## Quick Start (All)

1. Make sure you have [Python3 installed](https://www.python.org/downloads/).
2. Make sure you have [Git installed](https://git-scm.com/downloads).
3. Make sure you have [Docker and Docker Compose installed](https://docs.docker.com/get-docker/).

The `workshop` tool will try to detect Python3, Git, and Docker Compose on your system. It will give you an error if it cannot find them. They must be installed so that `workshop` can find them for this to work.

## Quick Start (Rust)

1. Make sure you have [Rust installed](https://rustup.rs/).
2. Intall the `workshop` tool:
   ```bash
   cargo install workshop
   ```
3. Install this workshop:
   ```bash
   workshop --install https://github.com/libp2p/universal-connectivity-workshop
   ```
4. Start the workshop in one terminal window:
   ```bash
   workshop
   ```
5. Follow the setup instructions `workshop` shows you in a second terminal window.
6. Select the workshop.
6. Complete all lessons.

## Status

This workshop has been ported to multiple programming languages and translated into multiple spoken languages.

Programming Languages:
 - **Rust**: Lessons 1 and 2 are confirmed to work, Lessons 3-8 are in progress.

Spoken Languages:
 - **English**

## What You'll Learn

Throughout this workshop, you'll build a complete [universal connectivity application](https://github.com/libp2p/universal-connectivity) from scratch, learning:

- **libp2p Fundamentals**: Peer identity, transport layers, and protocol composition
- **Network Protocols**: TCP, QUIC, and WebRTC transports for different connectivity scenarios
- **Peer Discovery**: Using Kademlia DHT and identify protocols for automatic peer discovery
- **Group Communication**: Implementing chat functionality with gossipsub pub/sub messaging

## Workshop Structure

The workshop consists of 7 progressive lessons with 4 interactive checkpoints where you'll connect to another peer to demonstrate your progress.

### Current Lesson Structure

1. **Identity and Basic Swarm** (Lesson 1): Create a basic swarm and set up peer identity
2. **TCP Transport** (Lesson 2): Implement TCP transport layer for connectivity
3. **Ping Checkpoint 🏆** (Lesson 3): Connect to a remote peer and send ping
4. **QUIC Transport** (Lesson 4): Add QUIC transport for improved connectivity
5. **Identify Checkpoint 🏆** (Lesson 5): Exchange peer information and capabilities
6. **Gossipsub Checkpoint 🏆** (Lesson 6): Implement pub/sub messaging for group communication
7. **Kademlia Checkpoint 🏆** (Lesson 7): Use DHT for distributed peer discovery and content routing

### Checkpoints Overview

1. **Ping Connection** (Lesson 3): Connect to a remote peer and send ping
2. **Identify Protocol** (Lesson 5): Extract peer information from a remote peer
3. **Gossipsub Messaging** (Lesson 6): Join a remote peer's chat room and send messages
4. **Kademlia Discovery** (Lesson 7): Use DHT to discover the multiaddr of a remote peer

## Prerequisites

- **Programming Knowledge**: Familiarity with writing applications in your favorite programming language
- **Networking Basics**: Understanding of IP addresses, ports, and basic networking
- **Development Environment**: A working development setup for your favorite programming language

## Workshop Format

This is an interactive workshop designed for classroom settings although you may complete these on your own as well. You'll work through exercises step-by-step, with:

- **Clear Learning Objectives**: Each lesson focuses on specific concepts and skills
- **Hands-on Exercises**: Practical coding challenges that build real functionality
- **Progressive Hints**: Multiple levels of help, from gentle nudges to complete solutions
- **Competitive Elements**: Timed checkpoints with prizes to maintain engagement
- **Collaborative Learning**: Opportunities to help peers and learn from each other

## Final Application

By the end of this workshop, you'll have built a peer-to-peer networking application featuring:

- Multi-transport connectivity (TCP, QUIC)
- Peer identity management and swarm networking
- Bidirectional connectivity with ping protocol
- Peer information exchange with identify protocol
- Group communication with gossipsub pub/sub messaging
- Distributed peer discovery with Kademlia DHT

Get ready to dive deep into the world of peer-to-peer networking with libp2p!
