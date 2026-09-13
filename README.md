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

## Options pricing, Greeks and performance benchmark

The repository includes European Black-Scholes pricing for calls and puts, Delta/Gamma/Vega calculations, inventory-aware option quoting and a reproducible scalar-versus-vectorized benchmark.

On the committed reference workload of **1,000,000 option calculations** (price + Delta + Gamma + Vega, seed 42, median of seven measured runs after warm-up), the scalar Python implementation took **0.933 s** versus **0.0863 s** for the vectorized NumPy/SciPy implementation, a **10.8x speedup**. The two implementations agreed to a maximum absolute difference of approximately **5.68e-14**. Runtime is hardware-dependent, so the benchmark script, environment metadata and raw JSON timings are committed for verification.

The repository also retains a separate quote-generation vectorization benchmark used for the market-making simulator; it should not be confused with the Black-Scholes benchmark above.

## Reproduce

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/run_experiment.py --paths 160 --steps 1000 --seed 7
python src/performance_benchmark.py
python src/options_benchmark.py --operations 1000000 --repeats 7 --seed 42
pytest -q
```

The simulation creates `outputs/path_results.csv` and `outputs/metrics.json`; quote-generation benchmarking writes `outputs/performance_benchmark.json`; Black-Scholes benchmarking writes `outputs/options_pricing_benchmark.json`.

## Start-to-finish workflow

1. Define the stochastic price and order-arrival assumptions.
2. Generate bid/ask quotes from the current mid-price, recent volatility and inventory.
3. Simulate fills on each side using distance-sensitive probabilities.
4. Update cash, inventory, turnover and mark-to-market P&L after every event.
5. Apply hard inventory limits and an inventory-skew rule to control position risk.
6. Repeat the experiment across hundreds of independent paths.
7. Compare the baseline and inventory-aware strategies using both return and risk metrics.
8. Implement Black-Scholes call/put pricing plus Delta, Gamma and Vega.
9. Generate a deterministic million-option workload and calculate price + Greeks with both scalar and vectorized implementations.
10. Verify numerical agreement to `1e-10`, benchmark seven full runs, and store median runtimes plus environment metadata.
11. Profile a separate quote-generation workload and validate vectorized output against its scalar reference.
12. Document assumptions and limitations so simulated outcomes and hardware-dependent benchmark results are not presented as live-trading performance.

## Repository map

- `src/simulate.py` - quote logic and single-path simulator
- `src/run_experiment.py` - Monte Carlo experiment and metrics
- `src/performance_benchmark.py` - reproducible scalar/vectorized market-making quote benchmark
- `src/options_pricing.py` - Black-Scholes pricing, Greeks and inventory-aware option quotes
- `src/options_hedging.py` - discrete delta-hedging simulation
- `src/options_benchmark.py` - scalar vs vectorized Black-Scholes price + Greeks benchmark
- `tests/test_options_benchmark.py` - numerical-equivalence and reproducibility tests for the options benchmark
- `tests/` - reproducibility, pricing, Greeks, benchmark and risk-limit tests
- `outputs/reference_metrics.json` - stored simulation results
- `outputs/performance_benchmark.json` - recorded quote-generation benchmark
- `outputs/options_pricing_benchmark.json` - recorded Black-Scholes + Greeks benchmark with environment metadata
- `RESEARCH_BRIEF.md` - concise interpretation for a recruiter/researcher

## Important limitation

This is a **research simulation**, not evidence of live trading profitability or exchange-level latency. It omits a real limit-order book, queue priority, network latency, fees/rebates, market impact, correlated order flow, jumps and regime shifts. Both performance benchmarks measure batched numerical calculations on one environment; neither is an end-to-end trading-system latency measurement.
