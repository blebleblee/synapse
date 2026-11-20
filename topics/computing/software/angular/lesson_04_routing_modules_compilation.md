# Lesson 4: Router Architecture, Module System, AOT Compilation

## 1. First-Principles Intuition & Invariants

Angular's router subsystem represents a sophisticated state machine that synchronizes browser history API mutations with component tree transformations, all while maintaining the illusion of a multi-page application within a single-page architecture. At its core, the router solves a deceptively complex problem: how do we declaratively map URL segments to component activation lifecycles, manage asynchronous data dependencies before rendering, enforce authorization constraints at navigation boundaries, and accomplish all of this while preserving browser semantics like back-button navigation and deep-linking? The solution Angular provides is a multi-phase pipeline that treats route transitions as transactions, where each phase can veto the navigation, load data, or transform state before committing the new component tree to the DOM.

The router's design reflects a fundamental tension in single-page application frameworks. On one hand, we want declarative route configuration that resembles traditional server-side routing tables—clean mappings from URL patterns to handlers. On the other hand, we need imperative control over the navigation lifecycle to handle authentication checks, data prefetching, unsaved form warnings, and conditional redirects. Angular resolves this by modeling routes as a tree structure that mirrors the component hierarchy, then executing a well-defined sequence of guards and resolvers during each navigation event. This approach ensures that by the time a component's constructor executes, all preconditions have been satisfied and all required data has been loaded, eliminating the awkward loading states and race conditions that plague naïve client-side routing implementations.

The invariants that govern Angular's router are precise and non-negotiable. First, navigation is transactional: either the entire route transition succeeds and the new component tree replaces the old, or the navigation is cancelled and the application remains in its prior state. There are no partial navigations where some components update while others remain stale. Second, the router enforces a strict ordering of lifecycle phases—guards evaluate before resolvers execute, resolvers complete before components instantiate, and the component tree activates atomically. Third, the router maintains bidirectional synchronization with the browser's history API, ensuring that programmatic navigation via `Router.navigate()` updates the URL bar and produces history entries, while browser-initiated navigation via back/forward buttons or direct URL manipulation triggers the same guard-resolver-activation pipeline. This bidirectional contract is what allows Angular applications to behave like traditional multi-page applications from the user's perspective while retaining full control over the rendering pipeline.

Angular's module system, built atop ECMAScript modules but extended with framework-specific semantics, serves as the compilation and dependency injection boundary. An NgModule is fundamentally a declaration of a closed world—it specifies which components, directives, and pipes exist within that world, which services are available via dependency injection, and how that world composes with other worlds through imports and exports. The module system's primary purpose is to enable ahead-of-time compilation by providing the compiler with complete static knowledge of all possible dependencies at build time. Without this closed-world assumption, the compiler would need to generate code that could handle any possible component being injected at runtime, leading to massive bundle sizes and runtime overhead. By forcing developers to declare all dependencies explicitly in module metadata, Angular's AOT compiler can perform whole-program optimization, tree-shake unused code, and generate optimized factory functions that construct components with minimal runtime overhead.

The introduction of the Ivy rendering engine in Angular version 9 marked a fundamental shift in the compilation model, moving from a global compilation strategy to a locality principle where each component compiles independently. Prior to Ivy, Angular's View Engine compiler would analyze an entire NgModule, build a complete dependency graph, and generate a single monolithic factory that orchestrated the construction of all components, directives, and pipes within that module. This approach required perfect static knowledge and made incremental compilation impossible—changing a single component required recompiling the entire module. Ivy inverts this model by making each component's compiled output self-contained, with all dependencies resolved through local references or dependency injection. The compiler emits a static component definition (`ɵcmp`) that contains all the instructions needed to instantiate that component's view, query its children, and bind its inputs and outputs, without any references to external factory functions. This locality principle enables true incremental compilation, reduces memory usage during builds, and makes the compiled JavaScript output more amenable to standard tree-shaking tools like Terser and Rollup.

