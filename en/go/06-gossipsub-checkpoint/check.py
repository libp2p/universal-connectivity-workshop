#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check script for Lesson 6: GossipSub Pub/Sub Checkpoint
Validates GossipSub implementation with topic join, publish, and subscribe.
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
import time

def check_output():
    """Check the output log for expected content"""
    if not os.path.exists("stdout.log"):
        print("✗ Error: stdout.log file not found")
        print("ℹ Run the application first to generate output")
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
            print("✗ Missing startup message")
            return False
        print("✓ Found startup message")

        # Check for peer ID
        peer_id_pattern = r"Local peer id: (12D3KooW[A-Za-z0-9]+)"
        peer_id_match = re.search(peer_id_pattern, output)
        if not peer_id_match:
            print("✗ Missing peer ID output")
            return False
        print(f"✓ Found peer ID: {peer_id_match.group(1)}")

        # Check for GossipSub creation
        if "GossipSub service created" not in output:
            print("✗ Missing 'GossipSub service created' message")
            print("ℹ Make sure you call: pubsub.NewGossipSub(ctx, h)")
            return False
        print("✓ GossipSub service created")

        # Check for topic join
        if "Joined topic:" not in output:
            print("✗ Missing topic join message")
            print("ℹ Make sure you call: ps.Join(topicName)")
            return False
        print("✓ Joined topic")

        # Check for subscription
        if "Subscribed to topic" not in output and "Subscribe" not in output:
            print("✗ Missing subscription message")
            print("ℹ Make sure you call: topic.Subscribe()")
            return False
        print("✓ Subscribed to topic")

        # Check for sent messages
        sent_pattern = r"\[SENT\].*Message #\d+"
        sent_matches = re.findall(sent_pattern, output)
        if not sent_matches:
            print("✗ No published messages found")
            print("ℹ Make sure you're publishing messages with topic.Publish()")
            return False
        print(f"✓ Found {len(sent_matches)} published message(s)")

        # Check message format
        if "Hello from" in output and "Message #" in output:
            print("✓ Messages have correct format")

        # Check for received messages (optional - may not have peers)
        received_pattern = r"\[RECEIVED\]"
        received_matches = re.findall(received_pattern, output)
        if received_matches:
            print(f"✓ Found {len(received_matches)} received message(s) from peers")
        else:
            print("ℹ No messages received from other peers (this is OK if running standalone)")

        # Check for application running message
        if "Application running" in output or "Messages will be published" in output:
            print("✓ Application reached running state")

        print("✓ All output checks passed")
        return True

    except Exception as e:
        print(f"✗ Error reading stdout.log: {e}")
        import traceback
        traceback.print_exc()
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
            "pubsub",
        ]

        for imp in required_imports:
            if imp not in code:
                print(f"✗ Missing import: {imp}")
                print("ℹ Add: pubsub \"github.com/libp2p/go-libp2p-pubsub\"")
                return False
        print("✓ Required imports found")

        # Check for GossipSub creation
        if "NewGossipSub" not in code:
            print("✗ Missing GossipSub creation")
            print("ℹ Add: ps, err := pubsub.NewGossipSub(ctx, h)")
            return False
        print("✓ GossipSub creation found")

        # Check for Join
        if ".Join(" not in code and "ps.Join" not in code:
            print("✗ Missing topic join")
            print("ℹ Add: topic, err := ps.Join(topicName)")
            return False
        print("✓ Topic join found")

        # Check for Subscribe
        if ".Subscribe()" not in code and "topic.Subscribe" not in code:
            print("✗ Missing subscription")
            print("ℹ Add: sub, err := topic.Subscribe()")
            return False
        print("✓ Subscription found")

        # Check for Publish
        if ".Publish(" not in code and "topic.Publish" not in code:
            print("✗ Missing publish call")
            print("ℹ Add: topic.Publish(ctx, []byte(msg))")
            return False
        print("✓ Publish call found")

        # Check for receiving messages
        if ".Next(" not in code and "sub.Next" not in code:
            print("✗ Missing message receiving")
            print("ℹ Add: msg, err := sub.Next(ctx)")
            return False
        print("✓ Message receiving found")

        # Check for goroutines (concurrent operations)
        goroutine_count = code.count("go func()")
        if goroutine_count < 2:
            print("⚠ Warning: Expected at least 2 goroutines (publish and receive)")
            print("ℹ Use: go func() { ... }() for concurrent operations")
        else:
            print(f"✓ Found {goroutine_count} goroutine(s) for concurrent operations")

        print("✓ Code structure is correct")
        return True

    except Exception as e:
        print(f"✗ Error reading code file: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main check function"""
    print("Checking Lesson 6: GossipSub Pub/Sub Checkpoint")
    print("=" * 60)

    try:
        # Check code structure first
        if not check_code_structure():
            print("\n⚠ Fix the code structure issues and try again")
            print("\nQuick fix checklist:")
            print("  1. Import: pubsub \"github.com/libp2p/go-libp2p-pubsub\"")
            print("  2. Create: ps, _ := pubsub.NewGossipSub(ctx, h)")
            print("  3. Join: topic, _ := ps.Join(\"topic-name\")")
            print("  4. Subscribe: sub, _ := topic.Subscribe()")
            print("  5. Publish: go func() { topic.Publish(ctx, data) }()")
            print("  6. Receive: go func() { msg, _ := sub.Next(ctx) }()")
            return False

        print()

        # Check the output
        if not check_output():
            print("\n⚠ Fix the output issues and try again")
            print("\nTroubleshooting:")
            print("  • Verify GossipSub service is created")
            print("  • Check topic join and subscription are successful")
            print("  • Ensure messages are being published")
            print("  • Verify publish/receive goroutines are running")
            print("  • Try running: go run app/main.go")
            return False

        print("=" * 60)
        print("✅ All checks passed! GossipSub pub/sub is working correctly.")
        print("✓ You have successfully:")
        print("   • Created GossipSub instance")
        print("   • Joined a topic")
        print("   • Subscribed to receive messages")
        print("   • Published messages to the topic")
        print("   • Implemented concurrent publish/receive")
        print("   • Built a P2P messaging application!")
        print("\n🎉 Ready for Lesson 7: Kademlia DHT Checkpoint (Final Lesson)!")

        return True

    except Exception as e:
        print(f"✗ Unexpected error during checking: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
