import sys
import re

SUCCESS = '\u2705'  # ✅
FAILURE = '\u274C'  # ❌

output = sys.stdin.read()

peerid_match = re.search(r'PeerId: ([A-Za-z0-9]+)', output)
listening_match = re.search(r'Listening on:\n(.+)', output, re.DOTALL)

if peerid_match and listening_match and len(listening_match.group(1).strip().split('\n')) >= 1:
    print(SUCCESS)
    sys.exit(0)
else:
    print(FAILURE)
    sys.exit(1)
