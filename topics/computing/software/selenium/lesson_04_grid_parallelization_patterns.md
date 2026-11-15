# Lesson 4: Selenium Grid Architecture, Test Parallelization Patterns

## 1. First-Principles Intuition & Invariants

The fundamental problem Selenium Grid solves is not merely speed, though speed is the most visible benefit. The deeper problem is one of environmental fidelity at scale. A test suite that takes forty minutes to run sequentially will take forty minutes to discover a regression that was introduced two hours ago. By the time a developer receives that signal, they have context-switched, opened three new files, and begun reasoning about an entirely different problem. The cognitive cost of re-establishing the mental model of what they were doing when the failing commit landed is substantial. Grid exists to compress the feedback loop, and to do so faithfully, without compromising the environmental realism that makes browser tests meaningful in the first place.

The intuition behind Grid maps directly onto a classic distributed work queue. You have a population of tests, each of which represents a unit of work that requires a browser session. You have a population of browser nodes, each of which is a resource capable of satisfying that session request. The coordination problem is matching demand to supply in a way that respects constraints, maximizes throughput, and maintains isolation between concurrent sessions. If you have held a mental model of Grid as "just running tests faster," replace it with a more precise model: Grid is a capability-aware session broker operating over a pool of heterogeneous browser resources.

Understanding why Grid must be capability-aware before anything else is the key to reasoning correctly about every architectural decision that follows. A test written against Chrome 114 behaves subtly differently from the same test run against Firefox 112. User-Agent strings differ, JavaScript engine timing characteristics differ, CSS rendering of edge cases differs. A test that asserts a pixel-precise layout may legitimately fail on one browser and pass on another due to sub-pixel font rendering differences that are not regressions. When a test client requests a session, it is not merely requesting "a browser." It is requesting a specific configuration of browser vendor, version, platform, and potentially custom capabilities such as a specific screen resolution or a pre-configured proxy. Grid's capability matching engine must route the request to a node that can satisfy the full capability specification, and it must do so without routing a Chrome test to a Firefox node simply because Firefox nodes happen to be idle.

The architectural evolution from Grid 3 to Grid 4 is worth internalizing because the design rationale explains why the internals are structured the way they are. Grid 3 used a single Hub process and one or more Node processes. The Hub held all state, brokered all sessions, and acted as both the HTTP entry point and the internal coordinator. This design worked adequately at modest scale but introduced a single point of failure, a single point of contention on the Hub's connection pool, and an operational coupling that made it impossible to scale the routing tier independently from the session management tier. Grid 4 decomposed the Hub into discrete components: the Router, the Distributor, the Session Map, the Session Queue, and individual Node services. Each component has a narrow responsibility. This decomposition is the standard pattern for evolving a monolith under load, and understanding which component is responsible for which behavior is essential to diagnosing production failures.

The core invariants the system must enforce are session isolation, capability fidelity, and session lifecycle correctness. Session isolation means that two concurrent test sessions must never share browser state: cookies, localStorage, the active URL, or any DOM state. Capability fidelity means that a session fulfills the requested capabilities exactly, not approximately. Session lifecycle correctness means that every session that is created is eventually destroyed, that browser processes do not accumulate as zombie sessions consuming node memory indefinitely, and that the Grid's view of session state is always consistent with the actual browser process state on the node.

---

## 2. Core Architecture & Mechanics

### Hub-Node Topology in Grid 4

The physical signal path of a session request in Grid 4 moves through a well-defined sequence of components. Understanding this path in detail is what allows you to place instrumentation, interpret log output, and reason about where a bottleneck or failure originates.

```
                        ┌─────────────────────────────────────────────────────┐
                        │                   TEST CLIENT                       │
                        │  RemoteWebDriver("http://grid-router:4444/wd/hub")  │
                        └────────────────────────┬────────────────────────────┘
                                                 │  POST /session {caps}
                                                 ▼
                        ┌────────────────────────────────────────────────────┐
                        │                     ROUTER                         │
                        │   Stateless HTTP reverse proxy + path classifier   │
                        │   /session  → Distributor                          │
                        │   /session/{id}/* → Session Map → Node             │
                        └────────────┬────────────────────────┬──────────────┘
                                     │                        │
                     new session     │          command on    │  existing session
                                     ▼          session       ▼
                        ┌─────────────────────┐    ┌────────────────────────┐
                        │    DISTRIBUTOR      │    │      SESSION MAP        │
                        │  Capability match   │    │  sessionId → nodeUrl   │
                        │  Slot allocation    │    │  (in-memory or Redis)  │
                        │  Node health track  │    └──────────┬─────────────┘
                        └──────┬──────────────┘               │
                               │                              │ proxy to node
                               │  reserve slot                ▼
                        ┌──────▼──────────────────────────────────────────────┐
                        │                 SESSION QUEUE                        │
                        │  Unbounded FIFO with capability-keyed pending items  │
                        │  Polled by Distributor on slot availability event    │
                        └───────────────────────────────────────────────────-─┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              ▼                      ▼                       ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │      NODE A      │  │      NODE B      │  │      NODE C      │
   │  Chrome 114 ×4   │  │  Firefox 112 ×2  │  │  Chrome 114 ×2   │
   │  Edge 114 ×2     │  │  Chrome 113 ×2   │  │  Safari 16 ×1    │
   └──────────────────┘  └──────────────────┘  └──────────────────┘
```

