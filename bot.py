import os
import json
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.getenv("8032544795:AAF6uK-SKxG5fzAWSUTRauqXor4YG7013Jk")
API_ID = int(os.getenv("29698707"))
API_HASH = os.getenv("22b012816bcf16d58d826e6e3606a273")

bot = Client("bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

HELPERS_FILE = "helpers.json"

if not os.path.exists(HELPERS_FILE):
    with open(HELPERS_FILE, "w") as f:
        json.dump([], f)

def load_helpers():
    with open(HELPERS_FILE) as f:
        return json.load(f)

def save_helpers(helpers):
    with open(HELPERS_FILE, "w") as f:
        json.dump(helpers, f)

@bot.on_message(filters.command("start"))
async def start(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 اتک", callback_data="attack")],
        [InlineKeyboardButton("📄 لیست اکانت‌ها", callback_data="list")],
        [InlineKeyboardButton("➕ اضافه کردن اکانت", callback_data="add")],
        [InlineKeyboardButton("📊 آمار ارسال‌ها", callback_data="stats")],
        [InlineKeyboardButton("📘 راهنما", callback_data="help")],
        [InlineKeyboardButton("ℹ️ درباره", callback_data="about")],
        [InlineKeyboardButton("💬 ارتباط با سازنده", url="https://t.me/YourID")]
    ])
    await message.reply("به ربات ارسال پیوی خوش آمدی!", reply_markup=keyboard)

@bot.on_callback_query()
async def callback(client, call):
    data = call.data
    if data == "list":
        helpers = load_helpers()
        msg = "\n".join(helpers) if helpers else "❌ اکانتی ثبت نشده."
        await call.message.reply(f"📄 لیست اکانت‌ها:\n\n{msg}")
    elif data == "add":
        await call.message.reply("➕ برای اضافه کردن اکانت، شماره را ارسال کنید.")
    elif data == "stats":
        await call.message.reply("📊 آمار ارسال‌ها: به‌زودی اضافه می‌شود.")
    elif data == "help":
        await call.message.reply("📘 راهنما:\nبا این ربات می‌تونی به کاربران پیام ارسال کنی.")
    elif data == "about":
        await call.message.reply("ℹ️ ربات ارسال به پیوی ساخته‌شده توسط @YourID")
    elif data == "attack":
        await call.message.reply("📩 ارسال پیام به کاربران به‌زودی فعال می‌شود.")

bot.run()
