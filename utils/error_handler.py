"""
Error Handler

This module provides centralized error handling for the Bjorn bot,
including both traditional commands and slash commands.
"""

import traceback
from datetime import datetime, timezone

import discord
from discord.ext import commands

from utils.logger import get_logger


class ErrorHandler:
    """
    Centralized error handler for the Bjorn bot.
    
    Handles errors from both traditional commands and slash commands.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)
    
    async def handle_slash_command_error(self, interaction: discord.Interaction, error: Exception):
        """
        Handle errors that occur during slash command execution.
        
        Args:
            interaction: The Discord interaction that caused the error
            error: The exception that occurred
        """
        
        self.logger.error(f"Slash command error in {interaction.command.name if interaction.command else 'unknown'}: {error}")
        self.logger.error(traceback.format_exc())
        
        # Create error embed
        embed = discord.Embed(
            title="❌ Command Error",
            color=self.bot.config.get_error_color(),
            timestamp=datetime.now(timezone.utc)
        )
        
        if isinstance(error, commands.CommandOnCooldown):
            embed.description = f"This command is on cooldown. Try again in {error.retry_after:.1f} seconds."
        elif isinstance(error, commands.MissingPermissions):
            embed.description = "You don't have permission to use this command."
        elif isinstance(error, commands.BotMissingPermissions):
            embed.description = "I don't have the required permissions to execute this command."
        elif isinstance(error, commands.MemberNotFound):
            embed.description = "Could not find the specified member."
        elif isinstance(error, commands.BadArgument):
            embed.description = "Invalid argument provided. Please check your input and try again."
        else:
            embed.description = "An unexpected error occurred while processing your command."
            embed.add_field(
                name="Error Details",
                value=f"``````",
                inline=False
            )
        
        embed.set_footer(text="If this error persists, please contact the bot developers.")
        
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            self.logger.error(f"Failed to send error message: {e}")
    
    async def handle_command_error(self, ctx: commands.Context, error: Exception):
        """
        Handle errors from traditional prefix commands (if any remain).
        
        Args:
            ctx: Command context
            error: The exception that occurred
        """
        
        self.logger.error(f"Command error in {ctx.command}: {error}")
        self.logger.error(traceback.format_exc())
        
        # Create error embed
        embed = discord.Embed(
            title="❌ Command Error",
            color=self.bot.config.get_error_color(),
            timestamp=datetime.now(timezone.utc)
        )
        
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
        elif isinstance(error, commands.CommandOnCooldown):
            embed.description = f"This command is on cooldown. Try again in {error.retry_after:.1f} seconds."
        elif isinstance(error, commands.MissingRequiredArgument):
            embed.description = f"Missing required argument: `{error.param.name}`"
        elif isinstance(error, commands.BadArgument):
            embed.description = "Invalid argument provided. Please check your input and try again."
        else:
            embed.description = "An unexpected error occurred while processing your command."
        
        try:
            await ctx.send(embed=embed)
        except Exception as e:
            self.logger.error(f"Failed to send error message: {e}")
    
    async def handle_event_error(self, event: str, *args, **kwargs):
        """
        Handle errors from event handlers.
        
        Args:
            event: Name of the event that caused the error
            *args: Event arguments
            **kwargs: Event keyword arguments
        """
        
        self.logger.error(f"Event error in {event}")
        self.logger.error(traceback.format_exc())
