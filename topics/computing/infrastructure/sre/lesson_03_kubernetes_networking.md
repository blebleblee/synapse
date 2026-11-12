# Lesson 3: Kubernetes Networking

## 1. First-Principles Intuition & Invariants

At its core, Kubernetes networking is a state machine—a declarative abstraction over a distributed system of interconnected, stateful entities that must maintain consistency across a cluster of heterogeneous nodes. The fundamental problem it solves is how to map a logical service endpoint to a set of dynamically changing pod IP addresses, all while preserving the semantics of TCP/UDP packet flow, routing, and load balancing in a containerized environment.

To understand this, one must begin with the **networking invariants** that govern how Kubernetes interacts with the underlying infrastructure. These invariants are not merely architectural choices—they are mathematical and operational constraints that define the correctness of the system. For instance, a Kubernetes service must be able to map a stable virtual IP (VIP) to a set of pods that may come and go, and it must do so without breaking existing connections or introducing latency that would compromise application performance.

The first invariant is that **every pod must have a unique IP address** within the cluster, and this IP must be routable from any node in the cluster. This is achieved through a **pod network plugin**, which typically implements a flat network model (e.g., Calico, Flannel, Cilium) or a more complex overlay network. The pod network is not just a layer of abstraction—it is a foundational construct that enables the next invariant: **services must be able to route traffic to pods using their IP addresses without requiring a proxy or NAT**.

The second invariant is that **services must be logically decoupled from pods**, meaning that a service should not be affected by pod lifecycle events such as creation, deletion, or migration. This is accomplished through a **virtual IP (VIP)** and a **load balancer**—either implemented in kernel space (e.g., kube-proxy with iptables) or in userspace (e.g., kube-proxy with IPVS or eBPF). The VIP is a logical address that is never actually assigned to a physical interface, but rather is used by the kernel to route packets to the appropriate backend pods.

The third invariant is that **network policies must enforce access control at the pod level**, ensuring that traffic is allowed or denied based on rules that are defined in a declarative manner. This is critical for security, especially in multi-tenant environments where pods from different applications must not be able to communicate with each other unless explicitly permitted.

These invariants are not just theoretical—they are enforced by the **control plane** and the **data plane** of Kubernetes. The control plane, through the API server, maintains the desired state of services, network policies, and pod networks. The data plane, implemented by the CNI plugins and kube-proxy, enforces this state by manipulating the kernel’s routing tables, iptables rules, or eBPF programs.

## 2. Core Architecture & Mechanics

Kubernetes networking is built on a layered architecture that spans from the kernel’s network stack to the application layer. At the base of this stack is the **CNI (Container Network Interface)** plugin, which is responsible for assigning IP addresses to pods and configuring their network interfaces. The most common CNI implementations include Calico, Flannel, and Cilium, each with their own approach to managing pod-to-pod communication.

The **kube-proxy** is the central component that implements the service abstraction. It runs as a daemonset on each node and is responsible for maintaining the mapping between service VIPs and pod endpoints. The kube-proxy can operate in three modes: **iptables**, **IPVS**, and **eBPF**. Each mode has its own trade-offs in terms of performance, scalability, and complexity.

In **iptables mode**, kube-proxy manipulates the kernel’s netfilter framework to create rules that redirect traffic to the appropriate backend pods. This is a well-established and widely supported approach, but it can become a bottleneck under high load due to the sheer number of rules that must be maintained. Each service requires a set of iptables rules that are updated whenever pods are added or removed.

In **IPVS mode**, kube-proxy leverages the **IP Virtual Server (IPVS)** module, which is a kernel-based load balancer that is optimized for high throughput and low latency. IPVS uses a hash table to map VIPs to backend servers, and it supports multiple load balancing algorithms such as round-robin, weighted round-robin, and least connections. This mode is more efficient than iptables for large-scale deployments, but it requires a kernel version that supports IPVS.

