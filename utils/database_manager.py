"""
Database Manager



This module provides database connectivity and operations for the Bjorn bot.
It handles database initialization, connection management, and provides high-level
data access methods for all bot features including store, marketplace, investments,
daily interest, and cooldown tracking.
"""



import asyncio
from datetime import datetime, timezone
from typing import List, Optional



from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import IntegrityError



from config.database import (
    Base, User, Guild, Warning, Item, Inventory, Referral, Transaction,
    Investment, StoreItem, MarketListing, CentralBank
)
from utils.logger import get_logger, log_database_operation




class DatabaseManager:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.async_url = (
            database_url.replace('sqlite:///', 'sqlite+aiosqlite:///')
            if database_url.startswith('sqlite:///') else database_url
        )
        self.engine = None
        self.session_factory = None
        self.logger = get_logger(__name__)



    async def initialize(self):
        self.logger.info("Initializing database connection...")
        self.engine = create_async_engine(self.async_url, echo=False, future=True)
        self.session_factory = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.logger.info("Database initialized successfully")
        await self._setup_initial_data()



    async def _setup_initial_data(self):
        async with self.session_factory() as session:
            count = await session.scalar(select(func.count(StoreItem.id)))
            if count == 0:
                self.logger.info("Adding default store items to database...")
                defaults = [
                    StoreItem(guild_id=0, name="Cookie", price=10, emoji="🍪"),
                    StoreItem(guild_id=0, name="Coffee", price=25, emoji="☕"),
                    StoreItem(guild_id=0, name="Trophy", price=100, emoji="🏆"),
                ]
                session.add_all(defaults)
                await session.commit()



    async def close(self):
        if self.engine:
            await self.engine.dispose()
            self.logger.info("Database connection closed")



    # User methods
    @log_database_operation("SELECT")
    async def get_user(self, user_id: int, username: str, discriminator: str) -> User:
        async with self.session_factory() as session:
            user = await session.get(User, user_id)
            if not user:
                user = User(id=user_id, username=username, discriminator=discriminator)
                session.add(user)
                await session.commit()
                await session.refresh(user)
            return user



    @log_database_operation("UPDATE")
    async def update_user_balance(self, user_id: int, amount: int) -> bool:
        async with self.session_factory() as session:
            user = await session.get(User, user_id)
            if not user or user.balance + amount < 0:
                return False
            user.balance += amount
            await session.commit()
            return True



    @log_database_operation("UPDATE")
    async def update_bank_balance(self, user_id: int, amount: int) -> bool:
        async with self.session_factory() as session:
            user = await session.get(User, user_id)
            if not user or user.bank_balance + amount < 0:
                return False
            user.bank_balance += amount
            await session.commit()
            return True



    # Cooldown tracking for daily/earn/weekly
    @log_database_operation("SELECT")
    async def can_use_daily(self, user_id: int) -> bool:
        async with self.session_factory() as session:
            user = await session.get(User, user_id)
            if not user or not user.last_daily:
                return True
            elapsed = datetime.now(timezone.utc) - user.last_daily
            return elapsed.total_seconds() >= 24 * 3600



    @log_database_operation("UPDATE")
    async def use_daily(self, user_id: int) -> bool:
        async with self.session_factory() as session:
            user = await session.get(User, user_id)
            if not user:
                return False
            user.last_daily = datetime.now(timezone.utc)
            await session.commit()
            return True



    @log_database_operation("SELECT")
    async def can_earn(self, user_id: int) -> bool:
        async with self.session_factory() as session:
            user = await session.get(User, user_id)
            if not user or not user.last_earn:
                return True
            elapsed = datetime.now(timezone.utc) - user.last_earn
            return elapsed.total_seconds() >= 300  # 5 minutes



    @log_database_operation("UPDATE")
    async def use_earn(self, user_id: int) -> bool:
        async with self.session_factory() as session:
            user = await session.get(User, user_id)
            if not user:
                return False
            user.last_earn = datetime.now(timezone.utc)
            await session.commit()
            return True



    # Inventory methods
    @log_database_operation("SELECT")
    async def get_inventory_item(self, user_id: int, item_id: int) -> Optional[Inventory]:
        async with self.session_factory() as session:
            return await session.get(Inventory, {"user_id": user_id, "item_id": item_id})



    @log_database_operation("INSERT")
    async def add_inventory(self, user_id: int, item_id: int, quantity: int) -> None:
        async with self.session_factory() as session:
            inv = await session.get(Inventory, {"user_id": user_id, "item_id": item_id})
            if inv:
                inv.quantity += quantity
            else:
                inv = Inventory(user_id=user_id, item_id=item_id, quantity=quantity)
                session.add(inv)
            await session.commit()



    @log_database_operation("UPDATE")
    async def update_inventory(self, user_id: int, item_id: int, delta: int) -> bool:
        async with self.session_factory() as session:
            inv = await session.get(Inventory, {"user_id": user_id, "item_id": item_id})
            if not inv or inv.quantity + delta < 0:
                return False
            inv.quantity += delta
            if inv.quantity == 0:
                await session.delete(inv)
            await session.commit()
            return True



    # Store methods
    @log_database_operation("SELECT")
    async def list_store_items(self, guild_id: int) -> List[StoreItem]:
        async with self.session_factory() as session:
            result = await session.execute(select(StoreItem).where(StoreItem.guild_id == guild_id))
            return result.scalars().all()



    @log_database_operation("INSERT")
    async def add_store_item(self, guild_id: int, name: str, price: int, emoji: str) -> bool:
        async with self.session_factory() as session:
            item = StoreItem(guild_id=guild_id, name=name, price=price, emoji=emoji)
            session.add(item)
            try:
                await session.commit()
                return True
            except IntegrityError:
                await session.rollback()
                return False



    @log_database_operation("DELETE")
    async def remove_store_item(self, guild_id: int, name: str) -> bool:
        async with self.session_factory() as session:
            stmt = delete(StoreItem).where(
                StoreItem.guild_id == guild_id,
                StoreItem.name == name
            )
            res = await session.execute(stmt)
            await session.commit()
            return res.rowcount > 0



    # Marketplace methods
    @log_database_operation("INSERT")
    async def create_market_listing(self, seller_id: int, guild_id: int,
                                    item_id: int, price: int, quantity: int = 1) -> int:
        async with self.session_factory() as session:
            listing = MarketListing(
                seller_id=seller_id,
                guild_id=guild_id,
                item_id=item_id,
                price=price,
                quantity=quantity
            )
            session.add(listing)
            await session.commit()
            await session.refresh(listing)
            return listing.id



    @log_database_operation("SELECT")
    async def list_market_listings(self, guild_id: int) -> List[MarketListing]:
        async with self.session_factory() as session:
            result = await session.execute(select(MarketListing).where(MarketListing.guild_id == guild_id))
            return result.scalars().all()



    @log_database_operation("UPDATE")
    async def update_market_listing(self, listing_id: int, quantity_delta: int) -> bool:
        async with self.session_factory() as session:
            listing = await session.get(MarketListing, listing_id)
            if not listing or listing.quantity + quantity_delta < 0:
                return False
            listing.quantity += quantity_delta
            if listing.quantity == 0:
                await session.delete(listing)
            await session.commit()
            return True



    @log_database_operation("DELETE")
    async def remove_market_listing(self, listing_id: int) -> bool:
        async with self.session_factory() as session:
            listing = await session.get(MarketListing, listing_id)
            if not listing:
                return False
            await session.delete(listing)
            await session.commit()
            return True



    # Central bank methods
    @log_database_operation("UPDATE")
    async def credit_central_bank(self, amount: int) -> None:
        async with self.session_factory() as session:
            cb = await session.get(CentralBank, 1)
            if not cb:
                cb = CentralBank(id=1, total_funds=amount)
                session.add(cb)
            else:
                cb.total_funds += amount
            await session.commit()



    @log_database_operation("SELECT")
    async def get_central_bank(self) -> CentralBank:
        async with self.session_factory() as session:
            cb = await session.get(CentralBank, 1)
            if not cb:
                cb = CentralBank(id=1, total_funds=0)
                session.add(cb)
                await session.commit()
            return cb



    # Daily interest
    @log_database_operation("UPDATE")
    async def apply_daily_interest(self, interest_rate: float) -> int:
        async with self.session_factory() as session:
            stmt = select(User).where(User.bank_balance > 0)
            result = await session.execute(stmt)
            users = result.scalars().all()



            count = 0
            for user in users:
                interest = int(user.bank_balance * interest_rate)
                if interest > 0:
                    user.bank_balance += interest
                    user.total_earned += interest
                    count += 1
                    transaction = Transaction(
                        user_id=user.id,
                        guild_id=None,
                        transaction_type='interest',
                        amount=interest,
                        description=f'Daily interest ({interest_rate*100:.1f}%)'
                    )
                    session.add(transaction)



            await session.commit()
            return count



    @log_database_operation("INSERT")
    async def log_transaction(self, user_id: int, guild_id: Optional[int], transaction_type: str, amount: int, description: str) -> None:
        async with self.session_factory() as session:
            transaction = Transaction(
                user_id=user_id,
                guild_id=guild_id,
                transaction_type=transaction_type,
                amount=amount,
                description=description
            )
            session.add(transaction)
            await session.commit()
