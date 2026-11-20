# Lesson 2: References, Branching, and Directed Acyclic Graphs

## 1. First-Principles Intuition & Invariants

Git's power lies not in its interface but in its mathematical core: a directed acyclic graph of immutable commit objects addressable by cryptographic hashes. While casual users perceive branches as containers for code, experienced engineers recognize them as lightweight pointers into this graph, movable labels atop a persistent, immutable history. Understanding Git's reference system and DAG structure transforms it from an opaque version control tool into a programmable database of source code states, where every operation becomes a graph traversal or pointer manipulation.

The directed acyclic graph forms Git's foundational invariant. Each commit object contains one or more parent pointers, creating edges that flow backward through time. A commit with no parents represents a repository's genesis, while commits with multiple parents document merge operations that unite divergent histories. The acyclic property emerges not from runtime enforcement but from Git's append-only design: commits are immutable content-addressed objects whose SHA-1 hashes derive from their parent references. Creating a cycle would require altering a commit's parent field, which would change its hash, which would invalidate any child commits referencing it—a cascading impossibility that makes the DAG structure self-enforcing.

References provide human-readable navigation through this cryptographic graph. While commit hashes offer mathematical precision, their forty-character hexadecimal strings resist human memory and manual operation. Git's reference system overlays symbolic names atop these hashes, creating stable entry points into the DAG that developers can manipulate through branch creation, merging, and rebasing. These references live in `.git/refs/` as plain text files containing SHA-1 hashes, though performance-critical repositories compress them into the packed-refs file. The reference namespace partitions into semantic domains: `heads/` for local branches, `remotes/` for tracking branches from external repositories, and `tags/` for immutable release markers.

Branches represent the most misunderstood concept in Git because they violate intuitions formed from centralized version control systems. In Subversion or Perforce, branches are heavyweight directory copies that consume storage proportional to repository size. Git inverts this model entirely: a branch is a 41-byte file containing a commit hash and a newline character. Creating a thousand branches costs 41 kilobytes regardless of repository history. This economy fundamentally changes development workflows, making branches disposable experimental spaces rather than carefully managed long-lived entities. The HEAD reference adds indirection, pointing to the current branch rather than directly to a commit, enabling Git to update the branch pointer automatically during commit operations while preserving the developer's conceptual position in the reference namespace.

The distinction between branches and commits crystallizes Git's architecture. Commits form the permanent, immutable historical record, while branches provide temporary, mutable viewports into that history. Deleting a branch removes only the reference file; the commits remain reachable through reflogs, other branches, or direct hash reference. This separation enables Git's most powerful property: nondestructive experimentation. Developers can create exploratory branches, pursue dead-end implementations, and abandon entire development threads without corrupting the canonical history. The commits persist in the object database until garbage collection prunes unreferenced objects, typically after a 30-day grace period.

Graph reachability defines what commits belong to which branches. A commit is reachable from a reference if the graph contains a path from that reference to the commit by following parent pointers backward through history. This transitive closure determines merge base computation, ancestry queries, and garbage collection behavior. When Git performs `git log feature-branch`, it traverses the DAG from the feature-branch reference backward through all parent edges, collecting every reachable commit. Branch merging unites reachability sets by creating a new commit with multiple parents, while rebasing rewrites history by duplicating commits with different parents, leaving the original commits unreachable unless another reference preserves them.

The DAG's mathematical properties constrain Git's operational semantics. Fast-forward merges occur when the target branch's commit is a direct ancestor of the source branch's commit—the graph contains a simple path connecting them. Git need only update the target reference to match the source reference, creating no new commit object. Three-way merges arise when neither branch is an ancestor of the other, indicating divergent development that requires reconciliation. Git computes the nearest common ancestor using graph algorithms, diffs both branches against this merge base, and attempts automatic content integration. Merge conflicts surface when both branches modified identical content regions, forcing manual resolution because Git's content-addressable model cannot automatically determine semantic intent.

