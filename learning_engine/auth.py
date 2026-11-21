"""
Synapse Instance Authentication & Protection Module.
Provides lightweight, zero-dependency password & token authentication
to protect hosted Synapse web deployments from unauthorized access.
"""

import os
import time
import json
import hmac
import base64
import hashlib
import secrets
from typing import Optional, Dict, Tuple
from .database import get_db_connection
from .config_manager import get_settings

# Rate limiting for failed login attempts: {ip: (failed_count, first_fail_time)}
_FAILED_ATTEMPTS: Dict[str, Tuple[int, float]] = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_SECONDS = 60
_MAX_TRACKED_IPS = 10_000

# One-time, short-lived tickets for the terminal WebSocket, so the long-lived
# bearer token never appears in a URL (proxy/access logs, history).
_WS_TICKETS: Dict[str, float] = {}
WS_TICKET_TTL_SECONDS = 30
_MAX_WS_TICKETS = 1_000
_EPHEMERAL_SECRET: Optional[str] = None

def get_server_secret() -> str:
    """
    Returns a persistent server secret key for HMAC token signing.
    Stored in SQLite so tokens survive server restarts.
    """
    env_secret = os.environ.get("SYNAPSE_SECRET_KEY")
    if env_secret:
        return env_secret

    try:
        with get_db_connection() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = 'auth:server_secret'").fetchone()
            if row and row["value"]:
                return json.loads(row["value"])
            
            new_secret = secrets.token_hex(32)
            conn.execute(
                "INSERT INTO settings (key, value) VALUES ('auth:server_secret', ?)",
                (json.dumps(new_secret),)
            )
            return new_secret
    except Exception:
        # DB unavailable: use a random per-process secret. Tokens will not
        # survive a restart, but they can never be forged from a known key.
        global _EPHEMERAL_SECRET
        if _EPHEMERAL_SECRET is None:
            _EPHEMERAL_SECRET = secrets.token_hex(32)
        return _EPHEMERAL_SECRET

def get_configured_password() -> Optional[str]:
    """
    Returns the configured protection password if set in environment or settings.
    """
    env_pwd = os.environ.get("SYNAPSE_PASSWORD") or os.environ.get("SYNAPSE_AUTH_PASSWORD")
    if env_pwd and env_pwd.strip():
        return env_pwd.strip()

    try:
        st = get_settings()
        pwd = st.get("auth_password")
        if pwd and isinstance(pwd, str) and pwd.strip():
            return pwd.strip()
    except Exception:
        pass

    return None

def is_auth_enabled() -> bool:
    """Returns True if instance password protection is active."""
    return get_configured_password() is not None

def verify_password(password: str) -> bool:
    """Constant-time verification of candidate password."""
    configured = get_configured_password()
    if not configured:
        return True
    return hmac.compare_digest(password.strip(), configured)

def get_client_ip(request) -> str:
    """
    Returns the client IP used for rate limiting. Behind a reverse proxy, set
    SYNAPSE_TRUST_PROXY=1 to use the address the proxy appended to
    X-Forwarded-For (the right-most entry); otherwise the socket peer is used,
    since the header is client-controlled.
    """
    if os.environ.get("SYNAPSE_TRUST_PROXY", "").strip().lower() in ("1", "true", "yes"):
        xff = request.headers.get("x-forwarded-for", "")
        hops = [h.strip() for h in xff.split(",") if h.strip()]
        if hops:
            return hops[-1]
    return request.client.host if request.client else "unknown"

def _prune_failed_attempts(now: float) -> None:
    expired = [ip for ip, (_, first) in _FAILED_ATTEMPTS.items() if now - first >= LOCKOUT_WINDOW_SECONDS]
    for ip in expired:
        del _FAILED_ATTEMPTS[ip]

def is_rate_limited(client_ip: str) -> bool:
    """Checks if client IP is currently locked out due to excessive failed attempts."""
    now = time.time()
    count, first_time = _FAILED_ATTEMPTS.get(client_ip, (0, 0.0))
    if count >= MAX_FAILED_ATTEMPTS:
        if now - first_time < LOCKOUT_WINDOW_SECONDS:
            return True
        # Window expired, reset
        _FAILED_ATTEMPTS.pop(client_ip, None)
    return False

def record_failed_attempt(client_ip: str):
    """Records a failed login attempt for rate-limiting."""
    now = time.time()
    if len(_FAILED_ATTEMPTS) >= _MAX_TRACKED_IPS:
        _prune_failed_attempts(now)
    count, first_time = _FAILED_ATTEMPTS.get(client_ip, (0, 0.0))
    if now - first_time >= LOCKOUT_WINDOW_SECONDS:
        _FAILED_ATTEMPTS[client_ip] = (1, now)
    else:
        _FAILED_ATTEMPTS[client_ip] = (count + 1, first_time)

def reset_failed_attempts(client_ip: str):
    """Clears failed attempts counter upon successful login."""
    _FAILED_ATTEMPTS.pop(client_ip, None)

def generate_auth_token() -> str:
    """Generates a signed HMAC-SHA256 bearer token valid for 30 days."""
    secret = get_server_secret()
    payload = {
        "exp": int(time.time()) + (86400 * 30),  # 30 days
        "sub": "admin",
        "rnd": secrets.token_hex(8)
    }
    raw = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8").rstrip("=")
    sig = hmac.new(secret.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{raw}.{sig}"

def verify_auth_token(token: Optional[str]) -> bool:
    """
    Verifies token validity and signature.
    If auth is not enabled on this instance, returns True.
    """
    if not is_auth_enabled():
        return True

    if not token or "." not in token:
        return False

    try:
        raw, sig = token.split(".", 1)
        secret = get_server_secret()
        expected_sig = hmac.new(secret.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return False

        # Add padding back if stripped
        padding = "=" * ((4 - len(raw) % 4) % 4)
        payload = json.loads(base64.urlsafe_b64decode((raw + padding).encode("utf-8")).decode("utf-8"))
        if payload.get("exp", 0) < time.time():
            return False

        return True
    except Exception:
        return False

def issue_ws_ticket() -> str:
    """Issues a one-time ticket for opening the terminal WebSocket."""
    now = time.time()
    if len(_WS_TICKETS) >= _MAX_WS_TICKETS:
        for t, exp in list(_WS_TICKETS.items()):
            if exp < now:
                del _WS_TICKETS[t]
        if len(_WS_TICKETS) >= _MAX_WS_TICKETS:
            _WS_TICKETS.pop(next(iter(_WS_TICKETS)))
    ticket = secrets.token_urlsafe(32)
    _WS_TICKETS[ticket] = now + WS_TICKET_TTL_SECONDS
    return ticket

def consume_ws_ticket(ticket: Optional[str]) -> bool:
    """Validates and invalidates a WebSocket ticket. Tickets work exactly once."""
    if not ticket:
        return False
    exp = _WS_TICKETS.pop(ticket, None)
    return exp is not None and exp >= time.time()
