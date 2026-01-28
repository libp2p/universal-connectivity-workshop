#!/usr/bin/env python3
"""
Dependencies checker for cpp-libp2p Universal Connectivity Workshop
Checks that all required C++ tools and libraries are available.
"""

import sys
import subprocess
import os
import re

def check_command(command, args=["--version"], description=None, min_version=None):
    """Check if a system command is available and optionally check version"""
    try:
        result = subprocess.run([command] + args,
                                capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            output = result.stdout + result.stderr
            version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', output)
            if version_match:
                version = version_match.group(1)
                if min_version:
                    if compare_versions(version, min_version) >= 0:
                        print(f"v {command} {version} is installed (>= {min_version} required)")
                        return True
                    else:
                        print(f"! {command} {version} is installed but >= {min_version} is required")
                        return False
                print(f"v {command} {version} is installed")
            else:
                print(f"v {command} is installed")
            return True
        else:
            desc = f" ({description})" if description else ""
            print(f"! {command}{desc} returned error")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        desc = f" ({description})" if description else ""
        print(f"! {command}{desc} is not installed")
        return False

def compare_versions(v1, v2):
    """Compare two version strings. Returns -1, 0, or 1"""
    def normalize(v):
        return [int(x) for x in re.sub(r'[^\d.]', '', v).split('.')]

    v1_parts = normalize(v1)
    v2_parts = normalize(v2)

    # Pad with zeros
    max_len = max(len(v1_parts), len(v2_parts))
    v1_parts.extend([0] * (max_len - len(v1_parts)))
    v2_parts.extend([0] * (max_len - len(v2_parts)))

    for a, b in zip(v1_parts, v2_parts):
        if a < b:
            return -1
        elif a > b:
            return 1
    return 0

def check_cmake():
    """Check CMake installation"""
    return check_command("cmake", ["--version"], "build system", "3.16")

def check_compiler():
    """Check C++ compiler installation"""
    # Try different compilers
    compilers = [
        ("g++", "10.0"),
        ("clang++", "12.0"),
        ("c++", None),
    ]

    for compiler, min_ver in compilers:
        try:
            result = subprocess.run([compiler, "--version"],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                output = result.stdout + result.stderr
                version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', output)
                if version_match:
                    version = version_match.group(1)
                    if min_ver and compare_versions(version, min_ver) < 0:
                        continue  # Try next compiler
                    print(f"v {compiler} {version} is installed")
                    return True
                print(f"v {compiler} is installed")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    print("! No suitable C++ compiler found (need GCC 10+ or Clang 12+)")
    return False

def check_libp2p():
    """Check if cpp-libp2p is installed"""
    libp2p_dir = os.environ.get('LIBP2P_INSTALL_DIR', os.path.expanduser('~/libp2p'))

    # Check if libp2p install directory exists
    if os.path.exists(os.path.join(libp2p_dir, 'lib', 'cmake', 'libp2p')):
        print(f"v cpp-libp2p found at {libp2p_dir}")
        return True

    # Check common locations
    common_paths = [
        os.path.expanduser('~/libp2p'),
        '/opt/libp2p',
        '/usr/local',
    ]

    for path in common_paths:
        if os.path.exists(os.path.join(path, 'lib', 'cmake', 'libp2p')):
            print(f"v cpp-libp2p found at {path}")
            return True

    print("! cpp-libp2p not found")
    print("  Build from source: https://github.com/libp2p/cpp-libp2p")
    return False

def check_hunter():
    """Check if Hunter dependencies are available"""
    hunter_dir = os.path.expanduser('~/.hunter')

    if os.path.exists(hunter_dir):
        # Look for Install directory
        for root, dirs, files in os.walk(hunter_dir):
            if 'Install' in dirs:
                install_path = os.path.join(root, 'Install')
                print(f"v Hunter dependencies found at {install_path}")
                return True

    print("i Hunter cache not found (will be created when building cpp-libp2p)")
    return False

def check_git():
    """Check git installation"""
    return check_command("git", ["--version"], "version control")

def check_docker():
    """Check Docker installation (optional)"""
    return check_command("docker", ["--version"], "containerization")

def check_openssl():
    """Check OpenSSL installation"""
    return check_command("openssl", ["version"], "cryptography library")

def check_pkg_config():
    """Check pkg-config installation"""
    return check_command("pkg-config", ["--version"], "library configuration")

def install_instructions():
    """Print installation instructions for missing dependencies"""
    print("\n" + "="*70)
    print("INSTALLATION INSTRUCTIONS")
    print("="*70)

    print("\n## Install Build Tools")
    print("\nLinux (Ubuntu/Debian):")
    print("  sudo apt-get update && sudo apt-get install -y \\")
    print("      build-essential cmake git pkg-config libssl-dev")

    print("\nmacOS:")
    print("  xcode-select --install")
    print("  brew install cmake openssl pkg-config")

    print("\n## Build cpp-libp2p (uses Hunter for dependencies)")
    print("  git clone https://github.com/libp2p/cpp-libp2p.git")
    print("  cd cpp-libp2p && mkdir build && cd build")
    print("  cmake .. -DCMAKE_BUILD_TYPE=Release -DTESTING=OFF \\")
    print("      -DCMAKE_INSTALL_PREFIX=$HOME/libp2p")
    print("  cmake --build . -j$(nproc)")
    print("  cmake --install .")

    print("\n## Set environment variables")
    print("  export LIBP2P_INSTALL_DIR=$HOME/libp2p")
    print("  export HUNTER_INSTALL_DIR=$(find ~/.hunter -type d -name Install | head -1)")

    print("\nFor Docker (recommended for consistent builds):")
    print("  Visit: https://docs.docker.com/get-docker/")

def main():
    """Main dependency checking function"""
    print("Checking dependencies for cpp-libp2p Universal Connectivity Workshop...")
    print("="*70)

    all_required_met = True

    # Check required tools
    print("\nChecking required build tools:")

    if not check_compiler():
        all_required_met = False

    if not check_cmake():
        all_required_met = False

    if not check_git():
        all_required_met = False

    if not check_pkg_config():
        print("  (pkg-config is recommended for finding libraries)")

    if not check_openssl():
        all_required_met = False

    # Check cpp-libp2p installation
    print("\nChecking cpp-libp2p:")

    if not check_libp2p():
        print("  (Build cpp-libp2p from source - see setup.md)")

    check_hunter()

    # Check optional tools
    print("\nChecking optional tools:")

    if not check_docker():
        print("  (Docker is recommended for consistent builds)")

    # Summary
    print("\n" + "="*70)
    if all_required_met:
        print("v All required dependencies are met!")
        print("You're ready to start the workshop!")
        print("\nNext steps:")
        print("  1. Navigate to: en/cpp/01-identity-and-swarm/")
        print("  2. Read: lesson.md")
        print("  3. Start coding in: app/")
    else:
        print("! Some required dependencies are missing.")
        install_instructions()
        sys.exit(1)

if __name__ == "__main__":
    main()
