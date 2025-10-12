"""
Database Models and Setup

This module defines all database models for the Bjorn bot using SQLAlchemy.
It provides the schema for all data storage including users, guilds, economy,
moderation, store, marketplace, investments, and other bot features.
"""

from datetime import datetime
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Integer,
    String, Text, UniqueConstraint, Index, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Define Base only here
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(BigInteger, primary_key=True)
    username = Column(String(32), nullable=False)
    discriminator = Column(String(4), nullable=False)
    balance = Column(Integer, default=0, nullable=False)
    bank_balance = Column(Integer, default=0, nullable=False)
    last_daily = Column(DateTime(timezone=True))
    last_earn = Column(DateTime(timezone=True))
    last_weekly = Column(DateTime(timezone=True))
    last_crime = Column(DateTime(timezone=True))
    total_earned = Column(Integer, default=0, nullable=False)
    total_spent = Column(Integer, default=0, nullable=False)

    inventories = relationship("Inventory", back_populates="user")
    investments = relationship("Investment", back_populates="user")
    referrals_made = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer")
    referrals_received = relationship("Referral", foreign_keys="Referral.referred_id", back_populates="referred")
    warnings = relationship("Warning", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, balance={self.balance}, bank={self.bank_balance})>"


class Guild(Base):
    __tablename__ = 'guilds'
    id = Column(BigInteger, primary_key=True)
    name = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<Guild(id={self.id}, name='{self.name}')>"


class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    price = Column(Integer, nullable=False)
    category = Column(String(20), default='misc')
    emoji = Column(String(10))

    def __repr__(self):
        return f"<Item(id={self.id}, name='{self.name}', price={self.price})>"


class Inventory(Base):
    __tablename__ = 'inventories'
    user_id = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    item_id = Column(Integer, ForeignKey('items.id'), primary_key=True)
    quantity = Column(Integer, default=1, nullable=False)

    user = relationship("User", back_populates="inventories")
    item = relationship("Item")

    def __repr__(self):
        return f"<Inventory(user={self.user_id}, item={self.item_id}, qty={self.quantity})>"


class Referral(Base):
    __tablename__ = 'referrals'
    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    referred_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    guild_id = Column(BigInteger, ForeignKey('guilds.id'), nullable=False)
    bonus_claimed = Column(Boolean, default=False, nullable=False)
    bonus_amount = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_made")
    referred = relationship("User", foreign_keys=[referred_id], back_populates="referrals_received")

    __table_args__ = (
        UniqueConstraint('referrer_id', 'referred_id', 'guild_id', name='unique_referral'),
        Index('idx_referral_guild', 'guild_id'),
    )

    def __repr__(self):
        return f"<Referral(id={self.id}, referrer={self.referrer_id}, referred={self.referred_id})>"


class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    guild_id = Column(BigInteger, ForeignKey('guilds.id'))
    transaction_type = Column(String(20), nullable=False)
    amount = Column(Integer, nullable=False)
    description = Column(Text)
    related_user_id = Column(BigInteger)
    related_item_id = Column(Integer, ForeignKey('items.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Transaction(id={self.id}, user={self.user_id}, type='{self.transaction_type}', amount={self.amount})>"


class Warning(Base):
    __tablename__ = 'warnings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    guild_id = Column(BigInteger, ForeignKey('guilds.id'), nullable=False)
    moderator_id = Column(BigInteger, nullable=False)
    reason = Column(Text, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="warnings")

    __table_args__ = (
        Index('idx_warning_user_guild', 'user_id', 'guild_id'),
        Index('idx_warning_active', 'active'),
    )

    def __repr__(self):
        return f"<Warning(id={self.id}, user={self.user_id}, active={self.active})>"


class Investment(Base):
    __tablename__ = 'investments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    amount = Column(Integer, nullable=False)
    investment_type = Column(String(50), nullable=False)
    expected_return = Column(Float, nullable=False)
    actual_return = Column(Float)
    status = Column(String(20), default='active', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    maturity_date = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="investments")

    __table_args__ = (
        Index('idx_investment_user', 'user_id'),
        Index('idx_investment_status', 'status'),
    )

    def __repr__(self):
        return f"<Investment(id={self.id}, user={self.user_id}, status='{self.status}')>"


class StoreItem(Base):
    """
    Server-controlled shop items.
    """
    __tablename__ = 'store_items'
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, ForeignKey('guilds.id'), index=True, nullable=False)
    name = Column(String(50), nullable=False)
    price = Column(Integer, nullable=False)
    emoji = Column(String(10))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('guild_id', 'name', name='uix_guild_name'),
    )

    def __repr__(self):
        return f"<StoreItem(id={self.id}, name='{self.name}', price={self.price})>"


class MarketListing(Base):
    """
    User-driven marketplace listings.
    """
    __tablename__ = 'market_listings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    seller_id = Column(BigInteger, ForeignKey('users.id'), index=True, nullable=False)
    guild_id = Column(BigInteger, ForeignKey('guilds.id'), index=True, nullable=False)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=False)
    price = Column(Integer, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('seller_id', 'item_id', 'guild_id', name='uix_seller_item_guild'),
    )

    def __repr__(self):
        return f"<MarketListing(id={self.id}, seller={self.seller_id}, item={self.item_id})>"


class CentralBank(Base):
    """
    Tracks all lost/forfeited funds.
    """
    __tablename__ = 'central_bank'
    id = Column(Integer, primary_key=True, autoincrement=True)
    total_funds = Column(Integer, default=0, nullable=False)
    last_updated = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    def __repr__(self):
        return f"<CentralBank(total_funds={self.total_funds})>"
