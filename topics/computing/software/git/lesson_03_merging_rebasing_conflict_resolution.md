# Lesson 3: Merging, Rebasing, and Conflict Resolution

## 1. First-Principles Intuition & Invariants

Git's power lies not in its superficial branching metaphor but in its precise representation of history as an immutable directed acyclic graph of content-addressed snapshots. Each commit is a cryptographic hash of its entire tree state and parent lineage, forming a Merkle tree where any alteration to historical content cascades forward, invalidating all descendant commit identifiers. This foundational invariant—that commits are mathematically immutable—gives Git its distributed resilience but introduces a central engineering challenge: how do we integrate divergent lines of development when independent actors have created incompatible modifications to the same codebase?

The merge problem in version control is fundamentally a problem of reconciling concurrent state mutations. When two developers fork from a common ancestor commit and independently advance their work, they create competing futures. The version control system must synthesize these futures into a coherent unified timeline without losing information or introducing logical inconsistencies. Unlike simpler systems that treat history as a linear sequence of patches, Git models history as a graph where multiple parents can contribute genetic material to a single descendant commit, or where the graph can be rewritten entirely to simulate an alternate timeline where concurrency never occurred.

At the heart of merge resolution lies the three-way merge algorithm, a technique borrowed from decades of research into text differencing and automatic program integration. The algorithm operates on a fundamental insight: to understand whether two modifications conflict, we must examine not just the two modified states but also their common ancestor. If Alice changes line 47 from "int x = 0;" to "int x = 1;" and Bob independently changes the same line to "int x = 2;", a two-way comparison between Alice's and Bob's versions reveals only that they differ—it cannot distinguish whether one should win, whether both changes are legitimate but incompatible, or whether they represent independent work on unrelated code. By anchoring the comparison at the merge base—the most recent common ancestor commit—we can determine that both parties modified the identical original line, signaling a genuine conflict requiring human adjudication.

Git's merge machinery operates within a strict set of invariants. First, merge commits are distinguished by having two or more parent pointers, creating a join point in the commit graph. Second, the merge base computation is a graph reachability problem: given two branch tips, we locate the lowest common ancestor through a bidirectional search up the parent chains. In simple cases with clean linear history, this ancestor is obvious; in complex graphs with criss-crossing merges, Git employs the recursive three-way merge strategy, which handles multiple candidate merge bases by recursively merging them first. Third, Git's diff and merge algorithms operate at the line granularity for text files, with pluggable drivers for binary formats. This line-level focus makes Git exceptionally good at merging independent changes to different functions in the same source file but requires human judgment when both parties edit the same statement.

Rebasing offers an alternative integration model rooted in the philosophy that history should tell a clean, linear story rather than preserve the chaotic reality of parallel development. Where merging creates explicit join points that acknowledge concurrent work, rebasing rewrites history to pretend that one line of work occurred strictly after another. The rebase operation takes a sequence of commits and replays them atop a new base, generating entirely new commit objects with new cryptographic identifiers but semantically equivalent content changes. This historical revisionism has profound implications: it produces a cleaner, more readable history at the cost of mutating shared state and potentially creating confusion for collaborators who have already incorporated the original commits into their work.

The tension between merging and rebasing reflects a deeper engineering tradeoff between fidelity and comprehensibility. Merges preserve the true structure of collaboration—they show when work happened in parallel, where integration points occurred, and who resolved conflicts. Rebase linearization erases this structure, producing a fiction where development proceeded in perfect sequence. For open-source projects where maintainers integrate dozens of contributions, rebasing produces a readable mainline history where each feature appears as a tidy sequence of commits. For teams working on shared branches with continuous integration, rebasing can produce chaos as developers repeatedly force-push rewritten history, invalidating their colleagues' working states.

The conflict detection mechanism operates through a three-way diff that partitions file content into clean regions and conflict regions. Clean regions are those where either both parties made identical changes, or only one party changed the content. Conflict regions are those where both parties modified overlapping sections differently. Git materializes conflicts directly in the working tree by inserting conflict markers—the infamous `<<<<<<<`, `=======`, and `>>>>>>>` delimiters—that bracket the competing versions. This in-tree conflict representation is elegant in its simplicity: the file system becomes the conflict resolution interface, allowing developers to edit conflicts with any text editor without requiring specialized tools.

Understanding these primitives—the immutable commit graph, the three-way merge algorithm, the rebase replay mechanism, and the conflict marker protocol—is essential before approaching the tactical workflows of collaborative development. Git gives developers extraordinary power to rewrite history, integrate parallel work, and recover from mistakes, but this power demands precision. A carelessly forced push can orphan colleagues' work; a misresolved conflict can silently introduce bugs; an ill-timed rebase can create duplicate commits that poison the repository with confusion. Mastery requires internalizing the invariants and building muscle memory for the workflows that respect them.

