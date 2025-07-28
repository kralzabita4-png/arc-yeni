# group_events.py

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import LOG_GROUP_ID
from ArchMusic import app  # Eğer botun ana app'i başka yerde tanımlıysa burayı değiştir.

async def new_message(chat_id: int, message: str, reply_markup=None):
    await app.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)

@app.on_message(filters.new_chat_members)
async def on_new_chat_members(client: Client, message: Message):
    bot_id = (await client.get_me()).id
    new_members = message.new_chat_members

    if any(user.id == bot_id for user in new_members):
        added_by = message.from_user.first_name if message.from_user else "Bilinmiyor"
        chatusername = f"@{message.chat.username}" if message.chat.username else "Yok"
        title = message.chat.title
        chat_id = message.chat.id

        text = (
            f"<u>#**Yeni Gruba Eklendi**</u> :\n\n"
            f"**Grup ID:** `{chat_id}`\n"
            f"**Grup Adı:** {title}\n"
            f"**Grup Link:** {chatusername}\n"
            f"**Gruba Ekleyen:** {added_by}"
        )

        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        added_by, user_id=message.from_user.id if message.from_user else 0
                    )
                ]
            ]
        )

        await new_message(LOG_GROUP_ID, text, reply_markup)

@app.on_message(filters.left_chat_member)
async def on_left_chat_member(client: Client, message: Message):
    bot_id = (await client.get_me()).id

    if message.left_chat_member.id == bot_id:
        title = message.chat.title
        chat_id = message.chat.id

        if message.from_user:
            removed_by = message.from_user.first_name
            user_id = message.from_user.id
        else:
            removed_by = "Bilinmiyor (grup silinmiş olabilir)"
            user_id = None

        text = (
            f"<u>#**Gruptan Çıkarıldı**</u> :\n\n"
            f"**Grup ID:** `{chat_id}`\n"
            f"**Grup Adı:** {title}\n"
            f"**Gruptan Çıkaran:** {removed_by}"
        )

        reply_markup = (
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(removed_by, user_id=user_id)]]
            ) if user_id else None
        )

        await new_message(LOG_GROUP_ID, text, reply_markup)
