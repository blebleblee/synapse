# Configuration, Model Pinning & Security Guide

Synapse is designed from the ground up for strict data sovereignty, credential isolation, and host machine safety.

---

## 1. Secure Credential Storage (Outside Codebase)

Synapse strictly separates public source code from private credentials. Cloud API keys are stored outside the repository tree:

* **Primary Path:** `~/.config/synapse/env`
* **File Permissions:** `chmod 600 ~/.config/synapse/env` (read/write only by your user)

### Format
```bash
ANTHROPIC_API_KEY=sk-...
ANTHROPIC_BASE_URL=https://api.anthropic.com
ANTHROPIC_MODEL=claude-opus-5-5
GEMINI_API_KEY=AIza...
```

Keys entered in **Settings ⚙** are used when no environment variable is set. Requests to Claude identify themselves as `Synapse-Workbench/<version>`; if your gateway requires a specific User-Agent, set `SYNAPSE_ANTHROPIC_USER_AGENT`. Current Claude models reject sampling parameters, so Synapse never sends `temperature`.

**Search index:** full-text search uses a SQLite FTS5 index stored next to the database (`data/search_index.db`, or `SYNAPSE_SEARCH_INDEX_PATH`). It is built in the background at startup (a few seconds) and updates changed files automatically before each search. It matches word prefixes, so `sql` finds `SQLite`. Delete the file to force a rebuild, or set `SYNAPSE_SEARCH_INDEX=0` to search by scanning files instead.

The Python learning engine automatically loads credentials from `~/.config/synapse/env` at startup. Because this file lives in your home directory, it is **physically impossible for git to stage, diff, or commit your private keys**.

---

## 2. Multi-Node Cluster Model Pinning

When operating a distributed Ollama cluster across local LAN machines (e.g. Mac Studio, RTX workstations, local laptops), you can bind specific models to specific hosts to prevent thrashing and model swapping.

### Configuration File: `.synapse_node_pins.json`
```json
{
  "192.168.1.100:11434": "qwen2.5-coder:32b",
  "127.0.0.1:11434": "qwen2.5-coder:7b"
}
```

### Management via Settings UI
Open **Settings ⚙ → Inference Cluster** to:
1. Probe live LAN cluster nodes and inspect GPU memory allocation.
2. Select and pin specific models to specific nodes via dropdown.
3. Reset all pins back to auto-discovery mode from **Settings ⚙ → System & Maintenance**.

---

## 3. Host Safety Interceptor (Interactive Guard)

When running the terminal in host mode (`env=host`), commands execute on your local machine. To prevent disastrous typos during operational labs, Synapse incorporates an in-stream safety interceptor in `app/backend/main.py`.

### Blocked Destructive Patterns:
- **Root / Home Deletions:** `rm -rf /`, `rm -rf ~`, `rm -rf *`
- **Block Device Overwrites:** `mkfs.*`, `dd if=... of=/dev/...`, `> /dev/sd*`
- **Resource Exhaustion:** `:(){ :|:& };:` (fork bombs)
- **Destructive Git Operations:** `git reset --hard`, `git clean -fd`
- **System Shutdowns:** `shutdown`, `reboot`, `halt`

If a blocked command is entered, execution is immediately paused, and the terminal prompts:
```text
DANGER [SYNAPSE HOST SAFETY GUARD]
Blocked destructive command on host OS: rm -rf /
To run anyway, type CONFIRM and press Enter. To cancel, press Enter or Ctrl+C:
```

---

## 4. Root-Anchored `.gitignore` Isolation

To ensure local SQLite caches and temporary files never pollute source control, `.gitignore` anchors runtime paths to the root:

```gitignore
# Runtime Database & State
/data/
/exports/
*.db
*.db-journal
*.db-wal
.synapse_cluster*.json
```

By anchoring `/data/` to root, legitimate curriculum courses under `topics/computing/data/` (such as `big_data`, `postgresql`, `database_internals`) remain fully tracked by Git without collision.

---

## 5. Hosted Instance Protection & Password Authentication

When deploying Synapse on a VPS, server, or cloud container accessible over a network, you can protect the entire workbench with instance-level password authentication:

### Enabling Protection
Set `SYNAPSE_PASSWORD` in your environment or in `~/.config/synapse/env`:

```bash
# Set instance protection password
export SYNAPSE_PASSWORD="YourStrongPasswordHere"

# Launch Synapse
synapse serve --host 0.0.0.0 --port 8000
```

### Security Architecture:
1. **Zero-Dependency Token Signing:** Generates HMAC-SHA256 bearer tokens signed with a persistent SQLite-backed server secret key (`auth:server_secret`), ensuring sessions persist across server restarts for 30 days.
2. **API Gating:** FastAPI HTTP middleware intercepts all `/api/*` endpoints (except `/api/auth/status`, `/api/auth/login` and `/api/health`), returning `401 Unauthorized` unless a valid token is provided in `Authorization: Bearer <token>` or `X-Synapse-Token`. Tokens in query strings (`?token=`) are not accepted, because URLs end up in access logs, proxy logs and browser history.
3. **PTY Terminal Handshake Verification:** Browsers cannot send headers on WebSockets, so the client first calls `POST /api/auth/ws-ticket` (with its bearer token) and connects to `/ws/terminal?ticket=<ticket>`. Tickets are random, single-use and expire after 30 seconds. Missing, reused or expired tickets are rejected with WebSocket code `1008`.
4. **Origin Check:** `/ws/terminal` rejects connections whose `Origin` is not the backend itself, the Vite dev server (`localhost:5173`) or an entry in `SYNAPSE_ALLOWED_ORIGINS`. This stops other websites from opening a shell (cross-site WebSocket hijacking). CORS uses the same allow-list.
5. **Cross-Site Requests:** HTTP requests other than `GET`, `HEAD` and `OPTIONS` that carry a foreign `Origin` header (including `null`) get `403`. Websites can send such requests without a CORS preflight (for example a `no-cors` POST), so CORS alone does not stop them. Clients that send no `Origin` (CLI, scripts) are unaffected. `/api/system/shutdown` additionally accepts only loopback clients.
6. **Brute-Force Protection:** Locks out a client IP after 5 failed password attempts within a 60-second window. Behind a reverse proxy, set `SYNAPSE_TRUST_PROXY=1` so the client address is taken from the entry the proxy appends to `X-Forwarded-For`; otherwise every user shares the proxy's address.
7. **Secrets Are Never Returned:** `GET /api/settings` omits internal `auth:*` keys (including the token signing secret) and returns API keys and passwords as a placeholder. Saving the placeholder back keeps the stored value; `auth:*` keys cannot be written through the API.
8. **Localhost-Only Default:** When `SYNAPSE_PASSWORD` is omitted, Synapse runs without a login prompt but only answers requests addressed to `localhost`, `127.0.0.1` or `[::1]` (HTTP `403` otherwise, WebSocket code `1008`). This blocks access from other machines and DNS-rebinding attacks from websites. To serve other hosts, set `SYNAPSE_PASSWORD`; to deliberately allow a host without a password, list it in `SYNAPSE_ALLOWED_HOSTS` (comma-separated).

> **Note on precedence:** values in `~/.config/synapse/env` override variables already set in your shell. If that file defines `SYNAPSE_PASSWORD`, running `SYNAPSE_PASSWORD=other synapse serve` still uses the file's password.

