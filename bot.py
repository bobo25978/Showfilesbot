import uuid
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

from config import *
from database import *

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

user_uploads = {}

async def is_joined(user_id):

    member = await bot.get_chat_member(FORCE_GROUP, user_id)

    if member.status in ["member","administrator","creator"]:
        return True

    return False


def join_keyboard():
    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton(
            "Join Group",
            url=f"https://t.me/{FORCE_GROUP.replace('@','')}"
        )
    )

    kb.add(
        InlineKeyboardButton(
            "Verify Join",
            callback_data="verify"
        )
    )

    return kb


@dp.message_handler(commands=['start'])
async def start(msg: types.Message):

    user_id = msg.from_user.id

    users.update_one(
        {"user_id":user_id},
        {"$set":{"user_id":user_id}},
        upsert=True
    )

    args = msg.get_args()

    if not await is_joined(user_id):
        await msg.answer(
            "Join group dulu untuk menggunakan bot",
            reply_markup=join_keyboard()
        )
        return

    if args:

        link = links.find_one({"code":args})

        if not link:
            await msg.answer("Link tidak valid")
            return

        files_list = link["files"]

        await send_files(msg.chat.id, files_list, 0)

        return

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton("Upload",callback_data="upload"),
        InlineKeyboardButton("Create Link",callback_data="create")
    )

    await msg.answer(
        "Welcome to File Store Bot",
        reply_markup=kb
    )


@dp.callback_query_handler(lambda c: c.data=="verify")
async def verify(call: types.CallbackQuery):

    if await is_joined(call.from_user.id):

        await call.message.edit_text(
            "Verified! sekarang kamu bisa menggunakan bot"
        )

    else:

        await call.answer(
            "Kamu belum join group",
            show_alert=True
        )


@dp.callback_query_handler(lambda c: c.data=="upload")
async def upload(call: types.CallbackQuery):

    user_uploads[call.from_user.id] = []

    await call.message.answer(
        "Silahkan upload file / video"
    )


@dp.message_handler(content_types=['video','document','photo'])
async def save_file(msg: types.Message):

    user_id = msg.from_user.id

    if user_id not in user_uploads:
        return

    sent = await msg.copy_to(DATABASE_CHANNEL)

    user_uploads[user_id].append(sent.message_id)

    await msg.reply(
        f"File disimpan ({len(user_uploads[user_id])})"
    )


@dp.callback_query_handler(lambda c: c.data=="create")
async def create(call: types.CallbackQuery):

    user_id = call.from_user.id

    files_list = user_uploads.get(user_id)

    if not files_list:
        await call.answer("Upload file dulu")
        return

    code = str(uuid.uuid4())[:8]

    links.insert_one({
        "code":code,
        "files":files_list
    })

    link = f"https://t.me/{(await bot.get_me()).username}?start={code}"

    await call.message.answer(
        f"Link kamu:\n{link}"
    )


async def send_files(chat_id, files_list, page):

    per_page = 10

    start = page * per_page

    end = start + per_page

    current = files_list[start:end]

    for msg_id in current:

        await bot.copy_message(
            chat_id,
            DATABASE_CHANNEL,
            msg_id
        )

    total_pages = (len(files_list)-1)//per_page

    kb = InlineKeyboardMarkup()

    if page>0:
        kb.insert(
            InlineKeyboardButton(
                "Prev",
                callback_data=f"page_{page-1}"
            )
        )

    if page<total_pages:
        kb.insert(
            InlineKeyboardButton(
                "Next",
                callback_data=f"page_{page+1}"
            )
        )

    kb.add(
        InlineKeyboardButton(
            "Join Group",
            url=f"https://t.me/{FORCE_GROUP.replace('@','')}"
        )
    )

    await bot.send_message(
        chat_id,
        f"Page {page+1}/{total_pages+1}",
        reply_markup=kb
    )


@dp.message_handler(commands=['broadcast'])
async def broadcast(msg: types.Message):

    if msg.from_user.id != ADMIN_ID:
        return

    text = msg.get_args()

    for u in users.find():

        try:

            await bot.send_message(
                u["user_id"],
                text
            )

        except:
            pass

    await msg.answer("Broadcast sent")


if __name__ == "__main__":
    executor.start_polling(dp)
