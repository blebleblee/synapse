# Lesson 2: Image Architecture, Layering, Registry Protocol

## 1. First-Principles Intuition & Invariants

Every container that ever ran on a Linux host began its life as an ordered sequence of immutable filesystem snapshots stacked into something that looks, to the processes inside it, like a perfectly ordinary root filesystem. This illusion is the central engineering achievement of the container image format, and understanding it from first principles is not merely academic. The decisions you make when writing a Dockerfile directly determine how much disk you consume, how long your CI pipeline spends pushing over a network, how much memory the kernel's page cache devotes to layer data, and whether a security scanner can accurately audit every byte your workload will execute.

The fundamental problem the image format solves is deduplication across time and space. Consider a fleet of a thousand nodes, each running dozens of microservices that all share the same Ubuntu base layer, the same OpenSSL library, and the same language runtime. If every image were a monolithic tarball, you would transfer gigabytes of redundant data for every deployment, store multiple copies of identical files on each node's disk, and evict useful pages from the kernel's page cache to make room for cold copies of data already resident in RAM. The layered image model solves all three problems simultaneously by making the shared lower layers both immutable and content-addressable: any two images that share a layer share the exact same bytes, the exact same inode mappings, and the exact same physical page frames.

The invariant that makes this work is immutability. A layer, once built, is never modified. Its content is identified by a cryptographic digest, specifically a SHA-256 hash of the uncompressed tarball of its filesystem delta. This content-addressed identity means you can verify integrity at every transfer boundary, deduplicate at the registry, deduplicate on the node's local store, and reason about layer composition as a pure function: given the same ordered sequence of layer digests, you always get the same merged filesystem. This is the OCI image content-addressability invariant, and every other property of the system flows from it.

The second invariant is that layers represent deltas, not full filesystem snapshots. When the Docker builder processes a `RUN apt-get install curl` instruction, it does not snapshot the entire filesystem. It records only the set of files added, modified, or deleted relative to the layer immediately below it. The layer format encodes deletions as special files called whiteout entries, defined by the OCI specification as files whose names begin with `.wh.`. A whiteout file at path `usr/bin/.wh.curl` signals that `usr/bin/curl` present in a lower layer must be hidden from the merged view. This delta encoding is what makes the deduplication strategy viable: a layer that installs a 50 MB package contributes exactly 50 MB to the image, not 50 MB plus the cumulative size of everything beneath it.

The union filesystem that assembles these layers at runtime is not itself part of the image specification. It is a kernel-level implementation detail that varies by host. The dominant implementation in production today is OverlayFS, merged into the mainline kernel in version 3.18 and now the default driver for virtually every container runtime on modern Linux. Understanding OverlayFS at the kernel level is prerequisite knowledge for diagnosing a wide class of production failures, including unexpected storage consumption, slow container start times, and subtle filesystem behavior differences between the build environment and the runtime environment.

OverlayFS presents a merged directory to userspace by compositing a stack of read-only lower directories with a single writable upper directory. The kernel's VFS layer handles all path resolution. When a process opens a file, the kernel's `ovl_lookup()` function walks the layer stack from top to bottom. If the file exists in the upper directory, that version is returned. If the file is absent from the upper directory but present in one of the lower directories, the kernel returns the lower layer's version directly, with no data copy. The file's pages are mapped directly from the lower layer's inode, which means that if ten containers share the same lower layer, they all share the same physical page frames for that layer's files. The kernel's page cache is a single physical copy serving all ten containers simultaneously, which is the memory-efficiency property that makes containers practical at the density required by modern microservice architectures.

The write path is where copy-on-write semantics enter. If a process inside a container attempts to modify a file that exists only in a lower read-only layer, the kernel's OverlayFS implementation performs a copy-up operation. The entire file is copied from the lower layer into the upper (writable) directory before the modification is applied. After copy-up, all subsequent writes go to the upper directory copy. The lower layer's inode is never touched. This has an important and frequently misunderstood performance implication: the first write to any file in a lower layer is expensive in proportion to the file's size, because the entire file must be read and written even if you are modifying only a single byte. For workloads that write to large files from lower layers, such as a database engine modifying its own shared library pages, this cost can be significant. This is precisely why running stateful workloads like databases directly on a container's writable layer is an antipattern; the correct architecture mounts a volume backed by a filesystem that does not incur copy-up overhead.

