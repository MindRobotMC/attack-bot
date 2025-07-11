import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import PhoneCodeInvalid, SessionPasswordNeeded, PhoneNumberInvalid, FloodWait

from database import (
    initialize_db, get_accounts_by_status, add_account,
    delete_account, get_all_accounts,
    initialize_group_table, add_group, delete_group, get_all_groups
)
import config

bot = Client("bot_session", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)
OWNER_ID = config.OWNER_ID

user_states = {}
group_states = {}

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

def groups_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 نمایش گروه‌ها", callback_data="show_groups")],
        [InlineKeyboardButton("➕ افزودن گروه جدید", callback_data="add_group")],
        [InlineKeyboardButton("❌ حذف گروه", callback_data="remove_group")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_main")]
    ])

def analyze_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 آنالیز اعضای چت", callback_data="analyze_chat")],
        [InlineKeyboardButton("🔊 آنالیز اعضای ویسکال", callback_data="analyze_voice")],
        [InlineKeyboardButton("📊 آنالیز پیشرفته", callback_data="analyze_advanced")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ])

# ---------------------- /start فقط برای مالک ----------------------
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

    elif data == "acc_reported":
        accounts = get_accounts_by_status("reported")
        if not accounts:
            await query.message.edit("⛔ اکانت ریپورت شده‌ای وجود ندارد.", reply_markup=account_menu())
            return
        text = "⛔ لیست اکانت‌های ریپورت:\n\n"
        for acc in accounts:
            duration = acc.get("report_duration") or "نامشخص"
            end_time = acc.get("report_end_time") or "نامشخص"
            text += f"نام: {acc['name']}\nیوزرنیم: @{acc['username']}\nشماره: {acc['phone']}\nمدت: {duration} ساعت\nتا: {end_time}\n\n"
        await query.message.edit(text, reply_markup=account_menu())

    elif data == "acc_recovering":
        accounts = get_accounts_by_status("recovering")
        if not accounts:
            await query.message.edit("🕓 اکانت در حال ریکاوری وجود ندارد.", reply_markup=account_menu())
            return
        text = "🕓 لیست اکانت‌های در حال ریکاوری:\n\n"
        for acc in accounts:
            ready_time = acc.get("ready_time") or "نامشخص"
            text += f"نام: {acc['name']}\nشماره: {acc['phone']}\nآماده در: {ready_time}\n\n"
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
        await query.message.edit("لطفاً اکانتی را برای حذف انتخاب کنید:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("delete_"):
        phone = data.split("delete_")[1]
        delete_account(phone)
        await query.message.edit(f"✅ اکانت {phone} با موفقیت حذف شد.", reply_markup=account_menu())
        try:
            await bot.send_message(config.LOG_GROUP_ID, f"❌ اکانت حذف شد:\n📞 {phone}")
        except Exception as e:
            print(f"خطا در ارسال لاگ حذف اکانت: {e}")

    elif data == "acc_logs":
        await query.message.edit("📄 بخش لاگ‌ها به‌زودی اضافه می‌شود...", reply_markup=account_menu())

    elif data == "groups":
        await query.message.edit("👥 مدیریت گروه‌ها:", reply_markup=groups_menu())

    elif data == "show_groups":
        groups = get_all_groups()
        if not groups:
            await query.message.edit("📋 گروهی یافت نشد.", reply_markup=groups_menu())
            return
        text = "📋 لیست گروه‌ها:\n\n"
        for g in groups:
            text += f"- {g}\n"
        await query.message.edit(text, reply_markup=groups_menu())

    elif data == "add_group":
        await query.message.edit("➕ لطفاً آیدی یا نام گروه جدید را ارسال کنید:")
        group_states[query.from_user.id] = {"step": "awaiting_new_group"}

    elif data == "remove_group":
        groups = get_all_groups()
        if not groups:
            await query.message.edit("❌ گروهی برای حذف وجود ندارد.", reply_markup=groups_menu())
            return
        buttons = [[InlineKeyboardButton(f"❌ {g}", callback_data=f"delgroup_{g}")] for g in groups]
        buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="groups")])
        await query.message.edit("❌ لطفاً گروهی را برای حذف انتخاب کنید:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("delgroup_"):
        group_name = data.split("delgroup_")[1]
        delete_group(group_name)
        await query.message.edit(f"✅ گروه '{group_name}' با موفقیت حذف شد.", reply_markup=groups_menu())

    elif data == "analyze":
        await query.message.edit("🔍 انتخاب نوع آنالیز:", reply_markup=analyze_menu())

    elif data == "analyze_chat":
        await query.message.edit("👥 لطفاً آیدی گروه (مثلاً -1001234567890) را ارسال کنید:")
        user_states[query.from_user.id] = {"step": "awaiting_chat_id"}

    elif data == "analyze_voice":
        await query.message.edit("🔊 لطفاً لینک گروه دارای ویسکال را ارسال کنید:")
        user_states[query.from_user.id] = {"step": "awaiting_voice_link"}

    elif data == "back_main":
        await query.message.edit("بازگشت به منوی اصلی:", reply_markup=main_buttons)

# ---------------------- پیام گروه ----------------------
@bot.on_message(filters.text & filters.user(OWNER_ID))
async def handle_text(client, message: Message):
    user_id = message.from_user.id

    # مدیریت افزودن گروه جدید
    if user_id in group_states:
        state = group_states[user_id]
        if state["step"] == "awaiting_new_group":
            group_name = message.text.strip()
            add_group(group_name)
            await message.reply(f"✅ گروه '{group_name}' با موفقیت افزوده شد.")
            del group_states[user_id]

    # مدیریت مراحل مختلف کاربر
    elif user_id in user_states:
        state = user_states[user_id]

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
                await message.reply("📨 کد ارسال شد. لطفاً کد را به‌صورت 123-45 وارد کنید:")

            except PhoneNumberInvalid:
                await message.reply("❌ شماره نامعتبر است.")
                del user_states[user_id]
            except FloodWait as e:
                await message.reply(f"⏳ لطفاً {e.value} ثانیه صبر کنید.")
                del user_states[user_id]
            except Exception as e:
                await message.reply(f"⚠️ خطا هنگام ارسال کد: {e}")
                del user_states[user_id]

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

                try:
                    await bot.send_message(config.LOG_GROUP_ID, f"📥 اکانت جدید ثبت شد:\n👤 {name}\n📞 {phone}\n🔗 @{username}")
                except Exception as e:
                    print(f"خطا در ارسال لاگ ثبت اکانت: {e}")

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

        # افزودن مراحل جدید آنالیز
        elif state["step"] == "awaiting_chat_id":
            chat_id = message.text.strip()
            accounts = get_accounts_by_status("healthy")
            if not accounts:
                await message.reply("❌ اکانت سالمی برای آنالیز وجود ندارد.")
                return

            phone = accounts[0]['phone']
            session = f"sessions/{phone}"
            helper = Client(session, config.API_ID, config.API_HASH)
            await helper.start()

            usernames = set()
            async for msg in helper.get_chat_history(int(chat_id), limit=1000):
                if msg.from_user and msg.from_user.username:
                    usernames.add(msg.from_user.username)

            result = '\n'.join([f"@{u}" for u in usernames]) or "هیچ یوزرنیمی یافت نشد."
            await client.send_message(config.LOG_GROUP_ID, f"👥 لیست اعضای فعال در چت گروه {chat_id}:\n{result}")
            await message.reply("✅ لیست در گروه گزارشات ارسال شد.")
            await helper.stop()
            del user_states[user_id]

        elif state["step"] == "awaiting_voice_link":
            link = message.text.strip()
            match = re.search(r"t\.me\/joinchat\/([\w\d_-]+)|t\.me\/\+([\w\d_-]+)", link)
            if not match:
                await message.reply("❌ لینک گروه نامعتبر است.")
                return

            invite_hash = match.group(1) or match.group(2)
            accounts = get_accounts_by_status("healthy")
            if not accounts:
                await message.reply("❌ اکانت سالمی برای آنالیز وجود ندارد.")
                return

            phone = accounts[0]['phone']
            session = f"sessions/{phone}"
            helper = Client(session, config.API_ID, config.API_HASH)
            await helper.start()

            try:
                chat = await helper.join_chat(invite_hash)
            except Exception as e:
                await message.reply(f"❌ خطا در ورود به گروه: {e}")
                await helper.stop()
                return

            try:
                call = await helper.get_group_call(chat.id)
                users = [f"@{p.user.username}" for p in call.participants if p.user and p.user.username]
                report = '\n'.join(users) or "هیچ کاربری در ویسکال نیست."
                await client.send_message(config.LOG_GROUP_ID, f"🔊 اعضای حاضر در ویسکال گروه {chat.title}:\n{report}")
                await message.reply("✅ لیست ویسکال در گروه گزارشات ارسال شد.")
            except Exception as e:
                await message.reply(f"❌ خطا در گرفتن ویسکال: {e}")

            await helper.stop()
            del user_states[user_id]

# ---------------------- اجرای اولیه ----------------------
initialize_db()
initialize_group_table()
bot.run()
