# Operational Verification Labs: Google GKE

## Objective & Environment Setup

Google Kubernetes Engine represents Google Cloud's managed Kubernetes offering, abstracting control plane operations while exposing the full Kubernetes API surface and underlying GCE virtual machine infrastructure. These operational verification labs ground GKE cluster diagnostics in the concrete reality of Linux kernel subsystems, container runtime internals, and distributed state machine reconciliation. The practitioner will instrument live clusters using kubectl for API server queries, crictl for direct containerd runtime inspection, tcpdump and ss for network socket state tracing, perf for CPU profiling, and etcdctl for distributed consensus verification when API server access permits.

Before executing these exercises, provision a GKE cluster in a Google Cloud project with sufficient IAM permissions to create node pools, configure networking, and SSH into worker nodes. The cluster should span at least three nodes across a single zone or multiple zones within a region to observe scheduling distribution, network plugin behavior, and persistent volume attachment under real workload. Install the gcloud CLI and authenticate with `gcloud auth login`, then configure kubectl context with `gcloud container clusters get-credentials CLUSTER_NAME --zone ZONE --project PROJECT_ID`. Verify connectivity with `kubectl cluster-info` and confirm that the API server endpoint resolves and responds.

On your local workstation or a bastion host with network access to the GKE cluster, install the diagnostic toolchain. Use your package manager to install iproute2 for `ip` and `ss`, tcpdump for packet capture, perf for performance counters, strace for system call tracing, and bpftool for eBPF introspection. Install crictl with `VERSION="v1.28.0"; wget https://github.com/kubernetes-sigs/cri-tools/releases/download/$VERSION/crictl-$VERSION-linux-amd64.tar.gz && sudo tar zxvf crictl-$VERSION-linux-amd64.tar.gz -C /usr/local/bin && rm -f crictl-$VERSION-linux-amd64.tar.gz`, then configure it to communicate with containerd by creating `/etc/crictl.yaml` with `runtime-endpoint: unix:///run/containerd/containerd.sock` and `image-endpoint: unix:///run/containerd/containerd.sock`. Install helm with `curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash` for chart-based application deployment. If etcd is exposed through the API server or you have direct access to control plane nodes in a private GKE setup, install etcdctl with `ETCD_VER=v3.5.10; curl -L https://github.com/etcd-io/etcd/releases/download/${ETCD_VER}/etcd-${ETCD_VER}-linux-amd64.tar.gz -o /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz && tar xzvf /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz -C /tmp && sudo mv /tmp/etcd-${ETCD_VER}-linux-amd64/etcdctl /usr/local/bin && rm -rf /tmp/etcd-${ETCD_VER}-linux-amd64*`.

GKE's managed control plane runs on Google-managed infrastructure, meaning direct etcd access and control plane SSH are unavailable in standard clusters. However, the practitioner can infer control plane health through API server latency, event streams, and controller manager reconciliation times. Node-level diagnostics require SSH access, enabled via `gcloud compute ssh NODE_NAME --zone ZONE` after identifying node names with `kubectl get nodes -o wide`. Ensure the compute.instances.get and compute.instances.setMetadata IAM permissions exist in your project role. For containerd runtime inspection, SSH into a node and elevate to root with `sudo -i` before invoking crictl commands, as the containerd socket requires privileged access.

The exercises below assume a running GKE cluster with at least one deployed workload. Deploy a baseline application with `kubectl create deployment nginx --image=nginx:1.25 --replicas=3` and expose it with `kubectl expose deployment nginx --port=80 --target-port=80 --type=LoadBalancer`. This creates three nginx pods distributed across nodes, a Service object with an external load balancer, and sufficient traffic to observe network flows, CPU scheduling, and persistent connection state.

## Exercise 1: Live State & Internal Subsystem Inspection

The first operational exercise establishes mastery over GKE cluster state inspection by tracing the path from Kubernetes API objects through the kubelet agent, containerd runtime, Linux namespaces, and network plugin data plane. This multi-layer traversal reveals the concrete implementation of declarative Kubernetes abstractions in terms of kernel constructs and runtime processes.

Begin by querying the API server for all pods across all namespaces with `kubectl get pods --all-namespaces -o wide`. This output displays pod names, namespaces, node assignments, IP addresses, and ready status. The node column reveals scheduling decisions made by the kube-scheduler, which evaluates resource requests, node affinity rules, taints, and tolerations to compute optimal pod placement. GKE uses the default scheduler with additional Google-specific predicates for regional persistent disk constraints and GPU affinity when applicable. Note the pod IP addresses, which are assigned by the CNI plugin from the cluster's pod CIDR range. GKE employs either the GKE-native VPC networking model with alias IP ranges or the legacy kubenet plugin, depending on cluster creation flags. In VPC-native mode, each pod receives an IP address from a secondary subnet range defined at cluster creation, enabling direct routing from VPC resources without NAT.

