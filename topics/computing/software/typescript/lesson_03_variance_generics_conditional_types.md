# Lesson 3: Variance, Generics, Conditional Types

## 1. First-Principles Intuition & Invariants

The type systems of modern programming languages exist to prove theorems about program behavior at compile time, transforming runtime crashes into static rejections before execution begins. TypeScript's structural type system extends JavaScript with a sophisticated layer of compile-time verification, but unlike nominal systems that rely on explicit inheritance declarations, TypeScript reasons about assignability through shape compatibility. This structural foundation leads to subtle yet profound implications when we introduce parametric polymorphism through generics and examine how type parameters behave under substitution.

At the heart of generic type reasoning lies the concept of variance, a property that describes how subtyping relationships propagate through type constructors. When we declare a generic type `Box<T>`, we create a type-level function that maps input types to output types. The critical question becomes: if `Dog` is a subtype of `Animal`, what is the relationship between `Box<Dog>` and `Box<Animal>`? The answer depends entirely on how `Box` uses its type parameter `T`. If `Box` only produces values of type `T` (as in a read-only container), then `Box<Dog>` should be assignable to `Box<Animal>` through covariance. If `Box` only consumes values of type `T` (as in a write-only sink), then the relationship inverts through contravariance, making `Box<Animal>` assignable to `Box<Dog>`. If `Box` both produces and consumes `T`, no safe substitution exists, and the type constructor becomes invariant.

These variance rules emerge from the principle of substitutability articulated in Barbara Liskov's seminal work on behavioral subtyping. A program fragment expecting a `Box<Animal>` must continue to function correctly when given a `Box<Dog>`, but only if the operations performed on that box respect the actual runtime types involved. Reading operations are safe under covariance because a function expecting an `Animal` can safely receive a `Dog`, which carries all the capabilities of its supertype. Writing operations require contravariance because a box that accepts any `Animal` can safely masquerade as a box that accepts only `Dog` instances, since the caller's promise to provide only dogs is a stronger guarantee than the box requires.

TypeScript models these relationships through its structural assignability algorithm, which recursively walks type structures comparing each position according to variance rules determined by usage. Function types introduce the most counterintuitive variance behavior: function parameters are contravariant while return types are covariant. This inversion stems from the perspective flip inherent in function types. When we substitute one function for another, the replacement must accept a broader range of inputs (contravariance in parameters) while promising to return a more specific output (covariance in return position). The type system encodes this through bidirectional checking, comparing parameter types in reverse subtype order while comparing return types in forward order.

Generic constraints allow us to bound the universe of types that may instantiate a type parameter, transforming universally quantified polymorphism into bounded quantification. When we write `<T extends Animal>`, we restrict `T` to be any subtype of `Animal`, enabling the compiler to assume that methods and properties of `Animal` will be available on values of type `T`. This constraint propagates through nested generic instantiations, creating a lattice of type relationships that the compiler traverses during type inference and checking. The constraint bound becomes the upper bound in the subtyping lattice, establishing a ceiling through which the type parameter cannot pass during substitution.

Conditional types introduce a form of dependent typing to TypeScript's type level, allowing types to be computed based on runtime-unavailable information about other types. The syntax `T extends U ? X : Y` creates a type-level conditional that resolves to `X` when `T` is assignable to `U` and `Y` otherwise. These conditionals execute during type checking, not at runtime, operating in the metalanguage of the type system itself. When a conditional type encounters a naked type parameter in the checked position, distribution occurs: the conditional distributes over union types, evaluating the conditional for each union member independently and collecting the results into a new union. This distributive property transforms conditional types into powerful type-level mapping operations, enabling the construction of sophisticated type transformations through purely declarative specifications.

Mapped types provide a mechanism for transforming the shape of object types through iteration over their property keys. The syntax `{ [K in keyof T]: Transform<T[K]> }` creates a homomorphic mapped type that preserves the modifiers and structure of the source type `T` while transforming each property type through `Transform`. The type system tracks whether mapped types are homomorphic, preserving optional and readonly modifiers only for homomorphic maps. Non-homomorphic maps that introduce new keys or transform the key type itself discard these modifiers, requiring explicit reapplication if preservation is desired.

