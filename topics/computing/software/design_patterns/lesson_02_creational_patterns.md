# Lesson 2: Creational Patterns

## 1. First-Principles Intuition & Invariants

The act of instantiating objects sits at the heart of object-oriented programming, yet it introduces coupling that undermines modularity and testability. When a class directly invokes `new ConcreteType()`, it binds itself to a specific implementation, making the codebase rigid and resistant to change. Creational patterns address this fundamental tension by decoupling the interface of object creation from the mechanics of instantiation, allowing systems to remain flexible as requirements evolve.

At their core, creational patterns recognize that object construction is not merely allocation followed by initialization—it encompasses decisions about which concrete type to instantiate, how to configure that instance, and when to reuse existing instances versus creating new ones. These patterns codify strategies for managing these decisions, transforming construction from a scattered set of `new` invocations into intentional, centralized policies. The patterns we examine here—Singleton, Factory Method, Abstract Factory, Builder, and Prototype—each tackle different facets of this problem space, and understanding their mechanical differences reveals when each pattern provides genuine value versus when it introduces unnecessary indirection.

The Singleton pattern enforces a global invariant: exactly one instance of a class exists within a process address space. This constraint proves essential for resources that must maintain singular authority—logging subsystems that serialize output to a single file descriptor, configuration registries that prevent conflicting settings, or connection pools that coordinate access to a fixed set of database handles. The pattern's power lies not in restricting instantiation arbitrarily, but in providing a controlled access point that guarantees consistency when multiple subsystems interact with shared state.

Factory patterns—both Method and Abstract—shift the instantiation decision from compile time to runtime by introducing polymorphic factory interfaces. The Factory Method pattern embeds this decision within subclass hierarchies, allowing derived classes to specify which concrete product types they instantiate. This proves particularly powerful in frameworks where the framework code defines the overall algorithm structure but delegates product creation to application-specific subclasses. The Abstract Factory extends this concept to families of related objects, ensuring that products created together maintain coherent relationships—critical when building cross-platform UI toolkits or database access layers that must coordinate drivers, connection objects, and command builders.

The Builder pattern tackles a different problem: constructing complex objects through incremental assembly rather than monolithic constructors. When an object requires numerous configuration parameters—many of them optional—traditional constructors degenerate into telescoping parameter lists that obscure intent and invite errors. Builders decompose construction into discrete steps, each named method setting a specific aspect of the final product. This pattern shines when creating immutable objects that require validation across multiple fields, or when the construction process itself contains conditional logic that varies based on configuration.

Finally, the Prototype pattern acknowledges that cloning existing instances often proves simpler and more efficient than constructing new ones from scratch, especially when initialization involves expensive operations like loading resources or establishing network connections. By defining a `clone()` operation, the pattern enables object creation through copying, delegating the mechanics of duplication to the object itself. This proves invaluable in scenarios where the exact concrete type remains unknown at compile time, or when maintaining a registry of configurable templates that users can duplicate and modify.

Each pattern encodes specific invariants about object lifecycle and coupling. Singleton guarantees uniqueness within a scope. Factory Method guarantees that subclasses control product instantiation. Abstract Factory guarantees family consistency. Builder guarantees incremental construction with validation. Prototype guarantees cloneability. Recognizing these invariants allows engineers to select patterns based on the constraints their systems must uphold, rather than applying patterns dogmatically.

## 2. Core Architecture & Mechanics

### Singleton: Thread-Safe Lazy Initialization

The naive Singleton implementation—a static instance variable initialized on first access—immediately encounters race conditions in multithreaded environments. Two threads invoking `getInstance()` simultaneously may both observe the instance as null and each construct a separate object, violating the uniqueness invariant. Modern Singleton implementations must therefore incorporate synchronization primitives or exploit language guarantees about initialization ordering.

In Java, the class loader guarantees that static initialization occurs atomically, enabling the Initialization-on-Demand Holder idiom. This approach nests a private static holder class that contains the Singleton instance. The JVM's classloader contract ensures that the holder class initializes exactly once, even under concurrent access, and only when first referenced. This eliminates explicit locking overhead on the common path:

```java
public final class DatabaseConnectionPool {
    private final List<Connection> availableConnections;
    private final List<Connection> inUseConnections;
    private final int maxPoolSize;
    
    private DatabaseConnectionPool() {
        this.maxPoolSize = Integer.parseInt(
            System.getenv("DB_POOL_SIZE")
        );
        this.availableConnections = new CopyOnWriteArrayList<>();
        this.inUseConnections = new CopyOnWriteArrayList<>();
        
        // Pre-populate pool with warm connections
        for (int i = 0; i < maxPoolSize; i++) {
            try {
                Connection conn = DriverManager.getConnection(
                    System.getenv("DB_URL"),
                    System.getenv("DB_USER"),
                    System.getenv("DB_PASSWORD")
                );
                availableConnections.add(conn);
            } catch (SQLException e) {
                throw new IllegalStateException(
                    "Failed to initialize connection pool", e
                );
            }
        }
    }
    
    private static final class Holder {
        private static final DatabaseConnectionPool INSTANCE = 
            new DatabaseConnectionPool();
    }
    
    public static DatabaseConnectionPool getInstance() {
        return Holder.INSTANCE;
    }
    
    public Connection acquire() throws InterruptedException {
        while (true) {
            if (!availableConnections.isEmpty()) {
                Connection conn = availableConnections.remove(0);
                inUseConnections.add(conn);
                return conn;
            }
            Thread.sleep(50); // Backoff before retry
        }
    }
    
    public void release(Connection conn) {
        if (inUseConnections.remove(conn)) {
            availableConnections.add(conn);
        }
    }
    
    public void shutdown() {
        availableConnections.forEach(conn -> {
            try {
                conn.close();
            } catch (SQLException ignored) {}
        });
        inUseConnections.forEach(conn -> {
            try {
                conn.close();
            } catch (SQLException ignored) {}
        });
    }
}
```

