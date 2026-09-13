from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

import numpy as np


def scalar_quotes(mid, inventory, realized_vol, half_spread=0.04, inventory_skew=0.018,
                  volatility_spread=0.10, tick_size=0.01):
    out_bid = np.empty(len(mid))
    out_ask = np.empty(len(mid))
    for i in range(len(mid)):
        half = max(half_spread + volatility_spread * realized_vol[i], tick_size)
        center = mid[i] - inventory_skew * inventory[i]
        out_bid[i] = np.floor((center - half) / tick_size) * tick_size
        out_ask[i] = np.ceil((center + half) / tick_size) * tick_size
    return out_bid, out_ask


def vectorized_quotes(mid, inventory, realized_vol, half_spread=0.04, inventory_skew=0.018,
                      volatility_spread=0.10, tick_size=0.01):
    half = np.maximum(half_spread + volatility_spread * realized_vol, tick_size)
    center = mid - inventory_skew * inventory
    bid = np.floor((center - half) / tick_size) * tick_size
    ask = np.ceil((center + half) / tick_size) * tick_size
    return bid, ask


def timed(fn, *args, repeats=7):
    samples = []
    for _ in range(repeats):
        start = perf_counter()
        result = fn(*args)
        samples.append(perf_counter() - start)
    return float(np.median(samples)), result


def main():
    n = 1_000_000
    rng = np.random.default_rng(42)
    mid = 100 + rng.normal(0, 1, n)
    inventory = rng.integers(-12, 13, n)
    realized_vol = np.abs(rng.normal(0.06, 0.01, n))
    scalar_time, scalar = timed(scalar_quotes, mid, inventory, realized_vol)
    vector_time, vector = timed(vectorized_quotes, mid, inventory, realized_vol)
    assert np.array_equal(scalar[0], vector[0])
    assert np.array_equal(scalar[1], vector[1])
    result = {
        "operations": n,
        "repeats": 7,
        "scalar_median_seconds": scalar_time,
        "vectorized_median_seconds": vector_time,
        "speedup_x": scalar_time / vector_time,
        "vectorized_throughput_per_second": n / vector_time,
        "seed": 42,
    }
    Path("outputs").mkdir(exist_ok=True)
    Path("outputs/performance_benchmark.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
