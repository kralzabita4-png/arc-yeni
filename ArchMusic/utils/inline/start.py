from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from ArchMusic import app  # Botun ana uygulaması

def start_pannel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text="▶️ " + _["S_B_1"],
                url=f"https://t.me/{app.username}?start=help",
            ),
            InlineKeyboardButton(
                text="⚙️ " + _["S_B_2"],
                callback_data="settings_helper"
            ),
        ],
    ]
    # Buraya destek kanalı ve grubu ekleyebilirsin, örnek:
    # buttons.append([
    #     InlineKeyboardButton(text="📢 " + _["S_B_4"], url="https://t.me/supportchannel"),
    #     InlineKeyboardButton(text="💬 " + _["S_B_3"], url="https://t.me/supportgroup"),
    # ])
    return buttons

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message: Message):
    _ = {
        "S_B_1": "Başlat",
        "S_B_2": "Ayarlar",
        "S_B_3": "Destek Grubu",
        "S_B_4": "Duyuru Kanalı"
    }
    buttons = start_pannel(_)
    await message.reply_text(
        "🎵 Merhaba! İşte seçenekleriniz:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
