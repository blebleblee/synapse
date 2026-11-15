# Operational Verification Labs: Systemd

## Objective & Toolchain Setup

Systemd represents the canonical modern Linux init system and service supervisor, managing the boot sequence, service dependencies, resource control through cgroups, and socket activation across contemporary distributions. This laboratory guide develops operational verification competencies for engineers implementing systemd unit files, custom service daemons, and D-Bus control interfaces. You will dissect systemd's internal state machines through runtime introspection, profile service startup latencies under thermal and I/O contention, and stress-test cgroup resource isolation boundaries using memory pressure and CPU saturation workloads.

The verification methodology grounds all diagnostics in measurable physical observables: wall-clock service activation times from kernel timestamps, RSS memory consumption deltas captured through procfs snapshots, and CPU scheduling latencies extracted from perf events and eBPF tracepoints. You will operate systemd's own diagnostic toolchain—systemctl, journalctl, systemd-analyze, and busctl—alongside kernel profiling instrumentation to construct causal models linking unit file directives to runtime resource behavior. This approach prioritizes empirical measurement over abstract documentation, building intuition for how systemd's declarative configuration language compiles into concrete process control syscalls, cgroup hierarchy manipulations, and inotify-based file monitoring.

Your development environment requires a Linux system running systemd version 250 or later, providing access to the systemd-oomd out-of-memory daemon and PSI (Pressure Stall Information) metrics. Install the complete systems profiling stack: perf from linux-tools, bpftrace for dynamic kernel tracing, valgrind for heap allocation tracking, and the LLVM toolchain including clang, lldb, and AddressSanitizer. For service daemon implementation exercises, configure Rust via rustup with the stable toolchain, and install the C development headers for libsystemd to enable native sd-notify integration. Verify your systemd version with `systemctl --version` and confirm cgroup v2 unified hierarchy mounting at `/sys/fs/cgroup` using `mount | grep cgroup2`. This unified hierarchy is mandatory for accurate memory accounting and CPU bandwidth enforcement.

Establish a non-privileged user namespace for safe experimentation using `systemd-run --user --scope` commands, which instantiate transient service units under your session slice without requiring root privileges or polluting the system service directory. Create a working directory at `~/systemd-labs` to house custom unit files, test binaries, and profiling artifacts. Install systemd development libraries with `sudo apt install libsystemd-dev` on Debian-based systems or `sudo dnf install systemd-devel` on Fedora, enabling compilation of C programs that communicate with systemd's readiness notification protocol. For Rust developers, add the `libsystemd` crate to your `Cargo.toml` dependencies, providing safe bindings to sd_notify, sd_journal_send, and other native systemd APIs.

## Exercise 1: AST, IR & Disassembly Analysis

Systemd's unit file parser implements a custom INI-style configuration language that compiles declarative service specifications into an internal dependency graph and process execution model. This exercise reverse-engineers that compilation process by analyzing how systemd transforms a high-level unit file into runtime process control structures, examining the resulting system call sequences through strace, and correlating unit directives with their concrete implementation in systemd's C codebase. You will write a minimal service daemon in Rust, construct a corresponding systemd unit file with resource limits and dependency ordering, then dissect the complete lifecycle from unit file parse through cgroup setup to final process execution.

Begin by implementing a trivial HTTP health check service that listens on a Unix domain socket and responds with a JSON status payload. This daemon will serve as the controlled artifact for systemd lifecycle analysis. Create `~/systemd-labs/health-daemon/src/main.rs` with a tokio async runtime that binds to `/run/user/$UID/health.sock`, accepts connections, and returns a hardcoded 200 OK response. The implementation must call `sd_notify` after socket binding completes to signal readiness to systemd, enabling precise measurement of the activation timeline. Wire the libsystemd crate into your project with `cargo add libsystemd`, then modify the main function to invoke `libsystemd::daemon::notify(false, &[libsystemd::daemon::NotifyState::Ready])` immediately after the socket listener initialization succeeds.

```rust
// ~/systemd-labs/health-daemon/src/main.rs
use std::os::unix::fs::PermissionsExt;
use tokio::net::UnixListener;
use tokio::io::{AsyncReadExt, AsyncWriteExt};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let socket_path = format!("/run/user/{}/health.sock", unsafe { libc::getuid() });
    
    // Remove stale socket if present
    let _ = std::fs::remove_file(&socket_path);
    
    let listener = UnixListener::bind(&socket_path)?;
    
    // Set socket permissions to 0600
    let metadata = std::fs::metadata(&socket_path)?;
    let mut perms = metadata.permissions();
    perms.set_mode(0o600);
    std::fs::set_permissions(&socket_path, perms)?;
    
    // Signal readiness to systemd
    libsystemd::daemon::notify(false, &[libsystemd::daemon::NotifyState::Ready])?;
    
    eprintln!("Health daemon ready on {}", socket_path);
    
    loop {
        let (mut stream, _addr) = listener.accept().await?;
        
        tokio::spawn(async move {
            let mut buf = [0u8; 1024];
            let _ = stream.read(&mut buf).await;
            
            let response = b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 27\r\n\r\n{\"status\":\"healthy\",\"ok\":true}";
            let _ = stream.write_all(response).await;
        });
    }
}
```

Compile the daemon with `cargo build --release` and verify it produces a statically-linked binary at `target/release/health-daemon`. Test the socket communication manually by launching the daemon in a terminal, then using `curl --unix-socket /run/user/$UID/health.sock http://localhost/` from another terminal to confirm the JSON response arrives. This establishes the baseline functionality before systemd integration.

Now construct the systemd unit file that declares service type, dependencies, resource limits, and restart policy. Create `~/.config/systemd/user/health-daemon.service` with a unit configuration specifying `Type=notify` to leverage the sd_notify readiness protocol, ensuring systemd waits for the explicit ready signal rather than assuming the service is active immediately after fork. Set memory and CPU limits using `MemoryMax=64M` and `CPUQuota=50%` to constrain resource consumption, enabling clean verification of cgroup enforcement later. The `Restart=on-failure` directive with `RestartSec=5s` implements exponential backoff for transient failures.

