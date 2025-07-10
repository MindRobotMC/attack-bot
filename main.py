import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import PhoneCodeInvalid, SessionPasswordNeeded, PhoneNumberInvalid, FloodWait
from asyncio import sleep

from database import initialize_db, get_accounts_by_status, add_account
import config

bot = Client("bot_session", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)
OWNER_ID = config.OWNER_ID

user_states = {}
user_sessions = {}

# ---------------------- منوی اصلی ----------------------
main_buttons = InlineKeyboardMarkup([
    [InlineKeyboardButton("📱 اکانت ها", callback_data="accounts")],
    [InlineKeyboardButton("👥 گروه ها", callback_data="groups")],
    [InlineKeyboardButton("🔍 آنالیز", callback_data="analyze")],
    [InlineKeyboardButton("📊 آمار", callback_data="stats")],
    [InlineKeyboardButton("ℹ️ درباره MC-STORE", callback_data="about")],
    [InlineKeyboardButton("📞 ارتباط با سازنده", callback_data="contact")],
    [InlineKeyboardButton("💰 دریافت فروش نمایندگی", callback_data="reseller")]
])

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

# ---------------------- استارت فقط برای مالک ----------------------
@bot.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start_owner(client, message):
    await message.reply("به منوی اصلی خوش آمدید:", reply_markup=main_buttons)

@bot.on_message(filters.command("start") & ~filters.user(OWNER_ID))
async def start_other(client, message):
    await message.delete()

# ---------------------- دکمه‌ها ----------------------
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
        await query.message.edit("لطفاً شماره اکانت را وارد کنید (با 98 شروع شود):")
        user_states[query.from_user.id] = {"step": "awaiting_phone"}

    elif data == "back_main":
        await query.message.edit("بازگشت به منوی اصلی:", reply_markup=main_buttons)

# ---------------------- ثبت اکانت جدید ----------------------
@bot.on_message(filters.text & filters.user(OWNER_ID))
async def handle_add_account(client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    state = user_states[user_id]

    # مرحله دریافت شماره
    if state["step"] == "awaiting_phone":
        phone = message.text.strip()
        if not phone.startswith("98"):
            await message.reply("❌ شماره باید با 98 شروع شود.")
            return

        session_name = f"sessions/{phone}"
        os.makedirs("sessions", exist_ok=True)

        helper = Client(session_name, config.API_ID, config.API_HASH)

        try:
            await helper.connect()
            sent_code = await helper.send_code(phone)
            state.update({
                "step": "awaiting_code",
                "phone": phone,
                "helper": helper,
                "code_hash": sent_code.phone_code_hash
            })
            await message.reply("📨 کد ارسال شد. لطفاً کد را وارد کنید (مثلاً 12345):")

        except PhoneNumberInvalid:
            await message.reply("❌ شماره نامعتبر است.")
            del user_states[user_id]
        except FloodWait as e:
            await message.reply(f"⏳ لطفاً {e.value} ثانیه صبر کنید.")
            del user_states[user_id]
        except Exception as e:
            await message.reply(f"⚠️ خطا هنگام ارسال کد: {e}")
            del user_states[user_id]

    # مرحله دریافت کد ورود
    elif state["step"] == "awaiting_code":
        code_input = message.text.strip().replace("-", "")
        phone = state["phone"]
        code_hash = state["code_hash"]
        helper: Client = state["helper"]

        try:
            await helper.sign_in(phone_number=phone, phone_code_hash=code_hash, phone_code=code_input)
            me = await helper.get_me()

            name = me.first_name or "بدون‌نام"
            username = me.username or "unknown"

            add_account({
                "name": name,
                "username": username,
                "phone": phone,
                "status": "healthy"
            })

            await message.reply(f"✅ اکانت با موفقیت افزوده شد:\nنام: {name}\nیوزرنیم: @{username}")
        except PhoneCodeInvalid:
            await message.reply("❌ کد اشتباه است.")
            return
        except SessionPasswordNeeded:
            await message.reply("🔐 ورود دو مرحله‌ای فعال است. لاگین ممکن نیست.")
        except Exception as e:
            await message.reply(f"❌ خطا در ورود: {e}")
        finally:
            await helper.disconnect()
            del user_states[user_id]

# ---------------------- اجرای اولیه ----------------------
initialize_db()
bot.run()
