# from monitor_spreads import sort_market_data
# import time
# from vars import SLEEP_BEFORE_RECHECK_LORIS


# while True:
#     sort_market_data()
#     time.sleep(SLEEP_BEFORE_RECHECK_LORIS) 



########
from monitor_spreads import sort_market_data
from flask import Flask
import threading
import time
import redis
import json
from telegram import  InlineKeyboardButton, InlineKeyboardMarkup
from telegram.update import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from redis_cache import get_redis_data
from vars import TELEGRAM_BOT_TOKEN, SLEEP_BEFORE_RECHECK_LORIS
from ai_analysis import ask_ai_for_analysis





app = Flask(__name__)

@app.route("/")
def index():
    return "Flask server is running with background workers!"




def spread_monitor():
    """Loop worker for sorting market data periodically."""
    while True:
        sort_market_data()
        time.sleep(SLEEP_BEFORE_RECHECK_LORIS)


# =====================
# Telegram Bot Handlers
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show buttons on /start command."""
    keyboard = [
        [InlineKeyboardButton("📊 Active Spreads", callback_data="spreads")],
        [InlineKeyboardButton("🤖 AI Analysis", callback_data="analysis")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose an option:", reply_markup=reply_markup)



async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses."""
    query = update.callback_query
    await query.answer()

    if query.data == "spreads":
        spreads, keys = get_active_spreads()
        await query.edit_message_text(text=f"Active spreads:\n{spreads}")

    elif query.data == "analysis":
        _, keys = get_active_spreads()
        # show user a list of keys to pick from
        keyboard = [[InlineKeyboardButton(key, callback_data=f"analysis_{key}")] for key in keys]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="Choose a pair for analysis:",
            reply_markup=reply_markup
        )

    elif query.data.startswith("analysis_"):
        key = query.data.replace("analysis_", "", 1)
        coin, buy_on, sell_on = key.split('_')
        analysis = ask_ai_for_analysis(coin, buy_on, sell_on)
        await query.edit_message_text(text=f"AI Analysis for {coin} ({buy_on} → {sell_on}):\n{analysis}")



def get_active_spreads():
    """Fetch all cached spreads from Redis and return formatted JSON for display."""
    # Fetch all data from Redis
    spreads_data, keys = get_redis_data()
    
    # Format JSON for readability
    formatted_spreads = []
    for key, data in spreads_data.items():
        # Assuming each data entry is a dictionary and you want a specific format
        spread_info = f"{key}\n{json.dumps(data, indent=2)}"
        formatted_spreads.append(spread_info)
    
    # Join all formatted spreads into a single string
    return "\n\n".join(formatted_spreads), keys




def start_telegram_bot():
    """Run the Telegram bot (blocking)."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.run_polling()


# =====================
# Entry Point
# =====================
if __name__ == "__main__":
    # Background worker for loris
    threading.Thread(target=spread_monitor, daemon=True).start()

    # Telegram bot in a separate thread
    threading.Thread(target=start_telegram_bot, daemon=True).start()

    # Start Flask app
    app.run(host="0.0.0.0", port=5000)
