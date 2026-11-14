# Lesson 4: Runner Infrastructure and Security Hardening

## 1. First-Principles Intuition & Invariants

GitHub Actions fundamentally operates as a distributed job execution system where untrusted user code runs on ephemeral compute substrates. The security model balances two competing tensions: enabling developers to execute arbitrary commands with sufficient privileges to build, test, and deploy software, while preventing lateral movement, credential exfiltration, and persistence attacks across workflow runs. This duality shapes every architectural decision in runner infrastructure, from process isolation boundaries to identity federation mechanisms.

At its core, a GitHub Actions runner is a continuously polling agent that maintains a persistent WebSocket connection to GitHub's workflow orchestration service. When a workflow event triggers—whether from a push, pull request, or manual dispatch—the orchestration layer consults the workflow YAML's `runs-on` declaration to select an appropriate runner pool. For hosted runners, GitHub provisions ephemeral virtual machines from Azure cloud capacity, guaranteeing clean state through full VM teardown after each job. For self-hosted runners, the organization assumes responsibility for isolation guarantees, introducing operational complexity in exchange for control over hardware specifications, network topology, and regulatory compliance boundaries.

The security invariant that governs runner infrastructure is **ephemeral execution with bounded trust**. Each workflow job receives a freshly provisioned execution environment with no residual filesystem state, environment variables, or cached credentials from prior runs. GitHub enforces this through hypervisor-level isolation for hosted runners and strongly recommends Docker-based ephemeral containers for self-hosted deployments. The trust boundary extends to the `GITHUB_TOKEN`, an automatically provisioned OAuth token with repository-scoped permissions that expires at job completion. This token's privilege set follows the principle of least privilege: by default, it grants read access to repository contents and write access only to workflow artifacts and checks, with explicit opt-in required for write operations on code, issues, or packages.

Authentication and authorization in Actions workflows operate through three distinct identity mechanisms. The `GITHUB_TOKEN` provides transient, job-scoped access suitable for repository operations within the workflow itself. For interactions with external cloud providers—AWS, Google Cloud, Azure—GitHub supports OpenID Connect (OIDC) token federation, allowing workflows to assume cloud IAM roles without storing long-lived credentials in repository secrets. OIDC tokens contain cryptographically signed claims about the workflow context: repository name, branch ref, commit SHA, and actor identity. Cloud providers validate these tokens against GitHub's public JWKS endpoint and map them to IAM roles through trust policies that enforce workflow origin constraints. This federation model eliminates the operational burden of rotating service account keys while providing fine-grained control over which workflows can assume which cloud identities.

The third identity layer involves repository secrets and organization-level secrets, encrypted at rest using AES-256-GCM and scoped to specific repositories or environments. Secrets never appear in workflow logs due to automatic masking performed by the runner agent, which intercepts stdout and stderr streams and replaces exact byte sequences matching registered secret values with `***`. However, this masking operates as a defense-in-depth measure rather than a cryptographic guarantee—sufficiently motivated attackers can exfiltrate secrets through encoding transformations, timing channels, or side-channel attacks like network requests to attacker-controlled endpoints.

GitHub's permission model for workflows distinguishes between three privilege domains: repository permissions (controlled by `GITHUB_TOKEN`), environment protection rules (approval gates and branch restrictions), and organization-level policies (runner group constraints and required workflow policies). Repository permissions default to restrictive for public repositories to prevent supply chain attacks via forked pull requests. A critical security invariant here is that pull requests from forks execute with read-only tokens and cannot access repository secrets unless explicitly approved by a maintainer. This prevents arbitrary code execution with elevated privileges in response to external contributions, a common attack vector in open-source ecosystems.

Audit logging provides tamper-evident records of all workflow executions, including runner selection, secret access patterns, and permission escalations. GitHub stores these logs for 90 days in the web UI and exposes them through the Audit Log API with structured JSON payloads containing actor identity, resource targets, and timestamp metadata. For compliance-sensitive organizations, streaming these logs to external SIEM systems like Splunk or Datadog enables real-time anomaly detection and forensic investigation. The audit trail includes runner registration events, allowing security teams to detect unauthorized self-hosted runners that could serve as persistence mechanisms or exfiltration channels.

