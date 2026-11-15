# Lesson 3: Object-Oriented Patterns

## 1. First-Principles Intuition & Invariants

JavaScript's object system emerged from a collision of design philosophies. When Brendan Eich designed the language in 1995, he fused Self's prototypal inheritance with a syntax deliberately mimicking Java's class-based model to appease corporate stakeholders at Netscape. This compromise produced a dynamically typed, single-threaded runtime where objects are mutable property maps, functions are first-class values carrying lexical scope closures, and the `this` keyword binds late according to call-site semantics rather than lexical position. Understanding JavaScript's object patterns requires dismantling the mental model of classical inheritance hierarchies and rebuilding from three foundational invariants.

The first invariant establishes that every JavaScript object is a dictionary mapping string or symbol keys to values, augmented by an internal `[[Prototype]]` slot pointing to another object or `null`. Property access traverses this prototype chain until a matching key is found or the chain terminates. This is not class-based inheritance with vtables and fixed layouts; it is delegation through runtime pointer chasing. When you write `obj.method()`, the engine walks `obj`, then `obj.[[Prototype]]`, then `obj.[[Prototype]].[[Prototype]]`, examining each object's own properties until `method` is located. This dynamic dispatch comes with performance costs—modern engines employ inline caches and hidden classes to amortize lookup overhead—but it grants extraordinary runtime flexibility.

The second invariant governs function invocation and the binding of `this`. Unlike lexically scoped variables that resolve at parse time according to nested scope chains, `this` resolves at call time based on how the function is invoked. A function called as a method (`obj.fn()`) binds `this` to `obj`. The same function invoked as a bare reference (`const f = obj.fn; f();`) binds `this` to the global object in sloppy mode or `undefined` in strict mode. Arrow functions break this rule entirely, capturing `this` lexically from their enclosing scope at definition time, which makes them unsuitable as methods but invaluable for callbacks that must preserve outer context. Constructor functions invoked with `new` bind `this` to a fresh object whose `[[Prototype]]` points to the constructor's `prototype` property. Mastery of JavaScript's object patterns hinges on internalizing these four call-site rules: default binding, implicit binding, explicit binding via `call`/`apply`/`bind`, and `new` binding, which supersede each other in that precedence order.

The third invariant addresses the composition versus inheritance dichotomy. Classical inheritance models code reuse through subclass chains where child classes override parent methods, but this creates brittle hierarchies. The fragile base class problem emerges when parent modifications ripple unpredictably through descendants. The diamond problem arises when a class inherits from multiple parents sharing a common ancestor, forcing the runtime to resolve ambiguous method calls. JavaScript's prototypal model theoretically avoids some of these pitfalls by treating inheritance as delegation rather than taxonomy, but ES6 classes reintroduce syntactic sugar that mimics classical hierarchies. The modern consensus favors composition: assembling objects from small, focused mixins or factories rather than constructing deep inheritance trees. This aligns with the SOLID principle of favoring composition over inheritance and the functional programming ethos of building complex systems from simple, composable units.

These invariants intersect with runtime performance characteristics. V8, SpiderMonkey, and JavaScriptCore optimize property access through hidden classes (also called shapes or maps), which assign fixed offsets to properties added in consistent order. Monomorphic call sites that always see the same hidden class benefit from inline caching, reducing property lookups to single-pointer dereferences. Polymorphic sites observing two to four shapes degrade to a small lookup table. Megamorphic sites seeing five or more shapes force a full dictionary lookup on every access. Constructor functions and ES6 classes generate objects with predictable shapes when properties are initialized in the same order, enabling aggressive optimization. Factory functions that conditionally add properties or use `Object.assign` often produce polymorphic shapes, sacrificing performance for flexibility. This tension between expressiveness and speed pervades JavaScript's object patterns.

## 2. Core Architecture & Mechanics

