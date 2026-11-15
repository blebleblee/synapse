# Lesson 2: Dependency Injection, Hierarchical Injectors, Providers

## 1. First-Principles Intuition & Invariants

Dependency injection in Angular constitutes a compile-time and runtime framework for transforming declarative constructor annotations into a directed acyclic graph of provider resolution nodes, where each component or service requests dependencies through typed tokens and receives concrete instances resolved through a hierarchical chain of injectors. At its foundation, Angular's DI system operates as a memoized factory registry that converts abstract provider declarations into singleton or transient instances, enforcing inversion-of-control semantics while maintaining strict type safety through TypeScript metadata reflection.

The conceptual shift from manual object instantiation to declarative dependency graphs emerges from a fundamental software engineering tension: as systems grow in complexity, the combinatorial explosion of constructor arguments and initialization sequences creates brittle coupling between consuming code and concrete implementations. Traditional object-oriented patterns require clients to know not only what services they need, but how to construct those services, recursively instantiating all transitive dependencies. This approach violates the dependency inversion principle and makes isolated unit testing nearly impossible, since test harnesses must replicate entire dependency chains to instantiate a single component under test.

Angular's injector hierarchy solves this problem by establishing a tree of resolution contexts that mirrors the component tree, where each node maintains its own provider registry and delegates upward to parent injectors when local resolution fails. The framework constructs this tree during application bootstrap and dynamically extends it as lazy-loaded modules instantiate their own injector subtrees. Every component exists within an injector context defined by three distinct scopes: the root application injector created during platform bootstrap, module-level injectors instantiated for each NgModule, and element-level injectors synthesized for components that declare providers in their metadata. This tripartite hierarchy ensures that service lifetimes align naturally with architectural boundaries—root-scoped singletons live for the application's entire execution, module-scoped instances persist only while their host module remains loaded, and component-scoped dependencies die when their host component destructs.

The resolution algorithm walks this injector chain through a depth-first traversal that begins at the requesting component's element injector, ascends through parent component injectors until reaching the module boundary, then continues upward through the module injector hierarchy until either locating a matching provider or exhausting the root injector and throwing a runtime exception. Angular optimizes this traversal through compile-time static analysis when AOT compilation transforms provider declarations into direct function calls within generated factory code, eliminating runtime reflection overhead for common dependency patterns. The framework represents providers through internal token-to-factory mappings where tokens serve as unique keys—typically TypeScript classes used as their own injection tokens, though string-based InjectionToken instances enable non-class dependencies like configuration objects or primitive values.

Provider declarations encode not just what to inject, but how to construct it, through four distinct provider recipes: ClassProvider instantiates the provided class via its constructor, FactoryProvider delegates to an arbitrary factory function that receives its own resolved dependencies, ValueProvider returns a pre-constructed singleton instance, and ExistingProvider creates an alias to another token's resolution chain. The framework's type system ensures that the token's type matches the provided value's type at compile time, catching misconfigurations before runtime instantiation. Angular's injector caches resolved instances within their registration scope, implementing a memoization strategy where the first resolution of a token triggers factory execution and subsequent requests return the cached singleton, provided the requester shares the same injector context. This singleton-per-injector semantic means that a service registered in multiple injector scopes yields distinct instances in each scope, a subtlety that frequently confuses developers expecting global singleton behavior.

The fundamental invariant governing Angular's DI system states that injection resolution must remain deterministic and side-effect-free during the construction phase, meaning that service constructors cannot trigger change detection, manipulate the DOM, or invoke asynchronous operations that would introduce nondeterministic initialization sequencing. The framework enforces this invariant by separating construction from initialization, using Angular's lifecycle hooks like `ngOnInit` to defer side-effectful initialization until after the entire dependency graph has been constructed and wired. This constraint enables Angular's compiler to aggressively optimize provider resolution through static factory generation, where the AOT compiler analyzes the dependency graph at build time and emits specialized JavaScript functions that directly instantiate services in topologically sorted order, eliminating all reflection overhead for production builds.