```ini
# ~/.config/systemd/user/health-daemon.service
[Unit]
Description=Health Check Daemon for Systemd Labs
After=network.target
Documentation=https://github.com/systemd/systemd

[Service]
Type=notify
ExecStart=/home/%u/systemd-labs/health-daemon/target/release/health-daemon
Restart=on-failure
RestartSec=5s

# Resource limits
MemoryMax=64M
CPUQuota=50%

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/run/user/%U

# Notification settings
NotifyAccess=main
TimeoutStartSec=30s

[Install]
WantedBy=default.target
```

Replace the hardcoded username in `ExecStart` with your actual home directory path, then reload the systemd user manager configuration with `systemctl --user daemon-reload` to parse the new unit file. This command triggers systemd's configuration parser, which lexes the INI syntax, validates section names against its internal schema, and constructs an in-memory dependency graph linking this service to `network.target` and `default.target`. Examine the parsed configuration with `systemctl --user cat health-daemon.service` to verify systemd correctly interpolated the `%u` and `%U` specifiers into your username and UID.

Start the service under strace observation to capture the complete system call sequence from unit activation through process execution. Execute `systemd-run --user --scope --collect strace -o /tmp/health-strace.log -f -e trace=execve,clone,cgroup,socket,bind,listen,sendmsg systemctl --user start health-daemon.service` to record all relevant syscalls. The `-f` flag follows child processes created by systemd's fork-exec model, while the filtered trace categories isolate the specific syscalls involved in service activation: execve for program loading, clone for process creation, socket/bind/listen for Unix domain socket setup, and sendmsg for the sd_notify readiness datagram transmission.

Inspect the resulting trace file with `less /tmp/health-strace.log` and identify the critical sequence. You will observe systemd executing `clone()` to spawn the service process, followed by a series of `openat()` and `write()` calls into `/sys/fs/cgroup/user.slice/user-$UID.slice/user@$UID.service/app.slice/health-daemon.service/` to configure cgroup controllers. The memory limit appears as a write to `memory.max` with the value 67108864 (64 MiB in bytes), and the CPU quota manifests as writes to `cpu.max` encoding "50000 100000" (50ms per 100ms period, yielding 50% bandwidth). This direct filesystem manipulation exposes how systemd's declarative directives compile into concrete cgroup cgroupfs writes.

Further into the trace, locate the `execve()` call that overlays your Rust binary onto the cloned process. The arguments array shows the full path to `health-daemon` with no additional parameters, confirming systemd passes through your ExecStart command verbatim. Immediately after the execve, the service process executes `socket(AF_UNIX, SOCK_STREAM)`, `bind()` to `/run/user/$UID/health.sock`, and `listen()` with a backlog of 128 connections. The final critical event is a `sendmsg()` call to systemd's notification socket at `/run/user/$UID/systemd/notify`, transmitting the datagram "READY=1\n". This message triggers systemd's state machine transition from "activating" to "active" state, unblocking any dependent units.

Correlate these runtime observations with systemd's source code by examining the service activation path in the official repository. Clone the systemd source with `git clone https://github.com/systemd/systemd.git ~/systemd-source`, then navigate to `src/core/service.c` and locate the `service_enter_start()` function. This function implements the state machine logic that forks the service process, configures its cgroup parameters via `unit_realize_cgroup()`, and enters the "activating" state while waiting for the readiness notification. Cross-reference the cgroup setup code in `src/core/cgroup.c`, specifically `cgroup_context_apply()`, which iterates over the parsed unit directives and translates them into cgroupfs filesystem operations.

Construct a visual dependency graph for your service using `systemd-analyze dot --user health-daemon.service | dot -Tsvg -o /tmp/health-deps.svg`, then open the resulting SVG in a browser. The graph illustrates the dependency edges connecting your service to `network.target`, `sysinit.target`, and ultimately to `basic.target`, forming a directed acyclic graph that systemd traverses during boot or manual activation. Red edges indicate "Requires" dependencies that mandate successful activation of the target, while green "After" edges encode ordering constraints without implying failure propagation. This visualization clarifies why systemd must wait for network initialization before starting your socket-based daemon.

Measure the end-to-end activation latency using systemd-analyze's built-in instrumentation. Query the service activation timestamp with `systemd-analyze --user blame | grep health-daemon` to see the elapsed wall-clock time from activation request to readiness signal receipt. On a typical system, this should complete within 50-200 milliseconds, dominated by Rust's async runtime initialization and tokio's thread pool spawn. Compare this against the theoretical minimum by examining the raw timestamp pairs in `systemctl --user show health-daemon.service -p ActiveEnterTimestamp -p ActiveEnterTimestampMonotonic`. The monotonic timestamp uses the CLOCK_MONOTONIC clock source, providing a non-adjustable reference for latency calculations that remains stable across NTP clock corrections.

Disassemble the compiled health-daemon binary to verify the sd_notify callsite. Run `objdump -d target/release/health-daemon | grep -A 20 'sd_notify'` to locate the assembly sequence implementing the readiness notification. You should observe a sequence loading the socket file descriptor from the `NOTIFY_SOCKET` environment variable, constructing the "READY=1" C string in a stack buffer, then invoking the `sendmsg()` syscall via the `libsystemd.so` shared library. The disassembly confirms that the high-level Rust `notify()` call compiles down to a straightforward datagram transmission with no hidden complexity or thread synchronization overhead.

