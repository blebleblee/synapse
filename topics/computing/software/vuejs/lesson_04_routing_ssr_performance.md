# Lesson 4: Routing, Server-Side Rendering, and Performance Optimization

## 1. First-Principles Intuition & Invariants

The browser's address bar is, at its core, a state machine. Every URL encodes application state—not merely the page the user is viewing, but the data they expect to see, the access level they hold, and the history they can navigate. When the web moved from server-rendered documents to single-page applications, the routing problem shifted from the HTTP server to the JavaScript runtime. The URL still had to work: bookmarks, back buttons, link sharing, and deep linking all depend on the address bar reflecting meaningful, stable application state. Vue Router is the mechanism by which Vue applications satisfy this contract.

Understanding Vue Router at a first-principles level means recognizing that it operates as a client-side state machine layered on top of the History API. `window.history.pushState` and `window.history.replaceState` allow JavaScript to mutate the browser's URL and history stack without issuing a network request. The `popstate` event fires when the user navigates back or forward. Vue Router wraps these primitives into a reactive routing layer: the current route is a reactive object injected into every component, so any component that reads `route.params.id` will re-render automatically when the route changes. This is not magic—it is Vue's reactivity system (the `ref` and `reactive` machinery built on `Proxy` traps) applied to routing state.

The first invariant of any routing system is that navigation must be a first-class, interceptable operation. Navigating from `/invoices` to `/invoices/42` involves more than swapping a component—it may require authentication checks, data prefetching, dirty-state confirmation dialogs, or analytics events. Vue Router exposes this through navigation guards: hooks that run synchronously or asynchronously during the navigation lifecycle before the DOM ever changes. The pipeline of guards gives you a formally ordered sequence of opportunities to cancel, redirect, or augment navigation.

Server-side rendering introduces a second invariant: the initial render must be deterministic and reproducible on two separate runtimes—Node.js and the browser—from identical application state. This is what makes SSR architecturally non-trivial. The server renders HTML from Vue component trees, serializes the state that produced that HTML, ships both to the browser, and the browser must then "hydrate"—attach event listeners and reactive bindings—to that existing DOM without re-rendering it from scratch. If the server state and client state diverge by even a single character, the hydration fails silently or loudly, and you get either broken interactivity or a full client-side re-render that destroys the performance benefits you paid for with SSR in the first place.

Performance optimization in a Vue application is ultimately about two things: reducing the amount of JavaScript the browser must parse and execute before the application becomes interactive, and reducing the amount of work Vue's runtime must perform on each render cycle. These goals are related but distinct. Bundle splitting addresses the first; memoization, `v-memo`, computed property caching, and virtual DOM optimization address the second. Senior engineers must hold both dimensions in mind simultaneously, because a perfectly optimized runtime that ships 2MB of JavaScript on first load is still a poor production system.

---

## 2. Core Architecture & Mechanics

### The Navigation Pipeline and Guard Execution Order

Vue Router's navigation pipeline is a linear sequence of hooks executed in a fixed order. The router resolves the target route record first—matching the new URL against the route configuration tree—and then runs guards in this order:

1. Component `beforeRouteLeave` on the component being left
2. Global `beforeEach` guards
3. Component `beforeRouteUpdate` on reused components
4. Route-level `beforeEnter` guards
5. Async component resolution (lazy-loaded route components are fetched here)
6. Component `beforeRouteEnter` in the entering component
7. Global `beforeResolve` guards
8. Navigation confirmed; global `afterEach` hooks fire

The pipeline is sequential and async-aware. Each guard receives `(to, from)` and can return `false` to abort, a route location object to redirect, or nothing (or `true`) to proceed. This design gives you a layered permission model. Global `beforeEach` handles authentication. Route-level `beforeEnter` handles per-route authorization. Component `beforeRouteLeave` handles unsaved-changes confirmation.

