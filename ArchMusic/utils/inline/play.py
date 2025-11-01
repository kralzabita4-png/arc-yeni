from pyrogram.types import InlineKeyboardButton
import random


# ===============================================
# 🌌 Kumsal Bots - Mavi Arayüz (Tam Panel Sürümü)
# Üstte Mavi Bar + Alt Kısımda 💠 Mavi & ❌ Kapat
# ===============================================


def random_bar():
    bars = [
        "▁▂▃▄▅▆▇█▇▆▅▄▃▂▁",
        "▰▱▰▱▰▱▰▱▰▱",
        "⠂⠄⠆⠇⠋⠙⠸⠼⠾⠷⠶⠦⠤⠂",
        "▁▃▅▇▅▃▁",
        "⣀⣤⣶⣷⣶⣤⣀",
        "▁▄▂▇▄▅▄▅▃",
        "▃▁▇▂▅▃▄▃▅",
        "▁▇▄▂▅▄▅▃▄",
    ]
    return random.choice(bars)


# ───────────────────────────────
# 🎵 Stream Menüsü
# ───────────────────────────────
def stream_markup(_, videoid, chat_id):
    bar = random_bar()
    buttons = [
        [InlineKeyboardButton(text=bar, callback_data="bar_locked")],
        [
            InlineKeyboardButton(text="💠 Mavi", url="https://t.me/MaviDuyuru"),
            InlineKeyboardButton(text="❌ Kapat", callback_data=f"forceclose {videoid}|{chat_id}")
        ]
    ]
    return buttons


# ───────────────────────────────
# 🧩 Track Seçimi
# ───────────────────────────────
def track_markup(_, videoid, user_id, channel, fplay):
    bar = random_bar()
    buttons = [
        [InlineKeyboardButton(text=bar, callback_data="bar_locked")],
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(text="💠 Mavi", url="https://t.me/MaviDuyuru"),
            InlineKeyboardButton(text="❌ Kapat", callback_data=f"forceclose {videoid}|{user_id}")
        ],
    ]
    return buttons


# ───────────────────────────────
# 📜 Playlist Menüsü
# ───────────────────────────────
def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    bar = random_bar()
    buttons = [
        [InlineKeyboardButton(text=bar, callback_data="bar_locked")],
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"YukkiPlaylists {videoid}|{user_id}|{ptype}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"YukkiPlaylists {videoid}|{user_id}|{ptype}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(text="💠 Mavi", url="https://t.me/MaviDuyuru"),
            InlineKeyboardButton(text="❌ Kapat", callback_data=f"forceclose {videoid}|{user_id}")
        ],
    ]
    return buttons


# ───────────────────────────────
# 📺 Canlı Yayın Menüsü
# ───────────────────────────────
def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    bar = random_bar()
    buttons = [
        [InlineKeyboardButton(text=bar, callback_data="bar_locked")],
        [
            InlineKeyboardButton(
                text=_["P_B_3"],
                callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(text="💠 Mavi", url="https://t.me/MaviDuyuru"),
            InlineKeyboardButton(text="❌ Kapat", callback_data=f"forceclose {videoid}|{user_id}")
        ],
    ]
    return buttons


# ───────────────────────────────
# 🔄 Slider Query Menüsü
# ───────────────────────────────
def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    bar = random_bar()
    query = f"{query[:20]}"
    buttons = [
        [InlineKeyboardButton(text=bar, callback_data="bar_locked")],
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="❮",
                callback_data=f"slider B|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text="❯",
                callback_data=f"slider F|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(text="💠 Mavi", url="https://t.me/MaviDuyuru"),
            InlineKeyboardButton(text="❌ Kapat", callback_data=f"forceclose {query}|{user_id}")
        ],
    ]
    return buttons


# ───────────────────────────────
# ⚙️ Kontrol Paneli (Sayfa 1)
# ───────────────────────────────
def panel_markup_1(_, videoid, chat_id):
    bar = random_bar()
    buttons = [
        [InlineKeyboardButton(text=bar, callback_data="bar_locked")],
        [
            InlineKeyboardButton(text="⏸ Pause", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="▶️ Resume", callback_data=f"ADMIN Resume|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="⏯ Skip", callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton(text="⏹ Stop", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="💠 Mavi", url="https://t.me/MaviDuyuru"),
            InlineKeyboardButton(text="❌ Kapat", callback_data=f"forceclose {videoid}|{chat_id}")
        ],
    ]
    return buttons


# ───────────────────────────────
# ⚙️ Kontrol Paneli (Sayfa 2)
# ───────────────────────────────
def panel_markup_2(_, videoid, chat_id):
    bar = random_bar()
    buttons = [
        [InlineKeyboardButton(text=bar, callback_data="bar_locked")],
        [
            InlineKeyboardButton(text="🔇 Mute", callback_data=f"ADMIN Mute|{chat_id}"),
            InlineKeyboardButton(text="🔊 Unmute", callback_data=f"ADMIN Unmute|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="🔀 Shuffle", callback_data=f"ADMIN Shuffle|{chat_id}"),
            InlineKeyboardButton(text="🔁 Loop", callback_data=f"ADMIN Loop|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="💠 Mavi", url="https://t.me/MaviDuyuru"),
            InlineKeyboardButton(text="❌ Kapat", callback_data=f"forceclose {videoid}|{chat_id}")
        ],
    ]
    return buttons


# ───────────────────────────────
# ⚙️ Kontrol Paneli (Sayfa 3)
# ───────────────────────────────
def panel_markup_3(_, videoid, chat_id):
    bar = random_bar()
    buttons = [
        [InlineKeyboardButton(text=bar, callback_data="bar_locked")],
        [
            InlineKeyboardButton(text="⏮ 10 Saniye", callback_data=f"ADMIN 1|{chat_id}"),
            InlineKeyboardButton(text="⏭ 10 Saniye", callback_data=f"ADMIN 2|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="⏮ 30 Saniye", callback_data=f"ADMIN 3|{chat_id}"),
            InlineKeyboardButton(text="⏭ 30 Saniye", callback_data=f"ADMIN 4|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="💠 Mavi", url="https://t.me/MaviDuyuru"),
            InlineKeyboardButton(text="❌ Kapat", callback_data=f"forceclose {videoid}|{chat_id}")
        ],
    ]
    return buttons