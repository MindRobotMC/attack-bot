import os
import json
import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import FloodWait, RPCError

# --- تنظیمات ربات ---
BOT_TOKEN = "8032544795:AAF6uK-SKxG5fzAWSUTRauqXor4YG7013Jk"
API_ID = 29698707
API_HASH = "22b012816bcf16d58d826e6e3606a273"
OWNER_ID = 7608419661

# --- فایل‌ها ---
HELPERS_FILE = "helpers.json"
ATTACK_GROUPS_FILE = "attack_groups.json"
STATS_FILE = "stats.json"
LOG_FILE = "attack_logs.json"

# --- اطمینان از وجود فایل‌ها ---
def ensure_file(filename, default):
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2, ensure_ascii=False)

ensure_file(HELPERS_FILE, [])
ensure_file(ATTACK_GROUPS_FILE, [])
ensure_file(STATS_FILE, {"daily": {}, "monthly": {}, "yearly": {}})
ensure_file(LOG_FILE, [])

# --- بارگذاری و ذخیره داده‌ها ---
def load_json(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- کلاینت اصلی ربات ---
bot = Client("mc_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

helper_clients = {}
user_states = {}
temp_data = {}

# --- منوها ---
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 منوی اتک", callback_data="menu_attack")],
        [InlineKeyboardButton("📊 مدیریت اکانت‌ها", callback_data="menu_accounts")],
        [InlineKeyboardButton("📈 آمار", callback_data="menu_stats")],
        [InlineKeyboardButton("🆔 دریافت آیدی", callback_data="menu_get_id")],
        [InlineKeyboardButton("📘 راهنما", url="https://t.me/+wZVsaT38RHE5YjU8")],
        [InlineKeyboardButton("💬 ارتباط با سازنده", url="https://t.me/CILMC")],
        [InlineKeyboardButton("🏢 نمایندگی", callback_data="menu_agency")],
    ])

def attack_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 همه گروه‌ها", callback_data="attack_all_groups")],
        [InlineKeyboardButton("✅ گروه‌های اتک زده شده", callback_data="attack_done")],
        [InlineKeyboardButton("🕐 گروه‌های آماده اتک", callback_data="attack_ready")],
        [InlineKeyboardButton("➕ ثبت گروه جدید", callback_data="attack_add_group")],
        [InlineKeyboardButton("↩️ بازگشت", callback_data="main")],
    ])

def accounts_status_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ اکانت‌های سالم", callback_data="acc_status_healthy")],
        [InlineKeyboardButton("❌ اکانت‌های ریپورت", callback_data="acc_status_reported")],
        [InlineKeyboardButton("🗑 اکانت‌های دیلیت شده", callback_data="acc_status_deleted")],
        [InlineKeyboardButton("🔄 اکانت‌های درحال ریکاوری", callback_data="acc_status_recovering")],
        [InlineKeyboardButton("➕ ثبت اکانت هلپر", callback_data="add_helper")],
        [InlineKeyboardButton("🗑 حذف اکانت", callback_data="delete_helper")],
        [InlineKeyboardButton("📋 مشاهده لاگ‌ها", callback_data="view_logs")],
        [InlineKeyboardButton("↩️ بازگشت", callback_data="main")],
    ])

def stats_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 آمار سالانه", callback_data="stats_yearly")],
        [InlineKeyboardButton("📆 آمار ماهانه", callback_data="stats_monthly")],
        [InlineKeyboardButton("📈 آمار روزانه", callback_data="stats_daily")],
        [InlineKeyboardButton("↩️ بازگشت", callback_data="main")],
    ])

def get_id_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 لیست همه یوزرنیم‌ها", callback_data="get_id_all_usernames")],
        [InlineKeyboardButton("🎙 آنالیز اعضای ویسکال", callback_data="get_id_voice_chat")],
        [InlineKeyboardButton("💬 آنالیز اعضای چت", callback_data="get_id_chat")],
        [InlineKeyboardButton("⚙️ آنالیز پیشرفته", callback_data="get_id_advanced")],
        [InlineKeyboardButton("↩️ بازگشت", callback_data="main")],
    ])

# --- اتصال هلپر ---
async def connect_helper(phone: str):
    if phone in helper_clients:
        return helper_clients[phone]
    client = Client(
        f"helper_{phone}",
        api_id=API_ID,
        api_hash=API_HASH,
        phone_number=phone
    )
    try:
        await client.start()
        helper_clients[phone] = client
        return client
    except Exception as e:
        print(f"[ERROR] اتصال هلپر {phone} شکست خورد: {e}")
        return None