Injection tokens represent the addressing mechanism for Angular's provider registry, functioning as unique keys that map consumer requests to provider factories. The framework distinguishes between type tokens—ordinary TypeScript classes used as both the injected type and the lookup key—and opaque tokens created through the `InjectionToken` class, which provide type-safe injection for non-class values like configuration strings, feature flags, or primitive constants. Type tokens leverage TypeScript's structural type system where the class constructor function itself serves as the runtime token value, enabling developers to inject dependencies by simply declaring constructor parameters with type annotations. The compiler extracts these annotations through TypeScript's experimental decorator metadata emission, which serializes type information into runtime-accessible metadata arrays attached to the constructor function. Opaque injection tokens solve the namespacing problem for primitive and object types by providing globally unique token instances that carry generic type parameters for compile-time type checking, preventing collisions between semantically distinct values that share the same runtime type.

The hierarchical injector tree establishes a scope and lifetime management system where service instances exist within well-defined boundaries and die when their containing injector destructs. Root-level providers registered through `providedIn: 'root'` metadata or the legacy `ModuleInjector` providers array create application-wide singletons that persist from bootstrap until teardown, making them suitable for global state management, HTTP clients, and authentication services. Module-level providers declared within feature module metadata instantiate when Angular loads the module and destruct when lazy-loaded modules unload, though eagerly loaded module providers effectively become root-scoped since the platform never unloads them. Component-level providers specified in the component decorator's providers array create new service instances for each component instance, enabling per-component state isolation and facilitating hierarchical services where child components inherit modified or overridden dependencies from their ancestors. This scoping mechanism implements a natural memory management strategy where Angular's component destruction logic automatically releases component-scoped dependencies, preventing memory leaks in long-running single-page applications.

The resolution algorithm's upward traversal pattern creates an override mechanism where child injectors shadow parent providers by registering providers for the same token at lower levels in the hierarchy. When a component declares a provider for a token that already exists in an ancestor injector, the framework resolves requests within that component subtree to the local provider instance, effectively forking the dependency graph for that branch of the component tree. This shadowing behavior enables powerful testing strategies where test harnesses override production services with mock implementations by registering test doubles at the TestBed's injector level, ensuring that all components under test receive mocked dependencies without modifying production code. The same mechanism supports feature-specific service customization where a lazy-loaded feature module provides a specialized implementation of a core service interface, allowing the feature's components to operate against different behavior without affecting the rest of the application.

Angular's provider resolution respects visibility modifiers through decorator-based metadata that constrains traversal patterns. The `@Optional` decorator marks a dependency as non-essential, instructing the injector to resolve the dependency if possible but inject `null` rather than throwing when no provider exists in the traversal chain. The `@Self` decorator restricts resolution to the current element injector, preventing upward traversal and ensuring that the dependency must be provided locally or fail immediately. The `@SkipSelf` decorator inverts this constraint by forcing the resolution to begin at the parent injector, enabling components to access ancestor-provided services while still declaring their own component-level overrides. The `@Host` decorator bounds the search to the nearest host component's element injector, terminating traversal at component boundaries rather than continuing into module injectors. These visibility modifiers compose with provider declarations to express precise control over dependency resolution scopes, enabling advanced patterns like optional feature detection and hierarchical service customization.

## 2. Core Architecture & Mechanics

Angular's injector hierarchy materializes as a parallel tree structure alongside the component tree, where each component node references an element injector synthesized during component instantiation and each NgModule generates a module injector during module compilation. The framework distinguishes between two fundamental injector types: the `ModuleInjector` hierarchy rooted at the platform injector that manages NgModule and root-scoped providers, and the `ElementInjector` hierarchy that mirrors the component tree and manages component and directive providers. These two hierarchies remain logically separate but interconnected through a fallback mechanism where element injector resolution failures trigger delegation to the module injector chain, implementing a two-tier resolution strategy that separates architectural concerns.

