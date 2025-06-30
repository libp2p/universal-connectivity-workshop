import sys
import re

SUCCESS = '\u2705' 
FAILURE = '\u274C'  

output = sys.stdin.read()

multiaddr_match = re.search(r'Listening on:.*(/ip4/.+/tcp/\d+/p2p/[A-Za-z0-9]+)', output, re.DOTALL)

if multiaddr_match:
    print(SUCCESS)
    sys.exit(0)
else:
    print(FAILURE)
    sys.exit(1)
