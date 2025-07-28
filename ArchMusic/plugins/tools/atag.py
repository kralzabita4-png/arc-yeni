from pyrogram import filters
from pyrogram.types import Message
from config import BANNED_USERS
from ArchMusic import app

# Etiketlemeyi iptal eden kullanıcılar için liste
cancel_users = set()

# /cancel komutu — işlemi durdurur
@app.on_message(filters.command("cancel") & filters.group & ~BANNED_USERS)
async def cancel_atag(client, message: Message):
    cancel_users.add(message.from_user.id)
    await message.reply("❌ Etiketleme işlemi iptal edildi.")

# /atag komutu — yöneticileri etiketler
@app.on_message(filters.command("atag") & filters.group & ~BANNED_USERS)
async def atag_command(client, message: Message):
    user_id = message.from_user.id

    if user_id in cancel_users:
        cancel_users.remove(user_id)
        return await message.reply("⛔ Etiketleme işlemi zaten iptal edilmişti.")

    try:
        chat_id = message.chat.id
        admins = await app.get_chat_administrators(chat_id)
    except Exception as e:
        return await message.reply(f"❌ Yöneticiler alınamadı: {str(e)}")

    if not admins:
        return await message.reply("❗ Grupta hiç yönetici bulunamadı.")

    etiketlenen = 0
    etiketlenmeyen = 0

    for admin in admins:
        if admin.user.is_bot:
            continue
        try:
            await message.reply(
                f"👑 [{admin.user.first_name}](tg://user?id={admin.user.id})",
                quote=False
            )
            etiketlenen += 1
        except Exception:
            etiketlenmeyen += 1

    await message.reply(
        f"📊 **Yönetici Etiketleme Sonucu:**\n"
        f"✅ Etiketlenen: {etiketlenen}\n"
        f"❌ Etiketlenemeyen: {etiketlenmeyen}\n"
        f"🏁 İşlem tamamlandı."
    )
