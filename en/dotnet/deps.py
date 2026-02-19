#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dependencies checker for .NET libp2p Universal Connectivity Workshop
Checks that all required tools and dependencies are available.
"""

import sys
import subprocess
import re
import os

# Use ASCII-compatible check marks for Windows compatibility
CHECK = "v"  # or "v" on systems that support it
CROSS = "x"  # or "x" on systems that support it
WARN = "!"   # or "!" on systems that support it

def check_command_version(command, version_flag="--version", min_version=None, version_regex=None):
    """Check if a command exists and optionally verify minimum version"""
    try:
        result = subprocess.run([command, version_flag],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            output = result.stdout + result.stderr

            if min_version and version_regex:
                match = re.search(version_regex, output)
                if match:
                    version = match.group(1)
                    if compare_versions(version, min_version) >= 0:
                        print(f"v {command} {version} is installed (>= {min_version})")
                        return True
                    else:
                        print(f"x {command} {version} is installed but {min_version} or higher is required")
                        return False

            # Just print the first line of version output
            first_line = output.strip().split('\n')[0]
            print(f"v {command} is installed: {first_line}")
            return True
        else:
            print(f"x {command} is not available")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print(f"x {command} is not installed")
        return False

def compare_versions(version1, version2):
    """Compare two version strings (e.g., '8.0.1' vs '8.0.0')"""
    def normalize(v):
        return [int(x) for x in re.sub(r'(\.0+)*$','', v).split(".")]
    return (normalize(version1) > normalize(version2)) - (normalize(version1) < normalize(version2))

def check_dotnet_sdk():
    """Check for .NET SDK (not just runtime)"""
    try:
        result = subprocess.run(["dotnet", "--list-sdks"],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            sdks = result.stdout.strip().split('\n')
            print(f"v .NET SDK is installed:")
            for sdk in sdks[:3]:  # Show first 3 SDKs
                print(f"  - {sdk}")
            if len(sdks) > 3:
                print(f"  ... and {len(sdks) - 3} more")

            # Check if .NET 8.0 or higher is available
            has_net8 = any('8.' in sdk or '9.' in sdk or '10.' in sdk for sdk in sdks)
            if has_net8:
                print(f"v .NET 8.0+ SDK available")
                return True
            else:
                print(f"x .NET 8.0 or higher not found. Please install .NET 8 SDK.")
                return False
        else:
            print(f"x No .NET SDKs found. Please install .NET 8 SDK.")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print(f"x dotnet command not found. Please install .NET 8 SDK.")
        return False

def check_nuget_package():
    """Check if Nethermind.Libp2p package is accessible"""
    print("\nChecking NuGet package availability...")
    try:
        # Create a temporary directory
        import tempfile
        import shutil

        with tempfile.TemporaryDirectory() as tmpdir:
            # Try to create a test project and add the package
            test_proj = os.path.join(tmpdir, "test.csproj")
            with open(test_proj, 'w') as f:
                f.write("""<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Nethermind.Libp2p" Version="1.0.0-preview.*" />
  </ItemGroup>
</Project>""")

            # Try to restore
            result = subprocess.run(["dotnet", "restore", test_proj],
                                    capture_output=True, text=True,
                                    timeout=30, cwd=tmpdir)

            if result.returncode == 0:
                print(f"v Nethermind.Libp2p package is accessible on NuGet")
                return True
            else:
                if "Unable to find package" in result.stderr or "not found" in result.stderr:
                    print(f"x Nethermind.Libp2p package not found on NuGet")
                    print(f"  (This is expected if the package is not yet published)")
                else:
                    print(f"x Error restoring Nethermind.Libp2p package")
                return False
    except Exception as e:
        print(f"! Could not verify NuGet package availability: {e}")
        return None  # Don't fail on this check

def check_docker():
    """Check Docker and Docker Compose"""
    docker_ok = check_command_version("docker", "--version")

    if docker_ok:
        # Check if Docker daemon is running
        try:
            result = subprocess.run(["docker", "ps"],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"v Docker daemon is running")
            else:
                print(f"! Docker is installed but daemon is not running")
                print(f"  Please start Docker Desktop")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print(f"! Docker daemon check failed")

    # Check Docker Compose (V2 is built into docker)
    try:
        result = subprocess.run(["docker", "compose", "version"],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"v Docker Compose (V2) is available")
        else:
            # Try old docker-compose command
            check_command_version("docker-compose", "--version")
    except:
        pass

    return docker_ok

def check_python():
    """Check Python version for running check scripts"""
    version_info = sys.version_info
    current_version = f"{version_info.major}.{version_info.minor}.{version_info.micro}"

    if version_info >= (3, 8):
        print(f"v Python {current_version} is installed (>= 3.8)")
        return True
    else:
        print(f"x Python 3.8+ is required for check scripts. Current: {current_version}")
        return False

def check_git():
    """Check Git availability"""
    return check_command_version("git", "--version")

def print_installation_instructions(failed_checks):
    """Print installation instructions for missing dependencies"""
    print("\n" + "="*70)
    print("INSTALLATION INSTRUCTIONS")
    print("="*70)

    if "dotnet" in failed_checks:
        print("\n📦 .NET SDK:")
        print("  Visit: https://dotnet.microsoft.com/download")
        print("  Download and install .NET 8 SDK (LTS)")
        print("  After installation, verify with: dotnet --version")

    if "docker" in failed_checks:
        print("\n🐳 Docker Desktop:")
        print("  Windows/Mac: https://www.docker.com/products/docker-desktop")
        print("  Linux: https://docs.docker.com/engine/install/")
        print("  After installation, start Docker Desktop")

    if "python" in failed_checks:
        print("\n🐍 Python 3.8+:")
        print("  Visit: https://www.python.org/downloads/")
        print("  Or use your system package manager")

    if "git" in failed_checks:
        print("\n📂 Git:")
        print("  Visit: https://git-scm.com/downloads")
        print("  Or use your system package manager")

    print("\n" + "="*70)

def main():
    """Main dependency checking function"""
    print("="*70)
    print("Checking dependencies for .NET libp2p Universal Connectivity Workshop")
    print("="*70 + "\n")

    all_ok = True
    failed_checks = []

    # Check .NET SDK
    print("Checking .NET SDK...")
    if not check_dotnet_sdk():
        all_ok = False
        failed_checks.append("dotnet")

    print("\nChecking build tools...")
    # Check Git
    if not check_git():
        print("  ! Git is recommended but not required for the workshop")

    # Check Docker
    print("\nChecking Docker...")
    if not check_docker():
        all_ok = False
        failed_checks.append("docker")
        print("  i Docker is required for running lessons in containers")

    # Check Python (for check scripts)
    print("\nChecking Python (for check scripts)...")
    if not check_python():
        all_ok = False
        failed_checks.append("python")

    # Check NuGet package (optional, might not be published yet)
    nuget_result = check_nuget_package()
    if nuget_result is False:
        print("  i Note: You may need to build dotnet-libp2p from source")

    print("\n" + "="*70)
    if all_ok:
        print("v All required dependencies are met!")
        print("\nYou're ready to start the .NET libp2p workshop!")
        print("\nNext steps:")
        print("  1. Read en/dotnet/setup.md for detailed setup instructions")
        print("  2. Navigate to en/dotnet/01-identity-and-host/")
        print("  3. Read the lesson.md file")
        print("  4. Start coding!\n")
    else:
        print("x Some required dependencies are missing.")
        print_installation_instructions(failed_checks)
        print("\nAfter installing missing dependencies, run this script again:")
        print("  python3 deps.py\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