## 2. Core Architecture & Mechanics

The three-way merge algorithm begins with identifying the merge base—the commit that represents the most recent common ancestor of the two branches being integrated. Git's `merge-base` computation traverses the commit graph using a priority queue approach that walks backward through parent links from both branch tips simultaneously, marking visited commits until it finds the first commit reachable from both starting points. In the presence of criss-cross merges where multiple valid merge bases exist, Git's recursive strategy first merges these bases together to create a virtual common ancestor, then uses that synthetic commit as the reference point for the final three-way merge.

Once the merge base is identified, Git constructs three views of the repository tree: the merge base tree, the current branch tree (often called "ours"), and the incoming branch tree (often called "theirs"). For each path in the union of these three trees, Git computes the diff from base to ours and from base to theirs. If only one side changed a file, that change wins automatically. If both sides made identical changes, the result is the shared modification. If both sides changed the same file but in non-overlapping regions, Git performs a line-level three-way text merge to synthesize the combined result. If both sides changed overlapping regions differently, Git declares a conflict and marks the file accordingly.

The line-level merge uses a longest common subsequence algorithm to identify matching and differing regions. Git computes the diff from the base to each branch, producing two edit scripts that describe insertions, deletions, and modifications. The merge algorithm then attempts to apply both edit scripts simultaneously. When edits affect disjoint line ranges, they commute cleanly. When they overlap, the system conservatively declares a conflict rather than risk silently producing semantically incorrect code.

Consider the concrete case of merging a feature branch into main. The developer begins on main and executes `git merge feature-auth`. Git first resolves the merge base, identifying the commit where feature-auth originally diverged from main. It then compares three trees: the original divergence point, the current state of main, and the current state of feature-auth. Suppose a file `auth.c` was modified on both branches. Git runs a three-way diff on this file, comparing the base version against both modifications.

If main changed the function `verify_token()` while feature-auth changed the unrelated function `hash_password()`, the merge succeeds automatically, producing a combined file with both changes. Git creates a new merge commit with two parents, pointing to both the previous tip of main and the tip of feature-auth. This merge commit's tree represents the integrated state, and its commit message by default lists the branches that were unified.

If instead both branches modified overlapping lines in `verify_token()`, Git inserts conflict markers:

```text
<<<<<<< HEAD
int verify_token(const char *token) {
    if (strlen(token) < MIN_TOKEN_LENGTH) return -1;
=======
int verify_token(const char *token, size_t len) {
    if (len < MIN_TOKEN_LENGTH) return -1;
>>>>>>> feature-auth
```

The section between `<<<<<<< HEAD` and `=======` shows the current branch's version, while the section between `=======` and `>>>>>>> feature-auth` shows the incoming branch's version. The developer must manually edit the file to resolve the conflict, removing the markers and producing the desired final state. After resolving all conflicts, the developer stages the corrected files with `git add` and completes the merge with `git commit`, which finalizes the merge commit.

The merge machinery supports multiple strategies beyond the default recursive strategy. The `ours` strategy completely ignores incoming changes, keeping the current branch's content while still recording the merge commit to mark the integration point. The `theirs` option (available via `-X theirs` to the recursive strategy) prefers the incoming branch's changes when conflicts occur. The `octopus` strategy handles merging more than two branches simultaneously, though it aborts if manual conflict resolution would be required. The `subtree` strategy is specialized for integrating one project as a subdirectory of another, adjusting the tree comparison to account for path offsets.

Fast-forward merges represent a special case where the merge base is identical to the current branch tip—meaning the current branch has not advanced since the incoming branch diverged. In this topology, no actual merge computation is necessary; Git can simply advance the current branch pointer to aim at the incoming branch's tip. This produces a perfectly linear history with no merge commit. Developers can force the creation of an explicit merge commit even in fast-forward cases by using `git merge --no-ff`, which creates a two-parent commit despite the linear relationship. This explicit merge commit serves as a historical marker showing where a feature branch was integrated, which can aid in later analysis or reversion.

Rebasing operates through a fundamentally different mechanism. The command `git rebase main` while on a feature branch instructs Git to replay the feature branch's commits atop the current tip of main. Git begins by identifying the merge base, just as in merging, then constructs a list of all commits reachable from the feature branch tip back to the merge base. These commits are the "todo list" for the rebase. Git then checks out the target base (main's tip), enters a special rebase state, and begins cherry-picking each commit from the todo list in order.

