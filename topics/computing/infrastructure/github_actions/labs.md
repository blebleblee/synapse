# Operational Verification Labs: GitHub Actions

## Objective & Environment Setup

GitHub Actions represents a distributed, event-driven continuous integration and deployment platform operating as a managed orchestration layer atop compute substrates spanning GitHub-hosted ephemeral runners and self-hosted persistent agents. The system architecture decouples workflow definition (declarative YAML manifests committed to `.github/workflows/`) from execution state managed by the Actions runtime controller, which schedules jobs onto runner fleets, provisions isolated execution environments, and streams logs through a pub-sub telemetry pipeline. Understanding GitHub Actions at the operational level requires treating it not as an abstract CI/CD abstraction but as a concrete distributed system subject to network partitions, resource exhaustion, credential rotation failures, and runner fleet scaling dynamics.

This laboratory guide grounds GitHub Actions verification in the diagnostic methodologies of infrastructure engineering: live state inspection through API introspection and runner telemetry, saturation profiling to characterize concurrency limits and cold-start latencies, and fault injection to validate recovery semantics under partial system failure. The exercises operate primarily through the GitHub CLI (`gh`), the Actions REST API, and direct runner host instrumentation when using self-hosted infrastructure. For GitHub-hosted runners, verification focuses on observable API state, workflow execution traces, and inferred scheduling behavior since the underlying compute substrate remains opaque. Self-hosted runner scenarios enable deeper instrumentation using `systemd` journal inspection, process tracing with `strace`, network flow analysis via `ss` and `tcpdump`, and CPU profiling with `perf`.

### Environment Prerequisites

Establish a GitHub repository with Actions enabled and administrative access to modify workflows, inspect run logs, and configure secrets. For hosted runner verification, no local infrastructure is required beyond the GitHub CLI and standard Unix diagnostic tools. Self-hosted runner exercises demand a Linux host (Ubuntu 22.04 LTS or equivalent) with root access for system-level instrumentation. Install the GitHub CLI via official package repositories rather than third-party distributions to ensure API compatibility and proper credential integration. The CLI must authenticate with a personal access token (classic or fine-grained) scoped to `repo`, `workflow`, and `admin:org` for comprehensive operational visibility.

Install the GitHub CLI and verify authentication state. On Debian-derived distributions, add the GitHub APT repository and install the `gh` package. After installation, authenticate interactively and validate that the CLI can retrieve repository metadata and workflow run history. The authentication flow exchanges an OAuth device code for a token stored in the system keyring, enabling subsequent CLI invocations to transparently sign API requests without embedding credentials in shell scripts or environment variables.

```bash
# Install GitHub CLI (Ubuntu/Debian)
sudo apt update
sudo apt install -y gh

# Authenticate with GitHub
gh auth login --web

# Verify authentication and API access
gh auth status
gh api user --jq '.login'

# Clone or create a test repository for workflow verification
gh repo clone your-org/actions-verification || \
  gh repo create actions-verification --public --clone

cd actions-verification
```

For self-hosted runner deployment, download the Actions runner package from the repository settings interface under "Actions > Runners > New self-hosted runner". The runner consists of a .NET Core application bundle that polls the GitHub API for queued jobs, downloads workflow artifacts, provisions isolated working directories, and executes job steps within child processes. The runner communicates exclusively over HTTPS to `api.github.com` and `pipelines.actions.githubusercontent.com`, with no inbound network requirements. Install the runner as a `systemd` service to enable automatic restarts, resource limits via cgroups, and centralized log aggregation through the journal.

```bash
# Download and configure self-hosted runner (run on target host)
mkdir ~/actions-runner && cd ~/actions-runner

# Retrieve registration token (expires in 1 hour)
RUNNER_TOKEN=$(gh api \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  /repos/your-org/actions-verification/actions/runners/registration-token \
  --jq '.token')

# Download runner package (x64 Linux)
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Configure runner with ephemeral mode for clean per-job execution
./config.sh --url https://github.com/your-org/actions-verification \
  --token ${RUNNER_TOKEN} \
  --name lab-runner-01 \
  --labels self-hosted,linux,x64,lab \
  --ephemeral

# Install as systemd service
sudo ./svc.sh install
sudo ./svc.sh start

# Verify runner registration
gh api /repos/your-org/actions-verification/actions/runners --jq '.runners[] | select(.name=="lab-runner-01")'
```

Prepare a baseline workflow manifest that exercises fundamental job scheduling, artifact handling, and matrix concurrency. This workflow serves as the instrumentation target for subsequent diagnostic exercises. The manifest defines multiple jobs with explicit dependencies, artifact uploads and downloads, parameterized matrix builds, and both successful and intentionally failing steps to populate the failure analysis pipeline.

Create `.github/workflows/baseline-verification.yml` with the following content:

```yaml
name: Baseline Verification Workflow

on:
  workflow_dispatch:
    inputs:
      matrix_size:
        description: 'Matrix parallelism factor'
        required: false
        default: '3'
        type: choice
        options:
          - '2'
          - '3'
          - '5'
          - '10'
      inject_failure:
        description: 'Inject step failure for fault testing'
        required: false
        default: 'false'
        type: boolean

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      build_time: ${{ steps.measure.outputs.duration }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Measure cold start latency
        id: measure
        run: |
          start_time=$(date +%s%3N)
          sleep 2
          end_time=$(date +%s%3N)
          duration=$((end_time - start_time))
          echo "duration=${duration}" >> $GITHUB_OUTPUT
          echo "Build duration: ${duration}ms"

      - name: Generate build artifact
        run: |
          mkdir -p artifacts
          echo "Build timestamp: $(date -Iseconds)" > artifacts/build-metadata.txt
          echo "Runner: ${{ runner.name }}" >> artifacts/build-metadata.txt
          echo "Workflow run: ${{ github.run_id }}" >> artifacts/build-metadata.txt
          dd if=/dev/urandom of=artifacts/payload.bin bs=1M count=10

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: artifacts/
          retention-days: 1

  test-matrix:
    needs: build
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test_id: ${{ fromJson(format('[{0}]', join(range(1, fromJson(github.event.inputs.matrix_size || '3') + 1), ','))) }}
      fail-fast: false
    steps:
      - name: Download build artifact
        uses: actions/download-artifact@v4
        with:
          name: build-output
          path: ./downloaded-artifacts

      - name: Verify artifact integrity
        run: |
          ls -lh downloaded-artifacts/
          sha256sum downloaded-artifacts/payload.bin
          cat downloaded-artifacts/build-metadata.txt

      - name: Execute test suite (matrix ${{ matrix.test_id }})
        run: |
          echo "Running test suite instance ${{ matrix.test_id }}"
          sleep $((RANDOM % 10 + 5))
          
          if [[ "${{ github.event.inputs.inject_failure }}" == "true" && ${{ matrix.test_id }} -eq 2 ]]; then
            echo "Injecting failure in matrix job 2"
            exit 1
          fi
          
          echo "Test suite ${{ matrix.test_id }} completed successfully"

  deploy:
    needs: test-matrix
    runs-on: ubuntu-latest
    if: success()
    steps:
      - name: Simulate deployment
        run: |
          echo "Deploying build from run ${{ github.run_id }}"
          echo "Build duration from upstream: ${{ needs.build.outputs.build_time }}ms"
          sleep 3
          echo "Deployment complete"

  cleanup:
    needs: [build, test-matrix, deploy]
    runs-on: ubuntu-latest
    if: always()
    steps:
      - name: Cleanup artifacts
        run: |
          echo "Cleanup job always runs regardless of upstream status"
          echo "Build status: ${{ needs.build.result }}"
          echo "Test matrix status: ${{ needs.test-matrix.result }}"
          echo "Deploy status: ${{ needs.deploy.result }}"
```

Commit this workflow manifest and trigger an initial execution to establish baseline telemetry. The workflow dispatch event allows parameterized invocation through the CLI or web interface, enabling controlled experimentation with matrix sizes and fault injection without modifying the YAML definition.

```bash
git add .github/workflows/baseline-verification.yml
git commit -m "Add baseline verification workflow for operational testing"
git push

# Trigger workflow with default parameters
gh workflow run baseline-verification.yml

# Monitor run status in real-time
gh run watch
```

## Exercise 1: Live State & Internal Subsystem Inspection

GitHub Actions execution state resides in a distributed control plane that reconciles desired workflow definitions against actual job execution status across a fleet of ephemeral or persistent runners. The primary diagnostic surface for this system is the Actions REST API, which exposes workflow runs, job states, step logs, and artifact metadata as versioned resources with monotonically increasing identifiers. Effective live state inspection requires understanding the state machine transitions that govern workflow lifecycle: `queued` → `in_progress` → `completed` (with conclusion `success`, `failure`, `cancelled`, or `skipped`). Each workflow run spawns one or more jobs, and each job contains an ordered sequence of steps that execute atomically within a single runner allocation.

Begin by enumerating recent workflow runs and extracting their execution timelines. The API returns run metadata including queue timestamps, start timestamps, completion timestamps, and conclusion status. Computing the delta between queue and start timestamps reveals runner acquisition latency, a critical metric when diagnosing capacity exhaustion or runner connectivity issues. For GitHub-hosted runners, queue latencies under 5 seconds indicate healthy fleet capacity, while sustained latencies exceeding 30 seconds suggest demand spikes or regional availability constraints.

```bash
# List recent workflow runs with timing metadata
gh api /repos/your-org/actions-verification/actions/runs \
  --jq '.workflow_runs[] | {
    id: .id,
    name: .name,
    status: .status,
    conclusion: .conclusion,
    queued: .run_started_at,
    started: .updated_at,
    queue_latency: (((.updated_at | fromdateiso8601) - (.run_started_at | fromdateiso8601)) | tostring + "s")
  }' | head -20

# Retrieve detailed job breakdown for a specific run
LATEST_RUN_ID=$(gh run list --workflow=baseline-verification.yml --limit=1 --json databaseId --jq '.[0].databaseId')

gh api /repos/your-org/actions-verification/actions/runs/${LATEST_RUN_ID}/jobs \
  --jq '.jobs[] | {
    job_name: .name,
    status: .status,
    conclusion: .conclusion,
    started_at: .started_at,
    completed_at: .completed_at,
    duration_seconds: (((.completed_at | fromdateiso8601) - (.started_at | fromdateiso8601)) | floor),
    runner_name: .runner_name,
    runner_id: .runner_id
  }'
```