# --- ارسال پیام اتک ---
async def send_attack(helper_client: Client, group: dict, message_text: str):
    chat_id = group.get("chat_id")
    if not chat_id:
        return False, "گروه آیدی ندارد"
    try:
        await helper_client.send_message(chat_id, message_text)
        return True, None
    except FloodWait as e:
        print(f"[WAIT] باید {e.x} ثانیه صبر کنیم.")
        await asyncio.sleep(e.x + 5)
        return False, "FloodWait"
    except RPCError as e:
        print(f"[RPC ERROR] {e}")
        return False, str(e)
    except Exception as e:
        print(f"[ERROR] ارسال پیام شکست خورد: {e}")
        return False, str(e)

# --- بروزرسانی آمار ---
def update_stats():
    stats = load_json(STATS_FILE) or {"daily": {}, "monthly": {}, "yearly": {}}
    now = datetime.now()
    day = now.strftime("%Y-%m-%d")
    month = now.strftime("%Y-%m")
    year = now.strftime("%Y")

    stats["daily"][day] = stats["daily"].get(day, 0) + 1
    stats["monthly"][month] = stats["monthly"].get(month, 0) + 1
    stats["yearly"][year] = stats["yearly"].get(year, 0) + 1

    save_json(STATS_FILE, stats)

# --- ذخیره لاگ اتک ---
def log_attack(phone, group_title, status, error=None):
    logs = load_json(LOG_FILE) or []
    logs.append({
        "phone": phone,
        "group": group_title,
        "status": status,
        "error": error,
        "timestamp": datetime.now().isoformat()
    })
    save_json(LOG_FILE, logs)

# --- حذف اکانت هلپر ---
def delete_helper_account(phone):
    helpers = load_json(HELPERS_FILE) or []
    helpers = [h for h in helpers if h.get("phone") != phone]
    save_json(HELPERS_FILE, helpers)
    if phone in helper_clients:
        client = helper_clients.pop(phone)
        asyncio.create_task(client.stop())

# --- دریافت لاگ‌های یک اکانت ---
def get_logs_by_phone(phone):
    logs = load_json(LOG_FILE) or []
    return [log for log in logs if log.get("phone") == phone]

# --- هندلر شروع ربات ---
@bot.on_message(filters.private & filters.command("start"))
async def start_handler(client, message):
    if message.from_user.id != OWNER_ID:
        return
    await message.reply("به ربات MC خوش آمدید!", reply_markup=main_menu())

