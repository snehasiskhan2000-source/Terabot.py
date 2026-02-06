import os
import time
import threading
import logging
import requests
import telebot
from telebot.types import Message
from flask import Flask

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
XAPIVERSE_KEY = os.getenv("XAPIVERSE_KEY")

# ---------------- LOGGING ---------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not BOT_TOKEN or not XAPIVERSE_KEY:
    raise SystemExit("❌ Missing BOT_TOKEN or XAPIVERSE_KEY")

# ---------------- BOT -------------------
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ---------------- FLASK -----------------
app = Flask(__name__)

@app.route("/")
def health():
    return "Bot is alive", 200

# ---------------- TERABOX API ----------------
def get_terabox_direct_link(share_url: str) -> str:
    """
    Uses XAPIVERSE API to fetch direct download link
    """
    api_url = "https://xapiverse.com/api/terabox"
    headers = {
        "Content-Type": "application/json",
        "xAPIverse-Key": XAPIVERSE_KEY
    }

    r = requests.post(
        api_url,
        headers=headers,
        json={"url": share_url},
        timeout=60
    )
    r.raise_for_status()

    data = r.json()
    file_list = data.get("list", [])
    if not file_list:
        raise Exception("No file found")

    file = file_list[0]

    return (
        file.get("download_link")
        or file.get("stream_url")
        or file.get("fast_stream_url", {}).get("720p")
    )

# ---------------- DOWNLOAD ----------------
def download_video(url: str, filename: str):
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

# ---------------- BOT HANDLERS ----------------
@bot.message_handler(commands=["start", "help"])
def start(message: Message):
    bot.reply_to(
        message,
        "👋 <b>Terabox Downloader Bot</b>\n\n"
        "Send a <b>Terabox link</b> and I’ll download & send the video 🎥"
    )

@bot.message_handler(func=lambda m: True)
def handle_link(message: Message):
    chat_id = message.chat.id
    text = message.text.strip()

    if "terabox" not in text.lower() and "1024tera" not in text.lower():
        return

    status = bot.reply_to(message, "⏳ Fetching download link...")

    file_path = "video.mp4"

    try:
        direct_url = get_terabox_direct_link(text)

        bot.edit_message_text(
            "📥 Downloading video...",
            chat_id,
            status.message_id
        )

        download_video(direct_url, file_path)

        bot.edit_message_text(
            "📤 Uploading to Telegram...",
            chat_id,
            status.message_id
        )

        with open(file_path, "rb") as video:
            bot.send_video(
                chat_id,
                video,
                caption="✅ Downloaded via Terabot",
                supports_streaming=True
            )

        bot.delete_message(chat_id, status.message_id)

    except Exception as e:
        logger.error(e)
        bot.edit_message_text(
            f"❌ Failed: {e}",
            chat_id,
            status.message_id
        )

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# ---------------- RUNNERS ----------------
def run_bot():
    bot.remove_webhook()
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(5)

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()
