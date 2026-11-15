# Lesson 4: Plugin Architecture, REST API, Security Primitives

## 1. First-Principles Intuition & Invariants

WordPress, beneath its reputation as a simple content management system, operates as a sophisticated event-driven plugin architecture built atop a procedural PHP runtime. The system's extensibility model rests on a hook-based inversion-of-control pattern where the core application defines extension points—actions and filters—that third-party code can bind to without modifying the core codebase itself. This architectural decision, made in WordPress's earliest iterations, transforms the platform from a monolithic application into a plugin container that mediates execution through a deterministic hook dispatch system.

The plugin lifecycle in WordPress follows a strict bootstrap sequence. When an HTTP request arrives, the web server (typically Apache with mod_php or nginx with php-fpm) invokes PHP to execute `index.php` in the WordPress root. This entry point loads `wp-config.php` for database credentials and environment configuration, then bootstraps `wp-settings.php`, which performs the critical task of loading all active plugins from the `wp-content/plugins/` directory. Each plugin's main file—identified by a specific header comment block—gets included via `require_once`, executing any top-level procedural code and registering hooks through the global `$wp_filter` registry. The invariant here is registration order determinism: plugins load in alphabetical directory name order, and hook callbacks execute in priority-queue order (lower integer priorities run first, with registration order as the tiebreaker for equal priorities).

Namespace collision represents the fundamental hazard in this procedural environment. PHP, prior to version 5.3, lacked formal namespaces, forcing WordPress to adopt a function prefix convention where every plugin function name should begin with a unique prefix (typically the plugin slug). The collision domain extends beyond functions to global variables, class names, and database table names. A plugin that carelessly defines `function get_user_data()` will trigger a fatal error if another plugin or WordPress core defines the same function, terminating the entire request. Modern WordPress development mitigates this through autoloading class-based architectures, where each class lives in a pseudo-namespace provided by unique class names, and through the judicious use of PHP's native namespace feature when the minimum PHP version permits.

The REST API, introduced as an infrastructure-grade component in WordPress 4.7, provides a JSON-over-HTTP interface that exposes WordPress data models—posts, users, taxonomies, media—as RESTful resources. Unlike the legacy XML-RPC interface it largely supersedes, the REST API adheres to Richardson Maturity Level 2, utilizing HTTP verbs (GET, POST, PUT, DELETE) and status codes (200, 201, 400, 401, 403, 404) semantically. Each endpoint registration defines a URL pattern, accepted HTTP methods, permission callback, and argument schema with validation rules. The API's design deliberately decouples authentication from authorization: authentication establishes identity through cookies, application passwords, or OAuth bearer tokens, while authorization enforces capability checks against the authenticated user's role.

Security in WordPress constitutes a multi-layered defense built on overlapping primitives that address distinct attack surfaces. The nonce system (despite its cryptographically incorrect name—these are not true numbers-used-once) provides CSRF protection through time-limited, action-specific tokens derived from the user's session and a server-side salt. Data sanitization strips potentially dangerous content on input, validation enforces schema constraints, and escaping prevents injection attacks on output. Capability checks enforce role-based access control at the application layer, while prepared statements with placeholders eliminate SQL injection at the database query layer. These primitives do not compose automatically; developers must consciously apply each primitive at the appropriate execution boundary.

The invariant across all security primitives is defense-in-depth through distrust: distrust user input (sanitize and validate), distrust output contexts (escape), distrust request origins (verify nonces), distrust permissions assumptions (check capabilities explicitly), and distrust SQL string concatenation (use prepared statements). A single missed check can compromise the entire system, because WordPress executes with database-level privileges sufficient to read, modify, or delete any content. The privilege boundary between administrative users and the database is thin; most exploitation chains target elevation from unauthenticated or low-privilege user contexts to administrator contexts, then leverage WordPress's administrative capabilities to achieve code execution or data exfiltration.

## 2. Core Architecture & Mechanics

The hook system operates through two global arrays—`$wp_filter` for registered callbacks and `$wp_actions` for execution tracking—managed by functions in `wp-includes/plugin.php`. When plugin code calls `add_action('init', 'my_function', 10, 1)`, WordPress stores a reference to `my_function` in `$wp_filter['init'][10]` as a `WP_Hook` object that maintains priority-ordered callbacks. The fourth parameter specifies accepted argument count, enabling WordPress to pass the correct number of arguments during dispatch. Actions and filters share the same underlying implementation; the distinction is semantic. Actions typically trigger side effects (sending email, logging events) and ignore return values, while filters transform data by passing a value through each callback and using the returned result.

The execution model follows a depth-first traversal. When `do_action('init')` executes, WordPress iterates through `$wp_filter['init']` in priority order, calling each registered callback with the provided arguments. If a callback internally triggers `do_action('another_hook')`, that hook dispatches completely before returning to the original `init` hook traversal. This creates a call stack where hook depth can theoretically grow unbounded, though WordPress core maintains practical limits through careful hook placement. Infinite recursion occurs if a hook callback triggers the same hook again; plugin developers must guard against this with static flags or removal guards.

