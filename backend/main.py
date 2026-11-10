import math
import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="TradePilot AI",
    description="Multi-market research and paper trading backend",
    version="0.3.0"
)

@app.get("/")
def home():
    return {
        "app": "TradePilot AI",
        "status": "running",
        "mode": "paper_trading",
        "live_trading": False
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/markets")
def markets():
    return {
        "status": "watchlist_ready",
        "data_connected": False,
        "markets": [
            {"name": "Bitcoin", "symbol": "BTC", "category": "Crypto"},
            {"name": "Ethereum", "symbol": "ETH", "category": "Crypto"},
            {"name": "EUR/USD", "symbol": "EURUSD", "category": "Forex"},
            {"name": "GBP/USD", "symbol": "GBPUSD", "category": "Forex"},
            {"name": "Gold", "symbol": "XAUUSD", "category": "Gold"}
        ]
    }

@app.get("/markets/crypto")
def crypto_prices():
    request = Request(
        "https://api.hyperliquid.xyz/info",
        data=json.dumps({"type": "allMids"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urlopen(request, timeout=15) as response:
            data = json.loads(response.read())
        prices = []
        received_at = datetime.now(timezone.utc).isoformat()
        for symbol in ["BTC", "ETH"]:
            if symbol in data:
                price = float(data[symbol])
                if price > 0:
                    prices.append({
                        "symbol": symbol,
                        "price_usd": price,
                        "server_received_at": received_at,
                        "timestamp_type": "server_received_at"
                    })
        return {
            "provider": "Hyperliquid public API",
            "data_connected": len(prices) == 2,
            "freshness_note": "Server receive time; exchange quote timestamp not provided",
            "markets": prices
        }
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Market data provider unavailable. Please try again."
        )


@app.get("/markets/binance")
def binance_prices():
    results = []
    for symbol in ["BTCUSDT", "ETHUSDT"]:
        url = f"https://data-api.binance.vision/api/v3/ticker/bookTicker?symbol={symbol}"
        try:
            request = Request(url, headers={"Accept": "application/json"})
            with urlopen(request, timeout=10) as response:
                quote = json.loads(response.read())
            bid = float(quote["bidPrice"])
            ask = float(quote["askPrice"])
            if not all(math.isfinite(x) and x > 0 for x in [bid, ask]) or ask < bid:
                raise ValueError("Invalid quote")
            results.append({
                "symbol": symbol.replace("USDT", ""),
                "market_type": "Binance Spot",
                "bid": bid,
                "ask": ask,
                "mid_price": (bid + ask) / 2,
                "spread": ask - bid,
                "server_received_at": datetime.now(timezone.utc).isoformat(),
                "status": "available"
            })
        except Exception:
            results.append({
                "symbol": symbol.replace("USDT", ""),
                "market_type": "Binance Spot",
                "status": "unavailable"
            })
    return {
        "provider": "Binance public Spot API",
        "data_connected": all(item["status"] == "available" for item in results),
        "markets": results
    }



@app.get("/markets/compare")
def compare_crypto_prices():
    try:
        hyper = crypto_prices()
    except HTTPException:
        hyper = {"markets": []}

    try:
        binance = binance_prices()
    except HTTPException:
        binance = {"markets": []}

    hyper_map = {
        item["symbol"]: item
        for item in hyper.get("markets", [])
        if isinstance(item, dict) and "symbol" in item
    }
    binance_map = {
        item["symbol"]: item
        for item in binance.get("markets", [])
        if isinstance(item, dict) and "symbol" in item
    }

    comparisons = []

    for symbol in ["BTC", "ETH"]:
        h = hyper_map.get(symbol)
        b = binance_map.get(symbol)

        if not h or not b or b.get("status") != "available":
            comparisons.append({
                "symbol": symbol,
                "status": "source_unavailable"
            })
            continue

        try:
            h_price = float(h["price_usd"])
            b_price = float(b["mid_price"])

            if not all(math.isfinite(x) and x > 0 for x in [h_price, b_price]):
                raise ValueError("Invalid price")

            difference = abs(h_price - b_price)
            difference_percent = (difference / b_price) * 100

            h_time = datetime.fromisoformat(
                h["server_received_at"].replace("Z", "+00:00")
            )
            b_time = datetime.fromisoformat(
                b["server_received_at"].replace("Z", "+00:00")
            )
            timestamp_gap = abs((h_time - b_time).total_seconds())

            comparisons.append({
                "symbol": symbol,
                "status": "comparison_available",
                "hyperliquid": {
                    "provider": "Hyperliquid",
                    "market_type": "Perpetual reference",
                    "price": h_price,
                    "server_received_at": h["server_received_at"]
                },
                "binance": {
                    "provider": "Binance",
                    "market_type": "Spot",
                    "mid_price": b_price,
                    "bid": b["bid"],
                    "ask": b["ask"],
                    "server_received_at": b["server_received_at"]
                },
                "absolute_difference": difference,
                "difference_percent": difference_percent,
                "timestamp_gap_seconds": timestamp_gap,
                "note": "Spot and perpetual prices may differ; this is a reference comparison, not an executable-price guarantee."
            })
        except (KeyError, TypeError, ValueError, OverflowError):
            comparisons.append({
                "symbol": symbol,
                "status": "invalid_data"
            })

    return {
        "status": "comparison_ready",
        "markets": comparisons
    }

@app.get("/markets/forex-gold")
def forex_gold_prices():
    url = (
        "https://biquote.io/api/latest"
        "?symbols=EURUSD&symbols=GBPUSD&symbols=XAUUSD"
    )

    request = Request(url, headers={"Accept": "application/json"})

    try:
        with urlopen(request, timeout=15) as response:
            data = json.loads(response.read())

        markets = []

        for symbol in ["EURUSD", "GBPUSD", "XAUUSD"]:
            quote = data.get(symbol)

            if not isinstance(quote, dict):
                markets.append({
                    "symbol": symbol,
                    "status": "unavailable"
                })
                continue

            try:
                mid = float(quote["mid"])
                bid = float(quote["bid"])
                ask = float(quote["ask"])
                age = float(quote["quoteAgeSeconds"])
            except (KeyError, TypeError, ValueError):
                markets.append({
                    "symbol": symbol,
                    "status": "invalid_data"
                })
                continue

            if not all(math.isfinite(value) for value in [mid, bid, ask, age]) or mid <= 0 or bid <= 0 or ask < bid or age < 0:
                markets.append({"symbol": symbol, "status": "invalid_data"})
                continue
            stale = bool(quote.get("stale", True))
            fresh = not stale and age <= 60

            markets.append({
                "symbol": symbol,
                "price_usd": mid,
                "bid": bid,
                "ask": ask,
                "spread": float(quote.get("spread", ask - bid)),
                "direction": quote.get("direction"),
                "day_change_percent": quote.get("dayDiffPercent"),
                "market_state": quote.get("marketState"),
                "source": quote.get("source"),
                "timestamp": quote.get("timestamp"),
                "quote_age_seconds": age,
                "stale": stale,
                "status": "available" if fresh else "stale"
            })

        return {
            "provider": "Biquote",
            "data_connected": all(
                market["status"] == "available"
                for market in markets
            ),
            "markets": markets
        }

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Forex and Gold market data unavailable"
        )
