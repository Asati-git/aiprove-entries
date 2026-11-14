"""Strategy for the AIProve eth-backtest challenge.

Self-contained (stdlib only). Reads bars.csv (minute,open,high,low,close,volume)
and prints the target ETH position for every bar, one per line.

Signal: mean reversion on 1-minute closes.
  z = (close_t - SMA_20(close)) / stdev_20(close)
  z > +3.5  -> short SIZE ETH   (price stretched above its recent mean)
  z < -3.5  -> long  SIZE ETH
  |z| < 0.5 -> flat
  otherwise -> keep the previous position

Only deep, statistically unusual deviations are faded, so the strategy trades
rarely (~70 times a day) and each trade carries a large expected reversion
relative to realistic maker/taker fees and size-scaled slippage. The position
during bar t is decided strictly from data up to and including bar t, and is
held through bar t -> t+1 (no look-ahead, no phantom fills).
"""

import csv
import sys

# Position size in ETH. Median 1-minute volume on this day is ~149 ETH, so a
# 25 ETH clip keeps size-scaled slippage small while the edge per trade scales
# linearly; past ~100 ETH slippage overtakes the edge (see robust.py sizing).
SIZE = 25.0


def run(bars_path: str):
    closes = []
    vols = []
    with open(bars_path, newline="") as f:
        for row in csv.DictReader(f):
            closes.append(float(row["close"]))
            vols.append(float(row["volume"]))

    lookback, entry, exit_z = 20, 3.5, 0.5
    positions = []
    cur = 0.0
    for t, c in enumerate(closes):
        if t < lookback:
            positions.append(0.0)
            continue
        w = closes[t - lookback : t]
        mean = sum(w) / lookback
        var = sum((x - mean) ** 2 for x in w) / lookback
        if var <= 1e-12:
            positions.append(cur)
            continue
        z = (c - mean) / var ** 0.5
        if z > entry:
            cur = -SIZE
        elif z < -entry:
            cur = SIZE
        elif abs(z) < exit_z:
            cur = 0.0
        positions.append(cur)
    return positions, closes, vols


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "bars.csv"
    pos, _, _ = run(path)
    for p in pos:
        print(f"{p:g}")
