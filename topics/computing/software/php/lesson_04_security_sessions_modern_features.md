# Lesson 4: Security Primitives, Session Management, Modern Language Features

## 1. First-Principles Intuition & Invariants

The evolution of PHP from a templating convenience layer into a robust application platform traces a story common to all successful systems software: initial permissiveness gradually constrained by security necessity and type discipline. Where early PHP embraced register_globals and magic quotes—features that blurred boundaries between trusted application state and untrusted external input—modern PHP enforces strict separation through input validation gates, parameterized query interfaces, and cryptographic session integrity. This transformation reflects a deeper architectural shift from string-centric scripting toward structured data flow with explicit trust boundaries.

Security in web applications fundamentally concerns **authority verification** and **data integrity preservation** across trust domain transitions. Every HTTP request crosses from an untrusted network—where attackers control payloads, headers, and timing—into the application's memory space, where code operates on the assumption that variables contain semantically valid data. The critical security invariant states that **no external input may influence control flow or query semantics without explicit validation and sanitization**. Violating this invariant creates injection vulnerabilities: SQL injection when untrusted strings alter query structure, Cross-Site Scripting (XSS) when unescaped output modifies HTML parsing context, and Cross-Site Request Forgery (CSRF) when ambient credentials enable unauthorized state transitions.

PHP's execution model compounds these risks through its shared-nothing architecture. Each request spawns a fresh process or reuses a pooled worker with clean memory, meaning state persists only through explicit serialization to databases, filesystem sessions, or external caches. This stateless foundation makes session management—the mechanism binding multiple HTTP requests to a coherent user identity—a first-order security concern. Sessions depend on cryptographic identifiers stored in cookies, which travel with every request and carry ambient authority. Without proper session configuration, applications expose themselves to fixation attacks (where attackers preset session IDs), hijacking through XSS-stolen cookies, or privilege escalation via unsecured session storage.

Modern PHP addresses these challenges through layered defenses. The PDO (PHP Data Objects) abstraction enforces prepared statements with driver-level parameter binding, ensuring queries remain structurally invariant regardless of input content. Output escaping functions like `htmlspecialchars()` transform data according to output context—HTML body, attribute, JavaScript, or URL—preventing injection through context-appropriate encoding. CSRF tokens implement the synchronizer token pattern, embedding cryptographic nonces in forms that attackers cannot forge due to same-origin policy restrictions. Password hashing through `password_hash()` applies bcrypt or Argon2 with automatic salt generation and configurable cost factors, defending against both rainbow tables and GPU-accelerated brute force.

Type declarations, introduced incrementally from PHP 7.0 onward and strengthened through union types, intersection types, and readonly properties, shift error detection from runtime crashes to static analysis boundaries. Where dynamic typing once allowed `$userId = $_GET['id']` to pass a SQL-injected string directly into a query, strict scalar types (`declare(strict_types=1)`) force explicit coercion or rejection at function boundaries. This compile-time discipline reduces the attack surface by making implicit type juggling—a historical source of authentication bypasses—mechanically impossible.

Attributes (PHP 8.0+) and enums (PHP 8.1+) extend type safety into metadata and discriminated unions. Attributes replace docblock annotations with structured, reflectable metadata that validators and routers can inspect without fragile string parsing. Enums eliminate magic constant proliferation, replacing `if ($status === 'active')` with exhaustive match expressions over `UserStatus::Active`, enabling static analysis to detect impossible states. Fibers (PHP 8.1+) provide cooperative multitasking within a single thread, allowing asynchronous I/O frameworks to interleave database queries and HTTP requests without blocking the event loop—critical for high-concurrency applications where per-request latency determines throughput.

The JIT compiler (PHP 8.0+), based on DynASM from LuaJIT, translates hot opcode sequences into native machine code at runtime. While opcache already eliminates script parsing overhead, the JIT accelerates CPU-intensive numerical workloads by eliminating the VM's dispatch loop and specializing type checks. For typical CRUD applications dominated by I/O latency, JIT provides minimal benefit, but for data processing, cryptographic operations, or complex business logic, it narrows the performance gap with ahead-of-time compiled languages.

Security, ultimately, rests on **fail-secure defaults** and **defense in depth**. PHP's security story succeeds not through eliminating vulnerabilities—an impossible goal given Turing-complete expressiveness—but by making secure patterns the path of least resistance: prepared statements easier than string concatenation, automatic CSRF tokens simpler than manual nonce management, and strict types opt-in but mechanically enforceable. The remainder of this lesson dissects these mechanisms at the implementation level, grounding each defense in the specific attack it defeats.

## 2. Core Architecture & Mechanics

### Input Validation and Trust Boundaries

Input validation establishes the first security perimeter, transforming untrusted external data into typed, bounded application values. PHP applications receive input through superglobal arrays—`$_GET`, `$_POST`, `$_COOKIE`, `$_SERVER`, and `$_FILES`—each representing a different protocol-level channel. These arrays contain **raw, unvalidated strings** (or arrays of strings) parsed from HTTP request components. The security contract requires that **no value from these superglobals directly influences application logic without passing through a validation gate**.

Validation operates along two orthogonal axes: **type enforcement** and **semantic constraints**. Type enforcement ensures input conforms to expected scalar types (integer, float, string, boolean) or structured shapes (arrays with specific keys). Semantic constraints verify business-level invariants: age within plausible ranges, email format matching RFC 5322, or user IDs corresponding to existing records. PHP's `filter_var()` function family provides built-in filters combining both concerns.

Consider a user profile update endpoint receiving numeric user IDs:

```php
declare(strict_types=1);

final class UserController {
    public function updateProfile(PDO $db): void {
        // WRONG: Direct usage permits SQL injection via array tricks
        // $userId = $_POST['user_id'];
        
        // CORRECT: Validate as positive integer
        $userId = filter_input(INPUT_POST, 'user_id', FILTER_VALIDATE_INT, [
            'options' => ['min_range' => 1]
        ]);
        
        if ($userId === false || $userId === null) {
            http_response_code(400);
            echo json_encode(['error' => 'Invalid user ID']);
            return;
        }
        
        // Now $userId is guaranteed integer >= 1
        $this->performUpdate($db, $userId);
    }
    
    private function performUpdate(PDO $db, int $userId): void {
        // Type declaration enforces compile-time guarantee
    }
}
```

The `FILTER_VALIDATE_INT` filter rejects non-numeric strings, floating-point representations, and values outside the specified range. The `false` return distinguishes validation failure from legitimate zero values. Critically, the `performUpdate()` method's type signature (`int $userId`) creates a second validation layer—the PHP runtime enforces that only integer values reach business logic, even if validation code is bypassed through refactoring errors.

For string inputs requiring semantic validation, custom validator classes encapsulate domain-specific rules:

```php
final class EmailValidator {
    private const MAX_LENGTH = 254; // RFC 5321
    
    public function validate(string $email): ?string {
        $email = trim($email);
        
        if (strlen($email) > self::MAX_LENGTH) {
            return null;
        }
        
        $filtered = filter_var($email, FILTER_VALIDATE_EMAIL);
        if ($filtered === false) {
            return null;
        }
        
        // Additional check: verify domain has MX or A records
        [$local, $domain] = explode('@', $filtered);
        if (!checkdnsrr($domain, 'MX') && !checkdnsrr($domain, 'A')) {
            return null;
        }
        
        return $filtered;
    }
}
```