The Router is intentionally stateless. It inspects only whether the incoming HTTP request is a new session creation (`POST /session`) or a command against an existing session (`POST|GET|DELETE /session/{id}/...`). For new session requests, it forwards to the Distributor. For existing session commands, it queries the Session Map to resolve the target node URL, then proxies the request directly to that node, bypassing the Distributor entirely. This design is critical for performance: once a session is established, every subsequent WebDriver command travels in one network hop from the Router to the Node without touching any coordination layer. At hundreds of commands per second across dozens of concurrent sessions, eliminating that indirection makes a measurable difference.

The Distributor owns two responsibilities: capability matching and slot allocation. When a session request arrives, the Distributor iterates over all registered nodes and their advertised slots. Each slot corresponds to one concurrent browser session. A node with four Chrome slots can serve four concurrent Chrome sessions. The Distributor evaluates the client's requested capabilities against each slot's stereotype. The matching algorithm checks for exact version matches when specified, vendor matches, platform matches, and any custom capability key-value pairs. The first node with a matching, unoccupied slot wins the allocation. If no slot is currently available, the request is placed into the Session Queue, where it waits until a slot becomes free or the new session timeout elapses.

The Session Map is conceptually the simplest component but critically important for correctness. It maintains a mapping from every live session ID to the URL of the node that owns it. In standalone mode this is an in-memory hash map. In a distributed deployment, this can be backed by Redis, allowing multiple Router instances to serve as an HA entry point without diverging on session location. When a node crashes while holding sessions, the Session Map entries for those sessions become stale. The Grid handles this via node heartbeat: nodes poll the Distributor at a configurable interval (default every ten seconds). If a node fails to heartbeat within the timeout window (default thirty seconds), the Distributor marks it unhealthy and removes its slots from the available pool. The Session Map entries for sessions that were on the dead node are cleaned up, and the client's subsequent WebDriver command will receive a 404 or 500 response, triggering retry logic in the test runner.

### Capability Matching in Depth

The W3C WebDriver specification defines a capability merging algorithm that Grid 4 implements faithfully. When a client sends `POST /session`, the request body carries an `alwaysMatch` object and a `firstMatch` array. The semantics are precise: `alwaysMatch` capabilities must be satisfied by any session the Grid returns. Each entry in `firstMatch` is a set of capabilities that may optionally be satisfied. The Grid processes the capability merge by iterating through `firstMatch` entries, merging each with `alwaysMatch`, and testing whether any node slot satisfies the merged result. The first successful merge that matches an available slot determines the session configuration.

A common production mistake is relying exclusively on `alwaysMatch` with highly specific version strings when the fleet has mixed browser versions. If the fleet has nodes running Chrome 114 and 115 and the test requests Chrome 114 specifically, all Chrome 115 slots are excluded. During peak hours when Chrome 114 slots are saturated, requests queue indefinitely rather than routing to 115. The correct pattern for cross-version suites uses `firstMatch` to express a preference ordering: prefer 114, but accept 115. This is the difference between a queueing system that gracefully degrades and one that deadlocks under load.

### Remote WebDriver Instantiation

From the test client's perspective, the entry point is the `RemoteWebDriver` constructor. The instantiation sequence is worth walking through in detail because it makes the failure modes obvious.

