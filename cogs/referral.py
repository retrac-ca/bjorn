"""
Referral Commands Cog

This module contains referral-related slash commands for the Bjorn bot.
Basic structure ready for expansion.
"""

import discord
from discord import app_commands
from discord.ext import commands

from utils.logger import get_logger
from utils.helpers import format_currency
from utils.decorators import log_command_usage


class ReferralCog(commands.Cog, name="Referral"):
    """
    Referral cog with slash commands.
    
    Basic structure for referral system.
    """

    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)

    @app_commands.command(name="referrals", description="View your referral statistics")
    async def referrals(self, interaction: discord.Interaction):
        """
        Display referral statistics for the user.
        """
        # This is a placeholder - implement referral tracking
        embed = discord.Embed(
            title="🔗 Referral System",
            description="Referral system coming soon! Invite friends to earn bonus coins.",
            color=self.bot.config.get_embed_color()
        )

        embed.add_field(
            name="📊 Your Stats",
            value="Referrals: 0\nBonus Earned: $0\nTotal Invites: 0",
            inline=False
        )

        embed.add_field(
            name="💡 How it works",
            value="• Invite friends to the server\n• Get bonus coins when they join\n• More features coming soon!",
            inline=False
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    """Load the Referral cog."""
    await bot.add_cog(ReferralCog(bot))
