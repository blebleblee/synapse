# Lesson 3: Secrets, Variables, and Context Propagation

## 1. First-Principles Intuition & Invariants

Every CI/CD system confronts the same foundational tension: pipelines require sensitive material—deployment credentials, API tokens, signing keys, cloud provider secrets—to perform their function, yet this material must never enter version control, appear in build logs, or leak into artifact payloads. GitHub Actions resolves this tension through a three-layer architecture of configuration injection that separates sensitive values from workflow logic at the design level. The system treats secrets as first-class, encrypted entities with scoped lifecycles, resolves them at dispatch time through a layered environment hierarchy, and applies post-hoc log redaction on the runner to prevent accidental disclosure. Understanding where each layer's trust boundary lies, how values propagate through expression evaluation, and where the masking mechanism fails is the difference between a pipeline that ships safely and one that exfiltrates credentials to a public log stream.

The invariants that govern this system are few but strict. Secrets are write-once, read-many: a secret's value is set through GitHub's API or web interface, encrypted at rest, and decrypted only at the moment a job is dispatched to a runner. Once decrypted, the value is injected into the runner process as an environment variable and simultaneously registered with the runner's log processor for string-level redaction. Log masking is best-effort, not cryptographic—the runner performs literal substring replacement on stdout and stderr, replacing any registered value with asterisks. If a secret is transformed through base64 encoding, URL encoding, character splitting, or arithmetic manipulation before reaching log output, the transformed value will not be masked unless explicitly registered. Expression evaluation is deterministic within a given context state: the same expression evaluated against the same context snapshot always yields the same result, which means workflows are reproducible as long as external state (repository contents, secret values, event payloads) is controlled. Matrix expansion is a compile-time operation performed by the control plane before any runner is provisioned—the cartesian product of matrix dimensions is computed once, generating a fixed set of job configurations, each with a unique `matrix` context. Context propagation is strictly one-directional within a workflow run: downstream jobs consume upstream outputs through the `needs` context, but an upstream job cannot observe the state of a job that depends on it. Across reusable workflow boundaries, contexts are propagated selectively: `inputs` and `secrets` must be passed explicitly, `vars` and `github` are inherited automatically, and `env` does not cross the boundary at all.

These invariants shape every engineering decision that follows. The layered environment hierarchy exists because infrastructure teams need different trust domains for different deployment targets—a staging environment should not share the production database password, and a pull request preview build should not have access to deploy tokens at all. The context object model exists because workflow authors need programmatic access to runtime state without embedding that state directly in YAML, which would make workflows non-portable and leak sensitive values into source control. The expression syntax exists because a declarative pipeline language needs a constrained, sandboxed evaluation environment that cannot execute arbitrary code but can express conditional logic, string manipulation, and data transformation. Matrix expansion exists because building and testing across multiple operating systems, CPU architectures, and runtime versions is a combinatorial problem that benefits from declarative specification rather than copy-pasted job definitions.

## 2. Core Architecture & Mechanics

### The Environment Hierarchy and Secret Resolution

GitHub Actions resolves configuration through a three-tier hierarchy: organization, repository, and environment. Organization-level secrets and variables are accessible to every repository within the organization that has been granted access, providing a mechanism to share infrastructure-wide credentials such as a common container registry token or a cloud provider service account key. Repository-level secrets are scoped to a single repository and override organization-level values when a name collision occurs. Environment-level secrets are scoped to a named deployment environment—declared via the `environment:` key on a job—and override both repository and organization values for that environment.

The resolution order is strictly environment > repository > organization. When a job specifies an environment, GitHub's control plane resolves each secret name by checking the environment first, then the repository, then the organization. The first match wins; lower-priority sources are not consulted. This allows a repository to define a `DATABASE_URL` secret for staging and an environment named `production` to define its own `DATABASE_URL` with the production endpoint, without any workflow logic to distinguish them.

```mermaid
flowchart TD
    ORG["Organization<br/>Secrets & Variables"] -->|"inherit"| REPO["Repository<br/>Secrets & Variables"]
    REPO -->|"inherit"| ENV["Environment<br/>Secrets (deployment-scoped)"]
    ENV -->|"highest priority"| RES["Resolution: env > repo > org"]
    REPO -->|"fallback"| RES
    ORG -->|"fallback"| RES
    RES --> RUN["Runner: environment variable injection<br/>+ log mask registration"]
```