```java
import org.openqa.selenium.remote.RemoteWebDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.remote.http.ClientConfig;
import java.net.URL;
import java.time.Duration;

public class GridSessionFactory {

    private static final String GRID_URL = "http://selenium-router:4444";

    public static RemoteWebDriver createChromeSession() throws Exception {
        ChromeOptions options = new ChromeOptions();

        // Capability negotiation: alwaysMatch via ChromeOptions
        options.setBrowserVersion("114");
        options.setPlatformName("linux");

        // Chrome-specific: disable GPU in headless container environments
        options.addArguments("--disable-gpu");
        options.addArguments("--no-sandbox");
        options.addArguments("--disable-dev-shm-usage");
        options.addArguments("--window-size=1920,1080");

        // Prevent shared state bleeding through cache dirs in parallel runs
        options.addArguments("--user-data-dir=/tmp/chrome-" + Thread.currentThread().getId());

        ClientConfig clientConfig = ClientConfig
            .defaultConfig()
            .baseUrl(new URL(GRID_URL))
            // Grid may queue the session if no slot is free; allow generous timeout
            .connectionTimeout(Duration.ofSeconds(60))
            .readTimeout(Duration.ofSeconds(300));

        return RemoteWebDriver.builder()
            .oneOf(options)
            .config(clientConfig)
            .build();
    }
}
```

When `RemoteWebDriver.builder().build()` executes, the client opens an HTTP connection to the Router at `POST /wd/hub/session` with the serialized capabilities payload. The Router classifies this as a new session request and forwards it to the Distributor. The Distributor runs capability matching, finds an available slot, instructs the target node to start a browser process, waits for the node to return a session ID, registers the session ID in the Session Map, and returns the full session response to the client. The client's `RemoteWebDriver` instance stores the session ID and the node URL for all subsequent commands.

The critical timeout to reason about here is the new session timeout, configured on the Grid Router as `--session-request-timeout`. When the queue is deep, a test client blocks at `RemoteWebDriver` construction waiting for a slot. If this timeout fires before a slot becomes available, the client receives an HTTP 500 with a `SessionNotCreatedException`. Your test runner must distinguish between this error (a resource exhaustion condition indicating the grid is undersized) and a `WebDriverException` on a command after session creation (a potential test code or application bug). Log the distinction explicitly.

### Container-Based Grid with Docker Selenium

The Docker Selenium project (`selenium/hub`, `selenium/node-chrome`, `selenium/node-firefox`) maps directly onto the Grid 4 component topology. Each component runs as a separate container, and nodes register themselves with the Hub using the `SE_EVENT_BUS_HOST` and `SE_EVENT_BUS_PUBLISH_PORT` environment variables. The event bus carries node registration, heartbeat, and slot availability notifications using an internal publish-subscribe protocol built on ZeroMQ.

A production-grade Docker Compose configuration that deploys a Router, Distributor, Session Queue, Session Map, Event Bus, and a fleet of Chrome and Firefox nodes looks like this:

```yaml
version: "3.8"

networks:
  selenium-grid:
    driver: bridge

services:
  selenium-event-bus:
    image: selenium/event-bus:4.18.1
    container_name: selenium-event-bus
    networks:
      - selenium-grid
    ports:
      - "4442:4442"
      - "4443:4443"
      - "5557:5557"
    environment:
      SE_OPTS: "--log-level FINE"

  selenium-sessions:
    image: selenium/sessions:4.18.1
    container_name: selenium-sessions
    networks:
      - selenium-grid
    ports:
      - "5556:5556"
    depends_on:
      - selenium-event-bus
    environment:
      SE_EVENT_BUS_HOST: selenium-event-bus
      SE_EVENT_BUS_PUBLISH_PORT: 4442
      SE_EVENT_BUS_SUBSCRIBE_PORT: 4443

  selenium-session-queue:
    image: selenium/session-queue:4.18.1
    container_name: selenium-session-queue
    networks:
      - selenium-grid
    ports:
      - "5559:5559"
    depends_on:
      - selenium-event-bus
    environment:
      SE_EVENT_BUS_HOST: selenium-event-bus
      SE_EVENT_BUS_PUBLISH_PORT: 4442
      SE_EVENT_BUS_SUBSCRIBE_PORT: 4443

  selenium-distributor:
    image: selenium/distributor:4.18.1
    container_name: selenium-distributor
    networks:
      - selenium-grid
    ports:
      - "5553:5553"
    depends_on:
      - selenium-event-bus
      - selenium-sessions
      - selenium-session-queue
    environment:
      SE_EVENT_BUS_HOST: selenium-event-bus
      SE_EVENT_BUS_PUBLISH_PORT: 4442
      SE_EVENT_BUS_SUBSCRIBE_PORT: 4443
      SE_SESSIONS_MAP_HOST: selenium-sessions
      SE_SESSIONS_MAP_PORT: 5556
      SE_SESSION_QUEUE_HOST: selenium-session-queue
      SE_SESSION_QUEUE_PORT: 5559
      SE_NODE_MAX_SESSIONS: "5"

  selenium-router:
    image: selenium/router:4.18.1
    container_name: selenium-router
    networks:
      - selenium-grid
    ports:
      - "4444:4444"
    depends_on:
      - selenium-distributor
      - selenium-sessions
      - selenium-session-queue
    environment:
      SE_DISTRIBUTOR_HOST: selenium-distributor
      SE_DISTRIBUTOR_PORT: 5553
      SE_SESSIONS_MAP_HOST: selenium-sessions
      SE_SESSIONS_MAP_PORT: 5556
      SE_SESSION_QUEUE_HOST: selenium-session-queue
      SE_SESSION_QUEUE_PORT: 5559
      SE_SESSION_REQUEST_TIMEOUT: "300"
      SE_SESSION_RETRY_INTERVAL: "5"

  chrome-node-1:
    image: selenium/node-chrome:4.18.1
    container_name: chrome-node-1
    networks:
      - selenium-grid
    shm_size: "2gb"
    depends_on:
      - selenium-event-bus
    environment:
      SE_EVENT_BUS_HOST: selenium-event-bus
      SE_EVENT_BUS_PUBLISH_PORT: 4442
      SE_EVENT_BUS_SUBSCRIBE_PORT: 4443
      SE_NODE_MAX_SESSIONS: "4"
      SE_NODE_OVERRIDE_MAX_SESSIONS: "true"
      SE_NODE_SESSION_TIMEOUT: "300"
      SE_SCREEN_WIDTH: "1920"
      SE_SCREEN_HEIGHT: "1080"
      SE_SCREEN_DEPTH: "24"
      SE_NODE_GRID_URL: "http://selenium-router:4444"

  chrome-node-2:
    image: selenium/node-chrome:4.18.1
    container_name: chrome-node-2
    networks:
      - selenium-grid
    shm_size: "2gb"
    depends_on:
      - selenium-event-bus
    environment:
      SE_EVENT_BUS_HOST: selenium-event-bus
      SE_EVENT_BUS_PUBLISH_PORT: 4442
      SE_EVENT_BUS_SUBSCRIBE_PORT: 4443
      SE_NODE_MAX_SESSIONS: "4"
      SE_NODE_OVERRIDE_MAX_SESSIONS: "true"
      SE_NODE_SESSION_TIMEOUT: "300"
      SE_SCREEN_WIDTH: "1920"
      SE_SCREEN_HEIGHT: "1080"
      SE_SCREEN_DEPTH: "24"
      SE_NODE_GRID_URL: "http://selenium-router:4444"

  firefox-node-1:
    image: selenium/node-firefox:4.18.1
    container_name: firefox-node-1
    networks:
      - selenium-grid
    shm_size: "2gb"
    depends_on:
      - selenium-event-bus
    environment:
      SE_EVENT_BUS_HOST: selenium-event-bus
      SE_EVENT_BUS_PUBLISH_PORT: 4442
      SE_EVENT_BUS_SUBSCRIBE_PORT: 4443
      SE_NODE_MAX_SESSIONS: "2"
      SE_NODE_OVERRIDE_MAX_SESSIONS: "true"
      SE_NODE_SESSION_TIMEOUT: "300"
      SE_SCREEN_WIDTH: "1920"
      SE_SCREEN_HEIGHT: "1080"
      SE_SCREEN_DEPTH: "24"
      SE_NODE_GRID_URL: "http://selenium-router:4444"
```

The `shm_size` parameter deserves explicit attention. Chrome allocates its inter-process communication segments in `/dev/shm`, which Docker limits to 64 MB by default. Chrome's renderer process uses shared memory for compositing frames. Under that limit, Chrome silently falls back to in-process rendering or crashes the renderer tab with a `STATUS_ACCESS_VIOLATION`-equivalent signal. Setting `shm_size` to at least 2 GB per node container eliminates this class of flaky test failure, which is otherwise extremely difficult to attribute correctly.

### Parallel Execution Models

Parallelization in a Selenium test suite can be decomposed into three orthogonal axes: parallelism at the test method level, at the test class level, and at the test suite (shard) level. Each has different implications for state management, session overhead, and infrastructure cost.

Test method level parallelism is the finest granularity. Each individual test method acquires its own WebDriver session, executes, and quits. This provides maximum isolation because no shared driver state can bleed between methods, but it carries maximum session creation overhead. Session creation in Grid 4 involves an HTTP round-trip to the Router, Distributor processing, node process spawn (for the browser), and browser startup. Chrome cold-start in a container is typically 800 ms to 1.5 seconds. For a suite of 500 test methods, session creation alone accounts for 400 to 750 seconds of wall-clock time if sessions are not reused. At method-level parallelism with fifty concurrent sessions, that amortizes well, but it must be weighed against the Grid's slot capacity.

