
import os
import asyncio
import random
import time
import datetime
from random import shuffle
from typing import List, Tuple, Union
from datetime import datetime as dt
from pyrogram import client, filters
from pyrogram.enums import *
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    User,
    ChatMember,
    CallbackQuery,
    ChatMemberUpdated,
)
from ArchMusic import app
from config import LOG_GROUP_ID, OWNER_ID
from ArchMusic.plugins.tools.kumsal import *

kumsal_tagger = {}
users = []

@app.on_message(filters.command("tag") & filters.group)
async def tag(app, message):
    admins = []
    async for member in app.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        admins.append(member.user.id)

    if message.from_user.id not in admins:
        await message.reply("❗ Bu komutu kullanmak için yönetici olmalısınız!")
        return

    args = message.command

    if len(args) > 1:
        msg_content = " ".join(args[1:])
    elif message.reply_to_message:
        msg_content = message.reply_to_message.text
        if msg_content is None:
            await message.reply("❗ Eski mesajı göremiyorum!")
            return
    else:
        msg_content = ""

    total_members = 0
    async for member in app.get_chat_members(message.chat.id):
        user = member.user
        if not user.is_bot and not user.is_deleted:
            total_members += 1
    user = message.from_user
    chat = message.chat
    
    await app.send_message(LOG_GROUP_ID, f"""

Etiket işlemi bildirimi.

Kullanan : {user.mention} [`{user.id}`]
Etiket Tipi : Tekli Tag

Grup : {chat.title}
Grup İD : `{chat.id}`

Sebep : {message.text}
"""
 )
    
    num = 1
    estimated_time = (total_members // num) * 5

    start_msg = await message.reply(f"""
**Üye etiketleme işlemi başlıyor.**

**Silinen hesapları ve botları atlayacak**

👥 __Toplam Etiketlenecek Üye Sayısı: {total_members}__
⏳ __Tahmini Süre: {estimated_time // 60} dakika__
""")
    
    kumsal_tagger[message.chat.id] = start_msg.id
    nums = 1
    usrnum = 0
    skipped_bots = 0
    skipped_deleted = 0
    total_tagged = 0
    usrtxt = ""
    
    async for member in app.get_chat_members(message.chat.id):
        user = member.user
        if user.is_bot:
            skipped_bots += 1
            continue
        if user.is_deleted:
            skipped_deleted += 1
            continue
        usrnum += 1
        total_tagged += 1
        usrtxt += f"• [{user.first_name}](tg://user?id={user.id})"
        if message.chat.id not in kumsal_tagger or kumsal_tagger[message.chat.id] != start_msg.id:
            return
        if usrnum == nums:
            await app.send_message(message.chat.id, f" **{msg_content}**\n\n{usrtxt}")
            usrnum = 0
            usrtxt = ""
            await asyncio.sleep(5)

    await app.send_message(message.chat.id, f"""
**Üye etiketleme işlemi tamamlandı** ✅

👥 __Etiketlenen üye: {total_tagged}__
🤖 __Atlanılan Bot Sayısı: {skipped_bots}__
💣 __Atlanılan Silinen Hesap Sayısı: {skipped_deleted}__
""")


@app.on_message(filters.command("guntag") & filters.group)
async def guntag(app, message):
    admins = []
    async for member in app.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        admins.append(member.user.id)

    if message.from_user.id not in admins:
        await message.reply("❗ Bu komutu kullanmak için yönetici olmalısınız!")
        return

    user = message.from_user
    chat = message.chat

    start_msg = await message.reply("☀️ **Günaydın mesajları başlıyor!** 👋")
    kumsal_tagger[message.chat.id] = start_msg.id

    skipped_bots = 0
    skipped_deleted = 0
    total_tagged = 0

    async for member in app.get_chat_members(message.chat.id):
        u = member.user
        if u.is_bot:
            skipped_bots += 1
            continue
        if u.is_deleted:
            skipped_deleted += 1
            continue

        total_tagged += 1
        # Tekli mesaj
        text = random.choice(guntag_messages).format(user=f"[{u.first_name}](tg://user?id={u.id})")
        await app.send_message(message.chat.id, text)
        await asyncio.sleep(2)  # Her kullanıcıya 2 saniye arayla

    await app.send_message(message.chat.id, f"""
**Günaydın mesajları tamamlandı!** ✅

👥 __Mesaj gönderilen üye: {total_tagged}__
🤖 __Atlanılan Bot: {skipped_bots}__
💣 __Atlanılan Silinen Hesap: {skipped_deleted}__
""")



@app.on_message(filters.command("gecetag") & filters.group)
async def gecetag(app, message):
    # Sadece yöneticiler kullanabilir
    admins = []
    async for member in app.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        admins.append(member.user.id)

    if message.from_user.id not in admins:
        await message.reply("❗ Bu komutu kullanmak için yönetici olmalısınız!")
        return

    user = message.from_user
    chat = message.chat

    start_msg = await message.reply("🌙 **İyi geceler mesajları başlıyor!** 😴")
    kumsal_tagger[chat.id] = start_msg.id

    skipped_bots = 0
    skipped_deleted = 0
    total_tagged = 0

    async for member in app.get_chat_members(chat.id):
        u = member.user
        if u.is_bot:
            skipped_bots += 1
            continue
        if u.is_deleted:
            skipped_deleted += 1
            continue

        total_tagged += 1

        # Tekli mesaj
        text = random.choice(gece_messages).format(user=f"[{u.first_name}](tg://user?id={u.id})")
        await app.send_message(chat.id, text)
        await asyncio.sleep(2)  # Her kullanıcıya 2 saniye arayla

    await app.send_message(chat.id, f"""
**İyi geceler mesajları tamamlandı!** ✅

👥 __Mesaj gönderilen üye: {total_tagged}__
🤖 __Atlanılan Bot: {skipped_bots}__
💣 __Atlanılan Silinen Hesap: {skipped_deleted}__
""")

@app.on_message(filters.command("kurttag") & filters.group)
async def kurttag(app, message):
    # Sadece adminler kullanabilir
    admins = []
    async for member in app.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        admins.append(member.user.id)

    if message.from_user.id not in admins:
        await message.reply("❗ Bu komutu kullanmak için yönetici olmalısınız!")
        return

    user = message.from_user
    chat = message.chat

    # LOG
    await app.send_message(LOG_GROUP_ID, f"""
Kurt oyunu daveti bildirimi.

Kullanan : {user.mention} [`{user.id}`]
Etiket Tipi : Tekli Kurt Tag

Grup : {chat.title}
Grup İD : `{chat.id}`

Sebep : {message.text}
""")

    start_msg = await message.reply("🐺 **Kurt oyunu başlıyor!** Silinen hesapları ve botları atlayacak.")
    kumsal_tagger[message.chat.id] = start_msg.id

    skipped_bots = 0
    skipped_deleted = 0
    total_tagged = 0

    

    async for member in app.get_chat_members(message.chat.id):
        u = member.user
        if u.is_bot:
            skipped_bots += 1
            continue
        if u.is_deleted:
            skipped_deleted += 1
            continue

        total_tagged += 1
        # Tekli mesaj
        await app.send_message(message.chat.id, f"[{u.first_name}](tg://user?id={u.id}), {random.choice(messages)}")
        await asyncio.sleep(2)  # Her kullanıcıya 2 saniye arayla

    await app.send_message(message.chat.id, f"""
**Kurt oyunu davetleri tamamlandı** ✅

👥 __Davet edilen üye: {total_tagged}__
🤖 __Atlanılan Bot: {skipped_bots}__
💣 __Atlanılan Silinen Hesap: {skipped_deleted}__
""")





@app.on_message(filters.command("tabutag") & filters.group)
async def tabutag(app, message):
    # Sadece adminler kullanabilir
    admins = []
    async for member in app.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        admins.append(member.user.id)

    if message.from_user.id not in admins:
        await message.reply("❗ Bu komutu kullanmak için yönetici olmalısınız!")
        return

    user = message.from_user
    chat = message.chat

    # LOG
    await app.send_message(LOG_GROUP_ID, f"""
Tabu oyunu daveti bildirimi.

Kullanan : {user.mention} [`{user.id}`]
Etiket Tipi : Tekli Tabu Tag

Grup : {chat.title}
Grup İD : `{chat.id}`

Sebep : {message.text}
""")

    start_msg = await message.reply("🎲 **Tabu oyunu başlıyor!** Silinen hesapları ve botları atlayacak.")
    kumsal_tagger[message.chat.id] = start_msg.id

    skipped_bots = 0
    skipped_deleted = 0
    total_tagged = 0

    async for member in app.get_chat_members(message.chat.id):
        u = member.user
        if u.is_bot:
            skipped_bots += 1
            continue
        if u.is_deleted:
            skipped_deleted += 1
            continue

        total_tagged += 1
        # Tekli mesaj, rastgele 50 mesajdan biri
        await app.send_message(
            message.chat.id,
            f"[{u.first_name}](tg://user?id={u.id}), {random.choice(tabu_messages)}"
        )
        await asyncio.sleep(2)  # Her kullanıcıya 2 saniye arayla

    await app.send_message(message.chat.id, f"""
**Tabu davetleri tamamlandı** ✅

👥 __Davet edilen üye: {total_tagged}__
🤖 __Atlanılan Bot: {skipped_bots}__
💣 __Atlanılan Silinen Hesap: {skipped_deleted}__
""")
    
#--------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------


    

@app.on_message(filters.command("utag") & filters.group)
async def utag(app, message):
    admins = []
    async for member in app.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        admins.append(member.user.id)

    if message.from_user.id not in admins:
        await message.reply("❗ Bu komutu kullanmak için yönetici olmalısınız!")
        return

    args = message.command

    if len(args) > 1:
        msg_content = " ".join(args[1:])
    elif message.reply_to_message:
        msg_content = message.reply_to_message.text
        if msg_content is None:
            await message.reply("❗ Eski mesajı göremiyorum!")
            return
    else:
        msg_content = ""

    total_members = 0
    async for member in app.get_chat_members(message.chat.id):
        user = member.user
        if not user.is_bot and not user.is_deleted:
            total_members += 1
    user = message.from_user
    chat = message.chat
    
    await app.send_message(LOG_GROUP_ID, f"""

Etiket işlemi bildirimi.

Kullanan : {user.mention} [`{user.id}`]
Etiket Tipi : Çoklu Tag

Grup : {chat.title}
Grup İD : `{chat.id}`

Sebep : {message.text}
"""
 )
    
    num = 5
    estimated_time = (total_members // num) * 5

    start_msg = await message.reply(f"""
**Üye etiketleme işlemi başlıyor.**

**Silinen hesapları ve botları atlayacak**

👥 __Toplam Etiketlenecek Üye Sayısı: {total_members}__
⏳ __Tahmini Süre: {estimated_time // 60} dakika__
""")
    
    kumsal_tagger[message.chat.id] = start_msg.id
    nums = 5
    usrnum = 0
    skipped_bots = 0
    skipped_deleted = 0
    total_tagged = 0
    usrtxt = ""
    
    async for member in app.get_chat_members(message.chat.id):
        user = member.user
        if user.is_bot:
            skipped_bots += 1
            continue
        if user.is_deleted:
            skipped_deleted += 1
            continue
        usrnum += 1
        total_tagged += 1
        usrtxt += f"• [{user.first_name}](tg://user?id={user.id})\n"
        if message.chat.id not in kumsal_tagger or kumsal_tagger[message.chat.id] != start_msg.id:
            return
        if usrnum == nums:
            await app.send_message(message.chat.id, f" **{msg_content}**\n\n{usrtxt}")
            usrnum = 0
            usrtxt = ""
            await asyncio.sleep(5)

    await app.send_message(message.chat.id, f"""
**Üye etiketleme işlemi tamamlandı** ✅

👥 __Etiketlenen üye: {total_tagged}__
🤖 __Atlanılan Bot Sayısı: {skipped_bots}__
💣 __Atlanılan Silinen Hesap Sayısı: {skipped_deleted}__
""")

@app.on_message(filters.command("cancel") & filters.group)
async def stop(app, message):
    admins = []
    async for member in app.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        admins.append(member.user.id)

    if message.from_user.id not in admins:
        await message.reply("❗ Bu komutu kullanmak için yönetici olmalısınız!")
        return
        
    if message.chat.id in kumsal_tagger:
        del kumsal_tagger[message.chat.id]
        await message.reply("⛔ __Etiketleme işlemi durduruldu!__")
    else:
        await message.reply("❗ __Etiketleme işlemi şu anda aktif değil.__")

members = {}

@app.on_message(filters.command("eros", ["/", ""]) & filters.group)
async def _eros(client: app, message: Message):
    chatID = message.chat.id
    statu = []
    if chatID in statu:
        return await message.reply("Aşıklar listesi güncelleniyor. Lütfen bekleyiniz..")

    async def scrapper(bot: app, msg: Message):
        chat_id = msg.chat.id
        temp = {}
        try:
            statu.append(chat_id)
            async for member in bot.get_chat_members(chat_id, limit=200):
                member: ChatMember

                if member.user.is_bot:
                    continue
                if member.user.is_deleted:
                    continue

                temp[member.user.id] = member.user
                await asyncio.sleep(0.05)

            members[chat_id]["members"] = temp
            members[chat_id]["lastUpdate"] = dt.now()
            statu.remove(chat_id)
            return True
        except Exception as e:
            print(e)
            return False

    async def ship_(users: dict):
        list_ = list(users.keys())
        random.shuffle(list_)

        member1ID = random.choice(list_)
        member2ID = random.choice(list_)

        while member1ID == member2ID:
            member2ID = random.choice(list_)

        member1: User = users[member1ID]
        member2: User = users[member2ID]

        mention1 = member1.mention if not member1.username else f"@{member1.username}"
        mention2 = member2.mention if not member2.username else f"@{member2.username}"

        text = f"**💘 ᴇʀᴏs'ᴜɴ ᴏᴋᴜ ᴀᴛɪʟᴅɪ.\n• ᴀsɪᴋʟᴀʀ  :\n\n{mention1} {random.choice(galp)} {mention2}**\n\n`ᴜʏᴜᴍʟᴜʟᴜᴋ ᴏʀᴀɴɪ: %{random.randint(0, 100)}`"
        return text

    if chatID not in members:
        members[chatID] = {}

    lastUpdate: dt = members[chatID].get("lastUpdate")
    if lastUpdate:
        now = dt.now()
        diff = now - lastUpdate
        if diff.seconds > 3600 * 4:
            msg = await message.reply(
                "Aşıklar listesi güncelleniyor, lütfen bekleyiniz..."
            )
            status = await scrapper(client, message)
            if status:
                await msg.delete()
                text = await ship_(members[chatID]["members"])
                return await message.reply(text)
            else:
                return await msg.edit(
                    "Bir hata oluştu, lütfen daha sonra tekrar deneyiniz."
                )
        else:
            text = await ship_(members[chatID]["members"])
            return await message.reply(text)

    else:
        msg = await message.reply("Aşıklar listesi güncelleniyor, lütfen bekleyiniz...")
        status = await scrapper(client, message)
        if status:
            await msg.delete()
            text = await ship_(members[chatID]["members"])
            return await message.reply(text)
        else:
            return await msg.edit(
                "Bir hata oluştu, lütfen daha sonra tekrar deneyiniz."
            )

chatMode = []

chat_mode_users = {}

@app.on_message(filters.command("chatmode") & filters.group)
async def chat_mode_controller(bot: app, msg: Message):
    admins = []
    async for member in bot.get_chat_members(msg.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        admins.append(member.user.id)

    if msg.from_user.id not in admins:
        await msg.reply("❗ Bu komutu kullanmak için yönetici olmalısınız!")
        return
        
    chat_id = msg.chat.id
    chat = msg.chat
    commands = msg.command
    chat_mode_users[chat_id] = msg.from_user.id  # Komutu gönderen kullanıcıyı kaydet

    await bot.send_message(LOG_GROUP_ID, f"""
#CHATMODE KULLANILDI
👤 Kullanan : [{msg.from_user.first_name}](tg://user?id={msg.from_user.id})
💥 Kullanıcı Id : {msg.from_user.id}
🪐 Kullanılan Grup : {chat.title}
💡 Grup ID : {chat.id}
◀️ Grup Link : @{chat.username}
""")
    
    if len(commands) == 1:
        status = "✅ Açık" if chat_id in chatMode else "❌ Kapalı"
        return await msg.reply(
            f"Durum : {status}\n\nSohbet modu kullanıcıların mesajlarına cevap verir.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Aç", callback_data="on"),
                        InlineKeyboardButton("Kapat", callback_data="off"),
                    ]
                ]
            ),
        )