The AOT compiler's tree-shaking capability derives from its ability to generate static code that modern JavaScript bundlers can analyze. When the compiler sees that a component is never referenced in any route configuration or parent template, it can elide the component definition entirely from the final bundle. More subtly, when a directive's selector cannot possibly match any elements in the application's templates, the compiler can omit that directive's factory. This dead-code elimination extends to service providers as well: if a service is provided in an NgModule that is never imported, and that service is not reachable through any component's constructor, the service implementation can be pruned. The key insight is that AOT compilation transforms Angular's declarative metadata into static JavaScript code whose data-flow properties are visible to standard compiler optimization passes. The `providedIn: 'root'` pattern for services takes this further by inverting the dependency relationship—instead of the module listing all its providers, each service declares which injector scope it belongs to, allowing the tree-shaker to eliminate the service if no component ever injects it.

## 2. Core Architecture & Mechanics

The router's internal architecture centers on the `Router` service, which orchestrates a pipeline of pure functions that transform a URL string into an activated component tree. When a navigation begins—whether triggered by clicking a `routerLink`, calling `router.navigate()`, or the user pressing the back button—the router captures the target URL and begins constructing a `UrlTree`, which is an immutable data structure representing the parsed URL segments, matrix parameters, query parameters, and fragment. The `UrlTree` structure mirrors the nested nature of routes, with primary and auxiliary outlets forming a tree where each node represents a segment and its associated parameters. This parsing phase is entirely synchronous and produces a canonical representation of the target state, divorced from the current component tree.

```text
Navigation Pipeline:

URL String
    ↓
[Parse] → UrlTree (segments + params)
    ↓
[Recognize] → RouterStateSnapshot (matched routes)
    ↓
[Guards: CanDeactivate] → boolean | UrlTree
    ↓
[Guards: CanLoad] → boolean | UrlTree
    ↓
[Guards: CanActivate] → boolean | UrlTree
    ↓
[Guards: CanActivateChild] → boolean | UrlTree
    ↓
[Resolvers] → { [key: string]: any }
    ↓
[Activate] → Update Component Tree + History API
    ↓
NavigationEnd Event
```

The recognition phase applies the route configuration tree to the `UrlTree` to produce a `RouterStateSnapshot`, which captures the matched routes, their parameters, and the component types that should be instantiated. Recognition walks the route configuration depth-first, attempting to match each URL segment against the path patterns defined in the configuration. When a route contains child routes, recognition recursively matches the remaining segments against the children. The matcher supports static segments (`/users`), parameterized segments (`/users/:id`), and wildcard segments (`**`), with precedence rules that prefer static matches over parameterized matches and match routes in configuration order. Auxiliary routes introduce additional complexity: the recognition phase must match multiple parallel URL trees simultaneously, one for each named outlet, ensuring that all outlets resolve to valid component states or the entire navigation fails atomically.

Guards implement the policy layer of navigation control. Each guard is a service that implements one of the guard interfaces—`CanDeactivate`, `CanLoad`, `CanActivate`, `CanActivateChild`, or `CanMatch`—and returns a boolean, a `UrlTree` for redirection, or an observable/promise that eventually resolves to one of those types. The router executes guards in a specific order designed to minimize side effects and optimize performance. `CanDeactivate` guards run first, giving the current route an opportunity to veto the navigation—this is where you implement unsaved changes warnings. `CanLoad` guards execute before lazy-loading a module's JavaScript bundle, preventing unnecessary network requests if authorization fails. `CanActivate` guards run after the route is loaded but before the component is instantiated, making them ideal for authentication checks. `CanActivateChild` guards apply to all child routes, allowing a parent route to enforce policies on its entire subtree. The newer `CanMatch` guards execute during route recognition itself, enabling route selection based on runtime conditions like feature flags or user roles.

The guard execution model is fully asynchronous and handles both synchronous and asynchronous guards uniformly through RxJS operators. The router collects all guards for a given phase into an array, then uses `concatMap` and `every` operators to execute them sequentially, short-circuiting on the first guard that returns false or a redirect `UrlTree`. This sequential execution ensures predictable ordering and prevents race conditions when multiple guards need to access shared state. If any guard returns a `UrlTree`, the router treats this as a redirect and begins a new navigation to that URL, running through the entire pipeline again. This redirect mechanism is powerful but requires care: if a guard redirects to a URL that triggers the same guard, you create an infinite loop that the router will eventually detect and abort with a navigation error.

