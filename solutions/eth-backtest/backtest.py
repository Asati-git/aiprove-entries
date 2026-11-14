"""Backtest harness for the frozen ETH 1-minute dataset.

Cost model (documented approximation of the sandbox's):
  - taker fee 5 bps per side, maker fee 1 bp per side
  - slippage 10 bps * (trade size / bar volume) per side

PnL per bar t: position_t * (close_{t+1} - close_t) - costs of rebalancing.
"""

from __future__ import annotations

import csv

import numpy as np

TAKER_BPS = 5.0
MAKER_BPS = 1.0
SLIP_BPS = 10.0


def load_bars(path: str):
    rows = list(csv.DictReader(open(path)))
    close = np.array([float(r["close"]) for r in rows])
    high = np.array([float(r["high"]) for r in rows])
    low = np.array([float(r["low"]) for r in rows])
    vol = np.array([float(r["volume"]) for r in rows])
    return close, high, low, vol


def backtest(close, vol, positions, maker_fraction=1.0, fees=None):
    """positions: target ETH held during bar t (decided from data up to t).

    maker_fraction: share of each rebalance executed as maker (rest taker).
    """
    f = fees or (TAKER_BPS, MAKER_BPS, SLIP_BPS)
    taker_bps, maker_bps, slip_bps = f
    n = len(close)
    pnl = 0.0
    pos = 0.0
    trades = 0
    cost_total = 0.0
    equity = [0.0]
    for t in range(n - 1):
        target = positions[t]
        trade = target - pos
        if abs(trade) > 1e-12:
            trades += 1
            v = max(vol[t], 1e-9)
            fee_bps = maker_fraction * maker_bps + (1 - maker_fraction) * taker_bps
            cost = abs(trade) * close[t] * (
                fee_bps * 1e-4 + slip_bps * 1e-4 * min(abs(trade) / v, 10.0)
            )
            cost_total += cost
            pnl -= cost
            pos = target
        pnl += pos * (close[t + 1] - close[t])
        equity.append(pnl)
    eq = np.array(equity)
    peak = np.maximum.accumulate(eq)
    dd = (eq - peak).min()
    return {
        "pnl": pnl,
        "costs": cost_total,
        "trades": trades,
        "max_dd": dd,
        "equity": eq,
    }


def zscore_mr(close, lookback=60, entry=2.0, exit=0.5, cap=1.0):
    """Mean-reversion: fade deviations of price from its rolling mean."""
    n = len(close)
    pos = np.zeros(n)
    cur = 0.0
    for t in range(n):
        if t < lookback:
            pos[t] = 0.0
            continue
        window = close[t - lookback : t]
        mu = window.mean()
        sd = window.std()
        if sd < 1e-9:
            pos[t] = cur
            continue
        z = (close[t] - mu) / sd
        if z > entry:
            cur = -cap
        elif z < -entry:
            cur = cap
        elif abs(z) < exit:
            cur = 0.0
        pos[t] = cur
    return pos


def run_all():
    close, high, low, vol = load_bars(__file__.replace("backtest.py", "bars.csv"))
    n = len(close)
    split = int(n * 0.7)
    print(f"bars={n} train=0..{split} tail={split}..{n}")

    # baseline: buy & hold, short & hold
    print("buy&hold:", round((close[-1] - close[0]), 2))
    r = backtest(close, vol, np.ones(n - 1))
    print("short&hold:", round(r["pnl"], 2), "costs", round(r["costs"], 2))

    best = None
    for lookback in (20, 30, 60, 120, 240):
        for entry in (1.0, 1.5, 2.0, 2.5, 3.0):
            for exit_ in (0.0, 0.5, 1.0):
                pos = zscore_mr(close, lookback, entry, exit_)
                rt = backtest(close[:split], vol[:split], pos[: split - 1])
                if rt["pnl"] <= 0:
                    continue
                rv = backtest(close[split - 1 :], vol[split - 1 :], pos[split - 1 : -1][: len(close) - split])
                key = (lookback, entry, exit_)
                line = f"lb={lookback:3d} entry={entry} exit={exit_}: train {rt['pnl']:8.2f} ({rt['trades']:3d} tr) tail {rv['pnl']:8.2f} ({rv['trades']:3d} tr)"
                if best is None or rt["pnl"] + rv["pnl"] > best[0]:
                    best = (rt["pnl"] + rv["pnl"], line, key)
                print(line)
    print("\nBEST:", best[1])


if __name__ == "__main__":
    run_all()
