import random
import string

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant

from config import *
from database import *

app = Client(
    "filesharebot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


# ================= GENERATE KEY =================

def gen_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))


# ================= CEK JOIN =================

async def check_join(user_id):
    try:
        await app.get_chat_member(FORCE_CHANNEL, user_id)
        return True
    except UserNotParticipant:
        return False
    except:
        return False


# ================= START =================

@app.on_message(filters.command("start"))
async def start(client, message):

    args = message.text.split()

    if len(args) == 1:
        await message.reply_text(
            "📦 Kirim video / file ke bot untuk mendapatkan link download."
        )
        return

    key = args[1]

    joined = await check_join(message.from_user.id)

    if not joined:

        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_CHANNEL.replace('@','')}")],
            [InlineKeyboardButton("✅ Saya Sudah Join", callback_data=f"check {key}")]
        ])

        await message.reply_text(
            "⚠️ Kamu harus join channel dulu.",
            reply_markup=btn
        )
        return

    data = get_file(key)

    if not data:
        await message.reply_text("❌ File tidak ditemukan.")
        return

    msg_id = data[0]

    await client.copy_message(
        chat_id=message.chat.id,
        from_chat_id=STORAGE_CHANNEL,
        message_id=msg_id
    )


# ================= UPLOAD FILE =================

@app.on_message(filters.video | filters.document)
async def upload(client, message):

    sent = await message.copy(STORAGE_CHANNEL)

    key = gen_key()

    save_file(key, sent.id)

    link = f"https://t.me/{(await app.get_me()).username}?start={key}"

    await message.reply_text(
        f"✅ File berhasil disimpan!\n\n🔗 Link:\n{link}"
    )


# ================= CEK JOIN BUTTON =================

@app.on_callback_query(filters.regex("check"))
async def check_button(client, query):

    key = query.data.split()[1]

    joined = await check_join(query.from_user.id)

    if not joined:
        await query.answer("❌ Kamu belum join!", show_alert=True)
        return

    data = get_file(key)

    if not data:
        await query.message.edit_text("❌ File tidak ditemukan.")
        return

    await client.copy_message(
        chat_id=query.message.chat.id,
        from_chat_id=STORAGE_CHANNEL,
        message_id=data[0]
    )

    await query.message.delete()


print("Bot Running...")
app.run()
