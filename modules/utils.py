# modules/utils.py

import re
from datetime import datetime, timedelta

def clean_phone_number(phone: str) -> str:
    """
    پاک‌سازی شماره تلفن و تبدیل به فرمت +98xxxxxxxxxx
    """
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("09"):
        phone = "+98" + phone[1:]
    elif phone.startswith("9") and len(phone) == 10:
        phone = "+98" + phone
    elif phone.startswith("989"):
        phone = "+" + phone
    return phone

def format_datetime(dt_str: str, format_out: str = "%Y-%m-%d %H:%M") -> str:
    """
    تبدیل رشته datetime به فرمت مشخص‌شده
    """
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime(format_out)
    except Exception:
        return dt_str

def estimate_report_end(duration_minutes: int) -> str:
    """
    برآورد زمان پایان ریپورت
    """
    end_time = datetime.now() + timedelta(minutes=duration_minutes)
    return end_time.isoformat()

def time_diff_from_now(target_time_str: str) -> str:
    """
    محاسبه زمان باقی‌مانده تا یک تاریخ
    """
    try:
        target_time = datetime.fromisoformat(target_time_str)
        now = datetime.now()
        delta = target_time - now
        minutes = int(delta.total_seconds() / 60)
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours} ساعت و {minutes} دقیقه"
    except Exception:
        return "نامشخص"

def is_valid_username(username: str) -> bool:
    """
    بررسی معتبر بودن یوزرنیم تلگرام
    """
    return re.fullmatch(r"@[a-zA-Z0-9_]{5,32}", username) is not None
