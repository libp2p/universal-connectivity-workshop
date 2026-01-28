#!/usr/bin/env python3
"""
Check script for Lesson 6: Gossipsub Checkpoint (C++)
Validates gossipsub protocol implementation.
"""

import sys
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def validate_peer_id(peer_id_str):
    """Validate peer ID format"""
    if peer_id_str.startswith("12D3KooW"):
        if 46 <= len(peer_id_str) <= 56:
            return True, f"Valid Ed25519 peer ID: {peer_id_str}"
    return False, f"Invalid peer ID: {peer_id_str}"

def check_code_structure():
    """Check code structure for gossipsub implementation"""
    app_file = os.path.join(SCRIPT_DIR, "app/main.cpp")

    if not os.path.exists(app_file):
        print("X Error: app/main.cpp not found")
        return False

    with open(app_file, "r") as f:
        code = f.read()

    print("i  Checking code structure...")

    # Check for gossip include
    if "libp2p/protocol/gossip" not in code:
        print("X Missing gossip protocol include")
        return False
    print("v Gossip protocol include found")

    # Check for gossip config
    if "gossip::Config" not in code:
        print("X Missing gossip Config")
        return False
    print("v Gossip Config found")

    # Check for gossip create
    if "gossip::create" not in code:
        print("X Missing gossip::create")
        return False
    print("v Gossip create found")

    # Check for subscribe
    if "subscribe" not in code:
        print("X Missing subscribe call")
        return False
    print("v Subscribe found")

    # Check for publish
    if "publish" not in code:
        print("X Missing publish call")
        return False
    print("v Publish found")

    # Check for topics
    if "universal-connectivity" not in code:
        print("X Missing universal-connectivity topic")
        return False
    print("v Universal connectivity topic found")

    # Check for gossip start
    if "gossip->start()" not in code:
        print("X Missing gossip->start()")
        return False
    print("v Gossip start found")

    print("v Code structure is correct")
    return True

def check_output():
    """Check application output"""
    stdout_log = os.path.join(SCRIPT_DIR, "stdout.log")

    if not os.path.exists(stdout_log):
        print("X Error: stdout.log not found")
        return False

    with open(stdout_log, "r") as f:
        output = f.read()

    print("i  Checking application output...")

    if not output.strip():
        print("X stdout.log is empty")
        return False

    # Check startup message
    if "Starting Universal Connectivity Application" not in output:
        print("X Missing startup message")
        return False
    print("v Found startup message")

    # Check peer ID
    peer_id_match = re.search(r"Local peer id: ([A-Za-z0-9]+)", output)
    if not peer_id_match:
        print("X Missing peer ID")
        return False

    peer_id = peer_id_match.group(1)
    valid, msg = validate_peer_id(peer_id)
    if not valid:
        print(f"X {msg}")
        return False
    print(f"v {msg}")

    # Check for gossipsub protocol
    if "Gossipsub" in output or "meshsub" in output or "gossip" in output.lower():
        print("v Gossipsub protocol active")
    else:
        print("X Gossipsub protocol not found in output")
        return False

    # Check for topics
    if "universal-connectivity" in output:
        print("v Topics configured")

    # Check for listening
    if "Listening on" in output:
        print("v Host is listening")

    # Check for publish (heartbeat)
    if "Published" in output or "heartbeat" in output:
        print("v Publishing messages")

    print("v Application started with gossipsub protocol")
    return True

def main():
    print("Checking Lesson 6: Gossipsub Checkpoint (C++)")
    print("=" * 60)

    if not check_code_structure():
        return False

    if not check_output():
        return False

    print("=" * 60)
    print("All checks passed! Gossipsub checkpoint completed.")
    print("v You have successfully:")
    print("   * Implemented the gossipsub protocol")
    print("   * Set up topic subscriptions")
    print("   * Configured message publishing")
    print("   * Combined with ping, identify, and multi-transport")
    print("\nReady for Lesson 7: Final Checkpoint!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