```
User clicks link
        │
        ▼
  Router resolves target route record
        │
        ▼
  beforeRouteLeave  ◄── leaving component
        │
        ▼
  beforeEach        ◄── global guards (auth, logging)
        │
        ▼
  beforeRouteUpdate ◄── reused component (same route, new params)
        │
        ▼
  beforeEnter       ◄── route-level guard
        │
        ▼
  async component   ◄── lazy chunk fetch (network I/O)
  resolution
        │
        ▼
  beforeRouteEnter  ◄── entering component
        │
        ▼
  beforeResolve     ◄── final global hook (data ready)
        │
        ▼
  Navigation commits
        │
        ▼
  afterEach         ◄── analytics, progress bar teardown
```

Consider a real authentication guard. The pattern below uses a Pinia store for auth state, redirects unauthenticated users to login while preserving the intended destination in `redirect`, and uses `beforeResolve` to prefetch route-level data before the component mounts—preventing the flash of empty content that plagues naïve SSR applications.

```typescript
// src/router/guards.ts
import type { Router } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDataStore } from '@/stores/data'

export function installGuards(router: Router): void {
  router.beforeEach(async (to, from) => {
    const auth = useAuthStore()

    // Routes without requiresAuth meta pass through immediately.
    if (!to.meta.requiresAuth) return true

    // If the user has no session, redirect to login with return path encoded.
    if (!auth.isAuthenticated) {
      return {
        name: 'Login',
        query: { redirect: to.fullPath },
      }
    }

    // Role-based access: route meta carries required role string.
    if (to.meta.role && !auth.hasRole(to.meta.role as string)) {
      return { name: 'Forbidden' }
    }

    return true
  })

  // beforeResolve fires after async components are resolved, so the component's
  // own data-fetching logic can be called here before it mounts.
  router.beforeResolve(async (to) => {
    if (to.meta.fetchData) {
      const data = useDataStore()
      try {
        await data.prefetch(to)
      } catch (err) {
        return { name: 'Error', params: { message: (err as Error).message } }
      }
    }
    return true
  })

  router.afterEach((to, from, failure) => {
    if (!failure) {
      // Emit page view to analytics pipeline on successful navigation only.
      window.__analytics?.page(to.fullPath)
    }
  })
}
```

```typescript
// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { installGuards } from './guards'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { requiresAuth: true, fetchData: true },
    children: [
      {
        path: 'invoices',
        name: 'InvoiceList',
        component: () => import('@/views/InvoiceListView.vue'),
        meta: { requiresAuth: true, role: 'billing' },
      },
      {
        path: 'invoices/:id(\\d+)',
        name: 'InvoiceDetail',
        component: () => import('@/views/InvoiceDetailView.vue'),
        meta: { requiresAuth: true, role: 'billing', fetchData: true },
        props: true,
      },
    ],
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
  },
  {
    path: '/forbidden',
    name: 'Forbidden',
    component: () => import('@/views/ForbiddenView.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    if (to.hash) return { el: to.hash, behavior: 'smooth' }
    return { top: 0 }
  },
})

installGuards(router)

export default router
```

The `/:id(\\d+)` path parameter syntax passes a regex constraint directly to Vue Router's internal path parser (based on `path-to-regexp`). This means `/invoices/abc` will not match and will fall through to the 404 route, which is a cheap guard that runs at route-resolution time rather than inside a guard hook.

### Dynamic Route Handling and Param Reactivity

A subtle but critical issue emerges with dynamic segments: when only the params change—navigating from `/invoices/1` to `/invoices/2`—Vue reuses the same component instance. The component does not unmount and remount; `created` and `mounted` hooks do not re-fire. This is intentional and correct—it avoids expensive DOM teardown—but it means any data-fetching logic gated on mount hooks will silently fail to re-execute.

The idiomatic solution is to watch `route.params` inside the component and re-fetch when they change, or to use the `beforeRouteUpdate` in-component guard:

```typescript
// src/views/InvoiceDetailView.vue
<script setup lang="ts">
import { watch } from 'vue'
import { useRoute } from 'vue-router'
import { useInvoiceStore } from '@/stores/invoices'

const route = useRoute()
const invoiceStore = useInvoiceStore()

async function loadInvoice(id: string) {
  await invoiceStore.fetchById(Number(id))
}

// Execute immediately on mount, then re-execute whenever :id changes.
watch(
  () => route.params.id as string,
  (id) => loadInvoice(id),
  { immediate: true }
)
</script>

<template>
  <div v-if="invoiceStore.current">
    <h1>Invoice #{{ invoiceStore.current.id }}</h1>
    <p>Amount: {{ invoiceStore.current.amount }}</p>
  </div>
  <div v-else>
    <p>Loading...</p>
  </div>
</template>
```

Alternatively, if you prefer the guard-based approach and need to run async logic before the component renders its new state, `onBeforeRouteUpdate` from `vue-router` provides the guard as a composable:

```typescript
import { onBeforeRouteUpdate } from 'vue-router'

onBeforeRouteUpdate(async (to, from) => {
  if (to.params.id !== from.params.id) {
    await invoiceStore.fetchById(Number(to.params.id))
  }
})
```

The `watch`-based approach is cleaner for most scenarios. The guard-based approach is preferable when you need to block the navigation itself (return `false` or redirect) based on the fetch result.

### SSR Hydration Mechanics

Vue's SSR architecture is built around `@vue/server-renderer`'s `renderToString` function, which executes the component tree in a Node.js context—no DOM, no `window`, no `document`—and produces an HTML string. That HTML is sent to the browser as the HTTP response body, so the user sees rendered content immediately without waiting for JavaScript to execute. The browser then loads the JavaScript bundle, which calls `createApp` and `app.mount('#app')`. At this point, Vue performs hydration.

Hydration is not re-rendering. Vue does not call `innerHTML` or touch the DOM nodes produced by the server. Instead, it walks the existing DOM tree and the virtual DOM tree produced by the client-side render in parallel, attaching event listeners and establishing reactive bindings at each node. The browser's time-to-first-byte (TTFB) reflects the SSR HTML, and the time-to-interactive (TTI) reflects the hydration completion.

The critical invariant is that the server HTML and the client virtual DOM must be structurally identical. If the server renders `<span>42</span>` and the client's first render produces `<span>43</span>`, Vue detects a hydration mismatch. In development mode it throws a warning and re-renders the mismatched subtree from scratch. In production mode, by default, it silently takes over the server DOM and continues—which means the user briefly sees stale server content before the client corrects it. For data-driven mismatches (the classic timestamp or random ID case), this is a real problem that degrades both performance and correctness.

The architectural solution is to serialize server state and replay it on the client. Nuxt.js calls this payload hydration; in a custom setup with Vite SSR you do it manually:

```typescript
// server-entry.ts – runs in Node.js
import { createApp } from './main'
import { renderToString } from '@vue/server-renderer'

export async function render(url: string): Promise<{ html: string; state: string }> {
  const { app, router, pinia } = createApp()

  await router.push(url)
  await router.isReady()

  const html = await renderToString(app)
  // Pinia serializes all store state to a plain object.
  const state = JSON.stringify(pinia.state.value)

  return { html, state }
}
```

```typescript
// client-entry.ts – runs in the browser
import { createApp } from './main'

const { app, router, pinia } = createApp()

// Rehydrate Pinia stores from the state injected by the server into the HTML.
if (window.__PINIA_STATE__) {
  pinia.state.value = window.__PINIA_STATE__
}

await router.isReady()
app.mount('#app')
```

```html
<!-- index.html template, rendered server-side -->
<html>
  <head><title>App</title></head>
  <body>
    <div id="app"><!--app-html--></div>
    <script>
      window.__PINIA_STATE__ = <!--app-state-->
    </script>
    <script type="module" src="/client-entry.ts"></script>
  </body>
</html>
```

