#!/usr/bin/env python3
"""
Dependencies checker for py-libp2p Universal Connectivity Workshop
Checks that all required Python packages and tools are available.
"""

import sys
import subprocess
import importlib
from importlib.metadata import version, PackageNotFoundError

def check_python_version():
    """Check if Python version meets minimum requirements"""
    min_version = "3.8"
    current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    if sys.version_info < (3, 8):
        print(f"[!] Python {min_version} or higher is required. Current version: {current_version}")
        return False

    print(f"[OK] Python {current_version} is installed")
    return True

def check_pip():
    """Check if pip is available"""
    try:
        import pip
        pip_version = pip.__version__
        print(f"[OK] pip {pip_version} is installed")
        return True
    except ImportError:
        print("[!] pip is not installed")
        return False

def install_package(package_name, min_version=None):
    """Install a Python package using pip"""
    package_spec = f"{package_name}>={min_version}" if min_version else package_name
    print(f"Installing {package_spec}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_spec, "-q"])
        print(f"[OK] Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError:
        print(f"[FAIL] Failed to install {package_name}")
        return False

def check_package(package_name, min_version=None, auto_install=False):
    """
    Check if a Python package is installed with optional version check.

    Args:
        package_name: Name of the package to check
        min_version: Minimum required version (optional)
        auto_install: Whether to auto-install if missing

    Returns:
        True if package is installed and meets version requirements, False otherwise
    """
    # Mapping of pip package names to their import names
    # Some packages have different names for installation vs import
    import_name_map = {
        'protobuf': 'google.protobuf',
    }

    import_name = import_name_map.get(package_name, package_name)

    try:
        # First try to import the package using the correct import name
        importlib.import_module(import_name)

        # Then check the version using the pip package name
        try:
            installed_version = version(package_name)

            if min_version:
                # Parse versions for comparison
                from packaging.version import parse as parse_version
                if parse_version(installed_version) < parse_version(min_version):
                    print(f"[!] {package_name} {installed_version} is installed, but >= {min_version} is required")
                    if auto_install:
                        return install_package(package_name, min_version)
                    return False

            print(f"[OK] {package_name} {installed_version} is installed")
        except PackageNotFoundError:
            # Package is importable but not in metadata (rare case)
            print(f"[OK] {package_name} is installed")

        return True

    except ImportError:
        if min_version:
            print(f"[!] {package_name} >= {min_version} is required but not installed")
        else:
            print(f"[!] {package_name} is not installed")

        if auto_install:
            return install_package(package_name, min_version)
        return False

def check_command(command, description=None):
    """Check if a system command is available"""
    try:
        result = subprocess.run([command, "--version"],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"[OK] {command} is installed")
            return True
        else:
            print(f"[!] {command} is not available")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        desc = f" ({description})" if description else ""
        print(f"[!] {command}{desc} is not installed")
        return False

def install_instructions():
    """Print installation instructions for missing dependencies"""
    print("\n" + "="*60)
    print("ADDITIONAL INSTALLATION INSTRUCTIONS")
    print("="*60)
    print("\nFor Docker (if you plan to use containerized lessons):")
    print("Visit: https://docs.docker.com/get-docker/")

def main():
    """Main dependency checking function"""
    print("Checking dependencies for py-libp2p Universal Connectivity Workshop...")
    print("="*70)

    # Check for --auto-install flag
    auto_install = "--auto-install" in sys.argv or "-y" in sys.argv

    if auto_install:
        print("Auto-install mode enabled\n")

    all_dependencies_met = True

    # Check Python version
    if not check_python_version():
        all_dependencies_met = False

    # Check pip
    if not check_pip():
        all_dependencies_met = False
        print("\n[ERROR] pip is required but not installed. Please install pip first.")
        sys.exit(1)

    # Check core Python packages with their minimum versions
    # Note: The order matters - install foundational packages first
    required_packages = [
        # Core dependencies used across all lessons
        ("libp2p", "0.2.0"),           # Main libp2p implementation - CRITICAL!
        ("trio", "0.20.0"),             # Async runtime for all lessons
        ("multiaddr", "0.0.9"),         # Multiaddress parsing

        # Cryptographic dependencies
        ("cryptography", "3.4.8"),      # Used for Ed25519, X25519, RSA keys
        ("base58", "1.0.3"),            # Base58 encoding for peer IDs (constrained by py-cid)

        # Protocol-specific dependencies
        ("protobuf", "3.20.0"),         # Protocol buffers for libp2p protocols

        # Additional optional dependencies (for advanced lessons)
        # Note: packaging is needed for version comparison in this script
        ("packaging", None),            # For version comparison
    ]

    print("\nChecking required Python packages:")
    packages_to_install = []

    for package, min_ver in required_packages:
        if not check_package(package, min_ver, auto_install=False):
            packages_to_install.append((package, min_ver))
            all_dependencies_met = False

    # Install missing packages if needed
    if packages_to_install:
        if auto_install:
            print("\nInstalling missing packages...")
            for package, min_ver in packages_to_install:
                if install_package(package, min_ver):
                    all_dependencies_met = True
                else:
                    all_dependencies_met = False
        else:
            print("\n" + "="*70)
            print("Would you like to install missing packages now? (y/n): ", end="")
            response = input().lower().strip()

            if response in ['y', 'yes']:
                print("\nInstalling missing packages...")
                for package, min_ver in packages_to_install:
                    if install_package(package, min_ver):
                        all_dependencies_met = True
                    else:
                        all_dependencies_met = False
            else:
                print("\nYou can install them manually with:")
                # Build the pip install command with version constraints
                install_cmd_parts = []
                for package, min_ver in packages_to_install:
                    if min_ver:
                        install_cmd_parts.append(f'"{package}>={min_ver}"')
                    else:
                        install_cmd_parts.append(package)
                print(f"pip install {' '.join(install_cmd_parts)}")

    # Check system tools
    print("\nChecking system tools:")
    if not check_command("git", "version control"):
        print("  (Git is recommended for cloning py-libp2p source)")

    check_command("docker", "containerization")

    print("\n" + "="*70)
    if all_dependencies_met:
        print("[SUCCESS] All required dependencies are met!")
        print("You're ready to start the workshop!")
    else:
        print("[!] Some required dependencies are missing.")
        install_instructions()
        sys.exit(1)

if __name__ == "__main__":
    main()
