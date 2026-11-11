**Operational Verification Labs: 01 Supervised Vs Unsupervised Learning**
===========================================================

**Objective & Environment Setup**
-----------------------------

### Required CLI Tools & Packages

* Install `python3`, `pip3`, `numpy`, `scikit-learn`, and `matplotlib` on your Linux/BSD system:
```bash
sudo apt-get update && sudo apt-get install -y python3 python3-pip
pip3 install numpy scikit-learn matplotlib
```
* Install `stress-ng` for load generation and `sysdig` for system inspection:
```bash
sudo apt-get install -y stress-ng sysdig
```
* Set environment variables for Python and Python packages:
```bash
export PYTHONPATH=$PYTHONPATH:/usr/lib/python3.x/site-packages
export PATH=$PATH:/usr/bin/python3
```
### Kernel Settings & Configuration

* Ensure kernel version is 4.15 or later:
```bash
uname -r
```
* Verify kernel settings for CPU frequency scaling and governor:
```bash
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
```
* Set kernel settings for CPU frequency scaling and governor:
```bash
echo "performance" > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
```
### Environment Variables

* Set environment variables for Python and Python packages:
```bash
export PYTHONPATH=$PYTHONPATH:/usr/lib/python3.x/site-packages
export PATH=$PATH:/usr/bin/python3
```
**Exercise 1: Live State & Internal Memory Inspection**
---------------------------------------------------

### Inspect Memory & Buffers

* Use `sysdig` to inspect memory and buffers:
```bash
sysdig -c memory -p "proc.name == 'python3' and mem.type == 'anon'"
```
* Use `pmap` to inspect process memory maps:
```bash
pmap -d $(pgrep python3)
```
### Inspect Processes & Metrics

* Use `ps` to inspect running processes:
```bash
ps -ef | grep python3
```
* Use `top` to inspect system metrics:
```bash
top -b -n 1
```
### Inspect Network Metrics

* Use `netstat` to inspect network connections:
```bash
netstat -tlnp | grep python3
```
* Use `ss` to inspect socket statistics:
```bash
ss -tlnp | grep python3
```
**Exercise 2: Benchmarking & Saturation Profiling**
-------------------------------------------------

### Benchmarking

* Use `stress-ng` to generate load:
```bash
stress-ng --cpu 4 --io 2 --vm 1 --timeout 60
```
* Use `sysdig` to inspect system metrics during load:
```bash
sysdig -c system -p "proc.name == 'stress-ng' and sys.cpu.utilization > 50"
```
### Saturation Profiling

* Use `sysdig` to inspect system metrics during saturation:
```bash
sysdig -c system -p "proc.name == 'python3' and sys.cpu.utilization > 90"
```
**Exercise 3: Fault Injection & Recovery Analysis**
---------------------------------------------------

### Simulate Sudden Failure

* Use `kill` to simulate sudden process failure:
```bash
kill -9 $(pgrep python3)
```
* Use `sysdig` to inspect system metrics during failure:
```bash
sysdig -c system -p "proc.name == 'python3' and sys.cpu.utilization > 50"
```
### Simulate Packet Loss

* Use `tc` to simulate packet loss:
```bash
tc qdisc add dev eth0 root netem loss 10%
```
* Use `sysdig` to inspect system metrics during packet loss:
```bash
sysdig -c system -p "proc.name == 'python3' and sys.cpu.utilization > 50"
```
**Diagnostic Cheat Sheet & Verification Checklist**
---------------------------------------------------

| CLI Command | Operational Flag | Description |
| --- | --- | --- |
| `sysdig` | `-c memory` | Inspect memory and buffers |
| `pmap` | `-d` | Inspect process memory maps |
| `ps` | `-ef` | Inspect running processes |
| `top` | `-b -n 1` | Inspect system metrics |
| `netstat` | `-tlnp` | Inspect network connections |
| `ss` | `-tlnp` | Inspect socket statistics |
| `stress-ng` | `--cpu 4 --io 2 --vm 1 --timeout 60` | Generate load |
| `sysdig` | `-c system` | Inspect system metrics |
| `kill` | `-9` | Simulate sudden process failure |
| `tc` | `qdisc add dev eth0 root netem loss 10%` | Simulate packet loss |

Note: This is a sample guide and may require modifications to suit specific system configurations and requirements.