The platform injector sits at the absolute root of the module injector hierarchy, created during Angular's bootstrap sequence through `platformBrowserDynamic()` or equivalent platform factory functions. This injector hosts platform-wide singletons like the compiler infrastructure, zone.js integration, and DOM manipulation primitives that must remain unique across potentially multiple Angular applications running on the same page. Below the platform injector, the root application injector instantiates during the `bootstrapModule()` call, processing the root NgModule's provider declarations and establishing the base dependency context for the entire application. Each eagerly loaded feature module contributes its providers to this root injector, effectively flattening module-scoped providers into root scope for modules imported during initial bootstrap. Lazy-loaded modules break this flattening behavior by instantiating their own child module injectors that branch from the root, creating isolated provider scopes that persist only while the lazy module remains active.

The element injector hierarchy emerges from component metadata processing where Angular's compiler analyzes each component's `providers` and `viewProviders` arrays, generating factory code that instantiates an element injector instance for components declaring providers and synthesizing a logical injector for components without explicit providers. Each element injector maintains a sparse map from injection tokens to cached provider instances, implementing a fast-path lookup that checks the local cache before delegating to parent injectors. The framework optimizes the common case where components don't declare providers by avoiding injector allocation entirely, instead encoding a parent pointer that skips directly to the nearest ancestor with an actual element injector. This optimization reduces memory overhead for component trees where only a handful of components declare providers, maintaining constant-time traversal performance through parent pointer compression.

Provider registration transforms declarative metadata into executable factory functions through Angular's compiler pipeline. When the AOT compiler processes a provider declaration like `{ provide: LoggerService, useClass: ConsoleLogger }`, it generates a factory function that instantiates `ConsoleLogger` by recursively resolving its constructor dependencies, wiring together the transitive dependency graph through nested factory invocations. The compiler performs static dependency analysis to detect circular dependencies at build time, failing compilation with diagnostic errors when cycles exist in the provider graph. For factory providers specified with `useFactory`, the compiler preserves the factory function reference and generates a wrapper that resolves the factory's declared dependencies array before invoking the factory with resolved arguments. Value providers bypass factory generation entirely, emitting direct references to the provided constant value for zero-overhead resolution.

```typescript
// Provider registration and factory generation mental model
import { Injectable, InjectionToken, Provider } from '@angular/core';

// Type token: class serves as its own injection token
@Injectable()
export class DataService {
  constructor(private http: HttpClient) {}
  
  fetchData(): Observable<Data> {
    return this.http.get<Data>('/api/data');
  }
}

// Opaque token: enables type-safe injection of non-class values
export const API_BASE_URL = new InjectionToken<string>('api.base.url', {
  providedIn: 'root',
  factory: () => 'https://api.production.com'
});

// Provider recipes demonstrating factory transformations
const providers: Provider[] = [
  // ClassProvider: injector instantiates DataService via constructor
  { provide: DataService, useClass: DataService },
  
  // FactoryProvider: injector invokes factory with resolved deps
  { 
    provide: DataService, 
    useFactory: (http: HttpClient, baseUrl: string) => {
      return new DataService(http);
    },
    deps: [HttpClient, API_BASE_URL]
  },
  
  // ValueProvider: injector returns pre-constructed instance
  { 
    provide: API_BASE_URL, 
    useValue: 'https://api.staging.com' 
  },
  
  // ExistingProvider: injector aliases token to another provider
  { 
    provide: 'LEGACY_DATA_SERVICE', 
    useExisting: DataService 
  }
];

// Tree-shakeable provider using providedIn metadata
@Injectable({
  providedIn: 'root'  // Registers in root injector, removed if never injected
})
export class AnalyticsService {
  trackEvent(event: string): void {
    console.log('Event tracked:', event);
  }
}

// Component-scoped provider demonstrating element injector registration
@Component({
  selector: 'app-dashboard',
  template: '<div>Dashboard</div>',
  providers: [
    // This instance exists per component instance, isolated from root
    { provide: DataService, useClass: DataService }
  ]
})
export class DashboardComponent {
  constructor(private data: DataService) {
    // Receives component-scoped DataService instance
  }
}
```

