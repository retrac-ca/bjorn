"""
Moderation Commands Cog

This module contains moderation commands for the Saint Toadle bot including
warning systems, bans, kicks, and moderation logging.
"""

from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands

from utils.decorators import requires_permissions, bot_requires_permissions, log_command_usage, typing, guild_only
from utils.helpers import format_time_delta, parse_time_string
from utils.logger import get_logger


class ModerationCog(commands.Cog, name="Moderation"):
    """
    Moderation commands cog.
    
    This cog provides moderation functionality including warnings,
    bans, kicks, mutes, and moderation logging.
    """
    
    def __init__(self, bot):
        """
        Initialize the moderation cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
        self.logger = get_logger(__name__)
    
    @commands.command(name='warn', help="Issue a warning to a user")
    @guild_only
    @requires_permissions('kick_members')
    @log_command_usage
    @typing
    async def warn_user(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """
        Issue a warning to a user.
        
        Args:
            member: Member to warn
            reason: Reason for the warning
        """
        if member == ctx.author:
            embed = discord.Embed(
                title="❌ Invalid Target",
                description="You cannot warn yourself.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You cannot warn someone with a higher or equal role.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        if member.bot:
            embed = discord.Embed(
                title="❌ Invalid Target",
                description="You cannot warn bots.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        # Add warning to database
        warning_id = await self.bot.db.add_warning(
            user_id=member.id,
            guild_id=ctx.guild.id,
            moderator_id=ctx.author.id,
            reason=reason
        )
        
        # Get user's total warnings
        warnings = await self.bot.db.get_user_warnings(member.id, ctx.guild.id)
        warning_count = len(warnings)
        
        # Create warning embed
        embed = discord.Embed(
            title="⚠️ User Warned",
            description=f"{member.mention} has been warned.",
            color=0xFFA500,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="👤 User",
            value=f"{member.mention}\n`{member.id}`",
            inline=True
        )
        
        embed.add_field(
            name="👮 Moderator",
            value=f"{ctx.author.mention}\n`{ctx.author.id}`",
            inline=True
        )
        
        embed.add_field(
            name="📋 Reason",
            value=reason,
            inline=False
        )
        
        embed.add_field(
            name="🔢 Warning Count",
            value=f"This user now has {warning_count} warning(s).",
            inline=False
        )
        
        embed.add_field(
            name="🆔 Warning ID",
            value=f"`{warning_id}`",
            inline=True
        )
        
        embed.set_footer(text=f"Warning ID: {warning_id}")
        
        await ctx.send(embed=embed)
        
        # Try to DM the user
        try:
            dm_embed = discord.Embed(
                title=f"⚠️ Warning in {ctx.guild.name}",
                description=f"You have been warned in **{ctx.guild.name}**.",
                color=0xFFA500,
                timestamp=datetime.now(timezone.utc)
            )
            
            dm_embed.add_field(
                name="👮 Moderator",
                value=str(ctx.author),
                inline=True
            )
            
            dm_embed.add_field(
                name="📋 Reason",
                value=reason,
                inline=False
            )
            
            dm_embed.add_field(
                name="🔢 Total Warnings",
                value=f"You now have {warning_count} warning(s) in this server.",
                inline=False
            )
            
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass  # User has DMs disabled
        
        # Check for auto-ban threshold
        if warning_count >= self.bot.config.auto_ban_threshold:
            try:
                await member.ban(reason=f"Auto-ban: Reached {self.bot.config.auto_ban_threshold} warnings")
                
                auto_ban_embed = discord.Embed(
                    title="🔨 Auto-Ban Triggered",
                    description=f"{member.mention} has been automatically banned for reaching {self.bot.config.auto_ban_threshold} warnings.",
                    color=0xFF0000
                )
                
                await ctx.send(embed=auto_ban_embed)
                
            except discord.Forbidden:
                no_ban_embed = discord.Embed(
                    title="❌ Auto-Ban Failed",
                    description=f"{member.mention} reached the warning threshold but I don't have permission to ban them.",
                    color=0xFF0000
                )
                await ctx.send(embed=no_ban_embed)
    
    @commands.command(name='warnings', aliases=['warns'], help="View warnings for a user")
    @guild_only
    @requires_permissions('kick_members')
    @log_command_usage
    async def view_warnings(self, ctx: commands.Context, member: discord.Member = None):
        """
        View warnings for a user.
        
        Args:
            member: Member to view warnings for (defaults to command author)
        """
        target = member or ctx.author
        
        # Get warnings from database
        warnings = await self.bot.db.get_user_warnings(target.id, ctx.guild.id)
        
        embed = discord.Embed(
            title=f"⚠️ Warnings for {target.display_name}",
            color=0xFFA500,
            timestamp=datetime.now(timezone.utc)
        )
        
        if not warnings:
            embed.description = "This user has no warnings."
            embed.color = 0x00FF00
        else:
            embed.description = f"Found {len(warnings)} warning(s)."
            
            for i, warning in enumerate(warnings[-10:], 1):  # Show last 10 warnings
                moderator = self.bot.get_user(warning.moderator_id)
                moderator_name = moderator.display_name if moderator else f"Unknown ({warning.moderator_id})"
                
                embed.add_field(
                    name=f"Warning #{warning.id}",
                    value=f"**Moderator:** {moderator_name}\n"
                          f"**Reason:** {warning.reason}\n"
                          f"**Date:** <t:{int(warning.created_at.timestamp())}:F>",
                    inline=False
                )
            
            if len(warnings) > 10:
                embed.set_footer(text=f"Showing latest 10 of {len(warnings)} warnings")
        
        embed.set_thumbnail(url=target.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='kick', help="Kick a member from the server")
    @guild_only
    @requires_permissions('kick_members')
    @bot_requires_permissions('kick_members')
    @log_command_usage
    @typing
    async def kick_member(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """
        Kick a member from the server.
        
        Args:
            member: Member to kick
            reason: Reason for the kick
        """
        if member == ctx.author:
            embed = discord.Embed(
                title="❌ Invalid Target",
                description="You cannot kick yourself.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You cannot kick someone with a higher or equal role.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        if member == ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Invalid Target",
                description="You cannot kick the server owner.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        # Try to DM the user before kicking
        try:
            dm_embed = discord.Embed(
                title=f"👢 Kicked from {ctx.guild.name}",
                description=f"You have been kicked from **{ctx.guild.name}**.",
                color=0xFFA500,
                timestamp=datetime.now(timezone.utc)
            )
            
            dm_embed.add_field(
                name="👮 Moderator",
                value=str(ctx.author),
                inline=True
            )
            
            dm_embed.add_field(
                name="📋 Reason",
                value=reason,
                inline=False
            )
            
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass  # User has DMs disabled
        
        # Perform the kick
        try:
            await member.kick(reason=f"Kicked by {ctx.author}: {reason}")
            
            embed = discord.Embed(
                title="👢 Member Kicked",
                description=f"{member} has been kicked from the server.",
                color=0xFFA500,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="👤 User",
                value=f"{member.mention}\n`{member.id}`",
                inline=True
            )
            
            embed.add_field(
                name="👮 Moderator",
                value=f"{ctx.author.mention}\n`{ctx.author.id}`",
                inline=True
            )
            
            embed.add_field(
                name="📋 Reason",
                value=reason,
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Kick Failed",
                description="I don't have permission to kick this user.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='ban', help="Ban a member from the server")
    @guild_only
    @requires_permissions('ban_members')
    @bot_requires_permissions('ban_members')
    @log_command_usage
    @typing
    async def ban_member(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """
        Ban a member from the server.
        
        Args:
            member: Member to ban
            reason: Reason for the ban
        """
        if member == ctx.author:
            embed = discord.Embed(
                title="❌ Invalid Target",
                description="You cannot ban yourself.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You cannot ban someone with a higher or equal role.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        if member == ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Invalid Target",
                description="You cannot ban the server owner.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        # Try to DM the user before banning
        try:
            dm_embed = discord.Embed(
                title=f"🔨 Banned from {ctx.guild.name}",
                description=f"You have been banned from **{ctx.guild.name}**.",
                color=0xFF0000,
                timestamp=datetime.now(timezone.utc)
            )
            
            dm_embed.add_field(
                name="👮 Moderator",
                value=str(ctx.author),
                inline=True
            )
            
            dm_embed.add_field(
                name="📋 Reason",
                value=reason,
                inline=False
            )
            
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass  # User has DMs disabled
        
        # Perform the ban
        try:
            await member.ban(reason=f"Banned by {ctx.author}: {reason}", delete_message_days=1)
            
            embed = discord.Embed(
                title="🔨 Member Banned",
                description=f"{member} has been banned from the server.",
                color=0xFF0000,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="👤 User",
                value=f"{member.mention}\n`{member.id}`",
                inline=True
            )
            
            embed.add_field(
                name="👮 Moderator",
                value=f"{ctx.author.mention}\n`{ctx.author.id}`",
                inline=True
            )
            
            embed.add_field(
                name="📋 Reason",
                value=reason,
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Ban Failed",
                description="I don't have permission to ban this user.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='clear', aliases=['purge'], help="Clear messages from a channel")
    @guild_only
    @requires_permissions('manage_messages')
    @bot_requires_permissions('manage_messages')
    @log_command_usage
    @typing
    async def clear_messages(self, ctx: commands.Context, amount: int, member: Optional[discord.Member] = None):
        """
        Clear messages from a channel.
        
        Args:
            amount: Number of messages to delete
            member: Optional member to filter messages by
        """
        if amount <= 0 or amount > 100:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="Please specify a number between 1 and 100.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        def check(message):
            if member:
                return message.author == member
            return True
        
        try:
            # Delete the command message first
            await ctx.message.delete()
            
            # Delete the specified messages
            deleted = await ctx.channel.purge(limit=amount, check=check)
            
            embed = discord.Embed(
                title="🗑️ Messages Cleared",
                description=f"Successfully deleted {len(deleted)} message(s).",
                color=0x00FF00
            )
            
            if member:
                embed.add_field(
                    name="👤 Filtered by",
                    value=member.mention,
                    inline=True
                )
            
            embed.add_field(
                name="👮 Moderator",
                value=ctx.author.mention,
                inline=True
            )
            
            # Send confirmation and delete it after 5 seconds
            confirmation = await ctx.send(embed=embed, delete_after=5)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Clear Failed",
                description="I don't have permission to delete messages.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
        except discord.HTTPException as e:
            embed = discord.Embed(
                title="❌ Clear Failed",
                description=f"An error occurred: {str(e)}",
                color=0xFF0000
            )
            await ctx.send(embed=embed)


async def setup(bot):
    """Load the Moderation cog."""
    await bot.add_cog(ModerationCog(bot))