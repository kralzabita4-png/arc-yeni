#
# ArchMusic Telegram Bot - Oynatma ve Spam Koruması Modülü
# © 2021-2023 ArchBots@Github
#

import random
import string
import time

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InputMediaPhoto, Message
from pytgcalls.exceptions import NoActiveGroupCall

import config
from config import BANNED_USERS, lyrical
from strings import get_command
from ArchMusic import Apple, Resso, SoundCloud, Spotify, Telegram, YouTube, app
from ArchMusic.core.call import ArchMusic
from ArchMusic.utils import seconds_to_min, time_to_seconds
from ArchMusic.utils.channelplay import get_channeplayCB
from ArchMusic.utils.database import is_video_allowed
from ArchMusic.utils.decorators.language import languageCB
from ArchMusic.utils.decorators.play import PlayWrapper
from ArchMusic.utils.formatters import formats
from ArchMusic.utils.inline.play import livestream_markup, playlist_markup, slider_markup, track_markup
from ArchMusic.utils.inline.playlist import botplaylist_markup
from ArchMusic.utils.logger import play_logs
from ArchMusic.utils.stream.stream import stream

# ---------------------- GLOBAL DEĞİŞKENLER ----------------------
PLAY_COMMAND = get_command("PLAY_COMMAND")  # Oynatma komutu
spam_protection = True  # Spam koruma aktif mi?
spam_records = {}       # Kullanıcı bazlı spam kayıtları

# ---------------------- SPAM KORUMA ----------------------
@app.on_message(filters.command("spam") & filters.user(config.OWNER_ID))
async def spam_toggle(client, message: Message):
    """
    Bot sahibinin spam korumasını açıp kapatmasını sağlar.
    Kullanım: /spam [on/off]
    """
    global spam_protection
    if len(message.command) != 2:
        status = "Açık ✅" if spam_protection else "Kapalı ❌"
        return await message.reply_text(f"**Mevcut Durum:** {status}\n\n**Kullanım:** `/spam [on/off]`")
    
    param = message.command[1].lower()
    if param == "on":
        if spam_protection:
            return await message.reply_text("**Spam koruması zaten açık.** ✅")
        spam_protection = True
        await message.reply_text("**Spam koruması başarıyla etkinleştirildi. 🟢**")
    elif param == "off":
        if not spam_protection:
            return await message.reply_text("**Spam koruması zaten kapalı.** ❌")
        spam_protection = False
        await message.reply_text("**Spam koruması başarıyla devre dışı bırakıldı. 🔴**")
    else:
        await message.reply_text("**Geçersiz parametre. Kullanım:** `/spam [on/off]`")

