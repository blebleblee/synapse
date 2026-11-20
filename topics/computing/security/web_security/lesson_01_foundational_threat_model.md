# Lesson 1: Foundational Threat Model

## 1. First-Principles Intuition & Invariants

The web was not designed to be secure. It was designed to share documents. Every security primitive layered onto HTTP since 1991 — TLS, cookies, CORS, CSP, SameSite, HSTS — is a retrofitted constraint applied to a protocol whose original trust model was closer to a university bulletin board than a global financial and identity infrastructure. Understanding web security at the level this curriculum demands means first internalizing that design heritage as the root cause of an entire class of structural vulnerabilities that no patch, header, or WAF rule can fully eliminate.

For practitioners with backgrounds in hardware security or embedded systems, the most useful reframe is to treat the web stack as a distributed state machine operating across an adversarially-controlled physical network, with no equivalent of the hardware root of trust you would find in a TPM, ARM TrustZone, or secure enclave. In embedded contexts, your trust boundary often coincides with physical silicon. In web security, trust boundaries are defined by protocol agreements between software components that have never met and cannot cryptographically verify each other's internal state. That gap is where every interesting attack lives.

The CIA triad — Confidentiality, Integrity, Availability — maps onto the web stack in ways that are more mechanically specific than the generic formulations found in compliance frameworks. Confidentiality in a web context is primarily a question of what data crosses which trust boundary without authorization. This covers HTTP response bodies delivered to the wrong origin via CORS misconfiguration, session tokens leaked through Referer headers, and plaintext credential transmission over non-TLS connections. Integrity is a question of whether a resource arrived from the claimed source unmodified and whether server-side state transitions were authorized by the legitimate principal. Cross-Site Request Forgery attacks are an integrity violation at the state-transition layer: the server receives a valid authenticated request and executes a state change that the user did not sanction. Availability, in its web-specific form, extends beyond volumetric DDoS into application-layer resource exhaustion — a single unauthenticated API endpoint that triggers an expensive database query or a regex engine subject to catastrophic backtracking can be weaponized to degrade a service using request rates well within normal traffic envelopes.

Threat actor capability modeling is the first discipline that separates practitioners from theorists. The web threat landscape is not monolithic, and conflating a nation-state APT with an opportunistic botnet scanner leads to defense architectures that spend resources against phantom adversaries while ignoring the actual threats in the access logs. At the lowest capability tier, you have automated scanners running tools like Nuclei, Nikto, and SQLMap against broad IP ranges using published vulnerability templates. These actors are not targeting you specifically; they are harvesting whatever vulnerable surface they can reach at scale. At the intermediate tier, you have financially motivated actors — ransomware operators, card skimmers, credential stuffers — who possess moderate tradecraft: the ability to modify public exploits, bypass naive rate limiting with distributed request infrastructure, and chain low-severity misconfigurations into critical impact. At the highest tier, you have state-sponsored actors and elite criminal organizations operating with zero-day capabilities, long dwell times, and the patience to map an organization's entire attack surface before executing a single exploitative request.

The invariant that governs all three tiers is this: attackers operate on the boundary between what a system is designed to do and what it can be made to do. Every security control is ultimately a constraint on the system's reachable state space. Attacking means finding a path through that state space that the designers did not model and the defenders did not instrument.

## 2. Core Architecture & Mechanics

### The HTTP Request-Response as an Attack Surface Topology

A single HTTP request traversing a modern web application is not a simple two-party transaction. It passes through a layered architecture in which each component boundary represents a distinct trust decision — and a distinct attack surface.

```text
Client Browser / API Consumer
         │
         │  (TLS, DNS, TCP/IP)
         ▼
   CDN / Reverse Proxy          ← Layer 7 filtering, TLS termination
   (Cloudflare, Nginx, HAProxy)
         │
         │  (HTTP/1.1, HTTP/2, HTTP/3)
         ▼
   API Gateway / Load Balancer  ← AuthN, rate limiting, routing
         │
         │  (Internal HTTP, gRPC)
         ▼
   Application Server           ← Business logic, session state
         │
         ├── Cache Layer         ← Redis, Memcached — deserialization risk
         │
         └── Database Layer      ← SQL/NoSQL injection surface
                │
                └── Object Store / Filesystem
```

