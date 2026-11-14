# Lesson 4: Execution Planning Orchestration

## 1. First-Principles Intuition & Invariants

Every production infrastructure system faces the same fundamental coordination problem: a desired state exists in human imagination and configuration files, an actual state exists in reality across dozens of APIs and cloud control planes, and the gap between them must be closed safely, predictably, and without interrupting live traffic. This is not a problem unique to Terraform. It is the same problem that distributed systems solve with consensus protocols, that databases solve with transaction logs, and that operating systems solve with copy-on-write page tables. What makes Terraform's approach distinctive is that it makes the reconciliation plan a first-class artifact — something you can inspect, diff, serialize, and approve before a single API call modifies reality.

The philosophical invariant at the heart of Terraform's design is that *mutation must be intentional*. Imperative infrastructure tools like raw shell scripts or Ansible playbooks collapse the planning and execution phases into a single pass. You cannot ask a Bash script what it *would* do before it does it. Terraform's architecture separates these phases completely: the plan phase is a pure read operation that constructs a change set by comparing desired state against observed state, and the apply phase is the effectful operation that drives reality toward the desired state. This separation is not merely ergonomic convenience — it is a correctness invariant. It means the system can guarantee that the apply phase will not encounter surprises that the plan phase did not anticipate, modulo races in the underlying provider APIs.

To understand why this matters for systems programmers and kernel engineers specifically, consider the analogy to memory-mapped I/O and atomic operations. When you issue a Compare-And-Swap instruction on a cache line, you are performing a check-then-act that is guaranteed to be atomic at the hardware level. The plan-then-apply model is Terraform's attempt to achieve a similar semantic at the infrastructure level — verify the precondition, compute the delta, then act. The critical difference is that cloud APIs are not atomic, and Terraform cannot prevent races between independent operators modifying the same resources. The state file serves as the optimistic lock: whoever holds the most recent state file version is authorized to plan and apply, and remote state backends with locking (DynamoDB, Terraform Cloud) enforce this through explicit lock acquisition.

The dependency graph is the second foundational invariant. Terraform models an infrastructure configuration as a directed acyclic graph where each resource or data source is a node and each reference between resources is a directed edge. This graph is constructed during the planning phase by the graph builder component within Terraform core. It is not optional or configurable — every Terraform plan is a traversal of this graph. The correctness of the plan depends entirely on the correctness of the graph, which in turn depends on the precision with which you express resource relationships. Implicit dependencies encoded via `depends_on` are blunt instruments; explicit data flow dependencies — where the output of one resource is consumed as the input attribute of another — are sharp instruments that give the graph builder precise, semantically meaningful edges. The practical consequence of this distinction is that explicit dependencies produce tighter, faster graphs with more parallelism, while `depends_on` forces sequential ordering across entire resource lifecycles even when the actual dependency is narrower.

The third invariant concerns what Terraform calls the *provider protocol boundary*. Terraform core is a pure orchestration engine. It knows nothing about AWS EC2 instances, Google Cloud VPCs, or Kubernetes namespaces. All knowledge of specific resource types lives in provider plugins, which communicate with core via gRPC over a versioned protocol (currently Plugin Protocol v6, formerly v5). This boundary is architecturally important because it means the planning algorithm in core operates on abstract resource schemas — typed key-value documents — rather than on API-specific constructs. The plan is computed by diffing two of these documents: the prior state (what Terraform last observed) and the desired configuration (what you declared). The provider's `PlanResourceChange` RPC is called during planning to allow provider-specific logic to normalize values, fill in computed attributes, and signal whether a change requires replacement rather than in-place modification. Understanding this boundary is essential for diagnosing mysterious plan behavior, because the final plan is a collaboration between core's graph-driven diffing logic and each provider's normalization logic.

## 2. Core Architecture & Mechanics

### The Plan Graph Construction Pipeline

