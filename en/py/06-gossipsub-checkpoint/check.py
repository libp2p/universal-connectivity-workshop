#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check script for Lesson 6: Gossipsub Checkpoint
Validates that the chat program can subscribe to topics and receive gossipsub messages.
"""

import sys
import io

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
import os
import re

def check_output():
    """Check the output log for expected gossipsub checkpoint functionality"""
    
    # 1. Check if the log file exists
    if not os.path.exists("checker.log"):
        print("! checker.log file not found.")
        print("i Please run your program and redirect its output to checker.log")
        print("i Example: python your_program.py [ARGS] > checker.log 2>&1")
        return False
    
    try:
        with open("checker.log", "r") as f:
            output = f.read()
        
        print("i Checking gossipsub checkpoint functionality...")
        
        # 2. Check if the log is empty
        if not output.strip():
            print("! checker.log is empty - application may have failed to start")
            return False

        # 3. Check if the host started
        # Looks for: "Host started, listening on: ..." (from logger.info)
        host_started_pattern = re.compile(r"Host started, listening on:")
        if not host_started_pattern.search(output):
            print("! Host start message not found.")
            print("i Make sure you are running with --verbose to capture info logs.")
            print(f"i Actual output (first 500 chars): {repr(output[:500])}...")
            return False
            
        print("v Host started successfully.")

        # 4. Check for Gossipsub subscription
        # Looks for: "Subscribed to topics: universal-connectivity, ..." (from logger.info)
        subscribe_pattern = re.compile(r"Subscribed to topics: .*universal-connectivity")
        if not subscribe_pattern.search(output):
            print("! Did not find subscription message for 'universal-connectivity'.")
            print("i Make sure you are running with --verbose to capture info logs.")
            return False

        print("v Subscribed to 'universal-connectivity' topic.")

        # 5. Check for a received chat message
        msg_pattern = re.compile(r"\[.+?\([A-Za-z0-9]{8,}\)\]: .+")
        msg_match = msg_pattern.search(output)
        
        if not msg_match:
            print("! No incoming chat message was found in the log.")
            print("i Make sure another peer connects and sends a message.")
            return False

        print(f"v Received Gossipsub message: {msg_match.group(0)}")

        return True
        
    except Exception as e:
        print(f"! Error reading checker.log: {e}")
        return False

def main():
    """Main check function"""
    print("i Checking Lesson 6: Gossipsub Checkpoint")
    print("i " + "=" * 50)
    
    try:
        if not check_output():
            print("i " + "=" * 50)
            print("! Check failed.")
            return False
        
        print("i " + "=" * 50)
        print("v Gossipsub checkpoint completed successfully!")
        print("i You have successfully:")
        print("i • Started the host with Gossipsub")
        print("i • Subscribed to the 'universal-connectivity' topic")
        print("i • Received and displayed a message from that topic")
        
        return True
        
    except Exception as e:
        print(f"! Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)