```php
<?php
/**
 * Plugin Name: Production Plugin Architecture Example
 * Description: Demonstrates lifecycle hooks, namespace safety, and hook mechanics
 * Version: 1.0.0
 * Requires PHP: 7.4
 */

namespace MyCompany\ProductionPlugin;

// Prevent direct access - common security pattern
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Main plugin class - encapsulates all functionality in a namespace-safe container
 */
class PluginCore {
    
    private static $instance = null;
    private $version = '1.0.0';
    private $option_key = 'mycompany_plugin_settings';
    
    /**
     * Singleton pattern prevents multiple instantiations
     */
    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    private function __construct() {
        // Register activation/deactivation hooks - must be called from main plugin file
        register_activation_hook(__FILE__, array($this, 'activate'));
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));
        
        // Register core WordPress hooks
        add_action('plugins_loaded', array($this, 'init'), 10);
        add_action('admin_menu', array($this, 'register_admin_menu'), 10);
        add_action('admin_init', array($this, 'register_settings'), 10);
        
        // REST API initialization - fires after WordPress loads but before query parsing
        add_action('rest_api_init', array($this, 'register_rest_routes'), 10);
        
        // Frontend hooks
        add_action('wp_enqueue_scripts', array($this, 'enqueue_frontend_assets'), 10);
        
        // Example filter - modifies content before display
        add_filter('the_content', array($this, 'filter_content'), 20, 1); // Priority 20 runs after default filters
    }
    
    /**
     * Activation hook - runs once when plugin is activated
     * Used for database table creation, option initialization, capability assignment
     */
    public function activate() {
        global $wpdb;
        
        // Create custom table with proper charset and collation
        $table_name = $wpdb->prefix . 'mycompany_data';
        $charset_collate = $wpdb->get_charset_collate();
        
        $sql = "CREATE TABLE IF NOT EXISTS {$table_name} (
            id bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT,
            user_id bigint(20) UNSIGNED NOT NULL,
            data_key varchar(255) NOT NULL,
            data_value longtext NOT NULL,
            created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY user_id (user_id),
            KEY data_key (data_key)
        ) {$charset_collate};";
        
        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($sql); // dbDelta intelligently handles table creation and updates
        
        // Initialize default options
        $default_settings = array(
            'feature_enabled' => true,
            'api_key' => '',
            'cache_duration' => 3600
        );
        
        add_option($this->option_key, $default_settings);
        
        // Set plugin version for future migration detection
        add_option('mycompany_plugin_version', $this->version);
        
        // Flush rewrite rules if plugin adds custom post types or endpoints
        flush_rewrite_rules();
    }
    
    /**
     * Deactivation hook - cleanup without removing data
     * Do NOT delete user data here - save that for uninstall.php
     */
    public function deactivate() {
        // Clear scheduled cron events
        wp_clear_scheduled_hook('mycompany_daily_task');
        
        // Flush rewrite rules to remove custom endpoints
        flush_rewrite_rules();
    }
    
    /**
     * Main initialization - runs after all plugins load
     */
    public function init() {
        // Load text domain for internationalization
        load_plugin_textdomain('mycompany-plugin', false, dirname(plugin_basename(__FILE__)) . '/languages');
        
        // Register custom post types, taxonomies, etc.
        $this->register_custom_post_type();
        
        // Schedule cron job if not already scheduled
        if (!wp_next_scheduled('mycompany_daily_task')) {
            wp_schedule_event(time(), 'daily', 'mycompany_daily_task');
        }
    }
    
    private function register_custom_post_type() {
        register_post_type('mycompany_item', array(
            'labels' => array(
                'name' => __('Items', 'mycompany-plugin'),
                'singular_name' => __('Item', 'mycompany-plugin')
            ),
            'public' => true,
            'has_archive' => true,
            'rewrite' => array('slug' => 'items'),
            'show_in_rest' => true, // Enables REST API and block editor support
            'supports' => array('title', 'editor', 'thumbnail', 'custom-fields')
        ));
    }
    
    /**
     * Register admin menu page
     */
    public function register_admin_menu() {
        add_menu_page(
            __('My Company Plugin', 'mycompany-plugin'), // Page title
            __('My Company', 'mycompany-plugin'),        // Menu title
            'manage_options',                             // Required capability
            'mycompany-plugin',                           // Menu slug
            array($this, 'render_admin_page'),            // Callback
            'dashicons-admin-generic',                    // Icon
            30                                             // Position
        );
    }
    
    /**
     * Register settings using Settings API
     */
    public function register_settings() {
        register_setting(
            'mycompany_plugin_settings_group', // Option group
            $this->option_key,                  // Option name
            array(
                'type' => 'array',
                'sanitize_callback' => array($this, 'sanitize_settings'),
                'default' => array()
            )
        );
        
        add_settings_section(
            'mycompany_main_section',
            __('Main Settings', 'mycompany-plugin'),
            array($this, 'render_settings_section'),
            'mycompany-plugin'
        );
        
        add_settings_field(
            'feature_enabled',
            __('Enable Feature', 'mycompany-plugin'),
            array($this, 'render_feature_toggle'),
            'mycompany-plugin',
            'mycompany_main_section'
        );
    }
    
    /**
     * Sanitize settings array - critical security boundary
     */
    public function sanitize_settings($input) {
        $sanitized = array();
        
        // Boolean sanitization
        $sanitized['feature_enabled'] = !empty($input['feature_enabled']);
        
        // Text sanitization - removes HTML tags and encodes special chars
        $sanitized['api_key'] = sanitize_text_field($input['api_key'] ?? '');
        
        // Integer sanitization with bounds checking
        $cache_duration = absint($input['cache_duration'] ?? 3600);
        $sanitized['cache_duration'] = max(300, min(86400, $cache_duration)); // Clamp between 5 min and 24 hours
        
        return $sanitized;
    }
    
    /**
     * Render admin page with nonce protection
     */
    public function render_admin_page() {
        // Capability check - prevents unauthorized access even if menu rendering failed
        if (!current_user_can('manage_options')) {
            wp_die(__('You do not have sufficient permissions to access this page.'));
        }
        
        ?>
        <div class="wrap">
            <h1><?php echo esc_html(get_admin_page_title()); ?></h1>
            <form method="post" action="options.php">
                <?php
                settings_fields('mycompany_plugin_settings_group'); // Outputs nonce and referer fields
                do_settings_sections('mycompany-plugin');
                submit_button();
                ?>
            </form>
        </div>
        <?php
    }
    
    public function render_settings_section() {
        echo '<p>' . esc_html__('Configure plugin behavior below.', 'mycompany-plugin') . '</p>';
    }
    
    public function render_feature_toggle() {
        $options = get_option($this->option_key);
        $checked = !empty($options['feature_enabled']) ? 'checked' : '';
        ?>
        <label>
            <input type="checkbox" 
                   name="<?php echo esc_attr($this->option_key); ?>[feature_enabled]" 
                   value="1" 
                   <?php echo $checked; ?>>
            <?php esc_html_e('Enable the main feature', 'mycompany-plugin'); ?>
        </label>
        <?php
    }
    
    /**
     * Register REST API endpoints
     */
    public function register_rest_routes() {
        // Namespace prevents collisions with other plugins
        $namespace = 'mycompany/v1';
        
        // Public endpoint - no authentication required
        register_rest_route($namespace, '/public-data', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_public_data'),
            'permission_callback' => '__return_true', // Explicitly allow public access
            'args' => array(
                'limit' => array(
                    'required' => false,
                    'default' => 10,
                    'validate_callback' => function($param) {
                        return is_numeric($param) && $param > 0 && $param <= 100;
                    },
                    'sanitize_callback' => 'absint'
                )
            )
        ));
        
        // Protected endpoint - requires authentication and specific capability
        register_rest_route($namespace, '/protected-data', array(
            'methods' => 'POST',
            'callback' => array($this, 'create_protected_data'),
            'permission_callback' => array($this, 'check_admin_permission'),
            'args' => array(
                'title' => array(
                    'required' => true,
                    'type' => 'string',
                    'sanitize_callback' => 'sanitize_text_field',
                    'validate_callback' => function($param) {
                        return !empty($param) && strlen($param) <= 200;
                    }
                ),
                'content' => array(
                    'required' => true,
                    'type' => 'string',
                    'sanitize_callback' => 'wp_kses_post' // Allows safe HTML subset
                )
            )
        ));
        
        // Resource-specific endpoint with ID parameter
        register_rest_route($namespace, '/items/(?P<id>\d+)', array(
            array(
                'methods' => 'GET',
                'callback' => array($this, 'get_item'),
                'permission_callback' => array($this, 'check_read_permission'),
                'args' => array(
                    'id' => array(
                        'validate_callback' => function($param) {
                            return is_numeric($param);
                        }
                    )
                )
            ),
            array(
                'methods' => 'DELETE',
                'callback' => array($this, 'delete_item'),
                'permission_callback' => array($this, 'check_delete_permission'),
                'args' => array(
                    'id' => array(
                        'validate_callback' => function($param) {
                            return is_numeric($param);
                        }
                    )
                )
            )
        ));
    }
    
    /**
     * Permission callback - checks user capability
     */
    public function check_admin_permission($request) {
        return current_user_can('manage_options');
    }
    
    public function check_read_permission($request) {
        // Allow public read or require authentication based on post status
        $id = $request->get_param('id');
        $post = get_post($id);
        
        if (!$post) {
            return new \WP_Error(
                'not_found',
                __('Item not found', 'mycompany-plugin'),
                array('status' => 404)
            );
        }
        
        if ($post->post_status === 'publish') {
            return true; // Public posts readable by anyone
        }
        
        return current_user_can('read_post', $id);
    }
    
    public function check_delete_permission($request) {
        $id = $request->get_param('id');
        return current_user_can('delete_post', $id);
    }
    
    /**
     * REST endpoint callback - public data retrieval
     */
    public function get_public_data($request) {
        $limit = $request->get_param('limit');
        
        $args = array(
            'post_type' => 'mycompany_item',
            'post_status' => 'publish',
            'posts_per_page' => $limit,
            'orderby' => 'date',
            'order' => 'DESC'
        );
        
        $query = new \WP_Query($args);
        $items = array();
        
        if ($query->have_posts()) {
            while ($query->have_posts()) {
                $query->the_post();
                $items[] = array(
                    'id' => get_the_ID(),
                    'title' => get_the_title(),
                    'excerpt' => get_the_excerpt(),
                    'date' => get_the_date('c'), // ISO 8601 format
                    'link' => get_permalink()
                );
            }
            wp_reset_postdata();
        }
        
        return rest_ensure_response($items); // Wraps array in WP_REST_Response
    }
    
    /**
     * REST endpoint callback - protected data creation with SQL injection prevention
     */
    public function create_protected_data($request) {
        global $wpdb;
        
        $user_id = get_current_user_id();
        $title = $request->get_param('title'); // Already sanitized by REST framework
        $content = $request->get_param('content');
        
        // Use prepared statement - NEVER concatenate SQL strings with user input
        $table_name = $wpdb->prefix . 'mycompany_data';
        
        $result = $wpdb->insert(
            $table_name,
            array(
                'user_id' => $user_id,
                'data_key' => $title,
                'data_value' => $content,
                'created_at' => current_time('mysql')
            ),
            array('%d', '%s', '%s', '%s') // Format specifiers: %d = integer, %s = string, %f = float
        );
        
        if (false === $result) {
            return new \WP_Error(
                'database_error',
                __('Failed to create data', 'mycompany-plugin'),
                array('status' => 500)
            );
        }
        
        $inserted_id = $wpdb->insert_id;
        
        return rest_ensure_response(array(
            'id' => $inserted_id,
            'message' => __('Data created successfully', 'mycompany-plugin')
        ));
    }
    
    /**
     * REST endpoint - retrieve single item
     */
    public function get_item($request) {
        $id = $request->get_param('id');
        $post = get_post($id);
        
        if (!$post || $post->post_type !== 'mycompany_item') {
            return new \WP_Error(
                'not_found',
                __('Item not found', 'mycompany-plugin'),
                array('status' => 404)
            );
        }
        
        $data = array(
            'id' => $post->ID,
            'title' => $post->post_title,
            'content' => apply_filters('the_content', $post->post_content),
            'status' => $post->post_status,
            'author' => get_the_author_meta('display_name', $post->post_author),
            'date' => get_the_date('c', $post),
            'modified' => get_the_modified_date('c', $post)
        );
        
        return rest_ensure_response($data);
    }
    
    /**
     * REST endpoint - delete item
     */
    public function delete_item($request) {
        $id = $request->get_param('id');
        $post = get_post($id);
        
        if (!$post || $post->post_type !== 'mycompany_item') {
            return new \WP_Error(
                'not_found',
                __('Item not found', 'mycompany-plugin'),
                array('status' => 404)
            );
        }
        
        $result = wp_delete_post($id, true); // Second param: bypass trash, permanently delete
        
        if (!$result) {
            return new \WP_Error(
                'delete_failed',
                __('Failed to delete item', 'mycompany-plugin'),
                array('status' => 500)
            );
        }
        
        return rest_ensure_response(array(
            'deleted' => true,
            'id' => $id
        ));
    }
    
    /**
     * Content filter example - modifies post content
     */
    public function filter_content($content) {
        // Only run on single post views, not archive pages
        if (!is_singular('post')) {
            return $content;
        }
        
        // Append custom content with proper escaping
        $custom_message = '<div class="mycompany-notice">' 
            . esc_html__('This content is enhanced by My Company Plugin.', 'mycompany-plugin')
            . '</div>';
        
        return $content . $custom_message;
    }
    
    /**
     * Enqueue frontend assets with proper dependencies and versioning
     */
    public function enqueue_frontend_assets() {
        // CSS
        wp_enqueue_style(
            'mycompany-frontend',
            plugins_url('assets/css/frontend.css', __FILE__),
            array(), // Dependencies
            $this->version,
            'all'
        );
        
        // JavaScript with dependencies on jQuery
        wp_enqueue_script(
            'mycompany-frontend',
            plugins_url('assets/js/frontend.js', __FILE__),
            array('jquery'),
            $this->version,
            true // Load in footer
        );
        
        // Localize script - passes PHP data to JavaScript
        wp_localize_script('mycompany-frontend', 'mycompanyData', array(
            'ajaxUrl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('mycompany_frontend_nonce'),
            'restUrl' => rest_url('mycompany/v1'),
            'restNonce' => wp_create_nonce('wp_rest')
        ));
    }
}

// Initialize plugin singleton
PluginCore::get_instance();
```

