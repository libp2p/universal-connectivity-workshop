#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check script for Lesson 7: Kademlia DHT Checkpoint
Validates that the student's solution implements peer discovery and understands DHT concepts.
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

    return True, f"Valid peer ID format: {peer_id_str}"

def check_output():
    """Check the output log for expected content"""
    if not os.path.exists("stdout.log"):
        print("✗ Error: stdout.log file not found")
        return False

    try:
        with open("stdout.log", "r", encoding='utf-8', errors='replace') as f:
            output = f.read()

        print("ℹ Checking application output...")

        if not output.strip():
            print("✗ stdout.log is empty - application may have failed to start")
            return False

        # Check for startup message
        if "Universal Connectivity" not in output and "Lesson 7" not in output:
            print("✗ Missing lesson 7 startup message")
            print(f"ℹ Actual output: {repr(output[:200])}")
            return False
        print("✓ Found startup message")

        # Check for peer ID output
        peer_id_pattern = r"Peer ID: (12D3KooW[A-Za-z0-9]+)"
        peer_id_match = re.search(peer_id_pattern, output)

        if not peer_id_match:
            print("✗ Missing peer ID output. Expected format: 'Peer ID: 12D3KooW...'")
            print(f"ℹ Actual output: {repr(output[:300])}")
            return False

        peer_id = peer_id_match.group(1)
        valid, message = validate_peer_id(peer_id)
        if not valid:
            print(f"✗ {message}")
            return False
        print(f"✓ {message}")

        # Check for mDNS discovery
        if "mDNS" not in output:
            print("✗ Missing mDNS discovery implementation")
            return False
        print("✓ mDNS discovery implementation found")

        # Check for DHT concepts explanation
        if "DHT" not in output or "Kademlia" not in output:
            print("✗ Missing DHT concepts explanation")
            return False
        print("✓ DHT concepts explanation found")

        # Check for network statistics
        if "Network Statistics" not in output or "connections" not in output.lower():
            print("✗ Missing network statistics display")
            return False
        print("✓ Network statistics display found")

        # Check for workshop completion message
        if "Workshop Complete" in output or "Congratulations" in output:
            print("✓ Workshop completion message found")
        else:
            print("⚠ Warning: No workshop completion message found")

        print("✓ Application ran successfully with discovery features")
        return True

    except Exception as e:
        print(f"✗ Error reading stdout.log: {e}")
        return False

def check_code_structure():
    """Check if the code has the expected structure"""
    app_file = "app/src/main/kotlin/Main.kt"

    if not os.path.exists(app_file):
        print("✗ Error: app/src/main/kotlin/Main.kt file not found")
        return False

    try:
        with open(app_file, "r", encoding='utf-8', errors='replace') as f:
            code = f.read()

        print("ℹ Checking code structure...")

        # Check for required imports
        required_imports = [
            "io.libp2p.core",
            "host",
            "MDnsDiscovery",
        ]

        for imp in required_imports:
            if imp not in code:
                print(f"✗ Missing import or usage: {imp}")
                return False
        print("✓ Required imports found")

        # Check for host creation
        if "host {" not in code:
            print("✗ Missing host creation (host { } DSL)")
            return False
        print("✓ Host creation found")

        # Check for mDNS discovery
        if "MDnsDiscovery" not in code:
            print("✗ Missing MDnsDiscovery implementation")
            return False
        print("✓ MDnsDiscovery implementation found")

        # Check for discovery listener
        if "newPeerFoundListeners" in code or "peerFound" in code.lower():
            print("✓ Peer discovery listener found")
        else:
            print("⚠ Warning: No peer discovery listener found")

        # Check for network statistics function
        if "displayNetworkStats" in code or "connections" in code.lower():
            print("✓ Network statistics function found")
        else:
            print("⚠ Warning: No network statistics function found")

        # Check for protocols
        if "Ping()" not in code or "Identify()" not in code:
            print("⚠ Warning: Missing standard protocols (Ping, Identify)")
        else:
            print("✓ Standard protocols configured")

        print("✓ Code structure is correct")
        return True

    except Exception as e:
        print(f"✗ Error reading code file: {e}")
        return False

def check_build_config():
    """Check if build configuration is correct"""
    build_file = "app/build.gradle.kts"

    if not os.path.exists(build_file):
        print("✗ Error: app/build.gradle.kts file not found")
        return False

    try:
        with open(build_file, "r", encoding='utf-8', errors='replace') as f:
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
    print("Checking Lesson 7: Kademlia DHT Checkpoint")
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
            return False

        print()

        # Check the output
        if not check_output():
            print("\n⚠ Fix the output issues and try again")
            return False

        print("=" * 60)
        print("✅ All checks passed! Your peer discovery application is working correctly.")
        print("✓ You have successfully:")
        print("   • Implemented mDNS local peer discovery")
        print("   • Created a comprehensive discovery application")
        print("   • Understood DHT concepts and architecture")
        print("   • Displayed network statistics and peer connections")
        print("   • Completed the jvm-libp2p workshop!")
        print("\n🎉 Congratulations on completing the Universal Connectivity Workshop!")
        print("🚀 You're now ready to build decentralized applications with jvm-libp2p!")

        return True

    except Exception as e:
        print(f"✗ Unexpected error during checking: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
