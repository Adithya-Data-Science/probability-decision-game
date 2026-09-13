# Research Brief - Quantitative Trading Simulation

## Decision problem
A liquidity-providing strategy earns the spread when passive orders are filled, but those fills create inventory and expose the strategy to subsequent price moves. The experiment asks whether a simple inventory-aware quote adjustment can control that risk relative to a fixed-spread baseline.

## Design
The simulated market evolves in discrete time. The mid-price follows a zero-drift stochastic process, while the probability of a passive fill decreases as a quote moves farther from the mid. The inventory-aware strategy shifts its quote center against its current position, widens the spread as realized volatility rises, and operates with a tighter position limit.

## Reference findings
Across 160 simulated paths of 1,000 steps, mean simulated P&L was similar between the two strategies, while the inventory-aware rule reduced mean inventory RMS by 87.3% and mean maximum absolute inventory by 78.5%. Simulated P&L standard deviation fell from 18.64 to 2.31.

## Interpretation discipline
Results are conditional on model assumptions and random seeds. They are not evidence of live-trading profitability. A next research step would use event-level order-book data, model queue position and fees, calibrate volatility and order flow from historical observations, and then test on out-of-sample periods.
