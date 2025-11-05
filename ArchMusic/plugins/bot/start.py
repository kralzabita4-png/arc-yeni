import asyncio
import random  # Glitch animasyonu için gerekli
from pyrogram import filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.errors import MessageNotModified  # Animasyon için gerekli
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from youtubesearchpython.__future__ import VideosSearch

import config
from config import BANNED_USERS
from config.config import OWNER_ID
from strings import get_command, get_string
from ArchMusic import Telegram, YouTube, app
from ArchMusic.misc import SUDOERS
from ArchMusic.plugins.play.playlist import del_plist_msg
from ArchMusic.plugins.sudo.sudoers import sudoers_list
from ArchMusic.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_assistant,
    get_lang,
    is_on_off,
    is_served_private_chat,
)
from ArchMusic.utils.decorators.language import LanguageStart
from ArchMusic.utils.inline import help_pannel, private_panel, start_pannel

loop = asyncio.get_running_loop()


# ===================== GÜZEL YÜKLENİYOR (Siber Glitch) =====================
async def show_loading(message: Message):
    """
    Bir metni "deşifre" ediyormuş gibi "glitch" efekti uygulayan animasyon.
    """
    
    # "Glitch" efekti için kullanılacak karakterler
    flicker_chars = "█▓▒░_/\@#%&?01*ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    # Deşifre edilecek adımlar
    status_messages = [
        "BAŞLATILIYOR...",
        "MODÜLLER YÜKLENİYOR...",
        "BAĞLANTI KURULUYOR...",
        "SİSTEM AKTİF!"
    ]
    
    loading_message = None
    
    try:
        # İlk boş mesajı gönder
        loading_message = await message.reply_text("```[ ... ]```")
        
        # Her durum mesajı için (Dış döngü)
        for target_text in status_messages:
            current_text = list(" " * len(target_text))
            
            # "Deşifre" animasyonu (İç döngü)
            # Her harfi tek tek yerine koy
            for i in range(len(target_text)):
                current_text[i] = target_text[i] # i'inci harfi sabitle
                
                # Sabitlenmemiş diğer harfleri "karıştır"
                for j in range(i + 1, len(target_text)):
                    current_text[j] = random.choice(flicker_chars)
                
                new_display_text = f"```[ {''.join(current_text)} ]```"
                
                try:
                    if loading_message.text != new_display_text:
                        await loading_message.edit(new_display_text)
                except MessageNotModified:
                    pass
                
                await asyncio.sleep(0.04) # Deşifre hızı (çok hızlı olmalı)
            
            # Kelimenin tamamı deşifre oldu, kısa bir süre bekle
            final_display_text = f"```[ {target_text} ]```"
            if loading_message.text != final_display_text:
                await loading_message.edit(final_display_text)
            
            await asyncio.sleep(0.5) # Bir sonraki adıma geçmeden önce durakla

        # Bitiş (Son mesajın kalıcı olması için)
        if loading_message:
            await loading_message.edit("```[ ✅ SİSTEM AKTİF! ]```")

    except Exception as e:
        print(f"Hata (show_loading): {e}")
        pass # Hata olursa 'None' döndürecek

    return loading_message


# ===================== START KOMUTU PARAMETRELERİ =====================
async def handle_start_params(client, message: Message, param: str, _):
    if param.startswith("help"):
        return await message.reply_text(_["help_1"], reply_markup=help_pannel(_))
    if param.startswith("song"):
        return await message.reply_text(_["song_2"])
    if param.startswith("sta"):
        return await message.reply_text("🔎 Kişisel istatistikler özelliği kaldırıldı.")
    if param.startswith("sud"):
        await sudoers_list(client, message, _)
        if await is_on_off(config.LOG):
            await app.send_message(config.LOG_GROUP_ID, f"{message.from_user.mention} az önce **SUDO LİSTESİNİ** kontrol etti.")
    if param.startswith("lyr"):
        query = param.replace("lyrics_", "", 1)
        lyrics = config.lyrical.get(query)
        return await Telegram.send_split_text(message, lyrics or "Şarkı sözleri bulunamadı.")
    if param.startswith("del"):
        return await del_plist_msg(client, message, _)
    if param.startswith("inf"):
        return await fetch_video_info(message, param, _)