Test class level parallelism shares one session across all methods within a class, creating the session in a `@BeforeClass` hook and quitting it in `@AfterClass`. This amortizes session creation cost across the class's methods and is the most common production pattern. The risk is state leakage between methods: a test that leaves the browser in a logged-in state, with specific cookies or localStorage entries, will corrupt the state assumptions of the next method unless the class design explicitly resets relevant state. The contract is that each test method must leave the browser in a neutral state or the class must handle state reset in a `@BeforeMethod` hook that navigates to a known URL and clears storage.

Suite-level sharding, also called test splitting, operates outside of Grid's direct concern. The test runner splits the full test inventory across N parallel JVM or process invocations, each of which runs a subset of tests sequentially or with class-level parallelism. Each JVM connects to the same Grid router. This is the model used by CI systems like GitHub Actions matrix builds or Jenkins parallel stages. Each matrix job is an independent OS-level process, and Grid serves as the shared resource pool. Sharding at the CI level is composable with method or class level parallelism within each shard; the two layers multiply throughput independently.

A TestNG parallel execution configuration that expresses class-level parallelism with thread count matching your Grid's available Chrome slot capacity looks like this:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE suite SYSTEM "https://testng.org/testng-1.0.dtd">

<suite name="ParallelSmokeSuite"
       parallel="classes"
       thread-count="8"
       verbose="1"
       data-provider-thread-count="4">

  <listeners>
    <listener class-name="com.example.grid.RetryAnalyzerListener"/>
    <listener class-name="com.example.grid.SessionCleanupListener"/>
  </listeners>

  <test name="ChromeSmoke" preserve-order="false">
    <parameter name="browser" value="chrome"/>
    <parameter name="browser-version" value="114"/>
    <parameter name="grid-url" value="http://selenium-router:4444"/>
    <classes>
      <class name="com.example.tests.LoginSuiteTest"/>
      <class name="com.example.tests.CheckoutFlowTest"/>
      <class name="com.example.tests.SearchResultsTest"/>
      <class name="com.example.tests.UserProfileTest"/>
      <class name="com.example.tests.PaymentMethodTest"/>
      <class name="com.example.tests.NotificationPreferencesTest"/>
      <class name="com.example.tests.AdminDashboardTest"/>
      <class name="com.example.tests.ReportGenerationTest"/>
    </classes>
  </test>

</suite>
```

The `thread-count="8"` value should match the number of Chrome slots your Grid exposes, not exceed it. When thread count exceeds slot count, the excess threads block at `RemoteWebDriver` construction waiting for a slot. This is not harmful, but it creates uneven test startup timing that can skew duration reporting and misleads capacity planning.

A thread-local `WebDriver` management pattern prevents the accidental driver sharing that causes some of the most confusing intermittent failures in parallel suites:

```java
package com.example.grid;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.firefox.FirefoxOptions;
import org.openqa.selenium.remote.RemoteWebDriver;
import org.openqa.selenium.remote.http.ClientConfig;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Optional;
import org.testng.annotations.Parameters;

import java.net.URL;
import java.time.Duration;

public abstract class BaseGridTest {

    // ThreadLocal ensures each parallel thread holds its own driver reference.
    // A static field without ThreadLocal would cause threads to overwrite each
    // other's driver, producing race conditions on quit() and command dispatch.
    private static final ThreadLocal<WebDriver> threadDriver = new ThreadLocal<>();

