# Lesson 2: Type Inference, Narrowing, Control Flow Analysis

## 1. First-Principles Intuition & Invariants

TypeScript's type system represents one of the most sophisticated implementations of gradual typing in a production language compiler, combining Hindley-Milner-derived inference with bidirectional type checking and control flow-sensitive analysis. Unlike structurally sound type systems that guarantee runtime safety through conservative static analysis, TypeScript's design philosophy embraces a pragmatic balance: it provides the ergonomic benefits of automatic type inference while maintaining compatibility with JavaScript's dynamic semantics through a carefully bounded soundness model. This lesson dissects the internal mechanics that power TypeScript's type checker—a component that must reconcile the competing demands of developer productivity, compile-time performance, and correctness guarantees across a language whose runtime semantics permit patterns that would be rejected by more conservative type systems.

The theoretical foundation of TypeScript's inference engine draws from the Hindley-Milner tradition but extends it substantially to handle features absent from the pure lambda calculus: mutable variables, imperative control flow, structural subtyping, intersection and union types, and higher-kinded type operators. Where classic Hindley-Milner operates through unification over a constraint graph to derive principal types, TypeScript implements a bidirectional type checking algorithm that alternates between synthesis mode—where types flow upward from expressions to their contexts—and checking mode—where expected types flow downward to constrain subexpressions. This bidirectional approach proves essential for handling contextual typing scenarios where the same expression must be typed differently depending on its usage site, such as a function literal whose parameter types are inferred from the signature of a higher-order function receiving it.

Control flow analysis in TypeScript operates at a fundamentally different level of granularity than traditional dataflow frameworks used in optimizing compilers. Rather than tracking abstract values through transfer functions over lattice elements, TypeScript's control flow graph operates directly on type refinements, maintaining a mapping from program points to refined type environments. Each conditional branch, type guard assertion, or discriminant check creates a flow node in an immutable graph structure, with edges representing both possible and impossible execution paths. The type checker walks this graph during analysis, accumulating type refinements along each path and computing the union of types at join points where multiple control flow paths reconverge. This approach enables TypeScript to understand that after testing `typeof x === "string"` in an if statement's condition, the variable `x` has type `string` in the consequent branch while retaining its original union type in the else branch—a capability that requires precise modeling of both positive and negative information flow.

The invariants that govern TypeScript's type system reveal deliberate compromises made to preserve JavaScript compatibility while maximizing static safety within those constraints. TypeScript maintains the invariant that all valid JavaScript programs are valid TypeScript programs when annotated with appropriate types, but it does not guarantee that all type-correct TypeScript programs are free of runtime type errors. The system admits unsound patterns in specific, well-documented scenarios: the `any` type acts as both a top and bottom type, breaking the usual subtyping lattice; bivariant function parameter checking permits unsound subsumption; and type assertions allow developers to override the type checker's conclusions. These soundness holes exist by design, reflecting the reality that JavaScript codebases frequently employ dynamic patterns—reflection, prototype manipulation, heterogeneous collections—that cannot be precisely typed without dependent types or refinement types, features that would push type checking into undecidable territory and destroy compilation performance.

TypeScript's gradual typing discipline maintains a critical separation between the static type world and the runtime value world. Type information exists purely at compile time and is erased completely during emit, leaving no runtime type tags or checks beyond those explicitly written by the developer. This erasure property imposes fundamental constraints on what the type system can express: types cannot be reified or inspected at runtime, generic type parameters cannot be used in `instanceof` checks, and the type system cannot enforce representation invariants that depend on runtime values. The type checker must therefore reason about program behavior using only the static structure of code, without executing it or maintaining symbolic execution states—a constraint that makes certain analyses, such as tracking precise numeric ranges or reasoning about pointer aliasing, infeasible within TypeScript's architecture.

## 2. Core Architecture & Mechanics

