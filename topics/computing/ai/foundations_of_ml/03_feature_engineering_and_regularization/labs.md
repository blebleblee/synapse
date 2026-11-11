Operational Verification Labs: 03 Feature Engineering And Regularization
===========================================================

### Objective & Environment Setup

**Required CLI Tools & Packages**

* `git` for version control
* `docker` for containerization
* `nvidia-docker` for GPU acceleration (optional)
* `python` 3.8+ for scripting
* `pip` for package management
* `scikit-learn` for feature engineering
* `keras` for regularization
* `tensorboard` for visualization

**Kernel Settings & Environment Variables**

* Enable kernel debugging: `echo "kernel.panic_on_oops=1" >> /etc/sysctl.conf`
* Set environment variable for GPU acceleration: `export CUDA_VISIBLE_DEVICES=0`

**Environment Setup**

```bash
# Clone the repository
git clone https://github.com/your-username/feature-engineering-and-regularization.git

# Navigate to the repository
cd feature-engineering-and-regularization

# Build the Docker image
docker build -t feature-engineering-and-regularization .

# Run the Docker container
docker run -it --gpus 1 feature-engineering-and-regularization
```

### Exercise 1: Live State & Internal Memory Inspection

**Inspecting Memory & Buffers**

* Use `pmap` to inspect memory usage: `pmap -d $(pidof python)`
* Use `strace` to inspect system calls: `strace -p $(pidof python)`
* Use `gdb` to inspect memory buffers: `gdb -q /proc/$(pidof python)/exe`

**Inspecting Processes & Metrics**

* Use `top` to inspect process metrics: `top -p $(pidof python)`
* Use `htop` to inspect process metrics: `htop -p $(pidof python)`
* Use `mpstat` to inspect CPU metrics: `mpstat -P ALL`

**Exact Runnable CLI Commands**

```bash
# Inspect memory usage
pmap -d $(pidof python)

# Inspect system calls
strace -p $(pidof python)

# Inspect memory buffers
gdb -q /proc/$(pidof python)/exe
```

### Exercise 2: Benchmarking & Saturation Profiling

**Benchmarking Commands**

* Use `ab` to benchmark HTTP requests: `ab -n 100 -c 10 http://localhost:5000/`
* Use `wrk` to benchmark HTTP requests: `wrk -t 4 -c 10 http://localhost:5000/`
* Use `sysbench` to benchmark CPU: `sysbench cpu --num-threads=4 --num-events=100000 run`

**Load Generation & Latency Profiling**

* Use `locust` to generate load: `locust -f load_test.py --no-web --headless`
* Use `tcpdump` to profile latency: `tcpdump -i any -n -s 0 -c 100 -W 100 -q 'tcp port 5000'`

**Exact Runnable CLI Commands**

```bash
# Benchmark HTTP requests
ab -n 100 -c 10 http://localhost:5000/

# Benchmark CPU
sysbench cpu --num-threads=4 --num-events=100000 run
```

### Exercise 3: Fault Injection & Recovery Analysis

**Simulating Sudden Failure**

* Use `kill` to simulate sudden failure: `kill -9 $(pidof python)`
* Use `docker restart` to restart the container: `docker restart feature-engineering-and-regularization`

**Inspecting Recovery Logs**

* Use `docker logs` to inspect recovery logs: `docker logs feature-engineering-and-regularization`
* Use `journalctl` to inspect system logs: `journalctl -u python`

**Exact Runnable CLI Commands**

```bash
# Simulate sudden failure
kill -9 $(pidof python)

# Inspect recovery logs
docker logs feature-engineering-and-regularization
```

### Diagnostic Cheat Sheet & Verification Checklist

| CLI Command | Operational Flag | Description |
| --- | --- | --- |
| `pmap` | `-d` | Inspect memory usage |
| `strace` | `-p` | Inspect system calls |
| `gdb` | `-q` | Inspect memory buffers |
| `top` | `-p` | Inspect process metrics |
| `htop` | `-p` | Inspect process metrics |
| `mpstat` | `-P ALL` | Inspect CPU metrics |
| `ab` | `-n` | Benchmark HTTP requests |
| `wrk` | `-t` | Benchmark HTTP requests |
| `sysbench` | `--num-threads` | Benchmark CPU |
| `locust` | `--no-web` | Generate load |
| `tcpdump` | `-i any` | Profile latency |
| `kill` | `-9` | Simulate sudden failure |
| `docker restart` |  | Restart container |
| `docker logs` |  | Inspect recovery logs |
| `journalctl` | `-u python` | Inspect system logs |

Note: This is a sample guide and you should adapt it to your specific use case and environment.
