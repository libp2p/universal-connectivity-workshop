#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dependency checker for go-libp2p workshop
Verifies that all required tools and dependencies are installed.
"""

import subprocess
import sys
import os
import shutil

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_command(command, version_flag="--version", min_version=None):
    """Check if a command exists and optionally verify minimum version"""
    try:
        result = subprocess.run(
            [command, version_flag],
            capture_output=True,
            text=True,
            timeout=5
        )
        return True, result.stdout + result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
        return False, ""

def check_go_version():
    """Check Go installation and version"""
    print("Checking Go installation...")

    # Check if go command exists
    if not shutil.which("go"):
        print("  ✗ Go is not installed")
        print("    Install from: https://go.dev/dl/")
        return False

    # Get version
    try:
        result = subprocess.run(
            ["go", "version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        version_str = result.stdout.strip()
        print(f"  ✓ {version_str}")

        # Extract version number
        import re
        match = re.search(r'go(\d+)\.(\d+)', version_str)
        if match:
            major, minor = int(match.group(1)), int(match.group(2))
            if major > 1 or (major == 1 and minor >= 21):
                print(f"  ✓ Version is sufficient (>= 1.21)")
                return True
            else:
                print(f"  ⚠ Version {major}.{minor} is below recommended 1.21")
                print("    Consider upgrading: https://go.dev/dl/")
                return True  # Still works, just warn

        return True
    except Exception as e:
        print(f"  ✗ Error checking Go version: {e}")
        return False

def check_go_modules():
    """Check if Go modules are working"""
    print("Checking Go modules...")

    try:
        result = subprocess.run(
            ["go", "env", "GO111MODULE"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            print(f"  ✓ Go modules enabled: {result.stdout.strip()}")
            return True
        else:
            print(f"  ⚠ Could not verify Go modules status")
            return True  # Not critical
    except Exception as e:
        print(f"  ⚠ Error checking Go modules: {e}")
        return True  # Not critical

def check_git():
    """Check Git installation"""
    print("Checking Git installation...")

    if not shutil.which("git"):
        print("  ✗ Git is not installed")
        print("    Install from: https://git-scm.com/downloads")
        return False

    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"  ✓ {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"  ✗ Error checking Git: {e}")
        return False

def check_docker():
    """Check Docker installation (optional)"""
    print("Checking Docker installation (optional)...")

    if not shutil.which("docker"):
        print("  ⚠ Docker is not installed (optional for local development)")
        print("    Install from: https://www.docker.com/get-started")
        return True  # Optional, so return True

    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"  ✓ {result.stdout.strip()}")

        # Check if Docker is running
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("  ✓ Docker daemon is running")
        else:
            print("  ⚠ Docker is installed but daemon might not be running")

        return True
    except Exception as e:
        print(f"  ⚠ Docker check warning: {e}")
        return True  # Optional

def check_python():
    """Check Python installation"""
    print("Checking Python installation...")

    version = sys.version_info
    print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")

    if version.major >= 3 and version.minor >= 8:
        print("  ✓ Python version is sufficient (>= 3.8)")
        return True
    else:
        print(f"  ⚠ Python {version.major}.{version.minor} is below recommended 3.8")
        return True  # Still works, just warn

def check_network():
    """Basic network connectivity check"""
    print("Checking network connectivity...")

    try:
        import socket
        socket.create_connection(("1.1.1.1", 53), timeout=3)
        print("  ✓ Network connectivity OK")
        return True
    except OSError:
        print("  ⚠ Network connectivity issue detected")
        print("    Some features may not work without internet access")
        return True  # Not critical for local testing

def test_go_libp2p_import():
    """Test if go-libp2p can be imported"""
    print("Testing go-libp2p import...")

    # Create a temporary test file
    test_code = '''package main
import _ "github.com/libp2p/go-libp2p"
func main() {}
'''

    test_dir = "/tmp/libp2p-test" if os.name != 'nt' else os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'libp2p-test')

    try:
        os.makedirs(test_dir, exist_ok=True)

        # Write test file
        test_file = os.path.join(test_dir, "test.go")
        with open(test_file, "w") as f:
            f.write(test_code)

        # Initialize module
        subprocess.run(
            ["go", "mod", "init", "test"],
            cwd=test_dir,
            capture_output=True,
            timeout=10
        )

        # Try to get the package
        result = subprocess.run(
            ["go", "get", "github.com/libp2p/go-libp2p@latest"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print("  ✓ go-libp2p can be imported successfully")
            return True
        else:
            print("  ⚠ Issue importing go-libp2p")
            print(f"    {result.stderr[:200]}")
            return True  # Not critical at this stage
    except Exception as e:
        print(f"  ⚠ Could not test go-libp2p import: {e}")
        return True  # Not critical
    finally:
        # Cleanup
        try:
            import shutil
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir)
        except:
            pass

def main():
    """Main dependency check function"""
    print("=" * 60)
    print("go-libp2p Workshop Dependency Checker")
    print("=" * 60)
    print()

    checks = [
        ("Go", check_go_version),
        ("Go Modules", check_go_modules),
        ("Git", check_git),
        ("Python", check_python),
        ("Docker", check_docker),
        ("Network", check_network),
        ("go-libp2p", test_go_libp2p_import),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
            print()
        except Exception as e:
            print(f"  ✗ Unexpected error in {name} check: {e}")
            results.append((name, False))
            print()

    # Summary
    print("=" * 60)
    print("Summary:")
    print("=" * 60)

    required_checks = ["Go", "Git", "Python"]
    optional_checks = ["Docker", "Network", "Go Modules", "go-libp2p"]

    required_passed = all(result for name, result in results if name in required_checks)
    optional_passed = [name for name, result in results if name in optional_checks and not result]

    if required_passed:
        print("✅ All required dependencies are installed!")
        print()
        print("You're ready to start the workshop!")
        print()
        print("Next steps:")
        print("  1. Navigate to lesson 01: cd 01-identity-and-host")
        print("  2. Read the lesson.md file")
        print("  3. Start coding in app/main.go")
        print("  4. Test with: go run app/main.go")

        if optional_passed:
            print()
            print("⚠ Optional dependencies not fully available:")
            for name in optional_passed:
                print(f"  • {name}")
            print("  These are not required but may enhance your experience")

        return True
    else:
        print("✗ Some required dependencies are missing")
        print()
        print("Please install missing dependencies and run this check again:")
        print("  python deps.py")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nCheck interrupted by user")
        sys.exit(1)