The resolution algorithm implements a multi-phase lookup strategy that optimizes for the common case of locally-provided dependencies while maintaining correctness for complex hierarchical scenarios. When a component requests a dependency during construction, Angular first consults the component's element injector, checking the local token-to-instance cache for a previously resolved value. Cache hits return immediately with zero overhead beyond the hash map lookup. On cache misses, the injector examines its provider registry to determine if it owns a provider for the requested token. If a local provider exists, the injector invokes the provider's factory function, recursively resolving any transitive dependencies through the same algorithm, then caches the resulting instance before returning it to the caller. If no local provider exists and no visibility constraints prevent delegation, the injector forwards the request to its parent element injector, repeating the process recursively until either finding a provider or exhausting the element injector chain.

When element injector traversal reaches a component boundary without resolution, Angular transitions to the module injector hierarchy by querying the component's host module injector. This cross-hierarchy delegation enables components to access module-level and root-level services without requiring explicit provider declarations in every component. The module injector traversal follows the same cache-check, provider-lookup, factory-invocation pattern, walking upward from the component's host module through parent module injectors until reaching the root application injector. If the root injector fails to resolve the token, Angular throws a `NullInjectorError` containing the full resolution chain, providing diagnostic information about where the framework searched and what constraints prevented resolution.

```typescript
// Hierarchical resolution demonstration with injector tree structure
import { Component, Injectable, Optional, Self, SkipSelf, Host } from '@angular/core';

// Root-scoped service available throughout the application
@Injectable({ providedIn: 'root' })
export class RootConfigService {
  readonly config = { theme: 'light', apiVersion: 'v2' };
}

// Service declared in feature module providers array
@Injectable()
export class FeatureService {
  constructor(private config: RootConfigService) {}
  
  getFeatureData(): string {
    return `Feature using ${this.config.config.theme} theme`;
  }
}

// Parent component providing component-scoped service
@Component({
  selector: 'app-parent',
  template: '<app-child></app-child>',
  providers: [
    { provide: 'PARENT_ID', useValue: 'parent-123' }
  ]
})
export class ParentComponent {
  constructor(
    // Resolves from root injector - RootConfigService is root-scoped
    private rootConfig: RootConfigService,
    
    // Resolves from component's element injector
    @Self() private parentId: string
  ) {}
}

// Child component demonstrating injector traversal
@Component({
  selector: 'app-child',
  template: '<div>Child</div>',
  providers: [
    { provide: 'CHILD_ID', useValue: 'child-456' }
  ]
})
export class ChildComponent {
  constructor(
    // Resolves from root injector via module hierarchy delegation
    private rootConfig: RootConfigService,
    
    // Resolves from parent's element injector - traverses up element tree
    @Optional() private parentId: string,
    
    // Resolves from own element injector - @Self prevents upward traversal
    @Self() private childId: string,
    
    // Skips own injector, resolves from parent - accesses ancestor scope
    @SkipSelf() @Optional() private parentIdAgain: string,
    
    // Resolves from feature module injector
    private featureService: FeatureService
  ) {
    console.log('Root config:', rootConfig.config);
    console.log('Parent ID:', parentId);  // 'parent-123'
    console.log('Child ID:', childId);    // 'child-456'
    console.log('Parent via SkipSelf:', parentIdAgain);  // 'parent-123'
  }
}
```

Angular's injector tree structure creates distinct lifetime boundaries that map naturally to application architecture. Services provided in root scope through `providedIn: 'root'` metadata live from application bootstrap until teardown, surviving across route navigations and component instantiations. The framework guarantees that every injection of a root-scoped service resolves to the same singleton instance, making these services suitable for cross-cutting concerns like authentication state, global caching, and feature flag management. Module-scoped services declared in NgModule providers arrays exhibit more nuanced lifetime semantics: eagerly loaded modules contribute their providers to the root injector, effectively promoting module-scoped services to root singletons, while lazy-loaded modules instantiate their own child injector that persists until Angular unloads the module. This asymmetry requires careful consideration when architecting shared services that must maintain state across module boundaries versus services that should reset when users navigate away from a lazy-loaded feature.

