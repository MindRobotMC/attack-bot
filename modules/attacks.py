import os
import asyncio
from datetime import datetime
from pyrogram.errors import FloodWait, RPCError
from modules.logs import add_log
from modules.database import get_connection  # فرض بر این است که در database.py تابع اتصال به DB هست

DATA_DIR = "data"
ATTACKS_LOG_DIR = os.path.join(DATA_DIR, "attacks_logs")

if not os.path.exists(ATTACKS_LOG_DIR):
    os.makedirs(ATTACKS_LOG_DIR)


def log_attack(phone: str, group_link: str, status: str, error: str = None):
    """ذخیره گزارش ارسال اتک به صورت فایل JSON و لاگ کلی"""
    import json

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "phone": phone,
        "group": group_link,
        "status": status,
        "error": error
    }
    log_file = os.path.join(ATTACKS_LOG_DIR, f"{phone}.json")
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except:
            logs = []
    logs.append(log_entry)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    # ذخیره در لاگ کلی
    add_log(phone, group_link, status, error)


async def send_attack(client, group_link: str, message, media_type: str = "text", media_path: str = None) -> bool:
    """
    ارسال پیام به گروه یا کانال با client مشخص.
    """
    try:
        if media_type == "text":
            await client.send_message(group_link, message)
        elif media_type == "photo":
            await client.send_photo(group_link, media_path, caption=message)
        elif media_type == "video":
            await client.send_video(group_link, media_path, caption=message)
        elif media_type == "sticker":
            await client.send_sticker(group_link, media_path)
        elif media_type == "document":
            await client.send_document(group_link, media_path, caption=message)
        else:
            await client.send_message(group_link, message)

        log_attack(client.session_name, group_link, "موفق")
        return True

    except FloodWait as e:
        wait_time = e.x
        log_attack(client.session_name, group_link, "FloodWait", error=f"باید {wait_time} ثانیه صبر کند")
        print(f"[FloodWait] باید {wait_time} ثانیه صبر کنیم برای اکانت {client.session_name}")
        await asyncio.sleep(wait_time + 5)
        return False

    except RPCError as e:
        log_attack(client.session_name, group_link, "RPCError", error=str(e))
        print(f"[RPCError] خطا برای {client.session_name}: {e}")
        return False

    except Exception as e:
        log_attack(client.session_name, group_link, "خطا", error=str(e))
        print(f"[ERROR] ارسال پیام شکست خورد برای {client.session_name}: {e}")
        return False


# دیتابیس: جدول groups
# فرض: جدول groups (id INTEGER PRIMARY KEY AUTOINCREMENT, link TEXT UNIQUE, attacked INTEGER DEFAULT 0)

def add_attack_group(group_link: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO groups (link, attacked) VALUES (?, 0)", (group_link,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_all_attack_groups(include_attacked: bool = False) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    if include_attacked:
        cursor.execute("SELECT link, attacked FROM groups")
    else:
        cursor.execute("SELECT link, attacked FROM groups WHERE attacked = 0")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


def set_group_attacked(group_link: str, attacked: bool = True):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE groups SET attacked = ? WHERE link = ?", (1 if attacked else 0, group_link))
    conn.commit()
    conn.close()


async def mass_attack(helper_clients: dict, message, media_type="text", media_path=None):
    """
    ارسال همگانی پیام به همه گروه‌ها با همه اکانت‌ها.

    - helper_clients: دیکشنری {phone: pyrogram.Client}
    - message: متن یا کپشن پیام
    - media_type: نوع پیام
    - media_path: مسیر فایل رسانه (اگر هست)

    خروجی: دیکشنری {phone: {group_link: True/False}}
    """
    groups = get_all_attack_groups(include_attacked=False)
    if not groups:
        print("[ERROR] گروهی برای ارسال وجود ندارد.")
        return {}

    results = {}

    for phone, client in helper_clients.items():
        results[phone] = {}
        for group_link in groups:
            success = await send_attack(client, group_link, message, media_type, media_path)
            results[phone][group_link] = success
            if success:
                set_group_attacked(group_link, True)
            # جلوگیری از ارسال سریع بیش از حد
            await asyncio.sleep(2)

    return results
