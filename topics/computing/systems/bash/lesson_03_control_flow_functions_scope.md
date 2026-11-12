# Lesson 3: Control Flow, Functions, Variable Scope, Arrays

## 1. First-Principles Intuition & Invariants

The shell, despite its surface simplicity as a text processing tool, is fundamentally a runtime interpreter for a Turing-complete imperative language. At its core lies a conceptual machine that must decide *which instructions to execute and in what order*, manage *naming and binding of data across execution contexts*, and organize *collections of related values* in memory. These three problems—control flow, scope, and data structures—form the skeleton upon which all shell programs are built.

Control flow in Bash represents the most direct manifestation of the stored-program concept. When the shell parses a script, it constructs an abstract syntax tree (AST) where each node represents a command, a conditional branch, or a loop. The execution engine walks this tree sequentially, but the tree itself contains branches and cycles that allow non-linear traversal. A `test` condition evaluation determines which path the engine takes; a `for` loop instructs the engine to revisit a subtree multiple times with different bindings. Understanding this requires abandoning the naive view of scripts as linear text and instead visualizing them as executable graphs with decision nodes and cycles.

Variable scope in a shell context is inseparable from the process model and the shell's implementation as an interpreter. Unlike compiled languages where scope is resolved at compile time through symbol tables and machine code organization, shell scope is resolved *at runtime through dynamic environment frames*. Each function invocation creates a new execution context—a frame on a logical stack—where local variable declarations shadow outer bindings. This is fundamentally a runtime behavior: the shell maintains a symbol table (internal hash tables or dynamic arrays) that it searches from innermost scope outward. When a variable is referenced, the interpreter performs a linear search through the scope chain. When a variable is assigned with the `local` keyword, it is registered in the current frame and automatically unbound when the frame exits. This is not a luxury of implementation; it is a core semantic property of how shells manage complexity across function boundaries.

Arrays in Bash represent a second-order data structure abstraction layered atop the string-as-universal-type principle. Bash offers two array models: indexed arrays, which are ordered collections accessed by integer position, and associative arrays (hash maps), which are unordered collections accessed by string keys. Internally, both are implemented as hash tables or ordered maps, but the indexed variant preserves insertion order and allows sparse population (elements can be omitted, creating gaps). The crucial invariant is that array elements are themselves strings; Bash does not support nested array structures natively. This limitation flows directly from Bash's design philosophy: strings are the atoms, and all abstraction is built by convention on top of string operations and parameter expansion.

At the deepest level, control flow, functions, and arrays are all manifestations of the same underlying principle: *the shell is a high-level interface to the Unix process model and the filesystem*. A loop is an instruction to the shell to repeatedly invoke subcommands with different environment bindings. A function is a named sequence of commands stored in the shell's memory, invoked as a single logical unit without spawning a new process (in most cases). An array is a structure that packs multiple values into a single namespace entry, reducing the number of variables the caller must manage. Each of these is a layer of abstraction that lets humans express intent at a higher level than raw process spawning and environment mutation.

## 2. Core Architecture & Mechanics

### 2.1 Conditional Evaluation: `test`, `[[ ]]`, and Exit Status Semantics

The foundation of control flow is the *exit status*—a single integer value (0–255) returned by every command that the shell evaluates to determine success or failure. By Unix convention, exit status 0 means success, and any non-zero value means failure. This design choice, simple as it appears, cascades through the entire shell language: conditionals do not evaluate to boolean true/false; instead, they *execute a command and inspect its exit status*.

The `test` command (and its synonym `[`) is a built-in utility that evaluates a condition and returns exit status 0 if the condition is true, exit status 1 if false. The command understands a vocabulary of unary operators (testing file attributes, string properties), binary operators (comparisons), and logical operators (combining conditions). When invoked as `test -f /etc/passwd`, the shell executes the built-in, which checks whether `/etc/passwd` is a regular file, and returns exit status 0 if the check succeeds. When you write `if test -f /etc/passwd; then ...`, you are not evaluating a boolean expression; you are *conditionally executing a sequence of commands based on the exit status of another command*.