Environments are more than secret scopes—they are deployment gates. An environment can be configured with protection rules through GitHub's API or repository settings: required reviewers who must approve before any job targeting that environment can start, deployment branch restrictions that limit which branches may deploy to a given environment, and wait timers that enforce a configurable delay between approval and execution. These rules are enforced by the control plane, not the runner. A job targeting a protected environment will remain in a queued state until all rules are satisfied, and if a required reviewer rejects the deployment, the job fails without ever provisioning a runner. This makes environments the primary mechanism for enforcing deployment safety in infrastructure pipelines.

### Secret Encryption and the Masking Pipeline

Secrets are encrypted at rest using libsodium sealed boxes, which combine X25519 elliptic-curve key exchange with XSalsa20-Poly1305 authenticated encryption. The encryption key is managed by GitHub's backend and is never exposed to clients, the API, or the runner. When a job is dispatched, the control plane decrypts the relevant secrets and transmits them to the runner over an encrypted channel as part of the job dispatch payload. The runner—`actions/runner`, a Go binary executing on a virtual machine or container—receives the decrypted secrets, registers each value with its internal log processor, and injects them as environment variables into the step process's execution environment.

The log masking mechanism is a post-processing step applied to every line of stdout and stderr emitted by a step. The runner maintains a set of registered secret values. Before a job's first step executes, all secrets resolved for the job are registered. During execution, additional values can be registered via the `::add-mask::` workflow command. For each line of output, the runner performs literal string replacement, substituting every occurrence of a registered value with `***`. This is substring matching, not regex, so a secret value of `AKIAIOSFODNN7EXAMPLE` will be redacted regardless of where it appears in a line, but the string `akiaiosfodnn7example` (lowercased) will not, because the matching is case-sensitive.

```yaml
name: Secret Handling Demonstration

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  REGION: us-east-1
  LOG_LEVEL: info

jobs:
  demonstrate-masking:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Access secrets and variables
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
          FEATURE_FLAGS: ${{ vars.FEATURE_FLAGS }}
        run: |
          echo "Region: ${REGION}"
          echo "Log level: ${LOG_LEVEL}"
          echo "Feature flags: ${FEATURE_FLAGS}"
          
          # The following line logs the access key, but the runner
          # masks it because AWS_ACCESS_KEY_ID is a registered secret.
          echo "Using access key: ${AWS_ACCESS_KEY_ID}"
          
          # Register an additional value for masking at runtime.
          # This is necessary when a secret is transformed, because
          # the transformed value is not automatically registered.
          ENCODED_KEY=$(echo -n "${AWS_SECRET_ACCESS_KEY}" | base64 -w0)
          echo "::add-mask::${ENCODED_KEY}"
          echo "Base64-encoded key (masked): ${ENCODED_KEY}"
          
          # Without the add-mask above, the base64-encoded secret
          # would appear in plaintext in the log output.
```

The critical failure mode here is transformation. If a step base64-encodes a secret, URL-encodes it, splits it across multiple lines, or hashes it, the transformed value is a new string that the log processor does not know about. Unless the workflow explicitly registers the transformed value via `::add-mask::`, it will appear in the log. This is not a bug—it is an inherent limitation of string-replacement masking. The mitigation is to register transformed values explicitly, or better, to avoid emitting secret-derived values to logs at all.

### The Context Object Taxonomy

Contexts are named namespaces that expose runtime state to expression evaluation. Each context is a JSON object whose properties can be accessed through dot notation (`github.ref`) or index notation (`secrets['MY_SECRET']`) within `${{ }}` expression blocks. The available contexts and their resolution timing differ, which determines where they can be used.

The `github` context is the most pervasive. It is populated by the control plane at dispatch time and contains event metadata: `github.event_name` (the trigger that started the run), `github.ref` (the fully-qualified ref, e.g., `refs/heads/main`), `github.sha` (the commit SHA), `github.repository` (owner/name), `github.actor` (the user who triggered the run), `github.event` (the full event payload as a JSON object), `github.run_id`, `github.run_number`, `github.run_attempt`, `github.workflow` (the workflow filename), `github.head_ref` and `github.base_ref` (for pull request events), and `github.ref_name` (the short ref name). This context is available at every expression evaluation point in the workflow, from job-level conditionals to step-level `run` interpolation.

