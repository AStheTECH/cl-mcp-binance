import json
import logging

from fastmcp import FastMCP
from pydantic import Field

from .service import BinanceClient

logger = logging.getLogger("binance-mcp-server")


def register_tools(mcp: FastMCP) -> None:
    """Register all Binance MCP tools."""

    # ========== Public Endpoints (No Auth) ==========

    @mcp.tool(
        name="binance_ping",
        description="Test connectivity to Binance API. Returns True if connection is successful. No authentication required.",
    )
    async def binance_ping() -> str:
        """Ping Binance API."""
        try:
            client = BinanceClient()
            result = await client.ping()
            return json.dumps({"success": True, "ping": result})
        except Exception as e:
            logger.error(f"Ping failed: {e}", exc_info=True)
            return json.dumps({"success": False, "error": str(e)})

    @mcp.tool(
        name="binance_server_time",
        description="Get Binance server time. No authentication required.",
    )
    async def binance_server_time() -> str:
        """Get server time."""
        try:
            client = BinanceClient()
            result = await client.get_server_time()
            return json.dumps({"success": True, "server_time": result})
        except Exception as e:
            logger.error(f"Failed to get server time: {e}", exc_info=True)
            return json.dumps({"success": False, "error": str(e)})

    @mcp.tool(
        name="binance_exchange_info",
        description="Get exchange information including trading rules, symbol information, and rate limits. No authentication required.",
    )
    async def binance_exchange_info() -> str:
        """Get exchange information."""
        try:
            client = BinanceClient()
            result = await client.get_exchange_info()

            # Extract only relevant symbol info to keep response manageable
            symbols = []
            for s in result.get("symbols", []):
                symbols.append(
                    {
                        "symbol": s.get("symbol"),
                        "status": s.get("status"),
                        "base_asset": s.get("baseAsset"),
                        "quote_asset": s.get("quoteAsset"),
                    }
                )

            output = {
                "success": True,
                "timezone": result.get("timezone"),
                "server_time": result.get("serverTime"),
                "symbols_count": len(symbols),
                "symbols": symbols[:100],  # Limit to first 100 for response size
            }
            return json.dumps(output, indent=2)
        except Exception as e:
            logger.error(f"Failed to get exchange info: {e}", exc_info=True)
            return json.dumps({"success": False, "error": str(e)})

    @mcp.tool(
        name="binance_orderbook",
        description="Get current order book for a trading pair. Shows bids and asks with prices and quantities. No authentication required.",
    )
    async def binance_orderbook(
        symbol: str = Field(..., description="Trading pair symbol (e.g., 'BTCUSDT')"),
        limit: int = Field(
            default=100,
            description="Number of bids/asks to return (max 5000)",
            ge=1,
            le=5000,
        ),
    ) -> str:
        """Get orderbook for a symbol."""
        try:
            client = BinanceClient()
            result = await client.get_orderbook(symbol, limit=limit)

            output = {
                "success": True,
                "symbol": symbol.upper(),
                "last_update_id": result.get("lastUpdateId"),
                "bids": result.get("bids", [])[:20],  # Limit display
                "asks": result.get("asks", [])[:20],
                "total_bids": len(result.get("bids", [])),
                "total_asks": len(result.get("asks", [])),
            }
            return json.dumps(output, indent=2)
        except Exception as e:
            logger.error(f"Failed to get orderbook for {symbol}: {e}", exc_info=True)
            return json.dumps({"success": False, "error": str(e)})

    @mcp.tool(
        name="binance_klines",
        description="Get candlestick/kline data for a trading pair. Returns OHLCV data for charting. No authentication required.",
    )
    async def binance_klines(
        symbol: str = Field(..., description="Trading pair symbol (e.g., 'BTCUSDT')"),
        interval: str = Field(
            default="1h", description="Kline interval: 1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M"
        ),
        limit: int = Field(
            default=100,
            description="Number of klines to return (max 1000)",
            ge=1,
            le=1000,
        ),
    ) -> str:
        """Get kline/candlestick data."""
        try:
            client = BinanceClient()
            result = await client.get_klines(symbol, interval=interval, limit=limit)

            klines = []
            for k in result:
                klines.append(
                    {
                        "open_time": k[0],
                        "open": k[1],
                        "high": k[2],
                        "low": k[3],
                        "close": k[4],
                        "volume": k[5],
                        "close_time": k[6],
                        "quote_volume": k[7],
                        "trades": k[8],
                    }
                )

            output = {
                "success": True,
                "symbol": symbol.upper(),
                "interval": interval,
                "count": len(klines),
                "klines": klines,
            }
            return json.dumps(output, indent=2)
        except Exception as e:
            logger.error(f"Failed to get klines for {symbol}: {e}", exc_info=True)
            return json.dumps({"success": False, "error": str(e)})

    @mcp.tool(
        name="binance_ticker_price",
        description="Get current price for a trading pair. If no symbol provided, returns prices for all symbols. No authentication required.",
    )
    async def binance_ticker_price(
        symbol: str = Field(
            default=None, description="Trading pair symbol (optional, e.g., 'BTCUSDT')"
        ),
    ) -> str:
        """Get ticker price."""
        try:
            client = BinanceClient()
            result = await client.get_ticker_price(symbol)

            if symbol:
                output = {
                    "success": True,
                    "symbol": result.get("symbol"),
                    "price": result.get("price"),
                }
            else:
                output = {
                    "success": True,
                    "count": len(result),
                    "prices": result[:100],  # Limit display
                }
            return json.dumps(output, indent=2)
        except Exception as e:
            logger.error(f"Failed to get ticker price for {symbol}: {e}", exc_info=True)
            return json.dumps({"success": False, "error": str(e)})

    # ========== Private Endpoints (Auth Required) ==========

    @mcp.tool(
        name="binance_account_info",
        description="Get account information including balances, commissions. Requires API key and secret.",
    )
    async def binance_account_info(
        api_key: str = Field(..., description="Binance API key"),
        api_secret: str = Field(..., description="Binance API secret"),
    ) -> str:
        """Get account information."""
        try:
            client = BinanceClient(api_key=api_key, api_secret=api_secret)
            result = await client.get_account_info()

            # Filter out zero balances
            non_zero_balances = [
                {"asset": b["asset"], "free": b["free"], "locked": b["locked"]}
                for b in result.get("balances", [])
                if float(b["free"]) > 0 or float(b["locked"]) > 0
            ]

            output = {
                "success": True,
                "maker_commission": result.get("makerCommission"),
                "taker_commission": result.get("takerCommission"),
                "balances": non_zero_balances,
            }
            return json.dumps(output, indent=2)
        except Exception as e:
            logger.error(f"Failed to get account info: {e}", exc_info=True)
            return json.dumps({"success": False, "error": str(e)})

    @mcp.tool(
        name="binance_create_order",
        description="Create a new order. Supports LIMIT and MARKET orders. Requires API key and secret.",
    )
    async def binance_create_order(
        api_key: str = Field(..., description="Binance API key"),
        api_secret: str = Field(..., description="Binance API secret"),
        symbol: str = Field(..., description="Trading pair symbol (e.g., 'BTCUSDT')"),
        side: str = Field(..., description="Order side: 'BUY' or 'SELL'"),
        order_type: str = Field(..., description="Order type: 'LIMIT' or 'MARKET'"),
        quantity: float = Field(..., description="Order quantity"),
        price: float = Field(
            default=None, description="Price for LIMIT orders (required for LIMIT)"
        ),
        time_in_force: str = Field(
            default="GTC",
            description="Time in force: 'GTC', 'IOC', 'FOK' (for LIMIT orders)",
        ),
    ) -> str:
        """Create an order."""
        try:
            client = BinanceClient(api_key=api_key, api_secret=api_secret)

            order_data = {
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": quantity,
            }

            if order_type.upper() == "LIMIT":
                if not price:
                    raise ValueError("Price is required for LIMIT orders")
                order_data["price"] = price
                order_data["timeInForce"] = time_in_force

            result = await client.create_order(order_data)

            output = {
                "success": True,
                "order_id": result.get("orderId"),
                "client_order_id": result.get("clientOrderId"),
                "symbol": result.get("symbol"),
                "side": result.get("side"),
                "type": result.get("type"),
                "price": result.get("price"),
                "orig_quantity": result.get("origQty"),
                "executed_quantity": result.get("executedQty"),
                "status": result.get("status"),
                "fills": result.get("fills", []),
            }
            return json.dumps(output, indent=2)
        except Exception as e:
            logger.error(f"Failed to create order: {e}", exc_info=True)
            return json.dumps({"success": False, "error": str(e)})

    @mcp.tool(
        name="binance_cancel_order",
        description="Cancel an existing order. Requires API key and secret.",
    )
    async def binance_cancel_order(
        api_key: str = Field(..., description="Binance API key"),
        api_secret: str = Field(..., description="Binance API secret"),
        symbol: str = Field(..., description="Trading pair symbol (e.g., 'BTCUSDT')"),
        order_id: int = Field(default=None, description="Order ID to cancel"),
        client_order_id: str = Field(
            default=None, description="Client order ID to cancel"
        ),
    ) -> str:
        """Cancel an order."""
        try:
            client = BinanceClient(api_key=api_key, api_secret=api_secret)
            result = await client.cancel_order(
                symbol, order_id=order_id, client_order_id=client_order_id
            )

            output = {
                "success": True,
                "symbol": result.get("symbol"),
                "order_id": result.get("orderId"),
                "client_order_id": result.get("clientOrderId"),
                "status": result.get("status"),
                "cancelled_quantity": result.get("cancelledQty", result.get("origQty")),
            }
            return json.dumps(output, indent=2)
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}", exc_info=True)
            return json.dumps({"success": False, "error": str(e)})

    @mcp.tool(
        name="binance_open_orders",
        description="Get all open orders. Optionally filter by symbol. Requires API key and secret.",
    )
    async def binance_open_orders(
        api_key: str = Field(..., description="Binance API key"),
        api_secret: str = Field(..., description="Binance API secret"),
        symbol: str = Field(
            default=None, description="Optional trading pair symbol to filter"
        ),
    ) -> str:
        """Get open orders."""
        try:
            client = BinanceClient(api_key=api_key, api_secret=api_secret)
            result = await client.get_open_orders(symbol=symbol)

            output = {
                "success": True,
                "count": len(result),
                "orders": [
                    {
                        "symbol": o.get("symbol"),
                        "order_id": o.get("orderId"),
                        "side": o.get("side"),
                        "price": o.get("price"),
                        "orig_quantity": o.get("origQty"),
                        "executed_quantity": o.get("executedQty"),
                        "status": o.get("status"),
                        "time": o.get("time"),
                    }
                    for o in result
                ],
            }
            return json.dumps(output, indent=2)
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}", exc_info=True)
            return json.dumps({"success": False, "error": str(e)})

    @mcp.tool(
        name="binance_my_trades",
        description="Get your trade history for a symbol. Requires API key and secret.",
    )
    async def binance_my_trades(
        api_key: str = Field(..., description="Binance API key"),
        api_secret: str = Field(..., description="Binance API secret"),
        symbol: str = Field(..., description="Trading pair symbol (e.g., 'BTCUSDT')"),
        limit: int = Field(
            default=100,
            description="Maximum trades to return (max 1000)",
            ge=1,
            le=1000,
        ),
    ) -> str:
        """Get trade history."""
        try:
            client = BinanceClient(api_key=api_key, api_secret=api_secret)
            result = await client.get_my_trades(symbol, limit=limit)

            output = {
                "success": True,
                "symbol": symbol.upper(),
                "count": len(result),
                "trades": [
                    {
                        "trade_id": t.get("id"),
                        "order_id": t.get("orderId"),
                        "price": t.get("price"),
                        "quantity": t.get("qty"),
                        "quote_quantity": t.get("quoteQty"),
                        "commission": t.get("commission"),
                        "commission_asset": t.get("commissionAsset"),
                        "time": t.get("time"),
                        "is_buyer": t.get("isBuyer"),
                        "is_maker": t.get("isMaker"),
                    }
                    for t in result
                ],
            }
            return json.dumps(output, indent=2)
        except Exception as e:
            logger.error(f"Failed to get trades: {e}", exc_info=True)
            return json.dumps({"success": False, "error": str(e)})

    @mcp.tool(
        name="binance_health_check",
        description="Check server readiness and basic connectivity.",
    )
    def binance_health_check() -> str:
        """Health check endpoint."""
        return json.dumps(
            {
                "status": "ok",
                "server": "CL Binance MCP Server",
                "type": "third-party integration",
                "auth_required": "for private endpoints only",
            }
        )
