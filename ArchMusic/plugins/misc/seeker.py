import asyncio
from pyrogram.types import InlineKeyboardMarkup
from strings import get_string
from ArchMusic.misc import db
from ArchMusic.utils.database import get_active_chats, get_lang, is_music_playing
from ArchMusic.utils.formatters import seconds_to_min
from ArchMusic.utils.inline import stream_markup
from ..admins.callback import wrong
import time

checker = {}
BASE_CONCURRENT = 50  # Minimum eşzamanlı chat
MAX_CONCURRENT = 100  # Maksimum eşzamanlı chat
BASE_DELAY = 1        # Minimum batch gecikmesi (saniye)
MAX_DELAY = 3         # Maksimum batch gecikmesi (saniye)

# Basit rate limit takip
last_requests = []
RATE_LIMIT = 30       # saniyede yapılabilecek edit_reply_markup sayısı


async def process_chat(chat_id, semaphore):
    async with semaphore:
        try:
            # Rate limit kontrolü
            now = time.time()
            last_requests[:] = [t for t in last_requests if now - t < 1]  # 1 saniyede kaç istek
            if len(last_requests) >= RATE_LIMIT:
                await asyncio.sleep(1)
            last_requests.append(time.time())

            if not await is_music_playing(chat_id):
                return

            playing_list = db.get(chat_id)
            if not playing_list or not isinstance(playing_list, list):
                return

            playing = playing_list[0]
            mystic = playing.get("mystic")
            if not mystic:
                return

            if wrong.get(chat_id, {}).get(mystic.id) is False:
                return

            try:
                language = await get_lang(chat_id)
            except Exception:
                language = "en"
            _ = get_string(language)

            try:
                buttons = stream_markup(
                    _,
                    playing.get("vidid"),
                    chat_id,
                    seconds_to_min(playing.get("played", 0)),
                    playing.get("dur")
                )
                await mystic.edit_reply_markup(
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
            except Exception as e:
                print(f"Failed to edit markup for chat {chat_id}: {e}")

        except Exception as e:
            print(f"Error processing chat {chat_id}: {e}")


async def markup_updater():
    while True:
        try:
            await asyncio.sleep(4)
            active_chats = await get_active_chats()
        except Exception as e:
            print(f"Failed to fetch active chats: {e}")
            await asyncio.sleep(2)
            continue

        if not active_chats:
            continue

        active_count = len(active_chats)
        # Dinamik throttling: chat sayısına göre concurrent ve delay ayarla
        max_concurrent = min(MAX_CONCURRENT, max(BASE_CONCURRENT, active_count // 10))
        batch_delay = min(MAX_DELAY, max(BASE_DELAY, active_count / 500))
        semaphore = asyncio.Semaphore(max_concurrent)

        for i in range(0, len(active_chats), max_concurrent):
            batch = active_chats[i:i + max_concurrent]
            tasks = [process_chat(chat_id, semaphore) for chat_id in batch]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(batch_delay)


async def start_updater():
    asyncio.create_task(markup_updater())
                  