The `env` context contains environment variables declared in the workflow file via the `env:` key at the workflow, job, or step level, plus variables set dynamically during step execution through the `$GITHUB_ENV` file mechanism. Variables written to `$GITHUB_ENV` become available in the `env` context for all subsequent steps in the same job. The `vars` context contains repository and organization variables—plaintext configuration values that are not encrypted and not masked. These are managed through GitHub's API or web interface and are useful for non-sensitive configuration like feature flag lists, deployment URLs, or tool version strings. The `secrets` context contains decrypted secret values and is populated at job dispatch time. Accessing `secrets.SOME_NAME` in an expression returns the decrypted value as a string.

The `steps` context exposes results from steps that have already executed in the current job. Each step with an `id:` key is accessible as `steps.<id>.outputs.<name>` (step outputs set via `$GITHUB_OUTPUT`), `steps.<id>.conclusion` (the step's final status: `success`, `failure`, `cancelled`, or `skipped`), and `steps.<id>.outcome` (the step's result before `if` conditionals are applied). The distinction between `conclusion` and `outcome` matters when a step has an `if: always()` or `if: failure()` conditional: a step that fails but has `if: always()` will have `outcome: failure` and `conclusion: success` because the conditional allowed it to pass.

The `needs` context provides access to outputs and results from jobs declared as dependencies. When a job specifies `needs: [build]`, it can access `needs.build.outputs.version`, `needs.build.result`, and `needs.build.outputs.*` for any outputs the `build` job declared. This is the primary mechanism for cross-job context propagation within a single workflow run. The `matrix` context contains the current matrix combination's values, available only within a job that uses a matrix strategy. The `strategy` context exposes `strategy.job-index` (the zero-based index of the current job within the expanded matrix), `strategy.job-total` (the total number of jobs in the matrix), and `strategy.fail-fast` (the boolean setting). The `runner` context exposes runner environment details: `runner.os`, `runner.arch`, `runner.temp`, `runner.tool_cache`, `runner.workspace`, and `runner.debug`.

For reusable workflows, two additional contexts become available. The `inputs` context contains values passed from the calling workflow via the `with:` key, typed according to the `workflow_call` trigger's input definitions. The `secrets` context in a reusable workflow contains only secrets explicitly passed by the caller via the `secrets:` key, with the exception of `GITHUB_TOKEN`, which is automatically injected.

The `$GITHUB_OUTPUT`, `$GITHUB_ENV`, and `$GITHUB_PATH` files are the mechanism by which steps propagate state to the context layer. The runner creates these as temporary files and sets their paths as environment variables before each step executes. A step writes key-value pairs to `$GITHUB_OUTPUT`, and the runner parses them after the step completes, populating the `steps.<id>.outputs` context for subsequent steps. The same pattern applies to `$GITHUB_ENV` for environment variables and `$GITHUB_PATH` for PATH modifications.

```yaml
name: Context Propagation Chain

on:
  push:
    branches: [main]

env:
  GLOBAL_CONFIG: production
  TIMEOUT_SECONDS: "300"

jobs:
  produce:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.extract.outputs.version }}
      artifact-name: ${{ steps.extract.outputs.artifact-name }}
      checksum: ${{ steps.extract.outputs.checksum }}
    steps:
      - uses: actions/checkout@v4

      - name: Extract version and compute checksum
        id: extract
        run: |
          VERSION=$(git describe --tags --always --dirty)
          ARTIFACT_NAME="app-${VERSION}.tar.gz"
          
          tar czf "$ARTIFACT_NAME" dist/
          CHECKSUM=$(sha256sum "$ARTIFACT_NAME" | awk '{print $1}')
          
          # Write outputs to $GITHUB_OUTPUT for downstream steps and jobs.
          echo "version=${VERSION}" >> "$GITHUB_OUTPUT"
          echo "artifact-name=${ARTIFACT_NAME}" >> "$GITHUB_OUTPUT"
          echo "checksum=${CHECKSUM}" >> "$GITHUB_OUTPUT"
          
          # Set an environment variable visible to subsequent steps.
          echo "ARTIFACT_PATH=$(pwd)/${ARTIFACT_NAME}" >> "$GITHUB_ENV"

      - name: Verify artifact
        env:
          EXPECTED_CHECKSUM: ${{ steps.extract.outputs.checksum }}
        run: |
          ACTUAL_CHECKSUM=$(sha256sum "$ARTIFACT_PATH" | awk '{print $1}')
          if [ "$ACTUAL_CHECKSUM" != "$EXPECTED_CHECKSUM" ]; then
            echo "Checksum mismatch: expected $EXPECTED_CHECKSUM, got $ACTUAL_CHECKSUM"
            exit 1
          fi
          echo "Checksum verified: $ACTUAL_CHECKSUM"

  consume:
    needs: produce
    runs-on: ubuntu-latest
    steps:
      - name: Use upstream job outputs
        env:
          VERSION: ${{ needs.produce.outputs.version }}
          ARTIFACT_NAME: ${{ needs.produce.outputs.artifact-name }}
          CHECKSUM: ${{ needs.produce.outputs.checksum }}
          GLOBAL: ${{ env.GLOBAL_CONFIG }}
        run: |
          echo "Deploying version $VERSION (artifact: $ARTIFACT_NAME)"
          echo "Checksum: $CHECKSUM"
          echo "Global config: $GLOBAL"
          echo "Triggered by: ${{ github.actor }} on ${{ github.ref_name }}"
```

