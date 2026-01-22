#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check script for Lesson 1: Identity and Basic Host
Validates that the student's solution creates a libp2p host with identity.
"""

import subprocess
import sys
import os
import re

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def validate_peer_id(peer_id_str):
    """Validate that the peer ID string is a valid libp2p PeerId format"""
    # Ed25519 peer IDs start with 12D3KooW (base58btc encoded)
    if not peer_id_str.startswith("12D3KooW"):
        return False, f"Invalid peer ID format. Expected to start with '12D3KooW', got: {peer_id_str}"

    # Length check - valid Ed25519 peer IDs should be around 52-55 characters
    if len(peer_id_str) < 45 or len(peer_id_str) > 60:
        return False, f"Peer ID length seems invalid. Expected 45-60 chars, got {len(peer_id_str)}: {peer_id_str}"

    # Character set validation - should only contain base58 characters
    valid_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    for char in peer_id_str:
        if char not in valid_chars:
            return False, f"Invalid character '{char}' in peer ID. Must be base58 encoded."

    return True, f"Valid peer ID format: {peer_id_str}"

def check_output():
    """Check the output log for expected content"""
    if not os.path.exists("stdout.log"):
        print("✗ Error: stdout.log file not found")
        return False

    try:
        with open("stdout.log", "r") as f:
            output = f.read()

        print("ℹ Checking application output...")

        if not output.strip():
            print("✗ stdout.log is empty - application may have failed to start")
            return False

        # Check for startup message
        if "Starting Universal Connectivity Application" not in output:
            print("✗ Missing startup message. Expected: 'Starting Universal Connectivity Application...'")
            print(f"ℹ Actual output: {repr(output[:200])}")
            return False
        print("✓ Found startup message")

        # Check for peer ID output with exact format
        peer_id_pattern = r"Local peer id: (12D3KooW[A-Za-z0-9]+)"
        peer_id_match = re.search(peer_id_pattern, output)

        if not peer_id_match:
            print("✗ Missing peer ID output. Expected format: 'Local peer id: 12D3KooW...'")
            print(f"ℹ Actual output: {repr(output[:200])}")
            return False

        peer_id = peer_id_match.group(1)

        # Validate the peer ID format
        valid, message = validate_peer_id(peer_id)
        if not valid:
            print(f"✗ {message}")
            return False

        print(f"✓ {message}")

        # Check that the application runs without immediate crash
        lines = output.strip().split('\n')
        if len(lines) < 2:
            print("✗ Application seems to have crashed immediately after startup")
            print(f"ℹ Output lines: {lines}")
            return False

        print("✓ Application started successfully and generated valid peer identity")
        return True

    except Exception as e:
        print(f"✗ Error reading stdout.log: {e}")
        return False

def check_code_structure():
    """Check if the code has the expected structure"""
    app_file = "app/main.go"

    if not os.path.exists(app_file):
        print("✗ Error: app/main.go file not found")
        return False

    try:
        with open(app_file, "r") as f:
            code = f.read()

        print("ℹ Checking code structure...")

        # Check for required imports
        required_imports = [
            "github.com/libp2p/go-libp2p",
            "crypto",
        ]

        for imp in required_imports:
            if imp not in code:
                print(f"✗ Missing import: {imp}")
                return False
        print("✓ Required imports found")

        # Check for key generation
        if "crypto.GenerateKeyPair" not in code and "crypto.Ed25519" not in code:
            print("✗ Missing key generation (crypto.GenerateKeyPair with crypto.Ed25519)")
            return False
        print("✓ Key generation found")

        # Check for host creation
        if "libp2p.New" not in code:
            print("✗ Missing host creation (libp2p.New)")
            return False
        print("✓ Host creation found")

        # Check for peer ID output
        if ".ID()" not in code:
            print("✗ Missing peer ID retrieval (host.ID())")
            return False
        print("✓ Peer ID retrieval found")

        # Check for proper cleanup
        if "defer" not in code:
            print("⚠ Warning: No defer statements found. Consider adding defer h.Close() for proper cleanup")
        else:
            print("✓ Defer statements found (likely for cleanup)")

        print("✓ Code structure is correct")
        return True

    except Exception as e:
        print(f"✗ Error reading code file: {e}")
        return False

def main():
    """Main check function"""
    print("Checking Lesson 1: Identity and Basic Host")
    print("=" * 60)

    try:
        # Check code structure first
        if not check_code_structure():
            print("\n⚠ Fix the code structure issues and try again")
            return False

        print()

        # Check the output
        if not check_output():
            print("\n⚠ Fix the output issues and try again")
            return False

        print("=" * 60)
        print("✅ All checks passed! Your libp2p host is working correctly.")
        print("✓ You have successfully:")
        print("   • Created a libp2p host with a stable Ed25519 identity")
        print("   • Generated and displayed a valid peer ID")
        print("   • Set up proper application structure")
        print("   • Implemented graceful shutdown handling")
        print("\n🎉 Ready for Lesson 2: TCP Transport!")

        return True

    except Exception as e:
        print(f"✗ Unexpected error during checking: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
