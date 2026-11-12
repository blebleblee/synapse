# Operational Verification Labs: Core

## Objective & Lab Bench Setup

Operational verification of a DevSecOps pipeline demands hands-on mastery of modern security scanning and attestation toolchains. This lab guides security practitioners through the complete workflow of static code analysis, container vulnerability auditing, cryptographic image signing, and policy enforcement. You will execute real security scanning operations across the full artifact lifecycle—from source code commit through container image deployment—and understand how to integrate these tools into a continuous verification loop.

The exercises are structured around a realistic DevSecOps scenario: a team maintains a microservices application, commits code to a Git repository, builds container images, publishes them to a registry, and must enforce security policies before deployment. Each exercise isolates a critical control point and provides exact CLI commands, test payloads, and configuration files ready to execute.

### Lab Bench Requirements

Before beginning, ensure your workstation has the following tools installed and accessible in your `$PATH`:

- **Trivy** (v0.45+): Container and artifact vulnerability scanner from Aqua Security
- **Semgrep** (v1.45+): Static analysis engine with custom rule support
- **Gitleaks** (v8.18+): Git repository secret scanner
- **Cosign** (v2.0+): Container image signing and verification tool
- **Syft** (v0.68+): Software Bill of Materials (SBOM) generator
- **Grype** (v0.65+): Vulnerability database matcher for SBOMs
- **Checkov** (v2.14+): Infrastructure-as-code (IaC) and container policy scanner
- **Conftest** (v0.41+): Policy-as-code enforcement using Rego
- **Docker CLI** or **Podman** (v4.0+): Container runtime for building and running images
- **Git** (v2.35+): Version control with full history
- **jq** (v1.6+): JSON query and processing utility

Verify all tools are installed:

```bash
trivy version && semgrep --version && gitleaks version && cosign version && \
  syft version && grype version && checkov --version && conftest --version
```

### Test Repository Setup

Create a dedicated lab workspace and initialize a Git repository with intentionally vulnerable code samples:

```bash
mkdir -p ~/devsecops-lab && cd ~/devsecops-lab
git init vulnerable-app
cd vulnerable-app
```

Initialize a basic project structure with a package manifest:

```bash
cat > package.json << 'EOF'
{
  "name": "vulnerable-app",
  "version": "1.0.0",
  "description": "Lab: Intentionally vulnerable microservice",
  "main": "app.js",
  "scripts": {
    "start": "node app.js"
  },
  "dependencies": {
    "express": "4.16.2",
    "lodash": "4.17.4"
  }
}
EOF
```

Create a Dockerfile with known base image vulnerabilities:

```bash
cat > Dockerfile << 'EOF'
FROM node:14-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 3000
CMD ["npm", "start"]
EOF
```

Create a Node.js application containing hardcoded credentials and insecure patterns:

```bash
cat > app.js << 'EOF'
const express = require('express');
const app = express();

const AWS_KEY = 'AKIA2JVJHBK7XQPQ5678';
const AWS_SECRET = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY';

app.get('/', (req, res) => {
  res.send('Hello World');
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});
EOF
```

Create a Kubernetes deployment manifest with security misconfigurations:

```bash
cat > deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vulnerable-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vulnerable-app
  template:
    metadata:
      labels:
        app: vulnerable-app
    spec:
      containers:
      - name: app
        image: node:14-alpine
        ports:
        - containerPort: 3000
        securityContext:
          runAsRoot: true
          privileged: true
        resources:
          limits:
            memory: "128Mi"
          requests:
            memory: "64Mi"
EOF
```

Commit all files to establish a scannable Git repository:

```bash
git config user.email "lab@devsecops.local" && git config user.name "Lab User"
git add . && git commit -m "Initial vulnerable application"
```

---

## Exercise 1: Static Code Analysis & Secret Scanning

Static code analysis identifies vulnerabilities in source code before compilation or execution. Semantic analysis engines understand code structure rather than relying on fragile pattern matching, yielding fewer false positives and deeper insight into control flow. Secret scanning detects accidental credential exposure in version control history through entropy analysis and format-specific pattern recognition. This exercise combines Semgrep for semantic pattern matching and Gitleaks for repository-wide secret audits.

