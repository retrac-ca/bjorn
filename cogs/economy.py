"""
Economy Commands Cog

This module contains all economy-related commands for the Saint Toadle bot.
It handles earning coins, checking balances, daily bonuses, crime activities,
and other economic features.
"""

import random
from datetime import datetime, timezone, timedelta
from typing import Optional

import discord
from discord.ext import commands

from utils.decorators import (
    requires_economy, requires_balance, log_command_usage, 
    typing, guild_only, require_database
)
from utils.helpers import format_currency, get_random_success_message, validate_amount
from utils.logger import get_logger


class EconomyCog(commands.Cog, name="Economy"):
    """
    Economy commands cog.
    
    This cog provides all economy-related functionality including
    earning coins, daily bonuses, crime activities, and balance management.
    """
    
    def __init__(self, bot):
        """
        Initialize the economy cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
        self.logger = get_logger(__name__)
        
        # Cache for cooldowns to improve performance
        self._earn_cooldowns = {}
        self._crime_cooldowns = {}
        
    @commands.command(name='earn', aliases=['work'], help="Earn coins through work")
    @require_database
    @requires_economy
    @log_command_usage
    @typing
    async def earn_coins(self, ctx: commands.Context):
        """
        Earn coins through work.
        
        Users can earn a random amount of coins within the configured range.
        Has a cooldown to prevent spam.
        """
        user_id = ctx.author.id
        current_time = datetime.now(timezone.utc)
        
        # Check cooldown (5 minutes)
        cooldown_time = timedelta(minutes=5)
        last_earn = self._earn_cooldowns.get(user_id)
        
        if last_earn and current_time - last_earn < cooldown_time:
            time_left = cooldown_time - (current_time - last_earn)
            minutes = int(time_left.total_seconds() // 60)
            seconds = int(time_left.total_seconds() % 60)
            
            embed = discord.Embed(
                title="⏰ Cooldown Active",
                description=f"You can work again in {minutes}m {seconds}s",
                color=0xFFA500
            )
            await ctx.send(embed=embed)
            return
        
        # Get or create user
        user = await self.bot.db.get_user(ctx.author.id, ctx.author.name, ctx.author.discriminator)
        
        # Generate random earnings
        min_earn = self.bot.config.earn_min
        max_earn = self.bot.config.earn_max
        earnings = random.randint(min_earn, max_earn)
        
        # Update user balance
        success = await self.bot.db.update_user_balance(user_id, earnings)
        
        if not success:
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to update your balance. Please try again.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        # Log transaction
        await self.bot.db.log_transaction(
            user_id=user_id,
            guild_id=ctx.guild.id,
            transaction_type='earn',
            amount=earnings,
            description='Work earnings'
        )
        
        # Set cooldown
        self._earn_cooldowns[user_id] = current_time
        
        # Create response embed
        work_activities = [
            "worked at the factory", "delivered packages", "wrote code",
            "fixed computers", "taught a class", "cleaned offices",
            "painted houses", "walked dogs", "did freelance work",
            "helped at a restaurant", "organized inventory", "repaired electronics"
        ]
        
        activity = random.choice(work_activities)
        new_balance = user.balance + earnings
        
        embed = discord.Embed(
            title="💼 Work Complete",
            description=f"You {activity} and earned {format_currency(earnings)}!",
            color=0x00FF00
        )
        embed.add_field(
            name="💰 New Balance", 
            value=format_currency(new_balance), 
            inline=True
        )
        embed.add_field(
            name="⏰ Next Work", 
            value="5 minutes", 
            inline=True
        )
        embed.set_footer(text=get_random_success_message())
        
        await ctx.send(embed=embed)
    
    @commands.command(name='balance', aliases=['bal', 'money'], help="Check your current balance")
    @require_database
    @requires_economy
    @log_command_usage
    async def check_balance(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """
        Check balance for yourself or another user.
        
        Args:
            member: Optional member to check balance for
        """
        target = member or ctx.author
        user = await self.bot.db.get_user(target.id, target.name, target.discriminator)
        
        embed = discord.Embed(
            title=f"💰 {target.display_name}'s Balance",
            color=self.bot.config.get_embed_color()
        )
        
        embed.add_field(
            name="💵 Wallet",
            value=format_currency(user.balance),
            inline=True
        )
        
        embed.add_field(
            name="🏦 Bank",
            value=format_currency(user.bank_balance),
            inline=True
        )
        
        total_wealth = user.balance + user.bank_balance
        embed.add_field(
            name="💎 Total Wealth",
            value=format_currency(total_wealth),
            inline=True
        )
        
        embed.add_field(
            name="📊 Statistics",
            value=f"**Total Earned:** {format_currency(user.total_earned)}\n"
                  f"**Total Spent:** {format_currency(user.total_spent)}\n"
                  f"**Level:** {user.level}",
            inline=False
        )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='daily', help="Claim your daily bonus")
    @require_database
    @requires_economy
    @log_command_usage
    @typing
    async def daily_bonus(self, ctx: commands.Context):
        """
        Claim daily bonus coins.
        
        Users can claim a daily bonus once every 24 hours.
        """
        user_id = ctx.author.id
        
        # Check if user can claim daily bonus
        can_claim = await self.bot.db.can_use_daily(user_id)
        
        if not can_claim:
            user = await self.bot.db.get_user(user_id, ctx.author.name, ctx.author.discriminator)
            next_claim = user.last_daily + timedelta(hours=24)
            time_left = next_claim - datetime.now(timezone.utc)
            
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            
            embed = discord.Embed(
                title="⏰ Daily Already Claimed",
                description=f"You can claim your next daily bonus in {hours}h {minutes}m",
                color=0xFFA500
            )
            await ctx.send(embed=embed)
            return
        
        # Generate random daily bonus
        min_bonus = self.bot.config.daily_bonus_min
        max_bonus = self.bot.config.daily_bonus_max
        bonus_amount = random.randint(min_bonus, max_bonus)
        
        # Update user balance and daily timestamp
        success = await self.bot.db.update_user_balance(user_id, bonus_amount)
        if success:
            await self.bot.db.use_daily(user_id)
        
        if not success:
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to claim daily bonus. Please try again.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        # Log transaction
        await self.bot.db.log_transaction(
            user_id=user_id,
            guild_id=ctx.guild.id,
            transaction_type='daily',
            amount=bonus_amount,
            description='Daily bonus'
        )
        
        user = await self.bot.db.get_user(user_id, ctx.author.name, ctx.author.discriminator)
        
        embed = discord.Embed(
            title="🎁 Daily Bonus Claimed!",
            description=f"You received {format_currency(bonus_amount)} as your daily bonus!",
            color=0x00FF00
        )
        embed.add_field(
            name="💰 New Balance",
            value=format_currency(user.balance),
            inline=True
        )
        embed.add_field(
            name="⏰ Next Daily",
            value="24 hours",
            inline=True
        )
        embed.set_footer(text="Come back tomorrow for another bonus!")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='crime', help="Commit a crime for potential rewards")
    @require_database
    @requires_economy
    @log_command_usage
    @typing
    async def commit_crime(self, ctx: commands.Context):
        """
        Commit a crime for potential rewards or fines.
        
        Has a chance of success or failure based on configuration.
        """
        user_id = ctx.author.id
        current_time = datetime.now(timezone.utc)
        
        # Check cooldown (10 minutes)
        cooldown_time = timedelta(minutes=10)
        last_crime = self._crime_cooldowns.get(user_id)
        
        if last_crime and current_time - last_crime < cooldown_time:
            time_left = cooldown_time - (current_time - last_crime)
            minutes = int(time_left.total_seconds() // 60)
            seconds = int(time_left.total_seconds() % 60)
            
            embed = discord.Embed(
                title="🚓 Laying Low",
                description=f"You need to lay low for {minutes}m {seconds}s before committing another crime",
                color=0xFFA500
            )
            await ctx.send(embed=embed)
            return
        
        # Get user
        user = await self.bot.db.get_user(user_id, ctx.author.name, ctx.author.discriminator)
        
        # Determine success/failure
        success_chance = self.bot.config.crime_success_rate
        is_successful = random.random() < success_chance
        
        crimes = [
            "robbed a bank", "pickpocketed someone", "hacked a system",
            "smuggled goods", "ran a con game", "stole a car",
            "broke into a house", "sold fake items", "cheated at cards",
            "ran an illegal casino", "counterfeited money", "hijacked a truck"
        ]
        
        crime_activity = random.choice(crimes)
        
        if is_successful:
            # Successful crime - give reward
            reward_min = self.bot.config.crime_reward_min
            reward_max = self.bot.config.crime_reward_max
            reward = random.randint(reward_min, reward_max)
            
            await self.bot.db.update_user_balance(user_id, reward)
            
            # Log transaction
            await self.bot.db.log_transaction(
                user_id=user_id,
                guild_id=ctx.guild.id,
                transaction_type='crime_success',
                amount=reward,
                description=f'Crime: {crime_activity}'
            )
            
            embed = discord.Embed(
                title="💰 Crime Successful!",
                description=f"You {crime_activity} and got away with {format_currency(reward)}!",
                color=0x00FF00
            )
            embed.add_field(
                name="💰 New Balance",
                value=format_currency(user.balance + reward),
                inline=True
            )
        else:
            # Failed crime - apply fine
            fine_min = self.bot.config.crime_fine_min
            fine_max = self.bot.config.crime_fine_max
            fine = random.randint(fine_min, fine_max)
            
            # Don't let balance go negative
            actual_fine = min(fine, user.balance)
            
            if actual_fine > 0:
                await self.bot.db.update_user_balance(user_id, -actual_fine)
            
            # Log transaction
            await self.bot.db.log_transaction(
                user_id=user_id,
                guild_id=ctx.guild.id,
                transaction_type='crime_failure',
                amount=-actual_fine,
                description=f'Crime fine: {crime_activity}'
            )
            
            embed = discord.Embed(
                title="🚔 Crime Failed!",
                description=f"You tried to {crime_activity[:-2]} but got caught!",
                color=0xFF0000
            )
            
            if actual_fine > 0:
                embed.add_field(
                    name="💸 Fine Paid",
                    value=format_currency(actual_fine),
                    inline=True
                )
                embed.add_field(
                    name="💰 New Balance",
                    value=format_currency(user.balance - actual_fine),
                    inline=True
                )
            else:
                embed.add_field(
                    name="🍀 Lucky Break",
                    value="You're too poor to pay a fine!",
                    inline=False
                )
        
        # Set cooldown
        self._crime_cooldowns[user_id] = current_time
        
        embed.add_field(
            name="⏰ Next Crime",
            value="10 minutes",
            inline=True
        )
        embed.set_footer(text="Crime doesn't pay... or does it?")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='give', aliases=['pay'], help="Give coins to another user")
    @require_database
    @requires_economy
    @log_command_usage
    @typing
    @guild_only
    async def give_coins(self, ctx: commands.Context, member: discord.Member, amount: str):
        """
        Give coins to another user.
        
        Args:
            member: Member to give coins to
            amount: Amount to give
        """
        if member.bot:
            embed = discord.Embed(
                title="❌ Invalid Target",
                description="You cannot give coins to bots.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        if member.id == ctx.author.id:
            embed = discord.Embed(
                title="❌ Invalid Target",
                description="You cannot give coins to yourself.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        # Get sender
        sender = await self.bot.db.get_user(ctx.author.id, ctx.author.name, ctx.author.discriminator)
        
        # Validate amount
        parsed_amount = validate_amount(amount, minimum=1, maximum=sender.balance)
        
        if parsed_amount is None:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description=f"Please specify a valid amount between 1 and {format_currency(sender.balance)}.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        if parsed_amount > sender.balance:
            embed = discord.Embed(
                title="💰 Insufficient Funds",
                description=f"You don't have enough coins. Your balance: {format_currency(sender.balance)}",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        # Process transfer
        sender_success = await self.bot.db.update_user_balance(ctx.author.id, -parsed_amount)
        recipient_success = await self.bot.db.update_user_balance(member.id, parsed_amount)
        
        if not (sender_success and recipient_success):
            # Rollback if needed
            if sender_success:
                await self.bot.db.update_user_balance(ctx.author.id, parsed_amount)
            
            embed = discord.Embed(
                title="❌ Transfer Failed",
                description="The transfer could not be completed. Please try again.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        # Log transactions
        await self.bot.db.log_transaction(
            user_id=ctx.author.id,
            guild_id=ctx.guild.id,
            transaction_type='transfer_sent',
            amount=-parsed_amount,
            description=f'Transfer to {member.display_name}',
            related_user_id=member.id
        )
        
        await self.bot.db.log_transaction(
            user_id=member.id,
            guild_id=ctx.guild.id,
            transaction_type='transfer_received',
            amount=parsed_amount,
            description=f'Transfer from {ctx.author.display_name}',
            related_user_id=ctx.author.id
        )
        
        embed = discord.Embed(
            title="💸 Transfer Complete",
            description=f"{ctx.author.mention} gave {format_currency(parsed_amount)} to {member.mention}!",
            color=0x00FF00
        )
        embed.add_field(
            name=f"{ctx.author.display_name}'s Balance",
            value=format_currency(sender.balance - parsed_amount),
            inline=True
        )
        embed.set_footer(text="Generosity is rewarding!")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='leaderboard', aliases=['lb', 'top'], help="View the richest users")
    @require_database
    @requires_economy
    @log_command_usage
    async def leaderboard(self, ctx: commands.Context, page: int = 1):
        """
        Display the wealth leaderboard.
        
        Args:
            page: Page number to view
        """
        users_per_page = 10
        offset = (page - 1) * users_per_page
        
        # Get leaderboard data
        leaderboard_data = await self.bot.db.get_leaderboard(limit=users_per_page)
        
        if not leaderboard_data:
            embed = discord.Embed(
                title="📊 Wealth Leaderboard",
                description="No users found in the leaderboard.",
                color=self.bot.config.get_embed_color()
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="📊 Wealth Leaderboard",
            color=self.bot.config.get_embed_color()
        )
        
        leaderboard_text = ""
        for i, user_data in enumerate(leaderboard_data, start=offset + 1):
            # Try to get user from Discord
            try:
                user = self.bot.get_user(user_data.id)
                display_name = user.display_name if user else f"User#{user_data.id}"
            except:
                display_name = f"User#{user_data.id}"
            
            total_wealth = user_data.balance + user_data.bank_balance
            
            # Add medal emojis for top 3
            medal = ""
            if i == 1:
                medal = "🥇 "
            elif i == 2:
                medal = "🥈 "
            elif i == 3:
                medal = "🥉 "
            
            leaderboard_text += f"{medal}**{i}.** {display_name} - {format_currency(total_wealth)}\n"
        
        embed.description = leaderboard_text
        embed.set_footer(text=f"Page {page} • Use {ctx.prefix}leaderboard <page> to view other pages")
        
        await ctx.send(embed=embed)


async def setup(bot):
    """Load the Economy cog."""
    await bot.add_cog(EconomyCog(bot))