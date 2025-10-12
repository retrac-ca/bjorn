"""
Utility helper functions
"""
from datetime import datetime, timedelta
from typing import Optional


def format_number(num: int) -> str:
    """Format number with commas"""
    return f"{num:,}"


def format_time_delta(td: timedelta) -> str:
    """Format timedelta to human readable string"""
    total_seconds = int(td.total_seconds())
    
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 and not parts:  # Only show seconds if nothing else
        parts.append(f"{seconds}s")
    
    return " ".join(parts) if parts else "0s"


def parse_time_string(time_str: str) -> Optional[timedelta]:
    """Parse time string like '1h', '30m', '2d' to timedelta"""
    try:
        if time_str.endswith('s'):
            return timedelta(seconds=int(time_str[:-1]))
        elif time_str.endswith('m'):
            return timedelta(minutes=int(time_str[:-1]))
        elif time_str.endswith('h'):
            return timedelta(hours=int(time_str[:-1]))
        elif time_str.endswith('d'):
            return timedelta(days=int(time_str[:-1]))
    except (ValueError, AttributeError):
        pass
    return None


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def get_level_from_exp(exp: int) -> int:
    """Calculate level from experience points"""
    return int((exp / 100) ** 0.5) + 1


def get_exp_for_level(level: int) -> int:
    """Calculate experience needed for a level"""
    return (level - 1) ** 2 * 100


def calculate_percentage(value: int, total: int) -> float:
    """Calculate percentage"""
    if total == 0:
        return 0.0
    return (value / total) * 100


def create_progress_bar(current: int, total: int, length: int = 10, filled_char: str = "█", empty_char: str = "░") -> str:
    """Create a text progress bar"""
    if total == 0:
        return empty_char * length
    
    filled = int((current / total) * length)
    return filled_char * filled + empty_char * (length - filled)