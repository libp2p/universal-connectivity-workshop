#!/usr/bin/env python3
import re, sys, os

output = open("stdout.log").read() if os.path.exists("stdout.log") else ""
checks = [
    (r"Local peer id:", "PeerId found"),
    (r"Listening on:", "TCP listening"),
    (r"Connected to remote peer", "Connection established"),
    (r"Ping:|ping", "Ping protocol active")
]

print("\n" + "="*50)
print("Checking Lesson 3: Ping Checkpoint")
print("="*50)

all_passed = True
for pattern, desc in checks:
    if re.search(pattern, output, re.IGNORECASE):
        print(f"v {desc}")
    else:
        print(f"x {desc} - not found")
        all_passed = False

if all_passed:
    print("\nv Lesson 3 completed! 🎉\n")
    sys.exit(0)
else:
    print("\nx Some checks failed\n")
    sys.exit(1)