Select a specific pod and extract its full specification with `kubectl get pod POD_NAME -n NAMESPACE -o yaml`. This YAML manifest contains the pod's API server representation, including container image references, resource limits and requests, volume mounts, environment variables, and the critical `nodeName` field that anchors the pod to a specific worker node. Examine the `status` section for the pod's phase, condition array, and container statuses. Each container status includes the `containerID` field in the format `containerd://CONTAINER_ID`, which provides the runtime-level identifier required for low-level inspection. Record this container ID for subsequent crictl queries.

Retrieve the node object with `kubectl get node NODE_NAME -o yaml` to inspect allocatable resources, capacity, conditions, and system information. The `status.allocatable` field reflects the resources available for pod scheduling after accounting for kubelet and system daemon reservations. GKE reserves CPU and memory based on node size, typically allocating 100m CPU and 255Mi memory for system overhead plus additional reserves scaling with node capacity. The `status.conditions` array reports DiskPressure, MemoryPressure, PIDPressure, and Ready states, which influence scheduling decisions and trigger eviction policies when resource thresholds are exceeded. The `status.nodeInfo` field exposes kernel version, container runtime version, kubelet version, and OS image, confirming the underlying GCE virtual machine configuration.

Establish an SSH connection to the node hosting your selected pod with `gcloud compute ssh NODE_NAME --zone ZONE`. Once connected, elevate to root with `sudo -i` to access privileged runtime sockets and kernel interfaces. Verify containerd is running with `systemctl status containerd` and inspect its configuration at `/etc/containerd/config.toml`. GKE's containerd configuration enables the CRI plugin, configures sandbox image repositories, and sets up cgroup drivers. The critical `[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]` section specifies the low-level runtime, typically runc, and configures system call filtering via seccomp.

List all containers on the node with `crictl ps`. This output displays container IDs, pod sandbox IDs, image names, creation timestamps, and states. Cross-reference the container ID extracted from the kubectl pod status with this list. Inspect the container details with `crictl inspect CONTAINER_ID`, which returns a JSON document containing the container's Linux namespace assignments, cgroup paths, mount points, environment variables, and runtime specification. The `info.runtimeSpec.linux.namespaces` array enumerates the mount, PID, network, IPC, UTS, and cgroup namespaces that isolate the container from the host system. Each namespace is identified by a type and path in `/proc/PID/ns/`, enabling manual namespace entry with `nsenter` for advanced debugging.

Examine the container's cgroup hierarchy by inspecting the `info.runtimeSpec.linux.cgroupsPath` field, typically in the format `/kubepods/burstable/podUID/CONTAINER_ID` or `/kubepods/guaranteed/podUID/CONTAINER_ID` depending on the pod's QoS class. Navigate to the cgroup filesystem at `/sys/fs/cgroup/` and traverse the hierarchy to the container's cgroup directory. In cgroup v2 systems, which GKE has adopted in newer node images, inspect `cgroup.controllers` to see available resource controllers, `cpu.max` for CPU quota and period, `memory.max` for memory limits, and `memory.current` for current usage. Read `cpu.stat` to observe throttling events with `nr_throttled` and `throttled_usec`, which indicate periods when the container exceeded its CPU quota and the kernel throttled execution. Query memory statistics with `cat memory.stat` to see `anon`, `file`, `slab`, and `inactive_file` breakdowns, revealing memory pressure and page cache efficiency.

Return to the pod's network configuration by identifying the pod's network namespace. Extract the main container process ID with `crictl inspect CONTAINER_ID | jq -r '.info.pid'` and enter the network namespace with `nsenter -t PID -n`. Within the namespace, execute `ip addr show` to list all network interfaces. The pod network namespace contains a loopback interface and an `eth0` interface connected to the host via a veth pair. The interface's IP address matches the pod IP assigned by the CNI plugin. Inspect the routing table with `ip route show` to confirm the default gateway, typically the node's primary interface in VPC-native networking or a bridge interface in kubenet mode. Query ARP neighbors with `ip neigh show` to observe MAC address resolution for the default gateway.

Examine socket state within the pod's network namespace with `ss -tulpn`, which lists all TCP and UDP listening sockets with their process IDs. For an nginx container, expect to see a listening socket on port 80 bound to all interfaces. Add the `-e` flag to display extended socket information including inode numbers, which correlate to file descriptors in `/proc/PID/fd/`. Use `ss -tipm` to query established TCP connections with detailed TCP_INFO metrics including congestion window size, retransmissions, round-trip time estimates, and send and receive queue depths. These metrics reveal network performance characteristics and identify congestion or packet loss scenarios.

