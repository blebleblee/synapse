# Lesson 4: Scripting Patterns, Parameter Expansion, Builtins

## 1. First-Principles Intuition & Invariants

Bash scripting occupies a unique position in the Unix ecosystem, functioning simultaneously as a command interpreter and a programming language. Unlike compiled languages where types and scoping are enforced at compile time, Bash operates as a dynamic, untyped command interpreter where the fundamental unit of execution is the word—a sequence of characters subject to a series of expansions and transformations before being passed to commands. This execution model explains why operations as simple as variable assignment, array indexing, or conditional testing can behave unexpectedly without proper quoting and parameter expansion syntax.

The Bash interpreter follows a predictable execution pipeline for every line of script: tokenization, expansion (brace, tilde, parameter, command substitution, arithmetic, word splitting, pathname globbing), quote removal, and finally execution. This pipeline is not merely a convenience layer—it defines how the shell interprets your code. Variables in this model are not first-class objects with type information; they are environment strings stored in a process's symbol table, accessed through parameter expansion syntax. Arrays, introduced in Bash 2.0 and extended in subsequent versions, function as flat associative maps where indices are strings, though the default array syntax treats them as zero-indexed sequences.

Scoping in Bash derives from Unix's process model and the inheritance of environment variables across parent-child processes. When you export a variable, you place it in the environment block passed to all child processes spawned by the current shell. Local variables exist only within the current shell's execution context and are not inherited unless explicitly passed. Function scope in Bash is dynamic, not lexical—a variable set inside a function, unless declared with the `local` keyword, modifies the variable in the caller's scope. This represents a fundamental departure from lexical scoping in compiled languages and reflects the shell's origin as a command glue layer rather than a general-purpose programming language.

Conditionals in Bash present one of the most frequently misunderstood design choices. The shell provides two syntaxes: the POSIX-compliant `[ ]` (test command) and the Bash-specific `[[ ]]` (conditional expression). The distinction is not syntactic sugar; `[ ]` is a true command that parses its arguments like any other utility, while `[[ ]]` is a keyword with special parsing rules. This difference has profound implications for word splitting, pathname expansion, and operator precedence. Understanding when to use each form is not a matter of style but of correctness and security.

Builtins in Bash represent commands that the shell executes directly without spawning a subprocess. This differs fundamentally from external utilities, which require a fork-exec cycle. For performance-critical scripts, preferring builtins over external commands can eliminate thousands of context switches. Builtins also represent a semantic trap: they operate within the shell's own address space, and their behavior is not guaranteed to match external commands with the same name. The `echo` builtin, for instance, behaves differently across shells, while `/bin/echo` offers more predictable behavior on Unix systems.

## 2. Core Architecture & Mechanics

### Parameter Expansion and Variable Substitution

Bash's parameter expansion follows a formal grammar defined in the POSIX shell specification and extended by Bash. Parameter expansion is triggered by the `$` character, followed by a parameter name, number, or special symbol. The fundamental form is `${parameter}`, which retrieves the value of `parameter`. Without the braces, `$parameter` works equally well in most contexts, but the braced form is necessary when the parameter name is followed by characters that would otherwise be parsed as part of the name.

Consider the distinction between `$var10` (which attempts to retrieve the variable `var10`, not the tenth element of an array named `var`) and `${var[10]}` (which explicitly indexes array `var` at position 10). This ambiguity arises because Bash's tokenization does not distinguish between variable names and array access syntax at the lexical level; the parser must look ahead to determine where the parameter name ends.

Parameter expansion includes several categories of transformations, each with distinct semantics:

**Default values and coercion.** The form `${parameter:-default}` expands to the value of `parameter` if it is set and non-null; otherwise it expands to `default`. The distinction between set-but-empty and unset is critical. If `parameter` is set to an empty string, `${parameter:-default}` returns `default`, but `${parameter-default}` returns the empty string. This distinction matters in scripts that distinguish between "not configured" (unset) and "configured to be empty" (set to empty string). Similarly, `${parameter:=default}` assigns `default` to `parameter` if it is unset or null, then expands to the assigned value. This supports lazy initialization patterns where a variable should adopt a default value on first access.

