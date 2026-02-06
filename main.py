import os
import time
import threading
import logging
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
XAPIVERSE_KEY = os.getenv("XAPIVERSE_KEY")

CHANNEL_USERNAME = "@techbittu69"

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not BOT_TOKEN or not XAPIVERSE_KEY:
    raise SystemExit("Missing BOT_TOKEN or XAPIVERSE_KEY")

# ---------------- BOT ----------------
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ---------------- FLASK ----------------
app = Flask(__name__)

@app.route("/")
def health():
    return "Alive", 200

# ---------------- FORCE JOIN ----------------
def is_joined(user_id):
    try:
        m = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return m.status in ("member", "administrator", "creator")
    except:
        return False

def force_join_markup():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(
            "📢 Join Channel",
            url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"
        ),
        InlineKeyboardButton(
            "✅ Joined",
            callback_data="check_join"
        )
    )
    return markup

# ---------------- START ----------------
@bot.message_handler(commands=["start"])
def start(message):
    if not is_joined(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "⚠️ <b>Access Restricted</b>\n\n"
            "Join the channel and press <b>Joined</b>.",
            reply_markup=force_join_markup()
        )
        return

    bot.send_message(
        message.chat.id,
        "✅ <b>Access Granted</b>\n\n"
        "Send a Terabox link to download the video 🎥"
    )

# ---------------- CALLBACKS ----------------
@bot.callback_query_handler(func=lambda c: c.data == "check_join")
def check_join(call):
    if is_joined(call.from_user.id):
        bot.edit_message_text(
            "✅ <b>You are verified!</b>\n\nSend a Terabox link.",
            call.message.chat.id,
            call.message.message_id
        )
    else:
        bot.answer_callback_query(
            call.id,
            "❌ You have not joined yet!",
            show_alert=True
        )

@bot.callback_query_handler(func=lambda c: c.data == "download_more")
def download_more(call):
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "📥 Send another Terabox link."
    )

# ---------------- TERABOX API ----------------
def get_direct_link(url):
    r = requests.post(
        "https://xapiverse.com/api/terabox",
        headers={
            "Content-Type": "application/json",
            "xAPIverse-Key": XAPIVERSE_KEY
        },
        json={"url": url},
        timeout=60
    )
    r.raise_for_status()
    data = r.json()
    file = data["list"][0]
    return file["download_link"]

# ---------------- DOWNLOAD ----------------
def download_file(url, path):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                f.write(chunk)

# ---------------- MAIN HANDLER ----------------
@bot.message_handler(func=lambda m: True)
def handle_link(message):
    if not is_joined(message.from_user.id):
        start(message)
        return

    text = message.text.lower()
    if "terabox" not in text and "1024tera" not in text:
        return

    status = bot.send_message(message.chat.id, "⏳ Processing...")
    file_path = "video.mp4"

    try:
        link = get_direct_link(message.text)
        bot.edit_message_text("📥 Downloading...", message.chat.id, status.message_id)
        download_file(link, file_path)

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(
                "⬇️ Download More",
                callback_data="download_more"
            )
        )

        with open(file_path, "rb") as v:
            bot.send_video(
                message.chat.id,
                v,
                caption="✅ Done",
                reply_markup=markup,
                supports_streaming=True
            )

        bot.delete_message(message.chat.id, status.message_id)

    except Exception as e:
        logger.error(e)
        bot.edit_message_text("❌ Failed", message.chat.id, status.message_id)

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# ---------------- RUN ----------------
def run_bot():
    bot.remove_webhook()
    bot.infinity_polling()

def run_flask():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()