References exist in a hierarchy that mirrors filesystem semantics but operates under different rules. The path `refs/heads/feature/new-api` creates both a reference named `feature/new-api` and an implicit namespace preventing a reference named simply `feature`. This constraint prevents ambiguity: if both existed, `git checkout feature` would be underspecified. The hierarchy also enables wildcard operations and namespace-scoped reference transfers. Remote tracking branches occupy `refs/remotes/<remote-name>/`, creating isolated namespaces for each configured remote repository. Tags partition into lightweight (direct commit pointers) and annotated (signed objects containing metadata), with annotated tags providing GPG signature verification for release authenticity.

Symbolic references introduce a level of indirection critical for Git's branching model. HEAD typically contains `ref: refs/heads/main` rather than a commit hash, making it a pointer to a pointer. This double indirection allows `git commit` to update the current branch reference while HEAD remains stable. Detached HEAD states occur when HEAD points directly to a commit hash, breaking the indirection chain. In this state, new commits become unreachable when switching branches because no reference preserves them—they exist only in the reflog until garbage collection. Understanding symbolic references clarifies seemingly magical Git behaviors: why commits appear on branches automatically, how `git checkout` updates the working directory, and why certain operations require explicit branch creation.

## 2. Core Architecture & Mechanics

Git's reference system organizes around a filesystem-based database stored in `.git/refs/` with performance optimization through packed-refs consolidation. Each reference exists as either a loose file containing a 40-character SHA-1 hash or an entry in the packed-refs file, a sorted text database that enables binary search without scanning thousands of individual files. The packed-refs optimization becomes critical in repositories with extensive branching history, where enumerating loose refs incurs filesystem metadata overhead. Git automatically packs refs during garbage collection and periodically consolidates active refs into the packed-refs file while preserving loose refs for recently modified branches.

The reference namespace hierarchy uses forward slashes as path separators, but Git enforces constraints preventing filesystem ambiguity. Creating `refs/heads/feature/experimental` places a file at `.git/refs/heads/feature/experimental`, which requires `.git/refs/heads/feature/` to be a directory. Attempting to create a reference named `refs/heads/feature` afterward fails because the directory already exists. This mutual exclusion prevents ambiguous reference resolution where `git show feature` could mean either the branch or a parent namespace. The namespace rules extend to packed-refs: Git parses the file as newline-delimited records but maintains the same hierarchical exclusion constraints in memory.

Branch mechanics center on HEAD manipulation and reference updates. The HEAD file lives at `.git/HEAD` and contains either a symbolic reference like `ref: refs/heads/main` or a direct commit hash. When HEAD points to a branch reference, Git operates in normal mode: commits advance the branch pointer, merges update the branch, and checkouts preserve the symbolic link. The actual branch file at `.git/refs/heads/main` contains only the commit hash representing the branch tip. During `git commit`, Git reads HEAD, resolves it to the branch reference, reads the branch reference to get the current commit hash, creates a new commit with the current hash as parent, writes the new commit to the object database, and atomically updates the branch reference to the new commit's hash.

```bash
# Physical reference structure
.git/
├── HEAD                          # ref: refs/heads/main
├── refs/
│   ├── heads/
│   │   ├── main                  # 7a3f9b2c4d8e5f6a7b8c9d0e1f2a3b4c5d6e7f8
│   │   ├── feature/
│   │   │   ├── new-api          # 2b4c6d8e0f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9
│   │   │   └── experimental     # 4d6e8f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6
│   │   └── hotfix/
│   │       └── security-patch   # 6e8f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7
│   ├── remotes/
│   │   └── origin/
│   │       ├── HEAD             # ref: refs/remotes/origin/main
│   │       ├── main             # 7a3f9b2c4d8e5f6a7b8c9d0e1f2a3b4c5d6e7f8
│   │       └── develop          # 8b0c2d4e6f8a0b2c4d6e8f0a2b4c6d8e0f2a4b6
│   └── tags/
│       ├── v1.0.0               # 9c1d3e5f7a9b1c3d5e7f9a1b3c5d7e9f1a3b5c7
│       └── v2.0.0-rc1           # 0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b4c6d8
└── packed-refs                   # Consolidated reference database
```

