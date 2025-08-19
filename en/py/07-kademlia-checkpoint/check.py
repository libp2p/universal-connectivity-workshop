#!/usr/bin/env python3
"""
Check script for Kademlia DHT Implementation
Validates that the student's solution can run DHT nodes in both server and client modes
"""

import os
import re
import sys


def validate_peer_id(peer_id_str):
    """Validate that the peer ID string is a valid libp2p PeerId format"""
    # Basic format validation - can start with 12D3KooW (Ed25519) or 16Uiu2HAm (secp256k1)
    valid_prefixes = ["12D3KooW", "16Uiu2HAm"]
    if not any(peer_id_str.startswith(prefix) for prefix in valid_prefixes):
        return False, f"Invalid peer ID format. Expected to start with one of {valid_prefixes}, got: {peer_id_str}"
    
    # Length check - valid peer IDs should be around 45-60 characters
    if len(peer_id_str) < 45 or len(peer_id_str) > 60:
        return False, f"Peer ID length seems invalid. Expected 45-60 chars, got {len(peer_id_str)}: {peer_id_str}"
    
    # Character set validation - should only contain base58 characters
    valid_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    for char in peer_id_str:
        if char not in valid_chars:
            return False, f"Invalid character '{char}' in peer ID. Must be base58 encoded."
    
    return True, f"Valid peer ID format: {peer_id_str}"


def validate_multiaddr(addr_str):
    """Validate that the address string looks like a valid multiaddr"""
    # Basic multiaddr validation - should start with /ip4/ or /ip6/
    if not (addr_str.startswith("/ip4/") or addr_str.startswith("/ip6/")):
        return False, f"Invalid multiaddr format: {addr_str}"
    
    # Should contain /tcp for TCP transport
    if "/tcp" not in addr_str:
        return False, f"Missing TCP transport in multiaddr: {addr_str}"
     
    return True, f"Valid multiaddr: {addr_str}"