Finally, inject artificial delays into the activation path to observe systemd's timeout handling. Modify your Rust daemon to sleep for 35 seconds before calling sd_notify, exceeding the `TimeoutStartSec=30s` directive. Recompile and restart the service with `systemctl --user restart health-daemon.service`, then watch `journalctl --user -u health-daemon.service -f` as systemd kills the service with SIGTERM after the timeout expires. The journal log shows the state transition sequence: "Starting" → "start-timeout" → "Stopped (failure)". Restore the original code and confirm that reducing the sleep to 5 seconds allows successful activation, demonstrating systemd's state machine timeout enforcement.

## Exercise 2: Cache Miss & Throughput Profiling

Service startup latency and steady-state throughput directly correlate with memory hierarchy behavior, as systemd forks and execs dozens of services during boot, each suffering cold-start instruction and data cache misses. This exercise profiles cache miss rates and memory bandwidth consumption during systemd service activation under varying thermal and load conditions, using perf hardware performance counters and eBPF-based latency histograms. You will induce cache pressure through synthetic memory-intensive workloads, measure the resulting service activation slowdown, and analyze the causal chain from LLC misses through memory controller saturation to elevated tail latencies.

Begin by establishing baseline cache behavior for the health-daemon service activation under idle system conditions. Use perf's hardware event sampling to capture L1, L2, and last-level cache (LLC) miss rates during a cold-start activation cycle. First, stop the service with `systemctl --user stop health-daemon.service`, then flush the page cache to ensure a genuine cold start with `sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'`. This writes "3" to the drop_caches control file, instructing the kernel to evict clean page cache entries, dentries, and inodes, forcing subsequent file reads to hit storage. Execute the profiled activation with `perf stat -e cycles,instructions,cache-references,cache-misses,LLC-loads,LLC-load-misses -p $(systemctl --user start health-daemon.service & echo $!)`, capturing the hardware counter values for the systemd manager process that orchestrates the service start.

The perf output displays raw event counts and derived metrics. Examine the cache-miss percentage calculated as `(cache-misses / cache-references) * 100`, which typically ranges from 5-15% for cold-start service activations on modern x86_64 systems with 8MB+ LLC capacity. The LLC-load-misses counter isolates last-level cache misses that propagate to main memory, representing the most expensive memory hierarchy tier with 100-200ns latency versus sub-5ns L1 hits. A cold-start activation exhibits elevated LLC misses as systemd loads the service binary's .text section, dynamic linker, shared libraries, and your Rust binary's compiled code into initially cold cache lines.

Generate cache pressure using a purpose-built memory-streaming workload that deliberately thrashes the LLC by accessing a working set larger than the cache capacity. Implement a simple C program that allocates a 32MB buffer, iterates through it with a stride matching cache line size (64 bytes on x86), and writes random data to each line. This sequential write pattern maximizes memory bandwidth consumption while evicting cached data. Create `~/systemd-labs/cache-pressure.c`:

```c
// ~/systemd-labs/cache-pressure.c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#define BUFFER_SIZE (32 * 1024 * 1024)  // 32 MiB
#define CACHE_LINE_SIZE 64

int main(int argc, char *argv[]) {
    uint8_t *buffer = malloc(BUFFER_SIZE);
    if (!buffer) {
        perror("malloc");
        return 1;
    }
    
    unsigned int seed = time(NULL);
    
    while (1) {
        for (size_t i = 0; i < BUFFER_SIZE; i += CACHE_LINE_SIZE) {
            // Write random data to each cache line
            uint64_t val = rand_r(&seed);
            memcpy(buffer + i, &val, sizeof(val));
        }
        
        // Prevent compiler optimization
        if (buffer[rand_r(&seed) % BUFFER_SIZE] == 0xFF) {
            printf(".");
        }
    }
    
    free(buffer);
    return 0;
}
```

Compile with optimizations disabled to preserve the memory access pattern: `gcc -O0 -o ~/systemd-labs/cache-pressure ~/systemd-labs/cache-pressure.c`. Launch multiple instances equal to your CPU core count to saturate memory bandwidth: `for i in $(seq 1 $(nproc)); do ~/systemd-labs/cache-pressure & done`. Monitor system memory bandwidth with `perf stat -a -e cycles,instructions,cache-misses,dTLB-load-misses sleep 5` to confirm the workload is generating cache misses at an elevated rate, typically increasing the baseline miss rate by 3-5×.

Measure service activation latency under cache pressure by restarting the health-daemon service while the cache-pressure workload saturates the LLC. Stop the service with `systemctl --user stop health-daemon.service`, flush caches again, then use systemd-analyze to capture activation timestamps: `systemctl --user start health-daemon.service && systemd-analyze --user critical-chain health-daemon.service`. The critical-chain output displays the full dependency chain with wall-clock durations, revealing the activation latency from the manager's perspective. Record this latency, then kill the cache-pressure processes with `killall cache-pressure` and repeat the measurement under idle conditions. The latency delta—typically 50-200ms of additional overhead—directly quantifies the cache contention penalty.

Construct a more granular view of cache behavior using perf record with instruction pointer sampling. Profile the health-daemon binary itself by attaching perf to the service process during activation. First, determine the service's main PID with `systemctl --user show health-daemon.service -p MainPID --value`, then record 5 seconds of cache-miss events: `sudo perf record -e cache-misses -c 1000 -g -p <PID> sleep 5`. The `-c 1000` flag samples every 1000th cache miss, building a call-graph profile that attributes misses to specific functions and code paths. Generate the report with `sudo perf report --stdio` to view the top cache-miss hotspots.

The report typically highlights the tokio runtime initialization sequence, particularly the thread pool spawn logic in `tokio::runtime::Builder::new_multi_thread()` and the async executor setup in `tokio::runtime::Runtime::block_on()`. These functions allocate per-thread work queues and synchronization primitives, incurring compulsory cache misses as fresh heap allocations pull data into the cache hierarchy. Secondary hotspots appear in the dynamic linker (`ld.so`) during shared library symbol resolution and the Rust standard library's allocator in `alloc::alloc::Global::alloc()`. This profile confirms that service activation latency is dominated by cold-start initialization overhead, not steady-state operational logic.

Drill deeper into the memory subsystem behavior using perf's TMA (Top-down Microarchitecture Analysis) metrics on Intel CPUs. Execute `perf stat --topdown -a sleep 5` during service activation to decompose execution into four categories: frontend-bound (instruction fetch stalls), backend-bound (execution resource stalls), retiring (useful work), and bad speculation (branch mispredictions). Under cache pressure, the backend-bound percentage increases substantially, typically from 20-30% baseline to 40-50% under contention, indicating execution stalls due to memory subsystem saturation. Cross-reference with the LLC-load-misses counter to confirm that memory latency is the primary backend bottleneck.

Visualize the cache miss spatial distribution across the service binary using perf's annotate feature. Generate an annotated disassembly with `sudo perf annotate --stdio health-daemon`, which overlays cache-miss sample counts directly onto assembly instructions. The hottest instructions correspond to indirect memory loads through pointer chains, such as vtable lookups in Rust's trait dispatch and hash table probes in the tokio runtime's task scheduler. These access patterns exhibit poor spatial locality, as each pointer dereference potentially jumps to a distant cache line, preventing hardware prefetchers from accurately predicting the next access.

Construct a time-series plot of cache miss rate versus service activation latency by scripting repeated activation cycles with varying background cache pressure. Write a shell script that alternates between idle and loaded conditions, recording both perf cache-misses counts and systemd-analyze activation timestamps. Create `~/systemd-labs/cache-latency-sweep.sh`:

```bash
#!/bin/bash
# ~/systemd-labs/cache-latency-sweep.sh