Exit the pod network namespace and inspect the host network configuration. List all interfaces with `ip link show` to identify veth pairs, bridge interfaces, and the primary node interface. GKE nodes running VPC-native networking create veth pairs for each pod, with one end in the pod's network namespace and the other on the host. Locate the veth peer by examining interface indices with `ip -d link show` and correlate peer_ifindex values. Inspect bridge forwarding tables with `bridge fdb show` if the node uses a Linux bridge, or examine routing policy database with `ip rule show` and routing tables with `ip route show table all` to trace packet forwarding paths.

Capture network traffic on the node's primary interface with `tcpdump -i ens4 -nn -vv 'port 80'`, replacing `ens4` with the actual interface name discovered via `ip link`. This capture reveals HTTP traffic to nginx pods, including TCP three-way handshakes, HTTP requests, and TCP connection teardowns. Add the `-X` flag to display packet payloads in hexadecimal and ASCII for protocol-level debugging. Filter traffic to a specific pod IP with `tcpdump -i ens4 -nn host POD_IP` to isolate flows and correlate them with Service load balancing decisions. The captured packets expose source and destination IP addresses, ports, TCP flags, sequence numbers, and window sizes, grounding network behavior in concrete packet flows rather than abstract Kubernetes constructs.

Inspect kubelet metrics by querying the kubelet's metrics endpoint with `curl -k https://localhost:10250/metrics --cert /var/lib/kubelet/pki/kubelet-client-current.pem --key /var/lib/kubelet/pki/kubelet-client-current.pem`. This returns Prometheus-format metrics including `kubelet_running_pods`, `kubelet_running_containers`, `kubelet_cgroup_manager_duration_seconds`, and `kubelet_runtime_operations_duration_seconds`. Parse these metrics with `grep` or pipe to `jq` if converted to JSON to extract critical operational indicators. The `kubelet_pleg_relist_duration_seconds` metric measures the Pod Lifecycle Event Generator relist duration, which should remain below one second to avoid kubelet performance degradation. Elevated values indicate slow container runtime operations or excessive pod churn.

Query node resource utilization with `kubectl top node` to display CPU and memory usage percentages and absolute values. This command queries the metrics-server component, which scrapes kubelet summary APIs and aggregates resource usage. Similarly, query pod-level metrics with `kubectl top pod -A` to identify resource-intensive workloads. These metrics reflect actual usage measured by cgroup accounting, not the resource requests and limits defined in pod specifications. Compare top output with requested and limit values to identify over-provisioned or under-provisioned pods, which indicate opportunities for vertical pod autoscaler tuning or manual resource adjustment.

Inspect persistent volumes by listing PVs with `kubectl get pv` and PVCs with `kubectl get pvc -A`. GKE provisions Persistent Disks as underlying storage, with CSI drivers translating Kubernetes storage APIs into GCE API calls. Select a PVC and describe it with `kubectl describe pvc PVC_NAME -n NAMESPACE` to view the bound PV, storage class, access modes, and capacity. Identify the underlying GCE disk with `kubectl get pv PV_NAME -o yaml` and examine the `spec.csi.volumeHandle` field, which contains the GCE disk URL. SSH into the node where the pod using the PVC is scheduled and verify the disk attachment with `lsblk` and `ls -l /dev/disk/by-id/`. The persistent disk appears as a SCSI device with a Google-prefixed identifier. Mount points are visible in `/proc/mounts` and correspond to the container's volume mount paths defined in the pod specification.

## Exercise 2: Benchmarking & Saturation Profiling

The second exercise establishes quantitative performance baselines for GKE cluster components under load, revealing CPU scheduling efficiency, network throughput limits, disk I/O bottlenecks, and API server request latency. Saturation profiling identifies resource exhaustion thresholds that trigger throttling, eviction, or service degradation.

Begin by deploying a CPU-intensive workload to measure node compute capacity and kernel scheduler behavior. Create a pod specification that runs a multi-threaded CPU stress test with explicit resource requests and limits. Save the following YAML as `cpu-stress.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: cpu-stress
  namespace: default
spec:
  containers:
  - name: stress
    image: polinux/stress
    resources:
      requests:
        cpu: "2000m"
        memory: "256Mi"
      limits:
        cpu: "2000m"
        memory: "256Mi"
    command: ["stress"]
    args: ["--cpu", "2", "--timeout", "300s"]
  restartPolicy: Never
```

Apply the manifest with `kubectl apply -f cpu-stress.yaml` and monitor pod scheduling with `kubectl get pod cpu-stress -w`. Once the pod enters the Running state, identify the assigned node with `kubectl get pod cpu-stress -o wide`. SSH into the node and observe real-time CPU usage with `top -p $(pgrep -f stress | tr '\n' ',' | sed 's/,$//')` to filter for stress processes. The output displays per-thread CPU utilization, which should approach but not exceed the 200% limit imposed by the cgroup CPU quota.

