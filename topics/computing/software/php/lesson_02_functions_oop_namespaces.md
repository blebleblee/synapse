# Lesson 2: Functions, Object-Oriented Programming, Namespaces

## 1. First-Principles Intuition & Invariants

PHP's execution model is a two-phase pipeline: the Zend Compiler transforms source text into a linear sequence of opcodes (`zend_op` structs packed into a `zend_op_array`), and the Zend Virtual Machine interprets those opcodes on a call stack of `zend_execute_data` frames. Every function you define—whether a global function, a class method, or an anonymous closure—compiles down to the same fundamental data structure: an op_array with a pointer to its literal table, its argument count, its compiled opcode sequence, and metadata describing its binding scope. Understanding this invariant collapses the apparent differences between procedural functions, class methods, and closures into a single mechanical framework. They are all executable opcode sequences with varying degrees of captured runtime context.

The critical distinction that a compiler engineer must internalize is how the Zend Engine resolves the relationship between a call site and its target op_array at runtime. Global functions are resolved at compile time: the compiler emits a `ZEND_DO_FCALL` or `ZEND_DO_ICALL` (internal call) opcode with a direct pointer to the target function's op_array, because global function definitions are hoisted during the compilation pass before any code executes. Class methods, by contrast, cannot be fully resolved until the engine knows the concrete class of the object receiving the message, which in PHP's dynamically typed world may vary per call site. Closures add a further layer: they are objects of the internal `Closure` class, but the engine stores a back-pointer to the compiled op_array and separately tracks a bound scope and an optional bound `$this` reference, enabling lexical capturing through `use` clauses that compile as explicit variable binding instructions.

Late static binding is perhaps the most conceptually subtle feature in PHP's object model, and it exists precisely because PHP's inheritance resolution is asymmetric. When a parent class method calls a static method using `self::`, the compiler binds the call to the class where the method is textually defined, not the class of the runtime object. This is an early-binding decision made at compile time. The `static::` keyword introduces a runtime indirection: the engine reads the actual class name from the current execution frame's `called_scope` field, which is set by the originating call and propagated through the frame chain. This is not polymorphism in the virtual-dispatch sense (that is `LateBinding`/`zend_class_entry` resolution on instance methods), but rather a delayed class-name binding that defers the self-reference to the class that the caller actually instantiated. The distinction matters enormously for framework design: base class factory methods, active record patterns, and ORM hierarchy traversal all depend on `static::` to ensure that inheritance chains produce the correct concrete class rather than the base class.

Namespaces in PHP are a compile-time mapping layer, not a runtime isolation mechanism. The compiler resolves namespace-qualified names to fully-qualified names (FQNs) during compilation, applying import rules and fallback semantics to produce a canonical string identifier. At runtime, class loading is a string-based lookup into a hash table (`EG(class_table)`), keyed by the lowercase FQN. Autoloading is simply a hook: when a class lookup misses, the engine invokes the registered autoloader functions in sequence, passing the missing class name as a string, and retries the lookup. PSR-4 is a community convention layered on top of this mechanism, mapping namespace prefixes to filesystem paths, but the engine itself has no awareness of PSR-4—it only knows about the `spl_autoload_register` call stack and the class table.

The central invariant governing all of PHP's function and method dispatch is that the engine never performs structural vtable lookups in the C++ sense. Instance method dispatch uses a hash table on the `zend_class_entry` keyed by the lowercase method name, resolved at the first call site and cached in the runtime cache (a per-opcode memoization slot). Subsequent calls to the same method on objects of the same class skip the hash lookup entirely, reading the cached function pointer directly. This design trades a slightly higher first-call cost for zero-cost repeated dispatch, which is the common path in long-running PHP applications.

## 2. Core Architecture & Mechanics

### Function Compilation and the Op Array

When the Zend Compiler encounters a `function` declaration, it allocates a new `zend_op_array`, compiles the function body into it, and registers the function in the global function table (`CG(function_table)`). The op_array carries the argument count, the list of compiled local variables (including temporary values), a literal constant table, and the opcode buffer itself. Each opcode is a fixed-size `zend_op` struct containing an opcode number, up to three operands (which can be constants, variable references, or intermediate results), and an extended value for opcode-specific flags.