The type inference mechanism in TypeScript operates through a sophisticated constraint-solving engine that builds and solves systems of type equations as it traverses the abstract syntax tree. When the compiler encounters an expression whose type must be inferred, it generates fresh type variables—placeholders representing unknown types—and establishes constraints between these variables based on the expression's structure and its surrounding context. Consider a simple variable declaration with an initializer: `let x = [1, 2, 3]`. The inference engine creates a type variable `T` for the array's element type, observes that the literal elements are all numeric literals with type `number`, and solves the constraint `T = number`, ultimately inferring `number[]` as the array's type. This process mirrors Hindley-Milner's Algorithm W but operates within a richer type algebra that includes union types, intersection types, literal types, and indexed access types.

Contextual typing represents TypeScript's most distinctive extension to traditional type inference, enabling bidirectional information flow where expected types influence the interpretation of expressions. When a function literal appears as an argument to a call where the parameter type is known, the type checker propagates this contextual type downward to constrain the lambda's parameter and return types. The mechanics of contextual typing operate through a contextual type cache maintained during the checking phase—a mapping from expression nodes to their expected types. Consider this higher-order function invocation:

```typescript
function map<T, U>(arr: T[], fn: (item: T) => U): U[] {
    return arr.map(fn);
}

const lengths = map(["hello", "world"], s => s.length);
```

When checking the callback `s => s.length`, the type checker queries the contextual type for this expression position, discovers the expected type `(item: string) => U` derived from the generic substitution `T = string`, and uses this information to infer that `s` has type `string` without requiring an explicit annotation. The return type `U` is then synthesized from the expression `s.length`, which has type `number`, completing the inference `U = number`. This bidirectional discipline avoids the need for pervasive type annotations while preserving principal types for expressions in isolation—expressions that lack a contextual type fall back to synthesis mode and infer maximally general types based solely on their internal structure.

Control flow analysis in TypeScript builds upon a graph representation that models the branching and merging structure of imperative control flow. The compiler constructs this control flow graph during semantic analysis, creating flow nodes at each point where type information might be refined: variable declarations, assignments, conditional expressions, type guard assertions, and discriminant checks. Each flow node maintains references to its antecedent nodes—the set of flow nodes that might have executed immediately before reaching the current point. The graph structure is immutable and cached, allowing efficient reanalysis when declaration files change without requiring full rebuilding of the control flow representation.

```
FlowStart (function entry)
    ↓
FlowLabel (x: string | number)
    ↓
FlowCondition (typeof x === "string")
    ↓                    ↓
FlowTrue (x: string)    FlowFalse (x: number)
    ↓                    ↓
    ↘                  ↙
      FlowLabel (merge point)
```

Type narrowing operates through a process of type subtraction and refinement that modifies the apparent type of variables along specific control flow paths. When the type checker encounters a type guard—a runtime test that discriminates between members of a union type—it computes the narrowed type by intersecting the variable's original type with the positive information revealed by the guard. For a test like `typeof x === "string"`, the narrowed type in the consequent branch is computed as `typeof(x) & string`, which simplifies to `string` if `x`'s original type included `string` as a union member. The complementary narrowing in the else branch removes the `string` possibility, computing the type as `typeof(x) \ string`, the set-theoretic difference. These refinements are recorded in the flow node's associated type facts, creating a persistent record of what the type checker has learned about program state at each point.

TypeScript's discriminated union analysis extends control flow narrowing with structural pattern matching on object properties. When a union type's members share a common discriminant property—a literal-typed field that uniquely identifies each variant—checking this property in a conditional enables the type checker to narrow the entire object to the corresponding variant type. The implementation tracks discriminant properties through a discriminant property cache that maps union types to their discriminable keys, enabling efficient lookup during control flow analysis. Consider this canonical example:

```typescript
type Success<T> = { status: "success"; value: T };
type Failure = { status: "error"; error: Error };
type Result<T> = Success<T> | Failure;

function processResult<T>(result: Result<T>): T | null {
    if (result.status === "success") {
        return result.value;  // result: Success<T>
    } else {
        console.error(result.error);  // result: Failure
        return null;
    }
}
```

Inside the consequent branch, the type checker has narrowed `result` from `Result<T>` to `Success<T>` by observing that `result.status === "success"` eliminates the `Failure` variant. This narrowing occurs because the checker detects that `status` is a discriminant property—it appears in both union members with mutually exclusive literal types. The narrowing logic examines each member of the union, retains only those whose discriminant property's type is compatible with the tested value, and produces a refined union. If only one member survives this filtering, the union collapses to a single type, enabling access to properties specific to that variant without type assertions.

Exhaustiveness checking leverages control flow analysis to detect when pattern matching over a discriminated union fails to handle all possible cases. The type checker uses a never-type analysis to determine whether any execution path leaves a union variable unnattowed to the `never` type—the empty type that inhabits no values. When all cases have been properly handled through narrowing, the remaining type at a function's exit point or in a default case should reduce to `never`. If instead a non-empty type remains, the checker can report a compile-time error indicating that additional cases exist. The idiomatic pattern places an assertion in the default case:

```typescript
function exhaustive(value: never): never {
    throw new Error(`Unhandled case: ${value}`);
}

type Shape = Circle | Square | Triangle;

function area(shape: Shape): number {
    switch (shape.kind) {
        case "circle":
            return Math.PI * shape.radius ** 2;
        case "square":
            return shape.size ** 2;
        case "triangle":
            return 0.5 * shape.base * shape.height;
        default:
            return exhaustive(shape);  // Error if new shape added
    }
}
```

If a developer later adds a `Pentagon` variant to the `Shape` union without updating the `area` function, the `default` case will become reachable with `shape` having type `Pentagon`, causing a type error when passing it to `exhaustive`, which expects `never`. This technique transforms a runtime bug—silently returning undefined or throwing at runtime—into a compile-time error that forces the developer to address the new case.

The type checker implements flow-sensitive analysis through a mechanism called flow caching that memoizes the refined type at each flow node to avoid redundant recomputation. When the checker needs to determine a variable's type at a given program point, it walks backward through the control flow graph from that point, accumulating refinements until reaching a flow node with a cached type or arriving at the variable's declaration. The cache uses weak references to flow nodes as keys, with values representing the narrowed type environment at that point. This caching strategy proves essential for compilation performance in large codebases, where the same variable might be referenced hundreds of times across nested control flow structures, each requiring type resolution.

Intersection and union types introduce significant complexity into the constraint-solving process because they form a type algebra with non-trivial identities and normalization rules. The type checker maintains types in a canonical form through a normalization process that applies distributive laws, absorbing elements, and simplification rules. For example, `string & number` normalizes to `never` because these types share no inhabitants, while `(A | B) & C` distributes to `(A & C) | (B & C)`. Union types are stored in a flattened representation with duplicate and never members removed, and the ordering of members is canonicalized to enable structural equality checks through simple reference comparison. These normalizations occur during type construction, ensuring that semantically equivalent types share a single representation in memory—a property that proves critical for performance, as type comparison occurs millions of times during checking of a large project.

## 3. High-Performance Optimization & Failure Modes

Type inference performance scales with the complexity of the constraint graph and the number of generic instantiations required during checking. The dominant cost in large TypeScript projects arises from instantiation of generic types with complex substitutions, particularly when higher-kinded type operators like mapped types and conditional types compose deeply. Each generic instantiation creates a fresh type in the type checker's internal representation, and if these types are not properly cached, redundant instantiation of structurally equivalent types can cause exponential blowup. The type checker employs a type instantiation cache keyed by the tuple of the generic type and its type arguments, enabling structural sharing when the same instantiation is requested multiple times across the program.