The commit DAG structure emerges from parent pointers embedded in commit objects. Each commit object contains a tree reference, author metadata, committer metadata, and zero or more parent references. The parent field stores complete 40-character SHA-1 hashes, creating cryptographically strong edges in the graph. Single-parent commits form linear history chains, while multi-parent commits document merge operations. Orphan commits with no parents represent initial commits or disconnected history grafts. Git stores commit objects in `.git/objects/` using content-addressable storage: the object's SHA-1 hash determines its storage path, with the first two hash characters forming a directory and the remaining 38 characters forming the filename.

```bash
# Commit object internal structure
commit 245
tree 8c3b9d1e5f7a9b1c3d5e7f9a1b3c5d7e9f1a3b5c
parent 7a3f9b2c4d8e5f6a7b8c9d0e1f2a3b4c5d6e7f8
author Alice Engineer <alice@example.com> 1704672000 -0800
committer Alice Engineer <alice@example.com> 1704672000 -0800

feat: implement distributed cache layer

Adds Redis-backed caching with automatic invalidation
and consistent hashing for horizontal scaling.
```

Graph traversal algorithms power Git's core operations. Ancestry determination uses depth-first search starting from a reference and following parent pointers until reaching orphan commits or previously visited nodes. Git maintains a visited set using commit timestamps and topological ordering to prune redundant traversals. The `git log` command implements reverse chronological traversal with optional path filtering that examines each commit's tree diff. Merge base computation finds the lowest common ancestor using a bidirectional search: simultaneously traverse backward from both branch tips, marking visited commits, until encountering a commit visited from both directions. For merge bases involving more than two branches, Git computes pairwise bases and reduces them to a minimal set.

Reachability queries determine commit visibility and garbage collection eligibility. A commit is reachable if any reference can reach it through parent traversal, including direct refs, symbolic refs, reflogs, and the stash. Git's garbage collection scans all references, builds the reachable set through graph traversal, and marks unreachable objects for deletion after a grace period. The grace period (default 30 days for loose objects, 90 days for packed objects) prevents data loss when developers hold local references not yet pushed. Pruning operations walk the object database, checking each object against the reachable set, and removing objects that fall outside this set and exceed the grace period.

```bash
# DAG structure with merge commits
      A---B---C  (main)
           \
            D---E---F  (feature)
                     \
                      G  (merge commit with parents F and C)

# After merge, commit G has parent pointers:
# parent[0] = F (first-parent, preserves feature branch history)
# parent[1] = C (merged branch, preserves main branch history)
```

Remote tracking branches introduce namespace isolation for distributed collaboration. When Git fetches from a remote repository, it writes remote branch references to `refs/remotes/<remote-name>/`, creating read-only mirrors of the remote's branch state. These tracking branches serve as local caches, enabling offline operation and merge base computation without network access. The `git fetch` operation updates remote tracking branches by comparing local tracking refs with the remote's advertised refs, downloading missing commits, and updating tracking refs to match remote state. Local branches establish upstream relationships through configuration entries like `branch.main.remote = origin` and `branch.main.merge = refs/heads/main`, enabling `git pull` to automatically merge remote changes into local branches.

Tag semantics differ fundamentally between lightweight and annotated variants. Lightweight tags are direct references to commit objects, stored as files in `.git/refs/tags/` containing only a commit hash. Annotated tags create separate tag objects containing metadata: tagger identity, timestamp, tag message, and optional GPG signature. The tag object then references the target commit, adding a level of indirection. This distinction matters for release management: annotated tags enable cryptographic verification of release authenticity through GPG signatures, while lightweight tags provide convenient bookmarks without audit overhead. Tag immutability is convention rather than technical constraint—tags are regular references and can be force-updated—but Git warns on tag modification to prevent accidental history corruption.

