#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import argparse
import re
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def validate_peer_id(peer_id, expected=None):
    if not peer_id or not isinstance(peer_id, str):
        return False, "PeerId is missing or not a string."
    if not (45 <= len(peer_id) <= 60):
        return False, f"PeerId length invalid: {len(peer_id)} (should be 45-60 chars)"
    if not all(c in BASE58_ALPHABET for c in peer_id):
        return False, "PeerId contains non-base58 characters."
    if not peer_id.startswith("12D3KooW"):
        return False, "PeerId does not start with '12D3KooW' (expected Ed25519 PeerId)."
    if expected and peer_id != expected:
        return False, f"PeerId does not match expected value from peer-id.json ({expected})"
    return True, "PeerId valid."

def validate_multiaddr(addr, require_circuit=False):
    if not addr or not isinstance(addr, str):
        return False, "Multiaddr is missing or not a string."
    if not (addr.startswith("/ip4/") or addr.startswith("/ip6/")):
        return False, "Multiaddr must start with /ip4/ or /ip6/."
    if "/p2p/" not in addr:
        return False, "Multiaddr must contain /p2p/<PeerId>."
    if require_circuit and "/p2p-circuit" not in addr:
        return False, "Multiaddr must include /p2p-circuit for relayed addresses."
    if not require_circuit and "/p2p-circuit" in addr:
        return False, "Relay node multiaddr should NOT include /p2p-circuit."
    return True, "Multiaddr valid."

def extract_peerid_from_log(log, node_type):
    match = re.search(r"Node started with id ([A-Za-z0-9]+)", log)
    if match:
        return match.group(1)
    else:
        print(f"✗ {node_type}: Could not find PeerId in log.")
        print(f"  Expected format: 'Node started with id <peer-id>'")
        print(f"  Log snippet: {log[:200]}...")
        return None

def extract_multiaddrs_from_log(log):
    # Match multiaddrs that appear after "Listening on:" or standalone
    # Pattern matches: /ip4/.../tcp/.../p2p/... or /ip6/.../tcp/.../p2p/...
    # More flexible pattern to handle various formats
    patterns = [
        r"/ip[46]/[\d\.:]+/tcp/\d+/p2p/[A-Za-z0-9]+",  # Standard format
        r"/ip4/[\d\.]+/tcp/\d+/p2p/[A-Za-z0-9]+",       # IPv4 specific
        r"/ip6/[\d\:a-fA-F]+/tcp/\d+/p2p/[A-Za-z0-9]+", # IPv6 specific
    ]
    all_addrs = []
    for pattern in patterns:
        matches = re.findall(pattern, log)
        all_addrs.extend(matches)
    return list(set(all_addrs))  # Remove duplicates

