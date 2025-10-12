"""
Investment Commands Cog

This module contains investment-related slash commands for the Bjorn bot.
It handles creating investments, checking portfolios, and managing returns.
"""

import random
from datetime import datetime, timezone, timedelta
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from utils.decorators import requires_economy, log_command_usage, typing, require_database
from utils.helpers import format_currency, get_random_success_message, validate_amount
from utils.logger import get_logger


class InvestmentCog(commands.Cog, name="Investment"):
    """
    Investment commands cog with slash commands.
    
    This cog provides investment functionality including creating investments,
    checking portfolios, and automated maturity processing.
    """
    
    def __init__(self, bot):
        """Initialize the investment cog."""
        self.bot = bot
        self.logger = get_logger(__name__)
        
        # Investment types with different risk/reward profiles
        self.investment_types = {
            "conservative": {
                "name": "Conservative Bonds",
                "min_days": 1,
                "max_days": 3,
                "min_return": 1.05,
                "max_return": 1.15,
                "risk": 0.1,
                "emoji": "🛡️"
            },
            "balanced": {
                "name": "Balanced Portfolio",
                "min_days": 2,
                "max_days": 5,
                "min_return": 0.8,
                "max_return": 1.8,
                "risk": 0.25,
                "emoji": "⚖️"
            },
            "aggressive": {
                "name": "High-Risk Stocks",
                "min_days": 3,
                "max_days": 7,
                "min_return": 0.5,
                "max_return": 3.0,
                "risk": 0.4,
                "emoji": "🚀"
            }
        }
    
    @app_commands.command(name="invest", description="Invest your coins for potential returns")
    @app_commands.describe(
        amount="Amount to invest",
        investment_type="Type of investment (conservative/balanced/aggressive)"
    )
    @app_commands.choices(investment_type=[
        app_commands.Choice(name="Conservative Bonds 🛡️ (Low risk, steady returns)", value="conservative"),
        app_commands.Choice(name="Balanced Portfolio ⚖️ (Medium risk, moderate returns)", value="balanced"),
        app_commands.Choice(name="High-Risk Stocks 🚀 (High risk, high potential)", value="aggressive"),
    ])
    async def invest(self, interaction: discord.Interaction, amount: int, investment_type: str):
        """Create a new investment."""
        if not self.bot.config.economy_enabled or not self.bot.config.investment_enabled:
            embed = discord.Embed(
                title="❌ Feature Disabled",
                description="Investment system is currently disabled.",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Validate amount
        if amount < self.bot.config.investment_min_amount:
            embed = discord.Embed(
                title="❌ Investment Too Small",
                description=f"Minimum investment amount is {format_currency(self.bot.config.investment_min_amount)}.",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if amount > self.bot.config.investment_max_amount:
            embed = discord.Embed(
                title="❌ Investment Too Large",
                description=f"Maximum investment amount is {format_currency(self.bot.config.investment_max_amount)}.",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get user and check balance
        user = await self.bot.db.get_user(interaction.user.id, interaction.user.name, interaction.user.discriminator)
        
        if user.balance < amount:
            embed = discord.Embed(
                title="💰 Insufficient Funds",
                description=f"You need {format_currency(amount)} but only have {format_currency(user.balance)}.",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get investment type details
        inv_type = self.investment_types[investment_type]
        
        # Calculate maturity date
        days_to_mature = random.randint(inv_type["min_days"], inv_type["max_days"])
        maturity_date = datetime.now(timezone.utc) + timedelta(days=days_to_mature)
        
        # Calculate expected return
        expected_return = random.uniform(inv_type["min_return"], inv_type["max_return"])
        
        # Deduct amount from balance
        success = await self.bot.db.update_user_balance(interaction.user.id, -amount)
        if not success:
            embed = discord.Embed(
                title="❌ Transaction Failed",
                description="Could not process investment. Please try again.",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create investment record
        investment_id = await self.bot.db.create_investment(
            user_id=interaction.user.id,
            amount=amount,
            investment_type=investment_type,
            expected_return=expected_return,
            maturity_date=maturity_date
        )
        
        # Log transaction
        await self.bot.db.log_transaction(
            user_id=interaction.user.id,
            guild_id=interaction.guild.id if interaction.guild else None,
            transaction_type='investment',
            amount=-amount,
            description=f'Investment: {inv_type["name"]}'
        )
        
        # Create response embed
        expected_payout = int(amount * expected_return)
        profit = expected_payout - amount
        
        embed = discord.Embed(
            title=f"{inv_type['emoji']} Investment Created!",
            description=f"You invested {format_currency(amount)} in **{inv_type['name']}**",
            color=0x00FF00
        )
        
        embed.add_field(
            name="💰 Expected Return",
            value=f"{format_currency(expected_payout)} ({expected_return:.2f}x)",
            inline=True
        )
        
        embed.add_field(
            name="📈 Potential Profit",
            value=format_currency(profit),
            inline=True
        )
        
        embed.add_field(
            name="⏰ Matures In",
            value=f"{days_to_mature} day(s)",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Risk Level",
            value=f"{inv_type['risk']*100:.0f}% chance of loss",
            inline=True
        )
        
        embed.add_field(
            name="🆔 Investment ID",
            value=f"`{investment_id}`",
            inline=True
        )
        
        embed.set_footer(text="Use /portfolio to check your investments")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="portfolio", description="View your investment portfolio")
    async def portfolio(self, interaction: discord.Interaction):
        """View user's investment portfolio."""
        if not self.bot.config.economy_enabled or not self.bot.config.investment_enabled:
            embed = discord.Embed(
                title="❌ Feature Disabled",
                description="Investment system is currently disabled.",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get user's investments
        investments = await self.bot.db.get_user_investments(interaction.user.id)
        
        if not investments:
            embed = discord.Embed(
                title="📊 Investment Portfolio",
                description="You don't have any investments yet. Use `/invest` to get started!",
                color=self.bot.config.get_embed_color()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Separate active and completed investments
        active_investments = [inv for inv in investments if inv.status == 'active']
        completed_investments = [inv for inv in investments if inv.status == 'completed']
        
        embed = discord.Embed(
            title="📊 Investment Portfolio",
            color=self.bot.config.get_embed_color()
        )
        
        if active_investments:
            active_value = sum(inv.amount for inv in active_investments)
            active_text = f"**Total Invested:** {format_currency(active_value)}\n"
            active_text += f"**Active Investments:** {len(active_investments)}\n\n"
            
            for inv in active_investments[:5]:  # Show up to 5 recent
                inv_type = self.investment_types.get(inv.investment_type, {})
                emoji = inv_type.get('emoji', '💼')
                name = inv_type.get('name', inv.investment_type.title())
                
                time_left = inv.maturity_date - datetime.now(timezone.utc)
                if time_left.total_seconds() > 0:
                    days_left = time_left.days
                    hours_left = time_left.seconds // 3600
                    time_str = f"{days_left}d {hours_left}h" if days_left > 0 else f"{hours_left}h"
                else:
                    time_str = "**READY TO COLLECT**"
                
                expected_return = int(inv.amount * inv.expected_return)
                
                active_text += f"{emoji} **{name}**\n"
                active_text += f"Amount: {format_currency(inv.amount)} → {format_currency(expected_return)}\n"
                active_text += f"Time left: {time_str}\n\n"
            
            if len(active_investments) > 5:
                active_text += f"*...and {len(active_investments) - 5} more*"
            
            embed.add_field(
                name="🟢 Active Investments",
                value=active_text,
                inline=False
            )
        
        if completed_investments:
            total_invested = sum(inv.amount for inv in completed_investments)
            total_returned = sum(int(inv.amount * inv.actual_return) for inv in completed_investments if inv.actual_return)
            profit = total_returned - total_invested
            
            completed_text = f"**Total Invested:** {format_currency(total_invested)}\n"
            completed_text += f"**Total Returned:** {format_currency(total_returned)}\n"
            completed_text += f"**Net Profit:** {format_currency(profit)}\n"
            completed_text += f"**Completed Investments:** {len(completed_investments)}"
            
            embed.add_field(
                name="✅ Investment History",
                value=completed_text,
                inline=False
            )
        
        embed.set_footer(text="Mature investments are automatically collected")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="investment-info", description="Get information about investment types")
    async def investment_info(self, interaction: discord.Interaction):
        """Display information about available investment types."""
        embed = discord.Embed(
            title="💼 Investment Guide",
            description="Choose your investment strategy based on your risk tolerance:",
            color=self.bot.config.get_embed_color()
        )
        
        for inv_type, details in self.investment_types.items():
            risk_desc = "Low" if details["risk"] < 0.2 else "Medium" if details["risk"] < 0.35 else "High"
            
            field_text = f"**Duration:** {details['min_days']}-{details['max_days']} days\n"
            field_text += f"**Returns:** {details['min_return']:.1f}x - {details['max_return']:.1f}x\n"
            field_text += f"**Risk Level:** {risk_desc} ({details['risk']*100:.0f}% loss chance)\n"
            field_text += f"**Best For:** "
            
            if inv_type == "conservative":
                field_text += "Steady, guaranteed profits"
            elif inv_type == "balanced":
                field_text += "Moderate risk with good returns"
            else:
                field_text += "High risk, high reward players"
            
            embed.add_field(
                name=f"{details['emoji']} {details['name']}",
                value=field_text,
                inline=True
            )
        
        embed.add_field(
            name="💡 Tips",
            value=f"• Minimum investment: {format_currency(self.bot.config.investment_min_amount)}\n"
                  f"• Maximum investment: {format_currency(self.bot.config.investment_max_amount)}\n"
                  f"• Investments mature automatically\n"
                  f"• Higher risk = higher potential rewards\n"
                  f"• Diversify your portfolio for best results",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    """Load the Investment cog."""
    await bot.add_cog(InvestmentCog(bot))