The nonce system provides cross-site request forgery protection through time-bucketed tokens. When `wp_create_nonce('action_name')` executes, WordPress generates a hash from the current user ID, the action name, a server salt stored in the database, and the current time bucket (12-hour window). The resulting token string gets embedded in forms or URLs. When processing a request, `wp_verify_nonce($nonce, 'action_name')` recomputes the hash for both the current and previous time buckets, accepting the nonce if either hash matches. This creates a validity window of 12 to 24 hours depending on when the nonce was generated within its bucket. The action name parameter namespaces nonces—a nonce generated for 'delete_post' will not validate when checked against 'edit_post', preventing token reuse across different operations.

Authentication in the REST API operates through multiple mechanisms that share a common end state: establishing a valid user context in the global `$current_user` variable. Cookie-based authentication, the default for same-origin requests from the WordPress admin interface, validates the PHP session cookie and checks a nonce passed via the `X-WP-Nonce` header. Application passwords, introduced in WordPress 5.6, allow external applications to authenticate using a secondary password scoped to API access, transmitted via HTTP Basic Authentication where the username matches the WordPress login and the password is the generated application-specific token. OAuth implementations require third-party plugins that implement the full OAuth 2.0 authorization flow, storing access tokens and managing refresh token rotation.

Database query construction must employ prepared statements to prevent SQL injection. The `$wpdb->prepare()` method accepts a SQL template with placeholders (`%d` for integers, `%f` for floats, `%s` for strings) and a variable argument list of values. WordPress escapes each value according to its placeholder type and interpolates the escaped values into the template, producing a safe SQL string. The critical invariant is: never concatenate user input directly into SQL strings. The pattern `$wpdb->query("SELECT * FROM table WHERE id = " . $_GET['id'])` is catastrophically unsafe—an attacker can inject `1 OR 1=1` to dump the entire table. The correct pattern uses `$wpdb->prepare("SELECT * FROM table WHERE id = %d", $_GET['id'])`, which casts the input to an integer and escapes it properly.

