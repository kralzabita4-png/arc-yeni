# Copyright (C) 2021-2023 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.
#

# REFAKTÖR NOTU (4. Tur):
# - HEDEF: Donmayı (lag) azaltmak ve akıcılığı artırmak.
# - 'safe_get_stream' ve 'seek_stream' fonksiyonları, FFmpeg'e
#   ek parametreler gönderecek şekilde güncellendi.
# - "-preset superfast": CPU yükünü azaltır, zayıf sunucularda donmayı önler.
# - "-reconnect 1 ...": Kaynak linki kesilirse otomatik yeniden bağlanır.

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


# --- REFAKTÖR 4: Akıcılık (Donma Önleme) Ayarları Eklendi ---
async def safe_get_stream(link: str, video: Union[bool, str] = None, chat_id: int = None):
    """
    Güvenli stream oluşturma.
    Donmayı önlemek için FFmpeg 'preset' ve 'reconnect' bayrakları eklendi.
    """
    from ArchMusic import YouTube
    try:
        if not link or not isinstance(link, str):
            return None

        audio_stream_quality = await get_audio_bitrate(chat_id)
        video_stream_quality = await get_video_bitrate(chat_id)

        # Bu parametreler CPU yükünü azaltır ve ağ hatalarını tolere eder
        ffmpeg_params = (
            "-preset superfast "
            "-reconnect 1 "
            "-reconnect_streamed 1 "
            "-reconnect_delay_max 5"
        )

        stream = (
            AudioVideoPiped(
                link,
                audio_parameters=audio_stream_quality,
                video_parameters=video_stream_quality,
                additional_ffmpeg_parameters=ffmpeg_params, # EKLENDİ
            )
            if video
            else AudioPiped(
                link, 
                audio_parameters=audio_stream_quality,
                additional_ffmpeg_parameters=ffmpeg_params, # EKLENDİ
            )
        )
        return stream
    except TypeError as e:
        LOGGER(__name__).error(f"TypeError: {e}")
        return None
    except Exception as e:
        LOGGER(__name__).error(f"Stream Error: {e}")
        return None


