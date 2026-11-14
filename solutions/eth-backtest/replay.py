"""Replay strategy.py positions over bars.csv with an explicit cost model.

Costs: maker 1 bp / taker 5 bps per side (blended via --maker-fraction),
slippage 10 bps * (trade size / bar volume) per side.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from strategy import run

MAKER_BPS = 1.0
TAKER_BPS = 5.0
SLIP_BPS = 10.0


def replay(closes, vols, positions, maker_fraction=1.0):
    pnl = 0.0
    costs = 0.0
    pos = 0.0
    trades = 0
    equity = [0.0]
    for t in range(len(closes) - 1):
        target = positions[t]
        trade = target - pos
        if abs(trade) > 1e-12:
            trades += 1
            fee_bps = maker_fraction * MAKER_BPS + (1 - maker_fraction) * TAKER_BPS
            costs += abs(trade) * closes[t] * (
                fee_bps * 1e-4 + SLIP_BPS * 1e-4 * min(abs(trade) / max(vols[t], 1e-9), 10.0)
            )
            pos = target
        pnl += pos * (closes[t + 1] - closes[t]) - (0)
        equity.append(pnl - costs)
    peak = 0.0
    dd = 0.0
    for e in equity:
        peak = max(peak, e)
        dd = min(dd, e - peak)
    return pnl - costs, costs, trades, dd


if __name__ == "__main__":
    bars = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "bars.csv")
    pos, closes, vols = run(bars)
    n = len(closes)
    split = int(n * 0.7)
    for label, sl in [("train 0-70%", slice(0, split)), ("tail 70-100%", slice(split - 1, n))]:
        p, c, tr, dd = replay(
            closes[sl], vols[sl], pos[sl], maker_fraction=0.5
        )
        print(f"{label}: net PnL {p:8.2f}  costs {c:6.2f}  trades {tr:3d}  maxDD {dd:7.2f}")
    p, c, tr, dd = replay(closes, vols, pos, maker_fraction=0.5)
    print(f"full   : net PnL {p:8.2f}  costs {c:6.2f}  trades {tr:3d}  maxDD {dd:7.2f}")