```php
<?php
/**
 * Comprehensive security primitives demonstration
 */

namespace MyCompany\Security;

class SecurityExamples {
    
    /**
     * NONCE GENERATION AND VALIDATION
     * Protects against Cross-Site Request Forgery (CSRF)
     */
    public function demonstrate_nonce_system() {
        // Generate nonce for specific action
        $nonce = wp_create_nonce('delete_user_post');
        
        // Embed in form (method 1 - hidden field)
        echo '<form method="post">';
        wp_nonce_field('delete_user_post', '_wpnonce'); // Creates hidden input with name="_wpnonce"
        echo '<input type="submit" value="Delete Post">';
        echo '</form>';
        
        // Embed in URL (method 2 - query parameter)
        $delete_url = wp_nonce_url(
            admin_url('admin-post.php?action=delete_post&id=123'),
            'delete_user_post',
            '_wpnonce'
        );
        echo '<a href="' . esc_url($delete_url) . '">Delete Post</a>';
        
        // Validation in processing function
        if (isset($_POST['_wpnonce'])) {
            $valid = wp_verify_nonce($_POST['_wpnonce'], 'delete_user_post');
            
            if (false === $valid) {
                wp_die(__('Security check failed. This action could not be completed.'));
            }
            
            // $valid returns:
            // 1 if nonce is valid and generated within current 12-hour bucket
            // 2 if nonce is valid and generated within previous 12-hour bucket
            // false if nonce is invalid or expired beyond 24 hours
            
            if (1 === $valid || 2 === $valid) {
                // Proceed with protected action
                $this->delete_post_securely($_POST['post_id']);
            }
        }
        
        // REST API nonce validation
        if (isset($_SERVER['HTTP_X_WP_NONCE'])) {
            $nonce_valid = wp_verify_nonce($_SERVER['HTTP_X_WP_NONCE'], 'wp_rest');
            
            if (!$nonce_valid) {
                return new \WP_Error('rest_cookie_invalid_nonce', __('Cookie nonce is invalid'), array('status' => 403));
            }
        }
    }
    
    /**
     * CAPABILITY CHECKS
     * Enforces role-based access control
     */
    public function demonstrate_capability_checks() {
        // Check if current user can perform action
        if (!current_user_can('edit_posts')) {
            wp_die(__('You do not have permission to edit posts.'));
        }
        
        // Check capability against specific object
        $post_id = 123;
        if (!current_user_can('edit_post', $post_id)) {
            wp_die(__('You do not have permission to edit this post.'));
        }
        
        // Common capabilities by role:
        // Administrator: 'manage_options', 'edit_users', 'delete_users', 'install_plugins'
        // Editor: 'edit_others_posts', 'publish_posts', 'delete_others_posts'
        // Author: 'publish_posts', 'edit_published_posts'
        // Contributor: 'edit_posts', 'delete_posts'
        // Subscriber: 'read'
        
        // Custom capability check for plugin-specific actions
        if (!current_user_can('manage_mycompany_settings')) {
            return new \WP_Error('capability_check_failed', __('Insufficient privileges'));
        }
        
        // Get user object and check capabilities programmatically
        $user = wp_get_current_user();
        if (!$user->exists()) {
            // User is not logged in
            return new \WP_Error('not_authenticated', __('Authentication required'));
        }
        
        // Check if user has specific role
        if (in_array('administrator', $user->roles, true)) {
            // User is admin
        }
        
        // Map custom post type capabilities
        $capabilities = array(
            'edit_post' => 'edit_mycompany_item',
            'edit_posts' => 'edit_mycompany_items',
            'edit_others_posts' => 'edit_others_mycompany_items',
            'publish_posts' => 'publish_mycompany_items',
            'read_post' => 'read_mycompany_item',
            'delete_post' => 'delete_mycompany_item'
        );
        
        // Add capabilities to role
        $role = get_role('editor');
        if ($role) {
            foreach ($capabilities as $cap) {
                $role->add_cap($cap);
            }
        }
    }
    
    /**
     * DATA SANITIZATION
     * Removes dangerous content from input
     */
    public function demonstrate_sanitization($input) {
        // Text field sanitization - strips HTML tags and encodes special characters
        $clean_text = sanitize_text_field($input['text']);
        // "Hello <script>alert('xss')</script>" becomes "Hello alert('xss')"
        
        // Textarea sanitization - strips tags but preserves line breaks
        $clean_textarea = sanitize_textarea_field($input['textarea']);
        
        // Email validation and sanitization
        $clean_email = sanitize_email($input['email']);
        // "user+tag@example.com<script>" becomes "user+tag@example.com"
        
        // URL sanitization - removes dangerous protocols
        $clean_url = esc_url_raw($input['url']);
        // "javascript:alert('xss')" becomes ""
        // "http://example.com/path?param=value" remains unchanged
        
        // File name sanitization - removes directory traversal attempts
        $clean_filename = sanitize_file_name($input['filename']);
        // "../../etc/passwd" becomes "etcpasswd"
        
        // HTML sanitization - allows safe HTML subset
        $clean_html = wp_kses_post($input['html']);
        // Allows: a, br, strong, em, p, ul, ol, li, blockquote, img, etc.
        // Removes: script, iframe, object, embed, form
        
        // Custom allowed HTML tags
        $allowed_html = array(
            'a' => array(
                'href' => array(),
                'title' => array(),
                'target' => array()
            ),
            'strong' => array(),
            'em' => array()
        );
        $custom_clean_html = wp_kses($input['custom_html'], $allowed_html);
        
        // Integer sanitization with absint() - absolute integer, never negative
        $clean_id = absint($input['id']);
        // "-5" becomes 5
        // "10.7" becomes 10
        // "abc" becomes 0
        
        // Array sanitization - recursive cleaning
        $clean_array = array_map('sanitize_text_field', $input['array_data']);
        
        // Key sanitization for array indices or database keys
        $clean_key = sanitize_key($input['option_name']);
        // "My Option Name!" becomes "my_option_name"
        
        return array(
            'text' => $clean_text,
            'textarea' => $clean_textarea,
            'email' => $clean_email,
            'url' => $clean_url,
            'filename' => $clean_filename,
            'html' => $clean_html,
            'id' => $clean_id,
            'array' => $clean_array,
            'key' => $clean_key
        );
    }
    
    /**
     * DATA VALIDATION
     * Enforces schema constraints and business rules
     */
    public function demonstrate_validation($input) {
        $errors = new \WP_Error();
        
        // Email validation
        if (!is_email($input['email'])) {
            $errors->add('invalid_email', __('Please provide a valid email address.'));
        }
        
        // URL validation
        if (!filter_var($input['url'], FILTER_VALIDATE_URL)) {
            $errors->add('invalid_url', __('Please provide a valid URL.'));
        }
        
        // Integer range validation
        if (!is_numeric($input['age']) || $input['age'] < 0 || $input['age'] > 120) {
            $errors->add('invalid_age', __('Age must be between 0 and 120.'));
        }
        
        // String length validation
        if (strlen($input['username']) < 3 || strlen($input['username']) > 20) {
            $errors->add('invalid_username_length', __('Username must be 3-20 characters.'));
        }
        
        // Pattern matching validation
        if (!preg_match('/^[a-z0-9_-]+$/i', $input['username'])) {
            $errors->add('invalid_username_chars', __('Username can only contain letters, numbers, hyphens, and underscores.'));
        }
        
        // Required field validation
        if (empty($input['required_field'])) {
            $errors->add('missing_required', __('This field is required.'));
        }
        
        // Enum validation - value must be in allowed set
        $allowed_statuses = array('draft', 'pending', 'published');
        if (!in_array($input['status'], $allowed_statuses, true)) {
            $errors->add('invalid_status', __('Invalid status value.'));
        }
        
        // Date validation
        $date = \DateTime::createFromFormat('Y-m-d', $input['date']);
        if (!$date || $date->format('Y-m-d') !== $input['date']) {
            $errors->add('invalid_date', __('Date must be in YYYY-MM-DD format.'));
        }
        
        // File upload validation
        if (isset($_FILES['upload'])) {
            $allowed_types = array('image/jpeg', 'image/png', 'image/gif');
            $file_type = $_FILES['upload']['type'];
            
            if (!in_array($file_type, $allowed_types, true)) {
                $errors->add('invalid_file_type', __('Only JPEG, PNG, and GIF images are allowed.'));
            }
            
            $max_size = 5 * 1024 * 1024; // 5MB
            if ($_FILES['upload']['size'] > $max_size) {
                $errors->add('file_too_large', __('File size must not exceed 5MB.'));
            }
        }
        
        // Check if any errors occurred
        if ($errors->has_errors()) {
            return $errors;
        }
        
        return true; // Validation passed
    }
    
    /**
     * OUTPUT ESCAPING
     * Prevents injection attacks when displaying data
     */
    public function demonstrate_escaping($data) {
        // HTML escaping - converts < > & " ' to entities
        echo '<p>' . esc_html($data['user_input']) . '</p>';
        // "<script>alert('xss')</script>" displays as literal text
        
        // Attribute escaping - for HTML attribute values
        echo '<input type="text" value="' . esc_attr($data['user_value']) . '">';
        // Escapes quotes and special characters that could break out of attribute
        
        // URL escaping - for href and src attributes
        echo '<a href="' . esc_url($data['user_url']) . '">Link</a>';
        // Removes javascript: and data: protocols
        
        // JavaScript escaping - for inline script blocks
        echo '<script>var userInput = "' . esc_js($data['user_input']) . '";</script>';
        // Escapes quotes, backslashes, and control characters
        
        // Textarea escaping
        echo '<textarea>' . esc_textarea($data['user_content']) . '</textarea>';
        // Escapes HTML entities
        
        // SQL escaping - for LIKE patterns
        global $wpdb;
        $search_term = $data['search'];
        $escaped_like = '%' . $wpdb->esc_like($search_term) . '%';
        // Escapes %, _, and backslash characters that have special meaning in LIKE
        
        // Context-aware escaping for allowed HTML
        echo wp_kses_post($data['post_content']);
        // Allows safe HTML tags, removes dangerous ones
        
        // Escaping in different contexts (guideline summary):
        // - HTML body content: esc_html()
        // - HTML attributes: esc_attr()
        // - URLs: esc_url()
        // - JavaScript strings: esc_js()
        // - SQL LIKE wildcards: $wpdb->esc_like()
        // - Allow limited HTML: wp_kses() or wp_kses_post()
    }
    
    /**
     * SQL INJECTION PREVENTION
     * Demonstrates safe database query patterns
     */
    public function demonstrate_sql_safety($user_id, $search_term, $status) {
        global $wpdb;
        
        // WRONG - Vulnerable to SQL injection
        // $query = "SELECT * FROM {$wpdb->posts} WHERE post_author = {$user_id}";
        // If $user_id is "1 OR 1=1", this exposes all posts
        
        // CORRECT - Using prepare() with placeholders
        $query = $wpdb->prepare(
            "SELECT * FROM {$wpdb->posts} WHERE post_author = %d",
            $user_id
        );
        $posts = $wpdb->get_results($query);
        
        // Multiple placeholders
        $query = $wpdb->prepare(
            "SELECT * FROM {$wpdb->posts} WHERE post_author = %d AND post_status = %s",
            $user_id,
            $status
        );
        
        // Array of values using vsprintf pattern
        $query = $wpdb->prepare(
            "SELECT * FROM {$wpdb->posts} WHERE ID IN (%d, %d, %d)",
            array(1, 2, 3)
        );
        
        // LIKE queries with wildcards
        $like_term = '%' . $wpdb->esc_like($search_term) . '%';
        $query = $wpdb->prepare(
            "SELECT * FROM {$wpdb->posts} WHERE post_title LIKE %s",
            $like_term
        );
        
        // INSERT with prepared values
        $wpdb->insert(
            $wpdb->prefix . 'custom_table',
            array(
                'user_id' => $user_id,
                'title' => $search_term,
                'count' => 42
            ),
            array('%d', '%s', '%d') // Format specifiers
        );
        
        // UPDATE with WHERE clause
        $wpdb->update(
            $wpdb->prefix . 'custom_table',
            array('status' => $status),  // Data to update
            array('id' => $user_id),     // WHERE clause
            array('%s'),                 // Format for data
            array('%d')                  // Format for WHERE
        );
        
        // DELETE with WHERE clause
        $wpdb->delete(
            $wpdb->prefix . 'custom_table',
            array('user_id' => $user_id),
            array('%d')
        );
        
        // Complex query with multiple conditions
        $query = $wpdb->prepare(
            "SELECT p.*, pm.meta_value 
             FROM {$wpdb->posts} p
             LEFT JOIN {$wpdb->postmeta} pm ON p.ID = pm.post_id
             WHERE p.post_type = %s 
               AND p.post_status = %s
               AND pm.meta_key = %s
             ORDER BY p.post_date DESC
             LIMIT %d",
            'post',
            'publish',
            'custom_field',
            10
        );
        
        // IN clause with dynamic list - requires manual placeholder generation
        $post_ids = array(1, 5, 10, 15);
        $placeholders = implode(',', array_fill(0, count($post_ids), '%d'));
        $query = $wpdb->prepare(
            "SELECT * FROM {$wpdb->posts} WHERE ID IN ($placeholders)",
            $post_ids
        );
        
        return $posts;
    }
    
    /**
     * AUTHENTICATION AND SESSION MANAGEMENT
     */
    public function demonstrate_authentication() {
        // Check if user is logged in
        if (!is_user_logged_in()) {
            // Redirect to login page with return URL
            $login_url = wp_login_url(get_permalink());
            wp_redirect($login_url);
            exit;
        }
        
        // Get current user data
        $current_user = wp_get_current_user();
        $user_id = $current_user->ID;
        $username = $current_user->user_login;
        $email = $current_user->user_email;
        
        // Programmatic login (use with caution)
        $user = get_user_by('login', 'admin');
        if ($user) {
            wp_set_current_user($user->ID);
            wp_set_auth_cookie($user->ID);
            // Never log users in without proper credential verification
        }
        
        // Logout current user
        wp_logout();
        
        // Generate application password (WordPress 5.6+)
        // This requires UI interaction - cannot be done programmatically for security
        
        // Validate application password in API request
        if (isset($_SERVER['PHP_AUTH_USER']) && isset($_SERVER['PHP_AUTH_PW'])) {
            $user = wp_authenticate_application_password(
                null,
                $_SERVER['PHP_AUTH_USER'],
                $_SERVER['PHP_AUTH_PW']
            );
            
            if (is_wp_error($user)) {
                // Authentication failed
                return new \WP_Error('authentication_failed', __('Invalid credentials'));
            }
            
            wp_set_current_user($user->ID);
        }
        
        // Session management - WordPress uses PHP sessions indirectly through cookies
        // Auth cookie structure: username|expiration|token|hmac
        // Token is hashed password fragment, HMAC validates integrity
        
        // Cookie security flags
        // COOKIEPATH: limits cookie to WordPress installation path
        // COOKIE_DOMAIN: restricts to specific domain
        // SECURE: requires HTTPS
        // HTTPONLY: prevents JavaScript access
        // SAMESITE: CSRF protection at browser level
        
        // Check auth cookie validity
        if (!wp_validate_auth_cookie($_COOKIE[LOGGED_IN_COOKIE], 'logged_in')) {
            // Cookie is invalid or expired
            wp_logout();
        }
    }
    
    /**
     * COMPREHENSIVE FORM PROCESSING EXAMPLE
     * Combines all security primitives
     */
    public function process_secure_form() {
        // 1. Check request method
        if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
            return new \WP_Error('invalid_method', __('Invalid request method'));
        }
        
        // 2. Verify nonce
        if (!isset($_POST['_wpnonce']) || !wp_verify_nonce($_POST['_wpnonce'], 'mycompany_form_action')) {
            return new \WP_Error('nonce_failed', __('Security verification failed'));
        }
        
        // 3. Check user capability
        if (!current_user_can('edit_posts')) {
            return new \WP_Error('capability_failed', __('You do not have permission to perform this action'));
        }
        
        // 4. Sanitize input
        $title = sanitize_text_field($_POST['title'] ?? '');
        $content = wp_kses_post($_POST['content'] ?? '');
        $category_id = absint($_POST['category'] ?? 0);
        $email = sanitize_email($_POST['email'] ?? '');
        
        // 5. Validate input
        $errors = new \WP_Error();
        
        if (empty($title)) {
            $errors->add('missing_title', __('Title is required'));
        }
        
        if (strlen($title) > 200) {
            $errors->add('title_too_long', __('Title must not exceed 200 characters'));
        }
        
        if (!empty($email) && !is_email($email)) {
            $errors->add('invalid_email', __('Invalid email address'));
        }
        
        if ($errors->has_errors()) {
            return $errors;
        }
        
        // 6. Process with safe database operations
        global $wpdb;
        
        $result = $wpdb->insert(
            $wpdb->prefix . 'custom_submissions',
            array(
                'title' => $title,
                'content' => $content,
                'category_id' => $category_id,
                'email' => $email,
                'user_id' => get_current_user_id(),
                'created_at' => current_time('mysql')
            ),
            array('%s', '%s', '%d', '%s', '%d', '%s')
        );
        
        if (false === $result) {
            return new \WP_Error('database_error', __('Failed to save submission'));
        }
        
        // 7. Return success response
        return array(
            'success' => true,
            'id' => $wpdb->insert_id,
            'message' => __('Submission saved successfully')
        );
    }
    
    private function delete_post_securely($post_id) {
        // Implementation of secure post deletion
        $post_id = absint($post_id);
        
        if (!current_user_can('delete_post', $post_id)) {
            return false;
        }
        
        return wp_delete_post($post_id, true);
    }
}
```

