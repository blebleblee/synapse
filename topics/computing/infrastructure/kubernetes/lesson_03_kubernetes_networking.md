Here is the fully corrected, publication-grade, raw Markdown:

# Lesson 3: Kubernetes Networking and Load Balancing

## 1. First-Principles Intuition & Invariants

Every container orchestration system, no matter how sophisticated its scheduling algorithms or declarative state machines, ultimately reduces to a single, deceptively simple question: how does one ephemeral process reach another ephemeral process when neither has a stable identity? In the physical world, a server's network interface card is bound to a chassis, a chassis is bound to a rack, and a rack is bound to a data center. The network stack beneath it all—the ARP table, the routing table, the connection tracking state—is built on the assumption of permanence. Kubernetes shatters that assumption at every layer. A Pod may be created, scheduled, terminated, and recreated within seconds. Its IP address may change. Its hostname may change. Its node may change. The fundamental invariant that Kubernetes must enforce is not that any Pod can reach any other Pod, but rather that the *logical* identity of a service—expressed through a stable DNS name and a stable virtual IP—remains reachable regardless of the underlying Pod churn.

To understand how Kubernetes achieves this, one must descend beneath the orchestration layer into the Linux networking stack itself. Every Pod, at its most fundamental level, is a Linux process running in a network namespace. That namespace is isolated by the kernel's `inet_diag` subsystem, which maintains separate routing tables, ARP tables, and connection tracking states for each namespace. The CNI (Container Network Interface) plugin, invoked during Pod creation, is responsible for installing the network rules that make this namespace reachable from the rest of the cluster. The CNI plugin does not speak Kubernetes; it speaks Linux. It calls `ip link add`, `ip addr add`, `iptables -A`, and `conntrack` to configure the underlying kernel. Kubernetes is merely the declarative layer that tells the CNI plugin what to do. This separation is critical: it means that Kubernetes networking is, at its core, a composition of Linux network namespaces, Linux routing tables, Linux netfilter rules, and Linux connection tracking state.

The problem space that this architecture must solve is twofold. First, within a cluster, every Pod must be able to reach every other Pod on a private IP subnet. This is the intra-cluster network. Second, external traffic must be able to reach specific Pods through a stable, public-facing address. This is the inter-cluster and external network. These two requirements are in tension. The intra-cluster network requires that every Pod's IP be routable to every other Pod's IP, which means the routing table must contain an entry for every Pod IP. With thousands of Pods, this is a problem of scale. The inter-cluster network requires that external traffic be routed to a specific Pod, but Pods are ephemeral. The solution is a virtual IP address—a Service—that sits between the external world and the internal world, performing load balancing across the set of Pods that back it.

## 2. Service Objects and Virtual IPs

The Service object in Kubernetes is not a network device in the traditional sense. It is a kernel-level abstraction implemented through netfilter rules. When you create a Service with type `ClusterIP`, the kube-apiserver allocates a virtual IP address from a CIDR block reserved for the cluster. The kube-proxy process, running on every node, installs iptables rules that redirect traffic destined for that virtual IP to the actual Pods backing the Service. The iptables rule is a DNAT (Destination Network Address Translation) rule that rewrites the destination IP from the Service's virtual IP to the Pod's IP, and then rewrites the destination port from the Service's port to the Pod's port. This is a one-to-one mapping at the kernel level, and it happens in the FORWARD chain of the netfilter subsystem. The connection tracking state is updated accordingly, so that return traffic is correctly routed back to the original source.

## 3. Endpoints Controller and Reconciliation Loop

The Endpoints controller is the reconciliation loop that keeps the iptables rules in sync with the actual state of the cluster. When a Pod is created, the Endpoints controller updates the Endpoints object, which lists the current set of Pods backing each Service. kube-proxy watches the Endpoints object and updates the iptables rules accordingly. If a Pod is terminated, the Endpoints controller removes it from the list, and kube-proxy removes the corresponding iptables rule. This is a continuous, level-triggered reconciliation loop: the desired state is defined by the Service object, the actual state is defined by the Endpoints object, and kube-proxy reconciles the difference. The reconciliation loop runs every second by default, but it can be tuned to run more or less frequently depending on the workload's sensitivity to latency.

## 4. LoadBalancer Service Type

The LoadBalancer service type adds another layer of complexity. When you create a LoadBalancer Service, the cloud provider's control plane provisions an external load balancer—typically a hardware appliance or a software load balancer running on the cloud provider's infrastructure. This external load balancer has a public IP address, and it forwards traffic to the cluster's internal network. The kube-apiserver configures the external load balancer to forward traffic to the Service's virtual IP. The external load balancer then performs its own load balancing across the set of Pods backing the Service. This is a two-tier load balancing architecture: the external load balancer distributes traffic across the cluster's nodes, and the internal kube-proxy distributes traffic across the Pods on each node.

## 5. Ingress Controller

The Ingress controller is a separate component that sits at the edge of the cluster, handling HTTP and HTTPS traffic. It is not part of the Kubernetes control plane; it is a third-party component that implements the Ingress API. The Ingress object is a declarative specification of how external HTTP traffic should be routed to Services within the cluster. It specifies rules for matching URLs, hostnames, and paths, and it maps those rules to backend Services. The Ingress controller watches the Ingress objects and configures its own load balancer to implement those rules. This is a separate reconciliation loop from the Service reconciliation loop. The Ingress controller must be deployed as a Pod within the cluster, and it must be accessible from outside the cluster. This creates a chicken-and-egg problem: how do you deploy the Ingress controller if you don't have an Ingress controller to deploy it? The solution is to deploy the Ingress controller behind a LoadBalancer Service, or to use a cloud provider's managed Ingress controller.

## 6. Network Policy

The network policy feature adds yet another layer of complexity. A NetworkPolicy object specifies rules for allowing or denying traffic between Pods. It is implemented by the kube-proxy process, which installs additional iptables rules to enforce the policy. The iptables rules are installed in the FORWARD chain of the netfilter subsystem.

### Network Policy Example

```mermaid
graph TD;
    A[Pod A] -->| "Allow traffic from Pod B" | B[Pod B];
    B -->| "Allow traffic from Pod A" | A;
    C[Pod C] -->| "Deny traffic from Pod D" | D[Pod D];
```

Note: I removed the LaTeX code and replaced it with plain text or code blocks for math. I also removed the "TODO" and "TBD" placeholders and converted the bullet-point lists to rich narrative paragraphs. The Mermaid diagrams are rewritten to follow the strict syntax.
