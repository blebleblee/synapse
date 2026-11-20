# Lesson 2: Semantic Analysis and Type Systems

## 1. First-Principles Intuition & Invariants

The syntactic parser—covered in our previous lesson—accepts or rejects input strings based purely on structural form. It constructs an abstract syntax tree that captures the hierarchical grammatical structure of the program text but remains semantically blind. A parser will happily accept `int x = "hello";` as syntactically valid C code because it matches the production rules for variable declarations. Yet this program is fundamentally meaningless: we cannot store a pointer to character data in a machine word designated for signed integer arithmetic. Semantic analysis bridges this chasm between syntactic well-formedness and executable meaning.

At its philosophical core, semantic analysis enforces the semantic function that maps syntactic constructs to their computational interpretation within a formal system of types, scopes, and semantic constraints. The type system serves as a lightweight proof system: every well-typed program carries a constructive proof that certain classes of runtime errors—type confusion, undefined variable access, arity mismatches—cannot occur. The compiler becomes a theorem prover, and the act of compilation becomes mechanized verification of partial correctness. This is not hyperbole. The Curry-Howard correspondence establishes a deep isomorphism between typed lambda calculi and intuitionistic logic, where types correspond to propositions and programs correspond to proofs. Modern compilers exploit this foundation to guarantee memory safety in Rust, prevent null pointer dereferences in Kotlin, and enforce resource linearity in systems like Clean and ATS.

The semantic analyzer operates on the abstract syntax tree produced by the parser, enriching it with semantic annotations while simultaneously performing three interlocking verification tasks. First, it resolves identifiers to their binding sites through scope analysis, constructing a symbol table that maps names to their declarations across lexical and dynamic scopes. Second, it performs type checking, verifying that every operation receives operands of compatible types and that every function call supplies arguments matching the callee's signature. Third, it enforces semantic constraints that cannot be expressed in context-free grammars: flow-sensitive definite assignment analysis, immutability invariants, lifetime constraints, and more.

The invariants that govern semantic analysis are rooted in the operational semantics of the target machine. A variable reference must resolve to exactly one declaration visible in the current scope; ambiguity is a compilation error. Every expression must possess a well-defined type determined either explicitly through annotation or implicitly through constraint-based inference. Control flow constructs like `break` and `continue` must appear within enclosing loop contexts. Return statements must produce values compatible with the function's declared return type. These invariants are not arbitrary linguistic restrictions but rather necessary conditions for generating correct machine code that respects the von Neumann execution model of sequential instruction fetch, decode, and execute.

Type systems come in many flavors, forming a rich design space with profound implications for both safety and expressiveness. Monomorphic type systems assign a single fixed type to each expression, as in Pascal or early C. Polymorphic systems permit generic abstraction through parametric polymorphism (ML, Haskell) or subtype polymorphism (Java, C++). Dependent type systems like those in Coq, Agda, and Idris allow types to depend on runtime values, enabling compile-time verification of array bounds, protocol conformance, and algorithmic correctness. Linear type systems track resource usage to prevent aliasing and enable safe manual memory management, as seen in Rust's ownership system and the region-based memory management of Cyclone.

The fundamental tension in type system design is the tradeoff between decidability and expressiveness. Hindley-Milner type inference—the foundation of ML and Haskell—achieves complete and decidable type reconstruction for rank-1 polymorphism but cannot infer higher-rank types or GADTs without programmer annotations. Subtyping introduces semantic subsumption where values of more specific types can inhabit contexts expecting less specific types, but subtype checking in the presence of generics and variance becomes undecidable for certain systems. Dependent types offer extraordinary expressive power but require sophisticated constraint solvers and often impose significant annotation burden on the programmer. Modern compiler design navigates these tradeoffs through hybrid approaches: local type inference for lambda arguments, bidirectional type checking that propagates expected types downward and synthesized types upward, and constraint generation with delayed solving.

## 2. Core Architecture & Mechanics

The semantic analysis phase is implemented as a collection of tree-walking passes over the abstract syntax tree, each enriching the tree with semantic information while verifying particular invariants. The architecture is fundamentally multi-pass: scope analysis constructs the symbol table in a first pass, type checking consumes this symbol table in a second pass, and subsequent passes perform flow analysis, definite assignment checking, and other semantic validations. Some compilers interleave these passes for efficiency, but the logical separation remains.

### Symbol Tables and Scope Resolution

The symbol table is the central data structure that maps identifiers to their semantic properties: type, storage class, memory location, and visibility scope. In its simplest incarnation, a symbol table is a hash map from strings to symbol records. However, real compilers require hierarchical symbol tables that respect lexical scoping rules. When a new scope is entered—a function body, a block statement, a loop—the compiler pushes a new scope frame onto a scope stack. Identifier lookup proceeds by searching the current scope, then its lexically enclosing parent scope, and so on until the identifier is found or the search reaches the global scope and fails.

```c
typedef struct Symbol {
    char *name;
    Type *type;
    StorageClass storage;    // auto, static, extern, register
    int offset;              // frame offset for locals
    bool is_defined;         // vs. merely declared
    struct Symbol *next;     // collision chain for hash table
} Symbol;

typedef struct Scope {
    Symbol *symbols[HASH_SIZE];
    struct Scope *parent;    // lexically enclosing scope
    int level;               // nesting depth (0 = global)
} Scope;

typedef struct SymbolTable {
    Scope *current;
    Scope *global;
} SymbolTable;
```

When the parser encounters a variable declaration, the semantic analyzer creates a new symbol entry in the current scope. If an identifier with the same name already exists in the same scope, the compiler emits a redeclaration error. If the identifier shadows a name from an outer scope, the new declaration hides the outer one within the current scope but does not replace it. When the scope exits, the scope frame is popped and the shadowed names become visible again.

Function symbols require special handling because most languages permit forward declarations and separate declaration from definition. The symbol table must track whether a function has been declared, whether it has been defined, and whether multiple declarations are compatible. In C, two function declarations are compatible if they have the same return type and parameter types after applying default argument promotions. The linker will later verify that every declared-but-not-defined symbol has exactly one definition across all translation units.

Name resolution in object-oriented languages introduces additional complexity. Member access expressions like `obj.field` require looking up `field` in the symbol table associated with the type of `obj`. If that type is a class, the lookup proceeds through the class's member table, then recursively through base class tables following the inheritance chain. Method overloading means a single name may map to multiple symbol entries distinguished by signature, requiring overload resolution during type checking. Template instantiation in C++ creates entirely new symbol table entries for each distinct type argument combination, and two-phase name lookup distinguishes dependent names (resolved at instantiation) from non-dependent names (resolved at template definition).

Modern compilers often build an attributed syntax tree (AST) where each node carries semantic annotations produced by the analyzer. Variable reference nodes are annotated with a pointer to the symbol table entry for the referenced variable. Type nodes are annotated with resolved type structures. Function call nodes are annotated with the resolved callee symbol, enabling later passes to generate direct or indirect call instructions without repeating name resolution.

### Type Representations and Type Checking

Types are first-class objects within the compiler's semantic engine, represented as directed acyclic graphs that capture the compositional structure of types. Primitive types like `int`, `float`, and `bool` are leaves. Compound types—pointers, arrays, structures, functions—are internal nodes with edges to their component types. A pointer to an array of ten integers is represented as a pointer node pointing to an array node (with size 10) pointing to an integer node. This representation enables structural equality testing and subtype checking through graph traversal.

```c
typedef enum {
    TYPE_INT, TYPE_FLOAT, TYPE_BOOL, TYPE_CHAR, TYPE_VOID,
    TYPE_POINTER, TYPE_ARRAY, TYPE_FUNCTION, TYPE_STRUCT, TYPE_UNION
} TypeKind;

typedef struct Type {
    TypeKind kind;
    union {
        struct {                    // TYPE_POINTER
            struct Type *base;
        } ptr;
        struct {                    // TYPE_ARRAY
            struct Type *elem;
            int size;
        } array;
        struct {                    // TYPE_FUNCTION
            struct Type *return_type;
            struct Type **params;
            int param_count;
            bool variadic;
        } func;
        struct {                    // TYPE_STRUCT, TYPE_UNION
            char *tag;
            Symbol **members;
            int member_count;
            int size;
            int alignment;
        } aggregate;
    };
} Type;
```

Type checking walks the AST recursively, computing the type of each expression from the types of its subexpressions. Literal expressions have known primitive types: integer literals have type `int`, string literals have type `char *`, and so forth. Variable references obtain their type from the symbol table entry. Binary operators are type-checked by verifying that both operands have compatible types and determining the result type according to the language's type coercion rules.

Integer promotions and usual arithmetic conversions introduce subtle complexity. In C, operands narrower than `int` are promoted to `int` before arithmetic. When a binary operator receives operands of different types—say `int` and `double`—the narrower type is converted to the wider type and the result has the wider type. The compiler must model these implicit conversions in the type checker and later emit explicit conversion instructions in the intermediate representation. Floating-point to integer conversions truncate toward zero. Pointer arithmetic scales by the pointed-to type's size: `ptr + n` advances the pointer by `n * sizeof(*ptr)` bytes, not `n` bytes.

Function calls require matching actual arguments to formal parameters. For each argument position, the type checker verifies that the actual argument's type is compatible with the corresponding formal parameter's type, applying implicit conversions when necessary and permitted. Variadic functions like `printf` accept a fixed initial set of typed parameters followed by an unbounded number of untyped arguments. The type checker cannot verify the types of variadic arguments at compile time; instead, the format string directs runtime interpretation, and mismatches cause undefined behavior.

Assignment compatibility is directional and context-dependent. In C, any integer type can be assigned to any other integer type with potential truncation or sign extension. Pointers to different types are generally incompatible, except that `void *` is a universal pointer type compatible with any object pointer. Pointers to compatible struct types are compatible even if the struct tags differ, provided the member layout matches. Const-correctness requires that non-const pointers cannot be assigned to const-qualified pointers without explicit casts.

### Type Inference and Constraint-Based Analysis

Explicit type annotations impose syntactic overhead and reduce code flexibility. Type inference allows the compiler to deduce types from context, enabling more concise source code without sacrificing static safety. Local variable type inference, as in C++11's `auto` or Java's `var`, is straightforward: the variable receives the type of its initializer expression. Function return type inference examines all return statements and unifies their types.

Full Hindley-Milner type inference, as implemented in ML and Haskell, is a constraint-based algorithm operating in two phases. The constraint generation phase walks the AST and assigns a fresh type variable to each expression whose type is not immediately known. It then generates equality constraints based on the program's structure. If `f` is applied to argument `a`, we generate constraints that `f` has a function type `α → β` and that the type of `a` equals `α`. If two branches of a conditional return values, their types must be equal. If a variable is referenced in multiple contexts, all uses must agree on the type.

```text
let id = λx. x in id 5
```

The constraint generation phase produces:

```text
id : τ₁
x : τ₂
λx. x : τ₂ → τ₂
id 5 : τ₃
5 : int
τ₁ = τ₂ → τ₂
τ₁ = int → τ₃
```

The unification phase solves this constraint system using Robinson's unification algorithm. Unification takes two types and attempts to find a substitution that makes them equal. Unifying `int → τ₃` with `τ₂ → τ₂` succeeds with substitution `[τ₂ := int, τ₃ := int]`. Applying this substitution yields `id : int → int` and `id 5 : int`. If unification encounters incompatible constructors—attempting to unify `int` with `bool`—it fails and the program is ill-typed.

The occurs check prevents infinite types. Unifying `τ` with `τ → τ` would require `τ` to be a function type whose return type is itself, a circular definition that leads to unsound type systems. The occurs check rejects such unifications. Modern type inference algorithms extend this foundation with let-polymorphism (allowing polymorphic generalization at let-bindings), rank-1 predicativity restrictions (preventing higher-rank polymorphism without explicit annotations), and constraint generation for type classes and overloading.

Subtyping complicates inference significantly. With subtyping, we must track not just equality constraints but also subtype constraints of the form `τ₁ <: τ₂`. Constraint solving becomes optimization: finding the most general substitution that satisfies all constraints. For structural subtyping, this is decidable but computationally expensive. For nominal subtyping with multiple inheritance or traits, the constraint graph may have no solution or multiple incomparable solutions.

### Semantic Constraints and Flow-Sensitive Analysis

Beyond type checking, semantic analysis enforces constraints that require understanding control flow. Definite assignment analysis ensures that every local variable is assigned a value before it is read. This prevents the undefined behavior that results from reading uninitialized stack memory. The analysis operates on the control flow graph, propagating definite-assignment states along edges. At each use of a variable, the compiler checks that the variable is definitely assigned on all paths reaching that use.

```text
int x;
if (cond) {
    x = 1;
}
print(x);  // Error: x may be uninitialized
```

After the assignment `x = 1`, the variable `x` is definitely assigned on the true branch. However, if `cond` is false, the assignment never executes. At the `print` call, the true and false branches rejoin. The analysis computes the meet of the definite-assignment states from both branches: a variable is definitely assigned at a merge point only if it is definitely assigned on all incoming branches. Since `x` is not definitely assigned on the false branch, the program is rejected.

Unreachable code detection identifies statements that can never execute. After a return statement within a block, all subsequent statements in that block are unreachable. Loops with constant false conditions are never entered. Unreachable code is typically a warning rather than an error, as it may result from conditional compilation or refactoring artifacts, but it often indicates programmer error.

Exhaustiveness checking for pattern matching and switch statements verifies that all possible cases are covered. Algebraic data types in functional languages have a known, finite set of constructors. The compiler can enumerate all constructors and verify that the pattern match handles each one. If any constructor is missing, the compiler issues a non-exhaustive pattern match error. Similarly, switch statements over enumerations can be checked for exhaustiveness, ensuring that no enum value falls through to a default case that the programmer assumed would never execute.

Ownership and lifetime analysis in Rust represents the most sophisticated semantic analysis in production compilers today. Every value has a unique owner, and ownership transfers when values are moved. References are borrowed with either shared immutable borrows or exclusive mutable borrows, enforced through a fractional permissions system. Lifetimes track the validity regions of references, and the borrow checker ensures that no reference outlives the data it points to. This analysis is flow-sensitive, path-sensitive, and interprocedural, requiring fixed-point iteration over the control flow graph to compute the precise liveness and validity regions of each variable and reference.

### Intermediate Representation and AST Lowering

The semantic analyzer often produces an enriched AST that serves as the input to subsequent compiler phases. However, the AST's structure is heavily influenced by the source language's syntax, making it awkward for optimization and code generation. Modern compilers lower the AST to an intermediate representation (IR) that abstracts away syntactic details and exposes semantic structure.

Three-address code (TAC) is a common IR where each instruction performs a single operation and stores the result in a temporary variable. Complex expressions are decomposed into sequences of primitive operations:

```text
// Source: a = b * c + d * e
t1 = b * c
t2 = d * e
a = t1 + t2
```

This form exposes instruction-level parallelism and simplifies optimization passes. Dead code elimination removes unused temporaries. Common subexpression elimination identifies redundant computations. Strength reduction replaces expensive operations with cheaper equivalents.

Static single assignment (SSA) form extends three-address code with the constraint that each variable is assigned exactly once. To accommodate control flow merges where a variable may have different values depending on the path taken, SSA introduces phi functions:

```text
if (cond) {
    x1 = 1;
} else {
    x2 = 2;
}
x3 = φ(x1, x2);  // x3 = x1 if from true branch, x2 if from false branch
```

