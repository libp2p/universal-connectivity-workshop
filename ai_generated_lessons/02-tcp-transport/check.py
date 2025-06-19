#!/usr/bin/env python3
"""
Check script for Lesson 2: TCP Transport
Validates that the student's solution can listen and handle connections.
"""

import subprocess
import sys
import os
import re

def run_docker_compose():
    """Run docker-compose to build and test the student's solution"""
    try:
        print("r Building and running student solution...")
        
        # Run docker-compose
        result = subprocess.run(
            ["docker", "compose", "up", "--build", "--abort-on-container-exit"],
            capture_output=True,
            text=True,
            timeout=120
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
        print("x Docker compose timed out after 120 seconds")
        return False
    except Exception as e:
        print(f"x Error running docker-compose: {e}")
        return False

def validate_multiaddr(addr_str):
    """Validate that the address string looks like a valid multiaddr"""
    # Basic multiaddr validation - should start with /ip4/ or /ip6/
    if not (addr_str.startswith("/ip4/") or addr_str.startswith("/ip6/")):
        return False, f"Invalid multiaddr format: {addr_str}"
    
    # Should contain /tcp/ for TCP transport
    if "/tcp/" not in addr_str:
        return False, f"Missing TCP transport in multiaddr: {addr_str}"
    
    return True, f"Valid multiaddr: {addr_str}"

def check_output():
    """Check the output log for expected TCP transport functionality"""
    if not os.path.exists("stdout.log"):
        print("x stdout.log file not found")
        return False
    
    try:
        with open("stdout.log", "r") as f:
            output = f.read()
        
        print("i Checking TCP transport functionality...")
        
        if not output.strip():
            print("x stdout.log is empty - application may have failed to start")
            return False
        
        # Check for startup message
        if "Starting Universal Connectivity application" not in output:
            print("x Missing startup message. Expected: 'Starting Universal Connectivity application...'")
            print(f"i Actual output: {repr(output[:500])}")
            return False
        print("v Found startup message")
        
        # Check for peer ID output
        peer_id_pattern = r"Local peer id: (12D3KooW[A-Za-z0-9]+)"
        peer_id_match = re.search(peer_id_pattern, output)
        
        if not peer_id_match:
            print("x Missing peer ID output. Expected format: 'Local peer id: 12D3KooW...'")
            return False
        
        peer_id = peer_id_match.group(1)
        print(f"v Found peer ID: {peer_id}")
        
        # Check for listening addresses
        listen_pattern = r"Listening on: ([/\w\.:]+)"
        listen_matches = re.findall(listen_pattern, output)
        
        if not listen_matches:
            print("x No listening addresses found. Expected format: 'Listening on: /ip4/.../tcp/...'")
            print(f"i Searching for pattern: {listen_pattern}")
            print(f"i In output: {repr(output)}")
            return False
        
        print(f"v Found {len(listen_matches)} listening address(es)")
        
        # Validate at least one listening address
        valid_addresses = 0
        for addr in listen_matches:
            valid, message = validate_multiaddr(addr)
            if valid:
                valid_addresses += 1
                print(f"v {message}")
            else:
                print(f"^ {message}")
        
        if valid_addresses == 0:
            print("x No valid listening addresses found")
            return False
        
        # Check that application runs for reasonable time without crashing
        lines = output.strip().split('\n')
        if len(lines) < 3:  # Should have startup, peer id, and at least one listening address
            print("x Application seems to have crashed too quickly")
            print(f"i Output lines: {lines}")
            return False
        
        print("v Application started successfully with TCP transport")
        
        # Optional: Check for connection attempts if arguments were provided
        if "Attempting to connect to:" in output:
            print("v Found connection attempt (command line argument detected)")
            
            # Look for connection results
            if "Connected to:" in output:
                print("v Successful outgoing connection detected")
            elif "Failed to connect" in output:
                print("i Connection attempt failed (may be expected if target not available)")
        
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
    print("i Checking Lesson 2: TCP Transport")
    print("i " + "=" * 50)
    
    try:
        # Run the student's solution
        if not run_docker_compose():
            return False
        
        # Check the output
        if not check_output():
            return False
        
        print("i " + "=" * 50)
        print("y TCP transport lesson completed successfully!")
        print("i You have successfully:")
        print("i • Configured TCP transport with Noise and Yamux")
        print("i • Set up listening on network interfaces")
        print("i • Handled connection events properly")
        print("i • Created a foundation for peer-to-peer communication")
        print("r Ready for Lesson 3: Ping Checkpoint!")
        
        return True
        
    except Exception as e:
        print(f"x Unexpected error during checking: {e}")
        return False
    finally:
        cleanup()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)