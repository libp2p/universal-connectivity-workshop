#!/usr/bin/env python3
"""
Dependencies checker for js-libp2p Universal Connectivity Workshop
Checks that all required tools (Node.js, npm, Docker) are available.
"""

import sys
import subprocess
import re
import shutil
import os

def get_version(command):
    """Get version string from command output"""
    try:
        # Try --version
        result = subprocess.run([command, "--version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout.strip()
        
        # Try -v
        result = subprocess.run([command, "-v"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout.strip()
            
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

def check_node():
    """Check Node.js version >= 18"""
    version_str = get_version("node")
    if not version_str:
        print("! Node.js is not installed")
        return False
    
    # Extract major version (handles v18.x.x or 18.x.x)
    match = re.search(r'v?(\d+)\.', version_str)
    if match:
        major = int(match.group(1))
        if major >= 18:
            print(f"✅ Node.js {version_str} is installed")
            return True
    
    print(f"! Node.js 18+ is required. Current version: {version_str}")
    return False

def check_npm():
    """Check npm version >= 9"""
    version_str = get_version("npm")
    if not version_str:
        print("⚠️ npm is not installed")
        return False
        
    match = re.search(r'(\d+)\.', version_str)
    if match:
        major = int(match.group(1))
        if major >= 9:
            print(f"✅ npm {version_str} is installed")
            return True
            
    print(f"⚠️ npm 9+ is required. Current version: {version_str}")
    return False

def check_docker():
    """Check if Docker is available and running"""
    if shutil.which("docker"):
        try:
            # Check if we can contact the daemon
            subprocess.run(["docker", "info"], 
                         capture_output=True, check=True)
            print("✅ Docker is installed and running")
            return True
        except subprocess.CalledProcessError:
            print("⚠️ Docker is installed but not running (or no permission)")
            print("  Please start Docker Desktop or the docker daemon.")
            return False
    else:
        print("⚠️ Docker is not installed")
        return False

def check_git():
    """Check if git is available"""
    if get_version("git"):
        print("✅ Git is installed")
        return True
    print("⚠️ Git is not installed (recommended)")
    return False # Not strictly fatal but highly recommended

def main():
    print("Checking dependencies for js-libp2p Universal Connectivity Workshop...")
    print("="*70)
    
    checks = [
        ("Node.js", check_node),
        ("npm", check_npm),
        ("Docker", check_docker),
        ("Git", check_git)
    ]
    
    all_passed = True
    for name, check in checks:
        if not check():
            if name != "Git": # Git is optional-ish
                all_passed = False
            
    print("="*70)
    if all_passed:
        print("✅ All system dependencies are met!")
        print("You're ready to proceed with the workshop setup.")
    else:
        print("⚠️ Some dependencies are missing or outdated.")
        print("Please install/update the missing tools before starting.")
        sys.exit(1)

if __name__ == "__main__":
    main()
