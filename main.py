import os
import time
import threading
import logging
import requests
import telebot
from telebot import types
from urllib.parse import quote_plus
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
XAPIVERSE_KEY = os.getenv("XAPIVERSE_KEY")
PLAYER_BASE = "https://teraplayer979.github.io/stream-player/"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not BOT_TOKEN or not XAPIVERSE_KEY:
    raise SystemExit("Missing BOT_TOKEN or XAPIVERSE_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "OK", 200

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

@bot.message_handler(commands=["start", "help"])
def start(message):
    bot.reply_to(message, "Send a Terabox link.")

@bot.message_handler(func=lambda m: True)
def handle(message):
    text = message.text.strip()
    if "terabox" not in text and "1024tera" not in text:
        return

    msg = bot.reply_to(message, "⏳ Processing...")

    try:
        r = requests.post(
            "https://xapiverse.com/api/terabox",
            headers={"xAPIverse-Key": XAPIVERSE_KEY},
            json={"url": text},
            timeout=60
        )
        data = r.json()
        files = data.get("list", [])
        if not files:
            bot.edit_message_text("No file found", message.chat.id, msg.message_id)
            return

        f = files[0]
        stream = (
            f.get("fast_stream_url", {}).get("720p")
            or f.get("stream_url")
            or f.get("download_link")
        )

        url = f"{PLAYER_BASE}?url={quote_plus(stream)}"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("▶️ Watch", url=url))

        bot.edit_message_text(
            f"✅ {f.get('name','File')}",
            message.chat.id,
            msg.message_id,
            reply_markup=kb
        )

    except Exception as e:
        logger.error(e)
        bot.edit_message_text("Error", message.chat.id, msg.message_id)

def run_bot():
    bot.remove_webhook()
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()