### Expression Syntax and Evaluation

Expression evaluation in GitHub Actions uses a constrained language embedded in `${{ }}` blocks. The evaluator supports literal types (null, boolean, number, string in single quotes, array, object), operators (comparison: `==`, `!=`, `<`, `>`, `<=`, `>=`; logical: `&&`, `||`, `!`; index: `[ ]`; property access: `.`), and a set of built-in functions. Expressions are evaluated in two phases: structural expressions such as `runs-on`, `environment`, and `strategy.matrix` are resolved by the control plane at workflow compilation time, while step-level expressions in `if`, `env`, `with`, and `run` fields are resolved by the runner immediately before the step executes.

The type coercion rules are important for `if` conditionals. A string is coerced to `false` when it is empty, `0`, `null`, or `false` (case-insensitive); any other string is `true`. This means `if: ${{ env.SOME_VAR }}` evaluates to true when `SOME_VAR` is set to any non-empty, non-zero, non-false string. Numbers coerce to boolean in the natural way: zero is false, non-zero is true. Null is false. Empty arrays and objects are true in GitHub Actions' coercion, which differs from JavaScript's semantics.

The function library includes `contains(haystack, needle)` (string or array membership), `startsWith(haystack, needle)`, `endsWith(haystack, needle)`, `format(template, args...)` (printf-style string formatting), `join(array, separator)`, `toJSON(value)`, `fromJSON(string)`, `hashFiles(patterns...)` (SHA-256 hash of files matching glob patterns), and the status-check functions `success()`, `failure()`, `cancelled()`, and `always()`. The `hashFiles()` function is particularly significant for cache key construction: it computes a deterministic hash over the content of files matching the provided glob patterns, sorted by path, and returns a hexadecimal digest. This allows cache keys to be content-addressed—a cache miss occurs only when the relevant files change.

```yaml
name: Expression Evaluation Patterns

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
    tags: ['v*']

jobs:
  evaluate:
    runs-on: ubuntu-latest
    if: ${{ !github.event.pull_request.draft }}
    steps:
      - uses: actions/checkout@v4

      - name: Conditional on event type
        if: ${{ github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v') }}
        run: echo "This is a release build for tag ${{ github.ref_name }}"

      - name: Conditional on branch and file changes
        if: ${{ github.ref == 'refs/heads/main' }}
        env:
          CHANGED: ${{ contains(toJSON(github.event.commits.*.modified), 'infrastructure/') }}
        run: |
          echo "Infrastructure files changed: ${CHANGED}"
          if [ "$CHANGED" = "true" ]; then
            echo "Triggering infrastructure deployment"
          fi

      - name: Type coercion demonstration
        env:
          EMPTY_STRING: ""
          ZERO_STRING: "0"
          NONEMPTY: "value"
        run: |
          echo "Empty string as boolean: ${{ env.EMPTY_STRING == 'true' }}"
          echo "Zero string as boolean: ${{ env.ZERO_STRING == 'true' }}"
          echo "Non-empty as boolean: ${{ env.NONEMPTY != '' }}"

      - name: JSON transformation in expressions
        env:
          MATRIX_JSON: ${{ toJSON(matrix) }}
          GITHUB_CONTEXT: ${{ toJSON(github) }}
        run: |
          echo "Full matrix context as JSON:"
          echo "$MATRIX_JSON" | jq .
          
          echo "Event name from github context:"
          echo "$GITHUB_CONTEXT" | jq -r '.event_name'

      - name: hashFiles for content-addressed cache keys
        env:
          LOCK_HASH: ${{ hashFiles('**/go.sum', '**/go.mod') }}
          SRC_HASH: ${{ hashFiles('src/**/*.go') }}
        run: |
          echo "Dependency lock hash: ${LOCK_HASH}"
          echo "Source file hash: ${SRC_HASH}"
```