---

## 2. Core Architecture & Mechanics

### The OverlayFS Mount Structure

When the container runtime creates a container from an image with four layers, it assembles those layers into an OverlayFS mount with a precisely defined directory layout. The runtime creates a working directory on the host's backing filesystem, allocates an upper directory for the container's writable layer, and passes all four image layers as a colon-separated `lowerdir` argument to the mount syscall.

```text
mount -t overlay overlay \
  -o lowerdir=/var/lib/docker/overlay2/L4:L3:L2:L1,\
     upperdir=/var/lib/docker/overlay2/<container-id>/diff,\
     workdir=/var/lib/docker/overlay2/<container-id>/work \
  /var/lib/docker/overlay2/<container-id>/merged
```

The `workdir` is an internal OverlayFS requirement for atomic rename and copy-up operations. It must reside on the same filesystem as the `upperdir`. The `merged` directory is the root that the container runtime bind-mounts into the container's mount namespace as `/`. From the perspective of any process executing inside that namespace, it sees a single coherent root filesystem with no visible evidence of the layered structure beneath it.

The directory hierarchy Docker's overlay2 storage driver maintains on the host looks like this:

```text
/var/lib/docker/overlay2/
├── <layer-sha256-A>/
│   ├── diff/            ← filesystem delta for layer A
│   ├── link             ← short symlink name (avoids page_table argument limits)
│   └── lower            ← colon-separated list of parent layer link names
├── <layer-sha256-B>/
│   ├── diff/
│   ├── link
│   └── lower
├── <container-id>/
│   ├── diff/            ← upper (writable) layer for this container
│   ├── merged/          ← unified root presented to container namespace
│   ├── work/            ← OverlayFS internal workdir
│   └── lower            ← resolved lower layer chain
└── l/
    ├── ABCDEF -> ../layer-sha256-A/diff   ← short symlinks
    └── GHIJKL -> ../layer-sha256-B/diff
```

The `l/` directory and the short symlink indirection solve a concrete kernel-level constraint. The `lowerdir` argument to the `mount` syscall is a single string passed through the kernel's page-table argument mechanism, which has a fixed size limit of one memory page. With long SHA-256-based directory names, a deeply layered image would exceed this limit. Docker's overlay2 driver pre-computes short alphanumeric symlinks under `l/` and uses those short names in the `lowerdir` string, keeping the argument well within the page boundary.

You can directly observe the live mount state of any running container using standard Linux mount inspection:

```bash
# Find the overlay mount for a specific container
docker inspect --format='{{.GraphDriver.Data.MergedDir}}' <container-id>

# Inspect the full mount options including lowerdir chain
cat /proc/mounts | grep overlay

# See the layer chain for a specific container
docker inspect --format='{{range .GraphDriver.Data}}{{println .}}{{end}}' <container-id>
```

### OCI Image Specification: The Manifest, Index, and Config

The OCI Image Specification defines three distinct JSON document types that together describe a distributable, verifiable image. Understanding their relationships is essential for working with multi-architecture registries, image signing, and efficient pull optimization.

The **Image Index** (historically called a "fat manifest") is the top-level object returned when you `docker pull ubuntu:22.04` on a modern registry. It is a JSON document containing an array of manifest descriptors, each identified by its SHA-256 digest and annotated with a platform selector specifying OS and CPU architecture. The registry returns the index first, and the client selects the appropriate manifest for its platform. This is the mechanism that allows a single image tag to serve `linux/amd64`, `linux/arm64`, and `linux/s390x` from the same reference.

```json
{
  "schemaVersion": 2,
  "mediaType": "application/vnd.oci.image.index.v1+json",
  "manifests": [
    {
      "mediaType": "application/vnd.oci.image.manifest.v1+json",
      "digest": "sha256:a1b2c3d4...",
      "size": 1842,
      "platform": { "architecture": "amd64", "os": "linux" }
    },
    {
      "mediaType": "application/vnd.oci.image.manifest.v1+json",
      "digest": "sha256:e5f6a7b8...",
      "size": 1799,
      "platform": { "architecture": "arm64", "os": "linux", "variant": "v8" }
    }
  ]
}
```

