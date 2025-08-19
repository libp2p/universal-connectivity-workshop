#!/usr/bin/env python3
"""
Check script for Lesson 5: Identify Checkpoint
Validates that the student's solution can exchange identification information with remote peers.
"""
import os
import re
import sys

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

def validate_multiaddr(addr_str):
    """Validate that the address string looks like a valid multiaddr"""
    if not (addr_str.startswith("/ip4/") or addr_str.startswith("/ip6/")):
        return False, f"Invalid multiaddr format: {addr_str}"
    if not ("/tcp" in addr_str):
        return False, f"Missing TCP transport in multiaddr: {addr_str}"
    return True, f"{addr_str}"

def check_output():
    """Check the output log for expected identify checkpoint functionality"""
    if not os.path.exists("checker.log"):
        print("x checker.log file not found")
        return False
    try:
        with open("checker.log", "r") as f:
            output = f.read()
        print("i Checking identify functionality...")
        if not output.strip():
            print("x checker.log is empty - application may have failed to start")
            return False
        incoming_pattern = r"incoming,([/\w\.:-]+),([/\w\.:-]+)"
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
        connected_pattern = r"connected,(12D3KooW[A-Za-z0-9]+),([/\w\.:-]+)"
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
        identify_pattern = r"identify,(12D3KooW[A-Za-z0-9]+),([/\w\.:-]+),([/\w\.:-]+)"
        identify_matches = re.search(identify_pattern, output)
        if not identify_matches:
            print("x No identify received")
            print(f"i Actual output: {repr(output)}")
            return False
        peerid = identify_matches.group(1)
        valid, peerid_message = validate_peer_id(peerid)
        if not valid:
            print(f"x {peerid_message}")
            return False
        protocol = identify_matches.group(2)
        agent = identify_matches.group(3)
        print(f"v Identify received from {peerid_message}: protocol={protocol}, agent={agent}")
        closed_pattern = r"closed,(12D3KooW[A-Za-z0-9]+)"
        closed_matches = re.search(closed_pattern, output)
        if not closed_matches:
            print("x Connection closure not detected")
            print(f"i Actual output: {repr(output)}")
            return False
        peerid = closed_matches.group(1)
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
    print("i Checking Lesson 5: Identify Checkpoint 🏆")
    print("i " + "=" * 50)
    try:
        if not check_output():
            return False
        print("i " + "=" * 50)
        print("y Identify checkpoint completed successfully! 🎉")
        print("i You have successfully:")
        print("i • Added Identify protocol to your libp2p node")
        print("i • Exchanged peer identification information")
        print("i • Displayed peer capabilities and protocol versions")
        print("i • Reached your second checkpoint!")
        print("Ready for Lesson 6: Gossipsub Checkpoint!")
        return True
    except Exception as e:
        print(f"x Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)