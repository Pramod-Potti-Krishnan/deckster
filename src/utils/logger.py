"""
Logging configuration for Deckster using Logfire.
"""
from typing import Optional

# Try to configure Logfire once at module import
LOGFIRE_CONFIGURED = False

try:
    import logfire
    from config.settings import get_settings
    
    settings = get_settings()
    
    if settings.LOGFIRE_TOKEN:
        try:
            # Try to configure Logfire
            # Suppress the project URL output by redirecting stdout and stderr temporarily
            import sys
            import io
            import os
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()
            # Also suppress via environment variable if supported
            os.environ['LOGFIRE_CONSOLE_NO_SHOW'] = '1'
            try:
                logfire.configure(token=settings.LOGFIRE_TOKEN, console=False)
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
            LOGFIRE_CONFIGURED = True
        except Exception as config_error:
            # Logfire configuration failed, silently disable
            LOGFIRE_CONFIGURED = False
    else:
        # No LOGFIRE_TOKEN configured, logging disabled
        LOGFIRE_CONFIGURED = False
        
except Exception as e:
    # Logfire import/setup failed, silently disable
    LOGFIRE_CONFIGURED = False


class LogfireLogger:
    """Wrapper to make Logfire work like standard Python logging."""
    
    def __init__(self, name: str):
        self.name = name
    
    def info(self, message, *args, **kwargs):
        # Handle % formatting if args provided
        if args:
            message = message % args
        logfire.info(f"[{self.name}] {message}", **kwargs)
    
    def warn(self, message, *args, **kwargs):
        if args:
            message = message % args
        logfire.warn(f"[{self.name}] {message}", **kwargs)
    
    def warning(self, message, *args, **kwargs):
        # Alias for warn
        self.warn(message, *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        if args:
            message = message % args
        logfire.error(f"[{self.name}] {message}", **kwargs)
    
    def debug(self, message, *args, **kwargs):
        if args:
            message = message % args
        logfire.debug(f"[{self.name}] {message}", **kwargs)
    
    def critical(self, message, *args, **kwargs):
        if args:
            message = message % args
        logfire.error(f"[{self.name}] CRITICAL: {message}", **kwargs)
    
    def exception(self, message, *args, **kwargs):
        if args:
            message = message % args
        logfire.error(f"[{self.name}] EXCEPTION: {message}", **kwargs)
    
    def setLevel(self, level):
        # No-op for compatibility
        pass


class NoOpLogger:
    """No-op logger when Logfire is not configured."""
    
    def __init__(self, name: str):
        self.name = name
    
    def info(self, *args, **kwargs): pass
    def warn(self, *args, **kwargs): pass
    def warning(self, *args, **kwargs): pass
    def error(self, *args, **kwargs): pass
    def debug(self, *args, **kwargs): pass
    def critical(self, *args, **kwargs): pass
    def exception(self, *args, **kwargs): pass
    def setLevel(self, level): pass


def setup_logger(name: str, level: Optional[str] = None):
    """
    Set up a logger using Logfire or no-op if not configured.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (ignored for Logfire)
        
    Returns:
        LogfireLogger or NoOpLogger instance
    """
    if LOGFIRE_CONFIGURED:
        return LogfireLogger(name)
    else:
        return NoOpLogger(name)


# Create a default logger for the package
logger = setup_logger(__name__)