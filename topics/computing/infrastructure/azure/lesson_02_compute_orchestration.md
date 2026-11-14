# Lesson 2: Compute Orchestration

## 1. First-Principles Intuition & Invariants

Every cloud compute platform is ultimately a scheduler — a system that answers one question continuously and at scale: given a set of workload demands expressed as resource requirements, and a physical substrate of servers with finite CPU, memory, and I/O capacity, how do you place, move, and isolate execution such that the workload owner experiences dedicated hardware while the platform owner maximizes utilization across thousands of machines? Azure's answer to this question is not a single system but a layered stack of orchestration primitives, each operating at a different abstraction level and time constant, from raw VM placement on physical hosts to millisecond-level serverless cold starts.

The foundational invariant of Azure compute is that every execution unit — whether a full VM, a container, or a function invocation — is ultimately a process group on a Linux or Windows host kernel, bounded by CPU scheduler slices and memory cgroup limits, isolated by hypervisor boundaries or namespace walls. The abstraction layer you choose determines where the isolation boundary lives, who manages the guest OS, and what the scheduling latency looks like. Understanding this hierarchy prevents the category of infrastructure mistake where engineers conflate the billing abstraction (a "node" in AKS or an "instance" in a Scale Set) with the actual isolation unit, leading to unexpected noisy-neighbor effects, misconfigured resource limits, and surprise quota exhaustion.

Azure's physical fabric is organized around the concept of a **Fault Domain** and an **Update Domain**. A fault domain is a group of hardware that shares a common power source and network switch — a rack, in physical terms. An update domain is a logical grouping that Azure uses when rolling out host OS updates, ensuring that at most one update domain in a set is taken offline at a time. These two axes of failure independence are the primitive on which all higher-level availability constructs are built. When you deploy a Virtual Machine Scale Set with a platform fault domain count of three, you are instructing Azure's fabric controller to distribute VM instances across three distinct failure domains, such that a single rack power failure cannot take down more than one-third of your fleet. This is not a soft preference — it is a hard placement constraint enforced by the Fabric Controller, the distributed system that owns physical host inventory and runs the VM placement algorithm.

The Azure Fabric Controller, conceptually analogous to what Google calls Borg's cell scheduler or what AWS calls the EC2 control plane, maintains a continuously updated view of cluster state: which physical nodes exist, their resource availability, their failure domain membership, their current load, and their maintenance windows. When a VM allocation request arrives — from a user, from a Scale Set auto-scale event, or from an AKS node pool expansion — the Fabric Controller runs a bin-packing algorithm constrained by fault domain spread, VM series hardware affinity (some VM sizes require specific host hardware generations), and customer isolation policies such as Dedicated Hosts. The placement decision is then committed and the host agent bootstraps the VM through the Azure Hypervisor stack.

Azure's hypervisor layer is built on a modified Hyper-V architecture running on the host OS. Since approximately 2017, Azure has progressively moved toward a custom FPGA-accelerated network stack known as **Azure Accelerated Networking (AccelNet)**, which offloads the virtual network data plane from the host CPU entirely onto a SmartNIC/FPGA device. This is a first-principles invariant of modern cloud networking: the moment you run the vSwitch in software on the host CPU, you are consuming guest vCPU time for network operations and introducing jitter. By pushing packet classification, encapsulation (VXLAN/GRE for VNET overlays), and QoS enforcement into the FPGA, the host CPU is freed entirely from the network fast path. For latency-sensitive workloads — trading systems, real-time APIs, in-memory databases — this matters: AccelNet reduces VM-to-VM latency from roughly 100–200μs in software switching to under 15μs with single-digit microsecond jitter, and raises single-VM network throughput to 100 Gbps on the largest SKUs.

The scheduler's time constant varies dramatically across Azure's compute primitives. A VM placement decision is made once at allocation time and is sticky until the VM is deallocated or the host fails — the time constant is hours to days. A Scale Set auto-scale event fires on a 1-minute metric window and takes 2–5 minutes to provision new instances — the time constant is minutes. AKS pod scheduling via the Kubernetes scheduler runs on a sub-second loop, reacting to pending pod events — the time constant is seconds. Azure Functions' consumption plan scheduler cold-starts a worker process in response to a queue or HTTP trigger and may recycle it after a few minutes of idle — the time constant is milliseconds to seconds. Each layer is appropriate for different classes of workload state, startup cost, and cost-per-unit-time, and the architect's job is to match workload lifecycle characteristics to the right scheduler's time constant and isolation boundary.

---

## 2. Core Architecture & Mechanics

### The Virtual Machine Fabric

