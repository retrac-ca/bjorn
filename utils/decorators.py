"""
Custom Decorators

This module provides custom decorators for the Bjorn bot including
permission checks, cooldowns, and utility decorators for slash commands.
"""

import asyncio
import functools
import time
from typing import Union, Callable, Any

import discord
from discord import app_commands
from discord.ext import commands

from utils.logger import get_logger, get_context_logger


def requires_economy(func):
    """Decorator to check if economy system is enabled."""
    @functools.wraps(func)
    async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
        if not self.bot.config.economy_enabled:
            embed = discord.Embed(
                title="❌ Feature Disabled",
                description="Economy system is currently disabled.",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        return await func(self, interaction, *args, **kwargs)
    return wrapper


def requires_moderator():
    """Decorator to check if user has moderation permissions."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            if not interaction.user.guild_permissions.manage_messages:
                embed = discord.Embed(
                    title="❌ Insufficient Permissions",
                    description="You need the `Manage Messages` permission to use this command.",
                    color=0xFF0000
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            return await func(self, interaction, *args, **kwargs)
        return wrapper
    return decorator


def require_database(func):
    """Decorator to ensure database is available."""
    @functools.wraps(func)
    async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
        if not hasattr(self.bot, 'db') or not self.bot.db:
            embed = discord.Embed(
                title="❌ Database Error",
                description="Database is not available. Please try again later.",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        return await func(self, interaction, *args, **kwargs)
    return wrapper


def log_command_usage(func):
    """Decorator to log slash command usage."""
    @functools.wraps(func)
    async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
        logger = get_context_logger(
            func.__module__,
            user_id=interaction.user.id,
            guild_id=interaction.guild.id if interaction.guild else None,
            command=func.__name__
        )
        
        start_time = time.perf_counter()
        logger.info(f"Executing slash command: {func.__name__}")
        
        try:
            result = await func(self, interaction, *args, **kwargs)
            execution_time = (time.perf_counter() - start_time) * 1000
            logger.info(f"Slash command completed successfully in {execution_time:.2f}ms")
            return result
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            logger.error(f"Slash command failed after {execution_time:.2f}ms: {str(e)}")
            raise
    
    return wrapper


def typing(func):
    """Decorator to show typing indicator during command execution."""
    @functools.wraps(func)
    async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
        # For slash commands, we can't show typing after responding
        # This decorator is kept for compatibility but doesn't do much for slash commands
        return await func(self, interaction, *args, **kwargs)
    return wrapper
