"""
Utility Commands Cog

This module contains utility commands for the Saint Toadle bot including
help commands, server information, user information, and other useful tools.
"""

import platform
import time
from datetime import datetime, timezone

import discord
from discord.ext import commands
import psutil

from utils.decorators import log_command_usage, typing
from utils.helpers import format_time_delta, send_paginated_embed
from utils.logger import get_logger


class UtilityCog(commands.Cog, name="Utility"):
    """
    Utility commands cog.
    
    This cog provides various utility commands including help,
    server information, user information, and bot statistics.
    """
    
    def __init__(self, bot):
        """
        Initialize the utility cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
        self.logger = get_logger(__name__)
    
    @commands.command(name='help', aliases=['h', 'commands'], help="Show help information")
    @log_command_usage
    async def help_command(self, ctx: commands.Context, *, command_name: str = None):
        """
        Custom help command with better formatting.
        
        Args:
            command_name: Specific command to get help for
        """
        if command_name:
            # Help for specific command
            command = self.bot.get_command(command_name)
            if not command:
                embed = discord.Embed(
                    title="❌ Command Not Found",
                    description=f"No command named `{command_name}` was found.",
                    color=0xFF0000
                )
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"📖 Help: {command.name}",
                description=command.help or "No description available.",
                color=self.bot.config.get_embed_color()
            )
            
            if command.aliases:
                embed.add_field(
                    name="Aliases",
                    value=", ".join(f"`{alias}`" for alias in command.aliases),
                    inline=False
                )
            
            embed.add_field(
                name="Usage",
                value=f"`{ctx.prefix}{command.name} {command.signature}`",
                inline=False
            )
            
            if command.cog_name:
                embed.add_field(
                    name="Category",
                    value=command.cog_name,
                    inline=True
                )
            
            if hasattr(command, 'cooldown') and command.cooldown:
                embed.add_field(
                    name="Cooldown",
                    value=f"{command.cooldown.per} seconds",
                    inline=True
                )
            
            await ctx.send(embed=embed)
            return
        
        # General help - show all commands by category
        embed = discord.Embed(
            title=f"📖 {self.bot.config.bot_name} Help",
            description=f"Use `{ctx.prefix}help <command>` for detailed information about a command.",
            color=self.bot.config.get_embed_color()
        )
        
        # Group commands by cog
        cogs = {}
        for command in self.bot.commands:
            if command.hidden:
                continue
            
            cog_name = command.cog_name or "No Category"
            if cog_name not in cogs:
                cogs[cog_name] = []
            cogs[cog_name].append(command)
        
        # Add fields for each category
        for cog_name, commands_list in cogs.items():
            if not commands_list:
                continue
            
            # Get emoji for category
            category_emojis = {
                "Economy": "💰",
                "Moderation": "🛡️",
                "Utility": "🛠️",
                "Profile": "👤",
                "Referral": "🔗",
                "Marketplace": "🏪",
                "Bank": "🏦",
                "No Category": "📋"
            }
            
            emoji = category_emojis.get(cog_name, "📋")
            command_names = [f"`{cmd.name}`" for cmd in commands_list]
            
            embed.add_field(
                name=f"{emoji} {cog_name} ({len(commands_list)})",
                value=" • ".join(command_names),
                inline=False
            )
        
        # Add bot info
        embed.add_field(
            name="ℹ️ Bot Information",
            value=f"**Prefix:** `{ctx.prefix}`\n"
                  f"**Total Commands:** {len(self.bot.commands)}\n"
                  f"**Servers:** {len(self.bot.guilds)}",
            inline=True
        )
        
        embed.add_field(
            name="🔗 Links",
            value="[Support Server](https://discord.gg/support) • [GitHub](https://github.com/sainttoadle)",
            inline=True
        )
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='ping', help="Check bot latency and response time")
    @log_command_usage
    async def ping(self, ctx: commands.Context):
        """
        Check bot latency and response time.
        """
        # Measure response time
        start_time = time.perf_counter()
        message = await ctx.send("🏓 Pinging...")
        end_time = time.perf_counter()
        
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        websocket_latency = self.bot.latency * 1000  # Convert to milliseconds
        
        # Determine latency quality
        if websocket_latency < 100:
            latency_emoji = "🟢"
            latency_status = "Excellent"
        elif websocket_latency < 200:
            latency_emoji = "🟡"
            latency_status = "Good"
        elif websocket_latency < 300:
            latency_emoji = "🟠"
            latency_status = "Fair"
        else:
            latency_emoji = "🔴"
            latency_status = "Poor"
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"{latency_emoji} **Status:** {latency_status}",
            color=self.bot.config.get_embed_color()
        )
        
        embed.add_field(
            name="📡 WebSocket Latency",
            value=f"{websocket_latency:.1f}ms",
            inline=True
        )
        
        embed.add_field(
            name="🔄 Response Time",
            value=f"{response_time:.1f}ms",
            inline=True
        )
        
        embed.add_field(
            name="⏱️ Uptime",
            value=format_time_delta(datetime.now(timezone.utc) - self.bot.start_time) if self.bot.start_time else "Unknown",
            inline=True
        )
        
        embed.set_footer(text="Lower is better!")
        
        await message.edit(content=None, embed=embed)
    
    @commands.command(name='serverinfo', aliases=['si', 'guildinfo'], help="Show server information")
    @log_command_usage
    @commands.guild_only()
    async def server_info(self, ctx: commands.Context):
        """
        Display information about the current server.
        """
        guild = ctx.guild
        
        embed = discord.Embed(
            title=f"🏰 {guild.name}",
            color=self.bot.config.get_embed_color(),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Basic info
        embed.add_field(
            name="📊 Basic Information",
            value=f"**ID:** {guild.id}\n"
                  f"**Owner:** {guild.owner.mention if guild.owner else 'Unknown'}\n"
                  f"**Created:** <t:{int(guild.created_at.timestamp())}:F>\n"
                  f"**Region:** {guild.preferred_locale}",
            inline=False
        )
        
        # Member counts
        total_members = guild.member_count
        humans = sum(1 for member in guild.members if not member.bot)
        bots = total_members - humans
        
        online_members = sum(1 for member in guild.members if member.status != discord.Status.offline)
        
        embed.add_field(
            name="👥 Members",
            value=f"**Total:** {total_members:,}\n"
                  f"**Humans:** {humans:,}\n"
                  f"**Bots:** {bots:,}\n"
                  f"**Online:** {online_members:,}",
            inline=True
        )
        
        # Channel counts
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed.add_field(
            name="📝 Channels",
            value=f"**Text:** {text_channels}\n"
                  f"**Voice:** {voice_channels}\n"
                  f"**Categories:** {categories}",
            inline=True
        )
        
        # Other info
        embed.add_field(
            name="🎭 Other",
            value=f"**Roles:** {len(guild.roles)}\n"
                  f"**Emojis:** {len(guild.emojis)}\n"
                  f"**Boost Level:** {guild.premium_tier}\n"
                  f"**Boosts:** {guild.premium_subscription_count}",
            inline=True
        )
        
        # Features
        if guild.features:
            features = []
            feature_mapping = {
                "COMMUNITY": "Community Server",
                "VERIFIED": "Verified",
                "PARTNERED": "Discord Partner",
                "DISCOVERABLE": "Server Discovery",
                "VANITY_URL": "Vanity URL",
                "INVITE_SPLASH": "Invite Splash",
                "BANNER": "Server Banner",
                "ANIMATED_ICON": "Animated Icon"
            }
            
            for feature in guild.features:
                feature_name = feature_mapping.get(feature, feature.replace('_', ' ').title())
                features.append(feature_name)
            
            if features:
                embed.add_field(
                    name="✨ Features",
                    value=", ".join(features[:5]),  # Limit to first 5
                    inline=False
                )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        
        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='userinfo', aliases=['ui', 'memberinfo'], help="Show user information")
    @log_command_usage
    async def user_info(self, ctx: commands.Context, member: discord.Member = None):
        """
        Display information about a user.
        
        Args:
            member: Member to show info for (defaults to command author)
        """
        member = member or ctx.author
        
        embed = discord.Embed(
            title=f"👤 {member.display_name}",
            color=member.color if member.color != discord.Color.default() else self.bot.config.get_embed_color(),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Basic info
        embed.add_field(
            name="📊 Basic Information",
            value=f"**Username:** {member.name}#{member.discriminator}\n"
                  f"**ID:** {member.id}\n"
                  f"**Bot:** {'Yes' if member.bot else 'No'}\n"
                  f"**Created:** <t:{int(member.created_at.timestamp())}:F>",
            inline=False
        )
        
        # Server-specific info (if in a guild)
        if ctx.guild and member in ctx.guild.members:
            embed.add_field(
                name="🏰 Server Information",
                value=f"**Joined:** <t:{int(member.joined_at.timestamp())}:F>\n"
                      f"**Nickname:** {member.nick or 'None'}\n"
                      f"**Top Role:** {member.top_role.mention}\n"
                      f"**Status:** {str(member.status).title()}",
                inline=False
            )
            
            # Roles (show top 10)
            roles = [role.mention for role in reversed(member.roles) if role != ctx.guild.default_role]
            if roles:
                roles_text = ", ".join(roles[:10])
                if len(roles) > 10:
                    roles_text += f" and {len(roles) - 10} more"
                
                embed.add_field(
                    name=f"🎭 Roles ({len(roles)})",
                    value=roles_text,
                    inline=False
                )
        
        # Permissions (if in guild and has permissions)
        if ctx.guild and member.guild_permissions:
            key_perms = []
            if member.guild_permissions.administrator:
                key_perms.append("Administrator")
            if member.guild_permissions.manage_guild:
                key_perms.append("Manage Server")
            if member.guild_permissions.manage_channels:
                key_perms.append("Manage Channels")
            if member.guild_permissions.manage_messages:
                key_perms.append("Manage Messages")
            if member.guild_permissions.kick_members:
                key_perms.append("Kick Members")
            if member.guild_permissions.ban_members:
                key_perms.append("Ban Members")
            
            if key_perms:
                embed.add_field(
                    name="🔑 Key Permissions",
                    value=", ".join(key_perms),
                    inline=False
                )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='botinfo', aliases=['about', 'stats'], help="Show bot information and statistics")
    @log_command_usage
    @typing
    async def bot_info(self, ctx: commands.Context):
        """
        Display bot information and statistics.
        """
        embed = discord.Embed(
            title=f"🤖 {self.bot.user.name} Information",
            description="A comprehensive Discord bot with economy, moderation, and social features.",
            color=self.bot.config.get_embed_color(),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Bot stats
        total_users = len(set(self.bot.get_all_members()))
        total_commands = len(self.bot.commands)
        
        embed.add_field(
            name="📊 Statistics",
            value=f"**Servers:** {len(self.bot.guilds):,}\n"
                  f"**Users:** {total_users:,}\n"
                  f"**Commands:** {total_commands}\n"
                  f"**Cogs:** {len(self.bot.cogs)}",
            inline=True
        )
        
        # Technical info
        python_version = platform.python_version()
        discord_version = discord.__version__
        
        embed.add_field(
            name="💻 Technical",
            value=f"**Python:** {python_version}\n"
                  f"**Discord.py:** {discord_version}\n"
                  f"**Platform:** {platform.system()}\n"
                  f"**Uptime:** {format_time_delta(datetime.now(timezone.utc) - self.bot.start_time) if self.bot.start_time else 'Unknown'}",
            inline=True
        )
        
        # System resources
        try:
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            cpu_usage = process.cpu_percent()
            
            embed.add_field(
                name="⚡ Resources",
                value=f"**Memory:** {memory_usage:.1f} MB\n"
                      f"**CPU:** {cpu_usage:.1f}%\n"
                      f"**Latency:** {self.bot.latency * 1000:.1f}ms",
                inline=True
            )
        except ImportError:
            # psutil not available
            embed.add_field(
                name="⚡ Resources",
                value=f"**Latency:** {self.bot.latency * 1000:.1f}ms",
                inline=True
            )
        
        # Database stats (if available)
        if hasattr(self.bot, 'db') and self.bot.db:
            try:
                db_stats = await self.bot.db.get_database_stats()
                total_records = sum(db_stats.values())
                
                embed.add_field(
                    name="🗄️ Database",
                    value=f"**Total Records:** {total_records:,}\n"
                          f"**Users:** {db_stats.get('users', 0):,}\n"
                          f"**Guilds:** {db_stats.get('guilds', 0):,}",
                    inline=True
                )
            except Exception as e:
                self.logger.error(f"Failed to get database stats: {e}")
        
        # Features
        features = []
        if self.bot.config.economy_enabled:
            features.append("💰 Economy")
        if self.bot.config.moderation_enabled:
            features.append("🛡️ Moderation")
        if self.bot.config.referral_enabled:
            features.append("🔗 Referrals")
        if self.bot.config.marketplace_enabled:
            features.append("🏪 Marketplace")
        if self.bot.config.profiles_enabled:
            features.append("👤 Profiles")
        
        if features:
            embed.add_field(
                name="✨ Features",
                value=" • ".join(features),
                inline=False
            )
        
        embed.add_field(
            name="🔗 Links",
            value="[Support Server](https://discord.gg/support) • [GitHub](https://github.com/sainttoadle) • [Website](https://sainttoadle.com)",
            inline=False
        )
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(
            text=f"Made with ❤️ in Python • Requested by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.send(embed=embed)


async def setup(bot):
    """Load the Utility cog."""
    await bot.add_cog(UtilityCog(bot))