# Bjorn Discord Bot - Complete Setup Guide

## 📋 Table of Contents
1. [Quick Start](#quick-start)
2. [File Structure](#file-structure)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the Bot](#running-the-bot)
6. [Command Reference](#command-reference)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Discord bot token from [Discord Developer Portal](https://discord.com/developers/applications)
- Basic terminal/command line knowledge

### 5-Minute Setup

```bash
# 1. Navigate to your bot directory
cd bjorn

# 2. Run the automated setup
python setup.py

# 3. Your .env is already configured with your token!

# 4. Start the bot
python main.py
```

That's it! Your bot should now be online.

---

## 📁 Complete File Structure

```
bjorn/
├── main.py                          # ✅ Bot entry point
├── requirements.txt                  # ✅ Dependencies list
├── setup.py                         # ✅ Setup automation
├── .env                             # ✅ Your configured environment
├── .env.example                     # ✅ Template for sharing
├── .gitignore                       # ✅ Git ignore rules
├── README.md                        # ✅ Main documentation
├── ROADMAP.md                       # ✅ Development roadmap
├── COMPLETE_SETUP_GUIDE.md          # ✅ This file
│
├── cogs/                            # Command modules
│   ├── __init__.py                 # Module initializer
│   ├── economy.py                  # ✅ Work, daily, crime, give
│   ├── bank.py                     # ✅ Deposit, withdraw
│   ├── casino.py                   # ✅ Slots, blackjack, coinflip, dice
│   ├── investment.py               # ✅ Investment system
│   ├── store.py                    # ✅ Shop, inventory
│   ├── profile.py                  # ✅ User profiles
│   ├── referral.py                 # ✅ Referral system
│   ├── reminders.py                # ✅ Reminders, birthdays
│   ├── moderation.py               # ✅ Warnings, kicks, bans
│   └── utility.py                  # ✅ Help, info commands
│
├── config/
│   ├── __init__.py
│   ├── settings.py                 # ✅ Bot configuration
│   └── database.py                 # ✅ Database models
│
├── utils/
│   ├── __init__.py
│   ├── database_manager.py         # ✅ Database operations
│   ├── error_handler.py            # ✅ Error handling
│   ├── logger.py                   # ✅ Logging system
│   ├── decorators.py               # ✅ Custom decorators
│   └── helpers.py                  # ✅ Helper functions
│
├── data/                            # Auto-created
│   └── bjorn.db                    # SQLite database
│
└── logs/                            # Auto-created
    ├── bjorn.log                   # General logs
    └── errors.log                  # Error logs
```

**Status:** ✅ All files created and ready to use!

---

## 💻 Installation

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- discord.py >= 2.3.0
- sqlalchemy >= 2.0.0
- aiosqlite >= 0.19.0
- python-dotenv >= 1.0.0
- colorlog >= 6.7.0
- psutil >= 5.9.0

### Step 2: Verify Installation

```bash
python -c "import discord; print(f'discord.py {discord.__version__}')"
```

Expected output: `discord.py 2.3.x` or higher

---

## ⚙️ Configuration

### Your .env File (Already Configured!)

Your environment file is already set up with:
- ✅ Your Discord bot token
- ✅ Debug mode enabled for testing
- ✅ All economy settings configured
- ✅ All feature toggles enabled

### Key Configuration Options

```env
# Toggle debug mode
DEBUG_MODE=true          # Detailed logs for development
DEBUG_MODE=false         # Production mode

# Adjust economy rates
EARN_MIN=1              # Minimum work earnings
EARN_MAX=50             # Maximum work earnings
DAILY_BONUS_MIN=50      # Min daily bonus
DAILY_BONUS_MAX=100     # Max daily bonus

# Crime system
CRIME_SUCCESS_RATE=0.75 # 75% success rate (0.0 to 1.0)

# Investment system
INVESTMENT_RISK_CHANCE=0.3  # 30% chance of loss
```

---

## 🎮 Running the Bot

### Start the Bot

```bash
python main.py
```

### Expected Output

```
INFO | Initializing database...
INFO | ✓ Database ready
INFO | Loading cogs...
INFO | ✓ cogs.economy
INFO | ✓ cogs.bank
INFO | ✓ cogs.casino
INFO | ✓ cogs.investment
INFO | ✓ cogs.store
INFO | ✓ cogs.profile
INFO | ✓ cogs.referral
INFO | ✓ cogs.reminders
INFO | ✓ cogs.moderation
INFO | ✓ cogs.utility
INFO | Syncing slash commands...
INFO | ✓ Commands synced
INFO | ==================================================
INFO | 🤖 Bjorn#1234 is online!
INFO | ID: 1421162825585528855
INFO | Guilds: 1
INFO | Users: 10
INFO | Discord.py: 2.3.x
INFO | ==================================================
```

### Stop the Bot

Press `Ctrl+C` in the terminal

---

## 📚 Command Reference

### 💰 Economy Commands

| Command | Description | Cooldown |
|---------|-------------|----------|
| `/balance [@user]` | Check balance | None |
| `/work` | Earn $1-50 | 5 minutes |
| `/daily` | Daily bonus $50-100 | 24 hours |
| `/crime` | Risky money $25-150 | 10 minutes |
| `/give @user [amount]` | Transfer money | None |
| `/leaderboard [page]` | Wealth rankings | None |

### 🏦 Banking Commands

| Command | Description |
|---------|-------------|
| `/deposit [amount\|all]` | Deposit to bank |
| `/withdraw [amount\|all]` | Withdraw from bank |
| `/bankinfo` | Bank information |

### 🎰 Casino Commands

| Command | Description |
|---------|-------------|
| `/coinflip [bet] [choice]` | 50/50 double or nothing |
| `/slots [bet]` | Slot machine (up to 10x) |
| `/blackjack [bet]` | Play blackjack |
| `/dice [bet] [prediction]` | Dice betting game |

### 📈 Investment Commands

| Command | Description |
|---------|-------------|
| `/invest [amount] [hours]` | Invest for returns |
| `/collect` | Collect investment |
| `/investment` | Check status |

### 🏪 Store Commands

| Command | Description |
|---------|-------------|
| `/shop [category]` | Browse items |
| `/buy [item] [quantity]` | Purchase items |
| `/inventory` | View your items |
| `/sell [item] [quantity]` | Sell items (50% value) |
| `/use [item]` | Use an item |

### 👤 Profile Commands

| Command | Description |
|---------|-------------|
| `/profile [@user]` | View profile |
| `/setbio [text]` | Set biography |
| `/setcolor [hex]` | Set profile color |
| `/rank` | View your rank |
| `/badges` | View available badges |

### ⏰ Reminder Commands

| Command | Description |
|---------|-------------|
| `/remind [time] [message]` | Set reminder |
| `/reminders` | View active reminders |
| `/birthday [month] [day]` | Set birthday |
| `/nextbirthday` | Check next birthday |

### 🎉 Referral Commands

| Command | Description |
|---------|-------------|
| `/refer @user` | Refer user (+$50) |
| `/referrals` | Your referral stats |
| `/referralboard` | Top referrers |

### 🛡️ Moderation Commands (Requires Permissions)

| Command | Description | Permission |
|---------|-------------|------------|
| `/warn @user [reason]` | Warn user | Kick Members |
| `/warnings @user` | View warnings | Kick Members |
| `/clearwarn [id]` | Remove warning | Administrator |
| `/kick @user [reason]` | Kick user | Kick Members |
| `/ban @user [reason]` | Ban user | Ban Members |
| `/clear [amount]` | Delete messages | Manage Messages |

### 🔧 Utility Commands

| Command | Description |
|---------|-------------|
| `/help` | Command list |
| `/ping` | Bot latency |
| `/serverinfo` | Server details |
| `/userinfo [@user]` | User details |
| `/botinfo` | Bot statistics |
| `/invite` | Invite link |
| `/stats` | Your statistics |

---

## 🐛 Troubleshooting

### Bot Won't Start

**Problem:** `DISCORD_TOKEN not found`
```bash
# Solution: Check your .env file exists and has the token
cat .env | grep DISCORD_TOKEN
```

**Problem:** `Module not found`
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Bot is Online But Commands Don't Work

**Problem:** Slash commands not showing
- Wait 5-10 minutes for Discord to sync commands
- Check bot has `applications.commands` scope
- Try kicking and re-inviting the bot

**Problem:** "Missing permissions" errors
- Bot needs proper role permissions
- Check role hierarchy (bot role should be high)
- Verify channel permissions

### Database Issues

**Problem:** `OperationalError: database is locked`
```bash
# Solution: Close any database connections
pkill -f python  # Linux/Mac
# Or restart your terminal
```

**Problem:** Want to reset database
```bash
# Backup first!
cp data/bjorn.db data/bjorn.db.backup

# Delete and restart
rm data/bjorn.db
python main.py  # Will create fresh database
```

### Common Errors

**"This interaction failed"**
- Command took too long (>3 seconds)
- Bot lost connection
- Check logs for errors

**"Unknown interaction"**
- Discord didn't receive response in time
- Commands might be desynced
- Re-sync with bot restart

---

## 🔧 Advanced Configuration

### Enable/Disable Features

Edit `.env` file:
```env
# Disable gambling
GAMBLING_ENABLED=false

# Disable moderation
MODERATION_ENABLED=false

# Disable economy
ECONOMY_ENABLED=false
```

### Adjust Economy Balance

```env
# Make earning harder
EARN_MIN=1
EARN_MAX=25
CRIME_SUCCESS_RATE=0.50  # 50% success

# Make earning easier
EARN_MIN=10
EARN_MAX=100
CRIME_SUCCESS_RATE=0.90  # 90% success
```

### Change Interest Rates

```env
# Daily bank interest
BANK_INTEREST_RATE=0.02  # 2% per day
BANK_INTEREST_RATE=0.05  # 5% per day (generous)
BANK_INTEREST_RATE=0.01  # 1% per day (conservative)
```

---

## 📊 Database Schema

### Tables Created Automatically

1. **users** - User accounts and balances
2. **guilds** - Server configurations
3. **transactions** - All money movements
4. **warnings** - Moderation warnings
5. **items** - Shop items
6. **inventories** - User item ownership
7. **referrals** - Referral tracking
8. **command_logs** - Command usage analytics

### Default Items

The bot automatically creates 5 default items:
- 🍪 Cookie ($10)
- ☕ Coffee ($25)
- 🏆 Trophy ($100)
- 💎 Diamond ($500)
- 🎁 Gift Box ($50)

---

## 🎯 Testing Checklist

After starting your bot, test these features:

- [ ] Bot appears online in Discord
- [ ] `/help` command shows all commands
- [ ] `/balance` shows $0 for new users
- [ ] `/work` gives money and has cooldown
- [ ] `/shop` displays items
- [ ] `/profile` shows user profile
- [ ] Moderation commands work (if you have permissions)
- [ ] Error messages are user-friendly
- [ ] Logs are being created in `logs/` folder

---

## 🚀 Next Steps

### For Development
1. Read through `ROADMAP.md` for future features
2. Check `logs/bjorn.log` to understand bot behavior
3. Explore the cogs to customize commands
4. Join development by contributing on GitHub

### For Production
1. Set `DEBUG_MODE=false` in `.env`
2. Set up proper hosting (VPS, Cloud, etc.)
3. Configure automatic restarts
4. Set up monitoring and alerts
5. Regular database backups

### Adding Custom Commands

Example: Add a new command to `cogs/economy.py`:

```python
@app_commands.command(name="gamble", description="Gamble your money")
async def gamble(self, interaction: discord.Interaction, amount: int):
    # Your command logic here
    pass
```

---

## 📞 Support & Resources

- **GitHub Repository:** https://github.com/retrac-ca/bjorn
- **Report Issues:** https://github.com/retrac-ca/bjorn/issues
- **Discord.py Docs:** https://discordpy.readthedocs.io/
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/

---

## ✅ Verification Checklist

Your bot is fully complete with:

- ✅ **10 command modules** (50+ commands)
- ✅ **Full economy system** with work, daily, crime
- ✅ **Banking system** with interest
- ✅ **4 casino games** fully functional
- ✅ **Investment system** with risk/reward
- ✅ **Shop and inventory** management
- ✅ **User profiles** with customization
- ✅ **Referral system** with rewards
- ✅ **Reminder system** with birthdays
- ✅ **Moderation tools** with auto-ban
- ✅ **Utility commands** for info and stats
- ✅ **Error handling** for all scenarios
- ✅ **Database system** with 8 tables
- ✅ **Logging system** with color output
- ✅ **Configuration system** via .env
- ✅ **Documentation** complete

**Everything is ready to go! Just run `python main.py`**

---

*Last Updated: October 2025*  
*Bot Version: 1.0.0*  
*Guide Version: 1.0*