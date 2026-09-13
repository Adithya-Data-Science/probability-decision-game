# Options Pricing, Greeks & Performance Benchmarking

A reproducible quantitative trading engineering project that implements European option valuation, first-order and second-order risk measures, inventory-aware option quoting, discrete delta hedging, and a measured scalar-versus-vectorized performance benchmark.

## Why this project exists

Options market making requires more than computing a theoretical price. A trading system must repeatedly estimate fair value and risk, update quotes as market conditions change, manage inventory exposure, and do those calculations quickly enough to support decision-making.

This project studies that workflow in a controlled research environment:

1. compute Black-Scholes prices for European calls and puts;
2. calculate Delta, Gamma, and Vega;
3. adjust bid/ask quotes for inventory and option risk;
4. simulate discrete delta hedging on stochastic price paths;
5. benchmark a scalar Python implementation against a vectorized NumPy/SciPy implementation;
6. verify that the faster implementation reproduces the scalar reference numerically;
7. store raw timings, environment metadata, tests, and limitations so the result can be independently checked.

## Core quantitative model

For spot price `S`, strike `K`, continuously compounded risk-free rate `r`, volatility `sigma`, and time to maturity `T`, the implementation uses the standard Black-Scholes quantities

```text
d1 = [ln(S/K) + (r + 0.5*sigma^2)T] / (sigma*sqrt(T))
d2 = d1 - sigma*sqrt(T)
```

The project supports European calls and puts and computes:

- **Option price** — model fair value under the Black-Scholes assumptions.
- **Delta** — sensitivity of option value to the underlying price.
- **Gamma** — sensitivity of Delta to the underlying price.
- **Vega** — sensitivity of option value to volatility.

The implementation is in [`src/options_pricing.py`](src/options_pricing.py).

## Inventory-aware option quoting

The `QuotePolicy` layer converts theoretical value into a simple two-sided quote. The quoted half-spread increases with volatility and absolute Gamma, while the quote midpoint shifts with inventory.

Conceptually:

```text
half_spread = base_spread + gamma_penalty*|gamma| + volatility_penalty*volatility
quote_mid   = fair_value - inventory_penalty*inventory
bid         = quote_mid - half_spread
ask         = quote_mid + half_spread
```

This is intentionally a stylized research rule rather than a production market-making model. Its purpose is to show how theoretical value, risk, and inventory can interact in quote construction.

## Discrete delta-hedging simulation

[`src/options_hedging.py`](src/options_hedging.py) simulates geometric-Brownian-motion price paths and repeatedly rebalances the underlying position toward the option Delta.

For each simulated path the engine:

1. prices an at-the-money European call;
2. initializes the hedge using the option's Delta;
3. accrues the cash balance at the risk-free rate;
4. recomputes Delta as spot and time-to-maturity change;
5. buys or sells the underlying to update the hedge;
6. settles the option payoff at expiration;
7. records hedge P&L and share turnover.

The simulator reports mean hedge P&L, hedge-P&L volatility, mean absolute hedge error, 95th-percentile absolute hedge error, and average share turnover across paths.

## Performance-engineering question

A trading workflow may need to value and risk-manage a large option set repeatedly. The benchmark therefore asks:

> How much faster is a vectorized implementation when computing Black-Scholes price, Delta, Gamma, and Vega for one million independent options, while preserving the numerical result of a transparent scalar reference implementation?

The benchmark code is in [`src/options_benchmark.py`](src/options_benchmark.py).

## Benchmark design

The benchmark generates **1,000,000 deterministic option cases** with seed `42` and samples valid values for:

- spot;
- strike;
- risk-free rate;
- volatility;
- time to maturity;
- call/put type.

Two implementations process the identical workload:

### Scalar reference

A Python loop computes Black-Scholes price plus Delta, Gamma, and Vega one option at a time. It uses standard-library `math` functions and serves as the readable reference implementation.

### Vectorized implementation

NumPy arrays and SciPy's vectorized normal-CDF implementation process the full option set in batches while applying the same formulas.

Both paths are warmed up first. Each full workload is then measured **seven times**, and the median runtime is reported to reduce sensitivity to one unusually fast or slow run.

## Recorded result

The committed reference output is stored in [`outputs/options_pricing_benchmark.json`](outputs/options_pricing_benchmark.json).

