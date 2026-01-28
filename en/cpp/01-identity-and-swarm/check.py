#!/usr/bin/env python3
"""
Check script for Lesson 1: Identity and Basic Host (C++)
Validates that the student's solution creates a libp2p host with identity.
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
    # RSA peer IDs start with Qm
    # secp256k1 peer IDs start with 16Uiu2HAm

    if peer_id_str.startswith("12D3KooW"):
        # Ed25519 peer ID - should be ~52 characters
        if len(peer_id_str) >= 46 and len(peer_id_str) <= 56:
            return True, f"Valid Ed25519 peer ID: {peer_id_str}"
        return False, f"Invalid Ed25519 peer ID length: {peer_id_str}"

    elif peer_id_str.startswith("Qm"):
        # RSA peer ID - should be 46 characters
        if len(peer_id_str) == 46:
            return True, f"Valid RSA peer ID: {peer_id_str}"
        return False, f"Invalid RSA peer ID length: {peer_id_str}"

    elif peer_id_str.startswith("16Uiu2HAm"):
        # secp256k1 peer ID
        if len(peer_id_str) >= 50:
            return True, f"Valid secp256k1 peer ID: {peer_id_str}"
        return False, f"Invalid secp256k1 peer ID length: {peer_id_str}"

    return False, f"Unknown peer ID format: {peer_id_str}"

def check_output():
    """Check the output log for expected content"""
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
            print("X Missing startup message. Expected: 'Starting Universal Connectivity Application...'")
            print(f"i  Actual output: {repr(output[:200])}")
            return False
        print("v Found startup message")

        # Check for peer ID output - try multiple patterns
        peer_id_patterns = [
            r"Local peer id: ([A-Za-z0-9]+)",
            r"Local peer id:\s*([A-Za-z0-9]+)",
            r"PeerId:\s*([A-Za-z0-9]+)",
            r"peer id:\s*([A-Za-z0-9]+)",
        ]

        peer_id = None
        for pattern in peer_id_patterns:
            peer_id_match = re.search(pattern, output, re.IGNORECASE)
            if peer_id_match:
                peer_id = peer_id_match.group(1)
                break

        if not peer_id:
            print("X Missing peer ID output. Expected format: 'Local peer id: <peer_id_string>'")
            print(f"i  Actual output: {repr(output[:500])}")
            return False

        # Validate the peer ID format
        valid, message = validate_peer_id(peer_id)
        if not valid:
            print(f"X {message}")
            return False

        print(f"v {message}")

        # Check for host startup message (optional but good to have)
        host_started_patterns = [
            "Host started",
            "host started",
            "Started host",
        ]

        host_started = any(pattern in output for pattern in host_started_patterns)
        if host_started:
            print("v Found host startup message")
        else:
            print("i  No explicit host startup message found (optional)")

        print("v Application started successfully and generated valid peer identity")
        return True

    except Exception as e:
        print(f"X Error reading stdout.log: {e}")
        return False

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
            "boost/asio",
        ]

        for inc in required_includes:
            if inc not in code:
                print(f"X Missing include: {inc}")
                return False
        print("v Required includes found")

        # Check for host creation using injector
        if "makeHostInjector" not in code:
            print("X Missing makeHostInjector call")
            return False
        print("v Host injector found")

        # Check for host creation from injector
        if "injector.create" not in code:
            print("X Missing injector.create call")
            return False
        print("v Injector create call found")

        # Check for peer ID retrieval (getId or getPeerInfo)
        if "getId" not in code and "getPeerInfo" not in code:
            print("X Missing peer ID retrieval (getId or getPeerInfo)")
            return False
        print("v PeerId retrieval found")

        # Check for toBase58 conversion
        if "toBase58" not in code:
            print("X Missing toBase58() call for peer ID display")
            return False
        print("v toBase58 conversion found")

        # Check for io_context run
        if "io_context" not in code:
            print("X Missing io_context")
            return False
        if ".run()" not in code and "->run()" not in code:
            print("X Missing io_context run() call")
            return False
        print("v Event loop found")

        print("v Code structure is correct")
        return True

    except Exception as e:
        print(f"X Error reading code file: {e}")
        return False

def main():
    """Main check function"""
    print("Checking Lesson 1: Identity and Basic Host (C++)")
    print("=" * 60)

    try:
        # Check code structure first
        if not check_code_structure():
            return False

        # Check the output
        if not check_output():
            return False

        print("=" * 60)
        print("All checks passed! Your libp2p host is working correctly.")
        print("v You have successfully:")
        print("   * Created a libp2p host with auto-generated Ed25519 identity")
        print("   * Generated and displayed a valid peer ID (12D3KooW...)")
        print("   * Set up a Boost.Asio event loop")
        print("   * Implemented proper host initialization")
        print("\nReady for Lesson 2: TCP Transport!")

        return True

    except Exception as e:
        print(f"X Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