Deeply nested conditional types represent one of the most problematic performance pathologies in the type system. Conditional types in TypeScript implement a form of type-level computation where the result type depends on a subtype check: `T extends U ? X : Y` evaluates to `X` if `T` is assignable to `U`, otherwise to `Y`. When these conditionals nest deeply or recurse, the type checker must explore multiple branches of the type-level computation tree, potentially evaluating exponentially many subtype checks. The compiler implements recursion depth limits and instantiation depth limits to prevent infinite loops, but these limits are heuristic and can still permit expensive computations to proceed for hundreds of recursion levels. Developers working with complex type-level programming should monitor the `--extendedDiagnostics` flag to expose instantiation counts and type checking time:

```typescript
// Problematic: deeply nested conditional recursion
type DeepAwait<T> = T extends Promise<infer U>
    ? DeepAwait<U>
    : T;

type Nested = Promise<Promise<Promise<Promise<string>>>>;
type Result = DeepAwait<Nested>;  // Instantiates 5 times
```

While this example remains tractable, the same pattern applied to union types causes multiplicative expansion. A conditional type over a union with ten members requires evaluation of all ten branches, and if each branch itself contains a conditional over a union, the expansion becomes quadratic. The solution involves writing conditional types that short-circuit aggressively or use intersection types to constrain branches before evaluation.

Control flow analysis performance degrades when functions contain excessive branching or when variables are reassigned frequently across many control flow nodes. Each assignment to a variable creates a new flow node, and type resolution requires walking backward through all assignments to find the narrowest type. Functions with hundreds of local variables and deeply nested conditionals can produce control flow graphs with thousands of nodes, causing type checking to become perceptibly slow. The mitigation strategy involves extracting complex control flow into separate functions, which creates flow graph partitions that can be analyzed independently, and using const assertions to prevent variables from being reassigned:

```typescript
// Problematic: single massive function with complex flow
function processLargeUnion(value: A | B | C | D | E | F): Result {
    let result: Result;
    if (value.kind === "A") {
        result = handleA(value);
    } else if (value.kind === "B") {
        result = handleB(value);
    }
    // ... many more branches
    return result;
}

// Optimized: dispatch table with const bindings
function processLargeUnion(value: A | B | C | D | E | F): Result {
    const handlers = {
        A: handleA,
        B: handleB,
        C: handleC,
        D: handleD,
        E: handleE,
        F: handleF
    };
    const handler = handlers[value.kind];
    return handler(value as any);  // Each handler has precise type
}
```

The dispatch table approach eliminates branching from the control flow graph while maintaining type safety within each handler function. Although this pattern requires a type assertion at the call site, the safety is preserved because each handler is implemented with a precise parameter type.

Inference failure modes arise when the constraint system becomes underconstrained or overconstrained, leading to types that are either too general or conflicting. Underconstrained inference occurs when a generic type parameter appears only in contravariant positions or does not appear at all, preventing the type checker from synthesizing a concrete type. The classic example involves a callback-free API where the generic parameter serves only as a return type annotation:

```typescript
function create<T>(): T {
    return {} as T;  // No way to infer T
}

const value = create();  // Inferred as create<unknown>()
```

The type checker defaults to `unknown` when it cannot infer a type parameter, which maximizes safety at the cost of requiring explicit type arguments or type assertions at the call site. Overconstrained inference occurs when conflicting constraints are generated, such as requiring a type parameter to simultaneously extend two incompatible types. The type checker resolves this by inferring `never`, indicating that no type satisfies the constraints:

```typescript
function impossible<T extends string & number>(value: T): T {
    return value;
}

const result = impossible(42);  // Error: number not assignable to never
```

These failure modes signal design problems in the API rather than compiler bugs—they indicate that the generic abstraction is attempting to express a relationship that cannot be maintained in the type system.