This validator combines PHP's built-in email filter with DNS verification, rejecting syntactically valid but unroutable addresses. The return type `?string` (nullable string) signals validation failure through `null`, allowing callers to distinguish missing input from invalid input through explicit null checks.

Array inputs require recursive validation to prevent deeply nested injection attacks. Consider a JSON API accepting hierarchical data:

```php
final class SchemaValidator {
    /**
     * Validates array structure against schema definition
     * 
     * @param array<string, mixed> $data
     * @param array<string, array{type: string, required?: bool, min?: int, max?: int}> $schema
     * @return array<string, mixed>
     * @throws ValidationException
     */
    public function validate(array $data, array $schema): array {
        $validated = [];
        
        foreach ($schema as $field => $rules) {
            $value = $data[$field] ?? null;
            $required = $rules['required'] ?? false;
            
            if ($value === null && $required) {
                throw new ValidationException("Missing required field: {$field}");
            }
            
            if ($value !== null) {
                $validated[$field] = match ($rules['type']) {
                    'int' => $this->validateInt($value, $rules),
                    'string' => $this->validateString($value, $rules),
                    'email' => $this->validateEmail($value),
                    'array' => is_array($value) ? $value : throw new ValidationException("Invalid array"),
                    default => throw new ValidationException("Unknown type: {$rules['type']}")
                };
            }
        }
        
        return $validated;
    }
    
    private function validateInt(mixed $value, array $rules): int {
        if (!is_numeric($value)) {
            throw new ValidationException("Expected integer");
        }
        
        $int = (int)$value;
        
        if (isset($rules['min']) && $int < $rules['min']) {
            throw new ValidationException("Value below minimum: {$rules['min']}");
        }
        
        if (isset($rules['max']) && $int > $rules['max']) {
            throw new ValidationException("Value above maximum: {$rules['max']}");
        }
        
        return $int;
    }
    
    private function validateString(mixed $value, array $rules): string {
        if (!is_string($value)) {
            throw new ValidationException("Expected string");
        }
        
        $len = mb_strlen($value);
        
        if (isset($rules['min']) && $len < $rules['min']) {
            throw new ValidationException("String too short");
        }
        
        if (isset($rules['max']) && $len > $rules['max']) {
            throw new ValidationException("String too long");
        }
        
        return $value;
    }
    
    private function validateEmail(mixed $value): string {
        if (!is_string($value)) {
            throw new ValidationException("Expected string");
        }
        
        $validator = new EmailValidator();
        $email = $validator->validate($value);
        
        if ($email === null) {
            throw new ValidationException("Invalid email format");
        }
        
        return $email;
    }
}
```

This schema-driven approach centralizes validation logic, making security reviews tractable and preventing inconsistencies across endpoints. The `match` expression (PHP 8.0+) provides exhaustive type dispatch with compile-time completeness checking—if a new type is added to the schema, the absence of a corresponding match arm triggers a runtime error.

### SQL Injection Defense Through Prepared Statements

SQL injection exploits the lack of boundary between query structure and data literals. When applications construct queries through string concatenation, attackers inject SQL syntax that alters the query's semantic meaning. Consider a naive authentication check:

```php
// CATASTROPHICALLY INSECURE
$username = $_POST['username'];
$password = $_POST['password'];

$query = "SELECT id FROM users WHERE username = '$username' AND password = '$password'";
$result = $db->query($query);
```

An attacker supplying `username = "admin' --"` transforms the query into:

```sql
SELECT id FROM users WHERE username = 'admin' --' AND password = ''
```

The `--` comment marker nullifies the password check, granting access without credential verification. More sophisticated payloads use `UNION` injections to exfiltrate entire tables or stacked queries to execute arbitrary DDL statements.

Prepared statements defeat injection by sending query structure and data through separate protocol channels. The database parses the query template into an execution plan before parameter binding occurs, making it structurally impossible for data to alter the query's logical structure. PDO provides prepared statement support across MySQL, PostgreSQL, SQLite, and other backends:

```php
final class AuthService {
    public function __construct(private PDO $db) {
        // Critical: Disable emulated prepares to ensure driver-level binding
        $this->db->setAttribute(PDO::ATTR_EMULATE_PREPARES, false);
        
        // Throw exceptions on error rather than silent failure
        $this->db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    }
    
    public function authenticate(string $username, string $password): ?int {
        $stmt = $this->db->prepare(
            'SELECT id, password_hash FROM users WHERE username = :username'
        );
        
        $stmt->execute(['username' => $username]);
        
        $user = $stmt->fetch(PDO::FETCH_ASSOC);
        if ($user === false) {
            // Username not found - use constant-time comparison to prevent timing leak
            password_verify($password, '$2y$10$invalidhashXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX');
            return null;
        }
        
        if (!password_verify($password, $user['password_hash'])) {
            return null;
        }
        
        return (int)$user['id'];
    }
}
```

The `:username` placeholder gets bound by PDO through the driver's native parameter binding mechanism. PostgreSQL's libpq and MySQL's binary protocol send parameters as separate typed values, making SQL injection mechanically impossible regardless of input content. The `ATTR_EMULATE_PREPARES` setting is critical—when enabled, PDO emulates preparation by client-side string escaping, reintroducing injection risk. Disabling emulation forces true server-side preparation.

For dynamic queries requiring variable column selection or table names (which cannot be parameterized), whitelist validation is mandatory:

```php
final class ReportGenerator {
    private const ALLOWED_COLUMNS = ['id', 'username', 'email', 'created_at'];
    private const ALLOWED_ORDERS = ['ASC', 'DESC'];
    
    public function generateReport(
        PDO $db,
        string $orderColumn,
        string $orderDirection,
        int $limit
    ): array {
        if (!in_array($orderColumn, self::ALLOWED_COLUMNS, true)) {
            throw new InvalidArgumentException('Invalid sort column');
        }
        
        if (!in_array($orderDirection, self::ALLOWED_ORDERS, true)) {
            throw new InvalidArgumentException('Invalid sort direction');
        }
        
        // Safe: identifiers validated against whitelist
        $sql = sprintf(
            'SELECT id, username, email FROM users ORDER BY %s %s LIMIT :limit',
            $orderColumn,
            $orderDirection
        );
        
        $stmt = $db->prepare($sql);
        $stmt->execute(['limit' => $limit]);
        
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }
}
```

Identifier whitelisting prevents injection through column or table name manipulation. The `in_array()` strict comparison mode (`true` third parameter) prevents type juggling attacks where `0 == 'string'` evaluates true.

### Output Escaping and Context-Aware Encoding

Output escaping transforms data according to the parsing context where it will be interpreted. HTML, JavaScript, URLs, and CSS each define distinct syntactic boundaries, requiring different encoding strategies. Failing to escape output creates Cross-Site Scripting (XSS) vulnerabilities, where attackers inject malicious scripts that execute in victims' browsers with full application authority.

The `htmlspecialchars()` function provides HTML context escaping by converting special characters into named entities:

```php
final class ProfileRenderer {
    public function renderUserBio(string $bio): string {
        // Escape for HTML body context
        $escaped = htmlspecialchars($bio, ENT_QUOTES | ENT_HTML5, 'UTF-8');
        
        return "<div class=\"user-bio\">{$escaped}</div>";
    }
}
```

The `ENT_QUOTES` flag converts both double and single quotes to entities, preventing attribute injection attacks. The `ENT_HTML5` flag ensures HTML5-compliant entity encoding. The explicit `UTF-8` encoding specification prevents charset confusion attacks where attackers exploit charset mismatches to smuggle unescaped characters.

JavaScript context requires different encoding because JavaScript interprets backslash escapes:

```php
final class JsonResponseRenderer {
    public function renderUserData(array $user): string {
        // json_encode handles JavaScript escaping automatically
        $json = json_encode($user, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT);
        
        return "<script>const userData = {$json};</script>";
    }
}
```

The `JSON_HEX_*` flags escape HTML-significant characters even within JSON strings, preventing breakout attacks where `</script>` inside a JSON string terminates the script block prematurely. For security-critical applications, prefer delivering JSON through separate API endpoints with `Content-Type: application/json` headers rather than embedding in HTML.

URL context requires percent-encoding:

```php
final class RedirectHandler {
    public function generateRedirectUrl(string $returnPath): string {
        // Validate returnPath is relative (prevents open redirect)
        if (str_starts_with($returnPath, 'http://') || str_starts_with($returnPath, 'https://')) {
            throw new InvalidArgumentException('Absolute URLs not allowed');
        }
        
        $encoded = rawurlencode($returnPath);
        
        return "/login?return=" . $encoded;
    }
}
```

The `rawurlencode()` function applies RFC 3986 percent-encoding, preventing URL injection through special characters. The absoluteness check prevents open redirect vulnerabilities where attackers craft return URLs pointing to phishing sites.

CSS context poses unique challenges because CSS allows JavaScript execution through `expression()` (Internet Explorer legacy) and `url()` data URIs. For user-supplied CSS values, strict whitelisting is the only safe approach:

```php
final class ThemeCustomizer {
    private const ALLOWED_COLORS = [
        'primary' => ['#007bff', '#0056b3', '#004085'],
        'danger' => ['#dc3545', '#c82333', '#bd2130'],
    ];
    
    public function applyColorTheme(string $theme, string $variant): string {
        $colors = self::ALLOWED_COLORS[$theme] ?? null;
        
        if ($colors === null || !in_array($variant, $colors, true)) {
            throw new InvalidArgumentException('Invalid theme configuration');
        }
        
        return "<style>:root { --theme-color: {$variant}; }</style>";
    }
}
```

Never allow users to inject arbitrary CSS. Even seemingly benign properties like `background-image` enable data exfiltration through URL tracking beacons.

### CSRF Protection Through Synchronizer Tokens

Cross-Site Request Forgery exploits ambient credentials—cookies sent automatically with every request—to execute unauthorized actions. An attacker embeds a malicious form on their site targeting the victim application:

```html
<!-- Attacker's site -->
<form action="https://bank.example.com/transfer" method="POST">
    <input type="hidden" name="to_account" value="attacker">
    <input type="hidden" name="amount" value="10000">
</form>
<script>document.forms[0].submit();</script>
```

When a victim authenticated to `bank.example.com` visits the attacker's page, their browser automatically includes session cookies with the POST request, causing the transfer to execute with the victim's authority.

The synchronizer token pattern defeats CSRF by embedding a cryptographic nonce in each form that attackers cannot forge due to same-origin policy. The token must be unpredictable, session-bound, and validated on every state-changing request:

```php
final class CsrfProtection {
    private const TOKEN_LENGTH = 32;
    private const TOKEN_LIFETIME = 3600; // 1 hour
    
    public function __construct(private SessionManager $session) {}
    
    public function generateToken(): string {
        $token = bin2hex(random_bytes(self::TOKEN_LENGTH));
        $expiry = time() + self::TOKEN_LIFETIME;
        
        $this->session->set('csrf_token', $token);
        $this->session->set('csrf_expiry', $expiry);
        
        return $token;
    }
    
    public function validateToken(string $token): bool {
        $expected = $this->session->get('csrf_token');
        $expiry = $this->session->get('csrf_expiry');
        
        if ($expected === null || $expiry === null) {
            return false;
        }
        
        if (time() > $expiry) {
            return false;
        }
        
        // Constant-time comparison prevents timing attacks
        return hash_equals($expected, $token);
    }
    
    public function requireValidToken(): void {
        $token = $_POST['csrf_token'] ?? '';
        
        if (!$this->validateToken($token)) {
            http_response_code(403);
            die('CSRF token validation failed');
        }
    }
}
```

The `random_bytes()` function sources entropy from the operating system's cryptographically secure random number generator (`/dev/urandom` on Unix, `CryptGenRandom` on Windows). The `hash_equals()` function performs constant-time string comparison, preventing attackers from inferring token values through timing side channels.

Forms include the token as a hidden field:

```php
final class TransferFormRenderer {
    public function __construct(
        private CsrfProtection $csrf,
        private HtmlEscaper $escaper
    ) {}
    
    public function render(): string {
        $token = $this->csrf->generateToken();
        $tokenEscaped = $this->escaper->escapeHtml($token);
        
        return <<<HTML
        <form method="POST" action="/transfer">
            <input type="hidden" name="csrf_token" value="{$tokenEscaped}">
            <input type="text" name="to_account" required>
            <input type="number" name="amount" required>
            <button type="submit">Transfer</button>
        </form>
        HTML;
    }
}
```

The form handler validates the token before processing:

```php
final class TransferController {
    public function __construct(
        private CsrfProtection $csrf,
        private BankingService $banking
    ) {}
    
    public function handleTransfer(): void {
        $this->csrf->requireValidToken();
        
        // Token validated - process transfer
        $toAccount = $_POST['to_account'] ?? '';
        $amount = filter_input(INPUT_POST, 'amount', FILTER_VALIDATE_INT);
        
        if ($amount === false || $amount <= 0) {
            http_response_code(400);
            die('Invalid amount');
        }
        
        $this->banking->transfer($toAccount, $amount);
        
        header('Location: /transfer/success');
    }
}
```

For AJAX applications, tokens can be embedded in a `<meta>` tag and read by JavaScript:

```php
echo '<meta name="csrf-token" content="' . $csrf->generateToken() . '">';
```

JavaScript reads the token and includes it in request headers:

```javascript
const token = document.querySelector('meta[name="csrf-token"]').content;

fetch('/api/transfer', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': token
    },
    body: JSON.stringify({ to_account: 'recipient', amount: 100 })
});
```

The server-side handler validates the header:

```php
final class ApiController {
    public function handleApiTransfer(): void {
        $token = $_SERVER['HTTP_X_CSRF_TOKEN'] ?? '';
        
        if (!$this->csrf->validateToken($token)) {
            http_response_code(403);
            echo json_encode(['error' => 'CSRF validation failed']);
            return;
        }
        
        // Process request
    }
}
```

### Session Management and Cookie Security

HTTP's statelessness requires explicit session state management through cookies containing session identifiers. Sessions map identifiers to server-side storage containing user authentication status, preferences, and transient data. The security of sessions depends entirely on protecting session identifiers from theft, fixation, and unauthorized access.