## 3. High-Performance Optimization & Failure Modes

Performance optimization in WordPress plugins centers on minimizing database queries, deferring expensive operations, and leveraging WordPress's built-in caching mechanisms. The most common performance antipattern is the N+1 query problem, where retrieving a list of posts triggers one additional query per post to fetch related metadata. WordPress provides `WP_Query` with the `update_post_meta_cache` and `update_post_term_cache` parameters that batch-fetch metadata and term relationships in two queries rather than one per post. For custom tables, developers should implement similar batch-loading patterns, fetching all required data in a single query with JOIN operations rather than iterating and querying individually.

Transient caching provides time-bound storage for expensive computations. The function `set_transient('key', $data, $expiration)` stores data in the database with an expiration timestamp, while `get_transient('key')` retrieves it if not expired, returning false otherwise. Transients suit API call results, complex query results, or rendered HTML fragments. Object caching with `wp_cache_set()` and `wp_cache_get()` offers request-lifetime memory caching, but without a persistent backend (Memcached, Redis), these caches evaporate at request end. Proper cache invalidation requires deleting transients when underlying data changes—updating a post should invalidate any transients that include that post's data.

Hook proliferation degrades performance when plugins register excessive callbacks, particularly on high-frequency hooks like `the_content` or `the_posts`. Each registered callback adds overhead to the dispatch mechanism. Profiling with Query Monitor or XHProf reveals which hooks dominate execution time. The optimization strategy involves consolidating callbacks, conditionally registering hooks only when needed (checking `is_admin()`, `is_singular()`, etc. before registration), and removing hooks after one-time initialization. The pattern `remove_action('hook_name', 'callback_function', priority)` detaches callbacks, though it requires knowing the exact callback reference and priority.

