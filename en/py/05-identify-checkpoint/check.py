#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check script for the Universal Connectivity Program (Identify Checkpoint)
Validates that the program's output shows it can connect, identify, and ping remote peers.
"""
import os
import re
import sys
import io

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Regex to capture a standard libp2p PeerID
PEER_ID_REGEX = r"(12D3KooW[A-Za-z0-9]+)"

def check_output():
    """Check the output log for expected identify checkpoint functionality"""
    
    # 1. Check if the log file exists
    if not os.path.exists("checker.log"):
        print("! checker.log file not found.")
        print("i Please run your program and redirect its output to checker.log")
        print("i Example: python main.py [ARGS] > checker.log 2>&1")
        return False
    
    try:
        with open("checker.log", "r") as f:
            output = f.read()
        print("i Checking identify functionality...")

        # 2. Check if the log is empty
        if not output.strip():
            print("! checker.log is empty - application may have failed to start")
            return False
        
        # 3. Check for successful connection
        # Looks for: "...Connected to: 12D3Koo..."
        connected_pattern = re.compile(r"Connected to: " + PEER_ID_REGEX)
        connected_match = connected_pattern.search(output)
        
        if not connected_match:
            print("! No successful connection message found (e.g., 'Connected to: ...')")
            print(f"i Actual output (first 500 chars): {repr(output[:500])}...")
            return False
        
        peer_id = connected_match.group(1)
        print(f"v Connection established with peer: {peer_id}")

        # 4. Check for sending identify request
        # Looks for: "[IDENTIFY] Sending identify request to 12D3Koo..."
        identify_sent_pattern = re.compile(r"\[IDENTIFY\] Sending identify request to " + re.escape(peer_id))
        if not identify_sent_pattern.search(output):
            print(f"! Did not find message for sending identify request to {peer_id}")
            return False
        
        print(f"v Sent identify request to {peer_id}")

        # 5. Check for receiving identify response
        # Looks for: "[IDENTIFY] Identified peer: 12D3Koo..."
        identify_recv_pattern = re.compile(r"\[IDENTIFY\] Identified peer: " + re.escape(peer_id))
        if not identify_recv_pattern.search(output):
            print(f"! Did not receive identify response from {peer_id}")
            return False

        print(f"v Received identify response from {peer_id}")

        # 6. Check for agent version
        # Looks for: "[IDENTIFY] Agent: universal-connectivity/0.1.0"
        agent_pattern = re.compile(r"\[IDENTIFY\] Agent: ([\w\./-]+)")
        agent_match = agent_pattern.search(output)
        if not agent_match:
            print(f"! Did not find agent version in identify response")
            return False
        
        print(f"v Identified remote agent: {agent_match.group(1)}")

        # 7. Check for protocol version
        # Looks for: "[IDENTIFY] Protocol version: /ipfs/0.1.0"
        proto_ver_pattern = re.compile(r"\[IDENTIFY\] Protocol version: ([\w\./-]+)")
        proto_ver_match = proto_ver_pattern.search(output)
        if not proto_ver_match:
            print(f"! Did not find protocol version in identify response")
            return False
        
        print(f"v Identified remote protocol version: {proto_ver_match.group(1)}")

        # 8. Check for at least one successful ping
        # Looks for: "[PING] Ping to 12D3Koo...: RTT 12.34ms"
        ping_pattern = re.compile(r"\[PING\] Ping to " + re.escape(peer_id) + r": RTT ([\d\.]+)ms")
        if not ping_pattern.search(output):
            print(f"w No successful ping message found for {peer_id}.")
            # This is a warning, not a failure, as identify is the main goal.
        else:
            print(f"v Successful ping to {peer_id} detected.")

        # If all checks passed
        return True

    except Exception as e:
        print(f"! Error reading or parsing checker.log: {e}")
        return False

def main():
    """Main check function"""
    print("i Checking Universal Connectivity: Identify Checkpoint")
    print("i " + "=" * 50)
    try:
        if not check_output():
            print("i " + "=" * 50)
            print("! Check failed.")
            return False
        
        print("i " + "=" * 50)
        print("v Identify checkpoint completed successfully!")
        print("i You have successfully:")
        print("i • Connected to a remote peer")
        print("i • Sent an identify request")
        print("i • Received and displayed the peer's identify information (Agent, Protocol)")
        return True
    except Exception as e:
        print(f"! Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)