from __future__ import annotations
from dataclasses import dataclass
from math import erf, exp, log, pi, sqrt
from typing import Literal

OptionType = Literal['call', 'put']

def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))

def norm_pdf(x: float) -> float:
    return exp(-0.5 * x * x) / sqrt(2.0 * pi)

@dataclass(frozen=True)
class EuropeanOption:
    strike: float
    maturity: float
    option_type: OptionType = 'call'

    def _d1_d2(self, spot: float, rate: float, vol: float, tau: float | None = None) -> tuple[float, float]:
        t = self.maturity if tau is None else tau
        if spot <= 0 or self.strike <= 0 or vol <= 0 or t <= 0:
            raise ValueError('spot, strike, volatility and time must be positive')
        d1 = (log(spot / self.strike) + (rate + 0.5 * vol * vol) * t) / (vol * sqrt(t))
        return d1, d1 - vol * sqrt(t)

    def price(self, spot: float, rate: float, vol: float, tau: float | None = None) -> float:
        t = self.maturity if tau is None else tau
        if t <= 0:
            return max(spot - self.strike, 0.0) if self.option_type == 'call' else max(self.strike - spot, 0.0)
        d1, d2 = self._d1_d2(spot, rate, vol, t)
        discount = exp(-rate * t)
        if self.option_type == 'call':
            return spot * norm_cdf(d1) - self.strike * discount * norm_cdf(d2)
        return self.strike * discount * norm_cdf(-d2) - spot * norm_cdf(-d1)

    def greeks(self, spot: float, rate: float, vol: float, tau: float | None = None) -> dict[str, float]:
        t = self.maturity if tau is None else tau
        d1, _ = self._d1_d2(spot, rate, vol, t)
        call_delta = norm_cdf(d1)
        delta = call_delta if self.option_type == 'call' else call_delta - 1.0
        gamma = norm_pdf(d1) / (spot * vol * sqrt(t))
        vega = spot * norm_pdf(d1) * sqrt(t)
        return {'delta': delta, 'gamma': gamma, 'vega': vega}

@dataclass(frozen=True)
class QuotePolicy:
    base_half_spread: float = 0.05
    inventory_penalty: float = 0.015
    gamma_penalty: float = 0.20
    vol_penalty: float = 0.08

    def quotes(self, fair_value: float, inventory: float, gamma: float, vol: float) -> tuple[float, float]:
        half_spread = self.base_half_spread + self.gamma_penalty * abs(gamma) + self.vol_penalty * vol
        quote_mid = fair_value - self.inventory_penalty * inventory
        return quote_mid - half_spread, quote_mid + half_spread