Instrument the stress workload with perf to capture CPU performance counters and identify instruction-level execution characteristics. Elevate to root and execute `perf stat -p $(pgrep -f stress | head -n 1) sleep 30` to collect 30 seconds of aggregate statistics including instructions executed, cycles consumed, cache references and misses, and branch prediction accuracy. The instructions-per-cycle (IPC) metric reveals CPU pipeline efficiency, with values below 1.0 indicating memory stalls, branch mispredictions, or data dependencies. Compare cache miss rates with `perf stat -e cache-references,cache-misses` to quantify memory hierarchy efficiency. High L3 cache miss rates suggest poor data locality or working sets exceeding cache capacity.

Record the container's CPU throttling behavior by reading cgroup statistics. Navigate to the pod's cgroup CPU controller at `/sys/fs/cgroup/kubepods/burstable/pod$(kubectl get pod cpu-stress -o jsonpath='{.metadata.uid}')/stress/cpu.stat` and execute `watch -n 1 cat cpu.stat` to monitor `nr_throttled` and `throttled_usec` in real time. Each increment of `nr_throttled` represents a scheduler period where the container exhausted its CPU quota, triggering kernel throttling. Accumulated throttled time in microseconds quantifies the performance impact. For guaranteed QoS pods with CPU limits equal to requests, throttling indicates the workload requires more CPU than allocated. For burstable pods, throttling is expected when limits exceed requests and the container attempts to burst beyond its request baseline.

Transition to network throughput profiling by deploying an iperf3 server and client within the cluster to measure pod-to-pod bandwidth and latency. Create a server deployment with `kubectl create deployment iperf3-server --image=networkstatic/iperf3 -- iperf3 -s` and expose it with a ClusterIP service via `kubectl expose deployment iperf3-server --port=5201`. Deploy a client pod with `kubectl run iperf3-client --image=networkstatic/iperf3 --rm -it --restart=Never -- iperf3 -c iperf3-server.default.svc.cluster.local -t 60 -P 4` to execute a 60-second test with four parallel streams. The output reports throughput in Gbits/sec, packet loss, jitter, and retransmissions. GKE nodes on n1-standard machine types typically achieve 10-16 Gbits/sec pod-to-pod throughput within the same zone, limited by virtio network interface bandwidth and GCE network tier. Cross-zone traffic incurs additional latency due to inter-zone routing but maintains similar throughput.

Capture network performance metrics at the socket level by SSHing into the node hosting the iperf3 client and executing `ss -tipm 'dst POD_IP' | grep -E 'cubic|cwnd|rtt'` during the test. This displays TCP congestion control algorithm (typically cubic), congestion window size, smoothed round-trip time, and retransmission statistics. A stable congestion window at the maximum value indicates the network path supports the offered load without packet loss. Retransmission counts above zero signal congestion or bit errors, necessitating further investigation with `netstat -s | grep retrans` to aggregate retransmission statistics across all connections.

Profile disk I/O performance by deploying a workload that writes and reads from a persistent volume. Create a storage class backed by SSD persistent disks with the following YAML saved as `ssd-sc.yaml`:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
  replication-type: regional-pd
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

Apply the storage class with `kubectl apply -f ssd-sc.yaml` and create a persistent volume claim with `kubectl apply -f -` using the following input:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: fast-storage
  namespace: default
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 100Gi
```

Deploy a pod that mounts the PVC and executes fio benchmarks with the following manifest saved as `fio-bench.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: fio-bench
  namespace: default
spec:
  containers:
  - name: fio
    image: dmonakhov/fio
    resources:
      requests:
        cpu: "1000m"
        memory: "512Mi"
      limits:
        cpu: "2000m"
        memory: "1Gi"
    volumeMounts:
    - name: data
      mountPath: /data
    command: ["/bin/sh"]
    args:
    - -c
    - |
      fio --name=randwrite --ioengine=libaio --iodepth=64 --rw=randwrite --bs=4k --direct=1 --size=10G --numjobs=4 --runtime=60 --group_reporting --directory=/data &&
      fio --name=randread --ioengine=libaio --iodepth=64 --rw=randread --bs=4k --direct=1 --size=10G --numjobs=4 --runtime=60 --group_reporting --directory=/data &&
      fio --name=seqwrite --ioengine=libaio --iodepth=64 --rw=write --bs=1M --direct=1 --size=10G --numjobs=1 --runtime=60 --group_reporting --directory=/data &&
      fio --name=seqread --ioengine=libaio --iodepth=64 --rw=read --bs=1M --direct=1 --size=10G --numjobs=1 --runtime=60 --group_reporting --directory=/data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: fast-storage
  restartPolicy: Never
