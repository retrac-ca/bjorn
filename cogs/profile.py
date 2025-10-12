"""
Profile Commands Cog

This module contains profile-related slash commands for the Bjorn bot,
including viewing and customizing user profiles.
"""

import discord
from discord import app_commands
from discord.ext import commands

from utils.logger import get_logger
from utils.helpers import format_currency
from utils.decorators import log_command_usage


class ProfileCog(commands.Cog, name="Profile"):
    """
    Profile cog with slash commands.
    
    Provides user profile viewing and customization.
    """

    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)

    @app_commands.command(name="profile", description="View a user's profile")
    @app_commands.describe(member="User to view profile for")
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        """
        Display a user's profile with stats and information.
        """
        member = member or interaction.user
        user = await self.bot.db.get_user(member.id, member.name, member.discriminator)

        embed = discord.Embed(
            title=f"👤 {member.display_name}'s Profile",
            color=user.profile_color or self.bot.config.get_embed_color()
        )

        # Basic info
        embed.add_field(
            name="💰 Economy",
            value=f"**Wallet:** {format_currency(user.balance)}\n"
                  f"**Bank:** {format_currency(user.bank_balance)}\n"
                  f"**Total Wealth:** {format_currency(user.balance + user.bank_balance)}",
            inline=True
        )

        embed.add_field(
            name="📊 Statistics",
            value=f"**Level:** {user.level}\n"
                  f"**Experience:** {user.experience:,}\n"
                  f"**Commands Used:** {user.commands_used:,}",
            inline=True
        )

        embed.add_field(
            name="🏆 Records",
            value=f"**Total Earned:** {format_currency(user.total_earned)}\n"
                  f"**Total Spent:** {format_currency(user.total_spent)}\n"
                  f"**Net Worth:** {format_currency(user.total_earned - user.total_spent)}",
            inline=True
        )

        # Bio if available
        if user.bio:
            embed.add_field(name="📝 Bio", value=user.bio, inline=False)

        # Badges if available
        if user.badges:
            badge_text = " ".join(user.badges)
            embed.add_field(name="🏅 Badges", value=badge_text, inline=False)

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(
            text=f"Member since {member.created_at.strftime('%Y-%m-%d')}",
            icon_url=member.display_avatar.url
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setbio", description="Set your profile bio")
    @app_commands.describe(bio="Your new bio (max 200 characters)")
    async def setbio(self, interaction: discord.Interaction, bio: str):
        """
        Set or update your profile bio.
        """
        if len(bio) > 200:
            embed = discord.Embed(
                title="❌ Bio Too Long",
                description="Bio must be 200 characters or less.",
                color=self.bot.config.get_error_color()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Update bio in database
        user = await self.bot.db.get_user(interaction.user.id, interaction.user.name, interaction.user.discriminator)
        # Note: You'll need to add a method to update bio in your database manager
        # For now, assuming it exists:
        # await self.bot.db.update_user_bio(interaction.user.id, bio)

        embed = discord.Embed(
            title="✅ Bio Updated",
            description=f"Your bio has been set to:\n\n{bio}",
            color=self.bot.config.get_success_color()
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="View the wealth leaderboard")
    @app_commands.describe(category="Category to rank by")
    @app_commands.choices(category=[
        app_commands.Choice(name="Total Wealth (Wallet + Bank)", value="total_wealth"),
        app_commands.Choice(name="Wallet Balance", value="balance"),
        app_commands.Choice(name="Bank Balance", value="bank_balance"),
        app_commands.Choice(name="Total Earned", value="total_earned"),
        app_commands.Choice(name="Experience", value="experience")
    ])
    async def leaderboard(self, interaction: discord.Interaction, category: str = "total_wealth"):
        """
        Display leaderboard for various categories.
        """
        users = await self.bot.db.get_leaderboard(limit=10, order_by=category)

        if not users:
            embed = discord.Embed(
                title="📊 Leaderboard",
                description="No users found in the leaderboard.",
                color=self.bot.config.get_embed_color()
            )
            await interaction.response.send_message(embed=embed)
            return

        category_names = {
            "total_wealth": "💰 Total Wealth",
            "balance": "💳 Wallet Balance",
            "bank_balance": "🏦 Bank Balance",
            "total_earned": "📈 Total Earned",
            "experience": "⭐ Experience"
        }

        embed = discord.Embed(
            title=f"📊 {category_names.get(category, category.title())} Leaderboard",
            color=self.bot.config.get_embed_color()
        )

        leaderboard_text = ""
        for i, user in enumerate(users, 1):
            # Try to get Discord user
            try:
                discord_user = await self.bot.fetch_user(user.id)
                username = discord_user.display_name
            except:
                username = user.username

            if category == "total_wealth":
                value = format_currency(user.balance + user.bank_balance)
            elif category in ["balance", "bank_balance", "total_earned"]:
                value = format_currency(getattr(user, category))
            else:
                value = f"{getattr(user, category):,}"

            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            leaderboard_text += f"{medal} **{username}** - {value}\n"

        embed.description = leaderboard_text
        embed.set_footer(text=f"Showing top {len(users)} users")

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    """Load the Profile cog."""
    await bot.add_cog(ProfileCog(bot))
