import os
import time
import threading
import logging
import requests
import telebot
from telebot import types
from urllib.parse import quote_plus
from flask import Flask

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
XAPIVERSE_KEY = os.getenv("XAPIVERSE_KEY")

PLAYER_BASE = "https://teraplayer979.github.io/stream-player/"

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not BOT_TOKEN or not XAPIVERSE_KEY:
    logger.error("Missing BOT_TOKEN or XAPIVERSE_KEY")
    raise SystemExit(1)

# ---------------- BOT ----------------
bot = telebot.TeleBot(BOT_TOKEN)

# ---------------- FLASK ----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ---------------- START ----------------
@bot.message_handler(commands=["start", "help"])
def start(message):
    bot.reply_to(message, "Send a Terabox link to stream or download.")

# ---------------- MAIN HANDLER ----------------
@bot.message_handler(func=lambda message: True)
def handle_link(message):
    url_text = message.text.strip()

    if "terabox" not in url_text and "1024tera" not in url_text:
        return

    status_msg = bot.reply_to(message, "⏳ Generating links...")

    try:
        response = requests.post(
            "https://xapiverse.com/api/terabox",
            headers={
                "Content-Type": "application/json",
                "xAPIverse-Key": XAPIVERSE_KEY
            },
            json={"url": url_text},
            timeout=60
        )

        if response.status_code != 200:
            bot.edit_message_text(
                message.chat.id,
                status_msg.message_id,
                f"❌ API Error: {response.status_code}"
            )
            return

        data = response.json()
        files = data.get("list", [])

        if not files:
            bot.edit_message_text(
                message.chat.id,
                status_msg.message_id,
                "❌ No file data found."
            )
            return

        file_info = files[0]
        streams = file_info.get("fast_stream_url", {})

        watch_url = (
            streams.get("720p")
            or streams.get("480p")
            or streams.get("360p")
            or file_info.get("stream_url")
            or file_info.get("download_link")
        )

        if not watch_url:
            bot.edit_message_text(
                message.chat.id,
                status_msg.message_id,
                "❌ No playable stream found."
            )
            return

        player_url = f"{PLAYER_BASE}?url={quote_plus(watch_url)}"
        download_url = file_info.get("download_link")
        file_name = file_info.get("name", "File Ready")

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("▶️ Watch Online", url=player_url))

        if download_url:
            markup.add(types.InlineKeyboardButton("⬇️ Download", url=download_url))

        bot.edit_message_text(
            message.chat.id,
            status_msg.message_id,
            f"✅ Ready!\n\n📦 {file_name}",
            reply_markup=markup
        )

    except Exception as e:
        logger.error(e)
        bot.edit_message_text(
            message.chat.id,
            status_msg.message_id,
            "⚠️ Something went wrong."
        )

# ---------------- RUN BOT ----------------
def run_bot():
    logger.info("Bot started")
    bot.remove_webhook()
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            logger.error(e)
            time.sleep(10)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()            timeout=60
        )

        if response.status_code != 200:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text=f"❌ API Error: {response.status_code}"
            )
            return

        json_data = response.json()
        logger.info(json_data)

        file_list = json_data.get("list", [])
        if not file_list:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text="❌ No file data found."
            )
            return

        file_info = file_list[0]

        fast_streams = file_info.get("fast_stream_url", {})

        watch_url = (
            fast_streams.get("720p")
            or fast_streams.get("480p")
            or fast_streams.get("360p")
            or file_info.get("stream_url")
            or file_info.get("download_link")
        )

        download_url = file_info.get("download_link")
        file_name = file_info.get("name", "File Ready")

        if not watch_url:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text="❌ No playable stream found."
            )
            return

        encoded_watch = quote_plus(watch_url)
        final_player_url = f"{PLAYER_BASE}?url={encoded_watch}"

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("▶️ Watch Online", url=final_player_url)
        )

        if download_url:
            markup.add(
                types.InlineKeyboardButton("⬇️ Download", url=download_url)
            )

        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=f"✅ Ready!\n\n📦 {file_name}",
            reply_markup=markup
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text="⚠️ Something went wrong."
        )

