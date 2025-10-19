from typing import Union
from pyrogram.types import InlineKeyboardButton

from config import SUPPORT_CHANNEL, SUPPORT_GROUP
from ArchMusic import app


def start_pannel(_):
    buttons = [
        [
            InlineKeyboardButton(text=_["S_B_1"], url=f"https://t.me/{app.username}?start=help"),
            InlineKeyboardButton(text=_["S_B_2"], callback_data="settings_helper"),
        ]
    ]

    # Destek butonları
    support_buttons = []
    if SUPPORT_CHANNEL:
        support_buttons.append(InlineKeyboardButton(text=_["S_B_4"], url=SUPPORT_CHANNEL))
    if SUPPORT_GROUP:
        support_buttons.append(InlineKeyboardButton(text=_["S_B_3"], url=SUPPORT_GROUP))

    if support_buttons:
        buttons.append(support_buttons)

    return buttons


def private_panel(_, BOT_USERNAME, OWNER: Union[bool, int] = None):
    buttons = [[InlineKeyboardButton(text=_["S_B_8"], callback_data="settings_back_helper")]]

    # Destek ve Owner butonları aynı satırda
    support_buttons = []
    if SUPPORT_CHANNEL:
        support_buttons.append(InlineKeyboardButton(text=_["S_B_4"], url=SUPPORT_CHANNEL))
    if SUPPORT_GROUP:
        support_buttons.append(InlineKeyboardButton(text=_["S_B_3"], url=SUPPORT_GROUP))
    if OWNER:
        support_buttons.append(InlineKeyboardButton(text=_["S_B_7"], user_id=OWNER))

    if support_buttons:
        buttons.append(support_buttons)

    # Botu gruba ekleme butonu
    buttons.append([InlineKeyboardButton(text=_["S_B_5"], url=f"https://t.me/{BOT_USERNAME}?startgroup=true")])

    return buttons
                                                    
