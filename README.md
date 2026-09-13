# Probability-Driven Market Making Simulation

An end-to-end quantitative trading simulation designed to study how a simple market maker balances spread capture, inventory risk and adverse selection under stochastic prices and order flow.

## Research question

Can inventory-aware quoting reduce inventory risk without giving up the economics of spread capture in a stylized electronic market?

## What the simulator does

- Simulates a mid-price random walk with configurable volatility.
- Models market-order arrivals with distance-sensitive fill probabilities.
- Posts bid/ask quotes and tracks fills, cash, inventory and mark-to-market P&L.
- Enforces position limits so the strategy cannot accumulate unlimited inventory.
- Compares a fixed-spread baseline with an inventory-aware strategy that shifts quotes and widens them when realized volatility rises.
- Runs Monte Carlo paths and reports P&L distribution, loss rate, turnover, trade count, inventory RMS, maximum inventory, spread capture and adverse-selection statistics.

## Reference result

Using 160 Monte Carlo paths of 1,000 steps each, the inventory-aware strategy produced similar mean simulated P&L to the fixed-spread baseline while reducing mean inventory RMS by **87.3%** and mean maximum absolute inventory by **78.5%**. Its simulated P&L standard deviation was **2.31** versus **18.64** for the baseline. These figures are model-dependent simulation outputs, not live-trading returns.

## Performance engineering benchmark

The repository includes a reproducible scalar-versus-vectorized benchmark for inventory-aware quote generation. On the recorded one-million-quote workload (seed 42, median of seven runs), NumPy vectorization produced identical bid/ask arrays while reducing median runtime from **2.803 seconds to 0.00819 seconds**, a **342x speedup** and approximately **122.1 million quotes per second** on the benchmark environment. Runtime varies by hardware, so the script and raw JSON output are committed for verification.

## Reproduce

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/run_experiment.py --paths 160 --steps 1000 --seed 7
python src/performance_benchmark.py
pytest -q
```

The simulation creates `outputs/path_results.csv` and `outputs/metrics.json`; the performance run writes `outputs/performance_benchmark.json`.

## Start-to-finish workflow

1. Define the stochastic price and order-arrival assumptions.
2. Generate bid/ask quotes from the current mid-price, recent volatility and inventory.
3. Simulate fills on each side using distance-sensitive probabilities.
4. Update cash, inventory, turnover and mark-to-market P&L after every event.
5. Apply hard inventory limits and an inventory-skew rule to control position risk.
6. Repeat the experiment across hundreds of independent paths.
7. Compare the baseline and inventory-aware strategies using both return and risk metrics.
8. Profile a quote-generation workload and validate vectorized output against the scalar reference.
9. Document assumptions and limitations so simulated outcomes are not presented as live-trading performance.

## Repository map

- `src/simulate.py` - quote logic and single-path simulator
- `src/run_experiment.py` - Monte Carlo experiment and metrics
- `src/performance_benchmark.py` - reproducible scalar/vectorized quote benchmark
- `src/options_pricing.py` - Black-Scholes pricing, Greeks and inventory-aware option quotes
- `src/options_hedging.py` - discrete delta-hedging simulation
- `tests/` - reproducibility, pricing, Greeks and risk-limit tests
- `outputs/reference_metrics.json` - stored simulation results
- `outputs/performance_benchmark.json` - recorded benchmark environment result
- `RESEARCH_BRIEF.md` - concise interpretation for a recruiter/researcher

## Important limitation

This is a **research simulation**, not evidence of live trading profitability or exchange-level latency. It omits a real limit-order book, queue priority, network latency, fees/rebates, market impact, correlated order flow, jumps and regime shifts. The benchmark measures batched numerical quote calculations on one environment, not end-to-end trading-system latency.
