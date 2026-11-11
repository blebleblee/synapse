# Operational Verification Labs: 02 Agentic Workflows And Tools

## Objective & Environment Setup

This lab guides you through the operational verification of agentic workflows and tools in a Linux/BSD environment. Ensure you have the following tools and packages installed:

* `htop` for process inspection
* `iftop` for network traffic analysis
* `sysdig` for system call inspection
* `stress-ng` for load generation
* `fio` for disk I/O benchmarking
* `sysctl` for kernel settings
* `dmesg` for kernel log inspection

Set the following environment variables:

* `LD_LIBRARY_PATH` to include the `sysdig` library path
* `PATH` to include the `stress-ng` and `fio` binary paths

## Exercise 1: Live State & Internal Memory Inspection

### 1.1 Inspect Memory Usage

Run the following command to inspect memory usage:
