"""
Marketplace Commands - User-to-user item trading
"""
import discord
from discord import app_commands
from discord.ext import commands

from utils.logger import get_logger


class MarketplaceCog(commands.Cog, name="Marketplace"):
    """User marketplace for trading items"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)

    @app_commands.command(name="listitem", description="List an item from your inventory for sale")
    @app_commands.describe(
        item_name="Name of item from your inventory",
        price="Your asking price",
        quantity="Quantity to list (default: 1)"
    )
    async def listitem(self, interaction: discord.Interaction, item_name: str, price: int, quantity: int = 1):
        """List item on marketplace"""
        if price <= 0:
            await interaction.response.send_message(
                "❌ Price must be positive!",
                ephemeral=True
            )
            return

        if quantity <= 0:
            await interaction.response.send_message(
                "❌ Quantity must be positive!",
                ephemeral=True
            )
            return

        # Check user's inventory
        inventory = await self.bot.db.get_user_inventory(interaction.user.id)
        item_data = None
        for item in inventory:
            if item_name.lower() in item['name'].lower():
                item_data = item
                break

        if not item_data:
            await interaction.response.send_message(
                f"❌ You don't have '{item_name}' in your inventory!",
                ephemeral=True
            )
            return

        if item_data['quantity'] < quantity:
            await interaction.response.send_message(
                f"❌ You only have {item_data['quantity']} of this item!",
                ephemeral=True
            )
            return

        # Remove from inventory
        success = await self.bot.db.update_inventory(
            interaction.user.id,
            item_data['item_id'],
            -quantity
        )

        if not success:
            await interaction.response.send_message(
                "❌ Failed to list item!",
                ephemeral=True
            )
            return

        # Create marketplace listing
        listing_id = await self.bot.db.create_market_listing(
            interaction.user.id,
            interaction.guild.id,
            item_data['item_id'],
            price,
            quantity
        )

        self.logger.info(
            f"User {interaction.user.name} (ID: {interaction.user.id}) "
            f"listed {quantity}x {item_data['name']} for ${price:,} each (Listing ID: {listing_id})"
        )

        embed = discord.Embed(
            title="📋 Item Listed!",
            description=f"**{quantity}x {item_data['emoji']} {item_data['name']}** listed on marketplace",
            color=discord.Color.green()
        )
        embed.add_field(name="Price Each", value=f"${price:,}", inline=True)
        embed.add_field(name="Total Value", value=f"${price * quantity:,}", inline=True)
        embed.add_field(name="Listing ID", value=f"#{listing_id}", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="marketplace", description="Browse user marketplace listings")
    async def marketplace(self, interaction: discord.Interaction):
        """View marketplace listings"""
        from sqlalchemy import select
        from config.database import MarketListing, Item, User

        async with self.bot.db.session_factory() as session:
            result = await session.execute(
                select(MarketListing, Item, User)
                .join(Item, MarketListing.item_id == Item.id)
                .join(User, MarketListing.seller_id == User.id)
                .where(MarketListing.guild_id == interaction.guild.id)
            )
            listings = result.all()

        if not listings:
            await interaction.response.send_message(
                "🏪 The marketplace is empty! Use `/listitem` to sell your items.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🏪 User Marketplace",
            description="Use `/buyitem <listing_id>` to purchase",
            color=discord.Color.gold()
        )

        for listing, item, seller in listings[:25]:
            total_value = listing.price * listing.quantity
            embed.add_field(
                name=f"#{listing.id} - {item.emoji} {item.name}",
                value=f"**Seller:** {seller.username}\n"
                      f"**Price:** ${listing.price:,} each\n"
                      f"**Quantity:** {listing.quantity}\n"
                      f"**Total:** ${total_value:,}",
                inline=True
            )

        embed.set_footer(text="Official shop items? Try /shop")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buyitem", description="Buy item from marketplace")
    @app_commands.describe(
        listing_id="Marketplace listing ID",
        quantity="Quantity to buy (default: all)"
    )
    async def buyitem(self, interaction: discord.Interaction, listing_id: int, quantity: int = None):
        """Purchase from marketplace"""
        from sqlalchemy import select
        from config.database import MarketListing, Item

        async with self.bot.db.session_factory() as session:
            result = await session.execute(
                select(MarketListing, Item)
                .join(Item)
                .where(MarketListing.id == listing_id)
            )
            listing_data = result.one_or_none()

        if not listing_data:
            await interaction.response.send_message(
                f"❌ Listing #{listing_id} not found!",
                ephemeral=True
            )
            return

        listing, item = listing_data

        # Check if trying to buy own listing
        if listing.seller_id == interaction.user.id:
            await interaction.response.send_message(
                "❌ You can't buy your own listing!",
                ephemeral=True
            )
            return

        # Determine quantity
        buy_quantity = quantity if quantity else listing.quantity

        if buy_quantity <= 0:
            await interaction.response.send_message(
                "❌ Quantity must be positive!",
                ephemeral=True
            )
            return

        if buy_quantity > listing.quantity:
            await interaction.response.send_message(
                f"❌ Only {listing.quantity} available!",
                ephemeral=True
            )
            return

        total_cost = listing.price * buy_quantity
        buyer = await self.bot.db.get_user(interaction.user.id)

        if buyer.balance < total_cost:
            await interaction.response.send_message(
                f"❌ Insufficient funds! Need ${total_cost:,}, have ${buyer.balance:,}",
                ephemeral=True
            )
            return

        # Process transaction
        await self.bot.db.update_user_balance(interaction.user.id, -total_cost)
        await self.bot.db.update_user_balance(listing.seller_id, total_cost)
        await self.bot.db.add_item_to_inventory(interaction.user.id, item.id, buy_quantity)

        # Update or remove listing
        if buy_quantity < listing.quantity:
            await self.bot.db.update_market_listing(listing_id, -buy_quantity)
        else:
            await self.bot.db.remove_market_listing(listing_id)

        # Log transaction
        if hasattr(self.bot.db, 'log_transaction'):
            try:
                await self.bot.db.log_transaction(
                    interaction.user.id,
                    interaction.guild.id,
                    'marketplace_purchase',
                    -total_cost,
                    f'Bought {buy_quantity}x {item.name} from user {listing.seller_id}'
                )
                await self.bot.db.log_transaction(
                    listing.seller_id,
                    interaction.guild.id,
                    'marketplace_sale',
                    total_cost,
                    f'Sold {buy_quantity}x {item.name} to user {interaction.user.id}'
                )
            except Exception as e:
                self.logger.error(f"Failed to log transactions: {e}")

        self.logger.info(
            f"Marketplace: {interaction.user.name} (ID: {interaction.user.id}) "
            f"bought {buy_quantity}x {item.name} for ${total_cost:,} "
            f"from seller ID: {listing.seller_id}"
        )

        embed = discord.Embed(
            title="✅ Purchase Complete!",
            description=f"You bought **{buy_quantity}x {item.emoji} {item.name}** from the marketplace!",
            color=discord.Color.green()
        )
        embed.add_field(name="Total Cost", value=f"${total_cost:,}", inline=True)
        embed.add_field(name="New Balance", value=f"${buyer.balance - total_cost:,}", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mylistings", description="View your active marketplace listings")
    async def mylistings(self, interaction: discord.Interaction):
        """View your listings"""
        from sqlalchemy import select
        from config.database import MarketListing, Item

        async with self.bot.db.session_factory() as session:
            result = await session.execute(
                select(MarketListing, Item)
                .join(Item)
                .where(MarketListing.seller_id == interaction.user.id)
                .where(MarketListing.guild_id == interaction.guild.id)
            )
            listings = result.all()

        if not listings:
            await interaction.response.send_message(
                "📋 You don't have any active listings!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"📋 Your Marketplace Listings",
            color=discord.Color.blue()
        )

        for listing, item in listings:
            total_value = listing.price * listing.quantity
            embed.add_field(
                name=f"#{listing.id} - {item.emoji} {item.name}",
                value=f"**Price:** ${listing.price:,} each\n"
                      f"**Quantity:** {listing.quantity}\n"
                      f"**Total Value:** ${total_value:,}",
                inline=True
            )

        embed.set_footer(text="Use /cancellisting <id> to remove a listing")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="cancellisting", description="Cancel your marketplace listing")
    @app_commands.describe(listing_id="Listing ID to cancel")
    async def cancellisting(self, interaction: discord.Interaction, listing_id: int):
        """Cancel a listing"""
        from sqlalchemy import select
        from config.database import MarketListing, Item

        async with self.bot.db.session_factory() as session:
            result = await session.execute(
                select(MarketListing, Item)
                .join(Item)
                .where(MarketListing.id == listing_id)
            )
            listing_data = result.one_or_none()

        if not listing_data:
            await interaction.response.send_message(
                f"❌ Listing #{listing_id} not found!",
                ephemeral=True
            )
            return

        listing, item = listing_data

        if listing.seller_id != interaction.user.id:
            await interaction.response.send_message(
                "❌ This is not your listing!",
                ephemeral=True
            )
            return

        # Return items to inventory
        await self.bot.db.add_item_to_inventory(
            interaction.user.id,
            listing.item_id,
            listing.quantity
        )

        # Remove listing
        await self.bot.db.remove_market_listing(listing_id)

        self.logger.info(
            f"User {interaction.user.name} (ID: {interaction.user.id}) "
            f"cancelled listing #{listing_id} ({listing.quantity}x {item.name})"
        )

        embed = discord.Embed(
            title="🗑️ Listing Cancelled",
            description=f"**{listing.quantity}x {item.emoji} {item.name}** returned to inventory",
            color=discord.Color.orange()
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(MarketplaceCog(bot))