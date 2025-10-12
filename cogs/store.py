"""
Store/Marketplace - Buy and manage items
"""
import discord
from discord import app_commands
from discord.ext import commands

from utils.logger import get_logger


class StoreCog(commands.Cog, name="Store"):
    """Marketplace for buying and selling items"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)

    @app_commands.command(name="shop", description="Browse the store")
    @app_commands.describe(category="Filter by category (optional)")
    async def shop(self, interaction: discord.Interaction, category: str = None):
        """Display available items in the shop"""
        # Get all items from database
        from sqlalchemy import select
        from config.database import Item
        
        async with self.bot.db.session_factory() as session:
            stmt = select(Item)
            if category:
                stmt = stmt.where(Item.category == category.lower())
            
            result = await session.execute(stmt)
            items = result.scalars().all()

        if not items:
            await interaction.response.send_message(
                "🏪 The shop is empty right now!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"🏪 Bjorn's Shop{f' - {category.title()}' if category else ''}",
            description="Use `/buy <item_name>` to purchase items",
            color=discord.Color.blue()
        )

        for item in items[:25]:  # Discord limit
            embed.add_field(
                name=f"{item.emoji} {item.name}",
                value=f"{item.description}\n**Price:** ${item.price:,}",
                inline=True
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="Buy an item from the shop")
    @app_commands.describe(
        item_name="Name of the item to buy",
        quantity="How many to buy (default: 1)"
    )
    async def buy(self, interaction: discord.Interaction, item_name: str, quantity: int = 1):
        """Purchase an item"""
        if quantity <= 0:
            await interaction.response.send_message(
                "❌ Quantity must be positive!",
                ephemeral=True
            )
            return

        # Find item
        from sqlalchemy import select
        from config.database import Item
        
        async with self.bot.db.session_factory() as session:
            result = await session.execute(
                select(Item).where(Item.name.ilike(f"%{item_name}%"))
            )
            item = result.scalar_one_or_none()

        if not item:
            await interaction.response.send_message(
                f"❌ Item '{item_name}' not found!",
                ephemeral=True
            )
            return

        total_cost = item.price * quantity
        user = await self.bot.db.get_user(interaction.user.id)

        if user.balance < total_cost:
            await interaction.response.send_message(
                f"❌ Insufficient funds! You need ${total_cost:,} but only have ${user.balance:,}",
                ephemeral=True
            )
            return

        # Process purchase
        await self.bot.db.update_user_balance(interaction.user.id, -total_cost)
        await self.bot.db.add_item_to_inventory(interaction.user.id, item.id, quantity)
        
        await self.bot.db.log_transaction(
            interaction.user.id,
            interaction.guild.id if interaction.guild else 0,
            'purchase',
            -total_cost,
            f'Bought {quantity}x {item.name}',
            related_item_id=item.id
        )

        embed = discord.Embed(
            title="✅ Purchase Successful!",
            description=f"You bought **{quantity}x {item.emoji} {item.name}**!",
            color=discord.Color.green()
        )
        embed.add_field(name="Total Cost", value=f"${total_cost:,}", inline=True)
        embed.add_field(name="Remaining Balance", value=f"${user.balance - total_cost:,}", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="inventory", description="View your inventory")
    async def inventory(self, interaction: discord.Interaction):
        """Display user's inventory"""
        items = await self.bot.db.get_user_inventory(interaction.user.id)

        if not items:
            await interaction.response.send_message(
                "📦 Your inventory is empty! Visit `/shop` to buy items.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"📦 {interaction.user.display_name}'s Inventory",
            color=discord.Color.purple()
        )

        for item in items[:25]:  # Discord limit
            embed.add_field(
                name=f"{item['emoji']} {item['name']}",
                value=f"{item['description']}\n**Quantity:** {item['quantity']}",
                inline=True
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sell", description="Sell an item from your inventory")
    @app_commands.describe(
        item_name="Name of the item to sell",
        quantity="How many to sell (default: 1)"
    )
    async def sell(self, interaction: discord.Interaction, item_name: str, quantity: int = 1):
        """Sell an item for 50% of its value"""
        if quantity <= 0:
            await interaction.response.send_message(
                "❌ Quantity must be positive!",
                ephemeral=True
            )
            return

        # Get user's inventory
        items = await self.bot.db.get_user_inventory(interaction.user.id)
        
        # Find matching item
        item_data = None
        for item in items:
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

        # Find item price
        from sqlalchemy import select
        from config.database import Item
        
        async with self.bot.db.session_factory() as session:
            result = await session.execute(
                select(Item).where(Item.id == item_data['item_id'])
            )
            item = result.scalar_one()

        # Sell for 50% of purchase price
        sell_price = (item.price // 2) * quantity

        # Remove from inventory
        from sqlalchemy import update
        from config.database import Inventory
        
        async with self.bot.db.session_factory() as session:
            new_quantity = item_data['quantity'] - quantity
            
            if new_quantity <= 0:
                # Remove entirely
                from sqlalchemy import delete
                await session.execute(
                    delete(Inventory)
                    .where(Inventory.user_id == interaction.user.id)
                    .where(Inventory.item_id == item_data['item_id'])
                )
            else:
                # Update quantity
                await session.execute(
                    update(Inventory)
                    .where(Inventory.user_id == interaction.user.id)
                    .where(Inventory.item_id == item_data['item_id'])
                    .values(quantity=new_quantity)
                )
            
            await session.commit()

        # Add money
        await self.bot.db.update_user_balance(interaction.user.id, sell_price)
        
        await self.bot.db.log_transaction(
            interaction.user.id,
            interaction.guild.id if interaction.guild else 0,
            'sell',
            sell_price,
            f'Sold {quantity}x {item.name}',
            related_item_id=item.id
        )

        embed = discord.Embed(
            title="💰 Item Sold!",
            description=f"You sold **{quantity}x {item.emoji} {item.name}**!",
            color=discord.Color.green()
        )
        embed.add_field(name="Earned", value=f"${sell_price:,}", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="use", description="Use an item from your inventory")
    @app_commands.describe(item_name="Name of the item to use")
    async def use_item(self, interaction: discord.Interaction, item_name: str):
        """Use a consumable item"""
        # Get user's inventory
        items = await self.bot.db.get_user_inventory(interaction.user.id)
        
        # Find matching item
        item_data = None
        for item in items:
            if item_name.lower() in item['name'].lower():
                item_data = item
                break

        if not item_data:
            await interaction.response.send_message(
                f"❌ You don't have '{item_name}' in your inventory!",
                ephemeral=True
            )
            return

        # TODO: Implement item effects based on item type
        # For now, just consume the item
        
        await interaction.response.send_message(
            f"✨ You used **{item_data['emoji']} {item_data['name']}**!\n\n"
            "*(Item effects system coming soon!)*",
            ephemeral=False
        )


async def setup(bot):
    await bot.add_cog(StoreCog(bot))