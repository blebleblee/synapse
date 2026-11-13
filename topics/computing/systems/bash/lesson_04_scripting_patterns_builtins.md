```markdown
# Lesson 4: Scripting Patterns, Parameter Expansion, Builtins

## 1. First-Principles Intuition & Invariants

Bash scripting occupies a unique position in the Unix ecosystem, functioning simultaneously as a command interpreter and a programming language. Unlike compiled languages where types and scoping are enforced at compile time, Bash operates as a dynamic, untyped command interpreter where the fundamental unit of execution is the word—a sequence of characters subject to a series of expansions and transformations before being passed to commands. This execution model explains why operations as simple as variable assignment, array indexing, or conditional testing can behave unexpectedly without proper quoting and parameter expansion syntax.

The Bash interpreter follows a predictable execution pipeline for every line of script: tokenization, expansion (brace, tilde, parameter, command substitution, arithmetic, word splitting, pathname globbing), quote removal, and finally execution. This pipeline is not merely a convenience layer—it defines how the shell interprets your code. Variables in this model are not first-class objects with type information; they are environment strings stored in a process's symbol table, accessed through parameter expansion syntax. Arrays, introduced in Bash 2.0 and extended in subsequent versions, function as associative maps where indices are strings, though the default array syntax treats them as zero-indexed sequences.

Scoping in Bash derives from Unix's process model and the inheritance of environment variables across parent-child processes. When you export a variable, you place it in the environment block passed to all child processes spawned by the current shell. Local variables exist only within the current shell's execution context and are not inherited unless explicitly passed. Function scope in Bash is dynamic, not lexical—a variable set inside a function, unless declared with the `local` keyword, modifies the variable in the caller's scope. This represents a fundamental departure from lexical scoping in compiled languages and reflects the shell's origin as a command glue layer rather than a general-purpose programming language.

Conditionals in Bash present one of the most frequently misunderstood design choices. The shell provides two syntaxes: the POSIX-compliant `[ ]` (test command) and the Bash-specific `[[ ]]` (conditional expression). The distinction is not syntactic sugar; `[ ]` is a true command that parses its arguments like any other utility, while `[[ ]]` is a keyword with special parsing rules. This difference has profound implications for word splitting, pathname expansion, and operator precedence. Understanding when to use each form is not a matter of style but of correctness and security.

Builtins in Bash represent commands that the shell executes directly without spawning a subprocess. This differs fundamentally from external utilities, which require a fork-exec cycle. For performance-critical scripts, preferring builtins over external commands can eliminate thousands of context switches. Builtins also represent a semantic trap: they operate within the shell's own address space, and their behavior is not guaranteed to match external commands with the same name. The `echo` builtin, for instance, behaves differently across shells, while `/bin/echo` offers more predictable behavior on Unix systems.

## 2. Core Architecture & Mechanics

### Parameter Expansion and Variable Substitution

Bash's parameter expansion follows a formal grammar defined in the POSIX shell specification and extended by Bash. Parameter expansion is triggered by the `$` character, followed by a parameter name, number, or special symbol. The fundamental form is `${parameter}`, which retrieves the value of `parameter`. Without the braces, `$parameter` works equally well in most contexts, but the braced form is necessary when the parameter name is followed by characters that would otherwise be parsed as part of the name.

Consider the distinction between `$var10` (which attempts to retrieve the variable `var10`, not the tenth element of an array named `var`) and `${var[10]}` (which explicitly indexes array `var` at position 10). This ambiguity arises because Bash's tokenization does not distinguish between variable names and array access syntax at the lexical level; the parser must look ahead to determine where the parameter name ends.

#### Default Values and Coercion

Parameter expansion includes several categories of transformations, each with distinct semantics. The form `${parameter:-default}` expands to the value of `parameter` if it is set and non-null; otherwise it expands to `default`. The distinction between set-but-empty and unset is critical. If `parameter` is set to an empty string, `${parameter:-default}` returns `default`, but `${parameter-default}` returns the empty string. This distinction matters in scripts that distinguish between "not configured" (unset) and "configured to be empty" (set to empty string). 

Similarly, `${parameter:=default}` assigns `default` to `parameter` if it is unset or null, then expands to the assigned value. This supports lazy initialization patterns where a variable should adopt a default value on first access:

```bash
#!/bin/bash

# Lazy initialization pattern
get_config_dir() {
    echo "${CONFIG_DIR:=/etc/myapp}"
}

# First call initializes CONFIG_DIR if unset
config_dir=$(get_config_dir)
echo "Config directory: $config_dir"