The `<!--app-html-->` and `<!--app-state-->` tokens are replaced by the Node.js server handler before the response is sent. With the Pinia state replayed before `app.mount`, the client's first render produces the same virtual DOM the server produced, hydration succeeds cleanly, and no subtrees need to be re-rendered.

### Code Splitting Architecture

Vite and Rollup split the application bundle at dynamic `import()` call sites. Every route component written as `component: () => import('@/views/InvoiceDetailView.vue')` becomes its own chunk in the production build. The browser only fetches the chunk when that route is first navigated to, keeping the initial JS payload small.

The module graph after a Vite production build for a medium-complexity application looks like this:

```
                    ┌─────────────────────┐
                    │   index-[hash].js   │  ← entry chunk: Vue runtime,
                    │   (vendor + app)    │    router, Pinia, shared utils
                    └────────┬────────────┘
                             │  dynamic import on navigation
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
  HomeView-[hash].js  Dashboard-[hash].js  Login-[hash].js
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
  InvoiceList-[hash].js  InvoiceDetail-[hash].js  (child route chunks)
```

Shared dependencies imported by multiple chunks are automatically split into separate shared chunks by Rollup's `splitChunks` heuristic. Vue itself, Pinia, and Vue Router appear in the entry chunk because they are needed immediately. A large date-formatting library imported only by `InvoiceDetailView` appears only in that route's chunk.

You control chunk grouping through Vite's `build.rollupOptions.output.manualChunks`. The following configuration isolates the vendor bundle and separates a heavy third-party charting library from the main vendor chunk:

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    target: 'esnext',
    rollupOptions: {
      output: {
        manualChunks(id) {
          // Isolate the charting library into its own chunk because it is
          // ~400KB and only needed in the analytics dashboard route.
          if (id.includes('node_modules/echarts')) {
            return 'vendor-echarts'
          }
          // All other node_modules go into a single stable vendor chunk.
          // A content-hash on this chunk means it is cached indefinitely
          // by the CDN until a dependency version actually changes.
          if (id.includes('node_modules')) {
            return 'vendor'
          }
        },
      },
    },
    // Warn when any single chunk exceeds 500KB gzipped.
    chunkSizeWarningLimit: 500,
  },
})
```

---

## 3. High-Performance Optimization & Failure Modes

### Bundle Analysis and the Identification of Weight

Before optimizing bundle size, you must measure it. `rollup-plugin-visualizer` generates an interactive treemap of chunk composition that makes over-bundled dependencies immediately visible:

```typescript
// vite.config.ts (add to plugins array)
import { visualizer } from 'rollup-plugin-visualizer'

plugins: [
  vue(),
  visualizer({
    filename: 'dist/bundle-analysis.html',
    open: false,
    gzipSize: true,
    brotliSize: true,
    template: 'treemap', // 'sunburst' | 'network' are also available
  }),
]
```

After running `vite build`, open `dist/bundle-analysis.html`. The treemap renders each module as a rectangle sized proportionally to its contribution to the bundle. Common findings at this stage: an entire `lodash` package imported for a single utility function (fix: import `lodash-es/debounce` directly, or replace with a one-line implementation), a full `moment.js` locale set included when only `en-US` is needed (fix: `import 'moment/locale/en'` explicitly and configure `moment-locales-webpack-plugin`), or a component library imported as a monolith when tree-shaking was available (fix: configure the library's Vite plugin for on-demand importing).

The key metric from `vite build` output is the gzipped chunk size. The browser's main thread parse cost scales with the uncompressed JavaScript size, not the wire size. A 300KB gzipped chunk that decompresses to 1.2MB still imposes 1.2MB of parse and compile cost on every cold load. For initial interactivity, the target is to keep the entry chunk below 150KB compressed and defer everything else.

### Lazy Loading Beyond Routes: Components and Assets

Route-level code splitting is the coarsest granularity. For heavy components that appear conditionally within a page—a rich text editor, a data grid, a PDF renderer—Vue's `defineAsyncComponent` applies the same lazy-loading pattern at the component level:

```typescript
// src/views/DashboardView.vue
<script setup lang="ts">
import { defineAsyncComponent, ref } from 'vue'

