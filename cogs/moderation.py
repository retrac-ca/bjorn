"""
Moderation Commands Cog

This module contains moderation-related slash commands for the Bjorn bot,
including warnings, kicking, banning, and clearing messages.
"""

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from utils.logger import get_logger
from utils.helpers import format_time_delta
from utils.decorators import requires_moderator, log_command_usage


class ModerationCog(commands.Cog, name="Moderation"):
    """
    Moderation cog with slash commands.

    This cog provides moderation functionality including warnings,
    kicks, bans, message clearing, and moderation logs.
    """

    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)

    @app_commands.command(name="warn", description="Warn a user with a reason")
    @app_commands.describe(member="Member to warn", reason="Reason for warning")
    @requires_moderator()
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        """
        Add a warning to the specified member for the given reason.
        """
        if member.bot:
            await interaction.response.send_message("You cannot warn bots.", ephemeral=True)
            return

        warning_id = await self.bot.db.add_warning(
            user_id=member.id,
            guild_id=interaction.guild.id if interaction.guild else None,
            moderator_id=interaction.user.id,
            reason=reason
        )

        await interaction.response.send_message(
            f"{member.mention} has been warned for: {reason}\nWarning ID: {warning_id}"
        )

        # Optionally check warning count and auto-ban if threshold exceeded
        warnings = await self.bot.db.get_user_warnings(member.id, interaction.guild.id)
        active_warning_count = sum(1 for w in warnings if w.active)
        if active_warning_count >= self.bot.config.auto_ban_threshold:
            try:
                await member.ban(reason=f"Auto-ban: {active_warning_count} warnings")
                await interaction.channel.send(f"{member.mention} has been banned automatically due to excessive warnings.")
            except discord.Forbidden:
                await interaction.channel.send(f"Failed to ban {member.mention} due to insufficient permissions.")

    @app_commands.command(name="warnings", description="View warnings for a user")
    @app_commands.describe(member="User to view warnings for")
    async def warnings(self, interaction: discord.Interaction, member: discord.Member = None):
        """
        View all warnings for a user in the current guild.
        """
        member = member or interaction.user
        warnings = await self.bot.db.get_user_warnings(member.id, interaction.guild.id)

        if not warnings:
            await interaction.response.send_message(f"{member.mention} has no warnings.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Warnings for {member.display_name}",
            color=self.bot.config.get_warning_color()
        )

        for warning in warnings[:10]:  # Show up to 10
            created = warning.created_at.strftime("%Y-%m-%d %H:%M UTC")
            status = "Active" if warning.active else "Expired"
            embed.add_field(
                name=f"ID: {warning.id} | {status}",
                value=f"Reason: {warning.reason}\nDate: {created}",
                inline=False
            )

        if len(warnings) > 10:
            embed.set_footer(text=f"Showing 10 of {len(warnings)} warnings")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.describe(member="Member to kick", reason="Reason for kick")
    @requires_moderator()
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        """
        Kick a member with optional reason.
        """
        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(f"{member.mention} has been kicked.\nReason: {reason or 'No reason specified'}")
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to kick that member.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to kick member: {e}", ephemeral=True)

    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.describe(member="Member to ban", reason="Reason for ban")
    @requires_moderator()
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        """
        Ban a member with optional reason.
        """
        try:
            await member.ban(reason=reason)
            await interaction.response.send_message(f"{member.mention} has been banned.\nReason: {reason or 'No reason specified'}")
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to ban that member.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to ban member: {e}", ephemeral=True)

    @app_commands.command(name="clear", description="Bulk delete messages")
    @app_commands.describe(limit="Number of messages to delete (max 100)")
    @requires_moderator()
    async def clear(self, interaction: discord.Interaction, limit: int):
        """
        Delete the specified number of messages from the channel.
        """
        if limit < 1 or limit > 100:
            await interaction.response.send_message("Please provide a number between 1 and 100.", ephemeral=True)
            return
        
        deleted = await interaction.channel.purge(limit=limit)
        await interaction.response.send_message(f"Deleted {len(deleted)} messages.", ephemeral=True)


async def setup(bot):
    """Load the Moderation cog."""
    await bot.add_cog(ModerationCog(bot))