The following complete, executable example demonstrates the full lifecycle of function definition, parameter handling with all of PHP's modes, and return type enforcement. It is a self-contained script that can be executed directly with `php`:

```php
<?php

declare(strict_types=1);

/**
 * Demonstrates PHP's complete parameter handling model: positional,
 * variadic, named, by-reference, and default values, along with
 * union, intersection, and return type enforcement.
 */

function buildPipeline(
    string $name,
    int $priority = 0,
    array &$stages = [],
    string ...$filters
): array {
    // $stages is passed by reference; modifications persist to the caller.
    $stages[] = "stage:" . $name;

    // $filters is a variadic parameter collected into an array.
    $resolvedFilters = array_map(
        static fn(string $f): string => "filter:{$f}",
        $filters
    );

    return [
        'name' => $name,
        'priority' => $priority,
        'stage_count' => count($stages),
        'filters' => $resolvedFilters,
    ];
}

// --- Execution demonstrating all parameter modes ---

$stagesRef = ['init'];

// Named arguments allow skipping the $priority default entirely
// while passing a variadic spread of filters.
$result = buildPipeline(
    name: 'ingest',
    stages: $stagesRef,
    filters: ...['validate', 'transform', 'enrich']
);

var_dump($result);
var_dump($stagesRef); // Mutated by reference: ['init', 'stage:ingest']
```

The `declare(strict_types=1)` directive at the top of the file is not a style preference—it fundamentally changes the coercion semantics at call sites within that file. Without strict mode, PHP applies implicit type coercion (string `"42"` becomes integer `42` when passed to an `int` parameter) following a permissive set of coercion rules. With strict mode enabled, the engine enforces exact type matches for scalar types at call sites defined in that file, throwing a `TypeError` on mismatch. The strictness is determined by the file containing the call site, not the file containing the function declaration, because type coercion is a property of the caller's expectations, not the callee's definition.

### Closures and Binding Semantics

A closure in PHP is an instance of the internal `Closure` class, but it is not a normal object. The engine stores the closure's op_array in a `zend_object` whose internal structure carries the compiled function pointer, the scope (the class in which the closure was textually defined, or `null` for a global closure), and an optional bound `$this` reference. The `use` clause compiles as explicit variable capture instructions: each captured variable is resolved at the point of closure creation, and a reference to the variable's value (or the variable slot itself, if captured by reference) is stored in the closure object's internal `used_variables` table.

The `Closure::bind` and `Closure::bindTo` methods allow re-binding the scope and `$this` pointer of an existing closure, which is the mechanism that powers frameworks like Laravel's macro system and PHPUnit's mock object property access. The following example demonstrates static closures, object-bound closures, scope rebinding, and the critical difference between capturing by value and by reference:

```php
<?php

declare(strict_types=1);

class ServiceContainer
{
    private string $secret = 'container-key';

    public function makeAccessor(): Closure
    {
        // A non-static closure defined inside a method
        // automatically captures $this and the class scope.
        return function (): string {
            return "Secret is: {$this->secret}";
        };
    }

    public function makeStaticAccessor(): Closure
    {
        // A static closure has no $this binding, but retains
        // the class scope, so it can access private static members.
        return static function (): string {
            return "Class scope: " . self::class;
        };
    }
}

class ExternalConsumer
{
    private string $secret = 'consumer-key';
}

$container = new ServiceContainer();
$closure = $container->makeAccessor();

// Normal invocation: uses the originally bound $this.
echo $closure() . "\n"; // Secret is: container-key

// Rebind to a different object and scope. The second argument
// sets the scope, which determines visibility for private/protected.
// Passing 'ExternalConsumer' as scope links the closure's self to
// that class, granting access to its private members.
$rebound = Closure::bind($closure, new ExternalConsumer(), ExternalConsumer::class);
echo $rebound() . "\n"; // Secret is: consumer-key

// --- By-value vs by-reference capture ---

$counter = 0;

// By value: captures the current value of $counter at closure creation.
$byValue = function () use ($counter) {
    return $counter;
};

// By reference: captures a reference to the $counter variable itself.
$byRef = function () use (&$counter) {
    $counter++;
};

$byValue();
$byRef();
$byRef();
echo $counter . "\n"; // 2 — $byRef mutated the original variable.
echo $byValue() . "\n"; // 0 — captured the original value before mutation.
```

