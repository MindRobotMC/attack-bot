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

# ایجاد فایل helpers.json اگر وجود نداشته باشد
if not os.path.exists(HELPERS_FILE):
    with open(HELPERS_FILE, "w") as f:
        json.dump([], f)

def load_helpers():
    with open(HELPERS_FILE) as f:
        return json.load(f)

def save_helpers(helpers):
    with open(HELPERS_FILE, "w") as f:
        json.dump(helpers, f)

def paginate(items, page=1, per_page=5):
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], len(items)

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

    if data.startswith("list") or data.startswith("page_"):
        page = 1
        if data.startswith("page_"):
            try:
                page = int(data.split("_")[1])
            except:
                page = 1

        helpers = load_helpers()
        if not helpers:
            await call.message.reply("⚠️ هنوز هیچ اکانتی اضافه نشده.")
            return

        per_page = 5
        page_items, total = paginate(helpers, page=page, per_page=per_page)
        total_pages = (total + per_page - 1) // per_page

        text = f"📄 <b>لیست اکانت‌ها (صفحه {page}/{total_pages}):</b>\n\n"
        buttons = []

        for i, phone in enumerate(page_items, start=(page - 1) * per_page + 1):
            text += f"<b>{i}.</b> <code>{phone}</code>\n"
            buttons.append([InlineKeyboardButton(f"❌ حذف {i}", callback_data=f"del_{phone}")])

        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"page_{page - 1}"))
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"page_{page + 1}"))

        if nav_buttons:
            buttons.append(nav_buttons)
        buttons.append([InlineKeyboardButton("🔄 بروزرسانی لیست", callback_data="list")])

        await call.message.reply(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="html"
        )

    elif data.startswith("del_"):
        phone = data.split("del_")[1]
        helpers = load_helpers()

        if phone in helpers:
            helpers.remove(phone)
            save_helpers(helpers)
            await call.message.reply(f"☑️ اکانت <code>{phone}</code> با موفقیت حذف شد.", parse_mode="html")
        else:
            await call.message.reply("⚠️ این شماره در لیست یافت نشد.")

    elif data == "add":
        if user_states.get(call.from_user.id) == "awaiting_phone":
            await call.message.reply("⏳ در انتظار دریافت شماره هستم، لطفاً شماره را وارد کنید.")
            return
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

@bot.on_message(filters.text)
async def handle_text(client, message):
    if message.from_user.id != OWNER_ID:
        return

    if message.text.startswith("/"):
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
            temp_data.pop(message.from_user.id, None)

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
            await client.export_session_string()  # باعث ذخیره session میشه
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
