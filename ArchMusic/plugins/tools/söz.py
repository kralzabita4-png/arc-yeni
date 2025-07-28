import random
import asyncio
from collections import defaultdict
from pyrogram import filters
from pyrogram.types import Message
from config import BANNED_USERS
from ArchMusic import app

# Grup bazlı iptal takibi
cancel_users = defaultdict(set)

# Söz listesi
SOZ_LISTESI = [
    "Hayal gücü bilgiden daha önemlidir. – Albert Einstein",
    "İmkansız, sadece tembellerin bahanesidir.",
    "Yavaş git ama asla durma. – Confucius",
    "Başarı, küçük çabaların tekrar edilmesidir.",
    "Ne olursa olsun, devam et.",
    "Karanlığa küfredeceğine bir mum yak.",
    "En büyük zafer, her düştüğünde kalkmaktır.",
    "Zaman en iyi öğretmendir ama öğrencilerini öldürür.",
    "Her şey seninle başlar.",
    "İnsan en çok kendiyle savaşıyor.",
    "Bugün yapmadığın şey, yarın pişmanlığın olabilir.",
    "Hayallerin peşinden gitmekten korkma.",
    "İyi şeyler zaman alır.",
    "Zirve tırmananlar içindir.",
    "Mutluluk bir varış noktası değil, yolculuktur.",
    "Vazgeçmek her zaman kaybetmek değildir.",
    "Gerçek özgürlük kendin olabilmektir.",
    "Gerçek güç affedebilme cesaretidir.",
    "Bir fikir dünyayı değiştirebilir.",
    "Fark yaratmak cesaret ister."
]

# En uygun Pyrogram Client'i bul
def get_real_client(app_obj):
    for attr in ("bot", "client", "userbot", "pyro"):
        real_client = getattr(app_obj, attr, None)
        if real_client:
            return real_client
    return app_obj  # fallback

real_client = get_real_client(app)

# /cancel komutu
@app.on_message(filters.command("cancel") & filters.group & ~BANNED_USERS)
async def cancel_soz(client, message: Message):
    cancel_users[message.chat.id].add(message.from_user.id)
    await message.reply("❌ Etiketleme işlemi iptal edildi.")

# /soz komutu
@app.on_message(filters.command("soz") & filters.group & ~BANNED_USERS)
async def soz_etiketle(client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id in cancel_users[chat_id]:
        cancel_users[chat_id].remove(user_id)
        return await message.reply("⛔ İşlem zaten iptal edilmişti.")

    await message.reply("📨 Sözler gönderiliyor. /cancel yazarsan durur.")

    try:
        admins = await real_client.get_chat_administrators(chat_id)
    except Exception as e:
        return await message.reply(f"⚠️ Admin listesi alınamadı:\n`{e}`")

    etiketlenen = 0
    atilamayan = 0

    for admin in admins:
        if admin.user.is_bot:
            continue

        if user_id in cancel_users[chat_id]:
            cancel_users[chat_id].remove(user_id)
            return await message.reply("🛑 İşlem iptal edildi.")

        soz = random.choice(SOZ_LISTESI)
        try:
            await message.reply(
                f"👤 [{admin.user.first_name}](tg://user?id={admin.user.id})\n\n📝 _{soz}_",
                quote=False
            )
            etiketlenen += 1
        except:
            atilamayan += 1

        await asyncio.sleep(1.5)

    await message.reply(
        f"✅ **Etiketleme Bitti**\n"
        f"👥 Etiketlenen: {etiketlenen}\n"
        f"❌ Atılamayan: {atilamayan}\n"
        f"🎯 Toplam: {etiketlenen + atilamayan}"
    )
