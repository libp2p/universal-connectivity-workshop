#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import sys
import io

# Fix Windows encoding issues
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def validate_peer_id(peer_id_str):
    """Validate that the peer ID string is a valid libp2p PeerId format"""
    if not peer_id_str.startswith("12D3KooW"):
        return False, f"Invalid peer ID format. Expected to start with '12D3KooW', got: {peer_id_str}"

    if len(peer_id_str) < 45 or len(peer_id_str) > 60:
        return False, f"Peer ID length seems invalid. Expected 45-60 chars, got {len(peer_id_str)}: {peer_id_str}"

    valid_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    for char in peer_id_str:
        if char not in valid_chars:
            return False, f"Invalid character '{char}' in peer ID. Must be base58 encoded."

    return True, f"{peer_id_str}"

def check_checker_output():
    """Check the checker log for expected functionality"""
    checker_log = "checker.log"
    
    if not os.path.exists(checker_log):
        print("X No checker.log found from Docker container")
        return False

    try:
        with open(checker_log, "r") as f:
            output = f.read()

        print("i Found checker.log from Docker container")
        print("i Checking checker functionality (CSV events)...")

        if not output.strip():
            print("X Checker log is empty - checker may have failed to start")
            return False
        
        # Check for error messages in checker log
        if "Error:" in output or "error" in output.lower():
            error_lines = [line for line in output.split('\n') if 'error' in line.lower() or 'Error' in line]
            if error_lines:
                print(f"X Checker log contains errors:")
                for error_line in error_lines[:3]:  # Show first 3 errors
                    print(f"i   {error_line}")
                # Don't return False yet - errors might be non-fatal

        # Check for listening addresses (printed on startup)
        listening_lines = [line for line in output.split('\n') if line.startswith('listening,')]
        if listening_lines:
            print("+ Checker printed listening addresses on startup")
            for line in listening_lines[:2]:  # Show first 2 listening addresses
                addr = line.replace('listening,', '')
                if '/p2p/' in addr:
                    print(f"  ✓ {addr}")
        
        # CSV-based checks for interactive readiness
        # 1) Peer ID implied by any connected/subscribe/msg lines
        connected = re.search(r"connected,(12D3KooW[A-Za-z0-9]+),", output)
        subscribed = re.search(r"subscribe,(12D3KooW[A-Za-z0-9]+),universal-connectivity", output)
        any_msg = re.search(r"msg,(12D3KooW[A-Za-z0-9]+),universal-connectivity,", output)

        # At least connected OR subscribed should be present
        if not (connected or subscribed):
            print("X Checker did not receive connections or subscriptions yet")
            return False

        if connected:
            peer = connected.group(1)
            valid, _ = validate_peer_id(peer)
            if not valid:
                print("X Invalid peer id in connected event")
                return False
            print("+ Checker accepted connection from student app")

        if subscribed:
            print("+ Checker observed subscription to universal-connectivity topic")

        if any_msg:
            print("+ Checker observed a chat message on universal-connectivity")

        return True

    except Exception as e:
        print(f"X Error reading checker.log: {e}")
        return False

