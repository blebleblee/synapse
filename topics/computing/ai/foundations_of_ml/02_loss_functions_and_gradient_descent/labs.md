**Operational Verification Labs: 02 Loss Functions And Gradient Descent**

## Objective & Environment Setup

### Required CLI Tools & Packages

* Install `git`, `python3`, `numpy`, `scipy`, and `matplotlib` on your Linux/BSD system:
```bash
sudo apt-get update && sudo apt-get install -y git python3 python3-pip numpy scipy matplotlib
```
* Install `keras` and `tensorflow` using pip:
```bash
pip3 install --user keras tensorflow
```
* Clone the `loss_functions_and_gradient_descent` repository:
```bash
git clone https://github.com/your-username/loss_functions_and_gradient_descent.git
```
### Kernel Settings & Environment Variables

* Ensure the kernel is configured to use the `perf` event system:
```bash
sudo sysctl -w kernel.perf_event_paranoid=-1
```
* Set the `LD_LIBRARY_PATH` environment variable to include the `tensorflow` installation:
```bash
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/python3.x/site-packages/tensorflow
```
## Exercise 1: Live State & Internal Memory Inspection

### Inspect Memory Usage & Buffers

* Use `top` to inspect memory usage and buffer allocation:
```bash
top -c -o mem
```
* Use `pmap` to inspect the memory map of the `tensorflow` process:
```bash
pmap -d $(pgrep -f tensorflow)
```
### Inspect Processes & Metrics

* Use `ps` to inspect the process list and identify the `tensorflow` process:
```bash
ps -ef | grep tensorflow
```
* Use `mpstat` to inspect CPU metrics and identify any bottlenecks:
```bash
mpstat -P ALL
```
### Inspect Gradient Descent Convergence

* Use `matplotlib` to plot the loss function and gradient descent convergence:
```bash
python3 plot_loss_function.py
```
## Exercise 2: Benchmarking & Saturation Profiling

### Run Benchmark Commands

* Use `ab` to run a benchmark on the `tensorflow` model:
```bash
ab -n 100 -c 10 http://localhost:5000/predict
```
* Use `wrk` to run a benchmark on the `tensorflow` model:
```bash
wrk -t 4 -c 10 -d 10s http://localhost:5000/predict
```
### Profile Latency & Saturation

* Use `perf` to profile latency and saturation on the `tensorflow` process:
```bash
perf stat -e cpu-clock,cache-misses,cache-references -a -p $(pgrep -f tensorflow)
```
## Exercise 3: Fault Injection & Recovery Analysis

### Simulate Sudden Failure

* Use `kill` to simulate a sudden failure of the `tensorflow` process:
```bash
kill -9 $(pgrep -f tensorflow)
```
* Use `journalctl` to inspect the recovery logs:
```bash
journalctl -u tensorflow
```
### Simulate Packet Loss & Corruption

* Use `tc` to simulate packet loss and corruption on the `tensorflow` model:
```bash
tc qdisc add dev lo root netem loss 10%
tc qdisc add dev lo root netem corrupt 10%
```
* Use `tcpdump` to inspect the packet loss and corruption:
```bash
tcpdump -i lo -n -vv
```

## Diagnostic Cheat Sheet & Verification Checklist

| CLI Command | Operational Flag | Description |
| --- | --- | --- |
| `top` | `-c` | Inspect memory usage and buffer allocation |
| `pmap` | `-d` | Inspect memory map of the `tensorflow` process |
| `ps` | `-ef` | Inspect process list and identify `tensorflow` process |
| `mpstat` | `-P ALL` | Inspect CPU metrics and identify bottlenecks |
| `ab` | `-n 100` | Run benchmark on `tensorflow` model |
| `wrk` | `-t 4` | Run benchmark on `tensorflow` model |
| `perf` | `-e cpu-clock` | Profile latency and saturation on `tensorflow` process |
| `kill` | `-9` | Simulate sudden failure of `tensorflow` process |
| `journalctl` | `-u tensorflow` | Inspect recovery logs |
| `tc` | `loss 10%` | Simulate packet loss and corruption on `tensorflow` model |
| `tcpdump` | `-i lo` | Inspect packet loss and corruption |

Note: This is a sample guide and you should adapt it to your specific environment and requirements.
