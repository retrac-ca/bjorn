#!/usr/bin/env python3
"""
Bjorn Discord Bot - Main Entry Point
A comprehensive multi-purpose Discord bot with slash commands
"""
import asyncio
import logging
import sys
import traceback
from pathlib import Path
from datetime import datetime

import discord
from discord.ext import commands
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import BotConfig
from utils.logger import setup_logging, get_logger
from utils.database_manager import DatabaseManager
from utils.error_handler import ErrorHandler


class BjornBot(commands.Bot):
    """Main bot class with slash command support"""

    def __init__(self):
        load_dotenv()
        self.config = BotConfig()
        setup_logging(self.config)
        self.logger = get_logger(__name__)

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.reactions = True
        intents.presences = True

        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            help_command=None
        )

        self.db = None
        self.start_time = None
        self.error_handler = ErrorHandler(self)

    async def setup_database(self):
        """Initialize database connection"""
        try:
            self.logger.info("Setting up database...")
            self.db = DatabaseManager(self.config.database_url)
            await self.db.initialize()
            self.logger.info("✓ Database ready")
        except Exception as e:
            self.logger.error(f"Database setup failed: {e}")
            raise

    async def load_cogs(self):
        """Load all bot cogs"""
        cogs = [
            'cogs.economy',
            'cogs.bank',
            'cogs.investment',
            'cogs.casino',
            'cogs.store',
            'cogs.profile',
            'cogs.referral',
            'cogs.moderation',
            'cogs.utility',
            'cogs.reminders'
        ]

        self.logger.info("Loading cogs...")
        for cog in cogs:
            try:
                await self.load_extension(cog)
                self.logger.debug(f"✓ {cog}")
            except Exception as e:
                self.logger.error(f"✗ {cog}: {e}")

    async def setup_hook(self):
        """Called before bot connects to Discord"""
        try:
            await self.setup_database()
            await self.load_cogs()
            
            # Sync slash commands globally
            self.logger.info("Syncing slash commands...")
            await self.tree.sync()
            self.logger.info("✓ Commands synced")
            
        except Exception as e:
            self.logger.error(f"Setup failed: {e}")
            raise

    async def on_ready(self):
        """Bot is ready and connected"""
        self.start_time = datetime.now()

        self.logger.info("="*50)
        self.logger.info(f"🤖 {self.user} is online!")
        self.logger.info(f"ID: {self.user.id}")
        self.logger.info(f"Guilds: {len(self.guilds)}")
        self.logger.info(f"Users: {len(set(self.get_all_members()))}")
        self.logger.info(f"Discord.py: {discord.__version__}")
        self.logger.info("="*50)

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.guilds)} servers | /help"
            )
        )

    async def on_guild_join(self, guild):
        """Bot joins a new server"""
        self.logger.info(f"Joined: {guild.name} (ID: {guild.id})")
        await self.db.get_guild(guild.id, guild.name)

    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        await self.error_handler.handle_command_error(ctx, error)

    async def close(self):
        """Clean shutdown"""
        self.logger.info("Shutting down...")
        if self.db:
            await self.db.close()
        await super().close()


async def main():
    """Main entry point"""
    bot = BjornBot()
    
    try:
        if not bot.config.discord_token:
            bot.logger.error("DISCORD_TOKEN not found!")
            return
            
        await bot.start(bot.config.discord_token)
        
    except KeyboardInterrupt:
        bot.logger.info("Keyboard interrupt received")
        await bot.close()
    except Exception as e:
        bot.logger.error(f"Fatal error: {e}")
        traceback.print_exc()
        await bot.close()


if __name__ == "__main__":
    if sys.version_info < (3, 8):
        print("Python 3.8+ required!")
        sys.exit(1)

    Path("data").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped")
    except Exception as e:
        print(f"Fatal: {e}")
        sys.exit(1)