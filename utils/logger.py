"""
Logging Configuration and Setup

This module provides centralized logging functionality for the Bjorn bot.
It includes colored console output, file logging, and structured log formatting.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import colorlog


def setup_logging(config) -> None:
    """
    Setup logging configuration for the bot.
    
    This function configures both console and file logging with appropriate
    formatters and handlers based on the bot configuration.
    
    Args:
        config: Bot configuration object containing logging settings
    """
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.log_level))
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors
    console_handler = colorlog.StreamHandler()
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(getattr(logging, config.log_level))
    root_logger.addHandler(console_handler)
    
    # File handler (if enabled)
    if config.log_to_file:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_dir / "bjorn.log",
            maxBytes=config.log_max_size,
            backupCount=config.log_backup_count,
            encoding='utf-8'
        )
        
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)  # File gets all logs
        root_logger.addHandler(file_handler)
    
    # Error file handler for ERROR and CRITICAL logs
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "errors.log",
        maxBytes=config.log_max_size // 2,  # Smaller error log
        backupCount=3,
        encoding='utf-8'
    )
    
    error_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s\n"
        "%(pathname)s:%(lineno)d\n",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    error_handler.setFormatter(error_formatter)
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)
    
    # Set specific loggers to appropriate levels
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    logging.getLogger('discord.gateway').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    # Log the setup completion
    logger = get_logger(__name__)
    logger.info("Logging system initialized successfully")
    logger.info(f"Log level: {config.log_level}")
    logger.info(f"File logging: {'enabled' if config.log_to_file else 'disabled'}")
    if config.debug_mode:
        logger.debug("Debug mode is enabled - detailed logging active")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    This function provides a consistent way to get loggers throughout the bot
    while maintaining the module name hierarchy.
    
    Args:
        name: The name of the module/logger
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


class BotLoggerAdapter(logging.LoggerAdapter):
    """
    Custom logger adapter for bot-specific logging.
    
    This adapter adds contextual information to log messages such as
    user IDs, guild IDs, and command information.
    """
    
    def __init__(self, logger: logging.Logger, extra: Optional[dict] = None):
        """
        Initialize the logger adapter.
        
        Args:
            logger: Base logger instance
            extra: Additional context data
        """
        super().__init__(logger, extra or {})
    
    def process(self, msg, kwargs):
        """
        Process log messages by adding contextual information.
        
        Args:
            msg: Log message
            kwargs: Keyword arguments
            
        Returns:
            tuple: Processed message and kwargs
        """
        extra = self.extra.copy()
        
        # Add timestamp if not present
        if 'timestamp' not in extra:
            extra['timestamp'] = datetime.now().isoformat()
        
        # Format the message with context
        context_parts = []
        if 'user_id' in extra:
            context_parts.append(f"User:{extra['user_id']}")
        if 'guild_id' in extra:
            context_parts.append(f"Guild:{extra['guild_id']}")
        if 'command' in extra:
            context_parts.append(f"Cmd:{extra['command']}")
        
        if context_parts:
            context_str = f"[{' | '.join(context_parts)}] "
            msg = f"{context_str}{msg}"
        
        return msg, kwargs


def get_context_logger(name: str, **context) -> BotLoggerAdapter:
    """
    Get a context-aware logger for specific operations.
    
    This is useful for logging command executions, user interactions,
    or other operations where context is important.
    
    Args:
        name: Logger name
        **context: Contextual information (user_id, guild_id, command, etc.)
        
    Returns:
        BotLoggerAdapter: Context-aware logger
    """
    base_logger = get_logger(name)
    return BotLoggerAdapter(base_logger, context)


class LoggingMixin:
    """
    Mixin class to add logging capabilities to other classes.
    
    This mixin provides a consistent logger property for classes
    that need logging functionality.
    """
    
    @property
    def logger(self) -> logging.Logger:
        """
        Get a logger for this class.
        
        Returns:
            logging.Logger: Logger instance named after the class
        """
        return get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")


def log_command_execution(func):
    """
    Decorator to log command execution details.
    
    This decorator automatically logs when commands start and finish,
    including execution time and any errors that occur.
    
    Args:
        func: The command function to wrap
        
    Returns:
        function: Wrapped function with logging
    """
    import functools
    import time
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract context from command
        ctx = args[1] if len(args) > 1 else None
        logger_context = {}
        
        if ctx and hasattr(ctx, 'author') and hasattr(ctx, 'guild'):
            logger_context.update({
                'user_id': ctx.author.id,
                'guild_id': ctx.guild.id if ctx.guild else None,
                'command': ctx.command.name if hasattr(ctx, 'command') else 'unknown'
            })
        
        logger = get_context_logger(func.__module__, **logger_context)
        
        start_time = time.perf_counter()
        logger.info(f"Executing command: {func.__name__}")
        
        try:
            result = await func(*args, **kwargs)
            execution_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
            logger.info(f"Command completed successfully in {execution_time:.2f}ms")
            return result
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            logger.error(f"Command failed after {execution_time:.2f}ms: {str(e)}")
            raise
    
    return wrapper


def log_database_operation(operation_type: str):
    """
    Decorator to log database operations.
    
    Args:
        operation_type: Type of database operation (SELECT, INSERT, UPDATE, DELETE)
    """
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.perf_counter()
            
            logger.debug(f"Starting {operation_type} operation: {func.__name__}")
            
            try:
                result = await func(*args, **kwargs)
                execution_time = (time.perf_counter() - start_time) * 1000
                logger.debug(f"{operation_type} operation completed in {execution_time:.2f}ms")
                return result
                
            except Exception as e:
                execution_time = (time.perf_counter() - start_time) * 1000
                logger.error(f"{operation_type} operation failed after {execution_time:.2f}ms: {str(e)}")
                raise
        
        return wrapper
    return decorator
