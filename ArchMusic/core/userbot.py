#
# Copyright (C) 2021-2023 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.
#

import sys
from pyrogram import Client
import config
from ..logging import LOGGER

assistants = []
assistantids = []
assistants_info = {}   # 🔹 Asistan bilgilerini dict olarak da tutalım


class Userbot(Client):
    def __init__(self):
        self.one = Client(
            "ArchMusicString1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
            no_updates=True,
        )
        self.two = Client(
            "ArchMusicString2",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING2),
            no_updates=True,
        )
        self.three = Client(
            "ArchMusicString3",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING3),
            no_updates=True,
        )
        self.four = Client(
            "ArchMusicString4",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING4),
            no_updates=True,
        )
        self.five = Client(
            "ArchMusicString5",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING5),
            no_updates=True,
        )

    async def start(self):
        LOGGER(__name__).info(f"🚀 Asistan Clientleri Başlatılıyor...")

        # 🔹 Yardımcı fonksiyon: tekrarı azaltır
        async def start_single(client, number):
            await client.start()
            # aynı gruba 3 defa katılmayı döngü ile yapalım
            for _ in range(3):
                try:
                    await client.join_chat("ARCH_SUPPORTS")
                except Exception as e:
                    LOGGER(__name__).warning(f"Asistan {number} destek grubuna katılamadı: {e}")

            assistants.append(number)
            try:
                await client.send_message(
                    config.LOG_GROUP_ID, f"✅ Asistan {number} başarıyla başlatıldı 🥀"
                )
            except Exception as e:
                LOGGER(__name__).error(
                    f"❌ Asistan {number} log grubuna erişemedi. Hata: {e}"
                )
                sys.exit()

            get_me = await client.get_me()

            # 🔹 Hesap silinmiş mi kontrol et
            if getattr(get_me, "is_deleted", False):
                LOGGER(__name__).error(f"❌ Asistan {number} hesabı silinmiş! Yeni string girilmeli.")
                return

            client.username = get_me.username
            client.id = get_me.id
            assistantids.append(get_me.id)

            client.name = f"{get_me.first_name} {get_me.last_name}" if get_me.last_name else get_me.first_name

            # 🔹 Asistan bilgilerini dict içinde sakla
            assistants_info[client.id] = {
                "username": client.username,
                "name": client.name,
                "number": number
            }

            LOGGER(__name__).info(
                f"✅ Asistan {number} {client.name} olarak başlatıldı [id: {client.id}]"
            )

        # 🔹 Her asistan için tek tek çalıştır
        if config.STRING1:
            await start_single(self.one, 1)
        if config.STRING2:
            await start_single(self.two, 2)
        if config.STRING3:
            await start_single(self.three, 3)
        if config.STRING4:
            await start_single(self.four, 4)
        if config.STRING5:
            await start_single(self.five, 5)
            
