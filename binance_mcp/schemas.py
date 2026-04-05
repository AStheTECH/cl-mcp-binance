from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


# Public API Schemas
class SymbolInfo(TypedDict, total=False):
    """Symbol information from exchange info."""

    symbol: str
    status: str
    baseAsset: str
    quoteAsset: str
    filters: List[Dict[str, Any]]


class OrderbookEntry(TypedDict):
    """Orderbook bid/ask entry."""

    price: str
    quantity: str


class Orderbook(TypedDict, total=False):
    """Orderbook response."""

    lastUpdateId: int
    bids: List[OrderbookEntry]
    asks: List[OrderbookEntry]


class Kline(TypedDict):
    """Kline/candlestick data."""

    open_time: int
    open: str
    high: str
    low: str
    close: str
    volume: str
    close_time: int
    quote_volume: str
    trades: int


class TickerPrice(TypedDict):
    """Ticker price."""

    symbol: str
    price: str


# Private API Schemas
class AccountAsset(TypedDict, total=False):
    """Account asset balance."""

    asset: str
    free: str
    locked: str


class AccountInfo(TypedDict, total=False):
    """Account information."""

    makerCommission: int
    takerCommission: int
    balances: List[AccountAsset]


class OrderRequest(TypedDict, total=False):
    """Order creation request."""

    symbol: str
    side: str  # BUY or SELL
    type: str  # LIMIT, MARKET, etc.
    quantity: str
    price: Optional[str]
    timeInForce: Optional[str]  # GTC, IOC, FOK
    newClientOrderId: Optional[str]


class OrderResponse(TypedDict, total=False):
    """Order response."""

    symbol: str
    orderId: int
    clientOrderId: str
    price: str
    origQty: str
    executedQty: str
    status: str
    timeInForce: str
    type: str
    side: str


class Trade(TypedDict, total=False):
    """Trade information."""

    symbol: str
    id: int
    orderId: int
    price: str
    qty: str
    quoteQty: str
    commission: str
    commissionAsset: str
    time: int
    isBuyer: bool
    isMaker: bool
