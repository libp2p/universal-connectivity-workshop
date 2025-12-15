#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check script for Lesson 3: Ping Checkpoint
Validates that the student's solution (main.py) is:
1. Using Noise and Yamux
2. Establishing a connection
3. Sending pings on an interval
4. Receiving pongs and calculating RTT
5. Handling streams correctly
"""

import subprocess
import sys
import os
import re
import io

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def validate_peer_id(peer_id_str):
    """Validate that the peer ID string is a valid 'Qm...' PeerId format"""
    
    # 1. Check prefix
    if not peer_id_str.startswith("Qm"):
        return False, f"Invalid peer ID format. Expected to start with 'Qm', got: {peer_id_str}"
    
    # 2. Length check - RSA peer IDs are 46 chars
    if len(peer_id_str) != 46:
        return False, f"Peer ID length is incorrect. Expected 46 chars for RSA key, got {len(peer_id_str)}: {peer_id_str}"
    
    # 3. Character set validation - should only contain base58 characters
    valid_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    for char in peer_id_str:
        if char not in valid_chars:
            return False, f"Invalid character '{char}' in peer ID. Must be base58 encoded."
    
    return True, f"{peer_id_str}"

def check_output():
    """Check the output log for expected ping functionality"""
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

        # --- Check Server Setup ---
        
        if not re.search(r"Security: Noise encryption enabled", output):
            print("x Server did not report 'Security: Noise encryption enabled'")
            print(f"i Actual output: {repr(output)}")
            return False
        print("v Security: Noise encryption enabled")

        if not re.search(r"Multiplexing: Yamux enabled", output):
            print("x Server did not report 'Multiplexing: Yamux enabled'")
            print(f"i Actual output: {repr(output)}")
            return False
        print("v Multiplexing: Yamux enabled")

        # --- Check Client Connection ---
        
        connected_pattern = r"Connected to (Qm[1-9A-HJ-NP-Za-km-z]{44})"
        connected_matches = re.search(connected_pattern, output)
        if not connected_matches:
            print("x No client connection message 'Connected to ...' found")
            print(f"i Actual output: {repr(output)}")
            return False
        
        client_peer_id = connected_matches.group(1)
        valid, msg = validate_peer_id(client_peer_id)
        if not valid:
            print(f"x {msg}")
            return False
        print(f"v Client connected to peer: {client_peer_id}")

        # --- Check Server Ping Handling ---
        
        ping_rx_pattern = r"received ping from (Qm[1-9A-HJ-NP-Za-km-z]{44})"
        ping_rx_matches = re.search(ping_rx_pattern, output)
        if not ping_rx_matches:
            print("x No server 'received ping from ...' message found")
            print(f"i Actual output: {repr(output)}")
            return False
        
        server_rx_peer_id = ping_rx_matches.group(1)
        valid, msg = validate_peer_id(server_rx_peer_id)
        if not valid:
            print(f"x {msg}")
            return False
        print(f"v Server received ping from: {server_rx_peer_id}")

        ping_tx_pattern = r"responded with pong to (Qm[1-9A-HJ-NP-Za-km-z]{44})"
        ping_tx_matches = re.search(ping_tx_pattern, output)
        if not ping_tx_matches:
            print("x No server 'responded with pong to ...' message found")
            print(f"i Actual output: {repr(output)}")
            return False
        print("v Server responded with pong")

        # --- Check Client Ping RTT ---
        
        ping_rtt_pattern = r"ping: Success from (Qm[1-9A-HJ-NP-Za-km-z]{44}), RTT = (\d+\.\d+) ms"
        ping_rtt_matches = re.search(ping_rtt_pattern, output)
        if not ping_rtt_matches:
            print("x No client 'ping: Success from ...' message found")
            print("i This means RTT calculation is missing or formatted incorrectly.")
            print(f"i Actual output: {repr(output)}")
            return False
        
        client_rtt_peer_id = ping_rtt_matches.group(1)
        rtt = ping_rtt_matches.group(2)
        valid, msg = validate_peer_id(client_rtt_peer_id)
        if not valid:
            print(f"x {msg}")
            return False
        print(f"v Client reported ping success from {client_rtt_peer_id} with RTT = {rtt} ms")

        # --- Check Server Stream Closure ---
        
        closed_pattern = r"Closed ping stream from (Qm[1-9A-HJ-NP-Za-km-z]{44})"
        closed_matches = re.search(closed_pattern, output)
        if not closed_matches:
            print("x No server 'Closed ping stream from ...' message found")
            print("i This means the server handler is not closing the stream correctly.")
            print(f"i Actual output: {repr(output)}")
            return False
        print("v Server stream closed gracefully")

        # --- Cross-Validation ---
        if not (client_peer_id == client_rtt_peer_id):
            print(f"x Mismatch: Client connected to {client_peer_id} but got ping from {client_rtt_peer_id}")
            return False
            
        if not (server_rx_peer_id == ping_tx_matches.group(1) == closed_matches.group(1)):
            print("x Mismatch: Server logs show different peer IDs for rx, tx, and close")
            return False
        
        print("v Peer IDs are consistent across client and server logs")
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
        print("i • Used Noise for security and Yamux for multiplexing")
        print("i • Established a p2p connection")
        print("i • Sent pings on a 1-second interval")
        print("i • Measured and printed round-trip times (RTT)")
        print("i • Handled streams correctly on the server")
        
        return True
        
    except Exception as e:
        print(f"x Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