# Verify assignment persisted
echo "CONFIG_DIR is now: $CONFIG_DIR"
```

The `${parameter:+word}` form expands to `word` if `parameter` is set and non-null; otherwise it expands to nothing. This is useful for conditional expansion where you want a computed value only when a variable has content:

```bash
backup_opts="${BACKUP_VERBOSE:+-v}${BACKUP_COMPRESS:+-z}"
tar $backup_opts -cf backup.tar data/
```

#### Parameter Substitution and Removal

The forms `${parameter#pattern}` and `${parameter%pattern}` remove the shortest match of `pattern` from the beginning and end of `parameter` respectively. The doubled forms `${parameter##pattern}` and `${parameter%%pattern}` remove the longest match. These operations are string-based and respect Bash's glob syntax, not regular expressions. For example:

```bash
#!/bin/bash

# File extension extraction
filename="archive.tar.gz"
echo "${filename##*.}"        # Output: gz (longest match from start)
echo "${filename#*.}"         # Output: tar.gz (shortest match from start)
echo "${filename%.*}"         # Output: archive.tar (remove shortest suffix)
echo "${filename%%.*}"        # Output: archive (remove longest suffix)

# Path manipulation
path="/usr/local/bin/python3"
echo "${path%/*}"             # Output: /usr/local/bin
echo "${path##*/}"            # Output: python3

# Configuration stripping
line="   leading and trailing spaces   "
stripped="${line#  }"         # Remove two leading spaces
echo "[$stripped]"
```

The distinction between `#` (prefix removal) and `%` (suffix removal) aligns mnemonically to their position on a QWERTY keyboard: `#` appears before `%`, so `#` removes from the front.

#### String Replacement

The form `${parameter/pattern/replacement}` replaces the first occurrence of `pattern` with `replacement`. The doubled form `${parameter//pattern/replacement}` replaces all occurrences:

```bash
#!/bin/bash

# Basic replacement
text="the quick brown fox"
echo "${text/brown/red}"      # Output: the quick red fox
echo "${text//[aeiou]/X}"     # Output: thX qXXck brXwn fXx (glob, not regex)

# Anchored replacement (prefix/suffix only)
path="/usr/bin:/usr/local/bin:/opt/bin"
# Replace only at start
echo "${path/#\/usr\/bin/\/opt\/bin}"    # Output: /opt/bin:/usr/local/bin:/opt/bin
# Replace only at end
echo "${path/%\/bin/\/sbin}"             # Output: /usr/bin:/usr/local/bin:/opt/sbin

# Dynamic replacement with parameter expansion
old_prefix="/old/path"
new_prefix="/new/path"
file_path="/old/path/to/file"
echo "${file_path//$old_prefix/$new_prefix}"  # Output: /new/path/to/file
```

These operations are case-sensitive and use glob syntax, not regex. The `replacement` string itself undergoes parameter expansion, allowing dynamic substitution.

#### Substring Extraction

The form `${parameter:offset}` extracts `parameter` starting at `offset` characters from the beginning. The form `${parameter:offset:length}` extracts exactly `length` characters starting at `offset`:

```bash
#!/bin/bash

string="The quick brown fox jumps over the lazy dog"

# Extract from position 4 to end
echo "${string:4}"                    # Output: quick brown fox jumps over the lazy dog

# Extract 5 characters starting at position 4
echo "${string:4:5}"                  # Output: quick

# Negative offset counts from end (requires space to avoid ambiguity with :-)
echo "${string: -8}"                  # Output: lazy dog
echo "${string: -8:4}"                # Output: lazy

# Practical: extract file timestamp
timestamp="2024-03-15T14:30:45Z"
year="${timestamp:0:4}"
month="${timestamp:5:2}"
day="${timestamp:8:2}"
echo "Date: $year-$month-$day"
```

If `offset` is negative and `length` is omitted, extraction proceeds from the offset position to the end of the string.

#### Case Modification

The forms `${parameter^}`, `${parameter^^}`, `${parameter,}`, and `${parameter,,}` convert the first character to uppercase, all characters to uppercase, the first character to lowercase, and all characters to lowercase respectively. These operations are locale-aware and respect the current `LC_CTYPE` setting:

```bash
#!/bin/bash

text="Hello World"

# Single character case change
echo "${text^}"                       # Output: Hello World (first char upper)
echo "${text,,}"                      # Output: hello world (all lower)
echo "${text^^}"                      # Output: HELLO WORLD (all upper)

# Conditional casing with pattern
word="bash"
echo "${word^[a-z]}"                  # Output: Bash (uppercase matching pattern)
echo "${word^^[aeiou]}"               # Output: bAsh (uppercase vowels)

# Practical: normalize environment variable names
env_var="database_host"
echo "${env_var^^}"                   # Output: DATABASE_HOST
```

These operations were introduced in Bash 4.0 and provide a native alternative to the external `tr` command for case conversion.

#### Indirection

The form `${!parameter}` performs indirect expansion: if `parameter` contains the name of another variable, the expansion yields the value of that named variable. For example, if `var=foo` and `foo=bar`, then `${!var}` expands to `bar`. This mechanism enables dynamic variable names and is frequently used in scripts that construct variable names programmatically:

```bash
#!/bin/bash

# Dynamic variable lookup
db_host_prod="prod.example.com"
db_host_staging="staging.example.com"
db_user_prod="admin"
db_user_staging="dev"

env="prod"
host="${!db_host_${env}}"             # Indirect expansion of db_host_prod
user="${!db_user_${env}}"             # Indirect expansion of db_user_prod
echo "Connecting to $host as $user"

# Iterate over named array references
declare -A config_server1
declare -A config_server2
config_server1[ip]="192.168.1.1"
config_server1[port]="8080"
config_server2[ip]="192.168.1.2"
config_server2[port]="8081"

for i in 1 2; do
    config_ref="config_server$i"
    # Note: Cannot directly dereference associative arrays via indirection
    # This is a limitation of Bash's type system
done
```

Indirect expansion also applies to array indices: `${!array[@]}` expands to all indices of the array `array`, not its values. This is essential for iterating over associative arrays:

```bash
#!/bin/bash

declare -A users
users[alice]="alice@example.com"
users[bob]="bob@example.com"
users[charlie]="charlie@example.com"

# Iterate over associative array keys
for key in "${!users[@]}"; do
    echo "$key: ${users[$key]}"
done
```

### Arrays and Associative Arrays

Bash supports two types of arrays: indexed arrays (introduced in Bash 2.0) and associative arrays (introduced in Bash 4.0). Indexed arrays use integer indices starting at zero, while associative arrays use arbitrary strings as keys. Both ty
