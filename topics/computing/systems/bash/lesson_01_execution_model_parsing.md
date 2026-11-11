# Lesson 1: Execution Model, Parsing, Command Resolution

## 1. First-Principles Intuition & Invariants

The Bash shell operates as a **read-eval-print loop** (REPL) mediating between human intention expressed as text and the kernel's process execution machinery. At its foundation, Bash is a compiler and runtime for a dynamically-typed, interpreted language whose execution model revolves around transforming character streams into process creation system calls. Every line of shell input traverses a deterministic pipeline: lexical scanning fragments the input stream into tokens, syntactic parsing builds an abstract syntax tree representing command structure, expansion phases transform metacharacters and variables into concrete argument vectors, and finally the execution engine dispatches either built-in functions within the shell's own address space or forks child processes to execute external binaries.

Understanding this execution model requires recognizing that the shell maintains **dual operational modes**: interactive sessions where it presents a prompt and awaits user input, and non-interactive script execution where it processes files as batch programs. These modes share the same parsing and execution core but differ in signal handling, job control semantics, and error propagation behavior. The shell's design reflects Unix philosophy: it treats everything as either a simple command (a single executable with arguments), a pipeline (commands connected via interprocess communication channels), or a compound command (control structures like loops and conditionals). This uniform abstraction allows the shell to compose complex behaviors from primitive operations while maintaining clean separation between the shell interpreter itself and the programs it orchestrates.

The critical invariant governing shell execution is the **argument vector contract**: regardless of how complex the input syntax becomes—with nested quotes, variable expansions, command substitutions, and glob patterns—the shell's ultimate responsibility is to produce an array of null-terminated C strings (`char *argv[]`) that the kernel's `execve` system call can consume. This contract enforces strict boundaries: the shell performs all textual transformations and expansions before process creation, meaning the invoked program receives a fully materialized argument list with no awareness of the shell's parsing or expansion logic. This separation of concerns enables the shell to implement sophisticated text processing while maintaining compatibility with programs written in any language, provided they adhere to the standard argument vector convention established by the C runtime.

Bash's execution model distinguishes between **built-in commands** executed within the shell's own process context and **external commands** that require forking a child process. Built-ins like `cd`, `export`, and `read` must execute in the shell's address space because they modify the shell's internal state—current working directory, environment variables, or input file descriptors—which would be invisible to a child process due to Unix's copy-on-write process isolation. External commands, conversely, execute in separate address spaces, inheriting a snapshot of the parent shell's environment and file descriptor table but unable to affect the shell's state except through explicit interprocess communication channels like exit codes, pipes, or shared files. This architectural decision has profound performance implications: built-ins execute with function call overhead (nanoseconds), while external commands incur the full cost of process creation, program loading, and dynamic linking (milliseconds).

The shell's parsing phase implements a **context-sensitive grammar** where the interpretation of characters depends on quoting state and position within the command structure. A dollar sign inside double quotes triggers variable expansion, but inside single quotes it represents a literal character. A newline terminates a simple command unless preceded by a backslash or occurring within an unclosed quote. This context-sensitivity means the shell cannot use a simple regular expression tokenizer; instead, it implements a stateful lexer that tracks quoting depth, escape sequences, and metacharacter positions. The parser must handle operator precedence for logical operators (`&&`, `||`), pipeline construction (`|`), and command sequencing (`;`, `&`), while also respecting reserved words (`if`, `while`, `function`) that alter parse tree structure. This grammatical complexity reflects the shell's dual nature as both an interactive command interpreter and a complete programming language.

## 2. Core Architecture & Mechanics

The shell's execution pipeline begins with **lexical analysis**, where the input character stream is segmented into tokens according to the shell's metacharacter set. The lexer recognizes operators (`|`, `&`, `;`, `&&`, `||`, `(`, `)`, `<`, `>`, `>>`, `<<`), reserved words that introduce control structures, and word tokens that will become command names and arguments. Whitespace characters (space, tab, newline) serve as token delimiters in unquoted contexts, but the lexer must track quoting state to determine whether a space is a delimiter or part of a word. The fundamental tokenization rule states that any character can be quoted to suppress its special meaning: a backslash quotes the next character, single quotes preserve all characters literally until the closing quote, and double quotes preserve most characters but allow variable expansion (`$var`), command substitution (`$(cmd)`), and arithmetic expansion (`$((expr))`).

