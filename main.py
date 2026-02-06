import os
import time
import sqlite3
import threading
import requests
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
FORCE_CHANNELS = [c.strip() for c in os.environ.get("FORCE_CHANNELS", "").split(",") if c.strip()]
PORT = int(os.environ.get("PORT", 10000))

DOWNLOAD_DIR = "downloads"
DB_FILE = "bot.db"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# ================= DATABASE =================
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
db = conn.cursor()

db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
db.execute("CREATE TABLE IF NOT EXISTS stats (downloads INTEGER DEFAULT 0)")
db.execute("INSERT OR IGNORE INTO stats VALUES (0)")
conn.commit()

# ================= FLASK =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Terabox Downloader Bot Running"

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

# ================= FORCE JOIN =================
def is_joined(uid):
    for ch in FORCE_CHANNELS:
        try:
            status = bot.get_chat_member(ch, uid).status
            if status in ("left", "kicked"):
                return False
        except:
            return False
    return True

def force_join_kb():
    kb = InlineKeyboardMarkup()
    for ch in FORCE_CHANNELS:
        kb.add(InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{ch.lstrip('@')}"))
    kb.add(InlineKeyboardButton("✅ Joined", callback_data="check_join"))
    return kb

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
        r = requests.get(api, params={"url": url}, timeout=20)
        data = r.json()
        if not data.get("ok"):
            return None
        return data["files"]
    except:
        return None

# ================= START =================
@bot.message_handler(commands=["start"])
def start(m):
    uid = m.from_user.id
    if not is_joined(uid):
        bot.send_message(uid, "🚨 Join required to use this bot", reply_markup=force_join_kb())
        return

    db.execute("INSERT OR IGNORE INTO users VALUES (?)", (uid,))
    conn.commit()

    bot.send_message(
        uid,
        "📦 <b>Terabox Downloader Bot</b>\n\nSend Terabox link to download videos.",
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
        bot.answer_callback_query(c.id, "Storage cleaned")

# ================= MESSAGE =================
@bot.message_handler(func=lambda m: True)
def handle(m):
    uid = m.from_user.id

    if not is_joined(uid):
        bot.send_message(uid, "🚨 Join required", reply_markup=force_join_kb())
        return

    if "terabox" not in m.text.lower():
        bot.send_message(uid, "❌ Send a valid Terabox link")
        return

    msg = bot.send_message(uid, "⏳ Fetching files...")
    files = fetch_terabox_info(m.text)

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
                bot.send_video(
                    uid,
                    v,
                    timeout=180,
                    reply_markup=download_more() if i == len(files) - 1 else None
                )

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
