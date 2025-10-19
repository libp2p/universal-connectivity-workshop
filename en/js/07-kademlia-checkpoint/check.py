#!/usr/bin/env python3
import os
import re
import sys

def validate_peer_id(peer_id_str):
    """Validate that the peer ID string is a valid libp2p PeerId format"""
    if not peer_id_str.startswith("12D3KooW"):
        return False, f"Invalid peer ID format. Expected to start with '12D3KooW', got: {peer_id_str}"

    if len(peer_id_str) < 45 or len(peer_id_str) > 60:
        return False, f"Peer ID length seems invalid. Expected 45-60 chars, got {len(peer_id_str)}: {peer_id_str}"

    valid_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    for char in peer_id_str:
        if char not in valid_chars:
            return False, f"Invalid character '{char}' in peer ID. Must be base58 encoded."

    return True, f"{peer_id_str}"

def validate_multiaddr(addr_str):
    """Validate that the address string looks like a valid multiaddr"""
    if not (addr_str.startswith("/ip4/") or addr_str.startswith("/ip6/")):
        return False, f"Invalid multiaddr format: {addr_str}"

    if "/tcp" not in addr_str:
        return False, f"Missing TCP transport in multiaddr: {addr_str}"

    if "/p2p/" not in addr_str:
        return False, f"Missing peer ID in multiaddr: {addr_str}"

    return True, f"{addr_str}"

