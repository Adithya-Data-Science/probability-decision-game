import numpy as np

from src.options_benchmark import (
    generate_inputs,
    max_abs_error,
    scalar_price_and_greeks,
    vectorized_price_and_greeks,
)


def test_vectorized_option_calculations_match_scalar_reference():
    data = generate_inputs(2_000, seed=123)
    scalar = scalar_price_and_greeks(data)
    vectorized = vectorized_price_and_greeks(data)
    assert max_abs_error(scalar, vectorized) < 1e-10


def test_benchmark_inputs_are_valid_and_reproducible():
    first = generate_inputs(100, seed=7)
    second = generate_inputs(100, seed=7)
    for key in first:
        assert np.array_equal(first[key], second[key])
    assert np.all(first["spot"] > 0)
    assert np.all(first["strike"] > 0)
    assert np.all(first["vol"] > 0)
    assert np.all(first["tau"] > 0)
