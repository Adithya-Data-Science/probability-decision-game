from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

from simulate import MarketConfig, StrategyConfig, simulate_path


def summarize(df: pd.DataFrame) -> dict:
    out = {}
    for strategy, g in df.groupby("strategy"):
        pnl = g["pnl"].to_numpy(float)
        out[strategy] = {
            "paths": int(len(g)),
            "mean_pnl": float(np.mean(pnl)),
            "median_pnl": float(np.median(pnl)),
            "pnl_std": float(np.std(pnl, ddof=1)),
            "loss_rate": float(np.mean(pnl < 0)),
            "p05_pnl": float(np.quantile(pnl, 0.05)),
            "p95_pnl": float(np.quantile(pnl, 0.95)),
            "mean_max_abs_inventory": float(g["max_abs_inventory"].mean()),
            "mean_inventory_rms": float(g["inventory_rms"].mean()),
            "mean_trades": float(g["trades"].mean()),
            "mean_turnover": float(g["turnover"].mean()),
            "mean_spread_capture": float(g["spread_capture"].mean()),
            "mean_adverse_selection": float(g["adverse_selection"].mean()),
        }
    if "inventory_aware" in out and "fixed_spread" in out:
        out["comparison"] = {
            "mean_pnl_delta": out["inventory_aware"]["mean_pnl"] - out["fixed_spread"]["mean_pnl"],
            "inventory_rms_reduction_pct": 100.0 * (
                1.0 - out["inventory_aware"]["mean_inventory_rms"] / out["fixed_spread"]["mean_inventory_rms"]
            ),
            "max_inventory_reduction_pct": 100.0 * (
                1.0 - out["inventory_aware"]["mean_max_abs_inventory"] / out["fixed_spread"]["mean_max_abs_inventory"]
            ),
        }
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--paths", type=int, default=160)
    p.add_argument("--steps", type=int, default=1000)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--out", type=Path, default=Path("outputs"))
    args = p.parse_args()

    market = MarketConfig(steps=args.steps)
    strategies = [
        StrategyConfig(name="fixed_spread", half_spread=0.04, inventory_skew=0.0, volatility_spread=0.0, max_inventory=18),
        StrategyConfig(name="inventory_aware", half_spread=0.04, inventory_skew=0.018, volatility_spread=0.10, max_inventory=12),
    ]

    rows = []
    for s_idx, strategy in enumerate(strategies):
        for i in range(args.paths):
            rows.append(simulate_path(args.seed + 100_000 * s_idx + i, market, strategy).as_dict())

    df = pd.DataFrame(rows)
    metrics = summarize(df)
    args.out.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out / "path_results.csv", index=False)
    (args.out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
