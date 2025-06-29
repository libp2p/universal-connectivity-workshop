import sys
import re

SUCCESS = '\u2705'  # ✅
FAILURE = '\u274C'  # ❌

output = sys.stdin.read()

# Look for a successful ping output
ping_match = re.search(r'pinged .+ in (\\d+)ms', output)

if ping_match:
    print(SUCCESS)
    sys.exit(0)
else:
    print(FAILURE)
    print('Output must include a successful ping with latency, e.g., "pinged ... in 3ms"')
    sys.exit(1)