Template literal types extend this transformation capability to string literal types, introducing pattern matching and concatenation operations at the type level. The type `${A}-${B}` constructs new string literal types through concatenation, while the intrinsic types `Uppercase`, `Lowercase`, `Capitalize`, and `Uncapitalize` provide string transformations. These primitives enable the construction of discriminated unions over string patterns, typed routing tables, and other string-based protocols that previously required runtime validation.

The interplay between these mechanisms creates a Turing-complete type system in which arbitrarily complex computations can be encoded as type-level programs. While this power enables precise modeling of sophisticated APIs and domain invariants, it also introduces the possibility of infinite type expansion, non-terminating type checking, and performance pathologies in the compiler. The TypeScript compiler implements depth limits and instantiation caches to bound these computations, trading theoretical completeness for practical tractability.

## 2. Core Architecture & Mechanics

The TypeScript compiler represents types internally as objects in an immutable type graph, with each type node carrying metadata about its structure, variance, and relationships to other types. Generic types are represented as `GenericType` nodes containing a target type and a list of type arguments, with instantiation lazily cached in a global map keyed by the combination of target and arguments. This caching strategy ensures that `Array<number>` produces the same type object regardless of where it appears in the program, enabling efficient reference equality checks during type comparison.

Variance computation occurs through a process called variance annotation, in which the compiler analyzes how each type parameter appears in the structure of its containing type. For each occurrence of a type parameter, the compiler tracks whether it appears in a covariant position (return types, property types in read-only positions), contravariant position (parameter types), or invariant position (property types in mutable positions). The overall variance of a type parameter is the intersection of all these occurrences: if a parameter appears in both covariant and contravariant positions, it becomes invariant. This analysis happens once per generic declaration and the result is cached, avoiding repeated traversals during type checking.

```typescript
// Variance analysis walkthrough
type Producer<T> = {
    produce: () => T;  // T appears in covariant position (return)
};

type Consumer<T> = {
    consume: (value: T) => void;  // T appears in contravariant position (parameter)
};

type Box<T> = {
    value: T;  // T appears in invariant position (mutable property)
    get: () => T;  // Also covariant
    set: (val: T) => void;  // Also contravariant
};

// Compiler marks Producer<T> as covariant in T
// Compiler marks Consumer<T> as contravariant in T  
// Compiler marks Box<T> as invariant in T
```

Function type checking implements parameter contravariance through bidirectional comparison. When checking whether function type `(x: A) => R` is assignable to `(y: B) => S`, the compiler first checks whether `B` is assignable to `A` (reverse order for parameters), then checks whether `R` is assignable to `S` (forward order for return). This bidirectional flow ensures that the substituted function can accept all arguments the original could have received while producing results compatible with the original's return type.

```typescript
class Animal { 
    name: string;
    constructor(name: string) { this.name = name; }
}

class Dog extends Animal { 
    breed: string;
    constructor(name: string, breed: string) {
        super(name);
        this.breed = breed;
    }
}

class Cat extends Animal {
    indoor: boolean;
    constructor(name: string, indoor: boolean) {
        super(name);
        this.indoor = indoor;
    }
}

// Parameter contravariance in action
type AnimalHandler = (animal: Animal) => void;
type DogHandler = (dog: Dog) => void;

const handleAnimal: AnimalHandler = (animal) => {
    console.log(animal.name);
};

const handleDog: DogHandler = (dog) => {
    console.log(`${dog.name} is a ${dog.breed}`);
};

// Valid: AnimalHandler accepts broader input, safe to use where DogHandler expected
const dogProcessor: DogHandler = handleAnimal;

// Invalid: DogHandler requires specific Dog, cannot substitute for broader AnimalHandler
// const animalProcessor: AnimalHandler = handleDog;  // Error

// Demonstrates why: handleDog would try to access breed on a Cat
const processPet = (handler: AnimalHandler) => {
    handler(new Cat("Whiskers", true));
};

// This would crash if we could pass handleDog
// processPet(handleDog);  // Correctly rejected by type system
```