When you execute `terraform plan`, Terraform proceeds through a deterministic sequence of internal phases. The entry point is the configuration loader, which reads all `.tf` files in the working directory, parses HCL into an AST, and resolves module calls recursively into a flat module tree. The module tree is then type-checked against provider schemas fetched from the provider plugin registry, producing a validated configuration object. This configuration object feeds the graph builder.

The graph builder constructs the dependency graph in two passes. The first pass creates one node per resource, data source, local value, output, and variable in the configuration. The second pass wires directed edges between nodes by analyzing attribute reference expressions: wherever a resource attribute references another resource by interpolation (`aws_subnet.private.id`), an edge is drawn from the referencing resource to the referenced resource. The resulting graph is then passed through several transformer stages, including the `ReferenceTransformer`, which adds edges for explicit references, the `OrphanResourceTransformer`, which adds nodes for resources present in the state but absent from the configuration (representing planned destroys), and the `ProviderTransformer`, which connects each resource node to its provider node.

```
Configuration Loader
        │
        ▼
   HCL AST Parser ──► Module Tree ──► Schema Validation
                                            │
                                            ▼
                               Graph Builder (Pass 1: Nodes)
                                            │
                                            ▼
                               Graph Builder (Pass 2: Edges)
                                            │
                              ┌─────────────┼─────────────┐
                              ▼             ▼             ▼
                   ReferenceTransformer  OrphanTransformer  ProviderTransformer
                              │             │             │
                              └─────────────┴─────────────┘
                                            │
                                            ▼
                               Topological Walk (Parallel)
                                            │
                              ┌─────────────┼─────────────┐
                              ▼             ▼             ▼
                     ReadState     PlanResourceChange   ReadDataSource
                              └─────────────┴─────────────┘
                                            │
                                            ▼
                                  Plan File (Binary)
                                  plan.tfplan (via -out)
```

The topological walk is where actual I/O occurs. Terraform walks the graph using a concurrent walker that respects topological ordering: a node becomes eligible for processing only after all of its upstream dependencies have been processed. For each resource node, the walker calls the provider's `ReadResource` RPC to refresh the prior state if `-refresh=true` (the default), then calls `PlanResourceChange` with the prior state, the proposed configuration, and any provider-supplied normalization. The provider returns a planned new state — a document that includes both the values known at plan time and placeholder sentinel values (shown as `(known after apply)`) for computed attributes that cannot be determined until the resource is actually created.

The concrete output of this walk is an ordered sequence of change objects. Each change object is a tuple of `(resource address, action, prior state, planned state)` where action is one of `no-op`, `create`, `read`, `update`, `replace`, or `delete`. The `replace` action is internally a `delete` followed by `create`, and its ordering (delete-then-create versus create-then-delete) is controlled by the `create_before_destroy` lifecycle flag. The full set of change objects, combined with the dependency graph, is serialized into a binary plan file when you pass `-out=plan.tffile` to `terraform plan`. This binary plan file is what `terraform apply plan.tffile` consumes — it does not re-plan, it executes the pre-computed change set exactly as recorded.

### Parallelism Model and the Concurrent Walker

Terraform's parallel execution model is explicit and bounded. By default, Terraform applies at most ten resource operations concurrently, controlled by the `-parallelism` flag. The concurrent walker maintains a semaphore-like count of active goroutines. When a node becomes eligible (all dependencies resolved), the walker checks whether the semaphore allows a new goroutine. If capacity is available, the node's operation is dispatched in a new goroutine; otherwise, it waits. This design ensures that the dependency graph determines *ordering* while the parallelism setting determines *concurrency*.

The practical consequence for infrastructure architects is that resource graph structure directly determines throughput during apply. Consider a configuration that provisions a VPC, then three subnets in parallel, then an EKS cluster that depends on all three subnets, then three node groups in parallel within the cluster. The critical path runs VPC → one subnet → EKS cluster → one node group, and the parallel resources on each tier can proceed concurrently. If you accidentally encode all three subnets as depending on each other (via an unnecessary `depends_on` chain), the parallel tier collapses to sequential, and your apply time triples for that segment.