# --- کال‌بک‌ها ---
@bot.on_callback_query()
async def callback_handler(client, call):
    if call.from_user.id != OWNER_ID:
        await call.answer("شما اجازه دسترسی ندارید.", show_alert=True)
        return

    data = call.data

    if data == "main":
        await call.message.edit_text("🏠 منوی اصلی", reply_markup=main_menu())
        await call.answer()
        return

    if data == "menu_attack":
        await call.message.edit_text("📩 منوی اتک", reply_markup=attack_menu())
        await call.answer()
        return

    if data == "menu_accounts":
        await call.message.edit_text("📊 مدیریت اکانت‌ها", reply_markup=accounts_status_menu())
        await call.answer()
        return

    if data == "menu_stats":
        await call.message.edit_text("📈 آمار ارسال‌ها", reply_markup=stats_menu())
        await call.answer()
        return

    if data == "menu_get_id":
        await call.message.edit_text("🆔 دریافت آیدی", reply_markup=get_id_menu())
        await call.answer()
        return

    if data == "menu_agency":
        await call.message.edit_text("🏢 بخش نمایندگی به زودی فعال می‌شود.", reply_markup=main_menu())
        await call.answer()
        return

    # نمایش همه گروه‌ها
    if data == "attack_all_groups":
        groups = load_json(ATTACK_GROUPS_FILE) or []
        if not groups:
            await call.message.edit_text("⚠️ گروهی ثبت نشده است.", reply_markup=attack_menu())
            await call.answer()
            return
        text = "📋 همه گروه‌ها:\n\n"
        for i, g in enumerate(groups, 1):
            attacked = g.get('attacked', False)
            attacked_text = "✅ اتک زده شده" if attacked else "❌ اتک زده نشده"
            text += f"{i}. {g.get('title', 'بدون عنوان')} - {attacked_text}\n"
        await call.message.edit_text(text, reply_markup=attack_menu())
        await call.answer()
        return

    if data == "attack_done":
        groups = load_json(ATTACK_GROUPS_FILE) or []
        done = [g for g in groups if g.get("attacked")]
        if not done:
            await call.message.edit_text("❌ هیچ گروهی اتک زده نشده است.", reply_markup=attack_menu())
            await call.answer()
            return
        text = "✅ گروه‌های اتک زده شده:\n\n"
        for i, g in enumerate(done, 1):
            text += f"{i}. {g.get('title', 'بدون عنوان')}\n"
        await call.message.edit_text(text, reply_markup=attack_menu())
        await call.answer()
        return

    if data == "attack_ready":
        groups = load_json(ATTACK_GROUPS_FILE) or []
        ready = [g for g in groups if not g.get("attacked")]
        if not ready:
            await call.message.edit_text("✅ همه گروه‌ها آماده اتک هستند.", reply_markup=attack_menu())
            await call.answer()
            return
        text = "🕐 گروه‌های آماده اتک:\n\n"
        for i, g in enumerate(ready, 1):
            text += f"{i}. {g.get('title', 'بدون عنوان')}\n"
        await call.message.edit_text(text, reply_markup=attack_menu())
        await call.answer()
        return

    if data == "attack_add_group":
        user_states[call.from_user.id] = "awaiting_attack_group"
        await call.message.edit_text("➕ لطفاً عنوان گروه جدید را ارسال کنید.")
        await call.answer()
        return

    # مدیریت اکانت‌ها با فیلتر وضعیت‌ها
    if data.startswith("acc_status_"):
        status = data[len("acc_status_"):]
        helpers = load_json(HELPERS_FILE) or []
        filtered = []
        if status == "healthy":
            filtered = [h for h in helpers if not h.get("report", False) and not h.get("deleted", False)]
            title = "✅ اکانت‌های سالم"
        elif status == "reported":
            filtered = [h for h in helpers if h.get("report", False)]
            title = "❌ اکانت‌های ریپورت"
        elif status == "deleted":
            filtered = [h for h in helpers if h.get("deleted", False)]
            title = "🗑 اکانت‌های دیلیت شده"
        elif status == "recovering":
            filtered = [h for h in helpers if h.get("recovering", False)]
            title = "🔄 اکانت‌های درحال ریکاوری"
        else:
            filtered = helpers
            title = "اکانت‌ها"

        if not filtered:
            await call.message.edit_text(f"⚠️ هیچ اکانتی با وضعیت {title} یافت نشد.", reply_markup=accounts_status_menu())
            await call.answer()
            return

        text = f"{title}:\n\n"
        for i, h in enumerate(filtered, 1):
            phone = h.get("phone", "ناشناخته")
            extra = ""
            if h.get("report", False):
                extra = f" - ریپورت تا {h.get('report_end', 'نامشخص')}"
            text += f"{i}. {phone}{extra}\n"
        text += "\nبرای حذف اکانت: /delete_helper <شماره>\nبرای مشاهده لاگ‌ها: /view_logs <شماره>"
        await call.message.edit_text(text, reply_markup=accounts_status_menu())
        await call.answer()
        return

    if data == "add_helper":
        if user_states.get(call.from_user.id):
            await call.answer("⏳ ابتدا فرایند قبلی را کامل کنید.", show_alert=True)
            return
        user_states[call.from_user.id] = "awaiting_phone"
        await call.message.edit_text("➕ لطفاً شماره اکانت هلپر را با +98 وارد کنید.")
        await call.answer()
        return

    if data == "delete_helper":
        await call.message.edit_text("برای حذف اکانت از دستور زیر استفاده کنید:\n\n/delete_helper +989123456789", reply_markup=accounts_status_menu())
        await call.answer()
        return

    if data == "view_logs":
        await call.message.edit_text("برای مشاهده لاگ‌ها از دستور زیر استفاده کنید:\n\n/view_logs +989123456789", reply_markup=accounts_status_menu())
        await call.answer()
        return

    # آمار ساده (سالانه، ماهانه، روزانه)
    if data == "stats_yearly":
        stats = load_json(STATS_FILE) or {}
        yearly = stats.get("yearly", {})
        text = "📅 آمار ارسال سالانه:\n"
        if not yearly:
            text += "⚠️ داده‌ای موجود نیست."
        else:
            for year, count in sorted(yearly.items()):
                text += f"{year}: {count}\n"
        await call.message.edit_text(text, reply_markup=stats_menu())
        await call.answer()
        return

    if data == "stats_monthly":
        stats = load_json(STATS_FILE) or {}
        monthly = stats.get("monthly", {})
        text = "📆 آمار ارسال ماهانه:\n"
        if not monthly:
            text += "⚠️ داده‌ای موجود نیست."
        else:
            for month, count in sorted(monthly.items()):
                text += f"{month}: {count}\n"
        await call.message.edit_text(text, reply_markup=stats_menu())
        await call.answer()
        return

    if data == "stats_daily":
        stats = load_json(STATS_FILE) or {}
        daily = stats.get("daily", {})
        text = "📈 آمار ارسال روزانه:\n"
        if not daily:
            text += "⚠️ داده‌ای موجود نیست."
        else:
            for day, count in sorted(daily.items()):
                text += f"{day}: {count}\n"
        await call.message.edit_text(text, reply_markup=stats_menu())
        await call.answer()
        return

    # دریافت آیدی نمونه
    if data == "get_id_all_usernames":
        await call.message.edit_text("لیست یوزرنیم‌ها:\n@user1\n@user2\n@user3", reply_markup=get_id_menu())
        await call.answer()
        return

    if data == "get_id_voice_chat":
        await call.message.edit_text("در حال پردازش اعضای ویسکال... (نیاز به پیاده‌سازی)", reply_markup=get_id_menu())
        await call.answer()
        return

    if data == "get_id_chat":
        await call.message.edit_text("در حال پردازش اعضای چت... (نیاز به پیاده‌سازی)", reply_markup=get_id_menu())
        await call.answer()
        return

    if data == "get_id_advanced":
        await call.message.edit_text("آنالیز پیشرفته... (نیاز به توسعه بیشتر)", reply_markup=get_id_menu())
        await call.answer()
        return

