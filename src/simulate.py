from __future__ import annotations
import argparse
import numpy as np

def optimal_policy(roll, rolls_remaining):
    if rolls_remaining == 0:
        return True
    threshold = 4 if rolls_remaining == 1 else 5
    return roll >= threshold

def simulate(trials=1_000_000, seed=42, policy=optimal_policy):
    rng = np.random.default_rng(seed)
    payoff = np.empty(trials, dtype=np.int8)
    for i in range(trials):
        for roll_index in range(3):
            roll = rng.integers(1, 7)
            remaining = 2 - roll_index
            if remaining == 0 or policy(roll, remaining):
                payoff[i] = roll
                break
    mean = payoff.mean()
    se = payoff.std(ddof=1) / np.sqrt(trials)
    return mean, (mean - 1.96 * se, mean + 1.96 * se)

def fixed_threshold(k):
    return lambda roll, remaining: roll >= k

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--trials", type=int, default=1_000_000)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    policies = {"optimal_adaptive": optimal_policy,
                **{f"fixed_{k}": fixed_threshold(k) for k in range(2, 7)}}
    for name, policy in policies.items():
        mean, ci = simulate(args.trials, args.seed, policy)
        print(f"{name:16s} mean={mean:.6f} 95% CI=({ci[0]:.6f}, {ci[1]:.6f})")
    print("exact optimal expected payoff = 4.666667")

if __name__ == "__main__":
    main()