The following configuration demonstrates both correct parallel structure and a subtle sequencing trap:

```hcl
# variables.tf
variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "availability_zones" {
  type    = list(string)
  default = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

# main.tf
terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "my-tfstate-prod"
    key            = "networking/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.region
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "main-vpc"
  }
}

# These three subnets have no dependency on each other.
# Their only shared dependency is aws_vpc.main.
# The concurrent walker will dispatch all three simultaneously
# once aws_vpc.main is applied. This is correct.
resource "aws_subnet" "private" {
  count             = 3
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "private-subnet-${count.index}"
    Tier = "private"
  }
}

resource "aws_subnet" "public" {
  count             = 3
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index + 3)
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "public-subnet-${count.index}"
    Tier = "public"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "main-igw"
  }
}

resource "aws_eip" "nat" {
  count  = 3
  domain = "vpc"

  # Correct: depends on IGW for NAT Gateway EIP allocation order,
  # but NOT on each other. All three EIPs are allocated in parallel.
  depends_on = [aws_internet_gateway.main]

  tags = {
    Name = "nat-eip-${count.index}"
  }
}

resource "aws_nat_gateway" "main" {
  count         = 3
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name = "nat-gw-${count.index}"
  }
}

resource "aws_route_table" "private" {
  count  = 3
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = {
    Name = "private-rt-${count.index}"
  }
}

resource "aws_route_table_association" "private" {
  count          = 3
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "public-rt"
  }
}

resource "aws_route_table_association" "public" {
  count          = 3
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}
```

This configuration encodes the dependency structure through data flow: `aws_subnet.private` depends on `aws_vpc.main` because it consumes `aws_vpc.main.id`. The three private subnets depend on the same VPC but not on each other, so they form a parallel tier in the graph. The NAT gateways form a downstream tier that also fans out in parallel. The graph builder sees these references and constructs edges accordingly without any `depends_on` annotation.

### Change Set Calculation: The Diff Algorithm

Terraform's change set calculation operates on the resource schema, which describes each attribute with a type, optionality, sensitivity, and computability. When comparing the prior state to the desired configuration, Terraform performs a structural diff of the two typed documents. The diff engine handles several special cases that systems architects must understand to avoid unexpected plan behavior.

Computed attributes — those marked `Computed: true` in the provider schema and absent from the configuration — are never treated as a desired-state constraint. If the prior state contains `arn = "arn:aws:iam::123456789012:role/my-role"` and the configuration does not specify `arn`, Terraform treats the ARN as a provider-managed output and never diffs it against the configuration. This is the mechanism that allows resources to have outputs you cannot specify.

The more subtle case is `Computed + Optional` attributes. These are attributes that you *may* specify in configuration, but which the provider will auto-populate if you do not. The `aws_vpc` resource's `default_security_group_id` is a canonical example. If you have never specified this attribute, Terraform records its last-known value from the provider in state and treats any provider-returned change as authoritative during planning. If you specify a value, Terraform treats your specified value as the desired state and diffs against it. The transition from "unspecified" to "specified" for such an attribute always triggers a plan diff, which frequently surprises engineers who add an explicit value to a previously unconstrained attribute for the first time.

The replace decision — whether a modification triggers in-place update or destroy-then-recreate — is made by the provider's `PlanResourceChange` implementation. Some attribute modifications cannot be performed in place because the underlying API does not support partial updates. The provider signals this by returning a response where the planned new state includes the `RequiresReplace` flag for the modified attributes. Terraform core aggregates these flags into the `replace` action for the whole resource. The `create_before_destroy` lifecycle flag then controls whether the new instance is created before the old one is destroyed, which is critical for zero-downtime replacements of resources that have exclusive naming constraints (like security groups, IAM roles, or DNS records).

