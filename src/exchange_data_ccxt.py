

from new_full_app_cctx import BinanceFutures, BybitFutures, GateFutures, OkxFutures, MEXCFutures, KuCoinFutures
from datetime import datetime, timezone
import pytz

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


# def get_market_exchange_data(spreads_data):
#     symbol = spreads_data['coin']
#     buy_market = spreads_data['buy_on']
#     sell_market = spreads_data['sell_on']

#     # Map roles → exchange names
#     market_roles = {
#         "buy_on": buy_market,
#         "sell_on": sell_market,
#     }

#     market_results = {}
#     return_data = []

#     for role, market_name in market_roles.items():
#         if market_name not in MARKET_MAP:
#             print(f"Unknown market: {market_name}")
#             continue

#         cls = MARKET_MAP[market_name]
#         market_instance = cls(symbol)   # just pass symbol directly

#         price = market_instance.get_price()
#         fnd = market_instance.get_funding_rate()
#         rate = fnd['funding_rate']
#         ts = fnd['next_funding_time']
#         market_comission = market_instance.get_commission()
#         market_comission_maker = market_comission['maker']
#         market_comission_taker = market_comission['taker']
#         volume = market_instance.get_volume()

#         result = {
#             'symbol': symbol,
#             'market_name': market_name,
#             'price': price,
#             'fund_rate': rate,
#             'fund_time_human': ms_to_kyiv_time(ts),
#             'fund_time': ts,
#             'volume': volume,
#             'comission_maker': market_comission_maker,
#             'comission_taker': market_comission_taker
#         }
#         return_data.append(result)

#         # ✅ now mapped by role instead of exchange name
#         market_results[role] = result

#     # import json
#     # print(market_results)
#     spread_pct = None

#     buy_price = market_results['buy_on']['price']
#     sell_price = market_results['sell_on']['price']
#     if buy_price and sell_price:
#         try:
#             spread_pct = round(((sell_price - buy_price) / buy_price) * 100, 4)
#         except ZeroDivisionError:
#             pass

#     return {'markets_data': return_data, 'spread_pct': spread_pct}




from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_market_data(role, market_name, symbol):
    if market_name not in MARKET_MAP:
        print(f"Unknown market: {market_name}")
        return role, None

    cls = MARKET_MAP[market_name]
    market_instance = cls(symbol)

    # run independent calls concurrently
    with ThreadPoolExecutor() as executor:
        futures = {
            "price": executor.submit(market_instance.get_price),
            "funding": executor.submit(market_instance.get_funding_rate),
            "commission": executor.submit(market_instance.get_commission),
            "volume": executor.submit(market_instance.get_volume),
        }

        results = {k: f.result() for k, f in futures.items()}

    fnd = results["funding"]
    comm = results["commission"]

    result = {
        "symbol": symbol,
        "market_name": market_name,
        "price": results["price"],
        "fund_rate": fnd.get("funding_rate"),
        "fund_time_human": ms_to_kyiv_time(fnd.get("next_funding_time")),
        "fund_time": fnd.get("next_funding_time"),
        "volume": results["volume"],
        "comission_maker": comm.get("maker"),
        "comission_taker": comm.get("taker"),
    }
    return role, result


def get_market_exchange_data(spreads_data):
    symbol = spreads_data["coin"]
    market_roles = {
        "buy_on": spreads_data["buy_on"],
        "sell_on": spreads_data["sell_on"],
    }

    market_results = {}
    return_data = []

    # run buy_on & sell_on in parallel
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_market_data, role, name, symbol)
                   for role, name in market_roles.items()]

        for f in as_completed(futures):
            role, result = f.result()
            if result:
                market_results[role] = result
                return_data.append(result)

    spread_pct = None
    if "buy_on" in market_results and "sell_on" in market_results:
        buy_price = market_results["buy_on"]["price"]
        sell_price = market_results["sell_on"]["price"]
        if buy_price and sell_price:
            try:
                spread_pct = round(((sell_price - buy_price) / buy_price) * 100, 4)
            except ZeroDivisionError:
                pass

    return {"markets_data": return_data, "spread_pct": spread_pct}