Each cherry-pick is itself a three-way merge operation: the base is the cherry-picked commit's parent, "ours" is the current rebase HEAD, and "theirs" is the cherry-picked commit itself. Git applies the changes from the cherry-picked commit atop the current rebase state, creating a new commit with identical author information and commit message but a new parent pointer and new cryptographic hash. If conflicts occur during any cherry-pick, Git pauses the rebase, materializes the conflicts in the working tree, and prompts the developer to resolve them. After resolution, `git rebase --continue` proceeds to the next commit in the todo list.

The critical distinction is that rebase generates entirely new commit objects. If the original feature branch had commits `A -> B -> C` based on main's commit `M`, and main has since advanced to `M -> M' -> M''`, the rebase produces new commits `A' -> B' -> C'` that apply the same logical changes but start from `M''`. The original commits `A`, `B`, and `C` still exist in the object database but are no longer reachable from any branch, making them eligible for eventual garbage collection.

Interactive rebase extends this mechanism with editorial power. The command `git rebase -i main` opens a text editor with the todo list, allowing the developer to reorder commits, squash multiple commits into one, edit commit messages, or drop commits entirely. Each line in the todo list begins with a verb: `pick` to include the commit as-is, `reword` to change its message, `edit` to pause and allow amending, `squash` to combine with the previous commit, `fixup` to squash but discard the commit message, or `drop` to omit the commit. This workflow enables developers to polish a messy feature branch into a clean narrative before integrating it into the mainline.

The rebase state is managed through files in `.git/rebase-merge/` or `.git/rebase-apply/`, depending on the rebase mode. These directories track the todo list, the current step, conflict state, and original branch position. If a rebase encounters an intractable conflict or the developer makes an error, `git rebase --abort` restores the original branch state by resetting to the recorded original HEAD. Conversely, `git rebase --skip` abandons the current commit and moves to the next one, useful when a commit's changes are no longer relevant or have already been applied.

The topology transformations can be visualized through commit graph diagrams. Before merge:

```text
      A---B---C feature
     /
D---E---F---G main
```

After `git merge feature` on main:

```text
      A---B---C feature
     /         \
D---E---F---G---M main
```

Before rebase:

```text
      A---B---C feature
     /
D---E---F---G main
```

After `git rebase main` on feature:

```text
              A'--B'--C' feature
             /
D---E---F---G main
```

The original commits `A`, `B`, `C` are orphaned, replaced by `A'`, `B'`, `C'` which incorporate the changes from `F` and `G`.

Conflict resolution during rebase follows the same marker-based protocol as merge conflicts, but the mental model differs. In a merge, "ours" refers to the current branch and "theirs" refers to the incoming branch. In a rebase, the semantics invert: "ours" is the new base onto which commits are being replayed, and "theirs" is the commit being cherry-picked. This inversion confuses many practitioners, especially when using `git checkout --ours` or `--theirs` to resolve conflicts, as these options select opposite content depending on whether the operation is a merge or rebase.

Advanced merge scenarios involve handling renames, which Git detects through content similarity analysis. If a file is renamed on one branch and modified on another, Git's rename detection computes a similarity index based on content overlap and correctly attributes the modification to the renamed file rather than treating it as a deletion plus an unrelated addition. The `-M` and `-C` options to `git diff` and `git log` control rename detection sensitivity, with higher thresholds requiring greater similarity to consider two files as a rename pair.

Binary files and large objects complicate the merge model since line-level merging is meaningless for non-text content. Git declares any binary file conflict as requiring manual resolution, materializing both versions in the working tree and forcing the developer to choose one or manually reconstruct the desired state. Git Large File Storage (LFS) extends Git with pointer files that reference external binary storage, allowing the merge machinery to operate on tiny pointer files while the actual large binaries are versioned separately.

## 3. High-Performance Optimization & Failure Modes

Merge performance degrades with repository scale, particularly when merge base computation must traverse deep history with complex topology. Repositories with thousands of criss-crossing merges can experience expensive merge base calculations as Git's recursive strategy repeatedly merges virtual ancestors. The `merge.renameLimit` configuration caps the number of file pairs examined for rename detection, trading accuracy for speed in repositories with massive refactorings. Setting `diff.algorithm` to `histogram` or `patience` can improve merge quality for codebases with significant code motion, as these algorithms better track moved blocks than the default Myers diff.

Conflict resolution scales poorly with conflict density. A merge that touches hundreds of files with dozens of conflicts becomes cognitively overwhelming, especially if the conflicts span architectural boundaries requiring deep semantic understanding. High-conflict merges often indicate that branches have diverged too far—a symptom of inadequate integration cadence. Teams practicing continuous integration merge or rebase frequently, keeping branches short-lived and divergence minimal. Feature flags and branch-by-abstraction techniques allow incomplete features to merge into mainline without activating, reducing the window of isolation.

