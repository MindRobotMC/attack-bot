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

helper_clients = {}  # {phone: Client}
user_states = {}     # {user_id: state}
temp_data = {}       # {user_id: {"phone": ..., "otp": ...}}

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
        [InlineKeyboardButton("🚀 اتک همگانی", callback_data="attack_mass")],
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

# --- اصلاح کد OTP (حذف کاراکتر غیرعددی) ---
def fix_otp_code(otp_raw: str) -> str:
    return ''.join(ch for ch in otp_raw if ch.isdigit())

# --- ورود هلپر با کد OTP بدون درخواست مجدد ---
async def login_helper_with_otp(phone, otp):
    client = Client(
        f"helper_{phone}",
        api_id=API_ID,
        api_hash=API_HASH,
        phone_number=phone,
        workdir=f"./sessions/helper_{phone}"
    )
    await client.connect()

    try:
        if not await client.is_user_authorized():
            await client.sign_in(phone, otp)
        if await client.is_user_authorized():
            helper_clients[phone] = client
            return client
        else:
            await client.disconnect()
            return None
    except Exception:
        await client.disconnect()
        return None

# --- اتصال هلپر (برای اکانت‌های لاگین شده) ---
async def connect_helper(phone: str):
    if phone in helper_clients:
        return helper_clients[phone]
    client = Client(
        f"helper_{phone}",
        api_id=API_ID,
        api_hash=API_HASH,
        phone_number=phone,
        workdir=f"./sessions/helper_{phone}"
    )
    try:
        await client.start()
        helper_clients[phone] = client
        print(f"[INFO] هلپر {phone} متصل شد.")
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

