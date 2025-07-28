import asyncio
import random
from pyrogram import filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

from config import BANNED_USERS
from ArchMusic import app

otag_sessions = {}

KARTLAR = [
    "🂡 Maça Ası", "🂱 Karo Ası", "🂭 Maça Kızı", "🃍 Kupa Kralı", "🂾 Maça Valesi",
    "🂩 Maça 10", "🃋 Kupa Kızı", "🃎 Kupa Valesi", "🃁 Kupa Ası", "🃑 Sinek Ası",
    "🃘 Sinek 9", "🃙 Sinek 10", "🃚 Sinek Vale", "🃛 Sinek Kız", "🃝 Sinek Kral",
    "🃎 Karo Valesi", "🃍 Karo Kralı", "🂽 Maça Kız", "🂾 Maça Vale", "🃞 Karo Kralı"
]

@app.on_message(filters.command("otag") & filters.group & ~BANNED_USERS)
async def otag_command(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    replied_user = None

    if len(message.command) > 1:
        if message.entities:
            for entity in message.entities:
                if entity.type in ["mention", "text_mention"]:
                    try:
                        replied_user = await client.get_users(message.text.split()[1])
                    except:
                        return await message.reply("Kullanıcı bulunamadı.")

    if replied_user:
        kart = random.choice(KARTLAR)
        return await message.reply(f"{kart} [{replied_user.first_name}](tg://user?id={replied_user.id})")

    members = []
    async for member in client.get_chat_members(chat_id):
        if member.user.is_bot:
            continue
        members.append(member.user)

    if not members:
        return await message.reply_text("Etiketlenecek kullanıcı bulunamadı.")

    otag_sessions[chat_id] = {
        "active": True,
        "last": None,
        "members": members,
        "from": user_id
    }

    await message.reply(
        f"🎴 **İskambil Etiketi Başlatılsın mı?**\n\n"
        f"👤 Başlatan: [{message.from_user.first_name}](tg://user?id={user_id})\n"
        f"📦 Kişi sayısı: {len(members)}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Başla", callback_data=f"start_otag:{user_id}"),
                InlineKeyboardButton("🛑 İptal", callback_data=f"cancel_otag:{user_id}")
            ]
        ])
    )

@app.on_callback_query(filters.regex(r"start_otag:(\d+)"))
async def start_otag(client, cq: CallbackQuery):
    uid = int(cq.matches[0].group(1))
    chat_id = cq.message.chat.id

    if cq.from_user.id != uid:
        return await cq.answer("Bu işlem sadece başlatan kişiye ait.", show_alert=True)

    session = otag_sessions.get(chat_id)
    if not session:
        return await cq.answer("Etiket oturumu bulunamadı.", show_alert=True)

    await cq.message.edit_text("🃏 Etiketleme başlatıldı. Durdurmak için: /cancel_otag")

    tagged, failed = 0, 0
    delay = 1.5
    chunk = 5
    members = session["members"]
    chunks = [members[i:i + chunk] for i in range(0, len(members), chunk)]

    for group in chunks:
        if not otag_sessions.get(chat_id, {}).get("active"):
            break
        try:
            tags = "\n".join(
                f"{random.choice(KARTLAR)} [{u.first_name}](tg://user?id={u.id})" for u in group
            )
            await client.send_message(
                chat_id=chat_id,
                text=f"{tags}\n\n🃏 Oyun devam ediyor...",
                reply_to_message_id=cq.message.id
            )
            await asyncio.sleep(delay)
            session["last"] = group[-1]
            tagged += len(group)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except:
            failed += len(group)

    last_user = session.get("last")
    name = f"[{last_user.first_name}](tg://user?id={last_user.id})" if last_user else "Yok"
    otag_sessions.pop(chat_id, None)

    await client.send_message(
        chat_id,
        f"✅ Etiketleme tamamlandı.\n"
        f"📌 Etiketlenen: {tagged}\n"
        f"❌ Başarısız: {failed}\n"
        f"🔚 Son etiketlenen: {name}"
    )

@app.on_callback_query(filters.regex(r"cancel_otag:(\d+)"))
async def cancel_otag(client, cq: CallbackQuery):
    uid = int(cq.matches[0].group(1))
    if cq.from_user.id != uid:
        return await cq.answer("Sadece başlatan iptal edebilir.", show_alert=True)

    chat_id = cq.message.chat.id
    otag_sessions.pop(chat_id, None)
    await cq.message.edit_text("🛑 Etiketleme iptal edildi.")

@app.on_message(filters.command("cancel_otag") & filters.group & ~BANNED_USERS)
async def cancel_otag_cmd(client, message: Message):
    chat_id = message.chat.id
    session = otag_sessions.get(chat_id)

    if not session:
        return await message.reply_text("🔍 Aktif bir etiketleme oturumu yok.")

    if message.from_user.id != session["from"]:
        return await message.reply_text("⛔ Sadece başlatan kullanıcı durdurabilir.")

    otag_sessions[chat_id]["active"] = False
    last_user = session.get("last")
    name = f"[{last_user.first_name}](tg://user?id={last_user.id})" if last_user else "Yok"
    await message.reply(
        f"🛑 Etiketleme durduruldu.\n"
        f"🔚 Son etiketlenen: {name}"
    )