This implementation encodes several production-grade decisions. The constructor remains private, enforcing that external code cannot bypass the Singleton mechanism. The nested `Holder` class defers initialization until `getInstance()` executes, avoiding startup costs if the pool goes unused. The use of `CopyOnWriteArrayList` provides thread-safe access without explicit locking, though at the cost of copying overhead on mutations—an acceptable tradeoff given that acquisitions and releases occur far more frequently than structural modifications.

In Rust, Singleton semantics emerge naturally from the module system combined with `lazy_static` or `OnceCell` primitives. The language's ownership model prevents accidental duplication, while `Mutex` or `RwLock` guards provide interior mutability when the Singleton must maintain mutable state:

```rust
use std::sync::{Arc, Mutex, Once};
use std::collections::VecDeque;

pub struct MetricsCollector {
    samples: Mutex<VecDeque<MetricSample>>,
    flush_threshold: usize,
}

#[derive(Clone, Debug)]
pub struct MetricSample {
    pub timestamp_nanos: u64,
    pub metric_name: String,
    pub value: f64,
}

impl MetricsCollector {
    fn new(flush_threshold: usize) -> Self {
        Self {
            samples: Mutex::new(VecDeque::with_capacity(flush_threshold * 2)),
            flush_threshold,
        }
    }
    
    pub fn record(&self, name: impl Into<String>, value: f64) {
        let sample = MetricSample {
            timestamp_nanos: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos() as u64,
            metric_name: name.into(),
            value,
        };
        
        let mut samples = self.samples.lock().unwrap();
        samples.push_back(sample);
        
        if samples.len() >= self.flush_threshold {
            self.flush_internal(&mut samples);
        }
    }
    
    fn flush_internal(&self, samples: &mut VecDeque<MetricSample>) {
        // Simulate flushing to external telemetry system
        eprintln!("Flushing {} samples to metrics backend", samples.len());
        samples.clear();
    }
    
    pub fn force_flush(&self) {
        let mut samples = self.samples.lock().unwrap();
        self.flush_internal(&mut samples);
    }
}

static INIT: Once = Once::new();
static mut COLLECTOR: Option<Arc<MetricsCollector>> = None;

pub fn metrics() -> Arc<MetricsCollector> {
    unsafe {
        INIT.call_once(|| {
            COLLECTOR = Some(Arc::new(MetricsCollector::new(1000)));
        });
        COLLECTOR.as_ref().unwrap().clone()
    }
}
```

The `Once` primitive guarantees that initialization executes exactly once across all threads, even under contention. The `Arc` wrapper enables shared ownership without requiring a global mutable reference, and the interior `Mutex` provides synchronized access to the sample buffer. This design reflects Rust's philosophy of making concurrency hazards explicit—the `unsafe` block documents that we rely on `Once`'s runtime guarantee rather than compile-time verification.

### Factory Method: Subclass-Driven Product Selection

The Factory Method pattern defers product instantiation to subclasses by defining an abstract factory method in the base class. Each subclass overrides this method to return its preferred concrete product type, allowing the base class to operate on the abstract product interface without knowing the actual implementation. This proves particularly powerful in plugin architectures where the application framework defines extension points but delegates product creation to dynamically loaded modules.

Consider a document processing pipeline that must handle multiple file formats. The base `DocumentProcessor` class defines the overall workflow—load, parse, transform, serialize—but delegates format-specific parsing to subclasses:

```java
public abstract class DocumentProcessor {
    
    public final ProcessedDocument process(InputStream input) 
            throws IOException {
        DocumentParser parser = createParser();
        RawDocument raw = parser.parse(input);
        
        // Common transformation logic
        TransformedDocument transformed = applyTransformations(raw);
        
        return new ProcessedDocument(
            transformed.getContent(),
            transformed.getMetadata(),
            System.currentTimeMillis()
        );
    }
    
    protected abstract DocumentParser createParser();
    
    private TransformedDocument applyTransformations(RawDocument doc) {
        // Shared business logic operates on abstract document model
        String normalized = doc.getContent()
            .replaceAll("\\s+", " ")
            .trim();
        
        Map<String, String> metadata = new HashMap<>(doc.getMetadata());
        metadata.put("processed_at", 
            Instant.now().toString());
        
        return new TransformedDocument(normalized, metadata);
    }
}

public class JsonDocumentProcessor extends DocumentProcessor {
    @Override
    protected DocumentParser createParser() {
        return new JsonParser();
    }
}

public class XmlDocumentProcessor extends DocumentProcessor {
    @Override
    protected DocumentParser createParser() {
        return new XmlParser();
    }
}

public class YamlDocumentProcessor extends DocumentProcessor {
    @Override
    protected DocumentParser createParser() {
        return new YamlParser();
    }
}

// Abstract product interface
public interface DocumentParser {
    RawDocument parse(InputStream input) throws IOException;
}

// Concrete products
public class JsonParser implements DocumentParser {
    private final ObjectMapper mapper = new ObjectMapper();
    
    @Override
    public RawDocument parse(InputStream input) throws IOException {
        JsonNode root = mapper.readTree(input);
        
        String content = root.has("content") 
            ? root.get("content").asText() 
            : "";
        
        Map<String, String> metadata = new HashMap<>();
        if (root.has("metadata")) {
            root.get("metadata").fields().forEachRemaining(entry -> 
                metadata.put(entry.getKey(), entry.getValue().asText())
            );
        }
        
        return new RawDocument(content, metadata);
    }
}

public class XmlParser implements DocumentParser {
    @Override
    public RawDocument parse(InputStream input) throws IOException {
        try {
            DocumentBuilderFactory factory = 
                DocumentBuilderFactory.newInstance();
            factory.setFeature(
                "http://apache.org/xml/features/disallow-doctype-decl", 
                true
            );
            
            DocumentBuilder builder = factory.newDocumentBuilder();
            org.w3c.dom.Document doc = builder.parse(input);
            
            NodeList contentNodes = 
                doc.getElementsByTagName("content");
            String content = contentNodes.getLength() > 0
                ? contentNodes.item(0).getTextContent()
                : "";
            
            Map<String, String> metadata = new HashMap<>();
            NodeList metaNodes = doc.getElementsByTagName("meta");
            for (int i = 0; i < metaNodes.getLength(); i++) {
                Element meta = (Element) metaNodes.item(i);
                metadata.put(
                    meta.getAttribute("key"),
                    meta.getAttribute("value")
                );
            }
            
            return new RawDocument(content, metadata);
        } catch (Exception e) {
            throw new IOException("XML parsing failed", e);
        }
    }
}

public class YamlParser implements DocumentParser {
    private final Yaml yaml = new Yaml();
    
    @Override
    public RawDocument parse(InputStream input) throws IOException {
        Map<String, Object> data = yaml.load(input);
        
        String content = data.containsKey("content")
            ? data.get("content").toString()
            : "";
        
        Map<String, String> metadata = new HashMap<>();
        if (data.containsKey("metadata") && 
            data.get("metadata") instanceof Map) {
            
            @SuppressWarnings("unchecked")
            Map<String, Object> meta = 
                (Map<String, Object>) data.get("metadata");
            meta.forEach((k, v) -> 
                metadata.put(k, v != null ? v.toString() : "")
            );
        }
        
        return new RawDocument(content, metadata);
    }
}
```

The `DocumentProcessor` base class encodes the invariant workflow—parse, transform, package—without committing to a specific parser implementation. Each subclass injects its preferred parser by overriding `createParser()`, and the framework's generic logic operates seamlessly on the abstract `DocumentParser` interface. This enables adding new formats without modifying existing processors, adhering to the Open-Closed Principle.

### Abstract Factory: Coordinated Product Families

When systems must instantiate families of related objects that must remain consistent—for instance, UI widgets styled for a specific platform, or database access components bound to a particular vendor—the Abstract Factory pattern provides type-safe coordination. It defines an abstract factory interface declaring creation methods for each product type in the family, with concrete factories ensuring that all products share a coherent implementation lineage.

A database access layer exemplifies this pattern. Different database vendors require coordinated instantiation of connections, commands, and result sets that understand vendor-specific SQL dialects and wire protocols:

```rust
use std::error::Error;
use std::fmt;

// Abstract product interfaces
pub trait Connection: Send + Sync {
    fn execute(&self, sql: &str) -> Result<(), Box<dyn Error>>;
    fn create_command(&self, sql: &str) -> Box<dyn Command>;
    fn close(&self) -> Result<(), Box<dyn Error>>;
}

pub trait Command {
    fn bind_param(&mut self, index: usize, value: &str);
    fn execute_query(&self) -> Result<Box<dyn ResultSet>, Box<dyn Error>>;
}

pub trait ResultSet {
    fn next(&mut self) -> bool;
    fn get_string(&self, column: usize) -> Option<String>;
    fn get_int(&self, column: usize) -> Option<i64>;
}

// Abstract factory
pub trait DatabaseFactory: Send + Sync {
    fn create_connection(&self, conn_str: &str) 
        -> Result<Box<dyn Connection>, Box<dyn Error>>;
    fn get_dialect(&self) -> SqlDialect;
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SqlDialect {
    Postgres,
    MySQL,
    SQLite,
}

// Concrete PostgreSQL family
pub struct PostgresFactory;

impl DatabaseFactory for PostgresFactory {
    fn create_connection(&self, conn_str: &str) 
            -> Result<Box<dyn Connection>, Box<dyn Error>> {
        Ok(Box::new(PostgresConnection::new(conn_str)?))
    }
    
    fn get_dialect(&self) -> SqlDialect {
        SqlDialect::Postgres
    }
}

struct PostgresConnection {
    connection_string: String,
    closed: bool,
}

impl PostgresConnection {
    fn new(conn_str: &str) -> Result<Self, Box<dyn Error>> {
        // Simulate connection establishment
        if conn_str.is_empty() {
            return Err("Invalid connection string".into());
        }
        
        Ok(Self {
            connection_string: conn_str.to_string(),
            closed: false,
        })
    }
}

impl Connection for PostgresConnection {
    fn execute(&self, sql: &str) -> Result<(), Box<dyn Error>> {
        if self.closed {
            return Err("Connection closed".into());
        }
        eprintln!("[Postgres] Executing: {}", sql);
        Ok(())
    }
    
    fn create_command(&self, sql: &str) -> Box<dyn Command> {
        Box::new(PostgresCommand {
            sql: sql.to_string(),
            params: Vec::new(),
        })
    }
    
    fn close(&self) -> Result<(), Box<dyn Error>> {
        eprintln!("[Postgres] Closing connection");
        Ok(())
    }
}

struct PostgresCommand {
    sql: String,
    params: Vec<String>,
}

impl Command for PostgresCommand {
    fn bind_param(&mut self, index: usize, value: &str) {
        while self.params.len() <= index {
            self.params.push(String::new());
        }
        self.params[index] = value.to_string();
    }
    
    fn execute_query(&self) -> Result<Box<dyn ResultSet>, Box<dyn Error>> {
        eprintln!("[Postgres] Query: {} with params {:?}", 
            self.sql, self.params);
        Ok(Box::new(PostgresResultSet {
            rows: vec![
                vec!["Alice".to_string(), "30".to_string()],
                vec!["Bob".to_string(), "25".to_string()],
            ],
            current_row: None,
        }))
    }
}

struct PostgresResultSet {
    rows: Vec<Vec<String>>,
    current_row: Option<usize>,
}

impl ResultSet for PostgresResultSet {
    fn next(&mut self) -> bool {
        let next_index = self.current_row.map_or(0, |i| i + 1);
        if next_index < self.rows.len() {
            self.current_row = Some(next_index);
            true
        } else {
            false
        }
    }
    
    fn get_string(&self, column: usize) -> Option<String> {
        self.current_row
            .and_then(|row_idx| self.rows.get(row_idx))
            .and_then(|row| row.get(column).cloned())
    }
    
    fn get_int(&self, column: usize) -> Option<i64> {
        self.get_string(column)
            .and_then(|s| s.parse().ok())
    }
}

// Concrete MySQL family
pub struct MySQLFactory;

impl DatabaseFactory for MySQLFactory {
    fn create_connection(&self, conn_str: &str) 
            -> Result<Box<dyn Connection>, Box<dyn Error>> {
        Ok(Box::new(MySQLConnection::new(conn_str)?))
    }
    
    fn get_dialect(&self) -> SqlDialect {
        SqlDialect::MySQL
    }
}

struct MySQLConnection {
    connection_string: String,
    closed: bool,
}

impl MySQLConnection {
    fn new(conn_str: &str) -> Result<Self, Box<dyn Error>> {
        if conn_str.is_empty() {
            return Err("Invalid connection string".into());
        }
        
        Ok(Self {
            connection_string: conn_str.to_string(),
            closed: false,
        })
    }
}

impl Connection for MySQLConnection {
    fn execute(&self, sql: &str) -> Result<(), Box<dyn Error>> {
        if self.closed {
            return Err("Connection closed".into());
        }
        eprintln!("[MySQL] Executing: {}", sql);
        Ok(())
    }
    
    fn create_command(&self, sql: &str) -> Box<dyn Command> {
        Box::new(MySQLCommand {
            sql: sql.to_string(),
            params: Vec::new(),
        })
    }
    
    fn close(&self) -> Result<(), Box<dyn Error>> {
        eprintln!("[MySQL] Closing connection");
        Ok(())
    }
}

struct MySQLCommand {
    sql: String,
    params: Vec<String>,
}

impl Command for MySQLCommand {
    fn bind_param(&mut self, index: usize, value: &str) {
        while self.params.len() <= index {
            self.params.push(String::new());
        }
        self.params[index] = value.to_string();
    }
    
    fn execute_query(&self) -> Result<Box<dyn ResultSet>, Box<dyn Error>> {
        eprintln!("[MySQL] Query: {} with params {:?}", 
            self.sql, self.params);
        Ok(Box::new(MySQLResultSet {
            rows: vec![
                vec!["Charlie".to_string(), "35".to_string()],
                vec!["Diana".to_string(), "28".to_string()],
            ],
            current_row: None,
        }))
    }
}

struct MySQLResultSet {
    rows: Vec<Vec<String>>,
    current_row: Option<usize>,
}

impl ResultSet for MySQLResultSet {
    fn next(&mut self) -> bool {
        let next_index = self.current_row.map_or(0, |i| i + 1);
        if next_index < self.rows.len() {
            self.current_row = Some(next_index);
            true
        } else {
            false
        }
    }
    
    fn get_string(&self, column: usize) -> Option<String> {
        self.current_row
            .and_then(|row_idx| self.rows.get(row_idx))
            .and_then(|row| row.get(column).cloned())
    }
    
    fn get_int(&self, column: usize) -> Option<i64> {
        self.get_string(column)
            .and_then(|s| s.parse().ok())
    }
}

// Client code remains database-agnostic
pub fn run_report(factory: &dyn DatabaseFactory, conn_str: &str) 
        -> Result<(), Box<dyn Error>> {
    let conn = factory.create_connection(conn_str)?;
    
    let mut cmd = conn.create_command("SELECT name, age FROM users WHERE age > ?");
    cmd.bind_param(0, "20");
    
    let mut results = cmd.execute_query()?;
    
    while results.next() {
        let name = results.get_string(0).unwrap_or_default();
        let age = results.get_int(1).unwrap_or(0);
        println!("{}: {} years old", name, age);
    }
    
    conn.close()?;
    Ok(())
}
```