The mechanical heart of contravariance lies in perspective inversion. From the caller's viewpoint, a function accepting `Animal` is safer than one requiring `Dog` because the caller might provide any animal. From the implementer's viewpoint, receiving a `Dog` is more restrictive, but this restriction is invisible to the caller who holds the broader `Animal` reference. The type system resolves this mismatch by making parameter types contravariant, aligning the implementer's restriction with the caller's guarantee.

Generic constraint checking operates through recursive instantiation bounded by the constraint. When the compiler encounters `<T extends Animal>` and later sees `T` used in expression position, it substitutes the constraint bound `Animal` as the type of that expression, enabling property access and method calls valid on `Animal`. During type parameter inference, the compiler collects constraints from all usage sites and computes the greatest lower bound that satisfies all constraints simultaneously. If no such bound exists, inference fails and the compiler reports an error.

```typescript
// Constraint mechanics and inference
function findOldest<T extends { age: number }>(items: T[]): T | undefined {
    if (items.length === 0) return undefined;
    
    // Compiler knows T has age property due to constraint
    return items.reduce((oldest, current) => 
        current.age > oldest.age ? current : oldest
    );
}

interface Person {
    name: string;
    age: number;
}

interface Dog {
    breed: string;
    age: number;
}

// Inference: T = Person (satisfies constraint)
const oldestPerson = findOldest([
    { name: "Alice", age: 30 },
    { name: "Bob", age: 45 }
]);

// Inference: T = Dog (satisfies constraint)
const oldestDog = findOldest([
    { breed: "Labrador", age: 7 },
    { breed: "Poodle", age: 5 }
]);

// Multiple constraints through intersection
function logAndReturn<T extends { toString(): string } & { length: number }>(value: T): T {
    console.log(`Value: ${value.toString()}, Length: ${value.length}`);
    return value;
}

// Inference finds intersection bound
logAndReturn([1, 2, 3]);  // T = number[] satisfies both constraints
logAndReturn("hello");     // T = string satisfies both constraints
```

Conditional type resolution proceeds through a multi-phase algorithm that handles naked type parameters, distributive instantiation, and recursive resolution. When the compiler encounters `T extends U ? X : Y` where `T` is a naked type parameter, it first checks whether `T` is currently constrained. If unconstrained, the conditional remains unresolved and distribution occurs during instantiation. If constrained, the compiler checks the constraint against `U`: if the constraint definitely extends `U`, the conditional resolves to `X`; if it definitely does not, resolution yields `Y`; if the relationship is indeterminate, the conditional remains pending.

Distribution over unions transforms `(A | B) extends U ? X : Y` into `(A extends U ? X : Y) | (B extends U ? X : Y)`, evaluating the conditional independently for each union member. This distributive property enables type-level filtering and mapping operations that would otherwise require complex recursive type definitions.

```typescript
// Distributive conditional type mechanics
type ExtractStrings<T> = T extends string ? T : never;

// Distribution occurs: evaluates separately for each union member
type Test1 = ExtractStrings<string | number | boolean>;
// Resolves to: (string extends string ? string : never) | 
//              (number extends string ? number : never) |
//              (boolean extends string ? boolean : never)
// Result: string | never | never → string

// Non-distributive conditional (tuple wrapper prevents distribution)
type ExtractStringsNonDist<T> = [T] extends [string] ? T : never;
type Test2 = ExtractStringsNonDist<string | number>;
// Evaluates once: [string | number] extends [string] ? ... : never
// Result: never (union does not extend string)

// Practical application: filtering null/undefined
type NonNullable<T> = T extends null | undefined ? never : T;
type SafeString = NonNullable<string | null | undefined>;  // string

// Extracting function return types
type ReturnType<T> = T extends (...args: any[]) => infer R ? R : never;

type Func = (x: number) => string;
type Result = ReturnType<Func>;  // string

// Conditional with inference
type UnpackArray<T> = T extends (infer U)[] ? U : T;
type NumArray = number[];
type Unpacked = UnpackArray<NumArray>;  // number
```

The `infer` keyword introduces type-level variable binding within conditional types, enabling pattern matching against complex type structures. When the compiler evaluates `T extends SomePattern<infer U>`, it attempts to match `T` against the pattern, binding any matched portions to the type variable `U`. This variable is then available in the true branch of the conditional. The compiler maintains a context stack of inferred type variables, with each conditional creating a new scope for its inferred bindings.

Mapped types execute through iteration over a source type's properties, transforming each property type according to a specified mapping function. The compiler represents mapped types as `MappedType` nodes containing a type parameter declaration, a constraint expression (the result of `keyof T`), and a template type that references the type parameter. During instantiation, the compiler resolves the constraint to a union of string literal types, then iterates over each literal, binding it to the type parameter and evaluating the template type.

```typescript
// Mapped type mechanics
type ReadonlyRecord<T> = {
    readonly [K in keyof T]: T[K];
};

interface Mutable {
    x: number;
    y: string;
}

type Immutable = ReadonlyRecord<Mutable>;
// Expands to: { readonly x: number; readonly y: string; }

// Conditional transformation within mapped type
type NullableProperties<T> = {
    [K in keyof T]: T[K] | null;
};

type MaybeNull = NullableProperties<{ a: number; b: string }>;
// Result: { a: number | null; b: string | null; }

// Key remapping with template literals
type Getters<T> = {
    [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};

interface State {
    name: string;
    count: number;
}

type StateGetters = Getters<State>;
// Expands to: { getName: () => string; getCount: () => number; }

// Filtering keys through conditional type
type PickByType<T, U> = {
    [K in keyof T as T[K] extends U ? K : never]: T[K];
};

interface Mixed {
    id: number;
    name: string;
    age: number;
    active: boolean;
}

type NumericFields = PickByType<Mixed, number>;
// Result: { id: number; age: number; }
```

Template literal types construct new string literal types through concatenation and transformation of existing literal types. The compiler maintains intrinsic type mappings for `Uppercase`, `Lowercase`, `Capitalize`, and `Uncapitalize`, which it applies during template literal resolution. When a template literal contains a union type in any substitution position, the compiler distributes over that union, producing a union of all possible string combinations.

```typescript
// Template literal type mechanics
type EventName<T extends string> = `on${Capitalize<T>}`;

type ClickEvent = EventName<"click">;  // "onClick"
type HoverEvent = EventName<"hover">;  // "onHover"

// Distribution over unions
type InputEvents = "focus" | "blur" | "change";
type InputHandlers = EventName<InputEvents>;
// Resolves to: "onFocus" | "onBlur" | "onChange"

// Pattern extraction through inference
type ExtractRouteParams<T extends string> = 
    T extends `${infer Start}/api/${infer Param}/${infer End}` 
        ? Param 
        : never;

type UserIdParam = ExtractRouteParams<"/app/api/users/list">;  // "users"

// Building type-safe route handlers
type HTTPMethod = "GET" | "POST" | "PUT" | "DELETE";
type Endpoint = "users" | "posts" | "comments";
type Route = `${HTTPMethod} /${Endpoint}`;

type ValidRoute = Route;
// Expands to: "GET /users" | "POST /users" | "PUT /users" | ... (12 combinations)

// Recursive template literal type for path building
type PathBuilder<T, Prefix extends string = ""> = {
    [K in keyof T]: T[K] extends object 
        ? PathBuilder<T[K], `${Prefix}${string & K}.`>
        : `${Prefix}${string & K}`;
}[keyof T];

interface Config {
    database: {
        host: string;
        port: number;
    };
    cache: {
        ttl: number;
    };
}

type ConfigPath = PathBuilder<Config>;
// Result: "database.host" | "database.port" | "cache.ttl"
```

The compiler's type checker maintains an instantiation cache keyed by generic type identity and type argument tuple, ensuring that repeated instantiations of `Array<number>` return the same type object. This cache operates at the type level, distinct from the symbol table that tracks runtime values. When the compiler encounters a generic type reference, it first normalizes the type arguments, then performs a cache lookup using the normalized representation. Cache hits avoid redundant type construction and enable efficient reference equality checks during type comparison.

