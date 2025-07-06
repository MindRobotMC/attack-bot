# modules/analysis.py

import os
import re
import json
from datetime import datetime
from pyrogram import Client
from pyrogram.types import Message

DATA_DIR = "data"
ANALYSIS_DIR = os.path.join(DATA_DIR, "analysis_results")

if not os.path.exists(ANALYSIS_DIR):
    os.makedirs(ANALYSIS_DIR)

def extract_usernames_from_text(text: str) -> list:
    """
    استخراج یوزرنیم‌ها از متن پیام
    """
    pattern = r"@[\w\d_]{5,32}"
    return re.findall(pattern, text)

async def analyze_group(client: Client, group_link: str, limit: int = 100):
    """
    آنالیز پیام‌های آخر گروه برای استخراج یوزرنیم‌ها

    پارامترها:
    - client: کلاینت Pyrogram (اکانت هلپر)
    - group_link: لینک یا آیدی گروه
    - limit: تعداد پیام‌هایی که بررسی می‌شود

    خروجی:
    - لیست یوزرنیم‌ها
    """
    usernames = set()
    try:
        async for msg in client.iter_history(group_link, limit=limit):
            if isinstance(msg, Message) and msg.text:
                extracted = extract_usernames_from_text(msg.text)
                usernames.update(extracted)
    except Exception as e:
        print(f"[ERROR] آنالیز {group_link} با خطا مواجه شد: {e}")
        return []

    return sorted(list(usernames))

def save_analysis_result(group_link: str, usernames: list):
    """
    ذخیره نتیجه آنالیز در فایل
    """
    safe_name = group_link.replace("https://t.me/", "").replace("@", "").replace("/", "_")
    filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    path = os.path.join(ANALYSIS_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        for u in usernames:
            f.write(u + "\n")

    return path