The constructor function pattern predates ES6 classes and remains foundational for understanding JavaScript's prototypal mechanics. A constructor is an ordinary function invoked with the `new` operator, triggering a four-step protocol. First, the runtime allocates a new object whose `[[Prototype]]` points to the constructor's `prototype` property. Second, the constructor body executes with `this` bound to the new object. Third, the constructor implicitly returns `this` unless it explicitly returns another object. Fourth, the returned object becomes the result of the `new` expression. This protocol allows constructor functions to initialize instance properties while sharing methods on the prototype.

```javascript
function HttpClient(baseURL, timeout) {
  this.baseURL = baseURL;
  this.timeout = timeout;
  this.requestCount = 0;
}

HttpClient.prototype.get = function(path) {
  this.requestCount++;
  return fetch(this.baseURL + path, { 
    signal: AbortSignal.timeout(this.timeout) 
  });
};

HttpClient.prototype.post = function(path, body) {
  this.requestCount++;
  return fetch(this.baseURL + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(this.timeout)
  });
};

const client = new HttpClient('https://api.example.com', 5000);
client.get('/users/42'); // this.requestCount increments
```

Each instance allocates its own `baseURL`, `timeout`, and `requestCount` properties in its object slot, consuming heap memory. The `get` and `post` methods reside on `HttpClient.prototype`, shared across all instances. Property access for `client.get` resolves by checking `client` for a `get` key, failing, then ascending to `client.[[Prototype]]` which points to `HttpClient.prototype`, finding `get` there. The method call `client.get('/users/42')` uses implicit binding, setting `this` to `client` during execution.

Static methods and properties attach directly to the constructor function itself rather than its prototype. Since functions are objects, they accept arbitrary property assignments. This pattern mimics class methods in classical languages.

```javascript
HttpClient.fromConfig = function(config) {
  return new HttpClient(config.baseURL, config.timeout || 3000);
};

HttpClient.DEFAULT_TIMEOUT = 3000;

const client = HttpClient.fromConfig({ baseURL: 'https://api.example.com' });
```

Inheritance chains link prototype objects. A child constructor's prototype becomes an instance of the parent constructor, establishing a delegation chain. This requires careful wiring to preserve constructor references.

```javascript
function RetryHttpClient(baseURL, timeout, maxRetries) {
  HttpClient.call(this, baseURL, timeout);
  this.maxRetries = maxRetries;
}

RetryHttpClient.prototype = Object.create(HttpClient.prototype);
RetryHttpClient.prototype.constructor = RetryHttpClient;

RetryHttpClient.prototype.get = function(path) {
  return this._retryRequest(() => HttpClient.prototype.get.call(this, path));
};

RetryHttpClient.prototype._retryRequest = function(fn) {
  let attempts = 0;
  const attempt = () => fn().catch(err => {
    if (++attempts < this.maxRetries) return attempt();
    throw err;
  });
  return attempt();
};

const retryClient = new RetryHttpClient('https://api.example.com', 5000, 3);
```

The `Object.create(HttpClient.prototype)` call allocates a new object whose `[[Prototype]]` points to `HttpClient.prototype`, avoiding the side effects of calling `new HttpClient()` to establish the chain. The explicit `constructor` reassignment repairs the broken constructor reference that `Object.create` discards. The `HttpClient.call(this, baseURL, timeout)` line invokes the parent constructor with `this` bound to the child instance, initializing inherited properties. Method overriding works through shadowing: `RetryHttpClient.prototype.get` replaces the inherited `get`, but `HttpClient.prototype.get.call(this, path)` explicitly delegates to the parent method using explicit `call` binding.

ES6 classes provide syntactic sugar over this prototypal machinery. The `class` keyword declares a constructor function and attaches methods to its prototype in a single declaration block. The `extends` keyword establishes the prototype chain, and `super` invokes parent methods.