### Matrix Strategy Expansion

Matrix expansion is a compile-time operation. The control plane computes the cartesian product of all matrix dimensions, applies `exclude` filters, applies `include` additions, and generates a discrete set of job configurations. Each configuration becomes a separate job with its own runner allocation, its own `matrix` context, and its own position in the `strategy` context.

The expansion proceeds in three phases. First, the cartesian product of all matrix key-value arrays is computed. A matrix with three keys—`os: [ubuntu-latest, windows-latest]`, `arch: [amd64, arm64]`, `runtime: [dotnet8, dotnet9]`—produces eight combinations. Second, `exclude` entries are evaluated: each exclude entry matches a combination if all of its key-value pairs are present in that combination, and matched combinations are removed. Third, `include` entries are evaluated: each include entry adds new key-value pairs to matching combinations, or if no existing combination matches all the include entry's original keys, a new combination is created.

The `fail-fast` setting controls whether the control plane cancels in-progress and pending matrix jobs when one job in the matrix fails. The default is `true`, which is appropriate for cost-sensitive pipelines but problematic when you need all matrix jobs to complete regardless of individual failures—for example, when collecting test results across platforms. The `max-parallel` setting caps the number of matrix jobs that run concurrently, which is useful when downstream systems (a container registry rate limit, a cloud API quota) cannot handle full parallelism.

```yaml
name: Multi-Platform Build Matrix

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read
  packages: write

env:
  GO_VERSION: "1.23"
  CGO_ENABLED: "0"

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      max-parallel: 4
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        arch: [amd64, arm64]
        exclude:
          - os: windows-latest
            arch: arm64
        include:
          - os: ubuntu-latest
            arch: amd64
            target: linux-amd64
          - os: ubuntu-latest
            arch: arm64
            target: linux-arm64
          - os: windows-latest
            arch: amd64
            target: windows-amd64
          - os: macos-latest
            arch: amd64
            target: darwin-amd64
          - os: macos-latest
            arch: arm64
            target: darwin-arm64
    steps:
      - uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: ${{ env.GO_VERSION }}

      - name: Restore build cache
        uses: actions/cache@v4
        with:
          path: |
            ~/go/pkg/mod
            ~/.cache/go-build
          key: ${{ matrix.target }}-go-${{ hashFiles('**/go.sum') }}
          restore-keys: |
            ${{ matrix.target }}-go-

      - name: Build binary
        env:
          GOOS: ${{ matrix.target == 'linux-arm64' && 'linux' || matrix.target == 'linux-amd64' && 'linux' || matrix.target == 'windows-amd64' && 'windows' || 'darwin' }}
          GOARCH: ${{ matrix.arch }}
          TARGET: ${{ matrix.target }}
        run: |
          mkdir -p dist
          go build -trimpath -ldflags="-s -w" -o "dist/app-${TARGET}" ./cmd/server
          echo "Built dist/app-${TARGET} for ${GOOS}/${GOARCH}"

      - name: Run tests
        run: go test -v -race -coverprofile="coverage-${{ matrix.target }}.out" ./...

      - name: Upload binary artifact
        uses: actions/upload-artifact@v4
        with:
          name: binary-${{ matrix.target }}
          path: dist/
          retention-days: 30

      - name: Upload coverage artifact
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: coverage-${{ matrix.target }}
          path: coverage-${{ matrix.target }}.out
          retention-days: 14

      - name: Report matrix position
        env:
          JOB_INDEX: ${{ strategy.job-index }}
          JOB_TOTAL: ${{ strategy.job-total }}
        run: |
          echo "Matrix job ${JOB_INDEX} of ${JOB_TOTAL}"
          echo "Running on ${{ runner.os }} ${{ runner.arch }}"
          echo "Matrix target: ${{ matrix.target }}"

  release:
    needs: build
    runs-on: ubuntu-latest
    if: ${{ github.ref == 'refs/heads/main' && github.event_name == 'push' }}
    environment:
      name: production
      url: https://app.example.com
    steps:
      - uses: actions/checkout@v4

      - name: Download all binary artifacts
        uses: actions/download-artifact@v4
        with:
          path: dist
          pattern: binary-*
          merge-multiple: true

      - name: Create GitHub release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          TAG="v$(date -u +%Y%m%d%H%M%S)"
          gh release create "$TAG" dist/* \
            --title "Release ${TAG}" \
            --notes "Automated release from commit ${{ github.sha }}" \
            --target main

  notify:
    needs: [build, release]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Report pipeline status
        env:
          BUILD_RESULT: ${{ needs.build.result }}
          RELEASE_RESULT: ${{ needs.release.result }}
          WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
        run: |
          STATUS="failed"
          if [ "$BUILD_RESULT" = "success" ] && { [ "$RELEASE_RESULT" = "success" ] || [ "$RELEASE_RESULT" = "skipped" ]; }; then
            STATUS="passed"
          fi
          
          PAYLOAD=$(jq -n \
            --arg status "$STATUS" \
            --arg repo "${{ github.repository }}" \
            --arg sha "${{ github.sha }}" \
            --arg actor "${{ github.actor }}" \
            '{text: "Pipeline \($status) for \($repo)@\($sha) by \($actor)"}')
          
          curl -sf -X POST \
            -H 'Content-Type: application/json' \
            -d "$PAYLOAD" \
            "$WEBHOOK_URL"
```