Each vertical arrow in this diagram is a trust boundary crossing. At each crossing, the receiving component must decide whether to trust the data arriving from upstream. The catastrophic error — repeated throughout web application history — is trusting data that has transited a component the application does not control. HTTP headers forwarded by a reverse proxy (`X-Forwarded-For`, `X-Real-IP`) carry attacker-controlled values. Query parameters, path segments, JSON body fields, and multipart form data are all attacker-controlled by definition. The application server's job is to validate these values against the system's intended state space before acting on them. Failure to do so completely, at every trust boundary, is the root cause of injection, deserialization, SSRF, and prototype pollution vulnerabilities.

### Origin, Site, and the Browser's Security Primitive

The browser's same-origin policy (SOP) is the foundational integrity control for web content, and misunderstanding its precise semantics is responsible for an enormous class of real-world vulnerabilities. An origin is defined as the tuple `(scheme, host, port)`. The SOP prevents a document loaded from `https://bank.example.com:443` from reading the response of a fetch request to `https://api.bank.example.com:443` — because despite sharing a registrable domain, the hostnames differ and the origins are distinct.

CORS (Cross-Origin Resource Sharing) is the escape valve on the SOP. When a server responds with `Access-Control-Allow-Origin: *`, it instructs the browser to permit any origin to read the response body. When it responds with `Access-Control-Allow-Origin: https://trusted.example.com`, it restricts that permission to one origin. The critical mechanical detail that practitioners must internalize is that CORS controls only what the browser will expose to JavaScript code on the requesting page. It does not prevent the request from being sent. A CORS misconfiguration does not enable an attacker to bypass authentication — it enables an attacker to read data from an authenticated session, which requires that the victim's browser makes the request with their credentials attached. This is precisely why `Access-Control-Allow-Credentials: true` combined with a dynamically-reflected origin value is a critical severity finding, not a low-severity misconfiguration.

The concept of "site" — used in SameSite cookie policy and security literature — has a subtly different definition than "origin." A site is defined as the registrable domain (eTLD+1) plus scheme. Under this definition, `https://app.example.com` and `https://api.example.com` are same-site but cross-origin. SameSite cookie restrictions operate at the site boundary, which means a subdomain takeover attack can violate SameSite protections while remaining cross-origin.

### Session State as a Cryptographic Assertion

An HTTP session token is, mechanically, a capability: possession of the token grants the bearer access to the associated server-side session state. The security of that capability rests on three properties: it must be unpredictable (sufficient entropy), it must be transmitted only over TLS, and it must be inaccessible to attacker-controlled JavaScript running on the same origin. The `HttpOnly` flag removes the cookie from the `document.cookie` API, preventing JavaScript access. The `Secure` flag prevents transmission over plaintext HTTP. The `SameSite=Strict` or `SameSite=Lax` attribute prevents the browser from attaching the cookie to cross-site requests, defeating the browser-side CSRF attack model.

The state machine for session lifecycle looks like this:

```text
[Unauthenticated]
      │
      │  POST /login (credentials validated)
      ▼
[Session Created]  ──── token stored in HttpOnly Secure SameSite cookie
      │
      │  Subsequent requests with token attached
      ▼
[Authenticated Session]
      │
      ├─── Token leaked via XSS → [Session Hijack]
      ├─── Token sent cross-site (SameSite=None) → [CSRF possible]
      ├─── Token transmitted over HTTP → [Network interception]
      └─── POST /logout or expiry
           │
           ▼
      [Session Invalidated]
```

A session that is never invalidated server-side — only by clearing the client-side cookie — is vulnerable to replay: an attacker who captures a token value from a log, a Referer header, or a network capture can replay it indefinitely. Server-side session invalidation, not client-side cookie deletion, is the correct termination mechanism.

### Attack Surface Taxonomy

Web attack surfaces decompose into four categories based on where the attacker's input is interpreted. This decomposition is mechanically important because it determines the appropriate validation and encoding strategy.

The first category is **server-side code execution**, where attacker-controlled data is interpreted as code or a code path selector by the server. SQL injection, OS command injection, server-side template injection, and XML external entity injection all fall here. The common invariant is that a parser on the server-side fails to maintain a strict separation between the data plane and the control plane. A SQL query is a control-plane artifact; user input is a data-plane artifact. Parameterized queries are the mechanically correct fix because they enforce this boundary at the database protocol level, not through string sanitization.

The second category is **client-side code execution**, where attacker-controlled data is interpreted as code by the victim's browser. Cross-site scripting is the canonical instance. The injection point can be the HTML document body (reflected or stored XSS), a JavaScript execution context (DOM XSS where `innerHTML`, `eval`, or `document.write` consume attacker data), or a subresource import chain (prototype pollution affecting library behavior). The severity is not "script injection" in the abstract — it is full compromise of the victim's session within the application's origin, equivalent in impact to stealing the session token.

The third category is **access control bypass**, where the application fails to verify that the authenticated principal is authorized to perform the requested operation on the requested resource. Broken Object Level Authorization (BOLA, also called IDOR) is the web's most prevalent critical vulnerability class and the most commonly underestimated by practitioners from non-web backgrounds. The mechanic is straightforward: an endpoint like `GET /api/invoices/48291` returns the invoice object identified by that integer. If the server validates that the requester is authenticated but does not validate that they are authorized to access invoice 48291 specifically, any authenticated user can enumerate the identifier space and retrieve arbitrary records. BOLA is not a cryptographic failure or a protocol flaw — it is a missing authorization check in application logic, which makes it invisible to network-layer security controls and hard to detect without semantic understanding of the application's data model.

The fourth category is **server-side request forgery (SSRF)**, where the server is induced to make a network request on behalf of the attacker to a destination the attacker specifies. Cloud-native architectures make SSRF critically dangerous because the internal network typically exposes the instance metadata service (AWS IMDSv1 at `169.254.169.254`, GCP at `metadata.google.internal`) without authentication. An SSRF vulnerability that can reach the metadata service can exfiltrate IAM credentials, enabling privilege escalation from web application compromise to cloud control plane access — a trust boundary crossing that spans from HTTP application logic all the way to infrastructure identity.

## 3. High-Performance Optimization & Failure Modes

### Building a Threat Model: Practical Methodology

A threat model is not a document — it is a continuous analytical process applied to a specific system at a specific moment in its evolution. The methodology used in production security engineering combines data flow diagramming with explicit trust boundary enumeration and attack tree construction. The process for a web application proceeds in three phases.

In the first phase, you produce a Data Flow Diagram (DFD) that is mechanically derived from the actual codebase and infrastructure configuration, not from an architect's memory. For each external-facing endpoint, trace the data from ingress through every transformation, storage operation, and downstream service call to its final disposition. This trace reveals implicit trust boundaries — cases where data received from one tier is forwarded to another tier without re-validation — and surfaces the full set of data stores that an attacker who compromises the application tier can reach.

In the second phase, you enumerate attack surfaces against the DFD using STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) as a systematic prompt, not as a checklist. STRIDE is valuable here not as a classification taxonomy but as a forcing function for asking mechanically specific questions: "Can an attacker present false identity claims to this component?" (Spoofing), "Can an attacker modify data in transit between these two components?" (Tampering), "Can an attacker cause this component to execute this operation without producing an audit record?" (Repudiation).

In the third phase, you build attack trees for the high-severity findings, rooting each tree at the security impact (e.g., "attacker reads another user's payment data") and decomposing down through the prerequisite conditions and attacker capabilities. This phase is where capability modeling becomes decisive: an attack path that requires a nation-state zero-day at every node deserves a different remediation priority than one that requires a nuclei template and an unrotated API key.

