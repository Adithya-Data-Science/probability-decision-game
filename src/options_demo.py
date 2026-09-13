import json
from src.options_pricing import EuropeanOption, QuotePolicy
from src.options_hedging import DeltaHedgingSimulator, HedgeConfig

cfg = HedgeConfig(paths=1000, steps=30, seed=17)
option = EuropeanOption(cfg.strike, cfg.maturity, 'call')
price = option.price(cfg.spot0, cfg.rate, cfg.vol)
greeks = option.greeks(cfg.spot0, cfg.rate, cfg.vol)
bid, ask = QuotePolicy().quotes(price, inventory=4.0, gamma=greeks['gamma'], vol=cfg.vol)
metrics = DeltaHedgingSimulator(cfg).run()
metrics.update({'initial_option_price': price, 'initial_delta': greeks['delta'], 'initial_gamma': greeks['gamma'], 'initial_vega': greeks['vega'], 'example_bid': bid, 'example_ask': ask})
print(json.dumps(metrics, indent=2))
