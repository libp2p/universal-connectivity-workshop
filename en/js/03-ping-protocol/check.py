#!/usr/bin/env python3
"""
Check script for Lesson 3: Ping Checkpoint
Validates that the student's solution can ping remote peers and measure round-trip times.
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
    
    return True, f"{peer_id_str}"

def validate_multiaddr(addr_str):
    """Validate that the address string looks like a valid multiaddr"""
    # Basic multiaddr validation - should start with /ip4/ or /ip6/
    if not (addr_str.startswith("/ip4/") or addr_str.startswith("/ip6/")):
        return False, f"Invalid multiaddr format: {addr_str}"
    
    # Should contain /tcp for TCP transport or /quic-v1 for QUIC transport
    if not ("/tcp" in addr_str or "/quic-v1" in addr_str):
        return False, f"Missing TCP or QUIC transport in multiaddr: {addr_str}"
     
    return True, f"{addr_str}"

def check_output():
    """Check the output log for expected TCP transport functionality"""
    if not os.path.exists("checker.log"):
        print("x checker.log file not found")
        return False
    
    try:
        with open("checker.log", "r") as f:
            output = f.read()
        
        print("i Checking ping functionality...")
        
        if not output.strip():
            print("x checker.log is empty - application may have failed to start")
            return False

        # a correct solution causes the checker to output a sequence of messages like the following:
        # incoming,/ip4/172.16.16.17/tcp/9092,/ip4/172.16.16.16/tcp/41972
        # connected,12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE,/ip4/172.16.16.16/tcp/41972
        # ping,12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE,10 ms
        # closed,12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE

        # check for:
        #   incoming,/ip4/172.16.16.17/tcp/9092,/ip4/172.16.16.16/tcp/41972
        incoming_pattern = r"incoming,([/\w\.:]+),([/\w\.:]+)"
        incoming_matches = re.search(incoming_pattern, output)
        if not incoming_matches:
            print("x No incoming dial received")
            print(f"i Actual output: {repr(output)}")
            return False

        t = incoming_matches.group(1)
        valid, t_message = validate_multiaddr(t)
        if not valid:
            print(f"x {t_message}")
            return False
        
        f = incoming_matches.group(2)
        valid, f_message = validate_multiaddr(f)
        if not valid:
            print(f"x {f_message}")
            return False

        print(f"v Your peer at {f_message} dialed remote peer at {t_message}")

        # check for:
        #   connected,12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE,/ip4/172.16.16.16/tcp/41972
        connected_pattern = r"connected,(12D3KooW[A-Za-z0-9]+),([/\w\.:]+)"
        connected_matches = re.search(connected_pattern, output)
        if not connected_matches:
            print("x No connection established")
            print(f"i Actual output: {repr(output)}")
            return False

        peerid = connected_matches.group(1)
        valid, peerid_message = validate_peer_id(peerid)
        if not valid:
            print(f"x {peerid_message}")
            return False
        
        f = connected_matches.group(2)
        valid, f_message = validate_multiaddr(f)
        if not valid:
            print(f"x {f_message}")
            return False

        print(f"v Connection established with {peerid_message} at {f_message}")

        # check for:
        #   ping,12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE,10 ms
        ping_pattern = r"ping,(12D3KooW[A-Za-z0-9]+),(\d+\s*ms)"
        ping_matches = re.search(ping_pattern, output)
        if not ping_matches:
            print("x No ping received")
            print(f"i Actual output: {repr(output)}")
            return False

        peerid = ping_matches.group(1)
        valid, peerid_message = validate_peer_id(peerid)
        if not valid:
            print(f"x {peerid_message}")
            return False
        
        ms = ping_matches.group(2)

        print(f"v Ping received from {peerid_message} with RTT {ms}")

        # check for:
        #   closed,12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE
        closed_pattern = r"closed,(12D3KooW[A-Za-z0-9]+)"
        closed_matches = re.search(closed_pattern, output)
        if not closed_matches:
            print("x Connection closure not detected")
            print(f"i Actual output: {repr(output)}")
            return False
        
        peerid = connected_matches.group(1)
        valid, peerid_message = validate_peer_id(peerid)
        if not valid:
            print(f"x {peerid_message}")
            return False
        
        print(f"v Connection {peerid_message} closed gracefully")

        return True
        
    except Exception as e:
        print(f"x Error reading checker.log: {e}")
        return False

def main():
    """Main check function"""
    print("i Checking Lesson 3: Ping Checkpoint 🏆")
    print("i " + "=" * 50)
    
    try:
        # Check the output
        if not check_output():
            return False
        
        print("i " + "=" * 50)
        print("y Ping checkpoint completed successfully! 🎉")
        print("i You have successfully:")
        print("i • Configured ping protocol with custom intervals")
        print("i • Established bidirectional connectivity")
        print("i • Measured round-trip times between peers")
        print("i • Reached your first checkpoint!")
        print("Ready for Lesson 4: QUIC Transport!")
        
        return True
        
    except Exception as e:
        print(f"x Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)