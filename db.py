import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger("groww_pulse.db")

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "idempotency.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                iso_week TEXT PRIMARY KEY,
                run_time TEXT,
                status TEXT
            )
        """)

def check_if_week_processed(iso_week: str) -> bool:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT status FROM runs WHERE iso_week = ?", (iso_week,))
        row = cursor.fetchone()
        if row and row[0] == 'SUCCESS':
            return True
    return False

def mark_week_processed(iso_week: str):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO runs (iso_week, run_time, status) VALUES (?, ?, ?)",
            (iso_week, datetime.now().isoformat(), 'SUCCESS')
        )
        logger.info(f"Marked week {iso_week} as SUCCESS in database.")
