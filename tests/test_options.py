import math
from src.options_pricing import EuropeanOption, QuotePolicy
from src.options_hedging import DeltaHedgingSimulator, HedgeConfig

def test_call_put_parity():
    s, k, r, v, t = 100.0, 105.0, 0.03, 0.22, 0.5
    call = EuropeanOption(k, t, 'call').price(s, r, v)
    put = EuropeanOption(k, t, 'put').price(s, r, v)
    assert abs((call - put) - (s - k * math.exp(-r * t))) < 1e-10

def test_greeks_positive_gamma_vega():
    g = EuropeanOption(100.0, 30/252, 'call').greeks(100.0, 0.02, 0.25)
    assert 0.0 < g['delta'] < 1.0
    assert g['gamma'] > 0.0
    assert g['vega'] > 0.0

def test_inventory_skews_quotes_lower_for_long_position():
    q = QuotePolicy(inventory_penalty=0.02)
    bid0, ask0 = q.quotes(5.0, 0.0, 0.02, 0.2)
    bid1, ask1 = q.quotes(5.0, 5.0, 0.02, 0.2)
    assert bid1 < bid0 and ask1 < ask0

def test_delta_hedging_reproducible():
    cfg = HedgeConfig(paths=50, steps=15, seed=11)
    assert DeltaHedgingSimulator(cfg).run() == DeltaHedgingSimulator(cfg).run()