Recursive conditional types enable sophisticated type-level computation but require careful depth limiting to prevent infinite expansion. The TypeScript compiler implements a recursion depth counter that increments on each conditional type instantiation and decrements on exit. When this counter exceeds a threshold (currently fifty levels), the compiler terminates resolution and reports an error. This limit trades completeness for termination, as some theoretically valid but deeply recursive type computations may exceed the bound.

```typescript
// Recursive conditional type for flattening nested arrays
type Flatten<T> = T extends (infer U)[]
    ? Flatten<U>
    : T;

type Nested = number[][][];
type Flat = Flatten<Nested>;  // number

// Recursive type with accumulator pattern
type Join<T extends string[], Separator extends string = ","> = 
    T extends [infer First extends string, ...infer Rest extends string[]]
        ? Rest extends []
            ? First
            : `${First}${Separator}${Join<Rest, Separator>}`
        : "";

type CSV = Join<["a", "b", "c"], ",">;  // "a,b,c"

// Deep readonly implementation
type DeepReadonly<T> = {
    readonly [K in keyof T]: T[K] extends object
        ? T[K] extends Function
            ? T[K]
            : DeepReadonly<T[K]>
        : T[K];
};

interface NestedStructure {
    user: {
        profile: {
            name: string;
            age: number;
        };
    };
    settings: {
        theme: string;
    };
}

type ImmutableStructure = DeepReadonly<NestedStructure>;
// All properties recursively marked readonly
```

## 3. High-Performance Optimization & Failure Modes

Type checking performance in TypeScript scales with the complexity of the type graph, the depth of generic instantiation, and the number of structural comparisons performed. Large codebases with deeply nested generic types can trigger pathological behavior in the type checker, leading to exponential blowup in instantiation count or comparison complexity. The most common performance antipattern involves excessive use of conditional types with broad unions, which triggers distributive evaluation for every union member, multiplying the work required at each recursive level.

Optimization begins with strategic use of type aliases to introduce memoization boundaries. When the compiler encounters a type alias, it resolves the alias once and caches the result, avoiding redundant recomputation. By extracting complex conditional types into named aliases, we transform repeated inline expansion into cached lookups. This technique proves particularly effective for recursive types, where aliasing intermediate results prevents redundant traversal of previously computed branches.

```typescript
// Inefficient: repeated inline conditional expansion
type BadExtract<T> = T extends { kind: "a"; value: infer U }
    ? U
    : T extends { kind: "b"; value: infer V }
        ? V
        : T extends { kind: "c"; value: infer W }
            ? W
            : never;

// Optimized: factored through intermediate types
type ExtractKind<T, K extends string> = T extends { kind: K; value: infer U }
    ? U
    : never;

type GoodExtract<T> = ExtractKind<T, "a"> | ExtractKind<T, "b"> | ExtractKind<T, "c">;

// Performance scaling comparison
type LargeUnion = { kind: "a"; value: number }
    | { kind: "b"; value: string }
    | { kind: "c"; value: boolean }
    | { kind: "d"; value: Date }
    | { kind: "e"; value: RegExp }
    | { kind: "f"; value: Error }
    | { kind: "g"; value: Map<string, unknown> }
    | { kind: "h"; value: Set<number> };

// BadExtract instantiated on LargeUnion requires O(n²) comparisons
// GoodExtract instantiated on LargeUnion requires O(n) comparisons
```

Union types degrade type checker performance when used in structural comparison contexts, as the checker must compare each union member against the target type. This effect compounds in nested structures where unions appear at multiple levels. Refactoring through discriminated unions with literal type tags enables the checker to use fast path discrimination, short-circuiting structural comparison when the discriminant differs. The transformation from structural comparison to discriminant checking changes algorithmic complexity from linear in the number of union members to constant time per member.

