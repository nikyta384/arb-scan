
import ccxt
from datetime import datetime, timezone
import pytz
import requests

KYIV_TZ = pytz.timezone("Europe/Kyiv")

EXCHANGE_CLASSES = {
    "binance": ccxt.binance,
    "bybit": ccxt.bybit,
    "gate": ccxt.gate,
    "mexc": ccxt.mexc,
    "kucoinfutures": ccxt.kucoinfutures,
    "okx": ccxt.okx
    
}

FUNDING_TIME_KEYS = {
    "gate": 'fundingTimestamp',
    "mexc": 'nextSettleTime',
    "kucoinfutures": 'fundingTime',
    "okx": 'fundingTime',
}

class BaseFuturesExchange:
    def __init__(self, coin):
        self.coin = coin.upper()
        self.exchange = None
        self.load_exchange()
        self.symbol = self.format_symbol()

    def load_exchange(self):
        """To be implemented in subclasses"""
        raise NotImplementedError

    def format_symbol(self):
        # Standard: COIN/USDT:USDT
        return f"{self.coin}/USDT:USDT"

    def get_price(self):
        ticker = self.exchange.fetch_ticker(self.symbol)
        return ticker['last']

    def get_funding_rate(self):
        info = self.exchange.fetch_funding_rate(self.symbol)
        ex_id = self.exchange.id
        # Decide fundingTimestamp key
        key = FUNDING_TIME_KEYS.get(ex_id, 'nextFundingTime')

        if ex_id == 'gate':
            next_funding_time = info.get(key)
            if next_funding_time is not None:
                next_funding_time = int(next_funding_time)
        elif ex_id == 'mexc' or ex_id == 'kucoinfutures':
            next_funding_time = int(info['info'].get(key))
        else:
            next_funding_time = int(info['info'].get(key))

        funding_rate = float(info.get('fundingRate', 0)) * 100
        return {"funding_rate": funding_rate, "next_funding_time": next_funding_time}

    def get_volume(self):
        if self.exchange.id == "kucoinfutures": # spot volume, kucoin don't share futures volume
            # KuCoin uses different symbol format and API for volume
            symbol_k = self.symbol.replace('/', '-').replace(':USDT', '')
            url = f"https://api.kucoin.com/api/v1/market/stats?symbol={symbol_k}"
            resp = requests.get(url)
            if resp.ok:
                try:
                    vol_value = float(resp.json()['data']['volValue'])
                except (TypeError, ValueError):
                    print(f"Kucoin cant return volume value for {symbol_k}")
                    vol_value = None
                return vol_value
            print(f"Kucoin response isn't ok: {resp}")
            return None
        elif self.exchange.id == "okx":
            ticker = self.exchange.fetch_ticker(self.symbol)
            volume_usd = float(ticker['info']['volCcy24h']) * float(ticker['last'])  
            return volume_usd
        else:
            ticker = self.exchange.fetch_ticker(self.symbol)
            import json
            # print(json.dumps(ticker, indent=4))
            return ticker.get('quoteVolume')

    def get_commission(self):
        if self.exchange.id == "gate":
            return {"maker": 0.02, "taker": 0.05}
        market = self.exchange.market(self.symbol)
        return {
            "maker": market.get('maker', 0) * 100,
            "taker": market.get('taker', 0) * 100,
        }


class BinanceFutures(BaseFuturesExchange):
    def load_exchange(self):
        self.exchange = ccxt.binance({"options": {"defaultType": "future"}})
        self.exchange.load_markets()


class BybitFutures(BaseFuturesExchange):
    def load_exchange(self):
        self.exchange = ccxt.bybit({"options": {"defaultType": "future"}})
        self.exchange.load_markets()


class GateFutures(BaseFuturesExchange):
    def load_exchange(self):
        self.exchange = ccxt.gate({"options": {"defaultType": "future"}})
        self.exchange.load_markets()


class MEXCFutures(BaseFuturesExchange):
    def load_exchange(self):
        self.exchange = ccxt.mexc({"options": {"defaultType": "future"}})
        self.exchange.load_markets()


class KuCoinFutures(BaseFuturesExchange):
    def load_exchange(self):
        self.exchange = ccxt.kucoinfutures()
        self.exchange.load_markets()

class OkxFutures(BaseFuturesExchange):
    def format_symbol(self):
        # OKX uses 'COIN-USDT-SWAP' for perpetual futures
        return f"{self.coin}-USDT-SWAP"

    def load_exchange(self):
        self.exchange = ccxt.okx({
            "options": {
                "defaultType": "swap"  # OKX calls perpetual futures "swap"
            }
        })
        self.exchange.load_markets()

# def print_exchange_info(exchange_obj):
#     price = exchange_obj.get_price()
#     funding = exchange_obj.get_funding_rate()
#     volume = exchange_obj.get_volume()
#     commission = exchange_obj.get_commission()
#     funding_time = datetime.fromtimestamp(funding['next_funding_time'] / 1000, tz=timezone.utc).astimezone(KYIV_TZ)

#     print(f"\nExchange: {exchange_obj.exchange.id.upper()}")
#     print(f"Price: {price}")
#     print(f"Funding rate: {funding['funding_rate']:.5f}%")
#     print(f"Funding time: {funding_time}")
#     print(f"Volume: {volume}")
#     print(f"Commission: {commission}")


# if __name__ == "__main__":
#     exchanges = [
#         BinanceFutures("ETH"),
#         BybitFutures("ETH"),
#         GateFutures("ETH"),
#         MEXCFutures("ETH"),
#         KuCoinFutures("ETH"),
#         OkxFutures("ETH"),
#     ]

#     for ex in exchanges:
#         print_exchange_info(ex)














