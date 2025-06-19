#!/usr/bin/env python3
import sys
import subprocess
import shutil

def check_command(command, min_version=None):
    try:
        # Check if command exists
        result = subprocess.run([command, "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"! {command} is not installed")
            return False
        
        # If a minimum version is specified, check it (simplified version check)
        if min_version and min_version not in result.stdout:
            print(f"! {command} version {min_version} or higher is required")
            return False
        
        print(f"v {command} is installed")
        return True
    except FileNotFoundError:
        print(f"! {command} is not installed")
        return False

def main():
    # Check required dependencies
    all_dependencies_met = True
    
    # Check if rust is installed
    if not check_command("rustc"):
        all_dependencies_met = False
    
    # Check if cargo is installed
    if not check_command("cargo"):
        all_dependencies_met = False
    
    if all_dependencies_met:
        print("All dependencies are met!")
        sys.exit(0)
    else:
        print("Some dependencies are missing. Please install them before continuing.")
        sys.exit(1)

if __name__ == "__main__":
    main()