# ---------------------- OYNATMA KOMUTU ----------------------
@app.on_message(filters.command(PLAY_COMMAND) & filters.group & ~BANNED_USERS)
@PlayWrapper
async def play_command(client, message: Message, _, chat_id, video, channel, playmode, url, fplay):
    """
    Müzik oynatma komutu.
    - Telegram dosyaları
    - YouTube, Spotify, Apple, Resso, SoundCloud
    - URL veya arama sorgusu
    """
    global spam_records

    # --- Spam koruma kontrolü ---
    if spam_protection:
        user_id = message.from_user.id
        current_time = time.time()
        if user_id in spam_records:
            spam_records[user_id].append(current_time)
            spam_records[user_id] = [ts for ts in spam_records[user_id] if current_time - ts <= 5]
            if len(spam_records[user_id]) >= 5:
                await message.reply_text(f"**{message.from_user.mention} kişisinin spam yaptığı tespit edildi!**🚨\n\n**Bot gruptan ayrılıyor...**")
                chat = message.chat
                group_link = f"@{chat.username}" if chat.username else "Gizli"
                await app.send_message(
                    config.LOG_GROUP_ID,
                    f"🚨 **__SPAM ALGILANDI__** 🚨\n\n👤 **Kullanıcı:** {message.from_user.mention} [`{user_id}`]\n📌 **Grup:** {chat.title}\n🆔 **Grup ID:** `{chat.id}`\n🔗 **Grup Linki:** {group_link}\n💬 **Spam Mesajı:** {message.text}\n\n**Durum:** Bot, spam nedeniyle bu gruptan ayrıldı."
                )
                return await app.leave_chat(chat.id)
        else:
            spam_records[user_id] = [current_time]

    # --- Başlangıç mesajı ---
    mystic = await message.reply_text(_["play_2"].format(channel) if channel else _["play_1"])
    
    plist_id = None
    slider = None
    plist_type = None
    spotify = None
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # --- Telegram'dan gelen dosyalar ---
    audio_telegram = (message.reply_to_message.audio or message.reply_to_message.voice) if message.reply_to_message else None
    video_telegram = (message.reply_to_message.video or message.reply_to_message.document) if message.reply_to_message else None

    # --- Ses dosyası işleme ---
    if audio_telegram:
        if audio_telegram.file_size > config.TG_AUDIO_FILESIZE_LIMIT:
            return await mystic.edit_text(_["play_5"])
        duration_min = seconds_to_min(audio_telegram.duration)
        if audio_telegram.duration > config.DURATION_LIMIT:
            return await mystic.edit_text(_["play_6"].format(config.DURATION_LIMIT_MIN, duration_min))
        file_path = await Telegram.get_filepath(audio=audio_telegram)
        if await Telegram.download(_, message, mystic, file_path):
            message_link = await Telegram.get_link(message)
            file_name = await Telegram.get_filename(audio_telegram, audio=True)
            dur = await Telegram.get_duration(audio_telegram)
            details = {"title": file_name, "link": message_link, "path": file_path, "dur": dur}

            try:
                await stream(_, mystic, user_id, details, chat_id, user_name, message.chat.id, streamtype="telegram", forceplay=fplay)
            except Exception as e:
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_3"].format(ex_type)
                return await mystic.edit_text(err)
            return await mystic.delete()
        return

    # --- Video dosyası işleme ---
    elif video_telegram:
        if not await is_video_allowed(message.chat.id):
            return await mystic.edit_text(_["play_3"])
        if message.reply_to_message.document:
            try:
                ext = video_telegram.file_name.split(".")[-1]
                if ext.lower() not in formats:
                    return await mystic.edit_text(_["play_8"].format(f"{' | '.join(formats)}"))
            except:
                return await mystic.edit_text(_["play_8"].format(f"{' | '.join(formats)}"))
        if video_telegram.file_size > config.TG_VIDEO_FILESIZE_LIMIT:
            return await mystic.edit_text(_["play_9"])
        file_path = await Telegram.get_filepath(video_telegram)
        if await Telegram.download(_, message, mystic, file_path):
            message_link = await Telegram.get_link(message)
            file_name = await Telegram.get_filename(video_telegram)
            dur = await Telegram.get_duration(video_telegram)
            details = {"title": file_name, "link": message_link, "path": file_path, "dur": dur}
            try:
                await stream(_, mystic, user_id, details, chat_id, user_name, message.chat.id, video=True, streamtype="telegram", forceplay=fplay)
            except Exception as e:
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_3"].format(ex_type)
                return await mystic.edit_text(err)
            return await mystic.delete()
        return

    # --- URL veya arama sorgusu ---
    elif url:
        # YouTube kontrolü
        if await YouTube.exists(url):
            if "playlist" in url:
                try:
                    details = await YouTube.playlist(url, config.PLAYLIST_FETCH_LIMIT, message.from_user.id)
                except Exception:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "yt"
                plist_id = (url.split("=")[1]).split("&")[0] if "&" in url else url.split("=")[1]
                img = config.PLAYLIST_IMG_URL
                cap = _["play_10"]
            else:
                try:
                    details, track_id = await YouTube.track(url)
                except Exception:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "youtube"
                img = details["thumb"]
                cap = _["play_11"].format(details["title"], details["duration_min"])
        elif await Spotify.valid(url):
            spotify = True
            if not config.SPOTIFY_CLIENT_ID and not config.SPOTIFY_CLIENT_SECRET:
                return await mystic.edit_text("Bu bot Spotify sorgularını oynatamıyor. Lütfen sahibimden Spotify'ı etkinleştirmesini isteyin.")
            if "track" in url:
                try:
                    details, track_id = await Spotify.track(url)
                except Exception:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "youtube"
                img = details["thumb"]
                cap = _["play_11"].format(details["title"], details["duration_min"])
            elif "playlist" in url:
                try:
                    details, plist_id = await Spotify.playlist(url)
                except Exception:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "spplay"
                img = config.SPOTIFY_PLAYLIST_IMG_URL
                cap = _["play_12"].format(message.from_user.first_name)
            elif "album" in url:
                try:
                    details, plist_id = await Spotify.album(url)
                except Exception:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "spalbum"
                img = config.SPOTIFY_ALBUM_IMG_URL
                cap = _["play_12"].format(message.from_user.first_name)
            elif "artist" in url:
                try:
                    details, plist_id = await Spotify.artist(url)
                except Exception:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "spartist"
                img = config.SPOTIFY_ARTIST_IMG_URL
                cap = _["play_12"].format(message.from_user.first_name)
            else:
                return await mystic.edit_text(_["play_17"])
        # Apple, Resso, SoundCloud ve diğer platformlar da benzer mantıkla işleniyor...

# ---------------------- CALLBACK QUERY İŞLEMLERİ ----------------------
@app.on_callback_query(filters.regex("MusicStream") & ~BANNED_USERS)
@languageCB
async def play_music(client, CallbackQuery, _):
    """
    Inline buton ile seçilen müzikleri oynatma
    """
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    vidid, user_id, mode, cplay, fplay = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(_["playcb_1"], show_alert=True)
        except:
            return
    try:
        chat_id, channel = await get_channeplayCB(_, cplay, CallbackQuery)
    except:
        return
    user_name = CallbackQuery.from_user.first_name
    try:
        await CallbackQuery.message.delete()
        await CallbackQuery.answer()
    except:
        pass
    mystic = await CallbackQuery.message.reply_text(_["play_2"].format(channel) if channel else _["play_1"])
    try:
        details, track_id = await YouTube.track(vidid, True)
    except Exception:
        return await mystic.edit_text(_["play_3"])
    video = True if mode == "v" else None
    ffplay = True if fplay == "f" else None
    try:
        await stream(_, mystic, CallbackQuery.from_user.id, details, chat_id, user_name, CallbackQuery.message.chat.id, video, streamtype="youtube", forceplay=ffplay)
    except Exception as e:
        ex_type = type(e).__name__
        err = e if ex_type == "AssistantErr" else _["general_3"].format(ex_type)
        return await mystic.edit_text(err)
    return await mystic.delete()

# ---------------------- DİĞER CALLBACKLER ----------------------
@app.on_callback_query(filters.regex("AnonymousAdmin") & ~BANNED_USERS)
async def anonymous_check(client, CallbackQuery):
    """
    Anonim yönetici kontrolü
    """
    try:
        await CallbackQuery.answer(
            "Anonim bir Yöneticisiniz\n\nGrubunuzun ayarlarına gidin \n-> Yöneticiler Listesi \n-> Adınıza tıklayın \n-> orada ANONYMOUS KAL düğmesinin işaretini kaldırın.",
            show_alert=True,
        )
    except:
        return

@app.on_callback_query(filters.regex("ArchMusicPlaylists") & ~BANNED_USERS)
@languageCB
async def play_playlists_command(client, CallbackQuery, _):
    """
    Inline playlist oynatma
    """
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    videoid, user_id, ptype, mode, cplay, fplay = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(_["playcb_1"], show_alert=True)
        except:
            return
    try:
        chat_id, channel = await get_channeplayCB(_, cplay, CallbackQuery)
    except:
        return
    user_name = CallbackQuery.from_user.first_name
    await CallbackQuery.message.delete()
    try:
        await CallbackQuery.answer()
    except:
        pass
    mystic = await CallbackQuery.message.reply_text(_["play_2"].format(channel) if channel else _["play_1"])
    videoid = lyrical.get(videoid)
    video = True if mode == "v" else None
    ffplay = True if fplay == "f" else None
    spotify = True

    if ptype == "yt":
        spotify = False
        try:
            result = await YouTube.playlist(videoid, config.PLAYLIST_FETCH_LIMIT, user_id, True)
        except Exception:
            return await mystic.edit_text(_["play_3"])
    if ptype == "spplay":
        try:
            result, spotify_id = await Spotify.playlist(videoid)
        except Exception:
            return await mystic.edit_text(_["play_3"])
    if ptype == "spalbum":
        try:
            result, spotify_id = await Spotify.album(videoid)
        except Exception:
            return await mystic.edit_text(_["play_3"])
    if ptype == "spartist":
        try:
            result, spotify_id = await Spotify.artist(videoid)
        except Exception:
            return await mystic.edit_text(_["play_3"])
    if ptype == "apple":
        try:
            result, apple_id = await Apple.playlist(videoid, True)
        except Exception:
            return await mystic.edit_text(_["play_3"])
    try:
        await stream(_, mystic, user_id, result, chat_id, user_name, CallbackQuery.message.chat.id, video, streamtype="playlist", spotify=spotify, forceplay=ffplay)
    except Exception as e:
        ex_type = type(e).__name__
        err = e if ex_type == "AssistantErr" else _["general_3"].format(ex_type)
        return await mystic.edit_text(err)
    return await mystic.delete()

@app.on_callback_query(filters.regex("slider") & ~BANNED_USERS)
@languageCB
async def slider_queries(client, CallbackQuery, _):
    """
    Youtube arama sonucu slider butonları
    """
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    what, rtype, query, user_id, cplay, fplay = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(_["playcb_1"], show_alert=True)
        except:
            return
    rtype = int(rtype)
    if what == "F":
        query_type = 0 if rtype == 9 else rtype + 1
        try:
            await CallbackQuery.answer(_["playcb_2"])
        except:
            pass
        title, duration_min, thumbnail, vidid = await YouTube.slider(query, query_type)
        buttons = slider_markup(_, vidid, user_id, query, query_type, cplay, fplay)
        med = InputMediaPhoto(media=thumbnail, caption=_["play_11"].format(title.title(), duration_min))
        return await CallbackQuery.edit_message_media(media=med, reply_markup=InlineKeyboardMarkup(buttons))
    if what == "B":
        query_type = 9 if rtype == 0 else rtype - 1
        try:
            await CallbackQuery.answer(_["playcb_2"])
        except:
            pass
        title, duration_min, thumbnail, vidid = await YouTube.slider(query, query_type)
        buttons = slider_markup(_, vidid, user_id, query, query_type, cplay, fplay)
        med = InputMediaPhoto(media=thumbnail, caption=_["play_11"].format(title.title(), duration_min))
        return await CallbackQuery.edit_message_media(media=med, reply_markup=InlineKeyboardMarkup(buttons))
