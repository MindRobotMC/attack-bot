import os
import json
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- مشخصات ربات ---
BOT_TOKEN = "8032544795:AAF6uK-SKxG5fzAWSUTRauqXor4YG7013Jk"
API_ID = 29698707
API_HASH = "22b012816bcf16d58d826e6e3606a273"
OWNER_ID = 7608419661

bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- مسیر فایل‌ها ---
HELPERS_FILE = "helpers.json"
STATS_FILE = "stats.json"
ATTACK_GROUPS_FILE = "attack_groups.json"
TARGET_IDS_FILE = "target_ids.json"  # فایل ذخیره آیدی‌هایی که ربات جمع کرده برای اتک

# --- وضعیت‌ها و داده‌های موقت ---
user_states = {}
temp_data = {}

# --- اطمینان از وجود فایل‌ها ---
def ensure_data_files():
    files_and_defaults = {
        HELPERS_FILE: [],
        STATS_FILE: {"daily": {}, "weekly": {}, "monthly": {}, "yearly": {}},
        ATTACK_GROUPS_FILE: [],
        TARGET_IDS_FILE: []  # لیست آیدی‌ها
    }
    for fname, default in files_and_defaults.items():
        if not os.path.exists(fname):
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=2, ensure_ascii=False)
            print(f"[INFO] فایل داده {fname} ساخته شد.")

ensure_data_files()

# --- توابع کمکی ---
def load_json(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] خطا در بارگذاری {filename}: {e}")
        return None

def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ERROR] خطا در ذخیره {filename}: {e}")

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
        [InlineKeyboardButton("📩 منوی اتک", callback_data="attack_menu")],
        [InlineKeyboardButton("📄 لیست اکانت‌ها", callback_data="list_1")],
        [InlineKeyboardButton("➕ اضافه کردن اکانت", callback_data="add")],
        [InlineKeyboardButton("📊 آمار ارسال‌ها", callback_data="stats")],
        [InlineKeyboardButton("📥 مدیریت لیست آیدی‌ها برای اتک", callback_data="target_ids_menu")],
        [InlineKeyboardButton("📘 راهنما", url="https://t.me/+wZVsaT38RHE5YjU8")],
        [InlineKeyboardButton("ℹ️ درباره MC", callback_data="about")],
        [InlineKeyboardButton("🧠 یوزرنیم اعضای چت فعال", callback_data="active_chat_custom")],
        [InlineKeyboardButton("💬 ارتباط با سازنده", url="https://t.me/mindrobotmc")],
    ])

# --- پیغام استارت ---
@bot.on_message(filters.private & filters.command("start"))
async def start_handler(client, message):
    if message.from_user.id != OWNER_ID:
        return
    await message.reply("به ربات MC خوش آمدید!", reply_markup=main_menu())