PHP's session management system provides built-in identifier generation, storage backends, and garbage collection. Secure session configuration requires explicit settings:

```php
final class SessionManager {
    public function start(): void {
        // Must be called before session_start()
        $this->configureSecureDefaults();
        
        session_start();
        
        // Regenerate ID on privilege elevation
        if (!isset($_SESSION['initiated'])) {
            session_regenerate_id(true);
            $_SESSION['initiated'] = true;
        }
    }
    
    private function configureSecureDefaults(): void {
        // Use cryptographically strong session IDs
        ini_set('session.sid_length', '48');
        ini_set('session.sid_bits_per_character', '6');
        
        // Prevent JavaScript access to session cookie (XSS mitigation)
        ini_set('session.cookie_httponly', '1');
        
        // Require HTTPS for session cookies (prevents sniffing)
        ini_set('session.cookie_secure', '1');
        
        // Strict same-site policy (CSRF mitigation)
        ini_set('session.cookie_samesite', 'Strict');
        
        // Limit session lifetime
        ini_set('session.gc_maxlifetime', '3600');
        ini_set('session.cookie_lifetime', '0'); // Expire on browser close
        
        // Use file-based storage with restricted permissions
        $sessionPath = '/var/lib/php/sessions';
        if (!is_dir($sessionPath)) {
            mkdir($sessionPath, 0700, true);
        }
        ini_set('session.save_path', $sessionPath);
        
        // Prevent session fixation through URL rewriting
        ini_set('session.use_only_cookies', '1');
        ini_set('session.use_strict_mode', '1');
    }
    
    public function set(string $key, mixed $value): void {
        $_SESSION[$key] = $value;
    }
    
    public function get(string $key): mixed {
        return $_SESSION[$key] ?? null;
    }
    
    public function destroy(): void {
        $_SESSION = [];
        
        if (isset($_COOKIE[session_name()])) {
            setcookie(
                session_name(),
                '',
                time() - 3600,
                '/',
                '',
                true,  // secure
                true   // httponly
            );
        }
        
        session_destroy();
    }
    
    public function regenerateId(): void {
        session_regenerate_id(true);
    }
}
```

The `cookie_httponly` flag prevents JavaScript from accessing the session cookie through `document.cookie`, mitigating XSS-based session theft. The `cookie_secure` flag restricts cookie transmission to HTTPS connections, preventing network sniffing. The `cookie_samesite` attribute prevents browsers from sending cookies with cross-origin requests, providing defense-in-depth against CSRF beyond token validation.

Session fixation attacks occur when attackers preset a victim's session ID before authentication, then hijack the session after login. Calling `session_regenerate_id()` after privilege elevation (login, role change) invalidates the old ID and issues a new one, breaking the fixation attack:

```php
final class LoginController {
    public function __construct(
        private SessionManager $session,
        private AuthService $auth
    ) {}
    
    public function handleLogin(): void {
        $username = $_POST['username'] ?? '';
        $password = $_POST['password'] ?? '';
        
        $userId = $this->auth->authenticate($username, $password);
        
        if ($userId === null) {
            http_response_code(401);
            echo 'Invalid credentials';
            return;
        }
        
        // Critical: Regenerate session ID after authentication
        $this->session->regenerateId();
        
        $this->session->set('user_id', $userId);
        $this->session->set('authenticated', true);
        $this->session->set('login_time', time());
        
        header('Location: /dashboard');
    }
}
```

For distributed applications running across multiple servers, file-based session storage fails due to lack of shared filesystem. Redis or Memcached provide centralized session stores with automatic expiration:

```php
final class RedisSessionHandler implements SessionHandlerInterface {
    private Redis $redis;
    private int $ttl;
    
    public function __construct(string $host, int $port, int $ttl = 3600) {
        $this->redis = new Redis();
        $this->redis->connect($host, $port);
        $this->ttl = $ttl;
    }
    
    public function open(string $path, string $name): bool {
        return true;
    }
    
    public function close(): bool {
        return true;
    }
    
    public function read(string $id): string|false {
        $data = $this->redis->get("session:{$id}");
        return $data === false ? '' : $data;
    }
    
    public function write(string $id, string $data): bool {
        return $this->redis->setex("session:{$id}", $this->ttl, $data);
    }
    
    public function destroy(string $id): bool {
        $this->redis->del("session:{$id}");
        return true;
    }
    
    public function gc(int $max_lifetime): int|false {
        // Redis handles expiration automatically
        return 0;
    }
}

// Register custom handler
$handler = new RedisSessionHandler('localhost', 6379);
session_set_save_handler($handler, true);
```

The `SessionHandlerInterface` implementation replaces PHP's default file-based storage with Redis, enabling session sharing across application servers behind a load balancer. The `setex` command atomically sets both value and expiration, ensuring sessions expire even if garbage collection never runs.

### Password Hashing and Credential Storage

Storing passwords in plaintext or reversibly encrypted form violates the fundamental principle that **authentication secrets must be cryptographically irretrievable**. Password hashing applies one-way functions with computational cost tuning, making brute-force attacks infeasible even after database compromise. PHP's `password_hash()` function implements bcrypt and Argon2 with automatic salt generation and secure defaults:

```php
final class PasswordHasher {
    public function hash(string $password): string {
        // Use Argon2id (PHP 7.3+) for maximum resistance to GPU/ASIC attacks
        return password_hash($password, PASSWORD_ARGON2ID, [
            'memory_cost' => 65536,  // 64 MB
            'time_cost' => 4,        // 4 iterations
            'threads' => 2           // 2 parallel threads
        ]);
    }
    
    public function verify(string $password, string $hash): bool {
        return password_verify($password, $hash);
    }
    
    public function needsRehash(string $hash): bool {
        return password_needs_rehash($hash, PASSWORD_ARGON2ID, [
            'memory_cost' => 65536,
            'time_cost' => 4,
            'threads' => 2
        ]);
    }
}
```

Argon2id combines Argon2i's resistance to side-channel attacks with Argon2d's resistance to GPU-based cracking. The memory cost forces attackers to allocate significant RAM per hash attempt, making parallel GPU attacks economically infeasible. The time cost parameter tunes iteration count, trading authentication latency for security. A properly tuned hash should take 250-500ms to compute on the target hardware.

The verification function executes in constant time regardless of password correctness, preventing timing attacks that leak information about password similarity:

```php
final class AuthService {
    public function __construct(
        private PDO $db,
        private PasswordHasher $hasher
    ) {}
    
    public function authenticate(string $username, string $password): ?int {
        $stmt = $this->db->prepare(
            'SELECT id, password_hash FROM users WHERE username = :username'
        );
        $stmt->execute(['username' => $username]);
        
        $user = $stmt->fetch(PDO::FETCH_ASSOC);
        
        if ($user === false) {
            // Perform dummy verification to maintain constant time
            $this->hasher->verify($password, '$argon2id$v=19$m=65536,t=4,p=2$ZHVtbXkAAAAAAAAAAAAAAA$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA');
            return null;
        }
        
        if (!$this->hasher->verify($password, $user['password_hash'])) {
            return null;
        }
        
        // Check if hash needs upgrading (cost parameters changed)
        if ($this->hasher->needsRehash($user['password_hash'])) {
            $newHash = $this->hasher->hash($password);
            $this->updatePasswordHash($user['id'], $newHash);
        }
        
        return (int)$user['id'];
    }
    
    private function updatePasswordHash(int $userId, string $newHash): void {
        $stmt = $this->db->prepare('UPDATE users SET password_hash = :hash WHERE id = :id');
        $stmt->execute(['hash' => $newHash, 'id' => $userId]);
    }
}
```

