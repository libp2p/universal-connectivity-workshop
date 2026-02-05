#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check script for Lesson 4: QUIC Transport (jvm-libp2p)
Validates multi-transport architecture understanding and ping protocol.
Note: QUIC is in BETA status in jvm-libp2p, so we check TCP transport.
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

        # Check for listening addresses section
        if "Listening on:" not in output:
            print("✗ Missing 'Listening on:' section")
            return False
        print("✓ Found listening addresses section")

        # Check for TCP addresses (primary transport)
        tcp_pattern = r'/ip[46]/[\d\.:a-fA-F]+/tcp/\d+/p2p/12D3KooW[A-Za-z0-9]+'
        tcp_matches = re.findall(tcp_pattern, output)
        if not tcp_matches:
            print("✗ No TCP listening addresses found")
            return False
        print(f"✓ Found {len(tcp_matches)} TCP listening address(es)")

        # Note about QUIC (informational, not required)
        quic_pattern = r'/ip[46]/[\d\.:a-fA-F]+/udp/\d+/quic-v1/p2p/12D3KooW[A-Za-z0-9]+'
        quic_matches = re.findall(quic_pattern, output)
        if quic_matches:
            print(f"ℹ Found {len(quic_matches)} QUIC address(es) (BETA feature)")
        else:
            print("ℹ No QUIC addresses (expected - QUIC is BETA in jvm-libp2p)")

        # Check for connection
        if "Connected to:" not in output:
            print("✗ No successful connection found")
            return False
        print("✓ Found successful connection")

        # Check for ping
        ping_pattern = r"Ping to .+ successful: RTT = (\d+)ms"
        ping_match = re.search(ping_pattern, output)
        if not ping_match:
            print("✗ No successful ping found")
            if "Ping" in output and "failed" in output:
                print("ℹ Ping failed - check error message in output")
            return False

        rtt_ms = ping_match.group(1)
        print(f"✓ Ping successful with RTT: {rtt_ms}ms")

        # Check for event handler output
        if "Event: Connected to" not in output:
            print("⚠ Warning: Connection event handler may not be working")
        else:
            print("✓ Connection event handler working")

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
        with open(app_file, "r") as f:
            code = f.read()

        print("ℹ Checking code structure...")

        # Check for required imports
        required_imports = [
            "io.libp2p.core.Host",
            "io.libp2p.protocol.Ping",
            "io.libp2p.transport.tcp.TcpTransport",
        ]

        for imp in required_imports:
            if imp not in code:
                print(f"✗ Missing import: {imp}")
                return False
        print("✓ Required imports found")

        # Check for host creation with DSL
        if "host {" not in code:
            print("✗ Missing host DSL creation")
            return False
        print("✓ Host DSL found")

        # Check for TCP transport
        if "TcpTransport" not in code:
            print("✗ Missing TcpTransport configuration")
            return False
        print("✓ TcpTransport found")

        # Check for ping protocol
        if "Ping()" not in code:
            print("✗ Missing Ping protocol")
            return False
        print("✓ Ping protocol found")

        # Check for listen address
        if 'listen("/ip4/0.0.0.0/tcp/0")' not in code and 'listen(' not in code:
            print("✗ Missing listen address configuration")
            return False
        print("✓ Listen address found")

        # Check for connection code
        if "node.network.connect" not in code:
            print("✗ Missing connection code")
            return False
        print("✓ Connection code found")

        # Check for ping execution
        if "ping.ping" not in code:
            print("✗ Missing ping execution")
            return False
        print("✓ Ping execution found")

        # Check for QUIC comments (educational)
        if "QUIC" in code or "quic" in code:
            print("✓ QUIC documentation found (good practice)")
        else:
            print("ℹ Consider adding QUIC comments for future reference")

        print("✓ Code structure is correct")
        return True

    except Exception as e:
        print(f"✗ Error reading code file: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main check function"""
    print("Checking Lesson 4: QUIC Transport (jvm-libp2p)")
    print("=" * 60)

    try:
        # Check code structure first
        if not check_code_structure():
            print("\n⚠ Fix the code structure issues and try again")
            print("\nQuick fix checklist:")
            print("  1. Import TcpTransport and Ping")
            print("  2. Configure TCP transport")
            print("  3. Add Ping protocol")
            print("  4. Connect to peers and ping")
            print("  5. Document QUIC beta status")
            return False

        print()

        # Check the output
        if not check_output():
            print("\n⚠ Fix the output issues and try again")
            print("\nTroubleshooting:")
            print("  • Verify TCP transport is working")
            print("  • Check connection to checkpoint server")
            print("  • Ensure ping protocol is added")
            print("  • Try running: ./gradlew run")
            return False

        print("=" * 60)
        print("✅ All checks passed! Multi-transport architecture understood.")
        print("✓ You have successfully:")
        print("   • Configured TCP transport (production-ready)")
        print("   • Added Ping protocol")
        print("   • Connected to remote peers")
        print("   • Measured RTT with ping")
        print("   • Understood QUIC beta status")
        print("   • Learned multi-transport patterns")
        print("\n🎉 Congratulations! You understand libp2p transport architecture!")
        print("\nℹ Note: QUIC is BETA in jvm-libp2p - use TCP for production")

        return True

    except Exception as e:
        print(f"✗ Unexpected error during checking: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