Drill into individual job logs to reconstruct step-level execution timelines. The GitHub CLI provides a `gh run view` command that streams logs with timestamps, enabling precise chronological analysis. Extract log lines with timestamp prefixes to compute per-step durations and identify bottlenecks such as excessive checkout times, artifact transfer delays, or pathological step scripts with unbounded execution time.

```bash
# Stream logs for the most recent run with timestamps
gh run view ${LATEST_RUN_ID} --log

# Extract step durations from timestamped logs (requires log download)
gh api /repos/your-org/actions-verification/actions/runs/${LATEST_RUN_ID}/logs > run-${LATEST_RUN_ID}-logs.zip
unzip -q run-${LATEST_RUN_ID}-logs.zip -d run-logs/

# Parse step timestamps from log files (example: build job)
grep -h "^20[0-9][0-9]-" run-logs/build/*.txt | \
  awk '{print $1, $2, $NF}' | \
  sort | \
  awk 'NR>1 {
    split($1, d, "-"); split($2, t, ":");
    ts = mktime(d[1] " " d[2] " " d[3] " " t[1] " " t[2] " " t[3]);
    if (prev_ts != "") print "Step duration:", ts - prev_ts, "seconds";
    prev_ts = ts;
  }'
```

For self-hosted runners, augment API-level inspection with direct host telemetry. The runner process executes as a long-lived daemon that spawns child worker processes for each assigned job. Inspect runner state by querying the systemd service status, examining process trees with `ps`, and analyzing journal logs for connection errors, job assignment events, and cleanup operations. The runner maintains a local cache directory structure under `_work/` that accumulates artifacts, repository checkouts, and temporary files between jobs unless configured in ephemeral mode.

```bash
# Inspect self-hosted runner systemd service state
sudo systemctl status actions.runner.your-org-actions-verification.lab-runner-01.service

# Examine runner process tree and resource usage
ps aux | grep Runner.Listener
pstree -p $(pgrep -f Runner.Listener)

# Analyze runner journal logs for job assignments and errors
sudo journalctl -u actions.runner.your-org-actions-verification.lab-runner-01.service \
  --since "1 hour ago" \
  --no-pager | \
  grep -E "(Job|Workflow|Error|Exception)"

# Inspect runner working directory structure
sudo ls -lh ~/actions-runner/_work/
sudo du -sh ~/actions-runner/_work/*
```

The runner communicates with GitHub over HTTPS using long-polling to retrieve job assignments. Monitor active network connections to diagnose connectivity issues or proxy misconfigurations. The runner establishes persistent connections to `api.github.com` (HTTPS/443) and `pipelines.actions.githubusercontent.com` (HTTPS/443) for job polling and artifact streaming respectively. Use `ss` to enumerate active sockets and confirm TLS session establishment.

```bash
# Monitor runner network connections in real-time
watch -n 2 'sudo ss -tnp | grep -E "(Runner|Listener)"'

# Capture detailed socket statistics including congestion control state
sudo ss -tipmn | grep -A 10 ":443"

# Verify DNS resolution for GitHub API endpoints
dig +short api.github.com
dig +short pipelines.actions.githubusercontent.com

# Test HTTPS connectivity with timing breakdown
curl -w "@-" -o /dev/null -s https://api.github.com <<'EOF'
    time_namelookup: %{time_namelookup}s
       time_connect: %{time_connect}s
    time_appconnect: %{time_appconnect}s
   time_pretransfer: %{time_pretransfer}s
      time_redirect: %{time_redirect}s
 time_starttransfer: %{time_starttransfer}s
                    ----------
         time_total: %{time_total}s
EOF
```

Artifact storage represents a distinct subsystem within the Actions architecture, decoupled from the job execution plane. Artifacts uploaded via `actions/upload-artifact` are chunked, compressed, and transmitted to blob storage with eventual consistency guarantees. Verify artifact integrity by downloading uploaded artifacts and comparing checksums against local originals. The artifact retention policy governs automatic deletion after a configured period (default 90 days, configurable per repository), but artifacts can be manually purged to conserve storage quotas.

```bash
# List artifacts for a specific workflow run
gh api /repos/your-org/actions-verification/actions/runs/${LATEST_RUN_ID}/artifacts \
  --jq '.artifacts[] | {
    name: .name,
    size_bytes: .size_in_bytes,
    created_at: .created_at,
    expires_at: .expires_at,
    download_url: .archive_download_url
  }'

# Download artifact for integrity verification
ARTIFACT_ID=$(gh api /repos/your-org/actions-verification/actions/runs/${LATEST_RUN_ID}/artifacts \
  --jq '.artifacts[0].id')

gh api /repos/your-org/actions-verification/actions/artifacts/${ARTIFACT_ID}/zip > artifact.zip
unzip -q artifact.zip -d artifact-contents/
ls -lh artifact-contents/
sha256sum artifact-contents/payload.bin
```

