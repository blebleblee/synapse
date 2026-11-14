# Lesson 3: Health Checks, Failure Detection, Connection Management

## 1. First-Principles Intuition & Invariants

At the heart of every load balancer lies a deceptively simple but profound question: which upstream servers are capable of serving traffic right now? This is not a static property that can be configured once and forgotten. The universe of distributed systems is hostile to static assumptions. Servers crash. Network partitions isolate entire availability zones. Application threads deadlock while the operating system continues responding to TCP handshakes. Memory leaks cause garbage collection pauses that render services temporarily unresponsive. The load balancer exists at the boundary between client expectations and backend reality, and its primary duty is to maintain a continuously updated model of which upstream endpoints can successfully satisfy requests.

Health checking is the mechanism by which a load balancer constructs and maintains this model. Unlike routing or scheduling algorithms that decide *how* to distribute traffic among known-good backends, health checking determines the membership of the healthy set itself. This is a fundamentally different concern. A least-connections scheduler that sends traffic to a dead backend has failed catastrophically, regardless of how sophisticated its algorithm. The health checking subsystem must therefore operate as a continuous background process, perpetually probing the state of the upstream world and updating the available backend pool.

The core architectural tension in health check design is the tradeoff between detection latency and system overhead. Ideally, a load balancer would detect backend failure instantaneously, removing the failed node from rotation within milliseconds. But instantaneous detection requires continuous probing at extremely high frequency, which imposes CPU cost on the load balancer, network bandwidth cost on the infrastructure, and handler thread cost on the upstream servers. A health check is not free—it is a request that must be processed, scheduled, and responded to. Multiply that cost by thousands of backend servers checked every second, and the health checking system itself becomes a significant source of load. The optimal strategy must balance rapid failure detection against the overhead costs of the detection mechanism itself.

This leads to the first core invariant: **health checks are statistical inference over a noisy channel**. A single failed health check does not necessarily mean the backend is truly down. Network packets are dropped. Transient CPU spikes cause timeouts. A backend experiencing momentary congestion might fail one probe but succeed on the next. Conversely, a backend might respond successfully to a trivial health check probe while being completely unable to serve real production traffic due to database connection pool exhaustion or deadlocked application logic. The health checking system must therefore implement hysteresis and statistical thresholds, requiring multiple consecutive failures before marking a backend unhealthy, and multiple consecutive successes before restoring it to the healthy pool.

The second invariant is that **passive health monitoring provides signal that active health checks cannot capture**. Active health checks are synthetic probes initiated by the load balancer on a fixed schedule. They test a predetermined endpoint with a predetermined request pattern. Passive health monitoring, by contrast, observes the actual production traffic flowing through the load balancer and infers backend health from the outcomes of real client requests. If a backend returns HTTP 503 Service Unavailable errors or TCP connection resets for actual client traffic, that is a much stronger signal of unavailability than a failed synthetic health check. Passive monitoring captures failure modes that active checks miss entirely: application-level errors, request timeouts under load, or degraded performance that falls below acceptable latency thresholds.

The third invariant concerns the difference between network reachability and application readiness. A server can be network-reachable—responding to TCP handshakes, ACKing packets, even responding to HTTP requests—while being completely unable to perform useful work. Consider a web application server that has not yet completed its startup initialization sequence: database connection pools not established, configuration not loaded, in-memory caches not warmed. The operating system TCP stack will happily accept connections, but the application layer cannot serve requests. Health checks must therefore probe at the application layer, not merely at the transport layer, and must verify that the application is ready to perform its intended function.

This leads directly to the concept of readiness versus liveness. Liveness checks answer the question "Is this process still running?" while readiness checks answer "Is this process ready to serve traffic?" A containerized application might be alive—the process is running, has not crashed, is not deadlocked—but not ready, perhaps because it is still loading a large dataset into memory or waiting for downstream dependencies to become available. Load balancers must implement readiness checks and must only route traffic to backends that have declared themselves ready, even if those backends are provably alive.

The failure detection problem is further complicated by the possibility of cascading failures and thundering herds. When a backend becomes overloaded and starts failing health checks, the load balancer removes it from the pool. The remaining healthy backends now receive a larger share of traffic. If the system was already near capacity, this redistribution can push the remaining backends into overload, causing them to fail health checks and be removed from the pool. The process cascades until the entire backend fleet is marked unhealthy, at which point the load balancer faces a terrible choice: route no traffic at all, or route traffic to backends it knows to be failing. This is the failure avalanche problem, and it demands sophisticated circuit breaker and graceful degradation strategies.

