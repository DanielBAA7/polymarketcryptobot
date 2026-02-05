#!/usr/bin/env python3
"""
Polymarket Transaction Listener

A CLI application that monitors a Polymarket user's transactions in real-time.

Usage:
    python main.py --user <WALLET_ADDRESS> [--interval 30] [--limit 100] [--debug]
"""

import argparse
import sys

from src.config.settings import settings
from src.services.listener import TransactionListener
from src.logging.logger import get_logger


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Monitor Polymarket user transactions in real-time",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --user 0x1234567890abcdef1234567890abcdef12345678
  python main.py --user 0x... --interval 10 --debug
        """
    )
    
    parser.add_argument(
        "--user",
        type=str,
        required=True,
        help="Polymarket wallet address to monitor (required)",
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Polling interval in seconds (default: 30)",
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Max transactions per request (default: 100, max: 500)",
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code (0 for success, 1 for error).
    """
    # Parse arguments
    args = parse_arguments()
    
    # Update settings from arguments
    settings.update_from_args(
        user_address=args.user,
        poll_interval=args.interval,
        transaction_limit=args.limit,
        debug=args.debug,
    )
    
    # Initialize logger
    logger = get_logger(debug=settings.debug)
    
    # Display banner
    logger.info("=" * 60)
    logger.info("  POLYMARKET TRANSACTION LISTENER")
    logger.info("=" * 60)
    
    # Validate settings
    try:
        settings.validate()
    except ValueError as e:
        logger.error(str(e))
        return 1
    
    # Create and start listener
    listener = TransactionListener(settings=settings, logger=logger)
    
    try:
        listener.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    finally:
        listener.stop()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
