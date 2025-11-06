# Copyright (C) 2021-2023 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.
#

# REFAKTÖR NOTU:
# - __init__, start, ping ve decorators metodları, 5 asistanı
#   manuel olarak değil, bir döngü kullanarak (DRY) yönetecek şekilde yeniden yazıldı.
# - Hata mesajları (örn: "Aktif Sesli Sohbet Bulunamadı") artık `strings`
#   dosyasından çekiliyor. Lütfen aşağıdaki anahtarları dil dosyalarınıza ekleyin:
#   - "call_stream_err": "❌ Ses kaynağı bulunamadı veya link hatalı!..."
#   - "call_no_active_vc": "Aktif Sesli Sohbet Bulunamadı..."
#   - "call_already_joined": "Asistan Zaten Sesli Sohbette..."
#   - "call_server_error": "Telegram Sunucu Hatası..."
# - `stop_stream` gibi fonksiyonlardaki 'except: pass' blokları,
#   hata ayıklamayı kolaylaştırmak için 'LOGGER.error' kullanacak şekilde iyileştirildi.

import asyncio
from datetime import datetime, timedelta
from typing import Union

from pyrogram import Client
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import (ChatAdminRequired,
                             UserAlreadyParticipant,
                             UserNotParticipant)
from pyrogram.types import InlineKeyboardMarkup
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.exceptions import (AlreadyJoinedError,
                                  NoActiveGroupCall,
                                  TelegramServerError,
                                  NoAudioSourceFound)
from pytgcalls.types import (JoinedGroupCallParticipant,
                               LeftGroupCallParticipant, Update)
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.stream import StreamAudioEnded

import config
from strings import get_string
from ArchMusic import LOGGER, YouTube, app
from ArchMusic.misc import db
from ArchMusic.utils.database import (add_active_chat,
                                      add_active_video_chat,
                                      get_assistant,
                                      get_audio_bitrate, get_lang,
                                      get_loop, get_video_bitrate,
                                      group_assistant, is_autoend,
                                      music_on, mute_off,
                                      remove_active_chat,
                                      remove_active_video_chat,
                                      set_loop)
from ArchMusic.utils.exceptions import AssistantErr
from ArchMusic.utils.inline.play import (stream_markup)
from ArchMusic.utils.stream.autoclear import auto_clean


autoend = {}
counter = {}
AUTO_END_TIME = 3


async def _clear_(chat_id):
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)


async def safe_get_stream(link: str, video: Union[bool, str] = None, chat_id: int = None):
    """
    Güvenli stream oluşturma:
    - Link boş veya hatalıysa None döner.
    - TypeError veya başka hataları yakalar.
    """
    from ArchMusic import YouTube
    try:
        if not link or not isinstance(link, str):
            return None

        # Ses/video kalitesi
        audio_stream_quality = await get_audio_bitrate(chat_id)
        video_stream_quality = await get_video_bitrate(chat_id)

        stream = (
            AudioVideoPiped(
                link,
                audio_parameters=audio_stream_quality,
                video_parameters=video_stream_quality,
            )
            if video
            else AudioPiped(link, audio_parameters=audio_stream_quality)
        )
        return stream
    except TypeError as e:
        LOGGER(__name__).error(f"TypeError: {e}")
        return None
    except Exception as e:
        LOGGER(__name__).error(f"Stream Error: {e}")
        return None


