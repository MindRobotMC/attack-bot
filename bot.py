import os
import json
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- مشخصات ---
BOT_TOKEN = "8032544795:AAF6uK-SKxG5fzAWSUTRauqXor4YG7013Jk"
API_ID = 29698707
API_HASH = "22b012816bcf16d58d826e6e3606a273"
OWNER_ID = 7608419661

bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- فایل‌های داده ---
HELPERS_FILE = "helpers.json"
STATS_FILE = "stats.json"
ATTACK_GROUPS_FILE = "attack_groups.json"

# --- متغیرهای موقت ---
user_states = {}
temp_data = {}

# --- ایجاد فایل‌ها ---
for filename, default in [
    (HELPERS_FILE, []),
    (STATS_FILE, {"daily": {}, "weekly": {}, "monthly": {}, "yearly": {}}),
    (ATTACK_GROUPS_FILE, [])
]:
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            json.dump(default, f, indent=2)

# --- توابع کمکی ---
def load_json(filename):
    with open(filename, "r") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def get_today_str():
    return datetime.now().strftime("%Y-%m-%d")

def get_week_str():
    now = datetime.now()
    return f"{now.year}-W{now.isocalendar()[1]}"

def get_month_str():
    return datetime.now().strftime("%Y-%m")

def get_year_str():
    return str(datetime.now().year)

# --- منوی اصلی ---
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 اتک", callback_data="attack_menu")],
        [InlineKeyboardButton("📄 لیست اکانت‌ها", callback_data="list_1")],
        [InlineKeyboardButton("➕ اضافه کردن اکانت", callback_data="add")],
        [InlineKeyboardButton("📊 آمار ارسال‌ها", callback_data="stats")],
        [InlineKeyboardButton("📘 راهنما", url="https://t.me/+wZVsaT38RHE5YjU8")],
        [InlineKeyboardButton("ℹ️ درباره MC", callback_data="about")],
        [InlineKeyboardButton("🆕 یوزرنیم ممبرای ویسکال", callback_data="get_voicecall_usernames")],
        [InlineKeyboardButton("🆕 یوزرنیم اعضای چت فعال", callback_data="get_activechat_usernames")],
        [InlineKeyboardButton("💬 ارتباط با سازنده", url="https://t.me/mindrobotmc")],
    ])

# --- شروع ربات ---
@bot.on_message(filters.private & filters.command("start"))
async def start(client, message):
    if message.from_user.id != OWNER_ID:
        return
    await message.reply("به ربات MC خوش آمدید!", reply_markup=main_menu())

