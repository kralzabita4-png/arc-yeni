from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import ChatMemberUpdated
from pyrogram import idle
from datetime import datetime
import config

from ..logging import LOGGER

# --- MongoDB Ayarları ---
TEMP_MONGODB = "mongodb+srv://userbot:userbot@userbot.nrzfzdf.mongodb.net/?retryWrites=true&w=majority"

if config.MONGO_DB_URI is None:
    LOGGER(__name__).warning(
        "No MONGO DB URL found. Bot ArchMusic'in veritabanını kullanacak."
    )
    temp_client = Client(
        "ArchMusic",
        bot_token=config.BOT_TOKEN,
        api_id=config.API_ID,
        api_hash=config.API_HASH,
    )
    temp_client.start()
    info = temp_client.get_me()
    username = info.username
    temp_client.stop()
    _mongo_async_ = AsyncIOMotorClient(TEMP_MONGODB)
    _mongo_sync_ = MongoClient(TEMP_MONGODB)
    mongodb = _mongo_async_[username]
    pymongodb = _mongo_sync_[username]
else:
    _mongo_async_ = AsyncIOMotorClient(config.MONGO_DB_URI)
    _mongo_sync_ = MongoClient(config.MONGO_DB_URI)
    mongodb = _mongo_async_["che"]
    pymongodb = _mongo_sync_["ArchMusic"]

# --- Grup Koleksiyonları ---
groups_collection_sync = pymongodb["groups"]   # Senkron
groups_collection_async = mongodb["groups"]    # Asenkron

# --- Pyrogram Bot ---
bot = Client(
    "ArchMusic",
    bot_token=config.BOT_TOKEN,
    api_id=config.API_ID,
    api_hash=config.API_HASH,
)

# --- Grup Mesajlarını Yakalama ---
@bot.on_message(filters.group)
async def add_group(client, message):
    group_id = message.chat.id
    group_name = message.chat.title

    existing = await groups_collection_async.count_documents({"group_id": group_id})
    if existing == 0:
        await groups_collection_async.insert_one({
            "group_id": group_id,
            "group_name": group_name,
            "added_at": datetime.utcnow()
        })
        print(f"Yeni grup eklendi: {group_name} ({group_id})")

    total_groups = await groups_collection_async.count_documents({})
    print(f"Botun gerçek bağlı olduğu toplam grup sayısı: {total_groups}")

# --- Bot Çıkarıldığında veya Kaldırıldığında MongoDB Güncelleme ---
@bot.on_chat_member_updated()
async def remove_group(client: Client, chat_member_update: ChatMemberUpdated):
    # Sadece botun durum değişikliklerini kontrol et
    if chat_member_update.new_chat_member.user.id != client.me.id:
        return

    status = chat_member_update.new_chat_member.status
    chat_id = chat_member_update.chat.id

    if status in ["kicked", "left"]:
        result = await groups_collection_async.delete_one({"group_id": chat_id})
        if result.deleted_count > 0:
            print(f"Bot bu gruptan çıkarıldı, MongoDB kaydı silindi: {chat_member_update.chat.title}")

    total_groups = await groups_collection_async.count_documents({})
    print(f"Botun gerçek bağlı olduğu toplam grup sayısı: {total_groups}")

# --- /gruplar Komutu ---
@bot.on_message(filters.command("gruplar") & filters.user(config.OWNER_ID))
async def show_groups(client, message):
    groups = await groups_collection_async.find().to_list(length=1000)
    total = len(groups)
    
    if total == 0:
        await message.reply("Botun bağlı olduğu grup bulunamadı.")
        return

    text = f"📊 Botun Bağlı Olduğu Gruplar ({total}):\n\n"
    for idx, g in enumerate(groups, start=1):
        text += f"{idx}. {g['group_name']} (`{g['group_id']}`)\n"

    await message.reply(text)
    print(f"Toplam grup sayısı: {total}")

# --- Botu Başlat ve Sürekli Çalıştır ---
if __name__ == "__main__":
    bot.start()
    print("ArchMusic botu başlatıldı ve çalışıyor...")
    idle()  # Botu durdurmadan çalıştırmaya devam eder
    bot.stop()
