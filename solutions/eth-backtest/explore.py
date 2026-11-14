"""Explore the frozen ETH 1-minute dataset."""
import csv
import numpy as np

rows = list(csv.DictReader(open(r"C:\Softs\aiprove\solutions\eth-backtest\bars.csv")))
close = np.array([float(r["close"]) for r in rows])
high = np.array([float(r["high"]) for r in rows])
low = np.array([float(r["low"]) for r in rows])
vol = np.array([float(r["volume"]) for r in rows])
rets = np.diff(close) / close[:-1]

print("bars:", len(close))
print("close first/last:", close[0], close[-1], "total return %:", (close[-1] / close[0] - 1) * 100)
print("mean 1m ret (bps):", rets.mean() * 1e4, "std (bps):", rets.std() * 1e4)
print("min/max close:", close.min(), close.max())
print("bar range avg (bps):", ((high - low) / close).mean() * 1e4)
print("volume mean/median:", vol.mean(), np.median(vol))
# autocorrelation of returns
for lag in [1, 2, 3, 5, 10]:
    print(f"autocorr lag {lag}:", np.corrcoef(rets[:-lag], rets[lag:])[0, 1].round(4))
# per-hour drift
for h in range(0, 24, 2):
    seg = rets[(h * 60):min((h + 2) * 60, len(rets))]
    if len(seg):
        print(f"hour {h:02d}-{h+2:02d}: drift {seg.mean()*1e4*len(seg):.1f} bps")