The dummy verification for nonexistent users ensures authentication timing remains constant regardless of username validity, preventing enumeration attacks that distinguish valid from invalid usernames through response time analysis.

### Modern Type System: Declarations, Union Types, and Strictness

PHP's gradual typing system allows incremental adoption of static type constraints without breaking dynamic code. Type declarations exist at multiple levels: parameter types, return types, property types, and—since PHP 8.0—union types combining multiple possibilities. The `declare(strict_types=1)` directive enables strict type checking within a file, rejecting implicit coercions that historically enabled type-juggling vulnerabilities:

```php
declare(strict_types=1);

final class UserRepository {
    public function __construct(private PDO $db) {}
    
    public function findById(int $userId): ?User {
        $stmt = $this->db->prepare('SELECT * FROM users WHERE id = :id');
        $stmt->execute(['id' => $userId]);
        
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        
        if ($row === false) {
            return null;
        }
        
        return User::fromArray($row);
    }
    
    public function findByEmail(string $email): ?User {
        $stmt = $this->db->prepare('SELECT * FROM users WHERE email = :email');
        $stmt->execute(['email' => $email]);
        
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        
        return $row !== false ? User::fromArray($row) : null;
    }
}
```

Without strict types, calling `findById('42')` with a string would silently coerce to integer. With strict types, PHP throws a `TypeError`, forcing explicit validation at API boundaries. This eliminates classes of vulnerabilities where type juggling causes unexpected equality: `'0e123' == '0e456'` evaluates true because both parse as scientific notation zero.

Union types (PHP 8.0+) express parameters or returns accepting multiple distinct types:

```php
final class ConfigLoader {
    /**
     * Load configuration from file or array
     * 
     * @param string|array<string, mixed> $source
     * @return array<string, mixed>
     */
    public function load(string|array $source): array {
        if (is_string($source)) {
            if (!file_exists($source)) {
                throw new InvalidArgumentException("Config file not found: {$source}");
            }
            return require $source;
        }
        
        return $source;
    }
}
```

The `string|array` union allows callers to pass either a file path or an inline configuration array, with runtime dispatch determining the code path. Intersection types (PHP 8.1+) express constraints requiring multiple type contracts simultaneously:

```php
interface Loggable {
    public function getLogContext(): array;
}

interface Cacheable {
    public function getCacheKey(): string;
}

final class CachedLogger {
    public function logCacheableEvent(Loggable&Cacheable $event): void {
        $key = $event->getCacheKey();
        $context = $event->getLogContext();
        
        // Implementation
    }
}
```

The `Loggable&Cacheable` intersection requires implementors to satisfy both interfaces, enabling the method to safely call methods from each without instanceof checks.

Readonly properties (PHP 8.1+) prevent modification after initialization, creating immutable value objects:

```php
final class UserId {
    public function __construct(
        public readonly int $value
    ) {
        if ($value < 1) {
            throw new InvalidArgumentException('User ID must be positive');
        }
    }
}

final class User {
    public function __construct(
        public readonly UserId $id,
        public readonly string $email,
        public readonly \DateTimeImmutable $createdAt
    ) {}
}
```

Attempting to modify `$user->id` after construction throws an error. This immutability eliminates temporal coupling bugs where object state changes unexpectedly, and prevents accidental mutation in multithreaded contexts.

### Enums for Type-Safe State Machines

Enumerations (PHP 8.1+) define closed sets of related constants with exhaustiveness checking. Unlike class constants, enums integrate with match expressions and type hints, enabling compile-time validation of state machine transitions:

```php
enum OrderStatus: string {
    case Pending = 'pending';
    case Processing = 'processing';
    case Shipped = 'shipped';
    case Delivered = 'delivered';
    case Cancelled = 'cancelled';
    
    public function canTransitionTo(OrderStatus $target): bool {
        return match ($this) {
            self::Pending => $target === self::Processing || $target === self::Cancelled,
            self::Processing => $target === self::Shipped || $target === self::Cancelled,
            self::Shipped => $target === self::Delivered,
            self::Delivered => false,
            self::Cancelled => false,
        };
    }
    
    public function getLabel(): string {
        return match ($this) {
            self::Pending => 'Awaiting Processing',
            self::Processing => 'In Progress',
            self::Shipped => 'In Transit',
            self::Delivered => 'Completed',
            self::Cancelled => 'Cancelled',
        };
    }
}

final class Order {
    public function __construct(
        public readonly int $id,
        private OrderStatus $status
    ) {}
    
    public function getStatus(): OrderStatus {
        return $this->status;
    }
    
    public function transitionTo(OrderStatus $newStatus): void {
        if (!$this->status->canTransitionTo($newStatus)) {
            throw new InvalidStateTransitionException(
                "Cannot transition from {$this->status->value} to {$newStatus->value}"
            );
        }
        
        $this->status = $newStatus;
    }
}
```

The backed enum (`string` type) allows database storage while maintaining type safety. The `canTransitionTo()` method encodes state machine rules directly in the enum, centralizing validation logic. The match expression enforces exhaustiveness—adding a new status without updating the match arms triggers a runtime error.

Usage demonstrates clarity improvements over string constants:

```php
$order = new Order(123, OrderStatus::Pending);

// Type-safe: IDE autocompletes valid statuses
$order->transitionTo(OrderStatus::Processing);

// Compile-time error: Cannot pass string
// $order->transitionTo('invalid');

// Runtime validation catches invalid transitions
try {
    $order->transitionTo(OrderStatus::Delivered); // Skip shipped state
} catch (InvalidStateTransitionException $e) {
    echo $e->getMessage();
}
```

### Attributes for Metadata-Driven Validation

Attributes (PHP 8.0+) attach structured metadata to classes, methods, properties, and parameters, enabling reflection-based frameworks to implement declarative validation, routing, and access control without docblock parsing:

```php
#[Attribute(Attribute::TARGET_PROPERTY)]
final class Validate {
    public function __construct(
        public readonly string $rule,
        public readonly array $parameters = []
    ) {}
}

#[Attribute(Attribute::TARGET_PROPERTY)]
final class Sanitize {
    public function __construct(
        public readonly string $filter
    ) {}
}

final class UserRegistrationDto {
    public function __construct(
        #[Validate('required')]
        #[Validate('email')]
        #[Sanitize('trim')]
        public readonly string $email,
        
        #[Validate('required')]
        #[Validate('min', ['length' => 12])]
        public readonly string $password,
        
        #[Validate('required')]
        #[Validate('min', ['length' => 2])]
        #[Validate('max', ['length' => 50])]
        #[Sanitize('trim')]
        public readonly string $name
    ) {}
}
```

A validation engine reflects over attributes to apply rules:

```php
final class AttributeValidator {
    public function validate(object $dto): array {
        $errors = [];
        $reflection = new \ReflectionClass($dto);
        
        foreach ($reflection->getProperties() as $property) {
            $propertyName = $property->getName();
            $value = $property->getValue($dto);
            
            // Apply sanitization first
            foreach ($property->getAttributes(Sanitize::class) as $attr) {
                $sanitize = $attr->newInstance();
                $value = $this->applySanitization($value, $sanitize->filter);
            }
            
            // Apply validation rules
            foreach ($property->getAttributes(Validate::class) as $attr) {
                $validate = $attr->newInstance();
                $result = $this->applyValidation($value, $validate->rule, $validate->parameters);
                
                if ($result !== true) {
                    $errors[$propertyName][] = $result;
                }
            }
        }
        
        return $errors;
    }
    
    private function applySanitization(mixed $value, string $filter): mixed {
        return match ($filter) {
            'trim' => is_string($value) ? trim($value) : $value,
            default => $value
        };
    }
    
    private function applyValidation(mixed $value, string $rule, array $params): string|true {
        return match ($rule) {
            'required' => $value !== null && $value !== '' ? true : 'Field is required',
            'email' => filter_var($value, FILTER_VALIDATE_EMAIL) !== false ? true : 'Invalid email',
            'min' => strlen($value) >= $params['length'] ? true : "Minimum length: {$params['length']}",
            'max' => strlen($value) <= $params['length'] ? true : "Maximum length: {$params['length']}",
            default => true
        };
    }
}
```

Controllers instantiate DTOs and validate declaratively:

```php
final class RegistrationController {
    public function __construct(
        private AttributeValidator $validator,
        private UserService $userService
    ) {}
    
    public function handleRegistration(): void {
        $dto = new UserRegistrationDto(
            email: $_POST['email'] ?? '',
            password: $_POST['password'] ?? '',
            name: $_POST['name'] ?? ''
        );
        
        $errors = $this->validator->validate($dto);
        
        if (!empty($errors)) {
            http_response_code(422);
            echo json_encode(['errors' => $errors]);
            return;
        }
        
        $this->userService->register($dto);
        
        http_response_code(201);
        echo json_encode(['message' => 'Registration successful']);
    }
}
```

This approach centralizes validation logic in DTO definitions, making security boundaries explicit and mechanically verifiable.

### Fibers for Cooperative Concurrency

Fibers (PHP 8.1+) implement userspace green threads, enabling cooperative multitasking within a single OS thread. Unlike traditional callback-based async programming, fibers preserve linear control flow, making asynchronous code resemble synchronous code while achieving high concurrency:

```php
final class HttpClient {
    public function fetchUrl(string $url): string {
        $fiber = new Fiber(function () use ($url): string {
            $context = stream_context_create([
                'http' => ['timeout' => 5]
            ]);
            
            $content = file_get_contents($url, false, $context);
            
            if ($content === false) {
                throw new RuntimeException("Failed to fetch {$url}");
            }
            
            return $content;
        });
        
        $fiber->start();
        
        return $fiber->getReturn();
    }
}
```

Fibers become powerful when combined with event loops that schedule fiber execution based on I/O readiness:

```php
final class FiberScheduler {
    private array $fibers = [];
    
    public function schedule(Fiber $fiber): void {
        $this->fibers[] = $fiber;
    }
    
    public function run(): void {
        while (!empty($this->fibers)) {
            foreach ($this->fibers as $key => $fiber) {
                if (!$fiber->isStarted()) {
                    $fiber->start();
                } elseif ($fiber->isSuspended()) {
                    $fiber->resume();
                }
                
                if ($fiber->isTerminated()) {
                    unset($this->fibers[$key]);
                }
            }
        }
    }
}

// Example: Concurrent HTTP fetches
$scheduler = new FiberScheduler();

$urls = ['https://example.com', 'https://example.org', 'https://example.net'];

foreach ($urls as $url) {
    $fiber = new Fiber(function () use ($url): void {
        $content = file_get_contents($url);
        echo "Fetched {$url}: " . strlen($content) . " bytes\n";
    });
    
    $scheduler->schedule($fiber);
}

$scheduler->run();
```

Production fiber implementations integrate with native async I/O through libuv or extensions like `ext-event`, suspending fibers during I/O waits and resuming when data becomes available. This approach saturates network bandwidth without thread overhead, making PHP competitive with Node.js and Go for I/O-bound workloads.

### JIT Compilation Architecture

The Just-In-Time compiler (PHP 8.0+) translates opcodes into native machine code at runtime, eliminating interpreter overhead for CPU-intensive workloads. PHP's JIT builds on the existing opcache infrastructure, which compiles scripts into an intermediate opcode representation stored in shared memory. The JIT operates as an additional compilation stage, identifying hot code paths through tracing and generating platform-specific assembly.

The compilation pipeline proceeds as follows:

1. **Script parsing**: Zend Engine parses PHP source into abstract syntax trees (AST)
2. **Opcode generation**: AST compiles into stack-based bytecode (ZEND_VM opcodes)
3. **Opcache storage**: Opcodes cached in shared memory, bypassing parse/compile on subsequent requests
4. **JIT tracing**: Runtime profiler identifies frequently executed opcode sequences
5. **Code generation**: DynASM assembler generates x86-64, ARM64, or other architecture machine code
6. **Linking and execution**: JIT code replaces interpreted opcodes, executing directly on CPU

The JIT operates in several modes configured via `opcache.jit` INI setting:

- **disabled (0)**: No JIT compilation
- **tracing (1255)**: Trace hot loops and compile entire execution traces
- **function (1205)**: Compile entire functions exceeding hotness threshold
- **on (tracing)**: Default tracing mode with balanced compilation strategy

A cryptographic hashing benchmark demonstrates JIT benefits:

```php
// Compute SHA-256 hashes in tight loop
function benchmarkHashing(int $iterations): void {
    $data = random_bytes(1024);
    
    $start = hrtime(true);
    
    for ($i = 0; $i < $iterations; $i++) {
        hash('sha256', $data);
    }
    
    $elapsed = (hrtime(true) - $start) / 1e9;
    
    echo "Hashed {$iterations} times in {$elapsed} seconds\n";
    echo "Rate: " . ($iterations / $elapsed) . " hashes/sec\n";
}

benchmarkHashing(100000);
```

With JIT disabled, the interpreter executes approximately 50,000 hashes per second. With JIT enabled (tracing mode), throughput increases to 75,000+ hashes per second—a 50% improvement. The JIT eliminates opcode dispatch overhead and specializes type checks based on runtime observations.

The performance gain varies dramatically by workload. I/O-bound web applications see negligible benefit because execution time dominates in database queries, filesystem access, and network I/O—operations the JIT cannot accelerate. CPU-intensive tasks like image processing, data serialization, and mathematical computations gain significantly.

JIT compilation incurs warmup overhead—initial requests compile code and accumulate profiling data before optimized paths execute. For short-running CLI scripts, JIT may degrade performance. For long-running application servers handling thousands of requests, amortized gains exceed warmup costs.

The JIT integrates with opcache's huge pages support, allocating JIT code buffers in transparent huge pages (2 MB on x86-64) to reduce TLB misses. Combined with CPU cache-aware opcode layout, this maximizes instruction throughput for hot code.

