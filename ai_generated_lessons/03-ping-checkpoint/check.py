#!/usr/bin/env python3
"""
Check script for Lesson 3: Ping Checkpoint
Validates that the student's solution successfully connects to checker and exchanges pings.
"""

import subprocess
import sys
import os
import re
import time

def run_docker_compose():
    """Run docker-compose to build and test the student's solution with checker"""
    try:
        print("r Building and running student solution with checker...")
        
        # Run docker-compose with appropriate profiles
        local_checker = os.environ.get("LOCAL_CHECKER", "true").lower() == "true"
        
        if local_checker:
            print("i Using local checker")
            cmd = ["docker", "compose", "--profile", "local-checker", "--profile", "always", "up", "--build", "--abort-on-container-exit"]
        else:
            print("i Using external checker")
            cmd = ["docker", "compose", "--profile", "always", "up", "--build", "--abort-on-container-exit"]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode != 0:
            print(f"x Docker compose failed with return code {result.returncode}")
            if result.stdout:
                print(f"x stdout: {result.stdout}")
            if result.stderr:
                print(f"x stderr: {result.stderr}")
            return False
            
        print("v Docker build and run completed successfully")
        return True
        
    except subprocess.TimeoutExpired:
        print("x Docker compose timed out after 180 seconds")
        return False
    except Exception as e:
        print(f"x Error running docker-compose: {e}")
        return False

def check_output():
    """Check the output log for expected ping checkpoint results"""
    if not os.path.exists("stdout.log"):
        print("x stdout.log file not found")
        return False
    
    try:
        with open("stdout.log", "r") as f:
            output = f.read()
        
        print("i Checking ping checkpoint results...")
        
        if not output.strip():
            print("x stdout.log is empty - application may have failed to start")
            return False
        
        # Check for basic startup
        if "Starting Universal Connectivity application" not in output and "Starting ping checker server" not in output:
            print("x Missing startup message from either student app or checker")
            print(f"i Actual output: {repr(output[:500])}")
            return False
        
        # Look for successful ping exchanges
        ping_success_pattern = r"Ping successful to.*RTT.*|Ping response sent to.*RTT.*"
        ping_successes = re.findall(ping_success_pattern, output)
        
        if len(ping_successes) < 1:
            print("x No successful ping exchanges found")
            print(f"i Looking for pattern: {ping_success_pattern}")
            print(f"i Actual output: {repr(output)}")
            return False
        
        print(f"v Found {len(ping_successes)} successful ping exchanges")
        
        # Check for connection establishment
        connection_pattern = r"Connected to:|Student connected:"
        if not re.search(connection_pattern, output):
            print("x No connection establishment found")
            return False
        
        print("v Found connection establishment")
        
        # Look for checkpoint completion if using local checker
        local_checker = os.environ.get("LOCAL_CHECKER", "true").lower() == "true"
        if local_checker:
            if "Checkpoint completed!" in output or "SUCCESS: Ping checkpoint completed" in output:
                print("v Checkpoint completion confirmed by checker")
            else:
                print("^ Checkpoint completion not explicitly confirmed, but ping exchanges detected")
        
        # Check for peer ID output
        peer_id_pattern = r"Local peer id: (12D3KooW[A-Za-z0-9]+)|Checker peer id: (12D3KooW[A-Za-z0-9]+)"
        if not re.search(peer_id_pattern, output):
            print("^ Peer ID not found in output (may be expected)")
        else:
            print("v Found peer ID in output")
        
        return True
        
    except Exception as e:
        print(f"x Error reading stdout.log: {e}")
        return False

def cleanup():
    """Clean up docker resources"""
    try:
        subprocess.run(["docker", "compose", "down"], capture_output=True, timeout=30)
    except:
        pass

def main():
    """Main check function"""
    print("i Checking Lesson 3: Ping Checkpoint")
    print("i " + "=" * 50)
    
    local_checker = os.environ.get("LOCAL_CHECKER", "true").lower() == "true"
    checker_multiaddr = os.environ.get("CHECKER_MULTIADDR", "/ip4/172.27.1.10/tcp/9000")
    
    print(f"i Local checker: {local_checker}")
    print(f"i Target multiaddr: {checker_multiaddr}")
    
    try:
        # Run the student's solution with checker
        if not run_docker_compose():
            return False
        
        # Check the output
        if not check_output():
            return False
        
        print("i " + "=" * 50)
        print("y Checkpoint 1 completed! Your ping protocol implementation works.")
        print("i You have successfully:")
        print("i • Added ping behavior to your libp2p node")
        print("i • Connected to a remote peer")
        print("i • Exchanged ping/pong messages")
        print("i • Handled libp2p events properly")
        print("r Ready for Lesson 4: QUIC Transport!")
        
        return True
        
    except Exception as e:
        print(f"x Unexpected error during checking: {e}")
        return False
    finally:
        cleanup()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)