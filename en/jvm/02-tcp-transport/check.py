#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check script for Lesson 2: TCP Transport
Validates TCP transport configuration, listening, and connection establishment.
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

def validate_listening_address(addr_str):
    """Validate that the listening address is properly formatted"""
    # Should match pattern: /ip4/x.x.x.x/tcp/port/p2p/12D3KooW...
    pattern = r'/ip[46]/[\d\.:a-fA-F]+/tcp/\d+/p2p/12D3KooW[A-Za-z0-9]+'
    if not re.search(pattern, addr_str):
        return False, f"Invalid listening address format: {addr_str}"
    return True, f"Valid listening address: {addr_str}"

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
        if "Starting Universal Connectivity Application" not in output:
            print("✗ Missing startup message")
            print(f"ℹ Actual output: {repr(output[:200])}")
            return False
        print("✓ Found startup message")

        # Check for peer ID
        peer_id_pattern = r"Local peer id: (12D3KooW[A-Za-z0-9]+)"
        peer_id_match = re.search(peer_id_pattern, output)
        if not peer_id_match:
            print("✗ Missing peer ID output")
            return False
        print(f"✓ Found peer ID: {peer_id_match.group(1)}")

        # Check for listening addresses
        if "Listening on:" not in output:
            print("✗ Missing 'Listening on:' section")
            return False
        print("✓ Found listening addresses section")

        # Check for at least one listening address
        listen_pattern = r'/ip[46]/[\d\.:a-fA-F]+/tcp/\d+/p2p/12D3KooW[A-Za-z0-9]+'
        listen_matches = re.findall(listen_pattern, output)
        if not listen_matches:
            print("✗ No valid listening addresses found")
            return False
        print(f"✓ Found {len(listen_matches)} listening address(es)")

        # Validate listening addresses
        for addr in listen_matches[:2]:  # Check first two addresses
            valid, msg = validate_listening_address(addr)
            if not valid:
                print(f"✗ {msg}")
                return False

        # Check for connection event handling
        if "New connection established:" in output or "Connected to:" in output:
            print("✓ Found connection event messages")
        else:
            print("ℹ No connection events found (this is OK if no peers were dialed)")

        print("✓ Application output is correct")
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
        with open(app_file, "r", encoding='utf-8') as f:
            code = f.read()

        print("ℹ Checking code structure...")

        # Check for required imports
        required_imports = [
            "io.libp2p.core",
            "TcpTransport",
            "NoiseXXSecureChannel",
            "Multiaddr",
        ]

        for imp in required_imports:
            if imp not in code:
                print(f"✗ Missing import or reference: {imp}")
                return False
        print("✓ Required imports found")

        # Check for transport configuration
        if "transports" not in code or "TcpTransport" not in code:
            print("✗ Missing TCP transport configuration")
            return False
        print("✓ TCP transport configuration found")

        # Check for security configuration
        if "secureChannels" not in code or "Noise" not in code:
            print("✗ Missing security channel configuration")
            return False
        print("✓ Security channel configuration found")

        # Check for muxer configuration
        if "muxers" not in code or ("Mplex" in code or "Yamux" in code):
            print("✓ Multiplexer configuration found")
        else:
            print("✗ Missing multiplexer configuration")
            return False

        # Check for listening configuration
        if "listen" not in code:
            print("✗ Missing network listening configuration")
            return False
        print("✓ Network listening configuration found")

        # Check for address printing
        if "listenAddresses" not in code:
            print("✗ Missing code to print listening addresses")
            return False
        print("✓ Address printing found")

        # Check for multiaddr parsing
        if "Multiaddr" not in code:
            print("✗ Missing multiaddress parsing")
            return False
        print("✓ Multiaddress parsing found")

        # Check for connection handling
        if "connect" not in code.lower():
            print("✗ Missing connection code")
            return False
        print("✓ Connection code found")

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
    print("Checking Lesson 2: TCP Transport")
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
        print("✅ All checks passed! TCP transport is working correctly.")
        print("✓ You have successfully:")
        print("   • Configured TCP transport with listening addresses")
        print("   • Added Noise security and Mplex multiplexing")
        print("   • Parsed multiaddresses from environment variables")
        print("   • Displayed listening addresses with peer ID")
        print("   • Implemented connection dialing")
        print("   • Set up event handling for connections")
        print("\n🎉 Ready for Lesson 3: Ping Protocol Checkpoint!")

        return True

    except Exception as e:
        print(f"✗ Unexpected error during checking: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
