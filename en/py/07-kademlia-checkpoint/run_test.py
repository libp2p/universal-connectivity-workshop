#!/usr/bin/env python3
"""
Test runner for Kademlia DHT Implementation
This script orchestrates running the server, client, and checker
"""

import os
import subprocess
import sys
import time
import signal
from typing import Optional


def run_command_background(cmd: list, log_file: str) -> subprocess.Popen:
    """Run a command in the background, redirecting output to a log file."""
    print(f"Running: {' '.join(cmd)} > {log_file}")
    with open(log_file, 'w') as f:
        proc = subprocess.Popen(
            cmd,
            stdout=f,
            stderr=subprocess.STDOUT,
            text=True
        )
    return proc


def wait_for_file(filepath: str, timeout: int = 10) -> bool:
    """Wait for a file to exist and have content."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    content = f.read().strip()
                    if content:
                        print(f"Found content in {filepath}: {content}")
                        return True
            except Exception:
                pass
        time.sleep(0.5)
    return False


def cleanup_processes(*processes):
    """Clean up background processes."""
    for proc in processes:
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()


def main():
    """Main test runner."""
    print("=" * 60)
    print("Kademlia DHT Implementation Test Runner")
    print("=" * 60)
    
    server_proc = None
    client_proc = None
    
    try:
        # Clean up any existing log files
        for log_file in ["server.log", "client.log", "checker.log"]:
            if os.path.exists(log_file):
                os.remove(log_file)
        
        # Remove any existing server address file
        for addr_file in ["server_node_addr.txt", "app/server_node_addr.txt"]:
            if os.path.exists(addr_file):
                os.remove(addr_file)
        
        print("1. Starting DHT server node...")
        server_proc = run_command_background(
            ["python", "app/main.py", "--mode", "server", "--port", "8000", "--verbose"],
            "server.log"
        )
        
        # Wait for server to start and create address file
        print("2. Waiting for server to initialize...")
        if not wait_for_file("app/server_node_addr.txt", timeout=15):
            print("X Server failed to start or create address file")
            return False
        
        # Read the server address
        with open("app/server_node_addr.txt", 'r') as f:
            server_addr = f.read().strip()
        print(f"3. Server started at: {server_addr}")
        
        # Wait a moment for server to fully initialize
        time.sleep(2)
        
        print("4. Starting DHT client node...")
        client_proc = run_command_background(
            ["python", "app/main.py", "--mode", "client", "--bootstrap", server_addr, "--verbose"],
            "client.log"
        )
        
        # Wait for client to connect
        print("5. Waiting for client to connect...")
        time.sleep(3)
        
        print("6. Running checker...")
        # Run checker with the server address
        env = os.environ.copy()
        env["REMOTE_PEERS"] = server_addr
        
        with open("checker.log", 'w') as f:
            checker_result = subprocess.run(
                ["python", "checker/checker.py"],
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True,
                env=env
            )
        
        print("7. Checker completed")
        
        # Wait a moment for everything to settle
        time.sleep(1)
        
        print("8. Running validation...")
        check_result = subprocess.run(
            ["python", "check.py"],
            capture_output=True,
            text=True
        )
        
        print("\n" + "=" * 60)
        print("TEST RESULTS")
        print("=" * 60)
        print(check_result.stdout)
        if check_result.stderr:
            print("STDERR:")
            print(check_result.stderr)
        
        success = check_result.returncode == 0
        print(f"\n{'SUCCESS' if success else 'FAILED'}")
        return success
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return False
    except Exception as e:
        print(f"Test runner error: {e}")
        return False
    finally:
        print("\n9. Cleaning up processes...")
        cleanup_processes(server_proc, client_proc)
        print("Cleanup complete")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)