#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check script for Lesson 5: Identify Protocol Checkpoint
Validates identify protocol usage and peerstore queries.
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

        # Check for custom agent version
        if "Agent version: universal-connectivity-app" not in output:
            print("✗ Missing custom agent version")
            print("ℹ Make sure you set: Identify(agentVersion = \"universal-connectivity-app/1.0.0\")")
            return False
        print("✓ Found custom agent version")

        # Check for listening addresses
        if "Listening on:" not in output:
            print("✗ Missing 'Listening on:' section")
            return False
        print("✓ Found listening addresses")

        # Check for connection
        if "Connected to:" not in output:
            print("✗ No successful connection found")
            return False
        print("✓ Found successful connection")

        # Check for identify protocol waiting
        if "Waiting for identify protocol" in output.lower() or "identify" in output.lower():
            print("✓ Found identify protocol reference")

        # Check for peer information section
        if "=== Peer Information" not in output:
            print("✗ Missing peer information section")
            print("ℹ Make sure you call displayPeerInfo() for connected peers")
            return False
        print("✓ Found peer information section")

        # Check for supported protocols
        if "Supported protocols" not in output:
            print("✗ Missing supported protocols information")
            print("ℹ Query: node.peerstore.getProtocols(peerId)")
            return False
        print("✓ Found supported protocols")

        # Check for at least one protocol listed
        protocol_pattern = r"  - /[a-z0-9/.]+"
        protocol_matches = re.findall(protocol_pattern, output)
        if not protocol_matches:
            print("✗ No protocols listed")
            print("ℹ Wait longer for identify to complete (add Thread.sleep)")
            return False
        print(f"✓ Found {len(protocol_matches)} protocol(s) listed")

        # Check for known addresses
        if "Known addresses" in output:
            print("✓ Found peer addresses")

        # Check for ping
        if "Ping to" in output and ("successful" in output or "RTT" in output):
            print("✓ Ping test successful")
        else:
            print("⚠ Warning: No successful ping found")

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
            "io.libp2p.core",
            "io.libp2p.protocol.Identify",
            "io.libp2p.protocol.Ping",
            "TcpTransport",
            "NoiseXXSecureChannel",
            "Multiaddr",
        ]

        for imp in required_imports:
            if imp not in code:
                print(f"✗ Missing import or reference: {imp}")
                return False
        print("✓ Required imports found")

        # Check for Identify protocol
        if "Identify" not in code or "protocols {" not in code:
            print("✗ Missing Identify protocol configuration")
            print("ℹ Add: protocols { +Identify(agentVersion = \"...\") }")
            return False
        print("✓ Identify protocol configuration found")

        # Check for agent version
        if "agentVersion" not in code or "universal-connectivity-app" not in code:
            print("✗ Missing custom agent version")
            print("ℹ Add: Identify(agentVersion = \"universal-connectivity-app/1.0.0\")")
            return False
        print("✓ Custom agent version found")

        # Check for Ping protocol
        if "Ping()" not in code:
            print("✗ Missing Ping protocol")
            print("ℹ Add: +Ping()")
            return False
        print("✓ Ping protocol found")

        # Check for peerstore access
        if "peerstore" not in code.lower():
            print("✗ Missing peerstore access")
            print("ℹ Add: node.peerstore")
            return False
        print("✓ Peerstore access found")

        # Check for getProtocols call
        if "getProtocols" not in code:
            print("✗ Missing getProtocols call")
            print("ℹ Add: node.peerstore.getProtocols(peerId)")
            return False
        print("✓ getProtocols call found")

        # Check for peer info display
        if "displayPeerInfo" in code or "Peer Information" in code:
            print("✓ Peer information display function found")
        else:
            print("⚠ Warning: Consider creating a displayPeerInfo() function")

        # Check for wait mechanism (identify completion)
        if "Thread.sleep" in code or "TimeUnit.SECONDS" in code:
            print("✓ Wait mechanism for identify completion found")
        else:
            print("⚠ Warning: No wait for identify completion found")
            print("ℹ Add: Thread.sleep(TimeUnit.SECONDS.toMillis(3))")

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
    print("Checking Lesson 5: Identify Protocol Checkpoint")
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
            print("  1. Add: protocols { +Ping() }")
            print("  2. Add: +Identify(agentVersion = \"universal-connectivity-app/1.0.0\")")
            print("  3. Access: node.peerstore")
            print("  4. Query: node.peerstore.getProtocols(peerId)")
            print("  5. Display: Print protocols and addresses")
            print("  6. Wait: Thread.sleep(3000) for identify")
            return False

        print()

        # Check the output
        if not check_output():
            print("\n⚠ Fix the output issues and try again")
            print("\nTroubleshooting:")
            print("  • Make sure custom agent version is set and displayed")
            print("  • Verify Identify protocol is added to protocols block")
            print("  • Verify peerstore queries are working")
            print("  • Wait 3 seconds after connection for identify")
            print("  • Check supported protocols are being listed")
            print("  • Try running: cd app && ./gradlew run")
            return False

        print("=" * 60)
        print("✅ All checks passed! Identify protocol is working correctly.")
        print("✓ You have successfully:")
        print("   • Set custom agent version")
        print("   • Added Identify protocol")
        print("   • Connected to peers")
        print("   • Queried peerstore for peer information")
        print("   • Displayed supported protocols")
        print("   • Retrieved peer metadata")
        print("   • Completed the identify checkpoint!")
        print("\n🎉 You've mastered jvm-libp2p fundamentals!")

        return True

    except Exception as e:
        print(f"✗ Unexpected error during checking: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