Route resolvers address the data-loading problem by allowing you to fetch data before a component activates. A resolver is a service implementing the `Resolve` interface with a `resolve()` method that returns the data directly or as an observable/promise. The router invokes all resolvers for a route in parallel (unlike guards, which run sequentially), waits for all of them to complete, and then merges their results into the `ActivatedRoute.data` observable. This design eliminates the loading-state problem: by the time your component's `ngOnInit` hook runs, `route.data` contains all resolved values, and your component can render immediately without showing spinners. The parallel execution of resolvers is an important performance optimization—if you have multiple independent data sources (user profile, permissions, application settings), the router will fetch them concurrently rather than waterfalling the requests.

```typescript
// Complete route configuration demonstrating guards and resolvers

export interface UserData {
  id: number;
  name: string;
  email: string;
  permissions: string[];
}

@Injectable({ providedIn: 'root' })
export class AuthGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean | UrlTree> {
    return this.authService.isAuthenticated$.pipe(
      map(isAuthenticated => {
        if (isAuthenticated) {
          return true;
        }
        return this.router.createUrlTree(['/login'], {
          queryParams: { returnUrl: state.url }
        });
      })
    );
  }
}

@Injectable({ providedIn: 'root' })
export class UnsavedChangesGuard implements CanDeactivate<EditComponent> {
  canDeactivate(
    component: EditComponent,
    currentRoute: ActivatedRouteSnapshot,
    currentState: RouterStateSnapshot,
    nextState?: RouterStateSnapshot
  ): Observable<boolean> | boolean {
    if (component.hasUnsavedChanges()) {
      return confirm('You have unsaved changes. Discard them?');
    }
    return true;
  }
}

@Injectable({ providedIn: 'root' })
export class UserResolver implements Resolve<UserData> {
  constructor(private userService: UserService) {}

  resolve(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<UserData> {
    const userId = route.paramMap.get('id');
    return this.userService.getUser(userId).pipe(
      catchError(error => {
        console.error('User load failed:', error);
        return of({
          id: 0,
          name: 'Unknown',
          email: '',
          permissions: []
        });
      })
    );
  }
}

export const routes: Routes = [
  {
    path: '',
    redirectTo: '/dashboard',
    pathMatch: 'full'
  },
  {
    path: 'dashboard',
    component: DashboardComponent,
    canActivate: [AuthGuard]
  },
  {
    path: 'users',
    canActivateChild: [AuthGuard],
    children: [
      {
        path: '',
        component: UserListComponent
      },
      {
        path: ':id',
        component: UserDetailComponent,
        resolve: {
          user: UserResolver
        }
      },
      {
        path: ':id/edit',
        component: EditComponent,
        canDeactivate: [UnsavedChangesGuard],
        resolve: {
          user: UserResolver
        }
      }
    ]
  },
  {
    path: 'admin',
    loadChildren: () => import('./admin/admin.module').then(m => m.AdminModule),
    canLoad: [AdminGuard]
  },
  {
    path: '**',
    component: NotFoundComponent
  }
];
```

The module system's mechanics revolve around the `NgModule` decorator and its metadata properties. The `declarations` array specifies components, directives, and pipes that belong to this module's compilation scope—these are the constructs available in templates within this module. The `imports` array brings in other modules, merging their exports into this module's compilation scope and making their providers available for dependency injection. The `exports` array specifies which declarations should be visible to other modules that import this module, creating a controlled API surface. The `providers` array configures dependency injection, registering services that will be instantiated by the module's injector. These metadata properties define the static boundaries that the AOT compiler analyzes to generate optimized code.

The lazy-loading mechanism exploits the module system's boundaries to enable code splitting. When you configure a route with `loadChildren` instead of `component`, you provide a function that returns a dynamic import promise. The router converts this into a JavaScript bundle boundary: the AOT compiler will place that module and all its dependencies into a separate chunk that is only loaded when the user navigates to that route. This code splitting is automatic and effective because NgModules form natural bundle boundaries—a lazy module and its imports form a dependency subgraph that can be severed from the main bundle. The router coordinates with Webpack or the Angular CLI's bundler to ensure that shared dependencies (like common libraries used by multiple lazy modules) are factored out into a shared chunk, avoiding duplication.