**Parameter substitution and removal.** The forms `${parameter#pattern}` and `${parameter%pattern}` remove the shortest match of `pattern` from the beginning and end of `parameter` respectively. The doubled forms `${parameter##pattern}` and `${parameter%%pattern}` remove the longest match. These operations are string-based and respect Bash's glob syntax, not regular expressions. For example, `${filename##*.}` removes all characters up to and including the last dot, effectively extracting the file extension. The distinction between `#` (prefix removal) and `%` (suffix removal) aligns mnemonically to their position on a QWERTY keyboard: `#` appears before `%`, so `#` removes from the front.

**String replacement.** The form `${parameter/pattern/replacement}` replaces the first occurrence of `pattern` with `replacement`. The doubled form `${parameter//pattern/replacement}` replaces all occurrences. If `pattern` begins with `#`, the replacement applies only to the beginning of the string; if it begins with `%`, only the end. These operations are case-sensitive and use glob syntax, not regex. The `replacement` string itself undergoes parameter expansion, allowing dynamic substitution. For instance, `${path//\/bin\//bin_}` replaces every occurrence of `/bin/` with `bin_`, where the backslashes escape the forward slashes because `/` carries special meaning in the pattern syntax.

**Substring extraction.** The form `${parameter:offset}` extracts `parameter` starting at `offset` characters from the beginning. The form `${parameter:offset:length}` extracts exactly `length` characters starting at `offset`. Negative offsets count from the end of the string, but require a space or parentheses to avoid ambiguity with the `${parameter:-default}` syntax: `${parameter: -5}` extracts the last five characters. If `offset` is negative and `length` is omitted, extraction proceeds from the offset position to the end of the string.

**Case modification.** The forms `${parameter^}`, `${parameter^^}`, `${parameter,}`, and `${parameter,,}` convert the first character to uppercase, all characters to uppercase, the first character to lowercase, and all characters to lowercase respectively. These operations are locale-aware and respect the current `LC_CTYPE` setting. The caret (`^`) and comma (`,`) operators were introduced in Bash 4.0 and provide a native alternative to the external `tr` command for case conversion.

**Indirection.** The form `${!parameter}` performs indirect expansion: if `parameter` contains the name of another variable, the expansion yields the value of that named variable. For example, if `var=foo` and `foo=bar`, then `${!var}` expands to `bar`. This mechanism enables dynamic variable names and is frequently used in scripts that construct variable names programmatically. Indirect expansion also applies to array indices: `${!array[@]}` expands to all indices of the array `array`, not its values.

### Arrays and Associative Arrays

Bash supports two types of arrays: indexed arrays (introduced in Bash 2.0) and associative arrays (introduced in Bash 4.0). Indexed arrays use integer indices starting at zero, while associative arrays use arbitrary strings as keys. Both types are implemented as hash tables internally, so lookup time is constant on average, but indexed arrays benefit from syntactic conveniences that associative arrays do not.

An indexed array is declared explicitly with `declare -a array` or implicitly by assignment:

```bash
array=(one two three)
array[0]=one
array[1]=two
array[2]=three
```

Array elements are accessed with `${array[index]}`. The special indices `@` and `*` expand to all elements of the array. The distinction between `${array[@]}` and `${array[*]}` mirrors the distinction between `"$@"` and `"$*"` for positional parameters: when quoted, `"${array[@]}"` expands to separate words, while `"${array[*]}"` expands to a single word with elements joined by the first character of `IFS`.

Associative arrays must be declared explicitly:

```bash
declare -A assoc
assoc[key1]=value1
assoc[key2]=value2
```

Array length is obtained with `${#array[@]}`, which counts the number of elements. Individual element lengths are retrieved with `${#array[index]}`, which counts characters in the element at `index`. Array slicing follows the substring extraction syntax: `${array[@]:offset:length}` extracts `length` elements starting at `offset`.

A critical detail often overlooked is that arrays are not first-class objects in Bash. They cannot be returned from functions, passed as arguments, or assigned in a single operation. The only way to "return" an array from a function is to echo its elements and capture them in the caller, or to use a global variable. This limitation stems from Bash's design as a command interpreter rather than a general-purpose programming language.

### Conditional Expressions and Test Constructs

Bash provides two syntaxes for conditional expressions: `[ expression ]` and `[[ expression ]]`. The `[ ]` syntax is POSIX-compliant and implemented as a builtin that behaves like the external `/usr/bin/[` command. The `[[ ]]` syntax is a Bash keyword with special parsing rules.

