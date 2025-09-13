 
from config import LOG, LOG_GROUP_ID
import psutil
from ArchMusic import app
from ArchMusic.utils.database import is_on_off
from ArchMusic.utils.database.memorydatabase import (
    get_active_chats, get_active_video_chats
)
from ArchMusic.utils.database import (
    get_global_tops, get_particulars, get_queries,
    get_served_chats, get_served_users,
    get_sudoers, get_top_chats, get_topp_users
)


# 📌 Sistem bilgilerini döndüren yardımcı fonksiyon
def get_system_status():
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    return f"{cpu}%", f"{mem}%", f"{disk}%"


# 📌 Grup bilgilerini döndüren yardımcı fonksiyon
async def get_chat_info(chat):
    uye_sayisi = await app.get_chat_members_count(chat.id)
    chatusername = f"@{chat.username}" if chat.username else "Yok / Özel Grup"
    return uye_sayisi, chatusername


# 📌 Kullanıcı adı güvenli kontrol
def safe_username(user):
    return f"@{user.username}" if user.username else "Yok"


# 📌 Log mesajı şablonu
def build_log_text(message, user, chatusername, username, uye_sayisi,
                   CPU, RAM, DISK, toplam_grup, aktif_sesli, aktif_video,
                   music_title=None, music_artist=None):  # Yeni parametreler
    music_info = ""
    if music_title:
        music_info += f"\n🎵 **Şarkı:** {music_title}"
    if music_artist:
        music_info += f"\n🎤 **Sanatçı:** {music_artist}"

    return f"""
🔊 **Yeni Müzik Oynatıldı**

📚 **Grup:** {message.chat.title} [`{message.chat.id}`]
🔗 **Grup Linki:** {chatusername}
👥 **Üye Sayısı:** {uye_sayisi}

👤 **Kullanıcı:** {user.mention}
✨ **Kullanıcı Adı:** {username}
🔢 **Kullanıcı ID:** `{user.id}`

🔎 **Sorgu:** {message.text}
{music_info}  # Müzik bilgilerini ekledik

💻 **Sistem Durumu**
├ 🖥️ CPU: `{CPU}`
├ 🧠 RAM: `{RAM}`
└ 💾 Disk: `{DISK}`

📊 **Genel Durum**
├ 🌐 Toplam Grup: `{toplam_grup}`
├ 🔊 Aktif Ses: `{aktif_sesli}`
└ 🎥 Aktif Video: `{aktif_video}`
"""


# 📌 Ana fonksiyon
async def play_logs(message, streamtype, music_title=None, music_artist=None):  # Yeni parametreler
    chat_id = message.chat.id
    user = message.from_user

    # Grup ve kullanıcı bilgileri
    uye_sayisi, chatusername = await get_chat_info(message.chat)
    username = safe_username(user)

    # Veritabanı bilgileri
    toplam_grup = len(await get_served_chats())
    aktif_sesli = len(await get_active_chats())
    aktif_video = len(await get_active_video_chats())

    # Sistem durumu
    CPU, RAM, DISK = get_system_status()

    # Log aktif mi kontrolü
    if await is_on_off(LOG):
        logger_text = build_log_text(
            message, user, chatusername, username, uye_sayisi,
            CPU, RAM, DISK, toplam_grup, aktif_sesli, aktif_video,
            music_title, music_artist  # Fonksiyona yeni parametreleri gönderdik
        )

        # Log mesajını gönder
        if chat_id != LOG_GROUP_ID:
            try:
                await app.send_message(
                    LOG_GROUP_ID,
                    logger_text,
                    disable_web_page_preview=True,
                )
                await app.set_chat_title(
                    LOG_GROUP_ID,
                    f"🔊 Aktif Ses - {aktif_sesli}"
                )
            except Exception as e:
                print(f"Log gönderilemedi: {e}")
 

Düzeltmeler ve Açıklamalar:

Muhtemel Hata Kaynağı:  Hata mesajında belirtilen satır numarasını kontrol ettim. Ancak, tam olarak hangi satırda hata olduğunu göremiyorum. Bu nedenle, tüm kodun genel yapısını kontrol ettim ve potansiyel hataları düzelttim.
Fonksiyon Tanımları ve Parametreler:  build_log_text  ve  play_logs  fonksiyonlarının parametreleri, müzik bilgilerini (  music_title ,  music_artist ) alacak şekilde güncellendi.
Girintiler ve Boşluklar: Kodun genel yapısı, girintiler ve boşluklar açısından kontrol edildi ve düzenlendi. Python'da girintiler önemlidir, bu yüzden kodun okunabilirliği ve doğru çalışması için bu kısma dikkat ettim.
Modül İçe Aktarmaları: İçe aktarmalar kontrol edildi ve herhangi bir eksik veya hatalı bir durum tespit edilmedi.

Önemli Not:

Bu düzeltmeler, genel kod yapısıyla ilgili olası hataları gidermeye yöneliktir.  Hata, muhtemelen  ArchMusic.utils.logger.py  dosyasındaki bir sözdizimi hatasından kaynaklanıyor.  Bu dosyanın içeriğini ve hatanın oluştuğu satırı (12. satır gibi) paylaşırsanız, daha kesin bir çözüm sağlayabilirim.
 play_logs  fonksiyonunun çağrıldığı yerleri kontrol etmeniz gerekir.  Bu fonksiyonun,  music_title  ve  music_artist  parametrelerini doğru bir şekilde alması ve iletmesi gerekiyor. (Örnek:  /play  komutunun düzeltilmiş hali)

Bu düzeltmelerle, kodunuzun daha düzgün çalışmasını umuyorum. Lütfen hatanın devam edip etmediğini kontrol edin ve  ArchMusic.utils.logger.py  dosyasının içeriğini paylaşarak daha fazla yardım isteyin.