### Class Mechanics, Inheritance, and Late Static Binding

PHP's class system is built on `zend_class_entry` structs, which serve as the runtime type descriptor for all instances. Each class entry holds a hash table of its own declared properties (not inherited ones), a hash table of its methods (which does include inherited methods, resolved at class linking time), a pointer to the parent class entry, a list of implemented interface entries, and the `ce_flags` bitmask that encodes whether the class is final, abstract, an interface, a trait, readonly, or anonymous.

When a class extends a parent, the engine performs a class linking pass at the moment the class is declared (which for autoloaded classes means at the moment the autoloader loads them). This pass copies parent method entries into the child's method table if the child does not override them, resolves property defaults, and validates interface contracts. Method override resolution is based on signature compatibility: the child method's parameter count, types, and return type must be contravariant in parameters and covariant in return type relative to the parent, enforced by `zend_verify_signature` during the linking pass.

Late static binding is implemented through the `called_scope` field on `zend_execute_data`. When you call `$childInstance->parentMethod()`, the execution frame's `called_scope` is set to `ChildClass`, even though the method's op_array was compiled in `ParentClass`. The `static::` keyword reads this field at runtime; `self::` ignores it and uses the scope class baked into the op_array at compile time. The following complete example demonstrates this in a realistic factory and registry pattern:

```php
<?php

declare(strict_types=1);

abstract class Model
{
    protected static string $table;
    protected array $attributes = [];

    final public function __construct(array $attributes = [])
    {
        $this->attributes = $attributes;
    }

    // self:: would bind $table resolution to Model, which has no $table.
    // static:: defers to the called_scope, resolving to the concrete subclass.
    public static function tableName(): string
    {
        return static::$table;
    }

    // The factory method pattern depends on late static binding to
    // instantiate the correct concrete class from a base class method.
    public static function create(array $attributes): static
    {
        // new static() instantiates called_scope, not self.
        return new static($attributes);
    }

    public function getAttribute(string $key): mixed
    {
        return $this->attributes[$key] ?? null;
    }
}

final class User extends Model
{
    protected static string $table = 'users';
}

final class Product extends Model
{
    protected static string $table = 'products';
}

// Late static binding in action:
echo User::tableName() . "\n";       // users
echo Product::tableName() . "\n";   // products

// Factory dispatch via new static():
$user = User::create(['id' => 1, 'name' => 'Alice']);
echo $user::class . "\n";            // User
echo $user->getAttribute('name') . "\n"; // Alice

$product = Product::create(['id' => 42, 'sku' => 'WIDGET']);
echo $product::class . "\n";         // Product
echo $product->getAttribute('sku') . "\n"; // WIDGET
```

### Interfaces, Traits, and Composition

Interfaces in PHP define a contract: a set of method signatures without implementations. A class implementing an interface must provide concrete methods matching every signature in the interface, and the class linking pass verifies this, throwing a fatal error if any method is missing or has an incompatible signature. The engine stores interface entries in the class's `interfaces` vector, and `instanceof` checks traverse this vector (and the parent chain) for a match.

Traits are PHP's mechanism for horizontal code reuse. At compile time, trait method bodies are not copied textually but rather inserted into the class's method table during the class linking pass. The `zend_do_inheritance_traits` function in the Zend Compiler walks each trait's method list and copies the `zend_op_array` pointers into the consuming class entry, applying conflict resolution rules from `insteadof` and `as` declarations. This means traits have no runtime existence: after linking, the consuming class's method table contains direct pointers to the trait's compiled op_arrays, and dispatch proceeds with no trait awareness at all.

The following example shows a complete trait composition with conflict resolution, abstract method requirements, and visibility modification:

```php
<?php

declare(strict_types=1);

trait Timestampable
{
    protected ?string $createdAt = null;
    protected ?string $updatedAt = null;

    public function setCreatedAt(?string $timestamp): void
    {
        $this->createdAt = $timestamp;
    }

    public function touch(): void
    {
        $this->updatedAt = date('Y-m-d H:i:s');
    }

    public function getUpdatedAt(): ?string
    {
        return $this->updatedAt;
    }
}

trait SoftDeletable
{
    protected bool $isDeleted = false;

    public function delete(): void
    {
        $this->isDeleted = true;
    }

    // Both traits could define a method that the consumer must disambiguate.
    public function restore(): void
    {
        $this->isDeleted = false;
    }
}

final class Document
{
    // Conflict resolution: if both traits defined delete(),
    // we would use `insteadof` to select one. Here we also
    // alias restore() to undelete() while keeping the original.
    use Timestampable, SoftDeletable {
        SoftDeletable::delete insteadof Timestampable;
        SoftDeletable::restore as undelete;
        Timestampable::touch as protected touchProtected;
    }

    public function __construct(
        private readonly string $title,
        private readonly string $content
    ) {}

    public function getTitle(): string
    {
        return $this->title;
    }

    public function isDeleted(): bool
    {
        return $this->isDeleted;
    }
}

$doc = new Document('Report', 'Body content');
$doc->setCreatedAt('2024-01-15 00:00:00');
$doc->touch();
echo $doc->getUpdatedAt() . "\n";

$doc->delete();
var_dump($doc->isDeleted()); // true

$doc->undelete(); // aliased method
var_dump($doc->isDeleted()); // false
```

### Magic Methods and Visibility

PHP defines a set of specially named methods that the engine intercepts at the opcode level. `__construct`, `__destruct`, `__get`, `__set`, `__isset`, `__unset`, `__call`, `__callStatic`, `__toString`, `__invoke`, `__serialize`, `__unserialize`, `__clone`, and `__sleep`/`__wakeup` are all dispatched by dedicated opcodes or internal checks rather than being called by user code directly. The `__get` and `__set` intercepts are triggered only when a property is inaccessible (undefined, protected/private from outside scope, or on a class using `__get`/`__set` without the property existing). This interception happens in the `ZEND_FETCH_OBJ` and `ZEND_ASSIGN_OBJ` opcode handlers, which check the property lookup result and, if a magic method exists on the class entry, redirect the operation.

The `readonly` property modifier, introduced in PHP 8.1, is enforced at the opcode level: the `ZEND_ASSIGN_OBJ` handler checks the property's flags and throws if a write is attempted outside the declaring class's constructor scope. Combined with constructor property promotion, this creates a terse immutable value object pattern:

```php
<?php

declare(strict_types=1);

final class Money
{
    // Constructor property promotion: each parameter becomes
    // a readonly property initialized directly. No manual
    // assignment boilerplate is required.
    public function __construct(
        public readonly int $amount,
        public readonly string $currency
    ) {}

    // Magic method: __toString allows implicit string conversion.
    public function __toString(): string
    {
        return "{$this->amount} {$this->currency}";
    }

    // Magic method: __get intercepts access to undefined properties.
    public function __get(string $name): mixed
    {
        return match ($name) {
            'formatted' => number_format($this->amount, 2) . ' ' . $this->currency,
            default => throw new \InvalidArgumentException("Unknown property: {$name}"),
        };
    }

    // __clone allows deep-copy logic when cloning an object.
    public function __clone()
    {
        // For immutable value objects, cloning is usually trivial,
        // but for objects holding resources or nested mutable state,
        // this is where you perform deep copies.
    }

    public function add(self $other): self
    {
        if ($other->currency !== $this->currency) {
            throw new \InvalidArgumentException('Currency mismatch');
        }
        return new self($this->amount + $other->amount, $this->currency);
    }
}

$price = new Money(1999, 'USD');
echo $price . "\n";              // 1999 USD (via __toString)
echo $price->formatted . "\n";  // 1,999.00 USD (via __get)

$total = $price->add(new Money(1, 'USD'));
echo $total . "\n";             // 2000 USD
```

### Namespaces, Resolution, and Autoloading

