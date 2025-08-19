
import os
import requests
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
from logging_config import logger
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to send message to Telegram: {e}")


def format_signal_message(loris_tools_spread, buy_on_markets_data, sell_on_markets_data,
                          fund_spread_percentage, exchange_market_spread,
                          maker_comission_buy_on_market, taker_comission_buy_on_market,
                          maker_comission_sell_on_market, taker_comission_sell_on_market, TIME_BEFORE_FUNDING, market_map, profit):
    message = (
        "🚨 *Arbitrage Opportunity Detected* 🚨\n\n"
        f"*Loris data:*\n"
        f"Coin: {loris_tools_spread['coin']}\n"
        f"Buy on ✅: {loris_tools_spread['buy_on']} at rate {loris_tools_spread['buy_on_rate']}\n"
        f"Sell on ❌: {loris_tools_spread['sell_on']} at rate {loris_tools_spread['sell_on_rate']}\n"
        f"Spread (bps): {loris_tools_spread['spread_bps']}\n"
        f"Funding Spread: {fund_spread_percentage}%\n\n"
        f"*Markets data:*\n"
        f"Buy ON ✅ - {buy_on_markets_data['market_name']}\n"
        f"Price: {buy_on_markets_data['price']}\n"
        f"Funding time: {buy_on_markets_data['fund_time_human']}\n"
        f"Volume: {buy_on_markets_data['volume']}\n"
        f"Commissions: Maker {maker_comission_buy_on_market}, Taker {taker_comission_buy_on_market}\n\n"
        f"Sell ON ❌ - {sell_on_markets_data['market_name']}\n"
        f"Price: {sell_on_markets_data['price']}\n"
        f"Funding time: {sell_on_markets_data['fund_time_human']}\n"
        f"Volume: {sell_on_markets_data['volume']}\n"
        f"Commissions: Maker {maker_comission_sell_on_market}, Taker {taker_comission_sell_on_market}\n\n"
        f"Exchange spread (%): {exchange_market_spread}%\n"
        f"Funding time matches within {TIME_BEFORE_FUNDING} minutes.\n"
        f"Profit: {profit}%.\n\n"
        f"[UAinvest link](https://uainvest.com.ua/arbitrage/{loris_tools_spread['coin'].lower()}-"
        f"{market_map[sell_on_markets_data['market_name']]}-swap-"
        f"{market_map[buy_on_markets_data['market_name']]}-swap)"
    )
    return message