### Lifecycle Meta-Arguments: Precise Control Over Change Semantics

Lifecycle meta-arguments are HCL-level directives embedded within a resource block that modify how Terraform's planning and apply logic handles that specific resource. They are not provider-specific; they are honored by Terraform core regardless of which provider manages the resource.

The `create_before_destroy` argument inverts the default destroy-before-create sequence during resource replacement. This matters enormously for resources that cannot have two instances with the same name simultaneously, or for resources that downstream systems depend on. Consider an `aws_security_group` referenced by multiple EC2 instances: if Terraform destroys the security group before creating its replacement, the EC2 instances will briefly have no security group assigned. With `create_before_destroy = true`, Terraform creates the replacement security group first, updates all downstream resources to reference the new one, then destroys the original. The constraint is that the new and old resource must be able to coexist during the transition window, which requires the new resource to have a different name than the old one — typically accomplished by using random suffixes via `random_pet` or `random_id` resources on names that must be unique.

The `prevent_destroy` argument converts any planned destruction of the resource into a plan-time error. It is a safety interlock, not a secret — it does not hide the resource from Terraform's awareness, and it does not persist if you remove the flag from configuration. Its value is in catching accidental destroys caused by resource renaming, module restructuring, or configuration mistakes. Production databases, KMS keys, and S3 buckets with critical data should carry this flag as a matter of discipline.

The `ignore_changes` argument instructs the planning algorithm to treat specified attributes as outside Terraform's desired-state domain for the purpose of diffing. When the prior state and the live resource diverge on an ignored attribute, Terraform will not compute a change for that attribute. This is the mechanism for coexisting with external automation that modifies resource attributes Terraform also manages — for example, an autoscaler that modifies `desired_capacity` on an ASG, or a tag enforcement tool that adds tags to resources. The `ignore_changes = all` variant is a blunt override that tells Terraform to never compute changes for any attribute of the resource, effectively making it a data source that only records its initial creation.

```hcl
resource "aws_autoscaling_group" "app" {
  name                = "app-asg"
  min_size            = 2
  max_size            = 20
  desired_capacity    = 4
  vpc_zone_identifier = aws_subnet.private[*].id

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  lifecycle {
    # The external autoscaler owns desired_capacity at runtime.
    # Terraform owns the min/max envelope and launch template.
    ignore_changes = [desired_capacity]

    # Prevent accidental destruction of the ASG.
    prevent_destroy = true

    # Create the new ASG before destroying the old one
    # during launch template version updates that require replacement.
    create_before_destroy = true
  }

  tag {
    key                 = "Name"
    value               = "app-node"
    propagate_at_launch = true
  }
}
```

The `replace_triggered_by` argument, introduced in Terraform 1.2, closes a long-standing gap in the lifecycle model. Before its introduction, there was no way to force replacement of a resource when a *different* resource changed in a way that did not modify any attribute reference. The canonical use case is rotating a TLS certificate or a secret: the secret value changes in an external system, Terraform detects the change via a data source, but no attribute of the consuming resource (say, a VM that reads the secret on boot) actually changes in the plan, so Terraform does not schedule a replacement. With `replace_triggered_by`, you can express that the VM must be replaced whenever the secret version resource changes.

```hcl
resource "aws_secretsmanager_secret_version" "app_creds" {
  secret_id     = aws_secretsmanager_secret.app_creds.id
  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
  })
}

resource "aws_instance" "app" {
  ami           = data.aws_ami.app.id
  instance_type = "m6i.large"
  subnet_id     = aws_subnet.private[0].id

  user_data = base64encode(templatefile("${path.module}/userdata.sh", {
    secret_arn = aws_secretsmanager_secret.app_creds.arn
  }))

  lifecycle {
    # Force instance replacement whenever the secret version changes.
    # This ensures instances always boot with the current credentials.
    replace_triggered_by = [aws_secretsmanager_secret_version.app_creds]
  }

  tags = {
    Name = "app-instance"
  }
}
```

