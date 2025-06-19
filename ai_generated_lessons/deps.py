#!/usr/bin/env python3
"""
Dependency checker for the Universal Connectivity Workshop (Rust)
Verifies that all required tools are properly installed.
"""

import subprocess
import sys
import os
import re
from typing import List, Tuple, Optional

def run_command(cmd: List[str]) -> Tuple[bool, str]:
    """Run a command and return (success, output)"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, ""

def check_rust_version() -> Tuple[bool, str]:
    """Check if Rust is installed with minimum version"""
    success, output = run_command(["rustc", "--version"])
    if not success:
        return False, "Rust compiler (rustc) not found"
    
    # Extract version number
    version_match = re.search(r'rustc (\d+)\.(\d+)\.(\d+)', output)
    if not version_match:
        return False, "Could not parse Rust version"
    
    major, minor, patch = map(int, version_match.groups())
    
    # Require Rust 1.70 or later for full libp2p compatibility
    if (major, minor) < (1, 70):
        return False, f"Rust version {major}.{minor}.{patch} is too old. Please upgrade to 1.70 or later."
    
    return True, f"Rust {major}.{minor}.{patch}"

def check_cargo() -> Tuple[bool, str]:
    """Check if Cargo is available"""
    success, output = run_command(["cargo", "--version"])
    if not success:
        return False, "Cargo package manager not found"
    return True, f"Cargo available"

def check_docker() -> Tuple[bool, str]:
    """Check if Docker is installed and running"""
    success, output = run_command(["docker", "--version"])
    if not success:
        return False, "Docker not found"
    
    # Check if Docker daemon is running
    success, _ = run_command(["docker", "info"])
    if not success:
        return False, "Docker is installed but not running. Please start Docker Desktop."
    
    return True, "Docker running"

def check_docker_compose() -> Tuple[bool, str]:
    """Check if Docker Compose is available"""
    # Try docker-compose command first
    success, output = run_command(["docker-compose", "--version"])
    if success:
        return True, "Docker Compose available"
    
    # Try docker compose subcommand (newer Docker versions)
    success, output = run_command(["docker", "compose", "version"])
    if success:
        return True, "Docker Compose (via docker compose) available"
    
    return False, "Docker Compose not found"

def check_build_tools() -> Tuple[bool, str]:
    """Check platform-specific build tools"""
    if os.name == 'nt':  # Windows
        # Check for Visual Studio Build Tools
        success, _ = run_command(["where", "cl"])
        if success:
            return True, "Visual Studio Build Tools available"
        else:
            return False, "Visual Studio Build Tools not found. Install Visual Studio Build Tools or Visual Studio Community."
    
    else:  # Unix-like systems
        # Check for essential build tools
        tools = ["gcc", "g++", "make"]
        missing = []
        
        for tool in tools:
            success, _ = run_command(["which", tool])
            if not success:
                missing.append(tool)
        
        if missing:
            return False, f"Missing build tools: {', '.join(missing)}. Install build-essential (Ubuntu/Debian) or Xcode Command Line Tools (macOS)."
        
        return True, "Build tools available"

def check_openssl() -> Tuple[bool, str]:
    """Check for OpenSSL development libraries (Unix-like systems)"""
    if os.name == 'nt':  # Windows - usually handled by vcpkg or similar
        return True, "OpenSSL (Windows)"
    
    # Check if pkg-config can find openssl
    success, _ = run_command(["pkg-config", "--exists", "openssl"])
    if success:
        return True, "OpenSSL development libraries available"
    
    return False, "OpenSSL development libraries not found. Install libssl-dev (Ubuntu/Debian) or openssl (macOS via Homebrew)."

def check_network_connectivity() -> Tuple[bool, str]:
    """Check basic network connectivity"""
    # Try to connect to a well-known host
    success, _ = run_command(["ping", "-c", "1", "8.8.8.8"] if os.name != 'nt' else ["ping", "-n", "1", "8.8.8.8"])
    if not success:
        return False, "Network connectivity issue. Please check your internet connection."
    
    return True, "Network connectivity"

def main():
    """Main dependency checker"""
    print("i Checking dependencies for Universal Connectivity Workshop (Rust)...")
    print("i " + "=" * 58)
    
    checks = [
        ("Rust Compiler", check_rust_version),
        ("Cargo Package Manager", check_cargo),
        ("Docker", check_docker),
        ("Docker Compose", check_docker_compose),
        ("Build Tools", check_build_tools),
        ("OpenSSL Libraries", check_openssl),
        ("Network Connectivity", check_network_connectivity),
    ]
    
    failed_checks = []
    
    for name, check_func in checks:
        try:
            success, message = check_func()
            if success:
                print(f"v {name}: {message}")
            else:
                print(f"x {name}: {message}")
                failed_checks.append(name)
        except Exception as e:
            print(f"x {name}: Error during check - {e}")
            failed_checks.append(name)
    
    print("i " + "=" * 58)
    
    if failed_checks:
        print(f"x {len(failed_checks)} dependency check(s) failed:")
        for check in failed_checks:
            print(f"x   - {check}")
        print("^ Please fix the issues above before starting the workshop.")
        print("i Refer to the setup.md file for detailed installation instructions.")
        sys.exit(1)
    else:
        print("y All dependency checks passed!")
        print("r You're ready to start the Universal Connectivity Workshop!")
        print("i Next steps:")
        print("i 1. Create a new Rust project: cargo new uc-app && cd uc-app")
        print("i 2. Run the workshop tool from your project directory")
        print("i 3. Select English → Rust → Universal Connectivity Workshop")
        print("i 4. Start with Lesson 1!")
        sys.exit(0)

if __name__ == "__main__":
    main()