@app.on_callback_query(filters.regex("^(on|off)$"))
async def chat_mode_callback(bot: app, cb: CallbackQuery):
    chat_id = cb.message.chat.id
    user_id = cb.from_user.id
    cmd = cb.data

    if chat_id not in chat_mode_users or chat_mode_users[chat_id] != user_id:
        await cb.answer("Bu işlemi yapma yetkiniz yok.", show_alert=True)
        return

    if cmd == "on":
        if chat_id in chatMode:
            await cb.edit_message_text("Sohbet modu zaten açık.")
        else:
            chatMode.append(chat_id)
            await cb.edit_message_text("Sohbet modu açıldı.")
    elif cmd == "off":
        if chat_id not in chatMode:
            await cb.edit_message_text("Sohbet modu zaten kapalı.")
        else:
            chatMode.remove(chat_id)
            await cb.edit_message_text("Sohbet modu kapatıldı.")

    await cb.answer()  


@app.on_message(filters.group & filters.text & ~filters.command("chatmode"), group=10)
async def chatModeHandler(bot: app, msg: Message):
    def lower(text):
        return str(text.translate({ord("I"): ord("ı"), ord("İ"): ord("i")})).lower()

    def kontrol(query: Union[str, list], text: str) -> bool:
        if isinstance(query, str):
            return query in text.split()
        elif isinstance(query, list):
            for q in query:
                if q in text.split():
                    return True
            return False
        else:
            return False

    if msg.chat.id not in chatMode or msg.from_user.is_self:
        return

    text = lower(msg.text)  # * Mesajı küçük harfe çeviriyoruz

    reply = None

    if text.startswith("Aynur"): # * Mesaj buse ile başlıyorsa cevap veriyoruz
        reply = random.choice(Aynur)
        await asyncio.sleep(0.06)
    
    elif kontrol(["selam", "slm", "sa", "selamlar", "selamm"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(slm)
        await asyncio.sleep(0.06)   
        #Bot chatmode komutları
    elif kontrol(["sahip"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(sahip)
        await asyncio.sleep(0.06)   
    
    elif kontrol(["naber"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(naber)
        await asyncio.sleep(0.06)  
         
    elif kontrol(["pelin"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(pelin)
        await asyncio.sleep(0.06)        
                 
    elif kontrol(["nasılsın"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(nasılsın)
        await asyncio.sleep(0.06)         
         
    elif kontrol(["tm","tamam","tmm"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(tm)
        await asyncio.sleep(0.06)          
         
    elif kontrol(["sus","suuss","suss"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(sus)
        await asyncio.sleep(0.06)  
    
    elif kontrol(["merhaba","mrb","meraba"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(merhaba)
        await asyncio.sleep(0.06)   
    
    elif kontrol(["yok"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(yok)
        await asyncio.sleep(0.06)   
        
    elif kontrol(["dur"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(dur)
        await asyncio.sleep(0.06)        
                 
    elif kontrol(["bot", "botu"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(bott)
        await asyncio.sleep(0.06)         
         
    elif kontrol(["napıyorsun"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(napıyorsun)
        await asyncio.sleep(0.06)          
         
    elif kontrol(["takılıyorum","takılıyom"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(takılıyorum)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["he"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(he)
        await asyncio.sleep(0.06)   
    
    elif kontrol(["hayır"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(hayır)
        await asyncio.sleep(0.06)   
        
    elif kontrol(["tm"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(tm)
        await asyncio.sleep(0.06)        
                 
    elif kontrol(["nerdesin"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(nerdesin)
        await asyncio.sleep(0.06)         
         
    elif kontrol(["özledim"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(özledim)
        await asyncio.sleep(0.06)          
         
    elif kontrol(["bekle"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(bekle)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["tünaydın"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(tünaydın)
        await asyncio.sleep(0.06)   
    
    elif kontrol(["günaydın"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(günaydın)
        await asyncio.sleep(0.06)   
        
    elif kontrol(["sohbetler"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(sohbetler)
        await asyncio.sleep(0.06)        
               
    elif kontrol(["konuşalım","konusalım"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(konuşalım)
        await asyncio.sleep(0.06)         
         
    elif kontrol(["saat"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(saat)
        await asyncio.sleep(0.06)          
         
    elif kontrol(["geceler"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(geceler)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["şaka"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(şaka)
        await asyncio.sleep(0.06)   
    
    elif kontrol(["kimsin"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(kimsin)
        await asyncio.sleep(0.06)   
        
    elif kontrol(["günler"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(günler)
        await asyncio.sleep(0.06)        
                 
    elif kontrol(["tanımıyorum"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(tanımıyorum)
        await asyncio.sleep(0.06)         
         
    elif kontrol(["konuşma"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(konuşma)
        await asyncio.sleep(0.06)          
         
    elif kontrol(["teşekkürler","tesekkürler","tşkr"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(teşekkürler)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["eyvallah","eywl"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(eyvallah)
        await asyncio.sleep(0.06)   
    
    elif kontrol(["sağol"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(sağol)
        await asyncio.sleep(0.06)   
        
    elif kontrol(["amk","aq","mg","mk"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(amk)
        await asyncio.sleep(0.06)        
                 
    elif kontrol(["yoruldum"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(yoruldum)
        await asyncio.sleep(0.06)         
         
    elif kontrol(["yaş"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(yaş)
        await asyncio.sleep(0.06)          
         
    elif kontrol(["eşşek","eşek"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(eşek)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["canım"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(canım)
        await asyncio.sleep(0.06)   
    
    elif kontrol(["aşkım","askım","ask"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(aşkım)
        await asyncio.sleep(0.06)   
        
    elif kontrol(["uyu"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(uyu)
        await asyncio.sleep(0.06)        
                 
    elif kontrol(["nereye","nere"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(nereye)
        await asyncio.sleep(0.06)         
         
    elif kontrol(["naber"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(naber)
        await asyncio.sleep(0.06)          
         
    elif kontrol(["küstüm","küsüm"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(küstüm)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["peki"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(peki)
        await asyncio.sleep(0.06)   
    
    elif kontrol(["ne","nee","neee","ney"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(ne)
        await asyncio.sleep(0.06)   
        
    elif kontrol(["takım"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(takım)
        await asyncio.sleep(0.06)        
                 
    elif kontrol(["benimle","bnmle"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(benimle)
        await asyncio.sleep(0.06)         
         
    elif kontrol(["seviyormusun","seviyomusun"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(seviyormusun)
        await asyncio.sleep(0.06)          
         
    elif kontrol(["nediyon"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(nediyon)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["özür"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(özür)
        await asyncio.sleep(0.06)   
    
    elif kontrol(["niye"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(niye)
        await asyncio.sleep(0.06)   
        
    elif kontrol(["bilmiyorum","bilmiyom","bilmiyos"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(bilmiyorum)
        await asyncio.sleep(0.06)        
                 
    elif kontrol(["küsme"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(küsme)
        await asyncio.sleep(0.06)         
         
    elif kontrol(["kumsal"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(kumsal)
        await asyncio.sleep(0.06)          
         
    elif kontrol(["nerelisin"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(nerelisin)
        await asyncio.sleep(0.06)  
    
    elif kontrol(["sevgilin"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(sevgilin)
        await asyncio.sleep(0.06)   
    
    elif kontrol(["olur"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(olur)
        await asyncio.sleep(0.06)   
        
    elif kontrol(["olmas","olmaz"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(olmaz)
        await asyncio.sleep(0.06)        
                 
    elif kontrol(["nasıl"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(nasıl)
        await asyncio.sleep(0.06)         
         
    elif kontrol(["hayatım"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(hayatım)
        await asyncio.sleep(0.06)          
         
    elif kontrol(["cus"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(cus)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["vallaha","valla","vallahi"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(vallaha)
        await asyncio.sleep(0.06)   
    
    elif kontrol(["yo"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(yo)
        await asyncio.sleep(0.06)   
        
    elif kontrol(["hayırdır"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(hayırdır)
        await asyncio.sleep(0.06)        
                 
    elif kontrol(["of"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(of)
        await asyncio.sleep(0.06)         
         
    elif kontrol(["aynen"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(aynen)
        await asyncio.sleep(0.06)          
         
    elif kontrol(["ağla"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(ağla)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["ağlama"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(ağlama)
        await asyncio.sleep(0.06)   
    
    elif kontrol(["sex","seks"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(sex)
        await asyncio.sleep(0.06)   
        
    elif kontrol(["evet"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(evet)
        await asyncio.sleep(0.06)        
                 
    elif kontrol(["hmm","hm","hımm","hmmm"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(hmm)
        await asyncio.sleep(0.06)         
         
    elif kontrol(["hıhım"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(hıhım)
        await asyncio.sleep(0.06)          
         
    elif kontrol(["git"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(git)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["komedi"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(komedi)
        await asyncio.sleep(0.06)   
    
    elif kontrol(["knka","kanka"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(knka)
        await asyncio.sleep(0.06)   
        
    elif kontrol(["ban"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(ban)
        await asyncio.sleep(0.06)        
                 
    elif kontrol(["sen"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(sen)
        await asyncio.sleep(0.06)         
         
    elif kontrol(["hiç"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(hiç)
        await asyncio.sleep(0.06)          
         
    elif kontrol(["aç","ac","açç"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(aç)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["barışalım","batısalım"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(barışalım)
        await asyncio.sleep(0.06)   
    
    elif kontrol(["şimdi"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(şimdi)
        await asyncio.sleep(0.06)   
        
    elif kontrol(["varoş"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(varoş)
        await asyncio.sleep(0.06)        
                 
    elif kontrol(["arkadaş","arkadas"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(arkadaş)
        await asyncio.sleep(0.06)         
         
    elif kontrol(["sus","suss","suus"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(sus)
        await asyncio.sleep(0.06)          
         
    elif kontrol(["üzüldüm","üşüldüm"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(üzüldüm)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["kötü"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(kötü)
        await asyncio.sleep(0.06)   
    
    elif kontrol(["akşamlar"], text): # * Selam yazısı metnin içinde varsa cevap veriyoruz
        reply = random.choice(akşamlar)
        await asyncio.sleep(0.06)   
        
    try:
        await msg.reply(reply)
    except Exception as e:
        print(e)

    msg.continue_propagation()  #! BURAYA DOKUNMA

@app.on_message(filters.command(commandList))
async def games(c: app, m: Message):
        
    "🎲", "🎯", "🏀", "⚽", "🎳", "🎰"

    command = m.command[0]

    if command == "zar":
        return await c.send_dice(m.chat.id, emoji="🎲",
                                 reply_markup=InlineKeyboardMarkup(
                                        [
                                            [
                                                InlineKeyboardButton(
                                                    "Tekrar Oyna ♻️", callback_data="zar"
                                                ),
                                            ]
                                        ]
                                    )
                                )

    elif command == "dart":
        return await c.send_dice(m.chat.id, emoji="🎯",
                                    reply_markup=InlineKeyboardMarkup(
                                            [
                                                [
                                                    InlineKeyboardButton(
                                                        "Tekrar Oyna ♻️", callback_data="dart"
                                                    ),
                                                ]
                                            ]
                                        )
                                    )

    elif command == "basket":
        return await c.send_dice(m.chat.id, emoji="🏀",
                                    reply_markup=InlineKeyboardMarkup(
                                            [
                                                [
                                                    InlineKeyboardButton(
                                                        "Tekrar Oyna ♻️", callback_data="basket"
                                                    ),
                                                ]
                                            ]
                                        )
                                    )

    elif command == "futbol":
        return await c.send_dice(m.chat.id, emoji="⚽",
                                    reply_markup=InlineKeyboardMarkup(
                                            [
                                                [
                                                    InlineKeyboardButton(
                                                        "Tekrar Oyna ♻️", callback_data="futbol"
                                                    ),
                                                ]
                                            ]
                                        )
                                    )

    elif command == "bowling":
        return await c.send_dice(m.chat.id, emoji="🎳",
                                    reply_markup=InlineKeyboardMarkup(
                                            [
                                                [
                                                    InlineKeyboardButton(
                                                        "Tekrar Oyna ♻️", callback_data="bowling"
                                                    ),
                                                ]
                                            ]
                                        )
                                    )

    elif command == "slot":
        return await c.send_dice(m.chat.id, emoji="🎰",
                                    reply_markup=InlineKeyboardMarkup(
                                            [
                                                [
                                                    InlineKeyboardButton(
                                                        "Tekrar Oyna ♻️", callback_data="slot"
                                                    ),
                                                ]
                                            ]
                                        )
                                    )

    elif command == "para":
        return await m.reply(
            "**Yazı 🪙**" if random.randint(0, 1) == 0 else "**Tura 🪙**"
        )

    elif command == "mani":
        return await m.reply_text(random.choice(mani))

    elif command == "saka":
        return await m.reply_text(f"**{random.choice(espri)}**")

    elif command == "d":
        return await m.reply_text(
            f"**✅ Doğruluk mu ? 🔪 Cesaret mi ? \n\n{m.from_user.mention} Doğruluk sorusu seçti !\n\n{random.choice(D_LİST)}**"
        )

    elif command == "c":
        return await m.reply_text(
            f"**✅ Doğruluk mu ? 🔪 Cesaret mi ? \n\n{m.from_user.mention} Cesaret sorusu seçti !\n\n{random.choice(C_LİST)}**"
        )


    return
# * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@app.on_callback_query(filters.regex("zar"))
async def zar(client: app, query: CallbackQuery):
    await client.send_dice(query.message.chat.id, emoji="🎲",
                           reply_markup=InlineKeyboardMarkup(
                                [
                                    [
                                        InlineKeyboardButton(
                                            "Tekrar Oyna ♻️", callback_data="zar"
                                        ),
                                    ]
                                ]
                            )
                        )

@app.on_callback_query(filters.regex("dart"))
async def dart(client: app, query: CallbackQuery):
    await client.send_dice(query.message.chat.id, emoji="🎯",
                           reply_markup=InlineKeyboardMarkup(
                                [
                                    [
                                        InlineKeyboardButton(
                                            "Tekrar Oyna ♻️", callback_data="dart"
                                        ),
                                    ]
                                ]
                            )
                        )

@app.on_callback_query(filters.regex("basket"))
async def basket(client: app, query: CallbackQuery):
    await client.send_dice(query.message.chat.id, emoji="🏀",
                           reply_markup=InlineKeyboardMarkup(
                                [
                                    [
                                        InlineKeyboardButton(
                                            "Tekrar Oyna ♻️", callback_data="basket"
                                        ),
                                    ]
                                ]
                            )
                        )

@app.on_callback_query(filters.regex("futbol"))
async def futbol(client: app, query: CallbackQuery):
    await client.send_dice(query.message.chat.id, emoji="⚽",
                           reply_markup=InlineKeyboardMarkup(
                                [
                                    [
                                        InlineKeyboardButton(
                                            "Tekrar Oyna ♻️", callback_data="futbol"
                                        ),
                                    ]
                                ]
                            )
                        )

@app.on_callback_query(filters.regex("bowling"))
async def bowling(client: app, query: CallbackQuery):
    await client.send_dice(query.message.chat.id, emoji="🎳",
                           reply_markup=InlineKeyboardMarkup(
                                [
                                    [
                                        InlineKeyboardButton(
                                            "Tekrar Oyna ♻️", callback_data="bowling"
                                        ),
                                    ]
                                ]
                            )
                        )

@app.on_callback_query(filters.regex("slot"))
async def slot(client: app, query: CallbackQuery):
    await client.send_dice(query.message.chat.id, emoji="🎰",
                           reply_markup=InlineKeyboardMarkup(
                                [
                                    [
                                        InlineKeyboardButton(
                                            "Tekrar Oyna ♻️", callback_data="slot"
                                        ),
                                    ]
                                ]
                            )
                        )


@app.on_message(filters.command(["slap", "sille"]) & filters.group)
async def slap(bot: app, message: Message):
        
    chat = message.chat
    if not message.reply_to_message:
        await message.reply_text("🚫 **Bir kullanıcıya cevap verin!**")
        return
    if message.reply_to_message.from_user.id == OWNER_ID:
        await message.reply_text(f"{random.choice(dontslapown)}")
        return
    if message.reply_to_message.from_user.id == app.id:
        await message.reply_text(f"{random.choice(dontslapme)}")
        return
    

    atan = message.from_user
    yiyen = message.reply_to_message.from_user

    atan_mesaj = f"[{atan.first_name}](tg://user?id={atan.id})"
    yiyen_mesaj = f"[{yiyen.first_name}](tg://user?id={yiyen.id})"

    goktug = random.choice(slapmessage)
    await message.reply_text(
        goktug.format(atan_mesaj, yiyen_mesaj),
    )

    await bot.send_message(
        LOG_GROUP_ID,
        f"""
👤 Kullanan : [{atan.first_name}](tg://user?id={atan.id})
💥 Kullanıcı Id : {atan.id}
🪐 Kullanılan Grup : {chat.title}
💡 Grup ID : {chat.id}
◀️ Grup Link : @{chat.username}
📚 Kullanılan Modül : {message.text}
"""
    )

@app.on_message(filters.command(["oner"]) & filters.group)
async def oner(bot: app, message: Message):
        
    chat = message.chat
    if not message.reply_to_message:
        await message.reply_text("🚫 Bir kullanıcıya cevap verin!")
        return
    if message.reply_to_message.from_user.id == OWNER_ID:
        await message.reply_text(f"{random.choice(sarki1)}")
        return
    if message.reply_to_message.from_user.id == app.id:
        await message.reply_text(f"{random.choice(sarki2)}")
        return
    

    atan = message.from_user
    yiyen = message.reply_to_message.from_user

    atan_mesaj = f"[{atan.first_name}](tg://user?id={atan.id})"
    yiyen_mesaj = f"[{yiyen.first_name}](tg://user?id={yiyen.id})"

    goktug = random.choice(sarkilar)
    await message.reply_text(
        goktug.format(atan_mesaj, yiyen_mesaj),
    )

    await bot.send_message(
        LOG_GROUP_ID,
        f"""
👤 Kullanan : [{atan.first_name}](tg://user?id={atan.id})
💥 Kullanıcı Id : {atan.id}
🪐 Kullanılan Grup : {chat.title}
💡 Grup ID : {chat.id}
◀️ Grup Link : @{chat.username}
📚 Kullanılan Modül : Şarkı Öneri
"""
    )