```
Input:    echo "Hello $USER" | grep -i 'world'
Tokens:   [echo] ["Hello $USER"] [|] [grep] [-i] ['world']
Quoting:  [none] [double      ] [op] [none] [none] [single ]
```

After tokenization, the **syntax parser** constructs an abstract syntax tree (AST) representing the command's structure. Simple commands form leaf nodes containing the command name and argument list. Pipelines connect multiple simple commands with interprocess communication edges. Logical operators create decision nodes that conditionally execute right subtrees based on left subtree exit status. Compound commands introduce control flow: `if` statements build conditional branches, `while` loops create cyclic execution paths, and subshells (`( )`) or command groups (`{ }`) establish scope boundaries. The parser enforces operator precedence: pipelines bind tighter than logical operators, which bind tighter than command separators. This precedence hierarchy allows complex commands like `cmd1 | cmd2 && cmd3 || cmd4 ; cmd5` to be unambiguously parsed into a tree structure that dictates execution order.

The **expansion phase** transforms abstract syntax tree nodes by applying eight sequential expansion operations in a rigidly defined order. First, brace expansion generates combinatorial argument sets from patterns like `{a,b,c}` or `{1..10}`. Second, tilde expansion converts `~` to the user's home directory path. Third, parameter expansion resolves variable references (`$VAR`, `${VAR}`) by consulting the shell's variable hash table. Fourth, command substitution spawns subshells to execute nested commands and captures their standard output as expansion text. Fifth, arithmetic expansion evaluates integer expressions within `$(( ))` delimiters. Sixth, word splitting divides expansion results into separate arguments using the `IFS` (Internal Field Separator) variable as delimiter specification. Seventh, pathname expansion (globbing) matches patterns like `*.txt` against the filesystem directory tree. Finally, quote removal strips the syntactic quotes that controlled earlier expansion phases, yielding the final argument vector.

The ordering of these expansions creates subtle semantic dependencies. Word splitting occurs **after** parameter expansion, meaning unquoted variables containing spaces will be split into multiple arguments, while quoted variables preserve whitespace. Pathname expansion happens after word splitting, so if a variable expands to `*.txt`, the asterisk becomes a glob pattern only if the variable was unquoted. This expansion discipline enforces the principle that **quoting controls splitting and globbing**: double quotes suppress word splitting and pathname expansion while preserving variable expansion, single quotes suppress all expansions including variable substitution, and backslash quotes individual characters. Understanding this ordering is essential for avoiding argument injection vulnerabilities where untrusted data splits unexpectedly or glob patterns match unintended files.

```
# Expansion order demonstration
VAR="*.txt"
echo $VAR        # Splits on space (none here), globs *.txt → file list
echo "$VAR"      # No split, no glob → literal string "*.txt"
echo '$VAR'      # No expansion at all → literal string "$VAR"
```

Once expansions complete, the shell enters the **execution phase** where it must resolve how to invoke the command. The command resolution algorithm proceeds through a strict priority hierarchy. First, the shell checks if the command name matches an **alias**, a textual macro that rewrites the command before further processing. If no alias matches, the shell searches its **function definition table** for a user-defined shell function. If no function exists, the shell consults its **built-in command dispatch table** to determine if the name corresponds to a built-in like `cd`, `echo`, or `test`. Only after exhausting these internal namespace checks does the shell perform **PATH search**, iterating through directories specified in the `$PATH` environment variable until it locates an executable file matching the command name. This resolution order means shell functions can shadow built-ins, and built-ins can shadow external commands, providing a layered namespace where inner scopes override outer ones.

```
Command Resolution Order:
1. Aliases           (textual macro substitution)
2. Shell Functions   (execute in current shell context)
3. Built-in Commands (execute in current shell process)
4. PATH Search       (fork + exec external binary)
5. Command Not Found (exit status 127)
```