| Metric | Recorded result |
| --- | ---: |
| Workload | 1,000,000 options |
| Calculations per option | Price + Delta + Gamma + Vega |
| Repeated full runs | 7 |
| Scalar median runtime | **0.9330 s** |
| Vectorized median runtime | **0.08634 s** |
| Measured speedup | **10.81x** |
| Maximum absolute numerical difference | **5.68e-14** |
| Validation tolerance | `1e-10` |

The vectorized implementation therefore produced the same calculations to far tighter than the required tolerance while reducing the median runtime by approximately **10.8x** on the recorded environment.

### Recorded environment

```text
Python 3.13.5
NumPy 2.3.5
SciPy 1.17.0
Linux x86_64
```

Runtime is hardware- and software-dependent. The purpose of committing the raw timings and environment is to make the performance claim auditable rather than imply that every machine will reproduce the identical number.

## Validation and testing

The project includes automated tests covering both finance logic and engineering behavior.

[`tests/test_options.py`](tests/test_options.py) validates:

- call-put parity;
- positive Gamma and Vega for a standard call configuration;
- valid call Delta bounds;
- inventory-dependent quote skew;
- deterministic delta-hedging simulation under a fixed seed.

[`tests/test_options_benchmark.py`](tests/test_options_benchmark.py) validates:

- scalar/vectorized agreement for price, Delta, Gamma, and Vega;
- deterministic input generation;
- benchmark result structure;
- strict numerical equivalence within the chosen tolerance.

The benchmark itself also refuses to report a performance result if maximum numerical disagreement exceeds `1e-10`.

## Start-to-finish workflow

1. Define European option inputs and Black-Scholes assumptions.
2. Implement call and put pricing in a reusable `EuropeanOption` class.
3. Implement Delta, Gamma, and Vega from the same model inputs.
4. Add an inventory- and risk-aware quote policy.
5. Validate core pricing relationships with automated tests.
6. Build a stochastic price-path generator for hedging experiments.
7. Recalculate Delta through time and simulate discrete hedge rebalancing.
8. Measure hedge error and turnover across repeatable paths.
9. Build a transparent scalar price-and-Greeks reference implementation.
10. Build a vectorized NumPy/SciPy implementation of the same calculations.
11. Generate one million deterministic call/put cases.
12. Warm up both implementations and time seven complete runs of each.
13. Compare every output array and enforce a `1e-10` maximum-error threshold.
14. Store raw timings, median runtimes, speedup, numerical error, and environment metadata in JSON.
15. Document assumptions and distinguish numerical benchmarking from exchange-level latency or live trading profitability.

## Reproduce the project

From the repository root:

```bash
python -m venv .venv
```

Activate the environment.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the options benchmark:

```bash
python src/options_benchmark.py --operations 1000000 --repeats 7 --seed 42
```

Run the complete automated test suite:

```bash
pytest -q
```

The benchmark recreates:

```text
outputs/options_pricing_benchmark.json
```

## Repository map

```text
src/
  options_pricing.py       Black-Scholes price, Greeks, and quote policy
  options_hedging.py       discrete delta-hedging simulation
  options_benchmark.py     scalar vs vectorized million-option benchmark

tests/
  test_options.py          pricing, Greeks, quoting, and hedging tests
  test_options_benchmark.py benchmark equivalence and reproducibility tests

outputs/
  options_pricing_benchmark.json  raw timing and validation evidence

requirements.txt           Python dependencies
README.md                  complete market-making project overview
```

## What the result demonstrates

This project demonstrates the ability to connect quantitative finance concepts with software implementation and empirical validation:

- probability and quantitative modeling;
- derivatives pricing and Greeks;
- inventory-aware decision rules;
- simulation and risk measurement;
- Python software design;
- NumPy/SciPy vectorization;
- performance measurement;
- numerical validation;
- automated testing;
- reproducible research documentation.

It also separates **model correctness** from **implementation speed**: the optimized path is only considered acceptable after its outputs are checked against the scalar reference.

## Limitations

This is a research and engineering project, not a production options market-making system.

The Black-Scholes model assumes continuous trading, constant volatility and rates, lognormal underlying dynamics, and frictionless markets. The hedging experiment uses simulated geometric-Brownian-motion paths and discrete rebalancing. The quote policy is stylized and does not model a real limit-order book, queue position, fees/rebates, market impact, volatility surfaces, jumps, stochastic volatility, transaction costs, exchange latency, or adverse selection in real options flow.

The **10.8x** figure is a batched numerical-computation benchmark on the recorded environment. It is not a claim of end-to-end trading-system latency or live-trading performance.
