"""Honest forecast builder for the AIProve forecast bounties.

Fetches live market data and turns it into the exact prediction strings the
AIProve web UI sends. Prints a table in dry-run; --live submits.

Usage:
    python run_forecasts.py            # dry run (default)
    python run_forecasts.py --live     # actually submit
    python run_forecasts.py --only btc-tomorrow,forecast-eth-24h
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import sys

sys.path.insert(0, __file__.rsplit("\\", 1)[0])

from aiprove.client import AIProveClient
from aiprove.prices import binance_daily_closes, current_price, stock_quote
from aiprove.wallet import load_wallet

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

# --- honest signal helpers -------------------------------------------------


def prob_from_momentum(momentum: float, k: float = 35.0, floor: float = 0.10, cap: float = 0.90) -> float:
    """Map a fractional 24h move to a probability of closing higher.

    A 2% 24h move maps to roughly p=0.67 — momentum, but honestly uncertain.
    """
    p = 1.0 / (1.0 + math.exp(-k * momentum))
    return max(floor, min(cap, p))


def crypto_direction(symbol: str) -> dict:
    closes = binance_daily_closes(symbol, limit=3)
    last = closes[-1]
    prev = closes[-2]
    cur = current_price(symbol)
    # move over the last ~24h, measured off the previous daily close
    momentum = cur / prev["close"] - 1.0
    p = prob_from_momentum(momentum)
    return {
        "prev_close": prev["close"],
        "current": cur,
        "momentum": momentum,
        "prob": p,
        "answer": "yes" if p >= 0.5 else "no",
    }


def build_predictions() -> list[dict]:
    preds = []

    btc = crypto_direction("BTCUSDT")
    eth = crypto_direction("ETHUSDT")

    # --- Brier yes/no + probability bounties -------------------------------
    preds.append({
        "slug": "btc-tomorrow",
        "prediction": f"{btc['answer']} {btc['prob']:.2f}",
        "rationale": f"BTC 24h momentum {btc['momentum']:+.2%} (prev close {btc['prev_close']:.0f}, now {btc['current']:.0f})",
    })
    preds.append({
        "slug": "forecast-eth-24h",
        "prediction": f"{eth['answer']} {eth['prob']:.2f}",
        "rationale": f"ETH 24h momentum {eth['momentum']:+.2%}",
    })
    preds.append({
        "slug": "forecast-btc-7d",
        "prediction": f"{btc['answer']} {min(0.65, btc['prob']):.2f}",
        "rationale": "same signal as 24h, damped — a week out is far less certain than a day",
    })

    # --- directional trade call --------------------------------------------
    preds.append({
        "slug": "signal-eth-pnl-24h",
        "prediction": "long" if eth["momentum"] >= 0 else "short",
        "rationale": f"ETH 24h momentum {eth['momentum']:+.2%}",
    })

    # --- point forecasts for stocks (weekend: last official close) ----------
    for slug, ticker, label in [
        ("spy-close-1dollar", "SPY", "SPY"),
        ("forecast-gold-tomorrow", "GLD", "GLD"),
        ("forecast-nvda-3d", "NVDA", "NVDA"),
    ]:
        try:
            q = stock_quote(ticker)
        except Exception as e:  # noqa: BLE001
            logging.warning("stooq %s failed: %s", ticker, e)
            continue
        preds.append({
            "slug": slug,
            "prediction": f"{q['close']:.2f}",
            "rationale": (
                f"last official {label} close {q['close']:.2f} ({q['date']}); "
                "random-walk point forecast — the last close is the least-biased "
                "estimate of the next close, and all rivals fight over cents of drift"
            ),
        })
    return preds


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="actually submit (default: dry run)")
    ap.add_argument("--only", help="comma-separated slugs to submit")
    args = ap.parse_args()

    preds = build_predictions()
    if args.only:
        keep = {s.strip() for s in args.only.split(",")}
        preds = [p for p in preds if p["slug"] in keep]

    print(f"{'slug':24} {'prediction':18} rationale")
    print("-" * 100)
    for p in preds:
        print(f"{p['slug']:24} {p['prediction']:18} {p['rationale']}")

    cfg = json.load(open(__file__.rsplit("\\", 1)[0] + "\\config.json", encoding="utf-8"))
    wcfg = cfg["wallet"]
    if wcfg.get("source") == "db":
        address, pk = load_wallet(address=wcfg.get("address"), db_path=wcfg.get("db_path"))
    else:
        from aiprove.wallet import load_from_env

        address, pk = load_from_env()
    client = AIProveClient(
        pk,
        api_base=cfg["api_base"],
        handle=cfg["handle"],
        dry_run=not args.live,
    )
    client.authenticate()

    if not args.live:
        print("\n[dry-run] would submit the predictions above from", address)
    for p in preds:
        client.submit_prediction(p["slug"], p["prediction"])
    if args.live:
        print("\nSubmitted", len(preds), "forecasts from", address)
        print(json.dumps(client.me(), indent=2)[:2000])


if __name__ == "__main__":
    main()
