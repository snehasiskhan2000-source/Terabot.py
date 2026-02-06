import os
import time
import logging
import threading
import requests
import telebot
from telebot import types
from flask import Flask
from urllib.parse import quote_plus

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
XAPIVERSE_KEY = os.getenv("XAPIVERSE_KEY")

PLAYER_BASE = "https://teraplayer979.github.io/stream-player/"

# --------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not BOT_TOKEN or not XAPIVERSE_KEY:
    logger.error("Missing BOT_TOKEN or XAPIVERSE_KEY")
    exit(1)

# ---------------- BOT -------------------
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=["start", "help"])
def start(message):
    bot.reply_to(message, "Send a Terabox link to stream or download.")

@bot.message_handler(func=lambda message: True)
def handle_link(message):
    url_text = message.text.strip()

    if "terabox" not in url_text and "1024tera" not in url_text:
        return

    status_msg = bot.reply_to(message, "⏳ Processing...")

    try:
        api_url = "https://xapiverse.com/api/terabox"
        headers = {
            "Content-Type": "application/json",
            "xAPIverse-Key": XAPIVERSE_KEY
        }

        response = requests.post(
            api_url,
            headers=headers,
            json={"url": url_text},
            timeout=60
        )

        if response.status_code != 200:
            bot.edit_message_text(
                "❌ API error",
                message.chat.id,
                status_msg.message_id
            )
            return

        data = response.json()
        file = data["list"][0]

        watch_url = (
            file.get("fast_stream_url", {}).get("720p")
            or file.get("stream_url")
            or file.get("download_link")
        )

        encoded = quote_plus(watch_url)
        final_url = f"{PLAYER_BASE}?url={encoded}"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("▶ Watch", url=final_url))

        bot.edit_message_text(
            f"✅ Ready\n📦 {file.get('name')}",
            message.chat.id,
            status_msg.message_id,
            reply_markup=markup
        )

    except Exception as e:
        logger.error(e)
        bot.edit_message_text(
            "⚠️ Failed",
            message.chat.id,
            status_msg.message_id
        )

# ---------------- FLASK -----------------
app = Flask(__name__)

@app.route("/")
def health():
    return "Bot is alive", 200

# ---------------- RUNNERS ----------------
def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(5)

def run_flask():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