# --- اجرای اتک همگانی ---
async def mass_attack(message_text: str):
    groups = load_json(ATTACK_GROUPS_FILE) or []
    helpers = load_json(HELPERS_FILE) or []
    if not groups or not helpers:
        return False, "گروه یا اکانتی برای اتک یافت نشد."

    results = []
    for group in groups:
        chat_id = group.get("chat_id")
        title = group.get("title", "بدون عنوان")
        for helper in helpers:
            phone = helper.get("phone")
            if not phone:
                continue
            client = await connect_helper(phone)
            if not client:
                results.append((phone, title, False, "عدم اتصال"))
                continue
            success, error = await send_attack(client, group, message_text)
            status = "موفق" if success else f"ناموفق: {error}"
            results.append((phone, title, success, error))
            log_attack(phone, title, status, error)
            update_stats()
            if error == "FloodWait":
                await asyncio.sleep(10)
    return True, results

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
            title = g.get("title", "بدون عنوان")
            text += f"{i}. {title} - {attacked_text}\n"
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
            await call.message.edit_text("🕐 هیچ گروهی آماده اتک نیست.", reply_markup=attack_menu())
            await call.answer()
            return
        text = "🕐 گروه‌های آماده اتک:\n\n"
        for i, g in enumerate(ready, 1):
            text += f"{i}. {g.get('title', 'بدون عنوان')}\n"
        await call.message.edit_text(text, reply_markup=attack_menu())
        await call.answer()
        return

    if data == "attack_add_group":
        user_states[call.from_user.id] = "awaiting_new_group"
        await call.message.edit_text("➕ لطفاً اطلاعات گروه جدید را به صورت `آیدی گروه | نام گروه` ارسال کنید.")
        await call.answer()
        return

    if data == "attack_mass":
        user_states[call.from_user.id] = "awaiting_mass_message"
        await call.message.edit_text("🚀 لطفاً پیام اتک را ارسال کنید.")
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

    if data == "acc_status_healthy":
        helpers = load_json(HELPERS_FILE) or []
        healthy = [h for h in helpers if not h.get("report") and not h.get("deleted")]
        if not healthy:
            await call.message.edit_text("✅ اکانتی یافت نشد.", reply_markup=accounts_status_menu())
            await call.answer()
            return
        text = "✅ اکانت‌های سالم:\n\n"
        for i, h in enumerate(healthy, 1):
            text += f"{i}. {h.get('phone')}\n"
        await call.message.edit_text(text, reply_markup=accounts_status_menu())
        await call.answer()
        return

    if data == "acc_status_reported":
        helpers = load_json(HELPERS_FILE) or []
        reported = [h for h in helpers if h.get("report")]
        if not reported:
            await call.message.edit_text("❌ اکانتی یافت نشد.", reply_markup=accounts_status_menu())
            await call.answer()
            return
        text = "❌ اکانت‌های ریپورت شده:\n\n"
        for i, h in enumerate(reported, 1):
            text += f"{i}. {h.get('phone')}\n"
        await call.message.edit_text(text, reply_markup=accounts_status_menu())
        await call.answer()
        return

    if data == "acc_status_deleted":
        helpers = load_json(HELPERS_FILE) or []
        deleted = [h for h in helpers if h.get("deleted")]
        if not deleted:
            await call.message.edit_text("🗑 اکانتی یافت نشد.", reply_markup=accounts_status_menu())
            await call.answer()
            return
        text = "🗑 اکانت‌های دیلیت شده:\n\n"
        for i, h in enumerate(deleted, 1):
            text += f"{i}. {h.get('phone')}\n"
        await call.message.edit_text(text, reply_markup=accounts_status_menu())
        await call.answer()
        return

    if data == "acc_status_recovering":
        helpers = load_json(HELPERS_FILE) or []
        recovering = [h for h in helpers if h.get("recovering")]
        if not recovering:
            await call.message.edit_text("🔄 اکانتی یافت نشد.", reply_markup=accounts_status_menu())
            await call.answer()
            return
        text = "🔄 اکانت‌های در حال ریکاوری:\n\n"
        for i, h in enumerate(recovering, 1):
            text += f"{i}. {h.get('phone')}\n"
        await call.message.edit_text(text, reply_markup=accounts_status_menu())
        await call.answer()
        return

    if data == "stats_yearly":
        stats = load_json(STATS_FILE) or {"yearly": {}}
        text = "📅 آمار سالانه:\n\n"
        for year, count in stats.get("yearly", {}).items():
            text += f"{year}: {count}\n"
        await call.message.edit_text(text, reply_markup=stats_menu())
        await call.answer()
        return

    if data == "stats_monthly":
        stats = load_json(STATS_FILE) or {"monthly": {}}
        text = "📆 آمار ماهانه:\n\n"
        for month, count in stats.get("monthly", {}).items():
            text += f"{month}: {count}\n"
        await call.message.edit_text(text, reply_markup=stats_menu())
        await call.answer()
        return

    if data == "stats_daily":
        stats = load_json(STATS_FILE) or {"daily": {}}
        text = "📈 آمار روزانه:\n\n"
        for day, count in stats.get("daily", {}).items():
            text += f"{day}: {count}\n"
        await call.message.edit_text(text, reply_markup=stats_menu())
        await call.answer()
        return

    # دریافت یوزرنیم‌ها، آنالیز و سایر موارد در آینده اضافه می‌شود.