const showEditor = ref(false)

// The editor chunk (~180KB) is not fetched until the user clicks "New Invoice".
const RichTextEditor = defineAsyncComponent({
  loader: () => import('@/components/RichTextEditor.vue'),
  loadingComponent: () => import('@/components/LoadingSpinner.vue'),
  errorComponent: () => import('@/components/ErrorState.vue'),
  delay: 200,    // ms before showing loadingComponent; avoids flash for fast networks
  timeout: 8000, // ms after which errorComponent is shown
})
</script>

<template>
  <button @click="showEditor = true">New Invoice</button>
  <RichTextEditor v-if="showEditor" />
</template>
```

For even finer control, `<Suspense>` integrates with async setup functions. A component with a top-level `await` in `<script setup>` is implicitly async—Vue suspends rendering that component's subtree until the awaited expression resolves, letting a parent `<Suspense>` boundary show a fallback slot:

```typescript
// src/components/InvoiceChart.vue
<script setup lang="ts">
import { useInvoiceStore } from '@/stores/invoices'
const store = useInvoiceStore()
// This await causes the component to be treated as async by Suspense.
await store.fetchChartData()
</script>

<template>
  <canvas id="chart" />
</template>
```

```html
<!-- Parent template -->
<Suspense>
  <template #default>
    <InvoiceChart />
  </template>
  <template #fallback>
    <SkeletonLoader />
  </template>
</Suspense>
```

`<Suspense>` is still marked experimental in Vue 3's official documentation for some edge cases, but it is production-stable for data-fetching patterns and is the foundation of Nuxt 3's page data fetching model.

### Virtual DOM Optimization: `v-memo` and `shallowRef`

Vue 3's virtual DOM reconciler performs a diff on every reactive dependency change. For list rendering of large datasets—thousands of table rows, for instance—the diff cost is non-trivial even when the underlying data hasn't changed. `v-memo` short-circuits the diff for a subtree when a specified array of values has not changed between renders:

```html
<!-- Without v-memo, every row re-diffs on any state change in the parent. -->
<!-- With v-memo, a row re-diffs only when its own item.id or selected state changes. -->
<tr
  v-for="item in invoices"
  :key="item.id"
  v-memo="[item.id, item.status, selectedId === item.id]"
>
  <td>{{ item.id }}</td>
  <td>{{ item.amount }}</td>
  <td>{{ item.status }}</td>
  <td><input type="checkbox" :checked="selectedId === item.id" /></td>
</tr>
```

The memo condition array is compared shallowly. When none of the values change, Vue skips the entire subtree diff and patch. For a 500-row table, this reduces the reconciliation cost of a selection change from O(500 component diffs) to O(2 component diffs): the row being deselected and the row being selected.

`shallowRef` and `shallowReactive` are the companion tools for large data structures. A `ref` containing a 10,000-element array tracks deep reactivity on every nested property. `shallowRef` only tracks reactivity on the top-level reference itself—replacing the entire array triggers updates, but mutating elements does not. For read-mostly datasets where you replace the reference on each fetch rather than mutating in place, `shallowRef` is both semantically correct and faster because Vue's proxy does not need to instrument the array's contents:

```typescript
import { shallowRef } from 'vue'

// Vue does not create deep Proxy traps over this array's elements.
// Reactivity fires only when invoices.value is reassigned.
const invoices = shallowRef<Invoice[]>([])

