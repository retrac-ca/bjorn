"""
Helper Functions

This module provides utility helper functions used throughout the Bjorn bot.
These functions handle common operations like formatting, validation, and calculations.
"""

import random
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Union, List, Dict, Any, Tuple
import asyncio

import discord
from discord.ext import commands


def format_currency(amount: int) -> str:
    """
    Format currency amount with commas and coin symbol.
    
    Args:
        amount: Amount to format
        
    Returns:
        str: Formatted currency string
    """
    return f"{amount:,} coins"


def format_large_number(number: int) -> str:
    """
    Format large numbers with K, M, B suffixes.
    
    Args:
        number: Number to format
        
    Returns:
        str: Formatted number string
    """
    if abs(number) < 1000:
        return str(number)
    elif abs(number) < 1000000:
        return f"{number/1000:.1f}K"
    elif abs(number) < 1000000000:
        return f"{number/1000000:.1f}M"
    else:
        return f"{number/1000000000:.1f}B"


def format_time_delta(delta: timedelta) -> str:
    """
    Format a time delta into a human-readable string.
    
    Args:
        delta: Time delta to format
        
    Returns:
        str: Formatted time string
    """
    total_seconds = int(delta.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds} seconds"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}m {seconds}s"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        return f"{days}d {hours}h"


def get_random_color() -> int:
    """
    Get a random color for embeds.
    
    Returns:
        int: Random hex color value
    """
    colors = [
        0xFF6B6B,  # Red
        0x4ECDC4,  # Teal
        0x45B7D1,  # Blue
        0xFFA726,  # Orange
        0x66BB6A,  # Green
        0xAB47BC,  # Purple
        0xFF7043,  # Deep Orange
        0x42A5F5,  # Light Blue
        0x26A69A,  # Teal
        0xD4E157   # Lime
    ]
    return random.choice(colors)


def create_progress_bar(current: int, maximum: int, length: int = 10, 
                       filled: str = "█", empty: str = "░") -> str:
    """
    Create a visual progress bar.
    
    Args:
        current: Current progress value
        maximum: Maximum progress value
        length: Length of the progress bar
        filled: Character for filled portions
        empty: Character for empty portions
        
    Returns:
        str: Progress bar string
    """
    if maximum == 0:
        return empty * length
    
    filled_length = int(length * current / maximum)
    return filled * filled_length + empty * (length - filled_length)


def parse_time_string(time_str: str) -> Optional[timedelta]:
    """
    Parse a time string into a timedelta object.
    
    Supports formats like: 1d, 2h, 30m, 45s, 1d2h30m
    
    Args:
        time_str: Time string to parse
        
    Returns:
        Optional[timedelta]: Parsed time delta or None if invalid
    """
    time_regex = re.compile(r'(\d+)([dhms])')
    matches = time_regex.findall(time_str.lower())
    
    if not matches:
        return None
    
    total_seconds = 0
    
    for amount, unit in matches:
        amount = int(amount)
        
        if unit == 's':
            total_seconds += amount
        elif unit == 'm':
            total_seconds += amount * 60
        elif unit == 'h':
            total_seconds += amount * 3600
        elif unit == 'd':
            total_seconds += amount * 86400
    
    return timedelta(seconds=total_seconds)


def validate_amount(amount: Union[str, int], minimum: int = 1, 
                   maximum: Optional[int] = None) -> Optional[int]:
    """
    Validate and parse an amount input.
    
    Args:
        amount: Amount to validate (can be string or int)
        minimum: Minimum allowed amount
        maximum: Maximum allowed amount (optional)
        
    Returns:
        Optional[int]: Validated amount or None if invalid
    """
    try:
        if isinstance(amount, str):
            # Handle special cases
            if amount.lower() in ['all', 'max']:
                return maximum if maximum else None
            
            # Remove commas and parse
            amount = int(amount.replace(',', ''))
        
        if amount < minimum:
            return None
        
        if maximum and amount > maximum:
            return None
        
        return int(amount)
    
    except (ValueError, TypeError):
        return None


def get_user_mention(user_id: int) -> str:
    """
    Get a user mention string.
    
    Args:
        user_id: Discord user ID
        
    Returns:
        str: User mention string
    """
    return f"<@{user_id}>"


def get_channel_mention(channel_id: int) -> str:
    """
    Get a channel mention string.
    
    Args:
        channel_id: Discord channel ID
        
    Returns:
        str: Channel mention string
    """
    return f"<#{channel_id}>"


def get_role_mention(role_id: int) -> str:
    """
    Get a role mention string.
    
    Args:
        role_id: Discord role ID
        
    Returns:
        str: Role mention string
    """
    return f"<@&{role_id}>"


