import os
import time
import asyncio
import logging
import aiohttp
import threading
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.async_telebot import AsyncTeleBot

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
XAPIVERSE_KEY = os.getenv("XAPIVERSE_KEY")

CHANNEL_USERNAME = "@techbittu69"
ADMINS = [5385495093]  # <-- replace with your Telegram ID

DOWNLOAD_DIR = "downloads"
AUTO_DELETE_AFTER = 600  # seconds (10 min)

# =========================================
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

bot = AsyncTeleBot(BOT_TOKEN, parse_mode="HTML")

# ================= FLASK ==================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Alive", 200

# ================= UTILS ==================
async def is_joined(user_id):
    try:
        m = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return m.status in ("member", "administrator", "creator")
    except:
        return False

def join_markup():
    m = InlineKeyboardMarkup(row_width=1)
    m.add(
        InlineKeyboardButton(
            "📢 Join Channel",
            url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"
        ),
        InlineKeyboardButton(
            "✅ Joined",
            callback_data="check_join"
        )
    )
    return m

def download_more_markup():
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton("⬇️ Download More", callback_data="download_more"))
    return m

def cleanup():
    now = time.time()
    for f in os.listdir(DOWNLOAD_DIR):
        path = os.path.join(DOWNLOAD_DIR, f)
        if os.path.isfile(path) and now - os.path.getmtime(path) > AUTO_DELETE_AFTER:
            os.remove(path)

def progress_bar(done, total):
    percent = (done / total) * 100 if total else 0
    filled = int(percent // 10)
    return "█" * filled + "░" * (10 - filled) + f" {percent:.1f}%"

# ================= TERABOX =================
async def get_files(url):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://xapiverse.com/api/terabox",
            headers={
                "Content-Type": "application/json",
                "xAPIverse-Key": XAPIVERSE_KEY
            },
            json={"url": url},
            timeout=60
        ) as r:
            data = await r.json()
            return data.get("list", [])

async def download_file(url, path, chat_id, msg_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            total = int(r.headers.get("Content-Length", 0))
            downloaded = 0
            last = time.time()

            with open(path, "wb") as f:
                async for chunk in r.content.iter_chunked(1024 * 1024):
                    f.write(chunk)
                    downloaded += len(chunk)

                    if time.time() - last > 3:
                        bar = progress_bar(downloaded, total)
                        await bot.edit_message_text(
                            f"📥 Downloading...\n{bar}",
                            chat_id,
                            msg_id
                        )
                        last = time.time()

# ================= START ===================
@bot.message_handler(commands=["start"])
async def start(m):
    if not await is_joined(m.from_user.id):
        await bot.send_message(
            m.chat.id,
            "⚠️ <b>Join the channel to use this bot</b>",
            reply_markup=join_markup()
        )
        return

    await bot.send_message(
        m.chat.id,
        "✅ <b>Welcome!</b>\nSend a Terabox link."
    )

# ================= CALLBACKS ===============
@bot.callback_query_handler(func=lambda c: c.data == "check_join")
async def check_join(c):
    if await is_joined(c.from_user.id):
        await bot.edit_message_text(
            "✅ <b>Verified!</b>\nSend a Terabox link.",
            c.message.chat.id,
            c.message.message_id
        )
    else:
        await bot.answer_callback_query(c.id, "❌ Join first!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data == "download_more")
async def download_more(c):
    await bot.answer_callback_query(c.id)
    await bot.send_message(c.message.chat.id, "📥 Send another Terabox link.")

# ================= ADMIN ===================
def admin_only(func):
    async def wrapper(m):
        if m.from_user.id not in ADMINS:
            return
        await func(m)
    return wrapper

@bot.message_handler(commands=["stats"])
@admin_only
async def stats(m):
    await bot.reply_to(
        m,
        f"📊 Files: {len(os.listdir(DOWNLOAD_DIR))}"
    )

# ================= HANDLER =================
@bot.message_handler(func=lambda m: True)
async def handle(m):
    if not await is_joined(m.from_user.id):
        await start(m)
        return

    if "terabox" not in m.text and "1024tera" not in m.text:
        return

    status = await bot.send_message(m.chat.id, "⏳ Fetching files...")
    files = await get_files(m.text)

    if not files:
        await bot.edit_message_text("❌ No files found.", m.chat.id, status.message_id)
        return

    for idx, file in enumerate(files, 1):
        name = file.get("name", f"video_{idx}.mp4")
        url = file.get("download_link")
        path = os.path.join(DOWNLOAD_DIR, name)

        await download_file(url, path, m.chat.id, status.message_id)

        with open(path, "rb") as v:
            await bot.send_video(
                m.chat.id,
                v,
                caption=name,
                reply_markup=download_more_markup(),
                supports_streaming=True
            )

        os.remove(path)
        cleanup()

    await bot.delete_message(m.chat.id, status.message_id)

# ================= RUN =====================
def run_flask():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(bot.infinity_polling())
