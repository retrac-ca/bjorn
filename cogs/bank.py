"""
Banking System - Deposits, withdrawals, and secure storage
"""
import discord
from discord import app_commands
from discord.ext import commands

from utils.logger import get_logger


class BankCog(commands.Cog, name="Bank"):
    """Banking system for secure money storage"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)

    @app_commands.command(name="deposit", description="Deposit money into your bank")
    @app_commands.describe(amount="Amount to deposit (or 'all' for everything)")
    async def deposit(self, interaction: discord.Interaction, amount: str):
        """Deposit money from wallet to bank"""
        user = await self.bot.db.get_user(interaction.user.id)

        # Handle "all" keyword
        if amount.lower() == "all":
            deposit_amount = user.balance
        else:
            try:
                deposit_amount = int(amount)
            except ValueError:
                await interaction.response.send_message(
                    "❌ Invalid amount! Use a number or 'all'",
                    ephemeral=True
                )
                return

        if deposit_amount <= 0:
            await interaction.response.send_message(
                "❌ Amount must be positive!",
                ephemeral=True
            )
            return

        if deposit_amount > user.balance:
            await interaction.response.send_message(
                f"❌ You only have ${user.balance:,} in your wallet!",
                ephemeral=True
            )
            return

        # Process deposit
        await self.bot.db.update_user_balance(interaction.user.id, -deposit_amount)
        
        # Update bank balance (TODO: Add dedicated method)
        from sqlalchemy import update
        from config.database import User
        async with self.bot.db.session_factory() as session:
            await session.execute(
                update(User)
                .where(User.id == interaction.user.id)
                .values(bank_balance=User.bank_balance + deposit_amount)
            )
            await session.commit()

        await self.bot.db.log_transaction(
            interaction.user.id,
            interaction.guild.id if interaction.guild else 0,
            'bank_deposit',
            deposit_amount
        )

        embed = discord.Embed(
            title="🏦 Deposit Successful",
            description=f"Deposited **${deposit_amount:,}** into your bank!",
            color=discord.Color.green()
        )
        
        # Fetch updated balance
        updated_user = await self.bot.db.get_user(interaction.user.id)
        embed.add_field(name="💵 Wallet", value=f"${updated_user.balance:,}", inline=True)
        embed.add_field(name="🏦 Bank", value=f"${updated_user.bank_balance:,}", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="withdraw", description="Withdraw money from your bank")
    @app_commands.describe(amount="Amount to withdraw (or 'all' for everything)")
    async def withdraw(self, interaction: discord.Interaction, amount: str):
        """Withdraw money from bank to wallet"""
        user = await self.bot.db.get_user(interaction.user.id)

        # Handle "all" keyword
        if amount.lower() == "all":
            withdraw_amount = user.bank_balance
        else:
            try:
                withdraw_amount = int(amount)
            except ValueError:
                await interaction.response.send_message(
                    "❌ Invalid amount! Use a number or 'all'",
                    ephemeral=True
                )
                return

        if withdraw_amount <= 0:
            await interaction.response.send_message(
                "❌ Amount must be positive!",
                ephemeral=True
            )
            return

        if withdraw_amount > user.bank_balance:
            await interaction.response.send_message(
                f"❌ You only have ${user.bank_balance:,} in your bank!",
                ephemeral=True
            )
            return

        # Process withdrawal
        await self.bot.db.update_user_balance(interaction.user.id, withdraw_amount)
        
        # Update bank balance
        from sqlalchemy import update
        from config.database import User
        async with self.bot.db.session_factory() as session:
            await session.execute(
                update(User)
                .where(User.id == interaction.user.id)
                .values(bank_balance=User.bank_balance - withdraw_amount)
            )
            await session.commit()

        await self.bot.db.log_transaction(
            interaction.user.id,
            interaction.guild.id if interaction.guild else 0,
            'bank_withdraw',
            withdraw_amount
        )

        embed = discord.Embed(
            title="🏦 Withdrawal Successful",
            description=f"Withdrew **${withdraw_amount:,}** from your bank!",
            color=discord.Color.green()
        )
        
        # Fetch updated balance
        updated_user = await self.bot.db.get_user(interaction.user.id)
        embed.add_field(name="💵 Wallet", value=f"${updated_user.balance:,}", inline=True)
        embed.add_field(name="🏦 Bank", value=f"${updated_user.bank_balance:,}", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bankinfo", description="View bank information and interest rates")
    async def bankinfo(self, interaction: discord.Interaction):
        """Display bank information"""
        embed = discord.Embed(
            title="🏦 Bjorn Bank",
            description="Secure storage for your money with daily interest!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="💰 Daily Interest Rate",
            value=f"{self.bot.config.bank_interest_rate * 100:.1f}%",
            inline=True
        )
        embed.add_field(
            name="🔒 Security",
            value="Your bank money is safe from robberies!",
            inline=True
        )
        embed.add_field(
            name="📊 How it Works",
            value="• Deposit money with `/deposit`\n"
                  "• Earn daily interest while stored\n"
                  "• Withdraw anytime with `/withdraw`\n"
                  "• Bank money can't be lost in crimes or gambling",
            inline=False
        )

        user = await self.bot.db.get_user(
            interaction.user.id,
            interaction.user.name,
            interaction.user.discriminator
        )
        daily_interest = int(user.bank_balance * self.bot.config.bank_interest_rate)
        
        if user.bank_balance > 0:
            embed.add_field(
                name="📈 Your Daily Interest",
                value=f"With ${user.bank_balance:,} in bank, you earn **${daily_interest:,}** daily!",
                inline=False
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(BankCog(bot))