# --- مدیریت کال‌بک‌ها ---
@bot.on_callback_query()
async def callback(client, call):
    if call.from_user.id != OWNER_ID:
        await call.answer("دسترسی ندارید.", show_alert=True)
        return

    data = call.data

    if data == "about":
        about_text = (
            "🤖 ربات MC - مدیریت پیشرفته اکانت‌ها و اتک\n"
            "توسعه یافته توسط @mindrobotmc\n"
            "هدف: تسهیل مدیریت و ارسال اتک و تحلیل آمار."
        )
        await call.message.edit_text(about_text, reply_markup=main_menu())
        await call.answer()
        return

    if data == "help":
        await call.message.edit_text(
            "📘 راهنما:\n"
            "برای آموزش کامل به کانال زیر مراجعه کنید:\n"
            "https://t.me/+wZVsaT38RHE5YjU8",
            reply_markup=main_menu()
        )
        await call.answer()
        return

    if data == "stats":
        stats = load_json(STATS_FILE)
        today = get_today_str()
        week = get_week_str()
        month = get_month_str()
        year = get_year_str()

        daily = stats.get("daily", {}).get(today, 0)
        weekly = stats.get("weekly", {}).get(week, 0)
        monthly = stats.get("monthly", {}).get(month, 0)
        yearly = stats.get("yearly", {}).get(year, 0)

        text = (
            f"📊 آمار ارسال‌ها:\n"
            f"🔹 روزانه: {daily}\n"
            f"🔹 هفتگی: {weekly}\n"
            f"🔹 ماهانه: {monthly}\n"
            f"🔹 سالانه: {yearly}"
        )
        await call.message.edit_text(text, reply_markup=main_menu())
        await call.answer()
        return

    if data.startswith("list_") or data == "list":
        page = 1
        if "_" in data:
            try:
                page = int(data.split("_")[1])
            except:
                page = 1

        helpers = load_json(HELPERS_FILE)
        if not helpers:
            await call.message.edit_text("⚠️ هیچ اکانتی ثبت نشده.", reply_markup=main_menu())
            await call.answer()
            return

        per_page = 5
        total = len(helpers)
        total_pages = (total + per_page - 1) // per_page
        page = max(1, min(page, total_pages))
        page_items = helpers[(page-1)*per_page : page*per_page]

        text = f"📄 <b>لیست اکانت‌ها (صفحه {page}/{total_pages}):</b>\n\n"
        buttons = []

        for i, acc in enumerate(page_items, start=(page-1)*per_page+1):
            phone = acc.get("phone")
            report = acc.get("report", False)
            report_end = acc.get("report_end", "ندارد")

            status = "✅ سالم" if not report else f"❌ ریپورت تا {report_end}"
            text += f"<b>{i}.</b> <code>{phone}</code> - {status}\n"

            btns = [
                InlineKeyboardButton("❌ حذف", callback_data=f"del_{phone}")
            ]
            buttons.append(btns)

        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"list_{page-1}"))
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"list_{page+1}"))
        if nav_buttons:
            buttons.append(nav_buttons)

        buttons.append([InlineKeyboardButton("🔄 بروزرسانی", callback_data=f"list_{page}")])
        buttons.append([InlineKeyboardButton("🏠 منوی اصلی", callback_data="main")])

        await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="html")
        await call.answer()
        return

    if data.startswith("del_"):
        phone = data.split("_", 1)[1]
        helpers = load_json(HELPERS_FILE)
        new_helpers = [acc for acc in helpers if acc.get("phone") != phone]
        save_json(HELPERS_FILE, new_helpers)
        await call.answer(f"اکانت {phone} حذف شد.")
        await call.message.edit_text("لیست اکانت‌ها بروزرسانی شد.", reply_markup=main_menu())
        return

    if data == "add":
        if user_states.get(call.from_user.id) == "awaiting_phone":
            await call.answer("⏳ لطفاً ابتدا شماره قبلی را وارد کنید.", show_alert=True)
            return
        user_states[call.from_user.id] = "awaiting_phone"
        await call.answer()
        await bot.send_message(call.from_user.id, "➕ لطفاً شماره اکانت را با +98 ارسال کنید.")
        return

    if data == "attack_menu":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ اتک زده شده‌ها", callback_data="attack_done")],
            [InlineKeyboardButton("❌ اتک زده نشده‌ها", callback_data="attack_not_done")],
            [InlineKeyboardButton("➕ ثبت گروه جدید", callback_data="attack_add_group")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main")],
        ])
        await call.message.edit_text("📩 منوی اتک", reply_markup=keyboard)
        await call.answer()
        return

    if data == "attack_done":
        groups = load_json(ATTACK_GROUPS_FILE)
        done = [g for g in groups if g.get("attacked", False)]
        if not done:
            await call.message.edit_text("❌ هیچ گروهی هنوز اتک زده نشده.", reply_markup=main_menu())
            await call.answer()
            return

        text = "✅ گروه‌های اتک زده شده:\n\n"
        buttons = []
        for i, g in enumerate(done, 1):
            text += f"{i}. {g.get('title', 'بدون عنوان')} - {g.get('group_id', 'نامشخص')}\n"
        buttons.append([InlineKeyboardButton("🏠 منوی اصلی", callback_data="main")])
        await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        await call.answer()
        return

    if data == "attack_not_done":
        groups = load_json(ATTACK_GROUPS_FILE)
        not_done = [g for g in groups if not g.get("attacked", False)]
        if not not_done:
            await call.message.edit_text("✅ همه گروه‌ها اتک زده شده‌اند.", reply_markup=main_menu())
            await call.answer()
            return

        text = "❌ گروه‌های اتک زده نشده:\n\n"
        buttons = []
        for i, g in enumerate(not_done, 1):
            text += f"{i}. {g.get('title', 'بدون عنوان')} - {g.get('group_id', 'نامشخص')}\n"
        buttons.append([InlineKeyboardButton("🏠 منوی اصلی", callback_data="main")])
        await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        await call.answer()
        return

    if data == "attack_add_group":
        if user_states.get(call.from_user.id) == "awaiting_attack_group":
            await call.answer("⏳ لطفاً ابتدا گروه قبلی را وارد کنید.", show_alert=True)
            return
        user_states[call.from_user.id] = "awaiting_attack_group"
        await call.answer()
        await bot.send_message(call.from_user.id, "➕ لطفاً آیدی گروه یا عنوان گروه جدید را ارسال کنید.")
        return

    if data == "get_voicecall_usernames":
        # نمونه ساده - برای توسعه خودتان
        await call.message.edit_text(
            "🆕 دریافت لیست یوزرنیم ممبرای ویسکال:\n(نمونه)\nuser1\nuser2\nuser3",
            reply_markup=main_menu()
        )
        await call.answer()
        return

    if data == "get_activechat_usernames":
        # نمونه ساده - برای توسعه خودتان
        await call.message.edit_text(
            "🆕 دریافت لیست یوزرنیم اعضای چت فعال:\n(نمونه)\nuserA\nuserB\nuserC",
            reply_markup=main_menu()
        )
        await call.answer()
        return

    if data == "main":
        await call.message.edit_text("🏠 منوی اصلی", reply_markup=main_menu())
        await call.answer()
        return

    await call.answer()