Component-scoped providers create the finest-grained isolation boundary, instantiating new service instances for each component instance and automatically destroying those instances when Angular destroys the component. This scoping strategy enables powerful patterns like form-specific validators that maintain per-form state, wizard step controllers that reset when users abandon the workflow, and component-level analytics trackers that accumulate metrics during the component's lifecycle then flush on destruction. The per-component singleton semantic means that child components injecting the service receive the same instance as their parent when the provider registration occurs in the parent component, creating implicit state sharing down the component tree without explicit prop drilling. Developers override this behavior by registering duplicate providers in child components, forking the dependency graph and creating isolated instances for the child subtree.

```typescript
// Component-scoped service demonstrating per-instance isolation
import { Injectable, OnDestroy } from '@angular/core';
import { Subject } from 'rxjs';

@Injectable()
export class FormStateService implements OnDestroy {
  private readonly destroy$ = new Subject<void>();
  private readonly changes = new Map<string, any>();
  
  recordChange(field: string, value: any): void {
    this.changes.set(field, value);
    console.log(`FormState recorded ${field}:`, value);
  }
  
  getChanges(): Record<string, any> {
    return Object.fromEntries(this.changes);
  }
  
  ngOnDestroy(): void {
    console.log('FormState destroyed with changes:', this.getChanges());
    this.destroy$.next();
    this.destroy$.complete();
  }
}

// Parent component providing form state service
@Component({
  selector: 'app-user-form',
  template: `
    <form>
      <app-name-field></app-name-field>
      <app-email-field></app-email-field>
    </form>
  `,
  providers: [FormStateService]  // New instance per component instance
})
export class UserFormComponent implements OnInit {
  constructor(private formState: FormStateService) {}
  
  ngOnInit(): void {
    console.log('UserForm initialized with FormState instance:', this.formState);
  }
}

// Child components share parent's FormStateService instance
@Component({
  selector: 'app-name-field',
  template: '<input (input)="onInput($event)">'
})
export class NameFieldComponent {
  constructor(private formState: FormStateService) {}
  
  onInput(event: Event): void {
    // Shares parent's FormStateService instance
    const value = (event.target as HTMLInputElement).value;
    this.formState.recordChange('name', value);
  }
}

@Component({
  selector: 'app-email-field',
  template: '<input (input)="onInput($event)">'
})
export class EmailFieldComponent {
  constructor(private formState: FormStateService) {}
  
  onInput(event: Event): void {
    // Shares same FormStateService instance as NameFieldComponent
    const value = (event.target as HTMLInputElement).value;
    this.formState.recordChange('email', value);
  }
}
```

Lazy loading introduces dynamic injector creation where Angular instantiates a new child module injector when the router loads a lazy module, establishing a distinct provider scope for that module's component tree. The lazy module's injector inherits from the root application injector, gaining access to root-scoped providers while isolating its own module-level providers from the rest of the application. This isolation prevents lazy module providers from polluting the root injector namespace and enables memory reclamation when users navigate away from the lazy feature, though in practice Angular rarely destroys lazy module injectors since router outlet caching typically keeps modules alive. Services provided in lazy modules that also inject root-scoped services create interesting dependency chains where the lazy service lives in the child injector but references singletons from the parent injector, mixing lifetime scopes in a single object graph.

The framework optimizes provider resolution through compile-time static analysis when AOT compilation analyzes the entire application graph. The compiler traces all injection sites, validates that providers exist in reachable injector scopes, and generates specialized factory functions that directly instantiate services in dependency order. These generated factories eliminate runtime reflection by hardcoding the constructor invocation sequence, transforming generic provider metadata into optimized JavaScript that executes with minimal overhead. For JIT compilation scenarios where the application compiles in the browser, Angular falls back to runtime reflection using TypeScript's decorator metadata, querying the `design:paramtypes` metadata attached to constructors to discover dependency types. This JIT path incurs higher overhead due to metadata parsing and dynamic factory creation, motivating the strong preference for AOT builds in production environments.

