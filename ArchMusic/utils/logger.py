from config import LOG, LOG_GROUP_ID
import psutil
import time
from datetime import timedelta, datetime
from ArchMusic import app
from ArchMusic.utils.startup import app_start_time
from ArchMusic.utils.database import is_on_off
from ArchMusic.utils.database.memorydatabase import (
    get_active_chats, get_active_video_chats)
from ArchMusic.utils.database import (
    get_global_tops, get_particulars, get_queries,
    get_served_chats, get_served_users,
    get_sudoers, get_top_chats, get_topp_users)



async def play_logs(message, streamtype):
    chat_id = message.chat.id
    user = message.from_user

    # Grup ve sistem bilgileri
    sayı = await app.get_chat_members_count(chat_id)
    toplamgrup = len(await get_served_chats())
    aktifseslisayısı = len(await get_active_chats())
    aktifvideosayısı = len(await get_active_video_chats())
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    CPU = f"{cpu}%"
    RAM = f"{mem}%"
    DISK = f"{disk}%"

    # Grup kullanıcı adı kontrolü
    if message.chat.username:
        chatusername = f"@{message.chat.username}"
    else:
        chatusername = "Gizli Grup"

    # Bot uptime
    uptime_sec = time.time() - app_start_time
    bot_uptime = str(timedelta(seconds=int(uptime_sec)))

    # Sunucu uptime
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    system_uptime = str(datetime.now() - boot_time).split('.')[0]

    # Kullanıcı şehir bilgisi (bio'dan)
    kullanici_bilgi = await app.get_users(user.id)
    kullanici_bio = kullanici_bilgi.bio if hasattr(kullanici_bilgi, 'bio') else "Belirtilmemiş"

    # Mesaj geçmişi sayısı ve ilk sorgu tarihi
    tum_sorgular = await get_queries()
    kullanici_sorgulari = [q for q in tum_sorgular if q.get('user_id') == user.id]
    mesaj_gecmisi_sayisi = len(kullanici_sorgulari)
    if kullanici_sorgulari:
        ilk_sorgu_timestamp = min(q.get('date', time.time()) for q in kullanici_sorgulari)
        ilk_sorgu_tarihi = datetime.fromtimestamp(ilk_sorgu_timestamp).strftime("%Y-%m-%d %H:%M:%S")
    else:
        ilk_sorgu_tarihi = "Bilinmiyor"

    # Grupların kategoriye göre dağılımı (örnek sabit eşleme)
    grup_kategorileri = {
        -1001234567890: "Müzik",
        -1009876543210: "Sohbet",
        # daha fazla grup id ve kategori ekle
    }
    kategori_sayac = {}
    gruplar = await get_served_chats()
    for gid in gruplar:
        kategori = grup_kategorileri.get(gid, "Bilinmiyor")
        kategori_sayac[kategori] = kategori_sayac.get(kategori, 0) + 1

    # Log aktif mi kontrolü
    if await is_on_off(LOG):
        logger_text = f"""
🔊 **Yeni Müzik Oynatıldı**

📚 **Grup:** {message.chat.title} [`{chat_id}`]  
🔗 **Grup Linki:** {chatusername}  
👥 **Üye Sayısı:** {sayı}  

👤 **Kullanıcı:** {user.mention}  
✨ **Kullanıcı Adı:** @{user.username}  
🔢 **Kullanıcı ID:** `{user.id}`  

🔎 **Sorgu:** {message.text}

💻 **Sistem Durumu**
├ 🖥️ CPU: `{CPU}`
├ 🧠 RAM: `{RAM}`
└ 💾 Disk: `{DISK}`

⏱️ **Uptime Bilgisi**
├ 🤖 Bot Çalışma Süresi: `{bot_uptime}`
└ 💻 Sunucu Uptime: `{system_uptime}`

📍 **Kullanıcı Konumu**
└ 🗺️ Profil Biyografi/Şehir: `{kullanici_bio}`

🗂️ **Kullanıcı Detayları**
├ 💬 Toplam Mesaj Sayısı: `{mesaj_gecmisi_sayisi}`
└ 📅 İlk Sorgu Tarihi: `{ilk_sorgu_tarihi}`

📊 **Grupların Kategorilere Göre Dağılımı**
"""
        for kategori, sayi in kategori_sayac.items():
            logger_text += f"├ {kategori}: `{sayi}`\n"

        # Log mesajını gönder
        if chat_id != LOG_GROUP_ID:
            try:
                await app.send_message(
                    LOG_GROUP_ID,
                    logger_text,
                    disable_web_page_preview=True,
                )
                await app.set_chat_title(LOG_GROUP_ID, f"🔊 Aktif Ses - {aktifseslisayısı}")
            except:
                pass
