# Operational Verification Labs: Core

## Conceptual Foundation

Before executing a single CLI command, understanding *why* each control exists and *how* it fits into the broader security architecture makes the difference between a practitioner who runs tools and one who designs pipelines. This section builds that mental model.

### The Artifact Lifecycle Threat Model

A DevSecOps pipeline is a trust-propagation mechanism. Source code is the least trusted input; a signed, policy-validated container image in a production registry is the most trusted output. Every transformation in between—dependency resolution, compilation, image layer construction, registry push—is an opportunity for an adversary to introduce malicious material. The controls in this lab are positioned to verify trust at each transformation boundary.

```mermaid
flowchart LR
    DEV["Developer\nWorkstation"]
    GIT["Git Repository\n(Source of Truth)"]
    CI["CI Build System"]
    REG["Container Registry"]
    K8S["Kubernetes\nAdmission Controller"]
    PROD["Production\nRuntime"]

    DEV -->|"commit + push"| GIT
    GIT -->|"trigger"| CI
    CI -->|"push signed image"| REG
    REG -->|"pull on deploy"| K8S
    K8S -->|"admit or reject"| PROD

    subgraph GATE1 ["Gate 1: Pre-Commit"]
        GL["Gitleaks\n(secret scan)"]
        SG["Semgrep\n(SAST)"]
    end

    subgraph GATE2 ["Gate 2: CI Build"]
        TR["Trivy\n(image CVEs)"]
        SY["Syft + Grype\n(SBOM + CVE match)"]
        CK["Checkov\n(IaC static analysis)"]
        CT["Conftest\n(policy-as-code)"]
    end

    subgraph GATE3 ["Gate 3: Registry Admission"]
        CS["Cosign\n(image signing)"]
        AT["Cosign Attest\n(SBOM + provenance)"]
    end

    subgraph GATE4 ["Gate 4: Runtime"]
        RT["Runtime Scanner\n(Falco / Trivy operator)"]
    end

    DEV -.->|"pre-commit hook"| GATE1
    CI -.->|"pipeline steps"| GATE2
    REG -.->|"OCI referrers"| GATE3
    K8S -.->|"continuous"| GATE4
```

The critical insight is that each gate operates on a different artifact representation: plaintext source, resolved dependency graph, OCI image layers, declarative manifest, and running process. No single tool covers all representations; defense in depth requires operating at every boundary.

### Why Semantic Analysis Outperforms Pattern Matching

Traditional SAST tools based on regular expressions operate on the token stream of source code. They cannot distinguish between:

```javascript
// False positive for a regex scanner — this is a test fixture, not a real key
const EXAMPLE_KEY = "AKIAIOSFODNN7EXAMPLE";

// True positive — this is an actual key assignment used in a live AWS call
const client = new AWS.S3({ accessKeyId: "AKIA2JVJHBK7XQPQ5678" });
```

Semgrep compiles source code into a language-specific Abstract Syntax Tree (AST) and matches structural patterns against it. This means rules can express relationships between nodes—data flow from a source (user input) to a sink (SQL query)—not just the presence of a string. The formal model is a subset of Datalog, making Semgrep rules composable via `pattern-and`, `pattern-not`, and `pattern-either` combinators.

Entropy-based secret scanning (used by Gitleaks) takes a different approach: it measures the Shannon entropy of a candidate string. High-entropy strings with the right length and character distribution are unlikely to be natural language and likely to be cryptographic material. The formula:

```text
H(X) = -Σ p(x) * log₂(p(x))
```

A randomly-generated AWS secret key has an entropy around 4.6 bits/character. English prose averages around 1.0–1.5 bits/character. Thresholds around 3.5–4.0 bits/character catch genuine secrets while suppressing most false positives.

### The SBOM as a Queryable Artifact Inventory

A Software Bill of Materials is not merely documentation—it is a machine-readable inventory that decouples *vulnerability discovery* from *build infrastructure*. Once an SBOM is generated, it can be:

- Correlated against any vulnerability database (NVD, OSV, GitHub Advisory) without rebuilding the image
- Signed as a cryptographic attestation alongside the image
- Queried by procurement and legal teams for license compliance
- Fed into an asset management system that alerts when new CVEs match installed components

The two dominant SBOM formats are **SPDX** (ISO/IEC 5962:2021) and **CycloneDX**. Syft can emit both. CycloneDX has richer vulnerability and dependency relationship support; SPDX has broader tooling adoption. For a new pipeline, CycloneDX is the pragmatic choice.

