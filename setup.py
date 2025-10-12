#!/usr/bin/env python3
"""
Bjorn Bot Setup Script
Automated setup and installation for the bot
"""
import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.8+"""
    print("Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required!")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def install_dependencies():
    """Install required packages"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies!")
        return False


def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    directories = ["data", "logs", "cogs", "config", "utils"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created/verified: {directory}/")
    
    return True


def create_env_file():
    """Create .env file from template"""
    print("\n⚙️ Setting up environment file...")
    
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if env_path.exists():
        response = input(".env file already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("⏭️ Skipping .env creation")
            return True
    
    # Check if .env.example exists
    if env_example_path.exists():
        with open(env_example_path, 'r') as f:
            template = f.read()
    else:
        # Create basic template
        template = """# Bjorn Discord Bot Configuration

# Discord Bot Token
DISCORD_TOKEN=your_token_here

# Bot Settings
BOT_NAME=Bjorn
DEBUG_MODE=false

# Database
DATABASE_URL=sqlite:///data/bjorn.db

# Economy Settings
EARN_MIN=1
EARN_MAX=50
DAILY_BONUS_MIN=50
DAILY_BONUS_MAX=100
WEEKLY_BONUS_MIN=200
WEEKLY_BONUS_MAX=500
REFERRAL_BONUS=50
BANK_INTEREST_RATE=0.02

# Investment System
INVESTMENT_MIN_AMOUNT=100
INVESTMENT_MAX_AMOUNT=10000
INVESTMENT_MIN_RETURN=0.5
INVESTMENT_MAX_RETURN=2.5
INVESTMENT_RISK_CHANCE=0.3

# Crime System
CRIME_SUCCESS_RATE=0.75
CRIME_REWARD_MIN=25
CRIME_REWARD_MAX=150
CRIME_FINE_MIN=10
CRIME_FINE_MAX=75

# Moderation Settings
AUTO_BAN_THRESHOLD=5
LOG_RETENTION_DAYS=30

# Logging Configuration
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# Feature Toggles
ECONOMY_ENABLED=true
MODERATION_ENABLED=true
REFERRAL_ENABLED=true
MARKETPLACE_ENABLED=true
PROFILES_ENABLED=true
INVESTMENT_ENABLED=true
DAILY_INTEREST_ENABLED=true
"""
    
    with open(env_path, 'w') as f:
        f.write(template)
    
    print("✅ .env file created!")
    print("\n⚠️ IMPORTANT: Edit .env and add your Discord bot token!")
    return True


def create_init_files():
    """Create __init__.py files in modules"""
    print("\n📝 Creating module init files...")
    modules = ["cogs", "config", "utils"]
    
    for module in modules:
        init_file = Path(module) / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"✅ Created: {init_file}")
    
    return True


def display_next_steps():
    """Display next steps for the user"""
    print("\n" + "="*60)
    print("🎉 Setup Complete!")
    print("="*60)
    print("\n📋 Next Steps:\n")
    print("1. Get your Discord bot token:")
    print("   - Go to https://discord.com/developers/applications")
    print("   - Create a new application (or select existing)")
    print("   - Go to 'Bot' section and copy the token")
    print()
    print("2. Edit the .env file:")
    print("   - Open .env in a text editor")
    print("   - Replace 'your_token_here' with your actual bot token")
    print()
    print("3. Enable bot intents:")
    print("   - In the Discord Developer Portal, go to 'Bot' section")
    print("   - Enable 'Message Content Intent'")
    print("   - Enable 'Server Members Intent'")
    print()
    print("4. Invite the bot to your server:")
    print("   - Go to 'OAuth2' > 'URL Generator'")
    print("   - Select scopes: 'bot' and 'applications.commands'")
    print("   - Select permissions: Administrator (or specific permissions)")
    print("   - Copy and open the generated URL")
    print()
    print("5. Run the bot:")
    print("   python main.py")
    print()
    print("="*60)
    print("📚 For more information, see README.md")
    print("🐛 Report issues: https://github.com/retrac-ca/bjorn/issues")
    print("="*60)


def main():
    """Main setup function"""
    print("="*60)
    print("🤖 Bjorn Discord Bot - Setup Script")
    print("="*60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n⚠️ Setup incomplete due to dependency installation failure")
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("\n⚠️ Setup incomplete due to directory creation failure")
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        print("\n⚠️ Setup incomplete due to .env file creation failure")
        sys.exit(1)
    
    # Create init files
    if not create_init_files():
        print("\n⚠️ Setup incomplete due to init file creation failure")
        sys.exit(1)
    
    # Display next steps
    display_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)