    @BeforeClass(alwaysRun = true)
    @Parameters({"browser", "browser-version", "grid-url"})
    public void setUpDriver(
            @Optional("chrome") String browser,
            @Optional("114") String browserVersion,
            @Optional("http://localhost:4444") String gridUrl) throws Exception {

        WebDriver driver = buildDriver(browser, browserVersion, gridUrl);
        threadDriver.set(driver);
        driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(0));
        driver.manage().timeouts().pageLoadTimeout(Duration.ofSeconds(30));
        driver.manage().window().maximize();
    }

    @AfterClass(alwaysRun = true)
    public void tearDownDriver() {
        WebDriver driver = threadDriver.get();
        if (driver != null) {
            try {
                driver.quit();
            } finally {
                // Remove the reference to prevent memory leak in long-lived
                // thread pools where threads are reused across test classes.
                threadDriver.remove();
            }
        }
    }

    protected WebDriver getDriver() {
        WebDriver driver = threadDriver.get();
        if (driver == null) {
            throw new IllegalStateException(
                "WebDriver not initialized for thread " + Thread.currentThread().getName() +
                ". Ensure setUpDriver() has been called before accessing getDriver()."
            );
        }
        return driver;
    }

    private WebDriver buildDriver(String browser, String version, String gridUrl) throws Exception {
        ClientConfig config = ClientConfig.defaultConfig()
            .baseUrl(new URL(gridUrl))
            .connectionTimeout(Duration.ofSeconds(60))
            .readTimeout(Duration.ofSeconds(300));

        switch (browser.toLowerCase()) {
            case "firefox": {
                FirefoxOptions options = new FirefoxOptions();
                options.setBrowserVersion(version);
                options.setPlatformName("linux");
                options.addPreference("browser.cache.disk.enable", false);
                options.addPreference("browser.cache.memory.enable", false);
                return RemoteWebDriver.builder()
                    .oneOf(options)
                    .config(config)
                    .build();
            }
            case "chrome":
            default: {
                ChromeOptions options = new ChromeOptions();
                options.setBrowserVersion(version);
                options.setPlatformName("linux");
                options.addArguments("--disable-gpu");
                options.addArguments("--no-sandbox");
                options.addArguments("--disable-dev-shm-usage");
                options.addArguments("--window-size=1920,1080");
                // Per-thread user-data-dir prevents Chrome from sharing extension
                // and profile state across concurrent sessions on the same node.
                options.addArguments(
                    "--user-data-dir=/tmp/chrome-profile-" + Thread.currentThread().getId()
                );
                return RemoteWebDriver.builder()
                    .oneOf(options)
                    .config(config)
                    .build();
            }
        }
    }
}
```

---

## 3. High-Performance Optimization & Failure Modes

### Session Queue Saturation and Backpressure

The most common production failure mode in a Grid deployment is queue saturation. When the inbound rate of session requests exceeds the rate at which slots become available, the Session Queue grows without bound until requests begin timing out. The symptoms are characteristically misleading: tests appear to hang at startup with no browser activity, CI jobs stall with no log output, and the eventual failure is a `SessionNotCreatedException` with a timeout message rather than any application error. Engineers unfamiliar with Grid internals frequently suspect test code or application bugs before identifying the Grid as the bottleneck.

The correct diagnostic sequence starts with the Grid's status endpoint. `GET http://selenium-router:4444/status` returns a JSON document containing the current slot inventory, occupied slot count, and node health. If `readyCount` equals zero and `sessionCount` is at the ceiling of `maxSessions`, you are observing queue saturation. The queue depth is not directly surfaced in this endpoint in Grid 4.18; you must query the Session Queue component directly at `GET http://selenium-session-queue:5559/se/grid/newsessionqueue/queue` to retrieve pending request count.

Mitigation has two dimensions: horizontal scaling and demand shaping. Horizontal scaling means adding more node containers. Because nodes register themselves with the Event Bus on startup, Grid 4 handles node addition dynamically without Router or Distributor restart. In a Kubernetes deployment, this is a Deployment replica count change and Grid absorbs it gracefully within the node heartbeat interval.

Demand shaping means controlling the inbound rate from the test runner. If your CI matrix spawns thirty parallel JVM processes each requesting eight sessions simultaneously, the peak burst is 240 session requests within a few seconds. If your Grid has 80 slots, 160 requests queue immediately. Setting a staggered thread startup delay in the test runner, or more precisely tuning the CI matrix to spawn fewer parallel JVMs with more intra-JVM parallelism, smooths the demand curve. Intra-JVM parallelism through TestNG thread pools naturally staggers session requests because each thread blocks on driver construction sequentially from the pool's queue.

### Resource Contention on Nodes

A node configured with `SE_NODE_MAX_SESSIONS=4` running four concurrent Chrome sessions is operating at significant memory pressure. A Chrome instance with a typical web application loaded occupies 300 to 600 MB of private memory, depending on the complexity of the DOM, the number of open tabs (each Chrome test should use a single tab per session), and JavaScript heap activity. Four concurrent sessions on a single container therefore require 1.2 to 2.4 GB of available memory, plus the overhead of the Xvfb virtual framebuffer, the Grid node Java process, and the operating system. Nodes that are memory-constrained exhibit a specific failure pattern: Chrome renderer processes begin crashing under the OOM killer with no test-code-visible error, and the WebDriver session loses connectivity mid-test with a `WebDriverException: chrome not reachable` message. The test runner retries, creates a new session, and may land on the same exhausted node, triggering a cascade.

The correct capacity model is to provision each Chrome slot with 512 MB of guaranteed memory plus a 200 MB headroom buffer. A four-slot Chrome node therefore needs a container memory limit of at least 2.8 GB. In the Docker Compose configuration above, this is expressed as:

```yaml
  chrome-node-1:
    image: selenium/node-chrome:4.18.1
    networks:
      - selenium-grid
    shm_size: "2gb"
    deploy:
      resources:
        limits:
          memory: "3g"
          cpus: "2.0"
        reservations:
          memory: "2g"
          cpus: "1.0"
```

CPU contention is a subtler issue than memory contention and produces harder-to-diagnose failures. When four Chrome instances compete for two CPU cores, rendering and JavaScript execution slow down. Tests with explicit sleeps or large `implicitlyWait` values may still pass because they have timing slack, but tests with tight timing assumptions (polling an element for 500 ms expecting it to appear after a 300 ms animation) begin flaking. The failure signal is increased test duration variance rather than outright failure, which is a classic sign of CPU starvation. Allocating at least one CPU core per two concurrent sessions, with burst capability, keeps execution timing predictable.

### Test Isolation Guarantees and Their Limits

Grid provides session-level isolation by running each session in a separate browser process. At the browser process boundary, there is genuine isolation: separate process memory, separate cookie stores, separate localStorage, separate network credential caches (HTTP Basic Auth, client certificates). However, Grid does not provide isolation at the network layer, the application layer, or the test data layer.

If two parallel test sessions target the same application user account and both attempt to modify that account's settings, they will interfere with each other regardless of session isolation at the browser level. This is a test design problem, not a Grid problem, but it surfaces specifically under parallelism and is therefore often misattributed to Grid. The correct architectural response is test data partitioning: each parallel test execution is allocated a unique user account, a unique order ID range, or a unique tenant namespace, and no two parallel tests share mutable application state.

Database-level isolation for integration tests running against a real backend follows the same principle. Each parallel test class should operate against a data fixture that it owns exclusively, created in a `@BeforeClass` setup step and deleted in `@AfterClass`. When this is not feasible due to shared database state, the alternative is serializing tests that share critical state into a single thread while keeping the rest of the suite parallel. TestNG's `dependsOnGroups` and group configuration allow expressing this constraint declaratively.

One isolation boundary that Grid explicitly does not enforce is filesystem state on the node container. If a test downloads a file to the browser's default download directory and a concurrent test on the same node also downloads a file, the files coexist in the same directory. Tests that assert on downloaded file content must either configure the download directory to a unique per-session path (via ChromeOptions preferences) or avoid filesystem assertions entirely in favor of network-layer interception through BiDi or CDP.

### Kubernetes Deployment and Dynamic Autoscaling

In a Kubernetes environment, the Docker Compose topology maps onto a standard Deployment-and-Service architecture, with the additional capability of horizontal pod autoscaling driven by Grid queue depth. The Grid's status endpoint provides the queue depth metric, which a custom Kubernetes metrics adapter can expose to the Horizontal Pod Autoscaler.

A Kubernetes Deployment for Chrome nodes that autoscales based on pending session requests looks like this:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: selenium-chrome-node
  namespace: selenium-grid
  labels:
    app: selenium-chrome-node
spec:
  replicas: 2
  selector:
    matchLabels:
      app: selenium-chrome-node
  template:
    metadata:
      labels:
        app: selenium-chrome-node
    spec:
      terminationGracePeriodSeconds: 3600
      containers:
        - name: selenium-chrome-node
          image: selenium/node-chrome:4.18.1
          env:
            - name: SE_EVENT_BUS_HOST
              value: selenium-event-bus
            - name: SE_EVENT_BUS_PUBLISH_PORT
              value: "4442"
            - name: SE_EVENT_BUS_SUBSCRIBE_PORT
              value: "4443"
            - name: SE_NODE_MAX_SESSIONS
              value: "4"
            - name: SE_NODE_OVERRIDE_MAX_SESSIONS
              value: "true"
            - name: SE_NODE_SESSION_TIMEOUT
              value: "300"
            - name: SE_NODE_GRID_URL
              value: "http://selenium-router:4444"
            - name: SE_SCREEN_WIDTH
              value: "1920"
            - name: SE_SCREEN_HEIGHT
              value: "1080"
            - name: SE_SCREEN_DEPTH
              value: "24"
          resources:
            requests:
              memory: "2Gi"
              cpu: "1500m"
            limits:
              memory: "3Gi"
              cpu: "2000m"
          volumeMounts:
            - name: dshm
              mountPath: /dev/shm
          livenessProbe:
            httpGet:
              path: /status
              port: 5555
            initialDelaySeconds: 30
            periodSeconds: 15
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /status
              port: 5555
            initialDelaySeconds: 15
            periodSeconds: 10
            failureThreshold: 2
      volumes:
        - name: dshm
          emptyDir:
            medium: Memory
            sizeLimit: "2Gi"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: selenium-chrome-node-hpa
  namespace: selenium-grid
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: selenium-chrome-node
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: External
      external:
        metric:
          name: selenium_grid_queue_size
        target:
          type: AverageValue
          averageValue: "2"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Pods
          value: 4
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 2
          periodSeconds: 120
