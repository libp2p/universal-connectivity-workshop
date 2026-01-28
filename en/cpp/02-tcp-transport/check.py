#!/usr/bin/env python3
"""
Check script for Lesson 2: TCP Transport (C++)
Validates that the student's cpp-libp2p solution can listen and connect to peers.
"""

import subprocess
import sys
import os
import re

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def validate_peer_id(peer_id_str):
    """Validate that the peer ID string is a valid libp2p format"""
    # Ed25519 peer IDs start with 12D3KooW
    if peer_id_str.startswith("12D3KooW"):
        if len(peer_id_str) >= 46 and len(peer_id_str) <= 56:
            return True, f"Valid Ed25519 peer ID: {peer_id_str}"
        return False, f"Invalid Ed25519 peer ID length: {peer_id_str}"

    # RSA peer IDs start with Qm
    elif peer_id_str.startswith("Qm"):
        if len(peer_id_str) == 46:
            return True, f"Valid RSA peer ID: {peer_id_str}"
        return False, f"Invalid RSA peer ID length: {peer_id_str}"

    return False, f"Unknown peer ID format: {peer_id_str}"

def validate_multiaddr(addr_str):
    """Validate that the address string looks like a valid multiaddr"""
    if not (addr_str.startswith("/ip4/") or addr_str.startswith("/ip6/")):
        return False, f"Invalid multiaddr format: {addr_str}"

    if "/tcp" not in addr_str:
        return False, f"Missing TCP transport in multiaddr: {addr_str}"

    return True, f"{addr_str}"

def check_code_structure():
    """Check if the code has the expected structure"""
    app_file = os.path.join(SCRIPT_DIR, "app/main.cpp")

    if not os.path.exists(app_file):
        print("X Error: app/main.cpp file not found")
        return False

    try:
        with open(app_file, "r") as f:
            code = f.read()

        print("i  Checking code structure...")

        # Check for required includes
        required_includes = [
            "libp2p/host/host.hpp",
            "libp2p/injector/host_injector.hpp",
            "libp2p/multi/multiaddress.hpp",
            "boost/asio",
        ]

        for inc in required_includes:
            if inc not in code:
                print(f"X Missing include: {inc}")
                return False
        print("v Required includes found")

        # Check for environment variable parsing
        if "REMOTE_PEERS" not in code:
            print("X Missing REMOTE_PEERS environment variable parsing")
            return False
        print("v REMOTE_PEERS parsing found")

        # Check for listen functionality
        if "listen" not in code.lower():
            print("X Missing listen functionality")
            return False
        print("v Listen functionality found")

        # Check for connect/dial functionality
        if "connect" not in code.lower():
            print("X Missing connect/dial functionality")
            return False
        print("v Connect functionality found")

        # Check for peer ID retrieval
        if "getId" not in code and "getPeerInfo" not in code:
            print("X Missing peer ID retrieval")
            return False
        print("v PeerId retrieval found")

        print("v Code structure is correct")
        return True

    except Exception as e:
        print(f"X Error reading code file: {e}")
        return False

def check_output():
    """Check the output log for expected TCP transport content"""
    stdout_log = os.path.join(SCRIPT_DIR, "stdout.log")

    if not os.path.exists(stdout_log):
        print("X Error: stdout.log file not found")
        return False

    try:
        with open(stdout_log, "r") as f:
            output = f.read()

        print("i  Checking application output...")

        if not output.strip():
            print("X stdout.log is empty - application may have failed to start")
            return False

        # Check for startup message
        if "Starting Universal Connectivity Application" not in output:
            print("X Missing startup message")
            print(f"i  Actual output: {repr(output[:200])}")
            return False
        print("v Found startup message")

        # Check for peer ID output
        peer_id_patterns = [
            r"Local peer id: ([A-Za-z0-9]+)",
            r"Local peer id:\s*([A-Za-z0-9]+)",
        ]

        peer_id = None
        for pattern in peer_id_patterns:
            peer_id_match = re.search(pattern, output, re.IGNORECASE)
            if peer_id_match:
                peer_id = peer_id_match.group(1)
                break

        if not peer_id:
            print("X Missing peer ID output")
            return False

        valid, message = validate_peer_id(peer_id)
        if not valid:
            print(f"X {message}")
            return False
        print(f"v {message}")

        # Check for listening address
        listen_patterns = [
            r"Listening on[:\s]+([/\w\.:]+)",
            r"Listen.*(/ip4/[^\s]+)",
        ]

        listen_addr = None
        for pattern in listen_patterns:
            listen_match = re.search(pattern, output, re.IGNORECASE)
            if listen_match:
                listen_addr = listen_match.group(1)
                break

        if listen_addr:
            valid, addr_msg = validate_multiaddr(listen_addr)
            if valid:
                print(f"v Listening on: {listen_addr}")
            else:
                print(f"i  Listen address format: {listen_addr}")
        else:
            print("i  No explicit listen address found (may be OK)")

        # Check for connection attempt or waiting message
        if "Waiting for connections" in output or "Attempting to connect" in output:
            print("v Connection handling ready")
        else:
            print("i  No explicit connection messages (may be OK if no REMOTE_PEERS)")

        print("v Application started successfully with TCP transport")
        return True

    except Exception as e:
        print(f"X Error reading stdout.log: {e}")
        return False

def main():
    """Main check function"""
    print("Checking Lesson 2: TCP Transport (C++)")
    print("=" * 60)

    try:
        # Check code structure first
        if not check_code_structure():
            return False

        # Check the output
        if not check_output():
            return False

        print("=" * 60)
        print("All checks passed! TCP transport is working correctly.")
        print("v You have successfully:")
        print("   * Configured TCP transport with cpp-libp2p")
        print("   * Set up listening on a TCP port")
        print("   * Implemented connection handling")
        print("   * Parsed multiaddresses from environment")
        print("\nReady for Lesson 3: Ping Checkpoint!")

        return True

    except Exception as e:
        print(f"X Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
