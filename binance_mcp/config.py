import logging
import os

# Binance API Base Endpoints
BINANCE_API_BASE = "https://api.binance.com"
BINANCE_API_TESTNET_BASE = "https://testnet.binance.vision"

# Use environment variable to switch to testnet
USE_TESTNET = os.getenv("BINANCE_USE_TESTNET", "false").lower() == "true"
API_BASE_URL = BINANCE_API_TESTNET_BASE if USE_TESTNET else BINANCE_API_BASE

# API Endpoints
ENDPOINTS = {
    "ping": "/api/v3/ping",
    "time": "/api/v3/time",
    "exchange_info": "/api/v3/exchangeInfo",
    "orderbook": "/api/v3/depth",
    "trades": "/api/v3/trades",
    "klines": "/api/v3/klines",
    "ticker_price": "/api/v3/ticker/price",
    "ticker_book": "/api/v3/ticker/bookTicker",
    "account": "/api/v3/account",
    "create_order": "/api/v3/order",
    "get_order": "/api/v3/order",
    "cancel_order": "/api/v3/order",
    "open_orders": "/api/v3/openOrders",
    "all_orders": "/api/v3/allOrders",
    "my_trades": "/api/v3/myTrades",
}

# Defaults
DEFAULT_RECV_WINDOW = 5000
DEFAULT_TIMEOUT = 30


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
