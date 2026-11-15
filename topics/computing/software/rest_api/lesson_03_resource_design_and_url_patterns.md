# Lesson 3: Resource Modeling, URL Design, and API Versioning

## 1. First-Principles Intuition & Invariants

The fundamental error most engineers make when designing a REST API is treating it as a remote procedure call system with a prettier URL. They name endpoints after verbs — `/getUser`, `/createOrder`, `/deleteAccount` — and reach for HTTP as nothing more than a transport envelope. What they produce compiles and ships, but it cannot be reasoned about, cached, or evolved without coordination across every consumer. The root cause is a failure to internalize what REST actually models: not *operations*, but *resources*.

Roy Fielding's 2000 dissertation introduced REST as an architectural style for distributed hypermedia systems, and the word "hypermedia" is load-bearing. The web's extraordinary longevity and scalability emerge from one foundational invariant: a resource has an identity that is stable across time and independent of the representation you retrieve. A URI is not a function call; it is an address for a thing. The HTTP method tells you what to do with the thing, and the response body is one possible representation of its current state. When you conflate the identifier with the action, you lose the ability to cache, to log, to build intermediaries, and to evolve the action semantics independently of the resource's identity.

This seems abstract until you feel the operational weight of a system that violated it. Consider an API where `/api/processPayment` accepts a POST, and six months later the team needs to expose payment status for a monitoring dashboard. Because the resource was never modeled — only the operation — there is no stable address for a payment entity. The team invents `/api/getPaymentStatus?transactionId=xyz`, then later `/api/payments/lookup`, then a webhook endpoint, all representing the same underlying state machine from different angles, none of them composable. Clients accumulate knowledge of all three paths. The API becomes an archaeological site.

The corrective discipline is to begin every API design session not with the question "what operations do we need?" but with the question "what entities does this system manage, and what are the meaningful relationships between them?" A payment is a resource. It has an identity (`/payments/{id}`), a lifecycle (created, authorized, captured, refunded, disputed), and a representation in JSON or some other format. Every subsequent operation — capture, refund, dispute — is modeled as either a mutation of that resource's state via PUT/PATCH or as the creation of a subordinate resource that represents the transition itself.

This resource-first thinking also forces you to confront *granularity* as a design decision with real tradeoffs. A resource that is too coarse — `/users/{id}` returning the user's profile, all their orders, all their payment methods, all their preferences in one payload — creates a chatty contract where every consumer gets data it doesn't need and where any change to any sub-entity breaks the entire response shape. A resource that is too fine — a separate endpoint for each field on a user record — creates an N+1 request problem in clients and defeats HTTP connection reuse. The pragmatic resolution, well-established in production API design, is to model top-level resources at the entity boundary of your domain model, expose sub-resources for aggregates that have independent identity and lifecycle, and use sparse fieldsets or projections at the HTTP layer to let clients declare what they need without multiplying endpoint surface area.

The invariants that follow from resource modeling are three. First, the resource identifier must be stable: once you assign `/orders/ord_8f3a` to an order, that path must resolve to that order for the lifetime of the system, regardless of what state the order is in. Deleting an order does not free its identifier for reuse; it means GET returns 404 or 410 (Gone), and DELETE is idempotent. Second, the HTTP method must carry its full semantic weight: GET is safe and idempotent, PUT is idempotent, POST is neither, PATCH is neither but signals partial intent. Violating these semantics breaks caching infrastructure, retry logic, and every proxy in the path. Third, representations are not resources: the resource `/users/42` might be represented as `application/json` today and `application/vnd.company.user+json;version=2` tomorrow. Content negotiation is the mechanism by which the protocol separates identity from representation, and exploiting it cleanly is what makes versioning tractable.

## 2. Core Architecture & Mechanics

### URL Hierarchy and the Grammar of Paths

A well-formed URL in a REST API is a sentence in a grammar. The path segments encode the resource hierarchy, and that hierarchy should directly reflect the ownership and containment relationships in your domain model. The basic production rule is:

```
/{collection}/{resource-id}/{sub-collection}/{sub-resource-id}
```

A collection is a plural noun representing a set of homogenous resources. A resource identifier follows, selecting a specific member. If that member owns a collection of subordinate resources with independent identity and lifecycle, a second collection segment follows. This grammar produces paths that are navigable by inspection:

```
GET    /orders                          → list all orders
POST   /orders                          → create a new order
GET    /orders/ord_8f3a                 → retrieve order ord_8f3a
PATCH  /orders/ord_8f3a                 → partially update order ord_8f3a
DELETE /orders/ord_8f3a                 → cancel or archive order ord_8f3a
GET    /orders/ord_8f3a/items           → list line items in this order
POST   /orders/ord_8f3a/items           → add a line item to this order
DELETE /orders/ord_8f3a/items/item_002  → remove a specific line item
```

The nesting depth should not exceed two levels in the common case. When you find yourself writing `/users/{uid}/organizations/{oid}/teams/{tid}/members/{mid}`, you have usually conflated the URL with a database join query. The team member resource has an identity that is sufficiently independent to live at `/team-members/{mid}`, with the team and organization identifiers carried as fields in the representation rather than encoded in every URL that addresses the resource.

Relationships that are many-to-many, or that represent an association as a first-class entity with its own state, deserve their own top-level collection. An enrollment in a course is not simply a link between a user and a course; it carries enrollment date, payment status, progress, and certificate eligibility. It belongs at `/enrollments/{id}`, with `userId` and `courseId` as fields. Forcing it into `/users/{uid}/courses/{cid}` makes it impossible to address the enrollment's own lifecycle and forces every mutation to know both IDs from the outer scope.

The following diagram captures the resource graph for an e-commerce domain and shows how the URL hierarchy maps to ownership, with cross-cutting relationships handled as top-level resources rather than nested paths:

```
┌─────────────────────────────────────────────────────────────────┐
│                      API Resource Graph                         │
├──────────────────────┬──────────────────────────────────────────┤
│  Top-Level Resources │  Subordinate Resources                   │
├──────────────────────┼──────────────────────────────────────────┤
│  /users              │  /users/{id}/addresses                   │
│  /products           │  /products/{id}/variants                 │
│  /orders             │  /orders/{id}/items                      │
│  /payments           │  (payments stand alone; ref order_id)    │
│  /shipments          │  /shipments/{id}/events                  │
│  /reviews            │  (reviews ref product_id + user_id)      │
└──────────────────────┴──────────────────────────────────────────┘

Relationship edges (not encoded in URL depth):
  payment ──→ order         (payment.order_id)
  review  ──→ product       (review.product_id)
  review  ──→ user          (review.user_id)
  shipment──→ order         (shipment.order_id)
```

### Path Parameters Versus Query Parameters

The distinction between path parameters and query parameters is not stylistic — it reflects a semantic contract about identity versus refinement. A path parameter selects a resource; removing it changes what resource you are addressing. A query parameter modifies how you retrieve or filter a collection without changing the collection's identity.

This means that any attribute that participates in the resource's identity belongs in the path. Locale, currency, and format do not participate in the identity of an order; they affect how the order's representation is rendered. `Accept-Language: fr-FR` in a header, or `?locale=fr-FR` as a query parameter, is correct. `/orders/fr-FR/ord_8f3a` is a modeling error that creates phantom resource identities and breaks cache keys.

Filtering a collection is always a query parameter concern. A client asking for all orders placed by a specific user, in a specific status window, is not addressing a different collection; it is asking for a constrained view of the same `/orders` collection:

```
GET /orders?user_id=usr_42&status=shipped&created_after=2024-01-01
```

Sorting and field projection follow the same rule:

```
GET /orders?sort=created_at:desc&fields=id,status,total_amount
```

Pagination belongs in query parameters as well, but the choice of pagination *mechanism* has significant performance consequences at scale.

### Pagination Strategies and Their Tradeoffs

