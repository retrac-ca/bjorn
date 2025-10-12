"""
Economy Commands Cog

This module contains economy-related slash commands for the Bjorn bot,
including earning, balance checking, daily bonuses, crime, and giving coins.
"""

import random
from datetime import datetime, timezone, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from utils.decorators import requires_economy, log_command_usage, typing, require_database
from utils.helpers import format_currency, format_time_delta, validate_amount
from utils.logger import get_logger


class EconomyCog(commands.Cog, name="Economy"):
    """Economy cog with slash commands."""

    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)

    @app_commands.command(name="balance", description="Check your wallet and bank balance")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        """Display the balance of the user or another member."""

        user = member or interaction.user
        db_user = await self.bot.db.get_user(user.id, user.name, user.discriminator)

        wallet_balance = db_user.balance
        bank_balance = db_user.bank_balance

        embed = discord.Embed(
            title=f"💰 {user.display_name}'s Balance",
            color=self.bot.config.get_embed_color()
        )
        embed.add_field(name="Wallet", value=format_currency(wallet_balance), inline=True)
        embed.add_field(name="Bank", value=format_currency(bank_balance), inline=True)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text="Use /balance to check your balance anytime")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="earn", description="Earn coins by working")
    async def earn(self, interaction: discord.Interaction):
        """Earn a random amount of coins (5-minute cooldown)."""

        db_user = await self.bot.db.get_user(interaction.user.id, interaction.user.name, interaction.user.discriminator)

        # Check cooldown: 5 minutes
        now = datetime.now(timezone.utc)
        if db_user.last_earn:
            elapsed = (now - db_user.last_earn).total_seconds()
            if elapsed < 300:
                remaining = timedelta(seconds=300 - elapsed)
                embed = discord.Embed(
                    title="⌛ Cooldown Active",
                    description=f"Please wait {format_time_delta(remaining)} before working again.",
                    color=self.bot.config.get_warning_color()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        # Calculate earning
        amount = random.randint(self.bot.config.earn_min, self.bot.config.earn_max)
        await self.bot.db.update_user_balance(interaction.user.id, amount)
        # Update last_earn timestamp in your db as well if not already done
        db_user.last_earn = now
        await self.bot.db.use_daily(interaction.user.id)  # If used for updating last_earn

        # Log transaction
        await self.bot.db.log_transaction(
            user_id=interaction.user.id,
            guild_id=interaction.guild.id if interaction.guild else None,
            transaction_type='earn',
            amount=amount,
            description='Work earnings'
        )

        embed = discord.Embed(
            title="💼 Work Completed",
            description=f"You earned {format_currency(amount)} coins working hard!",
            color=self.bot.config.get_success_color()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Claim your daily bonus")
    async def daily(self, interaction: discord.Interaction):
        """Claim a daily bonus once every 24 hours."""

        db_user = await self.bot.db.get_user(interaction.user.id, interaction.user.name, interaction.user.discriminator)

        if not await self.bot.db.can_use_daily(interaction.user.id):
            embed = discord.Embed(
                title="⌛ Daily Cooldown",
                description="You can only claim your daily bonus once every 24 hours.",
                color=self.bot.config.get_warning_color()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        amount = random.randint(self.bot.config.daily_bonus_min, self.bot.config.daily_bonus_max)
        await self.bot.db.update_user_balance(interaction.user.id, amount)
        await self.bot.db.use_daily(interaction.user.id)

        # Log transaction
        await self.bot.db.log_transaction(
            user_id=interaction.user.id,
            guild_id=interaction.guild.id if interaction.guild else None,
            transaction_type='daily_bonus',
            amount=amount,
            description='Daily bonus claimed'
        )

        embed = discord.Embed(
            title="🎉 Daily Bonus Claimed!",
            description=f"You received {format_currency(amount)} coins as your daily bonus!",
            color=self.bot.config.get_success_color()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="give", description="Give coins to another user")
    @app_commands.describe(member="Member to give coins to", amount="Amount of coins to give")
    async def give(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        """Transfer coins from your wallet to another user."""

        if member.bot:
            embed = discord.Embed(
                title="❌ Invalid Target",
                description="You cannot give coins to bots.",
                color=self.bot.config.get_error_color()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Validate amount
        if amount <= 0:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="Amount must be greater than zero.",
                color=self.bot.config.get_error_color()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        user = interaction.user
        db_user = await self.bot.db.get_user(user.id, user.name, user.discriminator)
        db_member = await self.bot.db.get_user(member.id, member.name, member.discriminator)

        if db_user.balance < amount:
            embed = discord.Embed(
                title="❌ Insufficient Funds",
                description=f"You only have {format_currency(db_user.balance)} coins.",
                color=self.bot.config.get_error_color()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Perform transaction
        await self.bot.db.update_user_balance(user.id, -amount)
        await self.bot.db.update_user_balance(member.id, amount)

        # Log transactions
        await self.bot.db.log_transaction(
            user_id=user.id,
            guild_id=interaction.guild.id if interaction.guild else None,
            transaction_type='transfer_out',
            amount=-amount,
            description=f'Transfer to {member.display_name}',
            related_user_id=member.id
        )
        await self.bot.db.log_transaction(
            user_id=member.id,
            guild_id=interaction.guild.id if interaction.guild else None,
            transaction_type='transfer_in',
            amount=amount,
            description=f'Transfer from {user.display_name}',
            related_user_id=user.id
        )

        embed = discord.Embed(
            title="💸 Transfer Complete",
            description=f"You gave {format_currency(amount)} coins to {member.mention}.",
            color=self.bot.config.get_success_color()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="crime", description="Attempt a risky crime to earn coins")
    async def crime(self, interaction: discord.Interaction):
        """Risk some coins with a crime. High risk, high reward!"""

        db_user = await self.bot.db.get_user(interaction.user.id, interaction.user.name, interaction.user.discriminator)

        # Determine success chance and rewards
        success_chance = self.bot.config.crime_success_rate
        success = random.random() < success_chance

        if success:
            amount = random.randint(self.bot.config.crime_reward_min, self.bot.config.crime_reward_max)
            await self.bot.db.update_user_balance(interaction.user.id, amount)
            transaction_type = "crime_success"
            description = "Crime succeeded"
            color = self.bot.config.get_success_color()
            title = "🏆 Crime Success!"
            desc = f"You successfully earned {format_currency(amount)} coins!"
        else:
            fine = random.randint(self.bot.config.crime_fine_min, self.bot.config.crime_fine_max)
            if db_user.balance >= fine:
                await self.bot.db.update_user_balance(interaction.user.id, -fine)
                fine_text = f" and lost {format_currency(fine)} coins in fines"
                transaction_type = "crime_fail"
                description = "Crime failed with fine"
            else:
                fine_text = ", but you had no coins to pay fines"
                transaction_type = "crime_fail_no_funds"
                description = "Crime failed, no funds for fines"
            color = self.bot.config.get_error_color()
            title = "🚔 Crime Failed!"
            desc = f"You got caught{fine_text}."

        # Log transaction
        await self.bot.db.log_transaction(
            user_id=interaction.user.id,
            guild_id=interaction.guild.id if interaction.guild else None,
            transaction_type=transaction_type,
            amount=amount if success else -fine if db_user.balance >= fine else 0,
            description=description
        )

        embed = discord.Embed(
            title=title,
            description=desc,
            color=color
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    """Load the Economy cog."""
    await bot.add_cog(EconomyCog(bot))
