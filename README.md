# Optimal Decision Strategy for a Sequential Probability Game

This project uses conditional expectation and Monte Carlo simulation to solve a three-roll keep-or-reroll decision problem.

## Game

A player rolls a fair six-sided die and may use at most three rolls. After roll one or two, the player may keep the current value or reroll. A reroll discards the previous value. The final kept value is the payoff.

## Optimal policy

With one roll remaining, rerolling has expected value 3.5, so keep 4, 5, or 6.

With two rolls remaining, the continuation value is:

```text
(3.5 + 3.5 + 3.5 + 4 + 5 + 6) / 6 = 4.25
```

Therefore, on the first roll keep 5 or 6; on the second roll keep 4, 5, or 6. The exact optimal expected payoff is 4.6667.

## Run

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/simulate.py --trials 1000000 --seed 42
pytest
```

The script compares the optimal adaptive policy against fixed-threshold policies and prints confidence intervals. No external dataset is required because the simulated random rolls are the data.

## Why this matters

The project demonstrates backward induction, conditional expectation, decisions under uncertainty, reproducible simulation, and comparison of adaptive and fixed strategies.