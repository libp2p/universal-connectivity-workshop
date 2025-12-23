#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check script for Lesson 5: Identify Checkpoint
Validates that the student's solution can exchange identification information with remote peers.
"""

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
    if not ("/tcp" in addr_str):
        return False, f"Missing TCP transport in multiaddr: {addr_str}"
     
    return True, f"{addr_str}"

def check_output():
    """Check the output logs from both nodes for identify protocol exchange"""
    print("ℹ Checking identify protocol functionality...")
    
    # Check Node1 log
    if not os.path.exists("node1.log"):
        print("✗ node1.log file not found")
        return False
    
    if not os.path.exists("node2.log"):
        print("✗ node2.log file not found")
        return False
    
    try:
        with open("node1.log", "r") as f:
            node1_log = f.read()
        
        with open("node2.log", "r") as f:
            node2_log = f.read()
        
        if not node1_log.strip():
            print("✗ node1.log is empty - Node1 may have failed to start")
            return False
        
        if not node2_log.strip():
            print("✗ node2.log is empty - Node2 may have failed to start")
            return False

        # Step 1: Node1 starts and listens
        if "Node1 started with id" not in node1_log:
            print("✗ Node1 did not start correctly")
            print(f"ℹ Node1 log snippet: {repr(node1_log[:200])}")
            return False
        
        node1_peer_id_match = re.search(r"Node1 started with id:\s*(12D3KooW[A-Za-z0-9]+)", node1_log)
        if not node1_peer_id_match:
            print("✗ Could not extract Node1 Peer ID")
            return False
        node1_peer_id = node1_peer_id_match.group(1)
        valid, node1_peer_message = validate_peer_id(node1_peer_id)
        if not valid:
            print(f"✗ {node1_peer_message}")
            return False
        print(f"✓ Node1 started with Peer ID: {node1_peer_id}")
        
        # Step 2: Node2 starts and reads Node1 address
        if "Node2 started with id" not in node2_log:
            print("✗ Node2 did not start correctly")
            return False
        
        node2_peer_id_match = re.search(r"Node2 started with id:\s*(12D3KooW[A-Za-z0-9]+)", node2_log)
        if not node2_peer_id_match:
            print("✗ Could not extract Node2 Peer ID")
            return False
        node2_peer_id = node2_peer_id_match.group(1)
        valid, node2_peer_message = validate_peer_id(node2_peer_id)
        if not valid:
            print(f"✗ {node2_peer_message}")
            return False
        print(f"✓ Node2 started with Peer ID: {node2_peer_id}")
        
        # Step 3: Node2 dials Node1 (using configurable address)
        if "[IDENTIFY] Node2: Dialing Node1" not in node2_log:
            print("✗ Node2 did not attempt to dial Node1")
            print(f"ℹ Node2 log snippet: {repr(node2_log[:300])}")
            return False
        
        if "[IDENTIFY] Node2: Connected to" not in node2_log:
            print("✗ Node2 did not connect to Node1")
            print(f"ℹ Node2 log snippet: {repr(node2_log[:300])}")
            return False
        
        if node1_peer_id not in node2_log:
            print(f"✗ Node2 connection log does not mention Node1 Peer ID {node1_peer_id}")
            return False
        print(f"✓ Node2 connected to Node1")
        
        # Step 4: Identify protocol exchange (both directions)
        # Node1 should identify Node2
        node1_identify_match = re.search(r"\[IDENTIFY\] Node1: Identified peer\s+(12D3KooW[A-Za-z0-9]+)", node1_log)
        if not node1_identify_match:
            print("✗ Node1 did not identify Node2")
            print(f"ℹ Node1 log snippet: {repr(node1_log[-500:])}")
            return False
        
        identified_peer_id = node1_identify_match.group(1)
        if identified_peer_id != node2_peer_id:
            print(f"✗ Node1 identified wrong peer. Expected {node2_peer_id}, got {identified_peer_id}")
            return False
        
        # Node2 should identify Node1
        node2_identify_match = re.search(r"\[IDENTIFY\] Node2: Identified peer\s+(12D3KooW[A-Za-z0-9]+)", node2_log)
        if not node2_identify_match:
            print("✗ Node2 did not identify Node1")
            print(f"ℹ Node2 log snippet: {repr(node2_log[-500:])}")
            return False
        
        identified_peer_id2 = node2_identify_match.group(1)
        if identified_peer_id2 != node1_peer_id:
            print(f"✗ Node2 identified wrong peer. Expected {node1_peer_id}, got {identified_peer_id2}")
            return False
        
        print(f"✓ Identify protocol exchange completed:")
        print(f"  • Node1 identified Node2: {node2_peer_id}")
        print(f"  • Node2 identified Node1: {node1_peer_id}")
        
        # Step 5: Check for dynamic address discovery via Identify protocol
        if "dynamically discovered listening addresses" not in node1_log:
            print("✗ Node1 did not discover Node2's listening addresses dynamically")
            return False
        
        if "dynamically discovered listening addresses" not in node2_log:
            print("✗ Node2 did not discover Node1's listening addresses dynamically")
            return False
        
        # Extract discovered addresses
        node1_addr_match = re.search(r"\[IDENTIFY\] Node1: Node2's dynamically discovered listening addresses \(\d+\):", node1_log)
        node2_addr_match = re.search(r"\[IDENTIFY\] Node2: Node1's dynamically discovered listening addresses \(\d+\):", node2_log)
        
        if not node1_addr_match or not node2_addr_match:
            print("ℹ Address discovery logged (format may vary)")
        else:
            print(f"✓ Dynamic address discovery via Identify protocol completed")
        
        # Step 6: Check for agent version in identify logs
        # Note: The actual agent version might be js-libp2p default, but we check for protocol exchange
        if "Peer agent:" not in node1_log or "Peer agent:" not in node2_log:
            print("ℹ Agent version information not found (non-critical)")
        else:
            print(f"✓ Agent version information exchanged")
        
        # Step 7: Check for protocol capabilities exchange
        if "Peer supports" not in node1_log or "Peer supports" not in node2_log:
            print("ℹ Protocol count information not found (non-critical)")
        else:
            print(f"✓ Protocol capabilities exchanged")
        
        # Step 8: Check bidirectional ping
        # Node2 pings Node1
        if "[PING] Node2: Pinging" not in node2_log:
            print("✗ Node2 did not ping Node1")
            return False
        
        node2_ping_match = re.search(r"\[PING\] Node2: Ping to .+ successful, RTT:\s*(\d+)\s*ms", node2_log)
        if node2_ping_match:
            rtt = node2_ping_match.group(1)
            print(f"✓ Node2 pinged Node1 successfully, RTT: {rtt} ms")
        else:
            print("ℹ Node2 ping attempt logged")
        
        # Node1 pings Node2 (bidirectional)
        if "[PING] Node1: Pinging" not in node1_log:
            print("ℹ Node1 did not ping Node2 (bidirectional ping not required but recommended)")
        else:
            node1_ping_match = re.search(r"\[PING\] Node1: Ping to .+ successful, RTT:\s*(\d+)\s*ms", node1_log)
            if node1_ping_match:
                rtt = node1_ping_match.group(1)
                print(f"✓ Node1 pinged Node2 successfully, RTT: {rtt} ms (bidirectional)")
            else:
                print("ℹ Node1 ping attempt logged")
        
        print(f"✓ All identify protocol steps completed successfully")
        return True
       
    except Exception as e:
        print(f"✗ Error reading logs: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main check function"""
    print("ℹ Checking Lesson 5: Identify Checkpoint 🏆")
    print("ℹ " + "=" * 50)
    
    try:
        # Check the output
        if not check_output():
            return False
        
        print("")
        print("ℹ " + "=" * 50)
        print("")
        print("✓ Identify checkpoint completed successfully! 🎉")
        print("")
        print("")
        print("Ready for Lesson 6: Gossipsub Checkpoint!")
        print("")
        
        return True
        
    except Exception as e:
        print(f"✗ Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)