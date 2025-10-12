"""
Utility Commands - General bot utilities and information
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import platform
import psutil
from typing import Optional

from utils.logger import get_logger


class UtilityCog(commands.Cog, name="Utility"):
    """Utility and information commands"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)

    @app_commands.command(name="help", description="View all bot commands")
    async def help(self, interaction: discord.Interaction):
        """Display help menu"""
        embed = discord.Embed(
            title="🤖 Bjorn Bot - Command List",
            description="A multi-purpose Discord bot with economy, casino, and more!",
            color=discord.Color.blue()
        )

        # Economy Commands
        embed.add_field(
            name="💰 Economy",
            value="`/balance` - Check your balance\n"
                  "`/work` - Work for money\n"
                  "`/daily` - Claim daily bonus\n"
                  "`/crime` - Commit a crime\n"
                  "`/give` - Give money to others\n"
                  "`/leaderboard` - View wealth rankings",
            inline=False
        )

        # Banking
        embed.add_field(
            name="🏦 Banking",
            value="`/deposit` - Deposit to bank\n"
                  "`/withdraw` - Withdraw from bank\n"
                  "`/bankinfo` - Bank information",
            inline=False
        )

        # Casino
        embed.add_field(
            name="🎰 Casino",
            value="`/coinflip` - Flip a coin\n"
                  "`/slots` - Slot machine\n"
                  "`/blackjack` - Play blackjack\n"
                  "`/dice` - Roll dice",
            inline=False
        )

        # Investment
        embed.add_field(
            name="📈 Investment",
            value="`/invest` - Invest money\n"
                  "`/collect` - Collect returns\n"
                  "`/investment` - Check status",
            inline=False
        )

        # Store
        embed.add_field(
            name="🏪 Store",
            value="`/shop` - Browse items\n"
                  "`/buy` - Buy items\n"
                  "`/inventory` - View inventory\n"
                  "`/sell` - Sell items\n"
                  "`/use` - Use an item",
            inline=False
        )

        # Profile
        embed.add_field(
            name="👤 Profile",
            value="`/profile` - View profile\n"
                  "`/setbio` - Set your bio\n"
                  "`/setcolor` - Set profile color\n"
                  "`/rank` - View your rank\n"
                  "`/badges` - View badges",
            inline=False
        )

        # Reminders
        embed.add_field(
            name="⏰ Reminders",
            value="`/remind` - Set a reminder\n"
                  "`/reminders` - View reminders\n"
                  "`/birthday` - Set birthday\n"
                  "`/nextbirthday` - Check next birthday",
            inline=False
        )

        # Referral
        embed.add_field(
            name="🎉 Referral",
            value="`/refer` - Refer a user\n"
                  "`/referrals` - View your referrals\n"
                  "`/referralboard` - Top referrers",
            inline=False
        )

        # Moderation (if user has permissions)
        if interaction.user.guild_permissions.kick_members:
            embed.add_field(
                name="🛡️ Moderation",
                value="`/warn` - Warn a user\n"
                      "`/warnings` - View warnings\n"
                      "`/clearwarn` - Remove warning\n"
                      "`/kick` - Kick a user\n"
                      "`/ban` - Ban a user\n"
                      "`/clear` - Delete messages",
                inline=False
            )

        # Utility
        embed.add_field(
            name="🔧 Utility",
            value="`/ping` - Check bot latency\n"
                  "`/serverinfo` - Server information\n"
                  "`/userinfo` - User information\n"
                  "`/botinfo` - Bot statistics",
            inline=False
        )

        embed.set_footer(text=f"Bjorn Bot v1.0 • {len(self.bot.guilds)} servers")
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction):
        """Display bot latency"""
        latency = round(self.bot.latency * 1000)
        
        # Determine status emoji
        if latency < 100:
            emoji = "🟢"
            status = "Excellent"
        elif latency < 200:
            emoji = "🟡"
            status = "Good"
        else:
            emoji = "🔴"
            status = "Poor"

        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"{emoji} **{latency}ms** - {status}",
            color=discord.Color.green() if latency < 100 else discord.Color.yellow() if latency < 200 else discord.Color.red()
        )
        
        embed.set_footer(text=f"API Latency: {latency}ms")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="View server information")
    async def serverinfo(self, interaction: discord.Interaction):
        """Display server information"""
        if not interaction.guild:
            await interaction.response.send_message("This command only works in servers!", ephemeral=True)
            return

        guild = interaction.guild

        # Count channels
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)

        # Count members
        total_members = guild.member_count
        bots = len([m for m in guild.members if m.bot])
        humans = total_members - bots

        embed = discord.Embed(
            title=f"📊 {guild.name}",
            color=discord.Color.blue()
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        # Basic Info
        embed.add_field(
            name="🆔 Server Info",
            value=f"**ID:** {guild.id}\n"
                  f"**Owner:** {guild.owner.mention if guild.owner else 'Unknown'}\n"
                  f"**Created:** <t:{int(guild.created_at.timestamp())}:R>",
            inline=True
        )

        # Members
        embed.add_field(
            name="👥 Members",
            value=f"**Total:** {total_members:,}\n"
                  f"**Humans:** {humans:,}\n"
                  f"**Bots:** {bots:,}",
            inline=True
        )

        # Channels
        embed.add_field(
            name="📁 Channels",
            value=f"**Categories:** {categories}\n"
                  f"**Text:** {text_channels}\n"
                  f"**Voice:** {voice_channels}",
            inline=True
        )

        # Roles
        embed.add_field(
            name="🎭 Roles",
            value=f"{len(guild.roles)} roles",
            inline=True
        )

        # Boosts
        embed.add_field(
            name="✨ Boosts",
            value=f"Level {guild.premium_tier}\n"
                  f"{guild.premium_subscription_count or 0} boosts",
            inline=True
        )

        # Emojis
        embed.add_field(
            name="😀 Emojis",
            value=f"{len(guild.emojis)}/{guild.emoji_limit}",
            inline=True
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="View user information")
    @app_commands.describe(user="User to view (optional)")
    async def userinfo(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Display user information"""
        target = user or interaction.user

        embed = discord.Embed(
            title=f"👤 {target.display_name}",
            color=target.color if target.color != discord.Color.default() else discord.Color.blue()
        )

        embed.set_thumbnail(url=target.display_avatar.url)

        # Basic Info
        embed.add_field(
            name="📝 Basic Info",
            value=f"**Username:** {target.name}\n"
                  f"**ID:** {target.id}\n"
                  f"**Bot:** {'Yes' if target.bot else 'No'}",
            inline=True
        )

        # Account Info
        created_timestamp = int(target.created_at.timestamp())
        embed.add_field(
            name="📅 Account",
            value=f"**Created:** <t:{created_timestamp}:R>\n"
                  f"**Full Date:** <t:{created_timestamp}:F>",
            inline=True
        )

        # Server Info (if in a server)
        if interaction.guild and isinstance(target, discord.Member):
            joined_timestamp = int(target.joined_at.timestamp()) if target.joined_at else None
            
            embed.add_field(
                name="📥 Server Member",
                value=f"**Joined:** <t:{joined_timestamp}:R>\n"
                      f"**Top Role:** {target.top_role.mention}",
                inline=False
            )

            # Roles (show up to 10)
            if len(target.roles) > 1:
                roles = [role.mention for role in reversed(target.roles[1:])][:10]
                roles_text = ", ".join(roles)
                if len(target.roles) > 11:
                    roles_text += f" (+{len(target.roles) - 11} more)"
                embed.add_field(
                    name=f"🎭 Roles [{len(target.roles) - 1}]",
                    value=roles_text,
                    inline=False
                )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="botinfo", description="View bot statistics")
    async def botinfo(self, interaction: discord.Interaction):
        """Display bot information and statistics"""
        # Get bot stats
        total_users = len(set(self.bot.get_all_members()))
        total_guilds = len(self.bot.guilds)

        # Get database stats
        db_stats = await self.bot.db.get_database_stats()

        # System info
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB

        # Calculate uptime
        if self.bot.start_time:
            uptime = datetime.now() - self.bot.start_time
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        else:
            uptime_str = "Unknown"

        embed = discord.Embed(
            title="🤖 Bjorn Bot Information",
            description="A multi-purpose Discord bot built with Python",
            color=discord.Color.blue()
        )

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        # Bot Stats
        embed.add_field(
            name="📊 Statistics",
            value=f"**Servers:** {total_guilds:,}\n"
                  f"**Users:** {total_users:,}\n"
                  f"**Commands:** {len(self.bot.tree.get_commands())}",
            inline=True
        )

        # System Info
        embed.add_field(
            name="💻 System",
            value=f"**Uptime:** {uptime_str}\n"
                  f"**Memory:** {memory_usage:.1f} MB\n"
                  f"**Python:** {platform.python_version()}",
            inline=True
        )

        # Database Stats
        embed.add_field(
            name="🗄️ Database",
            value=f"**Users:** {db_stats.get('users', 0):,}\n"
                  f"**Transactions:** {db_stats.get('transactions', 0):,}\n"
                  f"**Items:** {db_stats.get('items', 0):,}",
            inline=True
        )

        # Links
        embed.add_field(
            name="🔗 Links",
            value=f"[GitHub](https://github.com/retrac-ca/bjorn) • "
                  f"[Support](https://discord.gg/bjorn) • "
                  f"[Invite](https://discord.com/oauth2/authorize?client_id={self.bot.user.id})",
            inline=False
        )

        embed.set_footer(text=f"Bjorn Bot v1.0 • Made with ❤️ by retrac-ca")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="invite", description="Get bot invite link")
    async def invite(self, interaction: discord.Interaction):
        """Generate bot invite link"""
        # Generate invite URL with proper permissions
        permissions = discord.Permissions(
            read_messages=True,
            send_messages=True,
            embed_links=True,
            attach_files=True,
            read_message_history=True,
            add_reactions=True,
            kick_members=True,
            ban_members=True,
            manage_messages=True
        )

        invite_url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=permissions,
            scopes=["bot", "applications.commands"]
        )

        embed = discord.Embed(
            title="📨 Invite Bjorn Bot",
            description=f"Click [here]({invite_url}) to invite me to your server!",
            color=discord.Color.green()
        )

        embed.add_field(
            name="✨ Features",
            value="• Economy system with work, daily, crime\n"
                  "• Casino games (slots, blackjack, dice)\n"
                  "• Investment system\n"
                  "• Store and inventory\n"
                  "• Moderation tools\n"
                  "• Profile customization\n"
                  "• And much more!",
            inline=False
        )

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="stats", description="View your personal statistics")
    async def stats(self, interaction: discord.Interaction):
        """Display personal statistics"""
        user = await self.bot.db.get_user(interaction.user.id)

        embed = discord.Embed(
            title=f"📊 {interaction.user.display_name}'s Statistics",
            color=discord.Color.blue()
        )

        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        # Economy Stats
        net_worth = user.balance + user.bank_balance
        embed.add_field(
            name="💰 Economy",
            value=f"**Net Worth:** ${net_worth:,}\n"
                  f"**Total Earned:** ${user.total_earned:,}\n"
                  f"**Total Spent:** ${user.total_spent:,}",
            inline=True
        )

        # Activity Stats
        embed.add_field(
            name="📈 Activity",
            value=f"**Commands Used:** {user.commands_used:,}\n"
                  f"**Messages Sent:** {user.messages_sent:,}\n"
                  f"**Level:** {user.level}",
            inline=True
        )

        # Calculate some fun stats
        profit = user.total_earned - user.total_spent
        profit_color = "🟢" if profit >= 0 else "🔴"
        
        embed.add_field(
            name="💹 Profit/Loss",
            value=f"{profit_color} **${profit:,}**",
            inline=False
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(UtilityCog(bot))