### Instrumentation: Seeing the Attack Surface From the Outside

Before evaluating any specific vulnerability class, practitioners must establish the same external visibility that an attacker has. For a web application, this means passive and active reconnaissance against the HTTP attack surface.

The following sequence establishes baseline external visibility using tools native to the offensive web security discipline.

**Enumerate subdomains and certificate transparency logs:**

```bash
# Passive subdomain enumeration via certificate transparency
subfinder -d target.example.com -all -o subdomains.txt

# Corroborate with crt.sh directly
curl -s "https://crt.sh/?q=%.target.example.com&output=json" \
  | jq -r '.[].name_value' \
  | sort -u
```

**Probe HTTP surface and extract response fingerprints:**

```bash
# Resolve live hosts and collect HTTP response metadata
httpx -l subdomains.txt \
  -status-code \
  -title \
  -tech-detect \
  -content-length \
  -follow-redirects \
  -o live_hosts.json \
  -json

# Extract server headers for fingerprinting
httpx -l subdomains.txt \
  -include-response-header \
  -silent \
  | grep -i "server:\|x-powered-by:\|x-aspnet"
```

**Extract endpoints from JavaScript bundles:**

```bash
# Pull all script src values from live hosts
katana -list live_hosts.json \
  -js-crawl \
  -depth 3 \
  -concurrency 20 \
  -o endpoints.txt

# Extract API paths and interesting strings from JS
grep -oP '["'"'"'][/][a-zA-Z0-9_/\-\.]+["'"'"']' endpoints.txt \
  | sort -u \
  | grep -v "node_modules"
```

**Probe CORS policy on discovered API endpoints:**

```bash
# Test for origin reflection (critical CORS misconfiguration)
curl -sI \
  -H "Origin: https://attacker.example.com" \
  -H "Cookie: session=YOUR_VALID_SESSION" \
  "https://api.target.example.com/v1/user/profile" \
  | grep -i "access-control"

# Wildcard with credentials — look for this combination
# Access-Control-Allow-Origin: *
# Access-Control-Allow-Credentials: true
# This combination is forbidden by spec but misconfigured servers emit it
```

**Verify security header posture:**

```bash
# Check for missing security headers across all live hosts
nuclei -l live_hosts.json \
  -t ~/nuclei-templates/misconfiguration/http-missing-security-headers.yaml \
  -severity medium,high,critical \
  -o header_findings.txt
```

### Failure Modes in Threat Modeling

The most common failure in threat modeling is scope creep in the wrong direction: teams model the threats they understand rather than the threats that exist. Backend engineers model injection vulnerabilities with precision while leaving access control entirely unexamined. Frontend engineers model XSS while ignoring SSRF paths through server-side rendering. Practitioners from hardware backgrounds often over-index on cryptographic failures — TLS configuration, certificate validation — while missing application-layer authorization gaps that require no cryptographic attack to exploit.

A second failure mode is treating the threat model as a point-in-time artifact. Web applications change. Endpoints are added by feature deployments, third-party integrations extend the trust boundary to vendors the security team has never reviewed, and infrastructure migrations introduce new metadata service exposure. A threat model that is not version-controlled and updated against changelogs will diverge from the actual attack surface within weeks of a medium-velocity engineering team's normal output.

The third failure mode is the absence of an adversarial capability threshold in the threat model. A control that defeats a scanner but not a human attacker is not a security control — it is friction. If your CSRF protection is a custom header that any attacker with browser developer tools can observe and replay, the protection exists in the threat model but not in the actual threat landscape. Every control must be evaluated against the question: "What capability level does defeating this require, and is that capability above or below the realistic threat actor's baseline?"

The foundational invariant that carries forward through every subsequent lesson in this curriculum is this: web security is a problem of trust boundary enforcement across a system where every component, every protocol, and every piece of data was designed with a less adversarial world in mind. The practitioner's job is to find every point where the system's actual behavior diverges from its intended authorization model — and to do so before an attacker does.