### Part 1A: Semgrep Custom Rule Development

Semgrep operates as a rule engine that matches abstract syntax trees (ASTs) against user-defined patterns. Unlike regex-based scanning, Semgrep understands code structure, enabling precise detection of vulnerable patterns with minimal false positives. You will create custom rules to detect hardcoded credentials and insecure API key patterns.

Create a custom Semgrep rule file:

```bash
mkdir -p ~/.semgrep && cat > ~/.semgrep/credential-rules.yaml << 'EOF'
rules:
  - id: hardcoded-aws-key
    patterns:
      - pattern-either:
          - patterns:
              - pattern: |
                  $VAR = "AKIA..."
          - patterns:
              - pattern: |
                  const $VAR = "AKIA$_"
    message: "Potential hardcoded AWS access key detected"
    languages: [javascript, typescript, python, java]
    severity: CRITICAL
    metadata:
      category: security
      cwe: CWE-798
      owasp: A02:2021 – Cryptographic Failures

  - id: insecure-http-request
    patterns:
      - pattern-either:
          - pattern: |
              require("http").request(...)
          - pattern: |
              import http
              http.request(...)
    message: "Unencrypted HTTP request detected; use HTTPS instead"
    languages: [javascript, python]
    severity: WARNING
    metadata:
      category: security
      cwe: CWE-295

  - id: sql-injection-vulnerable-concat
    patterns:
      - pattern-either:
          - pattern: "query = $VAR + $USER_INPUT"
          - pattern: "query = f\"SELECT * FROM users WHERE id={$ID}\""
    message: "SQL injection vulnerability: query constructed via string concatenation"
    languages: [python, javascript]
    severity: HIGH
    metadata:
      category: security
      cwe: CWE-89
      owasp: A03:2021 – Injection
EOF
```

Run Semgrep against the test repository using the custom rule set:

```bash
semgrep --config ~/.semgrep/credential-rules.yaml \
  --json \
  --output ~/semgrep-findings.json \
  ~/devsecops-lab/vulnerable-app
```

Extract and display findings in a structured format:

```bash
jq '.results[] | {file: .path, rule: .check_id, message: .extra.message, line: .start.line}' \
  ~/semgrep-findings.json
```

### Part 1B: Repository Secret Scanning with Gitleaks

Gitleaks scans Git repositories for high-entropy strings matching known credential formats. The tool inspects the entire commit history, not just the current state, making it invaluable for detecting secrets that were committed and later deleted. Create a configuration file that tailors detection to your environment:

```bash
cat > ~/.gitleaks/config.toml << 'EOF'
title = "Lab Gitleaks Configuration"

[allowlist]
description = "Lab allowlist for false positives"

[[rules]]
id = "lab-aws-key"
description = "AWS Access Key"
regex = '''(AKIA[0-9A-Z]{16})'''
keywords = ["aws", "AKIA"]
entropy = 3.5
severity = "CRITICAL"

[[rules]]
id = "lab-generic-secret"
description = "Generic secret pattern"
regex = '''(?i)secret\s*=\s*['\"]?([a-zA-Z0-9_\-]{32,})['\"]?'''
entropy = 4.0
severity = "HIGH"
EOF
```

Run Gitleaks with the custom configuration:

```bash
gitleaks detect --config ~/.gitleaks/config.toml \
  --source ~/devsecops-lab/vulnerable-app \
  --verbose \
  --json > ~/gitleaks-findings.json
```

Parse and summarize findings:

```bash
echo "=== SECRET DETECTION RESULTS ==="
jq '.[] | {secret_type: .Description, location: .File, commit: .Commit, severity: .Severity}' \
  ~/gitleaks-findings.json | head -20
```

The Gitleaks output reveals that credentials were committed in `app.js`. This demonstrates a critical gap in the development workflow: credentials entered the repository before any scanning gate. Part 1C addresses pre-commit prevention.

### Part 1C: Pre-Commit Hook Integration

