from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import filters
from ArchMusic.utils.database import get_queue, get_song_duration, get_playmode, get_playtype, set_playmode, set_playtype
from ArchMusic import app, YouTube
from config import PLAYLIST_IMG_URL, PRIVATE_BOT_MODE, adminlist
from strings import get_string
from ArchMusic.utils.database import get_cmode, get_lang, is_active_chat, is_commanddelete_on, is_served_private_chat
from ArchMusic.misc import SUDOERS
from ArchMusic.utils.inline.playlist import botplaylist_markup

def PlayWrapper(command):
    async def wrapper(client, message):
        # ✅ Komut loglama ve hata raporlama
        try:
            user = message.from_user.first_name if message.from_user else "Anonim"
            uid = message.from_user.id if message.from_user else "?"
            print(f"[PLAY LOG] Kullanıcı: {user} ({uid}) | Komut: {message.text}")
        except Exception as e:
            print(f"[PLAY LOG HATA] {e}")

        if await is_maintenance() is False:
            if message.from_user.id not in SUDOERS:
                return await message.reply_text("Bot bakımda. Lütfen bir süre bekleyin...")

        if PRIVATE_BOT_MODE == str(True):
            if not await is_served_private_chat(message.chat.id):
                await message.reply_text(
                    "**Özel Müzik Botu**\n\nYalnızca sahibinden gelen yetkili sohbetler için. Önce sahibimden sohbetinize izin vermesini isteyin."
                )
                return await app.leave_chat(message.chat.id)

        if await is_commanddelete_on(message.chat.id):
            try:
                await message.delete()
            except:
                pass

        language = await get_lang(message.chat.id)
        _ = get_string(language)

        audio_telegram = (
            (message.reply_to_message.audio or message.reply_to_message.voice)
            if message.reply_to_message else None
        )
        video_telegram = (
            (message.reply_to_message.video or message.reply_to_message.document)
            if message.reply_to_message else None
        )

        url = await YouTube.url(message)

        # ✅ Kuyruk bilgisi ve oynatma modları
        try:
            chat_id_tmp = message.chat.id
            if await is_active_chat(chat_id_tmp):
                queue = await get_queue(chat_id_tmp)
                position = len(queue) + 1
                total = len(queue) + 1

                current_song = queue[0] if queue else None
                duration_text = ""
                if current_song:
                    duration = await get_song_duration(current_song['url'])
                    duration_text = f"⏱ Süre: {duration}"

                playmode = await get_playmode(chat_id_tmp)
                playtype = await get_playtype(chat_id_tmp)

                buttons = [
                    [InlineKeyboardButton(text=f"🎵 Sıradaki şarkın: {position}/{total}", callback_data=f"queue_detail_{chat_id_tmp}")],
                    [InlineKeyboardButton(text=f"🔁 Mod: {playmode}", callback_data="change_playmode"),
                     InlineKeyboardButton(text=f"🎚 Tip: {playtype}", callback_data="change_playtype")]
                ]

                await message.reply_text(
                    f"🎵 Şu anda bir şarkı çalıyor. Senin şarkın sırada!\n{duration_text}",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
        except:
            pass

        if audio_telegram is None and video_telegram is None and url is None:
            if len(message.command) < 2:
                if "stream" in message.command:
                    return await message.reply_text(_["str_1"])
                buttons = botplaylist_markup(_)
                return await message.reply_photo(
                    photo=PLAYLIST_IMG_URL,
                    caption=_["playlist_1"],
                    reply_markup=InlineKeyboardMarkup(buttons),
                )

        if message.sender_chat:
            upl = InlineKeyboardMarkup([
                [InlineKeyboardButton(text="How to Fix this? ", callback_data="AnonymousAdmin")]
            ])
            return await message.reply_text(_["general_4"], reply_markup=upl)

        if message.command[0][0] == "c":
            chat_id = await get_cmode(message.chat.id)
            if chat_id is None:
                return await message.reply_text(_["setting_12"])
            try:
                chat = await app.get_chat(chat_id)
            except:
                return await message.reply_text(_["cplay_4"])
            channel = chat.title
        else:
            chat_id = message.chat.id
            channel = None

        video = True if message.command[0][0] == "v" or "-v" in message.text else False
        fplay = True if message.command[0][-1] == "e" and await is_active_chat(chat_id) else None

        return await command(
            client,
            message,
            _,
            chat_id,
            video,
            channel,
            playmode,
            url,
            fplay,
        )

    return wrapper

# ✅ Callback handler: Kuyruk detayları
@app.on_callback_query(filters.regex(r"^queue_detail_\d+$"))
async def queue_detail_callback(client, callback_query):
    chat_id = int(callback_query.data.split("_")[-1])
    queue = await get_queue(chat_id)
    if not queue:
        await callback_query.message.reply_text("📭 Kuyruk boş!")
    else:
        text = "🎶 **Kuyrukta olan şarkılar:**\n\n"
        for i, song in enumerate(queue, 1):
            text += f"{i}. {song['title']} ⏱ {song.get('duration','?')}\n"
        await callback_query.message.reply_text(text)
        await callback_query.answer()

# ✅ Callback handler: Playmode ve Playtype aktif değişimi
@app.on_callback_query(filters.regex(r"^(change_playmode|change_playtype)$"))
async def playmode_callback(client, callback_query):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    # Sadece SUDOERS veya admin yetkili kullanıcılar değiştirebilir
    admins = adminlist.get(chat_id, [])
    if user_id not in SUDOERS and user_id not in admins:
        return await callback_query.answer("❌ Bu işlemi yapmaya yetkin yok.", show_alert=True)

    if callback_query.data == "change_playmode":
        current = await get_playmode(chat_id)
        # Örnek değişim: Normal -> Shuffle -> Repeat -> Normal
        new_mode = {"Normal":"Shuffle", "Shuffle":"Repeat", "Repeat":"Normal"}.get(current, "Normal")
        await set_playmode(chat_id, new_mode)
        await callback_query.answer(f"✅ Playmode değiştirildi: {new_mode}", show_alert=True)
    else:
        current = await get_playtype(chat_id)
        new_type = {"Everyone":"Sudo Only", "Sudo Only":"Everyone"}.get(current, "Everyone")
        await set_playtype(chat_id, new_type)
        await callback_query.answer(f"✅ Playtype değiştirildi: {new_type}", show_alert=True)
      
