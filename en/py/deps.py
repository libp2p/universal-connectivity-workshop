#!/usr/bin/env python3
"""
Dependencies checker for py-libp2p Universal Connectivity Workshop
Checks that all required Python packages and tools are available.
"""

import sys
import subprocess
import importlib.util
import pkg_resources
from packaging import version

def check_python_version():
    """Check if Python version meets minimum requirements"""
    min_version = "3.8"
    current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    if sys.version_info < (3, 8):
        print(f"! Python {min_version} or higher is required. Current version: {current_version}")
        return False
    
    print(f"✓ Python {current_version} is installed")
    return True

def check_pip():
    """Check if pip is available"""
    try:
        import pip
        pip_version = pip.__version__
        print(f"✓ pip {pip_version} is installed")
        return True
    except ImportError:
        print("! pip is not installed")
        return False

def check_package(package_name, min_version=None):
    """Check if a Python package is installed with optional version check"""
    try:
        if min_version:
            pkg_resources.require(f"{package_name}>={min_version}")
            installed_version = pkg_resources.get_distribution(package_name).version
            print(f"✓ {package_name} {installed_version} is installed")
        else:
            importlib.import_module(package_name)
            try:
                installed_version = pkg_resources.get_distribution(package_name).version
                print(f"✓ {package_name} {installed_version} is installed")
            except:
                print(f"✓ {package_name} is installed")
        return True
    except (ImportError, pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
        if min_version:
            print(f"! {package_name} >= {min_version} is required")
        else:
            print(f"! {package_name} is not installed")
        return False

def check_command(command, description=None):
    """Check if a system command is available"""
    try:
        result = subprocess.run([command, "--version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✓ {command} is installed")
            return True
        else:
            print(f"! {command} is not available")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        desc = f" ({description})" if description else ""
        print(f"! {command}{desc} is not installed")
        return False

def install_instructions():
    """Print installation instructions for missing dependencies"""
    print("\n" + "="*60)
    print("INSTALLATION INSTRUCTIONS")
    print("="*60)
    print("\nTo install the required Python packages, run:")
    print("pip install asyncio aiohttp multiaddr protobuf cryptography")
    print("\nFor py-libp2p (if available in the future):")
    print("pip install py-libp2p")
    print("\nAlternatively, install from source:")
    print("git clone https://github.com/libp2p/py-libp2p.git")
    print("cd py-libp2p")
    print("pip install -e .")
    print("\nFor Docker (if you plan to use containerized lessons):")
    print("Visit: https://docs.docker.com/get-docker/")

def main():
    """Main dependency checking function"""
    print("Checking dependencies for py-libp2p Universal Connectivity Workshop...")
    print("="*70)
    
    all_dependencies_met = True
    
    # Check Python version
    if not check_python_version():
        all_dependencies_met = False
    
    # Check pip
    if not check_pip():
        all_dependencies_met = False
    
    # Check core Python packages
    required_packages = [
        ("asyncio", None),  # Built-in, but check if importable
        ("aiohttp", "3.8.0"),
        ("multiaddr", None),
        ("protobuf", "3.20.0"),
        ("cryptography", "3.4.0"),
    ]
    
    print("\nChecking required Python packages:")
    for package, min_ver in required_packages:
        if not check_package(package, min_ver):
            all_dependencies_met = False
    
    # Check optional but recommended packages
    print("\nChecking optional packages:")
    optional_packages = [
        ("pytest", None),
        ("black", None),
        ("mypy", None),
    ]
    
    for package, min_ver in optional_packages:
        check_package(package, min_ver)  # Don't fail on optional packages
    
    # Check system tools
    print("\nChecking system tools:")
    if not check_command("git", "version control"):
        print("  (Git is recommended for cloning py-libp2p source)")
    
    check_command("docker", "containerization")  # Optional
    
    print("\n" + "="*70)
    if all_dependencies_met:
        print("✅ All required dependencies are met!")
        print("You're ready to start the workshop!")
    else:
        print("❌ Some required dependencies are missing.")
        install_instructions()
        sys.exit(1)

if __name__ == "__main__":
    main()