The distinction is semantically significant. Because `[ ]` is a command, its arguments undergo all the standard shell expansions, including word splitting and pathname expansion. This means that unquoted variables inside `[ ]` can cause syntax errors if they expand to multiple words or contain glob characters. The `[[ ]]` syntax, by contrast, does not perform word splitting or pathname expansion on its arguments, making it safer for testing variables that may contain spaces or special characters.

Compare these two conditionals:

```bash
file="my file.txt"
[ -f $file ]      # Error: -f is tested against "my" and "file.txt" separately
[[ -f $file ]]    # Correct: -f is tested against "my file.txt"
```

The `[ ]` syntax requires explicit quoting:

```bash
[ -f "$file" ]    # Correct: quotes prevent word splitting
```

The `[[ ]]` syntax also supports additional operators not available in `[ ]`:

- `=~` for regex matching: `[[ $string =~ ^[0-9]+$ ]]`
- `<` and `>` for lexicographic string comparison without escaping
- `&&` and `||` for logical AND and OR within the expression

The `=~` operator deserves special attention. It performs extended regular expression matching, not glob matching. The pattern on the right side should not be quoted if it contains regex metacharacters, because quoting causes the pattern to be treated as a literal string. Captured groups from the match are stored in the `BASH_REMATCH` array, with `${BASH_REMATCH[0]}` containing the entire match and subsequent indices containing captured subgroups.

Numeric comparisons in Bash use different operators inside `[ ]` and `(( ))`:

```bash
[ "$a" -eq "$b" ]    # Integer equality in [ ]
[[ $a -eq $b ]]      # Integer equality in [[ ]]
(( a == b ))         # Arithmetic comparison (C-style)
```

The `(( ))` syntax evaluates its contents as an arithmetic expression and returns success (exit status 0) if the result is non-zero, failure otherwise. This inverts the typical Unix convention where zero indicates success, but aligns with C-style boolean semantics where non-zero is true. Inside `(( ))`, variables do not require the `$` prefix, and all standard C arithmetic operators are available.

### Builtins and Command Execution

Builtins are commands executed directly by the shell without spawning a subprocess. This distinction has performance implications: invoking an external command requires a `fork()` system call to create a new process and an `exec()` call to replace that process with the command binary. Builtins bypass this overhead entirely.

The most commonly used builtins include:

- `cd`: Change the current directory. This must be a builtin because it modifies the state of the shell process itself. An external command could not change the working directory of its parent process due to Unix's process isolation model.
- `echo`: Print arguments to standard output. The builtin version is faster than `/bin/echo`, but its behavior varies across shells. Some versions interpret backslash escape sequences by default; others require the `-e` flag.
- `read`: Read a line from standard input into one or more variables. The `-r` flag disables backslash escaping, which is almost always desirable for reading raw input.
- `set`: Set shell options and positional parameters. The `set -e` option causes the shell to exit immediately if any command returns a non-zero exit status, while `set -u` treats unset variables as errors.
- `export`: Mark variables for export to the environment of child processes. Only exported variables are visible to external commands invoked by the shell.
- `local`: Declare a variable with function scope. Without this keyword, all variables in functions have global scope.

The `printf` builtin deserves special mention. Unlike `echo`, which has inconsistent behavior across shells, `printf` follows the POSIX specification and provides format string capabilities similar to C's `printf()` function:

```bash
printf "%s: %d\n" "Count" 42
printf "%10s %5d\n" "Item" 123  # Fixed-width fields
printf "%.2f\n" 3.14159          # Floating-point precision
```

The `printf` builtin is also more portable than `echo` for scripts that must run on multiple Unix variants.

Another critical builtin is `source` (or its synonym `.`), which reads and executes commands from a file in the current shell environment. This differs fundamentally from executing a script as a separate process: `source` does not create a new process, so variable assignments and function definitions in the sourced file affect the current shell. This mechanism is used to load configuration files and shared libraries of shell functions.

The `command` builtin forces the shell to execute a command even if a function with the same name exists. This is useful when a function wraps a builtin or external command but needs to invoke the original:

```bash
cd() {
    echo "Changing to $1"
    command cd "$1"  # Invoke the real cd builtin
}
```

Without `command`, the function would recurse infinitely.

### Quoting and Word Splitting

Quoting in Bash serves two purposes: preserving literal values and controlling word splitting. The shell recognizes three quoting mechanisms: single quotes, double quotes, and backslash escaping.

