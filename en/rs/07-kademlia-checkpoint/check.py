#!/usr/bin/env python3
"""
Check script for Lesson 7: Kademlia Checkpoint
Validates that the student's solution can subscribe bootstrap kademlia and get closest peers
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
    if not os.path.exists("checker.log"):
        print("x checker.log file not found")
        return False
    
    try:
        with open("checker.log", "r") as f:
            output = f.read()
        
        print("i Checking gossipsub checkpoint functionality...")
        
        if not output.strip():
            print("x checker.log is empty - application may have failed to start")
            return False
        
        # a correct solution causes the checker to output a sequence of messages like the following:
        # incoming,/ip4/172.16.16.17/udp/9091/quic-v1,/ip4/172.16.16.16/udp/41972/quic-v1
        # connected,12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE,/ip4/172.16.16.16/udp/41972/quic-v1
        # identify,12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE,/ipfs/id/1.0.0,universal-connectivity/0.1.0
        # subscribe,12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE,universal-connectivity
        # msg,12D3KooWPWpaEjf8raRBZztEXMcSTXp8WBZwtcbhT7Xy1jyKCoN9,universal-connectivity,Hello from 12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE!
        # closed,12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE

        # check for:
        #   incoming,/ip4/172.16.16.17/tcp/9092,/ip4/172.16.16.16/tcp/41972
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

        # check for:
        #   connected,12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE,/ip4/172.16.16.16/tcp/41972
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

        # check for:
        #   identify,12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE,/ipfs/id/1.0.0,universal-connectivity/0.1.0
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

        # check for:
        #   subscribe,12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE,universal-connectivity
        subscribe_pattern = r"subscribe,(12D3KooW[A-Za-z0-9]+),universal-connectivity"
        subscribe_matches = re.search(subscribe_pattern, output)
        if not subscribe_matches:
            print("x No subscribe received")
            print(f"i Actual output: {repr(output)}")
            return False

        peerid = subscribe_matches.group(1)
        valid, peerid_message = validate_peer_id(peerid)
        if not valid:
            print(f"x {peerid_message}")
            return False
        
        print(f"v Gossipsub subscribe received from {peerid_message}: topic=universal-connectivity")

        # check for:
        #   msg,12D3KooWPWpaEjf8raRBZztEXMcSTXp8WBZwtcbhT7Xy1jyKCoN9,universal-connectivity,Hello from Universal Connectivity!
        msg_pattern = r"msg,(12D3KooW[A-Za-z0-9]+),universal-connectivity,(.+)"
        msg_matches = re.search(msg_pattern, output)
        if not msg_matches:
            print("x No msg received")
            print(f"i Actual output: {repr(output)}")
            return False

        peerid = msg_matches.group(1)
        valid, peerid_message = validate_peer_id(peerid)
        if not valid:
            print(f"x {peerid_message}")
            return False
        
        msg = msg_matches.group(2)

        print(f"v Gossipsub message received from {peerid_message}: topic=universal-connectivity, msg={msg}")

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
    print("i Checking Lesson 7: Kademlia Checkpoint 🏆")
    print("i " + "=" * 50)
    
    try:
        # Check the output
        if not check_output():
            return False
        
        print("i " + "=" * 50)
        print("y Kademlia checkpoint completed successfully! 🎉")
        print("i You have successfully:")
        print("i • Configured Kademlia for bootstrapping and peer discovery")
        print("i • Reached your fourth checkpoint!")
        print("Ready for Lesson 8: Universal Connectivity!")
        
        return True
        
    except Exception as e:
        print(f"x Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
