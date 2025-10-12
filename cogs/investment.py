"""
Investment System - Invest money with risk/reward
"""
import random
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks

from utils.logger import get_logger


class InvestmentCog(commands.Cog, name="Investment"):
    """Investment and passive income system"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)
        self.active_investments = {}  # user_id: {amount, end_time, multiplier}
        
        if self.bot.config.daily_interest_enabled:
            self.daily_interest.start()

    def cog_unload(self):
        if self.bot.config.daily_interest_enabled:
            self.daily_interest.cancel()

    @app_commands.command(name="invest", description="Invest money for potential returns")
    @app_commands.describe(
        amount="Amount to invest",
        duration="Investment duration in hours (1-24)"
    )
    async def invest(self, interaction: discord.Interaction, amount: int, duration: int = 6):
        """Invest money with risk/reward"""
        if amount < self.bot.config.investment_min_amount:
            await interaction.response.send_message(
                f"❌ Minimum investment: ${self.bot.config.investment_min_amount:,}",
                ephemeral=True
            )
            return

        if amount > self.bot.config.investment_max_amount:
            await interaction.response.send_message(
                f"❌ Maximum investment: ${self.bot.config.investment_max_amount:,}",
                ephemeral=True
            )
            return

        if not (1 <= duration <= 24):
            await interaction.response.send_message(
                "❌ Duration must be between 1-24 hours",
                ephemeral=True
            )
            return

        user = await self.bot.db.get_user(interaction.user.id)
        if user.balance < amount:
            await interaction.response.send_message(
                f"❌ Insufficient funds! You have ${user.balance:,}",
                ephemeral=True
            )
            return

        # Check if user already has active investment
        if interaction.user.id in self.active_investments:
            await interaction.response.send_message(
                "❌ You already have an active investment! Wait for it to mature.",
                ephemeral=True
            )
            return

        # Deduct investment amount
        await self.bot.db.update_user_balance(interaction.user.id, -amount)

        # Calculate potential return (higher duration = better multiplier)
        base_multiplier = random.uniform(
            self.bot.config.investment_min_return,
            self.bot.config.investment_max_return
        )
        duration_bonus = 1 + (duration * 0.02)  # 2% bonus per hour
        multiplier = base_multiplier * duration_bonus

        # Store investment
        end_time = datetime.now() + timedelta(hours=duration)
        self.active_investments[interaction.user.id] = {
            'amount': amount,
            'end_time': end_time,
            'multiplier': multiplier
        }

        await self.bot.db.log_transaction(
            interaction.user.id,
            interaction.guild.id if interaction.guild else 0,
            'investment_start',
            -amount,
            f'{duration}h investment'
        )

        embed = discord.Embed(
            title="📈 Investment Started",
            description=f"Invested **${amount:,}** for **{duration} hours**",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Expected Return",
            value=f"{multiplier:.2f}x (${int(amount * multiplier):,})",
            inline=True
        )
        embed.add_field(
            name="Matures",
            value=f"<t:{int(end_time.timestamp())}:R>",
            inline=True
        )
        embed.set_footer(text="Use /collect to claim when ready!")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="collect", description="Collect your investment returns")
    async def collect(self, interaction: discord.Interaction):
        """Collect matured investment"""
        if interaction.user.id not in self.active_investments:
            await interaction.response.send_message(
                "❌ You don't have any active investments!",
                ephemeral=True
            )
            return

        investment = self.active_investments[interaction.user.id]
        now = datetime.now()

        if now < investment['end_time']:
            remaining = investment['end_time'] - now
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            
            await interaction.response.send_message(
                f"⏰ Investment not ready! Wait {hours}h {minutes}m",
                ephemeral=True
            )
            return

        # Determine if investment succeeded or failed
        failed = random.random() < self.bot.config.investment_fail_rate

        if failed:
            # Lost investment
            lost_amount = investment['amount']
            del self.active_investments[interaction.user.id]

            embed = discord.Embed(
                title="📉 Investment Failed!",
                description=f"The market crashed! You lost your investment of **${lost_amount:,}**",
                color=discord.Color.red()
            )

            await self.bot.db.log_transaction(
                interaction.user.id,
                interaction.guild.id if interaction.guild else 0,
                'investment_fail',
                0,
                'Investment failed'
            )
        else:
            # Successful investment
            returns = int(investment['amount'] * investment['multiplier'])
            profit = returns - investment['amount']
            
            await self.bot.db.update_user_balance(interaction.user.id, returns)
            del self.active_investments[interaction.user.id]

            embed = discord.Embed(
                title="📈 Investment Matured!",
                description=f"Your investment paid off!",
                color=discord.Color.green()
            )
            embed.add_field(name="Invested", value=f"${investment['amount']:,}", inline=True)
            embed.add_field(name="Returns", value=f"${returns:,}", inline=True)
            embed.add_field(name="Profit", value=f"${profit:,}", inline=True)

            await self.bot.db.log_transaction(
                interaction.user.id,
                interaction.guild.id if interaction.guild else 0,
                'investment_success',
                profit,
                f'Investment return: {investment["multiplier"]:.2f}x'
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="investment", description="Check your active investment")
    async def investment_status(self, interaction: discord.Interaction):
        """Check investment status"""
        if interaction.user.id not in self.active_investments:
            await interaction.response.send_message(
                "You don't have any active investments.",
                ephemeral=True
            )
            return

        investment = self.active_investments[interaction.user.id]
        now = datetime.now()
        
        if now >= investment['end_time']:
            status = "✅ Ready to collect!"
        else:
            remaining = investment['end_time'] - now
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            status = f"⏰ {hours}h {minutes}m remaining"

        embed = discord.Embed(
            title="📊 Your Investment",
            color=discord.Color.blue()
        )
        embed.add_field(name="Amount", value=f"${investment['amount']:,}", inline=True)
        embed.add_field(
            name="Expected Returns",
            value=f"${int(investment['amount'] * investment['multiplier']):,}",
            inline=True
        )
        embed.add_field(name="Status", value=status, inline=False)
        embed.add_field(
            name="Matures",
            value=f"<t:{int(investment['end_time'].timestamp())}:R>",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    @tasks.loop(hours=24)
    async def daily_interest(self):
        """Apply daily interest to bank balances"""
        self.logger.info("Applying daily bank interest...")
        
        try:
            # Get users with bank balance using raw SQL query
            from sqlalchemy import select, update
            from config.database import User
            
            async with self.bot.db.session_factory() as session:
                # Get all users with positive bank balance
                result = await session.execute(
                    select(User).where(User.bank_balance > 0)
                )
                users = result.scalars().all()
                
                count = 0
                for user in users:
                    interest = int(user.bank_balance * self.bot.config.bank_interest_rate)
                    if interest > 0:
                        # Update bank balance directly
                        await session.execute(
                            update(User)
                            .where(User.id == user.id)
                            .values(bank_balance=User.bank_balance + interest)
                        )
                        count += 1
                
                await session.commit()
                self.logger.info(f"Applied interest to {count} users")
                
        except Exception as e:
            self.logger.error(f"Failed to apply interest: {e}")

    @daily_interest.before_loop
    async def before_daily_interest(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(InvestmentCog(bot))