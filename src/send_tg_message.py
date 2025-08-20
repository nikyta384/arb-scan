
import os
import requests
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
from logging_config import logger
from vars import market_map

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to send message to Telegram: {e}")

def volume_human_format(number: float) -> str:
    # Define suffixes
    suffixes = ['', 'K', 'M', 'B', 'T']
    i = 0
    while abs(number) >= 1000 and i < len(suffixes) - 1:
        number /= 1000.0
        i += 1
    return f"{number:.3f}{suffixes[i]}"

def format_signal_message(loris_tools_spread, buy_on_markets_data, sell_on_markets_data,
                          fund_spread_percentage, exchange_market_spread,
                          maker_comission_buy_on_market, taker_comission_buy_on_market,
                          maker_comission_sell_on_market, taker_comission_sell_on_market, TIME_BEFORE_FUNDING, market_map, profit):
    message = (
        "🚨 *Arbitrage Opportunity Detected* 🚨\n\n"
        f"*Loris data:*\n"
        f"Coin: {loris_tools_spread['coin']}\n"
        f"Buy on ✅: {market_map[loris_tools_spread['buy_on']].upper()} ({loris_tools_spread['buy_on_rate']})\n"
        f"Sell on ❌: {market_map[loris_tools_spread['sell_on']].upper()} ({loris_tools_spread['sell_on_rate']})\n"
        f"Spread (bps): {loris_tools_spread['spread_bps']}\n\n"
        f"*Markets data:*\n"
        f"Buy ON ✅ - {market_map[buy_on_markets_data['market_name']].upper()}\n"
        f"Price: {buy_on_markets_data['price']}\n"
        f"Funding time: {buy_on_markets_data['fund_time_human']}\n"
        f"Volume: {volume_human_format(float(buy_on_markets_data['volume']))}\n"
        f"Commissions: Maker {maker_comission_buy_on_market}, Taker {taker_comission_buy_on_market}\n"
        f"Sell ON ❌ - {market_map[sell_on_markets_data['market_name']].upper()}\n"
        f"Price: {sell_on_markets_data['price']}\n"
        f"Funding time: {sell_on_markets_data['fund_time_human']}\n"
        f"Volume: {volume_human_format(float(sell_on_markets_data['volume']))}\n"
        f"Commissions: M {maker_comission_sell_on_market}, T {taker_comission_sell_on_market}\n\n"
        f"Funding Spread: {fund_spread_percentage}%\n"
        f"Exchange spread (%): {exchange_market_spread}%\n"
        f"Profit: {profit}%.\n\n"
        f"[UAinvest link](https://uainvest.com.ua/arbitrage/{loris_tools_spread['coin'].lower()}-"
        f"{market_map[sell_on_markets_data['market_name']]}-swap-"
        f"{market_map[buy_on_markets_data['market_name']]}-swap)"
    )
    return message