```typescript
// Inefficient: structural comparison across large union
type SlowHandler = (
    event: 
        | { type: "click"; x: number; y: number }
        | { type: "keypress"; key: string; modifiers: string[] }
        | { type: "scroll"; deltaX: number; deltaY: number }
        | { type: "resize"; width: number; height: number }
) => void;

// Optimized: discriminated union with literal type narrowing
type Event = 
    | { type: "click"; x: number; y: number }
    | { type: "keypress"; key: string; modifiers: string[] }
    | { type: "scroll"; deltaX: number; deltaY: number }
    | { type: "resize"; width: number; height: number };

type FastHandler = (event: Event) => void;

// Within function body, narrowing is O(1) through discriminant check
function handleEvent(event: Event): void {
    switch (event.type) {  // Fast discriminant branch
        case "click":
            console.log(`Click at ${event.x}, ${event.y}`);
            break;
        case "keypress":
            console.log(`Key ${event.key} pressed`);
            break;
        case "scroll":
            console.log(`Scrolled by ${event.deltaX}, ${event.deltaY}`);
            break;
        case "resize":
            console.log(`Resized to ${event.width}x${event.height}`);
            break;
    }
}
```

Generic constraint propagation can lead to cascading inference failures when constraints form dependency chains that the compiler cannot resolve in a single pass. The type checker uses a fixed-point iteration algorithm to resolve constraint dependencies, but this algorithm may fail to converge if cycles exist or if constraints mutually exclude each other. Explicit type annotations at intermediate points break these cycles by providing the compiler with concrete instantiation targets, eliminating the need for inference across the boundary.

```typescript
// Problematic constraint chain
function complexChain<A, B extends A[], C extends B[number]>(
    values: B,
    predicate: (item: C) => boolean
): C[] {
    return values.filter(predicate) as C[];  // Requires cast due to inference limits
}

// Improved: explicit intermediate type
function betterChain<T>(
    values: T[],
    predicate: (item: T) => boolean
): T[] {
    return values.filter(predicate);
}

// Usage with explicit instantiation
interface Item {
    id: number;
    name: string;
}

const items: Item[] = [
    { id: 1, name: "first" },
    { id: 2, name: "second" }
];

// Clear inference path
const filtered = betterChain(items, item => item.id > 1);
```

Conditional type distribution over deeply nested unions creates combinatorial explosion in the type space. When multiple conditional types distribute over unions independently, the resulting type is the Cartesian product of all distributions, growing exponentially with nesting depth. Avoiding distribution through tuple wrapping or constraining union size at API boundaries prevents this blowup. When distribution is necessary, factoring the computation into multiple stages with intermediate aliases bounds the expansion at each level.

```typescript
// Dangerous: nested distributive conditionals
type DistributeNested<T> = T extends any
    ? T extends string
        ? `string:${T}`
        : T extends number
            ? `number:${T}`
            : never
    : never;

type SmallUnion = "a" | "b" | 1 | 2;
type Result1 = DistributeNested<SmallUnion>;  // Manageable

type LargeUnion = "a" | "b" | "c" | "d" | 1 | 2 | 3 | 4 | 5 | 6;
// type Result2 = DistributeNested<LargeUnion>;  // Potential slowdown

// Safer: non-distributive with explicit handling
type SafeFormat<T> = [T] extends [string]
    ? `string:${T & string}`
    : [T] extends [number]
        ? `number:${T & number}`
        : never;

type Formatted<T> = T extends any ? SafeFormat<T> : never;
type Result3 = Formatted<LargeUnion>;  // Better performance
```

Recursive conditional types must include proper base cases to prevent infinite instantiation. The compiler detects simple cycles through structural identity checks, but complex recursive patterns may escape detection until the depth limit triggers. Designing recursive types with explicit termination conditions ensures predictable behavior and clearer error messages when the base case is not reached.

