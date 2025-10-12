"""
Store & Central Bank Commands Cog

This module implements a server-controlled Store and Central Bank for Bjorn.
"""

import discord
from discord import app_commands
from discord.ext import commands

from utils.logger import get_logger
from utils.helpers import format_currency
from utils.decorators import requires_moderator

class StoreCog(commands.Cog, name="Store"):
    """
    Store and Central Bank management and user commands.
    """

    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)

    @app_commands.command(name="store", description="List server store items for sale")
    async def store(self, interaction: discord.Interaction):
        items = await self.bot.db.list_store_items(interaction.guild.id)
        if not items:
            return await interaction.response.send_message(
                "🏬 The store is empty.", ephemeral=True
            )
        embed = discord.Embed(title="🏬 Store Listings", color=0x00FF00)
        for it in items:
            embed.add_field(
                name=f"{it.emoji} {it.name}",
                value=f"Price: {format_currency(it.price)}",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="storelist", description="Add an item to the store (Admin only)")
    @requires_moderator()
    @app_commands.describe(name="Item name", price="Price in coins", emoji="Emoji for item")
    async def storelist(self, interaction: discord.Interaction, name: str, price: int, emoji: str):
        success = await self.bot.db.add_store_item(interaction.guild.id, name, price, emoji)
        if success:
            await interaction.response.send_message(
                f"✅ Added **{emoji} {name}** for {format_currency(price)}"
            )
        else:
            await interaction.response.send_message(
                "❌ That item already exists in the store.", ephemeral=True
            )

    @app_commands.command(name="storeremove", description="Remove an item from the store (Admin only)")
    @requires_moderator()
    @app_commands.describe(name="Item name to remove")
    async def storeremove(self, interaction: discord.Interaction, name: str):
        removed = await self.bot.db.remove_store_item(interaction.guild.id, name)
        if removed:
            await interaction.response.send_message(f"🗑️ Removed **{name}** from the store.")
        else:
            await interaction.response.send_message("❌ Item not found.", ephemeral=True)

    @app_commands.command(name="buyitem", description="Buy an item from the store")
    @app_commands.describe(name="Item name to buy")
    async def buyitem(self, interaction: discord.Interaction, name: str):
        user = await self.bot.db.get_user(
            interaction.user.id, interaction.user.name, interaction.user.discriminator
        )
        items = await self.bot.db.list_store_items(interaction.guild.id)
        lookup = {it.name.lower(): it for it in items}
        it = lookup.get(name.lower())
        if not it:
            return await interaction.response.send_message("❌ Item not found.", ephemeral=True)
        if user.balance < it.price:
            return await interaction.response.send_message("❌ Insufficient funds.", ephemeral=True)

        # Debit user, credit central bank, add to inventory
        await self.bot.db.update_user_balance(user.id, -it.price)
        await self.bot.db.credit_central_bank(it.price)
        await self.bot.db.add_inventory(user.id, it.id, 1)
        await self.bot.db.log_transaction(
            user.id, interaction.guild.id, 'purchase', -it.price, f"Bought {it.name}"
        )
        await interaction.response.send_message(
            f"✅ You bought **{it.emoji} {it.name}** for {format_currency(it.price)}"
        )

    @app_commands.command(name="sellitem", description="Sell an item back to the store at 50% price")
    @app_commands.describe(name="Item name to sell")
    async def sellitem(self, interaction: discord.Interaction, name: str):
        user = await self.bot.db.get_user(
            interaction.user.id, interaction.user.name, interaction.user.discriminator
        )
        items = await self.bot.db.list_store_items(interaction.guild.id)
        lookup = {it.name.lower(): it for it in items}
        it = lookup.get(name.lower())
        if not it:
            return await interaction.response.send_message(
                "❌ That item is not sold in this store.", ephemeral=True
            )
        inv = await self.bot.db.get_inventory_item(user.id, it.id)
        if not inv or inv.quantity < 1:
            return await interaction.response.send_message(
                "❌ You do not own that item.", ephemeral=True
            )
        sell_price = it.price // 2
        await self.bot.db.update_inventory(user.id, it.id, -1)
        await self.bot.db.update_user_balance(user.id, sell_price)
        await self.bot.db.credit_central_bank(sell_price)
        await self.bot.db.log_transaction(
            user.id, interaction.guild.id, 'sell', sell_price, f"Sold {it.name}"
        )
        await interaction.response.send_message(
            f"💰 You sold **{it.emoji} {it.name}** for {format_currency(sell_price)}"
        )

    @app_commands.command(name="givecoins", description="Give coins to a user (Admin only)")
    @requires_moderator()
    @app_commands.describe(user="Target user", amount="Amount of coins")
    async def givecoins(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        await self.bot.db.update_user_balance(user.id, amount)
        await interaction.response.send_message(
            f"✅ Gave {format_currency(amount)} to {user.mention}"
        )

    @app_commands.command(name="takecoins", description="Take coins from a user into the central bank (Admin only)")
    @requires_moderator()
    @app_commands.describe(user="Target user", amount="Amount of coins")
    async def takecoins(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        dbuser = await self.bot.db.get_user(user.id, user.name, user.discriminator)
        deduct = min(amount, dbuser.balance)
        await self.bot.db.update_user_balance(user.id, -deduct)
        await self.bot.db.credit_central_bank(deduct)
        await interaction.response.send_message(
            f"✅ Took {format_currency(deduct)} from {user.mention}"
        )

    @app_commands.command(name="centralbank", description="Show central bank statistics")
    async def centralbank(self, interaction: discord.Interaction):
        cb = await self.bot.db.get_central_bank()
        embed = discord.Embed(title="🏦 Central Bank", color=0x00FFFF)
        embed.add_field(name="Vault Balance", value=format_currency(cb.total_funds), inline=True)
        embed.add_field(
            name="Last Updated",
            value=f"<t:{int(cb.last_updated.timestamp())}:F>",
            inline=True
        )
        # Placeholder for circulation stat
        embed.add_field(name="Coins in Circulation", value="N/A", inline=False)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(StoreCog(bot))