```

Apply the pod with `kubectl apply -f fio-bench.yaml` and monitor execution with `kubectl logs fio-bench -f`. The fio output reports IOPS, bandwidth, latency percentiles (p50, p95, p99), and I/O submission and completion statistics for each test phase. Regional SSD persistent disks provide approximately 30 IOPS per GB and 0.48 MB/s throughput per GB, with a maximum of 100,000 IOPS and 1,200 MB/s per disk. Compare observed performance against these specifications to validate proper disk attachment and identify any I/O throttling imposed by GCE disk quotas.

Instrument disk I/O at the kernel level by SSHing into the node hosting the fio pod and observing block device statistics with `iostat -xz 1` during the benchmark. This output displays per-device utilization percentages, read and write IOPS, throughput, average request size, average wait time, and service time. The `%util` column approaching 100% indicates the device is saturated, while elevated `await` values suggest queuing delays. Cross-reference the device name with the persistent disk attachment by listing SCSI devices with `lsscsi` and correlating bus addresses with the PV's volume handle.

Capture I/O system call latency with strace by attaching to one of the fio worker processes. Identify the fio process IDs with `pgrep -f fio` and execute `strace -c -p PID` for 10 seconds to collect system call frequency and latency statistics. The output aggregates time spent in write, read, pwrite64, pread64, and io_submit calls, revealing the proportion of execution time spent in user space versus kernel I/O operations. High cumulative time in io_submit indicates efficient asynchronous I/O, while elevated time in synchronous write and read calls suggests inefficient I/O patterns or insufficient queue depth.

Profile API server request latency by deploying a high-frequency kubectl query workload. Create a bash script that continuously lists pods across all namespaces and measures response time with `time kubectl get pods -A > /dev/null`. Wrap this in a loop with `for i in {1..100}; do time kubectl get pods -A > /dev/null; done 2>&1 | grep real` to execute 100 iterations and extract real elapsed time. Typical API server response times range from 50-200ms for list operations on clusters with hundreds of pods, scaling logarithmically with object count due to etcd's balanced tree indexes. Response times exceeding 500ms indicate API server overload, network latency, or etcd performance issues.

Inspect API server metrics by querying the GKE monitoring dashboard or using kubectl to access metrics if the API server exposes them. Execute `kubectl get --raw /metrics` to retrieve Prometheus-format metrics including `apiserver_request_duration_seconds`, `apiserver_request_total`, and `etcd_request_duration_seconds`. Parse these with `grep` to filter relevant metrics, such as `grep 'apiserver_request_duration_seconds_bucket{verb="LIST"'` to extract LIST operation latency histograms. The metric's bucket labels quantify request counts at various latency thresholds (e.g., 100ms, 500ms, 1s), enabling percentile calculation. Elevated etcd request durations signal consensus bottlenecks or disk I/O saturation on control plane nodes.

Simulate node failure and measure pod rescheduling latency by cordoning a node with `kubectl cordon NODE_NAME` to mark it unschedulable, then draining it with `kubectl drain NODE_NAME --ignore-daemonsets --delete-emptydir-data --force`. Monitor pod evictions and rescheduling with `kubectl get pods -A -w` to observe the sequence of Terminating and Pending states followed by Running on alternative nodes. Measure the elapsed time from drain initiation to all pods achieving Running state, quantifying the cluster's recovery time objective (RTO) for node failures. The drain process respects PodDisruptionBudgets, which constrain the number of concurrently disrupted pods in a deployment or statefulset, preventing cascading failures during maintenance operations.

## Exercise 3: Fault Injection & Recovery Analysis

The third exercise validates GKE cluster resilience through controlled fault injection, observing failure propagation, automated recovery mechanisms, and steady-state restoration. These experiments expose the gap between theoretical fault tolerance designs and actual runtime behavior under adverse conditions.

Begin with a network partition experiment that isolates a pod from its Service backends to test connection retry logic and timeout behavior. Deploy a multi-replica backend application with `kubectl create deployment backend --image=nginx:1.25 --replicas=5` and expose it via `kubectl expose deployment backend --port=80 --type=ClusterIP`. Deploy a client pod that continuously queries the service with a bash loop:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: client-loop
  namespace: default
spec:
  containers:
  - name: client
    image: curlimages/curl:8.4.0
    command: ["/bin/sh"]
    args:
    - -c
    - |
      while true; do
        curl -s -o /dev/null -w "Status: %{http_code}, Time: %{time_total}s\n" http://backend.default.svc.cluster.local
        sleep 1
      done
  restartPolicy: Never
```

Apply the client pod with `kubectl apply -f client-loop.yaml` and monitor its logs with `kubectl logs client-loop -f` to establish baseline connectivity showing 200 status codes and sub-10ms response times. Identify one of the backend pods with `kubectl get pods -l app=backend -o name | head -n 1` and inject a network fault by SSHing into the node hosting that pod and installing iptables rules to drop traffic. Identify the pod's IP with `kubectl get pod POD_NAME -o jsonpath='{.status.podIP}'` and execute `sudo iptables -A INPUT -s POD_IP -j DROP && sudo iptables -A OUTPUT -d POD_IP -j DROP` on the node. Observe the client logs to confirm that requests continue succeeding via the remaining four healthy backends, demonstrating Service load balancing resilience. Kube-proxy's iptables or IPVS rules distribute traffic across all Service endpoints, automatically bypassing unreachable pods after TCP connection timeouts.