The **Image Manifest** references exactly one Image Config and an ordered list of layer descriptors. The ordering is critical: layer `0` is the base, and each subsequent layer is applied on top. The manifest is itself content-addressed; its SHA-256 digest is what the Image Index points to, and it is what the client verifies after download.

```json
{
  "schemaVersion": 2,
  "mediaType": "application/vnd.oci.image.manifest.v1+json",
  "config": {
    "mediaType": "application/vnd.oci.image.config.v1+json",
    "digest": "sha256:9c8d7e6f...",
    "size": 7023
  },
  "layers": [
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
      "digest": "sha256:1a2b3c4d...",
      "size": 29536774
    },
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
      "digest": "sha256:5e6f7a8b...",
      "size": 15360
    }
  ]
}
```

The **Image Config** is a JSON document that is not a filesystem layer at all. It carries execution metadata: the default command (`Cmd`), entrypoint (`Entrypoint`), environment variables (`Env`), working directory (`WorkingDir`), exposed ports, and, critically, the full **DiffIDs** array. DiffIDs are the SHA-256 hashes of the uncompressed layer tarballs, while the manifest's layer descriptors reference the compressed blobs. This two-level hash structure is deliberate: the manifest digests allow transport-layer deduplication and verification at the registry API boundary, while the DiffIDs allow content verification after decompression on the client. The Image Config also contains the complete build history, recording every Dockerfile instruction along with whether it produced an empty layer.

The relationship among these three documents can be visualized as follows:

```text
Registry Tag Reference (ubuntu:22.04)
        │
        ▼
┌───────────────────┐
│   Image Index      │  (fat manifest, multi-arch)
│  digest: sha256:.. │
└────────┬──────────┘
         │  selects by platform
         ▼
┌───────────────────┐
│  Image Manifest    │  (single-arch)
│  digest: sha256:.. │
└──────┬─────┬──────┘
       │     │
       │     └─────────────────────────────────────┐
       ▼                                           ▼
┌──────────────┐                        ┌──────────────────┐
│ Image Config  │                        │  Layer Blob [0]  │
│  - Env, Cmd   │                        │  (gzip tarball)  │
│  - DiffIDs[]  │                        │  digest verified │
│  - History[]  │                        ├──────────────────┤
└──────────────┘                        │  Layer Blob [1]  │
                                        │  (gzip tarball)  │
                                        └──────────────────┘
```

### Registry Distribution Protocol

The OCI Distribution Specification (originally the Docker Registry HTTP API V2) defines the wire protocol used to push and pull images. Every `docker pull` and `docker push` resolves to a small number of well-defined HTTP operations against a content-addressed blob store. Understanding this protocol is prerequisite knowledge for operating air-gapped registries, debugging slow CI pipelines, and implementing custom registry proxies.

A pull operation proceeds in four phases. First, the client resolves the tag to a manifest digest via a `HEAD` or `GET` against the manifests endpoint: `GET /v2/<name>/manifests/<tag>`. The registry responds with the manifest JSON and its digest in the `Docker-Content-Digest` response header. Second, if the response is an Image Index, the client selects the appropriate platform manifest and fetches it by digest. Third, the client fetches the Image Config blob by its digest using `GET /v2/<name>/blobs/<digest>`. Fourth, the client iterates the manifest's layer list and for each layer checks whether the blob is already present in its local content store. If a layer is absent, the client fetches it with `GET /v2/<name>/blobs/<digest>`. Because blobs are content-addressed and the registry stores them by digest independently of image name, a blob that exists in `library/ubuntu` and is also referenced by `mycompany/appserver` is stored only once. When you pull `mycompany/appserver`, the registry-side deduplication means no duplicate storage, and the client-side check means no redundant transfer for layers already on the host.

A push operation is the mirror image. The client first checks blob existence via `HEAD /v2/<name>/blobs/<digest>`. If the registry returns `200`, the layer is already present and no upload is needed. If it returns `404`, the client initiates an upload session with `POST /v2/<name>/blobs/uploads/`, receives a session URL, streams the blob via `PATCH`, and commits with `PUT`. After all layers and the config blob are confirmed present, the client pushes the manifest with `PUT /v2/<name>/manifests/<tag>`. This existence check before upload is the mechanism that makes incremental image pushes fast: if only the top application layer changed, only that one blob is transferred.

