#!/usr/bin/env python3
import sys
import argparse
import json
import re

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
        return None

def extract_multiaddrs_from_log(log):
    return re.findall(r"/ip[46]/[\w\.:]+/\w+(?:/\w+)*", log)

def extract_advertised_relay_addr(log):
    match = re.search(r"Advertising with a relay address of ([^\s]+)", log)
    return match.group(1) if match else None

def extract_connected_to_relay(log):
    match = re.search(r"Connected to the relay ([A-Za-z0-9]+)", log)
    return match.group(1) if match else None

def extract_connected_to_listener(log):
    match = re.search(r"Connected to the listener node via ([^\s]+)", log)
    return match.group(1) if match else None

def main():
    parser = argparse.ArgumentParser(description="Validate circuit relay v2 node setup from logs and peer-id.json.")
    parser.add_argument('--relay-log', required=True, help='Path to relay node log')
    parser.add_argument('--listener-log', required=True, help='Path to listener node log')
    parser.add_argument('--dialer-log', required=True, help='Path to dialer node log')
    parser.add_argument('--relay-peerid-json', required=True, help='Path to relay peer-id.json')
    args = parser.parse_args()

    # Load relay peer-id.json
    with open(args.relay_peerid_json) as f:
        relay_peerid_json = json.load(f)
    relay_peerid_expected = relay_peerid_json["id"]

    # --- Relay Node ---
    with open(args.relay_log) as f:
        relay_log = f.read()
    relay_peerid = extract_peerid_from_log(relay_log, "Relay node")
    valid, msg = validate_peer_id(relay_peerid, expected=relay_peerid_expected)
    if valid:
        print(f"✓ Relay PeerId valid and matches peer-id.json: {relay_peerid}")
    else:
        print(f"✗ Relay PeerId invalid: {msg}")
        sys.exit(1)
    relay_multiaddrs = extract_multiaddrs_from_log(relay_log)
    relay_multiaddrs_valid = [ma for ma in relay_multiaddrs if validate_multiaddr(ma, require_circuit=False)[0]]
    if relay_multiaddrs_valid:
        print(f"✓ Relay node listening on {len(relay_multiaddrs_valid)} valid address(es):")
        for ma in relay_multiaddrs_valid:
            print(f"  {ma}")
    else:
        print("✗ Relay node did not advertise any valid multiaddrs (without /p2p-circuit).")
        sys.exit(1)

    # --- Listener Node ---
    with open(args.listener_log) as f:
        listener_log = f.read()
    listener_peerid = extract_peerid_from_log(listener_log, "Listener node")
    valid, msg = validate_peer_id(listener_peerid)
    if valid:
        print(f"✓ Listener PeerId valid: {listener_peerid}")
    else:
        print(f"✗ Listener PeerId invalid: {msg}")
        sys.exit(1)
    relay_connected = extract_connected_to_relay(listener_log)
    if relay_connected == relay_peerid:
        print(f"✓ Listener node connected to relay: {relay_peerid}")
    else:
        print(f"✗ Listener node did not connect to relay {relay_peerid} (found: {relay_connected})")
        sys.exit(1)
    advertised_addr = extract_advertised_relay_addr(listener_log)
    if advertised_addr and validate_multiaddr(advertised_addr, require_circuit=True)[0]:
        print(f"✓ Listener node advertised relay address: {advertised_addr}")
    else:
        print(f"✗ Listener node did not advertise a valid relay address with /p2p-circuit.")
        sys.exit(1)

    # --- Dialer Node ---
    with open(args.dialer_log) as f:
        dialer_log = f.read()
    dialer_peerid = extract_peerid_from_log(dialer_log, "Dialer node")
    valid, msg = validate_peer_id(dialer_peerid)
    if valid:
        print(f"✓ Dialer PeerId valid: {dialer_peerid}")
    else:
        print(f"✗ Dialer PeerId invalid: {msg}")
        sys.exit(1)
    dialed_addr = extract_connected_to_listener(dialer_log)
    if dialed_addr and validate_multiaddr(dialed_addr, require_circuit=True)[0]:
        print(f"✓ Dialer node connected to listener via relay address: {dialed_addr}")
    else:
        print(f"✗ Dialer node did not connect to listener via a valid relay address with /p2p-circuit.")
        sys.exit(1)

    print("\n✓ All nodes validated successfully! Your circuit relay v2 setup is correct.")
    sys.exit(0)

if __name__ == "__main__":
    main() 


# Script for Test run-- 
# python check.py \
#   --relay-log relay.log \
#   --listener-log listener.log \
#   --dialer-log dialer.log \
#   --relay-peerid-json peer-id.json