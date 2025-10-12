"""
Utility Commands Cog

This module contains utility-related slash commands for the Bjorn bot,
including help, ping, server info, user info, and bot stats.
"""

import platform
import time
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands
import psutil

from utils.logger import get_logger
from utils.helpers import format_time_delta
from utils.decorators import log_command_usage


class UtilityCog(commands.Cog, name="Utility"):
    """
    Utility cog with slash commands.

    Provides help, ping, server information, user information, and bot info commands.
    """

    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)

    @app_commands.command(name="help", description="Show help information")
    @log_command_usage
    async def help(self, interaction: discord.Interaction):
        """
        Send an embed listing available slash commands.
        """
        commands_list = self.bot.tree.get_commands()

        embed = discord.Embed(
            title=f"{self.bot.config.bot_name} Help",
            description="Here are the available slash commands:",
            color=self.bot.config.get_embed_color()
        )

        for cmd in commands_list:
            # skip subcommands
            if cmd.parent:
                continue
            name = f"/{cmd.name}"
            desc = cmd.description or "No description"
            embed.add_field(name=name, value=desc, inline=False)

        embed.set_footer(text=f"Requested by {interaction.user.display_name}",
                         icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ping", description="Check bot latency and response time")
    @log_command_usage
    async def ping(self, interaction: discord.Interaction):
        """
        Check latency and uptime of the bot.
        """
        start_time = time.perf_counter()
        await interaction.response.defer(ephemeral=True)
        end_time = time.perf_counter()

        websocket_latency = self.bot.latency * 1000  # ms
        response_time = (end_time - start_time) * 1000  # ms

        embed = discord.Embed(
            title="🏓 Pong!",
            description=(
                f"**WebSocket latency:** {websocket_latency:.1f}ms\n"
                f"**Response time:** {response_time:.1f}ms"
            ),
            color=self.bot.config.get_embed_color()
        )
        embed.set_footer(text="Lower is better!")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="serverinfo", description="Show information about this server")
    @log_command_usage
    async def serverinfo(self, interaction: discord.Interaction):
        """
        Display detailed information about the current guild/server.
        """
        guild = interaction.guild
        embed = discord.Embed(
            title=f"🏰 {guild.name} Information",
            color=self.bot.config.get_embed_color(),
            timestamp=datetime.now(timezone.utc)
        )

        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(
            name="Created At",
            value=f"<t:{int(guild.created_at.timestamp())}:F>",
            inline=True
        )
        embed.add_field(name="Locale", value=guild.preferred_locale, inline=True)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Show info about a user")
    @app_commands.describe(member="User to show info for")
    @log_command_usage
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        """
        Show detailed info about a user.
        """
        member = member or interaction.user
        embed = discord.Embed(
            title=f"👤 {member.display_name}",
            color=(
                member.color
                if member.color != discord.Color.default()
                else self.bot.config.get_embed_color()
            ),
            timestamp=datetime.now(timezone.utc)
        )

        embed.add_field(name="User ID", value=member.id, inline=True)
        embed.add_field(
            name="Account Created",
            value=f"<t:{int(member.created_at.timestamp())}:F>",
            inline=True
        )
        if member.joined_at:
            embed.add_field(
                name="Joined Server",
                value=f"<t:{int(member.joined_at.timestamp())}:F>",
                inline=True
            )
        embed.set_thumbnail(url=member.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="botinfo", description="Show information about the bot")
    @log_command_usage
    async def info(self, interaction: discord.Interaction):
        """
        Show bot information and stats.
        """
        embed = discord.Embed(
            title=f"🤖 {self.bot.user.name} Information",
            description="A comprehensive Discord bot with economy, moderation, and social features.",
            color=self.bot.config.get_embed_color(),
            timestamp=datetime.now(timezone.utc)
        )

        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(
            name="Users", value=str(len(set(self.bot.get_all_members()))), inline=True
        )
        embed.add_field(
            name="Commands", value=str(len(self.bot.tree.get_commands())), inline=True
        )

        embed.add_field(name="Python", value=platform.python_version(), inline=True)
        embed.add_field(name="Discord.py", value=discord.__version__, inline=True)
        uptime = (
            format_time_delta(datetime.now(timezone.utc) - self.bot.start_time)
            if self.bot.start_time
            else "Unknown"
        )
        embed.add_field(name="Uptime", value=uptime, inline=True)

        try:
            process = psutil.Process()
            mem = process.memory_info().rss / 1024 / 1024  # MB
            cpu = process.cpu_percent()
            embed.add_field(name="Memory", value=f"{mem:.1f} MB", inline=True)
            embed.add_field(name="CPU", value=f"{cpu:.1f}%", inline=True)
        except Exception:
            pass

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    """Load Utility cog."""
    await bot.add_cog(UtilityCog(bot))
