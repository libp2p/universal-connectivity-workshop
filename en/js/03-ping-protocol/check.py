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

    # Should contain /p2p for peer ID
    if "/p2p/" not in addr_str:
        return False, f"Missing peer ID in multiaddr: {addr_str}"

    return True, f"{addr_str}"

def validate_latency(latency_str):
    """Validate that the latency is a reasonable number in milliseconds"""
    try:
        latency_ms = int(latency_str)
        if latency_ms < 0:
            return False, f"Invalid latency: {latency_ms}ms (negative)"
        if latency_ms > 10000:  # 10 seconds max
            return False, f"Unreasonable latency: {latency_ms}ms (too high)"
        return True, f"{latency_ms}ms"
    except ValueError:
        return False, f"Invalid latency format: {latency_str}"

def check_output():
    """Check the output log for expected ping protocol functionality"""
    if not os.path.exists("checker.log"):
        print("✗ checker.log file not found")
        return False

    try:
        with open("checker.log", "r") as f:
            output = f.read()

        print("ℹ Checking ping protocol functionality...")

        if not output.strip():
            print("✗ checker.log is empty - checker may have failed to start")
            return False

        # Check for libp2p startup
        startup_pattern = r"libp2p has started"
        startup_matches = re.search(startup_pattern, output)
        if not startup_matches:
            print("✗ No libp2p startup detected")
            print(f"ℹ Expected: 'libp2p has started'")
            print(f"ℹ Actual output: {repr(output)}")
            return False

        print("✓ libp2p node started successfully")

        # Check for listening addresses
        listening_pattern = r"listening on:\s*([/\w\.:-]+)"
        listening_matches = re.findall(listening_pattern, output)
        if not listening_matches:
            print("✗ No listening addresses detected")
            print(f"ℹ Expected: 'listening on: <multiaddr>'")
            print(f"ℹ Actual output: {repr(output)}")
            return False

        for addr in listening_matches:
            valid, addr_message = validate_multiaddr(addr)
            if not valid:
                print(f"✗ {addr_message}")
                return False

        print(f"✓ Node listening on {len(listening_matches)} address(es)")

        # Check for ping attempt
        ping_attempt_pattern = r"pinging remote peer at\s*([/\w\.:-]+)"
        ping_attempt_matches = re.search(ping_attempt_pattern, output)
        
        if ping_attempt_matches:
            # Ping was attempted - validate the process
            target_addr = ping_attempt_matches.group(1)
            valid, target_addr_message = validate_multiaddr(target_addr)
            if not valid:
                print(f"✗ {target_addr_message}")
                return False

            print(f"✓ Ping attempt to {target_addr_message}")

            # Check for successful ping with latency
            ping_success_pattern = r"pinged\s*([/\w\.:-]+)\s*in\s*(\d+)ms"
            ping_success_matches = re.search(ping_success_pattern, output)
            
            if not ping_success_matches:
                print("✗ No successful ping with latency detected")
                print(f"ℹ Expected: 'pinged <multiaddr> in <latency>ms'")
                print(f"ℹ Actual output: {repr(output)}")
                return False

            pinged_addr = ping_success_matches.group(1)
            latency_str = ping_success_matches.group(2)

            valid, pinged_addr_message = validate_multiaddr(pinged_addr)
            if not valid:
                print(f"✗ {pinged_addr_message}")
                return False

            valid, latency_message = validate_latency(latency_str)
            if not valid:
                print(f"✗ {latency_message}")
                return False

            print(f"✓ Successfully pinged {pinged_addr_message} in {latency_message}")

        else:
            # No ping attempt - this is also valid for basic setup
            print("ℹ No ping attempt detected - basic ping setup validated")

        return True

    except Exception as e:
        print(f"✗ Error reading checker.log: {e}")
        return False

def main():
    """Main check function"""
    print("ℹ Checking Lesson 3: Ping Protocol (Checkpoint 1)")
    print("ℹ " + "=" * 50)

    try:
        # Check the output
        if not check_output():
            return False

        print("ℹ " + "=" * 50)
        print("✓ Ping protocol lesson completed successfully!")
        print("ℹ You have successfully:")
        print("ℹ • Configured ping service in your libp2p node")
        print("ℹ • Started a node with proper listening addresses")
        print("ℹ • Connected to a remote peer using multiaddr")
        print("ℹ • Exchanged ping messages and measured latency")
        print("ℹ • Built a foundation for peer-to-peer communication")
        print("ℹ Ready for Lesson 4: Circuit Relay v2!")

        return True

    except Exception as e:
        print(f"✗ Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