The distinction between hosted and self-hosted runners fundamentally alters the threat model. Hosted runners provide strong isolation through full VM provisioning but impose limitations on network topology—they originate from dynamic Azure IP ranges that complicate firewall allowlisting. Self-hosted runners enable fixed IP addresses, custom hardware configurations, and access to private network resources, but require organizations to maintain ephemeral execution guarantees through container lifecycle management or VM snapshotting. The failure mode here is persistent compromise: if an attacker gains code execution on a long-lived self-hosted runner, they can inject backdoors into the runner agent process, intercept subsequent workflow executions, and exfiltrate secrets across organizational boundaries.

## 2. Core Architecture & Mechanics

The GitHub Actions runner agent operates as a continuously running process that maintains bidirectional communication with GitHub's workflow orchestration backend through a multiplexed WebSocket connection. This architecture inverts the traditional CI polling model—rather than periodically checking for new jobs, the runner establishes a persistent connection and receives job assignments through server-initiated push messages. The WebSocket transport provides low-latency job dispatch while allowing GitHub to implement backpressure and load balancing across runner pools.

When an organization registers a self-hosted runner, the process generates a unique runner token by authenticating against GitHub's runner registration API with a time-limited registration token obtained from the repository or organization settings. This exchange produces a long-lived runner credential stored in `.runner` configuration files with restrictive filesystem permissions (mode 0600, root ownership). The runner agent reads this credential on startup and uses it to authenticate the WebSocket handshake, after which all communication proceeds over TLS 1.3 with certificate pinning to GitHub's infrastructure.

The job assignment protocol operates through a bidirectional message queue. GitHub's orchestration layer maintains a priority queue of pending jobs, ordered by workflow trigger time and job dependencies declared through `needs` clauses. When a runner connects and signals availability, the backend performs runner matching against job requirements: operating system (`runs-on: ubuntu-latest`), architecture (x64, ARM64), and label constraints for self-hosted pools. The assignment algorithm prefers idle runners over busy ones and implements fairness policies to prevent starvation of low-priority jobs.

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Workflow Orchestration                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │  Trigger     │─────▶│  Job Queue   │─────▶│  Runner      │  │
│  │  Event       │      │  (Priority)  │      │  Matcher     │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
└────────────────────────────────┬────────────────────────────────┘
                                 │ WebSocket (TLS 1.3)
                                 │ Runner Assignment Message
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Runner Agent Process                     │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │  Message     │─────▶│  Job         │─────▶│  Execution   │  │
│  │  Handler     │      │  Dispatcher  │      │  Context     │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│         │                                            │           │
│         │                                            ▼           │
│         │                                   ┌──────────────┐    │
│         └──────────────────────────────────▶│  Log Stream  │    │
│                                             │  Uploader    │    │
│                                             └──────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌───────────────────────────┐
                    │  Isolated Execution Env   │
                    │  (Docker / VM / Bare)     │
                    └───────────────────────────┘
```

Upon receiving a job assignment, the runner agent downloads the workflow definition and action metadata from GitHub's artifact storage. Actions can execute through three runtime models: JavaScript actions run directly in the Node.js runtime embedded in the runner agent; Docker container actions spawn an isolated container with the action's Dockerfile; composite actions expand into a sequence of sub-steps executed within the same job context. The runner maintains a working directory hierarchy for each job, typically structured as `_work/<repo>/<repo>` to isolate filesystem state between concurrent jobs on the same runner.

The `GITHUB_TOKEN` provisioning mechanism operates through a just-in-time issuance protocol. When a job begins execution, the runner requests a token from GitHub's token service by presenting the job's cryptographic context—workflow ID, run ID, and job ID—signed by the runner's authentication credential. GitHub validates this signature, consults the repository's permission configuration (defined in workflow YAML through `permissions:` blocks), and mints a JWT token with an audience claim of `https://github.com/<owner>` and subject claim identifying the workflow. This token contains a JSON payload with permission scopes encoded as boolean flags: `contents: read`, `issues: write`, `packages: write`, etc. The token's expiration timestamp aligns with the job's maximum timeout, typically 6 hours for hosted runners and configurable for self-hosted runners.

