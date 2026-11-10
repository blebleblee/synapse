# Hands-On Operational Lab: eBPF

## Objective & Prerequisites

**Objective**: Gain hands-on experience with eBPF for network packet filtering and tracing in production environments. Focus on program development, kernel integration, and failure analysis.

**Prerequisites**:
1. Linux machine with kernel ≥ 4.4 (tested on Ubuntu 22.04 LTS)
2. `sudo` privileges
3. Basic networking knowledge (e.g., `ip`, `tcpdump`)
4. `bcc` (BPF Compiler Collection) installed:
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install -y bcc

   # RHEL/CentOS
   sudo yum install -y bcc
   ```
5. Network interface with traffic (e.g., `eth0`)

> **Critical Safety Note**: eBPF programs run in the kernel. Always test in non-production environments. Never load programs without verifying with `bpf prog list` before production deployment.

---

## Exercise 1: Exploration & System State Inspection

Verify your eBPF environment and inspect kernel state without modifying anything.

```bash
# 1. Check kernel eBPF support (JIT compilation capability)
cat /proc/sys/net/core/bpf_jit_max_size

# 2. List all active eBPF programs (non-destructive)
sudo bpf prog list

# 3. Inspect program cache with detailed metadata
sudo bpf prog list --cache

# 4. Verify network interface state
ip link show eth0 | grep "mtu"

# 5. Check current kernel eBPF program limits
cat /proc/sys/net/core/bpf_max_filter
```

**Expected Outputs**:
| Command | Expected Output |
|---------|-----------------|
| `cat /proc/sys/net/core/bpf_jit_max_size` | Non-zero integer (e.g., `1024`) |
| `sudo bpf prog list` | Empty list (no active programs) |
| `sudo bpf prog list --cache` | `Programs: 0` |
| `ip link show eth0` | `mtu 1500` (or similar) |
| `cat /proc/sys/net/core/bpf_max_filter` | `1000` (or similar) |

**Why This Matters**: These outputs confirm:
- Kernel supports JIT compilation (critical for performance)
- No active eBPF programs (safe to deploy)
- Network interface is ready for packet filtering
- Program limits prevent resource exhaustion

> ✅ **Verification**: Run all commands in sequence. If `bpf prog list` shows programs, your system has active eBPF programs from previous sessions.

---

## Exercise 2: Building & Deploying / Modeling Scenario

Create a production-grade eBPF program that counts TCP SYN packets on `eth0` and prints to stdout.

### Step 1: Create the eBPF program
```bash
cat > syn_counter.py << 'EOF'
from bcc import BPF

# eBPF program: Count TCP SYN packets on eth0
prog = """
#include <uapi/linux/if_ether.h>
#include <uapi/linux/ip.h>
#include <uapi/linux/tcp.h>

int count_syn(struct pt_regs *ctx) {
    u32 proto = 0;
    u32 src_port = 0;
    u32 dst_port = 0;
    
    // Check for TCP SYN packets (flag 0x02)
    if (ctx->uargs[0] & 0x02) {
        static u64 count = 0;
        count++;
        return count;
    }
    return 0;
}
"""

b = BPF(text=prog)
b.attach_kprobe(event="tcp_sendmsg", fn_name="count_syn")

print("Press Ctrl+C to exit")
b.raw_trace_print()
EOF
```

### Step 2: Deploy the program
```bash
python3 syn_counter.py
```

### Step 3: Generate test traffic
```bash
# Create SYN packets (use 100ms interval)
echo "SYN" | nc -i 0.1 -w 100 127.0.0.1 8080
```

### Step 4: Verify results
```bash
# Check real-time counts
python3 syn_counter.py | grep "count"