Offset-based pagination is the most common and the most dangerous at scale. `GET /orders?page=5&per_page=20` instructs the database to skip 100 rows and return the next 20. On a table of 10 million rows, that `OFFSET 100` is free; that `OFFSET 9,999,980` requires the database to scan and discard nearly 10 million rows before returning your 20. The query time grows linearly with the offset, and because clients can request arbitrary offsets concurrently, a fleet of clients deep-paginating a large collection can saturate your database under what appears to be normal traffic.

Cursor-based pagination resolves this by encoding position rather than row count. The server returns a cursor — typically an opaque base64-encoded token wrapping the last seen primary key or a composite sort key — and the client passes it back on the next request:

```
GET /orders?after=eyJpZCI6Im9yZF84ZjNhIn0=&limit=20
```

On the server side, this translates to a range predicate that the database can satisfy with an index seek:

```sql
SELECT * FROM orders
WHERE id > 'ord_8f3a'
ORDER BY id ASC
LIMIT 20;
```

This query has O(log N) seek cost regardless of how deep into the collection the client is. The tradeoff is that cursor-based pagination does not support random access — you cannot jump to page 47 — but that is rarely a legitimate use case in production systems. Any UI that exposes a "jump to page N" control on a collection of millions of records is itself a UX failure waiting to become a database incident.

Keyset pagination is the generalized term for cursor-based approaches when sorting by composite keys. When the collection is sorted by `(created_at, id)`, the cursor encodes both values, and the range predicate becomes:

```sql
SELECT * FROM orders
WHERE (created_at, id) > ('2024-06-01T12:00:00Z', 'ord_8f3a')
ORDER BY created_at ASC, id ASC
LIMIT 20;
```

The API response envelope should carry navigation links in a `links` object following RFC 8288 (Web Linking), making the pagination contract self-describing:

```json
{
  "data": [ /* ... 20 order objects ... */ ],
  "pagination": {
    "limit": 20,
    "next_cursor": "eyJjcmVhdGVkX2F0IjoiMjAyNC0wNi0wMVQxMjowMTowMFoiLCJpZCI6Im9yZF85YTJiIn0=",
    "has_more": true
  },
  "links": {
    "next": "https://api.example.com/orders?after=eyJjcmVhdGVkX2F0IjoiMjAyNC0wNi0wMVQxMjowMTowMFoiLCJpZCI6Im9yZF85YTJiIn0=&limit=20"
  }
}
```

### Versioning Architectures

API versioning is ultimately a problem of change management under a contract, and there are three structural approaches to solving it, each with different operational profiles.

URI path versioning embeds the version in the path: `/v1/orders`, `/v2/orders`. This approach is explicit, trivially debuggable in access logs, and easy to route at the reverse-proxy layer. Its cost is that it treats the version as part of the resource identity, which Fielding would correctly identify as a modeling violation — the resource `/orders/ord_8f3a` is the same resource regardless of which representation version you request. URI versioning also makes it difficult for clients to adopt the new version incrementally per-resource; they must decide at the path prefix level.

Header versioning uses a custom request header (`API-Version: 2024-06-01`) or the `Accept` header with a versioned media type (`Accept: application/vnd.example.orders+json;version=2`). This keeps resource identifiers stable and allows per-request version negotiation, but it complicates caching: a proxy or CDN that does not vary its cache key on `API-Version` will serve wrong responses to clients on different versions. Correct implementation requires `Vary: API-Version` in every response, and debugging requires inspecting headers rather than just URLs.

Stripe's date-based versioning model deserves special attention because it represents a production-hardened solution at scale. Each API version corresponds to a calendar date string (`2024-11-01`). The client declares its version at account creation time, and the platform guarantees that client's response shapes and behavior are frozen at that date. When a breaking change ships, it ships behind a new date version. Clients upgrade by moving their version string forward and running their integration test suite. The server maintains a middleware chain of coercions that transforms new internal models into older representations for pinned clients — a unidirectional transformation pipeline rather than a fork of business logic. This eliminates the N×M explosion of maintaining full parallel implementations for every version combination, at the cost of building and testing that transformation layer carefully.

