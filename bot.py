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
        [InlineKeyboardButton("📄 لیست اکانت‌ها", callback_data="list_1")],
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

    if data.startswith("list_") or data == "list":
        page = int(data.split("_")[1]) if "_" in data else 1
        helpers = load_helpers()

        if not helpers:
            await call.message.edit_text("⚠️ هنوز هیچ اکانتی اضافه نشده.")
            return

        per_page = 5
        page_items, total = paginate(helpers, page=page, per_page=per_page)
        total_pages = (total + per_page - 1) // per_page

        text = f"📄 <b>لیست اکانت‌ها (صفحه {page}/{total_pages}):</b>\n\n"
        buttons = []

        for i, phone in enumerate(page_items, start=(page - 1) * per_page + 1):
            text += f"<b>{i}.</b> <code>{phone}</code>\n"
            buttons.append([InlineKeyboardButton(f"❌ حذف {i}", callback_data=f"del_{phone}")])

        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"list_{page - 1}"))
        if page < total_pages:
            nav.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"list_{page + 1}"))

        if nav:
            buttons.append(nav)
        buttons.append([InlineKeyboardButton("🔄 بروزرسانی", callback_data=f"list_{page}")])

        await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="html")
        return

    elif data.startswith("del_"):
        phone = data.split("del_")[1]
        helpers = load_helpers()
        if phone in helpers:
            helpers.remove(phone)
            save_helpers(helpers)
            await call.message.edit_text(f"☑️ اکانت <code>{phone}</code> حذف شد.", parse_mode="html")
        else:
            await call.message.answer("⚠️ این شماره در لیست نیست.")
        return

    elif data == "add":
        if user_states.get(call.from_user.id) == "awaiting_phone":
            await call.message.answer("⏳ لطفاً ابتدا شماره قبلی را وارد کنید.")
            return
        user_states[call.from_user.id] = "awaiting_phone"
        await call.message.answer("➕ شماره را با +98 بفرست.")
        return

    elif data == "stats":
        await call.message.answer("📊 آمار: به‌زودی افزوده می‌شود.")
        return

    elif data == "help":
        await call.message.answer("📘 با این ربات می‌تونی به کاربران پیام بدی.")
        return

    elif data == "about":
        await call.message.answer("ℹ️ ساخته‌شده توسط @mindrobotmc")
        return

    elif data == "attack":
        await call.message.answer("📩 این بخش به‌زودی فعال میشه.")
        return

@bot.on_message(filters.text)
async def handle_text(client, message):
    if message.from_user.id != OWNER_ID or message.text.startswith("/"):
        return

    state = user_states.get(message.from_user.id)

    if state == "awaiting_phone":
        phone = message.text.strip()
        if not phone.startswith("+98"):
            await message.reply("❌ لطفاً شماره با +98 شروع شود.")
            return

        session_name = phone.replace("+", "")
        try:
            tg_client = Client(session_name, api_id=API_ID, api_hash=API_HASH, in_memory=True)
            await tg_client.connect()
            sent = await tg_client.send_code(phone)
            temp_data[message.from_user.id] = {
                "phone": phone,
                "client": tg_client,
                "phone_code_hash": sent.phone_code_hash
            }
            user_states[message.from_user.id] = "awaiting_code"
            await message.reply("📨 کد ارسال شد. لطفاً کد را وارد کنید (مثال: 45-234).")
        except Exception as e:
            await message.reply(f"❌ خطا در ارسال کد:\n{e}")
            user_states.pop(message.from_user.id, None)
        return

    elif state == "awaiting_code":
        raw_code = message.text.strip()
        code = "".join(filter(str.isdigit, raw_code))  # پاک‌سازی خط فاصله و سایر
        data = temp_data.get(message.from_user.id)

        if not data:
            await message.reply("❌ مشکلی پیش اومده. از نو امتحان کن.")
            user_states.pop(message.from_user.id, None)
            return

        phone = data["phone"]
        phone_code_hash = data["phone_code_hash"]
        tg_client = data["client"]

        try:
            await tg_client.sign_in(phone_number=phone, phone_code_hash=phone_code_hash, phone_code=code)
            await tg_client.export_session_string()
            await tg_client.disconnect()

            helpers = load_helpers()
            if phone not in helpers:
                helpers.append(phone)
                save_helpers(helpers)

            await message.reply(f"✅ اکانت {phone} وارد شد و ذخیره شد.")
        except Exception as e:
            await message.reply(f"❌ ورود ناموفق:\n{e}")
        finally:
            user_states.pop(message.from_user.id, None)
            temp_data.pop(message.from_user.id, None)

bot.run()
