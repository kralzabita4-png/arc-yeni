import asyncio
import random
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait

from config import BANNED_USERS
from ArchMusic import app
from ArchMusic.utils.decorators.language import language

tag_sessions = {}

@app.on_message(
    filters.command(["tag", "utag"])
    & filters.group
    & ~BANNED_USERS
)
@language
async def tag_with_approval(client, message: Message, _):
    chat_id = message.chat.id
    user_id = message.from_user.id
    args = message.text.split()

    custom_msg = "Selam!"
    limit = None
    random_pick = False
    only_admins = False
    flood_delay = 1.0
    chunk_size = 5
    role_filter = None

    if len(args) > 1:
        if "-r" in args:
            random_pick = True
            try: limit = int(args[args.index("-r") + 1])
            except: return await message.reply_text("Geçersiz sayı: -r [sayı]")
        if "-l" in args:
            try: limit = int(args[args.index("-l") + 1])
            except: return await message.reply_text("Geçersiz sayı: -l [sayı]")
        if "-a" in args:
            only_admins = True
        if "-f" in args:
            try: flood_delay = float(args[args.index("-f") + 1])
            except: return await message.reply_text("Geçersiz süre: -f [saniye]")
        if "-c" in args:
            try: chunk_size = int(args[args.index("-c") + 1])
            except: return await message.reply_text("Geçersiz: -c [kişi sayısı]")
        if "-role" in args:
            try: role_filter = args[args.index("-role") + 1].lower()
            except: return await message.reply_text("Rol tanımlanamadı.")

        clean_args = [
            arg for arg in args[1:]
            if arg not in ["-r", "-l", "-a", "-f", "-c", "-role"]
            and not arg.replace('.', '', 1).isdigit()
        ]
        if clean_args:
            custom_msg = " ".join(clean_args)

    single_mode = message.command[0].lower() == "tag"

    members = []
    async for member in client.get_chat_members(chat_id):
        user = member.user
        if user.is_bot:
            continue
        if only_admins and member.status not in ["administrator", "creator"]:
            continue
        if role_filter:
            uname = (user.username or "").lower()
            fname = (user.first_name or "").lower()
            lname = (user.last_name or "").lower()
            bio = (await client.get_chat_member(chat_id, user.id)).user.bio or ""
            bio = bio.lower() if bio else ""
            if role_filter not in uname and role_filter not in fname and role_filter not in lname and role_filter not in bio:
                continue
        members.append(user)

    if not members:
        return await message.reply_text("Etiketlenecek uygun kullanıcı bulunamadı.")

    if random_pick:
        members = random.sample(members, min(limit or len(members), len(members)))
    elif limit:
        members = members[:limit]

    tag_sessions[chat_id] = {
        "active": False,
        "last": None,
        "approved": False,
        "members": members,
        "msg": custom_msg,
        "single": single_mode,
        "chunk": chunk_size,
        "flood": flood_delay,
        "from": user_id,
    }

    info_text = (
        "📢 **Etiketleme Onayı**\n\n"
        f"👤 Başlatan: [{message.from_user.first_name}](tg://user?id={user_id})\n"
        f"💬 Mesaj: `{custom_msg}`\n"
        f"👥 Kişi Sayısı: {len(members)}\n"
        f"📦 Mod: {'Tekli' if single_mode else f'Çoklu ({chunk_size})'}\n"
        f"⏱️ Gecikme: {flood_delay} saniye\n\n"
        f"✅ Başlamak için onay verin."
    )

    await message.reply(
        info_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Başla", callback_data=f"start_tag:{user_id}"),
             InlineKeyboardButton("🛑 Vazgeç", callback_data=f"cancel_tag:{user_id}")]
        ])
    )


@app.on_callback_query(filters.regex(r"start_tag:(\d+)"))
async def start_tagging(client, cq: CallbackQuery):
    uid = int(cq.matches[0].group(1))
    chat_id = cq.message.chat.id
    if cq.from_user.id != uid:
        return await cq.answer("Sadece komutu yazan onaylayabilir.", show_alert=True)

    session = tag_sessions.get(chat_id)
    if not session:
        return await cq.answer("Etiketleme bulunamadı.", show_alert=True)

    session["active"] = True
    session["approved"] = True
    await cq.message.edit_text("🔄 Etiketleme başlatılıyor...")
    await run_tagging(client, cq.message, session)


@app.on_callback_query(filters.regex(r"cancel_tag:(\d+)"))
async def cancel_tagging(client, cq: CallbackQuery):
    uid = int(cq.matches[0].group(1))
    chat_id = cq.message.chat.id

    # Debugging: Hangi kullanıcı ve chat üzerinde işlem yapıldığını kontrol et
    print(f"Cancel Tagging - User: {cq.from_user.id}, Requested User: {uid}, Chat ID: {chat_id}")  

    if cq.from_user.id != uid:
        return await cq.answer("Sadece başlatan iptal edebilir.", show_alert=True)

    session = tag_sessions.get(chat_id)
    if not session:
        return await cq.answer("Etiketleme bulunamadı.", show_alert=True)

    # Etiketleme işlemini iptal ediyoruz
    session["active"] = False
    tag_sessions.pop(chat_id, None)

    # Kullanıcıya iptal mesajı gönderiyoruz
    await cq.message.edit_text("❌ Etiketleme iptal edildi.")
    await cq.answer("İşlem iptal edildi.")


async def run_tagging(client, msg: Message, session: dict):
    chat_id = msg.chat.id
    members = session["members"]
    flood = session["flood"]
    single = session["single"]
    chunk_size = session["chunk"]
    custom_msg = session["msg"]

    tagged, failed = 0, 0

    if single:
        for user in members:
            # Eğer aktif değilse, işlemi durduruyoruz
            if not tag_sessions.get(chat_id, {}).get("active", False):
                break
            try:
                await msg.reply_text(f"[{user.first_name}](tg://user?id={user.id}) {custom_msg}")
                await asyncio.sleep(flood)
                tag_sessions[chat_id]["last"] = user
                tagged += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except:
                failed += 1
    else:
        chunks = [members[i:i + chunk_size] for i in range(0, len(members), chunk_size)]
        for group in chunks:
            # Eğer aktif değilse, işlemi durduruyoruz
            if not tag_sessions.get(chat_id, {}).get("active", False):
                break
            tags = " ".join(f"[{u.first_name}](tg://user?id={u.id})" for u in group)
            try:
                await msg.reply_text(f"{tags}\n{custom_msg}")
                await asyncio.sleep(flood)
                tag_sessions[chat_id]["last"] = group[-1]
                tagged += len(group)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except:
                failed += len(group)

    last_user = tag_sessions[chat_id].get("last")
    name = f"[{last_user.first_name}](tg://user?id={last_user.id})" if last_user else "Yok"

    # Etiketleme işlemi bitti, session'ı temizle
    tag_sessions.pop(chat_id, None)

    await msg.reply(
        f"✅ Etiketleme tamamlandı.\n"
        f"📌 Etiketlenen: {tagged}\n"
        f"❌ Başarısız: {failed}\n"
        f"🔚 Son etiketlenen: {name}"
    )