You can replay these protocol steps manually using `curl` to introspect any OCI-conformant registry:

```bash
# Authenticate and obtain a bearer token (Docker Hub example)
TOKEN=$(curl -s "https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/alpine:pull" \
  | jq -r .token)

# Fetch the image index for alpine:latest
curl -s -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.oci.image.index.v1+json,application/vnd.docker.distribution.manifest.list.v2+json" \
  https://registry-1.docker.io/v2/library/alpine/manifests/latest | jq .

# Fetch a specific platform manifest by digest
curl -s -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.oci.image.manifest.v1+json" \
  https://registry-1.docker.io/v2/library/alpine/manifests/sha256:<digest> | jq .

# Check if a blob exists (HEAD request returns 200 or 404)
curl -I -H "Authorization: Bearer $TOKEN" \
  https://registry-1.docker.io/v2/library/alpine/blobs/sha256:<layer-digest>
```

---

## 3. High-Performance Optimization & Failure Modes

### Layer Ordering and Cache Invalidation

The Docker builder's layer cache is a deterministic function of instruction type and content, but its invalidation behavior is asymmetric in a way that destroys build performance if you do not understand the mechanics. Each instruction in a Dockerfile produces a cache key computed from the instruction string, the keys of all instructions above it, and, for `COPY` and `ADD` instructions, the content hashes of the source files. The critical property is that invalidating any layer invalidates every layer beneath it in the final image. Because layers are assembled bottom-up, an instruction at position N that misses cache forces a rebuild of all instructions from N to the end.

The practical consequence is that instruction ordering is not a style concern. It is a performance invariant. Layers that change rarely must come first. Layers that change with every commit must come last. Consider a Node.js application where `package.json` changes once per week but application source changes dozens of times per day. If you structure the Dockerfile naively by copying the entire project tree first and then running `npm install`, every source change, even a one-character edit to a comment, invalidates the `npm install` layer, forcing a fresh network fetch of all dependencies on every build. The correct structure copies only the dependency manifest first, runs the install step (producing a stable, cacheable layer), and then copies application source as the final layer.

```dockerfile
FROM node:20-alpine AS base

WORKDIR /app

# Layer 1: dependency manifests only — changes rarely
# Cache hit on 95%+ of commits
COPY package.json package-lock.json ./

# Layer 2: install dependencies — expensive, but cached when layer 1 hits
RUN npm ci --omit=dev

# Layer 3: application source — changes on every commit, always rebuilt
# Invalidates only this layer and anything below it
COPY src/ ./src/

CMD ["node", "src/index.js"]
```

The same principle applies to system package installation. Every `RUN apt-get install` invocation that produces a new layer should install all packages needed at that stage in a single instruction. Splitting package installation across multiple `RUN` instructions creates unnecessary intermediate layers, bloats the image with APT cache data, and multiplies cache invalidation surface area. The correct pattern chains update, install, and cache cleanup in a single `RUN` command to ensure that the APT cache never persists beyond the layer boundary:

```dockerfile
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libssl-dev \
        ca-certificates \
        curl && \
    rm -rf /var/lib/apt/lists/*
```

Omitting the `rm -rf /var/lib/apt/lists/*` step does not simply waste disk space on the host. Because OverlayFS layers are immutable and additive, those cached package lists cannot be removed by a later `RUN rm` instruction without leaving whiteout entries in the new layer, which the filesystem union resolves as invisible but which the image tarball still contains in full. The bytes of the APT cache are permanently resident in the lower layer's tarball and will be transferred on every pull of that image. This is a category of image bloat that many teams discover only after auditing image sizes in production.

### Multi-Stage Builds and the Attack Surface Reduction Invariant

Multi-stage builds exist to solve the fundamental tension between build-time dependencies and runtime images. A compiled Rust binary requires a full toolchain, cargo registry caches, and intermediate build artifacts during compilation. None of those things should be present in the final image that runs in production: they increase attack surface, inflate image size, and slow pull times. Multi-stage builds give you a clean architectural boundary between the build environment and the runtime environment.