SSA form simplifies dataflow analysis by making def-use chains explicit in the variable names themselves. Constant propagation, copy propagation, and many other optimizations become trivial graph traversals. SSA construction requires computing the dominance frontier to determine phi placement, and SSA destruction converts phi functions back to ordinary assignments with register moves before code generation.

Control flow graphs (CFG) represent the program's execution paths as a directed graph where nodes are basic blocks—maximal sequences of straight-line code with no internal branches—and edges represent control flow transfers. Each basic block has a unique entry point at its first instruction and a unique exit point at its last instruction, which is a control flow instruction (jump, conditional branch, return). The CFG enables sophisticated analyses: dominator trees identify control dependencies, loop detection discovers natural loops for loop optimization, and reachability analysis prunes unreachable code.

Many modern compilers use multiple IR levels. LLVM IR is a typed, SSA-based, target-independent IR suitable for machine-independent optimization. After optimization, LLVM lowers the IR to SelectionDAG (a directed acyclic graph of machine operations) for instruction selection, then to machine instructions represented as MachineInstr objects, and finally to assembly or machine code. The GCC compiler traditionally used GIMPLE (a simplified AST form) and RTL (register transfer language) as IRs. Rust's compiler uses HIR (high-level IR, close to AST), MIR (mid-level IR, SSA-based control flow graph), and LLVM IR. Each lowering step discards high-level abstractions and exposes lower-level machine details, enabling optimizations at multiple semantic levels.

## 3. High-Performance Optimization & Failure Modes

Semantic analysis is the performance bottleneck in many compilers because it requires repeated traversal of large, pointer-rich data structures with poor cache locality. The symbol table, type structures, and AST nodes are allocated on the heap with no spatial locality. Each name lookup hashes a string, chases pointers through collision chains, and follows parent pointers up the scope stack. Type checking recursively descends the AST, dereferencing type pointers at every node. For large codebases with deeply nested scopes and complex type hierarchies, semantic analysis can consume a significant fraction of total compilation time.

Interning strings and types dramatically improves performance. Rather than storing each identifier and type as a separate heap allocation, the compiler maintains a global intern table that maps structural content to canonical pointers. Every occurrence of the identifier "count" points to the same interned string. Every instance of the type `int *` points to the same interned type structure. Structural equality tests reduce to pointer equality tests, and hash table lookups hash the pointer value rather than the string content. String interning also reduces memory usage: in a million-line codebase, the identifier "i" may appear tens of thousands of times, but only one copy of the string "i" exists in memory.

Arena allocation pools semantic data structures into contiguous memory regions. Rather than individually allocating each AST node and symbol with malloc, the compiler allocates large arenas (megabyte-sized contiguous buffers) and bump-allocates structures within the arena. Allocation becomes incrementing a pointer. Deallocation of an entire compilation unit's semantic structures becomes freeing the arenas, not traversing and freeing individual nodes. Arena allocation improves cache locality because structures allocated in sequence are likely to be accessed in sequence, and it eliminates per-allocation metadata overhead. GCC and Clang both use arena allocators extensively.

Caching and memoization eliminate redundant work. If the compiler resolves the same qualified name `std::vector<int>::size` thousands of times across a codebase, caching the resolution result in a hash table avoids repeated name lookups through nested namespaces and template instantiations. If unification repeatedly encounters the same pair of types, caching the unification result avoids redundant recursive traversals. However, cache invalidation becomes tricky: if a type is mutated (which should not happen after initial construction but sometimes does during incremental compilation), cached results involving that type must be invalidated.

Parallel semantic analysis is theoretically possible but difficult in practice. Type checking of independent translation units is embarrassingly parallel: compile each source file in parallel with separate symbol tables. However, when template instantiations or inline function definitions cross translation unit boundaries, dependencies emerge. Header files containing templates are parsed and semantically analyzed in every translation unit that includes them, leading to massive redundancy. Precompiled headers snapshot the symbol table and AST state after parsing frequently included headers, avoiding redundant parsing and semantic analysis. Modules in C++20 and Swift replace the textual inclusion model with semantic import of precompiled interfaces, dramatically reducing redundant work.