Database schema optimization matters for custom tables. Adding indexes on frequently queried columns dramatically improves SELECT performance but slows INSERT and UPDATE operations due to index maintenance overhead. The columns in WHERE clauses, JOIN conditions, and ORDER BY clauses should have indexes. Composite indexes (multi-column indexes) optimize queries that filter on multiple columns simultaneously, but column order in the index matters—place the most selective column first. The WordPress `dbDelta()` function handles index creation when included in the CREATE TABLE statement's KEY or INDEX clauses.

REST API performance optimization requires pagination on list endpoints to prevent unbounded result sets. Implementing the `per_page` and `page` parameters with default limits (typically 10-100) prevents a single request from fetching thousands of records. Endpoint caching via transients or HTTP cache headers (Cache-Control, ETag) reduces server load for frequently requested, rarely changing resources. The REST API response format includes `_links` and `_embedded` sections for HATEOAS-style navigation—these can be stripped when clients don't use them by implementing custom response handlers.

Authentication failures in the REST API manifest in several ways. Cookie authentication works for same-origin requests where JavaScript executes in the admin context and WordPress sets the auth cookie, but cross-origin requests blocked by CORS require alternative authentication. Application passwords solve this for external applications but require WordPress 5.6+ and SSL (WordPress refuses to create application passwords over non-HTTPS connections). OAuth implementations via plugins like WP OAuth Server add token endpoint complexity and require developers to handle token refresh logic and revocation.