```dockerfile
# ---- Build Stage ----
FROM rust:1.78-slim-bookworm AS builder

WORKDIR /build

# Cache dependency compilation separately from application compilation.
# Cargo only recompiles changed crates, so this layer is stable across
# source-only changes.
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo 'fn main() {}' > src/main.rs && \
    cargo build --release && \
    rm -rf src

# Now copy real source and trigger incremental recompilation
COPY src/ ./src/
RUN touch src/main.rs && cargo build --release

# ---- Runtime Stage ----
FROM debian:bookworm-slim AS runtime

# Install only runtime-required libraries; no compiler, no cargo, no sources
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libssl3 \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user; never run production workloads as UID 0
RUN useradd --uid 10001 --no-create-home --shell /sbin/nologin appuser

COPY --from=builder /build/target/release/myservice /usr/local/bin/myservice

USER appuser

EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/myservice"]
```

The runtime image produced by this Dockerfile contains the Debian slim base, the two runtime libraries, and the statically-linked binary. It contains no Rust toolchain, no Cargo registry, no source code, and no compilation artifacts. The difference in final image size between a naive single-stage build and this two-stage build is typically measured in hundreds of megabytes, and the reduction in exploitable attack surface, specifically in the elimination of compilers and package managers a compromised process could use to build further payloads, is architecturally significant.

The `COPY --from=builder` instruction is not limited to the immediately preceding stage. You can reference any named stage in the same Dockerfile, and you can reference external images using `COPY --from=<image-reference>`. This makes it practical to maintain separate base images for toolchains and to `COPY` pre-built tools from official images rather than installing them at build time:

```dockerfile
COPY --from=docker/buildx-bin:latest /buildx /usr/local/lib/docker/cli-plugins/docker-buildx
```

### Diagnosing Layer Bloat and Image Pathologies

Production images frequently develop pathologies where their size drifts far beyond what the manifest of installed software would justify. The standard `docker image ls` output shows only the compressed size. The uncompressed filesystem size, which is what the kernel actually maps into page cache, can be substantially larger. The first diagnostic tool is `docker image inspect` combined with direct examination of the layer store:

```bash
# Show all layers and their compressed sizes
docker image inspect <image> --format='{{json .RootFS.Layers}}'

# Use dive to interactively audit layer composition
# Install: https://github.com/wagoodman/dive
dive <image>

# Examine the uncompressed size of each layer directly
# by extracting and measuring the layer tarballs
docker save <image> | tar -xO manifest.json | python3 -m json.tool

# Enumerate all layers with their on-disk sizes in the overlay2 store
du -sh /var/lib/docker/overlay2/*/diff | sort -rh | head -20
```

The `dive` tool deserves particular attention in this context. It renders the filesystem delta of each layer alongside a running efficiency score, which measures the ratio of unique bytes to total bytes. An efficiency score below 0.95 generally indicates either duplicate data across layers or large files that are added in one layer and then partially deleted in a later layer, with the deletion represented as whiteout entries that cannot recover the bytes from the lower layer's tarball.

A common pathology is the secret-in-layer problem. Build arguments passed via `--build-arg` or files containing credentials copied into an intermediate layer are permanently embedded in the image history even if a subsequent instruction deletes them. Because layers are immutable and the lower layer's tarball still contains the file, any party with read access to the image can extract it by pulling the specific layer blob:

```bash
# Extract a specific layer from a pulled image to inspect its raw contents
docker save <image> -o image.tar
tar -xf image.tar
# Each layer is a directory containing a layer.tar
tar -tvf <layer-sha>/layer.tar | grep -i secret
```

The correct mitigation is to never introduce secrets into the build graph at all. For build-time secrets, Docker BuildKit provides a `--mount=type=secret` mechanism that injects a file into a `RUN` instruction's filesystem context without creating a layer entry:

```dockerfile
# syntax=docker/dockerfile:1.4
FROM python:3.12-slim

# The secret is mounted at /run/secrets/pip-token during this RUN only.
# It does not appear in any layer tarball or image history.
RUN --mount=type=secret,id=pip-token,target=/run/secrets/pip-token \
    pip install --extra-index-url "https://$(cat /run/secrets/pip-token)@pypi.company.internal/simple" \
        proprietary-library==2.3.1
```

