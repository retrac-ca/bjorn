"""
Bank Commands Cog

This module contains banking commands for the Saint Toadle bot including
deposit, withdraw, and interest management.
"""

import random
from datetime import datetime, timezone, timedelta
from typing import Optional

import discord
from discord.ext import commands

from utils.decorators import requires_economy, log_command_usage, typing, require_database
from utils.helpers import format_currency, validate_amount
from utils.logger import get_logger


class BankCog(commands.Cog, name="Bank"):
    """
    Banking commands cog.
    
    This cog provides banking functionality including deposits,
    withdrawals, and interest calculations.
    """
    
    def __init__(self, bot):
        """
        Initialize the bank cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
        self.logger = get_logger(__name__)
    
    @commands.command(name='deposit', aliases=['dep'], help="Deposit coins into your bank account")
    @require_database
    @requires_economy
    @log_command_usage
    @typing
    async def deposit_coins(self, ctx: commands.Context, amount: str):
        """
        Deposit coins into bank account.
        
        Args:
            amount: Amount to deposit (or 'all'/'max')
        """
        user = await self.bot.db.get_user(ctx.author.id, ctx.author.name, ctx.author.discriminator)
        
        # Validate amount
        parsed_amount = validate_amount(amount, minimum=1, maximum=user.balance)
        
        if parsed_amount is None or parsed_amount > user.balance:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description=f"Please specify a valid amount between 1 and {format_currency(user.balance)}.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        # Handle "all" or "max"
        if amount.lower() in ['all', 'max']:
            parsed_amount = user.balance
        
        if parsed_amount <= 0:
            embed = discord.Embed(
                title="💰 No Coins to Deposit",
                description="You don't have any coins to deposit.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        # Update balances
        wallet_success = await self.bot.db.update_user_balance(ctx.author.id, -parsed_amount)
        
        if wallet_success:
            # Update bank balance directly (need to add this method to database manager)
            async with self.bot.db.session_factory() as session:
                user_db = await session.get(self.bot.db.__class__.__module__.User, ctx.author.id)
                if user_db:
                    user_db.bank_balance += parsed_amount
                    await session.commit()
        
        # Log transaction
        await self.bot.db.log_transaction(
            user_id=ctx.author.id,
            guild_id=ctx.guild.id,
            transaction_type='deposit',
            amount=parsed_amount,
            description='Bank deposit'
        )
        
        embed = discord.Embed(
            title="🏦 Deposit Successful",
            description=f"You deposited {format_currency(parsed_amount)} into your bank account!",
            color=0x00FF00
        )
        
        embed.add_field(
            name="💵 Wallet",
            value=format_currency(user.balance - parsed_amount),
            inline=True
        )
        
        embed.add_field(
            name="🏦 Bank",
            value=format_currency(user.bank_balance + parsed_amount),
            inline=True
        )
        
        embed.set_footer(text="Your money is safe in the bank!")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='withdraw', aliases=['with'], help="Withdraw coins from your bank account")
    @require_database
    @requires_economy
    @log_command_usage
    @typing
    async def withdraw_coins(self, ctx: commands.Context, amount: str):
        """
        Withdraw coins from bank account.
        
        Args:
            amount: Amount to withdraw (or 'all'/'max')
        """
        user = await self.bot.db.get_user(ctx.author.id, ctx.author.name, ctx.author.discriminator)
        
        # Handle "all" or "max"
        if amount.lower() in ['all', 'max']:
            parsed_amount = user.bank_balance
        else:
            # Validate amount
            parsed_amount = validate_amount(amount, minimum=1, maximum=user.bank_balance)
        
        if parsed_amount is None or parsed_amount > user.bank_balance:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description=f"Please specify a valid amount between 1 and {format_currency(user.bank_balance)}.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        if parsed_amount <= 0:
            embed = discord.Embed(
                title="🏦 No Coins to Withdraw",
                description="You don't have any coins in your bank account.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        # Update balances
        wallet_success = await self.bot.db.update_user_balance(ctx.author.id, parsed_amount)
        
        if wallet_success:
            # Update bank balance directly
            async with self.bot.db.session_factory() as session:
                user_db = await session.get(self.bot.db.__class__.__module__.User, ctx.author.id)
                if user_db:
                    user_db.bank_balance -= parsed_amount
                    await session.commit()
        
        # Log transaction
        await self.bot.db.log_transaction(
            user_id=ctx.author.id,
            guild_id=ctx.guild.id,
            transaction_type='withdrawal',
            amount=parsed_amount,
            description='Bank withdrawal'
        )
        
        embed = discord.Embed(
            title="🏦 Withdrawal Successful",
            description=f"You withdrew {format_currency(parsed_amount)} from your bank account!",
            color=0x00FF00
        )
        
        embed.add_field(
            name="💵 Wallet",
            value=format_currency(user.balance + parsed_amount),
            inline=True
        )
        
        embed.add_field(
            name="🏦 Bank",
            value=format_currency(user.bank_balance - parsed_amount),
            inline=True
        )
        
        embed.set_footer(text="Don't spend it all at once!")
        
        await ctx.send(embed=embed)


async def setup(bot):
    """Load the Bank cog."""
    await bot.add_cog(BankCog(bot))