OUTPUT="cache_latency_data.csv"
echo "iteration,cache_pressure,activation_latency_ms,cache_misses,llc_misses" > "$OUTPUT"

for iteration in {1..20}; do
    # Alternate between idle and loaded
    if (( iteration % 2 == 0 )); then
        CACHE_PRESSURE="yes"
        # Start cache pressure
        for i in $(seq 1 $(nproc)); do
            ~/systemd-labs/cache-pressure &
        done
        PRESSURE_PIDS=$!
        sleep 2  # Let pressure stabilize
    else
        CACHE_PRESSURE="no"
    fi
    
    # Stop service and flush caches
    systemctl --user stop health-daemon.service 2>/dev/null
    sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
    
    # Measure activation with perf
    START=$(date +%s%N)
    PERF_OUTPUT=$(mktemp)
    perf stat -e cache-misses,LLC-load-misses -o "$PERF_OUTPUT" systemctl --user start health-daemon.service 2>&1
    END=$(date +%s%N)
    
    # Wait for service to fully activate
    sleep 1
    
    LATENCY_NS=$((END - START))
    LATENCY_MS=$((LATENCY_NS / 1000000))
    
    CACHE_MISSES=$(grep cache-misses "$PERF_OUTPUT" | awk '{print $1}' | tr -d ',')
    LLC_MISSES=$(grep LLC-load-misses "$PERF_OUTPUT" | awk '{print $1}' | tr -d ',')
    
    echo "$iteration,$CACHE_PRESSURE,$LATENCY_MS,$CACHE_MISSES,$LLC_MISSES" >> "$OUTPUT"
    
    rm "$PERF_OUTPUT"
    
    if [ "$CACHE_PRESSURE" = "yes" ]; then
        killall cache-pressure
    fi
    
    sleep 2
done

echo "Data written to $OUTPUT"
```

Make the script executable with `chmod +x ~/systemd-labs/cache-latency-sweep.sh` and run it to collect the dataset. The resulting CSV file enables correlation analysis between cache metrics and activation latency. Import the data into gnuplot or Python's matplotlib to generate scatter plots showing the positive correlation between LLC misses and activation time, with R² values typically exceeding 0.7 under controlled conditions.

Extend the analysis to memory bandwidth saturation by using perf's uncore performance monitoring units (PMUs) on Intel servers with integrated memory controllers. Query available uncore events with `perf list | grep uncore_imc`, looking for read and write bandwidth counters like `uncore_imc_0/cas_count_read/` and `uncore_imc_0/cas_count_write/`. These events count DRAM column access strobe (CAS) operations, directly measuring memory controller traffic. Profile service activation under cache pressure while monitoring memory bandwidth: `perf stat -e uncore_imc_0/cas_count_read/,uncore_imc_0/cas_count_write/ -a sleep 5`. Multiply the CAS counts by 64 bytes (cache line size) and divide by the measurement interval to obtain memory bandwidth in MB/s.

Correlate the memory bandwidth saturation with service activation latency by comparing bandwidth during idle versus loaded conditions. Under idle conditions, service activation generates modest memory traffic, typically 200-500 MB/s as systemd loads the binary and shared libraries. Under cache pressure from the memory-streaming workload, total system memory bandwidth approaches the theoretical DRAM limit (e.g., 30-50 GB/s for dual-channel DDR4-2400), with the service activation competing for memory controller bandwidth. The activation latency increases proportionally to the memory bandwidth contention, as each LLC miss incurs longer queuing delays at the saturated memory controller.

Finally, deploy eBPF-based latency tracking to capture a histogram of systemd's fork-exec durations across multiple service activations. Use bpftrace to instrument the kernel's `do_execve()` function and measure the elapsed time from entry to return. Create `~/systemd-labs/execve-latency.bt`:

```c
// ~/systemd-labs/execve-latency.bt
tracepoint:syscalls:sys_enter_execve
{
    @start[tid] = nsecs;
    @filename[tid] = str(args->filename);
}

tracepoint:syscalls:sys_exit_execve
/@start[tid]/
{
    $duration_us = (nsecs - @start[tid]) / 1000;
    
    @execve_latency_us = hist($duration_us);
    @by_binary[@filename[tid]] = hist($duration_us);
    
    delete(@start[tid]);
    delete(@filename[tid]);
}