Built-in command execution follows a lightweight dispatch model. The shell maintains a static dispatch table mapping built-in names to function pointers within the shell's binary. When executing a built-in, the shell invokes the corresponding function directly, passing the expanded argument vector. Because execution occurs in the shell's process context, built-ins can modify shell state: `cd` updates the current working directory via the `chdir` system call, `export` modifies the environment variable hash table, and `set` alters shell option flags. Built-ins can access and modify shell variables, file descriptors, and signal dispositions. The return value from a built-in function becomes the command's exit status, accessible via the `$?` special parameter. This in-process execution model makes built-ins orders of magnitude faster than external commands, a crucial optimization for commands invoked frequently in loops.

External command execution requires process creation machinery. The shell invokes the `fork` system call to create a child process that initially shares the parent's memory via copy-on-write pages. The child process inherits the parent's environment variables (exported variables only), file descriptor table (with descriptors marked close-on-exec being closed), signal dispositions, resource limits, and process group membership. The child then invokes `execve` with three critical arguments: the absolute path to the executable file (resolved via PATH search), the null-terminated argument vector produced by expansion, and the environment variable array. The `execve` system call replaces the child's address space with the new program image, transferring control to the dynamic linker (`ld.so`) which resolves shared library dependencies before finally jumping to the program's entry point. The parent shell blocks in a `waitpid` call until the child terminates, capturing its exit status to determine whether subsequent pipeline stages or logical operators should execute.

```mermaid
graph TD
    A[Input: echo $VAR | grep foo] --> B[Lexer: Tokenize]
    B --> C[Parser: Build AST]
    C --> D[Expansion: Resolve $VAR]
    D --> E{Command Type?}
    E -->|Built-in| F[Direct Function Call]
    E -->|External| G[fork + PATH Search]
    G --> H[execve]
    F --> I[Capture Exit Status]
    H --> I
    I --> J[Update $? Variable]
```

Subshell creation represents a distinct execution context. When the shell encounters parentheses `( cmd )`, it forks a child process but does not execute an external program. Instead, the child process continues running the shell interpreter, executing the command within the parentheses in this isolated context. The subshell inherits the parent's variables and functions but operates in a separate process with its own process ID, file descriptor table, and working directory. Any state modifications within the subshell—variable assignments, directory changes, function definitions—vanish when the subshell exits because they occurred in a separate address space destroyed by process termination. Subshells serve two critical purposes: they provide isolated execution environments for commands that might otherwise affect shell state, and they enable process substitution constructs like `<(cmd)` which present command output as if it were a file.

Pipelines introduce **interprocess communication** through kernel pipe objects. When constructing a pipeline `cmd1 | cmd2 | cmd3`, the shell creates anonymous pipes using the `pipe` system call, which returns paired file descriptors: a write end and a read end. The shell forks child processes for each pipeline stage, carefully duplicating pipe descriptors so each command's standard output connects to the next command's standard input. The first command inherits the pipeline's original stdin, the last command inherits the pipeline's original stdout, and intermediate commands have both stdin and stdout connected to pipes. The shell closes all unused pipe descriptors to prevent resource leaks and ensure proper end-of-file signaling when writers terminate. All pipeline commands execute concurrently as separate processes, with the kernel's pipe buffer (typically 64 KB) mediating data flow and providing flow control when buffers fill.

```
Pipeline: cmd1 | cmd2 | cmd3

Process Structure:
  Shell (parent)
    ├─ cmd1 (pid 1001): stdout → pipe1_write
    ├─ cmd2 (pid 1002): stdin ← pipe1_read, stdout → pipe2_write
    └─ cmd3 (pid 1003): stdin ← pipe2_read

Pipe Descriptors:
  pipe1: [read_fd=3, write_fd=4]
  pipe2: [read_fd=5, write_fd=6]

File Descriptor Wiring:
  cmd1: fd 0=terminal, fd 1=pipe1[w], fd 2=terminal
  cmd2: fd 0=pipe1[r], fd 1=pipe2[w], fd 2=terminal
  cmd3: fd 0=pipe2[r], fd 1=terminal, fd 2=terminal
```

