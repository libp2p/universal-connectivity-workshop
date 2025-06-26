#!/usr/bin/env python3
"""
Check script for Lesson 1: Identity and Basic Swarm
Validates that the student's solution creates a libp2p node with identity.
"""

import subprocess
import sys
import os
import re

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

def check_output():
    """Check the output log for expected content"""
    if not os.path.exists("stdout.log"):
        print("x Error: stdout.log file not found")
        return False
    
    try:
        with open("stdout.log", "r") as f:
            output = f.read()
        
        print("i Checking application output...")
        
        if not output.strip():
            print("x stdout.log is empty - application may have failed to start")
            return False
        
        # Check for startup message
        if "Starting Universal Connectivity Application".lower() not in output.lower():
            print("x Missing startup message. Expected: 'Starting Universal Connectivity Application...'")
            print(f"i Actual output: {repr(output)}")
            return False
        print("v Found startup message")
        
        # Check for peer ID output with exact format
        peer_id_pattern = r"Local peer id: (12D3KooW[A-Za-z0-9]+)"
        peer_id_match = re.search(peer_id_pattern, output)
        
        if not peer_id_match:
            print("x Missing peer ID output. Expected format: 'Local peer id: 12D3KooW...'")
            print(f"i Actual output: {repr(output)}")
            return False
        
        peer_id = peer_id_match.group(1)
        
        # Validate the peer ID format
        valid, message = validate_peer_id(peer_id)
        if not valid:
            print(f"x {message}")
            return False
        
        print(f"v {message}")
        
        # Check that the application runs without immediate crash
        lines = output.strip().split('\n')
        if len(lines) < 2:
            print("x Application seems to have crashed immediately after startup")
            print(f"i Output lines: {lines}")
            return False
        
        print("v Application started successfully and generated valid peer identity")
        return True
        
    except Exception as e:
        print(f"x Error reading stdout.log: {e}")
        return False

def main():
    """Main check function"""
    print("i Checking Lesson 1: Identity and Basic Swarm")
    print("i " + "=" * 50)
    
    try:
        # Check the output
        if not check_output():
            return False
        
        print("i " + "=" * 50)
        print("y All checks passed! Your libp2p node is working correctly.")
        print("i You have successfully:")
        print("i • Created a libp2p node with a stable Ed25519 identity")
        print("i • Generated and displayed a valid peer ID")
        print("i • Set up a basic event loop")
        print("Ready for Lesson 2: TCP Transport!")
        
        return True
        
    except Exception as e:
        print(f"Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
