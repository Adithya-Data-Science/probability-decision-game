from src.simulate import optimal_policy, simulate

def test_thresholds():
    assert not optimal_policy(4, 2)
    assert optimal_policy(5, 2)
    assert not optimal_policy(3, 1)
    assert optimal_policy(4, 1)

def test_simulation_near_exact_value():
    mean, _ = simulate(trials=200_000, seed=7)
    assert abs(mean - 14 / 3) < 0.02
