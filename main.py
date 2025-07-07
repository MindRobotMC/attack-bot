from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config

bot = Client("bot_session", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)

OWNER_ID = config.OWNER_ID

def main_menu():
    buttons = [
        [InlineKeyboardButton("📱 اکانت ها", callback_data="accounts")],
        [InlineKeyboardButton("👥 گروه ها", callback_data="groups")],
        [InlineKeyboardButton("🔍 آنالیز", callback_data="analyze")],
        [InlineKeyboardButton("📊 آمار", callback_data="stats")],
        [InlineKeyboardButton("ℹ️ درباره MC-STORE", callback_data="about")],
        [InlineKeyboardButton("📞 ارتباط با سازنده", callback_data="contact")],
        [InlineKeyboardButton("💰 دریافت فروش نمایندگی", callback_data="reseller")]
    ]
    return InlineKeyboardMarkup(buttons)

@bot.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start_owner(client, message):
    await message.reply(
        "سلام! به ربات MC-STORE خوش آمدی.\nلطفا یکی از گزینه‌های زیر را انتخاب کن:",
        reply_markup=main_menu()
    )

@bot.on_message(filters.command("start") & ~filters.user(OWNER_ID))
async def start_other(client, message):
    # حذف پیام کاربران غیر مالک
    await message.delete()

@bot.on_callback_query()
async def callback_handler(client, query):
    data = query.data
    if data == "accounts":
        await query.message.edit("شما وارد بخش اکانت ها شدید.")
    elif data == "groups":
        await query.message.edit("شما وارد بخش گروه ها شدید.")
    elif data == "analyze":
        await query.message.edit("شما وارد بخش آنالیز شدید.")
    elif data == "stats":
        await query.message.edit("شما وارد بخش آمار شدید.")
    elif data == "about":
        await query.message.edit("ربات MC-STORE نسخه ۱.۰\nساخته شده توسط [نام شما].")
    elif data == "contact":
        await query.message.edit("برای ارتباط با سازنده لطفا به آیدی @YourTelegramID مراجعه کنید.")
    elif data == "reseller":
        await query.message.edit("برای دریافت فروش نمایندگی لطفا با سازنده تماس بگیرید.")
    else:
        await query.answer("دکمه نامعتبر!", show_alert=True)

bot.run()
