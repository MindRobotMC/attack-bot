# modules/accounts.py

import sqlite3
from typing import List, Optional, Dict

DB_FILE = "database.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS helpers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL,
            username TEXT,
            name TEXT,
            report INTEGER DEFAULT 0,
            deleted INTEGER DEFAULT 0,
            recovering INTEGER DEFAULT 0,
            report_duration TEXT,
            report_end_time TEXT,
            ready_time TEXT
        )
    """)
    conn.commit()
    conn.close()

# ثبت اکانت جدید
def register_account(phone: str, username: str, name: Optional[str] = None) -> (bool, str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO helpers (phone, username, name) VALUES (?, ?, ?)", (phone, username, name or ""))
        conn.commit()
        return True, "اکانت با موفقیت ثبت شد."
    except sqlite3.IntegrityError:
        return False, "اکانت با این شماره قبلاً ثبت شده است."
    finally:
        conn.close()

# گرفتن لیست اکانت‌ها با فیلتر وضعیت اختیاری
def list_accounts(status_filter: Optional[Dict[str, int]] = None) -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM helpers"
    params = []
    if status_filter:
        filters = []
        for k, v in status_filter.items():
            filters.append(f"{k} = ?")
            params.append(1 if v else 0)
        query += " WHERE " + " AND ".join(filters)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# به‌روزرسانی اطلاعات اکانت بر اساس شماره
def update_account(phone: str, data: dict) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    fields = []
    params = []
    for key, value in data.items():
        fields.append(f"{key} = ?")
        # چون فیلدهای بولی به صورت INTEGER ذخیره میشن، مقدار درست فرستاده شود
        if isinstance(value, bool):
            value = 1 if value else 0
        params.append(value)
    params.append(phone)
    query = f"UPDATE helpers SET {', '.join(fields)} WHERE phone = ?"
    cursor.execute(query, params)
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

# حذف اکانت بر اساس شماره
def delete_account(phone: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM helpers WHERE phone = ?", (phone,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

# گرفتن اطلاعات یک اکانت بر اساس شماره
def get_account(phone: str) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM helpers WHERE phone = ?", (phone,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

# اطمینان از وجود جدول هنگام ایمپورت این ماژول
initialize_db()