### Serializing and Inspecting Plans

The `-out` flag to `terraform plan` serializes the computed change set to a binary plan file. This file is not human-readable by default, but `terraform show -json plan.tfplan` emits a structured JSON document that is fully machine-parseable. CI/CD pipelines should routinely parse this JSON to enforce policy constraints before apply — checking that no production databases are scheduled for destruction, that no IAM policies with `"*"` are being added, or that no untagged resources are being created.

The JSON plan document has a top-level structure that systems engineers should internalize:

```json
{
  "format_version": "1.2",
  "terraform_version": "1.6.3",
  "variables": { ... },
  "planned_values": {
    "root_module": {
      "resources": [ ... ],
      "child_modules": [ ... ]
    }
  },
  "resource_changes": [
    {
      "address": "aws_vpc.main",
      "type": "aws_vpc",
      "name": "main",
      "change": {
        "actions": ["create"],
        "before": null,
        "after": {
          "cidr_block": "10.0.0.0/16",
          "enable_dns_hostnames": true,
          "enable_dns_support": true
        },
        "after_unknown": {
          "id": true,
          "arn": true,
          "default_security_group_id": true
        }
      }
    }
  ],
  "configuration": { ... },
  "relevant_attributes": [ ... ],
  "timestamp": "2024-01-15T14:23:11Z"
}
```

The `after_unknown` map is particularly valuable. It identifies exactly which attributes cannot be determined until apply time because they are computed by the provider API. When downstream resources depend on these unknowns, the plan will show `(known after apply)` for those dependent attribute slots, and the apply phase will resolve them in topological order as each upstream resource completes.

## 3. High-Performance Optimization & Failure Modes

### Optimizing Plan Performance at Scale

Large Terraform configurations — those managing thousands of resources across dozens of modules — commonly suffer from planning latency measured in minutes rather than seconds. The primary cause is the refresh phase: by default, `terraform plan` calls `ReadResource` on every resource in the state before computing the plan. With 2,000 resources spread across AWS, this produces 2,000 sequential-or-mildly-parallel API calls, and even at 100ms per call with maximum parallelism of ten, the refresh phase takes roughly 20 seconds at best. In practice, provider rate limits, AWS API throttling, and cross-region resources can push this to several minutes.

The first optimization lever is `-refresh=false`. This instructs Terraform to skip the refresh phase entirely and compute the plan based solely on what is already recorded in the state file. This is safe in environments where you are confident no out-of-band changes have occurred — for example, in a CI/CD pipeline where Terraform is the sole infrastructure manager and no human operators apply changes manually. The tradeoff is that drift detection requires periodic explicit runs of `terraform refresh` or `terraform plan -refresh=true`.

The second optimization lever is state decomposition. A monolithic state file with 2,000 resources is a correctness hazard as well as a performance problem: every plan locks the entire state, meaning no two operators can run concurrent plans against different portions of the infrastructure. Decomposing state across logical boundaries — networking, compute, data, IAM — reduces the resource count per state to a manageable size, parallelizes operator workflows, and limits the blast radius of a runaway apply. The dependency between state files is managed through data sources, specifically `terraform_remote_state`, which allows one configuration to read the outputs of another's state file.

The third lever is targeted planning with `-target`. When you need to plan and apply a specific resource or module in isolation, `-target` restricts the graph walk to the named resource and its transitive dependencies. This is powerful for rapid iteration during development or for unblocking a specific resource that is stuck in an error state. However, it must be treated as an emergency tool rather than a workflow pattern: `-target` applies produce states that are inconsistent with the full configuration, and running a full plan immediately after a targeted apply will often show diffs on resources that the targeted apply left in an intermediate state.

### Drift and State Corruption

