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

def check_output():
    """Check the output log for expected content"""
    if not os.path.exists("stdout.log"):
        print("✗ Error: stdout.log file not found")
        print("ℹ Run the application first to generate output")
        return False

    try:
        with open("stdout.log", "r", encoding='utf-8', errors='replace') as f:
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
            print("ℹ Make sure you add gossip protocol to host")
            return False
        print("✓ GossipSub service created")

        # Check for topic join
        if "Joined topic:" not in output:
            print("✗ Missing topic join message")
            print("ℹ Make sure you call: api.subscribe(topicName)")
            return False
        print("✓ Joined topic")

        # Check for sent messages
        sent_pattern = r"\[SENT\].*Message #\d+"
        sent_matches = re.findall(sent_pattern, output)
        if not sent_matches:
            print("✗ No published messages found")
            print("ℹ Make sure you're publishing messages with api.publish()")
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
    app_file = "app/src/main/kotlin/Main.kt"

    if not os.path.exists(app_file):
        print("✗ Error: app/src/main/kotlin/Main.kt file not found")
        return False

    try:
        with open(app_file, "r", encoding='utf-8') as f:
            code = f.read()

        print("ℹ Checking code structure...")

        # Check for required imports
        required_imports = [
            "io.libp2p.pubsub.gossip.Gossip",
            "io.libp2p.protocol.Identify",
            "io.libp2p.protocol.Ping",
        ]

        for imp in required_imports:
            if imp not in code:
                print(f"✗ Missing import: {imp}")
                return False
        print("✓ Required imports found")

        # Check for Gossip creation
        if "Gossip()" not in code:
            print("✗ Missing Gossip instance creation")
            print("ℹ Add: val gossip = Gossip()")
            return False
        print("✓ Gossip instance creation found")

        # Check for gossip in protocols
        if "+gossip" not in code and "protocols" in code:
            print("✗ Gossip not added to protocols")
            print("ℹ Add gossip to protocols block")
            return False
        print("✓ Gossip added to protocols")

        # Check for router access
        if "gossip.router" not in code and ".router" not in code:
            print("✗ Missing GossipSub router access")
            print("ℹ Add: val api = gossip.router")
            return False
        print("✓ Router access found")

        # Check for subscribe
        if ".subscribe(" not in code and "api.subscribe" not in code:
            print("✗ Missing subscription")
            print("ℹ Add: api.subscribe(topicName)")
            return False
        print("✓ Subscription found")

        # Check for publish
        if ".publish(" not in code and "api.publish" not in code:
            print("✗ Missing publish call")
            print("ℹ Add: api.publish(topicName, data)")
            return False
        print("✓ Publish call found")

        # Check for message handler
        if "msg.from" not in code and "msg.data" not in code:
            print("⚠ Warning: Message handler may be missing")
            print("ℹ Use: api.subscribe { msg -> ... }")
        else:
            print("✓ Message handler found")

        # Check for thread usage
        if "thread(" in code or "Thread(" in code:
            print("✓ Threading found for concurrent operations")
        else:
            print("⚠ Warning: No threading detected for publishing")

        print("✓ Code structure is correct")
        return True

    except Exception as e:
        print(f"✗ Error reading code file: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_build_config():
    """Check if build configuration is correct"""
    build_file = "app/build.gradle.kts"

    if not os.path.exists(build_file):
        print("✗ Error: app/build.gradle.kts file not found")
        return False

    try:
        with open(build_file, "r", encoding='utf-8') as f:
            content = f.read()

        print("ℹ Checking build configuration...")

        # Check for jvm-libp2p dependency
        if "io.libp2p:jvm-libp2p" not in content:
            print("✗ Missing jvm-libp2p dependency in build.gradle.kts")
            return False
        print("✓ jvm-libp2p dependency found")

        # Check for JitPack repository
        if "jitpack.io" not in content:
            print("✗ Missing jitpack.io repository in build.gradle.kts")
            return False
        print("✓ JitPack repository configured")

        print("✓ Build configuration is correct")
        return True

    except Exception as e:
        print(f"✗ Error reading build file: {e}")
        return False

def main():
    """Main check function"""
    print("Checking Lesson 6: GossipSub Pub/Sub Checkpoint")
    print("=" * 60)

    try:
        # Check build configuration first
        if not check_build_config():
            print("\n⚠ Fix the build configuration issues and try again")
            return False

        print()

        # Check code structure
        if not check_code_structure():
            print("\n⚠ Fix the code structure issues and try again")
            print("\nQuick fix checklist:")
            print("  1. Create: val gossip = Gossip()")
            print("  2. Add to protocols: +gossip")
            print("  3. Get API: val api = gossip.router")
            print("  4. Subscribe: api.subscribe(topicName)")
            print("  5. Publish: api.publish(topicName, data)")
            print("  6. Handle: api.subscribe { msg -> ... }")
            return False

        print()

        # Check the output
        if not check_output():
            print("\n⚠ Fix the output issues and try again")
            print("\nTroubleshooting:")
            print("  • Verify GossipSub service is created")
            print("  • Check topic join and subscription are successful")
            print("  • Ensure messages are being published")
            print("  • Verify publish thread is running")
            print("  • Try running: gradle run")
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
        print("\n🎉 Congratulations on completing the GossipSub checkpoint!")

        return True

    except Exception as e:
        print(f"✗ Unexpected error during checking: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
