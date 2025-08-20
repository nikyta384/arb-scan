
import ccxt
from datetime import datetime, timezone
import pytz
import requests
from logging_config import logger
import time
import ccxt.base.errors

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
        self.symbol = None
        retries = 3
        while retries > 0:
            try:
                self.load_exchange()
                self.symbol = self.format_symbol()
                break  # Exit loop if successful
            except (TimeoutError, ccxt.base.errors.RequestTimeout) as e:
                logger.error(f"[{self.coin}] Timeout error loading exchange: {e}. Retries left: {retries-1}", exc_info=True)
                retries -= 1
                if retries > 0:
                    time.sleep(20)  # Wait for 20 seconds before retrying
            except Exception as e:
                logger.error(f"[{self.coin}] Failed to load exchange: {e}", exc_info=True)
                break  # Exit loop for any other error
        else:
            # If we exhausted all retries, set the exchange to None
            logger.error(f"[{self.coin}] Exhausted retries to load exchange. Setting exchange to None.")
            self.exchange = None

    def load_exchange(self):
        """To be implemented in subclasses"""
        raise NotImplementedError

    def format_symbol(self):
        # Standard: COIN/USDT:USDT
        return f"{self.coin}/USDT:USDT"

    def get_price(self):
        try:
            ticker = self.exchange.fetch_ticker(self.symbol)
            return ticker.get('last')
        except Exception as e:
            logger.error(f"[{self.exchange.id}] get_price error for {self.symbol}: {e}", exc_info=True)
            return None

    def get_funding_rate(self):
        try:
            info = self.exchange.fetch_funding_rate(self.symbol)
            ex_id = self.exchange.id
            key = FUNDING_TIME_KEYS.get(ex_id, 'nextFundingTime')

            if ex_id == 'gate':
                next_funding_time = info.get(key)
                if next_funding_time is not None:
                    next_funding_time = int(next_funding_time)
            elif ex_id in ('mexc', 'kucoinfutures', 'okx'):
                next_funding_time = int(info['info'].get(key))
            else:
                next_funding_time = int(info['info'].get(key))

            funding_rate = float(info.get('fundingRate', 0)) * 100
            return {"funding_rate": funding_rate, "next_funding_time": next_funding_time}
        except Exception as e:
            logger.error(f"[{self.exchange.id}] get_funding_rate error for {self.symbol}: {e}", exc_info=True)
            return None

    def get_volume(self):
        try:
            if self.exchange.id == "kucoinfutures":
                symbol_k = self.symbol.replace('/', '-').replace(':USDT', '')
                url = f"https://api.kucoin.com/api/v1/market/stats?symbol={symbol_k}"
                resp = requests.get(url)
                if resp.ok:
                    try:
                        return float(resp.json()['data']['volValue'])
                    except (TypeError, ValueError):
                        logger.warn(f"KuCoin can't parse volume value for {symbol_k}")
                        return None
                logger.warning(f"KuCoin response not OK: {resp}")
                return None
            elif self.exchange.id == "okx":
                ticker = self.exchange.fetch_ticker(self.symbol)
                return float(ticker['info']['volCcy24h']) * float(ticker['last'])
            else:
                ticker = self.exchange.fetch_ticker(self.symbol)
                return ticker.get('quoteVolume')
        except Exception as e:
            logger.error(f"[{self.exchange.id}] get_volume error for {self.symbol}: {e}", exc_info=True)
            return None

    def get_commission(self):
        try:
            if self.exchange.id == "gate":
                return {"maker": 0.02, "taker": 0.05}
            market = self.exchange.market(self.symbol)
            return {
                "maker": market.get('maker', 0) * 100,
                "taker": market.get('taker', 0) * 100,
            }
        except Exception as e:
            logger.error(f"[{self.exchange.id}] get_commission error for {self.symbol}: {e}", exc_info=True)
            return None


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














