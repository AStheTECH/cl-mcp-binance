# Binance MCP Server

A Model Context Protocol (MCP) server that provides access to Binance Spot API for trading and market data.

## Authentication

Binance API requires authentication for private endpoints (account info, orders, trades):

- **Public endpoints**: No authentication required (market data, orderbook, tickers)
- **Private endpoints**: API key and secret required (HMAC SHA256 authentication)

**Auth Model**: For private operations, API credentials must be provided with every tool call. The server is stateless and does not store credentials between requests.

**MCP Type**: Third-party integration (auth required for trading operations only)

## Setup

1. Get your Binance API credentials from [Binance API Management](https://www.binance.com/en/support/faq/how-to-create-api-keys-on-binance-360002502072)

2. For testing, use Binance Testnet:
   ```bash
   export BINANCE_USE_TESTNET=true