```javascript
class HttpClient {
  constructor(baseURL, timeout) {
    this.baseURL = baseURL;
    this.timeout = timeout;
    this.requestCount = 0;
  }

  get(path) {
    this.requestCount++;
    return fetch(this.baseURL + path, {
      signal: AbortSignal.timeout(this.timeout)
    });
  }

  post(path, body) {
    this.requestCount++;
    return fetch(this.baseURL + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(this.timeout)
    });
  }

  static fromConfig(config) {
    return new HttpClient(config.baseURL, config.timeout || 3000);
  }

  static DEFAULT_TIMEOUT = 3000;
}

class RetryHttpClient extends HttpClient {
  constructor(baseURL, timeout, maxRetries) {
    super(baseURL, timeout);
    this.maxRetries = maxRetries;
  }

  async get(path) {
    return this._retryRequest(() => super.get(path));
  }

  async _retryRequest(fn) {
    let attempts = 0;
    while (attempts < this.maxRetries) {
      try {
        return await fn();
      } catch (err) {
        if (++attempts >= this.maxRetries) throw err;
      }
    }
  }
}
```

The transpiled output reveals that classes desugar to constructor functions with prototype assignments. Class methods are non-enumerable by default, distinguishing them from manually assigned prototype properties. The `super` keyword requires statically determinable parent references at parse time, leveraging the `[[HomeObject]]` internal slot that binds a method to its defining class. This prevents the dynamic parent rebinding that prototype manipulation allowed, trading flexibility for safety.

Private fields introduced in ES2022 enforce true encapsulation through lexical scoping rather than convention. The `#` prefix signals that the field exists in a private namespace, accessible only within the class body.

```javascript
class SecureHttpClient extends HttpClient {
  #apiKey;

  constructor(baseURL, timeout, apiKey) {
    super(baseURL, timeout);
    this.#apiKey = apiKey;
  }

  get(path) {
    this.requestCount++;
    return fetch(this.baseURL + path, {
      headers: { 'Authorization': `Bearer ${this.#apiKey}` },
      signal: AbortSignal.timeout(this.timeout)
    });
  }
}

