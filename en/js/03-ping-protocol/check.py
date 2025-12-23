#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check script for Lesson 3: Ping Checkpoint
Validates that the student's solution can ping remote peers and measure round-trip times.
"""

import subprocess
import sys
import os
import re
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

        # CSV-based sequence from unified checker:
        #   connected,<peerId>,<remote-multiaddr>
        #   ping,<peerId>,<rtt> ms
        #   closed,<peerId>

        # 1. Connection established
        conn_open_pattern = r"connected,(12D3KooW[\w]+),([^\n]+)"
        conn_match = re.search(conn_open_pattern, output)
        if not conn_match:
            print("x No connection established")
            print(f"i Actual output: {repr(output)}")
            return False

        peerid = conn_match.group(1)
        remote_addr = conn_match.group(2).strip()

        # validate peer id and multiaddrs
        valid, peerid_message = validate_peer_id(peerid)
        if not valid:
            print(f"x {peerid_message}")
            return False

        # validate remote addr
        valid, addr_msg = validate_multiaddr(remote_addr)
        if not valid:
            print(f"x {addr_msg}")
            return False

        print(f"v Connection opened with peer {peerid_message}")

        # 2. Ping RTT line
        ping_pattern = r"ping,12D3KooW[\w]+,(\d+\s*ms)"
        ping_match = re.search(ping_pattern, output)
        if not ping_match:
            print("x Ping RTT not reported")
            print(f"i Actual output: {repr(output)}")
            return False

        ms = ping_match.group(1)
        print(f"v Ping round-trip time reported: {ms}")

        # 3. Peer disconnected/closed line
        peer_disc_pattern = r"closed\s*,\s*(12D3KooW[\w]+)"
        disc_match = re.search(peer_disc_pattern, output)
        if not disc_match:
            print("x Connection closed message not found")
            return False

        disc_peerid = disc_match.group(1)
        if disc_peerid != peerid:
            print("x Disconnected peer id does not match connected peer id")
            return False
        print(f"v Connection with {peerid_message} closed gracefully")

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
        print("Ready for Lesson 4: Circuit Relay-V2!")
        
        return True
        
    except Exception as e:
        print(f"x Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)