#!/usr/bin/env python3
import os
import re
import sys

def validate_peer_id(peer_id_str):
    """Validate that the peer ID string is a valid libp2p PeerId format"""
    # Basic format validation - should start with 12D3KooW (Ed25519 peer IDs)
    if not peer_id_str.startswith("12D3KooW"):
        return False, f"Invalid peer ID format. Expected to start with '12D3KooW', got: {peer_id_str}"

    # Length check - valid peer IDs should be around 45-60 characters
    if len(peer_id_str) < 45 or len(peer_id_str) > 60:
        return False, f"Peer ID length seems invalid. Expected 45-60 chars, got {len(peer_id_str)}: {peer_id_str}"

    # Character set validation - should only contain base58 characters
    valid_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    for char in peer_id_str:
        if char not in valid_chars:
            return False, f"Invalid character '{char}' in peer ID. Must be base58 encoded."

    return True, f"{peer_id_str}"

def validate_multiaddr(addr_str):
    """Validate that the address string looks like a valid multiaddr"""
    # Basic multiaddr validation - should start with /ip4/ or /ip6/
    if not (addr_str.startswith("/ip4/") or addr_str.startswith("/ip6/")):
        return False, f"Invalid multiaddr format: {addr_str}"

    # Should contain /tcp for TCP transport
    if "/tcp" not in addr_str:
        return False, f"Missing TCP transport in multiaddr: {addr_str}"

    # Should contain /p2p for peer ID
    if "/p2p/" not in addr_str:
        return False, f"Missing peer ID in multiaddr: {addr_str}"

    return True, f"{addr_str}"

def check_output():
    """Check the output log for expected gossipsub functionality"""
    # Workshop tool runs Docker Compose which creates stdout.log
    log_file = "stdout.log"
    
    if not os.path.exists(log_file):
        print("X No stdout.log found from Docker container")
        return False

    try:
        with open(log_file, "r") as f:
            output = f.read()
        
        print("i Found stdout.log from Docker container")

        print("i Checking gossipsub pub/sub functionality...")

        if not output.strip():
            print("X Log files are empty - application may have failed to start")
            return False

        # Check for coordinated multi-node startup with Peer IDs
        startup_pattern = r"\[NODE[12]\] Started with Peer ID:\s*(12D3KooW[A-Za-z0-9]+)"
        startup_matches = re.findall(startup_pattern, output)
        if len(startup_matches) < 2:
            print("X Insufficient nodes detected - expected both NODE1 and NODE2 startup")
            print(f"i Expected: '[NODE1] Started with Peer ID: <peer_id>' and '[NODE2] Started with Peer ID: <peer_id>'")
            print(f"i Actual output: {repr(output[:500])}")
            return False

        # Validate both peer IDs
        for i, peer_id in enumerate(startup_matches[:2]):
            valid, peer_id_message = validate_peer_id(peer_id)
            if not valid:
                print(f"X NODE{i+1} {peer_id_message}")
                return False

        print(f"+ NODE1 started with Peer ID: {startup_matches[0]}")
        print(f"+ NODE2 started with Peer ID: {startup_matches[1]}")
        print(f"+ Multi-node coordinated startup detected: {len(startup_matches)} nodes")

        # Check for coordinated listening addresses from both nodes
        listening_pattern = r"\[NODE[12]\] Listening on:\s*([/\w\.:-]+)"
        listening_matches = re.findall(listening_pattern, output)
        if len(listening_matches) < 4:  # Expect at least 2 addresses per node (2 nodes)
            print("X Insufficient listening addresses detected from coordinated nodes")
            print(f"i Expected: Multiple '[NODE1] Listening on: <multiaddr>' and '[NODE2] Listening on: <multiaddr>'")
            print(f"i Found: {len(listening_matches)} addresses")
            return False

        # Validate multiaddresses
        for addr in listening_matches[:4]:  # Check first 4 addresses
            valid, addr_message = validate_multiaddr(addr)
            if not valid:
                print(f"X {addr_message}")
                return False

        print(f"+ Both nodes listening on {len(listening_matches)} address(es) total")

        # Check for coordinated topic subscription from both nodes
        subscription_pattern = r"\[NODE[12]\] Subscribed to topic:\s*(universal-connectivity|gossipsub-chat)"
        subscription_matches = re.findall(subscription_pattern, output)
        if len(subscription_matches) < 2:
            print("X Insufficient topic subscriptions detected - expected both NODE1 and NODE2")
            print(f"i Expected: '[NODE1] Subscribed to topic: <topic>' and '[NODE2] Subscribed to topic: <topic>'")
            print(f"i Found: {len(subscription_matches)} subscription(s)")
            return False

        print(f"+ Both nodes subscribed to topic: {subscription_matches[0]} ({len(subscription_matches)} subscriptions total)")

        # Check for coordinated peer connection
        connection_pattern = r"\[NODE2\] Successfully connected to NODE1"
        connection_matches = re.search(connection_pattern, output)
        
        if not connection_matches:
            print("X No coordinated peer connection detected")
            print("i Expected: '[NODE2] Successfully connected to NODE1'")
            return False
        
        print("+ Successfully established peer-to-peer connection between nodes")
        
        # Check for coordinated message publishing from both nodes
        publish_pattern = r"\[NODE[12]\] (Response )?[Mm]essage published successfully"
        publish_matches = re.findall(publish_pattern, output)
        
        if len(publish_matches) < 2:
            print("X Insufficient coordinated message publishing detected")
            print(f"i Expected: Both NODE1 and NODE2 to publish messages, Found: {len(publish_matches)}")
            return False
        
        print(f"+ Coordinated message publishing detected: {len(publish_matches)} successful publications")
        
        # Check for cross-peer message reception (REQUIRED)
        received_pattern = r"\[NODE[12]\] Received message from (12D3KooW[A-Za-z0-9]+)"
        received_matches = re.findall(received_pattern, output)
        
        if len(received_matches) < 2:
            print("X Insufficient cross-peer message reception detected")
            print("i Expected: Both nodes to receive messages from each other")
            print(f"i Found: {len(received_matches)} message reception(s)")
            return False
        
        print(f"+ Cross-peer message exchange confirmed: {len(received_matches)} message(s) received between nodes")
        
        # Check for GossipSub mesh formation verification
        mesh_pattern = r"\[NODE[12]\] Sees \d+ peer\(s\) subscribed to topic"
        mesh_matches = re.findall(mesh_pattern, output)
        
        if len(mesh_matches) < 2:
            print("X Insufficient mesh formation verification detected")
            return False
        
        print("+ GossipSub mesh formation verified from both node perspectives")

        return True

    except Exception as e:
        print(f"X Error reading checker.log: {e}")
        return False

def main():
    """Main check function"""
    print("i Checking Lesson 6: GossipSub Pub/Sub")
    print("i " + "=" * 50)

    try:
        # Check the output
        if not check_output():
            return False

        print("i " + "=" * 50)
        print("+ GossipSub pub/sub lesson completed successfully!")
        print("i You have successfully:")
        print("i - Configured GossipSub service in your libp2p node")
        print("i - Started a node with proper Peer ID and listening addresses")
        print("i - Subscribed to a pub/sub topic")
        print("i - Implemented message publishing functionality")
        print("i - Built a foundation for decentralized messaging")
        print("i Ready for Lesson 7: Advanced libp2p features!")

        return True

    except Exception as e:
        print(f"X Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 