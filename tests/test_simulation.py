import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from simulate import MarketConfig, StrategyConfig, quote, simulate_path


def test_quotes_are_ordered():
    cfg = StrategyConfig(name="test")
    bid, ask = quote(100.0, 0, 0.05, cfg, 0.01)
    assert bid < ask


def test_seed_is_reproducible():
    market = MarketConfig(steps=100)
    cfg = StrategyConfig(name="test", max_inventory=6)
    first = simulate_path(11, market, cfg)
    second = simulate_path(11, market, cfg)
    assert first.pnl == second.pnl
    assert first.trades == second.trades


def test_position_limit_is_respected():
    market = MarketConfig(steps=500)
    cfg = StrategyConfig(name="test", max_inventory=5)
    result = simulate_path(17, market, cfg)
    assert result.max_abs_inventory <= 5
