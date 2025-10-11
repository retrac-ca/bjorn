"""
Error Handler

This module provides centralized error handling for the Saint Toadle bot.
It handles command errors, event errors, and provides user-friendly error messages.
"""

import traceback
from typing import Any, Optional
from datetime import datetime, timezone

import discord
from discord.ext import commands

from utils.logger import get_logger, get_context_logger


class ErrorHandler:
    """
    Centralized error handler for the Saint Toadle bot.
    
    This class manages all error handling including command errors,
    event errors, and provides appropriate responses to users.
    """
    
    def __init__(self, bot):
        """
        Initialize the error handler.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
        self.logger = get_logger(__name__)
    
    async def handle_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """
        Handle command errors and provide appropriate responses.
        
        Args:
            ctx: The command context
            error: The error that occurred
        """
        # Get context logger with user and guild information
        context_logger = get_context_logger(
            __name__,
            user_id=ctx.author.id,
            guild_id=ctx.guild.id if ctx.guild else None,
            command=ctx.command.name if ctx.command else 'unknown'
        )
        
        # Ignore certain errors that are handled elsewhere
        if hasattr(ctx.command, 'on_error'):
            return
        
        # Extract the original error if it's wrapped
        error = getattr(error, 'original', error)
        
        # Handle specific error types
        if isinstance(error, commands.CommandNotFound):
            # Silently ignore command not found errors
            return
        
        elif isinstance(error, commands.DisabledCommand):
            await self._send_error_embed(
                ctx,
                "Command Disabled",
                f"The command `{ctx.command}` is currently disabled.",
                color=0xFFA500
            )
            context_logger.warning(f"Disabled command attempted: {ctx.command}")
        
        elif isinstance(error, commands.NoPrivateMessage):
            await self._send_error_embed(
                ctx,
                "Server Only Command",
                "This command can only be used in a server, not in DMs.",
                color=0xFFA500
            )
        
        elif isinstance(error, commands.PrivateMessageOnly):
            await self._send_error_embed(
                ctx,
                "DM Only Command", 
                "This command can only be used in DMs.",
                color=0xFFA500
            )
        
        elif isinstance(error, commands.MissingPermissions):
            perms = ', '.join(error.missing_permissions)
            await self._send_error_embed(
                ctx,
                "Missing Permissions",
                f"You need the following permissions to use this command: `{perms}`",
                color=0xFF0000
            )
        
        elif isinstance(error, commands.BotMissingPermissions):
            perms = ', '.join(error.missing_permissions)
            await self._send_error_embed(
                ctx,
                "Bot Missing Permissions",
                f"I need the following permissions to execute this command: `{perms}`",
                color=0xFF0000
            )
        
        elif isinstance(error, commands.MissingRequiredArgument):
            await self._send_error_embed(
                ctx,
                "Missing Argument",
                f"Missing required argument: `{error.param.name}`\n"
                f"Usage: `{ctx.prefix}{ctx.command} {ctx.command.signature}`",
                color=0xFFA500
            )
        
        elif isinstance(error, commands.BadArgument):
            await self._send_error_embed(
                ctx,
                "Invalid Argument",
                f"Invalid argument provided.\n"
                f"Usage: `{ctx.prefix}{ctx.command} {ctx.command.signature}`",
                color=0xFFA500
            )
        
        elif isinstance(error, commands.CommandOnCooldown):
            retry_after = round(error.retry_after, 2)
            await self._send_error_embed(
                ctx,
                "Command on Cooldown",
                f"This command is on cooldown. Try again in `{retry_after}` seconds.",
                color=0xFFA500
            )
        
        elif isinstance(error, commands.MaxConcurrencyReached):
            await self._send_error_embed(
                ctx,
                "Command Busy",
                f"This command is already running. Please wait for it to finish.",
                color=0xFFA500
            )
        
        elif isinstance(error, discord.Forbidden):
            await self._send_error_embed(
                ctx,
                "Permission Error",
                "I don't have permission to perform this action.",
                color=0xFF0000
            )
        
        elif isinstance(error, discord.NotFound):
            await self._send_error_embed(
                ctx,
                "Not Found",
                "The requested resource could not be found.",
                color=0xFF0000
            )
        
        elif isinstance(error, discord.HTTPException):
            await self._send_error_embed(
                ctx,
                "Discord API Error",
                "An error occurred while communicating with Discord. Please try again.",
                color=0xFF0000
            )
            context_logger.error(f"Discord HTTP error: {error}")
        
        else:
            # Log unexpected errors
            context_logger.error(f"Unexpected error in command {ctx.command}: {error}")
            context_logger.error(traceback.format_exc())
            
            # Send generic error message to user
            await self._send_error_embed(
                ctx,
                "Unexpected Error",
                "An unexpected error occurred. The developers have been notified.",
                color=0xFF0000
            )
            
            # Log command to database if available
            if hasattr(self.bot, 'db') and self.bot.db:
                try:
                    await self.bot.db.log_command(
                        user_id=ctx.author.id,
                        guild_id=ctx.guild.id if ctx.guild else None,
                        command_name=ctx.command.name if ctx.command else 'unknown',
                        success=False,
                        error_message=str(error)[:500]  # Truncate long errors
                    )
                except Exception as db_error:
                    context_logger.error(f"Failed to log command error to database: {db_error}")
    
    async def handle_event_error(self, event: str, *args, **kwargs) -> None:
        """
        Handle errors that occur in event listeners.
        
        Args:
            event: Name of the event where error occurred
            *args: Event arguments
            **kwargs: Event keyword arguments
        """
        error_info = traceback.format_exc()
        
        self.logger.error(f"Error in event {event}: {error_info}")
        
        # Additional logging for specific events
        if event == 'on_message' and args:
            message = args[0]
            if hasattr(message, 'author') and hasattr(message, 'guild'):
                context_logger = get_context_logger(
                    __name__,
                    user_id=message.author.id,
                    guild_id=message.guild.id if message.guild else None,
                    event=event
                )
                context_logger.error(f"Message event error: {error_info}")
    
    async def _send_error_embed(self, ctx: commands.Context, title: str, 
                              description: str, color: int = 0xFF0000) -> None:
        """
        Send an error embed to the user.
        
        Args:
            ctx: Command context
            title: Error title
            description: Error description
            color: Embed color
        """
        try:
            embed = discord.Embed(
                title=f"❌ {title}",
                description=description,
                color=color,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Add command information if available
            if ctx.command:
                embed.set_footer(text=f"Command: {ctx.command.name}")
            
            await ctx.send(embed=embed, delete_after=30)  # Auto-delete after 30 seconds
            
        except discord.Forbidden:
            # Try to send a plain text message if embeds are not allowed
            try:
                await ctx.send(f"❌ **{title}**: {description}")
            except discord.Forbidden:
                # If we can't send messages at all, try to DM the user
                try:
                    await ctx.author.send(f"❌ **{title}**: {description}")
                except discord.Forbidden:
                    # Last resort: log that we couldn't notify the user
                    self.logger.warning(f"Could not send error message to user {ctx.author.id}")
        
        except Exception as e:
            self.logger.error(f"Failed to send error embed: {e}")


class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass


class EconomyError(Exception):
    """Custom exception for economy-related errors."""
    pass


class InsufficientFundsError(EconomyError):
    """Exception raised when user has insufficient funds."""
    pass


class InvalidAmountError(EconomyError):
    """Exception raised when an invalid amount is provided."""
    pass


class UserNotFoundError(Exception):
    """Exception raised when a user is not found."""
    pass


class ItemNotFoundError(Exception):
    """Exception raised when an item is not found."""
    pass


class PermissionError(Exception):
    """Custom exception for permission-related errors.""" 
    pass