def extract_advertised_relay_addr(log):
    # Try multiple patterns to extract the relay address
    patterns = [
        r"Advertising with a relay address of ([^\s]+)",
        r"Advertising with a relay address of (\/ip4\/[^\s]+)",
        r"relay address of (\/ip4\/[0-9.]+/tcp/[0-9]+/p2p/[A-Za-z0-9]+/p2p-circuit/p2p/[A-Za-z0-9]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, log)
        if match:
            return match.group(1)
    return None

def extract_connected_to_relay(log):
    match = re.search(r"Connected to the relay ([A-Za-z0-9]+)", log)
    return match.group(1) if match else None

def extract_connected_to_listener(log):
    # Try multiple patterns to extract the connection address
    patterns = [
        r"Connected to the listener node via ([^\s]+)",
        r"Connected to the listener node via (\/ip4\/[^\s]+)",
        r"Connected to the listener.*via (\/ip4\/[0-9.]+/tcp/[0-9]+/p2p/[A-Za-z0-9]+/p2p-circuit[^\s]*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, log)
        if match:
            return match.group(1)
    return None

def main():
    parser = argparse.ArgumentParser(description="Validate circuit relay v2 node setup from logs")
    parser.add_argument('--relay-log', required=True, help='./relay.log')
    parser.add_argument('--listener-log', required=True, help='./listener.log')
    parser.add_argument('--dialer-log', required=True, help='./dialer.log')
    args = parser.parse_args()

    print("=" * 50)
    print("Checking Lesson 4: Circuit Relay v2")
    print("=" * 50)
    print("")

    # --- Relay Node ---
    print("Checking Relay Node...")
    with open(args.relay_log) as f:
        relay_log = f.read()
    
    if not relay_log.strip():
        print("✗ Relay log is empty - relay node may have failed to start")
        sys.exit(1)
    
    # Check for error messages first
    if "Error" in relay_log or "error" in relay_log or "failed" in relay_log.lower():
        print("✗ Relay node encountered errors:")
        error_lines = [line for line in relay_log.split('\n') if 'error' in line.lower() or 'Error' in line or 'failed' in line.lower()]
        for line in error_lines[:5]:
            print(f"  {line}")
        sys.exit(1)
    
    relay_peerid = extract_peerid_from_log(relay_log, "Relay node")
    if not relay_peerid:
        sys.exit(1)
    
    valid, msg = validate_peer_id(relay_peerid)
    if not valid:
        print(f"✗ Relay PeerId invalid: {msg}")
        sys.exit(1)
    print(f"✓ Relay PeerId valid: {relay_peerid}")
        
    relay_multiaddrs = extract_multiaddrs_from_log(relay_log)
    relay_multiaddrs_valid = [ma for ma in relay_multiaddrs if validate_multiaddr(ma, require_circuit=False)[0]]
    if relay_multiaddrs_valid:
        print(f"✓ Relay node listening on {len(relay_multiaddrs_valid)} valid address(es):")
        for ma in relay_multiaddrs_valid:
            print(f"  {ma}")
    else:
        print("✗ Relay node did not advertise any valid multiaddrs (without /p2p-circuit).")
        print(f"  Found multiaddrs: {relay_multiaddrs}")
        sys.exit(1)

    # --- Listener Node ---
    print("\nChecking Listener Node...")
    with open(args.listener_log) as f:
        listener_log = f.read()
    
    if not listener_log.strip():
        print("✗ Listener log is empty - listener node may have failed to start")
        sys.exit(1)
    
    # Check for extraction failure or errors
    if "Failed to extract" in listener_log or "Error" in listener_log or "error" in listener_log.lower():
        print("✗ Listener node failed to start or extract relay address:")
        error_lines = [line for line in listener_log.split('\n') if 'Failed' in line or 'error' in line.lower() or 'Error' in line]
        for line in error_lines[:5]:
            print(f"  {line}")
        if "Failed to extract relay address" in listener_log:
            print("\n  Troubleshooting:")
            print(f"    - Check relay.log exists and contains 'Listening on:'")
            print(f"    - Verify relay address format includes /ip4/172.18.0.10")
        sys.exit(1)
    
    listener_peerid = extract_peerid_from_log(listener_log, "Listener node")
    if not listener_peerid:
        print("\n  Listener log content:")
        print(f"  {listener_log[:500]}...")
        sys.exit(1)
    
    valid, msg = validate_peer_id(listener_peerid)
    if not valid:
        print(f"✗ Listener PeerId invalid: {msg}")
        sys.exit(1)
    print(f"✓ Listener PeerId valid: {listener_peerid}")
    
    relay_connected = extract_connected_to_relay(listener_log)
    if relay_connected == relay_peerid:
        print(f"✓ Listener node connected to relay: {relay_peerid}")
    else:
        print(f"✗ Listener node did not connect to relay {relay_peerid} (found: {relay_connected or 'none'})")
        print(f"  Listener log snippet: {listener_log[:300]}...")
        sys.exit(1)
    
    advertised_addr = extract_advertised_relay_addr(listener_log)
    if advertised_addr and validate_multiaddr(advertised_addr, require_circuit=True)[0]:
        print(f"✓ Listener node advertised relay address: {advertised_addr}")
    else:
        print(f"✗ Listener node did not advertise a valid relay address with /p2p-circuit.")
        if advertised_addr:
            print(f"  Extracted address: {advertised_addr}")
            valid_check = validate_multiaddr(advertised_addr, require_circuit=True)
            print(f"  Validation: {valid_check[1]}")
        print(f"  Listener log snippet: {listener_log[:400]}...")
        sys.exit(1)

    # --- Dialer Node ---
    print("\nChecking Dialer Node...")
    with open(args.dialer_log) as f:
        dialer_log = f.read()
    
    if not dialer_log.strip():
        print("✗ Dialer log is empty - dialer node may have failed to start")
        sys.exit(1)
    
    # Check for extraction failure or errors
    if "Failed to extract" in dialer_log or "Error" in dialer_log or "error" in dialer_log.lower():
        print("✗ Dialer node failed to start or extract listener relay address:")
        error_lines = [line for line in dialer_log.split('\n') if 'Failed' in line or 'error' in line.lower() or 'Error' in line]
        for line in error_lines[:5]:
            print(f"  {line}")
        if "Failed to extract listener relay address" in dialer_log:
            print("\n  Troubleshooting:")
            print(f"    - Check listener.log exists and contains 'Advertising with a relay address of'")
            print(f"    - Verify listener successfully connected to relay")
        sys.exit(1)
    
    dialer_peerid = extract_peerid_from_log(dialer_log, "Dialer node")
    if not dialer_peerid:
        print("\n  Dialer log content:")
        print(f"  {dialer_log[:500]}...")
        sys.exit(1)
    
    valid, msg = validate_peer_id(dialer_peerid)
    if not valid:
        print(f"✗ Dialer PeerId invalid: {msg}")
        sys.exit(1)
    print(f"✓ Dialer PeerId valid: {dialer_peerid}")
    
    dialed_addr = extract_connected_to_listener(dialer_log)
    if dialed_addr and validate_multiaddr(dialed_addr, require_circuit=True)[0]:
        print(f"✓ Dialer node connected to listener via relay address: {dialed_addr}")
    else:
        print(f"✗ Dialer node did not connect to listener via a valid relay address with /p2p-circuit.")
        if dialed_addr:
            print(f"  Extracted address: {dialed_addr}")
            valid_check = validate_multiaddr(dialed_addr, require_circuit=True)
            print(f"  Validation: {valid_check[1]}")
        print(f"  Dialer log snippet: {dialer_log[:400]}...")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("✓ All nodes validated successfully!")
    print("=" * 50)
    print("")
    print("You have successfully:")
    print("  • Set up a relay node that forwards traffic")
    print("  • Configured a listener node to reserve a slot on the relay")
    print("  • Connected a dialer node to the listener through the relay")
    print("  • Demonstrated NAT traversal using Circuit Relay v2")
    print("")
    print("Ready for Lesson 5: Identify Protocol!")
    print("")
    sys.exit(0)

if __name__ == "__main__":
    main() 