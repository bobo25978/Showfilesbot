from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import string
import sqlite3
import asyncio

from config import *

app = Client(
    "videostorebot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# DATABASE
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# CREATE TABLE (FIX ERROR)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS videos(
    code TEXT,
    file_id TEXT
)
""")

conn.commit()


def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


async def check_join(user_id):
    try:
        member = await app.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


def join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_CHANNEL}")],
        [InlineKeyboardButton("✅ Verify", callback_data="verify")]
    ])


@app.on_message(filters.command("start"))
async def start(client, message):

    user_id = message.from_user.id

    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)",(user_id,))
    conn.commit()

    if len(message.command) > 1:

        code = message.command[1]

        if not await check_join(user_id):

            await message.reply_text(
                "⚠️ Untuk mendapatkan video\nSilahkan join channel dulu",
                reply_markup=join_keyboard()
            )
            return

        cursor.execute("SELECT file_id FROM videos WHERE code=?",(code,))
        data = cursor.fetchone()

        if data:
            await message.reply_video(data[0])

    else:

        await message.reply_text(
            "🤖 Kirim CODE video untuk mendapatkan file"
        )


@app.on_callback_query(filters.regex("verify"))
async def verify(client, callback):

    user_id = callback.from_user.id

    if await check_join(user_id):

        await callback.message.edit_text(
            "✅ Verifikasi berhasil\nSilahkan kirim CODE video"
        )

    else:

        await callback.answer(
            "❌ Kamu belum join channel",
            show_alert=True
        )


@app.on_message(filters.video & filters.user(ADMIN_ID))
async def upload_video(client, message):

    progress_msg = await message.reply_text("⬆️ Upload dimulai...")

    video = message.video
    size = video.file_size / (1024*1024)

    sent = await message.copy(STORAGE_CHANNEL)

    code = generate_code()

    cursor.execute(
        "INSERT INTO videos VALUES (?,?)",
        (code, sent.video.file_id)
    )

    conn.commit()

    link = f"https://t.me/{(await app.get_me()).username}?start={code}"

    await progress_msg.edit_text(

        f"✅ Upload selesai\n\n"
        f"📦 Size : {size:.2f} MB\n"
        f"🧾 CODE : `{code}`\n"
        f"🔗 LINK : {link}"
    )


@app.on_message(filters.text)
async def get_by_code(client, message):

    code = message.text.strip()

    cursor.execute("SELECT file_id FROM videos WHERE code=?",(code,))
    data = cursor.fetchone()

    if not data:
        return

    if not await check_join(message.from_user.id):

        await message.reply_text(
            "⚠️ Join channel dulu",
            reply_markup=join_keyboard()
        )
        return

    await message.reply_video(data[0])


@app.on_message(filters.command("broadcast") & filters.user(ADMIN_ID))
async def broadcast(client, message):

    if len(message.command) < 2:
        return await message.reply_text("Gunakan: /broadcast pesan")

    text = message.text.split(None,1)[1]

    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    success = 0

    for user in users:
        try:
            await app.send_message(user[0], text)
            success += 1
        except:
            pass

    await message.reply_text(
        f"📢 Broadcast selesai\nTerkirim ke {success} user"
    )


app.run()