# ===================== VIDEO BİLGİSİ =====================
async def fetch_video_info(message: Message, param: str, _):
    m = await message.reply_text("🔎 Bilgi Alınıyor...")
    query = f"https://www.youtube.com/watch?v={param.replace('info_', '', 1)}"
    results = VideosSearch(query, limit=1)
    result = (await results.next())["result"][0]

    caption = f"""
🎬 **{result['title']}**
⏳ Süre: {result['duration']}
👀 Görüntüleme: {result['viewCount']['short']}
🕒 Yayın: {result['publishedTime']}
📺 Kanal: [{result['channel']['name']}]({result['channel']['link']})
🔗 [YouTube'da İzle]({result['link']})
"""
    key = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎥 İzle", url=result['link']),
         InlineKeyboardButton("❌ Kapat", callback_data="close")]
    ])
    await m.delete()
    await app.send_photo(message.chat.id, photo=result['thumbnails'][0]['url'].split("?")[0], caption=caption, reply_markup=key)


# ===================== START KOMUTU (HATASIZ) =====================
@app.on_message(filters.command(get_command("START_COMMAND")) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_comm(client, message: Message, _):
    loading = await show_loading(message)
    await add_served_user(message.from_user.id)

    params = message.text.split(None, 1)
    if len(params) > 1:
        if loading:  # <-- DÜZELTME: 'None' kontrolü eklendi
            await loading.delete()
        return await handle_start_params(client, message, params[1], _)

    # Animasyon mesajını sil
    if loading:  # <-- DÜZELTME: 'None' kontrolü eklendi
        await loading.delete() 
    try:
        OWNER = OWNER_ID[0] if await app.resolve_peer(OWNER_ID[0]) else None
    except:
        OWNER = None

    out = private_panel(_, app.username, OWNER)
    caption = f"✨ {config.MUSIC_BOT_NAME} seni karşıladı!\n\n🎶 Tüm müzik komutları için aşağıdaki paneli kullanabilirsin."
    if config.START_IMG_URL:
        try:
            await message.reply_photo(photo=config.START_IMG_URL, caption=caption, reply_markup=InlineKeyboardMarkup(out))
        except:
            await message.reply_text(caption, reply_markup=InlineKeyboardMarkup(out))
    else:
        await message.reply_text(caption, reply_markup=InlineKeyboardMarkup(out))

    if await is_on_off(config.LOG):
        await app.send_message(config.LOG_GROUP_ID, f"👤 {message.from_user.mention} (@{message.from_user.username}) ({message.from_user.id}) /start komutunu kullandı.")


# ===================== GRUPA EKLENİNCE HOŞGELDİN MESAJI =====================
welcome_group = 2

@app.on_message(filters.new_chat_members, group=welcome_group)
async def welcome(client, message: Message):
    chat_id = message.chat.id
    if config.PRIVATE_BOT_MODE == "True" and not await is_served_private_chat(chat_id):
        await message.reply_text("**Özel Müzik Botu**\n\nYalnızca sahibinden yetkili sohbetlerde kullanılabilir.")
        return await app.leave_chat(chat_id)
    else:
        await add_served_chat(chat_id)

    for member in message.new_chat_members:
        try:
            language = await get_lang(chat_id)
            _ = get_string(language)
            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text(_["start_6"])
                    return await app.leave_chat(chat_id)
                if chat_id in await blacklisted_chats():
                    await message.reply_text(_["start_7"].format(f"https://t.me/{app.username}?start=sudolist"))
                    return await app.leave_chat(chat_id)

                userbot = await get_assistant(chat_id)
                out = start_pannel(_)
                video_url = "https://telegra.ph/file/acfb445238b05315f0013.mp4"
                video_caption = _["start_3"].format(config.MUSIC_BOT_NAME, userbot.username, userbot.id)
                await app.send_video(chat_id, video_url, caption=video_caption, reply_markup=InlineKeyboardMarkup(out))

            elif member.id in config.OWNER_ID:
                await message.reply_text(_["start_4"].format(config.MUSIC_BOT_NAME, member.mention))
            elif member.id in SUDOERS:
                await message.reply_text(_["start_5"].format(config.MUSIC_BOT_NAME, member.mention))
        except:
            continue
