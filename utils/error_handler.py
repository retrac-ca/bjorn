"""
Error Handler - Centralized error handling for bot commands
"""
import traceback
import discord
from discord import app_commands
from discord.ext import commands

from utils.logger import get_logger


class ErrorHandler:
    """Centralized error handling for bot"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)

    async def handle_command_error(self, ctx, error):
        """Handle command errors"""
        # Get the original error if it's wrapped
        error = getattr(error, 'original', error)

        # Ignore these errors
        ignored = (commands.CommandNotFound,)
        if isinstance(error, ignored):
            return

        # Command on cooldown
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"⏰ This command is on cooldown. Try again in {error.retry_after:.1f}s",
                ephemeral=True
            )
            return

        # Missing permissions
        if isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions)
            await ctx.send(
                f"❌ You need the following permissions: {perms}",
                ephemeral=True
            )
            return

        # Bot missing permissions
        if isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_permissions)
            await ctx.send(
                f"❌ I need the following permissions: {perms}",
                ephemeral=True
            )
            return

        # User input errors
        if isinstance(error, commands.BadArgument):
            await ctx.send(
                f"❌ Invalid argument provided!",
                ephemeral=True
            )
            return

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                f"❌ Missing required argument: {error.param.name}",
                ephemeral=True
            )
            return

        # Log the error
        self.logger.error(f"Command error in {ctx.command}: {error}")
        self.logger.error(traceback.format_exc())

        # Send generic error message
        embed = discord.Embed(
            title="❌ An Error Occurred",
            description="An unexpected error occurred while executing this command.",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Error Type",
            value=type(error).__name__,
            inline=False
        )

        if self.bot.config.debug_mode:
            embed.add_field(
                name="Error Details",
                value=f"```{str(error)[:1000]}```",
                inline=False
            )

        try:
            await ctx.send(embed=embed, ephemeral=True)
        except:
            pass

    async def handle_event_error(self, event, *args, **kwargs):
        """Handle event errors"""
        self.logger.error(f"Error in event {event}")
        self.logger.error(traceback.format_exc())

    async def handle_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle application command errors"""
        # Get the original error if it's wrapped
        error = getattr(error, 'original', error)

        # Command on cooldown
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"⏰ This command is on cooldown. Try again in {error.retry_after:.1f}s",
                ephemeral=True
            )
            return

        # Missing permissions
        if isinstance(error, app_commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions)
            await interaction.response.send_message(
                f"❌ You need the following permissions: {perms}",
                ephemeral=True
            )
            return

        # Check failure
        if isinstance(error, app_commands.CheckFailure):
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ You don't have permission to use this command!",
                    ephemeral=True
                )
            return

        # Log the error
        self.logger.error(f"App command error: {error}")
        self.logger.error(traceback.format_exc())

        # Send error message
        embed = discord.Embed(
            title="❌ An Error Occurred",
            description="An unexpected error occurred while executing this command.",
            color=discord.Color.red()
        )

        if self.bot.config.debug_mode:
            embed.add_field(
                name="Error Details",
                value=f"```{str(error)[:1000]}```",
                inline=False
            )

        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            pass