Reference resolution follows a priority hierarchy when resolving ambiguous names. Given a partial reference like `feature`, Git searches in order: (1) `.git/feature`, (2) `.git/refs/feature`, (3) `.git/refs/tags/feature`, (4) `.git/refs/heads/feature`, (5) `.git/refs/remotes/feature`, (6) `.git/refs/remotes/feature/HEAD`. This ordering prioritizes local branches over remote tracking branches and allows short names like `git checkout feature` to automatically resolve to `refs/heads/feature`. Disambiguation becomes critical in repositories with namespace collisions—if both `refs/heads/release` and `refs/tags/release` exist, Git requires explicit full reference paths like `refs/heads/release` to prevent ambiguity.

The reflog mechanism provides a safety net for reference updates, logging every change to references with timestamps and previous values. Each reference maintains its own reflog at `.git/logs/refs/heads/<branch>` or in the packed-refs-log for consolidated storage. Reflog entries contain the old and new commit hashes, committer identity, timestamp, and action description. This audit trail enables recovery from destructive operations: `git reflog` shows recent HEAD movements, and `git reset --hard HEAD@{3}` restores HEAD to its position three operations ago. Reflogs expire after 90 days by default for reachable entries and 30 days for unreachable entries, balancing recovery capability against storage overhead.

Detached HEAD states occur when HEAD points directly to a commit rather than a branch reference, breaking the indirection chain that enables automatic branch updates. Operations like `git checkout <commit-hash>` or `git checkout <tag>` create detached HEAD by updating HEAD to contain a direct commit reference. In this state, new commits advance HEAD but leave no permanent reference, making them garbage collection candidates once HEAD moves. Detached HEAD serves critical roles in examining historical states, testing old commits, and building from specific versions. Recovering commits from detached HEAD requires creating an explicit branch: `git branch recovery-branch` creates a branch reference pointing to the current detached HEAD commit, preserving it in the reference namespace.

## 3. High-Performance Optimization & Failure Modes

Branch proliferation creates performance challenges in repositories with thousands of refs, degrading operations that enumerate all references like `git fetch` and `git branch --list`. Git's loose ref design scales poorly because each reference query requires filesystem access with attendant metadata overhead. Repositories exceeding 10,000 refs experience measurable slowdowns in ref iteration. The packed-refs optimization addresses this by consolidating refs into a sorted text file enabling binary search. Manual ref packing via `git pack-refs --all` immediately consolidates all loose refs, while automatic packing occurs during garbage collection. For repositories with extreme ref counts, consider ref namespacing strategies: archive old branches to `refs/archive/`, use tag patterns instead of persistent branches, or implement ref cleanup policies deleting merged branches after retention windows.

Reference update atomicity relies on filesystem rename semantics, which vary across platforms and filesystems. Git updates refs by writing new content to a temporary file, then atomically renaming it over the existing ref file. POSIX systems guarantee atomic renames within a filesystem, but networked filesystems (NFS, SMB) and Windows sometimes violate atomicity. Concurrent ref updates from multiple Git processes can corrupt refs on non-atomic filesystems, manifesting as empty ref files or truncated commit hashes. The packed-refs mechanism improves atomicity for bulk updates but introduces eventual consistency: Git searches loose refs before packed-refs, and updates create loose refs shadowing packed-refs entries until next consolidation. High-throughput automated workflows should coordinate ref updates through locking mechanisms or single-writer patterns.

```bash
# Force pack all refs for repositories with ref proliferation
git pack-refs --all --prune

# Analyze ref count and packed-refs size
echo "Loose refs:" $(find .git/refs -type f | wc -l)
echo "Packed refs:" $(grep -c '^[0-9a-f]' .git/packed-refs 2>/dev/null || echo 0)

# Identify stale remote tracking branches
git remote prune origin --dry-run

# Bulk delete merged feature branches older than 90 days
git for-each-ref --format='%(refname:short) %(committerdate:unix)' refs/heads/feature/ | \
  awk -v cutoff=$(date -d '90 days ago' +%s) '$2 < cutoff {print $1}' | \
  xargs -r git branch -d
```

