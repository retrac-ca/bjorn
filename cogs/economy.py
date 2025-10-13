"""
Economy Commands - Work, daily rewards, crime, and transfers
"""
import random
from datetime import datetime, timezone, timedelta
from typing import Optional



import discord
from discord import app_commands
from discord.ext import commands



from utils.logger import get_logger
from utils.decorators import ensure_user_exists




class EconomyCog(commands.Cog, name="Economy"):
    """Economy system commands"""



    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)
        self.work_cooldowns = {}
        self.daily_cooldowns = {}
        self.crime_cooldowns = {}



    def _check_cooldown(self, user_id: int, cooldown_dict: dict, cooldown_seconds: int) -> Optional[int]:
        """Check if user is on cooldown, return seconds remaining or None"""
        if user_id in cooldown_dict:
            elapsed = (datetime.now() - cooldown_dict[user_id]).total_seconds()
            if elapsed < cooldown_seconds:
                return int(cooldown_seconds - elapsed)
        return None



    @app_commands.command(name="balance", description="Check your balance")
    @app_commands.describe(user="User to check (optional)")
    async def balance(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Check wallet and bank balance"""
        target = user or interaction.user
        
        db_user = await self.bot.db.get_user(target.id, target.name, target.discriminator)
        
        embed = discord.Embed(
            title=f"💰 {target.display_name}'s Balance",
            color=discord.Color.gold()
        )
        embed.add_field(name="💵 Wallet", value=f"${db_user.balance:,}", inline=True)
        embed.add_field(name="🏦 Bank", value=f"${db_user.bank_balance:,}", inline=True)
        embed.add_field(name="💎 Net Worth", value=f"${db_user.balance + db_user.bank_balance:,}", inline=True)
        
        embed.set_thumbnail(url=target.display_avatar.url)
        
        # Build footer with available attributes
        footer_parts = []
        if hasattr(db_user, 'level'):
            footer_parts.append(f"Level {db_user.level}")
        footer_parts.append(f"Total Earned: ${db_user.total_earned:,}")
        embed.set_footer(text=" • ".join(footer_parts))
        
        await interaction.response.send_message(embed=embed)



    @app_commands.command(name="work", description="Work to earn money")
    async def work(self, interaction: discord.Interaction):
        """Earn money by working (5 minute cooldown)"""
        user_id = interaction.user.id
        
        # Check cooldown (5 minutes)
        cooldown = self._check_cooldown(user_id, self.work_cooldowns, 300)
        if cooldown:
            await interaction.response.send_message(
                f"⏳ You're tired! Rest for {cooldown//60}m {cooldown%60}s",
                ephemeral=True
            )
            return



        # Generate earnings
        amount = random.randint(self.bot.config.earn_min, self.bot.config.earn_max)
        
        # Update user balance
        await self.bot.db.update_user_balance(user_id, amount)
        
        # Log transaction if method exists
        if hasattr(self.bot.db, 'log_transaction'):
            await self.bot.db.log_transaction(
                user_id, 
                interaction.guild.id if interaction.guild else 0,
                'work',
                amount,
                'Work earnings'
            )
        
        self.work_cooldowns[user_id] = datetime.now()



        # Random work messages
        jobs = [
            "delivered packages 📦",
            "coded a website 💻",
            "walked some dogs 🐕",
            "tutored students 📚",
            "fixed computers 🔧",
            "designed graphics 🎨",
            "made coffee ☕",
            "cleaned houses 🧹"
        ]
        
        embed = discord.Embed(
            title="💼 Work Complete!",
            description=f"You {random.choice(jobs)} and earned **${amount}**!",
            color=discord.Color.green()
        )
        embed.set_footer(text="Come back in 5 minutes!")
        
        await interaction.response.send_message(embed=embed)



    @app_commands.command(name="daily", description="Claim your daily bonus")
    async def daily(self, interaction: discord.Interaction):
        """Claim daily bonus (24 hour cooldown)"""
        user_id = interaction.user.id
        
        # Check if user can claim
        can_claim = await self.bot.db.can_use_daily(user_id)
        
        if not can_claim:
            user = await self.bot.db.get_user(user_id, interaction.user.name, interaction.user.discriminator)
            if user.last_daily:
                next_claim = user.last_daily + timedelta(days=1)
                remaining = next_claim - datetime.now(timezone.utc)
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                
                await interaction.response.send_message(
                    f"⏰ Daily already claimed! Come back in {hours}h {minutes}m",
                    ephemeral=True
                )
                return



        # Generate bonus with streak multiplier
        base_amount = random.randint(
            self.bot.config.daily_bonus_min,
            self.bot.config.daily_bonus_max
        )
        
        # TODO: Implement streak system
        amount = base_amount
        
        # Update balance and mark daily as used
        await self.bot.db.update_user_balance(user_id, amount)
        await self.bot.db.use_daily(user_id)
        await self.bot.db.log_transaction(
            user_id,
            interaction.guild.id if interaction.guild else 0,
            'daily',
            amount,
            'Daily bonus claim'
        )



        embed = discord.Embed(
            title="🎁 Daily Bonus Claimed!",
            description=f"You received **${amount}**!",
            color=discord.Color.gold()
        )
        embed.set_footer(text="Come back tomorrow for another bonus!")
        
        await interaction.response.send_message(embed=embed)



    @app_commands.command(name="crime", description="Commit a crime (risky!)")
    async def crime(self, interaction: discord.Interaction):
        """Attempt crime for money (10 minute cooldown)"""
        user_id = interaction.user.id
        
        # Check cooldown (10 minutes)
        cooldown = self._check_cooldown(user_id, self.crime_cooldowns, 600)
        if cooldown:
            await interaction.response.send_message(
                f"👮 The police are watching! Wait {cooldown//60}m {cooldown%60}s",
                ephemeral=True
            )
            return



        self.crime_cooldowns[user_id] = datetime.now()



        # Determine success
        success = random.random() < self.bot.config.crime_success_rate
        
        if success:
            # Crime succeeded
            amount = random.randint(
                self.bot.config.crime_reward_min,
                self.bot.config.crime_reward_max
            )
            await self.bot.db.update_user_balance(user_id, amount)
            await self.bot.db.log_transaction(
                user_id,
                interaction.guild.id if interaction.guild else 0,
                'crime_success',
                amount,
                'Successful crime earnings'
            )
            
            crimes = [
                "robbed a convenience store 🏪",
                "hacked a crypto wallet 💻",
                "pickpocketed a tourist 👜",
                "sold fake watches ⌚",
                "ran an illegal casino 🎰",
                "smuggled rare items 📦"
            ]
            
            embed = discord.Embed(
                title="😈 Crime Successful!",
                description=f"You {random.choice(crimes)} and got away with **${amount}**!",
                color=discord.Color.green()
            )
        else:
            # Crime failed
            fine = random.randint(
                self.bot.config.crime_fine_min,
                self.bot.config.crime_fine_max
            )
            
            user = await self.bot.db.get_user(user_id, interaction.user.name, interaction.user.discriminator)
            actual_fine = min(fine, user.balance)  # Can't take more than they have
            
            await self.bot.db.update_user_balance(user_id, -actual_fine)
            await self.bot.db.log_transaction(
                user_id,
                interaction.guild.id if interaction.guild else 0,
                'crime_fail',
                -actual_fine,
                'Crime failure fine'
            )
            
            fails = [
                "got caught red-handed 🚔",
                "triggered the alarm 🚨",
                "were spotted by cameras 📹",
                "got tackled by security 🛡️",
                "left fingerprints everywhere 👮",
                "tripped and fell 🤕"
            ]
            
            embed = discord.Embed(
                title="🚨 Crime Failed!",
                description=f"You {random.choice(fails)} and paid a **${actual_fine}** fine!",
                color=discord.Color.red()
            )



        embed.set_footer(text="Try again in 10 minutes!")
        await interaction.response.send_message(embed=embed)



    @app_commands.command(name="give", description="Give money to another user")
    @app_commands.describe(
        user="User to give money to",
        amount="Amount to give"
    )
    async def give(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Transfer money to another user"""
        if user.bot:
            await interaction.response.send_message("❌ You can't give money to bots!", ephemeral=True)
            return
        
        if user.id == interaction.user.id:
            await interaction.response.send_message("❌ You can't give money to yourself!", ephemeral=True)
            return
        
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
            return



        # Check sender has enough
        sender = await self.bot.db.get_user(interaction.user.id, interaction.user.name, interaction.user.discriminator)
        if sender.balance < amount:
            await interaction.response.send_message(
                f"❌ Insufficient funds! You only have ${sender.balance}",
                ephemeral=True
            )
            return



        # Process transfer
        await self.bot.db.update_user_balance(interaction.user.id, -amount)
        await self.bot.db.update_user_balance(user.id, amount)
        
        # Log both sides
        await self.bot.db.log_transaction(
            interaction.user.id,
            interaction.guild.id if interaction.guild else 0,
            'transfer_sent',
            -amount,
            f'Sent to {user.id}'
        )
        await self.bot.db.log_transaction(
            user.id,
            interaction.guild.id if interaction.guild else 0,
            'transfer_received',
            amount,
            f'Received from {interaction.user.id}'
        )



        embed = discord.Embed(
            title="💸 Transfer Complete",
            description=f"{interaction.user.mention} sent **${amount:,}** to {user.mention}!",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)



    @app_commands.command(name="leaderboard", description="View wealth rankings")
    @app_commands.describe(page="Page number (default: 1)")
    async def leaderboard(self, interaction: discord.Interaction, page: int = 1):
        """Display wealth leaderboard"""
        if page < 1:
            page = 1



        per_page = 10
        
        # Get top users by net worth
        from sqlalchemy import select, desc
        from config.database import User
        
        async with self.bot.db.session_factory() as session:
            # Get all users ordered by total wealth (balance + bank)
            result = await session.execute(
                select(User).order_by(desc(User.balance + User.bank_balance)).limit(100)
            )
            top_users = result.scalars().all()



        if not top_users:
            await interaction.response.send_message("No users found!", ephemeral=True)
            return



        # Calculate pagination
        total_pages = max(1, (len(top_users) + per_page - 1) // per_page)
        page = min(page, total_pages)
        
        offset = (page - 1) * per_page
        page_users = top_users[offset:offset + per_page]



        embed = discord.Embed(
            title="💰 Wealth Leaderboard",
            description=f"Top richest users (Page {page}/{total_pages})",
            color=discord.Color.gold()
        )



        for idx, user in enumerate(page_users, start=offset + 1):
            # Try to fetch Discord user
            try:
                discord_user = await self.bot.fetch_user(user.id)
                name = discord_user.name
            except:
                name = user.username



            medal = ""
            if idx == 1:
                medal = "🥇 "
            elif idx == 2:
                medal = "🥈 "
            elif idx == 3:
                medal = "🥉 "



            net_worth = user.balance + user.bank_balance
            embed.add_field(
                name=f"{medal}#{idx} {name}",
                value=f"💰 ${net_worth:,}\n💵 Wallet: ${user.balance:,} | 🏦 Bank: ${user.bank_balance:,}",
                inline=False
            )



        embed.set_footer(text=f"Page {page}/{total_pages}")
        
        await interaction.response.send_message(embed=embed)




async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
