import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "notes_tags.db"

DDL = f"""
CREATE TABLE IF NOT EXISTS entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT UNIQUE, mood INTEGER, note TEXT
);
"""

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_conn() as conn:
        conn.execute(DDL)
        conn.commit()

