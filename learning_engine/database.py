import sqlite3
import time
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from .security import WORKSPACE_ROOT

DB_PATH = WORKSPACE_ROOT / "data" / "synapse.db"

def get_connection() -> sqlite3.Connection:
    CONFIG_DIR = DB_PATH.parent
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    # Higher timeout for concurrency
    conn = sqlite3.connect(DB_PATH, timeout=20.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn

@contextmanager
def get_db_connection(retries: int = 5):
    conn = get_connection()
    last_err = None
    for attempt in range(retries):
        try:
            yield conn
            conn.commit()
            return
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                conn.rollback()
                last_err = e
                time.sleep((2 ** attempt) * 0.1)  # Exponential backoff 0.1, 0.2, 0.4...
                continue
            conn.rollback()
            raise e
        except Exception:
            conn.rollback()
            raise
        finally:
            # We don't close here because we are in the retry loop.
            pass
    conn.close()
    raise last_err or RuntimeError("Database locked after multiple retries")

def checkpoint_db(truncate: bool = False):
    """Force WAL checkpoint to prevent indefinite log growth."""
    try:
        conn = get_connection()
        mode = "TRUNCATE" if truncate else "PASSIVE"
        conn.execute(f"PRAGMA wal_checkpoint({mode});")
        conn.close()
    except Exception:
        pass

def vacuum_db():
    try:
        conn = get_connection()
        conn.execute("VACUUM;")
        conn.execute("PRAGMA integrity_check;")
        conn.close()
    except Exception:
        pass

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
