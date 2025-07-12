import os
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import SessionPasswordNeeded

from database import (
    initialize_db, get_accounts_by_status, add_account,
    delete_account, get_all_accounts,
    add_group, delete_group, get_all_groups,
    log_voice_participants
)
import config

bot = Client("bot_session", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)
OWNER_ID = config.OWNER_ID
REPORT_GROUP_ID = config.LOG_GROUP_ID

user_states = {}
group_states = {}

# ---------------------- منوها ----------------------
main_buttons = InlineKeyboardMarkup([
    [InlineKeyboardButton("📱 اکانت ها", callback_data="accounts")],
    [InlineKeyboardButton("👥 گروه ها", callback_data="groups")],
    [InlineKeyboardButton("🔍 آنالیز", callback_data="analyze")],
    [InlineKeyboardButton("📊 آمار", callback_data="stats")],
    [InlineKeyboardButton("ℹ️ درباره MC-STORE", callback_data="about")],
    [InlineKeyboardButton("📞 ارتباط با سازنده", callback_data="contact")],
    [InlineKeyboardButton("💰 دریافت فروش نمایندگی", callback_data="reseller")]
])

def analyze_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 آنالیز اعضای چت", callback_data="analyze_chat")],
        [InlineKeyboardButton("🔊 آنالیز اعضای ویسکال", callback_data="analyze_voice")],
        [InlineKeyboardButton("📊 آنالیز پیشرفته", callback_data="analyze_advanced")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ])

def account_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ اکانت‌های سالم", callback_data="acc_healthy")],
        [InlineKeyboardButton("⛔ اکانت‌های ریپورت", callback_data="acc_reported")],
        [InlineKeyboardButton("🕓 در حال ریکاوری", callback_data="acc_recovering")],
        [InlineKeyboardButton("➕ افزودن اکانت", callback_data="acc_add")],
        [InlineKeyboardButton("❌ حذف اکانت", callback_data="acc_remove")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ])

def groups_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 نمایش گروه‌ها", callback_data="show_groups")],
        [InlineKeyboardButton("➕ افزودن گروه", callback_data="add_group")],
        [InlineKeyboardButton("❌ حذف گروه", callback_data="remove_group")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ])

@bot.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start_owner(client, message):
    await message.reply("به منوی اصلی خوش آمدید:", reply_markup=main_buttons)

