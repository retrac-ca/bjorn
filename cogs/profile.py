"""
Profile Commands Cog

This module contains user profile commands for the Saint Toadle bot.
"""

import discord
from discord.ext import commands

from utils.decorators import log_command_usage, require_database
from utils.logger import get_logger


class ProfileCog(commands.Cog, name="Profile"):
    """User profile commands cog."""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)
    
    @commands.command(name='profile', aliases=['p'], help="View your or someone's profile")
    @require_database
    @log_command_usage
    async def view_profile(self, ctx: commands.Context, member: discord.Member = None):
        """View user profile."""
        target = member or ctx.author
        user = await self.bot.db.get_user(target.id, target.name, target.discriminator)
        
        embed = discord.Embed(
            title=f"👤 {target.display_name}'s Profile",
            color=user.profile_color,
            timestamp=ctx.message.created_at
        )
        
        embed.add_field(
            name="📊 Stats",
            value=f"**Level:** {user.level}\n"
                  f"**Experience:** {user.experience:,}\n"
                  f"**Commands Used:** {user.commands_used:,}",
            inline=True
        )
        
        if user.bio:
            embed.add_field(
                name="📝 Bio",
                value=user.bio,
                inline=False
            )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text=f"Joined: {user.created_at.strftime('%B %d, %Y')}")
        
        await ctx.send(embed=embed)


async def setup(bot):
    """Load the Profile cog."""
    await bot.add_cog(ProfileCog(bot))