def sanitize_input(text: str, max_length: int = 100) -> str:
    """
    Sanitize user input by removing harmful characters and limiting length.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized text
    """
    # Remove potential harmful characters
    sanitized = re.sub(r'[^\w\s\-_.,!?]', '', text)
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip()
    
    return sanitized.strip()


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List[List[Any]]: List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def get_ordinal(number: int) -> str:
    """
    Get ordinal suffix for a number (1st, 2nd, 3rd, etc.).
    
    Args:
        number: Number to get ordinal for
        
    Returns:
        str: Number with ordinal suffix
    """
    if 10 <= number % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(number % 10, 'th')
    
    return f"{number}{suffix}"


def calculate_level_exp(level: int) -> int:
    """
    Calculate experience required for a level.
    
    Args:
        level: Target level
        
    Returns:
        int: Required experience
    """
    return (level - 1) ** 2 * 100


def calculate_exp_level(experience: int) -> int:
    """
    Calculate level from experience points.
    
    Args:
        experience: Total experience
        
    Returns:
        int: Current level
    """
    import math
    return int(math.sqrt(experience / 100)) + 1


def get_random_success_message() -> str:
    """
    Get a random success message.
    
    Returns:
        str: Random success message
    """
    messages = [
        "Success! 🎉",
        "Great job! ⭐",
        "Well done! 👏",
        "Excellent! 💫",
        "Perfect! ✨",
        "Amazing! 🌟",
        "Outstanding! 🏆",
        "Fantastic! 🎊",
        "Wonderful! 🎈",
        "Superb! 🎯"
    ]
    return random.choice(messages)


def get_random_failure_message() -> str:
    """
    Get a random failure message.
    
    Returns:
        str: Random failure message
    """
    messages = [
        "Oops! Something went wrong. 😅",
        "That didn't work as expected. 🤔",
        "Better luck next time! 🍀",
        "Not quite right. Try again! 🔄",
        "Almost there! Keep trying! 💪",
        "Don't give up! 🌈",
        "Practice makes perfect! 📚",
        "You'll get it next time! ⭐",
        "Keep pushing forward! 🚀",
        "Every failure is a step to success! 🌟"
    ]
    return random.choice(messages)


async def send_paginated_embed(ctx: commands.Context, title: str, 
                             items: List[str], items_per_page: int = 10,
                             color: int = 0x7289DA) -> None:
    """
    Send a paginated embed with navigation reactions.
    
    Args:
        ctx: Command context
        title: Embed title
        items: List of items to paginate
        items_per_page: Items per page
        color: Embed color
    """
    if not items:
        embed = discord.Embed(
            title=title,
            description="No items found.",
            color=color
        )
        await ctx.send(embed=embed)
        return
    
    pages = chunk_list(items, items_per_page)
    current_page = 0
    
    def create_embed(page_num: int) -> discord.Embed:
        embed = discord.Embed(
            title=f"{title} (Page {page_num + 1}/{len(pages)})",
            description="\n".join(pages[page_num]),
            color=color
        )
        return embed
    
    if len(pages) == 1:
        # Single page, no navigation needed
        await ctx.send(embed=create_embed(0))
        return
    
    # Multi-page with navigation
    message = await ctx.send(embed=create_embed(current_page))
    
    # Add reaction controls
    await message.add_reaction("⬅️")
    await message.add_reaction("➡️")
    await message.add_reaction("❌")
    
    def check(reaction, user):
        return (user == ctx.author and 
                reaction.message.id == message.id and 
                str(reaction.emoji) in ["⬅️", "➡️", "❌"])
    
    timeout = 60  # 60 seconds timeout
    
    while True:
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=timeout, check=check)
            
            if str(reaction.emoji) == "⬅️" and current_page > 0:
                current_page -= 1
                await message.edit(embed=create_embed(current_page))
            elif str(reaction.emoji) == "➡️" and current_page < len(pages) - 1:
                current_page += 1
                await message.edit(embed=create_embed(current_page))
            elif str(reaction.emoji) == "❌":
                await message.delete()
                break
            
            # Remove the user's reaction
            await message.remove_reaction(reaction, user)
            
        except asyncio.TimeoutError:
            # Remove reactions on timeout
            try:
                await message.clear_reactions()
            except discord.Forbidden:
                pass
            break


def is_valid_hex_color(color_string: str) -> bool:
    """
    Check if a string is a valid hex color.
    
    Args:
        color_string: String to check
        
    Returns:
        bool: Whether the string is a valid hex color
    """
    hex_pattern = re.compile(r'^#?[0-9A-Fa-f]{6}$')
    return bool(hex_pattern.match(color_string))


def hex_to_int(hex_string: str) -> int:
    """
    Convert hex color string to integer.
    
    Args:
        hex_string: Hex color string
        
    Returns:
        int: Integer color value
    """
    if hex_string.startswith('#'):
        hex_string = hex_string[1:]
    return int(hex_string, 16)