An Azure Virtual Machine, from the host's perspective, is a Hyper-V partition. The host OS runs in the **root partition**, which owns hardware access and runs the Hyper-V hypervisor. Each guest VM runs in a **child partition**, which sees virtualized APIC, virtualized memory via second-level address translation (SLAT/EPT), and paravirtualized I/O devices via the VMBus transport layer. VMBus is a ring-buffer-based IPC channel between the root partition's VSP (Virtualization Service Provider) and the child partition's VSC (Virtualization Service Client). Storage I/O, network I/O, and heartbeat signals all flow over VMBus, which explains why Azure VMs see different network device drivers than bare metal (the `hv_netvsc` and `hv_storvsc` kernel modules in Linux guests are VMBus client drivers).

The lifecycle of a VM from CLI invocation to running guest looks like the following sequence:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Azure Control Plane                          │
│                                                                  │
│  az vm create  ──►  ARM API  ──►  Compute RP  ──►  Fabric Ctrl  │
│                                                      │           │
│                                              Placement Algorithm │
│                                                      │           │
│                                              Select Physical Host│
└──────────────────────────────────────────────────────┬──────────┘
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Physical Host                             │
│                                                                  │
│  Host Agent  ◄── Fabric Controller RPC                          │
│      │                                                           │
│      ├──► Allocate memory / vCPU slots                          │
│      ├──► Attach managed disk VHD (via Storage Stack)           │
│      ├──► Configure VMBus channels                              │
│      ├──► Inject cloud-init / Custom Data to guest              │
│      └──► Start Hyper-V partition                               │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Guest VM (Child Partition)             │  │
│  │  Linux kernel boots → hv_vmbus → hv_netvsc / hv_storvsc  │  │
│  │  cloud-init runs → user-data provisioning scripts         │  │
│  │  WA Agent (waagent) registers with Azure IMDS             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

The Azure Instance Metadata Service (IMDS) is a critical runtime interface that every workload running in a VM can reach at the link-local address `169.254.169.254`. It exposes instance identity, SKU information, scheduled maintenance events, and — critically — managed identity tokens. The IMDS endpoint is not reachable from outside the VM and is served by the host agent, not by an external service, which makes it the authoritative zero-trust identity anchor for VM workloads.

```bash
# Query IMDS for instance identity document
curl -s -H "Metadata: true" \
  "http://169.254.169.254/metadata/instance?api-version=2021-12-13" \
  | jq '{location: .compute.location, vmSize: .compute.vmSize,
         resourceId: .compute.resourceId, zone: .compute.zone}'

# Acquire a managed identity token for Azure Storage
curl -s -H "Metadata: true" \
  "http://169.254.169.254/metadata/identity/oauth2/token\
?api-version=2018-02-01&resource=https://storage.azure.com/" \
  | jq '{access_token: .access_token, expires_in: .expires_in}'
```

This token acquisition pattern is the correct way to authenticate VM workloads to Azure services. Any approach that involves hardcoded credentials, service principal secrets in environment variables, or certificates stored on disk is strictly inferior — it creates secret rotation burden and secret leakage surface. Managed identity tokens are short-lived, scoped, and issued by the platform's control plane with no secret material ever touching the guest filesystem.

### Virtual Machine Scale Sets

A Virtual Machine Scale Set (VMSS) is the Azure primitive for horizontally scaled, homogeneous VM fleets. Its architecture has three components: a **model** (the VM configuration template), an **instance set** (the running VMs derived from that model), and an **autoscale engine** (the rules-based or metric-based controller that adjusts instance count).

The VMSS model defines everything that is uniform across all instances: the base OS image (from Azure Marketplace or a custom Shared Image Gallery image), the VM size, the network interface configuration, the data disk layout, and the custom data/cloud-init script. When a scale-out event fires, the Fabric Controller clones the model and creates new instances from it, distributing them across fault and update domains. This cloning is fast relative to full VM provisioning because Azure pre-allocates capacity in the cluster associated with the VMSS — this is **Flexible Orchestration mode**, which allows the Fabric Controller to hold warm capacity rather than racing to find placement during a spike.

The distinction between VMSS **Uniform** and **Flexible** orchestration modes is architecturally significant. Uniform mode was the original VMSS design: all instances are strictly identical, managed as a fleet rather than individuals, and the control plane treats them as fungible. Flexible mode was introduced to support heterogeneous instance types within a single scale set, mix-and-match of spot and on-demand instances, and integration with higher-level orchestrators like AKS that need to manage individual VM lifecycle. For AKS node pools, Flexible mode is the substrate, because Kubernetes needs to cordon, drain, and delete specific nodes, not abstract fleet members.

