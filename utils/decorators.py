"""
Decorators

This module provides useful decorators for the Saint Toadle bot.
These decorators add functionality like cooldowns, permission checks,
and logging to bot commands.
"""

import functools
import time
from typing import Callable, Any, Union, List
from datetime import datetime, timezone

import discord
from discord.ext import commands

from utils.logger import get_context_logger
from utils.error_handler import PermissionError, InsufficientFundsError


def requires_economy(func: Callable) -> Callable:
    """
    Decorator that ensures economy features are enabled.
    
    Args:
        func: The function to decorate
        
    Returns:
        Callable: Decorated function
    """
    @functools.wraps(func)
    async def wrapper(self, ctx: commands.Context, *args, **kwargs):
        if not ctx.bot.config.economy_enabled:
            embed = discord.Embed(
                title="❌ Economy Disabled",
                description="Economy features are currently disabled.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        return await func(self, ctx, *args, **kwargs)
    
    return wrapper


def requires_balance(minimum: int = 0):
    """
    Decorator that checks if user has sufficient balance.
    
    Args:
        minimum: Minimum balance required
        
    Returns:
        function: Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, ctx: commands.Context, *args, **kwargs):
            # Get user from database
            user = await ctx.bot.db.get_user(ctx.author.id, ctx.author.name, ctx.author.discriminator)
            
            if user.balance < minimum:
                embed = discord.Embed(
                    title="💰 Insufficient Funds",
                    description=f"You need at least **{minimum:,}** coins to use this command.\n"
                              f"Your current balance: **{user.balance:,}** coins",
                    color=0xFF0000
                )
                await ctx.send(embed=embed)
                return
            
            return await func(self, ctx, *args, **kwargs)
        
        return wrapper
    return decorator


def cooldown_per_guild(rate: int, per: float, bucket: commands.BucketType = commands.BucketType.guild):
    """
    Custom cooldown decorator that works per guild.
    
    Args:
        rate: Number of times command can be used
        per: Time period in seconds
        bucket: Cooldown bucket type
        
    Returns:
        function: Decorator function
    """
    def decorator(func: Callable) -> Callable:
        if hasattr(func, '__commands_cooldown__'):
            func.__commands_cooldown__.append(commands.Cooldown(rate, per, bucket))
        else:
            func.__commands_cooldown__ = [commands.Cooldown(rate, per, bucket)]
        return func
    return decorator


def log_command_usage(func: Callable) -> Callable:
    """
    Decorator that logs command usage to database.
    
    Args:
        func: The function to decorate
        
    Returns:
        Callable: Decorated function
    """
    @functools.wraps(func)
    async def wrapper(self, ctx: commands.Context, *args, **kwargs):
        start_time = time.perf_counter()
        success = True
        error_msg = None
        
        logger = get_context_logger(
            func.__module__,
            user_id=ctx.author.id,
            guild_id=ctx.guild.id if ctx.guild else None,
            command=ctx.command.name if ctx.command else func.__name__
        )
        
        try:
            logger.info(f"Command started: {func.__name__}")
            result = await func(self, ctx, *args, **kwargs)
            logger.info(f"Command completed: {func.__name__}")
            return result
            
        except Exception as e:
            success = False
            error_msg = str(e)[:500]  # Truncate long error messages
            logger.error(f"Command failed: {func.__name__} - {e}")
            raise
        
        finally:
            execution_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
            
            # Log to database if available
            if hasattr(ctx.bot, 'db') and ctx.bot.db:
                try:
                    await ctx.bot.db.log_command(
                        user_id=ctx.author.id,
                        guild_id=ctx.guild.id if ctx.guild else None,
                        command_name=ctx.command.name if ctx.command else func.__name__,
                        success=success,
                        execution_time=execution_time,
                        error_message=error_msg
                    )
                except Exception as db_error:
                    logger.error(f"Failed to log command to database: {db_error}")
    
    return wrapper


def requires_permissions(*permissions: str):
    """
    Decorator that checks if user has required permissions.
    
    Args:
        *permissions: Required permissions
        
    Returns:
        function: Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, ctx: commands.Context, *args, **kwargs):
            if not ctx.guild:
                # Allow in DMs if no guild permissions are required
                return await func(self, ctx, *args, **kwargs)
            
            member = ctx.author
            missing_perms = []
            
            for perm in permissions:
                if not getattr(member.guild_permissions, perm, False):
                    missing_perms.append(perm.replace('_', ' ').title())
            
            if missing_perms:
                embed = discord.Embed(
                    title="❌ Missing Permissions",
                    description=f"You need the following permissions: {', '.join(missing_perms)}",
                    color=0xFF0000
                )
                await ctx.send(embed=embed)
                return
            
            return await func(self, ctx, *args, **kwargs)
        
        return wrapper
    return decorator


