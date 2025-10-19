import asyncio
from collections import deque
from pyrogram import filters, types
from pyrogram.enums import ParseMode
from ArchMusic import app
import speedtest
import time

# Komutlar
HIZ_TESTI_KOMUTLARI = ["speedtest", "hiztesti"]
HIZ_DURUM_KOMUTLARI = ["hizdurum", "speedstatus"]

# Kuyruk ve geçmiş sistemleri
test_kuyrugu = deque()
test_lock = asyncio.Lock()
gecmis_sonuclar = deque(maxlen=5)  # Son 5 testi sakla

# Tahmini test süresi
TAHMINI_SURE = 25


# 🔹 Hız testi fonksiyonu
async def hiz_testi_dinamik(m):
    test = speedtest.Speedtest()
    await m.edit("🔍 En iyi sunucu aranıyor...")
    await asyncio.to_thread(test.get_best_server)

    await m.edit("📥 İndirme hızı ölçülüyor...")
    await asyncio.to_thread(test.download)

    await m.edit("📤 Yükleme hızı ölçülüyor...")
    await asyncio.to_thread(test.upload)

    await m.edit("📡 Sonuçlar paylaşılıyor...")
    await asyncio.to_thread(test.results.share)
    return test.results.dict()


# 🔹 Emoji grafik fonksiyonu (renksiz)
def hiz_grafik_otomatik(indir, yukle, bar_length=20):
    max_speed = max(indir, yukle, 1)
    indir_bar = "▰" * int((indir/max_speed)*bar_length) + "▱" * (bar_length - int((indir/max_speed)*bar_length))
    yukle_bar = "▰" * int((yukle/max_speed)*bar_length) + "▱" * (bar_length - int((yukle/max_speed)*bar_length))
    return indir_bar, yukle_bar


# 🔹 Komut: Hız testi başlat
@app.on_message(filters.command(HIZ_TESTI_KOMUTLARI))
async def speedtest_start(client, mesaj):
    button = types.InlineKeyboardMarkup(
        [[types.InlineKeyboardButton("🚀 Hız Testini Başlat", callback_data="start_speedtest")]]
    )
    await mesaj.reply_text(
        "📶 Hız testi yapmak için aşağıdaki butona tıklayın:",
        reply_markup=button
    )


# 🔹 Callback: Kuyruklu hız testi
@app.on_callback_query(filters.regex("start_speedtest"))
async def speedtest_callback(client, callback_query):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.first_name
    m = callback_query.message

    # Kuyruğa ekle
    test_kuyrugu.append((user_id, callback_query))
    sira_no = len(test_kuyrugu)

    if sira_no > 1:
        await callback_query.answer(
            f"⏳ {sira_no - 1} kişi sırada. Tahmini bekleme ≈ {(sira_no - 1) * TAHMINI_SURE} sn.",
            show_alert=True
        )
    else:
        await callback_query.answer("🚀 Test başlatılıyor...", show_alert=False)

    async with test_lock:
        while test_kuyrugu:
            current_user, current_callback = test_kuyrugu[0]
            if current_user != user_id:
                await callback_query.answer("⌛ Sıranı bekliyorsun...", show_alert=True)
                return

            m_edit = await current_callback.message.edit_text(f"🔁 {username} için hız testi başlatılıyor...")

            try:
                sonuc = await hiz_testi_dinamik(m_edit)
            except Exception as e:
                await m_edit.edit(f"⚠ Hata: {e}")
                test_kuyrugu.popleft()
                return

            indir_mbps = round(sonuc['download'] / 10**6, 2)
            yukle_mbps = round(sonuc['upload'] / 10**6, 2)
            ping_ms = round(sonuc['ping'], 2)
            indir_grafik, yukle_grafik = hiz_grafik_otomatik(indir_mbps, yukle_mbps)

            client_lat = sonuc['client']['lat']
            client_lon = sonuc['client']['lon']
            server_lat = sonuc['server']['lat']
            server_lon = sonuc['server']['lon']

            client_map = f"https://www.google.com/maps/search/?api=1&query={client_lat},{client_lon}"
            server_map = f"https://www.google.com/maps/search/?api=1&query={server_lat},{server_lon}"

            cikti = f"""📊 <b>Hız Testi Sonuçları</b>

👤 <b>Kullanıcı:</b> {username}
🌐 <b>ISP:</b> {sonuc['client']['isp']}
🏳️ <b>Ülke:</b> {sonuc['client']['country']}
📍 <a href="{client_map}">Müşteri Konumu</a>

🖥️ <b>Sunucu:</b> {sonuc['server']['name']}
🌍 <b>Ülke:</b> {sonuc['server']['country']}, {sonuc['server']['cc']}
⚙️ <b>Sponsor:</b> {sonuc['server']['sponsor']}
🏓 <b>Ping:</b> {ping_ms} ms
📡 <a href="{server_map}">Sunucu Konumu</a>

📥 <b>İndirme:</b> {indir_mbps} Mbps
{indir_grafik}
📤 <b>Yükleme:</b> {yukle_mbps} Mbps
{yukle_grafik}
"""

            share_url = sonuc.get("share")

            if share_url:
                await m.reply_photo(share_url, caption=cikti, parse_mode=ParseMode.HTML)
            else:
                await m.reply_text(cikti, parse_mode=ParseMode.HTML)

            # Sonuç geçmişine ekle
            gecmis_sonuclar.append({
                "user": username,
                "indir": indir_mbps,
                "yukle": yukle_mbps,
                "ping": ping_ms,
                "zaman": time.strftime("%H:%M:%S")
            })

            await m_edit.delete()
            test_kuyrugu.popleft()


# 🔹 Komut: Kuyruk ve geçmiş durumu
@app.on_message(filters.command(HIZ_DURUM_KOMUTLARI))
async def hizdurum(client, mesaj):
    if not test_kuyrugu and not gecmis_sonuclar:
        await mesaj.reply_text("📭 Şu anda aktif hız testi yok ve geçmiş boş.")
        return

    durum = "<b>📡 Hız Testi Durumu</b>\n\n"

    if test_kuyrugu:
        durum += "🕒 <b>Aktif Kuyruk:</b>\n"
        for i, (uid, cb) in enumerate(test_kuyrugu, 1):
            durum += f"{i}. {cb.from_user.first_name}\n"
    else:
        durum += "✅ Aktif test yok.\n"

    if gecmis_sonuclar:
        durum += "\n<b>📜 Son 5 Hız Testi:</b>\n"
        for s in list(gecmis_sonuclar)[::-1]:
            durum += f"• {s['user']} ({s['zaman']}) → {s['indir']}⬇ / {s['yukle']}⬆ Mbps | {s['ping']} ms\n"

    await mesaj.reply_text(durum, parse_mode=ParseMode.HTML)
