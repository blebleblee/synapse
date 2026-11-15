# Lesson 1: Git Fundamentals — Objects, Hashing, and the Content-Addressable Store

## 1. First-Principles Intuition & Invariants

Every version control system makes an implicit promise: given a label — a branch name, a tag, a revision number — it will reconstruct the exact state of a project at some point in the past. What distinguishes Git from its predecessors is not that it makes this promise, but the mechanism by which it keeps it. Subversion identifies revisions with a monotonically incrementing integer stored in a central server. CVS tracks per-file revision histories with dotted decimal numbers. Both systems anchor their promises in a single, authoritative source of truth that you must trust because there is no independent way to verify its claims. Git refuses this architecture entirely. Its promise is not backed by a server's bookkeeping but by a mathematical proof embedded in every piece of data it stores.

The core insight driving Git's design is content-addressability: the address of an object is derived from its content, not assigned arbitrarily. When Git stores a file, it computes a SHA-1 digest of that file's contents and uses that digest as the storage key. If the content changes by even a single bit, the digest changes completely — the avalanche property of a cryptographic hash function ensures this. The corollary is that if you retrieve an object at a given address and it matches the expected hash, you have a mathematical guarantee of integrity with no central authority required. This is not an incidental feature. It is the foundational invariant from which Git's entire distributed model flows.

SHA-1 produces a 160-bit (20-byte) digest, conventionally expressed as a 40-character hexadecimal string. When you encounter `a1b2c3d4...` in Git output, you are reading a compressed representation of this digest, which simultaneously serves as an identity, a checksum, and a lookup key. Git stores every object it manages in a directory structure under `.git/objects/`, using the first two characters of the hex digest as a subdirectory name and the remaining 38 characters as the filename within that directory. An object with the hash `4b825dc642cb6eb9a060e54bf8d69288fbee4904` lives at `.git/objects/4b/825dc642cb6eb9a060e54bf8d69288fbee4904`. This fanout scheme prevents any single directory from accumulating tens of thousands of entries, which would degrade filesystem readdir performance.

The object store is immutable by design. Git never modifies an existing object; it only ever adds new ones. This immutability invariant has a profound consequence for distributed operation: two repositories that share an object hash share an identical object, with no synchronization protocol needed to verify this. When you clone a repository, Git transfers objects by hash. When you later fetch from a remote, Git computes the set difference between the two object graphs and transfers only what is missing. No timestamps, no locks, no coordination overhead. The hash graph is a self-describing, self-verifying data structure.

It is worth pausing to appreciate what SHA-1 collision resistance means in practice for Git. Linus Torvalds has described the choice of SHA-1 not purely as a security mechanism but as a consistency check: the probability of an accidental collision producing two objects with the same hash is astronomically small, and even a deliberately crafted collision (as researchers demonstrated with the SHAttered attack in 2017) requires enormous computational effort. Git has since added defenses against known collision attacks and is in the process of migrating to SHA-256, but the architectural principle — content-addressed objects with cryptographic hashing — remains unchanged. The choice of which hash function to use is a parameter; the content-addressability model is the invariant.

## 2. Core Architecture & Mechanics

Git's object store contains exactly four object types: blobs, trees, commits, and tags. These four types form a directed acyclic graph (DAG) that encodes every version of every file in a repository's history, along with the authorship metadata and tree structure that makes those versions meaningful. Understanding each type at the byte level is essential for every senior engineer who has ever needed to recover data from a corrupted repository, automate repository analysis, or debug a confusing merge conflict.

### The Blob

A blob stores raw file content. It has no filename, no permissions, no timestamp — only bytes. This is a deliberate design decision. Because filenames are not part of the blob, two files with identical content in different directories share a single blob object. Git computes a blob's hash by prepending a header of the form `blob <content-length>\0` to the raw content, then computing SHA-1 over the concatenation, then zlib-compressing the entire header-plus-content and writing it to the object store. The header is included in the hash to prevent type confusion: the hash of a blob and a tree with identical raw bytes will always differ.

You can observe this directly:

```bash
# Create a repository and inspect how Git stores a file
mkdir git-internals && cd git-internals
git init

echo 'hello, object store' > hello.txt
git add hello.txt

# Git wrote a blob; find it
find .git/objects -type f

# Read it back using git's plumbing
git cat-file -t $(git hash-object hello.txt)   # prints: blob
git cat-file -p $(git hash-object hello.txt)   # prints: hello, object store

# Manually reproduce the hash
printf 'blob 20\0hello, object store\n' | sha1sum
# Compare to:
git hash-object hello.txt
```