def bot_requires_permissions(*permissions: str):
    """
    Decorator that checks if bot has required permissions.
    
    Args:
        *permissions: Required permissions
        
    Returns:
        function: Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, ctx: commands.Context, *args, **kwargs):
            if not ctx.guild:
                # Skip permission check in DMs
                return await func(self, ctx, *args, **kwargs)
            
            bot_member = ctx.guild.me
            missing_perms = []
            
            for perm in permissions:
                if not getattr(bot_member.guild_permissions, perm, False):
                    missing_perms.append(perm.replace('_', ' ').title())
            
            if missing_perms:
                embed = discord.Embed(
                    title="❌ Bot Missing Permissions",
                    description=f"I need the following permissions: {', '.join(missing_perms)}",
                    color=0xFF0000
                )
                await ctx.send(embed=embed)
                return
            
            return await func(self, ctx, *args, **kwargs)
        
        return wrapper
    return decorator


def require_database(func: Callable) -> Callable:
    """
    Decorator that ensures database is available.
    
    Args:
        func: The function to decorate
        
    Returns:
        Callable: Decorated function
    """
    @functools.wraps(func)
    async def wrapper(self, ctx: commands.Context, *args, **kwargs):
        if not hasattr(ctx.bot, 'db') or not ctx.bot.db:
            embed = discord.Embed(
                title="❌ Database Error",
                description="Database is not available. Please try again later.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        return await func(self, ctx, *args, **kwargs)
    
    return wrapper


def typing(func: Callable) -> Callable:
    """
    Decorator that shows typing indicator while command is running.
    
    Args:
        func: The function to decorate
        
    Returns:
        Callable: Decorated function
    """
    @functools.wraps(func)
    async def wrapper(self, ctx: commands.Context, *args, **kwargs):
        async with ctx.typing():
            return await func(self, ctx, *args, **kwargs)
    
    return wrapper


def defer_response(ephemeral: bool = False):
    """
    Decorator that defers the response for slash commands.
    
    Args:
        ephemeral: Whether the response should be ephemeral
        
    Returns:
        function: Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, ctx: commands.Context, *args, **kwargs):
            # Only defer for slash commands (interactions)
            if hasattr(ctx, 'interaction') and ctx.interaction:
                await ctx.defer(ephemeral=ephemeral)
            
            return await func(self, ctx, *args, **kwargs)
        
        return wrapper
    return decorator


def guild_only(func: Callable) -> Callable:
    """
    Decorator that ensures command is only used in guilds.
    
    Args:
        func: The function to decorate
        
    Returns:
        Callable: Decorated function
    """
    @functools.wraps(func)
    async def wrapper(self, ctx: commands.Context, *args, **kwargs):
        if not ctx.guild:
            embed = discord.Embed(
                title="❌ Server Only",
                description="This command can only be used in a server.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        return await func(self, ctx, *args, **kwargs)
    
    return wrapper


def dm_only(func: Callable) -> Callable:
    """
    Decorator that ensures command is only used in DMs.
    
    Args:
        func: The function to decorate
        
    Returns:
        Callable: Decorated function
    """
    @functools.wraps(func)
    async def wrapper(self, ctx: commands.Context, *args, **kwargs):
        if ctx.guild:
            embed = discord.Embed(
                title="❌ DM Only",
                description="This command can only be used in DMs.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
        
        return await func(self, ctx, *args, **kwargs)
    
    return wrapper