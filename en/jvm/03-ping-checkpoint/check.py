#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check script for Lesson 3: Ping Protocol Checkpoint
Validates ping protocol implementation and connectivity to checkpoint server.
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

        # Check for listening addresses
        if "Listening on:" not in output:
            print("✗ Missing 'Listening on:' section")
            return False
        print("✓ Found listening addresses")

        # Check for ping protocol initialization
        if "Ping protocol initialized" not in output:
            print("✗ Missing 'Ping protocol initialized' message")
            print("ℹ Make sure you add Ping() to protocols { }")
            return False
        print("✓ Ping protocol initialized")

        # Check for connection attempt
        if "Dialing peer" not in output and "Connected to:" not in output:
            print("✗ No connection attempts found")
            print("ℹ Application should try to connect to peers")
            return False
        print("✓ Found connection attempt")

        # Check for successful connection
        connection_pattern = r"Connected to: (12D3KooW[A-Za-z0-9]+|Qm[A-Za-z0-9]+)"
        connection_match = re.search(connection_pattern, output)
        if not connection_match:
            print("✗ No successful connection found")
            print("ℹ Check network connectivity and peer addresses")
            return False
        print(f"✓ Connected to peer: {connection_match.group(1)}")

        # Check for ping attempt
        if "Pinging" not in output:
            print("✗ No ping attempts found")
            print("ℹ Application should ping connected peers")
            return False
        print("✓ Found ping attempt")

        # Check for successful ping with RTT
        ping_pattern = r"Ping to .+ successful: RTT = ([\d.]+)ms"
        ping_match = re.search(ping_pattern, output)
        if not ping_match:
            print("✗ No successful ping found")
            print("ℹ Check if ping completed and RTT was displayed")
            # Check if there was a ping failure message
            if "Ping" in output and "failed" in output:
                print("ℹ Ping failed - check error message in output")
            return False

        rtt_str = ping_match.group(1)
        print(f"✓ Ping successful with RTT: {rtt_str}ms")

        # Validate RTT is reasonable (less than 10 seconds)
        try:
            rtt_ms = float(rtt_str)
            if rtt_ms > 10000:  # More than 10 seconds
                print(f"⚠ Warning: RTT seems very high ({rtt_str}ms)")
            elif rtt_ms < 0:
                print(f"⚠ Warning: RTT is negative ({rtt_str}ms)")
        except ValueError:
            pass  # Couldn't parse, but that's OK

        # Check for running state
        if "Application running" in output or "Press Ctrl+C" in output:
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
        with open(app_file, "r") as f:
            code = f.read()

        print("ℹ Checking code structure...")

        # Check for required imports
        required_imports = [
            "io.libp2p.core",
            "host",
            "Ping",
        ]

        for imp in required_imports:
            if imp not in code:
                print(f"✗ Missing import: {imp}")
                print("ℹ Add: io.libp2p.protocol.Ping")
                return False
        print("✓ Required imports found")

        # Check for host DSL usage
        if "host {" not in code:
            print("✗ Missing host creation (host { } DSL)")
            return False
        print("✓ Host creation found")

        # Check for ping protocol addition
        if "Ping()" not in code:
            print("✗ Missing Ping protocol")
            print("ℹ Add: protocols { +Ping() }")
            return False
        print("✓ Ping protocol found")

        # Check for protocols block
        if "protocols {" not in code:
            print("✗ Missing protocols { } block")
            return False
        print("✓ Protocols block found")

        # Check for connection code
        if "network.connect" not in code and ".connect(" not in code:
            print("✗ Missing connection code")
            return False
        print("✓ Connection code found")

        # Check for ping call
        if ".ping()" not in code:
            print("✗ Missing ping call")
            print("ℹ Add: controller.ping()")
            return False
        print("✓ Ping call found")

        # Check for RTT handling
        if "rtt" not in code.lower() or "RTT" not in code:
            print("✗ Missing RTT handling")
            print("ℹ Add: println(\"RTT = \${rtt}ms\")")
            return False
        print("✓ RTT handling found")

        # Check for stream creation
        if "newStream" in code:
            print("✓ Stream creation found")
        else:
            print("ℹ Consider using node.network.newStream for ping protocol")

        # Check for timeout handling
        if "TimeUnit" in code or "get(" in code:
            print("✓ Timeout handling found")
        else:
            print("ℹ Consider adding timeouts for connection and ping")

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
        with open(build_file, "r") as f:
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
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main check function"""
    print("Checking Lesson 3: Ping Protocol Checkpoint")
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
            print("  1. Import: io.libp2p.protocol.Ping")
            print("  2. Add: protocols { +Ping() }")
            print("  3. Connect: node.network.connect(addr)")
            print("  4. Stream: node.network.newStream(\"/ipfs/ping/1.0.0\", peerId)")
            print("  5. Ping: controller.ping()")
            print("  6. Display: println(\"RTT = \${rtt}ms\")")
            return False

        print()

        # Check the output
        if not check_output():
            print("\n⚠ Fix the output issues and try again")
            print("\nTroubleshooting:")
            print("  • Check network connectivity to checkpoint server")
            print("  • Verify multiaddress format includes /p2p/<peer-id>")
            print("  • Ensure ping protocol was initialized successfully")
            print("  • Check for error messages in the output")
            print("  • Try running: cd app && ./gradlew run")
            return False

        print("=" * 60)
        print("✅ All checks passed! Ping protocol is working correctly.")
        print("✓ You have successfully:")
        print("   • Added Ping protocol to the host")
        print("   • Connected to the checkpoint server")
        print("   • Pinged the remote peer")
        print("   • Measured and displayed RTT")
        print("   • Completed your first checkpoint!")
        print("\n🎉 Ready for Lesson 4: QUIC Transport!")

        return True

    except Exception as e:
        print(f"✗ Unexpected error during checking: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
