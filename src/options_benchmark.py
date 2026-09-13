from __future__ import annotations

import argparse
import json
import math
import platform
import statistics
import time
from pathlib import Path

import numpy as np
from scipy import __version__ as scipy_version
from scipy.special import ndtr

SQRT_2 = math.sqrt(2.0)
SQRT_2PI = math.sqrt(2.0 * math.pi)


def generate_inputs(operations: int, seed: int = 42) -> dict[str, np.ndarray]:
    """Generate deterministic, valid European-option inputs for the benchmark."""
    if operations <= 0:
        raise ValueError("operations must be positive")
    rng = np.random.default_rng(seed)
    return {
        "spot": rng.uniform(70.0, 130.0, operations),
        "strike": rng.uniform(70.0, 130.0, operations),
        "rate": rng.uniform(0.0, 0.08, operations),
        "vol": rng.uniform(0.08, 0.60, operations),
        "tau": rng.uniform(1.0 / 252.0, 2.0, operations),
        "is_call": rng.integers(0, 2, operations, dtype=np.int8),
    }


def scalar_price_and_greeks(data: dict[str, np.ndarray]) -> tuple[np.ndarray, ...]:
    """Reference Python loop: Black-Scholes price, delta, gamma and vega."""
    spot = data["spot"]
    strike = data["strike"]
    rate = data["rate"]
    vol = data["vol"]
    tau = data["tau"]
    is_call = data["is_call"]
    n = len(spot)

    prices = np.empty(n)
    deltas = np.empty(n)
    gammas = np.empty(n)
    vegas = np.empty(n)

    for i in range(n):
        s = float(spot[i])
        k = float(strike[i])
        r = float(rate[i])
        sigma = float(vol[i])
        t = float(tau[i])

        sqrt_t = math.sqrt(t)
        d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / (sigma * sqrt_t)
        d2 = d1 - sigma * sqrt_t
        cdf_d1 = 0.5 * (1.0 + math.erf(d1 / SQRT_2))
        pdf_d1 = math.exp(-0.5 * d1 * d1) / SQRT_2PI
        discount = math.exp(-r * t)

        if is_call[i]:
            prices[i] = s * cdf_d1 - k * discount * (0.5 * (1.0 + math.erf(d2 / SQRT_2)))
            deltas[i] = cdf_d1
        else:
            prices[i] = k * discount * (0.5 * (1.0 + math.erf(-d2 / SQRT_2))) - s * (
                0.5 * (1.0 + math.erf(-d1 / SQRT_2))
            )
            deltas[i] = cdf_d1 - 1.0

        gammas[i] = pdf_d1 / (s * sigma * sqrt_t)
        vegas[i] = s * pdf_d1 * sqrt_t

    return prices, deltas, gammas, vegas


def vectorized_price_and_greeks(data: dict[str, np.ndarray]) -> tuple[np.ndarray, ...]:
    """Vectorized NumPy/SciPy implementation of the same Black-Scholes calculations."""
    spot = data["spot"]
    strike = data["strike"]
    rate = data["rate"]
    vol = data["vol"]
    tau = data["tau"]
    is_call = data["is_call"].astype(bool)

    sqrt_t = np.sqrt(tau)
    d1 = (np.log(spot / strike) + (rate + 0.5 * vol * vol) * tau) / (vol * sqrt_t)
    d2 = d1 - vol * sqrt_t
    discount = np.exp(-rate * tau)

    cdf_d1 = ndtr(d1)
    call_price = spot * cdf_d1 - strike * discount * ndtr(d2)
    put_price = strike * discount * ndtr(-d2) - spot * ndtr(-d1)
    prices = np.where(is_call, call_price, put_price)
    deltas = np.where(is_call, cdf_d1, cdf_d1 - 1.0)

    pdf_d1 = np.exp(-0.5 * d1 * d1) / np.sqrt(2.0 * np.pi)
    gammas = pdf_d1 / (spot * vol * sqrt_t)
    vegas = spot * pdf_d1 * sqrt_t
    return prices, deltas, gammas, vegas


def max_abs_error(reference: tuple[np.ndarray, ...], candidate: tuple[np.ndarray, ...]) -> float:
    return max(float(np.max(np.abs(a - b))) for a, b in zip(reference, candidate))


def timed(fn, data: dict[str, np.ndarray], repeats: int) -> tuple[list[float], tuple[np.ndarray, ...]]:
    samples: list[float] = []
    result: tuple[np.ndarray, ...] | None = None
    for _ in range(repeats):
        start = time.perf_counter()
        result = fn(data)
        samples.append(time.perf_counter() - start)
    assert result is not None
    return samples, result


def run_benchmark(operations: int = 1_000_000, repeats: int = 7, seed: int = 42) -> dict[str, object]:
    if repeats <= 0:
        raise ValueError("repeats must be positive")
    data = generate_inputs(operations, seed)

    # Warm up both code paths on a small deterministic slice so one-time import/cache
    # effects are not counted in the recorded full-workload timings.
    warmup = {key: value[: min(2_000, operations)] for key, value in data.items()}
    scalar_price_and_greeks(warmup)
    vectorized_price_and_greeks(warmup)

    scalar_times, scalar_result = timed(scalar_price_and_greeks, data, repeats)
    vector_times, vector_result = timed(vectorized_price_and_greeks, data, repeats)

    error = max_abs_error(scalar_result, vector_result)
    if error > 1e-10:
        raise AssertionError(f"vectorized results differ from scalar reference: max_abs_error={error}")

    scalar_median = float(statistics.median(scalar_times))
    vector_median = float(statistics.median(vector_times))
    return {
        "workload": "European Black-Scholes price + delta + gamma + vega",
        "operations": operations,
        "repeats": repeats,
        "seed": seed,
        "scalar_times_seconds": scalar_times,
        "vectorized_times_seconds": vector_times,
        "scalar_median_seconds": scalar_median,
        "vectorized_median_seconds": vector_median,
        "speedup_x": scalar_median / vector_median,
        "max_abs_error": error,
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy_version,
            "platform": platform.platform(),
        },
        "note": "Runtime is hardware-dependent; numerical equality is validated to 1e-10.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark scalar vs vectorized Black-Scholes price and Greeks.")
    parser.add_argument("--operations", type=int, default=1_000_000)
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="outputs/options_pricing_benchmark.json")
    args = parser.parse_args()

    result = run_benchmark(args.operations, args.repeats, args.seed)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
