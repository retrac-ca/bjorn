"""
Bank Commands Cog

This module contains banking-related slash commands for the Bjorn bot,
including deposits, withdrawals, and interest tracking.
"""

import discord
from discord import app_commands
from discord.ext import commands

from utils.logger import get_logger
from utils.helpers import format_currency
from utils.decorators import log_command_usage


class BankCog(commands.Cog, name="Bank"):
    """
    Banking cog with slash commands.
    
    Provides deposit, withdraw, and bank balance management.
    """

    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)

    @app_commands.command(name="deposit", description="Deposit coins from wallet to bank")
    @app_commands.describe(amount="Amount to deposit (or 'all' for everything)")
    async def deposit(self, interaction: discord.Interaction, amount: str):
        """
        Move coins from wallet to bank for safety.
        """
        user = await self.bot.db.get_user(interaction.user.id, interaction.user.name, interaction.user.discriminator)
        
        if amount.lower() == "all":
            deposit_amount = user.balance
        else:
            try:
                deposit_amount = int(amount)
            except ValueError:
                embed = discord.Embed(
                    title="❌ Invalid Amount",
                    description="Please enter a valid number or 'all'.",
                    color=self.bot.config.get_error_color()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        if deposit_amount <= 0:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="Amount must be greater than 0.",
                color=self.bot.config.get_error_color()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if user.balance < deposit_amount:
            embed = discord.Embed(
                title="❌ Insufficient Funds",
                description=f"You only have {format_currency(user.balance)} in your wallet.",
                color=self.bot.config.get_error_color()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Perform deposit
        await self.bot.db.update_user_balance(interaction.user.id, -deposit_amount)
        await self.bot.db.update_bank_balance(interaction.user.id, deposit_amount)

        # Log transaction
        await self.bot.db.log_transaction(
            user_id=interaction.user.id,
            guild_id=interaction.guild.id if interaction.guild else None,
            transaction_type='deposit',
            amount=deposit_amount,
            description='Bank deposit'
        )

        embed = discord.Embed(
            title="🏦 Deposit Successful",
            description=f"Deposited {format_currency(deposit_amount)} to your bank account.",
            color=self.bot.config.get_success_color()
        )
        
        # Show new balances
        new_wallet = user.balance - deposit_amount
        new_bank = user.bank_balance + deposit_amount
        embed.add_field(name="Wallet", value=format_currency(new_wallet), inline=True)
        embed.add_field(name="Bank", value=format_currency(new_bank), inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="withdraw", description="Withdraw coins from bank to wallet")
    @app_commands.describe(amount="Amount to withdraw (or 'all' for everything)")
    async def withdraw(self, interaction: discord.Interaction, amount: str):
        """
        Move coins from bank to wallet.
        """
        user = await self.bot.db.get_user(interaction.user.id, interaction.user.name, interaction.user.discriminator)
        
        if amount.lower() == "all":
            withdraw_amount = user.bank_balance
        else:
            try:
                withdraw_amount = int(amount)
            except ValueError:
                embed = discord.Embed(
                    title="❌ Invalid Amount",
                    description="Please enter a valid number or 'all'.",
                    color=self.bot.config.get_error_color()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        if withdraw_amount <= 0:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="Amount must be greater than 0.",
                color=self.bot.config.get_error_color()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if user.bank_balance < withdraw_amount:
            embed = discord.Embed(
                title="❌ Insufficient Funds",
                description=f"You only have {format_currency(user.bank_balance)} in your bank.",
                color=self.bot.config.get_error_color()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Perform withdrawal
        await self.bot.db.update_bank_balance(interaction.user.id, -withdraw_amount)
        await self.bot.db.update_user_balance(interaction.user.id, withdraw_amount)

        # Log transaction
        await self.bot.db.log_transaction(
            user_id=interaction.user.id,
            guild_id=interaction.guild.id if interaction.guild else None,
            transaction_type='withdrawal',
            amount=withdraw_amount,
            description='Bank withdrawal'
        )

        embed = discord.Embed(
            title="🏦 Withdrawal Successful",
            description=f"Withdrew {format_currency(withdraw_amount)} from your bank account.",
            color=self.bot.config.get_success_color()
        )
        
        # Show new balances
        new_wallet = user.balance + withdraw_amount
        new_bank = user.bank_balance - withdraw_amount
        embed.add_field(name="Wallet", value=format_currency(new_wallet), inline=True)
        embed.add_field(name="Bank", value=format_currency(new_bank), inline=True)

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    """Load the Bank cog."""
    await bot.add_cog(BankCog(bot))