Permission callback failures cause either over-permissive APIs (returning `true` or `__return_true` for protected endpoints) or overly restrictive APIs (checking `manage_options` for read operations). The correct pattern is context-specific: public data returns `true` or performs limited validation, user-specific data checks ownership (`get_current_user_id() === $request['user_id']`), and administrative data checks appropriate capabilities. Missing permission callbacks default to denying access, which is safe but non-functional.

SQL injection vulnerabilities persist when developers bypass `$wpdb->prepare()` in favor of string concatenation, particularly when constructing dynamic ORDER BY clauses, IN lists, or complex WHERE conditions. The belief that `esc_sql()` suffices is incorrect—it only escapes quotes, not SQL keywords. For ORDER BY clauses, whitelist the column name against an allowed set. For dynamic IN lists, generate placeholder strings programmatically: `implode(',', array_fill(0, count($values), '%d'))`, then use `$wpdb->prepare()` with the values array.

Cross-site scripting vulnerabilities emerge from missing output escaping, particularly in custom admin pages where developers assume admin users are trustworthy. An administrator account compromised via phishing or credential reuse can inject JavaScript that executes with administrative privileges, creating backdoor admin accounts or installing malicious plugins. The defense requires escaping all output, regardless of user role. The pattern `echo $data` is always wrong in templates; the correct pattern is `echo esc_html($data)` or the appropriate context-specific escaping function.

