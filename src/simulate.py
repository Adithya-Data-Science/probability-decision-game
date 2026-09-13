from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict
import numpy as np


@dataclass(frozen=True)
class MarketConfig:
    steps: int = 1500
    dt: float = 1.0
    start_price: float = 100.0
    sigma: float = 0.06
    base_arrival_rate: float = 0.45
    arrival_decay: float = 0.22
    tick_size: float = 0.01


@dataclass(frozen=True)
class StrategyConfig:
    name: str
    half_spread: float = 0.06
    inventory_skew: float = 0.012
    volatility_spread: float = 0.30
    max_inventory: int = 18
    order_size: int = 1


@dataclass
class PathResult:
    strategy: str
    pnl: float
    cash: float
    inventory: int
    max_abs_inventory: int
    trades: int
    turnover: float
    inventory_rms: float
    spread_capture: float
    adverse_selection: float

    def as_dict(self) -> Dict[str, float | int | str]:
        return asdict(self)


def _arrival_probability(base_rate: float, decay: float, distance: float, tick: float, dt: float) -> float:
    ticks = max(distance / max(tick, 1e-12), 0.0)
    intensity = base_rate * np.exp(-decay * ticks)
    return float(np.clip(1.0 - np.exp(-intensity * dt), 0.0, 1.0))


def quote(mid: float, inventory: int, realized_vol: float, cfg: StrategyConfig, tick_size: float) -> tuple[float, float]:
    spread_buffer = cfg.volatility_spread * realized_vol
    center = mid - cfg.inventory_skew * inventory
    half = max(cfg.half_spread + spread_buffer, tick_size)
    bid = np.floor((center - half) / tick_size) * tick_size
    ask = np.ceil((center + half) / tick_size) * tick_size
    if ask <= bid:
        ask = bid + tick_size
    return float(bid), float(ask)


def simulate_path(seed: int, market: MarketConfig, strategy: StrategyConfig) -> PathResult:
    rng = np.random.default_rng(seed)
    mid = market.start_price
    cash = 0.0
    inv = 0
    trades = 0
    turnover = 0.0
    max_abs_inv = 0
    inv_sq_sum = 0.0
    spread_capture = 0.0
    adverse_selection = 0.0
    recent_moves: list[float] = []

    for _ in range(market.steps):
        realized_vol = float(np.std(recent_moves[-50:])) if len(recent_moves) >= 5 else market.sigma
        bid, ask = quote(mid, inv, realized_vol, strategy, market.tick_size)

        bid_allowed = inv < strategy.max_inventory
        ask_allowed = inv > -strategy.max_inventory
        p_buy = _arrival_probability(market.base_arrival_rate, market.arrival_decay, mid - bid, market.tick_size, market.dt)
        p_sell = _arrival_probability(market.base_arrival_rate, market.arrival_decay, ask - mid, market.tick_size, market.dt)

        buy_fill = bid_allowed and rng.random() < p_buy
        sell_fill = ask_allowed and rng.random() < p_sell

        pre_mid = mid
        if buy_fill:
            qty = strategy.order_size
            cash -= bid * qty
            inv += qty
            trades += qty
            turnover += bid * qty
            spread_capture += (pre_mid - bid) * qty
        if sell_fill:
            qty = strategy.order_size
            cash += ask * qty
            inv -= qty
            trades += qty
            turnover += ask * qty
            spread_capture += (ask - pre_mid) * qty

        move = market.sigma * np.sqrt(market.dt) * rng.normal()
        mid = max(market.tick_size, mid + move)
        recent_moves.append(move)

        if buy_fill:
            adverse_selection += (mid - pre_mid) * strategy.order_size
        if sell_fill:
            adverse_selection += (pre_mid - mid) * strategy.order_size

        max_abs_inv = max(max_abs_inv, abs(inv))
        inv_sq_sum += inv * inv

    pnl = cash + inv * mid
    return PathResult(
        strategy=strategy.name,
        pnl=float(pnl),
        cash=float(cash),
        inventory=int(inv),
        max_abs_inventory=int(max_abs_inv),
        trades=int(trades),
        turnover=float(turnover),
        inventory_rms=float(np.sqrt(inv_sq_sum / market.steps)),
        spread_capture=float(spread_capture),
        adverse_selection=float(adverse_selection),
    )
