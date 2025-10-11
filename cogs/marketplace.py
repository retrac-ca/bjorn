"""
Marketplace Commands Cog

This module contains marketplace commands for the Saint Toadle bot.
"""

import discord
from discord.ext import commands

from utils.decorators import requires_economy, log_command_usage, require_database
from utils.logger import get_logger


class MarketplaceCog(commands.Cog, name="Marketplace"):
    """Marketplace commands cog."""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)
    
    @commands.command(name='shop', aliases=['store'], help="View the marketplace")
    @require_database
    @requires_economy
    @log_command_usage
    async def view_shop(self, ctx: commands.Context):
        """View available items in the marketplace."""
        # TODO: Implement marketplace system
        embed = discord.Embed(
            title="🏪 Marketplace",
            description="Marketplace system coming soon!",
            color=self.bot.config.get_embed_color()
        )
        await ctx.send(embed=embed)


async def setup(bot):
    """Load the Marketplace cog."""
    await bot.add_cog(MarketplaceCog(bot))