Measure the recovery time by removing the iptables rules with `sudo iptables -D INPUT -s POD_IP -j DROP && sudo iptables -D OUTPUT -d POD_IP -j DROP` and observing when the isolated pod rejoins the Service endpoint pool. Query Service endpoints with `kubectl get endpoints backend -o yaml` to see the list of ready addresses. The kubelet's liveness and readiness probe mechanisms detect pod health and update endpoint status accordingly. If the backend pod has no readiness probe defined, it remains in the endpoint list during the network partition, causing intermittent client failures until connection timeouts occur. Define a readiness probe by editing the deployment with `kubectl edit deployment backend` and adding:

```yaml
spec:
  template:
    spec:
      containers:
      - name: nginx
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 3
          failureThreshold: 2
```

Reapply the network partition and observe that the isolated pod transitions to non-ready status within 6-9 seconds (failureThreshold × periodSeconds), triggering immediate removal from the Service endpoint pool and eliminating client-visible failures.

Escalate to a complete node failure simulation by cordoning a node and forcibly terminating its kubelet process. SSH into a node hosting multiple pods and execute `sudo systemctl stop kubelet` to halt the kubelet service. Return to your workstation and monitor pod status with `kubectl get pods -A -o wide --field-selector spec.nodeName=NODE_NAME -w`. Initially, pods remain in Running state because the API server has not yet detected node failure. The node controller, part of the kube-controller-manager, polls node status via the kubelet's API endpoint with a default period of 5 seconds. After 40 seconds without a successful heartbeat (configurable via `--node-monitor-grace-period`), the node transitions to NotReady status visible with `kubectl get node NODE_NAME`. After an additional 5 minutes by default (configurable via `--pod-eviction-timeout`), the node controller marks pods for eviction and the scheduler places them on alternative nodes.

Observe the pod eviction sequence, noting the delay between node failure and pod rescheduling. This delay represents the cluster's mean time to detect (MTTD) and mean time to respond (MTTR) for node failures. For latency-sensitive applications, reduce `--pod-eviction-timeout` to accelerate eviction at the cost of increased risk of premature eviction during transient network partitions. Alternatively, deploy node-problem-detector as a DaemonSet to proactively detect hardware and kernel faults and taint nodes, triggering faster pod evictions through the taint-based eviction mechanism.

Inject a memory pressure scenario by deploying a pod that gradually consumes memory until the kernel out-of-memory (OOM) killer intervenes. Create a pod specification with a memory limit but no request, enabling burstable QoS:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: memory-eater
  namespace: default
spec:
  containers:
  - name: stress
    image: polinux/stress
    resources:
      limits:
        memory: "512Mi"
    command: ["stress"]
    args: ["--vm", "1", "--vm-bytes", "600M", "--vm-hang", "0"]
  restartPolicy: Never
```

Apply the pod with `kubectl apply -f memory-eater.yaml` and monitor its status with `kubectl get pod memory-eater -w`. The stress process attempts to allocate 600 MB, exceeding the 512 MB limit. The kernel's memory cgroup controller triggers an OOM kill when the container's memory usage breaches the limit, terminating the stress process. The kubelet detects the OOM kill via the container runtime and updates the pod status to reflect the OOMKilled reason visible with `kubectl describe pod memory-eater | grep -A 5 'Last State'`. The pod enters a CrashLoopBackOff state as the kubelet attempts to restart the container with exponential backoff delays.

Distinguish between container-level OOM kills and node-level OOM kills by examining kernel logs. SSH into the node hosting the memory-eater pod and inspect dmesg output with `sudo dmesg -T | grep -i 'killed process'`. Container-level OOM kills show the memory cgroup path and the killed process name, confirming the cgroup controller's enforcement of memory limits. Node-level OOM kills, triggered when the entire node exhausts physical memory, display system-wide memory statistics and often target the largest memory consumers, which may include kubelet or container runtime processes if workload memory requests are over-committed.

Test persistent volume failover by forcibly detaching a persistent disk from a node and observing reattachment to a new node during pod rescheduling. Deploy a StatefulSet with a PVC template:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: data-app
  namespace: default
spec:
  serviceName: data-app
  replicas: 3
  selector:
    matchLabels:
      app: data-app
  template:
    metadata:
      labels:
        app: data-app
    spec:
      containers:
      - name: app
        image: nginx:1.25
        volumeMounts:
        - name: data
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 50Gi
```

