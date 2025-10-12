#!/usr/bin/env python3
"""
Bjorn Discord Bot - Main Entry Point (Slash Commands Version)

A comprehensive Discord bot with economy, moderation, and social features.
Built with discord.py slash commands and SQLite database.
"""

import asyncio
import logging
import os
import sys
import traceback
from pathlib import Path
from datetime import datetime, timezone, timedelta

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import BotConfig
from utils.logger import setup_logging, get_logger
from utils.database_manager import DatabaseManager
from utils.error_handler import ErrorHandler


class BjornBot(commands.Bot):
    """
    Main bot class with slash commands support.
    
    This class handles bot initialization, database setup, cog loading,
    and provides centralized access to bot resources with slash commands.
    """
    
    def __init__(self):
        """Initialize the Bjorn bot with slash commands configuration."""
        
        # Load environment variables
        load_dotenv()
        
        # Initialize configuration
        self.config = BotConfig()
        
        # Setup logging system
        setup_logging(self.config)
        self.logger = get_logger(__name__)
        
        # Define bot intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.reactions = True
        
        # Initialize the bot for slash commands
        super().__init__(
            command_prefix=None,  # No prefix needed for slash commands
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        
        # Initialize database manager
        self.db = None
        
        # Store startup time
        self.start_time = None
        
        # Error handler
        self.error_handler = ErrorHandler(self)
        
        self.logger.info("Bjorn Bot (Slash Commands) initialized successfully")
    
    async def setup_database(self):
        """Initialize and setup the database connection."""
        try:
            self.logger.info("Setting up database connection...")
            self.db = DatabaseManager(self.config.database_url)
            await self.db.initialize()
            self.logger.info("Database connection established successfully")
        except Exception as e:
            self.logger.error(f"Failed to setup database: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    async def load_cogs(self):
        """Load all bot cogs (slash command modules)."""
        cogs_to_load = [
            'cogs.economy',
            'cogs.moderation', 
            'cogs.utility',
            'cogs.referral',
            'cogs.marketplace',
            'cogs.profile',
            'cogs.bank',
            'cogs.investment'  # New investment cog
        ]
        
        self.logger.info("Loading slash command cogs...")
        loaded_count = 0
        
        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                self.logger.debug(f"Loaded cog: {cog}")
                loaded_count += 1
            except Exception as e:
                self.logger.error(f"Failed to load cog {cog}: {e}")
                self.logger.error(traceback.format_exc())
        
        self.logger.info(f"Successfully loaded {loaded_count}/{len(cogs_to_load)} cogs")
    
    async def sync_commands(self):
        """Sync slash commands with Discord."""
        try:
            self.logger.info("Syncing slash commands...")
            synced = await self.tree.sync()
            self.logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            self.logger.error(f"Failed to sync commands: {e}")
    
    async def setup_hook(self):
        """Setup hook called by discord.py before connecting."""
        try:
            self.logger.info("Running setup hook...")
            
            # Setup database
            await self.setup_database()
            
            # Load cogs
            await self.load_cogs()
            
            # Sync slash commands
            await self.sync_commands()
            
            # Start daily interest task
            if self.config.daily_interest_enabled:
                self.daily_interest_task.start()
            
            self.logger.info("Setup hook completed successfully")
            
        except Exception as e:
            self.logger.error(f"Setup hook failed: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    @tasks.loop(hours=24)
    async def daily_interest_task(self):
        """Apply daily interest to all bank accounts."""
        try:
            self.logger.info("Running daily interest calculations...")
            
            if not self.db:
                return
            
            # Get all users with bank balances
            users_updated = await self.db.apply_daily_interest(self.config.bank_interest_rate)
            
            self.logger.info(f"Applied daily interest to {users_updated} accounts")
            
        except Exception as e:
            self.logger.error(f"Daily interest task failed: {e}")
    
    @daily_interest_task.before_loop
    async def before_daily_interest(self):
        """Wait until bot is ready before starting interest task."""
        await self.wait_until_ready()
    
    async def on_ready(self):
        """Event triggered when the bot is ready and connected to Discord."""
        self.start_time = datetime.now(timezone.utc)
        
        self.logger.info("="*50)
        self.logger.info(f"Bot is ready! Logged in as {self.user}")
        self.logger.info(f"Bot ID: {self.user.id}")
        self.logger.info(f"Connected to {len(self.guilds)} guilds")
        self.logger.info(f"Watching {len(set(self.get_all_members()))} users")
        self.logger.info(f"Discord.py version: {discord.__version__}")
        self.logger.info("="*50)
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"slash commands | {len(self.guilds)} servers"
        )
        await self.change_presence(activity=activity)
        
        if self.config.debug_mode:
            self.logger.debug("Debug mode is enabled")
        
        self.logger.info("Bjorn Bot (Slash Commands) is now online and ready!")
    
    async def on_guild_join(self, guild):
        """Event triggered when the bot joins a new guild."""
        self.logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
        
        # Sync commands to new guild
        try:
            await self.tree.sync(guild=guild)
            self.logger.info(f"Synced slash commands to {guild.name}")
        except Exception as e:
            self.logger.error(f"Failed to sync commands to {guild.name}: {e}")
        
        # Update bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"slash commands | {len(self.guilds)} servers"
        )
        await self.change_presence(activity=activity)
    
    async def on_guild_remove(self, guild):
        """Event triggered when the bot leaves a guild."""
        self.logger.info(f"Left guild: {guild.name} (ID: {guild.id})")
        
        # Update bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"slash commands | {len(self.guilds)} servers"
        )
        await self.change_presence(activity=activity)
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: Exception):
        """Global slash command error handler."""
        await self.error_handler.handle_slash_command_error(interaction, error)
    
    async def close(self):
        """Clean shutdown of the bot."""
        self.logger.info("Shutting down Bjorn Bot...")
        
        # Stop daily interest task
        if hasattr(self, 'daily_interest_task'):
            self.daily_interest_task.cancel()
        
        # Close database connection
        if self.db:
            await self.db.close()
            self.logger.info("Database connection closed")
        
        # Close the bot connection
        await super().close()
        self.logger.info("Bot shutdown complete")


async def main():
    """Main function to run the bot."""
    
    # Create bot instance
    bot = BjornBot()
    
    try:
        # Verify token exists
        if not bot.config.discord_token:
            bot.logger.error("DISCORD_TOKEN not found in environment variables!")
            bot.logger.error("Please set DISCORD_TOKEN in your .env file")
            return
        
        # Start the bot
        bot.logger.info("Starting Bjorn Bot (Slash Commands)...")
        await bot.start(bot.config.discord_token)
        
    except KeyboardInterrupt:
        bot.logger.info("Received keyboard interrupt, shutting down...")
        await bot.close()
    except Exception as e:
        bot.logger.error(f"Fatal error: {e}")
        bot.logger.error(traceback.format_exc())
        await bot.close()


if __name__ == "__main__":
    """Entry point when running the script directly."""
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or higher is required!")
        sys.exit(1)
    
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