OIDC token federation extends this model to external identity providers by generating a secondary JWT specifically formatted for cloud provider validation. When a workflow step invokes `aws sts assume-role-with-web-identity` or `gcloud auth login --cred-file`, the GitHub-issued OIDC token serves as proof of identity. The token's claims include structured workflow context: `repository_owner`, `repository`, `ref`, `sha`, and `workflow`. Cloud providers configure trust relationships by specifying allowed repository patterns in their IAM role trust policies. AWS, for example, validates the token's signature against GitHub's JWKS endpoint at `https://token.actions.githubusercontent.com/.well-known/jwks`, then evaluates trust policy conditions like `StringLike: {"token.actions.githubusercontent.com:sub": "repo:octo-org/octo-repo:ref:refs/heads/main"}` to restrict which workflows can assume the role.

The practical implementation of OIDC federation in an AWS workflow demonstrates the end-to-end credential flow:

```yaml
name: Deploy to AWS with OIDC
on:
  push:
    branches: [main]

permissions:
  id-token: write    # Required for OIDC token issuance
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsDeployRole
          aws-region: us-east-1

      - name: Deploy application
        run: |
          aws s3 sync ./build s3://production-bucket/
          aws cloudfront create-invalidation --distribution-id EDFDVBD6EXAMPLE --paths "/*"
```

The `configure-aws-credentials` action internally calls GitHub's token API endpoint to retrieve an OIDC token, then exchanges it with AWS STS to obtain temporary security credentials valid for the session duration. These credentials populate standard AWS environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`) that subsequent commands consume without requiring long-lived IAM user keys stored in repository secrets.

Self-hosted runner deployments require explicit lifecycle management to maintain ephemeral execution guarantees. The recommended pattern uses Docker-in-Docker or virtual machine snapshots to restore clean state between jobs. For Kubernetes-based self-hosted runners, the actions-runner-controller project implements an operator that dynamically provisions runner pods in response to workflow queue depth. Each pod executes a single job and terminates, with Kubernetes garbage collection removing the pod and all associated volumes. The pod template includes security contexts that disable privilege escalation and drop all Linux capabilities except those explicitly required for Docker socket access:

```yaml
apiVersion: actions.summerwind.dev/v1alpha1
kind: RunnerDeployment
metadata:
  name: production-runners
  namespace: github-actions
spec:
  replicas: 5
  template:
    metadata:
      labels:
        runner-group: production
    spec:
      repository: octo-org/octo-repo
      ephemeral: true    # Terminate pod after single job
      dockerEnabled: true
      dockerMTU: 1450    # Match cluster CNI MTU
      securityContext:
        fsGroup: 1000
      containers:
      - name: runner
        image: summerwind/actions-runner:v2.311.0
        securityContext:
          allowPrivilegeEscalation: false
          runAsNonRoot: true
          runAsUser: 1000
          capabilities:
            drop: ["ALL"]
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        volumeMounts:
        - name: docker-socket
          mountPath: /var/run/docker.sock
      volumes:
      - name: docker-socket
        hostPath:
          path: /var/run/docker.sock
          type: Socket
```

Audit logging for GitHub Actions workflow executions generates structured JSON events that capture the complete execution trace. Each workflow run produces log entries for run initiation, job assignment, secret access, and permission escalations. Organizations with GitHub Enterprise can stream these logs to external systems through the Audit Log API or webhook forwarding. The log schema includes essential forensic metadata: actor identity (user or service account), source IP address, user agent string, repository identifier, and workflow file path. For secret access events, the log records which secret was retrieved but never the secret's plaintext value, preserving confidentiality while enabling security monitoring.

