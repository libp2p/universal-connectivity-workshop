#!/usr/bin/env python3
"""
Check script for Lesson 1: Identity and Basic Host
Validates that the student's solution creates a libp2p host with identity.
"""

import subprocess
import sys
import os
import re
import base58

def validate_peer_id(peer_id_str):
    """Validate that the peer ID string is a valid base58 format"""
    try:
        # Try to decode the peer ID as base58
        decoded = base58.b58decode(peer_id_str)
        
        # Should be 32 bytes (SHA256 hash length)
        if len(decoded) != 32:
            return False, f"Invalid peer ID length. Expected 32 bytes, got {len(decoded)}: {peer_id_str}"
        
        # Check if it's a valid base58 string (no invalid characters)
        re_encoded = base58.b58encode(decoded).decode('ascii')
        if re_encoded != peer_id_str:
            return False, f"Peer ID base58 encoding is inconsistent: {peer_id_str}"
        
        return True, f"Valid peer ID format: {peer_id_str}"
        
    except Exception as e:
        return False, f"Invalid peer ID format: {peer_id_str} - Error: {e}"

def check_output():
    """Check the output log for expected content"""
    if not os.path.exists("stdout.log"):
        print("❌ Error: stdout.log file not found")
        return False
    
    try:
        with open("stdout.log", "r") as f:
            output = f.read()
        
        print("ℹ️  Checking application output...")
        
        if not output.strip():
            print("❌ stdout.log is empty - application may have failed to start")
            return False
        
        # Check for startup message
        if "Starting Universal Connectivity Application" not in output:
            print("❌ Missing startup message. Expected: 'Starting Universal Connectivity Application...'")
            print(f"ℹ️  Actual output: {repr(output[:200])}")
            return False
        print("✅ Found startup message")
        
        # Check for peer ID output
        peer_id_pattern = r"Local peer id: ([A-Za-z0-9]+)"
        peer_id_match = re.search(peer_id_pattern, output)
        
        if not peer_id_match:
            print("❌ Missing peer ID output. Expected format: 'Local peer id: <base58_string>'")
            print(f"ℹ️  Actual output: {repr(output[:200])}")
            return False
        
        peer_id = peer_id_match.group(1)
        
        # Validate the peer ID format
        valid, message = validate_peer_id(peer_id)
        if not valid:
            print(f"❌ {message}")
            return False
        
        print(f"✅ {message}")
        
        # Check for host startup message
        if "Host started with PeerId:" not in output:
            print("❌ Missing host startup message. Expected: 'Host started with PeerId: ...'")
            print(f"ℹ️  Actual output: {repr(output[:200])}")
            return False
        print("✅ Found host startup message")
        
        # Check that the application doesn't crash immediately
        lines = output.strip().split('\n')
        if len(lines) < 3:
            print("❌ Application seems to have crashed immediately after startup")
            print(f"ℹ️  Output lines: {lines}")
            return False
        
        print("✅ Application started successfully and generated valid peer identity")
        return True
        
    except Exception as e:
        print(f"❌ Error reading stdout.log: {e}")
        return False

def check_code_structure():
    """Check if the code has the expected structure"""
    app_file = "app/main.py"
    
    if not os.path.exists(app_file):
        print("❌ Error: app/main.py file not found")
        return False
    
    try:
        with open(app_file, "r") as f:
            code = f.read()
        
        print("ℹ️  Checking code structure...")
        
        # Check for required imports
        required_imports = [
            "trio",
            "ed25519",
            "base58"
        ]
        
        for imp in required_imports:
            if imp not in code:
                print(f"❌ Missing import: {imp}")
                return False
        print("✅ Required imports found")
        
        # Check for LibP2PHost class
        if "class LibP2PHost" not in code:
            print("❌ Missing LibP2PHost class definition")
            return False
        print("✅ LibP2PHost class found")
        
        # Check for async main function
        if "async def main" not in code:
            print("❌ Missing async main function")
            return False
        print("✅ Async main function found")
        
        # Check for key generation
        if "Ed25519PrivateKey.generate()" not in code:
            print("❌ Missing Ed25519 key generation")
            return False
        print("✅ Ed25519 key generation found")
        
        # Check for PeerId creation
        if "base58.b58encode" not in code:
            print("❌ Missing PeerId base58 encoding")
            return False
        print("✅ PeerId creation found")
        
        print("✅ Code structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Error reading code file: {e}")
        return False

def main():
    """Main check function"""
    print("🔍 Checking Lesson 1: Identity and Basic Host")
    print("=" * 60)
    
    try:
        # Check code structure first
        if not check_code_structure():
            return False
        
        # Check the output
        if not check_output():
            return False
        
        print("=" * 60)
        print("🎉 All checks passed! Your libp2p host is working correctly.")
        print("✅ You have successfully:")
        print("   • Created a libp2p host with a stable Ed25519 identity")
        print("   • Generated and displayed a valid peer ID")
        print("   • Set up a basic async event loop")
        print("   • Implemented proper host lifecycle management")
        print("\n🚀 Ready for Lesson 2: Transport and Multiaddrs!")
        
        return True
        
    except Exception as e:
        print(f"💥 Unexpected error during checking: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)