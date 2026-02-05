"""
Transaction data models for Polymarket Listener.

Defines dataclasses for representing transaction and activity data.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from colorama import Fore, Style


# Polygon blockchain explorer base URL
POLYGONSCAN_URL = "https://polygonscan.com/tx/"


@dataclass
class Transaction:
    """Represents a Polymarket transaction/activity."""
    
    id: str
    type: str
    timestamp: datetime
    market_slug: str
    side: str  # BUY or SELL
    shares: float  # Number of shares
    price_per_share: float  # Price per share (0.0 to 1.0)
    total_cost: float  # Total money spent/received
    outcome: str  # The outcome being traded (Yes/No)
    transaction_hash: str | None = None
    
    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Transaction":
        """
        Create a Transaction from API response data.
        
        Args:
            data: Dictionary from Polymarket API response.
        
        Returns:
            Transaction instance.
        """
        # Try multiple timestamp field names - prioritize match_time
        timestamp_raw = (
            data.get("match_time") or
            data.get("matchTime") or
            data.get("last_update") or
            data.get("lastUpdate") or
            data.get("timestamp") or 
            data.get("createdAt") or 
            data.get("created_at") or
            data.get("time") or
            data.get("blockTimestamp")
        )
        timestamp = datetime.now(tz=timezone.utc)  # Default fallback
        
        if timestamp_raw is not None:
            try:
                if isinstance(timestamp_raw, (int, float)):
                    # Check if it's in seconds or milliseconds
                    if timestamp_raw > 1e12:
                        timestamp = datetime.fromtimestamp(timestamp_raw / 1000, tz=timezone.utc)
                    else:
                        timestamp = datetime.fromtimestamp(timestamp_raw, tz=timezone.utc)
                elif isinstance(timestamp_raw, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00"))
                    except ValueError:
                        num_val = float(timestamp_raw)
                        if num_val > 1e12:
                            timestamp = datetime.fromtimestamp(num_val / 1000, tz=timezone.utc)
                        else:
                            timestamp = datetime.fromtimestamp(num_val, tz=timezone.utc)
            except (ValueError, TypeError, OSError):
                pass
        
        # Get side (BUY/SELL)
        side_raw = data.get("side", "").upper()
        if side_raw in ("BUY", "SELL"):
            side = side_raw
        else:
            # Fallback - try to determine from type
            tx_type = str(data.get("type", "")).upper()
            side = "BUY" if "BUY" in tx_type else ("SELL" if "SELL" in tx_type else "TRADE")
        
        # Get shares (size field)
        shares = float(data.get("size") or data.get("amount") or 0)
        
        # Get price per share (0.0 to 1.0 representing percentage)
        price_per_share = float(data.get("price") or data.get("avgPrice") or data.get("avg_price") or 0)
        
        # Calculate total cost
        total_cost = shares * price_per_share
        
        # Get other fields
        tx_type = data.get("type", "trade")
        market_slug = data.get("slug") or data.get("marketSlug") or data.get("market") or data.get("conditionId") or "Unknown Market"
        outcome = data.get("outcome") or "Unknown"
        tx_hash = data.get("transactionHash") or data.get("transaction_hash") or data.get("txHash")
        
        market_str = str(market_slug)
        return cls(
            id=str(data.get("id", "")),
            type=str(tx_type) if tx_type else "trade",
            timestamp=timestamp,
            market_slug=market_str[:100] if len(market_str) > 100 else market_str,
            side=side,
            shares=shares,
            price_per_share=price_per_share,
            total_cost=total_cost,
            outcome=str(outcome),
            transaction_hash=str(tx_hash) if tx_hash else None,
        )
    
    def get_blockchain_link(self) -> str | None:
        """Get the Polygonscan link for this transaction."""
        if self.transaction_hash:
            return f"{POLYGONSCAN_URL}{self.transaction_hash}"
        return None
    
    def format_display(self) -> str:
        """
        Format transaction for display with colored BUY/SELL.
        
        Returns:
            Formatted string representation.
        """
        time_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        price_pct = f"{self.price_per_share * 100:.1f}%"
        
        # Color the side: green for BUY, red for SELL
        if self.side == "BUY":
            colored_side = f"{Fore.GREEN}BUY{Style.RESET_ALL}"
        elif self.side == "SELL":
            colored_side = f"{Fore.RED}SELL{Style.RESET_ALL}"
        else:
            colored_side = self.side
        
        # Format: BUY: 47.7 shares @ 22.1% = $10.54
        display = (
            f"[{time_str}] {colored_side}: {self.shares:.1f} shares of '{self.outcome}' "
            f"@ {price_pct} = ${self.total_cost:.2f}"
        )
        
        # Add market on new line
        market_display = self.market_slug[:50] if len(self.market_slug) > 50 else self.market_slug
        display += f"\n         Market: {market_display}"
        
        # Add blockchain link if available
        link = self.get_blockchain_link()
        if link:
            display += f"\n         🔗 {link}"
        
        return display
    
    def __hash__(self) -> int:
        """Make Transaction hashable for set operations."""
        return hash(self.id)
    
    def __eq__(self, other: object) -> bool:
        """Check equality based on ID."""
        if not isinstance(other, Transaction):
            return False
        return self.id == other.id
