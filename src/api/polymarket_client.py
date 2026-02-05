"""
Polymarket API client.

Handles HTTP requests to the Polymarket Data API.
"""

import requests
from typing import Any

from src.config.settings import Settings
from src.logging.logger import PolymarketLogger, get_logger


class PolymarketAPIError(Exception):
    """Custom exception for Polymarket API errors."""
    
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class PolymarketClient:
    """HTTP client for Polymarket Data API."""
    
    def __init__(self, settings: Settings, logger: PolymarketLogger | None = None):
        """
        Initialize the API client.
        
        Args:
            settings: Application settings.
            logger: Logger instance for output.
        """
        self._settings = settings
        self._logger = logger or get_logger(debug=settings.debug)
        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/json",
            "User-Agent": "PolymarketListener/1.0",
        })
    
    def _make_request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """
        Make an HTTP GET request to the API.
        
        Args:
            endpoint: API endpoint path.
            params: Query parameters.
        
        Returns:
            Parsed JSON response.
        
        Raises:
            PolymarketAPIError: If the request fails.
        """
        url = f"{self._settings.api_base_url}{endpoint}"
        
        self._logger.debug(f"Request: GET {url}")
        if params:
            self._logger.debug(f"Params: {params}")
        
        try:
            response = self._session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            raise PolymarketAPIError("Request timed out", status_code=408)
        
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            error_message = f"HTTP {status_code}: {e.response.text}" if e.response else str(e)
            raise PolymarketAPIError(error_message, status_code=status_code)
        
        except requests.exceptions.RequestException as e:
            raise PolymarketAPIError(f"Request failed: {str(e)}")
    
    def get_activity(
        self,
        user_address: str,
        limit: int = 100,
        offset: int = 0,
        activity_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get user activity/transactions.
        
        Args:
            user_address: Polymarket wallet address.
            limit: Maximum results to return (max 500).
            offset: Pagination offset.
            activity_type: Filter by activity type (trade, split, merge, etc.).
        
        Returns:
            List of activity records.
        """
        params: dict[str, Any] = {
            "user": user_address,
            "limit": min(limit, 500),
            "offset": offset,
        }
        
        if activity_type:
            params["type"] = activity_type
        
        result = self._make_request("/activity", params=params)
        
        # API returns a list directly
        if isinstance(result, list):
            return result
        
        # Or it might be wrapped in a response object
        return result.get("data", result.get("activities", []))
    
    def get_trades(
        self,
        user_address: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Get user trade history.
        
        Args:
            user_address: Polymarket wallet address.
            limit: Maximum results to return.
            offset: Pagination offset.
        
        Returns:
            List of trade records.
        """
        params = {
            "user": user_address,
            "limit": min(limit, 500),
            "offset": offset,
        }
        
        result = self._make_request("/trades", params=params)
        
        if isinstance(result, list):
            return result
        
        return result.get("data", result.get("trades", []))
    
    def close(self) -> None:
        """Close the HTTP session."""
        self._session.close()