### Artifact and Cache Persistence

Artifacts and caches are two distinct persistence mechanisms with different semantics, lifecycles, and backends. Artifacts are files produced by a workflow run and stored in GitHub's blob storage for later retrieval. They are scoped to a specific workflow run and are accessible via `actions/download-artifact` within the same run, or via GitHub's API for cross-run access. The `actions/upload-artifact@v4` action uses a chunked upload protocol that streams file content to GitHub's artifact backend, and `actions/download-artifact@v4` retrieves them by name. Artifacts have a configurable retention period (default 90 days, configurable per repository) and are immutable once uploaded—a second upload with the same artifact name in the same run fails rather than overwriting.

Caches are content-addressed key-value stores backed by GitHub's cache infrastructure. The `actions/cache@v4` action provides two operations: a restore phase that runs as a step precondition, searching for a cache entry matching the provided key or a `restore-keys` prefix, and a save phase that runs at step completion, storing the specified path under the computed key if no exact match was found. Cache entries are scoped to the repository and branch: a cache created on a feature branch is accessible to that branch and to the default branch, and a cache created on the default branch is accessible to all branches. This scoping prevents untrusted branches from poisoning the cache for protected branches, though it introduces a bootstrapping problem for new branches, which must either populate their own cache or fall back to the default branch's cache via `restore-keys`.

The `hashFiles()` function is the standard mechanism for computing cache keys. It takes one or more glob patterns, finds all matching files in the workspace, sorts them by path, and returns a SHA-256 digest of their concatenated content. This makes cache keys content-addressed: a cache hit occurs only when the relevant dependency manifests or lock files are unchanged between runs. The `restore-keys` parameter provides prefix-based fallback matching, allowing a partial cache (e.g., from a previous commit where only a subset of dependencies changed) to be restored when the exact key does not match.

```yaml
name: Cache and Artifact Pipeline

on:
  push:
    branches: [main]
  pull_request:

env:
  NODE_VERSION: "20"

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}

      - name: Restore dependency cache
        uses: actions/cache@v4
        id: npm-cache
        with:
          path: |
            ~/.npm
            node_modules
            packages/*/node_modules
          key: ${{ runner.os }}-node-${{ env.NODE_VERSION }}-${{ hashFiles('**/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-node-${{ env.NODE_VERSION }}-
            ${{ runner.os }}-node-

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

      - name: Upload build output
        uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: |
            dist/
            build/
          retention-days: 14

      - name: Upload test reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-reports
          path: |
            coverage/
            test-results/
            junit.xml
          retention-days: 30
```

### Reusable Workflows and Cross-Boundary Propagation