```
Client Request ──→ [Version Header: 2023-08-01]
                         │
                         ▼
           ┌─────────────────────────────┐
           │  Versioning Middleware       │
           │  Dispatch table:            │
           │  2023-08-01 → coerce_v3()   │
           │  2024-01-15 → coerce_v4()   │
           │  2024-11-01 → passthrough() │
           └──────────┬──────────────────┘
                      │
                      ▼
           ┌──────────────────────┐
           │  Current Business    │
           │  Logic & Data Model  │
           └──────────┬───────────┘
                      │
                      ▼
           ┌──────────────────────────────┐
           │  Response Coercion Layer     │
           │  newest → 2024-11-01 (noop)  │
           │  newest → 2024-01-15 (xform) │
           │  newest → 2023-08-01 (xform) │
           └──────────────────────────────┘
```

The following complete Go snippet implements a minimal version coercion middleware that demonstrates the dispatch pattern. It compiles against the standard library with no external dependencies:

```go
package versioning

import (
	"encoding/json"
	"net/http"
	"sort"
	"time"
)

// Version represents an API version as a calendar date, following
// Stripe's model. Comparisons use standard time ordering.
type Version time.Time

func ParseVersion(s string) (Version, error) {
	t, err := time.Parse("2006-01-02", s)
	return Version(t), err
}

func (v Version) String() string {
	return time.Time(v).Format("2006-01-02")
}

func (v Version) Before(other Version) bool {
	return time.Time(v).Before(time.Time(other))
}

// Coercion is a function that transforms a response body map in-place
// to conform to a specific version's contract.
type Coercion func(body map[string]any)

// VersionedCoercion pairs a version boundary with the transformation
// that must be applied to downgrade a response to that version.
type VersionedCoercion struct {
	Since    Version
	Coerce   Coercion
}

// CoercionChain holds an ordered list of version coercions from newest
// to oldest. The chain is applied in reverse for older clients.
type CoercionChain struct {
	coercions []VersionedCoercion
}

// NewCoercionChain builds a chain, sorting coercions from newest to oldest.
func NewCoercionChain(entries []VersionedCoercion) *CoercionChain {
	sorted := make([]VersionedCoercion, len(entries))
	copy(sorted, entries)
	sort.Slice(sorted, func(i, j int) bool {
		return sorted[j].Since.Before(sorted[i].Since) // descending
	})
	return &CoercionChain{coercions: sorted}
}

// Apply transforms body for a client pinned to requestedVersion by running
// all coercions introduced after that version.
func (c *CoercionChain) Apply(requestedVersion Version, body map[string]any) {
	for _, vc := range c.coercions {
		if !requestedVersion.Before(vc.Since) {
			// Client's version is at or newer than this coercion; stop.
			break
		}
		vc.Coerce(body)
	}
}

// VersionMiddleware injects the requested API version into the request
// context and coerces response payloads for older clients.
func VersionMiddleware(chain *CoercionChain, currentVersion Version, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		versionStr := r.Header.Get("API-Version")
		if versionStr == "" {
			versionStr = currentVersion.String()
		}

		requested, err := ParseVersion(versionStr)
		if err != nil {
			http.Error(w, `{"error":"invalid API-Version header"}`, http.StatusBadRequest)
			return
		}

		// Wrap the ResponseWriter to intercept the body before it is flushed.
		crw := &capturingResponseWriter{ResponseWriter: w, header: http.Header{}}
		next.ServeHTTP(crw, r)

		// Only coerce JSON responses.
		ct := crw.header.Get("Content-Type")
		if ct != "application/json" && ct != "" {
			for k, vs := range crw.header {
				for _, v := range vs {
					w.Header().Add(k, v)
				}
			}
			w.WriteHeader(crw.status)
			w.Write(crw.body)
			return
		}

		var payload map[string]any
		if err := json.Unmarshal(crw.body, &payload); err != nil {
			w.WriteHeader(crw.status)
			w.Write(crw.body)
			return
		}

		chain.Apply(requested, payload)

		coerced, _ := json.Marshal(payload)
		for k, vs := range crw.header {
			for _, v := range vs {
				w.Header().Add(k, v)
			}
		}
		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("API-Version", currentVersion.String())
		w.WriteHeader(crw.status)
		w.Write(coerced)
	})
}

type capturingResponseWriter struct {
	http.ResponseWriter
	header http.Header
	body   []byte
	status int
}

func (c *capturingResponseWriter) Header() http.Header {
	if c.header == nil {
		c.header = http.Header{}
	}
	return c.header
}

func (c *capturingResponseWriter) WriteHeader(status int) {
	c.status = status
}

func (c *capturingResponseWriter) Write(b []byte) (int, error) {
	c.body = append(c.body, b...)
	return len(b), nil
}
```

