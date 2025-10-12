"""
Reminder System - Birthday and international day reminders
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List

import discord
from discord import app_commands
from discord.ext import commands, tasks

from utils.logger import get_logger
from utils.helpers import parse_time_string, format_time_delta


class RemindersCog(commands.Cog, name="Reminders"):
    """Birthday and reminder system"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)
        self.reminders: Dict[int, List[dict]] = {}  # user_id: [{time, message}]
        self.birthdays: Dict[int, str] = {}  # user_id: "MM-DD"
        
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    @app_commands.command(name="remind", description="Set a reminder")
    @app_commands.describe(
        time="Time until reminder (e.g., 1h, 30m, 2d)",
        message="Reminder message"
    )
    async def remind(self, interaction: discord.Interaction, time: str, message: str):
        """Create a reminder"""
        time_delta = parse_time_string(time)
        
        if not time_delta:
            await interaction.response.send_message(
                "❌ Invalid time format! Use: 1h, 30m, 2d, etc.",
                ephemeral=True
            )
            return

        if time_delta.total_seconds() < 60:
            await interaction.response.send_message(
                "❌ Minimum reminder time is 1 minute!",
                ephemeral=True
            )
            return

        if time_delta.total_seconds() > 86400 * 30:  # 30 days max
            await interaction.response.send_message(
                "❌ Maximum reminder time is 30 days!",
                ephemeral=True
            )
            return

        # Store reminder
        reminder_time = datetime.now() + time_delta
        
        if interaction.user.id not in self.reminders:
            self.reminders[interaction.user.id] = []
        
        self.reminders[interaction.user.id].append({
            'time': reminder_time,
            'message': message,
            'channel_id': interaction.channel_id
        })

        embed = discord.Embed(
            title="⏰ Reminder Set!",
            description=f"I'll remind you about: **{message}**",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="When",
            value=f"<t:{int(reminder_time.timestamp())}:R>",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="reminders", description="View your active reminders")
    async def view_reminders(self, interaction: discord.Interaction):
        """List all active reminders"""
        if interaction.user.id not in self.reminders or not self.reminders[interaction.user.id]:
            await interaction.response.send_message(
                "You don't have any active reminders!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="📋 Your Reminders",
            color=discord.Color.blue()
        )

        for idx, reminder in enumerate(self.reminders[interaction.user.id], 1):
            time_remaining = reminder['time'] - datetime.now()
            embed.add_field(
                name=f"#{idx} - {reminder['message'][:50]}",
                value=f"<t:{int(reminder['time'].timestamp())}:R>",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="birthday", description="Set your birthday")
    @app_commands.describe(
        month="Birth month (1-12)",
        day="Birth day (1-31)"
    )
    async def set_birthday(self, interaction: discord.Interaction, month: int, day: int):
        """Set user birthday"""
        if not (1 <= month <= 12):
            await interaction.response.send_message(
                "❌ Month must be between 1-12!",
                ephemeral=True
            )
            return

        if not (1 <= day <= 31):
            await interaction.response.send_message(
                "❌ Day must be between 1-31!",
                ephemeral=True
            )
            return

        # Store birthday (TODO: Add to database)
        self.birthdays[interaction.user.id] = f"{month:02d}-{day:02d}"

        embed = discord.Embed(
            title="🎂 Birthday Set!",
            description=f"Your birthday is set to **{month}/{day}**",
            color=discord.Color.green()
        )
        embed.set_footer(text="We'll wish you happy birthday when the day comes!")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="nextbirthday", description="Check when your next birthday is")
    async def next_birthday(self, interaction: discord.Interaction):
        """Check next birthday"""
        if interaction.user.id not in self.birthdays:
            await interaction.response.send_message(
                "❌ You haven't set your birthday yet! Use `/birthday` to set it.",
                ephemeral=True
            )
            return

        birthday_str = self.birthdays[interaction.user.id]
        month, day = map(int, birthday_str.split('-'))
        
        now = datetime.now()
        next_birthday = datetime(now.year, month, day)
        
        if next_birthday < now:
            next_birthday = datetime(now.year + 1, month, day)
        
        days_until = (next_birthday - now).days

        embed = discord.Embed(
            title="🎉 Next Birthday",
            description=f"Your birthday is in **{days_until} days**!",
            color=discord.Color.purple()
        )
        embed.add_field(
            name="Date",
            value=f"{month}/{day}",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    @tasks.loop(minutes=1)
    async def check_reminders(self):
        """Check and send due reminders"""
        now = datetime.now()
        
        for user_id, reminders in list(self.reminders.items()):
            for reminder in reminders[:]:
                if now >= reminder['time']:
                    # Send reminder
                    try:
                        channel = self.bot.get_channel(reminder['channel_id'])
                        if channel:
                            user = await self.bot.fetch_user(user_id)
                            embed = discord.Embed(
                                title="⏰ Reminder!",
                                description=reminder['message'],
                                color=discord.Color.gold()
                            )
                            await channel.send(f"{user.mention}", embed=embed)
                        
                        # Remove reminder
                        self.reminders[user_id].remove(reminder)
                        
                    except Exception as e:
                        self.logger.error(f"Failed to send reminder: {e}")
            
            # Clean up empty lists
            if not self.reminders[user_id]:
                del self.reminders[user_id]

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(RemindersCog(bot))