The `git hash-object` plumbing command is the lowest-level entry point into Git's object model. Without `-w` it only computes the hash without writing the object; with `-w` it writes. The `git cat-file` command is the complementary read path: `-t` returns the type, `-p` pretty-prints the content, and `-s` returns the size.

### The Tree

A tree encodes a directory listing. Where a filesystem inode stores a list of name-to-inode mappings, a Git tree stores a list of name-to-hash mappings, with each entry carrying a mode that encodes the entry type. A tree entry has the structure `<mode> <name>\0<binary-20-byte-hash>`. The mode field uses POSIX permission bit conventions in a simplified form: `100644` for a regular file, `100755` for an executable, `120000` for a symbolic link, and `040000` for a subdirectory (which points to another tree object). Like blobs, trees are prefixed with a `tree <size>\0` header before hashing.

Because a tree references its children by hash, it is itself content-addressed over the recursive structure of the entire subtree. If a file five levels deep changes, the blob hash changes, the tree referencing that blob changes, every ancestor tree up to the root changes, and ultimately the commit hash changes. This cascading hash invalidation means the root tree hash is a Merkle root — a single value that transitively commits to the state of every file in the working tree.

```bash
# Stage a directory structure
mkdir -p src/core
echo 'int main() { return 0; }' > src/core/main.c
echo 'CC=gcc' > Makefile
git add .

# Examine the index state
git ls-files --stage
# Output: mode hash stage filename
# 100644 <hash> 0 Makefile
# 100644 <hash> 0 src/core/main.c

# Write the tree from the index
TREE=$(git write-tree)
echo "Root tree: $TREE"

# Inspect the root tree
git cat-file -p $TREE
# tree <hash>    src
# blob <hash>    Makefile

# Recurse into the subtree
git cat-file -p <src-tree-hash>
# tree <hash>    core
git cat-file -p <core-tree-hash>
# blob <hash>    main.c
```

### The Commit

A commit object binds a root tree hash to authorship metadata and to zero or more parent commit hashes. Its format is a simple text record:

```
tree <root-tree-hash>
parent <parent-commit-hash>
author Name <email> <unix-timestamp> <tz-offset>
committer Name <email> <unix-timestamp> <tz-offset>

<blank line>
<commit message>
```

The parent field is absent for the initial commit, present once for a regular commit, and present twice for a merge commit. An octopus merge may have arbitrarily many parent lines. By including parent hashes, a commit transitively commits to its entire ancestry: the entire project history is encoded in a single Merkle DAG rooted at the latest commit hash. This is why `git log` can verify history integrity with `git fsck` and why a force-push that rewrites history cannot be silently forgiven — the new commits have different hashes and are literally different objects.

```bash
# Create the first commit manually using plumbing commands
TREE=$(git write-tree)
COMMIT=$(git commit-tree $TREE -m "initial commit")
echo $COMMIT

# Read the raw commit object
git cat-file -p $COMMIT

# Update HEAD to point to it
echo $COMMIT > .git/refs/heads/main
git log --oneline
```

The separation of author and committer timestamps is worth noting explicitly. When you cherry-pick or rebase a commit, the author name and date are preserved from the original commit, but the committer name and date reflect when you performed the operation. Rebase rewrites commits — it creates new commit objects with different parent hashes and different timestamps — and the fact that this changes all downstream hashes is not a bug. It is the hash function enforcing the semantics of history.

### The Tag

An annotated tag is a first-class object in the store. It contains a reference to any other object (almost always a commit), the tagger's identity, a timestamp, and a tag message. Because it is an object with its own hash, an annotated tag can be GPG-signed: the signature is embedded in the tag object body, and the hash of the signed tag object serves as a verifiable, tamper-evident label. A lightweight tag, by contrast, is not an object at all — it is simply a ref file containing a commit hash, indistinguishable in structure from a branch pointer.

```bash
# Create an annotated tag
git tag -a v1.0 -m "Release version 1.0" $COMMIT

# Inspect the tag object
TAG=$(git rev-parse v1.0^{})   # dereference to the tag object hash
git cat-file -p v1.0            # shows tag object body
git cat-file -t refs/tags/v1.0  # prints: tag
```

### The Object Graph in Full

The relationships among these four types form a complete, self-describing data structure:

```
HEAD
 │
 ▼
[commit a3f9...]  ◄── parent ──  [commit 7c2b...]  ◄── parent ──  [commit 1d08...]
  │                                 │                                 │
  ▼                                 ▼                                 ▼
[tree e4a1...]                  [tree 9f3c...]                   [tree 2b7d...]
  ├── blob 4b82...  Makefile       ├── blob 4b82...  Makefile       ├── blob 4b82...  Makefile
  └── tree 7e5d...  src/           └── tree 8c1a...  src/           └── tree 8c1a...  src/
        └── blob c9d3...  main.c         └── blob a1f4...  main.c         └── blob a1f4...  main.c
```

Notice that the blob for `Makefile` has the same hash (`4b82...`) in all three commits — the file never changed, so Git stores it exactly once. The `src/` tree changed between commit `1d08` and commit `7c2b`, causing new blob and tree objects to be created, while the unchanged state from commit `7c2b` to `a3f9` is represented by identical tree and blob hashes reused at zero additional storage cost. This structural sharing is not a compression optimization bolted on afterward; it falls out naturally from content-addressability.

### Refs, Packed Refs, and the Index

A ref is a named pointer to an object hash, stored as a plain UTF-8 text file under `.git/refs/`. The file `.git/refs/heads/main` contains the hex hash of the commit at the tip of `main`. When you commit, Git computes the new commit hash, writes the commit object to the object store, and atomically overwrites this file. HEAD itself is a symbolic ref stored at `.git/HEAD`, typically containing the string `ref: refs/heads/main` to indicate that it tracks the current branch indirectly.

For repositories with thousands of refs, maintaining one file per ref is expensive for directory enumeration and atomic update. Git compacts refs into a single file at `.git/packed-refs` using `git pack-refs`. Once packed, a ref is read from this file rather than from an individual path. The loose ref file, if present, takes precedence over the packed version for a given ref name, allowing new writes to proceed without touching the packed file.

The index (`.git/index`) is a binary file that caches the state of the working tree against the last commit. It stores the mode, hash, and stat information (mtime, ctime, dev, ino) for every tracked file. When you run `git status`, Git first checks the stat information in the index against the filesystem to quickly identify candidates for change, then computes hashes only for files whose stat data differs — this is the racy-git optimization. The index is the staging area: `git add` writes blob objects and updates the index; `git write-tree` turns the current index into a tree object.

## 3. High-Performance Optimization & Failure Modes

### Pack Files and Delta Compression

The loose object format — one zlib-compressed file per object — scales poorly for large repositories. A repository with ten years of commits may contain millions of objects. Reading such a repository one file at a time would be catastrophically slow on any filesystem, and transferring it over a network would be prohibitive. Git addresses this with pack files.

A pack file is a binary container that stores multiple objects, optionally using delta compression where one object is encoded as a base object plus a list of copy-and-insert operations (the OBJ_REF_DELTA and OBJ_OFS_DELTA formats). Git's delta selection algorithm uses a heuristic that groups objects by filename and content similarity, then chains deltas within each group. For text files with incremental changes — the dominant pattern in source repositories — the resulting pack files achieve compression ratios that make a full history of the Linux kernel fit in roughly a gigabyte.

```bash
# Inspect pack file contents
git gc --aggressive        # consolidate loose objects into a pack
ls .git/objects/pack/      # pack-<hash>.pack and pack-<hash>.idx

# Enumerate objects and their sizes in a pack
git verify-pack -v .git/objects/pack/pack-*.idx | sort -k 3 -n | tail -20

# Identify the largest objects in history (useful for auditing accidental binary commits)
git rev-list --objects --all \
  | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | awk '/^blob/ { print substr($0,6) }' \
  | sort -k 2 -n \
  | tail -20
```

The pack index (`.idx`) file allows Git to perform binary search for a given hash without deserializing the entire pack. The v2 index format stores a fan-out table, a sorted list of object hashes, CRC32 checksums per object, and 32-bit offsets. For packs larger than 2 GiB, an additional 64-bit offset table handles entries that overflow 32 bits.

Understanding pack file structure matters during garbage collection and remote operations. `git gc` runs automatically via `gc.auto` after a configurable number of loose objects accumulate. For CI servers that perform thousands of clones, excessive GC runs can stall pipelines. Tuning `gc.auto=0` and running `git gc` on a schedule, or using `git maintenance start` for background maintenance, is the production-grade approach.

### Shallow Clones and Partial Clones

A shallow clone creates a repository where the commit graph is truncated at a specified depth. Git writes a `.git/shallow` file containing the hashes of boundary commits — commits that are present but whose parents are treated as absent. This is useful for CI pipelines that need only the latest state without gigabytes of history.