```typescript
// Missing base case leads to depth limit error
type BadRecursive<T> = {
    value: T;
    next: BadRecursive<T>;  // No termination condition
};

// Proper base case with union termination
type GoodRecursive<T> = {
    value: T;
    next: GoodRecursive<T> | null;
};

// Recursive type with explicit depth bound
type BoundedRecursive<T, Depth extends number = 5> = {
    value: T;
    next: Depth extends 0 ? null : BoundedRecursive<T, [-1, 0, 1, 2, 3, 4][Depth]> | null;
};

// Tail-recursive accumulator pattern for efficiency
type TailRecursiveJoin<
    T extends string[],
    Acc extends string = "",
    Sep extends string = ","
> = T extends [infer First extends string, ...infer Rest extends string[]]
    ? TailRecursiveJoin<Rest, `${Acc}${Acc extends "" ? "" : Sep}${First}`, Sep>
    : Acc;

type JoinedPath = TailRecursiveJoin<["a", "b", "c", "d"], "", "/">;  // "a/b/c/d"
```

Mapped types over large interfaces incur cost proportional to the number of properties being mapped. When applying transformations that require conditional type evaluation per property, the cost multiplies. Introducing intermediate types that operate on property value types rather than entire object structures amortizes this cost by enabling the compiler to cache the property transformation independent of the containing object.

```typescript
// Expensive: conditional evaluation per property
type SlowTransform<T> = {
    [K in keyof T]: T[K] extends string
        ? T[K] | null
        : T[K] extends number
            ? T[K] | undefined
            : T[K];
};

// Optimized: factored property value transformation
type TransformValue<V> = V extends string
    ? V | null
    : V extends number
        ? V | undefined
        : V;

type FastTransform<T> = {
    [K in keyof T]: TransformValue<T[K]>;
};

// Benchmark interface
interface LargeInterface {
    prop1: string; prop2: number; prop3: boolean;
    prop4: string; prop5: number; prop6: boolean;
    prop7: string; prop8: number; prop9: boolean;
    prop10: string; prop11: number; prop12: boolean;
    // ... many more properties
}

// FastTransform computes TransformValue<T> once per unique property type
// SlowTransform re-evaluates conditional for every property occurrence
```

Template literal types with multiple union substitution positions generate the full Cartesian product of all unions involved. A template with two unions of size `n` and `m` produces `n × m` distinct string literal types. This expansion is often necessary for type safety but can be controlled by splitting complex templates into multiple stages or by using conditional types to prune invalid combinations before template expansion.

```typescript
// Explosive template expansion
type Method = "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
type Resource = "users" | "posts" | "comments" | "likes";
type Route = `${Method} /${Resource}`;  // 5 × 4 = 20 combinations

// Controlled through conditional filtering
type SafeMethod<M extends Method, R extends Resource> = 
    M extends "DELETE" 
        ? R extends "likes" 
            ? never 
            : `${M} /${R}`
        : `${M} /${R}`;

type FilteredRoute = Method extends infer M extends Method
    ? Resource extends infer R extends Resource
        ? SafeMethod<M, R>
        : never
    : never;
// Eliminates "DELETE /likes" from type space before full expansion

// Staged template construction
type MethodPrefix<M extends Method> = `${M} /`;
type ResourcePath<R extends Resource> = R;
type StagedRoute<M extends Method, R extends Resource> = `${MethodPrefix<M>}${ResourcePath<R>}`;
// Provides same result with clearer decomposition
```

The TypeScript compiler exposes performance tracing through the `--extendedDiagnostics` flag, which reports time spent in each phase of compilation including type checking, type resolution, and module loading. For pathological type performance issues, the `--generateTrace` flag produces a detailed event trace suitable for analysis in Chrome's trace viewer. These traces reveal hot paths in the type checker, identifying specific types or files responsible for disproportionate checking time. Optimization efforts should focus on these hot paths, as micro-optimizations elsewhere yield diminishing returns.

Variance errors manifest when attempting to assign a value of one generic type to a variable of another generic type where the variance rules prohibit the assignment. The error message reports the specific variance violation but often omits the chain of reasoning that led to the variance requirement. Reading the full error context reveals which usage pattern triggered invariance, enabling targeted refactoring to restore covariance or contravariance as desired.