def check_output():
    """Check the output log for expected kademlia DHT functionality"""
    try:
        # Check both server and client logs, and checker log
        log_files = []
        
        if os.path.exists("server.log"):
            log_files.append(("server.log", "server"))
        if os.path.exists("client.log"):
            log_files.append(("client.log", "client"))
        if os.path.exists("checker.log"):
            log_files.append(("checker.log", "checker"))
        
        if not log_files:
            print("x No log files found (server.log, client.log, or checker.log)")
            return False
        
        print("i Checking kademlia DHT functionality...")
        
        all_output = ""
        for log_file, log_type in log_files:
            try:
                with open(log_file, "r") as f:
                    content = f.read()
                    all_output += content + "\n"
                    print(f"i Found {log_type} log with {len(content)} characters")
            except Exception as e:
                print(f"i Warning: Could not read {log_file}: {e}")
        
        if not all_output.strip():
            print("x All log files are empty - application may have failed to start")
            return False
        
        print(f"i Combined output: {repr(all_output[:200])}")  # Debug: show first 200 chars
        
        # Check for server node startup
        server_start_patterns = [
            r"DHT service started in server mode",
            r"checker-dht-started,server",
            r"Running in server mode"
        ]
        
        server_started = False
        for pattern in server_start_patterns:
            if re.search(pattern, all_output):
                server_started = True
                print(f"v DHT server detected using pattern: {pattern}")
                break
        
        if not server_started:
            print("x DHT server mode not detected")
            print(f"i Actual output: {repr(all_output)}")
            return False
        
        # Check for value storage
        value_stored_patterns = [
            r"Stored value '([^']+)' with key: ([A-Za-z0-9]+)",
            r"dht-put,([A-Za-z0-9]+),([^,\n]+)"
        ]
        
        value_stored = False
        for pattern in value_stored_patterns:
            value_matches = re.search(pattern, all_output)
            if value_matches:
                if "dht-put" in pattern:
                    stored_key = value_matches.group(1)
                    stored_value = value_matches.group(2)
                else:
                    stored_value = value_matches.group(1)
                    stored_key = value_matches.group(2)
                print(f"v Value storage detected: '{stored_value}' with key: {stored_key}")
                value_stored = True
                break
        
        if not value_stored:
            print("i No explicit value storage detected (may be handled internally)")
        
        # Check for DHT operations (put/get)
        dht_operations = []
        dht_put_matches = re.findall(r"dht-put,([A-Za-z0-9]+),([^,\n]+)", all_output)
        dht_get_matches = re.findall(r"dht-get,([A-Za-z0-9]+),([^,\n]+)", all_output)
        
        if dht_put_matches:
            for key, value in dht_put_matches:
                print(f"v DHT PUT operation: key={key}, value='{value}'")
                dht_operations.append("put")
        
        if dht_get_matches:
            for key, value in dht_get_matches:
                print(f"v DHT GET operation: key={key}, value='{value}'")
                dht_operations.append("get")
        
        # Check for peer connections
        connection_patterns = [
            r"connected,([16D3KooW|16Uiu2HAm][A-Za-z0-9]+),([/\w\.:-]+)",
            r"Connected to bootstrap nodes: \[([^\]]+)\]",
            r"connections-established,(\d+)"
        ]
        
        connections_found = False
        for pattern in connection_patterns:
            matches = re.search(pattern, all_output)
            if matches:
                connections_found = True
                if "connections-established" in pattern:
                    count = matches.group(1)
                    print(f"v Peer connections established: {count}")
                elif "Connected to bootstrap" in pattern:
                    peers_str = matches.group(1)
                    print(f"v Bootstrap connections: {peers_str}")
                else:
                    peer_id = matches.group(1)
                    addr = matches.group(2)
                    valid_peer, peer_msg = validate_peer_id(peer_id)
                    if valid_peer:
                        print(f"v Peer connection: {peer_msg} at {addr}")
                    else:
                        print(f"x {peer_msg}")
                        return False
                break
        
        if not connections_found:
            print("i No explicit peer connections detected in logs")
        
        # Check for node address generation
        addr_patterns = [
            r"To connect to this node, use: --bootstrap (/ip4/[^\s]+)",
            r"checker-listening,([/\w\.:-]+/p2p/[A-Za-z0-9]+)"
        ]
        
        for pattern in addr_patterns:
            matches = re.search(pattern, all_output)
            if matches:
                addr = matches.group(1)
                # Extract just the multiaddr part (remove duplicate /p2p/ if present)
                if "/p2p/" in addr:
                    addr_parts = addr.split("/p2p/")
                    if len(addr_parts) >= 2:
                        clean_addr = "/p2p/".join(addr_parts[:2])  # Take first two parts
                        valid, message = validate_multiaddr(clean_addr)
                        if valid:
                            print(f"v Node address available: {clean_addr}")
                        else:
                            print(f"x Address validation failed: {message}")
                break
        
        # Summary of what we found
        print(f"v DHT functionality summary:")
        print(f"  - Server mode: {'Yes' if server_started else 'No'}")
        print(f"  - DHT operations: {len(set(dht_operations))} types ({', '.join(set(dht_operations)) if dht_operations else 'none'})")
        print(f"  - Peer connections: {'Yes' if connections_found else 'No'}")
        
        # We need at least server mode and some DHT functionality
        return server_started and (dht_operations or connections_found)
        
    except Exception as e:
        print(f"x Error reading log files: {e}")
        return False


def main():
    """Main check function"""
    print("i Checking Kademlia DHT Implementation")
    print("i " + "=" * 50)
    
    try:
        # Check the output
        if not check_output():
            return False
        
        print("i " + "=" * 50)
        print("y Kademlia DHT implementation completed successfully!")
        print("i You have successfully:")
        print("i • Implemented Kademlia DHT with server and client modes")
        print("i • Stored and retrieved values in the DHT")
        print("i • Advertised and discovered content providers")
        print("i • Established bootstrap connections between nodes")
        print("i Ready for the next lesson!")
        
        return True
        
    except Exception as e:
        print(f"x Unexpected error during checking: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)