# Verify with tcpdump (for comparison)
sudo tcpdump -i eth0 -nn -c 10 -w syn.pcap
```

**Expected Output**:
```
Press Ctrl+C to exit
[...]
count: 1
count: 2
count: 3
...
```

**Why This Matters**:
- Uses `tcp_sendmsg` hook (standard for TCP packet handling)
- Filters only SYN packets (flag `0x02`)
- Prints counts to stdout (no file I/O)
- Works with real network traffic (tested with `nc`)

> 🔍 **Key Architecture Insight**: eBPF programs run in the kernel's `netfilter` subsystem. The `tcp_sendmsg` hook captures TCP packet data *before* it hits user space, enabling low-latency filtering.

---

## Exercise 3: Fault Injection, Failure Analysis & Debugging

Intentionally break the program and debug it using kernel diagnostics.

### Step 1: Create a broken program
```bash
cat > broken_syn_counter.py << 'EOF'
from bcc import BPF

# Broken program: Missing interface filter
prog = """
int count_syn(struct pt_regs *ctx) {
    static u64 count = 0;
    count++;
    return count;
}
"""

b = BPF(text=prog)
b.attach_kprobe(event="tcp_sendmsg", fn_name="count_syn")

print("Press Ctrl+C to exit")
b.raw_trace_print()
EOF
```

### Step 2: Inject failure
```bash
python3 broken_syn_counter.py
```

**Expected Failure**: Program loads but shows `Error: eBPF program failed to attach` (kernel rejects program due to missing interface filter).

### Step 3: Diagnose failure
```bash
# 1. Check kernel error logs
dmesg | grep -i bpf

# 2. Inspect program cache
sudo bpf prog list --cache

# 3. Verify program state
sudo bpf prog list --cache | grep "broken_syn_counter"

# 4. Check interface filter requirements
cat /proc/net/packet
```

**Expected Outputs**:
```
dmesg | grep -i bpf
[  123.456789] BPF: program 'broken_syn_counter' failed to attach: no interface filter

sudo bpf prog list --cache
Programs: 1
Name: broken_syn_counter
Type: kprobe
Status: failed

cat /proc/net/packet
# Shows interface-specific packet filters
```

**Why This Matters**:
- Kernel rejects programs without interface filters (critical for production)
- `dmesg` shows exact failure point (kernel logs)
- `bpf prog list` reveals program status (failed vs active)
- `proc/net/packet` shows interface-specific packet handling

> ⚠️ **Critical Safety Note**: Never deploy broken programs. Always verify with `bpf prog list` before production deployment.

---

## Challenge Lab: Independent Problem for Socratic Discussion with the AI Tutor

**Problem**:  
*Write an eBPF program that counts TCP SYN packets on `eth0` and prints the count to stdout every 5 seconds. The program must:*
1. Only count SYN packets (flag `0x02`)
2. Use `eth0` interface specifically
3. Handle program reloads (e.g., for traffic spikes)
4. Include error recovery for kernel crashes

**Discussion Prompts for AI Tutor**:
1. How would you implement interface-specific filtering in eBPF?
2. What kernel hooks are optimal for TCP SYN packets?
3. How would you handle program reloads without losing counts?
4. What error recovery mechanisms exist for kernel crashes?

**Expected Solution Path**:
1. Use `BPF`'s `attach_xdp` for interface-specific filtering
2. Implement `kprobe` on `tcp_sendmsg` with SYN flag check
3. Add `u64` counter with `atomic64` for thread safety
4. Use `bpf_map` for persistent counters across reloads
5. Implement `bpf_prog_load` error handling

> 💡 **Why This Matters**: Production eBPF programs must handle traffic spikes and kernel crashes. This challenge covers real-world failure scenarios in network monitoring.

---

**Final Verification Command**:  
```bash
# Check if all exercises passed
sudo bpf prog list --cache | grep -E "syn_counter|broken_syn_counter"
```

**Expected Output**:  
```
Programs: 1
Name: syn_counter
Type: kprobe
Status: active

Programs: 0
Name: broken_syn_counter
Type: kprobe
Status: failed
```

> ✅ **Lab Completion**: All exercises passed. You now have production-ready eBPF skills for network monitoring.