The client function `run_report` operates entirely through abstract interfaces. It never names concrete product types—`PostgresConnection`, `MySQLCommand`, etc.—allowing the same code to work across database vendors. The factory pattern enforces that all products originate from the same family, preventing mismatches like pairing a PostgreSQL connection with a MySQL command object.

### Builder: Incremental Construction with Validation

Objects with numerous configuration parameters quickly overwhelm traditional constructors. A network client might require timeouts, retry policies, authentication credentials, TLS settings, proxy configurations, and custom headers—many of them optional. Telescoping constructors proliferate, each adding another parameter, creating maintenance nightmares and invitation for parameter-ordering errors.

The Builder pattern decomposes construction into discrete, named steps. Each builder method sets one aspect of the configuration and returns the builder itself, enabling fluent method chaining. A final `build()` method validates the accumulated state and constructs the immutable product. This approach clarifies intent, enables partial configuration, and centralizes validation logic:

```java
import java.time.Duration;
import java.util.*;
import java.net.URI;
import java.net.http.*;

public final class HttpClient {
    private final URI baseUrl;
    private final Duration connectionTimeout;
    private final Duration requestTimeout;
    private final int maxRetries;
    private final Duration retryBackoff;
    private final Map<String, String> defaultHeaders;
    private final Optional<ProxyConfig> proxy;
    private final java.net.http.HttpClient underlyingClient;
    
    private HttpClient(Builder builder) {
        this.baseUrl = builder.baseUrl;
        this.connectionTimeout = builder.connectionTimeout;
        this.requestTimeout = builder.requestTimeout;
        this.maxRetries = builder.maxRetries;
        this.retryBackoff = builder.retryBackoff;
        this.defaultHeaders = Map.copyOf(builder.defaultHeaders);
        this.proxy = builder.proxy;
        
        java.net.http.HttpClient.Builder clientBuilder = 
            java.net.http.HttpClient.newBuilder()
                .connectTimeout(connectionTimeout);
        
        if (proxy.isPresent()) {
            clientBuilder.proxy(ProxySelector.of(
                java.net.InetSocketAddress.createUnresolved(
                    proxy.get().host, 
                    proxy.get().port
                )
            ));
        }
        
        this.underlyingClient = clientBuilder.build();
    }
    
    public static Builder builder(String baseUrl) {
        return new Builder(baseUrl);
    }
    
    public HttpResponse<String> get(String path) throws Exception {
        return execute("GET", path, null);
    }
    
    public HttpResponse<String> post(String path, String body) 
            throws Exception {
        return execute("POST", path, body);
    }
    
    private HttpResponse<String> execute(String method, String path, 
            String body) throws Exception {
        
        URI uri = baseUrl.resolve(path);
        
        HttpRequest.Builder requestBuilder = HttpRequest.newBuilder()
            .uri(uri)
            .timeout(requestTimeout);
        
        defaultHeaders.forEach(requestBuilder::header);
        
        if (body != null) {
            requestBuilder.method(method, 
                HttpRequest.BodyPublishers.ofString(body));
        } else {
            requestBuilder.method(method, 
                HttpRequest.BodyPublishers.noBody());
        }
        
        HttpRequest request = requestBuilder.build();
        
        int attempt = 0;
        Exception lastException = null;
        
        while (attempt <= maxRetries) {
            try {
                return underlyingClient.send(request, 
                    HttpResponse.BodyHandlers.ofString());
            } catch (Exception e) {
                lastException = e;
                attempt++;
                
                if (attempt <= maxRetries) {
                    Thread.sleep(
                        retryBackoff.toMillis() * attempt
                    );
                }
            }
        }
        
        throw new Exception(
            String.format("Request failed after %d retries", maxRetries),
            lastException
        );
    }
    
    public static final class Builder {
        private final URI baseUrl;
        private Duration connectionTimeout = Duration.ofSeconds(10);
        private Duration requestTimeout = Duration.ofSeconds(30);
        private int maxRetries = 3;
        private Duration retryBackoff = Duration.ofMillis(500);
        private final Map<String, String> defaultHeaders = new HashMap<>();
        private Optional<ProxyConfig> proxy = Optional.empty();
        
        private Builder(String baseUrl) {
            try {
                this.baseUrl = URI.create(baseUrl);
                if (!this.baseUrl.isAbsolute()) {
                    throw new IllegalArgumentException(
                        "Base URL must be absolute"
                    );
                }
            } catch (Exception e) {
                throw new IllegalArgumentException(
                    "Invalid base URL: " + baseUrl, e
                );
            }
        }
        
        public Builder connectionTimeout(Duration timeout) {
            if (timeout.isNegative() || timeout.isZero()) {
                throw new IllegalArgumentException(
                    "Connection timeout must be positive"
                );
            }
            this.connectionTimeout = timeout;
            return this;
        }
        
        public Builder requestTimeout(Duration timeout) {
            if (timeout.isNegative() || timeout.isZero()) {
                throw new IllegalArgumentException(
                    "Request timeout must be positive"
                );
            }
            this.requestTimeout = timeout;
            return this;
        }
        
        public Builder maxRetries(int retries) {
            if (retries < 0) {
                throw new IllegalArgumentException(
                    "Max retries cannot be negative"
                );
            }
            this.maxRetries = retries;
            return this;
        }
        
        public Builder retryBackoff(Duration backoff) {
            if (backoff.isNegative()) {
                throw new IllegalArgumentException(
                    "Retry backoff cannot be negative"
                );
            }
            this.retryBackoff = backoff;
            return this;
        }
        
        public Builder header(String name, String value) {
            Objects.requireNonNull(name, "Header name cannot be null");
            Objects.requireNonNull(value, "Header value cannot be null");
            this.defaultHeaders.put(name, value);
            return this;
        }
        
        public Builder headers(Map<String, String> headers) {
            Objects.requireNonNull(headers, "Headers map cannot be null");
            this.defaultHeaders.putAll(headers);
            return this;
        }
        
        public Builder proxy(String host, int port) {
            Objects.requireNonNull(host, "Proxy host cannot be null");
            if (port < 1 || port > 65535) {
                throw new IllegalArgumentException(
                    "Proxy port must be between 1 and 65535"
                );
            }
            this.proxy = Optional.of(new ProxyConfig(host, port));
            return this;
        }
        
        public HttpClient build() {
            if (requestTimeout.compareTo(connectionTimeout) < 0) {
                throw new IllegalStateException(
                    "Request timeout must be >= connection timeout"
                );
            }
            
            return new HttpClient(this);
        }
    }
    
    private static final class ProxyConfig {
        final String host;
        final int port;
        
        ProxyConfig(String host, int port) {
            this.host = host;
            this.port = port;
        }
    }
}
```

