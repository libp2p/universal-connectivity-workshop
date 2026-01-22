#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check script for Lesson 4: QUIC Transport
Validates QUIC transport configuration alongside TCP.
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

        # Check for TCP addresses
        tcp_pattern = r'/ip[46]/[\d\.:a-fA-F]+/tcp/\d+/p2p/12D3KooW[A-Za-z0-9]+'
        tcp_matches = re.findall(tcp_pattern, output)
        if not tcp_matches:
            print("✗ No TCP listening addresses found")
            return False
        print(f"✓ Found {len(tcp_matches)} TCP listening address(es)")

        # Check for QUIC addresses
        quic_pattern = r'/ip[46]/[\d\.:a-fA-F]+/udp/\d+/quic-v1/p2p/12D3KooW[A-Za-z0-9]+'
        quic_matches = re.findall(quic_pattern, output)
        if not quic_matches:
            print("✗ No QUIC listening addresses found")
            print("ℹ Make sure you added: /ip4/0.0.0.0/udp/0/quic-v1")
            return False
        print(f"✓ Found {len(quic_matches)} QUIC listening address(es)")

        # Verify both transport types are present
        has_tcp = any(tcp_matches)
        has_quic = any(quic_matches)

        if not (has_tcp and has_quic):
            print("✗ Missing one or both transport types")
            if not has_tcp:
                print("  Missing: TCP transport")
            if not has_quic:
                print("  Missing: QUIC transport")
            return False
        print("✓ Both TCP and QUIC transports configured")

        # Check for ping service
        if "Ping service created" not in output:
            print("✗ Missing 'Ping service created' message")
            return False
        print("✓ Ping service created")

        # Check for connection
        if "Connected to:" not in output:
            print("✗ No successful connection found")
            return False
        print("✓ Found successful connection")

        # Check for ping
        ping_pattern = r"Ping to .+ successful: RTT = ([\d.]+[µmn]?s)"
        ping_match = re.search(ping_pattern, output)
        if not ping_match:
            print("✗ No successful ping found")
            if "Ping" in output and "failed" in output:
                print("ℹ Ping failed - check error message in output")
            return False

        rtt_str = ping_match.group(1)
        print(f"✓ Ping successful with RTT: {rtt_str}")

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
            "ping",
        ]

        for imp in required_imports:
            if imp not in code:
                print(f"✗ Missing import: {imp}")
                return False
        print("✓ Required imports found")

        # Check for TCP listen address
        if not ("ListenAddrStrings" in code or "ListenAddrs" in code):
            print("✗ Missing listen address configuration")
            return False

        if "/tcp/0" not in code and "/tcp/" not in code:
            print("✗ Missing TCP listen address")
            print("ℹ Add: /ip4/0.0.0.0/tcp/0")
            return False
        print("✓ TCP listen address found")

        # Check for QUIC listen address
        if "/quic" not in code.lower():
            print("✗ Missing QUIC listen address")
            print("ℹ Add: /ip4/0.0.0.0/udp/0/quic-v1")
            return False
        print("✓ QUIC listen address found")

        # Verify QUIC format
        if "/udp/" in code and "/quic" in code:
            print("✓ Proper QUIC multiaddress format")
        else:
            print("⚠ Warning: QUIC address format may be incorrect")
            print("ℹ Correct format: /ip4/0.0.0.0/udp/0/quic-v1")

        # Check for ping service
        if "ping.NewPingService" not in code:
            print("✗ Missing ping service creation")
            return False
        print("✓ Ping service creation found")

        # Check for connection code
        if "h.Connect" not in code and "host.Connect" not in code:
            print("✗ Missing connection code")
            return False
        print("✓ Connection code found")

        print("✓ Code structure is correct")
        return True

    except Exception as e:
        print(f"✗ Error reading code file: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main check function"""
    print("Checking Lesson 4: QUIC Transport")
    print("=" * 60)

    try:
        # Check code structure first
        if not check_code_structure():
            print("\n⚠ Fix the code structure issues and try again")
            print("\nQuick fix checklist:")
            print("  1. Keep TCP: /ip4/0.0.0.0/tcp/0")
            print("  2. Add QUIC: /ip4/0.0.0.0/udp/0/quic-v1")
            print("  3. Both in ListenAddrStrings()")
            return False

        print()

        # Check the output
        if not check_output():
            print("\n⚠ Fix the output issues and try again")
            print("\nTroubleshooting:")
            print("  • Verify both TCP and QUIC addresses in output")
            print("  • Check UDP port not blocked by firewall")
            print("  • Ensure QUIC multiaddress format correct")
            print("  • Try running: go run app/main.go")
            return False

        print("=" * 60)
        print("✅ All checks passed! QUIC transport is working correctly.")
        print("✓ You have successfully:")
        print("   • Added QUIC transport alongside TCP")
        print("   • Configured multi-transport listening")
        print("   • Connected using automatic transport selection")
        print("   • Verified connectivity with ping")
        print("   • Mastered multi-transport libp2p!")
        print("\n🎉 Ready for Lesson 5: Identify Protocol Checkpoint!")

        return True

    except Exception as e:
        print(f"✗ Unexpected error during checking: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
