#!/usr/bin/env python3
"""
Check script for Lesson 4: QUIC Transport (C++)
Validates QUIC transport implementation.
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
    """Check code structure for QUIC implementation"""
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

    # Check for QUIC multiaddress format
    if "quic" not in code.lower():
        print("X Missing QUIC transport configuration")
        return False
    print("v QUIC transport configuration found")

    # Check for UDP port (QUIC uses UDP)
    if "/udp/" not in code:
        print("X Missing UDP port configuration for QUIC")
        return False
    print("v UDP port configuration found")

    # Check for multi-transport setup
    if "tcp" not in code.lower() or "quic" not in code.lower():
        print("X Missing multi-transport configuration")
        return False
    print("v Multi-transport (TCP + QUIC) configuration found")

    # Check for transport detection
    if "getTransportType" in code or "transport" in code.lower():
        print("v Transport type detection found")

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

    # Check for TCP listening
    if "Listening on TCP" in output or ("Listening on" in output and "tcp" in output.lower()):
        print("v TCP transport active")
    else:
        print("i  TCP listening message not found (may be OK)")

    # Check for QUIC listening
    if "Listening on QUIC" in output or ("Listening on" in output and "quic" in output.lower()):
        print("v QUIC transport active")
    elif "QUIC" in output or "quic" in output:
        print("v QUIC transport referenced")
    else:
        print("i  QUIC listening may have failed (check if lsquic is available)")

    # Check for ping protocol
    if "ping" in output.lower() or "Ping" in output:
        print("v Ping protocol active")

    # Check for transport indication
    if "Transports" in output or "TCP + QUIC" in output:
        print("v Multi-transport support indicated")

    print("v Application started with QUIC transport support")
    return True

def main():
    print("Checking Lesson 4: QUIC Transport (C++)")
    print("=" * 60)

    if not check_code_structure():
        return False

    if not check_output():
        return False

    print("=" * 60)
    print("All checks passed! QUIC transport lesson completed.")
    print("v You have successfully:")
    print("   * Added QUIC transport support")
    print("   * Configured multi-transport (TCP + QUIC)")
    print("   * Maintained ping protocol across transports")
    print("\nReady for Lesson 5: mDNS Discovery!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