class Call(PyTgCalls):
    
    # REFAKTÖR EDİLDİ (DRY PRENSİBİ)
    def __init__(self):
        self.userbots = []
        self.pytgcalls = []

        # Config'den gelen ve None olmayan tüm string'leri topla
        session_strings = [
            str(s) for s in 
            [config.STRING1, config.STRING2, config.STRING3, config.STRING4, config.STRING5]
            if s
        ]

        for i, session_string in enumerate(session_strings, start=1):
            try:
                userbot = Client(
                    f"ArchMusicString{i}",
                    api_id=config.API_ID,
                    api_hash=config.API_HASH,
                    session_string=session_string,
                )
                pytg_instance = PyTgCalls(
                    userbot,
                    cache_duration=100,
                )
                self.userbots.append(userbot)
                self.pytgcalls.append(pytg_instance)
            except Exception as e:
                LOGGER(__name__).error(f"Asistan {i} başlatılamadı: {e}")

        # REFAKTÖR: Eski kod uyumluluğu için self.one, self.two vb. değişkenleri koru
        # Bu, group_assistant gibi diğer dosyalardaki kodların bozulmamasını sağlar.
        try:
            if len(self.pytgcalls) > 0: self.one = self.pytgcalls[0]
            if len(self.pytgcalls) > 1: self.two = self.pytgcalls[1]
            if len(self.pytgcalls) > 2: self.three = self.pytgcalls[2]
            if len(self.pytgcalls) > 3: self.four = self.pytgcalls[3]
            if len(self.pytgcalls) > 4: self.five = self.pytgcalls[4]
        except IndexError:
            LOGGER(__name__).warning("Tüm 5 asistan string'i tanımlanmamış olabilir, bu normaldir.")
            pass

    async def pause_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.pause_stream(chat_id)

    async def resume_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.resume_stream(chat_id)

    async def mute_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.mute_stream(chat_id)

    async def unmute_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.unmute_stream(chat_id)

    async def stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            await _clear_(chat_id)
            await assistant.leave_group_call(chat_id)
        # REFAKTÖR: Hata yakalama iyileştirildi
        except Exception as e:
            LOGGER(__name__).error(f"Stop_stream hatası (ChatID: {chat_id}): {e}")
            pass

    async def force_stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            check = db.get(chat_id)
            check.pop(0)
        # REFAKTÖR: Hata yakalama iyileştirildi
        except Exception as e:
            LOGGER(__name__).debug(f"Force_stop_stream 'pop' hatası (ChatID: {chat_id}): {e}")
            pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        try:
            await assistant.leave_group_call(chat_id)
        # REFAKTÖR: Hata yakalama iyileştirildi
        except Exception as e:
            LOGGER(__name__).error(f"Force_stop_stream 'leave' hatası (ChatID: {chat_id}): {e}")
            pass

    async def skip_stream(
        self, chat_id: int, link: str, video: Union[bool, str] = None
    ):
        assistant = await group_assistant(self, chat_id)
        stream = await safe_get_stream(link, video, chat_id)
        
        if not stream:
            # REFAKTÖR: Hata mesajı dil dosyalarından çekilmeli
            # Ancak bu fonksiyonda 'original_chat_id' olmadığı için 'get_lang' kullanamıyoruz.
            # Şimdilik sabit mesajı kullanıyoruz, bu orijinal kodda da böyleydi.
            return await app.send_message(
                chat_id,
                "**❌ Ses kaynağı bulunamadı veya link hatalı!**" 
            )
        await assistant.change_stream(chat_id, stream)

    async def seek_stream(
        self, chat_id, file_path, to_seek, duration, mode
    ):
        assistant = await group_assistant(self, chat_id)
        audio_stream_quality = await get_audio_bitrate(chat_id)
        video_stream_quality = await get_video_bitrate(chat_id)
        stream = (
            AudioVideoPiped(
                file_path,
                audio_parameters=audio_stream_quality,
                video_parameters=video_stream_quality,
                additional_ffmpeg_parameters=f"-ss {to_seek} -to {duration}",
            )
            if mode == "video"
            else AudioPiped(
                file_path,
                audio_parameters=audio_stream_quality,
                additional_ffmpeg_parameters=f"-ss {to_seek} -to {duration}",
            )
        )
        await assistant.change_stream(chat_id, stream)

    async def stream_call(self, link):
        assistant = await group_assistant(self, config.LOG_GROUP_ID)
        stream = await safe_get_stream(link, True, config.LOG_GROUP_ID)
        if not stream:
            return
        await assistant.join_group_call(
            config.LOG_GROUP_ID,
            stream,
            stream_type=StreamType().pulse_stream,
        )
        await asyncio.sleep(0.5)
        await assistant.leave_group_call(config.LOG_GROUP_ID)

    async def join_assistant(self, original_chat_id, chat_id):
        language = await get_lang(original_chat_id)
        _ = get_string(language)
        userbot = await get_assistant(chat_id)
        try:
            try:
                get = await app.get_chat_member(chat_id, userbot.id)
            except ChatAdminRequired:
                raise AssistantErr(_["call_1"])
            if get.status == ChatMemberStatus.BANNED or get.status == ChatMemberStatus.LEFT:
                raise AssistantErr(
                    _["call_2"].format(userbot.username, userbot.id)
                )
        except UserNotParticipant:
            chat = await app.get_chat(chat_id)
            if chat.username:
                try:
                    await userbot.join_chat(chat.username)
                except UserAlreadyParticipant:
                    pass
                except Exception as e:
                    raise AssistantErr(_["call_3"].format(e))
            else:
                try:
                    try:
                        try:
                            invitelink = chat.invite_link
                            if invitelink is None:
                                invitelink = (
                                    await app.export_chat_invite_link(
                                        chat_id
                                    )
                                )
                        except:
                            invitelink = (
                                await app.export_chat_invite_link(
                                    chat_id
                                )
                            )
                    except ChatAdminRequired:
                        raise AssistantErr(_["call_4"])
                    except Exception as e:
                        raise AssistantErr(e)
                    m = await app.send_message(
                        original_chat_id, _["call_5"]
                    )
                    if invitelink.startswith("https://t.me/+"):
                        invitelink = invitelink.replace(
                            "https://t.me/+", "https://t.me/joinchat/"
                        )
                    await asyncio.sleep(3)
                    await userbot.join_chat(invitelink)
                    await asyncio.sleep(4)
                    await m.edit(_["call_6"].format(userbot.name))
                except UserAlreadyParticipant:
                    pass
                except Exception as e:
                    raise AssistantErr(_["call_3"].format(e))

    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link,
        video: Union[bool, str] = None,
    ):
        # REFAKTÖR: Hata mesajları için dil dosyalarını yükle
        language = await get_lang(original_chat_id)
        _ = get_string(language)
        
        assistant = await group_assistant(self, chat_id)
        stream = await safe_get_stream(link, video, chat_id)
        
        if not stream:
            # REFAKTÖR: Hata mesajı dil dosyasından çekildi
            return await app.send_message(
                original_chat_id, # Orijinal kodda burası 'chat_id' idi, düzeltildi.
                _["call_stream_err"]
            )
        try:
            await assistant.join_group_call(
                chat_id,
                stream,
                stream_type=StreamType().pulse_stream,
            )
        except NoActiveGroupCall:
            try:
                await self.join_assistant(original_chat_id, chat_id)
            except Exception as e:
                raise e
            try:
                await assistant.join_group_call(
                    chat_id,
                    stream,
                    stream_type=StreamType().pulse_stream,
                )
            except Exception as e:
                # REFAKTÖR: Hata mesajı dil dosyasından çekildi
                raise AssistantErr(_["call_no_active_vc"])
        except AlreadyJoinedError:
            # REFAKTÖR: Hata mesajı dil dosyasından çekildi
            raise AssistantErr(_["call_already_joined"])
        except TelegramServerError:
            # REFAKTÖR: Hata mesajı dil dosyasından çekildi
            raise AssistantErr(_["call_server_error"])
        except NoAudioSourceFound:
            # REFAKTÖR: Hata mesajı dil dosyasından çekildi
            await app.send_message(
                original_chat_id,
                _["call_stream_err"]
            )
            await _clear_(chat_id)
            return
            
        await add_active_chat(chat_id)
        await mute_off(chat_id)
        await music_on(chat_id)
        if video:
            await add_active_video_chat(chat_id)
        if await is_autoend():
            counter[chat_id] = {}
            users = len(await assistant.get_participants(chat_id))
            if users == 1:
                autoend[chat_id] = datetime.now() + timedelta(
                    minutes=AUTO_END_TIME
                )

    # --- stream değişim kısmı aşağıda ---
    async def change_stream(self, client, chat_id):
        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)
        try:
            if loop == 0:
                popped = check.pop(0)
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)
            if popped:
                if config.AUTO_DOWNLOADS_CLEAR == str(True):
                    await auto_clean(popped)
            if not check:
                await _clear_(chat_id)
                return await client.leave_group_call(chat_id)
        except:
            try:
                await _clear_(chat_id)
                return await client.leave_group_call(chat_id)
            except:
                return
        else:
            queued = check[0]["file"]
            language = await get_lang(chat_id)
            _ = get_string(language)
            title = (check[0]["title"]).title()
            user = check[0]["by"]
            original_chat_id = check[0]["chat_id"]
            streamtype = check[0]["streamtype"]
            audio_stream_quality = await get_audio_bitrate(chat_id)
            video_stream_quality = await get_video_bitrate(chat_id)
            videoid = check[0]["vidid"]
            check[0]["played"] = 0
            if "live_" in queued:
                n, link = await YouTube.video(videoid, True)
                if n == 0:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_9"],
                    )
                stream = await safe_get_stream(link, str(streamtype) == "video", chat_id)
                if not stream:
                    # REFAKTÖR: Hata mesajı dil dosyasından çekildi
                    return await app.send_message(
                        original_chat_id,
                        _["call_stream_err"]
                    )
                
                try:
                    await client.change_stream(chat_id, stream)
                except Exception:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_9"],
                    )
                
                run = await app.send_message(
                    chat_id=original_chat_id,
                    text=_["stream_1"].format(
                        title,
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(stream_markup(_, title, chat_id))
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
            elif "vid_" in queued:
                mystic = await app.send_message(
                    original_chat_id, _["call_10"]
                )
                try:
                    file_path, direct = await YouTube.download(
                        videoid,
                        mystic,
                        videoid=True,
                        video=True
                        if str(streamtype) == "video"
                        else False,
                    )
                except:
                    return await mystic.edit_text(
                        _["call_9"], disable_web_page_preview=True
                    )
                stream = await safe_get_stream(file_path, str(streamtype) == "video", chat_id)
                if not stream:
                    # REFAKTÖR: Hata mesajı dil dosyasından çekildi
                    return await app.send_message(
                        original_chat_id,
                        _["call_stream_err"]
                    )
                try:
                    await client.change_stream(chat_id, stream)
                except Exception:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_9"],
                    )
                await mystic.delete()
                run = await app.send_message(
                    chat_id=original_chat_id,
                    text=_["stream_1"].format(
                        title,
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(stream_markup(_, title, chat_id))
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
            elif "index_" in queued:
                stream = await safe_get_stream(videoid, str(streamtype) == "video", chat_id)
                if not stream:
                    # REFAKTÖR: Hata mesajı dil dosyasından çekildi
                    return await app.send_message(
                        original_chat_id,
                        _["call_stream_err"]
                    )
                try:
                    await client.change_stream(chat_id, stream)
                except Exception:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_9"],
                    )
                run = await app.send_message(
                    chat_id=original_chat_id,
                    text=_["stream_2"].format(
                        title,
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(stream_markup(_, title, chat_id))
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
            else:
                stream = await safe_get_stream(queued, str(streamtype) == "video", chat_id)
                if not stream:
                    # REFAKTÖR: Hata mesajı dil dosyasından çekildi
                    return await app.send_message(
                        original_chat_id,
                        _["call_stream_err"]
                    )
                try:
                    await client.change_stream(chat_id, stream)
                except Exception:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_9"],
                    )
                run = await app.send_message(
                    chat_id=original_chat_id,
                    text=_["stream_1"].format(
                        title,
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(stream_markup(_, title, chat_id))
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"

    # REFAKTÖR EDİLDİ (DRY PRENSİBİ)
    async def ping(self):
        pings = []
        for instance in self.pytgcalls:
            pings.append(await instance.ping)
        
        if not pings:
            return "0" # Hiç asistan çalışmıyorsa
            
        return str(round(sum(pings) / len(pings), 3))

    # REFAKTÖR EDİLDİ (DRY PRENSİBİ)
    async def start(self):
        LOGGER(__name__).info("PyTgCalls İstemcileri Başlatılıyor...\n")
        for i, (userbot, instance) in enumerate(zip(self.userbots, self.pytgcalls), start=1):
            try:
                await instance.start()
                LOGGER(__name__).info(f"Asistan {i} ({userbot.me.first_name}) başlatıldı.")
            except Exception as e:
                LOGGER(__name__).error(f"Asistan {i} başlatılamadı: {e}")

    # REFAKTÖR EDİLDİ (DRY PRENSİBİ)
    async def decorators(self):
        
        # Önce handler fonksiyonlarını tanımla
        async def stream_services_handler(_, chat_id: int):
            await self.stop_stream(chat_id)

        async def stream_end_handler1(client, update: Update):
            if not isinstance(update, StreamAudioEnded):
                return
            await self.change_stream(client, update.chat_id)

        async def participants_change_handler(client, update: Update):
            if not isinstance(
                update, JoinedGroupCallParticipant
            ) and not isinstance(update, LeftGroupCallParticipant):
                return
            chat_id = update.chat_id
            users = counter.get(chat_id)
            if not users:
                try:
                    got = len(await client.get_participants(chat_id))
                except:
                    return
                counter[chat_id] = got
                if got == 1:
                    autoend[chat_id] = datetime.now() + timedelta(
                        minutes=AUTO_END_TIME
                    )
                    return
                autoend[chat_id] = {}
            else:
                final = (
                    users + 1
                    if isinstance(update, JoinedGroupCallParticipant)
                    else users - 1
                )
                counter[chat_id] = final
                if final == 1:
                    autoend[chat_id] = datetime.now() + timedelta(
                        minutes=AUTO_END_TIME
                    )
                    return
                autoend[chat_id] = {}

        # Şimdi bu handler'ları döngü içinde her asistan için kaydet
        for instance in self.pytgcalls:
            instance.on_kicked()(stream_services_handler)
            instance.on_closed_voice_chat()(stream_services_handler)
            instance.on_left()(stream_services_handler)
            
            instance.on_stream_end()(stream_end_handler1)
            
            instance.on_participants_change()(participants_change_handler)
            

ArchMusic = Call()