```typescript
// AOT-generated factory code mental model (simplified)
// Original component:
// @Component({ selector: 'app-root', providers: [DataService] })
// export class AppComponent {
//   constructor(private data: DataService) {}
// }

// Generated factory function (conceptual, not actual Angular output):
function AppComponentFactory() {
  // Resolve DataService from element injector
  let dataService = elementInjector.get(DataService);
  
  if (!dataService) {
    // Cache miss - invoke DataService factory
    const httpClient = moduleInjector.get(HttpClient);
    dataService = new DataService(httpClient);
    elementInjector.cache.set(DataService, dataService);
  }
  
  // Instantiate component with resolved dependencies
  return new AppComponent(dataService);
}

// Compiler eliminates reflection overhead by hardcoding dependency chain
// Runtime injector lookup replaced with direct constructor invocations
// Circular dependency detection happens at build time, not runtime
```

The injector tree's hierarchical structure creates a natural testing strategy where test harnesses override production providers by registering mocks at the TestBed's injector level. The TestBed creates an isolated root injector for each test case, allowing tests to provide mock implementations that shadow real services without affecting other tests or production code. Angular's testing utilities expose explicit APIs for configuring this test injector through `TestBed.configureTestingModule()`, where developers declare module imports, component declarations, and provider overrides. The testing framework applies these overrides at the root of the test injector hierarchy, ensuring that every component instantiated during the test receives mocked dependencies through normal resolution traversal. This mechanism preserves the application's actual dependency wiring while substituting concrete implementations, enabling high-fidelity integration tests that exercise real component logic against controlled service mocks.

## 3. High-Performance Optimization & Failure Modes

Provider scope selection directly impacts application performance through bundle size and runtime memory consumption. Root-scoped providers registered with `providedIn: 'root'` enable tree-shaking optimization where Angular's compiler eliminates unused services from production bundles when static analysis proves no components inject the service. The compiler traces injection sites through the component graph, marking reachable providers as required and pruning unreachable services during dead code elimination. This optimization only applies to services using `providedIn` metadata—providers declared in NgModule providers arrays cannot be tree-shaken because the compiler cannot statically prove whether external code might dynamically access the module's injector. Developers optimizing for minimal bundle size should prefer `providedIn: 'root'` over module-level provider arrays for all services that don't require module-specific scoping semantics.

Module-scoped provider declarations in lazy-loaded modules enable code splitting where the router defers loading feature bundles until users navigate to the corresponding route. Services declared in lazy module providers arrays remain excluded from the main bundle, loading only when the lazy chunk downloads. This strategy spreads application code across multiple bundles that load on demand, improving initial load performance by reducing the main bundle's byte count. The trade-off manifests as increased complexity in managing service lifetimes and shared state across module boundaries, since lazy module services live in isolated injector scopes that don't automatically share singleton instances with the root application. Developers shipping large applications should architect feature modules around lazy loading boundaries, carefully distinguishing between truly feature-specific services that belong in lazy modules versus core services that warrant root scope registration.

Component-scoped providers impose per-component instantiation overhead where Angular invokes the provider's factory function for every component instance. Applications rendering large lists of components with component-level providers incur multiplicative instantiation costs that degrade rendering performance. Virtual scrolling and trackBy optimization cannot eliminate this overhead since each visible component still requires its own service instance. The framework provides no automatic batching or pooling for component-scoped services, forcing developers to manually implement object pools or shared instances when instantiation costs dominate performance profiles. Profiling tools like Chrome DevTools Performance timeline reveal this overhead through clusters of constructor invocations during component creation, appearing as JavaScript execution spikes during list rendering or route transitions.

Circular dependencies between providers create unresolvable dependency graphs where service A's constructor requests service B while service B's constructor requests service A, forming a cycle that prevents any resolution order from satisfying both constructors. Angular's compiler detects these cycles during AOT compilation, emitting build errors with the full circular dependency chain. The framework cannot detect these cycles at runtime during JIT compilation until actual instantiation triggers the circular traversal, resulting in maximum call stack exceeded errors that crash the application. The resolution strategy involves breaking the cycle through lazy dependency injection using the `Injector` service directly, where one service retrieves its circular dependency on-demand after construction rather than through constructor injection. Alternatively, refactoring the dependency relationship to introduce a third service that both A and B depend upon eliminates the cycle by establishing a proper dependency hierarchy.

