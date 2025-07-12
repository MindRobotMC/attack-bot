import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional

# اطلاعات اتصال به PostgreSQL
DB_HOST = "dpg-d1p7bu49c44c738b2rm0-a.frankfurt-postgres.render.com"
DB_PORT = 5432
DB_NAME = "mcstore_db"
DB_USER = "mcstore_db_user"
DB_PASSWORD = "O90BhnUEvCw7XOQifMZm8PeJbD65drYy"

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=RealDictCursor
    )

# ------------------- جدول اکانت‌ها -------------------
def initialize_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            username TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL,
            report_duration INTEGER,
            report_end_time TEXT,
            ready_time TEXT
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()
    initialize_group_table()

def get_accounts_by_status(status: str) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE status = %s", (status,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def get_all_accounts() -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def add_account(account_data: Dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO accounts (name, username, phone, status, report_duration, report_end_time, ready_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (phone) DO NOTHING
    """, (
        account_data.get("name", "بدون‌نام"),
        account_data.get("username", "unknown"),
        account_data["phone"],
        account_data.get("status", "healthy"),
        account_data.get("report_duration"),
        account_data.get("report_end_time"),
        account_data.get("ready_time")
    ))
    conn.commit()
    cursor.close()
    conn.close()

def delete_account(phone: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM accounts WHERE phone = %s", (phone,))
    conn.commit()
    cursor.close()
    conn.close()

def update_account_status(phone: str, status: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE accounts SET status = %s WHERE phone = %s", (status, phone))
    conn.commit()
    cursor.close()
    conn.close()

def update_ready_time(phone: str, ready_time: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE accounts SET ready_time = %s WHERE phone = %s", (ready_time, phone))
    conn.commit()
    cursor.close()
    conn.close()

def update_report_info(phone: str, duration: Optional[int], end_time: Optional[str]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE accounts 
        SET report_duration = %s, report_end_time = %s
        WHERE phone = %s
    """, (duration, end_time, phone))
    conn.commit()
    cursor.close()
    conn.close()

# ------------------- جدول گروه‌ها -------------------
def initialize_group_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL UNIQUE
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def add_group(title: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO groups (title) VALUES (%s) ON CONFLICT DO NOTHING", (title,))
    conn.commit()
    cursor.close()
    conn.close()

def delete_group(title: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM groups WHERE title = %s", (title,))
    conn.commit()
    cursor.close()
    conn.close()

def get_all_groups() -> List[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM groups")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row["title"] for row in rows]
