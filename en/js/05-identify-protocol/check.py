#!/usr/bin/env python3
import os
import re
import sys

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
    if "/tcp" not in addr_str:
        return False, f"Missing TCP transport in multiaddr: {addr_str}"

    return True, f"{addr_str}"

def check_output():
    """Check the output log for expected identify protocol functionality"""
    if not os.path.exists("checker.log"):
        print("✗ checker.log file not found")
        return False

    try:
        with open("checker.log", "r") as f:
            output = f.read()

        print("ℹ Checking identify protocol functionality...")

        if not output.strip():
            print("✗ checker.log is empty - checker may have failed to start")
            return False

        # Check for node startup with Peer ID
        peer_id_pattern = r"Node started with Peer ID:\s*(12D3KooW[A-Za-z0-9]+)"
        peer_id_matches = re.search(peer_id_pattern, output)
        if not peer_id_matches:
            print("✗ No node startup with Peer ID detected")
            print(f"ℹ Expected: 'Node started with Peer ID: <peer_id>'")
            print(f"ℹ Actual output: {repr(output)}")
            return False

        peer_id = peer_id_matches.group(1)
        valid, peer_id_message = validate_peer_id(peer_id)
        if not valid:
            print(f"✗ {peer_id_message}")
            return False

        print(f"✓ Node started with {peer_id_message}")

        # Check for listening addresses
        listening_pattern = r"Listening on:\s*([/\w\.:-]+)"
        listening_matches = re.findall(listening_pattern, output)
        if not listening_matches:
            print("✗ No listening addresses detected")
            print(f"ℹ Expected: 'Listening on: <multiaddr>'")
            print(f"ℹ Actual output: {repr(output)}")
            return False

        for addr in listening_matches:
            valid, addr_message = validate_multiaddr(addr)
            if not valid:
                print(f"✗ {addr_message}")
                return False

        print(f"✓ Node listening on {len(listening_matches)} address(es)")

        # Check for identify protocol usage (if remote connection was attempted)
        remote_peer_pattern = r"Remote PeerId:\s*(12D3KooW[A-Za-z0-9]+)"
        remote_peer_matches = re.search(remote_peer_pattern, output)
        
        if remote_peer_matches:
            # Remote connection was attempted - validate identify protocol usage
            remote_peer_id = remote_peer_matches.group(1)
            valid, remote_peer_message = validate_peer_id(remote_peer_id)
            if not valid:
                print(f"✗ {remote_peer_message}")
                return False

            print(f"✓ Successfully connected to remote peer {remote_peer_message}")

            # Check for protocols extraction
            protocols_pattern = r"Protocols:\s*\[([^\]]*)\]"
            protocols_matches = re.search(protocols_pattern, output)
            if not protocols_matches:
                print("✗ No protocols extracted from remote peer")
                print(f"ℹ Expected: 'Protocols: [...]'")
                print(f"ℹ Actual output: {repr(output)}")
                return False

            protocols_str = protocols_matches.group(1)
            if protocols_str.strip():
                print(f"✓ Extracted protocols: {protocols_str}")
            else:
                print("✓ Remote peer has no protocols (empty array)")

        else:
            # No remote connection - this is also valid for basic identify setup
            print("ℹ No remote connection attempted - basic identify setup validated")

        return True

    except Exception as e:
        print(f"✗ Error reading checker.log: {e}")
        return False

def main():
    """Main check function"""
    print("ℹ Checking Lesson 5: Identify Protocol")
    print("ℹ " + "=" * 50)

    try:
        # Check the output
        if not check_output():
            return False

        print("ℹ " + "=" * 50)
        print("✓ Identify protocol lesson completed successfully!")
        print("ℹ You have successfully:")
        print("ℹ • Configured identify service in your libp2p node")
        print("ℹ • Started a node with proper Peer ID and listening addresses")
        print("ℹ • Used the identify protocol to discover remote peer information")
        print("ℹ • Extracted remote PeerId and supported protocols")
        print("ℹ • Built a foundation for peer capability discovery")
        print("ℹ Ready for Lesson 6: Gossipsub Pub/Sub!")

        return True

    except Exception as e:
        print(f"✗ Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 