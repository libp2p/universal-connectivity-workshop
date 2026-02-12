#!/usr/bin/env python3
"""
Verification script for Lesson 01: Identity and Basic Switch

This script checks that the nim-libp2p switch was created successfully
and outputs a valid PeerId.
"""

import re
import sys


def check_output(output: str) -> tuple[bool, str]:
    """
    Verify the lesson output contains a valid PeerId.

    Expected output format:
    PeerId: 12D3KooW...

    Args:
        output: The stdout from the lesson execution

    Returns:
        Tuple of (success: bool, message: str)
    """
    # Check for PeerId in the output
    # PeerIds in libp2p typically start with "12D3KooW" (Ed25519 keys) or "Qm" (RSA keys)
    peer_id_pattern = r"PeerId:\s*(12D3KooW[a-zA-Z0-9]+|Qm[a-zA-Z0-9]+)"

    match = re.search(peer_id_pattern, output)

    if not match:
        # Check if there's any PeerId-like string
        if "PeerId:" in output:
            return False, "PeerId found but format appears invalid. Expected format: 12D3KooW... or Qm..."
        return False, "No PeerId found in output. Make sure to print: echo \"PeerId: \", switch.peerInfo.peerId"

    peer_id = match.group(1)

    # Validate PeerId length (Ed25519 PeerIds are typically 52 characters)
    if len(peer_id) < 40:
        return False, f"PeerId appears too short: {peer_id}"

    return True, f"Successfully created switch with PeerId: {peer_id}"


def main():
    """Main entry point for the verification script."""
    # Read from stdin or file
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            output = f.read()
    else:
        output = sys.stdin.read()

    success, message = check_output(output)

    print(message)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