Single quotes preserve the literal value of all characters within the quotes. No expansions occur inside single quotes, not even backslash escaping. The only character that cannot appear inside single quotes is a single quote itself, because there is no escape mechanism. To include a literal single quote in a single-quoted string, you must end the string, add an escaped single quote, and start a new string:

```bash
echo 'It'"'"'s working'  # Prints: It's working
```

Double quotes preserve the literal value of most characters but allow parameter expansion, command substitution, and arithmetic expansion. The backslash retains its special meaning only when followed by `$`, backtick, double quote, backslash, or newline. This means that within double quotes, `\n` is not a newline but the two literal characters backslash and `n`, unless you are using `$'...'` quoting (see below).

Backslash escaping removes the special meaning of the next character. Outside quotes, a backslash followed by a newline is treated as line continuation, allowing long commands to span multiple lines.

Word splitting occurs after parameter expansion, command substitution, and arithmetic expansion. The shell splits the expanded text into words using the characters in the `IFS` (Internal Field Separator) variable as delimiters. By default, `IFS` contains space, tab, and newline. This means that if a variable expands to a string containing spaces, the shell treats each space-separated component as a separate word unless the expansion is quoted:

```bash
files="a.txt b.txt c.txt"
rm $files        # Passes three arguments: a.txt, b.txt, c.txt
rm "$files"      # Passes one argument: "a.txt b.txt c.txt"
```

Pathname expansion (globbing) occurs after word splitting. Unquoted words containing the characters `*`, `?`, or `[` are treated as patterns and expanded to match filenames. This expansion is controlled by several shell options, including `nullglob` (which causes patterns that match no files to expand to nothing rather than themselves) and `dotglob` (which causes `*` to match files beginning with a dot).

The `$'...'` quoting syntax, introduced in Bash 2.0, interprets ANSI C escape sequences such as `\n` (newline), `\t` (tab), and `\x##` (hexadecimal character code). This syntax is useful for embedding control characters in strings:

```bash
echo $'Line 1\nLine 2'  # Prints two lines
echo $'Column\tAligned'  # Prints tab-separated columns
```

### Process Substitution and Command Substitution

Command substitution replaces a command with its output. Bash supports two syntaxes: backticks and `$(...)`. The `$(...)` syntax is preferred because it nests properly and is easier to read:

```bash
current_date=$(date +%Y-%m-%d)
files=$(ls -1)
```

Command substitution captures standard output only, not standard error. To capture both, redirect stderr to stdout:

```bash
output=$(command 2>&1)
```

The output of command substitution undergoes word splitting and pathname expansion unless quoted. This is a frequent source of bugs:

```bash
files=$(find . -name "*.txt")
for f in $files; do       # Breaks if filenames contain spaces
    echo "$f"
done

# Correct approach:
while IFS= read -r f; do
    echo "$f"
done < <(find . -name "*.txt")
```

Process substitution is a Bash extension that creates a temporary named pipe or file descriptor for the output of a command, allowing it to be used where a filename is expected. The syntax is `<(command)` for input or `>(command)` for output:

```bash
diff <(sort file1) <(sort file2)  # Compare sorted versions without temp files
command > >(tee stdout.log) 2> >(tee stderr.log >&2)  # Tee stdout and stderr separately
```

Process substitution is implemented using named pipes on systems that support them, and `/dev/fd` file descriptors on systems that do not. The substitution expands to a filename (e.g., `/dev/fd/63`) that can be passed to commands expecting a file argument.

### Exit Status and Error Handling

Every command in Unix returns an exit status, an integer from 0 to 255. By convention, zero indicates success, and non-zero indicates failure. The exit status of the most recently executed command is available in the special parameter `$?`.

Pipelines present a complication: by default, the exit status of a pipeline is the exit status of the last command. This means that errors in earlier stages of the pipeline are silently ignored. The `pipefail` option changes this behavior to return the exit status of the rightmost command to exit with a non-zero status:

```bash
set -o pipefail
cat nonexistent_file | grep pattern | sort
echo $?  # Returns the exit status of cat, not sort
```

The `set -e` option causes the shell to exit immediately if any command returns a non-zero exit status. This option has several subtleties. Commands whose failure is tested in a conditional (e.g., `if command; then ...`) do not trigger an exit. Commands in a pipeline (except the last) do not trigger an exit unless `pipefail` is set. Commands invoked in a subshell do not trigger an exit in the parent shell.

