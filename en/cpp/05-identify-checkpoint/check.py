#!/usr/bin/env python3
"""
Check script for Lesson 5: Identify Checkpoint (C++)
Validates identify protocol implementation.
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
    """Check code structure for identify implementation"""
    app_file = os.path.join(SCRIPT_DIR, "app/main.cpp")

    if not os.path.exists(app_file):
        print("X Error: app/main.cpp not found")
        return False

    with open(app_file, "r") as f:
        code = f.read()

    print("i  Checking code structure...")

    # Check for identify protocol include
    if "libp2p/protocol/identify" not in code:
        print("X Missing identify protocol include")
        return False
    print("v Identify protocol include found")

    # Check for IdentifyMessageProcessor
    if "IdentifyMessageProcessor" not in code:
        print("X Missing IdentifyMessageProcessor")
        return False
    print("v IdentifyMessageProcessor found")

    # Check for IdentifyConfig
    if "IdentifyConfig" not in code:
        print("X Missing IdentifyConfig")
        return False
    print("v IdentifyConfig found")

    # Check for identify event subscription
    if "onIdentifyReceived" not in code:
        print("X Missing identify event subscription")
        return False
    print("v Identify event subscription found")

    # Check for identify start
    if "identify->start()" not in code:
        print("X Missing identify->start()")
        return False
    print("v Identify start found")

    # Check for ping protocol (should still be present)
    if "ping" not in code.lower():
        print("X Missing ping protocol")
        return False
    print("v Ping protocol still present")

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

    # Check for agent version
    if "Agent version" in output or "universal-connectivity" in output:
        print("v Agent version displayed")
    else:
        print("i  Agent version not explicitly shown (may be OK)")

    # Check for protocol version
    if "Protocol version" in output or "/ipfs/0.1.0" in output:
        print("v Protocol version displayed")

    # Check for identify protocol
    if "Identify" in output or "identify" in output or "/ipfs/id/1.0.0" in output:
        print("v Identify protocol active")
    else:
        print("X Identify protocol not found in output")
        return False

    # Check for ping protocol
    if "Ping" in output or "ping" in output:
        print("v Ping protocol active")

    # Check for listening
    if "Listening on" in output:
        print("v Host is listening")

    print("v Application started with identify protocol")
    return True

def main():
    print("Checking Lesson 5: Identify Checkpoint (C++)")
    print("=" * 60)

    if not check_code_structure():
        return False

    if not check_output():
        return False

    print("=" * 60)
    print("All checks passed! Identify checkpoint completed.")
    print("v You have successfully:")
    print("   * Implemented the identify protocol")
    print("   * Set up identify event handling")
    print("   * Combined identify with ping and multi-transport")
    print("\nReady for Lesson 6: DHT Discovery!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
