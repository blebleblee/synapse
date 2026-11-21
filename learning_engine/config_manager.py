import json
import re
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import closing
from .database import get_connection

MAX_SETTINGS_COUNT = 1000
MAX_VALUE_SIZE_BYTES = 1024 * 1024
MAX_KEY_LENGTH = 255
_KEY_VALIDATOR = re.compile(r'^[a-zA-Z0-9_\-\.\:]+$')

class ConfigError(Exception):
    pass

# Placeholder returned to API clients instead of secret values. When a client
# saves settings with this value unchanged, the stored secret is kept.
REDACTED_PLACEHOLDER = "__synapse_redacted__"

# Keys never exposed to or writable by API clients (server-internal state).
_INTERNAL_KEY_PREFIXES = ("auth:",)
_SECRET_KEY_RE = re.compile(r"(api_?key|password|secret|token)$", re.IGNORECASE)

def _is_internal_key(key: str) -> bool:
    return key.startswith(_INTERNAL_KEY_PREFIXES)

def _is_secret_key(key: str) -> bool:
    return bool(_SECRET_KEY_RE.search(key))

def redact_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Settings safe to return over the API: internal keys dropped, secrets masked."""
    out = {}
    for key, value in settings.items():
        if _is_internal_key(key):
            continue
        if _is_secret_key(key) and isinstance(value, str) and value:
            out[key] = REDACTED_PLACEHOLDER
        else:
            out[key] = value
    return out

def filter_client_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Settings an API client may write: internal keys rejected, and secrets left
    at the redaction placeholder are dropped so the stored value is preserved.
    """
    if not isinstance(settings, dict):
        raise ConfigError("Settings must be a dictionary")
    out = {}
    for key, value in settings.items():
        if not isinstance(key, str) or _is_internal_key(key):
            raise ConfigError(f"Setting key is reserved: {key}")
        if value == REDACTED_PLACEHOLDER:
            continue
        out[key] = value
    return out

def _validate_key(key: str) -> None:
    if not isinstance(key, str):
        raise ConfigError("Setting key must be string")
    if len(key) > MAX_KEY_LENGTH:
        raise ConfigError("Setting key exceeds maximum length")
    if not _KEY_VALIDATOR.match(key):
        raise ConfigError(f"Setting key contains invalid characters: {key}")

def _validate_value(value: Any) -> str:
    try:
        serialized = json.dumps(value)
    except (TypeError, ValueError) as e:
        raise ConfigError(f"Setting value is not JSON-serializable: {e}")
    if len(serialized.encode('utf-8')) > MAX_VALUE_SIZE_BYTES:
        raise ConfigError("Setting value exceeds size limit")
    return serialized

def get_settings() -> Dict[str, Any]:
    """Load settings from SQLite database safely."""
    try:
        with closing(get_connection()) as conn:
            with conn:
                rows = conn.execute("SELECT key, value FROM settings").fetchall()
            
            settings = {}
            for row in rows:
                try:
                    settings[row["key"]] = json.loads(row["value"])
                except json.JSONDecodeError as e:
                    print(f"Warning: Corrupted setting '{row['key']}' skipped: {e}")
            return settings
    except Exception as e:
        print(f"ConfigError: Failed to load settings: {e}")
        return {}

def save_settings(settings: Dict[str, Any]) -> None:
    """Save settings to SQLite database transactionally."""
    if not isinstance(settings, dict):
        raise ConfigError("Settings must be a dictionary")
    if len(settings) > MAX_SETTINGS_COUNT:
        raise ConfigError("Too many settings")

    validated_items = []
    for key, value in settings.items():
        _validate_key(key)
        serialized_value = _validate_value(value)
        validated_items.append((key, serialized_value))

    try:
        with closing(get_connection()) as conn:
            with conn:
                for key, serialized_value in validated_items:
                    conn.execute("""
                        INSERT INTO settings (key, value)
                        VALUES (?, ?)
                        ON CONFLICT(key) DO UPDATE SET value=excluded.value
                    """, (key, serialized_value))
    except Exception as e:
        raise ConfigError(f"Failed to save settings: {e}")
