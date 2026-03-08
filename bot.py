import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import *
from database import *
from utils import generate_code

bot = Client(
    "fileshare",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

upload_sessions = {}

# START
@bot.on_message(filters.command("start"))
async def start(client, message):

    add_user(message.from_user.id)

    args = message.text.split()

    if len(args) > 1:
        code = args[1]
        files = get_files(code)

        if not files:
            return await message.reply_text("❌ File tidak ditemukan")

        for f in files:
            await message.copy(message.chat.id, f[0])

        return

    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📤 Upload File", callback_data="upload")]
        ]
    )

    await message.reply_text(
        "Selamat datang di File Share Bot",
        reply_markup=buttons
    )


# FORCE JOIN
async def check_join(client, user_id):

    try:
        await client.get_chat_member(FORCE_CHANNEL, user_id)
        return True
    except:
        return False


# UPLOAD BUTTON
@bot.on_callback_query(filters.regex("upload"))
async def upload_btn(client, query):

    upload_sessions[query.from_user.id] = []

    await query.message.reply_text(
        "📤 Kirim semua video yang ingin dijadikan 1 link\n\n"
        "Jika sudah kirim /done"
    )


# RECEIVE VIDEO
@bot.on_message(filters.video | filters.document)
async def receive_file(client, message):

    uid = message.from_user.id

    if uid not in upload_sessions:
        return

    msg = await message.reply_text("⬆️ Uploading...")

    sent = await message.copy(STORAGE_CHANNEL)

    upload_sessions[uid].append(sent.id)

    await msg.edit_text("✅ File tersimpan")


# DONE
@bot.on_message(filters.command("done"))
async def done(client, message):

    uid = message.from_user.id

    if uid not in upload_sessions:
        return

    files = upload_sessions[uid]

    if not files:
        return await message.reply_text("❌ Tidak ada file")

    code = generate_code()

    for file_id in files:
        save_file(code, file_id)

    link = f"https://t.me/{(await bot.get_me()).username}?start={code}"

    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📥 Get File", url=link)]
        ]
    )

    await message.reply_text(
        f"✅ Link berhasil dibuat\n\n"
        f"🔗 {link}\n"
        f"📌 Code: `{code}`",
        reply_markup=buttons
    )

    del upload_sessions[uid]


# BROADCAST
@bot.on_message(filters.command("broadcast") & filters.user(ADMIN_ID))
async def broadcast(client, message):

    if not message.reply_to_message:
        return await message.reply_text("Reply pesan untuk broadcast")

    users = get_users()

    success = 0
    failed = 0

    msg = await message.reply_text("🚀 Broadcasting...")

    for u in users:

        try:
            await message.reply_to_message.copy(u[0])
            success += 1
        except:
            failed += 1

        await asyncio.sleep(0.05)

    await msg.edit_text(
        f"✅ Broadcast selesai\n\n"
        f"Berhasil: {success}\n"
        f"Gagal: {failed}"
    )


bot.run()