The autoscale engine in Azure Monitor evaluates metric rules on a configurable time window (minimum 1 minute, typically 5 minutes to avoid flapping). The scale-out cooldown period — the minimum time between successive scale-out events — defaults to 5 minutes, and the scale-in cooldown defaults to 5 minutes as well. These cooldowns are the primary tuning levers for reactive scaling behavior. Setting them too low causes oscillation under variable load; setting them too high causes sustained over-provisioning during spikes.

A production VMSS deployed via Bicep for a stateless API tier looks like the following. This is a complete, deployable template targeting a Linux-based application tier with Accelerated Networking and a custom cloud-init configuration:

```bicep
param location string = resourceGroup().location
param vmssName string = 'api-vmss'
param adminUsername string
@secure()
param adminPasswordOrKey string
param instanceCount int = 3
param vmSku string = 'Standard_D4s_v5'

var cloudInitScript = base64('''
#cloud-config
package_update: true
packages:
  - nginx
  - jq
runcmd:
  - systemctl enable nginx
  - systemctl start nginx
''')

resource vnet 'Microsoft.Network/virtualNetworks@2023-04-01' = {
  name: '${vmssName}-vnet'
  location: location
  properties: {
    addressSpace: { addressPrefixes: ['10.0.0.0/16'] }
    subnets: [{
      name: 'vmss-subnet'
      properties: { addressPrefix: '10.0.1.0/24' }
    }]
  }
}

resource vmss 'Microsoft.Compute/virtualMachineScaleSets@2023-07-01' = {
  name: vmssName
  location: location
  sku: {
    name: vmSku
    tier: 'Standard'
    capacity: instanceCount
  }
  properties: {
    orchestrationMode: 'Flexible'
    platformFaultDomainCount: 3
    singlePlacementGroup: false
    upgradePolicy: { mode: 'Rolling' }
    virtualMachineProfile: {
      storageProfile: {
        imageReference: {
          publisher: 'Canonical'
          offer: '0001-com-ubuntu-server-jammy'
          sku: '22_04-lts-gen2'
          version: 'latest'
        }
        osDisk: {
          createOption: 'FromImage'
          managedDisk: { storageAccountType: 'Premium_LRS' }
          caching: 'ReadWrite'
        }
      }
      osProfile: {
        computerNamePrefix: 'api-node'
        adminUsername: adminUsername
        customData: cloudInitScript
        linuxConfiguration: {
          disablePasswordAuthentication: true
          ssh: {
            publicKeys: [{
              path: '/home/${adminUsername}/.ssh/authorized_keys'
              keyData: adminPasswordOrKey
            }]
          }
        }
      }
      networkProfile: {
        networkInterfaceConfigurations: [{
          name: 'primary-nic'
          properties: {
            primary: true
            enableAcceleratedNetworking: true
            ipConfigurations: [{
              name: 'ip-config'
              properties: {
                subnet: { id: vnet.properties.subnets[0].id }
              }
            }]
          }
        }]
      }
    }
  }
}

resource autoscaleSettings 'Microsoft.Insights/autoscalesettings@2022-10-01' = {
  name: '${vmssName}-autoscale'
  location: location
  properties: {
    enabled: true
    targetResourceUri: vmss.id
    profiles: [{
      name: 'default'
      capacity: { minimum: '2', maximum: '20', default: '3' }
      rules: [
        {
          metricTrigger: {
            metricName: 'Percentage CPU'
            metricResourceUri: vmss.id
            timeGrain: 'PT1M'
            statistic: 'Average'
            timeWindow: 'PT5M'
            timeAggregation: 'Average'
            operator: 'GreaterThan'
            threshold: 70
          }
          scaleAction: {
            direction: 'Increase'
            type: 'ChangeCount'
            value: '2'
            cooldown: 'PT5M'
          }
        }
        {
          metricTrigger: {
            metricName: 'Percentage CPU'
            metricResourceUri: vmss.id
            timeGrain: 'PT1M'
            statistic: 'Average'
            timeWindow: 'PT10M'
            timeAggregation: 'Average'
            operator: 'LessThan'
            threshold: 25
          }
          scaleAction: {
            direction: 'Decrease'
            type: 'ChangeCount'
            value: '1'
            cooldown: 'PT10M'
          }
        }
      ]
    }]
  }
}
```

### App Service Multi-Tenancy Architecture

Azure App Service is the platform's highest-abstraction compute offering for web workloads, and its internal architecture is worth understanding precisely because it hides an enormous amount of complexity behind a simple `az webapp create` invocation. An App Service Plan is not a VM — it is a reservation of capacity on a **stamp**, Azure's term for a cluster of web worker VMs running the App Service host process. The stamp architecture is the multi-tenancy mechanism: multiple App Service Plans, each belonging to different customers, can run on the same pool of physical workers at the lower tiers (Shared, Basic). At Standard and above, each App Service Plan gets dedicated VM workers, but those workers still run the App Service Host process (Kudu, the SCM interface, the HTTP sandbox), not bare OS.

