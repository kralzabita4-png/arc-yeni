import asyncio
from collections import defaultdict
from pyrogram import filters
from pyrogram.types import Message
from config import BANNED_USERS
from ArchMusic import app

# Kullanıcı bazlı iptal takip sistemi
cancel_atag = defaultdict(set)

# /cancel komutu — Etiketleme iptali
@app.on_message(filters.command("cancel") & filters.group & ~BANNED_USERS)
async def cancel_atag_command(client, message: Message):
    cancel_atag[message.chat.id].add(message.from_user.id)
    await message.reply("❌ Etiketleme işlemi iptal edildi.")

# /atag komutu — Yöneticileri etiketleme
@app.on_message(filters.command("atag") & filters.group & ~BANNED_USERS)
async def atag_command(client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id in cancel_atag[chat_id]:
        cancel_atag[chat_id].remove(user_id)
        return await message.reply("⛔ İşlem zaten iptal edilmişti.")

    await message.reply("📨 Yöneticiler etiketleniyor... /cancel yazarak durdurabilirsin.")

    try:
        admins = await app.get_chat_members(chat_id, filter="administrators")
    except Exception as e:
        return await message.reply(f"⚠️ Yöneticiler alınamadı:\n`{e}`")

    etiketlenen = 0
    atilamayan = 0

    async for admin in admins:
        if admin.user.is_bot:
            continue

        if user_id in cancel_atag[chat_id]:
            cancel_atag[chat_id].remove(user_id)
            return await message.reply("🛑 Etiketleme işlemi iptal edildi.")

        try:
            await message.reply(
                f"👑 [{admin.user.first_name}](tg://user?id={admin.user.id})",
                quote=False
            )
            etiketlenen += 1
        except:
            atilamayan += 1

        await asyncio.sleep(1.5)  # Spam koruması

    await message.reply(
        f"✅ **Etiketleme Bitti**\n"
        f"👥 Etiketlenen: {etiketlenen}\n"
        f"❌ Atılamayan: {atilamayan}\n"
        f"🎯 Toplam: {etiketlenen + atilamayan}"
    )
