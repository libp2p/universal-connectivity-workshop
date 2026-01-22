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

        # Check for custom agent version
        if "Agent version: universal-connectivity-app" not in output:
            print("✗ Missing custom agent version")
            print("ℹ Make sure you set: libp2p.UserAgent(\"universal-connectivity-app/1.0.0\")")
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
        if "=== Peer Information:" not in output:
            print("✗ Missing peer information section")
            print("ℹ Make sure you call displayPeerInfo() for connected peers")
            return False
        print("✓ Found peer information section")

        # Check for supported protocols
        if "Supported protocols" not in output:
            print("✗ Missing supported protocols information")
            print("ℹ Query: h.Peerstore().GetProtocols(peerID)")
            return False
        print("✓ Found supported protocols")

        # Check for at least one protocol listed
        protocol_pattern = r"  - /[a-z0-9/.]+"
        protocol_matches = re.findall(protocol_pattern, output)
        if not protocol_matches:
            print("✗ No protocols listed")
            print("ℹ Wait longer for identify to complete (add time.Sleep)")
            return False
        print(f"✓ Found {len(protocol_matches)} protocol(s) listed")

        # Check for agent version or known addresses
        if "Agent version:" in output or "Known addresses" in output:
            print("✓ Found additional peer metadata")

        # Check for ping
        ping_pattern = r"Ping to .+ successful: RTT = ([\d.]+[µmn]?s)"
        ping_match = re.search(ping_pattern, output)
        if not ping_match:
            print("✗ No successful ping found")
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

        # Check for UserAgent configuration
        if "UserAgent" not in code:
            print("✗ Missing UserAgent configuration")
            print("ℹ Add: libp2p.UserAgent(\"universal-connectivity-app/1.0.0\")")
            return False
        print("✓ UserAgent configuration found")

        # Check for peerstore access
        if "Peerstore()" not in code:
            print("✗ Missing peerstore access")
            print("ℹ Add: h.Peerstore()")
            return False
        print("✓ Peerstore access found")

        # Check for GetProtocols call
        if "GetProtocols" not in code:
            print("✗ Missing GetProtocols call")
            print("ℹ Add: h.Peerstore().GetProtocols(peerID)")
            return False
        print("✓ GetProtocols call found")

        # Check for peer info display
        if "Peer Information" in code or "displayPeerInfo" in code:
            print("✓ Peer information display function found")
        else:
            print("ℹ Consider creating a displayPeerInfo() function")

        # Check for time.Sleep or event subscription (identify completion)
        if "time.Sleep" in code or "EvtPeerIdentification" in code:
            print("✓ Wait mechanism for identify completion found")
        else:
            print("⚠ Warning: No wait for identify completion found")
            print("ℹ Add: time.Sleep(2 * time.Second) after connection")

        print("✓ Code structure is correct")
        return True

    except Exception as e:
        print(f"✗ Error reading code file: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main check function"""
    print("Checking Lesson 5: Identify Protocol Checkpoint")
    print("=" * 60)

    try:
        # Check code structure first
        if not check_code_structure():
            print("\n⚠ Fix the code structure issues and try again")
            print("\nQuick fix checklist:")
            print("  1. Add: libp2p.UserAgent(\"universal-connectivity-app/1.0.0\")")
            print("  2. Access: peerStore := h.Peerstore()")
            print("  3. Query: protocols, _ := peerStore.GetProtocols(peerID)")
            print("  4. Display: Print protocols, agent version, addresses")
            print("  5. Wait: time.Sleep(2 * time.Second) for identify")
            return False

        print()

        # Check the output
        if not check_output():
            print("\n⚠ Fix the output issues and try again")
            print("\nTroubleshooting:")
            print("  • Make sure custom agent version is set and displayed")
            print("  • Verify peerstore queries are working")
            print("  • Wait 2 seconds after connection for identify")
            print("  • Check supported protocols are being listed")
            print("  • Try running: go run app/main.go")
            return False

        print("=" * 60)
        print("✅ All checks passed! Identify protocol is working correctly.")
        print("✓ You have successfully:")
        print("   • Set custom agent version")
        print("   • Connected to peers")
        print("   • Queried peerstore for peer information")
        print("   • Displayed supported protocols")
        print("   • Retrieved peer metadata")
        print("   • Completed the identify checkpoint!")
        print("\n🎉 Ready for Lesson 6: GossipSub Pub/Sub Checkpoint!")

        return True

    except Exception as e:
        print(f"✗ Unexpected error during checking: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
