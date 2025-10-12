"""
Profile System - User profiles and statistics
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from utils.logger import get_logger
from utils.helpers import create_progress_bar, get_exp_for_level


class ProfileCog(commands.Cog, name="Profile"):
    """User profile and statistics"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)

    @app_commands.command(name="profile", description="View a user's profile")
    @app_commands.describe(user="User to view (optional)")
    async def profile(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Display user profile"""
        target = user or interaction.user
        db_user = await self.bot.db.get_user(target.id, target.name, target.discriminator)

        # Calculate level progress
        current_level = db_user.level
        current_exp = db_user.experience
        exp_needed = get_exp_for_level(current_level + 1)
        exp_progress = current_exp - get_exp_for_level(current_level)
        exp_for_level = exp_needed - get_exp_for_level(current_level)
        
        progress_bar = create_progress_bar(exp_progress, exp_for_level, length=10)

        embed = discord.Embed(
            title=f"{target.display_name}'s Profile",
            color=db_user.profile_color or discord.Color.blue()
        )
        
        embed.set_thumbnail(url=target.display_avatar.url)

        # Bio
        if db_user.bio:
            embed.description = db_user.bio

        # Level & Experience
        embed.add_field(
            name="📊 Level & Experience",
            value=f"**Level:** {current_level}\n"
                  f"**XP:** {current_exp:,} ({exp_progress}/{exp_for_level})\n"
                  f"{progress_bar}",
            inline=False
        )

        # Economy Stats
        net_worth = db_user.balance + db_user.bank_balance
        embed.add_field(
            name="💰 Economy",
            value=f"**Net Worth:** ${net_worth:,}\n"
                  f"**Wallet:** ${db_user.balance:,}\n"
                  f"**Bank:** ${db_user.bank_balance:,}\n"
                  f"**Total Earned:** ${db_user.total_earned:,}\n"
                  f"**Total Spent:** ${db_user.total_spent:,}",
            inline=True
        )

        # Activity Stats
        embed.add_field(
            name="📈 Activity",
            value=f"**Commands Used:** {db_user.commands_used:,}\n"
                  f"**Messages Sent:** {db_user.messages_sent:,}",
            inline=True
        )

        # Badges
        if db_user.badges:
            badge_str = " ".join(db_user.badges)
            embed.add_field(
                name="🏆 Badges",
                value=badge_str or "No badges yet",
                inline=False
            )

        embed.set_footer(text=f"User ID: {target.id}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setbio", description="Set your profile bio")
    @app_commands.describe(bio="Your bio text (max 200 characters)")
    async def setbio(self, interaction: discord.Interaction, bio: str):
        """Set profile bio"""
        if len(bio) > 200:
            await interaction.response.send_message(
                "❌ Bio must be 200 characters or less!",
                ephemeral=True
            )
            return

        # Update bio in database
        from sqlalchemy import update
        from config.database import User
        
        async with self.bot.db.session_factory() as session:
            await session.execute(
                update(User)
                .where(User.id == interaction.user.id)
                .values(bio=bio)
            )
            await session.commit()

        embed = discord.Embed(
            title="✅ Bio Updated!",
            description=f"Your bio has been set to:\n\n*{bio}*",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setcolor", description="Set your profile color")
    @app_commands.describe(color="Hex color code (e.g., #FF0000 for red)")
    async def setcolor(self, interaction: discord.Interaction, color: str):
        """Set profile embed color"""
        # Parse hex color
        if not color.startswith('#'):
            color = '#' + color
        
        try:
            color_int = int(color[1:], 16)
            if not (0 <= color_int <= 0xFFFFFF):
                raise ValueError
        except (ValueError, IndexError):
            await interaction.response.send_message(
                "❌ Invalid color! Use hex format: #FF0000",
                ephemeral=True
            )
            return

        # Update color
        from sqlalchemy import update
        from config.database import User
        
        async with self.bot.db.session_factory() as session:
            await session.execute(
                update(User)
                .where(User.id == interaction.user.id)
                .values(profile_color=color_int)
            )
            await session.commit()

        embed = discord.Embed(
            title="✅ Color Updated!",
            description=f"Your profile color is now: {color}",
            color=color_int
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rank", description="View your server rank")
    async def rank(self, interaction: discord.Interaction):
        """Display user's rank in the server"""
        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server!",
                ephemeral=True
            )
            return

        # Get leaderboard
        leaderboard = await self.bot.db.get_leaderboard(limit=1000, order_by='balance')
        
        # Find user's position
        user_rank = None
        for idx, user in enumerate(leaderboard, 1):
            if user.id == interaction.user.id:
                user_rank = idx
                break

        if not user_rank:
            await interaction.response.send_message(
                "You're not ranked yet!",
                ephemeral=True
            )
            return

        db_user = await self.bot.db.get_user(interaction.user.id)
        net_worth = db_user.balance + db_user.bank_balance

        embed = discord.Embed(
            title=f"📊 {interaction.user.display_name}'s Rank",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Global Rank",
            value=f"**#{user_rank}** of {len(leaderboard)}",
            inline=True
        )
        embed.add_field(
            name="Net Worth",
            value=f"${net_worth:,}",
            inline=True
        )
        embed.add_field(
            name="Level",
            value=f"Level {db_user.level}",
            inline=True
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="badges", description="View available badges")
    async def badges(self, interaction: discord.Interaction):
        """List all available badges"""
        embed = discord.Embed(
            title="🏆 Available Badges",
            description="Earn badges by completing achievements!",
            color=discord.Color.gold()
        )

        badges_list = [
            ("💰", "Wealthy", "Have $10,000 net worth"),
            ("🎰", "Gambler", "Win 100 casino games"),
            ("💼", "Worker", "Use /work 500 times"),
            ("📈", "Investor", "Complete 50 successful investments"),
            ("🏦", "Banker", "Keep $50,000 in bank"),
            ("🎖️", "Veteran", "Be a member for 30 days"),
            ("👑", "VIP", "Premium membership"),
            ("⭐", "Star", "Get featured by staff")
        ]

        for emoji, name, requirement in badges_list:
            embed.add_field(
                name=f"{emoji} {name}",
                value=requirement,
                inline=True
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(ProfileCog(bot))