DAG traversal performance degrades with repository size and merge complexity, particularly for ancestry queries spanning thousands of commits. Operations like `git log --graph` and `git merge-base` require walking the commit graph, with time complexity proportional to the number of commits examined. Repositories with frequent merges between long-lived branches create dense DAGs where merge base computation explores exponentially many paths. Git's commit-graph file provides a precomputed topological index accelerating graph traversals by 3-10x. The commit-graph stores topological levels (maximum distance from any orphan commit), parent relationships, and commit metadata in a binary format enabling O(1) random access. Enable commit-graph generation in `.git/config` with `core.commitGraph = true` and maintain it via `git commit-graph write --reachable --changed-paths`.

```bash
# Enable and generate commit-graph with reachability indexes
git config core.commitGraph true
git commit-graph write --reachable --changed-paths

# Verify commit-graph performance impact
time git log --graph --oneline --all  # Before
git commit-graph write --reachable
time git log --graph --oneline --all  # After

# Incremental commit-graph maintenance
git commit-graph write --reachable --split --changed-paths

# Inspect commit-graph statistics
git commit-graph verify
ls -lh .git/objects/info/commit-graph*
```

Reflog accumulation causes unbounded growth in `.git/logs/` as every reference update persists indefinitely within the expiration window. Repositories with automated continuous integration creating and deleting branches generate reflog entries at high rates, potentially consuming gigabytes over months. Reflog entries for deleted references persist after branch deletion, holding commits in the reachable set and preventing garbage collection. Aggressive reflog expiration policies balance recovery capability against storage overhead. The configuration `gc.reflogExpire` controls expiration for reachable entries (default 90 days), while `gc.reflogExpireUnreachable` controls unreachable entries (default 30 days). High-churn repositories should reduce these to 14 days and 7 days respectively, accepting reduced recovery windows for storage efficiency.

```bash
# Configure aggressive reflog expiration for CI/CD repos
git config gc.reflogExpire 14.days.ago
git config gc.reflogExpireUnreachable 7.days.ago

# Immediately expire reflogs older than 7 days
git reflog expire --expire=7.days.ago --all

# Audit reflog storage consumption
du -sh .git/logs/
find .git/logs/refs -type f -exec wc -l {} + | sort -rn | head -20

# Prune and garbage collect with aggressive settings
git gc --aggressive --prune=now
```

Detached HEAD states create orphan commits vulnerable to garbage collection, causing data loss when developers unknowingly abandon work. The risk manifests in workflows examining historical commits (`git checkout v1.0.0`), bisecting bugs (`git bisect`), or building from specific commits. Orphan commits become unreachable when checking out a branch, triggering garbage collection after 30 days. Developers lose work believing commits were saved because they completed `git commit` successfully, not recognizing the detached HEAD warning. Prevent orphan commits by establishing a discipline: always create a named branch before committing in detached HEAD state. Git's warning message "You are in 'detached HEAD' state" should trigger immediate branch creation: `git checkout -b experiment-branch` before proceeding with commits.

```bash
# Detect if currently in detached HEAD
if ! git symbolic-ref -q HEAD > /dev/null; then
  echo "WARNING: Detached HEAD detected"
  echo "Current commit: $(git rev-parse HEAD)"
  echo "Create branch: git checkout -b <branch-name>"
fi

# Recover orphaned commits from reflog after accidental detachment
git reflog show --all
git checkout -b recovery-branch <commit-hash>

# List all orphaned commits not reachable from any ref
git fsck --unreachable --no-reflogs | grep commit
```

Merge base computation fails in repositories with multiple disconnected histories, typically from importing external codebases or force-pushing unrelated branches. When two branches share no common ancestor, `git merge-base` returns no result, causing merge operations to fail with "refusing to merge unrelated histories." This manifests during repository migrations, monorepo consolidations, or when accidentally pushing to wrong remote branches. The `--allow-unrelated-histories` flag bypasses this safety check, performing a merge without a merge base by treating both branch tips as orphan commits and merging their complete trees. Use this cautiously: merging unrelated histories creates synthetic merge bases that obscure true ancestry relationships and complicate future merges.

