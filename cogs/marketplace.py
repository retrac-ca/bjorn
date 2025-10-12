"""
Marketplace Commands Cog

This module contains marketplace-related slash commands for the Bjorn bot.
"""

import discord
from discord import app_commands
from discord.ext import commands

from utils.logger import get_logger
from utils.helpers import format_currency
from utils.decorators import log_command_usage


class MarketplaceCog(commands.Cog, name="Marketplace"):
    """
    User-driven marketplace cog with slash commands.

    Allows users to list, browse, buy, and remove their own marketplace listings.
    """

    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)

    @app_commands.command(name="listings", description="Browse marketplace listings")
    async def listings(self, interaction: discord.Interaction):
        listings = await self.bot.db.list_market_listings(interaction.guild.id)
        if not listings:
            return await interaction.response.send_message("🚫 No marketplace listings.", ephemeral=True)

        embed = discord.Embed(title="🛒 Marketplace Listings", color=0x00FF00)
        for lst in listings[:10]:
            item = await self.bot.db.get_item(lst.item_id)
            seller = await self.bot.fetch_user(lst.seller_id)
            embed.add_field(
                name=f"ID {lst.id}: {item.emoji} {item.name}",
                value=(
                    f"Price: {format_currency(lst.price)} • Qty: {lst.quantity} • "
                    f"Seller: {seller.display_name}"
                ),
                inline=False
            )
        if len(listings) > 10:
            embed.set_footer(text=f"And {len(listings)-10} more...")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="listitem", description="List your item for sale")
    @app_commands.describe(item_name="Store item name", price="Price per unit", quantity="Quantity to list")
    async def listitem(self, interaction: discord.Interaction, item_name: str, price: int, quantity: int = 1):
        store_items = await self.bot.db.list_store_items(interaction.guild.id)
        lookup = {it.name.lower(): it for it in store_items}
        item = lookup.get(item_name.lower())
        if not item:
            return await interaction.response.send_message(
                "❌ Item not found in store, cannot list.", ephemeral=True
            )

        inv = await self.bot.db.get_inventory_item(interaction.user.id, item.id)
        if not inv or inv.quantity < quantity:
            return await interaction.response.send_message(
                "❌ You do not have enough of that item.", ephemeral=True
            )

        listing_id = await self.bot.db.create_market_listing(
            seller_id=interaction.user.id,
            guild_id=interaction.guild.id,
            item_id=item.id,
            price=price,
            quantity=quantity
        )
        await self.bot.db.update_inventory(interaction.user.id, item.id, -quantity)
        await interaction.response.send_message(
            f"✅ Listed {quantity}× {item.name} at {format_currency(price)} each (Listing ID {listing_id})"
        )

    @app_commands.command(name="buylisting", description="Buy from a marketplace listing")
    @app_commands.describe(listing_id="ID of the listing", quantity="Quantity to buy")
    async def buylisting(self, interaction: discord.Interaction, listing_id: int, quantity: int = 1):
        listing = await self.bot.db.get_market_listing(listing_id)
        if not listing:
            return await interaction.response.send_message("❌ Listing not found.", ephemeral=True)

        if listing.quantity < quantity:
            return await interaction.response.send_message("❌ Not enough quantity available.", ephemeral=True)

        total_price = listing.price * quantity
        user = await self.bot.db.get_user(
            interaction.user.id, interaction.user.name, interaction.user.discriminator
        )
        if user.balance < total_price:
            return await interaction.response.send_message("❌ Insufficient funds.", ephemeral=True)

        # Transfer funds & inventory
        await self.bot.db.update_user_balance(interaction.user.id, -total_price)
        await self.bot.db.update_user_balance(listing.seller_id, total_price)
        await self.bot.db.update_market_listing(listing_id, -quantity)
        await self.bot.db.add_inventory(interaction.user.id, listing.item_id, quantity)

        await interaction.response.send_message(
            f"✅ Purchased {quantity}× listing #{listing_id} for {format_currency(total_price)}"
        )

    @app_commands.command(name="removemylisting", description="Remove your marketplace listing")
    @app_commands.describe(listing_id="ID of your listing")
    async def removemylisting(self, interaction: discord.Interaction, listing_id: int):
        listing = await self.bot.db.get_market_listing(listing_id)
        if not listing or listing.seller_id != interaction.user.id:
            return await interaction.response.send_message("❌ Listing not found or not yours.", ephemeral=True)

        await self.bot.db.update_inventory(interaction.user.id, listing.item_id, listing.quantity)
        await self.bot.db.remove_market_listing(listing_id)
        await interaction.response.send_message(
            f"🗑️ Removed listing #{listing_id} and returned items to your inventory."
        )


async def setup(bot):
    """Load the Marketplace cog."""
    await bot.add_cog(MarketplaceCog(bot))