Because `set -e` behavior is complex and often surprising, many experienced shell scripters prefer explicit error checking:

```bash
command || { echo "Command failed"; exit 1; }
```

The `trap` builtin registers commands to execute when the shell receives a signal or exits. This is useful for cleanup operations:

```bash
cleanup() {
    rm -f "$temp_file"
}
trap cleanup EXIT

temp_file=$(mktemp)
# ... use temp_file ...
# cleanup() is called automatically on exit
```

The `EXIT` pseudo-signal is triggered when the shell exits for any reason, including normal termination, errors (if `set -e` is enabled), or signals.

### Functions and Scope

Functions in Bash are defined with the syntax:

```bash
function_name() {
    # body
}
```

or equivalently:

```bash
function function_name {
    # body
}
```

The second syntax is a Bash extension; the first is POSIX-compliant.

Functions receive arguments through positional parameters `$1`, `$2`, etc., just like scripts. The special parameter `$@` expands to all arguments, and `$#` contains the argument count. Unlike scripts, functions execute in the current shell's process, so they can modify variables in the caller's scope unless those variables are declared `local`.

The `local` keyword declares a variable with function scope:

```bash
my_function() {
    local temp="temporary value"
    echo "$temp"
}
my_function
echo "$temp"  # Empty: temp is local to my_function
```

Without `local`, the variable would persist after the function returns and affect the caller's environment.

Functions cannot return arrays or complex data structures. The only return value is an integer exit status, set with the `return` command. To return a string or array, the function must either echo the value (which the caller captures with command substitution) or assign to a global variable.

Recursive functions are supported but limited by the shell's call stack depth. Deep recursion in Bash is impractical due to the overhead of function calls compared to compiled languages.

### Advanced Scripting Patterns

**Parsing command-line options.** The `getopts` builtin provides a standard mechanism for parsing short options (`-a`, `-b value`):

```bash
while getopts "a:b:h" opt; do
    case $opt in
        a) arg_a="$OPTARG" ;;
        b) arg_b="$OPTARG" ;;
        h) usage; exit 0 ;;
        \?) echo "Invalid option: -$OPTARG"; exit 1 ;;
    esac
done
shift $((OPTIND - 1))  # Remove parsed options from $@
```

The `getopts` builtin does not support long options (`--help`). For long options, you must parse `$@` manually or use the external `getopt` command (which has portability issues across BSD and GNU systems).

**Defensive coding practices.** Robust shell scripts begin with:

```bash
#!/bin/bash
set -euo pipefail
IFS=$'\n\t'
```

The `set -u` option treats unset variables as errors, preventing silent failures from typos. Setting `IFS` to newline and tab prevents word splitting on spaces, which is the source of many quoting bugs. The shebang line should specify `bash`, not `sh`, if the script uses Bash-specific features.

**Temporary file handling.** The `mktemp` command creates a unique temporary file or directory in a secure manner:

```bash
temp_file=$(mktemp)
trap "rm -f '$temp_file'" EXIT
# ... use temp_file ...
```

Never use predictable temporary filenames like `/tmp/myscript.$$`, which are vulnerable to race conditions and symlink attacks.

**Locking.** The `flock` command (on Linux) provides file-based locking to prevent concurrent execution:

```bash
exec 200>/var/lock/myscript.lock
flock -n 200 || { echo "Another instance is running"; exit 1; }
# ... critical section ...
```

This pattern ensures that only one instance of the script runs at a time.

**Structured error handling.** Rather than sprinkling `|| exit 1` throughout a script, define an error handling function:

```bash
die() {
    echo "Error: $*" >&2
    exit 1
}

[ -f "$config_file" ] || die "Config file not found: $config_file"
```

This centralizes error messaging and makes the script's structure clearer.

**Logging.** For scripts that run unattended, structured logging to syslog or a log file is essential:

```bash
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$log_file"
}

log "Starting backup"
perform_backup || log "Backup failed"
log "Backup completed"
```

The date format should be consistent and sortable. ISO 8601 format is recommended.

Bash scripting, approached with an understanding of its execution model and invariants, becomes a powerful tool for system automation and glue code. The key is recognizing the shell's limitations and choosing the appropriate level of abstraction for the task. For complex logic, a full programming language may be more appropriate. For orchestrating Unix commands and managing files, Bash remains unparalleled.