Apply the StatefulSet with `kubectl apply -f statefulset.yaml` and wait for all pods to achieve Running state. Identify one pod and its associated PVC with `kubectl get pod data-app-0 -o yaml | grep -A 5 volumes` and `kubectl get pvc data-data-app-0 -o yaml | grep volumeName`. Retrieve the underlying GCE disk name from the PV's volumeHandle. Cordon and drain the node hosting data-app-0 with `kubectl drain NODE_NAME --ignore-daemonsets --delete-emptydir-data`. The pod enters Terminating state, but the scheduler cannot place it on another node immediately because the persistent disk remains attached to the original node. GKE's CSI driver must detach the disk from the old node before attaching it to the new node, a process governed by the `attachdetach-controller`. Monitor the pod with `kubectl get pod data-app-0 -w` and observe the transition from Terminating to Pending to ContainerCreating to Running, with the Pending phase lasting 1-3 minutes while disk detachment and reattachment occur. Query PV attachment status with `kubectl get volumeattachment` to see CSI-managed attach operations in progress.

Inject a DNS resolution failure by tampering with CoreDNS configuration. GKE runs CoreDNS as a Deployment in the kube-system namespace to provide cluster DNS services. Scale CoreDNS to zero replicas with `kubectl scale deployment coredns -n kube-system --replicas=0` to simulate complete DNS outage. Deploy a client pod that attempts to resolve a Service DNS name:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dns-test
  namespace: default
spec:
  containers:
  - name: test
    image: busybox:1.36
    command: ["/bin/sh"]
    args:
    - -c
    - |
      while true; do
        nslookup kubernetes.default.svc.cluster.local
        echo "Exit code: $?"
        sleep 2
      done
  restartPolicy: Never
```

Apply the pod with `kubectl apply -f dns-test.yaml` and observe logs with `kubectl logs dns-test -f`. DNS lookups fail with connection timeout errors because no CoreDNS pods are available to service resolution requests. The pod's `/etc/resolv.conf` contains nameserver entries pointing to the CoreDNS Service ClusterIP, which has no backing endpoints. Restore DNS by scaling CoreDNS back to its original replica count with `kubectl scale deployment coredns -n kube-system --replicas=2` and observe immediate resolution success in the dns-test logs. This demonstrates the criticality of CoreDNS availability and the lack of built-in DNS caching at the pod level, which leaves applications vulnerable to transient DNS outages.

Test control plane API server resilience by simulating high request rates to trigger rate limiting. GKE's managed API server implements rate limits to prevent abuse and ensure fair resource allocation across clients. Generate high-frequency requests with a bash loop executing concurrent kubectl commands:

```bash
for i in {1..1000}; do
  kubectl get pods -A > /dev/null 2>&1 &
