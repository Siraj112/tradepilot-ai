import json
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
        for symbol in ["BTC", "ETH"]:
            if symbol in data:
                prices.append({
                    "symbol": symbol,
                    "price_usd": float(data[symbol])
                })

        return {
            "provider": "Hyperliquid public API",
            "data_connected": True,
            "markets": prices
        }

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Market data provider unavailable. Please try again."
        )
