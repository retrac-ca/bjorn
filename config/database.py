"""
Database Models and Setup

This module defines all database models for the Saint Toadle bot using SQLAlchemy.
It provides the schema for all data storage including users, guilds, economy,
moderation, and other bot features.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Integer, 
    String, Text, JSON, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Create base class for all models
Base = declarative_base()


class User(Base):
    """
    User model representing Discord users in the bot database.
    
    This model stores all user-related data including economy stats,
    profile information, and activity tracking.
    """
    __tablename__ = 'users'
    
    # Primary identification
    id = Column(BigInteger, primary_key=True)  # Discord user ID
    username = Column(String(32), nullable=False)
    discriminator = Column(String(4), nullable=False)
    display_name = Column(String(32))
    
    # Economy fields
    balance = Column(Integer, default=0, nullable=False)
    bank_balance = Column(Integer, default=0, nullable=False)
    total_earned = Column(Integer, default=0, nullable=False)
    total_spent = Column(Integer, default=0, nullable=False)
    
    # Activity tracking
    last_daily = Column(DateTime(timezone=True))
    last_weekly = Column(DateTime(timezone=True))
    last_earn = Column(DateTime(timezone=True))
    last_crime = Column(DateTime(timezone=True))
    
    # Profile information
    bio = Column(Text)
    profile_color = Column(Integer, default=0x7289DA)
    badges = Column(JSON, default=list)
    social_links = Column(JSON, default=dict)
    
    # Statistics
    commands_used = Column(Integer, default=0, nullable=False)
    messages_sent = Column(Integer, default=0, nullable=False)
    experience = Column(Integer, default=0, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    warnings = relationship("Warning", back_populates="user")
    inventories = relationship("Inventory", back_populates="user")
    referrals_made = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer")
    referrals_received = relationship("Referral", foreign_keys="Referral.referred_id", back_populates="referred")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_user_balance', 'balance'),
        Index('idx_user_level', 'level'),
        Index('idx_user_last_seen', 'last_seen'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Guild(Base):
    """
    Guild model representing Discord servers using the bot.
    
    This model stores server-specific configuration and statistics.
    """
    __tablename__ = 'guilds'
    
    # Primary identification
    id = Column(BigInteger, primary_key=True)  # Discord guild ID
    name = Column(String(100), nullable=False)
    
    # Configuration
    prefix = Column(String(5), default='!', nullable=False)
    welcome_channel = Column(BigInteger)
    log_channel = Column(BigInteger)
    mute_role = Column(BigInteger)
    
    # Feature toggles
    economy_enabled = Column(Boolean, default=True, nullable=False)
    moderation_enabled = Column(Boolean, default=True, nullable=False)
    referrals_enabled = Column(Boolean, default=True, nullable=False)
    
    # Economy settings
    daily_bonus_min = Column(Integer, default=50, nullable=False)
    daily_bonus_max = Column(Integer, default=100, nullable=False)
    interest_rate = Column(Float, default=0.02, nullable=False)
    
    # Statistics
    total_commands = Column(Integer, default=0, nullable=False)
    total_members = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Guild(id={self.id}, name='{self.name}')>"


class Warning(Base):
    """
    Warning model for tracking user warnings in guilds.
    
    This model stores moderation warnings issued to users by moderators.
    """
    __tablename__ = 'warnings'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    guild_id = Column(BigInteger, ForeignKey('guilds.id'), nullable=False)
    moderator_id = Column(BigInteger, nullable=False)
    
    # Warning details
    reason = Column(Text, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="warnings")
    
    # Constraints and indexes
    __table_args__ = (
        Index('idx_warning_user_guild', 'user_id', 'guild_id'),
        Index('idx_warning_active', 'active'),
    )
    
    def __repr__(self):
        return f"<Warning(id={self.id}, user_id={self.user_id})>"


class Item(Base):
    """
    Item model for marketplace items.
    
    This model defines items that can be bought, sold, or traded in the economy system.
    """
    __tablename__ = 'items'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Item details
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    price = Column(Integer, nullable=False)
    category = Column(String(20), default='misc', nullable=False)
    
    # Item properties
    stackable = Column(Boolean, default=True, nullable=False)
    tradeable = Column(Boolean, default=True, nullable=False)
    emoji = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Item(id={self.id}, name='{self.name}')>"


class Inventory(Base):
    """
    Inventory model linking users to their items.
    
    This model tracks what items users own and in what quantities.
    """
    __tablename__ = 'inventories'
    
    # Composite primary key
    user_id = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    item_id = Column(Integer, ForeignKey('items.id'), primary_key=True)
    
    # Quantity owned
    quantity = Column(Integer, default=1, nullable=False)
    
    # Timestamps
    acquired_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="inventories")
    item = relationship("Item")
    
    def __repr__(self):
        return f"<Inventory(user_id={self.user_id}, item_id={self.item_id}, quantity={self.quantity})>"


class Referral(Base):
    """
    Referral model tracking user invites and referrals.
    
    This model manages the referral system for tracking who invited whom.
    """
    __tablename__ = 'referrals'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    referrer_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    referred_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    guild_id = Column(BigInteger, ForeignKey('guilds.id'), nullable=False)
    
    # Referral details
    bonus_claimed = Column(Boolean, default=False, nullable=False)
    bonus_amount = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_made")
    referred = relationship("User", foreign_keys=[referred_id], back_populates="referrals_received")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('referrer_id', 'referred_id', 'guild_id', name='unique_referral'),
        Index('idx_referral_guild', 'guild_id'),
    )
    
    def __repr__(self):
        return f"<Referral(id={self.id}, referrer_id={self.referrer_id}, referred_id={self.referred_id})>"


class Transaction(Base):
    """
    Transaction model for tracking economy transactions.
    
    This model logs all economic activity for auditing and statistics.
    """
    __tablename__ = 'transactions'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Transaction details
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    guild_id = Column(BigInteger, ForeignKey('guilds.id'), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # earn, spend, transfer, etc.
    amount = Column(Integer, nullable=False)
    description = Column(Text)
    
    # Related data
    related_user_id = Column(BigInteger)  # For transfers
    related_item_id = Column(Integer, ForeignKey('items.id'))  # For purchases
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_transaction_user', 'user_id'),
        Index('idx_transaction_type', 'transaction_type'),
        Index('idx_transaction_date', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, user_id={self.user_id}, type='{self.transaction_type}')>"


class CommandLog(Base):
    """
    Command log model for tracking command usage.
    
    This model helps with debugging, analytics, and rate limiting.
    """
    __tablename__ = 'command_logs'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Command details
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    guild_id = Column(BigInteger, ForeignKey('guilds.id'))  # Nullable for DMs
    command_name = Column(String(50), nullable=False)
    success = Column(Boolean, default=True, nullable=False)
    execution_time = Column(Float)  # Milliseconds
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_command_user', 'user_id'),
        Index('idx_command_name', 'command_name'),
        Index('idx_command_date', 'created_at'),
        Index('idx_command_success', 'success'),
    )
    
    def __repr__(self):
        return f"<CommandLog(id={self.id}, command='{self.command_name}', user_id={self.user_id})>"


# Additional utility functions for database operations

def get_user_level(experience: int) -> int:
    """
    Calculate user level based on experience points.
    
    Uses a square root progression for level calculation.
    
    Args:
        experience: Total experience points
        
    Returns:
        int: User level
    """
    if experience < 0:
        return 1
    
    # Level = sqrt(experience / 100) + 1
    import math
    return int(math.sqrt(experience / 100)) + 1


def get_experience_for_level(level: int) -> int:
    """
    Calculate required experience for a given level.
    
    Args:
        level: Target level
        
    Returns:
        int: Required experience points
    """
    if level < 1:
        return 0
    
    # Experience = (level - 1)^2 * 100
    return (level - 1) ** 2 * 100