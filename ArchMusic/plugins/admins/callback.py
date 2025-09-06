import random
import asyncio
from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup
from config import AUTO_DOWNLOADS_CLEAR, BANNED_USERS, adminlist
from ArchMusic import YouTube, app
from ArchMusic.core.call import ArchMusic
from ArchMusic.misc import SUDOERS, db
from ArchMusic.utils.database import (
    is_active_chat, is_music_playing, is_muted, is_nonadmin_chat,
    music_off, music_on, mute_off, mute_on, set_loop
)
from ArchMusic.utils.decorators.language import languageCB
from ArchMusic.utils.formatters import seconds_to_min
from ArchMusic.utils.inline.play import (
    panel_markup_1, panel_markup_2, panel_markup_3,
    stream_markup, telegram_markup
)
from ArchMusic.utils.stream.autoclear import auto_clean

wrong = {}
downvote = {}
downvoters = {}

# -------------------
# Kuyruk Yönetimi
# -------------------

class QueueManager:
    """Chat bazlı güvenli asenkron kuyruk yöneticisi."""
    def __init__(self):
        self.queues = {}  # chat_id -> asyncio.Queue
        self.locks = {}   # chat_id -> asyncio.Lock

    def get_queue(self, chat_id):
        if chat_id not in self.queues:
            self.queues[chat_id] = asyncio.Queue()
        return self.queues[chat_id]

    def get_lock(self, chat_id):
        if chat_id not in self.locks:
            self.locks[chat_id] = asyncio.Lock()
        return self.locks[chat_id]

    async def add_track(self, chat_id, track):
        queue = self.get_queue(chat_id)
        await queue.put(track)

    async def pop_track(self, chat_id):
        queue = self.get_queue(chat_id)
        if queue.empty():
            return None
        return await queue.get()

    async def peek_track(self, chat_id):
        queue = self.get_queue(chat_id)
        if queue.empty():
            return None
        return queue._queue[0]  

    async def shuffle_queue(self, chat_id):
        queue = self.get_queue(chat_id)
        if queue.empty():
            return
        items = list(queue._queue)
        current = items.pop(0)
        random.shuffle(items)
        queue._queue.clear()
        queue._queue.append(current)
        for item in items:
            queue._queue.append(item)

queue_manager = QueueManager()

# -------------------
# Yardımcı Fonksiyonlar
# -------------------

async def safe_edit_markup(query: CallbackQuery, buttons):
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception:
        return

async def check_admin_rights(query: CallbackQuery, _):
    if query.from_user.id in SUDOERS:
        return True
    admins = adminlist.get(query.message.chat.id)
    if not admins:
        await query.answer(_["admin_18"], show_alert=True)
        return False
    if query.from_user.id not in admins:
        await query.answer(_["admin_19"], show_alert=True)
        return False
    return True

def update_wrong(chat_id, message_id, value: bool):
    if chat_id not in wrong:
        wrong[chat_id] = {}
    wrong[chat_id][message_id] = value

async def send_stream_message(query, stream_type, title, videoid, duration, user):
    templates = {
        "1": _["stream_1"],
        "2": _["stream_2"],
        "3": _["stream_3"]
    }
    text_template = templates.get(stream_type, _["stream_1"])
    if stream_type == "1":
        text = text_template.format(
            title, f"https://t.me/{app.username}?start=info_{videoid}", duration, user
        )
    else:
        text = text_template.format(title, duration, user)
    run = await query.message.reply_text(text=text)
    return run

# -------------------
# Panel Markup
# -------------------

@app.on_callback_query(filters.regex("PanelMarkup") & ~BANNED_USERS)
@languageCB
async def markup_panel(client, query: CallbackQuery, _):
    await query.answer()
    _, data = query.data.split(None, 1)
    videoid, _ = data.split("|")
    chat_id = query.message.chat.id
    buttons = panel_markup_1(_, videoid, chat_id)
    await safe_edit_markup(query, buttons)
    update_wrong(chat_id, query.message.id, False)

# -------------------
# Main Markup
# -------------------