Infrastructure drift — the divergence between Terraform state and reality caused by out-of-band changes — is the most common source of unexpected plan behavior in production. When a human engineer manually modifies a security group rule, resizes a database instance, or rotates a managed certificate via the cloud console, the state file still records the old values. The next `terraform plan` will generate a change set that attempts to revert the manual change, which may cause an outage if the manual change was intentional and load-bearing.

The structured response to drift is to either reconcile it into Terraform state or document it as an intentional exception via `ignore_changes`. Reconciling drift is done with `terraform import` for newly created resources or via `terraform refresh` followed by manual state file inspection for modified existing resources. The `terraform state` subcommands are the scalpel for surgical state manipulation: `terraform state rm` removes a resource from state without destroying it (useful when you want Terraform to stop managing a resource), `terraform state mv` renames a resource address in state (essential during module refactors), and `terraform state replace-provider` migrates resources between provider versions.

A more serious pathology is state file corruption, which typically occurs when two concurrent applies write conflicting state. Properly configured remote backends with locking prevent this: the DynamoDB-backed S3 backend acquires an exclusive lock at the start of any state-mutating operation and releases it on completion. If a Terraform process crashes mid-apply, the lock may remain held and must be manually cleared with `terraform force-unlock <lock-id>`. The lock ID is printed at the start of the apply and is also stored in the DynamoDB lock table, making it recoverable even if the terminal output is lost.

### Error Propagation and Partial Apply Recovery

When a Terraform apply encounters an error mid-execution, it does not roll back. This is a deliberate design decision rooted in the same constraint that prevents transactional semantics in distributed systems: cloud APIs are not transactional, and rolling back a partially created VPC with subnets, route tables, and security groups requires performing an equal amount of destructive work that carries its own failure modes. Instead, Terraform records the state of every resource it successfully created, modified, or destroyed before the error occurred, writes this partial state to the backend, and reports the error along with a summary of what succeeded.

The recovery workflow begins with running `terraform plan` against the partial state. Because the state now records the resources that were successfully created, the plan will show only the remaining work: the resources that failed, plus any resources that depended on the failed ones. In most cases, simply re-running `terraform apply` on the original plan file is sufficient, because the successfully applied resources will show as `no-op` in the new plan and the failed resources will be retried.

The edge case that causes the most operational pain is provider-side partial success: a resource creation call that succeeds at the API level but then fails during a configuration phase, such as an EC2 instance that launches successfully but whose user data script exits with an error code during initialization. From Terraform's perspective, the resource was created successfully — the provider returned a resource ID — and the resource is recorded in state. The user data failure is not visible to Terraform. The engineer must detect this through external monitoring, manually terminate the instance, remove it from state with `terraform state rm`, and re-apply.

### Advanced Pattern: Provider-Parallel Multi-Region Deployment

A production pattern worth dissecting is deploying the same infrastructure across multiple AWS regions using provider aliasing. This pattern uses Terraform's parallelism model to create region-specific resources concurrently, which is significantly faster than sequential per-region Terraform runs.