CSRF vulnerabilities beyond nonce failures include missing nonce checks on AJAX handlers, state-changing GET requests, and operations that bypass the nonce system entirely. WordPress AJAX functions registered with `wp_ajax_` and `wp_ajax_nopriv_` prefixes require manual nonce verification—WordPress does not automatically validate them. The pattern for AJAX handlers checks `check_ajax_referer('action_name')`, which calls `wp_verify_nonce()` and dies with -1 on failure. State-changing operations must use POST requests; WordPress convention uses GET only for reads.

Capability escalation vulnerabilities occur when plugins create custom capabilities without properly scoping them to appropriate roles. A plugin that adds `manage_mycompany_settings` capability to the Subscriber role grants low-privilege users administrative control over plugin functionality. The correct pattern uses `get_role()` to retrieve specific roles (Administrator, Editor) and adds capabilities only to those roles. Custom capabilities should follow WordPress naming conventions: `edit_{$post_type}`, `delete_{$post_type}`, `publish_{$post_type}`, etc.

File upload vulnerabilities arise from insufficient validation. Checking `$_FILES['upload']['type']` is insufficient because the MIME type comes from the client and can be spoofed. The correct validation uses `wp_check_filetype_and_ext()`, which checks file extension against WordPress's allowed MIME types list and verifies the extension matches the actual file content via magic byte inspection. Additionally, uploaded files should be moved to non-executable directories (default `wp-content/uploads/`) and WordPress should be configured to serve uploads with appropriate Content-Type headers rather than executing them as PHP.

Plugin conflicts manifest when two plugins define the same function, class, or global variable. The error message "Fatal error: Cannot redeclare function X" terminates execution. Defense requires wrapping all function definitions in `if (!function_exists())` checks, using PHP namespaces, or encapsulating functionality in unique class names with autoloading. For global JavaScript, namespacing variables under a plugin-specific object (`window.myCompanyPlugin = {}`) prevents collisions. Enqueueing scripts with unique handles and proper dependency declarations prevents load-order conflicts.

Memory exhaustion occurs when processing large datasets in plugin code, particularly when fetching posts without limits (`'posts_per_page' => -1`). The WordPress loop exhausts memory if thousands of post objects load simultaneously. The solution uses pagination with `'posts_per_page' => 100` and processes in batches, or uses `'fields' => 'ids'` to retrieve only post IDs rather than full objects, then loads full data in chunks. For import operations, processing in background jobs via WP-Cron or Action Scheduler prevents timeout and memory limits.

Race conditions in transient caching emerge when multiple requests simultaneously detect a missing cache key and each performs the expensive operation to populate it. This "cache stampede" wastes resources. The defense implements cache warming (pre-populating caches via scheduled jobs), cache locking (atomic check-and-set operations), or probabilistic early expiration (refreshing caches before they expire for high-traffic keys). WordPress core does not provide locking primitives; plugins requiring them must implement via database advisory locks or external coordination services.

The uninstall lifecycle, distinct from deactivation, handles permanent plugin removal. While `register_deactivation_hook()` runs when a plugin is deactivated (temporary), the uninstall process executes when a plugin is deleted from the admin interface. Plugins implement uninstall either via `register_uninstall_hook()` or by creating an `uninstall.php` file. Uninstall operations should remove custom database tables, delete options, clear transients, unschedule cron jobs, and delete uploaded files. The invariant is: deactivation is temporary and preserves data; uninstall is permanent and removes all traces. Users expect data preservation across deactivation but complete removal on deletion.
