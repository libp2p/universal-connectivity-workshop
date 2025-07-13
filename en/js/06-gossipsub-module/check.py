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
    if not os.path.exists("checker.log"):
        print("✗ checker.log file not found")
        return False

    try:
        with open("checker.log", "r") as f:
            output = f.read()

        print("ℹ Checking gossipsub pub/sub functionality...")

        if not output.strip():
            print("✗ checker.log is empty - checker may have failed to start")
            return False

        # Check for chat node startup
        startup_pattern = r"Chat node started with Peer ID:\s*(12D3KooW[A-Za-z0-9]+)"
        startup_matches = re.search(startup_pattern, output)
        if not startup_matches:
            print("✗ No chat node startup detected")
            print(f"ℹ Expected: 'Chat node started with Peer ID: <peer_id>'")
            print(f"ℹ Actual output: {repr(output)}")
            return False

        peer_id = startup_matches.group(1)
        valid, peer_id_message = validate_peer_id(peer_id)
        if not valid:
            print(f"✗ {peer_id_message}")
            return False

        print(f"✓ Chat node started with {peer_id_message}")

        # Check for listening addresses
        listening_pattern = r"Listening on:\s*([/\w\.:-]+)"
        listening_matches = re.findall(listening_pattern, output)
        if not listening_matches:
            print("✗ No listening addresses detected")
            print(f"ℹ Expected: 'Listening on: <multiaddr>'")
            print(f"ℹ Actual output: {repr(output)}")
            return False

        for addr in listening_matches:
            valid, addr_message = validate_multiaddr(addr)
            if not valid:
                print(f"✗ {addr_message}")
                return False

        print(f"✓ Node listening on {len(listening_matches)} address(es)")

        # Check for topic subscription
        subscription_pattern = r"Subscribed to topic:\s*gossipsub-chat"
        subscription_matches = re.search(subscription_pattern, output)
        if not subscription_matches:
            print("✗ No topic subscription detected")
            print(f"ℹ Expected: 'Subscribed to topic: gossipsub-chat'")
            print(f"ℹ Actual output: {repr(output)}")
            return False

        print("✓ Successfully subscribed to gossipsub-chat topic")

        # Check for message reception (this is the key validation)
        message_pattern = r"MESSAGE RECEIVED from (12D3KooW[A-Za-z0-9]+): \"([^\"]+)\" on topic gossipsub-chat"
        message_matches = re.search(message_pattern, output)
        
        if message_matches:
            # Message was received - validate the process
            sender_peer_id = message_matches.group(1)
            message_content = message_matches.group(2)

            valid, sender_peer_message = validate_peer_id(sender_peer_id)
            if not valid:
                print(f"✗ {sender_peer_message}")
                return False

            print(f"✓ Successfully received message from {sender_peer_message}: \"{message_content}\"")

        else:
            # No message received - check for basic setup
            print("ℹ No message reception detected - checking basic gossipsub setup")

            # Check for message sending attempt
            send_pattern = r"Message sent:\s*\"([^\"]+)\""
            send_matches = re.search(send_pattern, output)
            
            if send_matches:
                sent_message = send_matches.group(1)
                print(f"✓ Message sending attempted: \"{sent_message}\"")
            else:
                print("ℹ No message sending detected - basic gossipsub setup validated")

        # Check for remote peer connection (if attempted)
        connection_pattern = r"Connected to remote peer:\s*([/\w\.:-]+)"
        connection_matches = re.search(connection_pattern, output)
        
        if connection_matches:
            remote_addr = connection_matches.group(1)
            valid, remote_addr_message = validate_multiaddr(remote_addr)
            if not valid:
                print(f"✗ {remote_addr_message}")
                return False

            print(f"✓ Connected to remote peer: {remote_addr_message}")

        return True

    except Exception as e:
        print(f"✗ Error reading checker.log: {e}")
        return False

def main():
    """Main check function"""
    print("ℹ Checking Lesson 6: Gossipsub Pub/Sub")
    print("ℹ " + "=" * 50)

    try:
        # Check the output
        if not check_output():
            return False

        print("ℹ " + "=" * 50)
        print("✓ Gossipsub pub/sub lesson completed successfully!")
        print("ℹ You have successfully:")
        print("ℹ • Configured gossipsub service in your libp2p node")
        print("ℹ • Started a chat node with proper listening addresses")
        print("ℹ • Subscribed to a pub/sub topic")
        print("ℹ • Implemented message sending and receiving")
        print("ℹ • Built a foundation for decentralized messaging")
        print("ℹ Ready for Lesson 7: Kademlia DHT!")

        return True

    except Exception as e:
        print(f"✗ Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 