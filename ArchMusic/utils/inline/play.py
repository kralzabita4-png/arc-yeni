from pyrogram.types import InlineKeyboardButton
import random

# ===============================================
# 💠 Kumsal Bots - Mavi Arayüz (Deluxe Edition)
# Parıltılı • Akıcı • Premium Hissiyat
# ===============================================

def magic_bar():
    bars = [
        "★彡[▰▱▰▱▰▱▰▱]彡★",
        "✦☄️▁▂▃▄▅▆▇█▇▆▅▄▃▂▁☄️✦",
        "💠╌╌◦▰▱▰▱▰▱◦╌╌💠",
        "✨❯▰▱▰▱▰▱▰▱❮✨",
        "🌊⟪▰▱▰▱▰▱▰▱⟫🌊",
        "🌌·•▰▱▰▱▰▱▰▱•·🌌",
    ]
    return random.choice(bars)


def blue_footer(close_data):
    """Alt bar: sabit Mavi + Kapat kombinasyonu"""
    return [
        InlineKeyboardButton("💠 Mavi", url="https://t.me/MaviDuyuru"),
        InlineKeyboardButton("🚫 Kapat", callback_data=close_data)
    ]


# ───────────────────────────────
# 🎶 Stream Başlat Menüsü
# ───────────────────────────────
def stream_markup(_, videoid, chat_id):
    bar = magic_bar()
    return [
        [InlineKeyboardButton(bar, callback_data="bar_locked")],
        [
            InlineKeyboardButton("🎧 Sesli Oynat", callback_data=f"stream_play {videoid}|{chat_id}"),
            InlineKeyboardButton("📺 Görsel Oynat", callback_data=f"stream_video {videoid}|{chat_id}")
        ],
        blue_footer(f"forceclose {videoid}|{chat_id}")
    ]


# ───────────────────────────────
# 🎵 Şarkı Seçimi (Track)
# ───────────────────────────────
def track_markup(_, videoid, user_id, channel, fplay):
    bar = magic_bar()
    return [
        [InlineKeyboardButton(bar, callback_data="bar_locked")],
        [
            InlineKeyboardButton("🎧 Sesli", callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}"),
            InlineKeyboardButton("🎥 Görsel", callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}")
        ],
        [
            InlineKeyboardButton("⏪ Önceki", callback_data=f"slider B|Track|{user_id}"),
            InlineKeyboardButton("⏩ Sonraki", callback_data=f"slider F|Track|{user_id}")
        ],
        blue_footer(f"forceclose {videoid}|{user_id}")
    ]


# ───────────────────────────────
# ⚙️ Kontrol Paneli (Tek Sayfa – Deluxe)
# ───────────────────────────────
def control_panel(_, videoid, chat_id):
    bar = magic_bar()
    return [
        [InlineKeyboardButton(bar, callback_data="bar_locked")],
        [
            InlineKeyboardButton("⏸", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton("▶️", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton("⏹", callback_data=f"ADMIN Stop|{chat_id}")
        ],
        [
            InlineKeyboardButton("🔇", callback_data=f"ADMIN Mute|{chat_id}"),
            InlineKeyboardButton("🔊", callback_data=f"ADMIN Unmute|{chat_id}"),
            InlineKeyboardButton("🔁", callback_data=f"ADMIN Loop|{chat_id}")
        ],
        [
            InlineKeyboardButton("⏮ 10s", callback_data=f"ADMIN 1|{chat_id}"),
            InlineKeyboardButton("⏭ 10s", callback_data=f"ADMIN 2|{chat_id}")
        ],
        [
            InlineKeyboardButton("💫 Karıştır", callback_data=f"ADMIN Shuffle|{chat_id}"),
            InlineKeyboardButton("⏭ Atla", callback_data=f"ADMIN Skip|{chat_id}")
        ],
        blue_footer(f"forceclose {videoid}|{chat_id}")
    ]