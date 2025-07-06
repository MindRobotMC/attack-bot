import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from datetime import datetime

import modules.accounts as accounts
import modules.analysis as analysis
import modules.logs as logs
import modules.utils as utils
import modules.stats as stats
import modules.attacks as attacks
from modules.database import initialize_db

# مشخصات ربات
API_ID = 10423308
API_HASH = "c887be025508282c815633a95d25e878"
BOT_TOKEN = "8032544795:AAF6uK-SKxG5fzAWSUTRauqXor4YG7013Jk"

# راه‌اندازی دیتابیس و ربات
initialize_db()
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

helper_clients = {}
user_states = {}
temp_data = {}

# --- منوها ---
def main_menu():
    buttons = [
        [InlineKeyboardButton("📱 مدیریت اکانت‌ها", callback_data="menu_accounts")],
        [InlineKeyboardButton("📊 مشاهده آمار", callback_data="menu_stats")],
        [InlineKeyboardButton("🗒 لاگ‌ها", callback_data="view_logs")],
        [InlineKeyboardButton("🔧 تنظیم اتک", callback_data="menu_attack")],
        [InlineKeyboardButton("🔍 آنالیز گروه‌ها", callback_data="menu_analysis")],
    ]
    return InlineKeyboardMarkup(buttons)

def accounts_status_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ اکانت‌های سالم", callback_data="acc_status_healthy")],
        [InlineKeyboardButton("🚫 ریپورت", callback_data="acc_status_reported")],
        [InlineKeyboardButton("❌ دیلیت شده", callback_data="acc_status_deleted")],
        [InlineKeyboardButton("🔄 درحال ریکاوری", callback_data="acc_status_recovering")],
        [InlineKeyboardButton("⬅ بازگشت", callback_data="back_main")]
    ])

# --- هندلر استارت ---
@bot.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    await message.reply("سلام! به ربات مدیریت هلپر خوش آمدید.", reply_markup=main_menu())

# --- هندلر کال‌بک‌ها ---
@bot.on_callback_query()
async def callback_handler(client: Client, call: CallbackQuery):
    data = call.data

    if data == "menu_accounts":
        await call.message.edit_text("وضعیت اکانت‌ها:", reply_markup=accounts_status_menu())
        return await call.answer()

    if data == "back_main":
        await call.message.edit_text("منوی اصلی:", reply_markup=main_menu())
        return await call.answer()

    if data.startswith("acc_status_"):
        status = data.replace("acc_status_", "")
        status_map = {
            "healthy": {"report": False, "deleted": False},
            "reported": {"report": True},
            "deleted": {"deleted": True},
            "recovering": {"recovering": True}
        }
        text = accounts.list_helpers_text(status_map.get(status, {}))
        await call.message.edit_text(text, reply_markup=accounts_status_menu())
        return await call.answer()

    if data == "view_logs":
        helpers = accounts.load_helpers()
        if not helpers:
            await call.message.edit_text("اکانتی ثبت نشده است.", reply_markup=main_menu())
            return await call.answer()
        buttons = [[InlineKeyboardButton(h["phone"], callback_data=f"log_{h['phone']}")] for h in helpers]
        await call.message.edit_text("اکانتی را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(buttons))
        return await call.answer()

    if data.startswith("log_"):
        phone = data[4:]
        logs_list = logs.get_operations_by_account(phone)
        if not logs_list:
            await call.message.edit_text(f"📝 لاگی برای {phone} یافت نشد.", reply_markup=main_menu())
            return await call.answer()
        text = f"📄 آخرین لاگ‌های اکانت {phone}:\n\n"
        for log in logs_list[-10:]:
            ts = log["timestamp"]
            act = log["action"]
            st = log["status"]
            text += f"🕒 {ts}\n🔹 {act} - {st}\n\n"
        await call.message.edit_text(text, reply_markup=main_menu())
        return await call.answer()

    if data == "menu_stats":
        all_stats = stats.get_stats()
        if not all_stats:
            await call.message.edit_text("📉 آماری ثبت نشده است.", reply_markup=main_menu())
            return await call.answer()
        text = "📊 آمار کلی:\n\n"
        for key, val in all_stats.items():
            text += f"🔹 {key}: {val}\n"
        await call.message.edit_text(text, reply_markup=main_menu())
        return await call.answer()

    if data == "menu_attack":
        results = await attacks.mass_attack(helper_clients, message="سلام به همه!", media_type="text")
        text = "نتایج ارسال پیام:\n\n"
        for phone, group_result in results.items():
            text += f"📱 {phone}:\n"
            for group, success in group_result.items():
                icon = "✅" if success else "❌"
                text += f"  {icon} {group}\n"
        await call.message.edit_text(text, reply_markup=main_menu())
        return await call.answer()

    if data == "menu_analysis":
        await call.message.edit_text("این بخش در حال توسعه است...", reply_markup=main_menu())
        return await call.answer()

# --- مدیریت پیام‌های متنی ---
@bot.on_message(filters.text & filters.private)
async def handle_text(client: Client, message: Message):
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if state == "awaiting_phone":
        phone = utils.clean_phone_number(message.text.strip())
        if not (phone.startswith("+98") and phone[1:].isdigit()):
            return await message.reply("شماره صحیح نیست. با +98 وارد کنید.")
        temp_data[user_id] = {"phone": phone}
        user_states[user_id] = "awaiting_otp"
        return await message.reply("کد تایید ارسال شده را وارد کنید (مثال: 45-666)")

    if state == "awaiting_otp":
        otp_raw = message.text.strip()
        otp = ''.join(c for c in otp_raw if c.isdigit())
        if len(otp) < 4:
            return await message.reply("کد نامعتبر است. دوباره وارد کنید.")
        phone = temp_data[user_id]["phone"]

        client_helper = await accounts.login_helper_with_otp(phone, otp, API_ID, API_HASH, helper_clients)
        if not client_helper:
            user_states[user_id] = "awaiting_phone"
            return await message.reply("ورود موفق نبود. شماره را دوباره ارسال کنید.")

        accounts.update_account(phone, {"deleted": 0, "report": 0, "recovering": 0})

        user_states.pop(user_id, None)
        temp_data.pop(user_id, None)

        await message.reply(f"اکانت {phone} با موفقیت اضافه شد ✅", reply_markup=main_menu())

# --- دستور افزودن اکانت ---
@bot.on_message(filters.command("addhelper"))
async def add_helper_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    user_states[user_id] = "awaiting_phone"
    await message.reply("شماره اکانت هلپر را وارد کنید (مثال: +989123456789):")

# --- اجرای ربات ---
print("🤖 ربات در حال اجراست...")
bot.run()
