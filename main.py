# main.py
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import initialize_db, get_accounts_by_status
import config

bot = Client("bot_session", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)

OWNER_ID = config.OWNER_ID

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

@bot.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start_owner(client, message):
    await message.reply("به منوی اصلی خوش آمدید:", reply_markup=main_buttons)

@bot.on_message(filters.command("start") & ~filters.user(OWNER_ID))
async def start_other(client, message):
    await message.delete()

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

    elif data == "back_main":
        await query.message.edit("بازگشت به منوی اصلی:", reply_markup=main_buttons)

initialize_db()
bot.run()