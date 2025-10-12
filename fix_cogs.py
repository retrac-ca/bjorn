"""
Quick fix script to update all cog files with correct class names
Run this in your bjorn directory: python fix_cogs.py
"""
import os
from pathlib import Path

def fix_file(filepath, old_class, new_class):
    """Fix class name in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace class definition
        content = content.replace(f'class {old_class}(commands.Cog):', f'class {new_class}(commands.Cog, name="{old_class}"):')
        
        # Replace setup function
        content = content.replace(f'await bot.add_cog({old_class}(bot))', f'await bot.add_cog({new_class}(bot))')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Fixed {filepath.name}")
        return True
    except Exception as e:
        print(f"❌ Error fixing {filepath.name}: {e}")
        return False

def main():
    """Main fix function"""
    print("🔧 Fixing cog class names...\n")
    
    cogs_dir = Path('cogs')
    
    if not cogs_dir.exists():
        print("❌ cogs/ directory not found!")
        return
    
    fixes = [
        ('economy.py', 'Economy', 'EconomyCog'),
        ('bank.py', 'Bank', 'BankCog'),
        ('casino.py', 'Casino', 'CasinoCog'),
        ('investment.py', 'Investment', 'InvestmentCog'),
        ('store.py', 'Store', 'StoreCog'),
        ('profile.py', 'Profile', 'ProfileCog'),
        ('referral.py', 'Referral', 'ReferralCog'),
        ('reminders.py', 'Reminders', 'RemindersCog'),
        ('moderation.py', 'Moderation', 'ModerationCog'),
        ('utility.py', 'Utility', 'UtilityCog'),
    ]
    
    success_count = 0
    
    for filename, old_class, new_class in fixes:
        filepath = cogs_dir / filename
        if filepath.exists():
            if fix_file(filepath, old_class, new_class):
                success_count += 1
        else:
            print(f"⚠️  {filename} not found, skipping")
    
    print(f"\n✅ Fixed {success_count}/{len(fixes)} files")
    print("\n🚀 You can now run: python main.py")

if __name__ == '__main__':
    main()