#!/usr/bin/env python3
"""Check script for Lesson 2: TCP Transport"""

import re
import sys
import os

def check_output():
    if not os.path.exists("stdout.log"):
        print("x stdout.log not found")
        return False

    with open("stdout.log", "r") as f:
        output = f.read()

    print("\ni Checking Lesson 2: TCP Transport")
    print("i " + "=" * 50)

    # Check for PeerId
    if not re.search(r"Local peer id: ([A-Za-z0-9]+)", output):
        print("x No PeerId found")
        return False
    print("v PeerId found")

    # Check for listening
    if "Listening on:" not in output:
        print("x Not listening on any address")
        return False
    print("v Listening on TCP")

    # Check for connection attempt if REMOTE_PEERS was set
    if os.getenv("REMOTE_PEERS"):
        if "Connecting to:" not in output:
            print("x Did not attempt to connect to remote peers")
            return False
        print("v Attempted to connect to remote peers")

        # Optional: check if connection succeeded
        if "Connected to remote peer" in output:
            print("v Successfully connected to remote peer")

    return True

def main():
    if check_output():
        print("\n" + "=" * 50)
        print("v Lesson 2 completed successfully! 🎉")
        print("=" * 50)
        print("\ni You've successfully added TCP transport!")
        print("i Next: Lesson 3 - Add security and protocols\n")
        return True
    else:
        print("\n" + "=" * 50)
        print("x Lesson 2 check failed")
        print("=" * 50 + "\n")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