### OCI Referrers and Sigstore's Trust Model

Cosign leverages the **OCI Distribution Specification v1.1 Referrers API** to store signatures and attestations as OCI artifacts in the same registry namespace as the image they describe. A signature is not a separate object stored elsewhere—it is a manifest with `mediaType: application/vnd.oci.image.manifest.v1+json` that references the original image digest via the `subject` field.

The Sigstore trust model uses an **ephemeral key + transparency log** architecture called **Rekor**. When signing without a persistent key pair (`cosign sign` with OIDC), Cosign:

1. Requests an ephemeral signing certificate from Fulcio (a Sigstore CA) that embeds the signer's OIDC identity
2. Signs the image digest with the ephemeral key
3. Submits the signed certificate and image digest to Rekor, an append-only transparency log
4. Stores the Rekor log entry in the OCI referrers as proof of inclusion

This means anyone can verify who signed an image using only public infrastructure, without key management overhead. For this lab, we use long-lived key pairs to illustrate the fundamental mechanics; the keyless flow is noted where relevant.

---

## Lab Bench Setup

### Tool Installation and Version Verification

The following versions represent the minimum feature set required by the exercises. Later versions are compatible unless noted.

| Tool | Minimum Version | Purpose |
|------|----------------|---------|
| Trivy | 0.50+ | Container and filesystem vulnerability scanner (Aqua Security) |
| Semgrep | 1.60+ | AST-based static analysis engine (Semgrep Inc.) |
| Gitleaks | 8.18+ | High-entropy secret and credential scanner |
| Cosign | 2.2+ | OCI image signing, verification, and attestation (Sigstore) |
| Syft | 1.0+ | SBOM generator for containers and filesystems (Anchore) |
| Grype | 0.74+ | Vulnerability matcher for SBOMs and images (Anchore) |
| Checkov | 3.0+ | IaC static analysis and policy scanner (Bridgecrew/Palo Alto) |
| Conftest | 0.49+ | Policy-as-code enforcement via Rego (OPA) |
| Docker | 24.0+ | OCI container build and runtime |
| jq | 1.7+ | JSON query processor |

> **Trivy version note**: The `--severity` flag behavior changed in v0.46—it now filters *displayed* results by default but can be configured to also gate the exit code via `--exit-code 1`. This lab uses the explicit `--exit-code` flag throughout to avoid ambiguity.

Install all tools on a Debian/Ubuntu system:

```bash
# Trivy
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | \
  gpg --dearmor | sudo tee /usr/share/keyrings/trivy.gpg > /dev/null
echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb generic main" | \
  sudo tee /etc/apt/sources.list.d/trivy.list
sudo apt-get update && sudo apt-get install -y trivy

# Semgrep (via pip — the official distribution channel)
pip3 install semgrep==1.60.0

# Gitleaks
GITLEAKS_VERSION="8.18.4"
curl -sSfL "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" | \
  sudo tar -xz -C /usr/local/bin gitleaks

# Cosign
COSIGN_VERSION="2.2.4"
curl -sSfL "https://github.com/sigstore/cosign/releases/download/v${COSIGN_VERSION}/cosign-linux-amd64" \
  -o /usr/local/bin/cosign && sudo chmod +x /usr/local/bin/cosign

# Syft
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | \
  sh -s -- -b /usr/local/bin v1.0.1

# Grype
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | \
  sh -s -- -b /usr/local/bin v0.74.6

# Checkov
pip3 install checkov==3.1.0

# Conftest
CONFTEST_VERSION="0.49.0"
curl -sSfL "https://github.com/open-policy-agent/conftest/releases/download/v${CONFTEST_VERSION}/conftest_${CONFTEST_VERSION}_Linux_x86_64.tar.gz" | \
  sudo tar -xz -C /usr/local/bin conftest

# jq
sudo apt-get install -y jq
```

Verify all tools are present and report expected versions:

```bash
set -e
echo "=== Tool Version Verification ==="
printf "%-15s %s\n" "trivy:"     "$(trivy --version 2>&1 | head -1)"
printf "%-15s %s\n" "semgrep:"   "$(semgrep --version 2>&1)"
printf "%-15s %s\n" "gitleaks:"  "$(gitleaks version 2>&1)"
printf "%-15s %s\n" "cosign:"    "$(cosign version 2>&1 | head -1)"
printf "%-15s %s\n" "syft:"      "$(syft --version 2>&1)"
printf "%-15s %s\n" "grype:"     "$(grype version 2>&1 | head -1)"
printf "%-15s %s\n" "checkov:"   "$(checkov --version 2>&1)"
printf "%-15s %s\n" "conftest:"  "$(conftest --version 2>&1)"
printf "%-15s %s\n" "jq:"        "$(jq --version)"
echo "=== All tools verified ==="
```