@app.on_callback_query(filters.regex("MainMarkup") & ~BANNED_USERS)
@languageCB
async def main_markup(client, query: CallbackQuery, _):
    await query.answer()
    _, data = query.data.split(None, 1)
    videoid, _ = data.split("|")
    chat_id = query.message.chat.id
    if videoid == str(None):
        buttons = telegram_markup(_, chat_id)
    else:
        buttons = stream_markup(_, videoid, chat_id)
    await safe_edit_markup(query, buttons)
    update_wrong(chat_id, query.message.id, True)

# -------------------
# Sayfa Navigasyonu
# -------------------

@app.on_callback_query(filters.regex("Pages") & ~BANNED_USERS)
@languageCB
async def pages_callback(client, query: CallbackQuery, _):
    await query.answer()
    _, data = query.data.split(None, 1)
    state, pages, videoid, chat = data.split("|")
    chat_id = int(chat)
    pages = int(pages)
    page_map = {
        "Forw": {0: panel_markup_2, 1: panel_markup_3, 2: panel_markup_1},
        "Back": {0: panel_markup_3, 1: panel_markup_1, 2: panel_markup_2}
    }
    buttons = page_map.get(state, {}).get(pages, panel_markup_1)(_, videoid, chat_id)
    await safe_edit_markup(query, buttons)

# -------------------
# ADMIN Callback
# -------------------

@app.on_callback_query(filters.regex("ADMIN") & ~BANNED_USERS)
@languageCB
async def admin_actions(client, query: CallbackQuery, _):
    data = query.data.split(None, 1)[1]
    command, chat = data.split("|")
    chat_id = int(chat)

    if not await is_active_chat(chat_id):
        return await query.answer(_["general_6"], show_alert=True)

    mention = query.from_user.mention
    if not await is_nonadmin_chat(chat_id):
        if not await check_admin_rights(query, _):
            return

    if command in ["Pause", "Resume", "Stop", "End", "Mute", "Unmute", "Loop", "Shuffle", "Skip"]:
        await handle_music_commands(query, command, chat_id, mention, _)
    else:
        await handle_seek_commands(query, command, chat_id, mention, _)

# -------------------
# Müzik Komutları
# -------------------

async def handle_music_commands(query, command, chat_id, mention, _):
    if command == "Pause":
        if not await is_music_playing(chat_id):
            return await query.answer(_["admin_1"], show_alert=True)
        await music_off(chat_id)
        await ArchMusic.pause_stream(chat_id)
        await query.message.reply_text(_["admin_2"].format(mention))
    elif command == "Resume":
        if await is_music_playing(chat_id):
            return await query.answer(_["admin_3"], show_alert=True)
        await music_on(chat_id)
        await ArchMusic.resume_stream(chat_id)
        await query.message.reply_text(_["admin_4"].format(mention))
    elif command in ["Stop", "End"]:
        await ArchMusic.stop_stream(chat_id)
        await set_loop(chat_id, 0)
        await query.message.reply_text(_["admin_9"].format(mention))
    elif command == "Mute":
        if await is_muted(chat_id):
            return await query.answer(_["admin_5"], show_alert=True)
        await mute_on(chat_id)
        await ArchMusic.mute_stream(chat_id)
        await query.message.reply_text(_["admin_6"].format(mention))
    elif command == "Unmute":
        if not await is_muted(chat_id):
            return await query.answer(_["admin_7"], show_alert=True)
        await mute_off(chat_id)
        await ArchMusic.unmute_stream(chat_id)
        await query.message.reply_text(_["admin_8"].format(mention))
    elif command == "Loop":
        await set_loop(chat_id, 3)
        await query.message.reply_text(_["admin_25"].format(mention, 3))
    elif command == "Shuffle":
        await shuffle_queue(query, chat_id, mention, _)
    elif command == "Skip":
        await skip_track(query, chat_id, mention, _)

# -------------------
# Shuffle
# -------------------

async def shuffle_queue(query, chat_id, mention, _):
    lock = queue_manager.get_lock(chat_id)
    async with lock:
        await queue_manager.shuffle_queue(chat_id)
    await query.message.reply_text(_["admin_23"].format(mention))

# -------------------
# Skip
# -------------------