In **eBPF mode**, kube-proxy uses **eBPF programs** to implement service routing directly in the kernel. This approach is the most modern and performant, as it avoids the overhead of userspace manipulation and leverages the kernel’s eBPF JIT compiler for high-speed packet processing. eBPF programs are compiled to machine code and are executed in the kernel without the need for context switches, making them ideal for high-performance networking.

The **Ingress Controller** is another critical component in Kubernetes networking. It acts as a reverse proxy and load balancer for HTTP/HTTPS traffic, routing requests to the appropriate services based on hostnames and paths. The Ingress resource defines the rules for routing traffic, and the Ingress Controller implements these rules using a backend such as NGINX, Traefik, or HAProxy.

An **Ingress Controller** is not just a simple proxy—it is a **stateful, event-driven system** that watches the Kubernetes API for changes to Ingress resources and updates its internal routing tables accordingly. It maintains a mapping between hostnames, paths, and backend services, and it ensures that traffic is routed correctly even when services are scaled or updated.

The **Network Policy** mechanism is implemented using **CNI plugins** that support the Kubernetes NetworkPolicy API. Network policies define rules that control how pods can communicate with each other, and they are enforced by the CNI plugin at the kernel level. For example, Calico uses eBPF or iptables to implement network policies, and it maintains a set of rules that are applied to each pod’s network interface.

The **data plane** of Kubernetes networking is thus a complex interplay of kernel-level components, userspace daemons, and CNI plugins. The **control plane** ensures that the desired state is maintained, while the **data plane** enforces this state through kernel-level operations. The architecture is designed to be **distributed**, **scalable**, and **fault-tolerant**, with each component having a well-defined role and responsibility.

## 3. High-Performance Optimization & Failure Modes

Kubernetes networking is not just about correctness—it is also about performance and resilience. The system must be able to handle thousands of services and pods, and it must do so without introducing latency or dropping packets. This requires careful attention to **resource allocation**, **concurrency**, and **failure recovery**.

One of the most significant performance bottlenecks in Kubernetes networking is **iptables rule explosion**. As the number of services and pods increases, the number of iptables rules grows linearly, and this can lead to performance degradation. In large clusters, this can result in iptables rule updates taking several seconds, which can cause service disruptions. To mitigate this, operators often switch to **IPVS** or **eBPF** modes, which are more efficient at scale.

Another performance concern is **network policy enforcement**. When network policies are applied to a large number of pods, the CNI plugin must maintain a large number of rules to enforce access control. This can lead to increased memory usage and slower rule evaluation. Modern CNI plugins like **Cilium** use **eBPF** to implement network policies with **sub-second rule evaluation**, making them suitable for high-throughput environments.

Failure modes in Kubernetes networking are diverse and can be categorized into **control plane failures**, **data plane failures**, and **network infrastructure failures**. A **control plane failure** can cause the system to lose track of pod IPs or service VIPs, leading to traffic being dropped or misrouted. A **data plane failure** can occur when a node’s network stack becomes unresponsive, causing pods to lose connectivity. A **network infrastructure failure** can occur when the underlying network fabric (e.g., switches, routers) experiences issues, leading to packet loss or latency.

To mitigate these failures, Kubernetes provides several mechanisms. **Service discovery** is handled through **DNS**, which is integrated into the cluster and provides a stable endpoint for services. **Health checks** are implemented through **liveness and readiness probes**, which ensure that pods are only considered healthy when they are ready to serve traffic. **Pod rescheduling** is handled by the **scheduler**, which ensures that pods are moved to healthy nodes when failures occur.

In addition, **observability** is critical for identifying and resolving networking issues. Tools like **Prometheus**, **Grafana**, and **eBPF-based tracing** can be used to monitor network performance, detect anomalies, and provide insights into the behavior of the network stack. **eBPF** is particularly powerful in this regard, as it can provide detailed packet-level telemetry without the need for complex instrumentation.

In conclusion, Kubernetes networking is a sophisticated system that balances correctness, performance, and resilience. It is built on a foundation of well-defined invariants and is implemented through a combination of kernel-level components, userspace daemons, and CNI plugins. The system is designed to scale and adapt to changing conditions, but it requires careful tuning and monitoring to ensure optimal performance and reliability.
