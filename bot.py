import os
import json
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8032544795:AAF6uK-SKxG5fzAWSUTRauqXor4YG7013Jk"
API_ID = 29698707
API_HASH = "22b012816bcf16d58d826e6e3606a273"
OWNER_ID = 7608419661

bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

HELPERS_FILE = "helpers.json"
user_states = {}
temp_data = {}

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

@bot.on_message(filters.text & ~filters.command("start"))
async def handle_text(client, message):
    if message.from_user.id != OWNER_ID:
        return

    state = user_states.get(message.from_user.id)

    if state == "awaiting_phone":
        phone = message.text.strip()
        if not phone.startswith("+98"):
            await message.reply("❌ لطفاً شماره را با +98 شروع کنید.")
            return

        session_name = phone.replace("+", "")
        temp_data[message.from_user.id] = {"phone": phone, "session_name": session_name}
        user_states[message.from_user.id] = "awaiting_code"

        try:
            temp_data[message.from_user.id]["client"] = Client(
                session_name, api_id=API_ID, api_hash=API_HASH, in_memory=True
            )
            await temp_data[message.from_user.id]["client"].connect()
            await temp_data[message.from_user.id]["client"].send_code(phone)
            await message.reply("📨 کد تأیید به تلگرام ارسال شد. لطفاً کد را وارد کنید.")
        except Exception as e:
            await message.reply(f"❌ ارسال کد شکست خورد:\n{e}")
            user_states.pop(message.from_user.id, None)

    elif state == "awaiting_code":
        code = message.text.strip()
        data = temp_data.get(message.from_user.id)
        if not data:
            await message.reply("❌ مشکلی پیش آمده. لطفاً دوباره تلاش کنید.")
            user_states.pop(message.from_user.id, None)
            return

        phone = data["phone"]
        session_name = data["session_name"]
        client = data["client"]

        try:
            await client.sign_in(phone_number=phone, phone_code=code)
            await client.export_session_string()  # باعث میشه فایل session ذخیره بشه
            await client.disconnect()

            helpers = load_helpers()
            if phone not in helpers:
                helpers.append(phone)
                save_helpers(helpers)

            await message.reply(f"✅ اکانت {phone} با موفقیت اضافه شد و ذخیره شد.")
        except Exception as e:
            await message.reply(f"❌ ورود ناموفق:\n{e}")
        finally:
            user_states.pop(message.from_user.id, None)
            temp_data.pop(message.from_user.id, None)

bot.run()