async def skip_track(query, chat_id, mention, _):
    lock = queue_manager.get_lock(chat_id)
    async with lock:
        next_track = await queue_manager.pop_track(chat_id)
        if not next_track:
            await query.edit_message_text(f"{mention} tarafından atlandı")
            await query.message.reply_text(_["admin_10"].format(mention))
            return await ArchMusic.stop_stream(chat_id)

        title = next_track["title"].title()
        user = next_track["by"]
        queued = next_track["file"]
        videoid = next_track.get("vidid", "")
        streamtype = next_track.get("streamtype", "")
        duration = next_track.get("dur", "0:00")
        status = True if str(streamtype) == "video" else None
        db[chat_id][0]["played"] = 0

        if "live_" in queued:
            n, link = await YouTube.video(videoid, True)
            if n == 0:
                return await query.message.reply_text(_["admin_11"].format(title))
            await ArchMusic.skip_stream(chat_id, link, video=status)
            run = await send_stream_message(query, "1", title, videoid, duration, user)
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
        elif "vid_" in queued:
            mystic = await query.message.reply_text(_["call_10"], disable_web_page_preview=True)
            try:
                file_path, direct = await YouTube.download(videoid, mystic, videoid=True, video=status)
            except Exception:
                return await mystic.edit_text(_["call_9"])
            await ArchMusic.skip_stream(chat_id, file_path, video=status)
            run = await send_stream_message(query, "1", title, videoid, duration, user)
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
            await mystic.delete()
        elif "index_" in queued:
            await ArchMusic.skip_stream(chat_id, videoid, video=status)
            run = await send_stream_message(query, "2", title, videoid, duration, user)
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
        else:
            await ArchMusic.skip_stream(chat_id, queued, video=status)
            if videoid in ["telegram", "soundcloud"]:
                run = await send_stream_message(query, "3", title, videoid, duration, user)
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            else:
                run = await send_stream_message(query, "1", title, videoid, duration, user)
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"

        await query.edit_message_text(f"{mention} tarafından atlandı")

# -------------------
# Seek
# -------------------

async def handle_seek_commands(query, command, chat_id, mention, _):
    playing = db.get(chat_id)
    if not playing:
        return await query.answer(_["queue_2"], show_alert=True)

    duration_seconds = int(playing[0]["seconds"])
    if duration_seconds == 0:
        return await query.answer(_["admin_30"], show_alert=True)

    file_path = playing[0]["file"]
    if "index_" in file_path or "live_" in file_path:
        return await query.answer(_["admin_30"], show_alert=True)

    duration_played = int(playing[0]["played"])
    duration_to_skip = 10 if int(command) in [1,2] else 30
    duration = playing[0]["dur"]

    if int(command) in [1,3]:
        if (duration_played - duration_to_skip) <= 10:
            bet = seconds_to_min(duration_played)
            return await query.answer(
                f"Bot toplam süre aşıldığı için arama yapamıyor.\n\nŞu anda oynanan **{bet}** dakika/**{duration}** dakika",
                show_alert=True
            )
        to_seek = duration_played - duration_to_skip + 1
    else:
        if (duration_seconds - (duration_played + duration_to_skip)) <= 10:
            bet = seconds_to_min(duration_played)
            return await query.answer(
                f"Bot toplam süre aşıldığı için arama yapamıyor.\n\nŞu anda oynanan **{bet}** dakika/**{duration}** dakika",
                show_alert=True
            )
        to_seek = duration_played + duration_to_skip + 1

    await query.answer()
    mystic = await query.message.reply_text(_["admin_32"])
    try:
        await ArchMusic.seek_stream(
            chat_id,
            file_path,
            seconds_to_min(to_seek),
            duration,
            playing[0]["streamtype"],
        )
    except Exception:
        return await mystic.edit_text(_["admin_34"])

    if int(command) in [1,3]:
        db[chat_id][0]["played"] -= duration_to_skip
    else:
        db[chat_id][0]["played"] += duration_to_skip

    string = _["admin_33"].format(seconds_to_min(to_seek))
    await mystic.edit_text(f"{string}\n\nYapılan değişiklikler: {mention}")