```hcl
# providers.tf
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

provider "aws" {
  alias  = "eu_west_1"
  region = "eu-west-1"
}

provider "aws" {
  alias  = "ap_southeast_1"
  region = "ap-southeast-1"
}

# modules/regional_vpc/variables.tf
variable "vpc_cidr" {
  type = string
}

variable "region_name" {
  type = string
}

# modules/regional_vpc/main.tf
terraform {
  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = "~> 5.0"
      configuration_aliases = [aws]
    }
  }
}

resource "aws_vpc" "regional" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name   = "${var.region_name}-vpc"
    Region = var.region_name
  }
}

resource "aws_default_security_group" "regional" {
  vpc_id = aws_vpc.regional.id

  tags = {
    Name = "${var.region_name}-default-sg"
  }
}

# modules/regional_vpc/outputs.tf
output "vpc_id" {
  value = aws_vpc.regional.id
}

output "default_sg_id" {
  value = aws_default_security_group.regional.id
}

# root/main.tf
module "vpc_us_east_1" {
  source = "./modules/regional_vpc"

  providers = {
    aws = aws.us_east_1
  }

  vpc_cidr    = "10.1.0.0/16"
  region_name = "us-east-1"
}

module "vpc_eu_west_1" {
  source = "./modules/regional_vpc"

  providers = {
    aws = aws.eu_west_1
  }

  vpc_cidr    = "10.2.0.0/16"
  region_name = "eu-west-1"
}

module "vpc_ap_southeast_1" {
  source = "./modules/regional_vpc"

  providers = {
    aws = aws.ap_southeast_1
  }

  vpc_cidr    = "10.3.0.0/16"
  region_name = "ap-southeast-1"
}

# Global Route53 health checks referencing regional endpoints.
# These have explicit depends_on because they consume module outputs
# that are not referenced directly in their attribute blocks.
resource "aws_route53_health_check" "regional" {
  count             = 3
  fqdn              = "api.${["us-east-1", "eu-west-1", "ap-southeast-1"][count.index]}.example.com"
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = 3
  request_interval  = 30

  depends_on = [
    module.vpc_us_east_1,
    module.vpc_eu_west_1,
    module.vpc_ap_southeast_1
  ]

  tags = {
    Name = "regional-health-check-${count.index}"
  }
}
```

In this configuration, the three module calls share no data dependencies. The graph builder creates three independent subgraphs, one per module, and the concurrent walker dispatches all three simultaneously. The three VPCs and their sub-resources are created in parallel across three AWS regions, bounded only by the `-parallelism` setting. The Route53 health checks use `depends_on` at the module level because they depend on the regional VPCs being fully operational but do not consume any specific VPC attribute — the dependency is on operational readiness rather than on a specific output value.

### Precondition and Postcondition Contracts

Terraform 1.2 introduced `precondition` and `postcondition` blocks within resource and output lifecycle configurations, bringing contract-driven validation directly into the planning and apply phases. A precondition is evaluated before the resource operation begins; if it fails, Terraform aborts the operation for that resource and propagates the error through the dependency graph. A postcondition is evaluated after the resource operation succeeds; if it fails, the resource is considered failed even though the API operation completed, and Terraform marks the resource as tainted.

These constructs are particularly valuable for catching semantic errors that fall below Terraform's type system but above the cloud API's validation layer. An IAM policy document that is syntactically valid JSON but semantically incorrect — say, one that grants `s3:*` on `*` to all principals — will pass both Terraform's type validation and AWS's JSON parser. A precondition can enforce internal policy rules before the resource is created:

```hcl
resource "aws_iam_policy" "app" {
  name   = "app-policy"
  policy = data.aws_iam_policy_document.app.json

  lifecycle {
    precondition {
      condition = !can(
        regex("\"Effect\":\\s*\"Allow\".*\"Action\":\\s*\"\\*\".*\"Resource\":\\s*\"\\*\"",
          data.aws_iam_policy_document.app.json)
      )
      error_message = "IAM policy must not grant wildcard actions on wildcard resources. Review the policy document and scope down permissions."
    }

    postcondition {
      condition     = self.arn != ""
      error_message = "IAM policy creation succeeded but returned an empty ARN. This indicates a provider-side error."
    }
  }
}
```

The `self` reference in a postcondition refers to the resource's post-apply state, giving you access to all computed attributes that were `(known after apply)` during planning. This is the mechanism for validating that a resource was created with the expected configuration — confirming that the provider honored your specification rather than silently truncating or modifying values.

The strategic value of these contracts is that they move failures left in the pipeline. A postcondition failure is detected during `terraform apply` rather than during a downstream integration test or, worse, during a production incident. A precondition failure is detected during `terraform plan`, before any infrastructure is modified. For teams operating at scale across many modules and many engineers, preconditions and postconditions are the equivalent of type signatures in a strongly typed language: they make the contract of each resource explicit and enforceable, turning silent semantic errors into loud, attributable failures.