## 3. High-Performance Optimization & Failure Modes

### Input Validation Performance Patterns

Validation overhead compounds with request complexity—deeply nested JSON payloads or large file uploads can exhaust CPU and memory budgets before reaching business logic. Efficient validation employs early rejection patterns, validating structural constraints before semantic rules:

```php
final class OptimizedJsonValidator {
    private const MAX_DEPTH = 10;
    private const MAX_SIZE = 1048576; // 1 MB
    
    public function validate(string $json): array {
        // Reject oversized payloads immediately
        if (strlen($json) > self::MAX_SIZE) {
            throw new ValidationException('Payload exceeds maximum size');
        }
        
        // Decode with depth limit to prevent stack exhaustion
        $data = json_decode($json, true, self::MAX_DEPTH, JSON_THROW_ON_ERROR);
        
        // Validate structure before semantic rules
        return $this->validateStructure($data);
    }
    
    private function validateStructure(mixed $data): array {
        if (!is_array($data)) {
            throw new ValidationException('Expected JSON object');
        }
        
        // Fail fast on missing required fields
        $required = ['user_id', 'action', 'timestamp'];
        foreach ($required as $field) {
            if (!array_key_exists($field, $data)) {
                throw new ValidationException("Missing required field: {$field}");
            }
        }
        
        return $data;
    }
}
```

The size check prevents memory exhaustion from oversized JSON documents. The depth limit prevents stack overflow from deeply nested structures. Structural validation precedes expensive semantic checks like database lookups or API calls.

For bulk operations, batch validation amortizes overhead:

```php
final class BulkValidator {
    public function validateBatch(array $items, callable $validator): array {
        $errors = [];
        
        foreach ($items as $index => $item) {
            try {
                $validator($item);
            } catch (ValidationException $e) {
                $errors[$index] = $e->getMessage();
            }
        }
        
        return $errors;
    }
}
```

Returning all errors in one pass eliminates roundtrip latency for large imports.

### Prepared Statement Caching and Connection Pooling

Each prepared statement imposes parsing and planning overhead on the database server. Statement caching reuses prepared statements across requests:

```php
final class CachedPdoWrapper {
    private PDO $pdo;
    private array $statementCache = [];
    
    public function __construct(PDO $pdo) {
        $this->pdo = $pdo;
        $this->pdo->setAttribute(PDO::ATTR_EMULATE_PREPARES, false);
    }
    
    public function prepare(string $sql): PDOStatement {
        $key = md5($sql);
        
        if (!isset($this->statementCache[$key])) {
            $this->statementCache[$key] = $this->pdo->prepare($sql);
        }
        
        return $this->statementCache[$key];
    }
    
    public function execute(string $sql, array $params): PDOStatement {
        $stmt = $this->prepare($sql);
        $stmt->execute($params);
        return $stmt;
    }
}
```

This pattern works within a single request. For persistent connections (PHP-FPM with pm.max_requests > 1), statement cache persists across requests, eliminating repeated preparation.

Connection pooling through PgBouncer (PostgreSQL) or ProxySQL (MySQL) reduces connection establishment overhead:

```php
final class PooledDatabaseFactory {
    public static function create(): PDO {
        // Connect to pooler instead of database directly
        $dsn = 'pgsql:host=pgbouncer;port=6432;dbname=app';
        
        $pdo = new PDO($dsn, 'app_user', 'password', [
            PDO::ATTR_PERSISTENT => true,
            PDO::ATTR_EMULATE_PREPARES => false,
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
        ]);
        
        return $pdo;
    }
}
```

The pooler maintains hot connections to backend databases, assigning them to PHP workers on demand and recycling connections after request completion. This eliminates TCP handshake and authentication overhead.

### Session Storage Scalability

File-based session storage limits horizontal scaling because PHP workers on different servers cannot share filesystem sessions. Redis provides distributed session storage with automatic expiration:

```php
final class RedisSessionFactory {
    public static function configure(string $host = 'localhost', int $port = 6379): void {
        ini_set('session.save_handler', 'redis');
        ini_set('session.save_path', "tcp://{$host}:{$port}?timeout=2&database=1");
    }
}
```

For high-traffic applications, Redis clustering with hash-slot sharding distributes session load across multiple nodes. The Predis library provides cluster-aware client:

```php
use Predis\Client;

$redis = new Client([
    'tcp://redis-node1:6379',
    'tcp://redis-node2:6379',
    'tcp://redis-node3:6379'
], ['cluster' => 'redis']);
```

Redis Cluster automatically partitions session data by key hash, balancing load and providing failover through replica promotion.

Session data size directly impacts latency—large session arrays incur serialization overhead on every request. Minimize session storage by caching computed values externally:

```php
// WRONG: Store entire user object in session
$_SESSION['user'] = $userRepository->findById($userId);

// RIGHT: Store only user ID, fetch on demand
$_SESSION['user_id'] = $userId;

// Lazy load user when needed
function getCurrentUser(SessionManager $session, UserRepository $repo): User {
    static $user = null;
    
    if ($user === null) {
        $userId = $session->get('user_id');
        $user = $repo->findById($userId);
    }
    
    return $user;
}
```

This pattern reduces session size from kilobytes to tens of bytes, decreasing Redis network transfer and deserialization overhead.

### Output Escaping Performance and Caching

Escaping every string on every request wastes CPU. Template caching compiles templates with embedded escaping into PHP opcodes:

```php
final class CachedTemplateEngine {
    private string $cacheDir;
    
    public function __construct(string $cacheDir) {
        $this->cacheDir = $cacheDir;
    }
    
    public function render(string $template, array $data): string {
        $cacheFile = $this->cacheDir . '/' . md5($template) . '.php';
        
        if (!file_exists($cacheFile)) {
            $compiled = $this->compile($template);
            file_put_contents($cacheFile, $compiled);
        }
        
        extract($data, EXTR_SKIP);
        ob_start();
        require $cacheFile;
        return ob_get_clean();
    }
    
    private function compile(string $template): string {
        // Replace {{ variable }} with escaped output
        $compiled = preg_replace_callback(
            '/\{\{\s*(\$\w+)\s*\}\}/',
            fn($matches) => '<?= htmlspecialchars(' . $matches[1] . ', ENT_QUOTES | ENT_HTML5, "UTF-8") ?>',
            $template
        );
        
        return $compiled;
    }
}
```

The compiled template executes as native PHP with opcache acceleration, eliminating parsing and escaping overhead after initial compilation.

For API responses, JSON escaping through `json_encode()` benefits from native C implementation. Enable optimization flags:

```php
final class JsonResponseRenderer {
    public function render(array $data): string {
        return json_encode($data, 
            JSON_HEX_TAG | JSON_HEX_AMP | 
            JSON_UNESCAPED_SLASHES | 
            JSON_THROW_ON_ERROR
        );
    }
}
```

The `JSON_UNESCAPED_SLASHES` flag reduces output size by preventing forward-slash escaping. `JSON_THROW_ON_ERROR` converts warnings to exceptions, enabling proper error handling.

### CSRF Token Performance and Rotation

Generating cryptographic tokens on every form render imposes overhead. Token rotation balances security and performance:

```php
final class OptimizedCsrfProtection {
    private const TOKEN_LIFETIME = 3600;
    private const ROTATION_WINDOW = 600;
    
    public function __construct(private SessionManager $session) {}
    
    public function getToken(): string {
        $token = $this->session->get('csrf_token');
        $generated = $this->session->get('csrf_generated');
        
        $now = time();
        
        // Generate new token if none exists or expired
        if ($token === null || $generated === null || 
            ($now - $generated) > self::TOKEN_LIFETIME) {
            $token = $this->generateToken();
            $this->session->set('csrf_token', $token);
            $this->session->set('csrf_generated', $now);
        }
        
        return $token;
    }
    
    public function validateToken(string $token): bool {
        $expected = $this->session->get('csrf_token');
        $generated = $this->session->get('csrf_generated');
        
        if ($expected === null || $generated === null) {
            return false;
        }
        
        // Accept tokens within lifetime + rotation window
        $age = time() - $generated;
        if ($age > self::TOKEN_LIFETIME + self::ROTATION_WINDOW) {
            return false;
        }
        
        return hash_equals($expected, $token);
    }
    
    private function generateToken(): string {
        return bin2hex(random_bytes(32));
    }
}
```

The rotation window allows concurrent form submissions using slightly stale tokens, preventing race conditions where token regeneration invalidates in-flight requests.

For single-page applications with long-lived sessions, refresh tokens in background:

```javascript
// Fetch new token every 5 minutes
setInterval(async () => {
    const response = await fetch('/api/csrf-token');
    const { token } = await response.json();
    document.querySelector('meta[name="csrf-token"]').content = token;
}, 300000);
```

### Password Hashing Cost Tuning

Argon2 cost parameters directly trade security for latency. Measure actual hash time on production hardware:

```php
final class PasswordHashBenchmark {
    public function benchmark(int $memoryCost, int $timeCost): void {
        $password = 'test_password_123';
        
        $start = hrtime(true);
        
        password_hash($password, PASSWORD_ARGON2ID, [
            'memory_cost' => $memoryCost,
            'time_cost' => $timeCost,
            'threads' => 2
        ]);
        
        $elapsed = (hrtime(true) - $start) / 1e9;
        
        echo "Memory: {$memoryCost} KB, Time: {$timeCost}, Duration: {$elapsed} sec\n";
    }
}

$benchmark = new PasswordHashBenchmark();

// Test various cost parameters
$benchmark->benchmark(32768, 2);  // ~100ms
$benchmark->benchmark(65536, 4);  // ~400ms
$benchmark->benchmark(131072, 6); // ~1200ms
```

Target 250-500ms hash time—long enough to deter brute force but short enough to avoid user-facing latency. Lower costs for high-traffic authentication, higher costs for infrequent administrative actions.

### Type System Overhead and Optimization

Type declarations impose runtime checks on every function call. Strict types eliminate redundant validation:

```php
// REDUNDANT: Type already enforced
function processUserId(int $userId): void {
    if (!is_int($userId)) {  // Never true with strict types
        throw new InvalidArgumentException();
    }
    
    // ...
}

// OPTIMIZED: Trust type system
function processUserId(int $userId): void {
    // $userId guaranteed integer by type declaration
}
```

Union types incur dispatch overhead for type-specific logic. Minimize union complexity:

```php
// SLOW: Many possible types
function process(int|float|string|array|object $value): void {
    if (is_int($value)) { /* ... */ }
    elseif (is_float($value)) { /* ... */ }
    // ...
}

// FAST: Single type
function processInt(int $value): void {
    // Single code path
}
```

Prefer specific functions over unions when possible.

### Fiber Scheduling Overhead

Fiber context switches impose overhead—excessive fiber creation degrades performance:

```php
// WRONG: Create fiber per item
foreach ($urls as $url) {
    $fiber = new Fiber(fn() => fetchUrl($url));
    $fiber->start();
}

// RIGHT: Batch items per fiber
$batches = array_chunk($urls, 100);
foreach ($batches as $batch) {
    $fiber = new Fiber(function () use ($batch) {
        foreach ($batch as $url) {
            fetchUrl($url);
        }
    });
    $fiber->start();
}
```

Batching reduces fiber overhead while maintaining concurrency.

### JIT Compilation Pitfalls

The JIT optimizes based on runtime observations—polymorphic code resists optimization:

```php
// HARD TO OPTIMIZE: Return type varies
function getValue($input) {
    return is_string($input) ? strtoupper($input) : $input * 2;
}

// EASIER TO OPTIMIZE: Monomorphic types
function processString(string $input): string {
    return strtoupper($input);
}

function processInt(int $input): int {
    return $input * 2;
}
```

Type-specialized functions enable aggressive JIT optimization through invariant folding and dead code elimination. Polymorphic functions force runtime type checks on every invocation.

### Failure Mode: Timing Side Channels

Authentication systems leak information through response timing. Constant-time comparison prevents timing attacks:

```php
// VULNERABLE: Early exit on mismatch
function compareTokens(string $a, string $b): bool {
    if (strlen($a) !== strlen($b)) {
        return false;
    }
    
    for ($i = 0; $i < strlen($a); $i++) {
        if ($a[$i] !== $b[$i]) {
            return false;  // Early exit leaks position
        }
    }
    
    return true;
}

// SECURE: Constant-time comparison
function compareTokensSecure(string $a, string $b): bool {
    return hash_equals($a, $b);
}
```

The `hash_equals()` function compares entire strings regardless of mismatch position, preventing attackers from inferring correct bytes through timing analysis.

### Failure Mode: Session Fixation Through Subdomain Cookies

Cookies without explicit domain restrictions span all subdomains, enabling cross-subdomain session fixation:

```php
// VULNERABLE: Cookie accessible to attacker-controlled subdomain
session_set_cookie_params([
    'lifetime' => 0,
    'path' => '/',
    'domain' => '.example.com',  // Allows evil.example.com access
    'secure' => true,
    'httponly' => true,
    'samesite' => 'Strict'
]);

// SECURE: Restrict to specific subdomain
session_set_cookie_params([
    'lifetime' => 0,
    'path' => '/',
    'domain' => 'app.example.com',  // Explicit subdomain
    'secure' => true,
    'httponly' => true,
    'samesite' => 'Strict'
]);
```

Explicit subdomain specification prevents lateral session theft across organizational boundaries.

### Failure Mode: TOCTOU Races in Validation

Time-of-check-to-time-of-use races occur when validation and usage span separate operations:

```php
// VULNERABLE: File contents can change between check and use
if (file_exists($uploadPath) && filesize($uploadPath) < 1048576) {
    $contents = file_get_contents($uploadPath);  // TOCTOU race
}

// SECURE: Single atomic operation
$contents = file_get_contents($uploadPath);
if ($contents !== false && strlen($contents) < 1048576) {
    // Use $contents
}
```

Atomic operations eliminate race windows where attacker-controlled processes modify filesystem state.

Modern PHP security rests on defense-in-depth layering—input validation gates, parameterized queries, output escaping, cryptographic sessions, and type-safe enforcement. Each primitive addresses specific attack vectors while composing into holistic application security. The type system, enums, attributes, and fibers extend these primitives into language-level contracts, making secure patterns mechanically checkable and violations detectable at compile time rather than in production.