Connection management is the mechanism by which the load balancer maintains and reuses network connections to upstream backends. Every new TCP connection incurs a three-way handshake, consuming at least one round-trip time. For TLS connections, the overhead is even higher: a full TLS 1.3 handshake requires an additional round trip, and TLS 1.2 requires two. If the load balancer establishes a new connection for every client request, latency will be dominated by connection establishment overhead rather than actual request processing time. Connection pooling solves this by maintaining a pool of persistent connections to each backend, reusing them across multiple client requests.

But connection pooling introduces its own failure modes. Connections can break silently. A backend server might crash, leaving half-open TCP connections that appear valid to the load balancer but will never deliver responses. Network middle-boxes might drop connection state, causing packets to be silently discarded. The load balancer must therefore implement connection health validation, testing pooled connections before reusing them or detecting failures quickly when a reused connection turns out to be dead. This is where TCP keep-alive mechanics and application-layer connection validation become critical.

The final invariant is that **all failure detection is eventually consistent**. There is always a window of time between a backend failing and the load balancer detecting that failure. During this window, the load balancer may route traffic to the failed backend, resulting in client-visible errors. The goal of health checking and failure detection is not to eliminate this window entirely—that is impossible in a distributed system—but to minimize its duration and to provide mechanisms for graceful degradation when failures do occur.


## 2. Core Architecture & Mechanics

The canonical architecture of a health checking subsystem consists of three cooperating components: the active health checker, the passive health monitor, and the backend state manager. These components operate concurrently, feeding observations into a shared state machine that determines the current health status of each backend.

The active health checker is a background thread or coroutine pool that periodically issues synthetic probe requests to each backend endpoint. The probe request is typically a lightweight HTTP GET to a designated health check endpoint, or a TCP connection attempt, or a custom protocol-specific check. The checker measures both the success or failure of the probe and the latency of the response. It maintains per-backend state tracking consecutive successes and failures, implementing a sliding window or threshold counter that determines when to transition a backend between healthy and unhealthy states.

Consider a typical active health check state machine:

```
                   ┌─────────────┐
                   │   HEALTHY   │
                   └──────┬──────┘
                          │
              [fail_count >= threshold]
                          │
                          ▼
                   ┌─────────────┐
                   │  UNHEALTHY  │
                   └──────┬──────┘
                          │
            [success_count >= threshold]
                          │
                          ▼
                   ┌─────────────┐
                   │   HEALTHY   │
                   └─────────────┘
```

The state machine implements hysteresis through the threshold counters. A backend marked healthy must fail multiple consecutive health checks before transitioning to unhealthy, and a backend marked unhealthy must succeed multiple consecutive health checks before transitioning back to healthy. This prevents flapping, where transient network glitches cause a backend to oscillate rapidly between states. A typical configuration might require three consecutive failures to mark a backend unhealthy and two consecutive successes to restore it.

The probe interval and timeout parameters control the aggressiveness of failure detection. A probe interval of one second with a timeout of two seconds means the health checker issues a probe every second and waits up to two seconds for a response. If no response arrives within the timeout, the probe is considered failed. Shorter intervals enable faster failure detection but increase system overhead. Longer timeouts reduce false positives from slow backends but increase the time required to detect genuine failures.

The passive health monitor observes actual client traffic flowing through the load balancer. It tracks connection failures, request timeouts, and application-level errors on a per-backend basis. When a backend exhibits a pattern of errors exceeding a configured threshold, the passive monitor can mark the backend unhealthy without waiting for active health checks to detect the failure. This provides much faster failure detection for backends that fail under actual load but might still respond to synthetic health checks.

A reference implementation in Go might structure the passive monitor as follows:

```go
package healthcheck

import (
	"sync"
	"time"
)

type PassiveMonitor struct {
	mu               sync.RWMutex
	backendErrors    map[string]*errorWindow
	errorThreshold   float64
	windowDuration   time.Duration
	unhealthyCallback func(backend string)
}

type errorWindow struct {
	requests       int64
	errors         int64
	windowStart    time.Time
}

func NewPassiveMonitor(errorThreshold float64, windowDuration time.Duration, callback func(string)) *PassiveMonitor {
	return &PassiveMonitor{
		backendErrors:     make(map[string]*errorWindow),
		errorThreshold:    errorThreshold,
		windowDuration:    windowDuration,
		unhealthyCallback: callback,
	}
}

func (pm *PassiveMonitor) RecordRequest(backend string, isError bool) {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	now := time.Now()
	window, exists := pm.backendErrors[backend]
	
	if !exists || now.Sub(window.windowStart) > pm.windowDuration {
		window = &errorWindow{
			windowStart: now,
		}
		pm.backendErrors[backend] = window
	}

	window.requests++
	if isError {
		window.errors++
	}

	if window.requests >= 10 {
		errorRate := float64(window.errors) / float64(window.requests)
		if errorRate > pm.errorThreshold {
			pm.unhealthyCallback(backend)
		}
	}
}

func (pm *PassiveMonitor) ResetBackend(backend string) {
	pm.mu.Lock()
	defer pm.mu.Unlock()
	delete(pm.backendErrors, backend)
}
```

This implementation tracks requests and errors within a sliding time window. When the error rate exceeds the configured threshold and sufficient samples have been collected, it invokes a callback to mark the backend unhealthy. The passive monitor operates entirely on observed traffic, requiring no additional probing overhead.

The backend state manager is the authoritative source of truth for backend health status. It receives health observations from both the active checker and passive monitor, applies the configured state transition rules, and updates the available backend pool. Critically, it must synchronize access to shared state across multiple threads or coroutines, as health checkers typically run concurrently to avoid blocking the main request-processing path.

A production-grade NGINX configuration demonstrating active health checks looks like this:

```nginx
upstream backend_pool {
    zone backend_zone 64k;
    
    server 10.0.1.10:8080 max_fails=3 fail_timeout=30s;
    server 10.0.1.11:8080 max_fails=3 fail_timeout=30s;
    server 10.0.1.12:8080 max_fails=3 fail_timeout=30s;
    server 10.0.1.13:8080 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://backend_pool;
        proxy_next_upstream error timeout http_503;
        proxy_connect_timeout 2s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }
    
    location /health {
        access_log off;
        proxy_pass http://backend_pool/internal/health;
        proxy_connect_timeout 1s;
        proxy_read_timeout 2s;
    }
}
```

The `max_fails` and `fail_timeout` directives implement passive health checking. If a backend fails three times within thirty seconds, NGINX marks it temporarily unavailable and will not route traffic to it for the duration of the fail timeout. The `proxy_next_upstream` directive defines which error conditions trigger a retry to the next backend in the pool.

For active health checks, NGINX Plus provides dedicated directives:

```nginx
upstream backend_pool {
    zone backend_zone 64k;
    
    server 10.0.1.10:8080;
    server 10.0.1.11:8080;
    server 10.0.1.12:8080;
    server 10.0.1.13:8080;
}

match backend_health_check {
    status 200;
    header Content-Type = "application/json";
    body ~ "\"status\":\"healthy\"";
}

server {
    listen 80;
    
    location / {
        proxy_pass http://backend_pool;
        health_check interval=5s fails=2 passes=2 uri=/health match=backend_health_check;
    }
}
```

This configuration issues an HTTP GET to `/health` every five seconds, expecting a 200 status code, a JSON Content-Type header, and a response body containing the string `"status":"healthy"`. The backend must fail two consecutive checks to be marked unhealthy and pass two consecutive checks to be restored.

HAProxy provides similarly sophisticated health checking through its `option httpchk` directive:

```
global
    maxconn 50000
    log stdout format raw local0

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    option httplog
    option redispatch
    retries 3

backend app_servers
    balance leastconn
    option httpchk GET /health HTTP/1.1\r\nHost:\ health.internal
    http-check expect status 200
    http-check expect string "healthy"
    
    default-server inter 3s fall 3 rise 2 check
    
    server app1 10.0.1.10:8080 check
    server app2 10.0.1.11:8080 check
    server app3 10.0.1.12:8080 check
    server app4 10.0.1.13:8080 check
```

The `inter 3s` parameter sets the probe interval to three seconds. The `fall 3` parameter requires three consecutive failures before marking a backend down. The `rise 2` parameter requires two consecutive successes before marking it back up. The `http-check expect` directives validate both status code and response body content.

Connection pooling mechanics in HAProxy are controlled through the `http-reuse` directive:

```
backend app_servers
    mode http
    balance roundrobin
    http-reuse safe
    http-keep-alive 30s
    
    server app1 10.0.1.10:8080 check maxconn 100 pool-max-conn 50
    server app2 10.0.1.11:8080 check maxconn 100 pool-max-conn 50
```

The `http-reuse safe` directive enables connection reuse for requests that are known to be idempotent and safe. The `pool-max-conn 50` parameter limits the number of idle connections maintained in the pool per backend server. When a new request arrives, HAProxy first attempts to reuse an idle connection from the pool. If no idle connections are available and the backend has not reached `maxconn`, HAProxy establishes a new connection. If `maxconn` is reached, the request is queued.

The TCP keep-alive mechanism operates at the transport layer, sending periodic empty ACK packets to verify that the connection peer is still reachable. This is configured through socket options:

```go
package lb

import (
	"net"
	"time"
)

func configureKeepalive(conn *net.TCPConn) error {
	if err := conn.SetKeepAlive(true); err != nil {
		return err
	}
	if err := conn.SetKeepAlivePeriod(30 * time.Second); err != nil {
		return err
	}
	return nil
}
```

On Linux, the kernel provides fine-grained control over keep-alive behavior through three sysctls: `tcp_keepalive_time` (the idle time before the first probe), `tcp_keepalive_intvl` (the interval between subsequent probes), and `tcp_keepalive_probes` (the number of failed probes before declaring the connection dead). A typical production configuration might set these to 60 seconds, 10 seconds, and 6 probes respectively, detecting a dead connection within approximately two minutes of failure.

Circuit breaker patterns provide an additional layer of failure protection by preventing the load balancer from routing traffic to backends exhibiting sustained failure patterns. The circuit breaker exists in one of three states: closed (normal operation), open (failing fast without attempting requests), and half-open (tentatively testing whether the backend has recovered).

```go
package circuitbreaker

import (
	"errors"
	"sync"
	"time"
)

type State int

const (
	StateClosed State = iota
	StateOpen
	StateHalfOpen
)

type CircuitBreaker struct {
	mu                sync.Mutex
	state             State
	failureCount      int64
	successCount      int64
	lastFailureTime   time.Time
	failureThreshold  int64
	successThreshold  int64
	timeout           time.Duration
}

var ErrCircuitOpen = errors.New("circuit breaker is open")

func NewCircuitBreaker(failureThreshold, successThreshold int64, timeout time.Duration) *CircuitBreaker {
	return &CircuitBreaker{
		state:            StateClosed,
		failureThreshold: failureThreshold,
		successThreshold: successThreshold,
		timeout:          timeout,
	}
}

func (cb *CircuitBreaker) Call(fn func() error) error {
	cb.mu.Lock()
	
	if cb.state == StateOpen {
		if time.Since(cb.lastFailureTime) > cb.timeout {
			cb.state = StateHalfOpen
			cb.successCount = 0
		} else {
			cb.mu.Unlock()
			return ErrCircuitOpen
		}
	}
	
	cb.mu.Unlock()
	
	err := fn()
	
	cb.mu.Lock()
	defer cb.mu.Unlock()
	
	if err != nil {
		cb.failureCount++
		cb.lastFailureTime = time.Now()
		cb.successCount = 0
		
		if cb.failureCount >= cb.failureThreshold {
			cb.state = StateOpen
		}
		return err
	}
	
	if cb.state == StateHalfOpen {
		cb.successCount++
		if cb.successCount >= cb.successThreshold {
			cb.state = StateClosed
			cb.failureCount = 0
		}
	} else {
		cb.failureCount = 0
	}
	
	return nil
}

func (cb *CircuitBreaker) GetState() State {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	return cb.state
}
```

When the circuit breaker is closed, requests flow normally. Each failure increments the failure counter. When failures exceed the threshold, the breaker transitions to open, immediately rejecting all requests without attempting to contact the backend. After the configured timeout period, the breaker transitions to half-open, allowing a limited number of test requests through. If these succeed, the breaker closes and normal operation resumes. If they fail, the breaker reopens and the timeout period resets.


## 3. High-Performance Optimization & Failure Modes

The performance characteristics of health checking systems scale with the product of backend count, check frequency, and check complexity. A load balancer managing ten thousand backends with one-second check intervals must execute ten thousand health checks per second continuously. This is not merely a matter of CPU capacity—it requires careful attention to connection lifecycle management, memory allocation patterns, and scheduler latency.