## 3. High-Performance Optimization & Failure Modes

Command execution performance exhibits extreme bimodality depending on whether built-in or external command dispatch occurs. Built-in commands execute in tens of microseconds with minimal overhead beyond the function call and argument processing. External commands incur three major cost centers: process creation overhead (fork copies page tables and process control blocks), dynamic linking overhead (resolving shared library symbols), and program initialization overhead (running C runtime startup code). On modern Linux systems, these costs combine to produce a minimum external command latency of approximately 1-2 milliseconds even for trivial programs like `/bin/true`. This thousandfold performance gap makes optimizing loops to use built-ins instead of external commands a critical performance discipline.

```bash
# Anti-pattern: External command in tight loop (slow)
count=0
while [ $count -lt 10000 ]; do
    count=$(expr $count + 1)  # Forks expr process 10,000 times
done

# Optimized: Built-in arithmetic (fast)
count=0
while [ $count -lt 10000 ]; do
    ((count++))  # In-process arithmetic expansion
done
```

The PATH search mechanism can become a hidden performance bottleneck when paths contain many directories or network-mounted filesystems. Each PATH component requires a `stat` system call to check for executable file existence, and on network filesystems these stat operations can block for hundreds of milliseconds. The shell does not cache PATH search results across invocations, meaning repeatedly executing the same external command in a loop will perform the full PATH search every time. Two optimization strategies mitigate this cost: using absolute paths when the executable location is known avoids PATH search entirely, and restructuring scripts to minimize external command invocations reduces the number of searches performed. The `hash` built-in command maintains a lookup table of previously resolved command paths, but this cache is scoped to the current shell session and does not persist across script invocations.

Quoting errors represent the most prevalent class of shell programming bugs, manifesting as argument injection vulnerabilities or incorrect word splitting behavior. When a variable containing whitespace or glob characters is used unquoted, the shell splits it into multiple arguments and interprets wildcard characters as filesystem patterns. This behavior creates security vulnerabilities when variables contain untrusted data: a variable holding `file1.txt file2.txt` splits into two arguments where one was intended, and a variable containing `*.txt` unexpectedly expands to match all text files in the current directory. The defensive programming discipline requires **always quoting variable expansions** unless word splitting is explicitly desired. Double quotes preserve the variable's value as a single argument while allowing nested expansions, preventing both splitting and globbing vulnerabilities.

```bash
# Vulnerable: Unquoted variable allows injection
file="important.txt; rm -rf /"
cat $file  # Executes: cat important.txt ; rm -rf /

# Safe: Quoted variable prevents splitting
file="important.txt; rm -rf /"
cat "$file"  # Executes: cat "important.txt; rm -rf /"
```

Subshell proliferation degrades performance because each subshell creation incurs the cost of process forking. Command substitution `$(cmd)` and process substitution `<(cmd)` both create subshells, as do explicit subshell groups `( cmd )` and background jobs `cmd &`. When nested deeply or used in loops, subshells can create thousands of short-lived processes, overwhelming the process table and spending more time in process lifecycle management than useful work. Modern Bash includes **process substitution optimization** that reuses pipe file descriptors instead of creating named FIFOs, but the fundamental subshell creation cost remains. Refactoring to avoid command substitution in loops—by using shell built-ins, here-documents, or process substitution with `while read` loops—eliminates this overhead.

Pipeline failure semantics require careful consideration of the `pipefail` option. By default, the shell reports only the exit status of the last command in a pipeline, meaning early pipeline stages can fail silently while the overall pipeline reports success if the final command succeeds. This behavior creates reliability hazards in data processing pipelines where early stage failures corrupt data but go undetected. Setting `set -o pipefail` changes pipeline exit status to reflect the rightmost command with a non-zero exit status, but this can cause scripts to fail unexpectedly if any pipeline component emits non-zero status as a normal condition (like `grep` returning 1 when no matches are found). Robust pipeline error handling requires combining `pipefail` with explicit status checking via the `${PIPESTATUS[@]}` array, which records individual exit statuses for all pipeline components.

