# eth-backtest entry

Frozen dataset: `bars.csv` — 1440 one-minute ETH/USDT bars (Binance, 24h ending
2026-11-13 12:17 UTC), down −3.36% on the day.

## Strategy

Mean reversion on 1-minute closes (`strategy.py`, stdlib only):

```
z = (close_t - SMA_20) / stdev_20
z > +3.5 -> short 1 ETH      # price stretched well above its recent mean
z < -3.5 -> long  1 ETH
|z| < 0.5 -> flat            # reverted back, take the profit
otherwise  -> hold
```

Only deep deviations (3.5 sigma on a 20-minute window) are faded, so the
strategy trades rarely (46 times a day) and every trade carries a large expected
reversion relative to fees. The position for bar t is computed from data up to
and including bar t and held through t -> t+1: no look-ahead, no phantom fills.

## Reproduce

```
python strategy.py bars.csv      # prints the position for every bar
python replay.py                 # replays positions with the cost model below
python robust.py                # parameter-neighbourhood sensitivity table
```

Cost model in `replay.py`: maker 1 bp / taker 5 bps per side (blended 50/50),
slippage 10 bps * (size / bar volume) per side.

## Results (net, after costs, 50% maker blend)

| window | PnL (USDT) | trades | max DD |
|---|---|---|---|
| train (first 70%) | +64.28 | 30 | −17.86 |
| held-out tail (last 30%) | +19.34 | 16 | −12.74 |
| full day | +83.62 | 46 | −17.86 |
| buy & hold | −68.09 | 1 | — |

Profitable on the train window *and* the held-out tail, and stays positive with
fees doubled (`robust.py`). Parameters were picked on the train split only; the
entry threshold 3.5σ is profitable across every lookback tested (15/20/25/30).