interval:s:10
{
    print(@execve_latency_us);
    print(@by_binary);
}
```

Run the eBPF program with `sudo bpftrace ~/systemd-labs/execve-latency.bt`, then trigger multiple service activations with a loop: `for i in {1..50}; do systemctl --user restart health-daemon.service; sleep 1; done`. The bpftrace output displays a logarithmic histogram showing the distribution of execve latencies. Under idle conditions, the distribution clusters tightly around 5-15ms. Under cache pressure, the histogram broadens significantly, with a long tail extending to 50-100ms, quantifying the variance introduced by cache contention.

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

Systemd's concurrent service management, built on libudev event handling, D-Bus message dispatch, and epoll-driven I/O multiplexing, creates numerous opportunities for race conditions and memory leaks in both systemd itself and the services it supervises. This exercise deploys ThreadSanitizer (TSan) and LeakSanitizer (LSan) to detect data races and heap leaks in a multi-threaded service daemon under systemd supervision, then stress-tests cgroup memory accounting to verify proper resource cleanup during rapid service restart cycles. You will instrument a Rust service with sanitizer runtimes, inject deliberate concurrency bugs to validate detection, and profile systemd's own cgroup teardown logic for leaked kernel memory under resource pressure.

Implement a multi-threaded statistics collector daemon that aggregates metrics from multiple worker threads using shared atomic counters. This design introduces race conditions if synchronization primitives are misused or omitted, providing controlled targets for TSan detection. Create `~/systemd-labs/stats-daemon/src/main.rs` with a thread pool that increments shared counters and a main thread that periodically reads and logs the values. Deliberately introduce a data race by using non-atomic operations on shared state to verify TSan catches the violation.

```rust
// ~/systemd-labs/stats-daemon/src/main.rs
use std::sync::{Arc, Mutex};
use std::sync::atomic::{AtomicU64, Ordering};
use std::thread;
use std::time::Duration;

struct StatsCollector {
    // Correct: atomic counter
    atomic_counter: AtomicU64,
    // Incorrect: non-atomic counter for race detection
    racy_counter: u64,
}

impl StatsCollector {
    fn new() -> Self {
        StatsCollector {
            atomic_counter: AtomicU64::new(0),
            racy_counter: 0,
        }
    }
}

fn worker_thread(stats: Arc<Mutex<StatsCollector>>, id: usize) {
    loop {
        thread::sleep(Duration::from_millis(10));
        
        let mut stats_lock = stats.lock().unwrap();
        
        // Correct atomic increment
        stats_lock.atomic_counter.fetch_add(1, Ordering::Relaxed);
        
        // INTENTIONAL DATA RACE: non-atomic increment
        let current = stats_lock.racy_counter;
        drop(stats_lock);  // Drop lock early to create race window
        thread::sleep(Duration::from_micros(1));
        let mut stats_lock_again = stats.lock().unwrap();
        stats_lock_again.racy_counter = current + 1;
        
        if id == 0 && stats_lock_again.atomic_counter.load(Ordering::Relaxed) % 1000 == 0 {
            eprintln!(
                "Stats: atomic={}, racy={}",
                stats_lock_again.atomic_counter.load(Ordering::Relaxed),
                stats_lock_again.racy_counter
            );
        }
    }
}

