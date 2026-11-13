Operational Verification Labs: Monitoring Prometheus Grafana
=====================================================

### Objective and Environment Setup

Monitoring Prometheus Grafana is a critical infrastructure component for real-time system monitoring and analytics. This lab guide provides hands-on verification of Prometheus Grafana's operational integrity using real tools and frameworks. To begin, set up a cloud infrastructure environment with the following tools:

To install the required tools, run the following commands:

```bash
sudo apt-get update
sudo apt-get install -y kubectl iproute2 etcdctl crictl helm
sudo apt-get install -y ss ethtool tcpdump perf
```

Verify the installation of these tools using the following commands:

```bash
kubectl version
ip -s link show
etcdctl version
crictl version
helm version
ss -tipm
ethtool -i eth0
tcpdump -h
perf stat
```

### Exercise 1: Live State and Internal Subsystem Inspection

In this exercise, we will inspect the live state of the Prometheus Grafana deployment and its internal subsystems.

#### Verify Prometheus Deployment

Use `kubectl` to verify the Prometheus deployment:

```bash
kubectl get deployments -n monitoring
kubectl get pods -n monitoring
```

#### Inspect Prometheus Configuration

Use `kubectl` to inspect the Prometheus configuration:

```bash
kubectl get configmap prometheus-config -n monitoring -o yaml
```

#### Verify Grafana Deployment

Use `kubectl` to verify the Grafana deployment:

```bash
kubectl get deployments -n monitoring
kubectl get pods -n monitoring
```

#### Inspect Grafana Configuration

Use `kubectl` to inspect the Grafana configuration:

```bash
kubectl get configmap grafana-config -n monitoring -o yaml
```

#### Verify Prometheus Grafana Service

Use `kubectl` to verify the Prometheus Grafana service:

```bash
kubectl get svc prometheus-grafana -n monitoring
```

### Exercise 2: Benchmarking and Saturation Profiling

In this exercise, we will benchmark and profile the Prometheus Grafana system under saturation conditions.

#### Benchmark Prometheus

Use `kubectl` to benchmark Prometheus:

```bash
kubectl exec -it prometheus-0 -n monitoring -- prometheus --web.enable-lifecycle --web.enable-pprof
```

#### Profile Prometheus

Use `kubectl` to profile Prometheus:

```bash
kubectl exec -it prometheus-0 -n monitoring -- prometheus --web.enable-lifecycle --web.enable-pprof --web.enable-goroutine-profiling
```

#### Benchmark Grafana

Use `kubectl` to benchmark Grafana:

```bash
kubectl exec -it grafana-0 -n monitoring -- grafana-server --web.enable-lifecycle --web.enable-pprof
```

#### Profile Grafana

Use `kubectl` to profile Grafana:

```bash
kubectl exec -it grafana-0 -n monitoring -- grafana-server --web.enable-lifecycle --web.enable-pprof --web.enable-goroutine-profiling
```

### Exercise 3: Fault Injection and Recovery Analysis

In this exercise, we will inject faults into the Prometheus Grafana system and analyze its recovery behavior.

#### Inject Fault into Prometheus

Use `kubectl` to inject a fault into Prometheus:

```bash
kubectl exec -it prometheus-0 -n monitoring -- prometheus --web.enable-lifecycle --web.enable-pprof --web.enable-fault-injection
```

#### Inject Fault into Grafana

Use `kubectl` to inject a fault into Grafana:

```bash
kubectl exec -it grafana-0 -n monitoring -- grafana-server --web.enable-lifecycle --web.enable-pprof --web.enable-fault-injection
```

#### Analyze Recovery Behavior

Use `kubectl` to analyze the recovery behavior of Prometheus and Grafana:

```bash
kubectl logs prometheus-0 -n monitoring
kubectl logs grafana-0 -n monitoring
```

### Diagnostic Cheat Sheet and Verification Checklist

| **Diagnostic Tool** | **Command** | **Description** |
| --- | --- | --- |
| `kubectl` | `get deployments -n monitoring` | Verify Prometheus deployment |
| `kubectl` | `get pods -n monitoring` | Verify Prometheus and Grafana pods |
| `kubectl` | `get configmap prometheus-config -n monitoring -o yaml` | Inspect Prometheus configuration |
| `kubectl` | `get configmap grafana-config -n monitoring -o yaml` | Inspect Grafana configuration |
| `kubectl` | `get svc prometheus-grafana -n monitoring` | Verify Prometheus Grafana service |
| `ss` | `ss -tipm` | Verify network connections |
| `ethtool` | `ethtool -i eth0` | Verify network interface configuration |
| `tcpdump` | `tcpdump -h` | Verify network traffic capture |
| `perf` | `perf stat` | Verify system performance counters |

This lab guide provides a comprehensive hands-on verification of the Prometheus Grafana system using real tools and frameworks. By following these exercises, you can gain a deep understanding of the system's operational integrity and identify potential issues before they impact your production environment.
