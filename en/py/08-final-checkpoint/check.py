#!/usr/bin/env python3
"""
Check script for Lesson 8: Final Checkpoint
Validates that the student's solution implements the complete universal connectivity system
with ping, identify, gossipsub, kademlia, and chat messaging.
"""

import subprocess
import sys
import os
import re

#TODO: change this to use py-libp2p for PeerID validation
def validate_peer_id(peer_id_str):
    """Validate that the peer ID string is a valid libp2p PeerId format"""
    # Basic format validation - should start with 12D3KooW (Ed25519 peer IDs)
    if not peer_id_str.startswith("12D3KooW"):
        return False, f"Invalid peer ID format. Expected to start with '12D3KooW', got: {peer_id_str}"
    
    # Length check - valid peer IDs should be around 52-55 characters
    if len(peer_id_str) < 45 or len(peer_id_str) > 60:
        return False, f"Peer ID length seems invalid. Expected 45-60 chars, got {len(peer_id_str)}: {peer_id_str}"
    
    # Character set validation - should only contain base58 characters
    valid_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    for char in peer_id_str:
        if char not in valid_chars:
            return False, f"Invalid character '{char}' in peer ID. Must be base58 encoded."
    
    return True, f"Valid peer ID format: {peer_id_str}"

def validate_multiaddr(addr_str):
    """Validate that the address string looks like a valid multiaddr"""
    # Basic multiaddr validation - should start with /ip4/ or /ip6/
    if not (addr_str.startswith("/ip4/") or addr_str.startswith("/ip6/")):
        return False, f"Invalid multiaddr format: {addr_str}"
    
    # Should contain /tcp for TCP transport or /quic-v1 for QUIC transport
    if not ("/tcp" in addr_str or "/quic-v1" in addr_str):
        return False, f"Missing TCP or QUIC transport in multiaddr: {addr_str}"
     
    return True, f"Valid multiaddr: {addr_str}"

def check_output():
    """Check the output log for expected final checkpoint functionality"""
    if not os.path.exists("checker.log"):
        print("x checker.log file not found")
        return False
    
    try:
        with open("checker.log", "r") as f:
            output = f.read()
        
        print("i Checking final checkpoint functionality...")
        
        if not output.strip():
            print("x checker.log is empty - application may have failed to start")
            return False
        
        # Check for startup message
        if "Starting Universal Connectivity Application".lower() not in output.lower():
            print("x Missing startup message. Expected: 'Starting Universal Connectivity application...'")
            print(f"i Actual output: {repr(output)}")
            return False
        print("v Found startup message")
        
        # Check for peer ID output
        peer_id_pattern = r"Local peer id: (12D3KooW[A-Za-z0-9]+)"
        peer_id_match = re.search(peer_id_pattern, output)
        
        if not peer_id_match:
            print("x Missing peer ID output. Expected format: 'Local peer id: 12D3KooW...'")
            print(f"i Actual output: {repr(output)}")
            return False
        
        peer_id = peer_id_match.group(1)
        print(f"v Found peer ID: {peer_id}")

        # Validate the peer ID format
        valid, message = validate_peer_id(peer_id)
        if not valid:
            print(f"x {message}")
            return False
        print(f"v {message}")
        
        # Check for connection messages
        connected_pattern = r"Connected to: (12D3KooW[A-Za-z0-9]+) via"
        connected_matches = re.findall(connected_pattern, output)
        
        if not connected_matches:
            print("x No connected peers found. Expected format: 'Connected to: 12D3KooW... via ...'")
            print(f"i Actual output: {repr(output)}")
            return False
        print(f"v Found {len(connected_matches)} peer connection(s)")

        # Check for ping messages
        ping_pattern = r"Received a ping from (12D3KooW[A-Za-z0-9]+), round trip time: (\d+) ms"
        ping_matches = re.findall(ping_pattern, output)
        
        if not ping_matches:
            print("x No ping messages found. Expected format: 'Received a ping from 12D3KooW..., round trip time: X ms'")
            print(f"i Actual output: {repr(output)}")
            return False
        print(f"v Found {len(ping_matches)} ping message(s)")

        # Check for identify messages
        identify_pattern = r"Received identify from (12D3KooW[A-Za-z0-9]+): protocol_version:"
        identify_matches = re.findall(identify_pattern, output)
        
        if not identify_matches:
            print("x No identify messages found. Expected format: 'Received identify from 12D3KooW...: protocol_version: ...'")
            print(f"i Actual output: {repr(output)}")
            return False
        print(f"v Found {len(identify_matches)} identify message(s)")

        # Check for gossipsub messages (chat messages)
        chat_pattern = r"Received chat message from (12D3KooW[A-Za-z0-9]+):"
        chat_matches = re.findall(chat_pattern, output)
        
        if not chat_matches:
            print("x No chat messages found. Expected format: 'Received chat message from 12D3KooW...: ...'")
            print(f"i Actual output: {repr(output)}")
            return False
        print(f"v Found {len(chat_matches)} chat message(s)")

        # Check for kademlia messages (optional for basic functionality)
        kademlia_pattern = r"Kademlia bootstrap"
        if re.search(kademlia_pattern, output):
            print("v Found Kademlia bootstrap messages")
        else:
            print("i No Kademlia bootstrap messages found (this is optional)")
        
        # Check that application runs for reasonable time without crashing
        lines = output.strip().split('\n')
        if len(lines) < 5:  # Should have startup, peer id, connections, pings, identifies, and chat
            print("x Application seems to have crashed too quickly")
            print(f"i Output lines: {lines}")
            return False
        
        print("v Application completed final checkpoint successfully")
        
        return True
        
    except Exception as e:
        print(f"x Error reading checker.log: {e}")
        return False

def main():
    """Main check function"""
    print("i Checking Lesson 8: Final Checkpoint")
    print("i " + "=" * 50)
    
    try:
        # Check the output
        if not check_output():
            return False
        
        print("i " + "=" * 50)
        print("y Final checkpoint completed successfully!")
        print("i You have successfully implemented:")
        print("i • Complete libp2p swarm with multiple transports")
        print("i • Ping protocol for connectivity testing")
        print("i • Identify protocol for peer information exchange")
        print("i • Gossipsub for pub/sub messaging")
        print("i • Kademlia DHT for peer discovery")
        print("i • Chat messaging using universal connectivity protocol")
        print("i • Multi-protocol peer-to-peer communication system")
        print("🏆 Congratulations! You've completed the Universal Connectivity Workshop!")
        
        return True
        
    except Exception as e:
        print(f"x Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)