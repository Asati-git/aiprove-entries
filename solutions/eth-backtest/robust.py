"""Robustness check + trend filter variant."""
import numpy as np
from backtest import backtest, load_bars, zscore_mr


def mr_with_trend(close, lookback=20, entry=3.0, exit_=0.5, cap=1.0, trend_lb=240, trend_cap=0.3):
    n = len(close)
    pos = np.zeros(n)
    cur = 0.0
    for t in range(n):
        if t < lookback:
            pos[t] = 0.0
            continue
        w = close[t - lookback : t]
        mu, sd = w.mean(), w.std()
        z = (close[t] - mu) / sd if sd > 1e-9 else 0.0
        if z > entry:
            cur = -cap
        elif z < -entry:
            cur = cap
        elif abs(z) < exit_:
            cur = 0.0
        bias = 0.0
        if t >= trend_lb:
            bias = -trend_cap if close[t] < close[t - trend_lb] else trend_cap
        pos[t] = np.clip(cur + bias, -1, 1)
    return pos


close, high, low, vol = load_bars(__file__.replace("robust.py", "bars.csv"))
n = len(close)
split = int(n * 0.7)

print("== parameter neighbourhood (MR only) ==")
for lb in (15, 20, 25, 30):
    for entry in (2.5, 3.0, 3.5):
        pos = zscore_mr(close, lb, entry, 0.5)
        rt = backtest(close[:split], vol[:split], pos[: split - 1])
        rv = backtest(close[split - 1 :], vol[split - 1 :], pos[split - 1 : -1][: len(close) - split])
        tot = rt["pnl"] + rv["pnl"]
        print(f"lb={lb:2d} e={entry}: train {rt['pnl']:7.2f} tail {rv['pnl']:7.2f} total {tot:7.2f}")

print("\n== MR + trend bias ==")
for tb in (0.0, 0.2, 0.3, 0.5):
    for tlb in (120, 240, 480):
        pos = mr_with_trend(close, 20, 3.0, 0.5, 1.0, tlb, tb)
        rt = backtest(close[:split], vol[:split], pos[: split - 1])
        rv = backtest(close[split - 1 :], vol[split - 1 :], pos[split - 1 : -1][: len(close) - split])
        print(f"trend_bias={tb} trend_lb={tlb}: train {rt['pnl']:7.2f} tail {rv['pnl']:7.2f} total {rt['pnl']+rv['pnl']:7.2f} trades {rt['trades']+rv['trades']}")

print("\n== full-sample best MR, cost sensitivity ==")
pos = zscore_mr(close, 20, 3.0, 0.5)
for fees in [(5, 1, 10), (10, 2, 20), (2.5, 0.5, 5)]:
    r = backtest(close, vol, pos[: len(close) - 1], fees=fees)
    print(f"fees(taker,maker,slip bps)={fees}: pnl {r['pnl']:7.2f} trades {r['trades']} dd {r['max_dd']:7.2f}")
