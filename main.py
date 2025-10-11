#!/usr/bin/env python3
"""
Bjorn Discord Bot - Main Entry Point

A comprehensive Discord bot with economy, moderation, and social features.
Built with discord.py and SQLite database.

Author: Bjorn Development Team
License: MIT
"""
import asyncio
import logging
import os
import sys
import traceback
from pathlib import Path

import discord
from discord.ext import commands
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
    Main bot class that extends discord.py's Bot class.

    This class handles bot initialization, database setup, cog loading,
    and provides centralized access to bot resources.
    """

    def __init__(self):
        """Initialize the Bjorn bot with configuration and intents."""

        # Load environment variables
        load_dotenv()

        # Initialize configuration
        self.config = BotConfig()

        # Setup logging system
        setup_logging(self.config)
        self.logger = get_logger(__name__)

        # Define bot intents (permissions the bot needs)
        intents = discord.Intents.default()
        intents.message_content = True  # Required for reading message content
        intents.members = True          # Required for member events
        intents.guilds = True           # Required for guild events
        intents.reactions = True        # Required for reaction events

        # Initialize the bot with configuration
        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            help_command=None,  # We'll create a custom help command
            case_insensitive=True,
            strip_after_prefix=True
        )

        # Initialize database manager
        self.db = None

        # Store startup time
        self.start_time = None

        # Error handler
        self.error_handler = ErrorHandler(self)

        self.logger.info("Bjorn Bot initialized successfully")

    async def get_prefix(self, message):
        """
        Get the command prefix for a message.

        This function allows for per-guild prefixes in the future.
        Currently returns the default prefix from configuration.

        Args:
            message: The Discord message object

        Returns:
            str: The command prefix to use
        """
        # TODO: Implement per-guild prefix support
        return self.config.bot_prefix

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
        """Load all bot cogs (command modules)."""
        cogs_to_load = [
            'cogs.economy',
            'cogs.moderation',
            'cogs.utility',
            'cogs.referral',
            'cogs.marketplace',
            'cogs.profile',
            'cogs.bank'
        ]

        self.logger.info("Loading cogs...")
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

    async def setup_hook(self):
        """
        Setup hook called by discord.py before connecting.

        This is where we perform all initialization that needs to happen
        before the bot starts receiving events.
        """
        try:
            self.logger.info("Running setup hook...")

            # Setup database
            await self.setup_database()

            # Load cogs
            await self.load_cogs()

            self.logger.info("Setup hook completed successfully")

        except Exception as e:
            self.logger.error(f"Setup hook failed: {e}")
            self.logger.error(traceback.format_exc())
            raise

    async def on_ready(self):
        """Event triggered when the bot is ready and connected to Discord."""
        import datetime

        self.start_time = datetime.datetime.now()

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
            name=f"{self.config.bot_prefix}help | {len(self.guilds)} servers"
        )
        await self.change_presence(activity=activity)

        # Log additional startup information
        if self.config.debug_mode:
            self.logger.debug("Debug mode is enabled")

        self.logger.info("Bjorn Bot is now online and ready!")

    async def on_guild_join(self, guild):
        """Event triggered when the bot joins a new guild."""
        self.logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")

        # Update bot status with new guild count
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{self.config.bot_prefix}help | {len(self.guilds)} servers"
        )
        await self.change_presence(activity=activity)

    async def on_guild_remove(self, guild):
        """Event triggered when the bot leaves a guild."""
        self.logger.info(f"Left guild: {guild.name} (ID: {guild.id})")

        # Update bot status with new guild count
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{self.config.bot_prefix}help | {len(self.guilds)} servers"
        )
        await self.change_presence(activity=activity)

    async def on_command(self, ctx):
        """Event triggered when a command is invoked."""
        self.logger.debug(
            f"Command '{ctx.command}' invoked by {ctx.author} "
            f"in {ctx.guild.name if ctx.guild else 'DM'}"
        )

    async def on_command_completion(self, ctx):
        """Event triggered when a command completes successfully."""
        self.logger.debug(f"Command '{ctx.command}' completed successfully")

    async def on_command_error(self, ctx, error):
        """Global command error handler."""
        await self.error_handler.handle_command_error(ctx, error)

    async def on_error(self, event, *args, **kwargs):
        """Global error handler for events."""
        await self.error_handler.handle_event_error(event, *args, **kwargs)

    async def close(self):
        """Clean shutdown of the bot."""
        self.logger.info("Shutting down Bjorn Bot...")

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
        bot.logger.info("Starting Bjorn Bot...")
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