Discriminated union narrowing fails when discriminant properties are not checked directly or when multiple properties must be tested simultaneously. TypeScript's narrowing is syntactic rather than semantic—it analyzes the structure of the guard condition rather than reasoning about logical implications. Testing a derived property or using a helper function breaks the narrowing:

```typescript
type Result<T> = Success<T> | Failure;

function isSuccess<T>(result: Result<T>): result is Success<T> {
    return result.status === "success";
}

function process<T>(result: Result<T>): T | null {
    if (isSuccess(result)) {
        return result.value;  // Error: Property 'value' does not exist
    }
    return null;
}
```

Although `isSuccess` returns a type predicate that should narrow `result`, TypeScript does not trace the refinement through the function call. The type checker sees the call to `isSuccess` as opaque and does not propagate the narrowing. The workaround involves inlining the discriminant check or using a switch statement that the type checker recognizes:

```typescript
function process<T>(result: Result<T>): T | null {
    switch (result.status) {
        case "success":
            return result.value;  // Narrowed correctly
        case "error":
            return null;
    }
}
```

Switch statements over discriminant properties receive special handling in the control flow analyzer, which treats each case label as introducing a refinement. This special case recognition reflects a deliberate tradeoff in the type checker's architecture—fully general semantic analysis of predicates would require SMT solving and is infeasible within the performance budget of a compiler that must recheck code on every keystroke in an IDE.

Nullable type narrowing operates through a combination of control flow analysis and truthiness semantics. TypeScript recognizes certain idiomatic patterns for null checking and applies narrowing automatically. Testing a variable with `if (x)`, `if (x != null)`, or `if (x !== undefined)` all trigger narrowing that removes `null` and `undefined` from the variable's type in the consequent branch. However, this narrowing is fragile and breaks when the test is indirect or distributed across multiple conditions:

```typescript
function processOptional(value: string | null): number {
    const isValid = value != null;
    if (isValid) {
        return value.length;  // Error: value is still string | null
    }
    return 0;
}
```

The type checker does not propagate the nullability information through the `isValid` variable because that would require tracking boolean variable definitions and their relationship to refinements—a capability that would significantly complicate the flow analysis and degrade performance. The solution involves performing the null check inline or using the non-null assertion operator when the developer has reasoning that the checker cannot follow:

```typescript
function processOptional(value: string | null): number {
    const isValid = value != null;
    if (isValid) {
        return value!.length;  // Asserts value is non-null
    }
    return 0;
}
```

The non-null assertion operator `!` overrides the type checker's conclusion without generating any runtime code—it represents an escape hatch for situations where the static analysis cannot capture the developer's reasoning about program behavior.

Type widening during inference represents a deliberate imprecision that trades exactness for usability. When inferring the type of a mutable variable initialized with a literal, TypeScript widens the literal type to the nearest widened primitive type: `let x = "hello"` infers `string` rather than `"hello"`, while `const x = "hello"` infers the literal type `"hello"`. This widening reflects the assumption that mutable variables will be reassigned with different values of the same primitive type. Without widening, every subsequent assignment would require a type assertion:

```typescript
let name = "Alice";  // Type: string (widened)
name = "Bob";        // OK

const constName = "Alice";  // Type: "Alice" (literal)
let constCopy = constName;  // Type: "Alice" (no widening on copy)
constCopy = "Bob";          // Error: "Bob" not assignable to "Alice"
```

Developers can prevent widening by using const contexts or explicit type annotations. The `as const` assertion applies recursive const context to an entire object literal or array, preserving all literal types and marking arrays as readonly tuples:

```typescript
const config = {
    host: "localhost",
    port: 8080
} as const;  // Type: { readonly host: "localhost"; readonly port: 8080 }
```

This pattern proves essential when building type-safe state machines, routing tables, or configuration objects where literal types serve as discriminants. The widening-narrowing duality reflects TypeScript's gradual typing philosophy—mutable variables receive conservative widened types that permit flexibility, while const bindings and contextual positions receive precise narrowed types that maximize safety.