```typescript
// Circular dependency failure and resolution strategies
import { Injectable, Injector } from '@angular/core';

// BROKEN: Circular constructor dependency
@Injectable({ providedIn: 'root' })
export class ServiceA {
  constructor(private b: ServiceB) {}  // Requests B
}

@Injectable({ providedIn: 'root' })
export class ServiceB {
  constructor(private a: ServiceA) {}  // Requests A - cycle!
}
// Results in: Error: NG0200: Circular dependency in DI detected for ServiceA

// SOLUTION 1: Lazy injection via Injector
@Injectable({ providedIn: 'root' })
export class ServiceA {
  private _b?: ServiceB;
  
  constructor(private injector: Injector) {}
  
  get b(): ServiceB {
    // Defer B's resolution until after A's construction completes
    if (!this._b) {
      this._b = this.injector.get(ServiceB);
    }
    return this._b;
  }
}

@Injectable({ providedIn: 'root' })
export class ServiceB {
  constructor(private a: ServiceA) {}
}

// SOLUTION 2: Refactor through shared dependency
@Injectable({ providedIn: 'root' })
export class SharedState {
  readonly config = { feature: 'enabled' };
}

@Injectable({ providedIn: 'root' })
export class ServiceA {
  constructor(private state: SharedState) {}
}

@Injectable({ providedIn: 'root' })
export class ServiceB {
  constructor(private state: SharedState) {}
}
```

Provider token collisions occur when multiple providers register the same token in overlapping injector scopes, creating ambiguous resolution behavior where the chosen provider depends on injector hierarchy traversal order. String-based injection tokens particularly suffer from this issue since disparate modules might independently declare providers for generic token names like `'config'` or `'API_URL'`, causing unintended shadowing when modules compose. The framework resolves these collisions through last-registration-wins semantics at a given injector level and child-shadows-parent semantics across injector boundaries, but these rules create brittle configurations that break when module import order changes. The robust solution employs opaque `InjectionToken` instances exported from a shared module, ensuring token uniqueness through JavaScript object identity rather than string comparison. Each module imports the token definition and registers providers using the shared token instance, eliminating collision risk through namespace discipline.

Missing provider errors represent the most common DI failure mode, occurring when a component requests a dependency that no reachable injector provides. Angular throws `NullInjectorError` with a diagnostic message showing the injection token and the component's position in the tree, but the error often obscures the root cause when developers misunderstand injector scope boundaries. Components attempting to inject module-scoped services provided in a different lazy module fail because the injector hierarchies remain isolated—the requesting component's module injector cannot reach the lazy module's injector since they branch from different points in the tree. The resolution requires either promoting the shared service to root scope through `providedIn: 'root'`, or restructuring the module graph so both features import a shared module that provides the service. Static analysis tools and strict TypeScript configurations help catch these errors during development, but runtime failures still occur when dynamic module loading patterns circumvent compile-time validation.

Optional dependencies using the `@Optional` decorator provide graceful degradation when providers might not exist in all configurations, allowing components to adapt behavior based on service availability. This pattern enables feature detection where components check whether an optional service resolved to a non-null value, activating enhanced functionality when the service exists and falling back to basic behavior otherwise. The framework injects `null` for unresolved optional dependencies, requiring explicit null checks before service access. Optional dependencies particularly suit plugin architectures where core components conditionally integrate with optional feature modules, maintaining loose coupling between core and plugin code. The pattern incurs minimal overhead since the injector's null-return path avoids factory invocation, though excessive optional dependencies complicate testing by expanding the test case matrix across all service presence combinations.

