# Lesson 2: Language Semantics

## 1. First-Principles Intuition & Invariants

The Bourne shell family—and Bash as its modern descendant—evolved from a deceptively simple premise: the shell is both an interactive command interpreter and a scripting language. This dual nature creates an inherent tension between human usability and formal language semantics. Understanding Bash's language semantics requires abandoning the illusion that variable expansion, quoting, and word splitting are independent features. They are instead tightly coupled phases of a single *token recognition and expansion pipeline* that transforms raw input text into executable commands.

The Unix philosophy of "everything is text" reaches its logical extreme in Bash. The shell operates fundamentally on streams of bytes, parsing them into tokens through a stateful lexical analyzer. Each token undergoes a series of transformations—variable expansion, command substitution, arithmetic evaluation, and pathname expansion—before word splitting segregates the result into arguments. The order of these expansions is not arbitrary; it is semantically significant and deeply affects which characters are literal versus which trigger expansion.

The core invariant underlying Bash semantics is the *quote removal principle*: quoted strings disable specific expansions and word splitting, but they do not prevent expansion from occurring—they merely change which expansions apply and when quote characters themselves are removed from the result. This distinction is critical. A developer who conflates "quoting prevents expansion" with "quoting removes the need for expansion" will generate shell scripts that fail catastrophically on edge cases like filenames containing whitespace, glob metacharacters, or special characters.

Bash inherits from the Bourne shell a philosophy of backward compatibility that prioritizes historical behavior over orthogonality. This creates several semantic quirks: the `$` sigil introduces both variable references and command substitution; the `${...}` form permits parameter transformation operators that have no direct equivalent in positional arguments; pathname expansion (globbing) consumes unquoted asterisks and question marks in ways that surprise developers trained on regex engines. The shell does not enforce strong type distinctions between strings and arrays; a bare variable reference expands to a single word, while `"${array[@]}"` expands to multiple words, yet both syntactically use the `$` prefix.

The ultimate semantic invariant is that **the shell is a domain-specific language for process orchestration**, not a general-purpose programming language. Its expansion semantics are optimized for the common case of constructing command lines with variable interpolation, not for general data transformation. Understanding this teleology—that every expansion rule exists to solve a specific problem in command construction—illuminates why certain features exist and why their interactions can seem baroque.

## 2. Core Architecture & Mechanics

The Bash parser transforms input text through a well-defined expansion pipeline. This pipeline consists of distinct, sequentially-applied phases, each with precise termination conditions and side effects on the token stream.

### 2.1 The Expansion Pipeline: Phases and Ordering

The first phase is *lexical analysis and parsing*. The shell's lexer reads raw bytes and produces tokens: operators like `|`, `>`, `&`; keywords like `if` and `for`; and quoted or unquoted words. The lexer's key responsibility is to recognize quote boundaries and operator delimiters, applying a precedence system where operators and keywords are recognized only when they appear as complete tokens, not as substrings within words. This is why `>file` works as a redirection but `a>b` concatenates into a single unquoted word (since `>` is not delimited by whitespace).