# --- دریافت پیام‌ها برای تکمیل عملیات ---
@bot.on_message(filters.private & filters.incoming)
async def private_message_handler(client, message: Message):
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if user_id != OWNER_ID:
        return

    # دریافت شماره برای ثبت هلپر
    if state == "awaiting_phone":
        phone = message.text.strip()
        if not (phone.startswith("+98") and phone[1:].isdigit()):
            await message.reply("شماره صحیح نیست. لطفاً با +98 وارد کنید.")
            return
        temp_data[user_id] = {"phone": phone}
        user_states[user_id] = "awaiting_otp"
        await message.reply("لطفاً کد ارسال شده به تلگرام را ارسال کنید (مثال: 45_788).")
        return

    # دریافت کد OTP و ورود هلپر
    if state == "awaiting_otp":
        otp_raw = message.text.strip()
        otp = fix_otp_code(otp_raw)
        if not otp.isdigit() or len(otp) < 4:
            await message.reply("کد OTP نامعتبر است. دوباره ارسال کنید.")
            return

        phone = temp_data[user_id]["phone"]

        helper_client = await login_helper_with_otp(phone, otp)

        if helper_client is None:
            await message.reply("ورود موفق نبود، لطفاً شماره را دوباره ارسال کنید.")
            user_states[user_id] = "awaiting_phone"
            return

        helpers = load_json(HELPERS_FILE) or []
        helpers = [h for h in helpers if h.get("phone") != phone]
        helpers.append({
            "phone": phone,
            "report": False,
            "deleted": False,
            "recovering": False,
            "added_at": datetime.now().isoformat()
        })
        save_json(HELPERS_FILE, helpers)

        user_states.pop(user_id, None)
        temp_data.pop(user_id, None)

        await message.reply(f"اکانت هلپر {phone} با موفقیت ثبت شد.", reply_markup=main_menu())
        return

    # دریافت اطلاعات گروه جدید
    if state == "awaiting_new_group":
        text = message.text.strip()
        if "|" not in text:
            await message.reply("فرمت اشتباه است. لطفاً به صورت `آیدی گروه | نام گروه` ارسال کنید.")
            return
        chat_id_str, title = map(str.strip, text.split("|", 1))
        if not chat_id_str.startswith("-100") or not chat_id_str[1:].isdigit():
            await message.reply("آیدی گروه باید عددی و با -100 شروع شود.")
            return
        chat_id = int(chat_id_str)
        groups = load_json(ATTACK_GROUPS_FILE) or []
        groups.append({"chat_id": chat_id, "title": title, "attacked": False})
        save_json(ATTACK_GROUPS_FILE, groups)
        user_states.pop(user_id, None)
        await message.reply(f"گروه '{title}' با موفقیت ثبت شد.", reply_markup=attack_menu())
        return

    # دریافت پیام برای اتک همگانی
    if state == "awaiting_mass_message":
        msg = message.text.strip()
        success, results = await mass_attack(msg)
        if not success:
            await message.reply(f"خطا: {results}")
            user_states.pop(user_id, None)
            return

        text = "🚀 نتیجه اتک همگانی:\n\n"
        for phone, group_title, success, error in results:
            status = "✅ موفق" if success else f"❌ ناموفق ({error})"
            text += f"{phone} → {group_title}: {status}\n"

        user_states.pop(user_id, None)
        await message.reply(text, reply_markup=attack_menu())
        return

# --- دستورات حذف اکانت و مشاهده لاگ‌ها ---
@bot.on_message(filters.private & filters.command("delete_helper"))
async def delete_helper_cmd(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) != 2:
        await message.reply("استفاده صحیح: /delete_helper +989123456789")
        return
    phone = args[1]
    delete_helper_account(phone)
    await message.reply(f"اکانت {phone} حذف شد.", reply_markup=main_menu())

@bot.on_message(filters.private & filters.command("view_logs"))
async def view_logs_cmd(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) != 2:
        await message.reply("استفاده صحیح: /view_logs +989123456789")
        return
    phone = args[1]
    logs = get_logs_by_phone(phone)
    if not logs:
        await message.reply("هیچ لاگی یافت نشد.")
        return
    text = f"📜 لاگ‌های اکانت {phone}:\n\n"
    for log in logs[-10:]:
        text += f"{log.get('timestamp', '')} - {log.get('group', '')} - {log.get('status', '')}\n"
    await message.reply(text, reply_markup=accounts_status_menu())

# --- اجرای ربات ---
if __name__ == "__main__":
    print("[START] ربات MC در حال اجراست...")
    bot.run()
