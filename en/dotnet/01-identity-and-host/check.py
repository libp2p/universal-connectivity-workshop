#!/usr/bin/env python3
"""
Check script for Lesson 1: Identity and Host
Validates that the student's solution prints a valid PeerId
"""

import re
import sys
import os

def validate_peer_id(peer_id_str):
    """Validate PeerId format (CIDv0 or CIDv1)"""
    # CIDv0: starts with "Qm", 46 chars, base58
    # CIDv1: starts with "12D3KooW" or similar, variable length

    if peer_id_str.startswith("Qm"):
        if len(peer_id_str) != 46:
            return False, f"CIDv0 PeerId should be 46 chars, got {len(peer_id_str)}"
        valid_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        if not all(c in valid_chars for c in peer_id_str):
            return False, "Invalid base58 characters"
        return True, "Valid CIDv0 PeerId"

    elif peer_id_str.startswith("12D3KooW") or peer_id_str.startswith("bafz"):
        # CIDv1 format
        if len(peer_id_str) < 20:
            return False, "CIDv1 PeerId too short"
        return True, "Valid CIDv1 PeerId"

    else:
        return False, f"Unknown PeerId format: {peer_id_str}"

def check_output():
    """Check stdout.log for expected output"""
    if not os.path.exists("stdout.log"):
        print("x stdout.log not found")
        print("  Make sure your application is writing output")
        return False

    with open("stdout.log", "r") as f:
        output = f.read()

    print("i Checking lesson output...")
    print("i " + "=" * 50)

    if not output.strip():
        print("x stdout.log is empty")
        print("  Your application did not produce any output")
        return False

    # Check for startup message
    if "Starting Universal Connectivity Application" not in output:
        print("x Missing startup message")
        print("  Expected: 'Starting Universal Connectivity Application...'")
        return False
    print("v Startup message found")

    # Check for incomplete implementation message
    if "Implementation incomplete" in output:
        print("x Implementation is incomplete")
        print("  Follow the instructions in lesson.md to complete the code")
        return False

    # Extract PeerId
    peer_id_pattern = r"Local peer id: ([A-Za-z0-9]+)"
    match = re.search(peer_id_pattern, output)

    if not match:
        print("x No 'Local peer id:' message found")
        print("  Make sure to print: Console.WriteLine($\"Local peer id: {peer.Identity.PeerId}\");")
        print(f"\ni Actual output:\n{output}")
        return False

    peer_id = match.group(1)
    valid, msg = validate_peer_id(peer_id)

    if not valid:
        print(f"x {msg}")
        print(f"  PeerId found: {peer_id}")
        return False

    print(f"v {msg}: {peer_id}")
    return True

def main():
    """Main check function"""
    print("\n" + "=" * 60)
    print("  Checking Lesson 1: Identity and Host (.NET)")
    print("=" * 60 + "\n")

    if not check_output():
        print("\n" + "=" * 60)
        print("x Lesson 1 check failed")
        print("=" * 60)
        print("\ni Review the error messages above and:")
        print("  1. Check your Program.cs implementation")
        print("  2. Compare with the solution in lesson.md")
        print("  3. Make sure you're printing the PeerId correctly\n")
        return False

    print("\n" + "=" * 60)
    print("v Lesson 1 completed successfully! 🎉")
    print("=" * 60)
    print("\ni You have successfully:")
    print("  • Set up .NET dependency injection with AddLibp2p")
    print("  • Created a cryptographic identity (Ed25519)")
    print("  • Initialized an ILocalPeer")
    print("  • Generated and printed a valid PeerId")
    print("\ni Next: Lesson 2 - TCP Transport")
    print("  Learn how to listen and connect to other peers!\n")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
