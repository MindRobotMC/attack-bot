import sqlite3

DB_FILE = "database.db"

def get_connection():
    """
    ایجاد اتصال به دیتابیس SQLite و تنظیم row_factory برای دسترسی آسان به داده‌ها
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    """
    ایجاد جدول helpers در دیتابیس اگر وجود نداشته باشد
    """
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