A production audit log streaming pipeline typically uses GitHub's webhook mechanism to push events to a message queue, then processes them through a log normalization pipeline:

```yaml
name: Audit Log Forwarder
on:
  workflow_run:
    workflows: ["*"]
    types: [completed]

jobs:
  forward-logs:
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
    steps:
      - name: Fetch workflow run details
        id: run
        uses: actions/github-script@v7
        with:
          script: |
            const runData = await github.rest.actions.getWorkflowRun({
              owner: context.repo.owner,
              repo: context.repo.repo,
              run_id: context.payload.workflow_run.id
            });
            
            const auditEvent = {
              timestamp: runData.data.created_at,
              event: 'workflow_run.completed',
              actor: runData.data.triggering_actor.login,
              repository: context.repo.owner + '/' + context.repo.repo,
              workflow: runData.data.path,
              conclusion: runData.data.conclusion,
              run_id: runData.data.id,
              head_sha: runData.data.head_sha,
              head_branch: runData.data.head_branch
            };
            
            return auditEvent;

      - name: Send to SIEM
        env:
          SIEM_ENDPOINT: ${{ secrets.SIEM_WEBHOOK_URL }}
        run: |
          curl -X POST "$SIEM_ENDPOINT" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer ${{ secrets.SIEM_API_TOKEN }}" \
            -d '${{ steps.run.outputs.result }}'
```

Environment protection rules provide mandatory approval gates for workflows that deploy to sensitive environments like production. When a workflow job targets a protected environment (declared through `environment:` in the job definition), GitHub pauses execution and notifies designated reviewers. The job remains in a pending state until a reviewer approves or rejects the deployment. During this waiting period, the runner agent maintains the WebSocket connection but performs no execution. Protection rules also enforce wait timers—a minimum delay between approval and execution—and branch restrictions that prevent deployments from feature branches.

The implementation of environment protection in a multi-stage deployment pipeline demonstrates how approval gates integrate with job dependencies:

```yaml
name: Multi-Stage Deployment
on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build artifact
        run: |
          make build
          tar czf app.tar.gz ./dist
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: application
          path: app.tar.gz

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: application
      - name: Deploy to staging
        run: |
          tar xzf app.tar.gz
          ./deploy.sh staging

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://example.com
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: application
      - name: Deploy to production
        run: |
          tar xzf app.tar.gz
          ./deploy.sh production
```

In this pipeline, the `deploy-production` job blocks pending approval when it reaches the `environment: production` declaration. Reviewers receive notifications through GitHub's web interface and mobile app, with a detailed view of the pending deployment including commit SHA, actor identity, and workflow definition. Upon approval, the job resumes with the same `GITHUB_TOKEN` issued at workflow start, maintaining authentication continuity across the approval boundary.

## 3. High-Performance Optimization & Failure Modes

Runner performance optimization begins with understanding the computational bottlenecks inherent in CI/CD workloads. Most workflows exhibit three distinct phases: repository checkout (network-bound), dependency installation (network and disk-bound), and build/test execution (CPU-bound). Hosted runners provide consistent baseline performance with 2-core CPUs and 7GB RAM for the standard `ubuntu-latest` label, but larger runner configurations (4-core, 8-core, 16-core) dramatically reduce build times for parallelizable workloads. GitHub charges by the minute for hosted runners, making it economically viable to provision oversized runners for CPU-intensive jobs that exhibit linear scaling.

Self-hosted runners enable hardware-specific optimizations unavailable in the hosted model. Organizations frequently deploy runners with high-speed NVMe storage to accelerate dependency caching and artifact staging, particularly for Node.js and Python projects where package managers like npm and pip perform thousands of small file operations. For compile-heavy C++ or Rust projects, self-hosted runners with 64GB RAM and 16-core CPUs reduce incremental build times by maintaining warm compiler caches across workflow runs. However, this caching strategy directly contradicts the ephemeral execution security model—persistent build caches create opportunities for cache poisoning attacks where malicious workflow runs inject backdoors into shared cache artifacts consumed by subsequent builds.