Build invocation:

```bash
docker build --secret id=pip-token,src=~/.config/company/pip-token .
```

### Registry Storage and Garbage Collection

On a self-hosted registry, the relationship between tags, manifests, and blobs creates a reference-counting problem. When you push `myapp:v1.0.0` and then push a rebuilt `myapp:v1.0.0` to the same tag, the registry stores the new manifest under the tag reference but the old manifest and its unique blobs remain in the blob store. No tag points to the old manifest, but nothing has freed its storage. Over weeks of continuous deployment to a self-hosted registry, this unreferenced blob accumulation routinely consumes tens to hundreds of gigabytes.

The OCI Distribution Specification defines a garbage collection model in which the registry first builds a reference graph, marks all blobs reachable from any existing manifest, and then deletes any blob not in the reachable set. The registry-to-registry implementation varies, but on the reference implementation (`registry:2`) and on Harbor, garbage collection is a two-phase operation: first put the registry in read-only mode to prevent new writes from racing with the mark phase, then run collection.

For the Docker Distribution registry, the GC procedure is:

```bash
# Put registry into read-only mode by setting environment variable
# or by stopping write traffic before running GC
docker exec <registry-container> registry garbage-collect \
  --delete-untagged=true \
  /etc/docker/registry/config.yml
```

On Harbor, GC is managed through the administrator UI or API and executes with an integrated read-only lock. On cloud registries (ECR, GCR, Artifact Registry), lifecycle policies serve the same function by automatically expiring untagged images after a configurable retention period. The correct operational posture for any registry running continuous deployment is to define a lifecycle policy on day one, before the blob store grows large enough that GC becomes operationally risky.

### OverlayFS Failure Modes in Production

The most consequential OverlayFS failure mode in production is the interaction between overlayfs and the backing filesystem's limits. The overlay2 storage driver requires that the lower directories, upper directory, and work directory all reside on the same filesystem. On systems where `/var/lib/docker` is mounted on an XFS filesystem, OverlayFS requires XFS to be formatted with the `ftype=1` option to enable the filesystem's internal d-type (directory entry type) support. Without `ftype=1`, the kernel's overlayfs implementation cannot distinguish regular files from directories during whiteout resolution, and container creation fails with a cryptic error about directory entry types. This is a partitioning decision made at filesystem creation time and is not correctable without reformatting. Many production deployments have encountered this problem after expanding a Docker node fleet by mounting new EBS or NVMe volumes formatted with legacy defaults.

```bash
# Check ftype setting on an XFS filesystem
xfs_info /dev/sda1 | grep ftype

# Correct output for overlay2 compatibility:
# naming   =version 2              bsize=4096   ascii-ci=0, ftype=1
```

The second significant failure mode is inode exhaustion. Each file in a container's layer occupies an inode on the backing filesystem. A host running hundreds of containers, each with dozens of layers, can exhaust the inode table of an `ext4` filesystem whose inode count was fixed at mkfs time, even when substantial block space remains. The symptom is `ENOSPC` errors despite `df -h` showing available space. The diagnostic is `df -i`, which shows inode utilization independently of block utilization. The mitigation at filesystem creation time is `mkfs.ext4 -i 4096` to increase inode density, or migration to XFS, which allocates inodes dynamically and does not have a fixed inode count ceiling.

```bash
# Check inode utilization per filesystem
df -i /var/lib/docker

# Count inodes consumed by the overlay2 store
find /var/lib/docker/overlay2 -maxdepth 3 | wc -l

# Monitor inode usage trend over time
watch -n 5 'df -i /var/lib/docker'
```

Understanding these mechanics, from the OverlayFS page-sharing properties that justify high container density, through the OCI content-addressing model that makes registry deduplication exact rather than heuristic, to the copy-up overhead that makes writable layer workloads pathological for stateful data, gives you a complete mental model of the container image as a production artifact. Every optimization and every failure mode in this space traces back to one of the invariants established at the beginning of this lesson: immutability, content-addressability, and delta encoding. The image format is not an abstraction that hides filesystem complexity; it is a carefully engineered composition of kernel primitives that you can reason about, inspect, and optimize at every layer of the stack.
