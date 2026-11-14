import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from .security import WORKSPACE_ROOT

DB_PATH = WORKSPACE_ROOT / "data" / "synapse.db"

def get_connection() -> sqlite3.Connection:
    CONFIG_DIR = DB_PATH.parent
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

@contextmanager
def get_db_connection():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mastery (
                path TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                completed_lessons TEXT, -- JSON list
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

init_db()
