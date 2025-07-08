# database.py
import sqlite3
from typing import List, Dict
from datetime import datetime

DB_NAME = "accounts.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT NOT NULL,
            phone TEXT NOT NULL,
            status TEXT NOT NULL,
            report_duration INTEGER,
            report_end_time TEXT,
            ready_time TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_accounts_by_status(status: str) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE status = ?", (status,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
