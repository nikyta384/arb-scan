
from logging_config import logger
from ccxt.base.errors import BadSymbol
from loris_tools import loris_tools_parse
from exchange_data_ccxt import get_market_exchange_data
from funding_time import same_funding_time_and_soon
import time 
from send_tg_message import format_signal_message, send_telegram_message
from vars import market_map
SLEEP_BEFORE_RECHECK_LORIS = 50 # 50
TIME_BEFORE_FUNDING = 20 # 20


LORIS_MIN_BPS_SPREAD_PERCENTAGE = 0.3 # 0.3 30 bps

LORIS_MIN_FUND_SPREAD = 0 # 0
MIN_MARKET_SPREAD = -0.2 # -0.2
MIN_VOLUME = 300000 # 300000
FINAL_FUND_SPREAD_WITH_COMMISSIONS = 0.3 #0.3


def calculate_min_volume_24h(buy_on_volume, sell_on_volume):

    if buy_on_volume is None:
        if sell_on_volume > MIN_VOLUME:
            return True
        else:
            return False
    elif sell_on_volume is None:
        if buy_on_volume > MIN_VOLUME:
            return True
        else:
            return False
    else:
        if buy_on_volume > MIN_VOLUME and sell_on_volume > MIN_VOLUME:
            return True
        else:
            return False
def compare_exchange__and_fund_and_comis_spread(spread, fund_spread, commissions):
    if spread > MIN_MARKET_SPREAD and ((spread + fund_spread) - commissions) > FINAL_FUND_SPREAD_WITH_COMMISSIONS :
        return True
    else:
        return False
def get_profit(spread, fund_spread, commissions):
    profit = (spread + fund_spread) - commissions
    return profit



def sort_market_data():
    logger.info("Executing loop.")
    loris_tools_spreads = loris_tools_parse((LORIS_MIN_BPS_SPREAD_PERCENTAGE * 100), LORIS_MIN_FUND_SPREAD)
    if loris_tools_spreads:
        for loris_tools_spread in loris_tools_spreads:
            try:
                market_data_dict = get_market_exchange_data(loris_tools_spread)
            except BadSymbol as e:
                logger.warning(f"Skipping due to unknown market symbol error: {e}")
                continue
            if market_data_dict:
                markets_data = market_data_dict['markets_data']

                buy_on_markets_data = markets_data[0]
                maker_comission_buy_on_market = float(buy_on_markets_data['comission_maker']) * 2
                taker_comission_buy_on_market = float(buy_on_markets_data['comission_taker']) * 2

                sell_on_markets_data = markets_data[1]
                maker_comission_sell_on_market = float(sell_on_markets_data['comission_maker']) * 2
                taker_comission_sell_on_market = float(sell_on_markets_data['comission_taker']) * 2

                maker_total_commission = maker_comission_buy_on_market + maker_comission_sell_on_market
                taker_total_commission = taker_comission_buy_on_market + taker_comission_sell_on_market

                buy_on_volume = buy_on_markets_data['volume']
                sell_on_volume = sell_on_markets_data['volume']

                exchange_market_spread = float(market_data_dict['spread_pct'])
                fund_spread_percentage = float(loris_tools_spread['fund_spread_percentage'])

                # calculation by market
                if compare_exchange__and_fund_and_comis_spread(exchange_market_spread, fund_spread_percentage, taker_total_commission) and calculate_min_volume_24h(buy_on_volume, sell_on_volume) and same_funding_time_and_soon(markets_data, TIME_BEFORE_FUNDING):
                    profit = get_profit(exchange_market_spread, fund_spread_percentage, taker_total_commission)
                    echo_message = f"""
                    ✅Loris data: {loris_tools_spread['coin']}, buy_on {loris_tools_spread['buy_on']}, buy_on_rate {loris_tools_spread['buy_on_rate']},
                    sell_on {loris_tools_spread['sell_on']}, sell_on_rate {loris_tools_spread['sell_on_rate']}, 
                    spread_bps {loris_tools_spread['spread_bps']}
                    \nMarkets data: Buy ON - {buy_on_markets_data['market_name']}, price: {buy_on_markets_data['price']}, fund_time_human: {buy_on_markets_data['fund_time_human']}, volume: {buy_on_volume}, commisions: maker {maker_comission_buy_on_market} taker {taker_comission_buy_on_market} 
                    Sell ON - {sell_on_markets_data['market_name']}, price: {sell_on_markets_data['price']}, fund_time_human: {sell_on_markets_data['fund_time_human']}, volume: {sell_on_volume}, commisions: maker {maker_comission_sell_on_market} taker {taker_comission_sell_on_market}
                    \nExchange spread in percentage: {exchange_market_spread}%, fund_spread_percentage {fund_spread_percentage}%, Profit: {profit}%
                    """
                    logger.info(echo_message)
                    logger.info(f"Funding time matches and is within {TIME_BEFORE_FUNDING} minutes.")
                    logger.info(f"UAinvest link: https://uainvest.com.ua/arbitrage/{loris_tools_spread['coin'].lower()}-{market_map[sell_on_markets_data['market_name']]}-swap-{market_map[buy_on_markets_data['market_name']]}-swap\n")
                    message = format_signal_message(
                            loris_tools_spread,
                            buy_on_markets_data,
                            sell_on_markets_data,
                            fund_spread_percentage,
                            exchange_market_spread,
                            maker_comission_buy_on_market,
                            taker_comission_buy_on_market,
                            maker_comission_sell_on_market,
                            taker_comission_sell_on_market,
                            TIME_BEFORE_FUNDING,
                            market_map,
                            profit
                        )
                    send_telegram_message(message)
                else:
                    logger.info("Data has been received but not corresponding.")
            else:
               logger.error("Something wrong in market_data_dict.") 
    logger.info("Loop executed.")
      
while True:
    sort_market_data()
    time.sleep(SLEEP_BEFORE_RECHECK_LORIS) 