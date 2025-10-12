"""
Referral System - Invite tracking and rewards
"""
import discord
from discord import app_commands
from discord.ext import commands

from utils.logger import get_logger


class ReferralCog(commands.Cog, name="Referral"):
    """Referral and invite system"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)

    @app_commands.command(name="refer", description="Refer a user and earn rewards")
    @app_commands.describe(user="User to refer")
    async def refer(self, interaction: discord.Interaction, user: discord.Member):
        """Refer a user for rewards"""
        if user.bot:
            await interaction.response.send_message(
                "❌ You can't refer bots!",
                ephemeral=True
            )
            return

        if user.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ You can't refer yourself!",
                ephemeral=True
            )
            return

        # Check if referral already exists
        from sqlalchemy import select, and_
        from config.database import Referral as ReferralModel
        
        async with self.bot.db.session_factory() as session:
            result = await session.execute(
                select(ReferralModel).where(
                    and_(
                        ReferralModel.referrer_id == interaction.user.id,
                        ReferralModel.referred_id == user.id
                    )
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                await interaction.response.send_message(
                    "❌ You've already referred this user!",
                    ephemeral=True
                )
                return

            # Create referral
            new_referral = ReferralModel(
                referrer_id=interaction.user.id,
                referred_id=user.id,
                guild_id=interaction.guild.id if interaction.guild else 0,
                bonus_amount=self.bot.config.referral_bonus
            )
            session.add(new_referral)
            await session.commit()

        # Give referral bonus
        await self.bot.db.update_user_balance(
            interaction.user.id,
            self.bot.config.referral_bonus
        )

        await self.bot.db.log_transaction(
            interaction.user.id,
            interaction.guild.id if interaction.guild else 0,
            'referral_bonus',
            self.bot.config.referral_bonus,
            f'Referred {user.id}'
        )

        embed = discord.Embed(
            title="🎉 Referral Successful!",
            description=f"You referred {user.mention} and earned **${self.bot.config.referral_bonus:,}**!",
            color=discord.Color.green()
        )
        embed.set_footer(text="Keep referring friends to earn more!")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="referrals", description="View your referral statistics")
    async def referrals(self, interaction: discord.Interaction):
        """View referral stats"""
        from sqlalchemy import select, func
        from config.database import Referral as ReferralModel

        async with self.bot.db.session_factory() as session:
            # Count total referrals
            result = await session.execute(
                select(func.count(ReferralModel.id)).where(
                    ReferralModel.referrer_id == interaction.user.id
                )
            )
            total_referrals = result.scalar() or 0

            # Get recent referrals
            result = await session.execute(
                select(ReferralModel)
                .where(ReferralModel.referrer_id == interaction.user.id)
                .order_by(ReferralModel.created_at.desc())
                .limit(10)
            )
            recent_referrals = result.scalars().all()

        if total_referrals == 0:
            await interaction.response.send_message(
                "You haven't referred anyone yet! Use `/refer @user` to start earning rewards.",
                ephemeral=True
            )
            return

        total_earned = total_referrals * self.bot.config.referral_bonus

        embed = discord.Embed(
            title="📊 Your Referral Stats",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Total Referrals",
            value=f"{total_referrals}",
            inline=True
        )
        embed.add_field(
            name="Total Earned",
            value=f"${total_earned:,}",
            inline=True
        )

        if recent_referrals:
            recent_list = []
            for ref in recent_referrals[:5]:
                try:
                    user = await self.bot.fetch_user(ref.referred_id)
                    recent_list.append(f"• {user.name}")
                except:
                    recent_list.append(f"• User {ref.referred_id}")

            embed.add_field(
                name="Recent Referrals",
                value="\n".join(recent_list),
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="referralboard", description="View top referrers")
    async def referralboard(self, interaction: discord.Interaction):
        """Display referral leaderboard"""
        from sqlalchemy import select, func
        from config.database import Referral as ReferralModel, User

        async with self.bot.db.session_factory() as session:
            # Get top referrers
            result = await session.execute(
                select(
                    ReferralModel.referrer_id,
                    func.count(ReferralModel.id).label('count')
                )
                .group_by(ReferralModel.referrer_id)
                .order_by(func.count(ReferralModel.id).desc())
                .limit(10)
            )
            top_referrers = result.all()

        if not top_referrers:
            await interaction.response.send_message(
                "No referrals yet!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🏆 Top Referrers",
            description="Most active referrers in the community",
            color=discord.Color.gold()
        )

        for idx, (referrer_id, count) in enumerate(top_referrers, 1):
            try:
                user = await self.bot.fetch_user(referrer_id)
                name = user.name
            except:
                name = f"User {referrer_id}"

            medal = ""
            if idx == 1:
                medal = "🥇 "
            elif idx == 2:
                medal = "🥈 "
            elif idx == 3:
                medal = "🥉 "

            earned = count * self.bot.config.referral_bonus

            embed.add_field(
                name=f"{medal}#{idx} {name}",
                value=f"**{count}** referrals (${earned:,} earned)",
                inline=False
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(ReferralCog(bot))