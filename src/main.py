

########
from monitor_spreads import sort_market_data
from flask import Flask
import threading
import time
import redis
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update  # Updated import
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
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
        spreads, _ = get_redis_data()
        if spreads:
            await query.edit_message_text(text=f"Active spreads:\n{spreads}")
        else:
            await query.edit_message_text(text=f"No current spreads")
            
    elif query.data == "analysis":
        _, titles = get_redis_data()
        if titles:
            # show user a list of keys to pick from
            keyboard = [[InlineKeyboardButton(key, callback_data=f"analysis_{key}")] for key in titles]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="Choose a pair for analysis:",
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(text=f"No current spreads")

    elif query.data.startswith("analysis_"):
        key = query.data.replace("analysis_", "", 1)
        coin, buy_on, sell_on = key.split('_')
        analysis = ask_ai_for_analysis(coin, buy_on, sell_on)
        await query.edit_message_text(text=f"AI Analysis for {coin} ({buy_on} → {sell_on}):\n{analysis}")






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
    
    # Start Flask app in a separate thread
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000), daemon=True).start()

    # Run the Telegram bot in the main thread
    start_telegram_bot()
