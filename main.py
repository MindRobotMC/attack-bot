# main.py
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import SessionPasswordNeeded
from database import initialize_db, get_accounts_by_status, add_account
import config

from asyncio import sleep

bot = Client("bot_session", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)

OWNER_ID = config.OWNER_ID
user_states = {}

# منوی اصلی
main_buttons = InlineKeyboardMarkup([
    [InlineKeyboardButton("📱 اکانت ها", callback_data="accounts")],
    [InlineKeyboardButton("👥 گروه ها", callback_data="groups")],
    [InlineKeyboardButton("🔍 آنالیز", callback_data="analyze")],
    [InlineKeyboardButton("📊 آمار", callback_data="stats")],
    [InlineKeyboardButton("ℹ️ درباره MC-STORE", callback_data="about")],
    [InlineKeyboardButton("📞 ارتباط با سازنده", callback_data="contact")],
    [InlineKeyboardButton("💰 دریافت فروش نمایندگی", callback_data="reseller")]
])

# منوی اکانت‌ها
def account_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ اکانت‌های سالم", callback_data="acc_healthy")],
        [InlineKeyboardButton("⛔ اکانت‌های ریپورت", callback_data="acc_reported")],
        [InlineKeyboardButton("🕓 در حال ریکاوری", callback_data="acc_recovering")],
        [InlineKeyboardButton("➕ ثبت اکانت جدید", callback_data="acc_add")],
        [InlineKeyboardButton("❌ حذف اکانت", callback_data="acc_remove")],
        [InlineKeyboardButton("📄 لاگ‌ها", callback_data="acc_logs")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_main")]
    ])

# استارت فقط برای مالک
@bot.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start_owner(client, message):
    await message.reply("به منوی اصلی خوش آمدید:", reply_markup=main_buttons)

@bot.on_message(filters.command("start") & ~filters.user(OWNER_ID))
async def start_other(client, message):
    await message.delete()

# مدیریت دکمه‌ها
@bot.on_callback_query()
async def callback_handler(client, query):
    data = query.data

    if data == "accounts":
        await query.message.edit("📱 مدیریت اکانت‌ها:", reply_markup=account_menu())

    elif data == "acc_healthy":
        accounts = get_accounts_by_status("healthy")
        if not accounts:
            await query.message.edit("✅ اکانت سالمی یافت نشد.", reply_markup=account_menu())
            return

        text = "✅ لیست اکانت‌های سالم:\n\n"
        for acc in accounts:
            text += f"نام: {acc['name']}\nیوزرنیم: @{acc['username']}\nشماره: {acc['phone']}\nوضعیت: آماده\n\n"

        await query.message.edit(text, reply_markup=account_menu())

    elif data == "acc_add":
        await query.message.edit("لطفاً شماره اکانت را وارد کنید (با 98+):")
        user_states[query.from_user.id] = {"step": "awaiting_phone"}

    elif data == "back_main":
        await query.message.edit("بازگشت به منوی اصلی:", reply_markup=main_buttons)

# مدیریت پیام‌ها برای ثبت اکانت جدید
@bot.on_message(filters.text & filters.user(OWNER_ID))
async def handle_text(client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    state = user_states[user_id]

    # مرحله اول: دریافت شماره
    if state["step"] == "awaiting_phone":
        phone = message.text.strip()
        state["phone"] = phone
        state["step"] = "awaiting_code"
        await message.reply("لطفاً کد دریافتی را به فرمت 12-345 ارسال کن:")
        return

    # مرحله دوم: دریافت کد و لاگین
    elif state["step"] == "awaiting_code":
        code_input = message.text.strip()
        if "-" in code_input:
            parts = code_input.split("-")
            code = "".join(parts)
        else:
            code = code_input

        phone = state["phone"]
        session_name = f"sessions/{phone}"

        os.makedirs("sessions", exist_ok=True)
        helper = Client(session_name, config.API_ID, config.API_HASH, phone_number=phone)

        try:
            await helper.connect()
            sent_code = await helper.send_code(phone)
            await sleep(2)
            await helper.sign_in(phone, code)

            me = await helper.get_me()
            username = me.username or "unknown"
            name = me.first_name or "بدون‌نام"

            # ثبت در دیتابیس
            add_account({
                "name": name,
                "username": username,
                "phone": phone,
                "status": "healthy"
            })

            await message.reply(f"✅ اکانت با موفقیت اضافه شد:\nنام: {name}\nیوزرنیم: @{username}")
            del user_states[user_id]
        except SessionPasswordNeeded:
            await message.reply("❗ این اکانت دارای رمز دوم است و لاگین ممکن نیست.")
        except Exception as e:
            await message.reply(f"❌ خطا در ورود به اکانت: {e}")
        finally:
            await helper.disconnect()

# شروع دیتابیس
initialize_db()
bot.run()