The Ivy compiler's output for a component consists of a static component definition that contains a template function, a selector, input/output bindings, and view query definitions. The template function is a closure that receives a rendering context (the component instance) and emits a sequence of instruction calls that construct the view. These instructions—`ɵɵelementStart`, `ɵɵtext`, `ɵɵproperty`, `ɵɵlistener`—are imported from `@angular/core` and form a low-level intermediate representation that the runtime interpreter executes to build the DOM. The instruction set is designed for compactness and performance: each instruction does minimal work and has a small bytecode footprint, and the runtime maintains an implicit stack of parent elements to avoid passing context through every call.

```typescript
// Conceptual Ivy compiler output for a simple component

@Component({
  selector: 'app-user-card',
  template: `
    <div class="card">
      <h2>{{ user.name }}</h2>
      <p>{{ user.email }}</p>
      <button (click)="onEdit()">Edit</button>
    </div>
  `
})
export class UserCardComponent {
  @Input() user!: { name: string; email: string };
  @Output() edit = new EventEmitter<void>();

  onEdit() {
    this.edit.emit();
  }
}

// Compiled output (simplified for illustration)
export class UserCardComponent {
  static ɵfac = function UserCardComponent_Factory(t) {
    return new (t || UserCardComponent)();
  };

  static ɵcmp = /*@__PURE__*/ ɵɵdefineComponent({
    type: UserCardComponent,
    selectors: [['app-user-card']],
    inputs: { user: 'user' },
    outputs: { edit: 'edit' },
    decls: 6,
    vars: 2,
    consts: [[1, 'card'], [3, 'click']],
    template: function UserCardComponent_Template(rf, ctx) {
      if (rf & 1) { // Creation pass
        ɵɵelementStart(0, 'div', 0);
          ɵɵelementStart(1, 'h2');
            ɵɵtext(2);
          ɵɵelementEnd();
          ɵɵelementStart(3, 'p');
            ɵɵtext(4);
          ɵɵelementEnd();
          ɵɵelementStart(5, 'button', 1);
            ɵɵlistener('click', function UserCardComponent_Template_button_click_5_listener() {
              return ctx.onEdit();
            });
            ɵɵtext(6, 'Edit');
          ɵɵelementEnd();
        ɵɵelementEnd();
      }
      if (rf & 2) { // Update pass
        ɵɵadvance(2);
        ɵɵtextInterpolate(ctx.user.name);
        ɵɵadvance(2);
        ɵɵtextInterpolate(ctx.user.email);
      }
    }
  });
}
```

The template function's two-pass rendering strategy—a creation pass that builds the DOM structure and an update pass that binds dynamic values—is central to Ivy's performance characteristics. During the creation pass (indicated by `rf & 1`), the template function emits instructions that construct elements, attach listeners, and set static attributes. This pass runs only once when the component is first created. During the update pass (indicated by `rf & 2`), the template function emits instructions that update text nodes, element properties, and class/style bindings based on the component's current state. Change detection triggers the update pass, but the creation pass never runs again unless the component is destroyed and recreated. This separation allows the runtime to skip creation overhead during change detection cycles and focus only on updating bindings that might have changed.

The `ɵɵadvance` instruction is a pointer manipulation that moves the runtime's current element cursor forward by a specified number of nodes in the flat node list. This instruction is pure optimization: instead of passing node references through every binding instruction, the runtime maintains an implicit cursor that tracks the current position in the view. This reduces the instruction size and improves cache locality—the flat node list is a compact array that fits in L1 cache, while passing explicit references would require dereferencing pointers scattered across the heap.

## 3. High-Performance Optimization & Failure Modes

