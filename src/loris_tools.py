import json
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from logging_config import logger

# Assuming the JSON content is saved in a variable called `json_content` for parsing
# with open('loris-tools.json', 'r') as file:
#     json_content = json.load(file)


# Uncomment above and replace with actual API response string

def find_funding_spreads(data, LORIS_MIN_BPS_SPREAD, LORIS_MIN_FUND_SPREAD):
    funding_rates = data.get('funding_rates', {})

    # Interested exchanges
    exchanges_of_interest = [
        'binance_1_perp', 
        'bybit_1_perp', 
        'gateio_1_perp', 
        'kucoin_1_perp', 
        'mexc_1_perp', 
        'okx_1_perp'
    ]

    # Collect funding data only from these exchanges
    filtered_funding = {ex: funding_rates.get(ex, {}) for ex in exchanges_of_interest}



    # Get all cryptocurrencies available in these exchanges
    all_coins = set()
    for rates in filtered_funding.values():
        all_coins.update(rates.keys())

    # For each coin, compare funding rates across exchanges to find pairs where spread > 30
    significant_spread_pairs = []

    for coin in all_coins:
        # Gather funding rates where coin is present
        coin_rates = []
        for ex in exchanges_of_interest:
            rate = filtered_funding.get(ex, {}).get(coin)
            if rate is not None:
                coin_rates.append((ex, rate))

        # Compare each pair
        for i in range(len(coin_rates)):
            for j in range(i+1, len(coin_rates)):
                ex1, rate1 = coin_rates[i]
                ex2, rate2 = coin_rates[j]
                spread_bps = abs(rate1 - rate2)
                fund_spread = (float(rate2) - float(rate1)) / 100
                if spread_bps > LORIS_MIN_BPS_SPREAD and fund_spread > LORIS_MIN_FUND_SPREAD:
                    significant_spread_pairs.append({
                        'coin': coin,
                        'exchange1': ex1,
                        'rate1': rate1,
                        'exchange2': ex2,
                        'rate2': rate2,
                        'spread_bps': spread_bps,
                        'fund_spread': fund_spread
                    })

    return significant_spread_pairs

# def loris_tools_parse(LORIS_MIN_BPS_SPREAD, LORIS_MIN_FUND_SPREAD):
#     return_data = []
#     resp = requests.get('https://loris.tools/api/funding', verify=False)
#     resp.raise_for_status()
#     data = resp.json()
#     spreads = find_funding_spreads(data, LORIS_MIN_BPS_SPREAD, LORIS_MIN_FUND_SPREAD)
#     for entry in spreads:
#         spread_bps = round(float(entry['spread_bps']), 3)
#         fund_spread = round(float(entry['fund_spread']), 3)
#         return_data.append(
#             {
#                 'coin': entry['coin'],
#                 'buy_on': entry['exchange1'],
#                 'buy_on_rate': entry['rate1'],
#                 'sell_on': entry['exchange2'],
#                 'sell_on_rate': entry['rate2'],
#                 'spread_bps': spread_bps,
#                 'fund_spread_percentage': fund_spread
#             }
#         )
#     return return_data


def loris_tools_parse(LORIS_MIN_BPS_SPREAD, LORIS_MIN_FUND_SPREAD):
    return_data = []
    url = "https://loris.tools/api/funding"

    try:
        resp = requests.get(url, verify=False, timeout=10)
        resp.raise_for_status()

        data = resp.json()

        spreads = find_funding_spreads(data, LORIS_MIN_BPS_SPREAD, LORIS_MIN_FUND_SPREAD)

        for entry in spreads:
            spread_bps = round(float(entry['spread_bps']), 3)
            fund_spread = round(float(entry['fund_spread']), 3)

            return_data.append({
                'coin': entry['coin'],
                'buy_on': entry['exchange1'],
                'buy_on_rate': entry['rate1'],
                'sell_on': entry['exchange2'],
                'sell_on_rate': entry['rate2'],
                'spread_bps': spread_bps,
                'fund_spread_percentage': fund_spread
            })

        logger.info("Successfully parsed %d spreads", len(return_data))
        return return_data

    except requests.RequestException as e:
        logger.error("Request failed: %s", e, exc_info=True)
    except Exception as e:
        logger.error("Unexpected error in loris_tools_parse: %s", e, exc_info=True)

    return []  # Return empty list if error