High-frequency health checking demands a non-blocking, event-driven architecture. A naive implementation using blocking I/O with one thread per backend does not scale beyond a few hundred backends. The thread context switching overhead and memory consumption for thread stacks becomes prohibitive. Instead, production load balancers implement health checking using asynchronous I/O primitives: epoll on Linux, kqueue on BSD, IOCP on Windows. A single event loop thread can multiplex health checks for thousands of backends, issuing connection attempts and waiting for responses without blocking.

Consider the edge case of simultaneous health check expiry across all backends. If ten thousand backends are registered at system startup and the check interval is set to exactly one second, all health checks will fire simultaneously every second, creating a thundering herd of outbound connection attempts. This can exhaust ephemeral port ranges, trigger rate limiting in network infrastructure, or overwhelm the load balancer's own connection tracking tables. The solution is check jittering: introducing a small random offset to each backend's check schedule so that checks are uniformly distributed across the interval rather than synchronized.

```go
package healthcheck

import (
	"math/rand"
	"time"
)

func scheduleWithJitter(baseInterval time.Duration, jitterPercent float64) time.Duration {
	jitter := float64(baseInterval) * jitterPercent * (rand.Float64() - 0.5) * 2
	return baseInterval + time.Duration(jitter)
}

func (hc *ActiveHealthChecker) scheduleCheck(backend string) {
	interval := scheduleWithJitter(hc.interval, 0.2)
	time.AfterFunc(interval, func() {
		hc.executeCheck(backend)
		hc.scheduleCheck(backend)
	})
}
```

This implementation adds up to twenty percent jitter in either direction, spreading health checks across a forty percent window centered on the base interval. The jitter must be re-randomized on each iteration to prevent synchronization from gradually reemerging.

The choice of health check endpoint has profound implications for both accuracy and overhead. A common pattern is to implement a dedicated health check handler that performs minimal validation and returns immediately. But this raises a critical question: what constitutes a meaningful health signal? A handler that simply returns HTTP 200 without performing any real work provides no assurance that the application can actually process requests. The backend might be deadlocked, might have lost database connectivity, might be out of memory—but as long as the HTTP server thread can send back a static 200 response, the health check passes.

The solution is deep health checking: the health check endpoint must validate critical dependencies and subsystems before declaring itself healthy. A web application backend should verify database connectivity by executing a lightweight query. It should check that message queue connections are alive. It should validate that critical configuration is loaded and that no fatal initialization errors occurred. But this validation must be fast—a health check that takes hundreds of milliseconds to execute is itself a source of overhead and may cause false negatives under load.

A reference implementation for a deep health check endpoint in Go:

```go
package health

import (
	"context"
	"database/sql"
	"encoding/json"
	"net/http"
	"sync"
	"time"
)

type Checker struct {
	db    *sql.DB
	cache *Cache
}

type HealthResponse struct {
	Status  string            `json:"status"`
	Checks  map[string]string `json:"checks"`
	Version string            `json:"version"`
}

func (c *Checker) HealthCheckHandler(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
	defer cancel()

	response := HealthResponse{
		Status:  "healthy",
		Checks:  make(map[string]string),
		Version: "1.2.3",
	}

	var wg sync.WaitGroup
	var mu sync.Mutex

	wg.Add(2)

	go func() {
		defer wg.Done()
		if err := c.checkDatabase(ctx); err != nil {
			mu.Lock()
			response.Status = "unhealthy"
			response.Checks["database"] = "failed: " + err.Error()
			mu.Unlock()
		} else {
			mu.Lock()
			response.Checks["database"] = "ok"
			mu.Unlock()
		}
	}()

	go func() {
		defer wg.Done()
		if err := c.checkCache(ctx); err != nil {
			mu.Lock()
			response.Status = "unhealthy"
			response.Checks["cache"] = "failed: " + err.Error()
			mu.Unlock()
		} else {
			mu.Lock()
			response.Checks["cache"] = "ok"
			mu.Unlock()
		}
	}()

	done := make(chan struct{})
	go func() {
		wg.Wait()
		close(done)
	}()

	select {
	case <-done:
	case <-ctx.Done():
		response.Status = "unhealthy"
		response.Checks["timeout"] = "health check exceeded deadline"
	}

	w.Header().Set("Content-Type", "application/json")
	if response.Status == "unhealthy" {
		w.WriteHeader(http.StatusServiceUnavailable)
	} else {
		w.WriteHeader(http.StatusOK)
	}
	json.NewEncoder(w).Encode(response)
}

func (c *Checker) checkDatabase(ctx context.Context) error {
	return c.db.PingContext(ctx)
}

func (c *Checker) checkCache(ctx context.Context) error {
	return c.cache.Ping(ctx)
}
```

