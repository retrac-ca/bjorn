"""
Bot Configuration Settings

This module contains all configuration settings for the Bjorn bot.
It loads settings from environment variables with sensible defaults.
"""

import os
from typing import Optional


class BotConfig:
    """
    Centralized configuration class for the Bjorn bot.
    
    This class loads configuration from environment variables and provides
    default values for all settings. It's designed to be easily extensible
    and provides type hints for better development experience.
    """
    
    def __init__(self):
        """Initialize configuration by loading from environment variables."""
        
        # Discord Bot Configuration
        self.discord_token: str = os.getenv('DISCORD_TOKEN', '')
        self.bot_name: str = os.getenv('BOT_NAME', 'Bjorn')
        self.debug_mode: bool = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        
        # Database Configuration
        self.database_url: str = os.getenv('DATABASE_URL', 'sqlite:///data/bjorn.db')
        
        # Economy System Settings
        self.earn_min: int = int(os.getenv('EARN_MIN', '1'))
        self.earn_max: int = int(os.getenv('EARN_MAX', '50'))
        self.daily_bonus_min: int = int(os.getenv('DAILY_BONUS_MIN', '50'))
        self.daily_bonus_max: int = int(os.getenv('DAILY_BONUS_MAX', '100'))
        self.weekly_bonus_min: int = int(os.getenv('WEEKLY_BONUS_MIN', '200'))
        self.weekly_bonus_max: int = int(os.getenv('WEEKLY_BONUS_MAX', '500'))
        self.referral_bonus: int = int(os.getenv('REFERRAL_BONUS', '50'))
        self.bank_interest_rate: float = float(os.getenv('BANK_INTEREST_RATE', '0.02'))
        
        # Investment System Settings
        self.investment_min_amount: int = int(os.getenv('INVESTMENT_MIN_AMOUNT', '100'))
        self.investment_max_amount: int = int(os.getenv('INVESTMENT_MAX_AMOUNT', '10000'))
        self.investment_min_return: float = float(os.getenv('INVESTMENT_MIN_RETURN', '0.5'))
        self.investment_max_return: float = float(os.getenv('INVESTMENT_MAX_RETURN', '2.5'))
        self.investment_risk_chance: float = float(os.getenv('INVESTMENT_RISK_CHANCE', '0.3'))
        
        # Crime System Settings
        self.crime_success_rate: float = float(os.getenv('CRIME_SUCCESS_RATE', '0.75'))
        self.crime_reward_min: int = int(os.getenv('CRIME_REWARD_MIN', '25'))
        self.crime_reward_max: int = int(os.getenv('CRIME_REWARD_MAX', '150'))
        self.crime_fine_min: int = int(os.getenv('CRIME_FINE_MIN', '10'))
        self.crime_fine_max: int = int(os.getenv('CRIME_FINE_MAX', '75'))
        
        # Moderation Settings
        self.auto_ban_threshold: int = int(os.getenv('AUTO_BAN_THRESHOLD', '5'))
        self.log_retention_days: int = int(os.getenv('LOG_RETENTION_DAYS', '30'))
        
        # Logging Configuration
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.log_to_file: bool = os.getenv('LOG_TO_FILE', 'true').lower() == 'true'
        self.log_max_size: int = int(os.getenv('LOG_MAX_SIZE', '10485760'))  # 10MB
        self.log_backup_count: int = int(os.getenv('LOG_BACKUP_COUNT', '5'))
        
        # Feature Toggles
        self.economy_enabled: bool = os.getenv('ECONOMY_ENABLED', 'true').lower() == 'true'
        self.moderation_enabled: bool = os.getenv('MODERATION_ENABLED', 'true').lower() == 'true'
        self.referral_enabled: bool = os.getenv('REFERRAL_ENABLED', 'true').lower() == 'true'
        self.marketplace_enabled: bool = os.getenv('MARKETPLACE_ENABLED', 'true').lower() == 'true'
        self.profiles_enabled: bool = os.getenv('PROFILES_ENABLED', 'true').lower() == 'true'
        self.investment_enabled: bool = os.getenv('INVESTMENT_ENABLED', 'true').lower() == 'true'
        self.daily_interest_enabled: bool = os.getenv('DAILY_INTEREST_ENABLED', 'true').lower() == 'true'
        
        # Advanced Settings
        self.command_cooldown: int = int(os.getenv('COMMAND_COOLDOWN', '3'))
        self.max_warnings_per_user: int = int(os.getenv('MAX_WARNINGS_PER_USER', '10'))
        self.session_timeout: int = int(os.getenv('SESSION_TIMEOUT', '3600'))
        
        # Validate critical settings
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration settings and ensure they are within acceptable ranges."""
        # Validate Discord token
        if not self.discord_token:
            raise ValueError("DISCORD_TOKEN is required but not set!")
        
        # Validate economy ranges
        if self.earn_min >= self.earn_max:
            raise ValueError("EARN_MIN must be less than EARN_MAX")
        
        if self.daily_bonus_min >= self.daily_bonus_max:
            raise ValueError("DAILY_BONUS_MIN must be less than DAILY_BONUS_MAX")
        
        if self.weekly_bonus_min >= self.weekly_bonus_max:
            raise ValueError("WEEKLY_BONUS_MIN must be less than WEEKLY_BONUS_MAX")
        
        # Validate investment settings
        if self.investment_min_amount >= self.investment_max_amount:
            raise ValueError("INVESTMENT_MIN_AMOUNT must be less than INVESTMENT_MAX_AMOUNT")
        
        if not (0 <= self.investment_risk_chance <= 1):
            raise ValueError("INVESTMENT_RISK_CHANCE must be between 0 and 1")
        
        # Validate rates (must be between 0 and 1)
        if not (0 <= self.crime_success_rate <= 1):
            raise ValueError("CRIME_SUCCESS_RATE must be between 0 and 1")
        
        if not (0 <= self.bank_interest_rate <= 1):
            raise ValueError("BANK_INTEREST_RATE must be between 0 and 1")
    
    def get_embed_color(self) -> int:
        """Get the default embed color for the bot."""
        return 0x7289DA  # Discord blurple
    
    def get_success_color(self) -> int:
        """Get the success color for embeds."""
        return 0x00FF00  # Green
    
    def get_error_color(self) -> int:
        """Get the error color for embeds."""
        return 0xFF0000  # Red
    
    def get_warning_color(self) -> int:
        """Get the warning color for embeds."""
        return 0xFFA500  # Orange
    
    def get_info_color(self) -> int:
        """Get the info color for embeds."""
        return 0x00FFFF  # Cyan
    
    def __str__(self) -> str:
        """String representation of the configuration (without sensitive data)."""
        return (
            f"BotConfig("
            f"name='{self.bot_name}', "
            f"debug={self.debug_mode}, "
            f"economy={self.economy_enabled}, "
            f"moderation={self.moderation_enabled}, "
            f"investment={self.investment_enabled}"
            f")"
        )
    
    def __repr__(self) -> str:
        """Detailed representation of the configuration."""
        return self.__str__()