def check_output():
    """Check the output log for expected Kademlia DHT functionality"""
    log_file = "stdout.log"
    
    if not os.path.exists(log_file):
        print("X No stdout.log found from Docker container")
        return False

    try:
        with open(log_file, "r") as f:
            output = f.read()
        
        print("i Found stdout.log from Docker container")
        print("i Checking Kademlia DHT functionality...")

        if not output.strip():
            print("X Log file is empty - application may have failed to start")
            return False

        # Check for multi-node startup (Bootstrap, Provider, Consumer)
        bootstrap_pattern = r"\[BOOTSTRAP\] Started with Peer ID:\s*(12D3KooW[A-Za-z0-9]+)"
        provider_pattern = r"\[PROVIDER\] Started with Peer ID:\s*(12D3KooW[A-Za-z0-9]+)"
        consumer_pattern = r"\[CONSUMER\] Started with Peer ID:\s*(12D3KooW[A-Za-z0-9]+)"
        
        bootstrap_match = re.search(bootstrap_pattern, output)
        provider_match = re.search(provider_pattern, output)
        consumer_match = re.search(consumer_pattern, output)
        
        if not bootstrap_match:
            print("X Bootstrap node not detected")
            print("i Expected: '[BOOTSTRAP] Started with Peer ID: <peer_id>'")
            return False
        
        if not provider_match:
            print("X Provider node not detected")
            print("i Expected: '[PROVIDER] Started with Peer ID: <peer_id>'")
            return False
        
        if not consumer_match:
            print("X Consumer node not detected")
            print("i Expected: '[CONSUMER] Started with Peer ID: <peer_id>'")
            return False

        # Validate all three peer IDs
        bootstrap_peer = bootstrap_match.group(1)
        provider_peer = provider_match.group(1)
        consumer_peer = consumer_match.group(1)
        
        for node_name, peer_id in [("BOOTSTRAP", bootstrap_peer), ("PROVIDER", provider_peer), ("CONSUMER", consumer_peer)]:
            valid, message = validate_peer_id(peer_id)
            if not valid:
                print(f"X {node_name} {message}")
                return False
        
        print(f"+ BOOTSTRAP node started with Peer ID: {bootstrap_peer}")
        print(f"+ PROVIDER node started with Peer ID: {provider_peer}")
        print(f"+ CONSUMER node started with Peer ID: {consumer_peer}")
        print("+ Multi-node DHT network detected: 3 nodes")

        # Check for DHT mode configuration
        server_mode_pattern = r"\[(BOOTSTRAP|PROVIDER)\] DHT Mode: Server"
        server_mode_matches = re.findall(server_mode_pattern, output)
        
        if len(server_mode_matches) < 2:
            print("X Insufficient server mode DHT nodes detected")
            print("i Expected: BOOTSTRAP and PROVIDER in server mode")
            return False
        
        client_mode_pattern = r"\[CONSUMER\] DHT Mode: Client"
        if not re.search(client_mode_pattern, output):
            print("X Consumer node not in client mode")
            print("i Expected: '[CONSUMER] DHT Mode: Client'")
            return False
        
        print("+ DHT modes correctly configured: 2 server nodes, 1 client node")

        # Check for listening addresses from all nodes
        listening_pattern = r"\[(BOOTSTRAP|PROVIDER|CONSUMER)\] Listening on:\s*([/\w\.:-]+)"
        listening_matches = re.findall(listening_pattern, output)
        
        if len(listening_matches) < 6:
            print("X Insufficient listening addresses detected")
            print(f"i Expected: At least 6 addresses (2 per node), Found: {len(listening_matches)}")
            return False
        
        # Validate multiaddresses
        for node, addr in listening_matches[:6]:
            valid, addr_message = validate_multiaddr(addr)
            if not valid:
                print(f"X {addr_message}")
                return False
        
        print(f"+ All nodes listening: {len(listening_matches)} address(es) total")

        # Check for network formation (connections)
        provider_connection = r"\[PROVIDER\] Successfully connected to bootstrap node"
        consumer_connection = r"\[CONSUMER\] Successfully connected to bootstrap node"
        
        if not re.search(provider_connection, output):
            print("X Provider connection to bootstrap not detected")
            return False
        
        if not re.search(consumer_connection, output):
            print("X Consumer connection to bootstrap not detected")
            return False
        
        print("+ Network formation successful: All nodes connected to bootstrap")

        # Check for Peer Routing demonstration
        peer_routing_patterns = [
            r"\[CONSUMER\] Attempting to find provider peer",
            r"(\+ Peer routing|Successfully found peer via DHT)"
        ]
        
        peer_routing_success = True
        for pattern in peer_routing_patterns:
            if not re.search(pattern, output):
                peer_routing_success = False
                break
        
        if peer_routing_success:
            print("+ Peer routing demonstrated: Consumer successfully queried DHT for peer")
        else:
            print("X Peer routing demonstration incomplete")
            return False

        # Check for Content Routing demonstration
        content_routing_patterns = [
            r"\[PROVIDER\].*Announcing as content provider to DHT",
            r"\[PROVIDER\].*Successfully announced content availability",
            r"\[CONSUMER\].*Searching for content providers",
            r"(\+ Content routing|Content provider record stored)"
        ]
        
        content_routing_success = True
        for pattern in content_routing_patterns:
            if not re.search(pattern, output):
                content_routing_success = False
                break
        
        if content_routing_success:
            print("+ Content routing demonstrated: Provider announced, Consumer searched")
        else:
            print("X Content routing demonstration incomplete")
            return False

        # Check for CID handling
        cid_pattern = r"Content CID:\s*([a-zA-Z0-9]+)"
        cid_match = re.search(cid_pattern, output)
        
        if cid_match:
            print(f"+ Content ID (CID) created and used: {cid_match.group(1)}")
        else:
            print("X No valid Content ID (CID) detected")
            return False

        # Check for Distributed Value Storage (DHT Put/Get)
        value_storage_patterns = [
            r"\[PROVIDER\].*Storing value in DHT",
            r"\[PROVIDER\].*Successfully stored value in distributed hash table",
            r"\+ DHT PUT operation",
            r"\[CONSUMER\].*Retrieving value from DHT",
            r"(\+ DHT GET operation|Retrieved value from distributed storage|Distributed value storage mechanism demonstrated)"
        ]
        
        value_storage_success = True
        for pattern in value_storage_patterns:
            if not re.search(pattern, output):
                value_storage_success = False
                break
        
        if value_storage_success:
            print("+ Distributed value storage demonstrated: PUT and GET operations")
        else:
            print("X Distributed value storage demonstration incomplete")
            return False

        # Check for routing table inspection
        routing_table_pattern = r"\[(BOOTSTRAP|PROVIDER|CONSUMER)\] Known peers in routing table: \d+"
        routing_table_matches = re.findall(routing_table_pattern, output)
        
        if len(routing_table_matches) >= 3:
            print("+ DHT routing tables inspected: Network topology verified")
        else:
            print("X Routing table inspection incomplete")
            return False

        # Check for successful completion summary
        summary_patterns = [
            r"KADEMLIA DHT DEMONSTRATION SUMMARY",
            r"✓ BOOTSTRAP: Server mode DHT node",
            r"✓ PROVIDER: Server mode DHT node",
            r"✓ CONSUMER: Client mode DHT node",
            r"✓ Peer Routing",
            r"✓ Content Routing",
            r"✓ Value Storage"
        ]
        
        summary_checks = sum(1 for pattern in summary_patterns if re.search(pattern, output))
        
        if summary_checks >= 5:
            print("+ Comprehensive DHT demonstration summary present")
        else:
            print("X Incomplete demonstration summary")
            return False

        return True

    except Exception as e:
        print(f"X Error reading stdout.log: {e}")
        return False

def main():
    """Main check function"""
    print("i Checking Lesson 7: Kademlia DHT")
    print("i " + "=" * 50)

    try:
        if not check_output():
            return False
        
        print("")
        print("")
        print("i " + "=" * 50)
        print("+ Kademlia DHT lesson completed successfully!")
        print("i You have successfully:")
        print("i - Configured Kademlia DHT service in libp2p nodes")
        print("i - Created multi-node DHT network (Bootstrap, Provider, Consumer)")
        print("i - Implemented peer routing for decentralized peer discovery")
        print("i - Implemented content routing for content provider discovery")
        print("i - Implemented distributed value storage (DHT Put/Get)")
        print("i - Demonstrated client vs server DHT modes")
        print("i - Built foundation for decentralized applications!")
        print("")
        print("")
        print("i 🎉 Congratulations! Checkpoint 4 completed successfully! You now have a foundational understanding of Kademlia DHT!")
        print("i Ready for the next lesson!")

        return True

    except Exception as e:
        print(f"X Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