The `[[ ]]` construct is a shell keyword (not a command) that provides enhanced condition evaluation with additional operators and different word-splitting and globbing semantics. Unlike `[ ]`, which is subject to word splitting and pathname expansion (because it is a command receiving arguments), `[[ ]]` treats its contents as a special syntax layer where whitespace and metacharacters have their own rules. The expression `[[ $var == pattern ]]` performs pattern matching where `pattern` is interpreted as a glob pattern, not a literal string. The expression `[[ -v var ]]` tests whether a variable is set, a feature unavailable in `test`. Internally, `[[ ]]` is compiled by the parser into bytecode that the shell interpreter evaluates directly, avoiding the overhead of command invocation and argument parsing. This makes `[[ ]]` both more powerful and more efficient for most conditional logic.

Exit status propagation is crucial to understanding how control structures compose. When you write:

```bash
if command1; then
  command2
elif command3; then
  command4
else
  command5
fi
```

The shell executes `command1` and captures its exit status. If the exit status is 0, the shell executes `command2` and skips the `elif` and `else` blocks. If `command1` returns non-zero, the shell executes `command3`, and so on. Notice that the exit status of `command2` is *not* used for any decision; it is simply executed. Only the exit status of the command immediately following `if` or `elif` controls the flow. This distinction is critical when chaining commands: the exit status of the last command in a pipeline is the exit status of the entire pipeline, but intermediate command failures are masked unless the `pipefail` option is set.

### 2.2 Looping Constructs: Iteration as Repeated Command Invocation

The `for` loop is the shell's primary abstraction for iteration. In its most common form, `for var in word1 word2 word3; do command; done`, the shell expands the word list (performing brace expansion, parameter expansion, command substitution, and pathname expansion), produces an array of resulting values, and iterates: in each iteration, `var` is bound to the current element, and the commands inside the loop body are executed. Crucially, the loop does not maintain separate variable bindings for each iteration; instead, `var` is reassigned in the current scope on each iteration. If the loop body contains a function that modifies `var`, that modification persists into the next iteration unless explicitly reset.

Consider the interaction between loops and subshells. If any command in the loop body is a pipeline or runs in a subshell (explicitly via `( ... )` or implicitly via command substitution), variable assignments within that subshell do not propagate back to the parent loop. This is because a subshell is a separate process; it receives a copy of the parent's environment, modifies its copy, and exits. The parent's environment is unchanged. This creates a subtle but pervasive source of bugs: loops that accumulate results by appending to a variable often fail silently if the append operation is buried inside a pipeline. The solution is to avoid subshells in loops when the loop body must update outer-scope variables, or to use process substitution and `read` to capture output without spawning a subshell.

