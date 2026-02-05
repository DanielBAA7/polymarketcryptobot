"""
Colored logging utility for Polymarket Listener.

Provides a custom logger with color-coded output for different log levels.
"""

import logging
import sys
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama for Windows compatibility
init(autoreset=True)


# Custom log level for SUCCESS
SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log messages based on level."""
    
    COLORS = {
        logging.DEBUG: Fore.LIGHTBLACK_EX,      # Gray
        logging.INFO: Fore.CYAN,                 # Cyan
        SUCCESS_LEVEL: Fore.GREEN,               # Green
        logging.WARNING: Fore.YELLOW,            # Yellow
        logging.ERROR: Fore.RED,                 # Red
        logging.CRITICAL: Fore.RED + Style.BRIGHT,  # Bright Red
    }
    
    LEVEL_ICONS = {
        logging.DEBUG: "⚙️ ",
        logging.INFO: "ℹ️ ",
        SUCCESS_LEVEL: "✅",
        logging.WARNING: "⚠️ ",
        logging.ERROR: "❌",
        logging.CRITICAL: "🔥",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and icons."""
        color = self.COLORS.get(record.levelno, Fore.WHITE)
        icon = self.LEVEL_ICONS.get(record.levelno, "")
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        
        # Build the formatted message
        level_name = record.levelname.ljust(8)
        formatted_message = (
            f"{Fore.LIGHTBLACK_EX}{timestamp}{Style.RESET_ALL} "
            f"{color}{icon} {level_name}{Style.RESET_ALL} "
            f"{color}{record.getMessage()}{Style.RESET_ALL}"
        )
        
        return formatted_message


class PolymarketLogger:
    """Custom logger for Polymarket Listener with colored output."""
    
    def __init__(self, name: str = "polymarket", level: int = logging.INFO):
        """
        Initialize the logger.
        
        Args:
            name: Logger name identifier.
            level: Minimum log level to display.
        """
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        self._logger.handlers.clear()
        
        # Console handler with colored formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter())
        self._logger.addHandler(console_handler)
    
    def set_level(self, level: int) -> None:
        """Set the logging level."""
        self._logger.setLevel(level)
    
    def debug(self, message: str) -> None:
        """Log debug message (gray)."""
        self._logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log info message (cyan)."""
        self._logger.info(message)
    
    def success(self, message: str) -> None:
        """Log success message (green)."""
        self._logger.log(SUCCESS_LEVEL, message)
    
    def warning(self, message: str) -> None:
        """Log warning message (yellow)."""
        self._logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message (red)."""
        self._logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log critical message (bright red)."""
        self._logger.critical(message)


# Global logger instance
logger = PolymarketLogger()


def get_logger(name: str = "polymarket", debug: bool = False) -> PolymarketLogger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name identifier.
        debug: Enable debug level logging.
    
    Returns:
        Configured PolymarketLogger instance.
    """
    level = logging.DEBUG if debug else logging.INFO
    return PolymarketLogger(name=name, level=level)