```typescript
// Optional dependency pattern for feature detection
import { Component, Optional } from '@angular/core';
import { AnalyticsService } from './analytics.service';
import { ExperimentalFeatureService } from './experimental.service';

@Component({
  selector: 'app-feature',
  template: '<div>Feature content</div>'
})
export class FeatureComponent implements OnInit {
  constructor(
    // Analytics might not be configured in development environments
    @Optional() private analytics: AnalyticsService | null,
    
    // Experimental features only available when feature flag enabled
    @Optional() private experimental: ExperimentalFeatureService | null
  ) {}
  
  ngOnInit(): void {
    // Gracefully degrade when analytics unavailable
    this.analytics?.trackPageView('feature');
    
    // Conditionally enable experimental behavior
    if (this.experimental) {
      console.log('Experimental features active');
      this.experimental.enableAdvancedMode();
    }
  }
  
  onUserAction(): void {
    // Defensive programming for optional dependencies
    if (this.analytics) {
      this.analytics.trackEvent('user_action');
    }
  }
}
```

Injector scope leaks manifest when long-lived services inadvertently capture references to component-scoped services, preventing garbage collection of component trees and causing memory leaks in long-running applications. This failure mode emerges from event subscriptions where root-scoped services register callbacks that close over component-scoped dependencies, maintaining references beyond the component's intended lifetime. Angular's change detection and zone.js integration exacerbate this issue by keeping all registered callbacks alive until explicitly unsubscribed, creating subtle leaks that accumulate across component instantiation cycles. The mitigation pattern employs RxJS `takeUntil` operators that automatically unsubscribe when a component-scoped subject emits during `ngOnDestroy`, or manual subscription tracking through an array of `Subscription` objects that get batch-unsubscribed during cleanup. Memory profiling tools like Chrome DevTools Heap Snapshots reveal these leaks through growing retained sizes for component instances that should have been garbage collected after navigation events.

Provider override hierarchies enable dynamic service customization but introduce complexity around testing and runtime configuration. The shadowing mechanism where child injectors override parent providers creates implicit configuration layers that become difficult to reason about when overrides span multiple hierarchy levels. Deep override chains where a lazy module overrides a root provider, then a component overrides the lazy module's provider, result in three distinct instances for the same logical service token, often surprising developers expecting singleton behavior. The framework provides no runtime introspection API to query the active provider for a given token at a specific injector level, forcing developers to manually track override configurations through documentation or wrapper services. Testing scenarios multiply exponentially when exercising all override combinations, motivating strict conventions around where providers may be registered to limit scope proliferation.

Platform-level provider registration enables sharing services across multiple Angular applications running on the same page, though this advanced pattern rarely appears in typical applications. The platform injector sits above the root application injector in the hierarchy, hosting services like the Angular compiler and zone.js integration that must remain singleton across application boundaries. Custom platform-level providers support micro-frontend architectures where multiple independent Angular applications coordinate through shared platform services, avoiding duplicate service instantiation and enabling cross-application communication. The registration mechanism requires explicitly creating platform providers through `platformBrowserDynamic()` API configuration, bypassing normal module-level provider declarations. This pattern introduces significant complexity around service lifecycle management and version skew between applications sharing the platform injector, warranting use only in sophisticated micro-frontend deployments with mature coordination protocols.

Ahead-of-time compilation optimization eliminates nearly all DI runtime overhead by generating specialized factory functions that hardcode the dependency resolution graph. The AOT compiler analyzes provider declarations at build time, topologically sorts dependencies, and emits direct constructor invocation chains that bypass the generic injector resolution algorithm. Production applications should always use AOT builds to maximize runtime performance, though this optimization precludes dynamic provider registration patterns that some applications employ for plugin architectures. The compiler's static analysis detects most provider configuration errors during the build, failing fast with detailed diagnostic messages rather than allowing runtime failures to reach users. Tree-shaking integration during the AOT build process eliminates unused providers from the bundle, sometimes achieving 30-50% bundle size reductions for applications with many optional services. Developers should profile production bundles using source map explorers to identify services incorrectly marked as reachable, then refactor provider registration to use `providedIn` metadata instead of module provider arrays to unlock tree-shaking optimization.