const secureClient = new SecureHttpClient('https://api.example.com', 5000, 'secret-key');
console.log(secureClient.requestCount); // 0
console.log(secureClient.#apiKey); // SyntaxError
```

Private fields do not reside on the object or its prototype but in a separate internal data structure indexed by the class definition. Attempting to access `#apiKey` outside the class body produces a syntax error at parse time, not a runtime property lookup failure. This prevents reflection APIs like `Object.keys` or `Reflect.ownKeys` from exposing private state, a significant departure from naming conventions like `_apiKey` that rely on social contract rather than enforcement.

Composition over inheritance inverts the relationship between objects. Instead of defining a subclass that inherits behavior from a parent, composition assembles objects from small, reusable components. Factory functions provide the simplest composition mechanism, returning plain objects without prototypal chains.

```javascript
function createLogger(prefix) {
  return {
    log(message) {
      console.log(`[${prefix}] ${message}`);
    },
    error(message) {
      console.error(`[${prefix}] ERROR: ${message}`);
    }
  };
}

function createMetrics() {
  let requestCount = 0;
  let errorCount = 0;
  return {
    incrementRequests() { requestCount++; },
    incrementErrors() { errorCount++; },
    getStats() { return { requestCount, errorCount }; }
  };
}

function createHttpClient(baseURL, timeout) {
  const logger = createLogger('HttpClient');
  const metrics = createMetrics();

  return {
    baseURL,
    timeout,
    async get(path) {
      metrics.incrementRequests();
      logger.log(`GET ${path}`);
      try {
        return await fetch(baseURL + path, {
          signal: AbortSignal.timeout(timeout)
        });
      } catch (err) {
        metrics.incrementErrors();
        logger.error(err.message);
        throw err;
      }
    },
    getMetrics() {
      return metrics.getStats();
    }
  };
}

const client = createHttpClient('https://api.example.com', 5000);
client.get('/users/42');
```

This pattern eliminates prototypal chains entirely. Each client instance contains its own methods, logger, and metrics object. Memory overhead increases compared to shared prototype methods, but the benefit lies in decoupling. The logger and metrics components know nothing about HTTP clients; they are generic building blocks composable into any system. This aligns with the interface segregation principle: clients depend only on the narrow interfaces they consume.

Mixins generalize composition by merging properties from source objects into a target. Unlike inheritance, which establishes a fixed chain at construction time, mixins inject behavior dynamically.

```javascript
const withRetry = {
  async _retryRequest(fn, maxRetries = 3) {
    let attempts = 0;
    while (attempts < maxRetries) {
      try {
        return await fn();
      } catch (err) {
        if (++attempts >= maxRetries) throw err;
      }
    }
  }
};

const withCircuitBreaker = {
  _initCircuitBreaker() {
    this._failures = 0;
    this._state = 'CLOSED';
    this._threshold = 5;
    this._cooldown = 30000;
  },
  _recordSuccess() {
    this._failures = 0;
    this._state = 'CLOSED';
  },
  _recordFailure() {
    this._failures++;
    if (this._failures >= this._threshold) {
      this._state = 'OPEN';
      setTimeout(() => { this._state = 'HALF_OPEN'; }, this._cooldown);
    }
  },
  _canAttempt() {
    return this._state !== 'OPEN';
  }
};

class ResilientHttpClient extends HttpClient {
  constructor(baseURL, timeout) {
    super(baseURL, timeout);
    this._initCircuitBreaker();
  }

  async get(path) {
    if (!this._canAttempt()) {
      throw new Error('Circuit breaker OPEN');
    }
    return this._retryRequest(async () => {
      try {
        const result = await super.get(path);
        this._recordSuccess();
        return result;
      } catch (err) {
        this._recordFailure();
        throw err;
      }
    });
  }
}

Object.assign(ResilientHttpClient.prototype, withRetry, withCircuitBreaker);
```

The `Object.assign` call copies properties from `withRetry` and `withCircuitBreaker` onto `ResilientHttpClient.prototype`, making them available to all instances. This shallow copy means mixin methods execute with `this` bound to the client instance, granting access to instance state. Mixins provide behavior reuse without inheritance hierarchies, but they introduce namespace collisions if multiple mixins define the same property. Ordering matters: later mixins overwrite earlier ones.

Functional mixins return functions that accept a superclass and return a subclass, enabling chained composition. This pattern avoids namespace collisions by generating unique subclasses.

```javascript
const withRetry = (SuperClass) => class extends SuperClass {
  async _retryRequest(fn, maxRetries = 3) {
    let attempts = 0;
    while (attempts < maxRetries) {
      try {
        return await fn();
      } catch (err) {
        if (++attempts >= maxRetries) throw err;
      }
    }
  }
};

const withCircuitBreaker = (SuperClass) => class extends SuperClass {
  constructor(...args) {
    super(...args);
    this._failures = 0;
    this._state = 'CLOSED';
    this._threshold = 5;
    this._cooldown = 30000;
  }

  _recordSuccess() {
    this._failures = 0;
    this._state = 'CLOSED';
  }

  _recordFailure() {
    this._failures++;
    if (this._failures >= this._threshold) {
      this._state = 'OPEN';
      setTimeout(() => { this._state = 'HALF_OPEN'; }, this._cooldown);
    }
  }

  _canAttempt() {
    return this._state !== 'OPEN';
  }
};

class ResilientHttpClient extends withCircuitBreaker(withRetry(HttpClient)) {
  async get(path) {
    if (!this._canAttempt()) {
      throw new Error('Circuit breaker OPEN');
    }
    return this._retryRequest(async () => {
      try {
        const result = await super.get(path);
        this._recordSuccess();
        return result;
      } catch (err) {
        this._recordFailure();
        throw err;
      }
    });
  }
}
```

Each mixin function wraps the input class in a new subclass, stacking behaviors. The chain `withCircuitBreaker(withRetry(HttpClient))` produces a class hierarchy where `ResilientHttpClient` extends an anonymous class with circuit breaker logic, which extends an anonymous class with retry logic, which extends `HttpClient`. This preserves `instanceof` checks and prototype chains while allowing reusable behavior composition.

The `this` binding rules determine method behavior across these patterns. Consider a detached method reference, a common source of runtime errors.

```javascript
const client = new HttpClient('https://api.example.com', 5000);
const get = client.get;
get('/users/42'); // TypeError: Cannot read property 'requestCount' of undefined
```

The method reference `client.get` extracts the function without binding context. When invoked as `get('/users/42')`, the call site lacks an implicit receiver, so `this` defaults to `undefined` in strict mode (which class methods enforce). The fix applies explicit binding via `bind`, which returns a new function with `this` permanently bound.

```javascript
const get = client.get.bind(client);
get('/users/42'); // Works correctly
```

Arrow functions capture `this` lexically, making them unsuitable as methods but ideal for callbacks.

```javascript
class HttpClient {
  constructor(baseURL, timeout) {
    this.baseURL = baseURL;
    this.timeout = timeout;
    this.requestCount = 0;
  }

  get(path) {
    this.requestCount++;
    return fetch(this.baseURL + path, {
      signal: AbortSignal.timeout(this.timeout)
    });
  }

  batchGet(paths) {
    return Promise.all(paths.map(path => this.get(path)));
  }
}
```

The arrow function `path => this.get(path)` captures `this` from the `batchGet` method scope, where `this` refers to the client instance. Converting `batchGet` itself to an arrow function breaks the pattern because class methods require method syntax to receive the implicit receiver.

```javascript
class HttpClient {
  constructor(baseURL, timeout) {
    this.baseURL = baseURL;
    this.timeout = timeout;
    this.requestCount = 0;
    this.get = this.get.bind(this); // Bind in constructor
  }

  get(path) {
    this.requestCount++;
    return fetch(this.baseURL + path, {
      signal: AbortSignal.timeout(this.timeout)
    });
  }
}

const client = new HttpClient('https://api.example.com', 5000);
const get = client.get;
get('/users/42'); // Works due to constructor binding
```

Binding methods in the constructor ensures detached references work correctly but sacrifices the memory efficiency of shared prototype methods. Each instance allocates its own bound function, duplicating method code across instances. Public class fields with arrow function values provide the same semantics with cleaner syntax.

```javascript
class HttpClient {
  constructor(baseURL, timeout) {
    this.baseURL = baseURL;
    this.timeout = timeout;
    this.requestCount = 0;
  }

  get = (path) => {
    this.requestCount++;
    return fetch(this.baseURL + path, {
      signal: AbortSignal.timeout(this.timeout)
    });
  };
}
```

The field `get = (path) => {...}` allocates a new arrow function on each instance, capturing `this` from the constructor context. This enables safe method extraction at the cost of per-instance memory overhead.

## 3. High-Performance Optimization & Failure Modes

JavaScript engines optimize object property access through hidden classes, also called shapes or maps in V8 terminology. When a constructor initializes properties in a consistent order, the engine assigns a hidden class encoding property names and memory offsets. Objects sharing the same hidden class benefit from inline caches that replace dynamic property lookups with fixed-offset loads. Maintaining monomorphic call sites requires disciplined initialization patterns.

```javascript
class Point {
  constructor(x, y) {
    this.x = x; // Transition to Shape1
    this.y = y; // Transition to Shape2
  }

  distance() {
    return Math.sqrt(this.x * this.x + this.y * this.y);
  }
}

const p1 = new Point(3, 4);
const p2 = new Point(5, 12);
```

Both `p1` and `p2` transition through the same sequence of hidden classes: the initial empty shape, then Shape1 after assigning `x`, then Shape2 after assigning `y`. The `distance` method call site observes Shape2 consistently, enabling the engine to inline cache the `x` and `y` offsets. Conditional property addition breaks this optimization.

```javascript
class Point {
  constructor(x, y, label) {
    this.x = x;
    this.y = y;
    if (label) this.label = label; // Creates polymorphic shapes
  }
}

const p1 = new Point(3, 4);          // Shape2 (x, y)
const p2 = new Point(5, 12, 'origin'); // Shape3 (x, y, label)
```

Now `p1` and `p2` have different hidden classes. A function processing both points encounters polymorphic property access, degrading to a small cache or dictionary lookup. The fix initializes all properties unconditionally, using `undefined` or default values for optional fields.

```javascript
class Point {
  constructor(x, y, label = undefined) {
    this.x = x;
    this.y = y;
    this.label = label; // Always assigned, same shape
  }
}
```

Factory functions that use `Object.assign` or spread operators often produce polymorphic shapes because the engine cannot predict property order at parse time.

```javascript
function createPoint(config) {
  return { x: 0, y: 0, ...config };
}

const p1 = createPoint({ x: 3, y: 4 });
const p2 = createPoint({ y: 12, x: 5 }); // Different key order
```

The spread operator assigns properties in iteration order, which depends on the `config` argument. If callers pass objects with varying key orders, each invocation produces a different hidden class. Explicit property assignment in fixed order avoids this.

```javascript
function createPoint(config) {
  return {
    x: config.x ?? 0,
    y: config.y ?? 0
  };
}
```

Prototype pollution attacks exploit JavaScript's dynamic property assignment to inject properties onto `Object.prototype`, affecting all objects in the runtime. This vulnerability arises when user-controlled input modifies object properties without validation.

```javascript
function merge(target, source) {
  for (const key in source) {
    target[key] = source[key];
  }
  return target;
}

const userInput = JSON.parse('{"__proto__": {"isAdmin": true}}');
const config = {};
merge(config, userInput);

const unrelatedObject = {};
console.log(unrelatedObject.isAdmin); // true
```

The `merge` function iterates over `userInput` keys, including `__proto__`, which references `Object.prototype` when used as a property accessor. Assigning `target["__proto__"]` modifies the prototype chain rather than creating an own property. Every object inheriting from `Object.prototype` now has an `isAdmin` property. Defenses include using `Object.create(null)` to create objects without prototypes, validating keys against a whitelist, and using `Object.hasOwnProperty` checks.

```javascript
function merge(target, source) {
  for (const key in source) {
    if (Object.hasOwnProperty.call(source, key) && key !== '__proto__') {
      target[key] = source[key];
    }
  }
  return target;
}
```

Alternatively, use `Object.assign` with `Object.create(null)` to avoid prototype chain interference.

```javascript
const config = Object.assign(Object.create(null), userInput);
```

Memory leaks in class-based patterns often stem from closure captures. When methods or callbacks capture references to large objects or DOM nodes, the garbage collector cannot reclaim memory even after the parent object is no longer needed.

```javascript
class DataProcessor {
  constructor() {
    this.largeBuffer = new Uint8Array(100_000_000); // 100 MB
  }

  process(callback) {
    const result = this.analyzeBuffer();
    callback(() => {
      console.log('Buffer size:', this.largeBuffer.length);
    });
  }

  analyzeBuffer() {
    return this.largeBuffer.reduce((sum, byte) => sum + byte, 0);
  }
}

const processor = new DataProcessor();
processor.process(fn => {
  setTimeout(fn, 60000); // Keeps processor alive for 60 seconds
});
processor = null; // Intent to release, but closure prevents GC
```

The callback passed to `setTimeout` captures `this`, which references the `processor` instance and its 100 MB buffer. Even though the code nulls the `processor` variable, the closure keeps the instance alive until the timeout fires. The fix minimizes closure scope by extracting only necessary data.

```javascript
process(callback) {
  const result = this.analyzeBuffer();
  const bufferLength = this.largeBuffer.length;
  callback(() => {
    console.log('Buffer size:', bufferLength);
  });
}
```

Now the closure captures only the numeric `bufferLength` rather than the entire instance, allowing the garbage collector to reclaim the buffer.

Inheritance hierarchies deeper than three levels degrade maintainability and fragility. Each level couples child classes to parent implementations, making refactoring hazardous. The fragile base class problem manifests when a parent class change inadvertently breaks a distant descendant.

```javascript
class Animal {
  eat(food) {
    this.energy += food.calories;
  }
}

class Mammal extends Animal {
  eat(food) {
    super.eat(food);
    this.temperature += 0.1; // Mammals generate heat
  }
}

class Dog extends Mammal {
  eat(food) {
    super.eat(food);
    this.happiness += food.tastiness;
  }
}
```

If `Animal.eat` is refactored to validate food before updating energy, and the validation throws an exception, `Dog.eat` breaks because the super call propagates the exception before updating happiness. The fix favors composition by extracting eating logic into a reusable function.

```javascript
function consumeFood(entity, food) {
  entity.energy += food.calories;
  if (entity.bodyType === 'mammal') entity.temperature += 0.1;
  if (entity.traits?.includes('playful')) entity.happiness += food.tastiness;
}

class Dog {
  constructor() {
    this.energy = 100;
    this.temperature = 37.0;
    this.happiness = 50;
    this.bodyType = 'mammal';
    this.traits = ['playful', 'loyal'];
  }

  eat(food) {
    consumeFood(this, food);
  }
}
```

This flattens the hierarchy and makes the eating logic independently testable. Conditional behavior depends on data attributes rather than class identity.

Mixin collisions occur when multiple mixins define the same property. Last-write wins with `Object.assign`, silently overwriting earlier definitions.

```javascript
const mixinA = { log() { console.log('A'); } };
const mixinB = { log() { console.log('B'); } };

class MyClass {}
Object.assign(MyClass.prototype, mixinA, mixinB);

const instance = new MyClass();
instance.log(); // 'B' – mixinB overwrote mixinA
```

Functional mixins mitigate this through explicit chaining, where each mixin can choose to delegate to `super`.

```javascript
const mixinA = (SuperClass) => class extends SuperClass {
  log() {
    console.log('A');
    if (super.log) super.log();
  }
};

const mixinB = (SuperClass) => class extends SuperClass {
  log() {
    console.log('B');
    if (super.log) super.log();
  }
};

class MyClass extends mixinA(mixinB(class {})) {}

const instance = new MyClass();
instance.log();
// 'A'
// 'B'
```

The chaining order determines call sequence. `mixinA(mixinB(class {}))` wraps `mixinB`'s class in `mixinA`, so `mixinA.log` executes first and delegates to `super.log`, which invokes `mixinB.log`.

Performance profiling of class-based versus factory-based patterns reveals tradeoffs. Classes benefit from shared prototype methods, reducing memory footprint when instantiating thousands of objects. Factory functions allocate closures per instance, increasing heap pressure but enabling private state through lexical scope.

```javascript
// Class-based: shared methods, lower memory per instance
class Counter {
  constructor() { this.count = 0; }
  increment() { this.count++; }
}

const counters = Array.from({ length: 10000 }, () => new Counter());
// Each counter allocates ~16 bytes (count property + hidden class pointer)
// increment method shared on prototype: ~1 allocation

// Factory-based: closures per instance, higher memory
function createCounter() {
  let count = 0;
  return {
    increment() { count++; },
    getCount() { return count; }
  };
}

const counters2 = Array.from({ length: 10000 }, createCounter);
// Each counter allocates ~48 bytes (closure context + methods)
```

Benchmark tests on V8 show class-based instantiation runs 2–3× faster for simple objects due to optimized constructor inlining and hidden class reuse. Factory functions excel when encapsulation and composability outweigh per-instance overhead, particularly for objects with complex initialization logic or dynamic behavior.

The decision between constructors, classes, and factories hinges on project constraints. Performance-critical code paths with high object churn favor classes for their memory efficiency and optimization pathways. Application code that prioritizes testability, modularity, and runtime flexibility benefits from composition patterns using factories and mixins. Modern codebases often blend both: classes for data models and domain entities, factories for service objects and configuration builders, and mixins for cross-cutting concerns like logging, telemetry, and retry logic. Understanding the underlying prototypal machinery enables deliberate choices aligned with system requirements rather than dogmatic adherence to a single pattern.
