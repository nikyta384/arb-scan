
import os


SLEEP_BEFORE_RECHECK_LORIS = 50 # 50
TIME_BEFORE_FUNDING = 20 # 20


LORIS_MIN_BPS_SPREAD_PERCENTAGE = 0.3 # 0.3 30 bps

LORIS_MIN_FUND_SPREAD = 0 # 0
MIN_MARKET_SPREAD = -0.2 # -0.2
MIN_VOLUME = 300000 # 300000
FINAL_FUND_SPREAD_WITH_COMMISSIONS = 0.3 #0.3

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_CACHE_TTL = 300 # 5 min

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")



X_API_KEY =  os.getenv("X_API_KEY")
market_map = {
    'binance_1_perp': 'binance',
    'bybit_1_perp': 'bybit',
    'gateio_1_perp': 'gate',
    'kucoin_1_perp': 'kucoin',
    'mexc_1_perp': 'mexc',
    'okx_1_perp': 'okx',
}