# ---------------- BOT RUNNER ----------------
def run_bot():
    logger.info("Bot starting...")
    try:
        bot.remove_webhook()
        time.sleep(2)
    except Exception:
        pass

    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            logger.error(f"Polling crashed: {e}")
            time.sleep(10)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    # Run Flask in background thread
    threading.Thread(target=run_flask).start()

    # Run Telegram bot
    run_bot()                types.InlineKeyboardButton("📢 Join Channel to Use", url=CHANNEL_LINK)
            )
            bot.reply_to(
                message,
                "⚠️ **Access Denied**\n\nYou must join our update channel to use this bot.",
                parse_mode="Markdown",
                reply_markup=fs_markup
            )
            return
    except Exception as e:
        logger.error(f"Force Subscribe Check Failed: {e}")
        bot.reply_to(message, "⚠️ Error verifying subscription.")
        return

    status_msg = bot.reply_to(message, "⏳ Generating links...")

    try:
        api_url = "https://xapiverse.com/api/terabox"
        headers = {
            "Content-Type": "application/json",
            "xAPIverse-Key": XAPIVERSE_KEY
        }
        payload = {"url": url_text}

        response = requests.post(api_url, headers=headers, json=payload, timeout=60)

        if response.status_code != 200:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text=f"❌ API Error: {response.status_code}"
            )
            return

        json_data = response.json()
        file_list = json_data.get("list", [])
        if not file_list:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text="❌ No file data found."
            )
            return

        file_info = file_list[0]
        fast_streams = file_info.get("fast_stream_url", {})

        watch_url = (
            fast_streams.get("720p")
            or fast_streams.get("480p")
            or fast_streams.get("360p")
            or file_info.get("stream_url")
            or file_info.get("download_link")
        )

        download_url = file_info.get("download_link")
        file_name = file_info.get("name", "File Ready")

        if not watch_url:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text="❌ No playable stream found."
            )
            return

        encoded_watch = quote_plus(watch_url)
        final_player_url = f"{PLAYER_BASE}?url={encoded_watch}"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("▶️ Watch Online", url=final_player_url))

        if download_url:
            markup.add(types.InlineKeyboardButton("⬇️ Download", url=download_url))

        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=f"✅ Ready!\n\n📦 {file_name}",
            reply_markup=markup
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text="⚠️ Something went wrong."
        )

# --------------- SAFE RUNNER ------------
def run_bot():
    logger.info("Bot starting...")
    try:
        bot.remove_webhook()
        time.sleep(3)
    except:
        pass

    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            logger.error(f"Polling crashed: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_bot()    return kb

def admin_menu():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("📊 Stats", callback_data="stats"),
        InlineKeyboardButton("🧹 Clean", callback_data="clean"),
    )
    return kb

# ================= TERABOX API =================
def fetch_terabox_files(url):
    """
    Fetch Terabox files using your cookie (pcftoken) without proxy
    """
    headers = {"Cookie": f"pcftoken={TERABOX_COOKIE}"}
    try:
        # Using Terabox public API endpoint to list files
        r = requests.get("https://www.1024terabox.com/api/share/list", params={"shorturl": url}, headers=headers, timeout=20)
        data = r.json()
        if data.get("errno") != 0:
            return None
        files = []
        for f in data["list"]:
            # Build download link
            download_url = f.get("dlink")  # direct download link
            if not download_url:
                continue
            files.append({"name": f.get("server_filename"), "download": download_url, "size": f.get("size")})
        return files
    except:
        return None

# ================= START =================
@bot.message_handler(commands=["start"])
def start(m):
    uid = m.from_user.id
    if FORCE_CHANNELS and not is_joined(uid):
        bot.send_message(uid, "🚨 Join required", reply_markup=force_join_kb())
        return

    db.execute("INSERT OR IGNORE INTO users VALUES (?)", (uid,))
    conn.commit()
    bot.send_message(uid,
                     "📦 <b>Terabox Downloader Bot</b>\n\nSend Terabox link to download videos.",
                     reply_markup=main_menu(), parse_mode="HTML")

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    uid = c.from_user.id
    if c.data == "check_join":
        if is_joined(uid):
            bot.edit_message_text("✅ Access granted", uid, c.message.message_id, reply_markup=main_menu())
        else:
            bot.answer_callback_query(c.id, "Join all channels first")
    elif c.data == "download":
        bot.send_message(uid, "🔗 Send Terabox link")
    elif c.data == "stats" and uid == ADMIN_ID:
        users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        downloads = db.execute("SELECT downloads FROM stats").fetchone()[0]
        bot.edit_message_text(f"👤 Users: {users}\n📥 Downloads: {downloads}", uid, c.message.message_id, reply_markup=admin_menu())
    elif c.data == "clean" and uid == ADMIN_ID:
        for f in os.listdir(DOWNLOAD_DIR):
            os.remove(os.path.join(DOWNLOAD_DIR, f))
        bot.answer_callback_query(c.id, "Storage cleaned")

