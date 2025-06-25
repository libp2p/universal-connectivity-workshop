#!/usr/bin/env python3
import sys
import subprocess

def check_command(command, version_flag="--version", min_version=None):
    try:
        result = subprocess.run([command, version_flag], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"! {command} is not installed or not working")
            return False
        if min_version and min_version not in result.stdout:
            print(f"! {command} version {min_version} or higher is required")
            return False
        print(f"v {command} is installed: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print(f"! {command} is not installed")
        return False

def main():
    all_dependencies_met = True
    if not check_command("node"):  # Node.js
        all_dependencies_met = False
    if not check_command("npm"):   # npm
        all_dependencies_met = False
    if not check_command("docker"):  # Docker
        all_dependencies_met = False
    if not check_command("docker-compose", "--version"):  # Docker Compose
        all_dependencies_met = False
    if all_dependencies_met:
        print("All dependencies are met!")
        sys.exit(0)
    else:
        print("Some dependencies are missing. Please install them before continuing.")
        sys.exit(1)

if __name__ == "__main__":
    main()
