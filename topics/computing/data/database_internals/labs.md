# Operational Verification Labs: Core

## Objective & Environment Setup

### Required CLI Tools & Packages

* `git` for version control and dependency management
* `gcc` or `clang` for C/C++ compilation
* `make` for build automation
* `docker` for containerization and isolation
* `linux-tools` for kernel debugging and inspection
* `sysdig` for system call tracing and analysis
* `stress-ng` for load generation and benchmarking

### Kernel Settings & Environment Variables

* Enable kernel debugging and tracing: `echo "kernel.printk = 7 4 1 7" >> /etc/sysctl.conf`
* Set kernel log level: `echo "kernel.printk = 7 4 1 7" >> /etc/sysctl.conf`
* Enable system call tracing: `echo "1" > /proc/sys/kernel/ftrace_enabled`
* Set environment variable for kernel debugging: `export KDB_NOBREAK=1`

### Environment Setup
