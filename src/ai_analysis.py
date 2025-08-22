from vars import X_API_KEY


from xai_sdk import Client
from xai_sdk.chat import user, system
from xai_sdk.search import SearchParameters
from datetime import datetime, timedelta
from logging_config import logger

def get_date_range():
    # Get today's date
    from_date = datetime.today()
    # Calculate tomorrow's date
    to_date = from_date + timedelta(days=1)
    
    # Return the dates
    return from_date, to_date
def ask_ai_for_analysis(coin_name, ex1, ex2 ):
    logger.info(f"Asking for AI analysis for {coin_name} on {ex1} and {ex2}.")
    from_date, to_date = get_date_range()


    # Initialize the xAI client
    client = Client(api_key=X_API_KEY)

    system_message = f"""You are an expert cryptocurrency analyst.
    You must search the internet for the most recent information about the requested cryptocurrency (within last 2 days).
    Return ONLY valid JSON in this format:
    {{
    "sentiment": int (1 to 10, where 10 = very positive sentiment),
    "exchanhes": string (summary of todays news about the coin on exchanhe {ex1} and {ex2}  ),
    "news": string (summary of todays news about the coin)
    }}
    """
    user_prompt = f"Gather internet and x (Twitter) sentiments and news about {coin_name}. Provide the sentiment score and news summary for today. Gather data about price on futures on binance, bybit, mexc, okx, kucoin , gateio of {coin_name} coin, check reasons of possible spreads on exchanhes {ex1} and {ex2} of {coin_name} coin."

    try:
        chat = client.chat.create(
            model="grok-4-0709",  # Specify the model, e.g., grok-4-0709
            search_parameters=SearchParameters(mode="auto",from_date=from_date, to_date=to_date),
            response_format="json_object",
            
        )
        chat.append(system(system_message))
        chat.append(user(user_prompt))

        response = chat.sample()
        return response.content

    except Exception as e:
        msg = f"Error with AI analysis: {e}"
        logger.error(msg)
        return msg
