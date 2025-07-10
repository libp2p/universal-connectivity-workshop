#!/usr/bin/env python3
"""
Check script for Lesson 2: TCP Transport (Python)
Validates that the student's py-libp2p solution can connect and handle connections.
"""
import os
import re
import sys

def validate_peer_id(peer_id_str):
    """Validate that the peer ID string is a valid libp2p PeerId format"""
    # Basic format validation - should start with 12D3KooW (Ed25519 peer IDs)
    if not peer_id_str.startswith("12D3KooW"):
        return False, f"Invalid peer ID format. Expected to start with '12D3KooW', got: {peer_id_str}"
    
    # Length check - valid peer IDs should be around 45-60 characters
    if len(peer_id_str) < 45 or len(peer_id_str) > 60:
        return False, f"Peer ID length seems invalid. Expected 45-60 chars, got {len(peer_id_str)}: {peer_id_str}"
    
    # Character set validation - should only contain base58 characters
    valid_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    for char in peer_id_str:
        if char not in valid_chars:
            return False, f"Invalid character '{char}' in peer ID. Must be base58 encoded."
    
    return True, f"{peer_id_str}"

def validate_multiaddr(addr_str):
    """Validate that the address string looks like a valid multiaddr"""
    # Basic multiaddr validation - should start with /ip4/ or /ip6/
    if not (addr_str.startswith("/ip4/") or addr_str.startswith("/ip6/")):
        return False, f"Invalid multiaddr format: {addr_str}"
    
    # Should contain /tcp for TCP transport
    if "/tcp" not in addr_str:
        return False, f"Missing TCP transport in multiaddr: {addr_str}"
     
    return True, f"{addr_str}"

def check_output():
    """Check the output log for expected TCP transport functionality"""
    if not os.path.exists("checker.log"):
        print("✗ checker.log file not found")
        return False
    
    try:
        with open("checker.log", "r") as f:
            output = f.read()
        
        print("ℹ Checking TCP transport functionality...")
        
        if not output.strip():
            print("✗ checker.log is empty - checker may have failed to start")
            return False

        # A correct solution causes the checker to output a sequence of messages like:
        # incoming,/ip4/172.16.16.17/tcp/9092,listening
        # connected,12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE,('172.16.16.16', 41972)
        # closed,12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE

        # Check for incoming connection setup
        incoming_pattern = r"incoming,([/\w\.:-]+),listening"
        incoming_matches = re.search(incoming_pattern, output)
        if not incoming_matches:
            print("✗ No incoming connection listener setup detected")
            print(f"ℹ Actual output: {repr(output)}")
            return False

        listen_addr = incoming_matches.group(1)
        valid, addr_message = validate_multiaddr(listen_addr)
        if not valid:
            print(f"✗ {addr_message}")
            return False
        
        print(f"✓ Checker listening on {addr_message}")

        # Check for connection establishment
        connected_pattern = r"connected,(12D3KooW[A-Za-z0-9]+),\(['\"]([^'\"]+)['\"],\s*(\d+)\)"
        connected_matches = re.search(connected_pattern, output)
        if not connected_matches:
            print("✗ No connection established")
            print(f"ℹ Actual output: {repr(output)}")
            return False

        peer_id = connected_matches.group(1)
        remote_ip = connected_matches.group(2)
        remote_port = connected_matches.group(3)
        
        valid, peer_id_message = validate_peer_id(peer_id)
        if not valid:
            print(f"✗ {peer_id_message}")
            return False
        
        print(f"✓ Connection established with {peer_id_message} from {remote_ip}:{remote_port}")

        # Check for connection closure
        closed_pattern = r"closed,(12D3KooW[A-Za-z0-9]+)"
        closed_matches = re.search(closed_pattern, output)
        if not closed_matches:
            print("✗ Connection closure not detected")
            print(f"ℹ Actual output: {repr(output)}")
            return False
        
        closed_peer_id = closed_matches.group(1)
        valid, closed_peer_message = validate_peer_id(closed_peer_id)
        if not valid:
            print(f"✗ {closed_peer_message}")
            return False
        
        print(f"✓ Connection {closed_peer_message} closed gracefully")

        return True
        
    except Exception as e:
        print(f"✗ Error reading checker.log: {e}")
        return False

def main():
    """Main check function"""
    print("ℹ Checking Lesson 2: TCP Transport")
    print("ℹ " + "=" * 50)
    
    try:
        # Check the output
        if not check_output():
            return False
        
        print("ℹ " + "=" * 50)
        print("✓ TCP transport lesson completed successfully!")
        print("ℹ You have successfully:")
        print("ℹ • Configured TCP transport with Noise security")
        print("ℹ • Established connections with remote peers")
        print("ℹ • Handled connection events properly")
        print("ℹ • Created a foundation for peer-to-peer communication")
        print("ℹ Ready for Lesson 3: Ping Checkpoint!")
        
        return True
        
    except Exception as e:
        print(f"✗ Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)