class Call(PyTgCalls):
    
    def __init__(self):
        self.userbots = []
        self.pytgcalls = []

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
        except Exception as e:
            LOGGER(__name__).error(f"Stop_stream hatası (ChatID: {chat_id}): {e}")
            pass

    async def force_stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            check = db.get(chat_id)
            check.pop(0)
        except Exception as e:
            LOGGER(__name__).debug(f"Force_stop_stream 'pop' hatası (ChatID: {chat_id}): {e}")
            pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        try:
            await assistant.leave_group_call(chat_id)
        except Exception as e:
            LOGGER(__name__).error(f"Force_stop_stream 'leave' hatası (ChatID: {chat_id}): {e}")
            pass

    async def skip_stream(
        self, chat_id: int, link: str, video: Union[bool, str] = None
    ):
        assistant = await group_assistant(self, chat_id)
        # Değişiklik: 'safe_get_stream' artık donma önleyici ayarları içeriyor
        stream = await safe_get_stream(link, video, chat_id) 
        
        if not stream:
            try:
                language = await get_lang(chat_id)
                _ = get_string(language)
                await app.send_message(
                    chat_id,
                    _["call_stream_err"]
                )
            except Exception as e:
                LOGGER(__name__).error(f"skip_stream dil hatası: {e}")
                await app.send_message(
                    chat_id,
                    "**❌ Ses kaynağı bulunamadı veya link hatalı!**"
                )
            return
            
        await assistant.change_stream(chat_id, stream)

    # --- REFAKTÖR 4: Akıcılık (Donma Önleme) Ayarları Eklendi ---
    async def seek_stream(
        self, chat_id, file_path, to_seek, duration, mode
    ):
        assistant = await group_assistant(self, chat_id)
        audio_stream_quality = await get_audio_bitrate(chat_id)
        video_stream_quality = await get_video_bitrate(chat_id)
        
        # 'safe_get_stream' ile tutarlı olması için preset'leri buraya da ekliyoruz.
        ffmpeg_params = (
            "-preset superfast "
            f"-ss {to_seek} -to {duration}"
        )

        stream = (
            AudioVideoPiped(
                file_path,
                audio_parameters=audio_stream_quality,
                video_parameters=video_stream_quality,
                additional_ffmpeg_parameters=ffmpeg_params, # GÜNCELLENDİ
            )
            if mode == "video"
            else AudioPiped(
                file_path,
                audio_parameters=audio_stream_quality,
                additional_ffmpeg_parameters=ffmpeg_params, # GÜNCELLENDİ
            )
        )
        await assistant.change_stream(chat_id, stream)

    async def stream_call(self, link):
        assistant = await group_assistant(self, config.LOG_GROUP_ID)
        # 'safe_get_stream' artık donma önleyici ayarları içeriyor
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

    async def _check_assistant_status(self, userbot, chat_id, _):
        try:
            get = await app.get_chat_member(chat_id, userbot.id)
            if get.status == ChatMemberStatus.BANNED or get.status == ChatMemberStatus.LEFT:
                raise AssistantErr(
                    _["call_2"].format(userbot.username, userbot.id)
                )
            return True
        except ChatAdminRequired:
            raise AssistantErr(_["call_1"])
        except UserNotParticipant:
            return False

    async def _get_invite_link(self, chat, chat_id, _):
        try:
            invitelink = chat.invite_link
            if invitelink is None:
                invitelink = await app.export_chat_invite_link(chat_id)
            return invitelink
        except ChatAdminRequired:
            raise AssistantErr(_["call_4"])
        except Exception as e:
            LOGGER(__name__).error(f"Davet linki alınamadı: {e}")
            raise AssistantErr(str(e))

    async def _join_by_link(self, userbot, invitelink, original_chat_id, _):
        m = await app.send_message(original_chat_id, _["call_5"])
        if invitelink.startswith("https://t.me/+"):
            invitelink = invitelink.replace(
                "https://t.me/+", "https://t.me/joinchat/"
            )
        try:
            await asyncio.sleep(3)
            await userbot.join_chat(invitelink)
            await asyncio.sleep(4)
            await m.edit(_["call_6"].format(userbot.name))
        except UserAlreadyParticipant:
            await m.delete()
            pass
        except Exception as e:
            await m.delete()
            raise AssistantErr(_["call_3"].format(e))
    
    async def join_assistant(self, original_chat_id, chat_id):
        language = await get_lang(original_chat_id)
        _ = get_string(language)
        userbot = await get_assistant(chat_id)

        is_member = await self._check_assistant_status(userbot, chat_id, _)
        if is_member:
            return

        chat = await app.get_chat(chat_id)
        if chat.username:
            try:
                await userbot.join_chat(chat.username)
            except UserAlreadyParticipant:
                pass
            except Exception as e:
                raise AssistantErr(_["call_3"].format(e))
        else:
            invitelink = await self._get_invite_link(chat, chat_id, _)
            await self._join_by_link(userbot, invitelink, original_chat_id, _)

    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link,
        video: Union[bool, str] = None,
    ):
        language = await get_lang(original_chat_id)
        _ = get_string(language)
        
        assistant = await group_assistant(self, chat_id)
        # 'safe_get_stream' artık donma önleyici ayarları içeriyor
        stream = await safe_get_stream(link, video, chat_id) 
        
        if not stream:
            return await app.send_message(
                original_chat_id, 
                _["call_stream_err"]
            )
        
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
        except NoActiveGroupCall:
            raise AssistantErr(_["call_no_active_vc"])
        except AlreadyJoinedError:
            raise AssistantErr(_["call_already_joined"])
        except TelegramServerError:
            raise AssistantErr(_["call_server_error"])
        except NoAudioSourceFound:
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

    async def change_stream(self, client, chat_id):
        item = await self._handle_queue(client, chat_id)
        if not item:
            LOGGER(__name__).info(f"Kuyruk boş, {chat_id} için arama sonlandırıldı.")
            return
        
        language = await get_lang(chat_id)
        _ = get_string(language)
        
        original_chat_id = item["chat_id"]
        streamtype = str(item["streamtype"]) == "video"

        stream_source = await self._get_stream_input(item, _, original_chat_id)
        if not stream_source:
            LOGGER(__name__).warning(f"Stream kaynağı alınamadı: {item['title']}. Atlanıyor...")
            return await self.change_stream(client, chat_id)

        # 'safe_get_stream' artık donma önleyici ayarları içeriyor
        stream = await safe_get_stream(stream_source, streamtype, chat_id) 
        if not stream:
            await app.send_message(original_chat_id, _["call_stream_err"])
            LOGGER(__name__).warning(f"Safe_get_stream hatası: {item['title']}. Atlanıyor...")
            return await self.change_stream(client, chat_id)

        try:
            await client.change_stream(chat_id, stream)
        except Exception as e:
            LOGGER(__name__).error(f"Change_stream API hatası: {e}")
            await app.send_message(original_chat_id, _["call_9"])
            return await self.change_stream(client, chat_id)
        
        await self._send_stream_notification(item, chat_id, original_chat_id, _)

    async def _handle_queue(self, client, chat_id):
        check = db.get(chat_id)
        if not check:
            try:
                await _clear_(chat_id)
                await client.leave_group_call(chat_id)
            except Exception as e:
                LOGGER(__name__).error(f"Kuyruk boşken ayrılma hatası: {e}")
            return None
        
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
                await client.leave_group_call(chat_id)
                return None
                
        except Exception as e:
            LOGGER(__name__).error(f"Kuyruk yönetimi hatası: {e}")
            try:
                await _clear_(chat_id)
                await client.leave_group_call(chat_id)
            except:
                pass
            return None
        
        return check[0]

    async def _get_stream_input(self, item, _, original_chat_id):
        queued = item["file"]
        videoid = item["vidid"]
        streamtype = str(item["streamtype"]) == "video"

        if "live_" in queued:
            try:
                n, link = await YouTube.video(videoid, True)
                if n == 0:
                    await app.send_message(original_chat_id, text=_["call_9"])
                    return None
                return link
            except Exception as e:
                LOGGER(__name__).error(f"Canlı yayın linki alınamadı: {e}")
                await app.send_message(original_chat_id, text=_["call_9"])
                return None
                
        elif "vid_" in queued:
            mystic = await app.send_message(original_chat_id, _["call_10"])
            try:
                file_path, direct = await YouTube.download(
                    videoid,
                    mystic,
                    videoid=True,
                    video=streamtype,
                )
                await mystic.delete()
                return file_path
            except Exception as e:
                LOGGER(__name__).error(f"Video indirme hatası: {e}")
                await mystic.edit_text(_["call_9"], disable_web_page_preview=True)
                return None
                
        elif "index_" in queued:
            return videoid
            
        else:
            return queued

    async def _send_stream_notification(self, item, chat_id, original_chat_id, _):
        title = (item["title"]).title()
        user = item["by"]
        videoid = item["vidid"]
        
        if "index_" in item["file"]:
            msg_template = _["stream_2"]
        else:
            msg_template = _["stream_1"]
            
        run = await app.send_message(
            chat_id=original_chat_id,
            text=msg_template.format(
                title,
                f"https://t.me/{app.username}?start=info_{videoid}",
                item["dur"],
                user,
            ),
            reply_markup=InlineKeyboardMarkup(stream_markup(_, title, chat_id))
        )
        try:
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
            db[chat_id][0]["played"] = 0
        except Exception as e:
            LOGGER(__name__).error(f"Mystic mesajı DB'ye kaydedilemedi: {e}")

    async def ping(self):
        pings = []
        for instance in self.pytgcalls:
            pings.append(await instance.ping)
        
        if not pings:
            return "0"
            
        return str(round(sum(pings) / len(pings), 3))

    async def start(self):
        LOGGER(__name__).info("PyTgCalls İstemcileri Başlatılıyor...\n")
        for i, (userbot, instance) in enumerate(zip(self.userbots, self.pytgcalls), start=1):
            try:
                await instance.start()
                LOGGER(__name__).info(f"Asistan {i} ({userbot.me.first_name}) başlatıldı.")
            except Exception as e:
                LOGGER(__name__).error(f"Asistan {i} başlatılamadı: {e}")

    async def decorators(self):
        
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
            
            current_users = counter.get(chat_id)
            
            if current_users is None:
                try:
                    participant_list = await client.get_participants(chat_id)
                    final_users = len(participant_list)
                except Exception as e:
                    LOGGER(__name__).error(f"Katılımcı listesi alınamadı: {e}")
                    return
            else:
                final_users = (
                    current_users + 1
                    if isinstance(update, JoinedGroupCallParticipant)
                    else current_users - 1
                )
            
            if final_users < 0:
                final_users = 0 
                
            counter[chat_id] = final_users

            if final_users == 1:
                autoend[chat_id] = datetime.now() + timedelta(
                    minutes=AUTO_END_TIME
                )
            else:
                autoend[chat_id] = {}
            
            LOGGER(__name__).info(f"Katılımcı değişti {chat_id}: {final_users} kullanıcı.")


        for instance in self.pytgcalls:
            instance.on_kicked()(stream_services_handler)
            instance.on_closed_voice_chat()(stream_services_handler)
            instance.on_left()(stream_services_handler)
            
            instance.on_stream_end()(stream_end_handler1)
            
            instance.on_participants_change()(participants_change_handler)
            

ArchMusic = Call()