Incremental compilation and fine-grained dependency tracking allow compilers to avoid reanalyzing unchanged code. The compiler records which source entities (functions, types, constants) depend on which other entities. When a source file changes, the compiler invalidates only the entities that transitively depend on changed entities and reuses semantic analysis results for everything else. Rust's compiler (rustc) employs a query-based architecture where semantic analysis results are cached as query results with precise dependency edges. When source code changes, the query cache invalidates only the affected queries, minimizing recomputation.

Error recovery determines how gracefully the compiler handles ill-formed code. After detecting a semantic error—an undefined variable or type mismatch—the compiler faces a choice. It can abort immediately, reporting only the first error. This is fast but unhelpful when fixing one error reveals a cascade of subsequent errors. Alternatively, the compiler can attempt to recover, synthesizing a placeholder value or type to allow analysis to continue. If a variable reference fails to resolve, the compiler inserts a sentinel "error" type that is compatible with all other types, suppressing cascading errors. If a function call has the wrong argument count, the compiler still type-checks the function body using the declared parameter types. The goal is to report as many independent errors as possible in a single compilation, but error recovery is an art: too aggressive and the compiler reports spurious errors caused by incorrect recovery; too conservative and the compiler stops after the first error.

Error messages are the most visible product of semantic analysis. Poor error messages blame the symptom rather than the cause. When a type mismatch occurs deep in a template instantiation stack, reporting the mismatch at the instantiation site buries the root cause under layers of template machinery. Good compilers trace the error to the original type argument that caused the incompatibility. When unification fails, reporting "cannot unify `α` with `int → β`" is useless; reporting "expected a function but got an integer in expression `f x` at line 42" is actionable. Elm's compiler pioneered friendly error messages with suggestions: "You wrote `String.lenght` but I cannot find that function. Did you mean `String.length`?" Modern compilers employ heuristics like edit distance and scope-aware suggestions to guide programmers toward fixes.

Semantic analysis of gradually typed languages, which mix static and dynamic typing, requires runtime type checks where static guarantees are insufficient. TypeScript erases types at compilation, relying on JavaScript's runtime semantics. Type guards narrow union types through runtime checks: `if (typeof x === "string")` refines the type of `x` from `string | number` to `string` within the true branch. The compiler's semantic analyzer must model these refinements, propagating narrowed types through the control flow graph. Failure to track refinements leads to false positives where the compiler rejects safe code, forcing programmers to insert spurious type assertions.

Template metaprogramming in C++ stretches semantic analysis to its limits. Templates are Turing-complete, and template instantiation is compile-time evaluation. The compiler must evaluate constant expressions, perform constexpr function calls, and select specializations through SFINAE (Substitution Failure Is Not An Error). Deeply nested template instantiations create exponential blowup in the number of types the compiler must construct and compare. To prevent infinite instantiation, compilers impose instantiation depth limits. To prevent compile-time hangs, compilers impose timeout limits on constexpr evaluation. Error messages from template metaprograms are notoriously inscrutable because they report the final instantiation failure, not the logical error in the metaprogram's algorithm.

The future of semantic analysis is in richer type systems and more powerful static verification. Refinement types add logical predicates to types, enabling types like "integers greater than zero" or "sorted arrays." The type checker generates verification conditions discharged by SMT solvers. Liquid types infer refinement predicates automatically, combining type inference with predicate abstraction. Session types enforce communication protocols in concurrent systems, statically verifying that messages are sent and received in the correct order. Effect systems track computational effects like I/O, exceptions, and nondeterminism, enabling safe parallelization of pure code and preventing effect leakage across abstraction boundaries. These advanced type systems blur the line between compilers and program verifiers, using the type checker as a proof assistant to guarantee correctness properties far beyond simple type safety.