Namespace resolution in PHP follows a deterministic set of rules applied during compilation. A fully-qualified name (starting with `\`) is used as-is. A qualified name (containing `\` but not starting with one) is resolved relative to the current namespace, after checking for a matching `use` import. An unqualified name for a class triggers namespace fallback: the compiler first tries the current namespace, and if no such class exists at runtime, falls back to the global namespace. Unqualified function and constant calls have a runtime fallback to global scope by default, but this can be suppressed by importing the function or constant explicitly.

The autoloading mechanism is a chain of callbacks registered via `spl_autoload_register`. When the engine fails to find a class in `EG(class_table)`, it iterates through registered autoloaders, calling each with the fully-qualified class name (with leading backslash stripped). If an autoloader defines the class (by requiring the appropriate file), the engine retries the lookup and succeeds. PSR-4 is the standard convention: namespace segments map to directory paths, with the final segment being the class name appended with `.php`.

The following is a complete, production-grade PSR-4 autoloader implementation and namespace demonstration, designed to be placed in a project root:

```php
<?php

declare(strict_types=1);

// --- file: src/Psr4Autoloader.php ---

namespace App\Support;

/**
 * A complete PSR-4 autoloader implementation with spec-compliant
 * namespace prefix mapping, including support for multiple base
 * directories per prefix and fallback paths.
 */
final class Psr4Autoloader
{
    /** @var array<string, list<string>> Prefix => base directories */
    private array $prefixes = [];

    public function register(): void
    {
        spl_autoload_register([$this, 'loadClass']);
    }

    public function unregister(): void
    {
        spl_autoload_unregister([$this, 'loadClass']);
    }

    public function addNamespace(string $prefix, string $baseDir): void
    {
        // Normalize: ensure trailing backslash on prefix, trailing
        // directory separator on baseDir.
        $prefix = trim($prefix, '\\') . '\\';
        $baseDir = rtrim($baseDir, DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR;

        if (!isset($this->prefixes[$prefix])) {
            $this->prefixes[$prefix] = [];
        }
        $this->prefixes[$prefix][] = $baseDir;
    }

    public function loadClass(string $class): void
    {
        // The class name arrives fully qualified, no leading backslash.
        $prefix = $class;

        // Walk backwards through the class name's namespace segments
        // to find the longest registered prefix match.
        while (false !== $pos = strrpos($prefix, '\\')) {
            $prefix = substr($class, 0, $pos + 1);
            $relativeClass = substr($class, $pos + 1);

            if (isset($this->prefixes[$prefix])) {
                foreach ($this->prefixes[$prefix] as $baseDir) {
                    $file = $baseDir
                        . str_replace('\\', DIRECTORY_SEPARATOR, $relativeClass)
                        . '.php';

                    if ($this->requireFile($file)) {
                        return;
                    }
                }
            }

            $prefix = rtrim($prefix, '\\');
        }
    }

    private function requireFile(string $file): bool
    {
        if (file_exists($file)) {
            require $file;
            return true;
        }
        return false;
    }
}
```

```php
<?php

// --- file: src/Domain/UserRepository.php ---

namespace App\Domain;

use App\Domain\{User, UserCollection};

final class UserRepository
{
    /** @var array<int, User> */
    private array $storage = [];

    public function save(User $user): void
    {
        $this->storage[$user->id] = $user;
    }

    public function findById(int $id): ?User
    {
        return $this->storage[$id] ?? null;
    }

    public function all(): UserCollection
    {
        return new UserCollection(array_values($this->storage));
    }
}
```

```php
<?php

// --- file: src/Domain/User.php ---

namespace App\Domain;

final class User
{
    public function __construct(
        public readonly int $id,
        public readonly string $email,
        public readonly string $name,
    ) {}
}
```

```php
<?php

// --- file: src/Domain/UserCollection.php ---

namespace App\Domain;

use ArrayIterator;
use IteratorAggregate;
use Countable;
use Traversable;

/**
 * A type-safe, iterable collection implementing standard SPL interfaces.
 * This demonstrates interface implementation with multiple contracts.
 */
final class UserCollection implements IteratorAggregate, Countable
{
    /**
     * @param list<User> $users
     */
    public function __construct(
        private array $users = []
    ) {}

    public function getIterator(): Traversable
    {
        return new ArrayIterator($this->users);
    }

    public function count(): int
    {
        return count($this->users);
    }

    public function add(User $user): void
    {
        $this->users[] = $user;
    }

    public function filter(callable $predicate): self
    {
        return new self(array_filter($this->users, $predicate));
    }
}
```

```php
<?php

// --- file: bootstrap.php ---

declare(strict_types=1);

require __DIR__ . '/src/Support/Psr4Autoloader.php';

$loader = new App\Support\Psr4Autoloader();
$loader->addNamespace('App\\', __DIR__ . '/src/');
$loader->register();

// --- Usage ---

$repo = new App\Domain\UserRepository();

$repo->save(new App\Domain\User(1, 'alice@example.com', 'Alice'));
$repo->save(new App\Domain\User(2, 'bob@example.com', 'Bob'));

$collection = $repo->all();

foreach ($collection as $user) {
    echo "{$user->name} <{$user->email}>\n";
}

echo "Total: " . count($collection) . "\n";

$admins = $collection->filter(fn(App\Domain\User $u): bool =>
    str_ends_with($u->email, 'example.com')
);

echo "Filtered: " . count($admins) . "\n";
```

The namespace resolution flow can be visualized as follows:

```
Source: use App\Domain\UserRepository;
        $repo = new UserRepository();

  Compile Phase                          Runtime Phase
  ┌─────────────────────────┐           ┌──────────────────────────────┐
  │ 1. Lexer produces FQN   │           │ 1. ZEND_NEW opcode fires     │
  │    App\Domain\UserRepo  │           │ 2. Lookup in EG(class_table) │
  │ 2. use import matches   │           │    key: "app\domain\userrepo"│
  │    App\Domain\ prefix   │           │ 3. MISS → invoke autoloaders │
  │ 3. Emits FQN in opcode  │──────────▶│ 4. Psr4Autoloader::loadClass │
  │    literal              │           │ 5. require file → class link │
  └─────────────────────────┘           │ 6. Retry lookup → HIT        │
                                        │ 7. Allocate object, call     │
                                        │    __construct               │
                                        └──────────────────────────────┘
```

## 3. High-Performance Optimization & Failure Modes

### Autoloader Performance and Class Map Caching

The PSR-4 autoloader demonstrated above performs a filesystem `file_exists` check on every class load, which is acceptable during development but introduces unnecessary I/O latency in production. The standard optimization is to generate a class map—a precomputed associative array mapping fully-qualified class names to absolute file paths—at build time and use it as a zero-lookup autoloader. Composer's `--optimize-autoloader` flag (`composer dump-autoload --optimize`) does exactly this, replacing the namespace-prefix traversal with a single hash table lookup.

The performance difference is measurable: on a project with 2,000 classes, PSR-4 file resolution adds roughly 0.5ms per class load due to `stat` syscalls and string manipulation, while a class map resolves in under 1 microsecond per class because it is a single hash table access into an in-memory array. For long-running processes under PHP-FPM or inside RoadRunner, the opcache and class table persist across requests, so the autoloader fires only once per class per worker lifetime, but for CLI invocations and serverless deployments where every process starts cold, the class map is essential.

### Method Dispatch Caching and the Runtime Cache Slots

PHP's method dispatch is mediated by the runtime cache, a per-opcode memoization mechanism. The first time a `ZEND_INIT_METHOD_CALL` opcode executes for a given method name on a given class, the engine performs a hash table lookup on the class entry's method table, stores the resulting function pointer in the opcode's runtime cache slot, and on subsequent executions reads the cached pointer directly. This means that the performance cost of method dispatch is not uniform: the first call is significantly more expensive than subsequent calls.

In performance-critical inner loops, this has a practical implication: polymorphic call sites where the object class varies between calls defeat the cache, because each class change invalidates the cached slot and forces a new hash lookup. A call site that receives instances of three different classes in alternation will perform three hash lookups per cycle rather than one cached read. The engineering response is either to minimize polymorphism at hot call sites (use final classes where the dispatch is monomorphic) or to restructure the hot path to avoid method dispatch entirely by inlining the logic into the loop body or using a strategy table indexed by a discriminant integer.

### The `readonly` Trap and Circular References

The `readonly` property modifier enforces write-once semantics: a value can be assigned exactly once, and only within the declaring class's scope (typically the constructor). This creates an invariant that is valuable for value objects and DTOs, but it introduces a subtle failure mode with circular references. If two readonly objects must reference each other, neither can be constructed without the other already existing, and since neither can be mutated after construction, the circular reference cannot be established. The workaround is to use a mutable builder or a factory that constructs both objects with placeholder values and then sets the real references through a private setter or reflection—but reflection bypass of `readonly` was restricted in PHP 8.2 and further locked down in 8.3, making this an unreliable approach. The correct architectural response is to avoid circular readonly dependencies entirely, replacing them with a lookup mechanism (a registry or identity map) that resolves the reference lazily at access time rather than at construction time.

### Trait State Isolation and Property Conflict

Traits can declare properties, but the engine's conflict resolution for properties is blunt: if a trait declares a property and the consuming class declares a property with the same name, a fatal error is raised unless the default values are identical. There is no `insteadof` mechanism for properties. This means that traits carrying stateful properties are fragile composition units, because any consuming class that happens to use the same property name for a different purpose will collide. The production-grade pattern is to prefer dependency injection over stateful traits, or to namespace trait property names with a prefix to reduce collision probability. If a trait must carry state, the trait should declare its properties as private and expose them only through trait methods, which gives the consuming class a clean interface boundary even though the underlying storage is shared.

### Late Static Binding and the Abstract Factory Edge Case

The `new static()` pattern is powerful but has a specific edge case that catches engineers: when a base class method uses `new static()` and the child class overrides the constructor with additional required parameters, the factory method breaks because it cannot supply the new parameters. The solution is to constrain the return type and use `abstract` protected factory methods that subclasses must implement, rather than relying on `new static()` directly when the constructor contract varies across the hierarchy. Alternatively, PHP 8.0+'s named arguments can be used to pass only the parameters the base class knows about, but this requires the child constructor to have defaults for all additional parameters, which may not be semantically valid.

A complete example of the safe factory pattern:

```php
<?php

declare(strict_types=1);

abstract class SerializableModel
{
    abstract public static function fromArray(array $data): static;

    abstract public function toArray(): array;

    // A shared utility that depends on late static binding for
    // type identity but delegates construction to the subclass.
    public static function fromJson(string $json): static
    {
        $data = json_decode($json, true, 512, JSON_THROW_ON_ERROR);
        // Calls the subclass's fromArray, not a hypothetical base version.
        return static::fromArray($data);
    }
}

final class Article extends SerializableModel
{
    public function __construct(
        public readonly int $id,
        public readonly string $title,
        public readonly string $body,
    ) {}

    public static function fromArray(array $data): static
    {
        // Enforce the specific contract this subclass requires.
        return new self(
            id: $data['id'],
            title: $data['title'],
            body: $data['body'] ?? '',
        );
    }

    public function toArray(): array
    {
        return [
            'id' => $this->id,
            'title' => $this->title,
            'body' => $this->body,
        ];
    }
}

$article = Article::fromJson('{"id":1,"title":"Hello","body":"World"}');
echo $article::class . "\n"; // Article
echo $article->title . "\n"; // Hello
```

This pattern delegates the concrete construction responsibility to each subclass through an abstract method, ensuring that `static::fromArray()` always dispatches to the correct subclass implementation. The `fromJson` utility in the base class depends on `static::` to reach the right `fromArray`, but it never invokes `new static()` directly, so varying constructor signatures across subclasses are fully supported. The late static binding mechanism guarantees that `static::fromArray()` resolves to `Article::fromArray` when called as `Article::fromJson()`, which is the correct and type-safe behavior.

### Namespace Fallback Pitfalls

The unqualified function and constant fallback rule—where an unqualified call inside a namespace first checks the current namespace, then falls back to the global namespace—can cause silent failures when a global function is shadowed by a namespace-level function with the same name but a different signature. For example, if a namespace `App\Utils` defines a function `array_map`, all calls to `array_map()` within that namespace resolve to the local version, even in files that do not explicitly import it. The fallback only triggers if the local function does not exist; if it does exist, there is no fallback. The defensive pattern is to always prefix global function calls with a backslash (`\array_map(...)`) inside namespaced files, or to import the global function explicitly with `use function array_map`. This eliminates ambiguity and also produces a micro-optimization: the compiler emits a direct internal call opcode rather than a fallback-capable call opcode that checks two locations at runtime.