The failure mode of silent semantic conflicts is particularly insidious. Git's line-level merging can produce syntactically valid but semantically broken code when the conflict is at a higher level than individual lines. If one branch renames a function and another branch adds a call to that function using the old name, both changes merge cleanly but the result fails to compile. If one branch changes a function's signature and another adds a call using the old signature, the merge succeeds but introduces a type error. Comprehensive test suites are the only reliable defense against semantic conflicts—every merge should trigger a full build and test run to catch integration errors before they propagate.

Rebase introduces failure modes related to shared history mutation. If multiple developers are collaborating on a shared feature branch and one developer rebases and force-pushes, other developers' local branches now descend from commits that no longer exist in the remote. Subsequent pulls or pushes will detect the divergence and refuse to proceed unless the developer performs a forced update that discards local commits or manually reconciles the rewritten history. The golden rule is to never rebase commits that have been pushed to a shared branch unless all collaborators coordinate the rewrite. Rebase is safe and beneficial for local topic branches that have not been shared, or for feature branches owned by a single developer who is solely responsible for force-pushing.

The `git pull --rebase` workflow offers a middle ground, automatically rebasing local unpushed commits atop the fetched remote branch. This keeps local history clean while avoiding merge commits for simple pull operations. However, it requires understanding that each pull may rewrite recent local history, and any local branches based on those commits will need to be rebased as well. The `pull.rebase` configuration can be set to `true` to make this behavior default, though teams should establish clear conventions about when rebasing is appropriate.

Handling long-running feature branches demands discipline. As the mainline advances, the feature branch accumulates integration debt—the hidden cost of eventual conflict resolution. Periodically merging or rebasing the mainline into the feature branch surfaces conflicts incrementally rather than all at once. The choice between periodic merge and periodic rebase depends on team philosophy: periodic merges preserve the true history of integration points but create a cluttered graph, while periodic rebases keep the feature branch linear but rewrite history repeatedly.

Merge strategies for large-scale monorepos involve tooling beyond Git's native capabilities. Organizations like Google use massive monorepos with millions of commits and rely on custom merge automation, semantic conflict detection, and fine-grained dependency tracking to manage integration. For smaller teams, adopting a trunk-based development model with very short-lived feature branches minimizes merge complexity by reducing the opportunity for divergence.

The `git rerere` (reuse recorded resolution) mechanism caches conflict resolutions and automatically applies them to identical conflicts in future operations. When enabled via `rerere.enabled`, Git records the pre-resolution and post-resolution state of each conflict, indexing them by the conflict's content hash. If a subsequent merge or rebase produces an identical conflict, Git automatically applies the recorded resolution. This is invaluable during complex rebases where the same conflict may appear multiple times as commits are replayed, and for teams that maintain multiple long-lived branches where similar conflicts recur.

Conflict resolution strategies range from manual editing to tool-assisted workflows. The `git mergetool` command launches a configured graphical merge tool that displays the base, ours, theirs, and result panes, allowing developers to visually select chunks and construct the resolution interactively. Popular tools include `vimdiff`, `meld`, `kdiff3`, and `p4merge`, each with strengths for different workflows. For conflicts involving code, integrated development environments often provide semantic merge tools that understand language structure and can merge at the level of functions or classes rather than raw lines.

The nuclear option for irretrievably botched merges is `git merge --abort` during an active merge, or `git reset --hard ORIG_HEAD` immediately after completing a merge commit. Both restore the pre-merge state, allowing the developer to start fresh with a different strategy. The reflog (`git reflog`) serves as a safety net, recording every HEAD movement and allowing recovery of seemingly lost commits. Even after a forced rebase or a reset, the original commits remain in the object database and can be recovered via their reflog entries for a limited time before garbage collection.

Branch protection rules in hosted Git platforms like GitHub or GitLab enforce merge hygiene by requiring pull requests, status checks, and code reviews before integration. These platform features complement Git's core mechanics, transforming the raw merge operation into a gated workflow with quality assurance. Requiring that branches be up-to-date with the base before merging prevents races where a green pull request becomes broken by a subsequent merge to mainline.

The interplay between merge, rebase, and conflict resolution defines the collaborative workflow. Merging honors the true structure of parallel work and creates an auditable history of integration, at the cost of a complex graph. Rebasing produces a linear history that is easier to understand and bisect, at the cost of rewriting history and potential coordination hazards. Conflicts are inevitable when humans independently modify shared code, but disciplined integration cadence, strong test coverage, and tooling like rerere minimize their cost. Mastery lies not in avoiding conflicts but in recognizing which integration strategy serves the team's needs and executing it with precision.
