#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dependency checker for jvm-libp2p workshop
Verifies that all required tools and dependencies are installed.
"""

import subprocess
import sys
import os
import shutil
import re

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

def check_java_version():
    """Check Java installation and version"""
    print("Checking Java installation...")

    # Check if java command exists
    if not shutil.which("java"):
        print("  ✗ Java is not installed")
        print("    Install from: https://adoptium.net/")
        return False

    # Get version
    try:
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        version_str = result.stderr.strip()  # Java outputs version to stderr
        print(f"  ✓ {version_str.splitlines()[0] if version_str else 'Java installed'}")

        # Extract version number
        match = re.search(r'version "(\d+)\.?(\d*)', version_str)
        if match:
            major = int(match.group(1))
            # Java 9+ uses single version number, earlier uses 1.x
            if major == 1 and match.group(2):
                major = int(match.group(2))

            if major >= 11:
                print(f"  ✓ Version is sufficient (>= 11)")
                return True
            else:
                print(f"  ✗ Java {major} is below required version 11")
                print("    Install Java 11 or higher from: https://adoptium.net/")
                return False

        return True
    except Exception as e:
        print(f"  ✗ Error checking Java version: {e}")
        return False

def check_gradle():
    """Check Gradle installation (wrapper can be used instead)"""
    print("Checking Gradle installation...")

    if not shutil.which("gradle"):
        print("  ⚠ Gradle is not installed globally")
        print("    This is OK - we'll use Gradle wrapper (./gradlew)")
        return True  # Not critical, wrapper is fine

    try:
        result = subprocess.run(
            ["gradle", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        # Extract just the Gradle version line
        for line in result.stdout.splitlines():
            if "Gradle" in line:
                print(f"  ✓ {line}")
                break

        # Check version
        match = re.search(r'Gradle (\d+)\.(\d+)', result.stdout)
        if match:
            major = int(match.group(1))
            if major >= 8:
                print(f"  ✓ Version is sufficient (>= 8.0)")
            else:
                print(f"  ⚠ Gradle {major}.x is below recommended 8.0")

        return True
    except Exception as e:
        print(f"  ⚠ Could not check Gradle: {e}")
        return True  # Not critical

def check_kotlin_compiler():
    """Check Kotlin compiler (optional, Gradle handles it)"""
    print("Checking Kotlin compiler...")

    if not shutil.which("kotlinc"):
        print("  ⚠ Kotlin compiler not installed globally (optional)")
        print("    Gradle will download Kotlin automatically")
        return True  # Not critical

    try:
        result = subprocess.run(
            ["kotlinc", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        version_str = result.stderr if result.stderr else result.stdout
        print(f"  ✓ {version_str.strip()}")
        return True
    except Exception as e:
        print(f"  ⚠ Could not check Kotlin: {e}")
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

def test_jvm_libp2p_build():
    """Test if a minimal jvm-libp2p project can build"""
    print("Testing jvm-libp2p build...")

    test_dir = "/tmp/libp2p-test" if os.name != 'nt' else os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'libp2p-test')

    try:
        os.makedirs(test_dir, exist_ok=True)

        # Write minimal build.gradle.kts
        build_file = os.path.join(test_dir, "build.gradle.kts")
        with open(build_file, "w") as f:
            f.write('''
plugins {
    kotlin("jvm") version "1.9.24"
}

repositories {
    mavenCentral()
    maven("https://jitpack.io")
}

dependencies {
    implementation("io.libp2p:jvm-libp2p:1.1.1-RELEASE")
}
''')

        # Write minimal settings.gradle.kts
        settings_file = os.path.join(test_dir, "settings.gradle.kts")
        with open(settings_file, "w") as f:
            f.write('rootProject.name = "test"\n')

        # Try to build (downloads dependencies only)
        print("  ⏳ Downloading jvm-libp2p dependencies (this may take a minute)...")
        result = subprocess.run(
            ["gradle", "dependencies"] if shutil.which("gradle") else ["./gradlew", "dependencies"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0 or "jvm-libp2p" in result.stdout:
            print("  ✓ jvm-libp2p dependencies resolved successfully")
            return True
        else:
            print("  ⚠ Issue resolving jvm-libp2p dependencies")
            if "jitpack" in result.stdout or "jitpack" in result.stderr:
                print("    Note: jitpack.io builds on-demand, retry if needed")
            return True  # Not critical at this stage
    except subprocess.TimeoutExpired:
        print("  ⚠ Build test timed out (network may be slow)")
        return True  # Not critical
    except Exception as e:
        print(f"  ⚠ Could not test jvm-libp2p build: {e}")
        return True  # Not critical
    finally:
        # Cleanup
        try:
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir)
        except:
            pass

def main():
    """Main dependency check function"""
    print("=" * 60)
    print("jvm-libp2p Workshop Dependency Checker")
    print("=" * 60)
    print()

    checks = [
        ("Java", check_java_version),
        ("Gradle", check_gradle),
        ("Kotlin", check_kotlin_compiler),
        ("Git", check_git),
        ("Python", check_python),
        ("Docker", check_docker),
        ("Network", check_network),
        ("jvm-libp2p", test_jvm_libp2p_build),
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

    required_checks = ["Java", "Git", "Python"]
    optional_checks = ["Gradle", "Kotlin", "Docker", "Network", "jvm-libp2p"]

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
        print("  3. Start coding in app/src/main/kotlin/Main.kt")
        print("  4. Build with: cd app && ./gradlew build")
        print("  5. Run with: ./gradlew run")

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
