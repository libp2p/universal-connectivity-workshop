#!/usr/bin/env python3
"""
Check script for Lesson 3: Ping Checkpoint (C++)
Validates ping protocol implementation.
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
    """Check code structure for ping implementation"""
    app_file = os.path.join(SCRIPT_DIR, "app/main.cpp")

    if not os.path.exists(app_file):
        print("X Error: app/main.cpp not found")
        return False

    with open(app_file, "r") as f:
        code = f.read()

    print("i  Checking code structure...")

    # Check for ping protocol include
    if "libp2p/protocol/ping" not in code:
        print("X Missing ping protocol include")
        return False
    print("v Ping protocol include found")

    # Check for PingConfig
    if "PingConfig" not in code:
        print("X Missing PingConfig")
        return False
    print("v PingConfig found")

    # Check for interval configuration
    if "interval" not in code.lower():
        print("X Missing interval configuration")
        return False
    print("v Interval configuration found")

    # Check for timeout configuration
    if "timeout" not in code.lower():
        print("X Missing timeout configuration")
        return False
    print("v Timeout configuration found")

    # Check for startPinging or ping handling
    if "startPinging" not in code and "handle" not in code:
        print("X Missing ping start or handler")
        return False
    print("v Ping functionality found")

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

    # Check for ping protocol
    if "ping" in output.lower() or "Ping" in output:
        print("v Ping protocol active")
    else:
        print("i  No explicit ping messages (may be OK)")

    # Check for RTT measurement
    rtt_match = re.search(r"Ping RTT to [A-Za-z0-9]+: [\d.]+ms", output)
    if rtt_match:
        print(f"v RTT measurement found: {rtt_match.group(0)}")
    else:
        print("i  No RTT measurement found (requires remote peer connection)")

    # Check for listening
    if "Listening on" in output:
        print("v Host is listening")

    # Check for connection or waiting
    if "Waiting" in output or "Connected" in output:
        print("v Connection handling ready")

    print("v Application started with ping protocol")
    return True

def main():
    print("Checking Lesson 3: Ping Checkpoint (C++)")
    print("=" * 60)

    if not check_code_structure():
        return False

    if not check_output():
        return False

    print("=" * 60)
    print("All checks passed! Ping checkpoint completed.")
    print("v You have successfully:")
    print("   * Implemented the ping protocol")
    print("   * Configured ping interval and timeout")
    print("   * Set up ping handlers for bidirectional communication")
    print("\nReady for Lesson 4: QUIC Transport!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