Performance optimization in Angular's router begins with understanding the cost structure of navigation. The most expensive operation is typically guard execution, especially when guards perform HTTP requests or complex authorization checks. The sequential execution model means that a slow guard at the beginning of the pipeline blocks all subsequent phases, even if those phases would ultimately fail. To optimize this, you should order guards from cheapest to most expensive and from most likely to fail to least likely to fail. For example, place a synchronous role-check guard before an asynchronous permission-fetch guard. If the role check fails, you avoid the network request entirely. Similarly, use `CanLoad` guards for lazy modules to prevent downloading JavaScript bundles that the user cannot access—a `CanLoad` guard that checks local authentication state saves both CPU time (compilation of the module) and bandwidth (downloading the bundle).

Resolver optimization requires recognizing that resolvers block navigation until all data is loaded. This is desirable when the data is critical for rendering the component, but it becomes a liability when resolvers fetch optional data or data that could be loaded progressively. The best practice is to resolve only the minimal data required for the initial render and fetch supplementary data in `ngOnInit` using the component's lifecycle. For example, a user profile resolver might fetch just the user's name and ID, while the component's `ngOnInit` fetches the user's activity history in the background. This hybrid approach gives you fast navigation (the resolver completes quickly) without sacrificing data completeness (the component loads additional data after activation).

Caching resolver data is essential for performance when users navigate back and forth between routes. Angular's router does not cache resolver data by default—each navigation triggers fresh resolver executions. You can implement caching by storing resolved data in a service with appropriate cache invalidation logic. A simple time-based cache works for relatively static data: check if the cached data is less than five minutes old and return it immediately, otherwise fetch fresh data. For user-triggered mutations, invalidate the relevant cache entries explicitly. The router's `RouteReuseStrategy` provides a more sophisticated caching mechanism: it allows you to control whether route components are destroyed and recreated during navigation. By implementing a custom reuse strategy, you can tell the router to preserve component instances when navigating away and restore them when navigating back, eliminating both resolver execution and component initialization overhead.

```typescript
// Advanced RouteReuseStrategy for component-level caching

export interface RouteStorageObject {
  snapshot: ActivatedRouteSnapshot;
  handle: DetachedRouteHandle;
}

@Injectable({ providedIn: 'root' })
export class CustomReuseStrategy implements RouteReuseStrategy {
  private storedRoutes = new Map<string, RouteStorageObject>();

  shouldDetach(route: ActivatedRouteSnapshot): boolean {
    // Only cache routes explicitly marked with data.reuse = true
    return route.data['reuse'] === true;
  }

  store(route: ActivatedRouteSnapshot, handle: DetachedRouteHandle | null): void {
    if (handle && route.data['reuse']) {
      const key = this.getRouteKey(route);
      this.storedRoutes.set(key, { snapshot: route, handle });
    }
  }

  shouldAttach(route: ActivatedRouteSnapshot): boolean {
    const key = this.getRouteKey(route);
    return this.storedRoutes.has(key);
  }

  retrieve(route: ActivatedRouteSnapshot): DetachedRouteHandle | null {
    const key = this.getRouteKey(route);
    const stored = this.storedRoutes.get(key);
    return stored ? stored.handle : null;
  }

  shouldReuseRoute(future: ActivatedRouteSnapshot, curr: ActivatedRouteSnapshot): boolean {
    // Default behavior: reuse if the route configuration is the same
    return future.routeConfig === curr.routeConfig;
  }

  private getRouteKey(route: ActivatedRouteSnapshot): string {
    // Create a unique key that includes path and parameters
    const path = route.pathFromRoot
      .map(r => r.url.map(segment => segment.toString()).join('/'))
      .join('/');
    const params = JSON.stringify(route.params);
    return `${path}?${params}`;
  }

  clearCache(): void {
    this.storedRoutes.clear();
  }
}

// Usage in route configuration
export const routes: Routes = [
  {
    path: 'expensive-list',
    component: ExpensiveListComponent,
    data: { reuse: true }, // This component will be cached
    resolve: {
      items: ExpensiveListResolver
    }
  }
];
```

