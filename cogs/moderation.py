"""
Moderation Commands - Server management and moderation tools
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from utils.logger import get_logger


class ModerationCog(commands.Cog, name="Moderation"):
    """Moderation tools for server management"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)

    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.describe(
        user="User to warn",
        reason="Reason for warning"
    )
    @app_commands.default_permissions(kick_members=True)
    @app_commands.checks.has_permissions(kick_members=True)
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        """Issue a warning to a user"""
        if user.bot:
            await interaction.response.send_message("❌ You can't warn bots!", ephemeral=True)
            return

        if user.id == interaction.user.id:
            await interaction.response.send_message("❌ You can't warn yourself!", ephemeral=True)
            return

        if user.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ You can't warn users with equal or higher roles!", ephemeral=True)
            return

        # Add warning
        warning_id = await self.bot.db.add_warning(
            user.id,
            interaction.guild.id,
            interaction.user.id,
            reason
        )

        # Get warning count
        warnings = await self.bot.db.get_user_warnings(user.id, interaction.guild.id)
        warning_count = len(warnings)

        embed = discord.Embed(
            title="⚠️ User Warned",
            description=f"{user.mention} has been warned",
            color=discord.Color.orange()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Warning Count", value=f"{warning_count}", inline=True)
        embed.add_field(name="Warning ID", value=f"#{warning_id}", inline=True)
        embed.set_footer(text=f"Moderator: {interaction.user}")

        # Check for auto-ban
        if warning_count >= self.bot.config.auto_ban_threshold:
            try:
                await user.ban(reason=f"Auto-ban: Reached {warning_count} warnings")
                embed.add_field(
                    name="🔨 Auto-Ban",
                    value=f"User automatically banned for reaching {warning_count} warnings",
                    inline=False
                )
            except discord.Forbidden:
                embed.add_field(
                    name="⚠️ Auto-Ban Failed",
                    value="Missing permissions to ban user",
                    inline=False
                )

        # Try to DM user
        try:
            dm_embed = discord.Embed(
                title=f"⚠️ Warning in {interaction.guild.name}",
                description=f"You have been warned by {interaction.user.name}",
                color=discord.Color.orange()
            )
            dm_embed.add_field(name="Reason", value=reason, inline=False)
            dm_embed.add_field(name="Total Warnings", value=f"{warning_count}", inline=True)
            await user.send(embed=dm_embed)
        except:
            pass

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="warnings", description="View warnings for a user")
    @app_commands.describe(user="User to check warnings for")
    @app_commands.checks.has_permissions(kick_members=True)
    async def warnings(self, interaction: discord.Interaction, user: discord.Member):
        """View user's warnings"""
        warnings = await self.bot.db.get_user_warnings(user.id, interaction.guild.id, active_only=False)

        if not warnings:
            await interaction.response.send_message(
                f"{user.mention} has no warnings!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"⚠️ Warnings for {user.display_name}",
            color=discord.Color.orange()
        )

        active_warnings = [w for w in warnings if w.active]
        embed.description = f"**Total:** {len(warnings)} | **Active:** {len(active_warnings)}"

        for warning in warnings[:10]:  # Show latest 10
            moderator = interaction.guild.get_member(warning.moderator_id)
            mod_name = moderator.name if moderator else f"User {warning.moderator_id}"
            
            status = "🟢" if warning.active else "🔴"
            timestamp = f"<t:{int(warning.created_at.timestamp())}:R>"
            
            embed.add_field(
                name=f"{status} Warning #{warning.id}",
                value=f"**Reason:** {warning.reason}\n"
                      f"**Moderator:** {mod_name}\n"
                      f"**Date:** {timestamp}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clearwarn", description="Remove a warning")
    @app_commands.describe(warning_id="Warning ID to remove")
    @app_commands.checks.has_permissions(administrator=True)
    async def clearwarn(self, interaction: discord.Interaction, warning_id: int):
        """Clear a warning"""
        from sqlalchemy import update
        from config.database import Warning
        
        async with self.bot.db.session_factory() as session:
            result = await session.execute(
                update(Warning)
                .where(Warning.id == warning_id)
                .where(Warning.guild_id == interaction.guild.id)
                .values(active=False)
            )
            await session.commit()
            
            if result.rowcount == 0:
                await interaction.response.send_message(
                    "❌ Warning not found!",
                    ephemeral=True
                )
                return

        embed = discord.Embed(
            title="✅ Warning Cleared",
            description=f"Warning #{warning_id} has been deactivated",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.describe(
        user="User to kick",
        reason="Reason for kick"
    )
    @app_commands.default_permissions(kick_members=True)
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        """Kick a user"""
        if user.bot:
            await interaction.response.send_message("❌ You can't kick bots!", ephemeral=True)
            return

        if user.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ You can't kick users with equal or higher roles!", ephemeral=True)
            return

        try:
            # Try to DM user first
            try:
                dm_embed = discord.Embed(
                    title=f"🚪 Kicked from {interaction.guild.name}",
                    description=f"You were kicked by {interaction.user.name}",
                    color=discord.Color.red()
                )
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                await user.send(embed=dm_embed)
            except:
                pass

            await user.kick(reason=f"{interaction.user}: {reason}")

            embed = discord.Embed(
                title="🚪 User Kicked",
                description=f"{user.mention} has been kicked",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Moderator: {interaction.user}")

            await interaction.response.send_message(embed=embed)

        except discord.Forbidden:
            await interaction.response.send_message("❌ Missing permissions to kick this user!", ephemeral=True)

    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.describe(
        user="User to ban",
        reason="Reason for ban",
        delete_messages="Days of messages to delete (0-7)"
    )
    @app_commands.default_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided", delete_messages: int = 0):
        """Ban a user"""
        if user.bot:
            await interaction.response.send_message("❌ You can't ban bots!", ephemeral=True)
            return

        if user.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ You can't ban users with equal or higher roles!", ephemeral=True)
            return

        if not (0 <= delete_messages <= 7):
            await interaction.response.send_message("❌ Delete messages must be between 0-7 days!", ephemeral=True)
            return

        try:
            # Try to DM user first
            try:
                dm_embed = discord.Embed(
                    title=f"🔨 Banned from {interaction.guild.name}",
                    description=f"You were banned by {interaction.user.name}",
                    color=discord.Color.red()
                )
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                await user.send(embed=dm_embed)
            except:
                pass

            await user.ban(reason=f"{interaction.user}: {reason}", delete_message_days=delete_messages)

            embed = discord.Embed(
                title="🔨 User Banned",
                description=f"{user.mention} has been banned",
                color=discord.Color.dark_red()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Moderator: {interaction.user}")

            await interaction.response.send_message(embed=embed)

        except discord.Forbidden:
            await interaction.response.send_message("❌ Missing permissions to ban this user!", ephemeral=True)

    @app_commands.command(name="clear", description="Bulk delete messages")
    @app_commands.describe(amount="Number of messages to delete (1-100)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        """Bulk delete messages"""
        if not (1 <= amount <= 100):
            await interaction.response.send_message(
                "❌ Amount must be between 1-100!",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            deleted = await interaction.channel.purge(limit=amount)
            
            await interaction.followup.send(
                f"✅ Deleted {len(deleted)} messages!",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send("❌ Missing permissions!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ModerationCog(bot))