```bash
# Without pipefail: Failure masked
false | true
echo $?  # Prints 0 (last command succeeded)

# With pipefail: Failure exposed
set -o pipefail
false | true
echo $?  # Prints 1 (first command failed)

# Fine-grained status inspection
set -o pipefail
command1 | command2 | command3
statuses=("${PIPESTATUS[@]}")
echo "Stage 1: ${statuses[0]}, Stage 2: ${statuses[1]}, Stage 3: ${statuses[2]}"
```

File descriptor leakage occurs when scripts create file descriptors but fail to close them, exhausting the per-process descriptor limit (typically 1024 on Linux). Pipelines, command substitutions, and process substitutions all create file descriptors that must be explicitly closed or rely on close-on-exec flags. The shell automatically closes pipe descriptors in child processes, but scripts that manually open files using `exec` must remember to close them with `exec {fd}>&-` or risk accumulating leaked descriptors across loop iterations. File descriptor exhaustion manifests as cryptic "Too many open files" errors from unrelated commands, making the leak's source difficult to diagnose. The `lsof` and `/proc/$$/fd` mechanisms enable runtime descriptor auditing to detect leaks.

Shell parsing ambiguities arise from the context-sensitive grammar, particularly around command substitution nesting and quote escaping. When nesting command substitutions `$(cmd1 $(cmd2))`, the inner substitution must be parsed to determine where the outer substitution ends. Historical `backtick` syntax `` `cmd` `` required backslash escaping when nested, creating complex escape sequences like `` `echo \`date\`` ``, but modern `$()` syntax supports arbitrary nesting without escaping. Quote handling inside command substitutions follows independent quoting rules: quotes within `$(cmd)` protect the substituted command's arguments, not the outer shell's arguments. This distinction requires careful reasoning about which parsing context applies to each syntactic element.

The shell's error handling model defaults to **continue-on-error**: a failed command does not terminate the script unless the `set -e` (errexit) option is enabled. This permissive default reflects the shell's interactive heritage where users expect to continue working after command failures, but it creates reliability hazards in scripts where undetected errors compound. The `set -e` option terminates the script if any command returns non-zero status, but it interacts subtly with conditionals (commands in `if` tests do not trigger errexit), subshells (errexit does not propagate to subshells unless inherited), and pipelines (only the last command triggers errexit unless `pipefail` is set). Robust error handling requires combining `set -euo pipefail` to enable errexit, undefined variable detection, and pipeline failure propagation, while understanding that errexit does not apply to commands whose failure is explicitly tested.

Command resolution security vulnerabilities arise when untrusted data influences PATH contents or command names. If an attacker can prepend a directory they control to the PATH environment variable, they can place malicious executables with names matching standard commands, causing the shell to execute attacker-controlled code when invoking what appear to be benign commands like `ls` or `cat`. This **PATH injection** attack vector requires either controlling PATH directly or exploiting relative paths in setuid programs. The mitigation strategy uses absolute paths for security-sensitive commands (`/bin/ls` instead of `ls`) or carefully sanitizes PATH to include only trusted directories with appropriate permissions. Scripts running with elevated privileges must never trust inherited PATH values and should explicitly set PATH to a minimal trusted set.

Glob expansion denial-of-service occurs when pathname patterns match an unexpectedly large number of files, causing the argument vector to exceed kernel limits. The kernel enforces a maximum argument vector size (typically 2 MB on Linux, controlled by `ARG_MAX`), beyond which `execve` fails with `E2BIG`. A pattern like `*` in a directory containing millions of files will attempt to pass all filenames as arguments, potentially exceeding this limit and causing command failure. Additionally, glob expansion performs a full directory traversal, which on slow filesystems or with deeply nested hierarchies can block the shell for seconds or minutes. Defensive glob usage requires either constraining pattern scope (`*.txt` instead of `*`), using `find` with `-exec` for scalable file processing, or disabling globbing with `set -f` when processing untrusted patterns.