Inspect workflow run annotations and job annotations to identify warnings, errors, and deprecation notices surfaced by the Actions runtime. Annotations are structured messages attached to specific lines in workflow files or log outputs, indicating configuration issues, deprecated action versions, or security vulnerabilities in dependencies. The API exposes annotations as a filterable collection enabling automated compliance scanning.

```bash
# Retrieve annotations for a workflow run
gh api /repos/your-org/actions-verification/actions/runs/${LATEST_RUN_ID}/annotations \
  --jq '.[] | {
    level: .annotation_level,
    message: .message,
    path: .path,
    start_line: .start_line,
    end_line: .end_line
  }'

# Filter critical and error-level annotations
gh api /repos/your-org/actions-verification/actions/runs/${LATEST_RUN_ID}/annotations \
  --jq '.[] | select(.annotation_level == "failure" or .annotation_level == "error")'
```

Workflow concurrency controls prevent multiple runs of the same workflow from executing simultaneously when configured with a `concurrency` key. Inspect the concurrency group assignments and pending cancellations to diagnose unexpected queue behavior or orphaned runs. The runtime applies concurrency limits at the repository or workflow level, automatically cancelling in-progress runs when new commits trigger the same workflow group.

```bash
# Inspect pending and queued runs for concurrency analysis
gh api /repos/your-org/actions-verification/actions/runs \
  --jq '.workflow_runs[] | select(.status == "queued" or .status == "in_progress") | {
    id: .id,
    name: .name,
    status: .status,
    event: .event,
    branch: .head_branch,
    queued_at: .run_started_at
  }'

# Manually cancel a queued or in-progress run
QUEUED_RUN_ID=<run_id_from_above>
gh run cancel ${QUEUED_RUN_ID}
gh run view ${QUEUED_RUN_ID} --json status,conclusion
```

## Exercise 2: Benchmarking & Saturation Profiling

GitHub Actions performance characteristics depend on multiple subsystem interactions: runner acquisition latency from the scheduler, artifact storage throughput to blob backends, network I/O to external services, and CPU/memory utilization within job execution containers. Systematic benchmarking isolates each dimension to establish baseline performance envelopes and identify saturation points where additional concurrency yields diminishing returns or triggers throttling mechanisms.

Begin by characterizing runner cold-start latency, defined as the interval between workflow trigger and first step execution. For GitHub-hosted runners, cold-start encompasses queue wait time, VM provisioning, image pull, and runtime initialization. Self-hosted runners exhibit lower latency for subsequent jobs when persistent but incur similar startup costs when configured in ephemeral mode. Measure cold-start by triggering workflows with minimal step payloads and extracting queue-to-start deltas from API timestamps.

Create a minimal benchmark workflow that executes a no-op step and immediately terminates:

```yaml
name: Cold Start Benchmark

on:
  workflow_dispatch:

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - name: Timestamp checkpoint
        run: echo "Execution start at $(date -Iseconds)"
```

Trigger this workflow repeatedly and collect timing statistics:

```bash
# Function to trigger workflow and measure cold-start latency
benchmark_cold_start() {
  local run_id
  
  # Trigger workflow
  gh workflow run cold-start-benchmark.yml
  sleep 2  # Allow API propagation
  
  # Get most recent run ID
  run_id=$(gh run list --workflow=cold-start-benchmark.yml --limit=1 --json databaseId --jq '.[0].databaseId')
  
  # Wait for completion
  gh run watch ${run_id} --exit-status > /dev/null 2>&1
  
  # Extract timing data
  gh api /repos/your-org/actions-verification/actions/runs/${run_id} \
    --jq '{
      queued: .run_started_at,
      started: .updated_at,
      cold_start_ms: (((.updated_at | fromdateiso8601) - (.run_started_at | fromdateiso8601)) * 1000 | floor)
    }'
}

# Run 20 iterations and compute statistics
for i in {1..20}; do
  echo "Iteration $i:"
  benchmark_cold_start
  sleep 10  # Rate limit between triggers
done > cold_start_samples.json

# Compute statistics (requires jq and basic stats tools)
jq -s 'map(.cold_start_ms) | {
  min: min,
  max: max,
  mean: (add / length),
  median: (sort | if length % 2 == 0 then (.[length/2 - 1] + .[length/2]) / 2 else .[length/2] end)
}' cold_start_samples.json
```

Artifact transfer throughput governs the maximum sustainable rate of data movement between jobs. Benchmark artifact upload and download performance by generating payloads of varying sizes and measuring transfer durations. The Actions artifact service implements client-side chunking with parallel uploads, achieving multi-gigabit throughput under ideal network conditions but degrading under latency or packet loss.

Extend the baseline workflow to parameterize artifact size:

```yaml
name: Artifact Throughput Benchmark

on:
  workflow_dispatch:
    inputs:
      artifact_size_mb:
        description: 'Artifact size in MB'
        required: true
        default: '100'
        type: string

jobs:
  upload:
    runs-on: ubuntu-latest
    steps:
      - name: Generate artifact
        run: |
          mkdir -p artifact
          dd if=/dev/urandom of=artifact/payload.bin bs=1M count=${{ github.event.inputs.artifact_size_mb }} status=progress
          sha256sum artifact/payload.bin > artifact/checksum.txt

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: throughput-test-${{ github.run_id }}
          path: artifact/

  download:
    needs: upload
    runs-on: ubuntu-latest
    steps:
      - name: Download artifact
        uses: actions/download-artifact@v4
        with:
          name: throughput-test-${{ github.run_id }}
          path: ./downloaded

      - name: Verify integrity
        run: |
          cd downloaded
          sha256sum -c checksum.txt
```

Execute this workflow with progressively larger payloads and extract per-job durations:

```bash
# Benchmark artifact throughput across size spectrum
for size in 10 50 100 500 1000; do
  echo "Testing ${size}MB artifact..."
  
  gh workflow run artifact-throughput-benchmark.yml \
    --field artifact_size_mb=${size}
  
  sleep 5
  run_id=$(gh run list --workflow=artifact-throughput-benchmark.yml --limit=1 --json databaseId --jq '.[0].databaseId')
  
  gh run watch ${run_id} --exit-status
  
  # Extract job durations
  gh api /repos/your-org/actions-verification/actions/runs/${run_id}/jobs \
    --jq --arg size "${size}" '.jobs[] | {
      size_mb: $size,
      job: .name,
      duration_s: (((.completed_at | fromdateiso8601) - (.started_at | fromdateiso8601)) | floor)
    }'
  
  sleep 30  # Cooling period between tests
done > artifact_throughput_results.json

# Compute throughput metrics
jq -s 'group_by(.job) | map({
  job: .[0].job,
  samples: map({size_mb: (.size_mb | tonumber), duration_s: .duration_s, throughput_mbps: ((.size_mb | tonumber) * 8 / .duration_s)}),
  mean_throughput_mbps: (map(.throughput_mbps) | add / length)
})' artifact_throughput_results.json
```

Matrix concurrency saturation testing reveals the effective parallelism limits imposed by runner availability and repository concurrency quotas. GitHub enforces per-repository and per-organization concurrency limits that throttle job scheduling when demand exceeds allocated capacity. For hosted runners, the default concurrency limit is 20 jobs per repository, while self-hosted runners have no intrinsic limit beyond physical host capacity.

Trigger workflows with progressively larger matrix dimensions and observe queue behavior:

```bash
# Saturation test: trigger workflow with large matrix
for matrix_size in 5 10 20 40 80; do
  echo "Testing matrix size: ${matrix_size}"
  
  gh workflow run baseline-verification.yml \
    --field matrix_size=${matrix_size}
  
  sleep 5
  run_id=$(gh run list --workflow=baseline-verification.yml --limit=1 --json databaseId --jq '.[0].databaseId')
  
  # Monitor job state transitions in real-time
  watch -n 5 "gh api /repos/your-org/actions-verification/actions/runs/${run_id}/jobs \
    --jq '.jobs | group_by(.status) | map({status: .[0].status, count: length})'"
  
  gh run watch ${run_id} --exit-status
  
  # Analyze queue wait times
  gh api /repos/your-org/actions-verification/actions/runs/${run_id}/jobs \
    --jq --arg matrix_size "${matrix_size}" '.jobs[] | {
      matrix_size: $matrix_size,
      job_name: .name,
      queue_wait_s: (((.started_at | fromdateiso8601) - (.created_at | fromdateiso8601)) | floor)
    }'
  
  sleep 60
done > matrix_saturation_results.json

# Identify saturation point where queue wait times spike
jq -s 'group_by(.matrix_size) | map({
  matrix_size: .[0].matrix_size,
  mean_queue_wait_s: (map(.queue_wait_s) | add / length),
  max_queue_wait_s: (map(.queue_wait_s) | max)
})' matrix_saturation_results.json
```

For self-hosted runners, profile CPU and memory utilization during job execution to identify resource bottlenecks. The runner process spawns child worker processes that execute job steps, with resource limits inherited from the parent systemd service. Use `perf` to sample CPU activity and `systemd-cgtop` to monitor cgroup resource accounting in real-time.

```bash
# Profile self-hosted runner CPU utilization during job execution
# Trigger a CPU-intensive workflow first
cat <<'EOF' > .github/workflows/cpu-stress.yml
name: CPU Stress Test

on:
  workflow_dispatch:

jobs:
  stress:
    runs-on: self-hosted
    steps:
      - name: CPU burn
        run: |
          stress-ng --cpu $(nproc) --timeout 60s --metrics
EOF

git add .github/workflows/cpu-stress.yml
git commit -m "Add CPU stress workflow"
git push

gh workflow run cpu-stress.yml
sleep 5

# Capture perf profile on runner host
RUNNER_PID=$(pgrep -f Runner.Listener)
sudo perf record -F 99 -p ${RUNNER_PID} -g -- sleep 30
sudo perf report --stdio --sort comm,dso,symbol | head -50

# Monitor cgroup resource usage
sudo systemd-cgtop -n 1 --depth=3 | grep actions.runner
```

