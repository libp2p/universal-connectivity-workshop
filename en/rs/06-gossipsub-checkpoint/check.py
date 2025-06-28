#!/usr/bin/env python3
"""
Check script for Lesson 6: Gossipsub Checkpoint
Validates that the student's solution can subscribe to topics and receive gossipsub messages.
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

def validate_multiaddr(addr_str):
    """Validate that the address string looks like a valid multiaddr"""
    # Basic multiaddr validation - should start with /ip4/ or /ip6/
    if not (addr_str.startswith("/ip4/") or addr_str.startswith("/ip6/")):
        return False, f"Invalid multiaddr format: {addr_str}"
    
    # Should contain /tcp for TCP transport or /quic-v1 for QUIC transport
    if not ("/tcp" in addr_str or "/quic-v1" in addr_str):
        return False, f"Missing TCP or QUIC transport in multiaddr: {addr_str}"
     
    return True, f"Valid multiaddr: {addr_str}"

def check_output():
    """Check the output log for expected gossipsub checkpoint functionality"""
    if not os.path.exists("stdout.log"):
        print("x stdout.log file not found")
        return False
    
    try:
        with open("stdout.log", "r") as f:
            output = f.read()
        
        print("i Checking gossipsub checkpoint functionality...")
        
        if not output.strip():
            print("x stdout.log is empty - application may have failed to start")
            return False
        
        # Check for startup message
        if "Starting Universal Connectivity Application".lower() not in output.lower():
            print("x Missing startup message. Expected: 'Starting Universal Connectivity Application...'")
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

        # Check for topic subscriptions
        expected_topics = [
            "universal-connectivity",
            "universal-connectivity-file", 
            "universal-connectivity-browser-peer-discovery"
        ]
        
        subscribed_topics = []
        for topic in expected_topics:
            subscribe_pattern = f"Subscribed to topic: {re.escape(topic)}"
            if re.search(subscribe_pattern, output):
                subscribed_topics.append(topic)
                print(f"v Found subscription to topic: {topic}")
            else:
                print(f"x Missing subscription to topic: {topic}")
                print(f"i Expected pattern: {subscribe_pattern}")
                return False
        
        if len(subscribed_topics) != len(expected_topics):
            print(f"x Missing topic subscriptions. Expected {len(expected_topics)}, found {len(subscribed_topics)}")
            return False
        
        # Check for dialing multiaddr
        dial_multiaddr_pattern = r"Dialing: ([/\w\.:]+)"
        dial_multiaddr_matches = re.search(dial_multiaddr_pattern, output)
        
        if not dial_multiaddr_matches:
            print("x No dialed multiaddr found. Expected format: 'Dialing: /ip4/.../tcp/...' or similar")
            print(f"i Actual output: {repr(output)}")
            return False

        multiaddr = dial_multiaddr_matches.group(1)
        print(f"v Found dialed multiaddr: {multiaddr}")

        # Check for connection establishment
        connected_pattern = rf"Connected to: (12D3KooW[A-Za-z0-9]+) via {re.escape(multiaddr)}"
        connected_match = re.search(connected_pattern, output)
        if not connected_match:
            print(f"x Missing connection message")
            print(f"i Expected pattern: {connected_pattern}")
            print(f"i Actual output: {repr(output)}")
            return False

        remote_peer_id = connected_match.group(1)
        print(f"v Found connection to peer: {remote_peer_id}")

        # Check for ping messages
        ping_pattern = rf"Received a ping from {re.escape(remote_peer_id)}, round trip time: (\d+) ms"
        ping_matches = re.findall(ping_pattern, output)
        
        if ping_matches:
            print(f"v Found {len(ping_matches)} ping messages")
        else:
            print("x Missing ping messages - connection may not be fully established")
            return False

        # Check for identify events
        identify_pattern = rf"Identified peer: {re.escape(remote_peer_id)} with protocol version: ([^\s]+)"
        if re.search(identify_pattern, output):
            print("v Found identify message")
        else:
            print("x Missing identify message")
            return False

        # Check for gossipsub messages (either received or peer subscription events)
        gossipsub_message_pattern = r"Received message on topic '[^']+': .+ from .+ \(type: .+\)"
        peer_subscribed_pattern = r"Peer .+ subscribed to topic: .+"
        
        gossipsub_messages = re.findall(gossipsub_message_pattern, output)
        peer_subscriptions = re.findall(peer_subscribed_pattern, output)
        
        if gossipsub_messages:
            print(f"v Found {len(gossipsub_messages)} gossipsub messages")
        elif peer_subscriptions:
            print(f"v Found {len(peer_subscriptions)} peer subscription events")
        else:
            print("x Missing gossipsub activity. Expected either received messages or peer subscription events")
            print(f"i Actual output: {repr(output)}")
            return False
        
        # Check that application runs for reasonable time without crashing
        lines = output.strip().split('\n')
        if len(lines) < 8:  # Should have startup, peer id, subscriptions, dialing, connection, ping, identify, and gossipsub messages
            print("x Application seems to have crashed too quickly")
            print(f"i Output lines: {lines}")
            return False
        
        print("v Application started successfully with gossipsub functionality")
        
        return True
        
    except Exception as e:
        print(f"x Error reading stdout.log: {e}")
        return False

def main():
    """Main check function"""
    print("i Checking Lesson 6: Gossipsub Checkpoint 🏆")
    print("i " + "=" * 50)
    
    try:
        # Check the output
        if not check_output():
            return False
        
        print("i " + "=" * 50)
        print("y Gossipsub checkpoint completed successfully! 🎉")
        print("i You have successfully:")
        print("i • Configured Gossipsub for publish-subscribe messaging")
        print("i • Subscribed to Universal Connectivity topics")
        print("i • Implemented protobuf message serialization")
        print("i • Handled gossipsub events and peer subscriptions")
        print("i • Reached your third checkpoint!")
        print("Ready for Lesson 7: Kademlia Checkpoint!")
        
        return True
        
    except Exception as e:
        print(f"x Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
