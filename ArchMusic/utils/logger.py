from config import LOG, LOG_GROUP_ID
import psutil
import time
import datetime
from ArchMusic import app
from ArchMusic.utils.database import is_on_off
from ArchMusic.utils.database.memorydatabase import (
    get_active_chats, get_active_video_chats)
from ArchMusic.utils.database import (
    get_global_tops, get_particulars, get_queries,
    get_served_chats, get_served_users,
    get_sudoers, get_top_chats, get_topp_users)


START_TIME = time.time()  # Botun başlama zamanı


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
    disk = psutil.disk_usage("/")
    disk_percent = disk.percent
    disk_free = round(disk.free / (1024 ** 3), 2)  # GB olarak boş alan

    CPU = f"{cpu}%"
    RAM = f"{mem}%"
    DISK = f"{disk_percent}%"

    # Grup kullanıcı adı kontrolü
    if message.chat.username:
        chatusername = f"@{message.chat.username}"
    else:
        chatusername = "Gizli Grup"

    # Bot uptime hesaplama
    uptime_seconds = int(time.time() - START_TIME)
    uptime_str = str(datetime.timedelta(seconds=uptime_seconds))

    # Aktif grup sayısı ve toplam kullanıcı sayısı
    aktif_grup_sayisi = len(await get_active_chats())
    toplam_kullanıcı_sayısı = len(await get_served_users())

    # Bu grup aktif sesli mi kontrolü (örnek)
    aktif_sesli_grup_mu = chat_id in await get_active_chats()
    aktif_sesli_grup_mu_text = "Evet" if aktif_sesli_grup_mu else "Hayır"

    # Log aktif mi kontrolü
    if await is_on_off(LOG):
        logger_text = f"""
🔊 **Yeni Müzik Oynatıldı**

📚 **Grup:** {message.chat.title} [`{chat_id}`]  
🔗 **Grup Linki:** {chatusername}  
👥 **Üye Sayısı:** {sayı}  
📍 **Bu Grup Aktif Sesli mi?:** {aktif_sesli_grup_mu_text}

👤 **Kullanıcı:** {user.mention}  
✨ **Kullanıcı Adı:** @{user.username}  
🔢 **Kullanıcı ID:** `{user.id}`  

🔎 **Sorgu:** {message.text}

💻 **Sistem Durumu**
├ 🖥️ CPU: `{CPU}`
├ 🧠 RAM: `{RAM}`
├ 💾 Disk Kullanımı: `{DISK}`
├ ⏱️ Bot Uptime: `{uptime_str}`
└ 💽 Boş Disk Alanı: `{disk_free} GB`

📊 **Genel Durum**
├ ⚡️ Aktif Grup Sayısı: `{aktif_grup_sayisi}`
├ 👥 Toplam Kullanıcı (tüm gruplar): `{toplam_kullanıcı_sayısı}`
├ 🌐 Toplam Grup: `{toplamgrup}`
├ 🔊 Aktif Ses: `{aktifseslisayısı}`
└ 🎥 Aktif Video: `{aktifvideosayısı}`
"""
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