### Intentionally Vulnerable Test Repository

The lab targets a repository constructed to trigger real findings across all scanning tools. Each vulnerability is deliberate and educational.

```bash
mkdir -p ~/devsecops-lab && cd ~/devsecops-lab
git init vulnerable-app
cd vulnerable-app
git config user.email "lab@devsecops.local"
git config user.name "Lab User"
```

Create a `package.json` pinning known-vulnerable dependency versions. `express@4.16.2` is affected by [CVE-2024-29041](https://nvd.nist.gov/vuln/detail/CVE-2024-29041) (open redirect); `lodash@4.17.4` is affected by [CVE-2019-10744](https://nvd.nist.gov/vuln/detail/CVE-2019-10744) (prototype pollution) and [CVE-2021-23337](https://nvd.nist.gov/vuln/detail/CVE-2021-23337) (command injection via `_.template`):

```bash
cat > package.json << 'EOF'
{
  "name": "vulnerable-app",
  "version": "1.0.0",
  "description": "Lab: Intentionally vulnerable microservice for DevSecOps training",
  "main": "app.js",
  "scripts": {
    "start": "node app.js"
  },
  "dependencies": {
    "express": "4.16.2",
    "lodash": "4.17.4",
    "axios": "0.21.1"
  },
  "engines": {
    "node": ">=14.0.0"
  }
}
EOF
```

Create the application with multiple vulnerability classes: hardcoded credentials, SQL injection via string concatenation, and use of a deprecated HTTP (non-TLS) client:

```bash
cat > app.js << 'EOF'
// INTENTIONALLY VULNERABLE — lab training purposes only
const express = require('express');
const http    = require('http');   // CWE-319: cleartext transmission
const app     = express();

// CWE-798: Use of hardcoded credentials
// This AWS access key ID matches the AKIA[0-9A-Z]{16} pattern that Gitleaks
// and Semgrep will flag. The secret below is the canonical AWS documentation
// example key — it is not a real credential.
const AWS_ACCESS_KEY_ID     = 'AKIA2JVJHBK7XQPQ5678';
const AWS_SECRET_ACCESS_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY';

app.use(express.json());

// CWE-89: SQL injection via string concatenation
// The `id` parameter is directly interpolated into a SQL query string.
app.get('/user', (req, res) => {
  const id    = req.query.id;
  const query = "SELECT * FROM users WHERE id = " + id;  // ← injection point
  // db.query(query) would execute here in a real app
  res.json({ query });
});

// CWE-319: data fetched over plaintext HTTP
app.get('/fetch', (req, res) => {
  http.get('http://internal-service/data', (apiRes) => {
    res.json({ status: apiRes.statusCode });
  });
});

app.get('/health', (_req, res) => {
  res.json({ status: 'ok' });
});

app.listen(3000, () => console.log('Listening on :3000'));
EOF
```

Create a `Dockerfile` that intentionally uses an end-of-life base image (`node:14-alpine`). Node 14 reached EOL on 2023-04-30 and contains unfixed CVEs in both the Node.js runtime and the musl libc version bundled in the alpine base:

```bash
cat > Dockerfile << 'EOF'
# INTENTIONALLY VULNERABLE BASE IMAGE — lab training purposes only
# node:14-alpine uses Node.js 14.x (EOL) on Alpine 3.15
# Multiple CVEs exist in this image; Trivy will detect them.
FROM node:14-alpine

WORKDIR /app

COPY package.json ./
RUN npm install --production

COPY . .

EXPOSE 3000
CMD ["npm", "start"]
EOF
```

Create a Kubernetes manifest with four distinct security misconfigurations that Checkov and Conftest will flag:

```bash
cat > deployment.yaml << 'EOF'
# INTENTIONALLY MISCONFIGURED — lab training purposes only
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vulnerable-app
  namespace: default
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
      # CKV_K8S_30: no pod-level securityContext
      containers:
      - name: app
        image: node:14-alpine
        ports:
        - containerPort: 3000
        securityContext:
          runAsUser: 0
```
