"""
Database Manager

This module provides database connectivity and operations for the Saint Toadle bot.
It handles database initialization, connection management, and provides high-level
data access methods for all bot features.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
import json

from sqlalchemy import create_engine, select, update, delete, and_, or_, func, desc
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError, OperationalError

from config.database import Base, User, Guild, Warning, Item, Inventory, Referral, Transaction, CommandLog
from utils.logger import get_logger, log_database_operation


class DatabaseManager:
    """
    Centralized database manager for the Saint Toadle bot.
    
    This class handles all database operations including connection management,
    data access methods, and provides a high-level interface for bot features.
    """
    
    def __init__(self, database_url: str):
        """
        Initialize the database manager.
        
        Args:
            database_url: Database connection string
        """
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        self.logger = get_logger(__name__)
        
        # Convert SQLite URL for async if needed
        if database_url.startswith('sqlite:///'):
            self.async_url = database_url.replace('sqlite:///', 'sqlite+aiosqlite:///')
        else:
            self.async_url = database_url
    
    async def initialize(self):
        """
        Initialize the database connection and create tables.
        
        This method sets up the async database engine, creates the session factory,
        and ensures all tables exist in the database.
        """
        try:
            self.logger.info("Initializing database connection...")
            
            # Create async engine
            self.engine = create_async_engine(
                self.async_url,
                echo=False,  # Set to True for SQL debugging
                future=True,
                pool_pre_ping=True
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create all tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            self.logger.info("Database initialized successfully")
            
            # Run any necessary migrations or setup
            await self._setup_initial_data()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _setup_initial_data(self):
        """Setup initial data such as default items."""
        try:
            # Check if we need to add default items
            async with self.session_factory() as session:
                items_count = await session.scalar(select(func.count(Item.id)))
                
                if items_count == 0:
                    self.logger.info("Adding default items to database...")
                    
                    default_items = [
                        Item(name="Cookie", description="A delicious cookie", price=10, category="food", emoji="🍪"),
                        Item(name="Coffee", description="Wake up with coffee", price=25, category="drink", emoji="☕"),
                        Item(name="Trophy", description="A shiny trophy", price=100, category="misc", emoji="🏆"),
                        Item(name="Diamond", description="A rare diamond", price=500, category="valuable", emoji="💎"),
                        Item(name="Gift Box", description="Mystery box", price=50, category="misc", emoji="🎁"),
                    ]
                    
                    session.add_all(default_items)
                    await session.commit()
                    self.logger.info(f"Added {len(default_items)} default items")
                    
        except Exception as e:
            self.logger.error(f"Failed to setup initial data: {e}")
    
    async def close(self):
        """Close the database connection."""
        if self.engine:
            await self.engine.dispose()
            self.logger.info("Database connection closed")
    
    # User Management Methods
    
    @log_database_operation("SELECT")
    async def get_user(self, user_id: int, username: str = None, discriminator: str = None) -> User:
        """
        Get a user from the database, creating if not exists.
        
        Args:
            user_id: Discord user ID
            username: Discord username (for new users)
            discriminator: Discord discriminator (for new users)
            
        Returns:
            User: User object from database
        """
        async with self.session_factory() as session:
            # Try to get existing user
            result = await session.get(User, user_id)
            
            if result is None:
                # Create new user
                new_user = User(
                    id=user_id,
                    username=username or f"User{user_id}",
                    discriminator=discriminator or "0000"
                )
                session.add(new_user)
                await session.commit()
                await session.refresh(new_user)
                
                self.logger.info(f"Created new user: {user_id}")
                return new_user
            
            return result
    
    @log_database_operation("UPDATE")
    async def update_user_balance(self, user_id: int, amount: int) -> bool:
        """
        Update user's balance.
        
        Args:
            user_id: Discord user ID
            amount: Amount to add (can be negative)
            
        Returns:
            bool: Success status
        """
        async with self.session_factory() as session:
            user = await session.get(User, user_id)
            if not user:
                return False
            
            new_balance = user.balance + amount
            if new_balance < 0:
                return False  # Insufficient funds
            
            user.balance = new_balance
            if amount > 0:
                user.total_earned += amount
            else:
                user.total_spent += abs(amount)
            
            await session.commit()
            return True
    
    @log_database_operation("SELECT")
    async def get_leaderboard(self, limit: int = 10, order_by: str = 'balance') -> List[User]:
        """
        Get leaderboard of users.
        
        Args:
            limit: Number of users to return
            order_by: Field to order by ('balance', 'total_earned', 'level')
            
        Returns:
            List[User]: Top users
        """
        async with self.session_factory() as session:
            order_field = getattr(User, order_by, User.balance)
            stmt = select(User).order_by(desc(order_field)).limit(limit)
            result = await session.execute(stmt)
            return result.scalars().all()
    
    # Economy Methods
    
    @log_database_operation("INSERT")
    async def log_transaction(self, user_id: int, guild_id: int, transaction_type: str, 
                            amount: int, description: str = None, related_user_id: int = None) -> bool:
        """
        Log an economic transaction.
        
        Args:
            user_id: User who performed the transaction
            guild_id: Guild where transaction occurred
            transaction_type: Type of transaction
            amount: Transaction amount
            description: Optional description
            related_user_id: Related user (for transfers)
            
        Returns:
            bool: Success status
        """
        async with self.session_factory() as session:
            transaction = Transaction(
                user_id=user_id,
                guild_id=guild_id,
                transaction_type=transaction_type,
                amount=amount,
                description=description,
                related_user_id=related_user_id
            )
            
            session.add(transaction)
            await session.commit()
            return True
    
    @log_database_operation("SELECT")
    async def can_use_daily(self, user_id: int) -> bool:
        """
        Check if user can use daily command.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            bool: Whether user can claim daily bonus
        """
        async with self.session_factory() as session:
            user = await session.get(User, user_id)
            if not user or not user.last_daily:
                return True
            
            # Check if 24 hours have passed
            now = datetime.now(timezone.utc)
            time_diff = now - user.last_daily
            return time_diff.total_seconds() >= 24 * 3600
    
    @log_database_operation("UPDATE")
    async def use_daily(self, user_id: int) -> bool:
        """
        Mark daily as used for user.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            bool: Success status
        """
        async with self.session_factory() as session:
            user = await session.get(User, user_id)
            if not user:
                return False
            
            user.last_daily = datetime.now(timezone.utc)
            await session.commit()
            return True
    
    # Inventory Methods
    
    @log_database_operation("SELECT")
    async def get_user_inventory(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get user's inventory with item details.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            List[Dict]: Inventory items with details
        """
        async with self.session_factory() as session:
            stmt = select(Inventory, Item).join(Item).where(Inventory.user_id == user_id)
            result = await session.execute(stmt)
            
            inventory = []
            for inv, item in result:
                inventory.append({
                    'item_id': item.id,
                    'name': item.name,
                    'description': item.description,
                    'quantity': inv.quantity,
                    'emoji': item.emoji,
                    'category': item.category
                })
            
            return inventory
    
    @log_database_operation("UPDATE")
    async def add_item_to_inventory(self, user_id: int, item_id: int, quantity: int = 1) -> bool:
        """
        Add item to user's inventory.
        
        Args:
            user_id: Discord user ID
            item_id: Item ID to add
            quantity: Quantity to add
            
        Returns:
            bool: Success status
        """
        async with self.session_factory() as session:
            # Check if user already has this item
            existing = await session.get(Inventory, (user_id, item_id))
            
            if existing:
                existing.quantity += quantity
                existing.updated_at = datetime.now(timezone.utc)
            else:
                new_inventory = Inventory(
                    user_id=user_id,
                    item_id=item_id,
                    quantity=quantity
                )
                session.add(new_inventory)
            
            await session.commit()
            return True
    
    # Moderation Methods
    
    @log_database_operation("INSERT")
    async def add_warning(self, user_id: int, guild_id: int, moderator_id: int, 
                         reason: str) -> int:
        """
        Add a warning to a user.
        
        Args:
            user_id: User being warned
            guild_id: Guild where warning occurred
            moderator_id: Moderator who issued warning
            reason: Reason for warning
            
        Returns:
            int: Warning ID
        """
        async with self.session_factory() as session:
            warning = Warning(
                user_id=user_id,
                guild_id=guild_id,
                moderator_id=moderator_id,
                reason=reason
            )
            
            session.add(warning)
            await session.commit()
            await session.refresh(warning)
            return warning.id
    
    @log_database_operation("SELECT")
    async def get_user_warnings(self, user_id: int, guild_id: int, 
                               active_only: bool = True) -> List[Warning]:
        """
        Get user's warnings in a guild.
        
        Args:
            user_id: Discord user ID
            guild_id: Discord guild ID
            active_only: Whether to only return active warnings
            
        Returns:
            List[Warning]: User's warnings
        """
        async with self.session_factory() as session:
            stmt = select(Warning).where(
                and_(Warning.user_id == user_id, Warning.guild_id == guild_id)
            )
            
            if active_only:
                stmt = stmt.where(Warning.active == True)
            
            result = await session.execute(stmt)
            return result.scalars().all()
    
    # Guild Management
    
    @log_database_operation("SELECT")
    async def get_guild(self, guild_id: int, name: str = None) -> Guild:
        """
        Get guild from database, creating if not exists.
        
        Args:
            guild_id: Discord guild ID
            name: Guild name (for new guilds)
            
        Returns:
            Guild: Guild object
        """
        async with self.session_factory() as session:
            result = await session.get(Guild, guild_id)
            
            if result is None:
                new_guild = Guild(
                    id=guild_id,
                    name=name or f"Guild{guild_id}"
                )
                session.add(new_guild)
                await session.commit()
                await session.refresh(new_guild)
                
                self.logger.info(f"Created new guild: {guild_id}")
                return new_guild
            
            return result
    
    # Command Logging
    
    @log_database_operation("INSERT")
    async def log_command(self, user_id: int, guild_id: int, command_name: str,
                         success: bool = True, execution_time: float = None,
                         error_message: str = None) -> None:
        """
        Log command usage.
        
        Args:
            user_id: User who ran the command
            guild_id: Guild where command was run
            command_name: Name of the command
            success: Whether command succeeded
            execution_time: Command execution time in milliseconds
            error_message: Error message if command failed
        """
        async with self.session_factory() as session:
            log_entry = CommandLog(
                user_id=user_id,
                guild_id=guild_id,
                command_name=command_name,
                success=success,
                execution_time=execution_time,
                error_message=error_message
            )
            
            session.add(log_entry)
            await session.commit()
    
    # Utility Methods
    
    async def cleanup_old_data(self, days: int = 30) -> None:
        """
        Clean up old data from the database.
        
        Args:
            days: Number of days to keep data
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        async with self.session_factory() as session:
            # Clean old command logs
            await session.execute(
                delete(CommandLog).where(CommandLog.created_at < cutoff_date)
            )
            
            # Clean old transactions (keep important ones)
            await session.execute(
                delete(Transaction).where(
                    and_(
                        Transaction.created_at < cutoff_date,
                        Transaction.transaction_type.not_in(['transfer', 'purchase'])
                    )
                )
            )
            
            await session.commit()
            self.logger.info(f"Cleaned up data older than {days} days")
    
    async def get_database_stats(self) -> Dict[str, int]:
        """
        Get database statistics.
        
        Returns:
            Dict[str, int]: Statistics about database tables
        """
        async with self.session_factory() as session:
            stats = {}
            
            # Count records in each table
            tables = [User, Guild, Warning, Item, Inventory, Referral, Transaction, CommandLog]
            
            for table in tables:
                count = await session.scalar(select(func.count(table.id)))
                stats[table.__tablename__] = count
            
            return stats