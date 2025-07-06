import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from modules.database import get_connection  # تابع اتصال به دیتابیس

def initialize_logs_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            phone TEXT NOT NULL,
            username TEXT,
            action TEXT NOT NULL,
            status TEXT NOT NULL,
            details TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_log(phone: str, username: Optional[str], action: str, status: str, details: str = ""):
    """
    افزودن یک رکورد لاگ به دیتابیس
    """
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO logs (timestamp, phone, username, action, status, details)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (timestamp, phone, username or "", action, status, details))
    conn.commit()
    conn.close()

def get_all_operations() -> List[Dict]:
    """
    واکشی تمام لاگ‌ها از دیتابیس
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]

def get_operations_by_account(phone: str) -> List[Dict]:
    """
    واکشی لاگ‌های اختصاصی یک اکانت (بر اساس شماره تلفن)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs WHERE phone = ? ORDER BY timestamp DESC", (phone,))
    rows = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]

# هنگام بارگذاری ماژول، جدول لاگ‌ها را ایجاد کن
initialize_logs_table()
