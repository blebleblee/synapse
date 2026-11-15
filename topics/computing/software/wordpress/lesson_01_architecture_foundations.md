# Lesson 1: Core Architecture, Request Lifecycle, Hook System

## 1. First-Principles Intuition & Invariants

WordPress began as a publishing system in 2003, but beneath its accessible interface lies a sophisticated execution model built on four invariant principles that govern every request. The first invariant establishes that WordPress operates as a stateless request processor: each HTTP request triggers a complete bootstrap sequence, loading the entire framework from scratch without persistent in-memory state between requests. This differs fundamentally from application servers that maintain long-running processes. The PHP execution model, combined with WordPress's design, means that every page load reconstructs the runtime environment, registers hooks, loads plugins and themes, queries the database, and tears down completely before the next request arrives.

The second invariant defines WordPress as a hook-driven event system rather than a traditional object-oriented framework. While WordPress contains classes and objects, its architectural soul resides in the hook system—a publish-subscribe mechanism where code registers callbacks at named extension points distributed throughout the execution lifecycle. Actions represent side-effect operations where multiple handlers execute in sequence without returning values, while filters form transformation pipelines where each handler receives the output of the previous handler and returns a modified result. This distinction creates a composable architecture where plugins and themes extend functionality by inserting behavior at precise moments in the request lifecycle without modifying core files.

The third invariant establishes that WordPress maintains a strict three-phase initialization sequence: core loading, plugin activation, and theme initialization. Core files define the foundational APIs, database abstraction, and hook infrastructure. Plugins load next, registering their hooks and extending functionality in a deterministic order controlled by plugin dependencies and load order. Themes load last, providing presentation logic and final opportunities to modify output. This sequence creates a dependency graph where each phase can rely on the availability of previous phases, but premature access to later-phase functionality produces undefined behavior.

The fourth invariant positions the WordPress database abstraction layer (`wpdb`) as a mandatory gateway to all persistent data. Direct SQL execution bypasses WordPress's caching mechanisms, security escaping, and table prefix abstraction. The `wpdb` class provides methods like `prepare()` for parameterized queries, `get_results()` for result set retrieval, and `insert()` for safe data persistence. Understanding that WordPress queries flow through this single abstraction point reveals why database optimization focuses on query reduction rather than raw SQL performance, and why object caching produces dramatic performance improvements by intercepting `wpdb` calls before database execution.

These four invariants—stateless request processing, hook-driven architecture, three-phase initialization, and mandatory database abstraction—form the conceptual foundation for understanding every WordPress operation from plugin development to performance optimization.

## 2. Core Architecture & Mechanics

The WordPress request lifecycle begins when the web server invokes `index.php` in the WordPress root directory. This entry point performs exactly one operation: it loads `wp-blog-header.php`, which orchestrates the complete request lifecycle through three sequential function calls. The first call to `wp()` processes the request and determines what content to display. The second call to `template_loader()` identifies and loads the appropriate theme template file. Between these operations, WordPress has bootstrapped its entire runtime environment, executed all plugin code, queried the database, and prepared the response.

Before `wp-blog-header.php` can function, `index.php` must load `wp-load.php`, which searches upward through the directory tree to locate `wp-config.php`. This configuration file defines database credentials, authentication salts, debugging flags, and custom constants that alter WordPress behavior. Constants like `WP_DEBUG`, `WP_DEBUG_LOG`, and `WP_DEBUG_DISPLAY control error reporting. `WP_MEMORY_LIMIT` sets the PHP memory ceiling. `WP_CACHE` enables external object caching. `DISABLE_WP_CRON` prevents the pseudo-cron system from firing on page loads. Every constant defined in `wp-config.php` influences the subsequent bootstrap sequence, making this file the first decision point in request processing.

After loading configuration, `wp-config.php` includes `wp-settings.php`, which executes the core bootstrap sequence. This file performs initialization in strict order. It defines core constants like `WPINC` that point to the includes directory. It loads compatibility files that normalize PHP behavior across versions. It initializes the object cache through `wp_start_object_cache()`, which either connects to Memcached, Redis, or falls back to transient-based caching. It includes core class files like `wpdb` for database access, `WP_Query` for content retrieval, and `WP_Rewrite` for URL routing.

The plugin loading mechanism follows a deterministic sequence. WordPress reads the `active_plugins` option from the database, which contains an ordered array of plugin file paths relative to the plugins directory. For each active plugin, WordPress includes the main plugin file, allowing it to register hooks, define functions, and initialize classes. Plugin authors register initialization hooks at `plugins_loaded`, which fires after all plugins have been included but before theme loading begins. This hook provides the earliest safe moment for plugins to interact with each other, since all plugin code is guaranteed to be in memory.

```php
// Core plugin loading sequence in wp-settings.php
foreach ( wp_get_active_and_valid_plugins() as $plugin ) {
    wp_register_plugin_realpath( $plugin );
    include_once( $plugin );
    do_action( 'plugin_loaded', $plugin );
}
unset( $plugin );