done
wait
```

This spawns 1000 parallel kubectl processes, overwhelming the API server's per-client rate limits. Monitor for 429 Too Many Requests errors in the command output or by inspecting kubectl's verbose output with `kubectl get pods -v=8` to see HTTP response codes. The API server's default rate limit is 400 queries per second (QPS) per client, with burst allowances up to 600 requests. Sustained exceedance triggers exponential backoff in kubectl, visible as delayed retries. Query API server metrics with `kubectl get --raw /metrics | grep apiserver_flowcontrol_rejected_requests_total` to see cumulative rejection counts per priority level, revealing the API server's flow control enforcement.

## Diagnostic Cheat Sheet & Verification Checklist

The operational verification of GKE clusters demands fluency with multi-layer diagnostic commands that traverse Kubernetes abstractions, container runtime interfaces, Linux kernel primitives, and network protocol stacks. This cheat sheet consolidates essential commands and verification procedures for rapid troubleshooting and capacity planning.

Query all cluster resources across namespaces with `kubectl get all -A` to obtain a global view of deployments, pods, services, and replicasets. Filter by namespace with `-n NAMESPACE` or by label selectors with `-l app=nginx`. Extract detailed YAML specifications with `kubectl get RESOURCE NAME -o yaml` and JSON with `-o json`, piping to `jq` for structured parsing. Inspect resource events with `kubectl describe RESOURCE NAME` to see scheduling decisions, image pull statuses, probe failures, and controller actions.

Verify node health and capacity with `kubectl get nodes -o wide` to display node IPs, OS versions, kernel versions, and container runtime versions. Describe nodes with `kubectl describe node NODE_NAME` to inspect conditions, allocatable resources, and current resource utilization. Query node metrics with `kubectl top node` to see real-time CPU and memory consumption. SSH into nodes with `gcloud compute ssh NODE_NAME --zone ZONE` for direct kernel and runtime inspection.

List containers on a node with `crictl ps` and inspect individual containers with `crictl inspect CONTAINER_ID`. Extract container logs with `crictl logs CONTAINER_ID` and execute commands inside containers with `crictl exec -it CONTAINER_ID /bin/sh`. List pod sandboxes with `crictl pods` and inspect sandbox details with `crictl inspectp POD_ID`. Query container image details with `crictl images` and remove unused images with `crictl rmi IMAGE_ID` to reclaim node disk space.

Examine cgroup resource limits and usage by navigating to `/sys/fs/cgroup/kubepods/` and traversing the QoS class hierarchy (guaranteed, burstable, besteffort). Read CPU quota with `cat cpu.max`, memory limit with `cat memory.max`, and current usage with `cat cpu.stat` and `cat memory.current`. Monitor cgroup events with `cat memory.events` to detect OOM kills and memory pressure thresholds.

Trace network connectivity with `ping`, `traceroute`, and `mtr` from within pods or the node. Enter a pod's network namespace with `kubectl exec -it POD_NAME -- /bin/sh` and execute `ip addr`, `ip route`, and `ss -tulpn` to inspect interface configuration, routing tables, and socket state. Capture packets with `tcpdump -i any -nn host POD_IP` on the node to observe traffic flows. Query iptables rules with `sudo iptables -t nat -L -n -v` and `sudo iptables -t filter -L -n -v` to inspect kube-proxy's load balancing rules.

Profile CPU performance with `perf stat -p PID` to collect hardware performance counters. Record execution traces with `perf record -p PID -g -- sleep 30` and analyze with `perf report` to identify hot functions. Trace system calls with `strace -p PID -c` for aggregate statistics or `strace -p PID -e trace=open,read,write` to filter specific calls. Profile disk I/O with `iostat -xz 1` and memory allocation with `vmstat 1`.

Query API server metrics with `kubectl get --raw /metrics` and parse with `grep` for specific metric families. Monitor etcd health if accessible with `etcdctl endpoint health --cluster` and query member status with `etcdctl member list`. Inspect control plane component logs via GKE's logging integration with `gcloud logging read "resource.type=k8s_control_plane_component" --limit 50 --format json`.

Verify Service endpoints with `kubectl get endpoints SERVICE_NAME` to list pod IPs registered for load balancing. Test Service DNS resolution from within a pod with `nslookup SERVICE_NAME.NAMESPACE.svc.cluster.local`. Query CoreDNS logs with `kubectl logs -n kube-system -l k8s-app=kube-dns` to diagnose resolution failures.

Inspect persistent volume status with `kubectl get pv` and `kubectl get pvc -A`. Describe PVs with `kubectl describe pv PV_NAME` to see reclaim policy, storage class, and CSI driver details. Query volume attachments with `kubectl get volumeattachment` to monitor CSI attach and detach operations during pod scheduling.

Test pod eviction and rescheduling by cordoning nodes with `kubectl cordon NODE_NAME` and draining with `kubectl drain NODE_NAME --ignore-daemonsets --delete-emptydir-data`. Monitor pod distribution with `kubectl get pods -A -o wide` to verify scheduler placement across available nodes. Uncordon nodes with `kubectl uncordon NODE_NAME` to restore schedulability.

Validate network policies by deploying test pods in different namespaces and verifying connectivity with `curl` or `nc`. Create baseline network policies that deny all ingress and egress, then incrementally add allow rules to test isolation. Query active network policies with `kubectl get networkpolicy -A` and describe with `kubectl describe networkpolicy POLICY_NAME -n NAMESPACE`.

Monitor cluster autoscaler behavior by inspecting logs with `kubectl logs -n kube-system -l app=cluster-autoscaler` to see scaling decisions, node provisioning, and scale-down evaluations. Query node pool configurations with `gcloud container node-pools list --cluster CLUSTER_NAME --zone ZONE` to verify autoscaling parameters and machine types.

Verify workload identity and IAM bindings by describing pods with `kubectl describe pod POD_NAME` and inspecting the `serviceAccountName` field. Query the Kubernetes service account with `kubectl get serviceaccount SA_NAME -o yaml` and verify the IAM policy binding with `gcloud iam service-accounts get-iam-policy GSA_EMAIL`. Test workload identity authentication from within a pod with `curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token` to retrieve OAuth2 access tokens.

Diagnose admission controller rejections by inspecting API server audit logs accessible via GKE's Cloud Logging. Query logs with `gcloud logging read "resource.type=k8s_cluster AND protoPayload.status.code!=0" --limit 50` to filter failed API requests. Parse the `protoPayload` field to extract rejection reasons from validating and mutating webhooks.

This comprehensive verification methodology grounds GKE operational excellence in empirical measurement and first-principles understanding of kernel scheduling, network forwarding, cgroup resource isolation, and distributed state machine reconciliation. The practitioner emerges with the diagnostic fluency to navigate from high-level kubectl abstractions down to packet captures, performance counters, and cgroup statistics, establishing quantitative baselines for capacity planning and rapidly isolating root causes during incident response.