# --- هندلر کال‌بک‌ها ---
@bot.on_callback_query()
async def callback_handler(client, call):
    if call.from_user.id != OWNER_ID:
        await call.answer("شما اجازه دسترسی به این بخش را ندارید.", show_alert=True)
        return

    data = call.data

    # منوی اصلی
    if data == "main":
        await call.message.edit_text("🏠 منوی اصلی", reply_markup=main_menu())
        await call.answer()
        return

    # درباره
    if data == "about":
        about_text = (
            "🤖 ربات MC - مدیریت پیشرفته اکانت‌ها و اتک\n"
            "توسعه یافته توسط @mindrobotmc\n"
            "هدف: تسهیل مدیریت و ارسال اتک و تحلیل آمار."
        )
        await call.message.edit_text(about_text, reply_markup=main_menu())
        await call.answer()
        return

    # راهنما
    if data == "help":
        await call.message.edit_text(
            "📘 راهنما:\nبرای آموزش کامل به کانال زیر مراجعه کنید:\nhttps://t.me/+wZVsaT38RHE5YjU8",
            reply_markup=main_menu()
        )
        await call.answer()
        return

    # آمار ارسال‌ها
    if data == "stats":
        stats = load_json(STATS_FILE) or {}
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

    # لیست اکانت‌ها - صفحه‌بندی
    if data.startswith("list_") or data == "list":
        page = 1
        if "_" in data:
            try:
                page = int(data.split("_")[1])
            except:
                page = 1

        helpers = load_json(HELPERS_FILE) or []
        if not helpers:
            await call.message.edit_text("⚠️ هیچ اکانتی ثبت نشده.", reply_markup=main_menu())
            await call.answer()
            return

        per_page = 5
        total = len(helpers)
        total_pages = (total + per_page - 1) // per_page
        page = max(1, min(page, total_pages))
        page_items = helpers[(page - 1) * per_page: page * per_page]

        text = f"📄 <b>لیست اکانت‌ها (صفحه {page}/{total_pages}):</b>\n\n"
        buttons = []

        for i, acc in enumerate(page_items, start=(page - 1) * per_page + 1):
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
            nav_buttons.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"list_{page - 1}"))
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"list_{page + 1}"))
        if nav_buttons:
            buttons.append(nav_buttons)

        buttons.append([InlineKeyboardButton("🔄 بروزرسانی", callback_data=f"list_{page}")])
        buttons.append([InlineKeyboardButton("🏠 منوی اصلی", callback_data="main")])

        await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")
        await call.answer()
        return

    # حذف اکانت
    if data.startswith("del_"):
        phone = data.split("_", 1)[1]
        helpers = load_json(HELPERS_FILE) or []
        new_helpers = [acc for acc in helpers if acc.get("phone") != phone]
        save_json(HELPERS_FILE, new_helpers)
        await call.answer(f"اکانت {phone} حذف شد.")
        await call.message.edit_text("لیست اکانت‌ها بروزرسانی شد.", reply_markup=main_menu())
        return

    # اضافه کردن اکانت - شروع
    if data == "add":
        if user_states.get(call.from_user.id) == "awaiting_phone":
            await call.answer("⏳ لطفاً ابتدا شماره قبلی را وارد کنید.", show_alert=True)
            return
        user_states[call.from_user.id] = "awaiting_phone"
        await call.answer()
        await bot.send_message(call.from_user.id, "➕ لطفاً شماره اکانت را با +98 ارسال کنید.")
        return

    # منوی اتک
    if data == "attack_menu":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ گروه‌های اتک زده شده", callback_data="attack_done")],
            [InlineKeyboardButton("❌ گروه‌های اتک زده نشده", callback_data="attack_not_done")],
            [InlineKeyboardButton("➕ ثبت گروه جدید", callback_data="attack_add_group")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main")],
        ])
        await call.message.edit_text("📩 منوی اتک", reply_markup=keyboard)
        await call.answer()
        return

    # گروه‌های اتک زده شده
    if data == "attack_done":
        groups = load_json(ATTACK_GROUPS_FILE) or []
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

    # گروه‌های اتک زده نشده
    if data == "attack_not_done":
        groups = load_json(ATTACK_GROUPS_FILE) or []
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

    # ثبت گروه اتک جدید
    if data == "attack_add_group":
        if user_states.get(call.from_user.id) == "awaiting_attack_group":
            await call.answer("⏳ لطفاً ابتدا گروه قبلی را وارد کنید.", show_alert=True)
            return
        user_states[call.from_user.id] = "awaiting_attack_group"
        await call.answer()
        await bot.send_message(call.from_user.id, "➕ لطفاً آیدی گروه یا عنوان گروه جدید را ارسال کنید.")
        return

    # منوی مدیریت آیدی‌ها (برای اتک)
    if data == "target_ids_menu":
        target_ids = load_json(TARGET_IDS_FILE) or []
        text = f"📥 تعداد آیدی‌های ذخیره شده: {len(target_ids)}\n\n"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ اضافه کردن دستی آیدی", callback_data="add_target_id_manual")],
            [InlineKeyboardButton("🗑️ پاک کردن همه آیدی‌ها", callback_data="clear_target_ids")],
            [InlineKeyboardButton("🚀 ارسال اتک به آیدی‌ها", callback_data="send_attack_to_targets")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main")],
        ])
        await call.message.edit_text(text, reply_markup=keyboard)
        await call.answer()
        return

    # اضافه کردن دستی آیدی برای اتک
    if data == "add_target_id_manual":
        user_states[call.from_user.id] = "awaiting_target_id_manual"
        await call.message.edit_text("➕ لطفاً آیدی عددی (مثلا 123456789) را ارسال کنید. (برای افزودن چند آیدی آنها را با فاصله یا خط جدید جدا کنید.)")
        await call.answer()
        return

    # پاک کردن همه آیدی‌ها
    if data == "clear_target_ids":
        save_json(TARGET_IDS_FILE, [])
        await call.message.edit_text("✅ همه آیدی‌ها حذف شدند.", reply_markup=main_menu())
        await call.answer()
        return

    # ارسال اتک به لیست آیدی‌ها
    if data == "send_attack_to_targets":
        target_ids = load_json(TARGET_IDS_FILE) or []
        helpers = load_json(HELPERS_FILE) or []

        if not target_ids:
            await call.answer("❌ لیست آیدی‌ها خالی است.", show_alert=True)
            return

        if not helpers:
            await call.answer("❌ هیچ اکانت هلپری اضافه نشده.", show_alert=True)
            return

        # شروع اتک
        user_states[call.from_user.id] = "attacking_targets"
        temp_data[call.from_user.id] = {
            "targets": target_ids,
            "current_index": 0,
            "results": []
        }

        await call.message.edit_text(f"🚀 ارسال اتک به {len(target_ids)} آیدی شروع شد...\nلطفاً منتظر بمانید.")
        await call.answer()

        await attack_targets(client, call.from_user.id)
        return

    # پاسخ به بقیه موارد و کال‌بک‌های نامشخص
    await call.answer()