@bot.on_callback_query()
async def handle_callbacks(client, query):
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

    elif data == "acc_reported":
        accounts = get_accounts_by_status("reported")
        if not accounts:
            await query.message.edit("⛔ اکانت ریپورت شده‌ای وجود ندارد.", reply_markup=account_menu())
            return
        text = "⛔ لیست اکانت‌های ریپورت:\n\n"
        for acc in accounts:
            text += f"نام: {acc['name']}\nیوزرنیم: @{acc['username']}\nشماره: {acc['phone']}\nمدت: {acc.get('report_duration', 'نامشخص')}\nتا: {acc.get('report_end_time', 'نامشخص')}\n\n"
        await query.message.edit(text, reply_markup=account_menu())

    elif data == "acc_recovering":
        accounts = get_accounts_by_status("recovering")
        if not accounts:
            await query.message.edit("🕓 اکانت در حال ریکاوری وجود ندارد.", reply_markup=account_menu())
            return
        text = "🕓 لیست اکانت‌های در حال ریکاوری:\n\n"
        for acc in accounts:
            text += f"نام: {acc['name']}\nشماره: {acc['phone']}\nآماده در: {acc.get('ready_time', 'نامشخص')}\n\n"
        await query.message.edit(text, reply_markup=account_menu())

    elif data == "acc_add":
        await query.message.edit("📲 لطفاً شماره اکانت را وارد کنید (با 98 شروع شود):")
        user_states[query.from_user.id] = {"step": "awaiting_phone"}

    elif data == "acc_remove":
        accounts = get_all_accounts()
        if not accounts:
            await query.message.edit("❌ هیچ اکانتی برای حذف وجود ندارد.", reply_markup=account_menu())
            return
        buttons = [[InlineKeyboardButton(f"❌ {acc['phone']}", callback_data=f"delete_{acc['phone']}")] for acc in accounts]
        buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="accounts")])
        await query.message.edit("❌ لطفاً اکانتی را برای حذف انتخاب کنید:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("delete_"):
        phone = data.split("delete_")[1]
        delete_account(phone)
        await query.message.edit(f"✅ اکانت {phone} حذف شد.", reply_markup=account_menu())

    elif data == "groups":
        await query.message.edit("👥 مدیریت گروه‌ها:", reply_markup=groups_menu())

    elif data == "show_groups":
        groups = get_all_groups()
        if not groups:
            await query.message.edit("📋 گروهی یافت نشد.", reply_markup=groups_menu())
            return
        text = "📋 لیست گروه‌ها:\n\n" + '\n'.join([f"- {g}" for g in groups])
        await query.message.edit(text, reply_markup=groups_menu())

    elif data == "add_group":
        await query.message.edit("➕ لطفاً آیدی یا نام گروه را ارسال کنید:")
        group_states[query.from_user.id] = {"step": "awaiting_new_group"}

    elif data == "remove_group":
        groups = get_all_groups()
        if not groups:
            await query.message.edit("❌ گروهی برای حذف نیست.", reply_markup=groups_menu())
            return
        buttons = [[InlineKeyboardButton(f"❌ {g}", callback_data=f"delgroup_{g}")] for g in groups]
        buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="groups")])
        await query.message.edit("❌ گروه مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("delgroup_"):
        group_name = data.split("delgroup_")[1]
        delete_group(group_name)
        await query.message.edit(f"✅ گروه '{group_name}' حذف شد.", reply_markup=groups_menu())

    elif data == "analyze":
        await query.message.edit("🔍 انتخاب نوع آنالیز:", reply_markup=analyze_menu())

    elif data == "analyze_voice":
        await query.message.edit("🔊 لینک گروه ویس‌کال را ارسال کنید:")
        user_states[query.from_user.id] = {"step": "awaiting_voice_link"}

    elif data == "analyze_chat":
        await query.message.edit("👥 لینک گروه چت را ارسال کنید:")
        user_states[query.from_user.id] = {"step": "awaiting_chat_link"}

    elif data == "back_main":
        await query.message.edit("به منوی اصلی بازگشت:", reply_markup=main_buttons)


@bot.on_message(filters.text & filters.user(OWNER_ID))
async def handle_text(client, message: Message):
    user_id = message.from_user.id

    # مدیریت وضعیت گروه‌ها
    if user_id in group_states:
        state = group_states[user_id]
        if state["step"] == "awaiting_new_group":
            group_name = message.text.strip()
            add_group(group_name)
            await message.reply(f"✅ گروه '{group_name}' افزوده شد.")
            del group_states[user_id]
        return

    # مدیریت وضعیت کاربران (افزودن اکانت و آنالیز)
    if user_id in user_states:
        state = user_states[user_id]

        # افزودن اکانت - دریافت شماره تلفن
        if state["step"] == "awaiting_phone":
            phone = message.text.strip()
            if not phone.startswith("98"):
                await message.reply("❌ شماره باید با 98 شروع شود.")
                return
            session_path = f"sessions/{phone}"
            os.makedirs("sessions", exist_ok=True)
            helper = Client(session_path, config.API_ID, config.API_HASH)
            try:
                await helper.connect()
                sent_code = await helper.send_code(phone)
                state.update({
                    "step": "awaiting_code",
                    "phone": phone,
                    "helper": helper,
                    "code_hash": sent_code.phone_code_hash
                })
                await message.reply("📨 کد تایید به شماره ارسال شد. لطفاً کد را به صورت 12-345 ارسال کنید:")
            except Exception as e:
                await message.reply(f"⚠️ خطا در ارسال کد: {e}")
                await helper.disconnect()
                del user_states[user_id]
            return

        # افزودن اکانت - دریافت کد ورود
        if state["step"] == "awaiting_code":
            code = message.text.strip().replace("-", "")
            helper = state["helper"]
            try:
                await helper.sign_in(phone_number=state["phone"], phone_code_hash=state["code_hash"], phone_code=code)
                me = await helper.get_me()
                add_account({
                    "name": me.first_name,
                    "username": me.username or "unknown",
                    "phone": state["phone"],
                    "status": "healthy"
                })
                await message.reply(f"✅ اکانت @{me.username or 'unknown'} اضافه شد.")
                await helper.disconnect()
                del user_states[user_id]
            except SessionPasswordNeeded:
                state["step"] = "awaiting_2fa"
                await message.reply("🔒 لطفاً رمز عبور دو مرحله‌ای را وارد کنید:")
            except Exception as e:
                await message.reply(f"❌ خطا در ورود: {e}")
                await helper.disconnect()
                del user_states[user_id]
            return

        # افزودن اکانت - دریافت رمز عبور دو مرحله‌ای
        if state["step"] == "awaiting_2fa":
            password = message.text.strip()
            helper = state["helper"]
            try:
                await helper.check_password(password)
                me = await helper.get_me()
                add_account({
                    "name": me.first_name,
                    "username": me.username or "unknown",
                    "phone": state["phone"],
                    "status": "healthy"
                })
                await message.reply(f"✅ اکانت @{me.username or 'unknown'} با موفقیت اضافه شد.")
            except Exception as e:
                await message.reply(f"❌ خطا در رمز عبور دو مرحله‌ای: {e}")
            finally:
                await helper.disconnect()
                del user_states[user_id]
            return

        # آنالیز ویس‌کال
        if state["step"] == "awaiting_voice_link":
            link = message.text.strip()
            await message.reply("🔍 در حال ورود به گروه و آنالیز...")

            accounts = get_accounts_by_status("healthy")
            if not accounts:
                await message.reply("❌ هیچ اکانت سالمی یافت نشد.")
                del user_states[user_id]
                return

            phone = accounts[0]["phone"]
            session_path = f"sessions/{phone}"
            helper = Client(session_path, config.API_ID, config.API_HASH, phone_number=phone)

            try:
                await helper.start()
                chat = await helper.join_chat(link)
                participants = await helper.get_participants(chat.id)
                usernames = [p.username or p.first_name for p in participants if p.username]

                log_voice_participants(chat.title, usernames)
                text = f"🔊 ویس‌کال گروه {chat.title} تحلیل شد.\n\nافراد حاضر:\n" + "\n".join([f"@{u}" for u in usernames])
                await bot.send_message(REPORT_GROUP_ID, text)
                await message.reply("✅ نتیجه در گروه گزارش ارسال شد.")

            except Exception as e:
                await message.reply(f"⚠️ خطا در آنالیز: {e}")

            finally:
                await helper.stop()
                del user_states[user_id]
            return

        # آنالیز چت
        if state["step"] == "awaiting_chat_link":
            link = message.text.strip()
            await message.reply("📥 در حال بررسی 2000 پیام آخر...")

            accounts = get_accounts_by_status("healthy")
            if not accounts:
                await message.reply("❌ هیچ اکانت سالمی برای بررسی نیست.")
                del user_states[user_id]
                return

            phone = accounts[0]["phone"]
            session_path = f"sessions/{phone}"
            helper = Client(session_path, config.API_ID, config.API_HASH, phone_number=phone)

            try:
                await helper.start()
                chat = await helper.join_chat(link)
                messages = []
                async for msg in helper.get_chat_history(chat.id, limit=2000):
                    messages.append(msg)

                user_counts = {}
                for msg in messages:
                    if msg.from_user:
                        username = msg.from_user.username or msg.from_user.first_name
                        user_counts[username] = user_counts.get(username, 0) + 1

                active_users = [u for u, count in user_counts.items() if count > 50]

                if not active_users:
                    await message.reply("❌ هیچ کاربر فعالی یافت نشد.")
                else:
                    result = "📊 کاربران فعال (بیش از 50 پیام):\n\n" + "\n".join([f"@{u}" for u in active_users])
                    await bot.send_message(REPORT_GROUP_ID, result)
                    await message.reply("✅ لیست کاربران فعال ارسال شد.")

            except Exception as e:
                await message.reply(f"⚠️ خطا: {e}")

            finally:
                await helper.stop()
                del user_states[user_id]
            return


async def main():
    initialize_db()
    await bot.start()
    print("✅ ربات آماده است.")
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