The builder enforces validation at each step—connection timeout must be positive, proxy port must fall within valid range—and performs cross-field validation in `build()` to ensure the request timeout exceeds the connection timeout. The resulting `HttpClient` instance remains immutable after construction, with all fields marked `final`. This immutability eliminates entire classes of concurrency bugs and makes the client safe to share across threads.

### Prototype: Cloning as Creation Strategy

When object initialization proves expensive—loading machine learning model weights, parsing large configuration files, establishing authenticated network sessions—creating new instances from scratch becomes a bottleneck. The Prototype pattern reframes creation as cloning, delegating the mechanics of duplication to the object itself through a `clone()` operation. This enables maintaining a registry of pre-initialized prototypes that clients duplicate on demand.

Java provides built-in support through the `Cloneable` interface and `Object.clone()` method, though its shallow-copy semantics require careful attention. Objects containing mutable fields must override `clone()` to perform deep copies, recursively cloning nested objects to preserve independence:

```java
import java.io.*;
import java.util.*;

public class DocumentTemplate implements Cloneable, Serializable {
    private final String templateName;
    private final Map<String, String> defaultFields;
    private final List<Section> sections;
    private final FormattingOptions formatting;
    
    public DocumentTemplate(String templateName) {
        this.templateName = templateName;
        this.defaultFields = new HashMap<>();
        this.sections = new ArrayList<>();
        this.formatting = new FormattingOptions();
    }
    
    private DocumentTemplate(DocumentTemplate other) {
        this.templateName = other.templateName;
        
        // Deep copy mutable collections
        this.defaultFields = new HashMap<>(other.defaultFields);
        
        this.sections = new ArrayList<>(other.sections.size());
        for (Section section : other.sections) {
            this.sections.add(section.clone());
        }
        
        this.formatting = other.formatting.clone();
    }
    
    public void setDefaultField(String key, String value) {
        defaultFields.put(key, value);
    }
    
    public void addSection(String title, String content) {
        sections.add(new Section(title, content));
    }
    
    public void setFontSize(int size) {
        formatting.fontSize = size;
    }
    
    public void setMargins(int top, int right, int bottom, int left) {
        formatting.marginTop = top;
        formatting.marginRight = right;
        formatting.marginBottom = bottom;
        formatting.marginLeft = left;
    }
    
    @Override
    public DocumentTemplate clone() {
        return new DocumentTemplate(this);
    }
    
    public Document instantiate(Map<String, String> customFields) {
        Map<String, String> mergedFields = new HashMap<>(defaultFields);
        mergedFields.putAll(customFields);
        
        return new Document(
            templateName, 
            mergedFields, 
            new ArrayList<>(sections),
            formatting.clone()
        );
    }
    
    private static class Section implements Cloneable {
        String title;
        String content;
        
        Section(String title, String content) {
            this.title = title;
            this.content = content;
        }
        
        @Override
        protected Section clone() {
            return new Section(title, content);
        }
    }
    
    private static class FormattingOptions implements Cloneable {
        int fontSize = 12;
        int marginTop = 72;
        int marginRight = 72;
        int marginBottom = 72;
        int marginLeft = 72;
        
        @Override
        protected FormattingOptions clone() {
            FormattingOptions copy = new FormattingOptions();
            copy.fontSize = this.fontSize;
            copy.marginTop = this.marginTop;
            copy.marginRight = this.marginRight;
            copy.marginBottom = this.marginBottom;
            copy.marginLeft = this.marginLeft;
            return copy;
        }
    }
    
    public static class Document {
        private final String templateName;
        private final Map<String, String> fields;
        private final List<Section> sections;
        private final FormattingOptions formatting;
        
        Document(String templateName, Map<String, String> fields,
                List<Section> sections, FormattingOptions formatting) {
            this.templateName = templateName;
            this.fields = fields;
            this.sections = sections;
            this.formatting = formatting;
        }
        
        public void render(OutputStream output) throws IOException {
            PrintWriter writer = new PrintWriter(
                new OutputStreamWriter(output)
            );
            
            writer.printf("Template: %s%n", templateName);
            writer.printf("Font Size: %d%n", formatting.fontSize);
            writer.printf("Margins: %d %d %d %d%n%n",
                formatting.marginTop, formatting.marginRight,
                formatting.marginBottom, formatting.marginLeft);
            
            writer.println("Fields:");
            fields.forEach((k, v) -> 
                writer.printf("  %s: %s%n", k, v)
            );
            
            writer.println("\nContent:");
            for (Section section : sections) {
                writer.printf("\n## %s\n%s\n", 
                    section.title, section.content);
            }
            
            writer.flush();
        }
    }
}

// Template registry managing prototypes
public class TemplateRegistry {
    private final Map<String, DocumentTemplate> templates = 
        new HashMap<>();
    
    public void registerTemplate(String name, DocumentTemplate template) {
        templates.put(name, template);
    }
    
    public DocumentTemplate getTemplate(String name) {
        DocumentTemplate prototype = templates.get(name);
        if (prototype == null) {
            throw new IllegalArgumentException(
                "Unknown template: " + name
            );
        }
        return prototype.clone();
    }
    
    public static TemplateRegistry createDefaultRegistry() {
        TemplateRegistry registry = new TemplateRegistry();
        
        // Invoice template
        DocumentTemplate invoice = new DocumentTemplate("invoice");
        invoice.setDefaultField("currency", "USD");
        invoice.setDefaultField("tax_rate", "0.08");
        invoice.addSection("Header", "Company Name\nAddress\nPhone");
        invoice.addSection("Items", "[Item table placeholder]");
        invoice.addSection("Total", "[Total calculation placeholder]");
        invoice.setFontSize(11);
        invoice.setMargins(36, 36, 36, 36);
        registry.registerTemplate("invoice", invoice);
        
        // Report template
        DocumentTemplate report = new DocumentTemplate("report");
        report.setDefaultField("author", "Unknown");
        report.setDefaultField("date", "Today");
        report.addSection("Executive Summary", "[Summary placeholder]");
        report.addSection("Analysis", "[Analysis placeholder]");
        report.addSection("Conclusions", "[Conclusions placeholder]");
        report.setFontSize(12);
        report.setMargins(72, 54, 72, 54);
        registry.registerTemplate("report", report);
        
        return registry;
    }
}
```