```bash
# Diagnose unrelated histories during failed merge
git merge feature-branch
# fatal: refusing to merge unrelated histories

# Inspect whether branches share common ancestry
git merge-base main feature-branch
# Empty output indicates no common ancestor

# Merge unrelated histories with explicit override
git merge --allow-unrelated-histories feature-branch

# Identify disconnected DAG components
git log --oneline --graph --all --simplify-by-decoration
```

Reference namespace collisions occur when automation creates refs matching existing namespaces, violating Git's hierarchical exclusion rules. Attempting `git branch feature` when `feature/experimental` exists fails because `.git/refs/heads/feature` must be a directory for the child branch to exist. Similarly, creating `feature/experimental` when `feature` exists as a branch fails. These conflicts surface in CI/CD systems auto-generating branch names from ticket identifiers or build numbers without namespace coordination. Prevention requires enforcing branch naming conventions: reserve top-level namespaces for categories (`feature/`, `hotfix/`, `release/`), never create branches matching category names, and validate branch creation in pre-receive hooks rejecting namespace violations.

```bash
# Detect namespace collision preventing branch creation
git branch feature
# fatal: cannot lock ref 'refs/heads/feature': 'refs/heads/feature'
# exists; cannot create 'refs/heads/feature'

# List all refs to identify conflicting namespaces
git for-each-ref --format='%(refname)' | sort

# Rename conflicting branch to free namespace
git branch -m feature feature-main

# Enforce namespace discipline in pre-receive hook
#!/bin/bash
while read oldrev newrev refname; do
  if [[ "$refname" =~ ^refs/heads/(feature|hotfix|release)$ ]]; then
    echo "ERROR: Top-level category branches not allowed: $refname"
    exit 1
  fi
done
```

Remote tracking branch desynchronization creates phantom branches that no longer exist in the remote repository, accumulating as developers delete merged branches remotely but forget to prune local tracking refs. The `git branch -r` output lists stale remote tracking branches that `git fetch` never updates because the remote stopped advertising them. These phantom refs consume mental overhead, clutter branch listings, and occasionally cause confusion when developers checkout stale tracking branches expecting current work. Regular pruning via `git remote prune origin` removes tracking branches whose remote counterparts vanished. Automating prune during fetch through `git config remote.origin.prune true` maintains tracking branch accuracy without manual intervention.

```bash
# Configure automatic pruning during fetch
git config remote.origin.prune true

# Manually prune stale remote tracking branches
git remote prune origin --dry-run  # Preview
git remote prune origin            # Execute

# Identify tracking branches without upstream refs
comm -23 \
  <(git branch -r | grep origin/ | cut -d'/' -f2- | sort) \
  <(git ls-remote --heads origin | cut -d'/' -f3- | sort)
```

Tag mutability violates the immutability expectation for release markers, creating reproducibility failures when tags silently change between checkouts. Git allows force-updating tags with `git tag -f`, enabling malicious or accidental tag modification that alters release artifacts without version number changes. Developers building from `v1.0.0` at different times receive different code, breaking reproducible builds and audit trails. Prevent tag mutation through server-side `receive.denyNonFastForwards` and `receive.denyDeletes` for `refs/tags/*`, rejecting force-pushed tags. Annotated tags with GPG signatures provide cryptographic integrity: signature verification detects tag modification, though this requires rigorous key management and verification discipline in build pipelines.

```bash
# Detect tag mutation by comparing local and remote tags
git ls-remote --tags origin | while read hash ref; do
  tag=${ref#refs/tags/}
  local_hash=$(git rev-parse "refs/tags/$tag" 2>/dev/null)
  if [[ -n "$local_hash" && "$local_hash" != "$hash" ]]; then
    echo "WARNING: Tag $tag differs between local ($local_hash) and remote ($hash)"
  fi
done

# Server-side configuration preventing tag mutation
git config receive.denyNonFastForwards true
git config receive.denyDeletes true

# Create immutable annotated tag with GPG signature
git tag -a -s v2.0.0 -m "Release 2.0.0 - production deployment"

# Verify tag signature before building
git tag -v v2.0.0
git verify-tag v2.0.0
```