The tension between performance and security in self-hosted runner deployments manifests in cache management strategies. Docker-based ephemeral runners typically mount a persistent volume for Docker layer caching, allowing subsequent builds to reuse base image layers without re-downloading from registries. This provides substantial performance gains—a typical Node.js application's Docker build might reduce from 5 minutes to 30 seconds when base layers are cached. However, the cache becomes a persistence vector. A compromised workflow could modify cached layers to include malicious binaries that execute in future workflow runs. The mitigation involves cache isolation through content-addressable storage: Docker's layer caching already provides this through SHA256 content hashes, but organizations must implement additional controls to prevent workflows from one repository from consuming cached layers produced by another repository.

Network topology significantly impacts self-hosted runner performance when workflows interact with private infrastructure. Hosted runners originate from Azure's public IP ranges, requiring organizations to expose deployment targets through internet-facing endpoints or VPN ingress points. Self-hosted runners deployed within private VPC networks avoid this complexity but introduce failure modes related to network partition. If the runner agent loses connectivity to GitHub's orchestration backend—whether due to firewall rule changes, DNS failures, or network splits—it continues polling for reconnection with exponential backoff. Jobs assigned during the partition remain in pending state indefinitely until the runner reestablishes connectivity or the job timeout elapses (default 360 minutes). This behavior can obscure the root cause of deployment failures, as workflows report "runner not found" errors rather than network connectivity failures.

GitHub's hosted runner provisioning uses Azure Spot VMs for cost optimization, introducing occasional capacity failures where job assignments fail due to insufficient VM inventory in the requested region. The orchestration layer automatically retries job assignment with backoff, but workflows with tight SLA requirements may exceed acceptable latency windows during regional capacity crunches. The failure mode manifests as jobs stuck in "Queued" state for minutes to hours. Self-hosted runners eliminate this failure mode by providing dedicated capacity but shift the operational burden to the organization's infrastructure team.

Workflow concurrency limits prevent resource exhaustion but introduce queueing latency. GitHub imposes organization-level concurrency caps based on plan tier: free tier allows 20 concurrent jobs across the organization, with higher limits for paid plans. When workflow trigger volume exceeds available concurrency, jobs queue pending available runners. For high-velocity repositories with frequent pull requests, this queueing can delay feedback cycles and impact developer productivity. The optimization strategy involves workflow parallelization through job matrices that distribute test suites across multiple runners, combined with aggressive concurrency group constraints that cancel in-progress workflow runs when newer commits arrive:

```yaml
name: CI Pipeline
on:
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true    # Cancel older runs when new commits arrive

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20, 22]
        shard: [1, 2, 3, 4]    # Parallelize test suite across 4 shards
      fail-fast: false         # Continue other matrix jobs on failure
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'
      - run: npm ci
      - name: Run test shard
        run: |
          npx jest --shard=${{ matrix.shard }}/4 --ci --coverage
      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage-node${{ matrix.node-version }}-shard${{ matrix.shard }}
          path: coverage/
```

This configuration spawns 12 parallel jobs (3 Node versions × 4 shards), reducing total test time from 20 minutes on a single runner to approximately 5 minutes with sufficient runner capacity. The `cancel-in-progress` directive ensures that only the most recent commit's workflow consumes runner resources, preventing queue buildup during rapid development iterations.

Secret management at scale requires explicit versioning and rotation strategies. GitHub secrets have no built-in versioning—updating a secret value immediately affects all workflow runs, including in-progress jobs that already retrieved the old value. This creates a race condition during secret rotation: workflows initiated before rotation but executing after rotation receive the new secret value, potentially breaking deployments that expect the old value. The mitigation pattern involves temporarily maintaining parallel secrets with version suffixes (`DATABASE_PASSWORD_V1`, `DATABASE_PASSWORD_V2`) and coordinating workflow updates before deleting the old version.

