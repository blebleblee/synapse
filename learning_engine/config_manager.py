import json
from pathlib import Path
from typing import Dict, Any
from .database import get_connection

def get_settings() -> Dict[str, Any]:
    """Load settings from SQLite database."""
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {row["key"]: json.loads(row["value"]) for row in rows}

def save_settings(settings: Dict[str, Any]):
    """Save settings to SQLite database."""
    conn = get_connection()
    with conn:
        for key, value in settings.items():
            conn.execute("""
                INSERT INTO settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """, (key, json.dumps(value)))
    conn.close()
