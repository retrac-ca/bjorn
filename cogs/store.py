"""
Store Commands - Admin-controlled official shop
"""
import discord
from discord import app_commands
from discord.ext import commands

from utils.logger import get_logger


class StoreCog(commands.Cog, name="Store"):
    """Official shop - Admin managed items"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)

    def _is_admin(self, interaction: discord.Interaction) -> bool:
        """Check if user is admin"""
        return (
            interaction.user.id == interaction.guild.owner_id
            or interaction.user.guild_permissions.administrator
        )

    @app_commands.command(name="shopadditem", description="(Admin) Add item to official shop")
    @app_commands.describe(
        name="Item name",
        description="Item description",
        price="Item price",
        emoji="Item emoji",
        category="Item category"
    )
    async def shopadditem(
        self,
        interaction: discord.Interaction,
        name: str,
        description: str,
        price: int,
        emoji: str,
        category: str
    ):
        """Admin-only: Add item to official shop"""
        if not self._is_admin(interaction):
            await interaction.response.send_message(
                "❌ Admin only command!",
                ephemeral=True
            )
            return

        if price < 0:
            await interaction.response.send_message(
                "❌ Price cannot be negative!",
                ephemeral=True
            )
            return

        from sqlalchemy import insert
        from config.database import Item

        try:
            async with self.bot.db.session_factory() as session:
                stmt = insert(Item).values(
                    name=name,
                    description=description,
                    price=price,
                    emoji=emoji,
                    category=category.lower()
                )
                await session.execute(stmt)
                await session.commit()

            # Log the action
            self.logger.info(
                f"Admin {interaction.user.name} (ID: {interaction.user.id}) "
                f"added item '{name}' to shop (Price: ${price}, Category: {category})"
            )

            embed = discord.Embed(
                title="✅ Item Added to Shop!",
                description=f"**{emoji} {name}** added to official shop",
                color=discord.Color.green()
            )
            embed.add_field(name="Price", value=f"${price:,}", inline=True)
            embed.add_field(name="Category", value=category.title(), inline=True)
            embed.set_footer(text=f"Added by {interaction.user.name}")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            self.logger.error(f"Failed to add item '{name}': {e}")
            await interaction.response.send_message(
                "❌ Failed to add item. Item may already exist!",
                ephemeral=True
            )

    @app_commands.command(name="shopedititem", description="(Admin) Edit shop item")
    @app_commands.describe(
        item_name="Name of item to edit",
        new_name="New name (optional)",
        new_description="New description (optional)",
        new_price="New price (optional)",
        new_emoji="New emoji (optional)",
        new_category="New category (optional)"
    )
    async def shopedititem(
        self,
        interaction: discord.Interaction,
        item_name: str,
        new_name: str = None,
        new_description: str = None,
        new_price: int = None,
        new_emoji: str = None,
        new_category: str = None
    ):
        """Admin-only: Edit shop item"""
        if not self._is_admin(interaction):
            await interaction.response.send_message(
                "❌ Admin only command!",
                ephemeral=True
            )
            return

        from sqlalchemy import select, update
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

            updates = {}
            changes = []

            if new_name:
                updates['name'] = new_name
                changes.append(f"name: {item.name} → {new_name}")
            if new_description:
                updates['description'] = new_description
                changes.append(f"description updated")
            if new_price is not None:
                if new_price < 0:
                    await interaction.response.send_message(
                        "❌ Price cannot be negative!",
                        ephemeral=True
                    )
                    return
                updates['price'] = new_price
                changes.append(f"price: ${item.price} → ${new_price}")
            if new_emoji:
                updates['emoji'] = new_emoji
                changes.append(f"emoji: {item.emoji} → {new_emoji}")
            if new_category:
                updates['category'] = new_category.lower()
                changes.append(f"category: {item.category} → {new_category.lower()}")

            if not updates:
                await interaction.response.send_message(
                    "❌ No changes specified!",
                    ephemeral=True
                )
                return

            await session.execute(
                update(Item).where(Item.id == item.id).values(**updates)
            )
            await session.commit()

        # Log the action
        self.logger.info(
            f"Admin {interaction.user.name} (ID: {interaction.user.id}) "
            f"edited item '{item.name}': {', '.join(changes)}"
        )

        embed = discord.Embed(
            title="✅ Item Updated!",
            description=f"**{item.name}** has been updated",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Changes",
            value="\n".join(f"• {change}" for change in changes),
            inline=False
        )
        embed.set_footer(text=f"Edited by {interaction.user.name}")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="shopdeleteitem", description="(Admin) Delete shop item")
    @app_commands.describe(item_name="Name of item to delete")
    async def shopdeleteitem(self, interaction: discord.Interaction, item_name: str):
        """Admin-only: Delete shop item"""
        if not self._is_admin(interaction):
            await interaction.response.send_message(
                "❌ Admin only command!",
                ephemeral=True
            )
            return

        from sqlalchemy import select, delete
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

            item_data = {
                'name': item.name,
                'price': item.price,
                'emoji': item.emoji
            }

            await session.execute(delete(Item).where(Item.id == item.id))
            await session.commit()

        # Log the action
        self.logger.warning(
            f"Admin {interaction.user.name} (ID: {interaction.user.id}) "
            f"deleted item '{item_data['name']}' (Price: ${item_data['price']})"
        )

        embed = discord.Embed(
            title="🗑️ Item Deleted",
            description=f"**{item_data['emoji']} {item_data['name']}** removed from shop",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Deleted by {interaction.user.name}")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="shop", description="Browse the official shop")
    @app_commands.describe(category="Filter by category (optional)")
    async def shop(self, interaction: discord.Interaction, category: str = None):
        """Browse official shop items"""
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
            title=f"🏪 Official Shop{f' - {category.title()}' if category else ''}",
            description="Use `/buy <item_name>` to purchase items",
            color=discord.Color.blue()
        )

        for item in items[:25]:
            embed.add_field(
                name=f"{item.emoji} {item.name}",
                value=f"{item.description}\n**Price:** ${item.price:,}",
                inline=True
            )

        embed.set_footer(text="Looking for user items? Try /marketplace")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="Buy item from official shop")
    @app_commands.describe(
        item_name="Name of item to buy",
        quantity="Quantity (default: 1)"
    )
    async def buy(self, interaction: discord.Interaction, item_name: str, quantity: int = 1):
        """Purchase item from official shop"""
        if quantity <= 0:
            await interaction.response.send_message(
                "❌ Quantity must be positive!",
                ephemeral=True
            )
            return

        from sqlalchemy import select
        from config.database import Item

        async with self.bot.db.session_factory() as session:
            result = await session.execute(
                select(Item).where(Item.name.ilike(f"%{item_name}%"))
            )
            item = result.scalar_one_or_none()

        if not item:
            await interaction.response.send_message(
                f"❌ Item '{item_name}' not found in shop!",
                ephemeral=True
            )
            return

        total_cost = item.price * quantity
        user = await self.bot.db.get_user(interaction.user.id)

        if user.balance < total_cost:
            await interaction.response.send_message(
                f"❌ Insufficient funds! Need ${total_cost:,}, have ${user.balance:,}",
                ephemeral=True
            )
            return

        # Process purchase
        await self.bot.db.update_user_balance(interaction.user.id, -total_cost)
        await self.bot.db.add_item_to_inventory(interaction.user.id, item.id, quantity)
        await self.bot.db.credit_central_bank(total_cost)

        # Log transaction
        if hasattr(self.bot.db, 'log_transaction'):
            try:
                await self.bot.db.log_transaction(
                    interaction.user.id,
                    interaction.guild.id if interaction.guild else 0,
                    'shop_purchase',
                    -total_cost,
                    f'Bought {quantity}x {item.name} from official shop'
                )
            except Exception as e:
                self.logger.error(f"Failed to log transaction: {e}")

        self.logger.info(
            f"User {interaction.user.name} (ID: {interaction.user.id}) "
            f"bought {quantity}x {item.name} for ${total_cost:,}"
        )

        embed = discord.Embed(
            title="✅ Purchase Complete!",
            description=f"You bought **{quantity}x {item.emoji} {item.name}**!",
            color=discord.Color.green()
        )
        embed.add_field(name="Total Cost", value=f"${total_cost:,}", inline=True)
        embed.add_field(name="New Balance", value=f"${user.balance - total_cost:,}", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="inventory", description="View your inventory")
    async def inventory(self, interaction: discord.Interaction):
        """View your inventory"""
        items = await self.bot.db.get_user_inventory(interaction.user.id)

        if not items:
            await interaction.response.send_message(
                "📦 Your inventory is empty! Visit `/shop` to buy items.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"📦 {interaction.user.display_name}'s Inventory",
            description="Use `/listitem` to sell items on the marketplace",
            color=discord.Color.purple()
        )

        for item in items[:25]:
            embed.add_field(
                name=f"{item['emoji']} {item['name']}",
                value=f"{item['description']}\n**Quantity:** {item['quantity']}",
                inline=True
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(StoreCog(bot))