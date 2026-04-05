import hashlib
import hmac
import json
import logging
import time
from typing import Any, Dict, List, Optional

import httpx

from .config import API_BASE_URL, DEFAULT_RECV_WINDOW, DEFAULT_TIMEOUT, ENDPOINTS

logger = logging.getLogger("binance-mcp-server")


class BinanceClient:
    """Client for Binance Spot API."""

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """Initialize Binance API client.

        Args:
            api_key: Binance API key (required for private endpoints)
            api_secret: Binance API secret (required for private endpoints)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = API_BASE_URL
        self.recv_window = DEFAULT_RECV_WINDOW

    def _generate_signature(self, query_string: str) -> str:
        """Generate HMAC SHA256 signature for private endpoints."""
        if not self.api_secret:
            raise ValueError("API secret required for private endpoints")
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _build_headers(self, is_private: bool = False) -> Dict[str, str]:
        """Build request headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if is_private and self.api_key:
            headers["X-MBX-APIKEY"] = self.api_key
        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        is_private: bool = False,
    ) -> Any:
        """Make HTTP request to Binance API."""
        url = f"{self.base_url}{endpoint}"
        headers = self._build_headers(is_private)

        # Add timestamp and signature for private endpoints
        if is_private:
            if not self.api_key or not self.api_secret:
                raise ValueError("API key and secret required for private endpoints")

            params = params or {}
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = self.recv_window

            # Sort parameters and generate signature
            query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            signature = self._generate_signature(query_string)
            params["signature"] = signature

        async with httpx.AsyncClient() as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(
                        url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT
                    )
                elif method.upper() == "POST":
                    response = await client.post(
                        url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT
                    )
                elif method.upper() == "DELETE":
                    response = await client.delete(
                        url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT
                    )
                else:
                    raise ValueError(f"Unsupported method: {method}")

                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Binance returns error details in response body
                error_body = e.response.text
                logger.error(
                    f"Binance API error: {e.response.status_code} - {error_body}"
                )
                raise Exception(f"Binance API error: {error_body}")

    # ========== Public Endpoints (No Auth) ==========

    async def ping(self) -> bool:
        """Test connectivity to Binance API."""
        await self._request("GET", ENDPOINTS["ping"])
        return True

    async def get_server_time(self) -> int:
        """Get server time from Binance."""
        result = await self._request("GET", ENDPOINTS["time"])
        return result.get("serverTime", 0)

    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information (symbols, filters, etc.)."""
        return await self._request("GET", ENDPOINTS["exchange_info"])

    async def get_orderbook(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get orderbook for a symbol."""
        params = {"symbol": symbol.upper(), "limit": limit}
        return await self._request("GET", ENDPOINTS["orderbook"], params=params)

    async def get_recent_trades(
        self, symbol: str, limit: int = 500
    ) -> List[Dict[str, Any]]:
        """Get recent trades for a symbol."""
        params = {"symbol": symbol.upper(), "limit": limit}
        return await self._request("GET", ENDPOINTS["trades"], params=params)

    async def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[List[Any]]:
        """Get kline/candlestick data."""
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit,
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        return await self._request("GET", ENDPOINTS["klines"], params=params)

    async def get_ticker_price(self, symbol: Optional[str] = None) -> Any:
        """Get ticker price for a symbol or all symbols."""
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()
        return await self._request("GET", ENDPOINTS["ticker_price"], params=params)

    async def get_book_ticker(self, symbol: Optional[str] = None) -> Any:
        """Get best price/quantity on orderbook."""
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()
        return await self._request("GET", ENDPOINTS["ticker_book"], params=params)

    # ========== Private Endpoints (Auth Required) ==========

    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information (balances, commissions)."""
        return await self._request("GET", ENDPOINTS["account"], is_private=True)

    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order."""
        params = {
            "symbol": order_data["symbol"].upper(),
            "side": order_data["side"].upper(),
            "type": order_data["type"].upper(),
            "quantity": str(order_data["quantity"]),
        }

        # Add price for limit orders
        if order_data["type"].upper() == "LIMIT":
            params["price"] = str(order_data["price"])
            params["timeInForce"] = order_data.get("timeInForce", "GTC")

        if order_data.get("newClientOrderId"):
            params["newClientOrderId"] = order_data["newClientOrderId"]

        return await self._request(
            "POST", ENDPOINTS["create_order"], params=params, is_private=True
        )

    async def get_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get order status."""
        params = {"symbol": symbol.upper()}
        if order_id:
            params["orderId"] = order_id
        elif client_order_id:
            params["origClientOrderId"] = client_order_id
        else:
            raise ValueError("Either order_id or client_order_id is required")

        return await self._request(
            "GET", ENDPOINTS["get_order"], params=params, is_private=True
        )

    async def cancel_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Cancel an order."""
        params = {"symbol": symbol.upper()}
        if order_id:
            params["orderId"] = order_id
        elif client_order_id:
            params["origClientOrderId"] = client_order_id
        else:
            raise ValueError("Either order_id or client_order_id is required")

        return await self._request(
            "DELETE", ENDPOINTS["cancel_order"], params=params, is_private=True
        )

    async def get_open_orders(
        self, symbol: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all open orders."""
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()
        return await self._request(
            "GET", ENDPOINTS["open_orders"], params=params, is_private=True
        )

    async def get_all_orders(
        self, symbol: str, limit: int = 500, order_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all orders for a symbol."""
        params = {"symbol": symbol.upper(), "limit": limit}
        if order_id:
            params["orderId"] = order_id
        return await self._request(
            "GET", ENDPOINTS["all_orders"], params=params, is_private=True
        )

    async def get_my_trades(
        self, symbol: str, limit: int = 500, from_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get account trade history."""
        params = {"symbol": symbol.upper(), "limit": limit}
        if from_id:
            params["fromId"] = from_id
        return await self._request(
            "GET", ENDPOINTS["my_trades"], params=params, is_private=True
        )