Network I/O profiling isolates bandwidth consumption patterns during artifact transfers and external API calls. Use `tcpdump` to capture packets during a workflow run, then analyze traffic patterns with `tshark` or `wireshark`. Filter for TLS handshakes to GitHub domains and measure payload sizes to distinguish control-plane metadata from data-plane artifact transfers.

```bash
# Capture network traffic during workflow execution
sudo tcpdump -i any -w actions-traffic.pcap 'host api.github.com or host pipelines.actions.githubusercontent.com' &
TCPDUMP_PID=$!

# Trigger workflow with large artifact
gh workflow run artifact-throughput-benchmark.yml --field artifact_size_mb=500
sleep 5
run_id=$(gh run list --workflow=artifact-throughput-benchmark.yml --limit=1 --json databaseId --jq '.[0].databaseId')
gh run watch ${run_id} --exit-status

# Stop capture
sudo kill -INT ${TCPDUMP_PID}

# Analyze captured traffic
tshark -r actions-traffic.pcap -q -z io,stat,1,"SUM(frame.len)frame.len"
tshark -r actions-traffic.pcap -q -z conv,tcp
```

## Exercise 3: Fault Injection & Recovery Analysis

GitHub Actions resilience depends on graceful degradation under partial failures: runner disconnections, network timeouts, artifact corruption, and transient API errors. Systematic fault injection validates recovery semantics and exposes hidden assumptions in workflow definitions such as missing retry logic, unbounded resource consumption, or silent data loss.

Begin by injecting deliberate step failures to verify job-level error propagation and workflow-level failure handling. The baseline workflow includes an optional failure injection parameter that causes a specific matrix job to exit with non-zero status. Trigger this scenario and observe the impact on dependent jobs and the overall workflow conclusion.

```bash
# Inject step failure in matrix job 2
gh workflow run baseline-verification.yml \
  --field matrix_size=5 \
  --field inject_failure=true

sleep 5
run_id=$(gh run list --workflow=baseline-verification.yml --limit=1 --json databaseId --jq '.[0].databaseId')

# Monitor job state transitions
gh run watch ${run_id}

# Analyze failure propagation
gh api /repos/your-org/actions-verification/actions/runs/${run_id}/jobs \
  --jq '.jobs[] | {
    name: .name,
    status: .status,
    conclusion: .conclusion,
    steps: [.steps[] | select(.conclusion == "failure") | {name: .name, conclusion: .conclusion}]
  }'

# Verify cleanup job executed despite upstream failures
gh api /repos/your-org/actions-verification/actions/runs/${run_id}/jobs \
  --jq '.jobs[] | select(.name == "cleanup") | {
    name: .name,
    conclusion: .conclusion,
    dependency_results: [.steps[] | select(.name == "Cleanup artifacts")]
  }'
```

Simulate runner disconnection by forcibly terminating the self-hosted runner process during active job execution. The Actions runtime detects runner heartbeat failures and automatically re-queues the job for assignment to another healthy runner. This recovery mechanism ensures eventual consistency but does not preserve partial step progress, requiring idempotent step implementations to tolerate restarts.

```bash
# Trigger long-running workflow on self-hosted runner
cat <<'EOF' > .github/workflows/runner-disconnect-test.yml
name: Runner Disconnect Resilience

on:
  workflow_dispatch:

jobs:
  long-running:
    runs-on: self-hosted
    steps:
      - name: Phase 1
        run: |
          echo "Starting phase 1"
          sleep 30
          echo "Phase 1 complete"

      - name: Phase 2
        run: |
          echo "Starting phase 2"
          sleep 30
          echo "Phase 2 complete"

      - name: Phase 3
        run: |
          echo "Starting phase 3"
          sleep 30
          echo "Phase 3 complete"
EOF

git add .github/workflows/runner-disconnect-test.yml
git commit -m "Add runner disconnect test workflow"
git push

gh workflow run runner-disconnect-test.yml
sleep 5
run_id=$(gh run list --workflow=runner-disconnect-test.yml --limit=1 --json databaseId --jq '.[0].databaseId')

# Wait for job to reach Phase 2, then kill runner process
sleep 40
RUNNER_PID=$(pgrep -f Runner.Listener)
sudo kill -9 ${RUNNER_PID}

# Monitor job re-queue and re-assignment
watch -n 2 "gh api /repos/your-org/actions-verification/actions/runs/${run_id}/jobs \
  --jq '.jobs[] | {status: .status, conclusion: .conclusion, runner_name: .runner_name}'"

# Restart runner and observe job completion
sudo systemctl start actions.runner.your-org-actions-verification.lab-runner-01.service
gh run watch ${run_id}
```