Pre-commit hooks prevent credentials from entering version control in the first place. Install and configure a Git hook that runs Gitleaks before allowing commits:

```bash
cd ~/devsecops-lab/vulnerable-app
mkdir -p .git/hooks
```

Create the pre-commit hook:

```bash
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
set -e

echo "Running Gitleaks pre-commit scan..."
gitleaks protect --verbose --staged

if [ $? -ne 0 ]; then
  echo "FAILED: Gitleaks detected secrets in staged changes. Commit aborted."
  exit 1
fi

echo "Gitleaks scan passed."
exit 0
EOF

chmod +x .git/hooks/pre-commit
```

Test the hook by attempting to stage a new secret:

```bash
echo 'const API_KEY = "AKIA9999999999999999"' >> app.js
git add app.js
git commit -m "Test pre-commit hook" || echo "Hook prevented insecure commit as expected"
```

Reset the repository to a clean state:

```bash
git reset --hard HEAD
```

---

## Exercise 2: Container Image Scanning & Artifact Verification

Container images are complex artifacts built from base images, dependencies, and application code. Each layer introduces potential vulnerabilities. This exercise covers vulnerability scanning using Trivy, SBOM generation, and cryptographic signing for image attestation.

### Part 2A: Building and Scanning Container Images

Build the vulnerable container image:

```bash
cd ~/devsecops-lab/vulnerable-app
docker build -t vulnerable-app:1.0.0 .
```

Scan the image with Trivy to identify vulnerabilities in the base image and dependencies:

```bash
trivy image --severity CRITICAL,HIGH \
  --format json \
  --output ~/trivy-image-scan.json \
  vulnerable-app:1.0.0
```

Display critical findings:

```bash
jq '.Results[] | select(.Type=="Library") | {package: .Name, severity: .Vulnerabilities[].Severity, cve: .Vulnerabilities[].VulnerabilityID}' \
  ~/trivy-image-scan.json | head -30
```

Trivy identifies vulnerabilities in the node:14-alpine base image and in the npm dependencies. The express 4.16.2 and lodash 4.17.4 versions contain known remote code execution and prototype pollution flaws respectively. These findings drive remediation: update the base image to node:20-alpine and pin dependencies to patched versions.

### Part 2B: Software Bill of Materials Generation

A Software Bill of Materials (SBOM) documents every component in an artifact, enabling downstream vulnerability correlation and license compliance. Generate an SBOM using Syft:

```bash
syft vulnerable-app:1.0.0 \
  --output json \
  --file ~/sbom-vulnerable-app.json
```

Examine the SBOM structure:

```bash
jq '.artifacts[] | {name: .name, version: .version, type: .type}' \
  ~/sbom-vulnerable-app.json | head -20
```

Match the SBOM against vulnerability databases using Grype:

```bash
grype sbom:~/sbom-vulnerable-app.json \
  --output json \
  --file ~/grype-scan.json
```

Compare Grype results to Trivy results. Both tools identify the same vulnerabilities, but Grype operates on SBOM data, allowing offline scanning and integration into policy gates that may not have direct image access.

### Part 2C: Image Signing with Cosign

Cosign provides container image signing and verification, establishing a chain of custody for artifacts. Generate a key pair for signing:

```bash
cosign generate-key-pair
```

When prompted, set a passphrase for the private key. Cosign stores keys in `~/.cosign/cosign.key` and `~/.cosign/cosign.pub`.

Sign the container image:

```bash
cosign sign --key ~/.cosign/cosign.key vulnerable-app:1.0.0
```

Verify the signature:

```bash
cosign verify --key ~/.cosign/cosign.pub vulnerable-app:1.0.0
```

Successful verification confirms that the image has not been tampered with since signing. Attach an SBOM as an image attestation:

```bash
cosign attach sbom --sbom ~/sbom-vulnerable-app.json vulnerable-app:1.0.0
```

Retrieve and inspect the attached SBOM:

```bash
cosign download sbom vulnerable-app:1.0.0 | jq '.artifacts[] | {name, version}'
```

---

## Exercise 3: Infrastructure-as-Code Policy Enforcement

