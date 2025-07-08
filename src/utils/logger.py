"""
Logging configuration for Deckster.
"""
import logging
import sys
from typing import Optional
from config.settings import get_settings

# Try to import logfire, but fall back to standard logging if not available
try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with consistent formatting.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (defaults to settings.LOG_LEVEL)
        
    Returns:
        Configured logger instance
    """
    settings = get_settings()
    log_level = level or settings.LOG_LEVEL
    
    # Configure logfire if available and token is set
    if LOGFIRE_AVAILABLE and settings.LOGFIRE_TOKEN:
        try:
            logfire.configure(
                service_name="deckster",
                service_version="1.0.0",
                environment=settings.APP_ENV,
                token=settings.LOGFIRE_TOKEN
            )
            # Use logfire's logger
            logger = logfire.get_logger(name)
            logger.setLevel(getattr(logging, log_level.upper()))
            return logger
        except Exception as e:
            # Fall back to standard logging if logfire configuration fails
            print(f"Logfire configuration failed: {e}")
    
    # Standard logging configuration
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Avoid duplicate handlers
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
    
    return logger


# Create a default logger for the package
logger = setup_logger(__name__)