Artifact corruption scenarios validate checksum verification and retry logic. Manually corrupt an uploaded artifact and trigger a downstream job that attempts to download and verify it. The artifact download action implements automatic retry with exponential backoff for transient failures but does not detect silent data corruption without explicit checksum validation in workflow steps.

```bash
# Upload artifact, manually corrupt it, then attempt download
cat <<'EOF' > .github/workflows/artifact-corruption-test.yml
name: Artifact Corruption Test

on:
  workflow_dispatch:

jobs:
  upload:
    runs-on: ubuntu-latest
    steps:
      - name: Generate artifact with checksum
        run: |
          mkdir artifact
          dd if=/dev/urandom of=artifact/data.bin bs=1M count=50
          sha256sum artifact/data.bin > artifact/checksum.txt

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: corruption-test-${{ github.run_id }}
          path: artifact/

  verify:
    needs: upload
    runs-on: ubuntu-latest
    steps:
      - name: Download artifact
        uses: actions/download-artifact@v4
        with:
          name: corruption-test-${{ github.run_id }}
          path: ./downloaded

      - name: Verify checksum
        run: |
          cd downloaded
          sha256sum -c checksum.txt
EOF

git add .github/workflows/artifact-corruption-test.yml
git commit -m "Add artifact corruption test"
git push

# This test validates that checksum verification catches corruption
# Manual corruption requires API manipulation beyond CLI scope
# Instead, demonstrate checksum verification with intentional mismatch

gh workflow run artifact-corruption-test.yml
run_id=$(gh run list --workflow=artifact-corruption-test.yml --limit=1 --json databaseId --jq '.[0].databaseId')
gh run watch ${run_id}
```

Network partition simulation for self-hosted runners validates retry behavior and timeout handling. Use `iptables` to temporarily block outbound HTTPS connections to GitHub API endpoints, then observe runner reconnection attempts and job assignment backoff.

```bash
# Block GitHub API connectivity
sudo iptables -A OUTPUT -d api.github.com -j DROP
sudo iptables -A OUTPUT -d pipelines.actions.githubusercontent.com -j DROP

# Monitor runner journal for connection failures
sudo journalctl -u actions.runner.your-org-actions-verification.lab-runner-01.service -f &
JOURNAL_PID=$!

# Wait 2 minutes to observe retry attempts
sleep 120

# Restore connectivity
sudo iptables -D OUTPUT -d api.github.com -j DROP
sudo iptables -D OUTPUT -d pipelines.actions.githubusercontent.com -j DROP

# Stop journal monitoring
kill ${JOURNAL_PID}

# Verify runner reconnected
gh api /repos/your-org/actions-verification/actions/runners \
  --jq '.runners[] | select(.name=="lab-runner-01") | {name: .name, status: .status}'
```

Credential rotation failures represent a common operational failure mode where expired or revoked personal access tokens prevent workflow execution. Simulate this by temporarily revoking the runner registration token and observing the impact on job assignments. The runner will fail to poll for new jobs and eventually mark itself offline, requiring manual re-registration.

```bash
# List current runners and their status
gh api /repos/your-org/actions-verification/actions/runners \
  --jq '.runners[] | {id: .id, name: .name, status: .status, labels: .labels}'

# Remove runner registration (simulates token revocation)
RUNNER_ID=$(gh api /repos/your-org/actions-verification/actions/runners \
  --jq '.runners[] | select(.name=="lab-runner-01") | .id')

gh api --method DELETE /repos/your-org/actions-verification/actions/runners/${RUNNER_ID}

# Observe runner service failure
sudo systemctl status actions.runner.your-org-actions-verification.lab-runner-01.service

# Trigger workflow and observe job queuing without runner
gh workflow run baseline-verification.yml
sleep 5
run_id=$(gh run list --workflow=baseline-verification.yml --limit=1 --json databaseId --jq '.[0].databaseId')

gh api /repos/your-org/actions-verification/actions/runs/${run_id}/jobs \
  --jq '.jobs[] | {name: .name, status: .status, runner_name: .runner_name}'

# Re-register runner with new token
cd ~/actions-runner
RUNNER_TOKEN=$(gh api \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  /repos/your-org/actions-verification/actions/runners/registration-token \
  --jq '.token')

./config.sh --url https://github.com/your-org/actions-verification \
  --token ${RUNNER_TOKEN} \
  --name lab-runner-01 \
  --labels self-hosted,linux,x64,lab \
  --ephemeral \
  --replace

sudo ./svc.sh start
```

## Diagnostic Cheat Sheet & Verification Checklist

This reference consolidates the essential diagnostic commands and verification procedures for rapid troubleshooting of GitHub Actions workflows, runner infrastructure, and artifact pipelines.

### Workflow State Inspection

