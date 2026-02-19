# Lesson 7: Pubsub Peer Discovery

Use pubsub for peer discovery instead of Kademlia DHT.

## Learning Objectives
- Understand alternative discovery mechanisms
- Use pubsub for peer discovery
- Build peer topology dynamically

## Background
Kademlia DHT is not yet stable in dotnet-libp2p, so we use pubsub-based peer discovery as an alternative.

Pubsub peer discovery works by:
1. Announcing your presence on a rendezvous topic
2. Discovering other peers subscribed to the same topic
3. Connecting to discovered peers

## Your Task
- Subscribe to a discovery topic
- Announce your presence
- Discover and connect to peers

## Success Criteria
- Subscribe to discovery topic
- Discover peers via pubsub
- Build connected peer mesh

## Hints

### Hint: Complete Solution

See the code example in the lesson above for the complete working solution.

### Key Points
- Follow the step-by-step instructions
- Make sure all using statements are included
- Check error messages for debugging hints
- Ensure environment variables are set correctly
