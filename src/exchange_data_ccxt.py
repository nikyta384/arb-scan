

from new_full_app_cctx import BinanceFutures, BybitFutures, GateFutures, OkxFutures, MEXCFutures, KuCoinFutures
from datetime import datetime, timezone
import pytz
from logging_config import logger
# Mapping now only stores the class
MARKET_MAP = {
    'binance_1_perp': BinanceFutures,
    'bybit_1_perp': BybitFutures,
    'gateio_1_perp': GateFutures,
    'kucoin_1_perp': KuCoinFutures,
    'mexc_1_perp': MEXCFutures,
    'okx_1_perp': OkxFutures,
}

KYIV_TZ = pytz.timezone("Europe/Kyiv")


def ms_to_kyiv_time(ms):
    if not ms:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).astimezone(KYIV_TZ)

##exchange_data_cctx.py

def get_market_exchange_data(spreads_data):
    symbol = spreads_data['coin']
    buy_market = spreads_data['buy_on']
    sell_market = spreads_data['sell_on']

    # Map roles → exchange names
    market_roles = {
        "buy_on": buy_market,
        "sell_on": sell_market,
    }

    market_results = {}
    return_data = []

    for role, market_name in market_roles.items():
        if market_name not in MARKET_MAP:
            logger.warning(f"Unknown market: {market_name}")
            return None

        cls = MARKET_MAP[market_name]
        market_instance = cls(symbol)   # just pass symbol directly

        price = market_instance.get_price()
        fnd = market_instance.get_funding_rate()
        market_comission = market_instance.get_commission()
        volume = market_instance.get_volume()
        # ✅ Check if any required value is None
        if (
            price is None
            or fnd is None
            or market_comission is None
        ):
            logger.error(
                f"[{market_name}] Missing data for {symbol}: "
                f"price={price}, funding={fnd}, commission={market_comission}, volume={volume}"
            )
            return None
        rate = fnd['funding_rate']
        ts = fnd['next_funding_time']
        
        market_comission_maker = market_comission['maker']
        market_comission_taker = market_comission['taker']
        

        result = {
            'symbol': symbol,
            'market_name': market_name,
            'price': price,
            'fund_rate': rate,
            'fund_time_human': ms_to_kyiv_time(ts),
            'fund_time': ts,
            'volume': volume,
            'comission_maker': market_comission_maker,
            'comission_taker': market_comission_taker
        }
        return_data.append(result)

        # ✅ now mapped by role instead of exchange name
        market_results[role] = result

    # import json
    # print(market_results)
    spread_pct = None

    buy_price = market_results['buy_on']['price']
    sell_price = market_results['sell_on']['price']
    if buy_price and sell_price:
        try:
            spread_pct = round(((sell_price - buy_price) / buy_price) * 100, 4)
        except ZeroDivisionError:
            pass

    return {'markets_data': return_data, 'spread_pct': spread_pct}