# --- هندلر پیام‌ها ---
@bot.on_message(filters.private & ~filters.command("start"))
async def message_handler(client, message: Message):
    if message.from_user.id != OWNER_ID:
        # حذف پیام کاربران غیر مجاز
        await message.delete()
        return

    state = user_states.get(message.from_user.id)

    if state == "awaiting_phone":
        phone = message.text.strip()
        helpers = load_json(HELPERS_FILE) or []
        if any(h.get("phone") == phone for h in helpers):
            await message.reply("⚠️ این شماره قبلاً ثبت شده است.", reply_markup=accounts_status_menu())
            user_states.pop(message.from_user.id, None)
            return
        # ذخیره موقت شماره
        temp_data[message.from_user.id] = {"phone": phone}
        await message.reply("📲 لطفاً کد OTP دریافتی را ارسال کنید.")
        user_states[message.from_user.id] = "awaiting_otp"
        return

    if state == "awaiting_otp":
        otp = message.text.strip()
        phone = temp_data.get(message.from_user.id, {}).get("phone")
        # فرضی: otp = "1234"
        if otp != "1234":
            await message.reply("⚠️ کد OTP اشتباه است. دوباره تلاش کنید.")
            return

        # اضافه کردن اکانت هلپر به فایل
        helpers = load_json(HELPERS_FILE) or []
        helpers.append({"phone": phone, "report": False, "deleted": False, "recovering": False})
        save_json(HELPERS_FILE, helpers)
        await message.reply(f"✅ اکانت {phone} با موفقیت ثبت شد.", reply_markup=accounts_status_menu())
        user_states.pop(message.from_user.id, None)
        temp_data.pop(message.from_user.id, None)
        return

    if state == "awaiting_attack_group":
        title = message.text.strip()
        groups = load_json(ATTACK_GROUPS_FILE) or []
        groups.append({"title": title, "chat_id": None, "attacked": False})
        save_json(ATTACK_GROUPS_FILE, groups)
        await message.reply(f"✅ گروه '{title}' با موفقیت ثبت شد.", reply_markup=attack_menu())
        user_states.pop(message.from_user.id, None)
        return

# --- فرمان حذف اکانت هلپر ---
@bot.on_message(filters.private & filters.command("delete_helper"))
async def delete_helper_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) != 2:
        await message.reply("استفاده: /delete_helper <شماره>")
        return
    phone = args[1]
    delete_helper_account(phone)
    await message.reply(f"اکانت {phone} حذف شد.", reply_markup=accounts_status_menu())

# --- فرمان مشاهده لاگ‌ها ---
@bot.on_message(filters.private & filters.command("view_logs"))
async def view_logs_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) != 2:
        await message.reply("استفاده: /view_logs <شماره>")
        return
    phone = args[1]
    logs = get_logs_by_phone(phone)
    if not logs:
        await message.reply("هیچ لاگی برای این اکانت یافت نشد.")
        return
    text = f"📋 لاگ‌های اکانت {phone}:\n\n"
    for log in logs[-10:]:
        ts = log.get("timestamp", "")
        group = log.get("group", "")
        status = log.get("status", "")
        error = log.get("error", "")
        text += f"{ts} - {group} - {status}"
        if error:
            text += f" (Error: {error})"
        text += "\n"
    await message.reply(text)

# --- اجرای ربات ---
print("Starting MC Bot...")
bot.run()
