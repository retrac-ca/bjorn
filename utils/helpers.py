"""
Helper Functions

This module provides utility functions used throughout the Bjorn bot.
"""

import re
from datetime import timedelta
from typing import Union, List, Optional


def format_currency(amount: int) -> str:
    """
    Format an integer amount as currency.
    
    Args:
        amount: The amount to format
        
    Returns:
        str: Formatted currency string
    """
    return f"${amount:,}"


def format_time_delta(delta: timedelta) -> str:
    """
    Format a timedelta into a human-readable string.
    
    Args:
        delta: The timedelta to format
        
    Returns:
        str: Human-readable time string
    """
    total_seconds = int(delta.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds}s"
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


def validate_amount(amount: str) -> Optional[int]:
    """
    Validate and convert an amount string to integer.
    
    Args:
        amount: Amount string to validate
        
    Returns:
        int or None: Validated amount or None if invalid
    """
    try:
        # Remove common currency symbols and separators
        cleaned = re.sub(r'[$,\s]', '', amount)
        value = int(cleaned)
        return value if value > 0 else None
    except (ValueError, TypeError):
        return None


def get_random_success_message() -> str:
    """
    Get a random success message.
    
    Returns:
        str: Random success message
    """
    messages = [
        "Great job! 🎉",
        "Success! ✅",
        "Well done! 👏",
        "Excellent! 🌟",
        "Perfect! 💫",
        "Outstanding! 🏆",
        "Fantastic! 🎊",
        "Amazing! ⭐"
    ]
    import random
    return random.choice(messages)


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.
    
    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        str: Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    Split a list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List[List]: List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