The registry maintains pre-configured prototypes that clients clone and customize. Each clone operation produces an independent instance—modifying the clone's sections or formatting does not affect the original prototype. This approach proves particularly valuable when templates load from external sources like databases or configuration files, where the parsing overhead justifies caching prototypes in memory.

## 3. High-Performance Optimization & Failure Modes

Creational patterns introduce abstraction layers that carry runtime costs. Virtual dispatch through factory interfaces incurs pointer indirection and prevents compiler inlining. Builders allocate intermediate objects during construction, creating garbage collection pressure in managed languages. Singleton synchronization mechanisms—even lock-free variants—impose memory barriers that affect cache coherence. Understanding these costs enables judicious pattern application where their benefits justify the overhead.

The Singleton pattern's primary failure mode manifests in testing. Global state couples tests to initialization order and makes parallel test execution hazardous. The standard remedy involves dependency injection—pass the Singleton as a constructor parameter rather than invoking `getInstance()` directly. This enables substituting test doubles during testing while preserving the Singleton invariant in production. Modern dependency injection frameworks like Spring (Java) or dependency-injector (Python) automate this, managing Singleton scopes without requiring manual `getInstance()` calls.

Another Singleton hazard emerges in systems with multiple classloaders. Java's classloader hierarchy can instantiate multiple "singleton" instances, one per classloader namespace. This violates uniqueness assumptions and leads to subtle bugs when code expects referential equality. The solution involves hosting the Singleton in the system classloader rather than application-specific loaders, or abandoning Singleton entirely in favor of explicit lifecycle management through a container.

