#!/usr/bin/env python3
"""
Check script for Lesson 4: QUIC Transport
Validates that the student's solution can connect with QUIC and ping remote peers.
"""
import os
import re
import sys
import time

def validate_peer_id(peer_id_str):
    """Validate that the peer ID string is a valid libp2p PeerId format"""
    if not peer_id_str.startswith("12D3KooW"):
        return False, f"Invalid peer ID format. Expected to start with '12D3KooW', got: {peer_id_str}"
    if len(peer_id_str) < 45 or len(peer_id_str) > 60:
        return False, f"Peer ID length seems invalid. Expected 45-60 chars, got {len(peer_id_str)}: {peer_id_str}"
    valid_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    for char in peer_id_str:
        if char not in valid_chars:
            return False, f"Invalid character '{char}' in peer ID. Must be base58 encoded."
    return True, peer_id_str

def validate_multiaddr(addr_str):
    """Validate that the address string looks like a valid multiaddr"""
    if not (addr_str.startswith("/ip4/") or addr_str.startswith("/ip6/")):
        return False, f"Invalid multiaddr format: {addr_str}"
    if "/quic-v1" not in addr_str:
        return False, f"Missing QUIC transport in multiaddr (expected /quic-v1): {addr_str}"
    if "/udp/" not in addr_str:
        return False, f"Missing UDP transport in multiaddr: {addr_str}"
    return True, addr_str

def check_output():
    """Check the output log for expected QUIC transport functionality"""
    log_path = "checker.log"
    
    # Check if log file exists
    if not os.path.exists(log_path):
        print(f"✗ {log_path} file not found")
        print(f"ℹ️  Expected log file at: {os.path.abspath(log_path)}")
        return False
    
    try:
        with open(log_path, "r") as f:
            output = f.read()
        
        if not output.strip():
            print(f"✗ {log_path} is empty - application may have failed to start")
            return False

        print(f"ℹ️  Log file contents ({len(output)} bytes):")
        print("-" * 60)
        print(output[:500])  # Print first 500 chars for debugging
        if len(output) > 500:
            print("... (truncated)")
        print("-" * 60)

        # Check for incoming dial
        incoming_pattern = r"incoming,([/\w\.:-]+),([/\w\.:-]+)"
        incoming_matches = re.search(incoming_pattern, output)
        if not incoming_matches:
            print("✗ No incoming dial received")
            print("ℹ️  Expected pattern: incoming,<target_addr>,<from_addr>")
            return False
        
        target_addr = incoming_matches.group(1)
        from_addr = incoming_matches.group(2)
        
        valid, t_message = validate_multiaddr(target_addr)
        if not valid:
            print(f"✗ Invalid target address: {t_message}")
            return False
        
        valid, f_message = validate_multiaddr(from_addr)
        if not valid:
            print(f"✗ Invalid from address: {f_message}")
            return False
        
        print(f"✓ Incoming dial detected: {f_message} → {t_message}")

        # Check for connection establishment
        connected_pattern = r"connected,(12D3KooW[A-Za-z0-9]+),([/\w\.:-]+)"
        connected_matches = re.search(connected_pattern, output)
        if not connected_matches:
            print("✗ No connection established")
            print("ℹ️  Expected pattern: connected,<peer_id>,<addr>")
            return False
        
        peer_id = connected_matches.group(1)
        conn_addr = connected_matches.group(2)
        
        valid, peer_message = validate_peer_id(peer_id)
        if not valid:
            print(f"✗ {peer_message}")
            return False
        
        valid, addr_message = validate_multiaddr(conn_addr)
        if not valid:
            print(f"✗ {addr_message}")
            return False
        
        print(f"✓ Connection established with peer {peer_message}")
        print(f"  Address: {addr_message}")

        # Check for ping
        ping_pattern = r"ping,(12D3KooW[A-Za-z0-9]+),(\d+\.?\d*)\s*ms"
        ping_matches = re.search(ping_pattern, output)
        if not ping_matches:
            print("✗ No ping received")
            print("ℹ️  Expected pattern: ping,<peer_id>,<rtt> ms")
            return False
        
        ping_peer_id = ping_matches.group(1)
        rtt = ping_matches.group(2)
        
        valid, peer_message = validate_peer_id(ping_peer_id)
        if not valid:
            print(f"✗ {peer_message}")
            return False
        
        print(f"✓ Ping received from {peer_message}")
        print(f"  RTT: {rtt} ms")

        # Check for connection closure
        closed_pattern = r"closed,(12D3KooW[A-Za-z0-9]+)"
        closed_matches = re.search(closed_pattern, output)
        if not closed_matches:
            print("✗ Connection closure not detected")
            print("ℹ️  Expected pattern: closed,<peer_id>")
            return False
        
        closed_peer_id = closed_matches.group(1)
        valid, peer_message = validate_peer_id(closed_peer_id)
        if not valid:
            print(f"✗ {peer_message}")
            return False
        
        print(f"✓ Connection {peer_message} closed gracefully")

        return True
        
    except Exception as e:
        print(f"✗ Error reading {log_path}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main check function"""
    print("=" * 60)
    print("QUIC Transport Checker - Lesson 4")
    print("=" * 60)
    
    try:
        if not check_output():
            print("\n" + "=" * 60)
            print("❌ QUIC Transport check FAILED")
            print("=" * 60)
            print("\nTroubleshooting tips:")
            print("1. Ensure checker.log is being generated")
            print("2. Check that QUIC transport is properly configured")
            print("3. Verify peer connection was established")
            print("4. Confirm ping protocol is working")
            return False
        
        print("\n" + "=" * 60)
        print("✅ QUIC Transport completed successfully! 🎉")
        print("=" * 60)
        print("\nYou have successfully:")
        print("  • Configured QUIC transport")
        print("  • Established bidirectional connectivity")
        print("  • Measured round-trip times between peers")
        print("  • Gracefully closed connections")
        print("\n🎓 Ready for Lesson 5: Identify Checkpoint!")
        return True
        
    except Exception as e:
        print(f"\n✗ Unexpected error during checking: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)