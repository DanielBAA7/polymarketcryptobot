"""
Configuration management for Polymarket Listener.

Handles loading settings from environment variables and command line arguments.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


@dataclass
class Settings:
    """Application configuration settings."""
    
    # API Configuration
    api_base_url: str = "https://data-api.polymarket.com"
    
    # User Configuration
    user_address: str = ""
    
    # Polling Configuration
    poll_interval: int = 30  # seconds
    transaction_limit: int = 100  # max per request
    
    # Logging Configuration
    debug: bool = False
    
    # Retry Configuration
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    
    @classmethod
    def from_env(cls) -> "Settings":
        """
        Load settings from environment variables.
        
        Returns:
            Settings instance with values from environment.
        """
        return cls(
            api_base_url=os.getenv("API_BASE_URL", "https://data-api.polymarket.com"),
            user_address=os.getenv("USER_ADDRESS", ""),
            poll_interval=int(os.getenv("POLL_INTERVAL", "1")),
            transaction_limit=int(os.getenv("TRANSACTION_LIMIT", "100")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            retry_delay=int(os.getenv("RETRY_DELAY", "5")),
        )
    
    def update_from_args(
        self,
        user_address: str | None = None,
        poll_interval: int | None = None,
        transaction_limit: int | None = None,
        debug: bool | None = None,
    ) -> None:
        """
        Update settings from command line arguments.
        
        Args:
            user_address: Polymarket wallet address to monitor.
            poll_interval: Seconds between API polls.
            transaction_limit: Max transactions per request.
            debug: Enable debug logging.
        """
        if user_address is not None:
            self.user_address = user_address
        if poll_interval is not None:
            self.poll_interval = poll_interval
        if transaction_limit is not None:
            self.transaction_limit = transaction_limit
        if debug is not None:
            self.debug = debug
    
    def validate(self) -> None:
        """
        Validate required settings.
        
        Raises:
            ValueError: If required settings are missing or invalid.
        """
        if not self.user_address:
            raise ValueError("User address is required. Use --user option.")
        
        if not self.user_address.startswith("0x"):
            raise ValueError("User address must be a valid Ethereum address (0x...)")
        
        if len(self.user_address) != 42:
            raise ValueError("User address must be 42 characters (0x + 40 hex chars)")
        
        if self.poll_interval < 1:
            raise ValueError("Poll interval must be at least 1 second")
        
        if self.transaction_limit < 1 or self.transaction_limit > 500:
            raise ValueError("Transaction limit must be between 1 and 500")


# Global settings instance
settings = Settings.from_env()