The second phase is *quote processing and removal*. The shell identifies matching quote pairs—single quotes (`'...'`), double quotes (`"..."`), and `$'...'` ANSI-C quotes—and marks regions within those quotes as quote-protected. Single quotes suppress all expansions and escape sequences. Double quotes permit variable expansion (`$var`), command substitution (`` `cmd` `` or `$(cmd)`), and a limited set of backslash escapes (`\"`, `\\`, `` \` ``, `\$`, and `\newline`). The `$'...'` construct interprets ANSI-C escape sequences like `\n`, `\t`, and `\xHH`, enabling binary data in scripts. Importantly, quote characters are removed from the result; `echo "hello"` does not print the double-quote characters themselves.

The third phase is *parameter expansion*. The shell expands variables prefixed with `$` or enclosed in `${...}`. A bare `$var` expands to the value of the variable named `var`; if `var` is unset, the expansion yields an empty string (unless `set -u` is enabled, which causes an error). The `${var}` form is equivalent but enables parameter transformation operators: `${var:-default}` provides a default value if `var` is unset or empty; `${var#pattern}` removes the shortest match of `pattern` from the start; `${var##pattern}` removes the longest match; `${var%pattern}` and `${var%%pattern}` remove from the end; `${var/pattern/replacement}` performs substring substitution; `${var^pattern}` and `${var,pattern}` perform case transformation. These operators are evaluated during expansion, not as separate passes, which means `${var#${prefix}}` expands the inner `${prefix}` first, then applies the removal to `${var}`.

The fourth phase is *command substitution*. The shell recognizes `` `command` `` or `$(command)` and executes `command` in a subshell, capturing its standard output. The subshell inherits the current shell's variables and settings but runs in a separate process context. Trailing newlines in the output are removed; if the command produces no output, the substitution yields an empty string. Command substitution is recursive: `$(echo $(date))` first expands the inner `$(date)`, then passes its output to `echo`, then captures that result.

The fifth phase is *arithmetic expansion*. The shell recognizes `$((expression))` and evaluates `expression` as an arithmetic expression in base-10 integer arithmetic. The expression may contain variables (referenced without `$`), operators (`+`, `-`, `*`, `/`, `%`, `**`, bitwise operators), and function calls (e.g., `abs(x)`). No quoting or escaping is necessary inside the `$((...))`; the shell's arithmetic parser takes precedence. If the expression evaluates to zero, the expansion yields the string `0`; non-zero values yield their numeric representation.

The sixth phase is *word splitting*. Unquoted words containing the results of expansions are split on Internal Field Separator (IFS) characters—by default, whitespace (space, tab, newline). Importantly, word splitting does not occur inside double quotes; `"$var"` expands `$var` but does not split the result on IFS. This is a common source of bugs: `echo $var` may produce multiple words if `$var` contains IFS characters, while `echo "$var"` always produces a single word. Word splitting is also context-sensitive: in array assignments like `arr=($var)`, word splitting occurs even if `$var` is not quoted, enabling convenient array initialization from space-separated strings.

The seventh phase is *pathname expansion* (globbing). Unquoted words containing the glob metacharacters `*`, `?`, or `[...]` are expanded by matching them against filenames in the current directory and parent directories (relative to the current working directory or the patterns' relative path components). A `*` matches zero or more characters; a `?` matches exactly one character; `[abc]` matches any of `a`, `b`, or `c`; `[!abc]` or `[^abc]` matches any character except those in the set; `[a-z]` matches ranges. If no files match the pattern, the word is left unchanged (unless `shopt -s nullglob` is set, in which case the pattern produces no words). Pathname expansion respects the `GLOBIGNORE` variable and does not match filenames starting with `.` unless the pattern explicitly includes `.`.

After these seven phases, the resulting tokens are executed as a command: the first token is looked up as a builtin, function, or external executable; subsequent tokens become arguments.

### 2.2 Variable Expansion in Detail

Variables in Bash are dynamic name-value pairs stored in a hash table. Assignment is syntactically simple: `var=value` creates or updates the variable `var` with the string value `value`. No spaces surround the `=` operator; `var = value` is interpreted as running the command `var` with arguments `=` and `value`. The scope of a variable is the current shell and its child subshells by default; exporting via `export var` places the variable in the environment, making it available to child processes launched via `exec` or subprocess operators.

The `$var` reference expands as follows: if `var` is set, the expansion yields its value; if `var` is unset and `set -u` is enabled, an error is raised; otherwise, an empty string results. This behavior is modified by parameter expansion operators. The `${var:-default}` form expands to `$var` if it is set and non-empty, otherwise to `default`. The distinction between "set but empty" and "unset" is crucial: `${var:-default}` treats an empty string the same as an unset variable, while `${var-default}` (without the colon) only applies the default if the variable is unset, not if it is empty.

Parameter transformation operators are applied during expansion, not as post-processing. When the shell encounters `${var#pattern}`, it expands `$var` to its value, then attempts to match `pattern` at the start of the result. If a match is found, the matched portion is removed and the remainder is the expansion result. The `pattern` itself is subject to expansion; `${var#${prefix}}` expands `${prefix}` first, then uses its value as the removal pattern. This recursive expansion is powerful but can introduce subtle bugs: if `prefix` contains glob metacharacters, they are not interpreted as glob patterns but as literal characters to match in the removal.

Arrays in Bash introduce additional semantic complexity. An array is declared via `arr=(element1 element2 ...)`, and individual elements are accessed via `${arr[index]}` where `index` is an arithmetic expression. The `${arr[*]}` form expands to all elements concatenated into a single word (IFS-separated), while `${arr[@]}` expands to multiple words, each being a separate array element. This distinction is critical for preserving array structure across function calls and redirections. A bare reference like `$arr` expands only the first element, equivalent to `${arr[0]}`, which is a common source of confusion.

Arrays also support negative indexing and range slicing. `${arr[-1]}` expands to the last element; `${arr[-2]}` to the second-to-last. The slice operator `${arr[@]:offset:length}` extracts `length` elements starting at `offset`; if `length` is omitted, the slice extends to the end of the array. Slicing with negative offsets counts from the end; `${arr[@]:-5}` extracts the last five elements.

### 2.3 Quoting Mechanisms and Their Interaction with Expansion

Single quotes suppress all expansions: `echo '$var'` prints the literal string `$var`, not the value of the variable `var`. Inside single quotes, backslashes are literal characters, not escape introducers. The only way to include a single quote inside a single-quoted string is to end the quote, add an escaped single quote `\'`, and resume quoting: `'can'\''t'` produces the string `can't`.

Double quotes permit variable expansion, command substitution, and a limited set of backslash escapes. `echo "The time is $(date)"` expands the command substitution. `echo "Price: $amount"` expands the variable. Backslash escapes inside double quotes are recognized only before characters that have special meaning: `\"` produces a literal double quote, `\$` produces a literal dollar sign (preventing variable expansion), `` \` `` produces a literal backtick, `\\` produces a literal backslash, and `\newline` escapes a newline to permit line continuation. Backslash followed by any other character is literal; `echo "\n"` produces a backslash followed by `n`, not a newline.

ANSI-C quoting via `$'...'` interprets escape sequences: `$'\n'` expands to a newline, `$'\t'` to a tab, `$'\xHH'` to the byte with hex value HH, and `$'\uHHHH'` to the Unicode character. This is useful for embedding binary data or special characters without relying on external tools. For example, `printf '%s\0' a b c | od -c` can be replaced with `printf '%s\0' $'a\0b\0c'`.

The interaction between quoting and word splitting is a common semantic trap. Consider three variations:

```bash
var="hello world"
echo $var              # prints: hello world (two words)
echo "$var"            # prints: hello world (one word)
echo $'hello\nworld'   # prints: hello\nworld (two lines)
```

In the first case, `$var` expands to `hello world`, then word splitting segregates it into two arguments to `echo`, which prints them space-separated. In the second case, `"$var"` expands to `hello world` as a single word, preventing word splitting; `echo` receives one argument and prints it as-is. In the third case, the ANSI-C quote expands to a literal newline, but word splitting does not occur inside any quoting mechanism, so `echo` receives one argument containing a newline character, which it prints as two lines.

### 2.4 Command Substitution Mechanics

Command substitution executes a command and captures its output. The two syntactic forms—`` `command` `` and `$(command)`—are semantically equivalent, though `$(...)` nests more safely and is preferred in modern scripts. The command runs in a subshell: a child process that inherits the parent shell's variables and settings but has a separate process ID, file descriptor table, and job control state.

The captured output undergoes trailing newline removal: if the command produces output ending in one or more newlines, those trailing newlines are removed. This is why `echo $(date)` produces output without an extra blank line, even though `date` appends a newline to its output. Leading and internal newlines are preserved; `echo $(printf 'a\nb\nc')` produces `a b c` (with spaces replacing internal newlines due to word splitting) if unquoted, or `a` followed by a literal newline and `b` followed by a newline and `c` if double-quoted.

Command substitution is expensive: it spawns a new process, which requires fork and exec system calls, memory allocation, and I/O redirection setup. In performance-critical scripts, developers often use process substitution or here-documents to avoid subshells. However, command substitution is necessary when the command's output must be captured and injected into the current command line; there is no alternative mechanism for this use case.

Nesting command substitutions is valid but requires careful quoting. `echo "$(echo "$(date)")"` works as follows: the innermost `$(date)` expands to the current date string; that result becomes the argument to the middle `echo`; that output is captured by the outer `$(...)` and becomes the argument to the outer `echo`. The quoting isolates each layer from word splitting and glob expansion.

### 2.5 Word Splitting and IFS Semantics

The Internal Field Separator (IFS) variable controls word splitting. Its default value is the three characters space, tab, and newline. When the shell expands an unquoted variable, the result is split on any sequence of IFS characters; consecutive separators collapse into a single separator. This behavior is inherited from the original Bourne shell, where space-separated command-line arguments were the norm.

The mechanics of word splitting are subtle. The shell distinguishes between IFS characters that are whitespace (space, tab, newline by default) and those that are non-whitespace. Whitespace IFS characters are treated as delimiters that collapse; non-whitespace IFS characters always separate words but multiple consecutive non-whitespace separators do not collapse. For example, if `IFS=:`, then `echo $var` where `var="a::b"` expands to three words: `a`, an empty string, and `b`. This is rarely useful; IFS is typically whitespace or a single character like `:` (as in PATH parsing).

Word splitting occurs only on unquoted expansions. After variable expansion, command substitution, and arithmetic expansion, if the result is not quoted, the shell splits on IFS. This is why `"$var"` prevents word splitting—the double quotes protect the result from splitting—but `$var` does not. A common pattern is to use `"${var[@]}"` for arrays to preserve element boundaries; without quotes, `${arr[@]}` would be split on IFS, potentially breaking elements that contain whitespace.

Modifying IFS is powerful but error-prone. A script that sets `IFS=:` to parse colon-separated data must remember to restore the original IFS afterward, or else all subsequent word splitting uses the modified separator. The safe pattern is to use a subshell or local scope:

```bash
# Safe pattern: subshell scope
(
  IFS=:
  read -r key value  0 )); then` uses arithmetic evaluation for the condition (note the double parentheses, which are shorthand for `[[ $(( count > 0 )) ]]`). The result of arithmetic is treated as a boolean: zero is false, non-zero is true. This is the opposite of C's convention (where zero is false and non-zero is true in conditionals, but this is because the condition is the return value of arithmetic, not a numeric value).

## 3. High-Performance Optimization & Failure Modes

### 3.1 Expansion Order and Semantic Gotchas

The order of expansions is not merely procedural; it has profound effects on correctness. A common mistake is to assume that word splitting occurs before pathname expansion, but the actual order is variable expansion, command substitution, arithmetic expansion, word splitting, then pathname expansion. This means that unquoted variables containing glob metacharacters will have those characters interpreted as globs, not as literal strings.

Consider a script that lists files matching a pattern stored in a variable:

```bash
pattern="*.txt"
ls $pattern      # WRONG: pattern is expanded, then *.txt is globbed
ls "$pattern"    # CORRECT: pattern is expanded to *.txt as a single word
```

In the first case, `$pattern` expands to `*.txt`, then glob expansion matches all `.txt` files, and `ls` receives them as arguments. This works for the intended use case but fails if `pattern` contains shell metacharacters that should be literal. In the second case, `"$pattern"` expands to the literal string `*.txt` as a single word, and `ls` receives it as a filename argument (which will fail unless a file is literally named `*.txt`).

Another gotcha involves command substitution and word splitting. `echo $(cat file.txt)` expands the output of `cat file.txt`, then word-splits the result. If `file.txt` contains multiple lines, each line becomes a separate word. `echo "$(cat file.txt)"` quotes the result, preserving line structure as a single word. For correct behavior, nearly all command substitutions should be quoted.

### 3.2 Performance Implications of Expansion Choices

Excessive command substitution is a performance anti-pattern. Each `$(...)` forks a subshell, allocates memory, and waits for completion. In a tight loop, this is measurable overhead. An equivalent using parameter expansion is orders of magnitude faster:

```bash
# SLOW: command substitution in a loop
for file in *.txt; do
  base=$(basename "$file" .txt)
  echo "$base"
done

# FAST: parameter expansion
for file in *.txt; do
  base="${file%.txt}"
  echo "$base"
done
```

The parameter expansion `${file%.txt}` removes the `.txt` suffix without spawning a process. For processing large numbers of files, the difference is substantial.

Similarly, large globs can degrade performance. If the current directory contains millions of files, `ls *.txt` requires the shell to match the glob against every filename, an O(n) operation. In such scenarios, using `find` with `-name` filtering is more efficient, as `find` applies the filter during directory traversal, not after.

### 3.3 Edge Cases and Defensive Practices

Filenames with special characters are a persistent source of bugs. A filename containing a space, such as `my file.txt`, can cause expansions to behave unexpectedly:

```bash
file="my file.txt"
cat $file        # WRONG: expands to two arguments "my" and "file.txt"
cat "$file"      # CORRECT: expands to one argument "my file.txt"
```

Filenames containing newlines are rare but possible. They break many shell patterns:

```bash
# This breaks if $file contains a newline
for file in $list; do
  process "$file"
done

# This is safer for filenames with newlines
while IFS= read -r -d '' file; do
  process "$file"
done < <(find . -print0)
```

The `-d ''` option to `read` treats the null byte as the delimiter, enabling correct handling of filenames containing newlines. The process substitution `< <(find . -print0)` feeds the output of `find -print0` (which outputs null-terminated filenames) into the read loop.

Variables that are unset can cause scripts to fail silently or produce unexpected results. The `set -u` option causes the shell to raise an error when an unset variable is referenced, providing early detection of bugs:

```bash
set -u  # exit on unset variable reference
echo "$undefined_var"  # error: undefined_var: unbound variable
```

However, `set -u` has one notable exception: unset parameters in `${var:-default}` forms are handled gracefully, returning the default without error. This makes `set -u` compatible with scripts using defensive parameter expansion.

Array handling introduces further complexity. A bare reference to an array like `echo $arr` expands only the first element, not the entire array. Developers often expect `$arr` to expand to all elements joined by IFS, but this is not the case. The correct forms are `${arr[@]}` for multiple words or `${arr[*]}` for a single word. Furthermore, when an array is passed as an argument to a function, it must be expanded properly; `func $arr` passes only the first element, while `func "${arr[@]}"` passes all elements as separate arguments.

### 3.4 Debugging Expansion Issues

The `set -x` option enables command tracing, printing each command after expansion to stderr. This is invaluable for debugging expansion bugs:

```bash
set -x
var="hello world"
echo $var
```

The output is:

```
+ echo hello world
hello world
```

The `+` prefix shows the expanded command; you can see that `echo` receives two arguments. With `echo "$var"`, the trace shows `+ echo 'hello world'` (with quoting to indicate it is a single argument).

The `declare -p` builtin prints all variables and their values, useful for inspecting what variables are set and what they contain. For arrays, `declare -p arr` shows the array's elements and indices, enabling verification that an array was populated correctly.

### 3.5 Semantic Interactions: Complex Expansion Chains

Nested expansions can produce surprising results because each layer of expansion is processed in the defined order. Consider:

```bash
var='$other'
other="value"
echo $var          # prints: $other (no nested expansion)
echo ${var}        # prints: $other (same as above)
eval "echo $var"   # prints: value (eval re-parses the string)
```

In the first two cases, `$var` expands to the literal string `$other`, not the value of the variable `other`. The shell does not recursively expand variables; `$var` expands once, yielding the string `$other`, which is then passed to `echo` without further expansion. If recursive expansion were desired, `eval` can force re-parsing, but this is dangerous if the variable contains untrusted data, as `eval` is vulnerable to injection attacks.

Command substitution combined with variable expansion requires careful quoting:

```bash
cmd="echo hello"
$(eval "$cmd")     # executes: echo hello
$($cmd)            # error: tries to execute "echo" with argument "hello"
```

In the first case, `eval` treats the string as shell code and re-parses it. In the second case, `$cmd` expands to `echo hello`, then the shell attempts to execute the word `echo` as a command with `hello` as an argument inside the command substitution. This is subtle but important: command substitution expects a command, not a variable that might contain a command.

Arithmetic expressions with nested variables require careful attention to quoting:

```bash
var=10
echo $(($var + 5))       # prints: 15
echo $(("$var" + 5))     # also prints: 15 (quotes don't affect arithmetic)
echo $((var + 5))        # also prints: 15 (no $ needed inside $((...)))
```

Inside arithmetic expansion, variable names are referenced without `$`, so `var` and `$var` are equivalent. Quoting has no effect because arithmetic parsing takes precedence over quote processing.

The interaction between arrays and word splitting in command substitution is particularly tricky:

```bash
arr=(one two three)
cmd=$(echo "${arr[@]}")  # cmd expands to "one two three"
# Later:
$cmd                     # tries to execute: "one two three" as command
```

If the intent is to pass the array elements as arguments, this approach fails because command substitution produces a single string. The correct approach is direct array expansion without command substitution, or explicit use of `declare` and `export` if the array must be passed to a subshell.

---

This exploration of Bash language semantics reveals a language optimized for interactive command-line use and simple scripting tasks. The expansion pipeline, while complex, is deterministic and learnable. Mastery requires internalizing the ordering of expansions, the subtle interactions between quoting and splitting, and the defensive practices that prevent bugs from accumulating in production scripts. The investment in understanding these semantics pays dividends in scripts that handle edge cases gracefully and perform efficiently at scale.
