# Synapse Deployment & Service Daemons

This directory contains operating system daemons and sandbox assets for running **Synapse** persistently across headless servers, workstations, and isolated execution containers.

---

## 📂 Directory Contents

| File | Target Environment | Purpose |
| :--- | :--- | :--- |
| **`learning-workbench.service`** | Linux (Systemd) | Headless background daemon with auto-restart on boot. |
| **`com.synapse.workbench.plist`** | macOS (Launchd) | User LaunchAgent daemon starting Synapse on macOS desktop login. |
| **`Dockerfile.sandbox`** | Docker / Podman | Hardened runtime container for isolating untrusted terminal lab commands. |

*(Note: For standard Docker container deployment, use the canonical `docker-compose.yml` located in the repository root).*

---

## 🐧 1. Linux Systemd Service (`learning-workbench.service`)

Runs the Synapse FastAPI service and static frontend continuously in the background on Linux servers (e.g. Ubuntu, Debian, Fedora, Arch).

### Installation
```bash
# 1. Edit the service file to set your actual workspace path and user:
# /etc/systemd/system/learning-workbench.service
sudo cp deploy/learning-workbench.service /etc/systemd/system/

# 2. Reload systemd and enable daemon on boot
sudo systemctl daemon-reload
sudo systemctl enable --now learning-workbench

# 3. Check status
sudo systemctl status learning-workbench
```

---

## 🍏 2. macOS Launchd Agent (`com.synapse.workbench.plist`)

Automatically launches the Synapse backend whenever you log into macOS.

### Installation
```bash
# 1. Copy LaunchAgent to your user Library
cp deploy/com.synapse.workbench.plist ~/Library/LaunchAgents/

# 2. Load and start the agent
launchctl load ~/Library/LaunchAgents/com.synapse.workbench.plist

# 3. Verify it is running
launchctl list | grep synapse
```

To stop:
```bash
launchctl unload ~/Library/LaunchAgents/com.synapse.workbench.plist
```

---

## 🛡️ 3. Execution Sandbox (`Dockerfile.sandbox`)

Builds an isolated container sandbox for safely running untrusted lab commands or experimental CLI scripts with restricted cgroups and non-root UID.

### Building & Running Sandbox
```bash
docker build -t synapse-sandbox -f deploy/Dockerfile.sandbox deploy/
docker run --rm -it \
  --memory="2g" \
  --cpus="2.0" \
  --pids-limit=100 \
  synapse-sandbox
```