fn main() {
    let stats = Arc::new(Mutex::new(StatsCollector::new()));
    
    // Signal readiness to systemd
    let _ = libsystemd::daemon::notify(false, &[libsystemd::daemon::NotifyState::Ready]);
    
    eprintln!("Stats daemon started with {} workers", num_cpus::get());
    
    let mut handles = vec![];
    for id in 0..num_cpus::get() {
        let stats_clone = Arc::clone(&stats);
        let handle = thread::spawn(move || worker_thread(stats_clone, id));
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
}
```

Add the required dependencies to `Cargo.toml`: `libsystemd = "0.7"` and `num_cpus = "1.16"`. Build the daemon with ThreadSanitizer enabled by setting the `RUSTFLAGS` environment variable to activate LLVM's TSan instrumentation: `RUSTFLAGS="-Z sanitizer=thread" cargo +nightly build --target x86_64-unknown-linux-gnu`. Note that TSan requires the nightly Rust toolchain due to its unstable sanitizer feature. If the nightly toolchain is not installed, run `rustup toolchain install nightly` before compiling.

Create a systemd user unit for the stats daemon at `~/.config/systemd/user/stats-daemon.service`, configuring it with restrictive memory limits to enable leak detection. Set `MemoryMax=128M` to provide a bounded heap for LSan tracking and `TasksMax=32` to limit thread spawning.

```ini
# ~/.config/systemd/user/stats-daemon.service
[Unit]
Description=Statistics Collection Daemon with TSan
After=default.target

[Service]
Type=notify
ExecStart=/home/%u/systemd-labs/stats-daemon/target/x86_64-unknown-linux-gnu/debug/stats-daemon
Restart=on-failure
RestartSec=3s

MemoryMax=128M
TasksMax=32

Environment=TSAN_OPTIONS=log_path=/tmp/tsan-stats-daemon.log:halt_on_error=0:second_deadlock_stack=1

NotifyAccess=main
TimeoutStartSec=10s

[Install]
WantedBy=default.target
```

The `TSAN_OPTIONS` environment variable configures ThreadSanitizer's runtime behavior: `log_path` redirects race reports to a dedicated file for post-mortem analysis, `halt_on_error=0` prevents immediate termination on the first detected race, and `second_deadlock_stack=1` includes full stack traces for deadlock detection. Reload the systemd configuration with `systemctl --user daemon-reload` and start the service with `systemctl --user start stats-daemon.service`.

Monitor the TSan output log in real-time using `tail -f /tmp/tsan-stats-daemon.log.*`. Within seconds, ThreadSanitizer will report a data race on the `racy_counter` field, displaying the conflicting read and write operations with full stack traces pinpointing the source locations. The report shows two threads accessing `racy_counter` concurrently: one thread reading the current value inside the first lock acquisition, and another thread writing the incremented value after reacquiring the lock. The intermediate lock release creates a race window where another thread can interleave its own read-modify-write sequence, causing lost updates.

The TSan report format includes the memory address of the racy variable, the type of access (read vs. write), and the instruction pointers of both conflicting accesses. Cross-reference these addresses with the compiled binary using `llvm-symbolizer` to resolve instruction pointers to source lines: `llvm-symbolizer -e target/x86_64-unknown-linux-gnu/debug/stats-daemon <address>`. This confirms the exact line in `worker_thread()` responsible for the race, validating that TSan accurately detects the unsynchronized access despite the surrounding Mutex usage.

Fix the data race by removing the premature lock drop and ensuring the read-modify-write sequence remains within a single critical section. Modify the worker thread to increment `racy_counter` without releasing the lock between reading and writing:

```rust
// Corrected version: atomic read-modify-write
let mut stats_lock = stats.lock().unwrap();
stats_lock.atomic_counter.fetch_add(1, Ordering::Relaxed);
stats_lock.racy_counter += 1;  // Now safe: lock held throughout
```

Recompile with TSan and restart the service. The TSan log should now remain empty, confirming the race is eliminated. This validates TSan's efficacy for detecting subtle concurrency bugs that manifest only under specific thread interleavings.

Next, instrument the daemon with LeakSanitizer to detect memory leaks during service lifecycle operations. Modify the main function to deliberately leak heap memory by allocating a vector and leaking it with `std::mem::forget()`, preventing the Drop implementation from freeing the memory. Add this code before the worker thread loop:

```rust
// INTENTIONAL MEMORY LEAK for LSan detection
let leaked_vec = vec![0u8; 1024 * 1024];  // 1 MiB allocation
std::mem::forget(leaked_vec);
```

Compile with LeakSanitizer enabled: `RUSTFLAGS="-Z sanitizer=leak" cargo +nightly build --target x86_64-unknown-linux-gnu`. Update the systemd unit file to use the LSan-instrumented binary and configure LSan options:

```ini
Environment=LSAN_OPTIONS=log_path=/tmp/lsan-stats-daemon.log:verbosity=1:exitcode=0
```

The `exitcode=0` option prevents LSan from terminating the process with a non-zero exit code on leak detection, allowing systemd to treat the service as successfully stopped rather than failed. Reload systemd configuration and start the service. After startup completes, stop the service with `systemctl --user stop stats-daemon.service` to trigger LSan's leak report at process termination.

Examine the LSan log with `cat /tmp/lsan-stats-daemon.log.*`. The report lists detected memory leaks with allocation stack traces, showing a 1 MiB direct leak from the `vec![0u8; ...]` allocation in main. The stack trace includes the exact source location and the allocation function (`__rust_alloc`), providing a clear audit trail for debugging. LSan differentiates between "direct leaks" (memory with no surviving pointers) and "indirect leaks" (memory reachable only through leaked objects), helping diagnose complex leak chains.

Stress-test systemd's cgroup resource accounting by rapidly restarting the service in a loop, monitoring for memory accumulation in the systemd manager process or kernel cgroup structures. Write a shell script that cycles the service 1000 times while sampling cgroup memory usage: create `~/systemd-labs/cgroup-stress.sh`:

```bash
#!/bin/bash
# ~/systemd-labs/cgroup-stress.sh

SERVICE="stats-daemon.service"
ITERATIONS=1000
CGROUP_PATH="/sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/app.slice/$SERVICE"

echo "iteration,cgroup_memory_current,cgroup_memory_peak,systemd_rss_kb" > cgroup_stress_data.csv

for i in $(seq 1 $ITERATIONS); do
    systemctl --user restart "$SERVICE"
    sleep 0.5
    
    # Wait for service to enter active state
    while ! systemctl --user is-active --quiet "$SERVICE"; do
        sleep 0.1
    done
    
    # Sample cgroup memory
    if [ -f "$CGROUP_PATH/memory.current" ]; then
        MEM_CURRENT=$(cat "$CGROUP_PATH/memory.current")
        MEM_PEAK=$(cat "$CGROUP_PATH/memory.peak")
    else
        MEM_CURRENT=0
        MEM_PEAK=0
    fi
    
    # Sample systemd manager RSS
    SYSTEMD_PID=$(pgrep -u $(id -u) '^systemd$')
    SYSTEMD_RSS=$(ps -o rss= -p "$SYSTEMD_PID")
    
    echo "$i,$MEM_CURRENT,$MEM_PEAK,$SYSTEMD_RSS" >> cgroup_stress_data.csv
    
    systemctl --user stop "$SERVICE"
    sleep 0.2
done

echo "Stress test complete. Data written to cgroup_stress_data.csv"
```

Execute the script with `bash ~/systemd-labs/cgroup-stress.sh` and monitor system behavior using `htop` in a separate terminal. The script samples three metrics: `memory.current` (current cgroup RSS), `memory.peak` (historical high watermark), and the systemd manager's RSS. Under correct operation, these values should remain stable across iterations, with only transient spikes during service startup. If systemd or the kernel cgroup subsystem leaks memory, the systemd RSS will exhibit a monotonic increase, accumulating several hundred kilobytes per iteration.

Plot the time-series data using gnuplot to visualize memory trends. Create `~/systemd-labs/plot-cgroup-stress.gp`:

```gnuplot
set terminal png size 1200,800
set output 'cgroup_stress_plot.png'
set datafile separator ','
set xlabel 'Iteration'
set ylabel 'Memory (bytes / KB)'
set y2label 'Systemd RSS (KB)' tc lt 3
set ytics nomirror
set y2tics
set key top left
set grid

plot 'cgroup_stress_data.csv' using 1:2 with lines lw 2 title 'Cgroup memory.current' axes x1y1, \
     'cgroup_stress_data.csv' using 1:3 with lines lw 2 title 'Cgroup memory.peak' axes x1y1, \
     'cgroup_stress_data.csv' using 1:4 with lines lw 2 lc rgb 'red' title 'Systemd RSS' axes x1y2
```

Generate the plot with `gnuplot ~/systemd-labs/plot-cgroup-stress.gp`, producing `cgroup_stress_plot.png`. The plot should show stable memory usage for both the cgroup metrics and systemd RSS. Any upward trend in systemd RSS indicates a potential leak in systemd's service management logic, warranting further investigation with Valgrind or systemd's internal memory profiling.

Profile systemd's cgroup teardown logic using Valgrind to detect kernel-side memory leaks. Valgrind cannot instrument the systemd manager directly without breaking its operation, so instead analyze the service process itself under Valgrind supervision. Modify the stats-daemon unit file to launch the service under Valgrind's memcheck tool:

```ini
ExecStart=/usr/bin/valgrind --leak-check=full --log-file=/tmp/valgrind-stats-daemon.log /home/%u/systemd-labs/stats-daemon/target/x86_64-unknown-linux-gnu/debug/stats-daemon
```

Remove the TSan and LSan compilation flags, recompile without sanitizers using `cargo build`, then reload systemd configuration and restart the service. After startup, stop the service to trigger Valgrind's leak report. Examine the log with `less /tmp/valgrind-stats-daemon.log`, focusing on the "definitely lost" and "indirectly lost" leak categories. Valgrind's report includes allocation backtraces for all leaked blocks, enabling precise identification of the leak source.

Compare Valgrind's heap profiling with systemd's own memory pressure detection using PSI (Pressure Stall Information) metrics. Query the cgroup's memory pressure with `cat "$CGROUP_PATH/memory.pressure"`, which reports three pressure levels: `some` (partial stalls), `full` (complete stalls), and moving averages over 10s, 60s, and 300s windows. Under normal operation, memory pressure remains near zero. If the service allocates memory faster than the kernel can reclaim pages under the cgroup limit, the `some` pressure percentage increases, signaling memory contention.

Induce memory pressure by reducing the service's `MemoryMax` to 32M and adding a memory allocation stress loop to the Rust code:

```rust
// Allocate memory in a loop to trigger cgroup pressure
let mut allocations = Vec::new();
for _ in 0..100 {
    let big_vec = vec![0u8; 1024 * 1024];  // 1 MiB
    allocations.push(big_vec);
    thread::sleep(Duration::from_millis(100));
}
```

Restart the service and monitor `memory.pressure` in real-time: `watch -n 0.5 "cat $CGROUP_PATH/memory.pressure"`. The `some` pressure percentage should climb above 10%, and the `full` pressure may spike if allocations exceed the limit, triggering the OOM killer. Correlate the pressure metrics with systemd's journal logs using `journalctl --user -u stats-daemon.service`, which records OOM kill events as "memory cgroup out of memory" messages.

Verify that systemd correctly cleans up cgroup directories after service termination by checking for stale cgroup paths. After stopping the service, confirm the cgroup directory no longer exists: `ls $CGROUP_PATH` should return "No such file or directory". If the directory persists, systemd has failed to unmount the cgroup hierarchy, leaving orphaned kernel memory. This condition is detectable via `systemctl status` showing a "cgroup-empty: yes" field, indicating the cgroup is empty but not yet removed.

Finally, deploy bpftrace to instrument systemd's cgroup creation and destruction syscalls, measuring the frequency and latency of cgroup operations during the rapid restart stress test. Create `~/systemd-labs/cgroup-syscalls.bt`:

```c
// ~/systemd-labs/cgroup-syscalls.bt
tracepoint:syscalls:sys_enter_mkdir
/comm == "systemd"/
{
    @mkdir_start[tid] = nsecs;
    @mkdir_path[tid] = str(args->pathname);
}

tracepoint:syscalls:sys_exit_mkdir
/@mkdir_start[tid] && strcontains(@mkdir_path[tid], "cgroup")/
{
    $duration_us = (nsecs - @mkdir_start[tid]) / 1000;
    @mkdir_latency_us = hist($duration_us);
    delete(@mkdir_start[tid]);
    delete(@mkdir_path[tid]);
}

tracepoint:syscalls:sys_enter_rmdir
/comm == "systemd"/
{
    @rmdir_start[tid] = nsecs;
}

tracepoint:syscalls:sys_exit_rmdir
/@rmdir_start[tid]/
{
    $duration_us = (nsecs - @rmdir_start[tid]) / 1000;
    @rmdir_latency_us = hist($duration_us);
    delete(@rmdir_start[tid]);
}

interval:s:5
{
    print("=== Cgroup mkdir latency ===");
    print(@mkdir_latency_us);
    print("=== Cgroup rmdir latency ===");
    print(@rmdir_latency_us);
}
```

Run the eBPF program with `sudo bpftrace ~/systemd-labs/cgroup-syscalls.bt`, then execute the cgroup stress test in another terminal. The bpftrace output displays histograms of mkdir and rmdir latencies for systemd's cgroup operations. Under normal conditions, mkdir completes in 50-200 microseconds, and rmdir in 10-100 microseconds. Elevated latencies or increasing trends suggest kernel contention on the cgroup hierarchy lock, a known scalability bottleneck in older kernels predating cgroup v2 optimizations.

## Developer Cheat Sheet & Toolchain Checklist

**Systemd Configuration & State Inspection**
```bash
# Reload systemd user manager after unit file changes
systemctl --user daemon-reload

# Query unit file as parsed by systemd
systemctl --user cat <service>

# Show all unit properties (timestamps, PIDs, cgroup path)
systemctl --user show <service>

# Display dependency tree as directed graph
systemd-analyze --user dot <service> | dot -Tsvg -o output.svg

# Measure service activation latency
systemd-analyze --user critical-chain <service>

# List all failed units
systemctl --user --failed

# Inspect cgroup hierarchy
systemd-cgls --user

# Query cgroup resource usage
systemd-cgtop --user
```

**Performance Profiling & Hardware Counters**
```bash
# Profile cache behavior during command execution
perf stat -e cache-references,cache-misses,LLC-loads,LLC-load-misses <command>

# Record instruction pointer samples on cache misses
perf record -e cache-misses -c 1000 -g -p <PID> sleep 5

# Generate annotated disassembly with sample counts
perf annotate --stdio <binary>

# Measure memory bandwidth via uncore PMUs (Intel servers)
perf stat -e uncore_imc_0/cas_count_read/,uncore_imc_0/cas_count_write/ -a sleep 5

# Top-down microarchitecture analysis (Intel)
perf stat --topdown -a sleep 5

# Flamegraph generation from perf data
perf record -F 99 -g -p <PID> sleep 30
perf script | ~/FlameGraph/stackcollapse-perf.pl | ~/FlameGraph/flamegraph.pl > profile.svg
```

**ThreadSanitizer & LeakSanitizer with Rust**
```bash
# Install nightly Rust toolchain for sanitizers
rustup toolchain install nightly

# Compile with ThreadSanitizer
RUSTFLAGS="-Z sanitizer=thread" cargo +nightly build --target x86_64-unknown-linux-gnu

# Compile with LeakSanitizer
RUSTFLAGS="-Z sanitizer=leak" cargo +nightly build --target x86_64-unknown-linux-gnu

# Configure sanitizer runtime options via environment
export TSAN_OPTIONS="log_path=/tmp/tsan.log:halt_on_error=0:second_deadlock_stack=1"
export LSAN_OPTIONS="log_path=/tmp/lsan.log:verbosity=1:exitcode=0"

# Resolve instruction pointers to source lines
llvm-symbolizer -e <binary> <address>
```

**Cgroup v2 Resource Accounting**
```bash
# Verify cgroup v2 unified hierarchy
mount | grep cgroup2

# Query current memory usage
cat /sys/fs/cgroup/<slice>/<service>/memory.current

# Query historical memory peak
cat /sys/fs/cgroup/<slice>/<service>/memory.peak

# Monitor memory pressure (PSI metrics)
cat /sys/fs/cgroup/<slice>/<service>/memory.pressure

# Query CPU usage statistics
cat /sys/fs/cgroup/<slice>/<service>/cpu.stat

# Set memory limit (in bytes)
echo 67108864 > /sys/fs/cgroup/<slice>/<service>/memory.max

# Set CPU bandwidth limit (quota microseconds per period microseconds)
echo "50000 100000" > /sys/fs/cgroup/<slice>/<service>/cpu.max
```

**eBPF Tracing with bpftrace**
```bash
# Trace syscall latencies for specific process
bpftrace -e 'tracepoint:syscalls:sys_enter_* /comm == "systemd"/ { @start[tid] = nsecs; } tracepoint:syscalls:sys_exit_* /@start[tid]/ { @latency_us = hist((nsecs - @start[tid]) / 1000); delete(@start[tid]); }'

# Monitor cgroup mkdir/rmdir operations
bpftrace <script.bt>

# List available tracepoints
bpftrace -l 'tracepoint:*'

# List kprobes for kernel functions
bpftrace -l 'kprobe:*cgroup*'
```

**Systemd Journal Analysis**
```bash
# Follow service logs in real-time
journalctl --user -u <service> -f

# Query logs since last boot
journalctl --user -u <service> -b

# Filter by priority level
journalctl --user -u <service> -p err

# Show logs in JSON format for parsing
journalctl --user -u <service> -o json-pretty

# Export logs to file
journalctl --user -u <service> > service.log
```

**Memory Diagnostics with Valgrind**
```bash
# Full heap leak check with backtraces
valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes --log-file=valgrind.log <binary>

# Detect uninitialized memory reads
valgrind --track-origins=yes <binary>

# Massif heap profiler for allocation patterns
valgrind --tool=massif <binary>
ms_print massif.out.<pid>
```

**Stress Testing & Workload Generation**
```bash
# Generate cache pressure with memory streaming
gcc -O0 -o cache-pressure cache-pressure.c
for i in $(seq 1 $(nproc)); do ./cache-pressure & done

# Flush page cache and dentries
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'

# Monitor system load averages
uptime

# Display per-CPU utilization
mpstat -P ALL 1

# Monitor I/O wait and memory pressure
vmstat 1
```

**Checklist: Pre-Production Systemd Service Deployment**
- [ ] Unit file specifies `Type=notify` with sd_notify readiness signal
- [ ] `MemoryMax` and `CPUQuota` limits configured for resource isolation
- [ ] `Restart=on-failure` with exponential backoff via `RestartSec`
- [ ] Security hardening: `NoNewPrivileges=true`, `ProtectSystem=strict`, `PrivateTmp=true`
- [ ] Service compiled with TSan and LSan for race/leak detection
- [ ] Activation latency measured under cache pressure scenarios
- [ ] Cgroup memory accounting verified via rapid restart stress test
- [ ] Journal logs analyzed for OOM kills and timeout failures
- [ ] Dependency graph validated with `systemd-analyze dot`
- [ ] Service tested under PSI memory pressure with graceful degradation

**Critical File Paths**
- User unit directory: `~/.config/systemd/user/`
- User cgroup root: `/sys/fs/cgroup/user.slice/user-$UID.slice/user@$UID.service/`
- User journal: `~/.local/share/systemd/user/journal/` or `/var/log/journal/<machine-id>/user-$UID.journal`
- Systemd notify socket: `/run/user/$UID/systemd/notify`
- Perf output: `perf.data` (default), query with `perf report`
- TSan logs: Set via `TSAN_OPTIONS=log_path=<path>`
- LSan logs: Set via `LSAN_OPTIONS=log_path=<path>`