Infrastructure-as-code (IaC) files define Kubernetes manifests, Terraform configurations, and container security settings. These files must be validated against security policies before deployment. This exercise combines Checkov for IaC scanning and Conftest for policy-as-code enforcement using the Rego language.

### Part 3A: Checkov IaC Scanning

Checkov performs static analysis on IaC files, detecting misconfigurations, missing controls, and security drift. Scan the Kubernetes deployment manifest:

```bash
checkov -f ~/devsecops-lab/vulnerable-app/deployment.yaml \
  --format json \
  --output-file ~/checkov-scan.json \
  --check CKV_K8S_1,CKV_K8S_4,CKV_K8S_9
```

Display failed checks:

```bash
jq '.failed_checks[] | {check_id: .check_id, resource: .resource, message: .check.name}' \
  ~/checkov-scan.json
```

The deployment fails multiple checks: containers run as root (CKV_K8S_1), privilege escalation is enabled (CKV_K8S_4), and resource requests are not defined (CKV_K8S_9). Remediate by updating the deployment manifest with proper security controls.

### Part 3B: Policy-as-Code with Conftest & Rego

Conftest enforces custom policies using Rego, a declarative policy language. Create a Rego policy file that enforces Kubernetes security requirements:

```bash
mkdir -p ~/devsecops-lab/policies && cat > ~/devsecops-lab/policies/k8s-security.rego << 'EOF'
package main

deny[msg] {
  input.kind == "Deployment"
  containers := input.spec.template.spec.containers
  container := containers[_]
  not container.securityContext.runAsNonRoot
  msg := sprintf("Container '%s' must run as non-root user", [container.name])
}

deny[msg] {
  input.kind == "Deployment"
  containers := input.spec.template.spec.containers
  container := containers[_]
  container.securityContext.privileged == true
  msg := sprintf("Container '%s' must not run in privileged mode", [container.name])
}

deny[msg] {
  input.kind == "Deployment"
  containers := input.spec.template.spec.containers
  container := containers[_]
  not container.resources.requests
  msg := sprintf("Container '%s' must define resource requests", [container.name])
}

warn[msg] {
  input.kind == "Deployment"
  not input.spec.template.spec.securityContext.runAsNonRoot
  msg := "Pod security context should enforce runAsNonRoot"
}
EOF
```

Run Conftest against the deployment:

```bash
conftest test ~/devsecops-lab/vulnerable-app/deployment.yaml \
  --policy ~/devsecops-lab/policies \
  --output json > ~/conftest-results.json
```

Examine policy violations:

```bash
jq '.[] | {status: .status, message: .message}' ~/conftest-results.json
```

The policy violations correspond to the security misconfigurations identified by Checkov. Update the deployment to satisfy both Checkov and Conftest policies:

```bash
cat > ~/devsecops-lab/vulnerable-app/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vulnerable-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vulnerable-app
  template:
    metadata:
      labels:
        app: vulnerable-app
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
      - name: app
        image: node:20-alpine
        ports:
        - containerPort: 3000
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
        resources:
          limits:
            memory: "128Mi"
            cpu: "250m"
          requests:
            memory: "64Mi"
            cpu: "100m"
EOF
```

Rerun Conftest:

```bash
conftest test ~/devsecops-lab/vulnerable-app/deployment.yaml \
  --policy ~/devsecops-lab/policies \
  --output json
```

---

## Exercise 4: End-to-End Verification Pipeline

This final exercise integrates all scanning stages into a cohesive pipeline. Create a shell script that orchestrates Gitleaks, Semgrep, Trivy, Checkov, and Conftest in sequence, enforcing a gate at each stage.

Create the pipeline script:

```bash
cat > ~/devsecops-lab/verify-pipeline.sh << 'EOF'
#!/bin/bash
set -e

REPO_PATH="$1"
IMAGE_NAME="$2"
IMAGE_TAG="$3"

echo "=== STAGE 1: Repository Secret Scanning ==="
gitleaks detect --source "$REPO_PATH" --verbose
if [ $? -ne 0 ]; then
  echo "FAILED: Secrets detected in repository"
  exit 1
fi

echo "=== STAGE 2: Static Code Analysis ==="
semgrep --config ~/.semgrep/credential-rules.yaml \
  --json \
  --output /tmp/semgrep-findings.json \
  "$REPO_PATH"
SEMGREP_FINDINGS=$(jq '.results | length' /tmp/semgrep-findings.json)
if [ "$SEMGREP_FINDINGS" -gt 0 ]; then
  echo "WARNING: $SEMGREP_FINDINGS Semgrep findings detected"
  jq '.results[] | {rule: .check_id, severity: .extra.severity}' /tmp/semgrep-findings.json
fi

echo "=== STAGE 3: Container Image Scanning ==="
docker build -t "$IMAGE_NAME:$IMAGE_TAG" "$REPO_PATH"
trivy image --severity CRITICAL,HIGH \
  --format json \
  --output /tmp/trivy-scan.json \
  "$IMAGE_NAME:$IMAGE_TAG"
CRITICAL_VULNS=$(jq '.Results[] | select(.Vulnerabilities[].Severity=="CRITICAL") | length' /tmp/trivy-scan.json)
if [ "$CRITICAL_VULNS" -gt 0 ]; then
  echo "FAILED: $CRITICAL_VULNS critical vulnerabilities in image"
  exit 1
fi

echo "=== STAGE 4: IaC Policy Validation ==="
MANIFEST_FILE=$(find "$REPO_PATH" -name "deployment.yaml" -o -name "*.yaml" | head -1)
if [ -n "$MANIFEST_FILE" ]; then
  conftest test "$MANIFEST_FILE" \
    --policy ~/devsecops-lab/policies \
    --output json > /tmp/conftest-results.json
  DENIES=$(jq 'map(select(.status=="deny")) | length' /tmp/conftest-results.json)
  if [ "$DENIES" -gt 0 ]; then
    echo "FAILED: $DENIES policy violations in IaC"
    jq '.[] | select(.status=="deny") | .message' /tmp/conftest-results.json
    exit 1
  fi
fi

echo "=== STAGE 5: Image Signing ==="
cosign sign --key ~/.cosign/cosign.key "$IMAGE_NAME:$IMAGE_TAG"

echo "=== VERIFICATION COMPLETE ==="
echo "Image $IMAGE_NAME:$IMAGE_TAG passed all gates and is signed."
EOF

chmod +x ~/devsecops-lab/verify-pipeline.sh
```

Execute the pipeline:

```bash
~/devsecops-lab/verify-pipeline.sh ~/devsecops-lab/vulnerable-app vulnerable-app 2.0.0
```

The pipeline orchestrates the complete verification workflow. If any stage fails, the pipeline halts, preventing insecure artifacts from progressing. Each stage provides detailed feedback, enabling developers to remediate issues before resubmission.

---

## Operational Considerations

The exercises in this lab establish foundational scanning and verification practices. Production deployments require additional considerations.

**Tool Integration**: Integrate scanning tools into CI/CD pipelines using native plugins (GitHub Actions, GitLab CI) or orchestration platforms (Jenkins, Tekton). Ensure that pipeline gates are enforced and cannot be bypassed through manual overrides.

**Baseline Management**: Vulnerability scanners generate findings against continuously evolving databases. Establish baseline tolerances and update policies as new vulnerabilities are disclosed. Use CVSS scores and exploit availability as severity signals, but supplement with threat modeling and asset criticality.

**False Positive Handling**: Scanning tools generate false positives, particularly for static analysis. Develop processes for triage and remediation. Suppress specific findings only when justified by technical review, and document suppression decisions in audit logs.

**Supply Chain Governance**: Restrict image registries and artifact stores to signed, verified artifacts. Implement admission controllers in Kubernetes that verify image signatures before deployment. Audit all artifact pulls and deployments.

**Continuous Monitoring**: Scanning containers at build time is insufficient. Container orchestrators like Kubernetes continue running vulnerable images throughout their lifecycle. Implement runtime vulnerability scanning and automated remediation workflows.