do_action( 'plugins_loaded' );
```

The hook system implementation resides in `wp-includes/plugin.php`, which defines global arrays that store registered callbacks. The `$wp_filter` global maps hook names to priority-sorted arrays of callbacks. When code calls `add_action('init', 'my_function', 10)`, WordPress stores the function reference in `$wp_filter['init'][10][]`. The priority parameter (default 10) controls execution order, with lower numbers executing first. When WordPress reaches the hook point and calls `do_action('init')`, it iterates through all registered callbacks in priority order, executing each function.

Filters differ from actions only in their return value handling. When WordPress calls `apply_filters('the_content', $content)`, it passes the content through each registered filter function in sequence. Each filter receives the output of the previous filter and returns its modified version. The final filtered value returns to the calling code. This creates a transformation pipeline where twenty plugins might each modify post content—one adding social sharing buttons, another implementing code syntax highlighting, another converting markdown to HTML—without any plugin knowing about the others.

```php
// Simplified filter application logic
function apply_filters( $hook_name, $value ) {
    global $wp_filter;
    
    if ( !isset( $wp_filter[$hook_name] ) ) {
        return $value;
    }
    
    ksort( $wp_filter[$hook_name] ); // Sort by priority
    
    foreach ( $wp_filter[$hook_name] as $priority => $functions ) {
        foreach ( $functions as $function ) {
            $value = call_user_func( $function['function'], $value );
        }
    }
    
    return $value;
}
```

After plugin initialization completes, WordPress loads the active theme. The theme loading sequence first determines which theme to load by reading the `template` and `stylesheet` options from the database. The template option specifies the parent theme directory, while stylesheet specifies the child theme. WordPress loads the parent theme's `functions.php` first, then loads the child theme's `functions.php`, allowing child themes to override or extend parent functionality. This two-phase loading creates inheritance without requiring themes to explicitly extend parent classes.

Following theme initialization, WordPress executes `wp()`, which creates a `WP` object and calls its `main()` method. This method invokes `WP::parse_request()` to analyze the URL and determine what content to display. The URL parsing system works backward from modern pretty permalinks to the underlying query string representation. If the site uses permalinks like `/2024/03/post-title/`, WordPress uses rewrite rules stored in the database to transform this into `?year=2024&monthnum=03&name=post-title`. The `WP_Rewrite` class manages this bidirectional mapping between URLs and query parameters.

The parsed query parameters flow into `WP_Query`, WordPress's content retrieval engine. This class translates query parameters into SQL queries against the posts table. When code executes `new WP_Query(['post_type' => 'post', 'posts_per_page' => 10])`, the class constructs a SELECT statement with appropriate WHERE clauses, JOIN operations for taxonomy queries, and ORDER BY clauses for sorting. The query execution passes through `wpdb`, which prepares the statement, executes it, retrieves results, and caches them in the object cache.

```php
// Simplified WP_Query SQL generation
public function get_posts() {
    global $wpdb;
    
    $where = "WHERE 1=1";
    $where .= " AND {$wpdb->posts}.post_type = 'post'";
    $where .= " AND {$wpdb->posts}.post_status = 'publish'";
    
    if ( $this->query_vars['author'] ) {
        $where .= $wpdb->prepare( " AND {$wpdb->posts}.post_author = %d", 
                                  $this->query_vars['author'] );
    }
    
    $limits = "LIMIT 0, 10";
    
    $request = "SELECT {$wpdb->posts}.* FROM {$wpdb->posts} {$where} {$limits}";
    
    $this->posts = $wpdb->get_results( $request );
    
    return $this->posts;
}
```

The database abstraction layer in `wpdb` maintains several critical invariants. Every query passes through the `prepare()` method for parameter escaping, preventing SQL injection. The class automatically prefixes table names using the configured `$table_prefix`, enabling multiple WordPress installations in a single database. It tracks query counts and execution time when `SAVEQUERIES` is defined, supporting performance analysis. Most importantly, `wpdb` integrates with the object cache, checking for cached results before executing queries and storing results after successful execution.

Object caching operates through a simple key-value interface. When code calls `wp_cache_get('posts', 'post_group')`, WordPress first checks the external cache backend (Redis, Memcached) for the key. If found, it returns the cached value immediately, bypassing database queries. If not found, the code executes its query through `wpdb` and stores results with `wp_cache_set('posts', $results, 'post_group', 3600)`. The cache group parameter ('post_group') provides namespacing, while the timeout (3600 seconds) controls expiration. Cache invalidation occurs through `wp_cache_delete()` or `wp_cache_flush()`, typically triggered by content updates.

The template loading phase begins after query execution completes. WordPress examines the query results to determine template hierarchy—the ordered list of template files WordPress will attempt to load. For a single post view, WordPress looks for `single-{post_type}-{slug}.php`, then `single-{post_type}.php`, then `single.php`, then `singular.php`, then `index.php`. The first existing file in this sequence loads and generates output. Template files contain a mix of PHP logic and HTML markup, with special template tags like `the_title()`, `the_content()`, and `the_permalink()` that output post data.

Within template files, The Loop represents WordPress's fundamental content iteration pattern. This while loop tests `have_posts()` and calls `the_post()` to advance through query results:

```php
<?php
if ( have_posts() ) {
    while ( have_posts() ) {
        the_post();
        ?>
        <article>
            <h2><?php the_title(); ?></h2>
            <div><?php the_content(); ?></div>
        </article>
        <?php
    }
}
?>
```

Each call to `the_post()` sets global variables like `$post`, `$id`, and `$authordata` to the current post's values. Template tags read these globals to output formatted data. The `the_content()` function retrieves the post content and applies the `the_content` filter, allowing plugins to transform output. Shortcodes expand during this filter application, converting `[gallery]` tags into HTML markup through registered shortcode handlers.

The response generation concludes with output buffering and final filters. WordPress starts output buffering early in the request lifecycle, capturing all echoed content. After the template executes, WordPress retrieves the buffered content and applies final filters like `wp_footer`, allowing plugins to inject tracking scripts or analytics code. The complete HTML document flows through the `shutdown` action hook, providing last-chance cleanup operations, then transmits to the client and terminates the PHP process.

## 3. High-Performance Optimization & Failure Modes

WordPress performance optimization targets three bottlenecks: database query volume, plugin execution overhead, and theme rendering cost. The stateless request model means every page load repeats the entire bootstrap sequence, making initialization cost the baseline performance floor. Reducing this floor requires aggressive caching at multiple layers: opcode caching through OPcache to eliminate PHP parsing overhead, object caching through Redis or Memcached to eliminate database queries, and page caching through Varnish or Nginx to eliminate WordPress execution entirely.

Object cache effectiveness depends on cache key design and invalidation strategy. Well-designed cache keys include version identifiers or dependency hashes that automatically invalidate when dependencies change. A query caching posts modified in the last week should incorporate the maximum modification timestamp in the cache key: `wp_cache_get("recent_posts_{$max_modified_time}")`. When new posts publish or existing posts update, the timestamp changes, naturally invalidating stale cache entries without explicit deletion logic.

Cache stampedes represent a failure mode where cache expiration triggers simultaneous regeneration attempts. When a popular cache entry expires, hundreds of concurrent requests race to regenerate the value, each executing expensive database queries. Probabilistic early expiration mitigates this failure mode by randomly refreshing cache entries before actual expiration. If a cache entry has a 60-second lifetime, code requests after 50 seconds have a 20% chance of triggering regeneration, spreading regeneration load across time.

```php
function cache_get_with_pee( $key, $group, $ttl, $regenerate_callback ) {
    $value = wp_cache_get( $key, $group );
    
    if ( false !== $value ) {
        $age = time() - wp_cache_get( "{$key}_timestamp", $group );
        $pee_threshold = $ttl * 0.8; // Refresh after 80% of TTL
        
        if ( $age > $pee_threshold && ( rand() / getrandmax() ) < 0.2 ) {
            // 20% chance to regenerate after threshold
            $value = $regenerate_callback();
            wp_cache_set( $key, $value, $group, $ttl );
            wp_cache_set( "{$key}_timestamp", time(), $group, $ttl );
        }
        
        return $value;
    }
    
    $value = $regenerate_callback();
    wp_cache_set( $key, $value, $group, $ttl );
    wp_cache_set( "{$key}_timestamp", time(), $group, $ttl );
    
    return $value;
}
```

Database query optimization focuses on reducing query count rather than optimizing individual queries. A common antipattern executes N+1 queries: retrieving a list of posts, then querying author data for each post individually. WordPress's `WP_Query` supports eager loading through the `update_post_caches()` function, which batch-loads metadata, term relationships, and author data for all posts in a single set of queries. Custom queries should follow this pattern, using `IN` clauses to fetch related data in bulk.

The `WP_Query` class exposes parameters that control caching behavior. Setting `'cache_results' => false` disables result caching for one-time queries that won't benefit from caching. Setting `'update_post_meta_cache' => false` and `'update_post_term_cache' => false` skips metadata and taxonomy caching for queries that don't require this data. These parameters reduce cache memory consumption and eliminate unnecessary queries for specialized query contexts.

Hook execution overhead scales with the number of registered callbacks. Sites with fifty plugins might register thousands of hook callbacks, each adding function call overhead. Critical performance paths should minimize hook usage or use selective hook firing. The `remove_action()` and `remove_filter()` functions detach callbacks when their functionality isn't required. For example, disabling emoji support by removing emoji-related hooks eliminates several inline scripts and external requests.

Query monitoring in production environments requires careful instrumentation. The `SAVEQUERIES` constant enables query logging, but stores all queries in memory, consuming significant resources on high-traffic sites. Production monitoring should sample requests, logging queries for a random subset of requests or requests that exceed duration thresholds. The `log_slow_queries` constant combined with a custom filter on `wpdb` enables threshold-based query logging:

```php
// Log queries exceeding 0.05 seconds
add_filter( 'log_query_custom_data', function( $data, $query, $query_time ) {
    if ( $query_time > 0.05 ) {
        error_log( sprintf(
            "Slow query (%0.4fs): %s\nBacktrace: %s",
            $query_time,
            $query,
            wp_debug_backtrace_summary()
        ) );
    }
    return $data;
}, 10, 3 );
```

Theme rendering cost increases with template complexity and conditional logic. Each conditional statement like `is_home()` or `is_single()` executes query introspection, checking post types, query variables, and conditionals. Template files should cache these checks in local variables at the start of rendering rather than repeatedly checking conditions. Complex conditional trees benefit from early returns that skip unnecessary rendering logic.

Plugin loading order creates subtle failure modes when plugins make assumptions about execution sequence. If Plugin A registers a hook at priority 10 and Plugin B registers the same hook at priority 5, Plugin B executes first. If Plugin A modifies data that Plugin B depends on, the dependency breaks. Hook priority design should consider that lower priorities execute first and that priority collisions resolve in plugin load order. Critical dependencies should use much higher priority differences (gaps of 100 rather than 1) to ensure clear execution order even if intervening plugins register callbacks.

The WordPress admin interface executes the same hook system as the frontend but includes additional hooks for admin pages, settings registration, and AJAX handlers. Admin performance differs from frontend performance because admin pages execute on every request without page caching. Heavy admin operations should implement progressive loading patterns where initial page loads return minimal data and JavaScript requests load additional content asynchronously. The Heartbeat API provides a polling mechanism for real-time updates but should be throttled or disabled on pages that don't require live updates.

Transient storage provides a database-backed alternative to object caching for data that doesn't require external cache backends. The `set_transient()` function stores key-value pairs with expiration times in the options table. Unlike object cache, transients persist across requests and survive cache flushes, making them appropriate for API responses, external data feeds, and computed values with medium expiration times (minutes to hours). Transient cleanup occurs opportunistically during option reads, but stale transients accumulate in the database, requiring periodic cleanup through custom WP-CLI commands or scheduled jobs.

Security considerations intersect with performance optimization through several mechanisms. Nonce validation on every form submission adds overhead but prevents CSRF attacks. User capability checks through `current_user_can()` add database queries to verify role assignments. These security operations should never be bypassed for performance, but can be optimized by caching user capabilities for the request duration and batching capability checks before expensive operations. The authentication system maintains user sessions in the database, reading session data on every authenticated request. Redis-based session storage eliminates this database query while maintaining session security.

Understanding WordPress's architecture from request entry through response generation enables systematic performance optimization and reliable plugin development. The hook system provides extension points throughout the lifecycle, the database abstraction ensures safe data access, and the caching infrastructure allows eliminating redundant work. Mastering these systems transforms WordPress from a simple publishing platform into a high-performance application framework capable of serving millions of requests per hour.
