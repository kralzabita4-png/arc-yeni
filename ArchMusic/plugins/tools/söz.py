import random
import asyncio
from collections import defaultdict
from pyrogram import filters
from pyrogram.types import Message
from config import BANNED_USERS
from ArchMusic import app

# Grup bazlı iptal listesi
cancel_users = defaultdict(set)

# 50 sözlük
SOZ_LISTESI = [
    "Hayal gücü bilgiden daha önemlidir. – Albert Einstein",
    "İmkansız, sadece tembellerin bahanesidir.",
    "Yavaş git ama asla durma. – Confucius",
    "Başarı, küçük çabaların tekrar edilmesidir. – Robert Collier",
    "Ne olursa olsun, devam et. – Haruki Murakami",
    "Karanlığa küfredeceğine bir mum yak.",
    "En büyük zafer, hiç düşmemek değil; her düştüğünde kalkmaktır. – Nelson Mandela",
    "Zaman, en büyük öğretmendir ama tüm öğrencilerini öldürür.",
    "Güçlü olmak, her zaman kazanmak değil, her zaman devam etmektir.",
    "Her şey seninle başlar.",
    "Yarın, bugünden daha güzel olacak.",
    "Düşüncelerine dikkat et, sözlerin olur.",
    "Sözlerine dikkat et, davranışların olur.",
    "Hayat, cesur olanları sever.",
    "Bugün yapmadığın şey, yarın pişmanlığın olabilir.",
    "Gülümsemek, karşındakine verebileceğin en güzel hediyedir.",
    "Değişim, kendi içinde başlar.",
    "En güzel günler henüz yaşanmadı.",
    "İnsan en çok kendiyle savaşıyor.",
    "Sabır, her şeyin ilacıdır.",
    "Kendine inandığın gün, her şey değişir.",
    "Bir fikir dünyayı değiştirebilir.",
    "Düşüncelerini değiştir, hayatın değişsin.",
    "Hayat kısa, mutlu olmayı unutma.",
    "Küçük adımlar büyük farklar yaratır.",
    "Kendini sevmek, her şeyin başlangıcıdır.",
    "Bugünün işi yarına kalmasın.",
    "Mutluluk bir varış noktası değil, bir yolculuktur.",
    "Ne ekersen, onu biçersin.",
    "Gerçek güç, affedebilme cesaretidir.",
    "Her yeni gün, yeni bir başlangıçtır.",
    "Sessizlik bazen en güçlü cevaptır.",
    "Zor zamanlar, güçlü insanlar yaratır.",
    "İnanç, en karanlık anda bile ışık yakabilir.",
    "Bir adım at, yol görünür.",
    "Hayallerin peşinden gitmekten korkma.",
    "Başarısızlık, başarıya giden yoldur.",
    "Bir gülümseme her şeyi değiştirebilir.",
    "Hatalar, en iyi öğretmendir.",
    "Kalbinle düşün, aklınla hisset.",
    "Gerçek özgürlük, kendin olabilmektir.",
    "Vazgeçmek, her zaman kaybetmek değildir.",
    "Dünya seninle daha güzel.",
    "Fark yaratmak cesaret ister.",
    "İçindeki çocuğu kaybetme.",
    "Zirve, tırmananlar içindir.",
    "Kendine verdiğin sözleri tut.",
    "Yol uzun olsa da yürümeye değerdir.",
    "İyi şeyler zaman alır.",
    "Hayat, seni bekliyor."
]

# /cancel komutu
@app.on_message(filters.command("cancel") & filters.group & ~BANNED_USERS)
async def cancel_soz(client, message: Message):
    cancel_users[message.chat.id].add(message.from_user.id)
    await message.reply("❌ Söz etiketleme işlemi iptal edildi.")

# /soz komutu — adminlere etiketli söz gönder
@app.on_message(filters.command("soz") & filters.group & ~BANNED_USERS)
async def soz_admin_etiket(client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id in cancel_users[chat_id]:
        cancel_users[chat_id].remove(user_id)
        return await message.reply("⛔ Söz gönderimi zaten iptal edilmişti.")

    try:
        admins = await app.get_chat_administrators(chat_id)
    except Exception as e:
        return await message.reply(f"❌ Admin listesi alınamadı: {e}")

    if not admins:
        return await message.reply("❗ Grupta yönetici yok.")

    etiketlenen = 0
    atilamayan = 0

    await message.reply("📜 Sözler gönderiliyor... /cancel yazarsanız işlem durur.")

    for admin in admins:
        if admin.user.is_bot:
            continue

        # Kullanıcı iptal ettiyse durdur
        if user_id in cancel_users[chat_id]:
            cancel_users[chat_id].remove(user_id)
            return await message.reply("🛑 Söz gönderimi durduruldu.")

        soz = random.choice(SOZ_LISTESI)

        try:
            await message.reply(
                f"👤 [{admin.user.first_name}](tg://user?id={admin.user.id})\n\n📜 _{soz}_",
                quote=False
            )
            etiketlenen += 1
        except Exception:
            atilamayan += 1

        await asyncio.sleep(1.5)  # Flood limiti için gecikme

    await message.reply(
        f"✅ **Söz Etiketleme Tamamlandı**\n\n"
        f"📌 Etiketlenen kişi: {etiketlenen}\n"
        f"⛔ Atılamayan: {atilamayan}\n"
        f"🎯 Toplam: {etiketlenen + atilamayan}"
    )
