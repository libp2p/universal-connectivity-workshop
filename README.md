![libp2p](https://raw.githubusercontent.com/libp2p/universal-connectivity-workshop/main/libp2p.png)

# Building Universal Connectivity with **lib**p2p

Welcome to the Universal Connectivity Workshop! This hands-on workshop teaches you how to build peer-to-peer applications using libp2p, the powerful networking stack for decentralized applications.

## Status

This workshop has been ported to multiple programming languages and translated into multiple spoken languages.

Programming Languages:
 - **Rust**: uses [rust-libp2p](https://github.com/libp2p/rust-libp2p)

Spoken Languages:
 - **English**

## What You'll Learn

Throughout this workshop, you'll build a complete [universal connectivity application](https://github.com/libp2p/universal-connectivity) from scratch, learning:

- **libp2p Fundamentals**: Peer identity, transport layers, and protocol composition
- **Network Protocols**: TCP, QUIC, and WebRTC transports for different connectivity scenarios
- **Peer Discovery**: Using Kademlia DHT and identify protocols for automatic peer discovery
- **Group Communication**: Implementing chat functionality with gossipsub pub/sub messaging
- **NAT Traversal**: Overcoming network restrictions with relay servers and hole punching
- **Custom Protocols**: Building request-response protocols for file sharing
- **Production Readiness**: Creating a complete application with terminal UI and error handling

## Workshop Structure

The workshop consists of 12 progressive lessons with 5 interactive checkpoints where you'll connect to another peer to demonstrate your progress.

### Checkpoints Overview

1. **Ping Connection** (Lesson 3): Connect to a remote peer and send ping
2. **Identify Protocol** (Lesson 5): Extract peer information from a remote peer
3. **Kademlia Discovery** (Lesson 7): Use DHT to discover the multiaddr of a remote peer
4. **Chat Connection** (Lesson 8): Join a remote peer's chat room and send messages
5. **Final Application** (Lesson 12): Complete universal connectivity with all features

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

By the end of this workshop, you'll have built a complete universal connectivity application featuring:

- Multi-transport connectivity (TCP, QUIC, WebRTC)
- Automatic peer discovery via DHT
- Real-time group chat with gossipsub
- File sharing between peers
- NAT traversal capabilities

Get ready to dive deep into the world of peer-to-peer networking with libp2p!