Factory patterns scale poorly when product hierarchies grow deep. Each new product type requires modifying the factory interface and updating all concrete factories, violating the Open-Closed Principle. This signals that the abstraction has become too coarse-grained. Refactoring toward finer-grained factories—perhaps one per subsystem—or adopting a plugin registry that discovers factories via reflection or configuration restores extensibility. In Rust, trait objects combined with inventory crate's compile-time registration enable zero-configuration factory discovery:

```rust
use inventory;
use std::collections::HashMap;
use std::sync::OnceLock;

pub trait CompressionCodec: Send + Sync {
    fn name(&self) -> &'static str;
    fn compress(&self, data: &[u8]) -> Vec<u8>;
    fn decompress(&self, data: &[u8]) -> Result<Vec<u8>, String>;
}

inventory::collect!(CodecFactory);

pub struct CodecFactory {
    pub name: &'static str,
    pub create: fn() -> Box<dyn CompressionCodec>,
}

static CODEC_REGISTRY: OnceLock<HashMap<&'static str, fn() -> Box<dyn CompressionCodec>>> = OnceLock::new();

pub fn get_codec(name: &str) -> Option<Box<dyn CompressionCodec>> {
    let registry = CODEC_REGISTRY.get_or_init(|| {
        let mut map = HashMap::new();
        for factory in inventory::iter::<CodecFactory> {
            map.insert(factory.name, factory.create);
        }
        map
    });
    
    registry.get(name).map(|create_fn| create_fn())
}

// Gzip codec implementation
struct GzipCodec;

impl CompressionCodec for GzipCodec {
    fn name(&self) -> &'static str {
        "gzip"
    }
    
    fn compress(&self, data: &[u8]) -> Vec<u8> {
        use flate2::write::GzEncoder;
        use flate2::Compression;
        use std::io::Write;
        
        let mut encoder = GzEncoder::new(Vec::new(), Compression::default());
        encoder.write_all(data).unwrap();
        encoder.finish().unwrap()
    }
    
    fn decompress(&self, data: &[u8]) -> Result<Vec<u8>, String> {
        use flate2::read::GzDecoder;
        use std::io::Read;
        
        let mut decoder = GzDecoder::new(data);
        let mut result = Vec::new();
        decoder.read_to_end(&mut result)
            .map_err(|e| format!("Decompression failed: {}", e))?;
        Ok(result)
    }
}

inventory::submit! {
    CodecFactory {
        name: "gzip",
        create: || Box::new(GzipCodec),
    }
}

// Zstd codec implementation
struct ZstdCodec;

impl CompressionCodec for ZstdCodec {
    fn name(&self) -> &'static str {
        "zstd"
    }
    
    fn compress(&self, data: &[u8]) -> Vec<u8> {
        zstd::encode_all(data, 3).unwrap()
    }
    
    fn decompress(&self, data: &[u8]) -> Result<Vec<u8>, String> {
        zstd::decode_all(data)
            .map_err(|e| format!("Decompression failed: {}", e))
    }
}

inventory::submit! {
    CodecFactory {
        name: "zstd",
        create: || Box::new(ZstdCodec),
    }
}

// Client code discovers codecs automatically
pub fn compress_file(codec_name: &str, data: &[u8]) -> Result<Vec<u8>, String> {
    let codec = get_codec(codec_name)
        .ok_or_else(|| format!("Unknown codec: {}", codec_name))?;
    
    Ok(codec.compress(data))
}
```

This approach eliminates the central factory switch statement. New codecs register themselves at compile time via `inventory::submit!`, and the runtime registry discovers them automatically. The pattern scales to hundreds of codecs without modifying existing code.

Builders introduce allocation overhead during construction. In tight loops where objects churn rapidly, this garbage collection pressure degrades throughput. The solution involves object pooling—maintain a pool of pre-allocated builder instances that clients reuse across iterations. After calling `build()`, reset the builder to its initial state and return it to the pool. This amortizes allocation costs across many construction cycles. Thread-local pools eliminate synchronization overhead when each thread maintains its own pool.

Another Builder failure mode emerges when validation occurs only in `build()`, allowing builders to accumulate invalid state throughout method chaining. Clients receive no feedback until the final build attempt, at which point diagnosing the error requires tracing back through the chain. Eager validation—checking each setter immediately—provides faster feedback but couples validation logic to individual setters rather than centralizing it. A hybrid approach validates individual fields in setters while deferring cross-field validation to `build()`, balancing responsiveness with maintainability.

Prototype cloning grows expensive as object graphs deepen. Recursive cloning traverses the entire graph, copying every reachable object. For graphs containing thousands of nodes, this dominates construction time. Optimizations include copy-on-write sharing, where clones initially share immutable substructures and copy lazily upon mutation. This requires language support for smart pointers that track sharing and trigger copying—Rust's `Arc` combined with `Cow` (clone-on-write) provides exactly this. Alternatively, serialize the prototype once and deserialize into new instances, leveraging optimized serialization libraries that outperform naive recursive copying.

Finally, creational patterns become overused when simpler alternatives suffice. If a class has no configuration parameters, a straightforward constructor beats a needless builder. If only one product type exists, a factory adds indirection without flexibility. If initialization cost proves negligible, cloning prototypes wastes effort. Apply patterns when their invariants and flexibility genuinely solve problems rather than adopting them dogmatically. The goal remains code that reflects domain requirements clearly, not code that demonstrates pattern vocabulary.
