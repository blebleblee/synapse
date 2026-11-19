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
2. **API Gating:** FastAPI HTTP middleware intercepts all `/api/*` endpoints (except `/api/auth/*` and `/api/health`), returning `401 Unauthorized` unless a valid token is provided in `Authorization: Bearer <token>` or `X-Synapse-Token`.
3. **PTY Terminal Handshake Verification:** The `/ws/terminal` WebSocket checks `?token=<token>` before accepting the connection, rejecting unauthenticated shell requests with WebSocket code `1008`.
4. **Brute-Force Protection:** Automatically locks out client IPs after 5 failed password attempts within a 60-second window.
5. **Open Local Default:** When `SYNAPSE_PASSWORD` is omitted, Synapse runs without authentication prompts, preserving instant offline startup for local desktop use.

