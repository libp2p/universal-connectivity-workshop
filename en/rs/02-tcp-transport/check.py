#!/usr/bin/env python3
"""
Check script for Lesson 2: TCP Transport
Validates that the student's solution can listen and handle connections.
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

#TODO: change this to use py-multiaddr for Multiaddr validation
def validate_multiaddr(addr_str):
    """Validate that the address string looks like a valid multiaddr"""
    # Basic multiaddr validation - should start with /ip4/ or /ip6/
    if not (addr_str.startswith("/ip4/") or addr_str.startswith("/ip6/")):
        return False, f"Invalid multiaddr format: {addr_str}"
    
    # Should contain /tcp/ for TCP transport
    if "/tcp/" not in addr_str:
        return False, f"Missing TCP transport in multiaddr: {addr_str}"
    
    return True, f"Valid multiaddr: {addr_str}"

def check_output():
    """Check the output log for expected TCP transport functionality"""
    if not os.path.exists("stdout.log"):
        print("x stdout.log file not found")
        return False
    
    try:
        with open("stdout.log", "r") as f:
            output = f.read()
        
        print("i Checking TCP transport functionality...")
        
        if not output.strip():
            print("x stdout.log is empty - application may have failed to start")
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
        
        # Check for dialing multiaddr
        dial_multiaddr_pattern = r"Dialing: ([/\w\.:]+)"
        dial_multiaddr_matches = re.search(dial_multiaddr_pattern, output)
        
        if not dial_multiaddr_matches:
            print("x No dialed multiaddr found. Expected format: 'Dialing: /ip4/.../tcp/...'")
            print(f"i Actual output: {repr(output)}")
            return False

        multiaddr = dial_multiaddr_matches.group(1)
        valid, message = validate_multiaddr(multiaddr)
        if not valid:
            print(f"x {message}")
            return False
        
        print(f"v {message}")

        # Check for "Connected to: {peer_id}" message
        connected_pattern = rf"Connected to: (12D3KooW[A-Za-z0-9]+) via {re.escape(multiaddr)}"
        connected_match = re.search(connected_pattern, output)
        if not connected_match:
            print(f"x Missing connection message")
            print(f"i Expected pattern: {connected_pattern}")
            print(f"i Actual output: {repr(output)}")
            return False

        remote_peer_id = connected_match.group(1)

        # Check for "Connection to {peer_id} closed gracefully" message
        closed_pattern = rf"Connection to {re.escape(remote_peer_id)} closed gracefully"
        if re.search(closed_pattern, output):
            print(f"v Found graceful closure message for peer ID: {remote_peer_id}")
        else:
            print(f"x Missing graceful closure message for peer ID: {remote_peer_id}")
            print(f"i Actual output: {repr(output)}")
            return False
        
        # Check that application runs for reasonable time without crashing
        lines = output.strip().split('\n')
        if len(lines) < 3:  # Should have startup, peer id, and at least one listening address
            print("x Application seems to have crashed too quickly")
            print(f"i Output lines: {lines}")
            return False
        
        print("v Application started successfully with TCP transport")
        
        return True
        
    except Exception as e:
        print(f"x Error reading stdout.log: {e}")
        return False

def main():
    """Main check function"""
    print("i Checking Lesson 2: TCP Transport")
    print("i " + "=" * 50)
    
    try:
        # Check the output
        if not check_output():
            return False
        
        print("i " + "=" * 50)
        print("y TCP transport lesson completed successfully!")
        print("i You have successfully:")
        print("i • Configured TCP transport with Noise and Yamux")
        print("i • Dialed a remote peer")
        print("i • Handled connection events properly")
        print("i • Created a foundation for peer-to-peer communication")
        print("Ready for Lesson 3: Ping Checkpoint!")
        
        return True
        
    except Exception as e:
        print(f"x Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
