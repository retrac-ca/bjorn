#!/usr/bin/env python3
"""
Setup Script for Bjorn Discord Bot

This script helps set up the Bjorn bot environment and dependencies.
Run this script after downloading/extracting the bot files.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def print_header():
    """Print setup header."""
    print("="*60)
    print("🐻 Bjorn Discord Bot Setup")
    print("="*60)
    print()


def check_python_version():
    """Check if Python version is compatible."""
    print("🔍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required!")
        print(f"   Current version: {platform.python_version()}")
        print("   Please install Python 3.8+ and try again.")
        return False
    
    print(f"✅ Python version: {platform.python_version()}")
    return True


def check_pip():
    """Check if pip is available."""
    print("\n🔍 Checking pip availability...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        print("✅ pip is available")
        return True
    except subprocess.CalledProcessError:
        print("❌ Error: pip is not available!")
        print("   Please install pip and try again.")
        return False


def create_directories():
    """Create necessary directories."""
    print("\n📁 Creating directories...")
    
    directories = ["data", "logs"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")


def install_dependencies():
    """Install Python dependencies."""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print("   Please check your internet connection and try again.")
        return False
    except FileNotFoundError:
        print("❌ Error: requirements.txt not found!")
        return False


def setup_env_file():
    """Set up environment file."""
    print("\n🔧 Setting up environment file...")
    
    if Path(".env").exists():
        print("⚠️  .env file already exists. Skipping creation.")
        return True
    
    if not Path(".env.example").exists():
        print("❌ Error: .env.example file not found!")
        return False
    
    try:
        # Copy .env.example to .env
        with open(".env.example", "r") as src:
            content = src.read()
        
        with open(".env", "w") as dst:
            dst.write(content)
        
        print("✅ Created .env file from .env.example")
        print("⚠️  Please edit the .env file and add your Discord bot token!")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False


def verify_bot_structure():
    """Verify bot file structure."""
    print("\n🔍 Verifying bot structure...")
    
    required_files = [
        "main.py",
        "requirements.txt",
        "README.md",
        ".env.example"
    ]
    
    required_dirs = [
        "config",
        "cogs", 
        "utils"
    ]
    
    missing_files = []
    missing_dirs = []
    
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    for directory in required_dirs:
        if not Path(directory).exists():
            missing_dirs.append(directory)
    
    if missing_files or missing_dirs:
        print("❌ Missing required files/directories:")
        for file in missing_files:
            print(f"   - {file}")
        for directory in missing_dirs:
            print(f"   - {directory}/")
        return False
    
    print("✅ All required files and directories found!")
    return True


def print_next_steps():
    """Print next steps for user."""
    print("\n" + "="*60)
    print("🎉 Setup Complete!")
    print("="*60)
    print()
    print("Next steps:")
    print("1. Edit the .env file and add your Discord bot token")
    print("2. Make sure your bot has the necessary permissions")
    print("3. Run the bot with: python main.py")
    print()
    print("For more information, see README.md")
    print()
    print("Discord Bot Permissions needed:")
    print("- Send Messages")
    print("- Read Message History") 
    print("- Embed Links")
    print("- Attach Files")
    print("- Manage Messages (for moderation)")
    print("- Kick Members (for moderation)")
    print("- Ban Members (for moderation)")
    print()
    print("Enjoy your Bjorn bot! 🐻")


def main():
    """Main setup function."""
    print_header()
    
    # Run setup steps
    steps = [
        ("Checking Python version", check_python_version),
        ("Checking pip", check_pip),
        ("Verifying bot structure", verify_bot_structure),
        ("Creating directories", lambda: (create_directories(), True)[1]),
        ("Installing dependencies", install_dependencies),
        ("Setting up environment file", setup_env_file),
    ]
    
    failed_steps = []
    
    for step_name, step_function in steps:
        if not step_function():
            failed_steps.append(step_name)
    
    if failed_steps:
        print(f"\n❌ Setup failed! Failed steps: {', '.join(failed_steps)}")
        print("Please fix the issues above and run setup again.")
        return False
    
    print_next_steps()
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
