"""
Transaction listener service.

Continuously polls for new transactions and processes them.
"""

import time
from collections.abc import Callable

from src.api.polymarket_client import PolymarketClient, PolymarketAPIError
from src.config.settings import Settings
from src.models.transaction import Transaction
from src.logging.logger import PolymarketLogger, get_logger


class TransactionListener:
    """
    Service that continuously listens for new Polymarket transactions.
    
    Polls the API at regular intervals and detects new transactions
    by tracking previously seen transaction IDs.
    """
    
    def __init__(
        self,
        settings: Settings,
        client: PolymarketClient | None = None,
        logger: PolymarketLogger | None = None,
    ):
        """
        Initialize the transaction listener.
        
        Args:
            settings: Application settings.
            client: API client instance (created if not provided).
            logger: Logger instance (created if not provided).
        """
        self._settings = settings
        self._logger = logger or get_logger(debug=settings.debug)
        self._client = client or PolymarketClient(settings, self._logger)
        
        # Track seen transaction IDs to detect new ones
        self._seen_ids: set[str] = set()
        self._running: bool = False
        self._retry_count: int = 0
        
        # Optional callback for new transactions
        self._on_new_transaction: Callable[[Transaction], None] | None = None
    
    def set_callback(self, callback: Callable[[Transaction], None]) -> None:
        """
        Set a callback function for new transactions.
        
        Args:
            callback: Function to call with each new transaction.
        """
        self._on_new_transaction = callback
    
    def _fetch_transactions(self) -> list[Transaction]:
        """
        Fetch transactions from the API with pagination support.
        
        Returns:
            List of Transaction objects.
        """
        all_activities = []
        limit = min(self._settings.transaction_limit, 500)  # API max is 500
        total_to_fetch = self._settings.transaction_limit
        offset = 0
        
        # Paginate through results - use trades endpoint for actual trade data
        while len(all_activities) < total_to_fetch:
            batch_limit = min(limit, total_to_fetch - len(all_activities))
            raw_activities = self._client.get_trades(
                user_address=self._settings.user_address,
                limit=batch_limit,
                offset=offset,
            )
            
            if not raw_activities:
                break  # No more data
            
            all_activities.extend(raw_activities)
            offset += len(raw_activities)
            
            # If we got fewer than requested, there's no more data
            if len(raw_activities) < batch_limit:
                break
        
        transactions = []
        for i, activity in enumerate(all_activities):
            # Log first activity's keys to debug timestamp field
            if i == 0:
                self._logger.debug(f"API response keys: {list(activity.keys())}")
                self._logger.debug(f"Sample activity: {activity}")
            tx = Transaction.from_api_response(activity)
            transactions.append(tx)
        
        return transactions
    
    def _process_transactions(self, transactions: list[Transaction]) -> list[Transaction]:
        """
        Process transactions and identify new ones.
        
        Args:
            transactions: List of fetched transactions.
        
        Returns:
            List of new (unseen) transactions.
        """
        new_transactions = []
        
        for tx in transactions:
            if tx.id not in self._seen_ids:
                self._seen_ids.add(tx.id)
                new_transactions.append(tx)
        
        return new_transactions
    
    def _display_transaction(self, tx: Transaction) -> None:
        """
        Display a transaction with formatted output.
        
        Args:
            tx: Transaction to display.
        """
        self._logger.success(f"NEW TRANSACTION: {tx.format_display()}")
        
        callback = self._on_new_transaction
        if callback is not None:
            callback(tx)
    
    def _poll_once(self) -> int:
        """
        Perform a single poll cycle.
        
        Returns:
            Number of new transactions found.
        """
        try:
            transactions = self._fetch_transactions()
            self._retry_count = 0  # Reset on success
            
            new_transactions = self._process_transactions(transactions)
            
            for tx in new_transactions:
                self._display_transaction(tx)
            
            return len(new_transactions)
        
        except PolymarketAPIError as e:
            self._retry_count += 1
            
            if e.status_code == 429:
                self._logger.warning("Rate limited. Waiting before retry...")
                time.sleep(60)
            elif self._retry_count <= self._settings.max_retries:
                self._logger.warning(
                    f"API error (attempt {self._retry_count}/{self._settings.max_retries}): {e}"
                )
                time.sleep(self._settings.retry_delay * self._retry_count)
            else:
                self._logger.error(f"Max retries exceeded. Error: {e}")
                raise
            
            return 0
    
    def start(self) -> None:
        """
        Start the transaction listener.
        
        Runs in an infinite loop until stopped.
        """
        self._running = True
        self._logger.info(f"Starting listener for user: {self._settings.user_address}")
        self._logger.info(f"Poll interval: {self._settings.poll_interval}s")
        self._logger.info("-" * 60)
        
        # Initial fetch to populate seen IDs
        self._logger.info("Fetching initial transactions...")
        try:
            initial_transactions = self._fetch_transactions()
            self._logger.info(f"Loaded {len(initial_transactions)} existing transactions")
            self._logger.info("-" * 60)
            
            # Display all loaded transactions
            self._logger.info("EXISTING TRANSACTIONS:")
            for i, tx in enumerate(initial_transactions, 1):
                self._seen_ids.add(tx.id)
                self._logger.info(f"  [{i}] {tx.format_display()}")
            
            self._logger.info("-" * 60)
        except PolymarketAPIError as e:
            self._logger.error(f"Failed to fetch initial transactions: {e}")
            raise
        
        # Main polling loop
        self._logger.info("Listening for new transactions... (Ctrl+C to stop)")
        
        while self._running:
            try:
                new_count = self._poll_once()
                
                if new_count == 0:
                    self._logger.debug("No new transactions")
                
                time.sleep(self._settings.poll_interval)
            
            except KeyboardInterrupt:
                self._logger.info("Stopping listener...")
                break
    
    def stop(self) -> None:
        """Stop the transaction listener."""
        self._running = False
        self._client.close()
        self._logger.info("Listener stopped")
