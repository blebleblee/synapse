# Lesson 2: Sed Advanced Patterns — Flow Control, Scripting, and Complex Transformations

## 1. First-Principles Intuition & Invariants

Sed was designed in 1973 by Lee McMahon at Bell Labs as a stream editor built on top of the ed line editor, and that heritage is not merely historical trivia. The fundamental computational model that McMahon chose — a single-pass, line-oriented state machine — is the invariant from which every advanced feature in sed derives its power and its constraints. Understanding why sed works the way it does requires internalizing this model at the level of its execution loop before writing a single complex script.

At its core, sed processes input through a cycle. It reads one line from the input stream into what is called the pattern space, executes the entire sequence of commands against that pattern space, and then — unless suppressed by `-n` — prints the pattern space to standard output and clears it before reading the next line. This cycle is not a suggestion or an approximation; it is the architectural invariant around which every sed program is structured. The pattern space is a mutable string buffer. That buffer is the only thing sed's commands operate on during normal execution.

The critical insight that separates novice from expert sed usage is recognizing that this single-pass model implies two things simultaneously: it is extremely memory-efficient (sed's memory consumption is bounded by the size of the largest line it must hold, not the size of the file), and it is architecturally incapable of random access. You cannot jump to line 500 and then back to line 10. You cannot hold an arbitrary number of lines in memory simultaneously. Every advanced sed technique is, at its root, a clever exploitation of two supplementary buffers — the hold space and the cycle counter — to simulate state within this strict sequential model.

The hold space is a second string buffer, persistent across cycles. Unlike the pattern space, which is wiped at the end of each cycle, the hold space retains its content until explicitly modified. This asymmetry is the foundation of multi-line processing, reversal, and deferred output. Beginners encounter sed as a substitution tool. Senior engineers must encounter it as a two-register state machine with conditional branching, because that is precisely what it is.

The branching model is equally fundamental. Sed's `b` and `t` commands are unconditional and conditional branch instructions respectively. Labels, defined with the `:label` syntax, are jump targets within the script. The `t` command branches to a label *only if* a successful substitution has occurred since the last line was read or since the last `t` test was evaluated. This conditional-on-substitution-success model is not arbitrary; it is the mechanism by which sed implements iteration. Because sed has no native loop construct, the combination of substitution, `t`, and a label is the canonical way to implement bounded repetition within a single cycle. The sequence reads: attempt a substitution, and if it succeeded, jump back and try again. This is a while-loop expressed through the semantics of a string-rewriting system.

Understanding the `t` command's reset condition is crucial to avoiding silent logical errors. The substitution flag is reset under exactly two conditions: when a new line is read into the pattern space (starting a new cycle), and when a `t` or `T` branch instruction is evaluated, regardless of whether the branch was taken. This means a `t` command that falls through (because the preceding substitution failed) also resets the flag. If your script relies on chained `t` checks, you must account for this reset behavior or your control flow will be incorrect.

The POSIX standard defines sed's behavior, but the two dominant implementations — GNU sed and BSD/macOS sed — diverge in several important ways. GNU sed supports `\w`, `\+`, `\|` and other extended-regex extensions in basic regex mode, as well as `-E` for ERE (which uses `+`, `|`, `?` without backslash escaping). BSD sed requires `-E` for extended regex and does not support all GNU extensions. The `\n` in a replacement string inserts a newline in GNU sed; BSD sed requires a literal escaped newline. Any production script intended to run on both platforms must be written to the POSIX common subset or must explicitly gate on `$(uname)`. Throughout this lesson, GNU sed 4.x behavior is the reference implementation.

---

## 2. Core Architecture & Mechanics

### The Execution Engine

The sed execution engine can be described precisely as a state machine over two string buffers with a program counter that moves through a list of compiled commands. At process startup, sed compiles the script into an internal representation — a linked list of command nodes, each containing an address specification, an operator, and operator arguments. The address specification determines whether a command fires on a given cycle. It can be a line number, a regex match, a range between two addresses, the last line (`$`), or the complement of any of these (via `!`).

The execution model for a single cycle looks like this:

```
READ line into pattern space
FOR EACH command in script:
    IF address matches current line:
        EXECUTE command
        IF command is 'd':  GOTO next_cycle
        IF command is 'q':  PRINT and EXIT
        IF command is 'b label': GOTO label
        IF command is 't label' AND sub_flag: RESET sub_flag; GOTO label
END FOR
PRINT pattern space (unless -n)
CLEAR pattern space
next_cycle:
```

This pseudocode reveals something that diagram-centric explanations obscure: `d` does not "delete the line and continue." It terminates the current cycle entirely, jumping directly to the next cycle without executing any subsequent commands and without printing. This is distinct from `D`, which deletes only the first line of the pattern space and re-starts the cycle from the beginning of the script with the remaining content still in the pattern space. The difference between `d` and `D` is the difference between discarding the entire buffer and re-entering the program loop with a partial buffer — a distinction that becomes critical in multi-line processing.

The control flow graph of a sed script with branching looks like this:

```
                    ┌─────────────────────────────┐
                    │        READ new line         │
                    │   (reset substitution flag)  │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │         cmd[0]: s/a/b/       │◄──── :loop_label
                    └──────────────┬──────────────┘
                           match? ─┤─ no match?
                           [flag=1]│         │
                    ┌──────────────▼──┐       │
                    │  cmd[1]: t loop │       │
                    │  (flag==1?)     │       │
                    └──┬──────────────┘       │
                 yes ──┤                      │
                       │  no (fall-through)   │
         ┌─────────────▼──────────────┐       │
         │  RESET flag; GOTO :loop    │       │
         └────────────────────────────┘       │
                                              ▼
                              ┌───────────────────────────┐
                              │     remaining commands     │
                              └────────────┬──────────────┘
                                           ▼
                              ┌───────────────────────────┐
                              │     PRINT pattern space    │
                              └───────────────────────────┘
```

### Multi-Line Commands: N, D, and P

The `N`, `D`, and `P` commands form a triad for multi-line processing that must be understood as a coordinated mechanism rather than three independent features.

`N` appends the next line from input to the pattern space, inserting a newline character (`\n`) between the current content and the appended line. This is the only way to get more than one input line into the pattern space simultaneously. After `N`, the pattern space contains a multi-line string, and you can use `\n` in your regex to match and manipulate the boundary between original lines. This is how sed can join continuation lines, collapse multi-line constructs, and perform transformations that span line boundaries — operations that are impossible in the basic single-line cycle.

`P` prints only the first line of the pattern space (up to and including the first embedded `\n`). This is the multi-line analogue of the default print, used in conjunction with `N` and `D` to implement a sliding-window buffer.

`D` deletes the first line of the pattern space (up to and including the first embedded `\n`) and then re-starts the execution cycle from the beginning of the script without reading a new line. This re-start behavior is what makes `D` the critical ingredient in a sliding multi-line window: after deleting the consumed line, the script re-processes the remaining content in the pattern space as if it were a freshly read line, allowing the script to continue matching across the now-shifted window.

The canonical multi-line join pattern — joining a line ending with `\` to its successor — demonstrates the triad in action:

```sed
# Join lines where the current line ends with a backslash
:join
/\\$/ {
    N
    s/\\\n//
    b join
}
```

This script reads a line. If it ends with `\`, it appends the next line via `N`, removes the `\` and embedded newline, then branches back to `:join` to test whether the now-combined line still ends with `\`. It loops until no trailing backslash remains, producing a single joined line from an arbitrary number of continuation lines.

### Hold Space Operations

The hold space commands form the foundation of any sed program that must reference earlier content while processing later content. `h` copies the pattern space to the hold space (overwriting). `H` appends the pattern space to the hold space (with a separating `\n`). `g` copies the hold space to the pattern space (overwriting). `G` appends the hold space to the pattern space. `x` exchanges the pattern and hold spaces.

A concrete and illuminating example is line reversal. Reversing the order of lines in a file without loading the entire file into memory at once is a classic systems programming problem. GNU `tac` does this, but implementing it in pure sed reveals the hold space's power:

```sed
# Reverse line order: last line first
1!G
h
$!d
```

On line 1, `1!G` does not fire (the `!` inverts the address match), so the pattern space contains only line 1. `h` copies it to the hold space. `$!d` deletes the pattern space and starts the next cycle (since we're not on the last line). On line 2, `1!G` appends the hold space (line 1) to the pattern space, so the pattern space is now "line2\nline1". `h` saves this to the hold space. `$!d` discards and continues. This accumulates in reverse order. When the last line is reached, `$!d` does not fire, so the fully reversed content is printed.

This is a pure two-register algorithm — equivalent to building a stack using only the two available registers in a minimal register machine.

### Regex Mechanics: Backreferences and Extended Patterns

Sed uses Basic Regular Expressions (BRE) by default, in which grouping is `\(` and `\)` and backreferences are `\1` through `\9`. With `-E` (or `--regexp-extended`), ERE syntax uses unescaped `(` and `)` for grouping. Backreferences in the *replacement* string of a substitution refer to the content captured by the corresponding group in the match, which enables a wide class of structural transformations.

Consider the problem of swapping two comma-separated fields:

```sed
s/^\([^,]*\),\([^,]*\)$/\2,\1/
```

The first group `\([^,]*\)` captures everything up to the first comma. The second group captures everything after it to end-of-line. The replacement swaps them. This pattern — capture groups as named slots in a structural decomposition — is the primary mechanism for non-destructive field manipulation in sed.

Sed does not natively support lookaheads or lookbehinds as Perl-compatible regex does. This is a hard architectural constraint of POSIX ERE. The workaround for lookahead-equivalent behavior is to use branching and backreferences to simulate the assertion. For example, to replace a word only when followed by a specific suffix without consuming the suffix:

```sed
s/\(word\)\(suffix\)/replacement\2/
```

This captures the suffix and re-emits it in the replacement, achieving the effect of a lookahead without the POSIX engine needing to support one. The technique works because the replacement string can reference any captured group, allowing you to "protect" context that must not be consumed.

### Script Composition and `-f`

Production sed usage rarely involves one-liners. Complex transformations are built as script files invoked with the `-f` flag, which loads sed commands from a file rather than the command line. Multiple `-f` flags concatenate scripts in order. This is the basis for composable, modular sed pipelines.

A complete, production-grade sed script for normalizing C preprocessor include paths — stripping system path prefixes from `#include` directives while preserving local includes — illustrates the full range of features:

```sed
# normalize-includes.sed
# Normalize #include directives: convert absolute system paths to bare names.
# Usage: sed -E -f normalize-includes.sed input.c

# Skip blank lines and non-include lines
/^[[:space:]]*#[[:space:]]*include[[:space:]]*/!b end

# Handle angle-bracket includes: strip path, keep filename
s|^([[:space:]]*#[[:space:]]*include[[:space:]]*)<[^>]*/([^/>]+)>|\1<\2>|

# Handle quoted includes: strip path, keep filename
s|^([[:space:]]*#[[:space:]]*include[[:space:]]*)\"[^\"]*\/([^/\"]+)\"|\1"\2"|

:end
```

Observe the use of `|` as the delimiter in the substitution command. The `s` command accepts any character as its delimiter — the first character after `s` defines the delimiter. Using `|` when the pattern or replacement contains `/` is not stylistic preference; it is a readability invariant that prevents the visual and syntactic noise of escaping every path separator.

The script also demonstrates the `b end` early-exit idiom: if the line doesn't match a `#include` directive, branch unconditionally to `:end`, which falls off the bottom of the script and prints the line unchanged. This is the sed equivalent of a guard clause.

---

## 3. High-Performance Optimization & Failure Modes

### Performance Characteristics

Sed's performance model is determined by two primary factors: the cost of regex matching per cycle and the total number of cycles executed. For most workloads, sed is I/O-bound before it becomes CPU-bound, but pathological regex patterns can reverse this.

The most common performance failure mode is catastrophic backtracking in BRE/ERE patterns. POSIX mandates leftmost-longest match semantics, and most sed implementations use a backtracking NFA engine. A pattern like `\(a*\)*b` applied to a string of `a`s with no trailing `b` will exhibit O(2^n) backtracking behavior. The fix is to rethink the pattern to avoid nested quantifiers over the same character class. In practice, `[^b]*b` is the correct pattern for "zero or more non-`b` characters followed by `b`," and it runs in linear time.

GNU sed's `-i` (in-place editing) flag creates a temporary file, writes the transformed output to it, and then renames it over the original. This rename is atomic on POSIX systems as long as the source and destination are on the same filesystem. If `/tmp` is a different filesystem from your target file — common in containerized environments where `/tmp` is tmpfs — GNU sed with `--suffix` will write the temp file to the same directory as the target, ensuring the rename remains atomic. BSD sed's `-i ''` syntax differs from GNU sed's `-i ''`; on macOS, the empty string must be a separate argument, while GNU sed accepts `-i` with no argument or `-i''` as one argument. This is a common portability failure that breaks scripts silently.

The hold space accumulation pattern — where you use `H` to collect all lines and then process them on the last line — is an anti-pattern for large files. The hold space grows to the size of the entire file, and the pattern space on the final line contains the complete file content. Any substitution on that content is O(n) in file size with high constant factors. For files beyond a few megabytes, this pattern is better served by `awk`, which provides true array-based multi-line access.

### Failure Modes in Multi-Line Processing

The `N` command has an edge case that terminates the script on some implementations if it is executed on the last line of input (there is no next line to append). GNU sed exits without printing the pattern space in this case, which is a silent data loss failure. The portable fix is to guard `N` with a last-line check:

```sed
$!N
```

The `$!` address means "not the last line," so `N` only fires when there is guaranteed to be another line to read. If you are running in a loop where `N` is inside a `:label`/`b label` construct, you must ensure the last-line guard is in place or the script will silently drop content.

### The `D` Re-entry Trap

The `D` command's re-start behavior is the source of infinite loops in poorly constructed scripts. If a script contains `D` and the conditions that cause `D` to fire remain true after re-entry with the modified pattern space, the script will loop forever. The invariant to enforce is that every execution path through a `D` instruction must reduce the content of the pattern space by at least the first line, and the script's subsequent logic must handle a shorter pattern space without immediately re-triggering `D`.

Consider a script meant to collapse multiple blank lines into a single blank line:

```sed
# Correct blank-line collapsing
/^$/ {
    N
    /^\n$/!P
    D
}
```

This reads: when a blank line is found, append the next line. If the pattern space is not `\n` (i.e., the next line was also blank), do not print (because we're suppressing the extra blank). Then `D` removes the first blank line from the pattern space and re-starts. If the appended line was not blank, `P` prints the first blank line, `D` removes it, and the non-blank line is re-processed normally. This script correctly handles arbitrary runs of blank lines because every `D` invocation is guaranteed to reduce the pattern space by one line, and the loop terminates when the appended line is non-blank.

### Composing Scripts for Production Pipelines

In a build system context — for example, post-processing compiler-generated assembly, normalizing configuration files, or preprocessing C source before custom macro expansion — sed scripts are most reliably composed through `-f` files rather than command-line arguments. This prevents shell quoting errors (single quotes inside the sed script require different quoting disciplines depending on whether the script is in a file or passed via `-e`), enables version control, and allows comments via `#`.

A production pattern for a multi-stage normalization pipeline:

```bash
#!/usr/bin/env bash
set -euo pipefail

INPUT="$1"
OUTPUT="$2"
SCRIPT_DIR="$(dirname "$0")/sed-scripts"

sed -E \
    -f "${SCRIPT_DIR}/01-strip-comments.sed" \
    -f "${SCRIPT_DIR}/02-normalize-whitespace.sed" \
    -f "${SCRIPT_DIR}/03-rewrite-includes.sed" \
    "${INPUT}" > "${OUTPUT}"
```

Each `-f` script is independently testable. The pipeline composes them in a single sed process (all `-f` scripts are concatenated into one program), which means a single pass over the input serves all three transformation stages. This is the key performance invariant: multiple `-f` files do not invoke multiple sed processes. The scripts execute sequentially within a single cycle, so the I/O cost is O(n) in input size regardless of how many transformation stages you compose.

For transformations that genuinely require multiple independent passes — where the output of one pass is structural input to the next — the UNIX pipeline (`sed ... | sed ...`) composes processes through kernel pipe buffers. The cost of this is an additional context switch and pipe I/O per stage, which is typically negligible compared to regex matching but becomes measurable at gigabyte scale.

The authoritative diagnostic tool for validating sed script behavior against expected output is `diff`. The correct development workflow for a production sed script is to build a corpus of input/output pairs, run the script against each input, and assert exact byte-level equality between the actual and expected outputs. A sed script that is "mostly right" is a liability in a build pipeline. The correctness invariant must be absolute.