This handler validates both database and cache connectivity in parallel with a two-second timeout. If any check fails or the timeout expires, it returns HTTP 503. The parallel execution ensures that the total health check latency is bounded by the slowest dependency rather than the sum of all dependencies.

Connection pool exhaustion is a particularly insidious failure mode. When the load balancer maintains a connection pool to each backend, it must handle the case where all pooled connections are in use and new requests arrive. The naive strategy is to block waiting for a connection to become available, but this can cause cascading timeouts and request pile-ups. A better approach is to impose a strict timeout on connection acquisition and fail fast if no connection becomes available within the timeout window.

```go
package pool

import (
	"context"
	"errors"
	"net"
	"sync"
	"time"
)

var ErrPoolExhausted = errors.New("connection pool exhausted")

type ConnectionPool struct {
	mu          sync.Mutex
	conns       []net.Conn
	maxSize     int
	idleTimeout time.Duration
	dialFunc    func() (net.Conn, error)
}

func NewConnectionPool(maxSize int, idleTimeout time.Duration, dialFunc func() (net.Conn, error)) *ConnectionPool {
	return &ConnectionPool{
		conns:       make([]net.Conn, 0, maxSize),
		maxSize:     maxSize,
		idleTimeout: idleTimeout,
		dialFunc:    dialFunc,
	}
}

func (p *ConnectionPool) Get(ctx context.Context) (net.Conn, error) {
	deadline, hasDeadline := ctx.Deadline()
	if !hasDeadline {
		deadline = time.Now().Add(5 * time.Second)
	}

	for {
		p.mu.Lock()
		if len(p.conns) > 0 {
			conn := p.conns[len(p.conns)-1]
			p.conns = p.conns[:len(p.conns)-1]
			p.mu.Unlock()
			
			if err := p.validateConnection(conn); err != nil {
				conn.Close()
				continue
			}
			return conn, nil
		}
		p.mu.Unlock()

		if time.Now().After(deadline) {
			return nil, ErrPoolExhausted
		}

		conn, err := p.dialFunc()
		if err != nil {
			return nil, err
		}
		return conn, nil
	}
}

func (p *ConnectionPool) Put(conn net.Conn) {
	p.mu.Lock()
	defer p.mu.Unlock()

	if len(p.conns) < p.maxSize {
		p.conns = append(p.conns, conn)
	} else {
		conn.Close()
	}
}

func (p *ConnectionPool) validateConnection(conn net.Conn) error {
	conn.SetReadDeadline(time.Now().Add(1 * time.Second))
	defer conn.SetReadDeadline(time.Time{})
	
	one := make([]byte, 1)
	_, err := conn.Read(one)
	if err == nil {
		return errors.New("unexpected data on idle connection")
	}
	
	if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
		return nil
	}
	
	return err
}
```

The `validateConnection` method attempts a non-blocking read with a short timeout to verify that the connection is still alive. If the read succeeds, the connection has unexpected data and is considered invalid. If the read times out, the connection is valid. Any other error indicates a broken connection.

Graceful degradation during widespread backend failure requires sophisticated policy decisions. When a majority of backends are marked unhealthy, the load balancer faces several options. It can continue routing only to the remaining healthy backends, risking overload on those survivors. It can begin routing to unhealthy backends with the reasoning that some traffic getting through is better than none. It can return immediate errors to clients, failing fast rather than attempting doomed requests. Or it can implement retry budgets and fallback logic.

A retry budget is a mechanism that limits the total number of retries the load balancer will attempt across all requests within a time window. This prevents retry storms, where each failed request triggers multiple retries, multiplying the load on already-struggling backends and accelerating the failure cascade. The budget is typically expressed as a percentage of total requests: if the retry rate exceeds ten percent of throughput, for example, the load balancer stops retrying and begins failing fast.