```bash
# List recent runs with status
gh run list --workflow=<workflow-name> --limit=20

# Watch run in real-time
gh run watch <run-id>

# View complete logs
gh run view <run-id> --log

# Download logs for offline analysis
gh api /repos/<owner>/<repo>/actions/runs/<run-id>/logs > logs.zip

# Inspect job breakdown
gh api /repos/<owner>/<repo>/actions/runs/<run-id>/jobs \
  --jq '.jobs[] | {name: .name, status: .status, conclusion: .conclusion, duration_s: (((.completed_at | fromdateiso8601) - (.started_at | fromdateiso8601)) | floor)}'

# Check for annotations (errors/warnings)
gh api /repos/<owner>/<repo>/actions/runs/<run-id>/annotations
```

### Runner Diagnostics

```bash
# List registered runners
gh api /repos/<owner>/<repo>/actions/runners \
  --jq '.runners[] | {id: .id, name: .name, status: .status, busy: .busy, labels: [.labels[].name]}'

# Self-hosted runner service status
sudo systemctl status actions.runner.<org>-<repo>.<runner-name>.service

# Runner process tree and resource usage
ps aux | grep Runner.Listener
pstree -p $(pgrep -f Runner.Listener)

# Runner journal logs
sudo journalctl -u actions.runner.<org>-<repo>.<runner-name>.service --since "1 hour ago"

# Network connectivity check
sudo ss -tnp | grep Runner
curl -I https://api.github.com
curl -I https://pipelines.actions.githubusercontent.com
```

### Performance Profiling

```bash
# Cold-start latency measurement
gh api /repos/<owner>/<repo>/actions/runs/<run-id> \
  --jq '{queued: .run_started_at, started: .updated_at, cold_start_ms: (((.updated_at | fromdateiso8601) - (.run_started_at | fromdateiso8601)) * 1000 | floor)}'

# Job duration breakdown
gh api /repos/<owner>/<repo>/actions/runs/<run-id>/jobs \
  --jq '.jobs[] | {job: .name, duration_s: (((.completed_at | fromdateiso8601) - (.started_at | fromdateiso8601)) | floor)}'

# Artifact upload/download throughput
# (measure via job step timestamps in logs)

# CPU profiling (self-hosted runner)
sudo perf record -F 99 -p $(pgrep -f Runner.Listener) -g -- sleep 30
sudo perf report --stdio

# Memory usage
sudo systemd-cgtop -n 1 | grep actions.runner

# Network throughput
sudo tcpdump -i any -w capture.pcap 'host api.github.com or host pipelines.actions.githubusercontent.com'
tshark -r capture.pcap -q -z io,stat,1
```

### Artifact Management

```bash
# List artifacts for a run
gh api /repos/<owner>/<repo>/actions/runs/<run-id>/artifacts \
  --jq '.artifacts[] | {name: .name, size_mb: (.size_in_bytes / 1048576 | floor), expires_at: .expires_at}'

# Download artifact
gh api /repos/<owner>/<repo>/actions/artifacts/<artifact-id>/zip > artifact.zip

# Delete artifact
gh api --method DELETE /repos/<owner>/<repo>/actions/artifacts/<artifact-id>

# Check repository storage quota
gh api /repos/<owner>/<repo>/actions/cache/usage
```

### Fault Injection Scenarios

```bash
# Inject step failure
gh workflow run <workflow> --field inject_failure=true

# Kill runner mid-job
sudo kill -9 $(pgrep -f Runner.Listener)

# Block GitHub API connectivity
sudo iptables -A OUTPUT -d api.github.com -j DROP
sudo iptables -D OUTPUT -d api.github.com -j DROP  # restore

# Remove runner registration
gh api --method DELETE /repos/<owner>/<repo>/actions/runners/<runner-id>

# Cancel in-progress run
gh run cancel <run-id>
```

### Verification Checklist

**Pre-Deployment Validation:**
- [ ] Workflow YAML syntax valid (`yamllint .github/workflows/*.yml`)
- [ ] Required secrets configured in repository settings
- [ ] Runner labels match workflow `runs-on` selectors
- [ ] Artifact retention policy aligns with compliance requirements
- [ ] Concurrency groups prevent overlapping deployments
- [ ] Matrix dimensions do not exceed runner capacity

**Post-Execution Verification:**
- [ ] All jobs reached expected conclusion (`success`, `failure`, `cancelled`)
- [ ] Cleanup jobs executed regardless of upstream failures
- [ ] Artifacts uploaded successfully with correct retention
- [ ] Step durations within expected performance envelopes
- [ ] No critical annotations or security warnings
- [ ] Runner logs contain no connection errors or OOM events

**Operational Health Indicators:**
- [ ] Cold-start latency < 10s for hosted runners
- [ ] Queue wait time < 5s under normal load
- [ ] Artifact upload throughput > 50 Mbps
- [ ] Runner CPU utilization < 80% sustained
- [ ] Runner memory usage < 90% of cgroup limit
- [ ] Zero job re-queue events in past 24 hours

This laboratory methodology establishes a systematic operational discipline for GitHub Actions infrastructure, grounding abstract workflow definitions in concrete distributed system behaviors observable through API telemetry, runner instrumentation, and controlled fault injection. Mastery requires iterative practice: trigger workflows, extract telemetry, hypothesize failure modes, inject faults, and verify recovery semantics until the system's state machine transitions become intuitive and debuggable under production load.