def check_output():
    """Check the output log for expected Universal Connectivity functionality"""
    log_file = "stdout.log"
    
    if not os.path.exists(log_file):
        print("X No stdout.log found from Docker container")
        return False

    try:
        with open(log_file, "r") as f:
            output = f.read()
        
        print("i Found stdout.log from Docker container")
        print("i Checking Universal Connectivity functionality...")

        if not output.strip():
            print("X Log file is empty - application may have failed to start")
            return False

        # Check for application startup
        if not re.search(r"Starting Universal Connectivity Application", output):
            print("X Application startup message not found")
            print("i Expected: 'Starting Universal Connectivity Application...'")
            return False
        
        print("+ Application started successfully")

        # Check for Peer ID
        peer_id_pattern = r"\[SYSTEM\] Generated Peer ID:\s*(12D3KooW[A-Za-z0-9]+)"
        peer_id_match = re.search(peer_id_pattern, output)
        
        if not peer_id_match:
            print("X Peer ID not found")
            print("i Expected: '[SYSTEM] Generated Peer ID: <peer_id>'")
            return False
        
        peer_id = peer_id_match.group(1)
        valid, message = validate_peer_id(peer_id)
        if not valid:
            print(f"X {message}")
            return False
        
        print(f"+ Peer ID generated: {peer_id}")

        # Check for node startup
        if not re.search(r"\[SYSTEM\] Node started successfully", output):
            print("X Node startup confirmation not found")
            return False
        
        print("+ Node started successfully")

        # Check for listening addresses
        listening_pattern = r"\[SYSTEM\] Listening on \d+ address\(es\)"
        if not re.search(listening_pattern, output):
            print("X Listening addresses not found")
            return False
        
        print("+ Node listening on addresses")

        # Check for protocol initialization
        protocols_found = 0
        
        # Check Identify
        if re.search(r"identify", output, re.IGNORECASE):
            print("+ Identify protocol detected")
            protocols_found += 1
        
        # Check Ping
        if re.search(r"ping", output, re.IGNORECASE):
            print("+ Ping protocol detected")
            protocols_found += 1
        
        # Check Gossipsub/Chat
        if re.search(r"\[CHAT\].*Subscribed to topic", output):
            print("+ Gossipsub (Chat) protocol initialized")
            protocols_found += 1
        
        # Check DHT
        if re.search(r"\[DHT\].*Kademlia|kad", output, re.IGNORECASE):
            print("+ Kademlia DHT initialized")
            protocols_found += 1

        if protocols_found < 3:
            print(f"X Insufficient protocols detected ({protocols_found}/4)")
            return False
        
        print(f"+ Multiple protocols working together ({protocols_found}/4 detected)")

        # Check for chat room initialization
        if not re.search(r"\[CHAT\].*Initializing chat room", output):
            print("X Chat room initialization not found")
            return False
        
        print("+ Chat room initialized")

        # Check for chat room join
        if not re.search(r"\[CHAT\] Joined chat room as:", output):
            print("X Chat room join confirmation not found")
            return False
        
        print("+ Successfully joined chat room")

        # Check for introduction message
        if re.search(r"ready to chat|has joined|introduction|hello", output, re.IGNORECASE):
            print("+ Introduction/welcome message sent")
        
        # Check for message publishing capability
        if re.search(r"\[CHAT\].*Publishing message|Message sent", output):
            print("+ Message publishing capability verified")
        
        # Check for system running
        if re.search(r"\[SYSTEM\].*Running|Listening for messages", output):
            print("+ System running and operational")

        return True

    except Exception as e:
        print(f"X Error reading stdout.log: {e}")
        return False

def main():
    """Main check function"""
    print("i Checking Lesson 8: Final Checkpoint - Universal Connectivity")
    print("i " + "=" * 60)

    try:
        # Check checker first
        print("\ni Step 1: Validating Checker Application")
        print("i " + "-" * 60)
        if not check_checker_output():
            print("X Checker validation failed")
            return False
        
        # Then check lesson output
        print("\ni Step 2: Validating Student Application")
        print("i " + "-" * 60)
        if not check_output():
            print("X Student application validation failed")
            return False

        print("i " + "=" * 60)
        print("+ Final Checkpoint completed successfully!")
        print("i You have successfully:")
        print("i - Integrated all libp2p protocols (TCP, Ping, Identify, Gossipsub, DHT)")
        print("i - Created a complete peer-to-peer communication system")
        print("i - Implemented chat messaging functionality")
        print("i - Connected to and communicated with the checker peer")
        print("i - Built a production-ready Universal Connectivity application")
        print("i - Created an interactive checker that students can dial and chat with!")
        print("")
        print("i 🎉 CONGRATULATIONS! You've completed the entire workshop!")
        print("i 🎉 You're now ready to build any peer-to-peer application with js-libp2p!")
        print("i 🎉 Developers can now dial into the checker and join the chat room!")

        return True

    except Exception as e:
        print(f"X Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