Reusable workflows, triggered via `workflow_call`, are the mechanism for sharing pipeline logic across repositories or within a repository's different workflows. The calling workflow passes inputs via `with:` and secrets via `secrets:`. The called workflow receives these through the `inputs` and `secrets` contexts. Variables (`vars`) and the `github` context are inherited automatically—the called workflow sees the caller's repository, event, and actor, not its own repository's metadata. The `env` context is not inherited: environment variables set in the calling workflow are not visible in the called workflow unless explicitly passed as inputs.

```yaml
# .github/workflows/reusable-container-build.yml
name: Reusable Container Build

on:
  workflow_call:
    inputs:
      image-name:
        required: true
        type: string
      dockerfile-path:
        required: false
        type: string
        default: Dockerfile
      push-image:
        required: false
        type: boolean
        default: false
      build-args:
        required: false
        type: string
        default: ""
    secrets:
      registry-username:
        required: true
      registry-password:
        required: true

env:
  REGISTRY: ghcr.io

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to container registry
        if: ${{ inputs.push-image }}
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.registry-username }}
          password: ${{ secrets.registry-password }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ inputs.image-name }}
          tags: |
            type=sha,format=long
            type=ref,event=branch
            type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}

      - name: Build and push image
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ${{ inputs.dockerfile-path }}
          push: ${{ inputs.push-image }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            VERSION=${{ github.sha }}
            BUILD_ARGS=${{ inputs.build-args }}
```

```yaml
# .github/workflows/deploy.yml
name: Deploy Application

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  packages: write

jobs:
  build-container:
    uses: ./.github/workflows/reusable-container-build.yml
    with:
      image-name: ${{ github.repository }}
      dockerfile-path: Dockerfile
      push-image: ${{ github.ref == 'refs/heads/main' }}
      build-args: |
        ENVIRONMENT=production
    secrets:
      registry-username: ${{ github.actor }}
      registry-password: ${{ secrets.GITHUB_TOKEN }}

  deploy:
    needs: build-container
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Kubernetes
        env:
          KUBECONFIG_DATA: ${{ secrets.PROD_KUBECONFIG }}
          IMAGE: ghcr.io/${{ github.repository }}:${{ github.sha }}
        run: |
          echo "$KUBECONFIG_DATA" | base64 -d > /tmp/kubeconfig
          export KUBECONFIG=/tmp/kubeconfig
          
          sed -i "s|IMAGE_PLACEHOLDER|${IMAGE}|g" deploy/deployment.yaml
          
          kubectl apply -f deploy/namespace.yaml
          kubectl apply -f deploy/deployment.yaml
          kubectl apply -f deploy/service.yaml
          kubectl apply -f deploy/ingress.yaml
          
          kubectl rollout status deployment/app -n production --timeout=300s
          
          rm -f /tmp/kubeconfig
```

## 3. High-Performance Optimization & Failure Modes

### Cache Key Design for Monorepos

In a monorepo where multiple services share a single repository, a naive cache key like `${{ runner.os }}-deps-${{ hashFiles('**/package-lock.json') }}` produces a cache miss whenever any service's lock file changes, even if the service being built has unaffected dependencies. The fix is to scope the `hashFiles()` glob patterns to the specific service's directory, producing per-service cache keys that change independently:

```yaml
- name: Cache service-specific dependencies
  uses: actions/cache@v4
  with:
    path: |
      services/payment-api/node_modules
      services/payment-api/.next/cache
    key: ${{ runner.os }}-payment-api-${{ hashFiles('services/payment-api/package-lock.json', 'services/shared/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-payment-api-
```

The `restore-keys` prefix allows fallback to a previous cache from the same service when the lock file has changed but the underlying dependency tree is largely the same. The restore phase searches keys in order: exact key match first, then prefix matches from longest to shortest. The first hit is used, and the save phase runs after the step completes, storing the updated path content under the exact key only if no exact match was found during restore. This avoids redundant cache writes and prevents cache thrashing.

### Matrix Optimization

Matrix explosion is the most common source of wasted CI minutes. A matrix with `os: [ubuntu, windows, macos]`, `arch: [amd64, arm64]`, `runtime: [go1.22, go1.23]`, and `mode: [debug, release]` produces twenty-four jobs. If only `ubuntu/amd64` needs to test both runtimes and both modes, the `exclude` and `include` keys must be used to prune the cartesian product rather than running all combinations. The pattern is to start with the full matrix, exclude combinations that are not needed, and use `include` to add properties to the remaining combinations:

```yaml
strategy:
  fail-fast: false
  max-parallel: 8
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    arch: [amd64, arm64]
    mode: [debug, release]
    exclude:
      - os: windows-latest
        arch: arm64
      - os: macos-latest
        arch: arm64
        mode: debug
      - os: macos-latest
        arch: amd64
    include:
      - os: ubuntu-latest
        arch: arm64
        mode: release
        target: linux-arm64-release
      - os: ubuntu-latest
        arch: amd64
        mode: release
        target: linux-amd64-release
```

The `max-parallel` setting should be tuned to the downstream system's capacity. If jobs push to a container registry with a rate limit of eight concurrent uploads, `max-parallel: 8` prevents rate-limit failures without serializing the entire matrix.

### Secret Leakage Vectors

The most common secret leakage vector is indirect output: a step echoes a variable that was set from a secret, and the output appears in the log. The runner masks the exact secret value, but if the variable is concatenated, truncated, or formatted before output, the substring may no longer match the registered value. For example, `echo "Token: ${TOKEN:0:8}..."` prints the first eight characters of a token, which will not be masked because the eight-character prefix is not the full registered value. The mitigation is to never echo secret-derived values, even partial ones.

A subtler vector is shell injection through untrusted context values. If a workflow interpolates `${{ github.event.pull_request.title }}` directly into a `run` step, and the PR title contains shell metacharacters, the shell interprets them:

```yaml
# UNSAFE: shell injection via PR title
- run: echo "Processing PR: ${{ github.event.pull_request.title }}"

# SAFE: pass via environment variable
- env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: echo "Processing PR: ${PR_TITLE}"
```

The environment variable pattern is safe because the shell does not interpret the value of a variable when expanding `${PR_TITLE}`—it performs word splitting and glob expansion, but not command substitution or redirection, on variable values. For values that may contain glob characters, wrap the expansion in double quotes: `echo "Processing PR: ${PR_TITLE}"`.

### Cache Poisoning and Concurrency

Cache entries are scoped by branch, but caches created on the default branch are accessible to all branches. This means a pull request from a fork can create a cache entry on its own branch, but that entry is not accessible to the default branch. However, if a workflow running on the default branch uses `restore-keys` that match a pattern also used by feature branches, and the feature branch's cache was created with different content, the default branch may restore stale or malicious content. The mitigation is to use branch-specific prefixes in cache keys and to avoid overly broad `restore-keys` patterns on protected branches.

Cache writes are not atomic. When two jobs in the same matrix run concurrently and both attempt to save a cache under the same key, the behavior is undefined: one write may succeed and the other may fail silently, or the cache backend may reject the second write. This is not a problem when cache keys include matrix-specific values like `${{ matrix.target }}`, but it is a problem when cache keys are shared across matrix jobs. The fix is to include a matrix dimension in the cache key to ensure uniqueness.

### GITHUB_TOKEN Permission Minimization

The `GITHUB_TOKEN` secret is automatically provisioned for every workflow run and is scoped to the repository. Its permissions can be restricted at the workflow level or job level using the `permissions` key. The principle of least privilege demands that each job receive only the permissions it needs. A job that only builds and tests needs `contents: read` at most. A job that creates releases needs `contents: write`. A job that pushes packages needs `packages: write`. Over-granting permissions creates a privilege escalation path: if a job is compromised (through a dependency confusion attack, a malicious action, or shell injection), the attacker's capabilities are bounded by the token's permissions.

```yaml
permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      checks: write
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test

  release:
    needs: test
    runs-on: ubuntu-latest
    if: ${{ github.ref == 'refs/heads/main' }}
    permissions:
      contents: write
      packages: write
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: gh release create "${{ github.sha }}" dist/*
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Environment Protection Rules as Deployment Gates

Environments are the strongest deployment safety mechanism in GitHub Actions. A job that targets an environment with required reviewers will not start until a reviewer approves, and the approval is recorded in the audit log. This is enforced by the control plane, not the runner, which means it cannot be bypassed by modifying the workflow file—a change to the workflow file requires a commit, which triggers a new run, which must again seek approval before the protected environment's jobs can execute. Combining environment protection rules with branch restrictions (only the `main` branch may deploy to `production`) and wait timers (a five-minute delay between approval and execution, providing a window for cancellation) creates a defense-in-depth deployment gate that is appropriate for infrastructure pipelines managing production systems.
