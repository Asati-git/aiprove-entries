"""Live market prices for honest forecasts.

- BTC / ETH: Binance public klines (fallback: CoinGecko).
- SPY / NVDA / GLD: stooq.com free CSV quotes (last official close).
"""

from __future__ import annotations

import datetime as dt
import logging

import requests

log = logging.getLogger("aiprove.prices")

BINANCE = "https://api.binance.com"
COINGECKO = "https://api.coingecko.com/api/v3"
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart"


def binance_daily_closes(symbol: str, limit: int = 3) -> list[dict]:
    """Last `limit` daily UTC candles: [{open, high, low, close, ts}]."""
    r = requests.get(
        f"{BINANCE}/api/v3/klines",
        params={"symbol": symbol, "interval": "1d", "limit": limit},
        timeout=15,
    )
    r.raise_for_status()
    return [
        {
            "ts": dt.datetime.fromtimestamp(k[0] / 1000, dt.timezone.utc),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
        }
        for k in r.json()
    ]


def coingecko_price(ids: str) -> float:
    r = requests.get(f"{COINGECKO}/simple/price", params={"ids": ids, "vs_currencies": "usd"}, timeout=15)
    r.raise_for_status()
    return list(r.json().values())[0]["usd"]


def current_price(symbol: str) -> float:
    """symbol like 'BTCUSDT' / 'ETHUSDT'."""
    try:
        r = requests.get(f"{BINANCE}/api/v3/ticker/price", params={"symbol": symbol}, timeout=15)
        r.raise_for_status()
        return float(r.json()["price"])
    except Exception as e:  # noqa: BLE001
        log.warning("binance ticker failed (%s); falling back to coingecko", e)
        ids = {"BTCUSDT": "bitcoin", "ETHUSDT": "ethereum"}[symbol]
        return coingecko_price(ids)


def stock_quote(ticker: str) -> dict:
    """Last daily candle for a US ticker (e.g. 'SPY'), from Yahoo Finance."""
    r = requests.get(
        f"{YAHOO}/{ticker}",
        params={"range": "5d", "interval": "1d"},
        headers={"user-agent": "Mozilla/5.0"},
        timeout=15,
    )
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    ts = res["timestamp"]
    q = res["indicators"]["quote"][0]
    closes = [(t, c) for t, c in zip(ts, q["close"]) if c is not None]
    t, c = closes[-1]
    return {
        "date": dt.datetime.fromtimestamp(t, dt.timezone.utc).date().isoformat(),
        "close": float(c),
        "closes": [float(x) for _, x in closes],
    }