```bash
# Clone with depth 1 for a fast CI checkout
git clone --depth 1 https://github.com/torvalds/linux.git linux-shallow

# Check how many objects were fetched
git -C linux-shallow count-objects -v

# Deepen later if needed
git -C linux-shallow fetch --deepen 50
```

A partial clone (introduced in Git 2.17) is more sophisticated: it fetches commits and trees lazily while omitting blob objects until they are accessed. The filter spec `--filter=blob:none` creates a blobless clone, downloading trees and commits up front but fetching blobs on demand. This is particularly effective for monorepos where most files are irrelevant to any given workflow.

```bash
git clone --filter=blob:none https://github.com/example/monorepo.git
```

The trade-off is latency on first access: any operation that needs to read a blob not yet locally present will trigger a network round-trip. For sparse-checkout workflows where engineers work in well-defined subdirectories, blobless partial clones combined with `git sparse-checkout` reduce clone time and disk usage by an order of magnitude.

### Object Store Corruption and Recovery

Because Git's object store is content-addressed, corruption is detectable and often recoverable. `git fsck` traverses the entire object graph, verifying that every referenced hash exists and matches its content. It identifies dangling objects (objects not reachable from any ref), missing objects, and corrupted objects.

```bash
# Full integrity check
git fsck --full --strict

# Check only reachable objects
git fsck --connectivity-only

# Recover dangling commits after an accidental reset
git fsck --lost-found
ls .git/lost-found/commit/   # each file is a recovered commit hash
```

The most common cause of a "missing object" error in production is an interrupted `git gc` or a filesystem failure during a push to a bare repository. If a pack file is partially written, the index may reference objects that do not exist in the pack body. Recovery depends on whether the objects exist in another repository. If you have a remote, re-fetching will restore missing objects. If the repository is a central bare repo with no other copy, the objects may be unrecoverable, which is an argument for maintaining at least two independent backups of critical bare repositories.

The `git replace` mechanism allows you to substitute one object for another without rewriting history — useful for injecting a repaired commit object to fix a corrupted message or author field without changing the hashes that downstream repositories have already recorded. The replacement is stored as a ref under `refs/replace/` and is transparent to most porcelain commands once the `--replace-objects` behavior is activated.

### The SHA-256 Transition

Git 2.29 introduced experimental support for SHA-256 repositories via `git init --object-format=sha256`. SHA-256 produces a 256-bit digest, expressed as a 64-character hex string, and eliminates the theoretical vulnerability exposed by SHAttered. The object format, header structure, and DAG semantics are identical; only the hash function and digest length change. Interoperability between SHA-1 and SHA-256 repositories requires a translation layer (the `compatibility object format` work ongoing in git's development), and no major hosting provider has fully migrated yet. For greenfield infrastructure projects with long time horizons, initializing repositories with `--object-format=sha256` is the defensible choice.

```bash
# Initialize a SHA-256 repository
git init --object-format=sha256 sha256-repo
cd sha256-repo

echo 'testing sha256' > test.txt
git add test.txt
git hash-object test.txt    # 64-character hex digest

# Confirm object format
git cat-file --batch-check='%(objectname) %(objecttype)' --batch-all-objects
```

### Practical Invariants for Production Workflows

The content-addressable model imposes several invariants that every senior engineer should internalize. First, identical content always produces identical hashes regardless of filename, path, or when the file was added — this means that moving a file is represented in Git as a deletion and an addition with the same blob hash, and Git's rename detection in `git diff -M` works by comparing blob hashes across sides of a diff. Second, any operation that claims to "modify" a commit — rebase, amend, cherry-pick — actually creates a new commit object with a new hash; the original object remains in the store until garbage collected. Third, force-pushing a branch after rewriting history does not delete the original objects from remotes that have already fetched them; it only moves the ref pointer. This is why `git reflog` can recover from almost any accidental rewrite during the default 90-day expiry window.

```bash
# Inspect the reflog to find a commit before an accidental reset
git reflog --format='%H %gd %gs' | head -20

# Restore a lost commit
git checkout -b recovery-branch <lost-commit-hash>

# Expire and prune to actually reclaim space (do this deliberately, not accidentally)
git reflog expire --expire=now --all
git gc --prune=now
```

These mechanics underpin every higher-level Git operation: branching, merging, rebasing, bisecting, and distributed collaboration. A mental model that treats branches as pointers into an immutable DAG of content-addressed objects, rather than as mutable containers of files, eliminates entire categories of confusion around detached HEADs, merge conflicts, and history rewrites. The hash is not bookkeeping metadata attached to a version — it is the version, inseparable from the content it identifies.
