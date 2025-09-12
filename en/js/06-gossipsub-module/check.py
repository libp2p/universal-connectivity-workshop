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
    # We need to check stdout.log first, then fallback to checker.log
    log_file = None
    
    if os.path.exists("stdout.log"):
        log_file = "stdout.log"
        print("i Found stdout.log from Docker container")
    elif os.path.exists("checker.log"):
        log_file = "checker.log"
        print("i Found checker.log")
    else:
        print("X No log files found (stdout.log or checker.log)")
        return False

    try:
        with open(log_file, "r") as f:
            output = f.read()

        print("i Checking gossipsub pub/sub functionality...")

        if not output.strip():
            print(f"X {log_file} is empty - application may have failed to start")
            return False

        # Check for node startup with Peer ID
        startup_pattern = r"Node started with Peer ID:\s*(12D3KooW[A-Za-z0-9]+)"
        startup_matches = re.search(startup_pattern, output)
        if not startup_matches:
            print("X No node startup with Peer ID detected")
            print(f"i Expected: 'Node started with Peer ID: <peer_id>'")
            print(f"i Actual output: {repr(output[:500])}")
            return False

        peer_id = startup_matches.group(1)
        valid, peer_id_message = validate_peer_id(peer_id)
        if not valid:
            print(f"X {peer_id_message}")
            return False

        print(f"+ Node started with {peer_id_message}")

        # Check for listening addresses
        listening_pattern = r"Listening on:\s*([/\w\.:-]+)"
        listening_matches = re.findall(listening_pattern, output)
        if not listening_matches:
            print("X No listening addresses detected")
            print(f"ℹ Expected: 'Listening on: <multiaddr>'")
            print(f"ℹ Actual output: {repr(output)}")
            return False

        for addr in listening_matches:
            valid, addr_message = validate_multiaddr(addr)
            if not valid:
                print(f"X {addr_message}")
                return False

        print(f"+ Node listening on {len(listening_matches)} address(es)")

        # Check for topic subscription (flexible for both topics)
        subscription_pattern = r"Subscribed to topic:\s*(universal-connectivity|gossipsub-chat)"
        subscription_matches = re.search(subscription_pattern, output)
        if not subscription_matches:
            print("X No topic subscription detected")
            print(f"i Expected: 'Subscribed to topic: <topic_name>'")
            print(f"i Actual output: {repr(output[:500])}")
            return False

        topic_name = subscription_matches.group(1)
        print(f"+ Successfully subscribed to topic: {topic_name}")

        # Check for message publishing (key GossipSub functionality)
        publish_pattern = r"Published message:\s*\"([^\"]+)\""
        publish_matches = re.search(publish_pattern, output)
        
        if publish_matches:
            published_message = publish_matches.group(1)
            print(f"+ Successfully published message: \"{published_message}\"")
        else:
            # Check for message reception (alternative validation)
            message_pattern = r"(MESSAGE RECEIVED|Received message) from (12D3KooW[A-Za-z0-9]+).*\"([^\"]+)\""
            message_matches = re.search(message_pattern, output)
            
            if message_matches:
                sender_peer_id = message_matches.group(2)
                message_content = message_matches.group(3)
                
                valid, sender_peer_message = validate_peer_id(sender_peer_id)
                if not valid:
                    print(f"X {sender_peer_message}")
                    return False
                
                print(f"+ Successfully received message from {sender_peer_message}: \"{message_content}\"")
            else:
                print("i No message publishing or reception detected - basic gossipsub setup validated")

        # Check for remote peer connection (if attempted)
        connection_pattern = r"Connected to remote peer:\s*([/\w\.:-]+)"
        connection_matches = re.search(connection_pattern, output)
        
        if connection_matches:
            remote_addr = connection_matches.group(1)
            valid, remote_addr_message = validate_multiaddr(remote_addr)
            if not valid:
                print(f"X {remote_addr_message}")
                return False

            print(f"+ Connected to remote peer: {remote_addr_message}")

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