```typescript
// Variance violation example
interface Container<T> {
    get(): T;
    set(value: T): void;  // Presence of parameter forces invariance
}

class Animal {
    name: string;
    constructor(name: string) { this.name = name; }
}

class Dog extends Animal {
    bark(): void { console.log("Woof!"); }
}

const dogContainer: Container<Dog> = {
    get: () => new Dog("Rex"),
    set: (dog: Dog) => console.log(`Set ${dog.name}`)
};

// Error: Container<Dog> not assignable to Container<Animal>
// const animalContainer: Container<Animal> = dogContainer;

// Fixing through readonly split
interface ReadonlyContainer<out T> {  // 'out' enforces covariance
    get(): T;
}

interface WriteableContainer<in T> {  // 'in' enforces contravariance
    set(value: T): void;
}

// Now covariance works for readonly container
const readonlyDogContainer: ReadonlyContainer<Dog> = {
    get: () => new Dog("Rex")
};

const readonlyAnimalContainer: ReadonlyContainer<Animal> = readonlyDogContainer;  // Valid

// And contravariance works for writeable container
const writeableAnimalContainer: WriteableContainer<Animal> = {
    set: (animal: Animal) => console.log(`Set ${animal.name}`)
};

const writeableDogContainer: WriteableContainer<Dog> = writeableAnimalContainer;  // Valid
```

Generic constraints that are too restrictive prevent valid instantiations while overly permissive constraints allow invalid operations. Striking the right balance requires understanding the minimum set of capabilities required by the generic function body. Using intersection types to combine multiple interface constraints enables precise specification without introducing artificial nominal types.

```typescript
// Too restrictive: requires specific class
function processUser<T extends User>(user: T): string {
    return `User: ${user.name}, ${user.email}`;
}

class User {
    constructor(public name: string, public email: string) {}
}

// Cannot process plain objects, even if structurally compatible
// processUser({ name: "Alice", email: "alice@example.com" });  // Error

// Right constraint: structural interface
function processUserStructural<T extends { name: string; email: string }>(
    user: T
): string {
    return `User: ${user.name}, ${user.email}`;
}

// Works with any compatible structure
processUserStructural({ name: "Alice", email: "alice@example.com" });
processUserStructural(new User("Bob", "bob@example.com"));

// Multiple constraints through intersection
function logAndValidate<T extends { toString(): string } & { validate(): boolean }>(
    value: T
): void {
    if (value.validate()) {
        console.log(value.toString());
    }
}

// Generic constraint with conditional type
type EnsureArray<T> = T extends any[] ? T : T[];

function processList<T>(items: EnsureArray<T>): void {
    // items guaranteed to be an array type
    console.log(`Processing ${items.length} items`);
}
```

Conditional type resolution can produce `never` unexpectedly when the extends check fails for all branches of a distributed union. This often indicates a logical error in the conditional structure or a misunderstanding of distributive behavior. Wrapping the checked type in a tuple disables distribution, changing the resolution behavior and often revealing the underlying issue.

```typescript
// Unexpected never due to distribution
type ExtractNumbers<T> = T extends number ? T : never;
type MixedUnion = string | boolean;
type Result = ExtractNumbers<MixedUnion>;  // never (no numbers in union)

// Intended: check if union contains numbers
type ContainsNumber<T> = [T] extends [infer U extends number]
    ? U
    : never;

// Or use separate existence check
type HasNumber<T> = T extends any ? (number extends T ? true : false) : false;
type Check = HasNumber<string | number>;  // boolean (union of true | false)

// Proper filtering with distribution
type ExtractByType<T, U> = T extends U ? T : never;
type Numbers = ExtractByType<string | number | boolean, number>;  // number
```

Understanding these mechanical and optimization principles enables construction of type systems that remain tractable as codebases scale. The TypeScript type system provides extraordinary expressive power through its combination of structural typing, generics, variance, conditional types, and template literals. Wielding this power effectively requires respecting the algorithmic complexity hiding behind declarative syntax and structuring types to align with the compiler's checking strategy rather than working against it. The result is a type layer that proves increasingly sophisticated invariants about program behavior while compiling in reasonable time, delivering the core promise of static typing: confidence without runtime overhead.