# ================= MESSAGE =================
@bot.message_handler(func=lambda m: True)
def handle(m):
    uid = m.from_user.id
    if FORCE_CHANNELS and not is_joined(uid):
        bot.send_message(uid, "🚨 Join required", reply_markup=force_join_kb())
        return
    if "terabox" not in m.text.lower():
        bot.send_message(uid, "❌ Send a valid Terabox link")
        return

    msg = bot.send_message(uid, "⏳ Fetching files...")
    files = fetch_terabox_files(m.text)
    if not files:
        bot.edit_message_text("❌ Failed to fetch files", uid, msg.message_id)
        return

    for i, f in enumerate(files):
        size_mb = int(f.get("size", 0)) / (1024 * 1024)
        if size_mb > 1900:
            continue
        try:
            r = requests.get(f["download"], stream=True, timeout=60)
            path = os.path.join(DOWNLOAD_DIR, f["name"])
            with open(path, "wb") as out:
                for chunk in r.iter_content(1024 * 1024):
                    out.write(chunk)

            with open(path, "rb") as v:
                bot.send_video(uid, v, timeout=180, reply_markup=download_more() if i == len(files)-1 else None)

            os.remove(path)
            db.execute("UPDATE stats SET downloads = downloads + 1")
            conn.commit()
        except:
            continue

    bot.delete_message(uid, msg.message_id)

# ================= RUN =================
def run_bot():
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60)
        except Exception as e:
            print("Restarting:", e)
            time.sleep(5)

threading.Thread(target=run_flask, daemon=True).start()
run_bot()
# ================= MENUS =================
def main_menu():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📥 Download Terabox", callback_data="download"))
    return kb

def download_more():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⬇️ Download More", callback_data="download"))
    return kb

def admin_menu():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("📊 Stats", callback_data="stats"),
        InlineKeyboardButton("🧹 Clean", callback_data="clean"),
    )
    return kb

# ================= TERABOX API =================
def fetch_terabox_info(url):
    api = "https://terabox-downloader-api.vercel.app/api"
    try:
        r = requests.get(api, params={"url": url}, timeout=25)
        data = r.json()
        if not data.get("ok"):
            return None
        return data["files"]
    except Exception as e:
        print("API error:", e)
        return None

# ================= START =================
@bot.message_handler(commands=["start"])
def start(m):
    uid = m.from_user.id

    if not is_joined(uid):
        bot.send_message(uid, "🚨 Please join required channels", reply_markup=force_join_kb())
        return

    db.execute("INSERT OR IGNORE INTO users VALUES (?)", (uid,))
    conn.commit()

    bot.send_message(
        uid,
        "📦 <b>Terabox Downloader Bot</b>\n\nSend any Terabox link.",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    uid = c.from_user.id

    if c.data == "check_join":
        if is_joined(uid):
            bot.edit_message_text("✅ Access granted", uid, c.message.message_id, reply_markup=main_menu())
        else:
            bot.answer_callback_query(c.id, "Join all channels first")

    elif c.data == "download":
        bot.send_message(uid, "🔗 Send Terabox link")

    elif c.data == "stats" and uid == ADMIN_ID:
        users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        downloads = db.execute("SELECT downloads FROM stats").fetchone()[0]
        bot.edit_message_text(
            f"👤 Users: {users}\n📥 Downloads: {downloads}",
            uid, c.message.message_id, reply_markup=admin_menu()
        )

    elif c.data == "clean" and uid == ADMIN_ID:
        for f in os.listdir(DOWNLOAD_DIR):
            os.remove(os.path.join(DOWNLOAD_DIR, f))
        bot.answer_callback_query(c.id, "✅ Storage cleaned")

# ================= MESSAGE =================
@bot.message_handler(func=lambda m: True)
def handle(m):
    uid = m.from_user.id
    text = m.text or ""

    if not is_joined(uid):
        bot.send_message(uid, "🚨 Join required", reply_markup=force_join_kb())
        return

    if "terabox" not in text.lower():
        bot.send_message(uid, "❌ Please send a valid Terabox link")
        return

    msg = bot.send_message(uid, "⏳ Fetching files...")
    files = fetch_terabox_info(text)

    if not files:
        bot.edit_message_text("❌ Failed to fetch files. Try later.", uid, msg.message_id)
        return

    for f in files:
        size_mb = int(f.get("size", 0)) / (1024 * 1024)
        if size_mb > MAX_SIZE_MB:
            bot.send_message(uid, f"⚠️ Skipped large file: {f['name']}")
            continue

        try:
            name = clean_name(f["name"])
            path = os.path.join(DOWNLOAD_DIR, name)

            r = requests.get(f["download"], stream=True, timeout=60)
            with open(path, "wb") as out:
                for chunk in r.iter_content(1024 * 1024):
                    out.write(chunk)

            with open(path, "rb") as v:
                bot.send_video(uid, v, timeout=180, reply_markup=download_more())

            os.remove(path)
            db.execute("UPDATE stats SET downloads = downloads + 1")
            conn.commit()

        except Exception as e:
            print("Download error:", e)
            bot.send_message(uid, f"❌ Failed: {f['name']}")

    bot.delete_message(uid, msg.message_id)

# ================= RUN =================
def run_bot():
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60)
        except Exception as e:
            print("Restarting:", e)
            time.sleep(5)

threading.Thread(target=run_flask, daemon=True).start()
run_bot()