The `while` loop executes the loop body repeatedly as long as a condition (a command's exit status) remains 0. The `until` loop is the inverse: it executes the loop body repeatedly as long as a condition returns non-zero. Both constructs are commonly paired with `read` to iterate over lines in a file or stdin:

```bash
while IFS= read -r line; do
  process "$line"
done < file.txt
```

Here, `read` attempts to read a line from `file.txt`, returning exit status 0 on success and 1 at end-of-file. The loop continues as long as `read` succeeds. Note the `IFS=` prefix: this clears the Internal Field Separator for this command only, instructing `read` not to strip leading/trailing whitespace. Without this, lines with leading or trailing spaces would be silently modified. The `-r` flag instructs `read` to treat backslashes as literal characters, not escape sequences. These details matter because they affect the correctness of data parsing.

The `case` statement is a specialized conditional for matching a value against multiple patterns. Its structure is:

```bash
case $var in
  pattern1)
    commands
    ;;
  pattern2)
    commands
    ;;
  *)
    commands
    ;;
esac
```

The shell expands `$var`, then compares the result against each pattern in sequence (using pathname expansion syntax: `*` matches any string, `?` matches a single character, `[...]` matches a character class). When a pattern matches, the corresponding commands are executed, and control jumps to the end of the `case` statement. If no pattern matches and a `*)` catch-all is present, its commands are executed. The `;;` terminator is mandatory; it prevents fall-through to the next case (though some shells support `;;&` for fall-through behavior).

### 2.3 Function Declaration and Invocation: Process and Scope

A function in Bash is a named sequence of commands that can be invoked by name without spawning a separate process. When the shell parses a function definition:

```bash
myfunction() {
  echo "Hello, $1"
}
```

it does not execute the function body; it stores the function in memory (in an internal symbol table) and returns to the prompt. When you later invoke `myfunction arg`, the shell looks up the function in its symbol table, executes the function body in the *current shell process*, and returns control to the caller. All variable assignments in the function affect the calling shell unless the variable is declared `local`.

This in-process invocation is fundamentally different from external command execution. When you invoke an external command like `ls`, the shell forks a new process, executes the command in that process, waits for it to exit, and captures its exit status. When you invoke a function, no fork occurs; the function runs in the same process context as the caller, sharing all variables and file descriptors. This has profound implications for performance (no fork overhead) and for state management (all side effects are visible to the caller).

The parameters passed to a function are received as positional parameters: `$1`, `$2`, etc. These are *distinct from the caller's positional parameters*. When a function is invoked, the shell saves the caller's `$@` and `$#`, sets new values for the function's parameters, executes the function body, and restores the caller's parameters upon return. This parameter-switching mechanism allows functions to abstract over their arguments without polluting the caller's parameter space. However, any variable *not* explicitly declared `local` is shared between the function and its caller, creating an implicit coupling.

The `local` keyword declares a variable to exist only within the current function scope and any nested function scopes. When a `local` variable is assigned:

```bash
myfunction() {
  local x=10
  echo "$x"
}
```

the shell creates a new binding for `x` in the current function's scope. If the caller had a variable named `x`, it is now shadowed; references to `x` inside the function resolve to the local binding. When the function returns, the `local` binding is unbound, and the caller's `x` (if it existed) is visible again. Internally, the shell maintains a scope chain: a stack of symbol tables, one for each function invocation level (with the global scope at the base). Variable lookup is performed by searching from the top of the stack downward; variable assignment (without `local`) modifies or creates a binding in the topmost frame.

A key invariant: `local` declarations must appear *before* the variable is used, even if the variable is later assigned. The declaration `local x` creates the binding in the current scope immediately; any previous global binding with the same name is now shadowed. If you later assign `x=10`, you are assigning to the local binding, not creating a new one. If you do not declare `x` local and assign `x=10`, you are modifying the global binding (or creating a new global if it does not exist).

Function return values are communicated via exit status (a number from 0 to 255) or by modifying caller-visible variables. The `return` keyword sets the exit status:

```bash
myfunction() {
  if [[ condition ]]; then
    return 0
  else
    return 1
  fi
}

if myfunction; then
  echo "Success"
fi
```

For returning complex data (strings, arrays), you must use variables or stdout. Writing values to stdout and capturing them with command substitution is idiomatic:

```bash
get_value() {
  echo "result"
}

value=$(get_value)
```

However, command substitution creates a subshell, so any side effects (variable modifications, directory changes) are lost. To return data without a subshell, modify a variable passed by the caller (a pattern sometimes called "output by reference"):

```bash
get_value() {
  local -n outvar=$1
  outvar="result"
}

myvar=""
get_value myvar
echo "$myvar"  # Prints "result"
```

This uses a *nameref* (name reference), a feature that makes `outvar` an alias for the variable passed as the first argument. When you assign to `outvar`, you are actually assigning to the original variable in the caller's scope. This is a powerful pattern for returning multiple values or large data structures without the overhead of subshells or stdout capture.

### 2.4 Variable Scope: Dynamic Binding and the Scope Chain

Bash implements *dynamic scoping*, not lexical scoping. This means that variable binding is determined at runtime based on the call stack, not at parse time based on textual nesting. Consider:

```bash
x=10

func1() {
  x=20
  func2
}

func2() {
  echo "$x"
}

func1  # Prints 20, not 10
```

When `func2` executes, it looks up `x` in the scope chain: first in its own local scope (none exists), then in `func1`'s scope (where `x` is 20), then in the global scope. It finds `x=20` and prints it. The text of `func2` does not indicate that it uses `func1`'s `x`; the binding is determined at runtime based on which function called it. This is radically different from lexical scoping, where `func2` would use the global `x` because it is textually defined in the global scope.

Dynamic scoping is powerful for certain patterns (e.g., implicit context passing through function call chains), but it can be confusing and is a source of subtle bugs. The solution is to use `local` declarations liberally. By declaring all variables in a function as `local`, you ensure that the function does not accidentally capture or modify caller-visible variables.

Global variables are accessible from any function and any script sourced into the same shell. When you assign a variable at the top level of a script (not inside a function), it is a global variable. When you source a script with `. script.sh` or `source script.sh`, the script runs in the current shell process, and any variables it defines become global. This is different from executing a script as an external command (e.g., `bash script.sh`), which spawns a new shell process and does not affect the caller's variables.

Environment variables are a special class of global variables that are exported to child processes. When you assign `var=value` in a shell and then run an external command, that command does not see `var` unless you explicitly export it: `export var=value`. The `export` keyword marks a variable for inheritance by child processes. Internally, the shell maintains an environment list (similar to the Unix `environ` array in C) and passes this list to each child process at fork time. This is how child processes inherit the parent's configuration.

### 2.5 Arrays: Indexed and Associative

Bash arrays are collections of strings, accessed by position (indexed arrays) or by key (associative arrays). An indexed array is declared and populated:

```bash
arr=(a b c)
echo "${arr[0]}"    # Prints "a"
echo "${arr[@]}"    # Prints "a b c"
echo "${#arr[@]}"   # Prints 3 (length)
```

The syntax `arr=(...)` is array literal syntax; the shell expands the words inside the parentheses and assigns them as array elements. Sparse arrays are supported: `arr[10]=x` creates an array with only index 10 populated; indices 0–9 are unset. The `@` symbol in `"${arr[@]}"` expands to all elements, properly quoted (each element is treated as a separate word). Without quotes, `${arr[@]}` expands to all elements, subject to word splitting. The distinction is crucial: `echo ${arr[@]}` may split multi-word elements, while `echo "${arr[@]}"` preserves element boundaries.

Iterating over an indexed array is accomplished with:

```bash
for i in "${!arr[@]}"; do
  echo "Index $i: ${arr[$i]}"
done
```

The `${!arr[@]}` expansion produces the indices of the array, not the elements. This allows safe iteration even when the array is sparse.

Associative arrays are hash maps, declared and used as:

```bash
declare -A map
map[key1]="value1"
map[key2]="value2"

echo "${map[key1]}"    # Prints "value1"
echo "${map[@]}"       # Prints values (order undefined)
echo "${!map[@]}"      # Prints keys (order undefined)
```

The `declare -A` statement is mandatory; it informs the shell that `map` is an associative array. Without this declaration, `map[key]=value` is interpreted as an arithmetic assignment (which fails) or as trying to use a scalar variable as an array (which causes a different error). Iteration over associative arrays follows the same pattern as indexed arrays, but the order of keys is undefined (implementation-dependent, often insertion order in bash but not guaranteed).

Arrays cannot be nested in Bash. You cannot have an array of arrays directly. However, you can simulate nested structures using nameref and function parameters. For example, to pass an array to a function and modify it:

```bash
modify_array() {
  local -n arr_ref=$1
  arr_ref[0]="modified"
}

myarr=(a b c)
modify_array myarr
echo "${myarr[0]}"  # Prints "modified"
```

Here, `arr_ref` is a nameref to `myarr`, so assigning to `arr_ref[0]` modifies `myarr[0]`.

A subtle but important detail: array subscripts are expanded and evaluated as arithmetic expressions. Writing `arr[$x]` does not treat `$x` as a literal string; instead, it evaluates `$x` as a number and uses the result as the index. This means `arr[01]` is the same as `arr[1]` (leading zeros are ignored in arithmetic context). For associative arrays, subscripts are *not* arithmetic expressions; `map[01]` is distinct from `map[1]` because they are distinct string keys.

## 3. High-Performance Optimization & Failure Modes

### 3.1 Subshell Overhead and Variable Capture

One of the most common performance pitfalls in shell scripts is unnecessary subshell creation. Subshells occur in several contexts: explicit parentheses, command substitution (backticks or `$(...)`), pipes, and background processes. Each subshell is a fork operation—a system call that creates a new process with a copy of the parent's memory space. On modern systems, fork is relatively fast (the kernel uses copy-on-write to avoid physically duplicating memory), but the overhead is still significant compared to in-process function calls. For tight loops that perform many iterations, repeatedly forking subshells can dominate runtime.

A common anti-pattern is using command substitution inside a loop that accumulates results:

```bash
# Inefficient: command substitution creates a subshell on each iteration
result=""
while IFS= read -r line; do
  result+=$(process_line "$line")
done < input.txt
```

Each iteration spawns a subshell for the `process_line` function (if it is external), captures its output, and appends it to `result`. For large files with many lines, this can become a bottleneck. A better approach is to use functions (which do not spawn subshells) and accumulate output in a variable or array:

```bash
# Efficient: function invocation in-process
result=""
process_line() {
  result+="$1"  # Modify caller's variable directly
}

while IFS= read -r line; do
  process_line "$line"
done < input.txt
```

or

```bash
# Alternative: capture output to array, join at the end
declare -a results
while IFS= read -r line; do
  results+=("$(process_line "$line")")
done < input.txt

# Join array elements
result="${results[*]}"
```

The second approach still uses command substitution, but it accumulates results in an array, which is then joined once, rather than performing string concatenation on each iteration.

Pipeline performance is another consideration. Each pipe segment (except the last) runs in a subshell, so a pipeline like `cmd1 | cmd2 | cmd3` spawns two subshells. For simple data transformations, using external tools in a pipeline is often necessary and acceptable. However, when the same data flows through many filters, constructing a pipeline can be expensive. In such cases, reading data into memory (if it fits) and processing it with shell constructs is sometimes faster.

### 3.2 Array Operations and Large Collections

Bash arrays are fundamentally list structures: indexed arrays are stored as ordered collections (often sparse), and associative arrays are hash maps. Both are implemented as internal hash tables or similar dynamic structures within the shell process. As arrays grow large, operations become slower: expanding `"${arr[@]}"` requires the shell to iterate through all elements, and iterating with `for` loops has linear time complexity.

For very large collections (tens of thousands of elements or more), Bash is not the right tool; the overhead of the shell interpreter becomes prohibitive. However, for moderate sizes (up to a few thousand elements), arrays are practical. Some performance tips:

Avoid repeated array expansion. If you need to process all array elements multiple times, store the expanded list in a variable first:

```bash
# Inefficient: arr is expanded twice
if [[ " ${arr[*]} " == *" $needle "* ]]; then
  # Also process arr again...
  for elem in "${arr[@]}"; do
    ...
  done
fi

# Efficient: expand once
arr_expanded=" ${arr[*]} "
if [[ "$arr_expanded" == *" $needle "* ]]; then
  ...
fi
for elem in "${arr[@]}"; do
  ...
done
```

Use associative arrays for membership testing. If you need to check whether a value is in a set, an associative array is more efficient than a linear search:

```bash
# Linear search: O(n)
is_member() {
  local needle=$1
  for elem in "${arr[@]}"; do
    [[ "$elem" == "$needle" ]] && return 0
  done
  return 1
}

# Hash map lookup: O(1) average case
declare -A set
for elem in "${arr[@]}"; do
  set[$elem]=1
done

[[ -v set[$needle] ]] && echo "Found"
```

Avoid repeatedly modifying sparse arrays. If you create an array with large index gaps and frequently iterate over it, the iteration cost is proportional to the largest index, not the number of elements:

```bash
# Inefficient: largest index is 1000000, iteration is slow
declare -a arr
arr[1000000]="value"
for i in "${!arr[@]}"; do
  echo "$i: ${arr[$i]}"  # Only one iteration, but shell checks all indices
done

# Use associative array if you need sparse collections
declare -A map
map[1000000]="value"
for k in "${!map[@]}"; do
  echo "$k: ${map[$k]}"  # Only iterates over actual keys
done
```

### 3.3 Scope Chain Depth and Function Call Overhead

While function calls do not spawn subshells, they do have overhead: the shell must manage the scope chain, save and restore the caller's positional parameters, and handle `local` variable binding and unbinding. For deeply nested function call chains (especially in recursive functions), this overhead accumulates.

Recursive functions in Bash are supported but should be used cautiously. Each recursive call adds a frame to the scope chain, consuming memory. Additionally, Bash does not optimize tail calls, so a tail-recursive function does not avoid stack growth. For problems that are naturally recursive (e.g., tree traversal), recursion is acceptable if the recursion depth is bounded and reasonable. For unbounded recursion or deep recursion, an iterative approach with an explicit stack (simulated with an array) is preferable.

An example of recursion with bounded depth: traversing a directory tree to a fixed depth. An example of unbounded recursion to avoid: implementing a general-purpose tree traversal that could recurse arbitrarily deep. In the latter case, an iterative approach with explicit state management is more robust.

### 3.4 Edge Cases and Common Failure Modes

**Unset variables in conditionals**: A variable that has never been assigned is unset. Referencing an unset variable in a scalar context expands to the empty string, but in certain contexts (like `set -u`), it triggers an error. In conditionals, unset variables can cause subtle bugs:

```bash
if [[ $unset_var == "value" ]]; then
  echo "Match"
fi
```

This does not error; `$unset_var` expands to the empty string, and the comparison is `"" == "value"`, which is false. However, if the intent was to check whether the variable is set and has a specific value, this logic is flawed. Use `[[ -v var ]]` to test for variable existence:

```bash
if [[ -v unset_var && $unset_var == "value" ]]; then
  echo "Match"
fi
```

**Word splitting in loops and conditionals**: The default behavior of word splitting can cause subtle bugs in loops. Writing `for word in $string; do ...` causes `$string` to be split on whitespace, but multiple spaces are collapsed, and any shell metacharacters are expanded. The correct pattern is `for word in $string;` when you intend splitting, or `for word in "$string";` when you intend to treat the string as a single item. Similarly, in conditionals, `[[ $var == pattern ]]` performs pattern matching, while `[[ "$var" == pattern ]]` performs pattern matching on the expanded value of `$var`. Omitting quotes often leads to unintended globbing or word splitting.

**Array iteration with unquoted expansions**: Writing `for elem in ${arr[@]}; do ...` (without quotes) causes word splitting on array elements. If array elements contain spaces, they are split into multiple words. Always use `"${arr[@]}"` (with quotes) to preserve element boundaries.

**Function parameter shadowing**: If a function parameter (like `$1`) is used as a loop variable, or if a loop variable shadows a function parameter, bugs can result:

```bash
process_items() {
  for item in "$@"; do
    # $item is the loop variable, $1 is the first parameter
    # If we reassign item, $1 is not affected, but we might expect it to be
    item="modified: $item"
  done
  # $item still contains the last modified value here
}
```

The `for item in "$@"` loop creates a loop variable `item` that is distinct from the function parameters `$1`, `$2`, etc. Modifying `item` does not affect `$1`. This is usually the desired behavior, but it can be a source of confusion.

**Nameref cycles and invalid references**: A nameref that references a non-existent variable or a nameref that creates a cycle (a nameref that references itself, directly or indirectly) causes errors or unexpected behavior:

```bash
declare -n ref=undefined_var
echo "$ref"  # Expands to empty string (no error in many cases)

declare -n a=b
declare -n b=a
echo "$a"  # Potential cycle; behavior is undefined or error
```

Always validate that nameref targets exist and are not part of a cycle.

**Case statement patterns**: Case patterns use glob syntax, which can be surprising. Writing `case $var in a|b) ...;; esac` matches `a` or `b`, but writing `case $var in "a|b") ...;; esac` matches the literal string `"a|b"`. Without quotes, the pipe is interpreted as an alternation operator:

```bash
case "test" in
  te[st])    # Matches "tes" or "tet", not "test"
    echo "Wrong"
    ;;
  test)      # Matches "test"
    echo "Correct"
    ;;
esac
```

Patterns in case statements are not regular expressions; they are glob patterns. If you need regex matching, use `[[ =~ ]]` in conditionals instead.

**Loop control with `break` and `continue`**: The `break` and `continue` statements operate on the innermost loop. If you have nested loops and call a function from the inner loop, the function cannot affect the outer loop's control flow:

```bash
outer_loop() {
  for i in 1 2 3; do
    inner_function
  done
}

inner_function() {
  for j in a b c; do
    if [[ condition ]]; then
      break  # Breaks the inner loop in the function, not the outer loop
    fi
  done
}
```

If you need to break from an outer loop based on a condition in a nested context, use return values or variables and check them after the loop returns.

By mastering these constructs and understanding their underlying mechanisms—exit status propagation, process model implications, scope chain dynamics, and array implementation details—you can write efficient, robust shell scripts that scale and handle edge cases correctly. The key is to think in terms of the shell's fundamental abstractions: processes, environments, and text streams, not in terms of high-level language features that shell happens to syntactically resemble.