# --- دریافت متن برای اضافه کردن اکانت و ثبت گروه اتک ---
@bot.on_message(filters.private & filters.text)
async def handle_text(client, message):
    if message.from_user.id != OWNER_ID:
        return

    state = user_states.get(message.from_user.id)

    if state == "awaiting_phone":
        phone = message.text.strip()
        if not phone.startswith("+98"):
            await message.reply("❌ شماره باید با +98 شروع شود.")
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
            await message.reply("📨 کد به تلگرام ارسال شد. لطفاً کد را وارد کنید (مثال: 45-234).")
        except Exception as e:
            await message.reply(f"❌ خطا در ارسال کد: {e}")
            user_states.pop(message.from_user.id, None)
        return

    if state == "awaiting_code":
        raw_code = message.text.strip()
        code = "".join(filter(str.isdigit, raw_code))
        data = temp_data.get(message.from_user.id)
        if not data:
            await message.reply("❌ مشکلی پیش آمده، لطفاً دوباره تلاش کنید.")
            user_states.pop(message.from_user.id, None)
            return

        phone = data["phone"]
        phone_code_hash = data["phone_code_hash"]
        tg_client = data["client"]

        try:
            await tg_client.sign_in(phone_number=phone, phone_code_hash=phone_code_hash, phone_code=code)
            session_string = await tg_client.export_session_string()
            await tg_client.disconnect()

            helpers = load_json(HELPERS_FILE)
            acc_data = {
                "phone": phone,
                "report": False,
                "report_end": None
            }
            if not any(acc.get("phone") == phone for acc in helpers):
                helpers.append(acc_data)
                save_json(HELPERS_FILE, helpers)

            await message.reply(f"✅ اکانت {phone} وارد شد و ذخیره شد.\n\nکد جلسه:\n<code>{session_string}</code>", parse_mode="html")
        except Exception as e:
            await message.reply(f"❌ ورود ناموفق:\n{e}")
        finally:
            user_states.pop(message.from_user.id, None)
            temp_data.pop(message.from_user.id, None)
        return

    if state == "awaiting_attack_group":
        group_text = message.text.strip()
        groups = load_json(ATTACK_GROUPS_FILE)
        if any(g.get("group_id") == group_text or g.get("title") == group_text for g in groups):
            await message.reply("⚠️ این گروه قبلاً ثبت شده است.")
            user_states.pop(message.from_user.id, None)
            return

        group_data = {
            "group_id": group_text,
            "title": group_text,
            "attacked": False,
            "created_at": datetime.now().isoformat()
        }
        groups.append(group_data)
        save_json(ATTACK_GROUPS_FILE, groups)
        await message.reply(f"✅ گروه جدید ثبت شد:\n{group_text}")
        user_states.pop(message.from_user.id, None)
        return

# --- اجرای ربات ---
bot.run()
