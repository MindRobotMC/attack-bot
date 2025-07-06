import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict
from modules.database import get_connection  # تابع اتصال به دیتابیس

def initialize_stats_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value INTEGER DEFAULT 0,
            last_updated TEXT
        )
    """)
    conn.commit()
    conn.close()

def update_stat(key: str, increment: int = 1):
    """
    افزایش مقدار آماری مشخص به اندازه increment (پیش‌فرض 1)
    اگر کلید وجود نداشت، ایجاد می‌شود.
    """
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    cursor.execute("SELECT value FROM stats WHERE key = ?", (key,))
    row = cursor.fetchone()
    if row:
        new_value = row[0] + increment
        cursor.execute("UPDATE stats SET value = ?, last_updated = ? WHERE key = ?", (new_value, now, key))
    else:
        cursor.execute("INSERT INTO stats (key, value, last_updated) VALUES (?, ?, ?)", (key, increment, now))
    conn.commit()
    conn.close()

def get_stat(key: str) -> int:
    """
    دریافت مقدار آماری با کلید مشخص
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM stats WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return 0

def get_stats() -> Dict[str, int]:
    """
    واکشی تمام آمارهای ذخیره شده به صورت دیکشنری {key: value}
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM stats")
    rows = cursor.fetchall()
    conn.close()
    return {key: value for key, value in rows}

def reset_stats():
    """
    ریست تمام آمارها به صفر (در صورت نیاز)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE stats SET value = 0")
    conn.commit()
    conn.close()

# جدول آمار هنگام لود ماژول ساخته شود
initialize_stats_table()
