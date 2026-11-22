# Terminal Sandboxes: Rancher Desktop, Docker, k3s & Host Safety

Synapse provides an integrated WebSocket PTY terminal designed for executing hands-on operational labs. To prevent accidents on your host machine while learning system administration, networking, or kernel engineering, Synapse supports multiple sandbox tiers across **macOS**, **Windows**, and **Linux**.

---

## 1. Sandbox Tier Matrix

| Sandbox Environment | Isolation Level | Setup Requirement | Supported OS | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **Local Host Shell** | Native Host OS | None (built-in) | macOS, Windows, Linux | Fast CLI navigation, local git, Python |
| **Docker (Ubuntu 24.04)** | Container Sandbox | Docker / Rancher Desktop | macOS, Windows, Linux | Linux labs, package installations, root experiments |
| **Kubernetes (k3s / Netshoot)** | Ephemeral Pod | k3s / Minikube / Rancher | macOS, Windows, Linux | Cloud-native, network tracing, eBPF |

If the Docker daemon or the Kubernetes cluster is not reachable, choosing that profile shows the setup steps and opens **no shell**. Synapse never falls back to a host shell behind a "Sandbox" label; choose **Host Shell (Local)** to work on your own machine on purpose.

---

## 2. Setting Up Rancher Desktop (Recommended for Mac & Windows)

Rancher Desktop provides open-source container management and a local Kubernetes cluster without proprietary licensing restrictions.

### Installation
1. Download from [rancherdesktop.io](https://rancherdesktop.io/).
2. In **Preferences → Container Engine**, select **`dockerd (moby)`**.
3. In **Preferences → Kubernetes**, check **Enable Kubernetes** (k3s).
4. Verify from your terminal:
   ```bash
   docker info
   kubectl cluster-info
   ```

When Rancher Desktop is running, Synapse's terminal drawer will automatically detect the Docker socket and allow selecting **Docker (Ubuntu 24.04)** or **Kubernetes (Netshoot)** from the environment dropdown.

---

## 3. Host Shell Safety Guard (Interactive Command Interceptor)

When executing in **Host Machine** mode (`env=host`), commands execute directly on your local system. To prevent catastrophic accidents during operational labs, Synapse incorporates an **in-stream safety verification interceptor** in the terminal bridge.

### How It Works
1. As you type commands, the terminal buffer tracks keystrokes.
2. When you press **Enter**, the command is inspected against destructive patterns:
   - Recursive root or home deletions (`rm -rf /`, `rm -rf ~`, `rm -rf *`)
   - Raw disk formatting or block device writes (`mkfs`, `dd ... of=/dev/...`, `> /dev/...`)
   - Fork bombs (`:(){ :|:& };:`)
   - Hard git resets and cleanups (`git reset --hard`, `git clean -fd`)
   - System shutdowns (`shutdown`, `reboot`, `halt`)
3. If a destructive pattern matches, **the command is blocked from reaching the host OS**.
4. The terminal displays a high-visibility warning:
   ```text
    DANGER  [SYNAPSE HOST SAFETY GUARD]
   Blocked destructive command on host OS: rm -rf /
   This operation can permanently destroy host system files or your workspace.
   To run anyway, type CONFIRM and press Enter. To cancel, press Enter or Ctrl+C: 
   ```
5. Unless you explicitly type **`CONFIRM`** and press Enter, the command is cancelled and cleared with `Ctrl+C`.

---

## 4. Troubleshooting

* **Docker environment option is grayed out:** Ensure your Docker daemon or Rancher Desktop is running (`docker info`). Synapse checks the daemon status before spawning container shells.
* **PTY allocation limits on macOS:** If you run many concurrent terminal sessions, macOS may reach its default `kern.tty.ptmx_max` limit. Synapse automatically falls back to a bidirectional pipe bridge so your terminal session never crashes.