async function fetchInvoices() {
  const data = await api.get<Invoice[]>('/invoices')
  // Assignment triggers reactivity; mutation of elements would not.
  invoices.value = data
}
```

### SSR Hydration Failure Modes and Mitigations

The most common hydration mismatch arises from accessing browser-only globals in component setup code. `localStorage`, `window.innerWidth`, and `navigator.userAgent` are undefined during server-side rendering. The runtime exception ("localStorage is not defined") crashes the SSR render entirely or produces incorrect HTML.

The idiomatic defense is to guard browser-only code behind `onMounted`, which only runs on the client, or to use an `import.meta.env.SSR` check:

```typescript
<script setup lang="ts">
import { ref, onMounted } from 'vue'

// Initialize with a safe default that the server can render without issue.
const prefersDark = ref(false)

// onMounted never fires on the server; this code is client-only.
onMounted(() => {
  prefersDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
})
</script>
```

For a Vite SSR build, `import.meta.env.SSR` is `true` during the server render and `false` during the client build, letting you dead-code-eliminate browser-only imports at build time:

```typescript
let analytics: typeof import('@/lib/analytics') | null = null

if (!import.meta.env.SSR) {
  analytics = await import('@/lib/analytics')
}
```

A subtler hydration failure occurs with time-dependent rendering. A component that renders the current time—`new Date().toLocaleTimeString()`—will produce different output on the server (render time) versus the client (hydration time, which is later). The fix is to pass the timestamp as serialized state rather than recomputing it, or to use a `ClientOnly` wrapper component that suppresses SSR rendering entirely for that subtree:

```typescript
// src/components/ClientOnly.vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
const mounted = ref(false)
onMounted(() => { mounted.value = true })
</script>

<template>
  <slot v-if="mounted" />
</template>
```

This component renders nothing on the server and renders its slot content only after the client has mounted. The hydration mismatch is avoided because Vue sees an empty node on both sides during hydration. The tradeoff is that the content is not in the server HTML, so it does not contribute to SEO or first-paint. Use this pattern only for genuinely client-specific UI—clock widgets, localStorage-driven preferences, browser-API-dependent features.

### Production Profiling with Vue DevTools and Performance API

Vue DevTools 7 (the browser extension and the `vite-plugin-vue-devtools` Vite plugin) exposes a component profiler that renders a flame graph of component render times. For production builds where DevTools is unavailable, you instrument render performance manually using the Performance API:

```typescript
// src/composables/useRenderTiming.ts
import { onBeforeMount, onMounted, getCurrentInstance } from 'vue'

export function useRenderTiming(): void {
  const instance = getCurrentInstance()
  const name = instance?.type.__name ?? 'UnknownComponent'

  onBeforeMount(() => {
    performance.mark(`${name}-mount-start`)
  })

  onMounted(() => {
    performance.mark(`${name}-mount-end`)
    performance.measure(
      `${name} mount duration`,
      `${name}-mount-start`,
      `${name}-mount-end`
    )
    const [entry] = performance.getEntriesByName(`${name} mount duration`)
    if (entry.duration > 16) {
      // 16ms is one frame at 60fps. Flag components that block a full frame.
      console.warn(`[perf] ${name} took ${entry.duration.toFixed(1)}ms to mount`)
    }
  })
}
```

This composable drops breadcrumbs in the browser's Performance timeline, visible in Chrome DevTools under the "Timings" row of the Performance panel. Any component whose mount duration exceeds 16ms is a candidate for profiling its setup logic, deferring data fetching, or applying `v-memo` to its template.

The correct mental model for Vue production performance is a layered budget. The network budget covers initial HTML delivery and chunk loading; keep the entry chunk lean and use preload hints for predictable next-navigation chunks with `<link rel="modulepreload">`. The parse budget covers the time the browser spends compiling JavaScript; smaller chunks and ES module native loading (not CommonJS) help here. The runtime budget covers the time Vue spends in reactivity tracking and virtual DOM reconciliation; `v-memo`, `shallowRef`, `computed` caching, and `defineAsyncComponent` are the tools. No single optimization dominates—senior engineers profile first, identify the binding constraint, and apply the targeted fix rather than applying all optimizations indiscriminately to code that is already fast enough.