```

The `terminationGracePeriodSeconds: 3600` on the node pod is deliberate and important. When Kubernetes terminates a pod, it sends SIGTERM and waits for `terminationGracePeriodSeconds` before sending SIGKILL. If a node pod receives SIGTERM while holding active sessions and the grace period is too short, those sessions are killed mid-test, producing false failures. Setting the grace period to one hour ensures that normal session timeout (300 seconds) will have expired and sessions will have completed before the pod is forcibly killed. The Grid node is configured to stop accepting new sessions after receiving SIGTERM (via the node's drain behavior), so new requests are not routed to it after the signal, while in-flight sessions complete.

The `emptyDir` volume with `medium: Memory` mounted at `/dev/shm` replaces the container's default `/dev/shm` with a memory-backed tmpfs of 2 GB. This is the Kubernetes-native equivalent of the Docker Compose `shm_size` parameter and addresses the same Chrome renderer shared memory exhaustion problem.

### Flakiness Attribution and Structural Retry Policy

Flaky tests in a parallel Grid execution are a signal that something in the system lacks sufficient isolation or determinism. The temptation is to introduce broad retry logic that re-runs any failing test up to three times and considers a test passing if it passes on any attempt. This is a rational short-term operational choice but a dangerous long-term engineering choice because it converts latent reliability problems into invisible ones.

A more principled approach classifies retry eligibility by exception type. A `SessionNotCreatedException` during driver construction is always a Grid infrastructure issue and should be retried. A `StaleElementReferenceException` on a WebDriver command is a test-timing issue that may be retried at the WebDriver command level, not the test level. A test-level `AssertionError` should never be retried automatically, because an assertion failure indicates that the application under test produced an incorrect result, which is exactly the information the test exists to surface.

```java
package com.example.grid;

import org.openqa.selenium.SessionNotCreatedException;
import org.openqa.selenium.WebDriverException;
import org.testng.IRetryAnalyzer;
import org.testng.ITestResult;

public class GridAwareRetryAnalyzer implements IRetryAnalyzer {

    private static final int MAX_INFRASTRUCTURE_RETRIES = 2;
    private int infrastructureRetryCount = 0;

    @Override
    public boolean retry(ITestResult result) {
        Throwable cause = result.getThrowable();

        if (cause == null) {
            return false;
        }

        // Retry only on Grid infrastructure failures, never on assertion failures.
        if (isInfrastructureFailure(cause) && infrastructureRetryCount < MAX_INFRASTRUCTURE_RETRIES) {
            infrastructureRetryCount++;
            System.err.printf(
                "[RetryAnalyzer] Infrastructure failure on attempt %d for test '%s': %s%n",
                infrastructureRetryCount,
                result.getMethod().getMethodName(),
                cause.getMessage()
            );
            return true;
        }

        return false;
    }

    private boolean isInfrastructureFailure(Throwable t) {
        if (t instanceof SessionNotCreatedException) {
            return true;
        }
        if (t instanceof WebDriverException) {
            String message = t.getMessage();
            return message != null && (
                message.contains("chrome not reachable") ||
                message.contains("unable to connect to renderer") ||
                message.contains("Session ID is null") ||
                message.contains("connection refused")
            );
        }
        return false;
    }
}
```

This retry policy is conservative by design. Infrastructure failures on session creation are transient and retry-worthy. Application-level assertion failures are deterministic and must surface unretried so that they reach the developer's attention immediately. Blurring this distinction with broad retry policies is how flakiness debt accumulates until a test suite with a 20% per-run infrastructure noise floor is considered "normal" and the signal from genuine regressions is permanently degraded.

The final invariant of a healthy Grid deployment is that the total number of zombie sessions — sessions in the Session Map that no longer correspond to a live browser process — should trend to zero over time. Monitor the Grid status endpoint's `sessionCount` against your test runner's reported test execution count. After a full suite run, `sessionCount` should return to zero within twice the `SE_NODE_SESSION_TIMEOUT` value. If it does not, sessions are leaking, which means `driver.quit()` is not being called reliably in test teardown hooks. The `alwaysRun = true` attribute on `@AfterClass` teardown methods and the `finally` block pattern in the `tearDownDriver` implementation above are the structural guarantees that ensure quit is called even when the test body throws an unexpected exception.