Module system optimization centers on minimizing bundle size through effective tree-shaking and code splitting. The key insight is that the unit of tree-shaking is the ECMAScript module, not the NgModule. When you import a component from a barrel file (an `index.ts` that re-exports multiple modules), you create a bundler dependency on that entire file and everything it imports. To maximize tree-shaking, import directly from the source file: `import { UserComponent } from './user.component'` instead of `import { UserComponent } from './components'`. This allows the bundler to see that you only need `user.component.ts` and can ignore all other files in that directory.

The `providedIn: 'root'` pattern for services is preferable to module-level providers because it enables tree-shaking of unused services. When a service uses `providedIn: 'root'`, the compiler emits code that registers the service with the root injector only if some component injects it. If no component requests the service, the entire service class and its dependencies can be eliminated from the bundle. In contrast, when you list a service in a module's `providers` array, the module takes a hard dependency on that service and it will be included in the bundle regardless of usage. The only time you should use module-level providers is when you need a different instance of the service for each lazy-loaded module (scoped providers) or when you need to use factory functions with complex initialization logic.

Lazy loading effectiveness depends on maximizing the size difference between the main bundle and lazy bundles. Small lazy bundles (under 50 KB) provide minimal benefit because the parsing and evaluation time for the JavaScript is comparable to the overhead of the router's lazy-loading mechanism. To create meaningful lazy bundles, aggregate related features into feature modules and lazy-load the entire feature. For example, instead of lazy-loading individual admin components, create an admin feature module that contains all admin-related components, services, and routes, resulting in a single large lazy bundle. The router's `preloadingStrategy` option allows you to preload lazy bundles in the background after the initial application has loaded, eliminating the latency on first access while still benefiting from code splitting. The `PreloadAllModules` strategy works well for applications where users are likely to visit most routes during a session, while a custom selective preloading strategy can prioritize specific high-traffic routes.

```typescript
// Custom selective preloading strategy

@Injectable({ providedIn: 'root' })
export class SelectivePreloadingStrategy implements PreloadingStrategy {
  preloadedModules: string[] = [];

  preload(route: Route, load: () => Observable<any>): Observable<any> {
    if (route.data && route.data['preload']) {
      console.log('Preloading:', route.path);
      this.preloadedModules.push(route.path || '');
      return load();
    }
    return of(null);
  }
}

// Router configuration with preloading
export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(
      routes,
      withPreloading(SelectivePreloadingStrategy),
      withDebugTracing() // Enable for debugging navigation events
    )
  ]
};

// Route with preload flag
export const routes: Routes = [
  {
    path: 'dashboard',
    loadChildren: () => import('./dashboard/dashboard.module').then(m => m.DashboardModule),
    data: { preload: true } // This module will be preloaded
  },
  {
    path: 'settings',
    loadChildren: () => import('./settings/settings.module').then(m => m.SettingsModule)
    // No preload flag - will only load on demand
  }
];
```

AOT compilation optimization requires understanding the compiler's constraint system. The compiler must be able to statically evaluate all decorator metadata at build time, which means you cannot use dynamic expressions in component decorators. For example, you cannot compute the template URL based on an environment variable because that variable's value is unknown at compile time. Similarly, you cannot use spread operators or computed property names in component metadata. These restrictions exist because the compiler performs constant folding and dead code elimination during compilation—it needs concrete values to generate optimal code. When you violate these constraints, the compiler either falls back to less-optimized code generation or emits a build error.

The compiler's template type-checking feature catches many errors at build time that would otherwise manifest as runtime failures. Angular supports three template type-checking modes: basic, full, and strict. Basic mode only checks property bindings, full mode adds method call validation, and strict mode enables full template type checking equivalent to TypeScript's strict mode. Strict template checking catches errors like calling methods with incorrect argument types, referencing non-existent properties in templates, and using the wrong type in event handlers. The type checker works by generating a TypeScript file that contains expressions corresponding to each template binding, then running the TypeScript compiler on those generated files. This technique allows Angular to leverage TypeScript's sophisticated type inference and error reporting without implementing a separate type system.

