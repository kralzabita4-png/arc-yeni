from pyrogram import Client, filters
from pyrogram.types import Message, ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus
from config import LOG_GROUP_ID
from ArchMusic import app


async def send_log(text: str, reply_markup=None):
    try:
        await app.send_message(chat_id=LOG_GROUP_ID, text=text, reply_markup=reply_markup)
    except Exception as e:
        print(f"[HATA] Log mesajı gönderilemedi:\n{e}")


# ✅ Yeni kullanıcı veya bot eklendiğinde
@app.on_message(filters.new_chat_members)
async def on_new_member(client: Client, message: Message):
    bot_id = (await client.get_me()).id
    for user in message.new_chat_members:
        ad = message.from_user.first_name if message.from_user else "Bilinmiyor"
        chat = message.chat
        chat_link = f"@{chat.username}" if chat.username else "Yok"

        if user.id == bot_id:
            text = (
                f"<u>#✅ <b>Bot Gruba Eklendi</b></u>\n\n"
                f"👥 <b>Grup:</b> {chat.title}\n"
                f"🆔 <b>Grup ID:</b> `{chat.id}`\n"
                f"🔗 <b>Link:</b> {chat_link}\n"
                f"➕ <b>Ekleyen:</b> {ad}"
            )
        else:
            text = (
                f"<u>#👤 <b>Kullanıcı Eklendi</b></u>\n\n"
                f"🙋 <b>Adı:</b> {user.mention}\n"
                f"🆔 <b>ID:</b> `{user.id}`\n"
                f"👥 <b>Grup:</b> {chat.title}\n"
                f"➕ <b>Ekleyen:</b> {ad}"
            )

        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(ad, user_id=message.from_user.id)]] if message.from_user else []
        )

        await send_log(text, markup)


# ✅ Kullanıcı veya bot ayrıldığında
@app.on_message(filters.left_chat_member)
async def on_left_member(client: Client, message: Message):
    bot_id = (await client.get_me()).id
    user = message.left_chat_member
    ad = message.from_user.first_name if message.from_user else "Bilinmiyor"
    chat = message.chat

    if user.id == bot_id:
        text = (
            f"<u>#🚫 <b>Bot Gruptan Atıldı</b></u>\n\n"
            f"👥 <b>Grup:</b> {chat.title}\n"
            f"🆔 <b>Grup ID:</b> `{chat.id}`\n"
            f"❌ <b>Atan:</b> {ad}"
        )
    else:
        text = (
            f"<u>#🚷 <b>Kullanıcı Ayrıldı/Atıldı</b></u>\n\n"
            f"🙋 <b>Adı:</b> {user.mention}\n"
            f"🆔 <b>ID:</b> `{user.id}`\n"
            f"👥 <b>Grup:</b> {chat.title}\n"
            f"❌ <b>Çıkaran:</b> {ad}"
        )

    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(ad, user_id=message.from_user.id)]] if message.from_user else []
    )

    await send_log(text, markup)


# ✅ Yetki değişiklikleri, ban/ban kaldırma
@app.on_chat_member_updated
async def on_chat_member_update(client: Client, update: ChatMemberUpdated):
    old = update.old_chat_member
    new = update.new_chat_member
    user = new.user
    chat = update.chat

    if not user:
        return  # Güvenlik: kullanıcı boş gelirse işlem yapma

    try:
        user_name = user.mention or f"{user.first_name} (`{user.id}`)"
    except:
        user_name = f"ID: `{user.id}`"

    if old.status != new.status:
        if new.status == ChatMemberStatus.ADMINISTRATOR:
            text = (
                f"<u>#🛡️ <b>Yönetici Yapıldı</b></u>\n\n"
                f"🙋 <b>Kullanıcı:</b> {user_name}\n"
                f"🆔 <b>ID:</b> `{user.id}`\n"
                f"👥 <b>Grup:</b> {chat.title}\n"
                f"🆔 <b>Grup ID:</b> `{chat.id}`"
            )
        elif old.status == ChatMemberStatus.ADMINISTRATOR and new.status == ChatMemberStatus.MEMBER:
            text = (
                f"<u>#⚠️ <b>Yetkiler Alındı</b></u>\n\n"
                f"🙋 <b>Kullanıcı:</b> {user_name}\n"
                f"🆔 <b>ID:</b> `{user.id}`\n"
                f"👥 <b>Grup:</b> {chat.title}\n"
                f"🆔 <b>Grup ID:</b> `{chat.id}`"
            )
        elif new.status == ChatMemberStatus.BANNED:
            text = (
                f"<u>#⛔️ <b>Kullanıcı Banlandı</b></u>\n\n"
                f"🙋 <b>Kullanıcı:</b> {user_name}\n"
                f"🆔 <b>ID:</b> `{user.id}`\n"
                f"👥 <b>Grup:</b> {chat.title}\n"
                f"🆔 <b>Grup ID:</b> `{chat.id}`"
            )
        elif old.status == ChatMemberStatus.BANNED and new.status == ChatMemberStatus.MEMBER:
            text = (
                f"<u>#🔓 <b>Ban Kaldırıldı</b></u>\n\n"
                f"🙋 <b>Kullanıcı:</b> {user_name}\n"
                f"🆔 <b>ID:</b> `{user.id}`\n"
                f"👥 <b>Grup:</b> {chat.title}\n"
                f"🆔 <b>Grup ID:</b> `{chat.id}`"
            )
        elif new.status == ChatMemberStatus.LEFT:
            text = (
                f"<u>#🚪 <b>Kullanıcı Ayrıldı</b></u>\n\n"
                f"🙋 <b>Kullanıcı:</b> {user_name}\n"
                f"🆔 <b>ID:</b> `{user.id}`\n"
                f"👥 <b>Grup:</b> {chat.title}\n"
                f"🆔 <b>Grup ID:</b> `{chat.id}`"
            )
        else:
            return

        await send_log(text)
