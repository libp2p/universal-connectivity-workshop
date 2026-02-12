#!/usr/bin/env python3
"""
Check script for Lesson 6: Gossipsub Checkpoint (Nim)
Validates that the student's nim-libp2p solution can:
1. Establish a connection to the remote peer
2. Subscribe to Gossipsub topics
3. Receive and send messages on topics
"""

import subprocess
import sys
import os
import re


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

    if not ("/tcp" in addr_str or "/quic-v1" in addr_str):
        return False, f"Missing TCP or QUIC transport in multiaddr: {addr_str}"

    return True, f"{addr_str}"


def check_output():
    """Check the output log for expected Gossipsub functionality"""
    if not os.path.exists("checker.log"):
        print("x checker.log file not found")
        return False

    try:
        with open("checker.log", "r") as f:
            output = f.read()

        print("i Checking Gossipsub checkpoint functionality...")

        if not output.strip():
            print("x checker.log is empty - application may have failed to start")
            return False

        # Check for incoming connection
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

        # Check for connection established
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

        print(f"v Connection established with {peerid_message}")

        # Check for Gossipsub subscription
        subscribed_pattern = r"subscribed,(12D3KooW[A-Za-z0-9]+),([a-zA-Z0-9\-]+)"
        subscribed_matches = re.search(subscribed_pattern, output)
        if not subscribed_matches:
            print("x No Gossipsub topic subscription detected")
            print("i CRITICAL: The peer must subscribe to a Gossipsub topic!")
            print(f"i Actual output: {repr(output)}")
            return False

        peerid = subscribed_matches.group(1)
        topic = subscribed_matches.group(2)

        print(f"v Peer {peerid[:12]}... subscribed to topic '{topic}'")

        # Check for message received or published
        message_pattern = r"message,(12D3KooW[A-Za-z0-9]+),([a-zA-Z0-9\-]+)"
        message_matches = re.search(message_pattern, output)
        if not message_matches:
            print("x No Gossipsub message exchange detected")
            print("i The peer should send or receive messages on the subscribed topic")
            print(f"i Actual output: {repr(output)}")
            return False

        peerid = message_matches.group(1)
        topic = message_matches.group(2)

        print(f"v Message exchanged with {peerid[:12]}... on topic '{topic}'")

        # Check for connection closure
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
    print("i Checking Lesson 6: Gossipsub Checkpoint (Nim)")
    print("i " + "=" * 50)

    try:
        # Check the output
        if not check_output():
            return False

        print("i " + "=" * 50)
        print("v Gossipsub checkpoint completed successfully!")
        print("i You have successfully:")
        print("i - Established a connection with the remote peer")
        print("i - Subscribed to Gossipsub topics")
        print("i - Exchanged messages using pub/sub")
        print("i - Reached your third checkpoint!")
        print("i Ready for Lesson 7: Kademlia DHT!")

        return True

    except Exception as e:
        print(f"x Unexpected error during checking: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