Common failure modes in the router typically involve asynchronous timing issues. A frequent mistake is navigating during guard execution, which creates nested navigation contexts that interfere with each other. If a `CanActivate` guard calls `router.navigate()`, the router will start a new navigation before the current navigation completes, and the current navigation will be cancelled. This is usually not what you want—instead, return a `UrlTree` from the guard to redirect declaratively. Another timing issue arises when guards or resolvers have side effects that depend on the navigation completing. For example, if a resolver dispatches a Redux action that updates the store, and a component's `ngOnInit` hook reads from that store, you might get stale data because the resolver's side effect hasn't propagated yet. The solution is to avoid side effects in resolvers and instead return the data directly, letting the component decide how to integrate it into application state.

Memory leaks in routed components occur when subscriptions are not cleaned up in `ngOnDestroy`. The most common culprit is subscribing to an observable in `ngOnInit` and not unsubscribing when the component is destroyed. Angular's router destroys and recreates components during navigation, so a component that is navigated to repeatedly will create multiple subscription instances, each of which continues to consume memory and process events until explicitly unsubscribed. The idiomatic solution is to use the `async` pipe in templates whenever possible, as it handles subscription lifecycle automatically. When you must subscribe imperatively, store the subscription and unsubscribe in `ngOnDestroy`, or use RxJS operators like `takeUntil` with a subject that emits on destruction.

```typescript
// Pattern for safe subscription management

@Component({
  selector: 'app-user-detail',
  template: `
    <div *ngIf="user$ | async as user">
      <h1>{{ user.name }}</h1>
      <p>{{ user.email }}</p>
    </div>
  `
})
export class UserDetailComponent implements OnInit, OnDestroy {
  user$!: Observable<UserData>;
  private destroy$ = new Subject<void>();

  constructor(
    private route: ActivatedRoute,
    private userService: UserService
  ) {}

  ngOnInit() {
    // Pattern 1: async pipe (preferred - no manual cleanup needed)
    this.user$ = this.route.data.pipe(
      map(data => data['user'])
    );

    // Pattern 2: takeUntil for imperative subscriptions
    this.route.paramMap.pipe(
      takeUntil(this.destroy$),
      switchMap(params => {
        const id = params.get('id');
        return this.userService.getUser(id);
      })
    ).subscribe(user => {
      console.log('User loaded:', user);
      // Side effects here
    });
  }

  ngOnDestroy() {
    // Signal all subscriptions to complete
    this.destroy$.next();
    this.destroy$.complete();
  }
}
```

The module system's failure mode typically involves circular dependencies and improper import ordering. When two modules import each other, either directly or transitively through a chain of imports, the JavaScript module loader cannot determine initialization order and may execute module code before its dependencies are ready. This manifests as `undefined` references or components that fail to register. The solution is to restructure your module hierarchy to eliminate cycles, often by extracting shared code into a third module that both original modules import. Angular's compiler will detect some circular dependencies at build time and emit warnings, but runtime detection requires careful examination of import graphs.

Tree-shaking failures happen when you inadvertently create references to code you want to eliminate. The most common cause is barrel files that import side-effect-causing modules. For example, if your `index.ts` imports a module that executes code at the top level (registering a global event handler, configuring a third-party library), then importing anything from that barrel file will pull in the side-effect code. The bundler cannot eliminate it because it cannot prove the side effect is unused. The solution is to avoid side effects in module-level code and mark truly safe side-effect-only files with the `/*#__PURE__*/` annotation, which signals to the bundler that the code can be safely eliminated if its exports are unused.

The production build process combines multiple optimization passes: AOT compilation, tree-shaking via Rollup or Webpack, minification with Terser, and compression with Brotli or Gzip. Each pass requires the previous pass to succeed and produce analyzable output. AOT compilation must generate code that preserves semantic meaning while being amenable to tree-shaking—this is why Ivy's instruction-based output is pure function calls rather than class instantiations or complex object literals. Tree-shaking must eliminate dead code without breaking runtime invariants—this is why Angular's decorators and metadata must resolve to static values. Minification must rename symbols without breaking references across module boundaries—this is why Angular's public API exports are carefully managed and private APIs are annotated with `ɵ` prefixes. The entire pipeline is a carefully orchestrated sequence of transformations, each one making assumptions about the invariants preserved by prior transformations. Understanding this pipeline allows you to diagnose production build failures and optimize for minimal bundle size.
