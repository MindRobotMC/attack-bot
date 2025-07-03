import os
import json
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8032544795:AAF6uK-SKxG5fzAWSUTRauqXor4YG7013Jk"
API_ID = 29698707
API_HASH = "22b012816bcf16d58d826e6e3606a273"
OWNER_ID = 7608419661  # فقط شما مجاز هستید

bot = Client("bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

HELPERS_FILE = "helpers.json"
user_states = {}  # وضعیت کاربران

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
    if message.from_user.id != OWNER_ID:
        return
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 اتک", callback_data="attack")],
        [InlineKeyboardButton("📄 لیست اکانت‌ها", callback_data="list")],
        [InlineKeyboardButton("➕ اضافه کردن اکانت", callback_data="add")],
        [InlineKeyboardButton("📊 آمار ارسال‌ها", callback_data="stats")],
        [InlineKeyboardButton("📘 راهنما", callback_data="help")],
        [InlineKeyboardButton("ℹ️ درباره", callback_data="about")],
        [InlineKeyboardButton("💬 ارتباط با سازنده", url="https://t.me/mindrobotmc")]
    ])
    await message.reply("به ربات ارسال پیوی خوش آمدی!", reply_markup=keyboard)

@bot.on_callback_query()
async def callback(client, call):
    if call.from_user.id != OWNER_ID:
        return
    data = call.data
    if data == "list":
        helpers = load_helpers()
        msg = "\n".join(helpers) if helpers else "❌ اکانتی ثبت نشده."
        await call.message.reply(f"📄 لیست اکانت‌ها:\n\n{msg}")
    elif data == "add":
        user_states[call.from_user.id] = "awaiting_phone"
        await call.message.reply("➕ لطفاً شماره اکانت را با +98 ارسال کنید.")
    elif data == "stats":
        await call.message.reply("📊 آمار ارسال‌ها: به‌زودی اضافه می‌شود.")
    elif data == "help":
        await call.message.reply("📘 راهنما:\nبا این ربات می‌تونی به کاربران پیام ارسال کنی.")
    elif data == "about":
        await call.message.reply("ℹ️ ربات ارسال پیوی ساخته‌شده توسط @mindrobotmc")
    elif data == "attack":
        await call.message.reply("📩 ارسال پیام به کاربران به‌زودی فعال می‌شود.")

@bot.on_message(filters.text & ~filters.command(["start"]))
async def handle_text(client, message):
    if message.from_user.id != OWNER_ID:
        return
    state = user_states.get(message.from_user.id)
    if state == "awaiting_phone":
        phone = message.text.strip()
        if not phone.startswith("+"):
            await message.reply("❌ لطفاً شماره را با +98 شروع کنید.")
            return
        helpers = load_helpers()
        if phone in helpers:
            await message.reply("⚠️ این شماره قبلاً اضافه شده است.")
        else:
            helpers.append(phone)
            save_helpers(helpers)
            await message.reply("✅ شماره ذخیره شد. حالا فایل `add_account.py` را اجرا کن و کد را بزن.")
        user_states.pop(message.from_user.id)

bot.run()