OIDC federation introduces complexity in debugging authentication failures. When a workflow's OIDC token fails to assume a cloud IAM role, the error message typically originates from the cloud provider's STS service with generic "Not authorized" text. The root cause may be any of several misconfigurations: trust policy restrictions on repository name, branch patterns, or workflow environment; token audience claim mismatches; or network path failures between the runner and cloud provider endpoints. The diagnostic process requires enabling AWS CloudTrail or equivalent audit logging on the cloud side to capture the full STS request and response, then correlating the denied token claims with the IAM trust policy predicates. GitHub does not log the OIDC token's payload claims in workflow output for security reasons, requiring developers to extract claims through the `github.rest.actions.getOIDCToken()` API in a separate debug workflow.

A common failure mode in self-hosted runner deployments involves Docker socket permission errors when workflows attempt to build images or run containers. Workflows expect the Docker socket at `/var/run/docker.sock` to be accessible to the runner agent's process, but security-conscious deployments run the agent as a non-root user. The socket's default permissions (root:docker with mode 0660) prevent access, causing Docker commands to fail with "permission denied" errors. The remediation involves either adding the runner user to the `docker` group—which grants root-equivalent privileges since Docker socket access allows arbitrary container execution—or using Docker-in-Docker sidecar containers with user namespace remapping to isolate container file systems.

Resource exhaustion on self-hosted runners manifests in subtle ways. Unlike hosted runners that terminate after each job, long-running self-hosted runners accumulate Docker images, volumes, and network objects across multiple workflow runs. Without periodic garbage collection, disk space exhaustion eventually blocks new job execution. The runner agent has no built-in cleanup mechanism for Docker resources, requiring organizations to implement custom cleanup workflows or cron jobs that run `docker system prune` to reclaim space. Similarly, workflow runs that spawn background processes without proper cleanup leave orphaned processes that consume CPU and memory, degrading runner performance over time. The robust pattern involves wrapping workflow steps in explicit cleanup blocks using `always()` conditions to ensure teardown occurs even when steps fail:

```yaml
jobs:
  integration-test:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
      
      - name: Start test infrastructure
        id: infra
        run: |
          docker-compose -f test/docker-compose.yml up -d
          echo "containers=$(docker-compose -f test/docker-compose.yml ps -q | tr '\n' ' ')" >> $GITHUB_OUTPUT
      
      - name: Run integration tests
        run: |
          npm run test:integration
      
      - name: Cleanup test infrastructure
        if: always()
        run: |
          docker-compose -f test/docker-compose.yml down -v
          docker rm -f ${{ steps.infra.outputs.containers }} || true
          docker network prune -f
```

The `if: always()` condition ensures cleanup executes regardless of test outcome, preventing container accumulation across multiple workflow runs.

High-availability self-hosted runner deployments require load balancing and automatic scaling strategies. The actions-runner-controller for Kubernetes implements horizontal pod autoscaling based on workflow queue depth metrics exposed through GitHub's API. When pending jobs exceed available runners, the controller scales the runner deployment's replica count, with newly provisioned pods automatically registering with GitHub and receiving job assignments. Scaling down occurs with graceful shutdown: the controller marks pods for termination but allows them to complete in-progress jobs before sending termination signals. This ensures workflows never encounter mid-execution runner failures due to scale-down events.

The ultimate failure mode in runner infrastructure is persistent compromise leading to supply chain attacks. If an attacker gains access to a self-hosted runner's host system, they can modify the runner agent binary to intercept secrets, inject backdoors into build artifacts, or exfiltrate source code. Unlike hosted runners where each job executes in a freshly provisioned VM, self-hosted runners persist across jobs, making detection of runtime modifications difficult. The defense strategy involves treating self-hosted runners as ephemeral compute substrates—deploying them in containers or VMs with immutable root filesystems, storing logs in tamper-evident append-only storage, and implementing behavioral monitoring that detects anomalous network connections or privilege escalations. Organizations with high security requirements should consider GitHub's large hosted runners with custom networking (GitHub Enterprise Cloud feature) rather than self-hosted runners, trading control for GitHub's responsibility to maintain isolation boundaries.
