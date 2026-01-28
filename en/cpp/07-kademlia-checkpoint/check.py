#!/usr/bin/env python3
"""
Validation script for Lesson 7: Kademlia Checkpoint (Final)
Verifies that the application implements Kademlia DHT and all previous protocols.
"""

import re
import sys
from pathlib import Path

def check_stdout_log():
    """Check stdout.log for expected output patterns."""
    log_file = Path(__file__).parent / "stdout.log"

    if not log_file.exists():
        print("FAIL: stdout.log not found")
        print("Run 'docker compose up --build' first")
        return False

    content = log_file.read_text()

    checks = [
        ("peer ID generation", r"Local peer id: 12D3KooW[a-zA-Z0-9]+"),
        ("TCP listening", r"Listening on TCP:.*9000"),
        ("QUIC listening", r"Listening on QUIC:.*9001"),
        ("Ping protocol", r"Ping.*ping.*1\.0\.0"),
        ("Identify protocol", r"Identify.*id.*1\.0\.0"),
        ("Gossipsub protocol", r"Gossipsub.*meshsub.*1\.0\.0"),
        ("Kademlia protocol", r"Kademlia.*kad.*1\.0\.0"),
        ("Chat topic subscription", r"universal-connectivity"),
        ("Discovery topic", r"universal-connectivity-browser-peer-discovery"),
        ("Transports enabled", r"Transports.*TCP.*QUIC"),
    ]

    all_passed = True
    for name, pattern in checks:
        if re.search(pattern, content, re.IGNORECASE):
            print(f"PASS: {name}")
        else:
            print(f"FAIL: {name} - pattern not found: {pattern}")
            all_passed = False

    return all_passed

def check_source_code():
    """Check main.cpp for required implementations."""
    source_file = Path(__file__).parent / "app" / "main.cpp"

    if not source_file.exists():
        print("FAIL: main.cpp not found")
        return False

    content = source_file.read_text()

    checks = [
        ("Kademlia header", r"#include.*kademlia"),
        ("Kademlia injector", r"makeKademliaInjector"),
        ("Kademlia creation", r"get_kademlia"),
        ("Kademlia start", r"kademlia->start"),
        ("Add peer to DHT", r"kademlia->addPeer"),
        ("Bootstrap DHT", r"kademlia->bootstrap"),
        ("Gossipsub create", r"gossip::create"),
        ("Identify protocol", r"IdentifyMessageProcessor"),
        ("Ping protocol", r"protocol::Ping"),
        ("TCP transport", r"/tcp/"),
        ("QUIC transport", r"/quic"),
    ]

    all_passed = True
    for name, pattern in checks:
        if re.search(pattern, content):
            print(f"PASS: {name} found in source")
        else:
            print(f"FAIL: {name} not found in source")
            all_passed = False

    return all_passed

def main():
    print("=" * 50)
    print("Lesson 7: Kademlia Checkpoint (Final) Validation")
    print("=" * 50)
    print()

    print("Checking source code...")
    print("-" * 30)
    source_ok = check_source_code()
    print()

    print("Checking runtime output...")
    print("-" * 30)
    runtime_ok = check_stdout_log()
    print()

    print("=" * 50)
    if source_ok and runtime_ok:
        print("SUCCESS: All checks passed!")
        print("Lesson 7 complete - Universal Connectivity ready!")
        return 0
    else:
        print("FAILURE: Some checks failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