# --- ارسال اتک به آیدی‌ها ---
async def attack_targets(client: Client, user_id: int):
    state_data = temp_data.get(user_id)
    if not state_data:
        return

    targets = state_data.get("targets", [])
    idx = state_data.get("current_index", 0)
    results = state_data.get("results", [])

    helpers = load_json(HELPERS_FILE) or []
    if not helpers:
        # خطا: اکانت هلپر نیست
        await bot.send_message(user_id, "❌ هیچ اکانت هلپری یافت نشد. لطفاً ابتدا اکانت اضافه کنید.")
        user_states.pop(user_id, None)
        temp_data.pop(user_id, None)
        return

    # برای هر آیدی در لیست، پیام یا دستور ارسال می‌کنیم
    # استفاده چرخشی از اکانت‌ها برای اتک بهتر
    while idx < len(targets):
        target_id = targets[idx]
        helper_acc = helpers[idx % len(helpers)]
        phone = helper_acc.get("phone")
        session_name = phone.replace("+", "")
        message_text = "⚠️ این یک پیام اتک تستی است."

        try:
            # ایجاد کلاینت با سشن استرینگ ذخیره شده
            tg_client = Client(session_name, api_id=API_ID, api_hash=API_HASH)
            await tg_client.start()

            # ارسال پیام به آیدی هدف
            await tg_client.send_message(chat_id=int(target_id), text=message_text)

            await tg_client.stop()

            results.append({"target": target_id, "status": "موفق"})
            await bot.send_message(user_id, f"✅ ارسال موفق به آیدی {target_id}")
        except Exception as e:
            results.append({"target": target_id, "status": f"خطا: {e}"})
            await bot.send_message(user_id, f"❌ ارسال به آیدی {target_id} با خطا: {e}")

        idx += 1
        state_data["current_index"] = idx
        state_data["results"] = results

    # پایان اتک
    user_states.pop(user_id, None)
    temp_data.pop(user_id, None)
    await bot.send_message(user_id, "🚀 ارسال اتک به همه آیدی‌ها به پایان رسید.")

# --- هندلر پیام‌های متنی برای دریافت ورودی‌ها ---
@bot.on_message(filters.private & filters.text)
async def text_handler(client, message):
    if message.from_user.id != OWNER_ID:
        return

    state = user_states.get(message.from_user.id)

    # اضافه کردن اکانت - شماره تلفن
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

    # اضافه کردن اکانت - کد تایید
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

            helpers = load_json(HELPERS_FILE) or []
            acc_data = {
                "phone": phone,
                "session_string": session_string,
                "report": False,
                "report_end": None
            }
            if not any(acc.get("phone") == phone for acc in helpers):
                helpers.append(acc_data)
                save_json(HELPERS_FILE, helpers)

            await message.reply(
                f"✅ اکانت {phone} وارد شد و ذخیره شد.\n\nکد جلسه:\n<code>{session_string}</code>",
                parse_mode="HTML"
            )
        except Exception as e:
            error_msg = str(e)
            if "PHONE_CODE_EXPIRED" in error_msg:
                await message.reply("❌ کد تایید منقضی شده است. لطفاً دوباره شماره خود را ارسال کنید تا کد جدید دریافت کنید.")
                user_states[message.from_user.id] = "awaiting_phone"
                temp_data.pop(message.from_user.id, None)
            else:
                await message.reply(f"❌ ورود ناموفق:\n{error_msg}")
        finally:
            user_states.pop(message.from_user.id, None)
            temp_data.pop(message.from_user.id, None)
        return

    # ثبت گروه اتک
    if state == "awaiting_attack_group":
        group_text = message.text.strip()
        groups = load_json(ATTACK_GROUPS_FILE) or []
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

    # اضافه کردن دستی آیدی برای اتک
    if state == "awaiting_target_id_manual":
        raw_ids = message.text.strip()
        # تفکیک آیدی‌ها براساس فضا یا خط جدید
        ids = set()
        for line in raw_ids.splitlines():
            parts = line.split()
            for p in parts:
                if p.isdigit():
                    ids.add(p)

        if not ids:
            await message.reply("❌ هیچ آیدی عددی معتبری پیدا نشد.")
            return

        target_ids = load_json(TARGET_IDS_FILE) or []
        # اضافه کردن بدون تکراری
        for new_id in ids:
            if new_id not in target_ids:
                target_ids.append(new_id)
        save_json(TARGET_IDS_FILE, target_ids)

        await message.reply(f"✅ {len(ids)} آیدی جدید اضافه شد.\nمجموع آیدی‌ها: {len(target_ids)}")
        user_states.pop(message.from_user.id, None)
        return

# --- اجرای ربات ---
if __name__ == "__main__":
    print("[INFO] ربات در حال اجراست...")
    bot.run()