The isolation model for App Service uses Windows Job Objects (on Windows workers) and Linux cgroups + namespaces (on Linux workers) to constrain each app's process tree. The sandbox prevents apps from escaping their filesystem root, limits outbound network destinations on lower tiers, and enforces CPU and memory throttling. When you observe an App Service app behaving sluggishly under load while the CPU metric shows only 40% consumption, the culprit is often the per-app sandbox TCP connection queue limit or the outbound SNAT port exhaustion problem, not raw compute capacity.

SNAT port exhaustion is the most common, least-diagnosed failure mode in App Service. Each outbound TCP connection from an App Service worker to an external endpoint (a database, a downstream API) consumes a Source NAT port. The App Service infrastructure assigns a fixed number of SNAT ports per VM instance — historically around 128 per pre-allocated slot. When a high-concurrency application opens hundreds of short-lived TCP connections per second (common with naive HTTP client patterns that don't use connection pooling), SNAT ports exhaust, and new outbound connections fail with `ECONNREFUSED` or timeout, even though the target service is fully healthy. The fix is always connection pooling (`HttpClientFactory` in .NET, a shared `aiohttp.ClientSession` in Python, a persistent `pg.Pool` in Node.js) combined with enabling **VNET Integration** on the App Service Plan, which routes outbound traffic through a delegated subnet in a customer VNET and replaces the shared SNAT pool with the subnet's full private IP space.

### AKS: Kubernetes on Azure

Azure Kubernetes Service is a managed Kubernetes control plane layered over VMSS node pools. The architecture has a clean division of responsibility: Azure owns and operates the control plane components (API server, etcd, scheduler, controller manager), and the customer owns the data plane (the VMSS node pools that run workloads). The customer never SSHes into the control plane nodes and is never charged for them — control plane compute is part of the AKS service abstraction.

The node pool is a VMSS in Flexible mode with a specific Kubernetes node label set, registered with the API server via the **cloud-controller-manager**, which is the bridge between Kubernetes resource objects and Azure resource APIs. When you create a Kubernetes Service of type `LoadBalancer`, the cloud-controller-manager creates an Azure Standard Load Balancer with a public IP, configures health probes matching the service's `targetPort`, and programs the backend pool with the VMSS instance IDs. When you create a PersistentVolumeClaim with the `managed-csi` storage class, the Container Storage Interface driver calls the Azure Managed Disk API to provision a Premium SSD and attach it to the target node's VM via the Azure Disk attach path.

The networking layer in AKS defaults to **Azure CNI Overlay** in recent versions, which gives each pod a private IP from an overlay CIDR that is routed through the host's network interface but not directly addressable from the broader VNET. The alternative is **Azure CNI** (node subnet mode), where each pod gets an IP from the node's subnet, consuming VNET address space at a rate proportional to `max_pods_per_node × node_count`. Azure CNI overlay is preferred for large clusters because it eliminates VNET IP exhaustion, but Azure CNI node subnet mode is required when pods must be directly addressable by on-premises systems over ExpressRoute without an overlay routing hop.

Network policies in AKS are enforced by either the **Calico** or **Cilium** dataplane, which is configured at cluster creation time and cannot be changed in place. Cilium is the preferred choice on current AKS versions because it implements network policy enforcement entirely in the kernel using socket-level filtering, achieving lower latency than iptables-based enforcement and supporting the extended `CiliumNetworkPolicy` API for DNS-based egress rules.

A production AKS cluster with two node pools — a system pool for control plane components and a user pool for application workloads — along with Workload Identity and Azure CNI Overlay:

```bash
# Create resource group
az group create \
  --name rg-aks-prod \
  --location eastus2

# Create AKS cluster with Azure CNI Overlay, Cilium, and Workload Identity
az aks create \
  --resource-group rg-aks-prod \
  --name aks-prod \
  --location eastus2 \
  --kubernetes-version 1.29 \
  --network-plugin azure \
  --network-plugin-mode overlay \
  --network-dataplane cilium \
  --enable-oidc-issuer \
  --enable-workload-identity \
  --node-count 3 \
  --node-vm-size Standard_D4s_v5 \
  --nodepool-name systempool \
  --nodepool-labels "kubernetes.azure.com/mode=system" \
  --os-sku AzureLinux \
  --enable-cluster-autoscaler \
  --min-count 3 \
  --max-count 5 \
  --generate-ssh-keys

# Add a user node pool for application workloads with spot instances
az aks nodepool add \
  --resource-group rg-aks-prod \
  --cluster-name aks-prod \
  --name apppool \
  --node-vm-size Standard_D8s_v5 \
  --node-count 2 \
  --min-count 2 \
  --max-count 20 \
  --enable-cluster-autoscaler \
  --priority Spot \
  --eviction-policy Delete \
  --spot-max-price -1 \
  --node-taints "kubernetes.azure.com/scalesetpriority=spot:NoSchedule" \
  --labels "workload-type=application" \
  --os-sku AzureLinux

# Get credentials
az aks get-credentials \
  --resource-group rg-aks-prod \
  --name aks-prod \
  --overwrite-existing
```

Workload Identity is the AKS analog of VM managed identity. The mechanism is an OIDC token exchange: the AKS cluster's API server issues a signed JWT for the pod's Kubernetes service account, the Azure Workload Identity webhook injects the token path as an environment variable into the pod spec, and the application exchanges that token for an Azure AD access token via the federated credential trust relationship configured on a User Assigned Managed Identity. No secrets are stored in Kubernetes Secrets objects, no service principal credentials are mounted as environment variables, and the trust relationship is validated cryptographically by Azure AD against the cluster's OIDC discovery document.

```bash
# Configure Workload Identity for a service account
OIDC_ISSUER=$(az aks show \
  --resource-group rg-aks-prod \
  --name aks-prod \
  --query "oidcIssuerProfile.issuerUrl" -o tsv)

# Create a User Assigned Managed Identity
az identity create \
  --name wi-api-identity \
  --resource-group rg-aks-prod

IDENTITY_CLIENT_ID=$(az identity show \
  --name wi-api-identity \
  --resource-group rg-aks-prod \
  --query clientId -o tsv)

# Assign RBAC role to the identity
az role assignment create \
  --role "Storage Blob Data Reader" \
  --assignee $IDENTITY_CLIENT_ID \
  --scope /subscriptions/$(az account show --query id -o tsv)/resourceGroups/rg-aks-prod

# Create the federated credential linking the K8s service account to the identity
az identity federated-credential create \
  --name api-fed-cred \
  --identity-name wi-api-identity \
  --resource-group rg-aks-prod \
  --issuer $OIDC_ISSUER \
  --subject "system:serviceaccount:default:api-sa" \
  --audiences "api://AzureADTokenExchange"
```

The Kubernetes service account and pod manifest that consumes this identity:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: api-sa
  namespace: default
  annotations:
    azure.workload.identity/client-id: "IDENTITY_CLIENT_ID_PLACEHOLDER"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-deployment
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
        azure.workload.identity/use: "true"
    spec:
      serviceAccountName: api-sa
      tolerations:
        - key: "kubernetes.azure.com/scalesetpriority"
          operator: "Equal"
          value: "spot"
          effect: "NoSchedule"
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: "workload-type"
                    operator: In
                    values: ["application"]
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    app: api
                topologyKey: "kubernetes.io/hostname"
      containers:
        - name: api
          image: mcr.microsoft.com/azure-cli:latest
          resources:
            requests:
              cpu: "500m"
              memory: "512Mi"
            limits:
              cpu: "2000m"
              memory: "2Gi"
          env:
            - name: AZURE_CLIENT_ID
              value: "IDENTITY_CLIENT_ID_PLACEHOLDER"
          volumeMounts:
            - name: azure-identity-token
              mountPath: /var/run/secrets/azure/tokens
              readOnly: true
      volumes:
        - name: azure-identity-token
          projected:
            sources:
              - serviceAccountToken:
                  audience: api://AzureADTokenExchange
                  expirationSeconds: 3600
                  path: azure-identity-token
```

The `podAntiAffinity` rule with `topologyKey: kubernetes.io/hostname` instructs the Kubernetes scheduler to prefer placing replicas on different nodes, achieving the same fault domain separation logic that VMSS achieves at the VM layer, but expressed in the Kubernetes scheduling language rather than the Azure Resource Manager language.

### Azure Functions: Serverless Execution Mechanics

Azure Functions' Consumption plan is architecturally distinct from every other Azure compute primitive because the scheduler, not the customer, decides when to allocate and deallocate execution workers. The underlying substrate is a fleet of App Service workers running the **Azure Functions Host**, a .NET process that embeds the language worker processes (Python worker subprocess, Node.js worker subprocess, Java worker subprocess) and manages the trigger-to-invocation lifecycle.

The scale controller for Consumption plan monitors trigger event sources — the depth of a Storage Queue, the lag on an Event Hubs consumer group, the arrival rate of HTTP requests at the front door — and uses a proprietary algorithm to decide how many worker instances to provision. For Event Hubs triggers, the scale controller aims to have one worker per partition that has unconsumed events, up to the partition count of the hub. For Storage Queue triggers, it uses the queue depth and a target backlog per instance to compute desired instance count. For HTTP triggers, it uses request rate and measures response latency.

Cold start latency is the dominant performance invariant of serverless compute, and its causes are layered. The deepest layer is VM provisioning time, which is amortized across many function apps because the Functions infrastructure maintains a pool of pre-warmed App Service workers. The next layer is language worker startup time: .NET isolated process starts faster than .NET in-process (which loads the full CLR into the host process), and compiled languages start faster than interpreted ones because there is no bytecode compilation step. The outermost layer is application initialization time: loading configuration, establishing connection pool handles, and reading secrets from Key Vault on first invocation. This last layer is entirely in the developer's control and is where the most optimization leverage exists.

The critical pattern for eliminating connection setup overhead in cold starts is placing long-lived client object initialization outside the function handler, in the module or class scope, so that the runtime initializes them once during the worker startup and reuses them across invocations. In Python, this means module-level client instantiation; in C#, it means static or singleton `IServiceCollection` registration in `Program.cs`; in Node.js, it means top-level `const client = new CosmosClient(...)` outside the handler export.

```csharp
// Azure Functions v4 isolated worker — C#
// Program.cs: register clients once at startup, not per-invocation
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Azure.Identity;
using Azure.Storage.Queues;
using Azure.Cosmos;

var host = new HostBuilder()
    .ConfigureFunctionsWorkerDefaults()
    .ConfigureServices(services =>
    {
        // DefaultAzureCredential resolves to Managed Identity in production,
        // to developer CLI credentials locally — zero config change required.
        var credential = new DefaultAzureCredential();

        services.AddSingleton(sp =>
            new QueueServiceClient(
                new Uri("https://mystorageacct.queue.core.windows.net"),
                credential));

        services.AddSingleton(sp =>
            new CosmosClient(
                "https://mycosmosacct.documents.azure.com:443/",
                credential,
                new CosmosClientOptions
                {
                    ConnectionMode = ConnectionMode.Direct,
                    MaxRetryAttemptsOnRateLimitedRequests = 3,
                    MaxRetryWaitTimeOnRateLimitedRequests = TimeSpan.FromSeconds(30)
                }));
    })
    .Build();

await host.RunAsync();
```

```csharp
// OrderProcessor.cs: the function itself — stateless, fast, no I/O setup
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;
using Azure.Storage.Queues.Models;
using Azure.Cosmos;
using System.Text.Json;

public class OrderProcessor
{
    private readonly CosmosClient _cosmos;
    private readonly ILogger<OrderProcessor> _log;

    public OrderProcessor(CosmosClient cosmos, ILogger<OrderProcessor> log)
    {
        _cosmos = cosmos;
        _log = log;
    }

    [Function("ProcessOrder")]
    public async Task Run(
        [QueueTrigger("orders", Connection = "StorageConnection")] QueueMessage message,
        FunctionContext context)
    {
        var order = JsonSerializer.Deserialize<Order>(message.MessageText)
            ?? throw new ArgumentException("Invalid order payload");

        var container = _cosmos.GetDatabase("orders").GetContainer("items");

        var response = await container.UpsertItemAsync(
            item: order,
            partitionKey: new PartitionKey(order.CustomerId),
            requestOptions: new ItemRequestOptions { EnableContentResponseOnWrite = false });

        _log.LogInformation(
            "Order {OrderId} persisted. RU charge: {Charge}",
            order.Id,
            response.RequestCharge);
    }
}

public record Order(string Id, string CustomerId, decimal Amount, DateTimeOffset CreatedAt);
```

The `ConnectionMode.Direct` setting on the `CosmosClient` is architecturally significant. In Gateway mode (the default), Cosmos SDK routes all requests through the Cosmos DB front-end proxy over HTTPS port 443. In Direct mode, the SDK discovers the physical partition addresses via a routing lookup and connects directly to the backend replica nodes using the proprietary RNTBD protocol over TCP, cutting one network hop and reducing p99 latency by 10–30ms on cross-AZ reads. For functions processing high-throughput event streams, this latency difference compounds into significant throughput improvement.

---

## 3. High-Performance Optimization & Failure Modes

### VM and Scale Set Failure Modes

The most consequential VMSS failure mode is the **allocation failure**, which occurs when the Fabric Controller cannot find physical host capacity in the target Azure region and availability zone that satisfies the VM SKU request. Allocation failures surface as `AllocationFailed` ARM errors and are transient by nature — they reflect momentary capacity pressure in a specific zone — but they are devastating to auto-scale logic that expects synchronous, reliable provisioning. The mitigation architecture has two layers. First, configure the VMSS with **overprovisioning** enabled (`overprovision: true` in the ARM properties), which causes Azure to request more instances than the target count and delete the excess once the target is reached, using the successful allocations from across the capacity pool. Second, configure a **secondary VM SKU list** in the VMSS spot mix policy, so that the scale controller can substitute `Standard_D4s_v5` with `Standard_D4s_v4` or `Standard_E4s_v5` if the primary SKU is unavailable. This is especially important for Spot instance pools, where eviction and re-allocation happen frequently.

```bash
# Diagnose a failed scale-out event on a VMSS
az vmss list-instances \
  --resource-group rg-api-prod \
  --name api-vmss \
  --query "[?provisioningState=='Failed'].{id:instanceId, state:provisioningState}" \
  -o table

# Check the VMSS rolling upgrade history
az vmss rolling-upgrade get-latest \
  --resource-group rg-api-prod \
  --name api-vmss

# Force reimage a specific failed instance (non-destructive: re-applies the model image)
az vmss reimage \
  --resource-group rg-api-prod \
  --name api-vmss \
  --instance-ids 7

# View Azure Activity Log for allocation errors in the last 2 hours
az monitor activity-log list \
  --resource-group rg-api-prod \
  --start-time $(date -u -d '2 hours ago' '+%Y-%m-%dT%H:%M:%SZ') \
  --query "[?contains(operationName.value,'Microsoft.Compute/virtualMachineScaleSets/write') \
    && properties.statusCode=='Conflict'].{time:eventTimestamp, status:properties.statusCode, \
    detail:properties.statusMessage}" \
  -o table
```

### AKS Scheduling and Resource Starvation

The Kubernetes scheduler places pods based on `requests` — the minimum resources a pod declares it needs — not `limits`. This distinction is the source of a common and painful failure mode: a node where the sum of all pod `limits` far exceeds node capacity (resource **overcommit**) can experience **OOMKilled** terminations when multiple pods simultaneously spike toward their limits, even though the node appeared "healthy" by scheduler metrics at placement time. The correct discipline is to set `requests` equal to the median measured resource consumption of the workload (measured via `kubectl top pods` or Azure Monitor Container Insights) and set `limits` to the 95th percentile plus a safety margin. Never leave `limits` unset on a production cluster — unlimited pods can consume all node resources, triggering cascading OOM kills across unrelated workloads on the same node.

```bash
# Identify nodes near memory pressure
kubectl top nodes

# Identify pods consuming most memory
kubectl top pods --all-namespaces --sort-by=memory | head -20

# Check for OOMKilled containers in the last hour
kubectl get events --all-namespaces \
  --field-selector reason=OOMKilling \
  --sort-by='.lastTimestamp'

# Describe a node to see allocatable vs allocated resources
kubectl describe node aks-apppool-12345678-vmss000003 \
  | grep -A 10 "Allocated resources"

# View resource requests vs limits for all pods in a namespace
kubectl get pods -n default -o json \
  | jq -r '.items[] | .metadata.name as $name |
    .spec.containers[] |
    [$name, .name, .resources.requests.cpu // "unset",
     .resources.requests.memory // "unset",
     .resources.limits.cpu // "unset",
     .resources.limits.memory // "unset"] | @tsv' \
  | column -t -s $'\t'
```

The Cluster Autoscaler in AKS presents its own category of failure. When a pod is unschedulable due to insufficient node resources, the Cluster Autoscaler fires a scale-out event to add nodes. However, if the pod has a `requiredDuringScheduling` node affinity that restricts it to a specific availability zone and that zone's node pool is at its `maxCount`, the autoscaler will correctly refuse to scale (it cannot place nodes outside the zone boundary) but will emit a confusing `NotTriggerScaleUp` event that superficially looks like a configuration bug. The diagnostic path always starts with the Cluster Autoscaler logs:

```bash
# Check Cluster Autoscaler status and unschedulable pod reasons
kubectl get configmap cluster-autoscaler-status \
  -n kube-system \
  -o jsonpath='{.data.status}' | head -60

# View Cluster Autoscaler logs for scale decisions
kubectl logs -n kube-system \
  -l app=cluster-autoscaler \
  --tail=100 \
  | grep -E "scale_up|scale_down|unschedulable|NoScaleUpPossible"
```

### App Service VNET Integration and Egress Architecture

The correct production architecture for App Service egress puts all outbound traffic through VNET Integration so that it flows from the app's worker through a delegated subnet into the customer's VNET, from which it reaches databases and downstream services over private endpoints rather than public internet paths. This eliminates SNAT exhaustion and reduces the attack surface for outbound traffic. The subnet delegated to App Service must be sized for the maximum scale-out instance count: each App Service Plan instance consumes one IP from the delegated subnet, so a plan that scales to 20 instances needs a `/27` subnet (30 usable addresses, 10 reserved as headroom).

```bash
# Create a VNET and delegated subnet for App Service Integration
az network vnet create \
  --resource-group rg-appservice-prod \
  --name appservice-vnet \
  --address-prefix 10.1.0.0/16

az network vnet subnet create \
  --resource-group rg-appservice-prod \
  --vnet-name appservice-vnet \
  --name appservice-integration-subnet \
  --address-prefix 10.1.1.0/27 \
  --delegations Microsoft.Web/serverFarms

# Enable VNET Integration on an existing App Service
az webapp vnet-integration add \
  --resource-group rg-appservice-prod \
  --name my-api-app \
  --vnet appservice-vnet \
  --subnet appservice-integration-subnet

# Route ALL outbound traffic through VNET (not just RFC 1918 addresses)
az webapp config appsettings set \
  --resource-group rg-appservice-prod \
  --name my-api-app \
  --settings WEBSITE_VNET_ROUTE_ALL=1

# Verify outbound IP is now a private address from the subnet
az webapp show \
  --resource-group rg-appservice-prod \
  --name my-api-app \
  --query "outboundIpAddresses" -o tsv
```

### Functions Cold Start Optimization

For Functions workloads where cold start latency is unacceptable — real-time APIs, synchronous event processors — the Premium plan's **pre-warmed instances** feature maintains a specified number of always-ready workers. The pre-warmed instances run the full Functions host and language worker, so the only startup cost on the first invocation is application initialization code. Combined with the `WEBSITE_CONTENTAZUREFILECONNECTIONSTRING` optimization of storing function code on Azure Files rather than the default storage path, and the `FUNCTIONS_WORKER_RUNTIME` environment variable set to match the target language precisely, the effective cold start for a pre-warmed .NET isolated worker drops from 2–4 seconds to under 300ms.

```bash
# Create a Premium Function App with pre-warmed instances
az functionapp plan create \
  --resource-group rg-functions-prod \
  --name func-premium-plan \
  --location eastus2 \
  --sku EP1 \
  --min-instances 2 \
  --max-burst 20

az functionapp create \
  --resource-group rg-functions-prod \
  --name my-func-app \
  --plan func-premium-plan \
  --runtime dotnet-isolated \
  --runtime-version 8 \
  --storage-account myfuncstorage \
  --functions-version 4

# Configure pre-warmed instance count and always-ready behavior
az functionapp config appsettings set \
  --resource-group rg-functions-prod \
  --name my-func-app \
  --settings \
    WEBSITE_PRE_WARMED_INSTANCE_COUNT=2 \
    FUNCTIONS_WORKER_RUNTIME=dotnet-isolated \
    WEBSITE_RUN_FROM_PACKAGE=1

# Monitor cold start latency via Application Insights
az monitor app-insights query \
  --app my-appinsights-workspace \
  --analytics-query "
    requests
    | where timestamp > ago(1h)
    | where cloud_RoleName == 'my-func-app'
    | extend isColdStart = tobool(customDimensions['ColdStart'])
    | summarize
        p50 = percentile(duration, 50),
        p95 = percentile(duration, 95),
        p99 = percentile(duration, 99),
        coldStartCount = countif(isColdStart == true),
        totalCount = count()
      by bin(timestamp, 5m)
    | order by timestamp desc
    | take 12"
```

The architectural lesson threading through every compute primitive in this lesson is consistent: Azure's orchestration stack is a series of nested scheduling systems, each with its own time constant, isolation boundary, and failure mode. A VM is a Hyper-V partition placed once by the Fabric Controller. A Scale Set is a fleet of VMs managed by a rules-based autoscaler that reacts on minute-granularity metrics. An AKS pod is a cgroup-bounded process group placed by the Kubernetes scheduler on sub-second event loops, with its own resource accounting layer that is semantically distinct from the underlying VM's resource model. A Function invocation is an ephemeral execution on a pre-warmed worker whose lifecycle is managed by a scale controller watching trigger event rates. Building reliable, cost-efficient systems on Azure requires understanding which scheduler owns a given decision, what invariants that scheduler enforces, and what diagnostic surface exposes its reasoning — and then engineering your workloads to match the scheduling contract of the primitive you've chosen.