Using this middleware to register a breaking change — say, renaming `full_name` to `display_name` on user objects — looks like this:

```go
v20240101, _ := versioning.ParseVersion("2024-01-01")
v20231001, _ := versioning.ParseVersion("2023-10-01")
current, _   := versioning.ParseVersion("2024-06-01")

chain := versioning.NewCoercionChain([]versioning.VersionedCoercion{
    {
        Since: v20240101,
        // Clients pinned before 2024-01-01 expect "full_name".
        Coerce: func(body map[string]any) {
            if dn, ok := body["display_name"]; ok {
                body["full_name"] = dn
                delete(body, "display_name")
            }
        },
    },
    {
        Since: v20231001,
        // Clients pinned before 2023-10-01 expect address as a string
        // rather than a structured object.
        Coerce: func(body map[string]any) {
            if addr, ok := body["address"].(map[string]any); ok {
                body["address"] = addr["line1"].(string) + ", " + addr["city"].(string)
            }
        },
    },
})

mux := http.NewServeMux()
mux.HandleFunc("/users/{id}", userHandler)

http.ListenAndServe(":8080", versioning.VersionMiddleware(chain, current, mux))
```

Each coercion is a pure function over the response body map. The chain accumulates them in version order and applies only the ones that postdate the client's pinned version. Adding a new breaking change means appending one entry to the slice — the existing coercions are untouched, and no business logic forks.

## 3. High-Performance Optimization & Failure Modes

### Caching Coherence Under Versioned Resources

The most underappreciated performance failure mode in versioned REST APIs is cache poisoning at the CDN or reverse-proxy layer. When you introduce header-based versioning and forget to declare `Vary: API-Version` in responses, a CDN caches the first response it sees for `/users/42` — say, a v2024-01-01 representation — and serves it to all subsequent clients, including those pinned to `2023-10-01` who expect a structurally different body. The resulting bugs are intermittent, appear only on cache-hit code paths, and are extraordinarily difficult to reproduce locally.

The correct response headers for a versioned API serving `gzip`-compressed JSON are:

```
Content-Type: application/json
Content-Encoding: gzip
Vary: Accept-Encoding, API-Version, Accept
Cache-Control: public, max-age=60, stale-while-revalidate=300
API-Version: 2024-06-01
```

The `Vary` directive tells every intermediary — Cloudflare, Fastly, nginx, Varnish — that the response body is a function of the named request headers. A cache must store separate entries for each distinct combination of `Accept-Encoding`, `API-Version`, and `Accept` values. The combinatorial explosion is real but bounded: in practice, a mature API serves two or three live versions and two content types, producing at most six cache buckets per resource URL rather than one.

For ETag-based conditional GET — the mechanism by which a client can ask "has this resource changed since I last fetched it?" — the ETag must encode the version as part of its opaque identifier. If your ETag is simply a hash of the resource's database row, two clients on different API versions will receive responses with matching ETags but different body shapes. A subsequent conditional GET with `If-None-Match` from a v1 client could be satisfied by a v2-keyed cache entry. The correct ETag is a hash of the tuple `(resource_id, resource_version, api_version)`:

```go
func generateETag(resourceID string, resourceUpdatedAt time.Time, apiVersion string) string {
    h := sha256.New()
    fmt.Fprintf(h, "%s|%d|%s", resourceID, resourceUpdatedAt.UnixNano(), apiVersion)
    return fmt.Sprintf(`"%x"`, h.Sum(nil)[:16])
}
```

### Backward Compatibility Contracts and the Tolerant Reader Pattern

The robustness principle — Postel's law — states that an implementation should be liberal in what it accepts and conservative in what it sends. Applied to REST API evolution, this translates to the Tolerant Reader pattern: clients must be written to ignore unknown fields in responses, to treat missing optional fields as absent rather than erroneous, and to handle new enum values in discriminated unions gracefully rather than throwing a deserialization exception.

The practical implication is that you should enforce Tolerant Reader behavior in client code review and in your SDK generation pipeline. A client SDK generated by OpenAPI tooling that maps every response field to a strict struct and throws an `UnknownFieldException` on new JSON keys will break every time you add an additive change — adding a field, adding a new enum value — that you have explicitly promised is non-breaking. Additive changes are only non-breaking if clients tolerate them.

On the server side, backward compatibility demands a precise taxonomy of change types. Additive changes — new optional fields, new endpoints, new query parameters, new enum values — are safe. Renamings, field removals, type changes from string to integer, and semantic changes to existing behavior are breaking. This taxonomy must be encoded in your API change review process, not left to individual engineers to reason about case by case. A lightweight automation approach is to diff your OpenAPI schema between releases and classify each change using a tool like `openapi-diff` or `oasdiff`, which can be integrated into CI to gate merges on breaking-change classifications:

```bash
# Install oasdiff (single binary, no runtime dependency)
go install github.com/tufin/oasdiff@latest

# Compare the base branch schema against the current branch
oasdiff breaking \
  https://raw.githubusercontent.com/example/api/main/openapi.yaml \
  ./openapi.yaml \
  --format text

# In CI, fail the build if breaking changes are detected without a version bump
oasdiff breaking \
  schemas/openapi-main.yaml \
  schemas/openapi-pr.yaml \
  --fail-on ERR
```

The `--fail-on ERR` flag causes the command to exit with a non-zero status code when it detects breaking changes classified as errors (removals, type changes) but not for warnings (additive changes, deprecations). This integrates cleanly into a GitHub Actions or GitLab CI step as a merge gate.

### Filtering at Scale: Push the Predicate, Not the Data

A common failure mode in list endpoints is implementing server-side filtering as a post-database application-layer filter. The endpoint fetches a large result set, materializes it into objects, then discards objects that don't match query parameters. This pattern emerges when engineers prototype against an ORM and never revisit performance as the dataset grows. At 100 rows it is invisible; at 10 million rows it OOMs the service.

The correct architecture pushes the predicate into the storage layer. Every query parameter that participates in filtering must map to a database predicate, and every such predicate must be backed by an appropriate index. When you expose `GET /orders?user_id=X&status=Y&created_after=Z`, the query plan must use a composite index on `(user_id, status, created_at)`, not a full table scan filtered in Go or Java. This requires deliberate index design to precede — not follow — API surface design.

Compound filter expressions, as exposed by APIs like Stripe's or Algolia's (`gte`, `lte`, `in`, `not` operators per field), require more sophisticated query builder logic to prevent SQL injection while supporting arbitrary filter combinations. The standard approach is a whitelist of filterable fields mapped to typed predicates that are parameterized but structurally composed:

```go
type FilterField string

const (
    FilterStatus    FilterField = "status"
    FilterCreatedAt FilterField = "created_at"
    FilterUserID    FilterField = "user_id"
    FilterTotal     FilterField = "total_amount"
)

type Operator string

const (
    OpEq  Operator = "eq"
    OpGte Operator = "gte"
    OpLte Operator = "lte"
    OpIn  Operator = "in"
)

type Filter struct {
    Field    FilterField
    Op       Operator
    Value    any
}

// BuildWhereClause constructs a parameterized WHERE clause from a slice
// of validated Filter structs. All field names are whitelisted; only
// values are interpolated as SQL parameters, never field names or operators.
func BuildWhereClause(filters []Filter) (string, []any) {
    allowed := map[FilterField]string{
        FilterStatus:    "status",
        FilterCreatedAt: "created_at",
        FilterUserID:    "user_id",
        FilterTotal:     "total_amount",
    }

    clauses := make([]string, 0, len(filters))
    args := make([]any, 0, len(filters))
    paramIdx := 1

    for _, f := range filters {
        col, ok := allowed[f.Field]
        if !ok {
            continue // silently skip unknown fields
        }

        switch f.Op {
        case OpEq:
            clauses = append(clauses, fmt.Sprintf("%s = $%d", col, paramIdx))
            args = append(args, f.Value)
            paramIdx++
        case OpGte:
            clauses = append(clauses, fmt.Sprintf("%s >= $%d", col, paramIdx))
            args = append(args, f.Value)
            paramIdx++
        case OpLte:
            clauses = append(clauses, fmt.Sprintf("%s <= $%d", col, paramIdx))
            args = append(args, f.Value)
            paramIdx++
        case OpIn:
            vals, ok := f.Value.([]any)
            if !ok || len(vals) == 0 {
                continue
            }
            placeholders := make([]string, len(vals))
            for i, v := range vals {
                placeholders[i] = fmt.Sprintf("$%d", paramIdx)
                args = append(args, v)
                paramIdx++
            }
            clauses = append(clauses, fmt.Sprintf("%s IN (%s)", col, strings.Join(placeholders, ", ")))
        }
    }

    if len(clauses) == 0 {
        return "1=1", nil
    }
    return strings.Join(clauses, " AND "), args
}
```

Field names are never interpolated — they are resolved through a whitelist map to hardcoded column name strings. Only values flow through `$N` parameter placeholders. The filter structs themselves are populated from validated query parameter parsing, not from raw user input. This pattern scales to arbitrary filter complexity without opening SQL injection vectors.

### Deprecation Lifecycle and Sunset Headers

Removing a version cleanly requires a deprecation lifecycle that gives clients enough warning to migrate without requiring your team to maintain dead versions indefinitely. The HTTP `Sunset` header (RFC 8594) is the standard mechanism: it carries an HTTP-date value indicating when the resource or version will cease to be available.

A response from a deprecated API version should carry both the `Deprecation` and `Sunset` headers alongside a `Link` header pointing to the migration guide:

```
Deprecation: Sat, 01 Jun 2024 00:00:00 GMT
Sunset: Mon, 01 Dec 2025 00:00:00 GMT
Link: <https://docs.example.com/api/migration/v3>; rel="deprecation"
API-Version: 2023-10-01
```

This metadata is machine-readable. A well-instrumented API client SDK can log a warning on every call that returns a `Deprecation` header, surfacing the migration deadline to the engineer at the point of consumption rather than in a newsletter they won't read. Stripe's SDKs implement exactly this pattern: they inspect `Stripe-Version` and `Deprecation` on every response and emit a structured log warning that includes the version string, the sunset date, and a documentation URL. At scale, this reduces the support burden from "why did my integration break in December?" to a migration logged months in advance in the engineer's own application logs.

The final invariant of API versioning is organizational: a version is a promise, and promises have costs. Every version you create is a tax on your team's attention for its entire supported lifetime. The engineering discipline of resource modeling, clean URL grammar, and backward-compatible additive evolution exists precisely to minimize the number of versions you must cut by maximizing how much you can safely add without breaking what already works. The teams that version least frequently are not the ones who change least; they are the ones who modeled their resources most carefully at the start and built their change review process to defend the additive boundary.
