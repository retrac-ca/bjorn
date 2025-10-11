"""
Referral Commands Cog

This module contains referral system commands for the Saint Toadle bot.
"""

import discord
from discord.ext import commands

from utils.decorators import requires_economy, log_command_usage, guild_only
from utils.logger import get_logger


class ReferralCog(commands.Cog, name="Referral"):
    """Referral system commands cog."""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)
    
    @commands.command(name='refer', help="Refer a friend to earn bonuses")
    @guild_only
    @requires_economy
    @log_command_usage
    async def refer_user(self, ctx: commands.Context):
        """Refer a user to earn referral bonuses."""
        # TODO: Implement referral system
        embed = discord.Embed(
            title="🔗 Referral System",
            description="Referral system coming soon!",
            color=self.bot.config.get_embed_color()
        )
        await ctx.send(embed=embed)


async def setup(bot):
    """Load the Referral cog."""
    await bot.add_cog(ReferralCog(bot))