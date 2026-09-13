from __future__ import annotations
from dataclasses import dataclass
from math import exp, sqrt
import numpy as np
from .options_pricing import EuropeanOption

@dataclass(frozen=True)
class HedgeConfig:
    spot0: float = 100.0
    strike: float = 100.0
    maturity: float = 30 / 252
    rate: float = 0.02
    vol: float = 0.25
    steps: int = 30
    paths: int = 1000
    seed: int = 17

class DeltaHedgingSimulator:
    def __init__(self, config: HedgeConfig):
        self.config = config
        self.option = EuropeanOption(config.strike, config.maturity, 'call')

    def _path(self, rng: np.random.Generator) -> np.ndarray:
        c = self.config
        dt = c.maturity / c.steps
        z = rng.standard_normal(c.steps)
        log_returns = (c.rate - 0.5 * c.vol**2) * dt + c.vol * sqrt(dt) * z
        path = np.empty(c.steps + 1)
        path[0] = c.spot0
        path[1:] = c.spot0 * np.exp(np.cumsum(log_returns))
        return path

    def hedge_path(self, rng: np.random.Generator) -> dict[str, float]:
        c = self.config
        dt = c.maturity / c.steps
        path = self._path(rng)
        premium = self.option.price(c.spot0, c.rate, c.vol)
        shares = self.option.greeks(c.spot0, c.rate, c.vol)['delta']
        cash = premium - shares * c.spot0
        turnover = abs(shares)
        for step in range(1, c.steps + 1):
            cash *= exp(c.rate * dt)
            tau = max(c.maturity - step * dt, 0.0)
            spot = float(path[step])
            new_delta = self.option.greeks(spot, c.rate, c.vol, tau)['delta'] if tau > 0 else 0.0
            trade = new_delta - shares
            cash -= trade * spot
            turnover += abs(trade)
            shares = new_delta
        terminal = float(path[-1])
        payoff = max(terminal - c.strike, 0.0)
        return {'pnl': cash + shares * terminal - payoff, 'turnover_shares': turnover}

    def run(self) -> dict[str, float]:
        rng = np.random.default_rng(self.config.seed)
        result = [self.hedge_path(rng) for _ in range(self.config.paths)]
        pnl = np.array([x['pnl'] for x in result])
        turnover = np.array([x['turnover_shares'] for x in result])
        return {
            'paths': self.config.paths,
            'steps': self.config.steps,
            'mean_hedge_pnl': float(pnl.mean()),
            'hedge_pnl_std': float(pnl.std(ddof=1)),
            'mean_abs_hedge_error': float(np.mean(np.abs(pnl))),
            'p95_abs_hedge_error': float(np.quantile(np.abs(pnl), 0.95)),
            'mean_turnover_shares': float(turnover.mean()),
        }