```go
package retry

import (
	"sync/atomic"
	"time"
)

type RetryBudget struct {
	requestCount   int64
	retryCount     int64
	budgetPercent  float64
	windowDuration time.Duration
	lastReset      int64
}

func NewRetryBudget(budgetPercent float64, windowDuration time.Duration) *RetryBudget {
	return &RetryBudget{
		budgetPercent:  budgetPercent,
		windowDuration: windowDuration,
		lastReset:      time.Now().UnixNano(),
	}
}

func (rb *RetryBudget) MayRetry() bool {
	now := time.Now().UnixNano()
	lastReset := atomic.LoadInt64(&rb.lastReset)
	
	if time.Duration(now-lastReset) > rb.windowDuration {
		if atomic.CompareAndSwapInt64(&rb.lastReset, lastReset, now) {
			atomic.StoreInt64(&rb.requestCount, 0)
			atomic.StoreInt64(&rb.retryCount, 0)
		}
	}

	requests := atomic.LoadInt64(&rb.requestCount)
	retries := atomic.LoadInt64(&rb.retryCount)

	if requests == 0 {
		return true
	}

	currentRetryRate := float64(retries) / float64(requests)
	return currentRetryRate < rb.budgetPercent
}

func (rb *RetryBudget) RecordRequest() {
	atomic.AddInt64(&rb.requestCount, 1)
}

func (rb *RetryBudget) RecordRetry() {
	atomic.AddInt64(&rb.retryCount, 1)
}
```

This implementation uses lock-free atomic operations to track request and retry counts within a sliding window. Before attempting a retry, the load balancer checks whether the current retry rate is below the budget threshold.

The final critical consideration is the interaction between health checking and connection draining during deployments. When a backend is being shut down for maintenance or deployment, it should stop accepting new connections while allowing existing connections to complete their work. The health check endpoint should immediately begin returning unhealthy status, signaling the load balancer to stop routing new requests. But the backend should not forcibly close existing connections until all in-flight requests have completed or timed out.

A deployment-aware health check implementation:

```go
package lifecycle

import (
	"context"
	"net/http"
	"sync/atomic"
	"time"
)

type ShutdownManager struct {
	shuttingDown  int32
	inflightCount int64
	shutdownChan  chan struct{}
}

func NewShutdownManager() *ShutdownManager {
	return &ShutdownManager{
		shutdownChan: make(chan struct{}),
	}
}

func (sm *ShutdownManager) BeginShutdown() {
	if atomic.CompareAndSwapInt32(&sm.shuttingDown, 0, 1) {
		close(sm.shutdownChan)
	}
}

func (sm *ShutdownManager) IsShuttingDown() bool {
	return atomic.LoadInt32(&sm.shuttingDown) == 1
}

func (sm *ShutdownManager) IncrementInflight() {
	atomic.AddInt64(&sm.inflightCount, 1)
}

func (sm *ShutdownManager) DecrementInflight() {
	atomic.AddInt64(&sm.inflightCount, -1)
}

func (sm *ShutdownManager) WaitForDrain(timeout time.Duration) bool {
	deadline := time.After(timeout)
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()

	for {
		if atomic.LoadInt64(&sm.inflightCount) == 0 {
			return true
		}

		select {
		case <-deadline:
			return false
		case <-ticker.C:
		}
	}
}

func (sm *ShutdownManager) HealthCheckHandler(w http.ResponseWriter, r *http.Request) {
	if sm.IsShuttingDown() {
		w.WriteHeader(http.StatusServiceUnavailable)
		w.Write([]byte("shutting down"))
		return
	}

	w.WriteHeader(http.StatusOK)
	w.Write([]byte("healthy"))
}

func (sm *ShutdownManager) WrapHandler(handler http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if sm.IsShuttingDown() {
			w.WriteHeader(http.StatusServiceUnavailable)
			return
		}

		sm.IncrementInflight()
		defer sm.DecrementInflight()

		handler.ServeHTTP(w, r)
	})
}
```

When the shutdown sequence begins, the manager immediately marks itself as shutting down, causing health checks to fail. The load balancer detects this and stops sending new traffic. Meanwhile, the wrapper middleware tracks in-flight requests. The shutdown coordinator waits for the in-flight count to reach zero before terminating the process, ensuring graceful connection draining without data loss or incomplete responses.

This architecture enables zero-downtime rolling deployments: old instances are gradually drained as health checks fail, new instances are brought online and begin passing health checks, and traffic seamlessly shifts from the old fleet to the new without dropping requests or causing client-visible errors. The health checking system, properly tuned and deeply integrated with application lifecycle management, transforms from a simple liveness probe into a sophisticated orchestration mechanism enabling continuous deployment at scale.
