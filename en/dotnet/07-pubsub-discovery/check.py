#!/usr/bin/env python3
import re, sys, os
output = open("stdout.log").read() if os.path.exists("stdout.log") else ""
checks = [
    (r"Local peer id:", "PeerId"),
    (r"peer discovery|discovery topic", "Discovery topic"),
    (r"Announced presence|announcement", "Presence announcement"),
]
all_passed = all(re.search(p, output, re.IGNORECASE) for p, _ in checks)
for p, desc in checks:
    print(f"{'v' if re.search(p, output, re.IGNORECASE) else 'x'} {desc}")
print(f"\n{'v Lesson 7 completed! 🎉 Workshop finished!' if all_passed else 'x Some checks failed'}\n")
sys.exit(0 if all_passed else 1)
