# Lesson 5: Identity Security

## 1. First-Principles Intuition & Invariants

Identity security in Azure represents a fundamental shift from perimeter-based network defenses to a cryptographically verifiable, stateless authorization model rooted in distributed token validation. At its core, Azure Active Directory (now Microsoft Entra ID, though we retain the Azure AD nomenclature for technical precision) implements a federated identity provider that decouples authentication state from resource authorization through standardized OAuth 2.0 and OpenID Connect (OIDC) protocols. This architecture enables zero-trust principles where every access request—whether originating from a virtual machine, containerized workload, developer laptop, or external service—must present cryptographically signed, time-bound credentials that encode both identity claims and fine-grained permissions.

The architecture resolves a classical distributed systems challenge: how to grant granular access to resources across organizational boundaries without sharing secrets, synchronizing password databases, or establishing point-to-point trust relationships. Traditional approaches required either replicating user directories to every resource domain or implementing brittle LDAP federation schemes with bidirectional trust chains. Azure AD federation instead leverages public-key cryptography to establish transitive trust through signed tokens. A client authenticates once to the identity provider, receives a JSON Web Token (JWT) signed with the provider's private key, and presents this token to any Azure resource. The resource validates the token's signature against the provider's public keys (published at a well-known JWKS endpoint), verifies temporal validity, and extracts authorization claims—all without contacting the identity provider for each request. This stateless validation property enables horizontal scaling: resource servers can process millions of authorization decisions per second without distributed coordination or shared session state.

The security invariants governing this model derive from RFC 6749 (OAuth 2.0) and RFC 7519 (JWT) specifications, extended with Microsoft-specific claims and validation rules. Every access token carries an expiration timestamp (`exp` claim), a not-before timestamp (`nbf`), an issuer identifier (`iss`), and an audience field (`aud`) specifying the intended recipient resource. Critically, the token's cryptographic signature binds these claims to the issuer's identity through RSASSA-PKCS1-v1_5 or ECDSA algorithms with SHA-256 hashing. A validator rejecting a token with mismatched audience, expired timestamps, or invalid signatures upholds the zero-trust principle: explicit verification at every resource boundary, never implicit trust.

Azure extends this foundation with managed identities—a credential propagation mechanism that eliminates secret storage entirely for Azure-hosted workloads. A virtual machine, container instance, or App Service slot can acquire an identity without ever possessing a password, client secret, or certificate private key. Behind the scenes, the Azure Instance Metadata Service (IMDS) running on the hypervisor host intercepts HTTP requests to a non-routable link-local address (169.254.169.254) and exchanges the VM's cryptographic attestation for a time-bound access token. This design solves the secret rotation problem: tokens expire hourly, and the IMDS dynamically provisions fresh credentials without developer intervention. For kernel engineers and systems programmers, managed identities represent a hardware-rooted trust anchor—the VM's identity derives from the hypervisor's ability to cryptographically attest which tenant and subscription owns the compute resource, similar to how TPM-based measured boot chains trust to hardware.

Role-Based Access Control (RBAC) in Azure implements a hierarchical authorization model where permissions inherit along a resource management tree. Every Azure resource belongs to a resource group, which belongs to a subscription, which belongs to a management group hierarchy, ultimately rooted in an Azure AD tenant. When assigning a role (a named collection of permissions) to a principal (a user, group, service principal, or managed identity) at a parent scope, that principal automatically inherits those permissions for all child resources. This inheritance model reduces administrative overhead but introduces subtle security implications: a `Contributor` role at the subscription level grants write access to every resource group, storage account, virtual network, and database within that subscription. The principle of least privilege therefore demands assigning roles at the narrowest possible scope, typically at the resource or resource group level rather than subscription or management group.

Azure Key Vault provides cryptographically isolated secret storage backed by FIPS 140-2 Level 2 validated Hardware Security Modules (HSMs). Unlike application configuration files or environment variables, secrets stored in Key Vault never appear in plaintext on disk or in memory outside the HSM boundary. Applications retrieve secrets through authenticated API calls, receiving ephemeral values over TLS 1.2+ encrypted channels. Key Vault's integration with managed identities eliminates the bootstrapping problem: a VM can authenticate to Key Vault using its managed identity token, retrieve a database connection string or API key, and establish downstream connections—all without storing credentials in code repositories, container images, or configuration management systems.

Conditional Access policies implement runtime authorization decisions based on contextual signals beyond static identity and role assignments. A policy evaluates request-time attributes such as source IP address, device compliance state, sign-in risk score (from Azure AD Identity Protection's machine learning models), application sensitivity label, and user/group membership. Policy outcomes include granting access, denying access, or requiring additional authentication factors through step-up MFA challenges. This model aligns with zero-trust principles by treating every access request as potentially hostile: even a valid token from an authenticated user may be rejected if the request originates from an anomalous geographic location, an unmanaged device, or during a detected credential leak incident.

The mathematical foundation of token-based authorization rests on asymmetric cryptography's non-repudiation property. Given a message `m`, a private key `k_priv`, and a signature function `S`, the identity provider generates a signature `σ = S(k_priv, m)`. Any validator possessing the corresponding public key `k_pub` can verify that `V(k_pub, m, σ) = true`, confirming the message originated from the holder of `k_priv` and remains unmodified. The security reduction relies on the computational hardness of forging signatures without the private key—either solving the RSA problem (factoring large semiprimes) or the discrete logarithm problem in elliptic curve groups. Azure AD rotates signing keys periodically and publishes key identifiers (`kid`) in token headers, enabling validators to fetch the correct public key from the JWKS endpoint without requiring coordinated key distribution.

## 2. Core Architecture & Mechanics

Azure Active Directory federation operates as a distributed system with geographically replicated directory services, token issuance endpoints, and policy evaluation engines. The architecture separates the authentication plane (verifying user credentials), the authorization plane (evaluating permissions and policies), and the token issuance plane (generating cryptographically signed artifacts). This separation enables independent scaling: authentication can leverage hardware security keys and biometric factors, authorization can incorporate real-time risk signals, and token issuance can achieve sub-100ms latencies through regional caching of signing keys and user claims.

The OAuth 2.0 authorization code flow, the most secure flow for interactive user authentication, proceeds through a sequence of cryptographic redirects and token exchanges:

```
┌──────────┐                                  ┌──────────────┐
│  Client  │                                  │   Azure AD   │
│  (Web    │                                  │  (Identity   │
│   App)   │                                  │   Provider)  │
└─────┬────┘                                  └──────┬───────┘
      │                                              │
      │  1. GET /authorize                          │
      │     ?response_type=code                     │
      │     &client_id=<app_id>                     │
      │     &redirect_uri=<callback>                │
      │     &scope=openid profile                   │
      ├─────────────────────────────────────────────>│
      │                                              │
      │  2. 302 Redirect to login.microsoftonline   │
      │     User authenticates (password, MFA, etc) │
      │<─────────────────────────────────────────────┤
      │                                              │
      │  3. 302 Redirect to client callback         │
      │     ?code=<authorization_code>              │
      │<─────────────────────────────────────────────┤
      │                                              │
      │  4. POST /token                             │
      │     grant_type=authorization_code           │
      │     code=<authorization_code>               │
      │     client_id=<app_id>                      │
      │     client_secret=<secret>                  │
      ├─────────────────────────────────────────────>│
      │                                              │
      │  5. JSON Response:                          │
      │     { "access_token": "eyJ0eXAi...",        │
      │       "id_token": "eyJ0eXAi...",            │
      │       "refresh_token": "0.AToA...",         │
      │       "expires_in": 3600 }                  │
      │<─────────────────────────────────────────────┤
      │                                              │
      │  6. Access protected resource               │
      │     Authorization: Bearer eyJ0eXAi...       │
      ├──────────────────────────────────────────────> Resource
      │                                                 Server
```

The authorization code itself is a single-use, short-lived (10-minute) opaque token that the client exchanges for an access token through a back-channel POST request. This two-step exchange prevents token leakage through browser history or referrer headers: the authorization code appears in the front-channel redirect URL, but the sensitive access token only traverses the secure back-channel between client and identity provider. The client authenticates this back-channel request using its client secret or certificate, proving it is the legitimate recipient of the authorization code rather than an attacker who intercepted the redirect.

Access tokens in Azure AD are typically 1-2 KB JSON Web Tokens with three base64url-encoded segments separated by periods: `<header>.<payload>.<signature>`. The header specifies the signing algorithm and key identifier:

```json
{
  "typ": "JWT",
  "alg": "RS256",
  "kid": "nOo3ZDrODXEK1jKWhXslHR_KXEg"
}
```

The payload contains standardized claims (from RFC 7519) and Azure-specific extensions:

```json
{
  "aud": "https://management.azure.com/",
  "iss": "https://sts.windows.net/72f988bf-86f1-41af-91ab-2d7cd011db47/",
  "iat": 1704067200,
  "nbf": 1704067200,
  "exp": 1704070800,
  "sub": "AAAAAAAAAAAAAAAAAAAAALongOpaqueIdentifier",
  "tid": "72f988bf-86f1-41af-91ab-2d7cd011db47",
  "oid": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "upn": "alice@contoso.com",
  "scp": "user_impersonation",
  "roles": ["Storage Blob Data Contributor"],
  "ver": "2.0"
}
```

The `aud` claim specifies the resource URI, ensuring tokens issued for Azure Resource Manager cannot be replayed against Microsoft Graph or Azure Storage. The `iss` claim identifies the tenant-specific token endpoint, preventing cross-tenant token reuse. The `sub` claim is a pairwise pseudonymous identifier stable within a single application but different across applications, protecting user privacy. The `oid` claim is the immutable object identifier for the user or service principal in the directory. The `scp` claim contains delegated permissions for user tokens, while the `roles` claim contains application permissions for service principal tokens.

Managed identities eliminate the need for explicit credential management by leveraging the Azure Instance Metadata Service as a credential broker. When a VM or container requests an access token, the IMDS endpoint validates the caller's identity through kernel-enforced network isolation—only processes running on the specific compute resource can reach 169.254.169.254, and the hypervisor ensures one VM cannot spoof another's metadata requests. The IMDS then contacts Azure AD on behalf of the compute resource, presenting the resource's Azure Resource Manager identifier as proof of identity. Azure AD issues an access token scoped to the managed identity's assigned roles, and the IMDS returns this token to the calling process. The entire exchange occurs without the workload ever possessing long-term credentials:

```
┌───────────────┐       ┌──────────────┐       ┌───────────┐
│  Application  │       │     IMDS     │       │ Azure AD  │
│   (VM/Pod)    │       │  (Hypervisor │       │  (Token   │
│               │       │   Service)   │       │  Endpoint)│
└───────┬───────┘       └──────┬───────┘       └─────┬─────┘
        │                      │                     │
        │ GET /metadata/       │                     │
        │   identity/oauth2/   │                     │
        │   token?resource=    │                     │
        │   https://vault...   │                     │
        ├─────────────────────>│                     │
        │                      │                     │
        │                      │ POST /oauth2/token  │
        │                      │   (with VM identity)│
        │                      ├────────────────────>│
        │                      │                     │
        │                      │ {"access_token":    │
        │                      │  "eyJ0eXAi...",     │
        │                      │  "expires_in": 3600}│
        │                      │<────────────────────┤
        │                      │                     │
        │ {"access_token":     │                     │
        │  "eyJ0eXAi...",      │                     │
        │  "expires_in": 3600} │                     │
        │<─────────────────────┤                     │
        │                      │                     │
```

Role-Based Access Control operates on a graph model where resources form a directed acyclic graph (DAG) with inheritance edges. Each node in the graph (management group, subscription, resource group, or resource) can have role assignments—bindings between a security principal, a role definition, and a scope. When evaluating whether a principal has permission to perform an operation on a resource, the Azure Resource Manager traverses the graph from the resource upward to the root, collecting all applicable role assignments. A role assignment at a parent node grants permissions on all descendant nodes through inheritance. Role definitions themselves are collections of `Actions` (control plane operations like `Microsoft.Compute/virtualMachines/write`) and `DataActions` (data plane operations like `Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read`). Azure's built-in roles range from `Owner` (full control including role assignments) to `Reader` (read-only access) to granular roles like `Virtual Machine Contributor` (manage VMs but not network or storage).

The RBAC permission check algorithm implements a union of allows with explicit denies taking precedence:

```
function HasPermission(principal, resource, action):
    assignments = CollectRoleAssignments(principal, resource)
    allows = []
    denies = []
    
    for assignment in assignments:
        role = GetRoleDefinition(assignment.roleDefinitionId)
        for permission in role.permissions:
            if MatchesPattern(action, permission.actions):
                allows.append(assignment)
            if MatchesPattern(action, permission.notActions):
                denies.append(assignment)
    
    if denies is not empty:
        return false
    if allows is not empty:
        return true
    return false
```

The pattern matching supports wildcards, enabling compact role definitions like `Microsoft.Storage/*/read` to grant read permissions across all storage operations. The `notActions` clause enables negative permissions—a role can grant broad access via wildcard while explicitly excluding sensitive operations. Critically, Azure evaluates RBAC permissions at request time rather than caching authorization decisions, ensuring revoked role assignments take effect immediately without waiting for token expiration.

Azure Key Vault implements a multi-tiered security architecture where secrets, keys, and certificates reside in FIPS 140-2 Level 2 validated HSMs (or Level 3 for Premium SKU). The Key Vault service never extracts private key material from the HSM—cryptographic operations like signing, encryption, and decryption occur within the HSM boundary. When an application retrieves a secret, Key Vault first validates the caller's managed identity or service principal token, checks the Key Vault access policy or RBAC permissions, and if authorized, retrieves the secret value from the HSM-backed storage. The secret travels encrypted over TLS 1.3 to the caller, who decrypts it in memory. For keys used in cryptographic operations, Key Vault exposes APIs like `Sign`, `Verify`, `Encrypt`, and `Decrypt` that accept plaintext or ciphertext payloads and return results computed entirely within the HSM. This design prevents key exfiltration: even a compromised Key Vault service cannot extract private keys since the HSM enforces separation between key storage and operation interfaces.

Key Vault access policies define permissions as a combination of secret permissions (`get`, `list`, `set`, `delete`), key permissions (`sign`, `verify`, `wrapKey`, `unwrapKey`), and certificate permissions (`get`, `create`, `import`). Each permission grants a specific API capability, enabling least-privilege access. For example, an application that only needs to retrieve database credentials can be granted `secrets/get` without `secrets/list` (preventing enumeration of other secrets) or `secrets/set` (preventing unauthorized modification). Key Vault also supports soft-delete and purge protection, ensuring accidentally deleted secrets remain recoverable for 90 days and cannot be permanently purged by an attacker even with delete permissions.

Conditional Access policies implement a decision engine that evaluates multi-dimensional signals at authentication time and dynamically adjusts access requirements. A policy consists of assignments (which users, groups, or workload identities it applies to), cloud apps (which resources it governs), conditions (contextual factors that trigger the policy), and access controls (the enforcement action). The evaluation flow proceeds as a series of boolean expressions:

```
function EvaluateConditionalAccess(request):
    applicable_policies = []
    
    for policy in enabled_policies:
        if policy.assignments.includes(request.user) and
           policy.cloud_apps.includes(request.resource) and
           EvaluateConditions(policy.conditions, request):
            applicable_policies.append(policy)
    
    for policy in applicable_policies:
        if policy.grant_controls.require_mfa and not request.has_mfa:
            return RequireStepUpAuthentication("mfa")
        if policy.grant_controls.require_compliant_device and not request.device_compliant:
            return Deny("device_not_compliant")
        if policy.grant_controls.require_approved_app and not request.app_approved:
            return Deny("unapproved_app")
    
    return Allow()
```

Conditions can evaluate user risk level (low, medium, high from Azure AD Identity Protection's anomaly detection), sign-in risk (based on impossible travel, anonymous IP, malware-linked IP), device platform (Windows, macOS, iOS, Android), location (named locations or IP ranges), and client application type (browser vs. native app). A policy requiring MFA for high-risk sign-ins implements adaptive authentication: normal requests proceed with just a password, but suspicious requests trigger real-time push notifications to the user's registered authenticator app. If the user approves the MFA challenge, the session continues; otherwise, access is denied and the incident logged for security operations review.

Session controls provide ongoing enforcement beyond initial authentication. A policy can limit session lifetime to a fixed duration, require periodic reauthentication, or apply app-enforced restrictions that signal to cloud applications to enforce additional security controls. For example, a Conditional Access policy can instruct Exchange Online to block downloading attachments or SharePoint to prevent file downloads, implementing information barriers at the data plane without modifying application code.

The zero-trust network model eliminates implicit trust based on network location. Traditional perimeter security assumed anything inside the corporate network was trusted, but modern threat models recognize that attackers breach networks through phishing, lateral movement, and compromised endpoints. Zero-trust instead verifies every access request regardless of origin: a user connecting from the corporate office network faces the same authentication and authorization checks as one connecting from a coffee shop. Azure Private Link and Virtual Network service endpoints enable private connectivity to Azure services without traversing the public internet, but even these connections enforce identity-based access controls rather than relying on network segmentation alone. A VM in a VNet communicates with Azure Storage over a private endpoint, presenting an access token for every request—the network path provides defense-in-depth against packet interception, but the authorization decision remains identity-driven.

## 3. High-Performance Optimization & Failure Modes

Token caching and refresh strategies determine authentication overhead in distributed systems. Access tokens expire after 60-75 minutes (the exact duration varies to prevent synchronized expiration storms across millions of clients), requiring applications to request new tokens before the current one expires. Naive implementations that acquire a fresh token for every outbound request introduce 50-100ms of latency per request and risk throttling by Azure AD's rate limits (typically 1,000-10,000 requests per second per tenant, depending on license SKU). Production-grade applications instead cache tokens in memory with an expiration buffer—requesting a new token when 90% of the lifetime has elapsed—and reuse the cached token for all requests within that window. Refresh tokens, which have 90-day idle expiration (extended to 180 days with continuous use), enable background token renewal without user interaction, maintaining seamless access for long-running services.

The token acquisition flow must handle transient failures gracefully. Azure AD occasionally returns 429 (Too Many Requests) or 503 (Service Unavailable) responses during regional load spikes or planned maintenance events. Robust client libraries implement exponential backoff with jitter: after a failed request, the client waits `min(base * 2^attempt + random(0, jitter), max_delay)` seconds before retrying. The randomized jitter prevents thundering herd behavior where thousands of clients retry simultaneously, amplifying load on the already-stressed identity provider. Microsoft's official SDK libraries (Azure.Identity for .NET, azure-identity for Python, @azure/identity for Node.js) encapsulate these retry semantics and should be preferred over hand-rolled HTTP clients.

Managed identity token acquisition from IMDS introduces a subtle race condition during VM startup. The managed identity backend provisions credentials asynchronously after VM creation, sometimes requiring 30-60 seconds before tokens become available. Applications that immediately request tokens on boot may encounter 404 errors from IMDS. The correct pattern is retry-with-backoff or delaying token acquisition until the application's first outbound request. Kubernetes workloads using Azure AD Pod Identity face similar initialization delays, as the Node Managed Identity Controller must assign the identity to the pod's network namespace before IMDS recognizes the pod's requests.

Role assignment propagation exhibits eventual consistency with 5-15 minute latencies. When a security principal receives a new role assignment, the change must replicate across Azure Resource Manager's global distributed database and invalidate cached authorization decisions in regional API gateways. During this propagation window, requests may fail with 403 (Forbidden) despite the role assignment appearing in the Azure Portal. Production automation scripts must account for this delay: after creating a managed identity and assigning roles, introduce a 2-3 minute sleep or implement retry logic on the first resource access attempt. The consistency model guarantees that once a principal successfully executes an operation, that capability remains until explicitly revoked—there are no scenarios where a granted permission spontaneously disappears.

Key Vault throttles requests at both the service tier (shared quota across all operations) and individual secret/key tier (protecting against tight loops that hammer a single resource). The Standard SKU provides 2,000 requests per 10 seconds per vault for secrets, 10,000 for key operations. Premium SKU doubles these limits. Exceeding throttle limits returns 429 with a `Retry-After` header indicating seconds until the quota resets. High-throughput applications should cache retrieved secrets in memory rather than fetching from Key Vault on every use—a database connection string or API key retrieved once per hour achieves the same security posture as per-request retrieval with 3,600× lower load. For secrets that change frequently, Key Vault supports secret versions and change notifications through Event Grid, enabling cache invalidation without polling.

Conditional Access policy evaluation occurs synchronously in the authentication path, adding 10-50ms latency per sign-in. Policies with complex condition logic (evaluating dozens of user attributes, group memberships, and device properties) increase this latency. Organizations deploying hundreds of policies should structure them hierarchically: broad policies at the tenant level for baseline requirements (require MFA for all users), specific policies at the application level for sensitive resources (require compliant devices for financial systems). Azure AD evaluates policies in undefined order and applies all matching controls, so conflicting policies (one requiring MFA, another blocking access) default to the most restrictive outcome—a deny control overrides grant controls.

Sign-in logs and audit logs provide forensic visibility into authentication and authorization events. Sign-in logs capture every authentication attempt with timestamps, source IP, device details, MFA method, Conditional Access policy outcomes, and result status (success, failure, interrupted). Audit logs record directory modifications: role assignments created, group memberships changed, application permissions granted. For production security operations, stream these logs to Azure Monitor, Azure Sentinel, or an external SIEM through diagnostic settings rather than querying the Portal API—the streaming path provides sub-minute latency and unbounded retention, whereas the Portal API limits queries to 30 days of history with 5-minute granularity.

Token validation failures manifest as opaque 401 (Unauthorized) responses from Azure resources. Debugging requires correlating the failed request with the access token's claims. Extract the token from the `Authorization: Bearer <token>` header and decode the base64url-encoded payload (no signature validation needed for debugging, only for production use). Common validation failures include audience mismatch (token issued for `https://management.azure.com/` presented to `https://storage.azure.com/`), expired token (current time exceeds `exp` claim), signature verification failure (token signed with a key no longer in the JWKS set, indicating clock skew or key rotation), and missing required claims (application expects `roles` claim but token only contains `scp`).

Cross-tenant access introduces additional complexity when users from one Azure AD tenant need to access resources in another. Azure AD B2B (Business-to-Business) guest users receive a home-tenant-issued token that the resource tenant accepts through federated trust. The guest user authenticates against their home tenant, receives a token with a `tid` claim identifying the home tenant, and presents this token to the resource tenant. The resource tenant validates the token's signature against the home tenant's public keys and evaluates RBAC permissions based on the guest user's object ID in the resource tenant's directory. This model preserves the guest's home tenant's identity governance (MFA policies, Conditional Access) while granting the resource tenant control over authorization. Performance-sensitive applications should cache the guest user's group memberships and role assignments since cross-tenant group expansion adds 20-30ms latency per request.

Service-to-service authentication using application-only tokens (OAuth 2.0 client credentials flow) bypasses user delegation, enabling daemon services and background jobs to access resources. The service principal authenticates using a client secret or certificate, receives a token with `roles` claims (not `scp`), and operates with its own granted permissions rather than impersonating a user. This flow requires careful scope limitation: a service principal with `Storage Blob Data Owner` at the subscription level can delete any blob in any storage account within that subscription. Granular roles like `Storage Blob Data Contributor` and resource-level assignments enforce least privilege. Certificate-based authentication provides stronger security than client secrets, as certificates support hardware-backed private key storage (TPM, HSM) and longer expiration periods (1-2 years versus 2-year maximum for secrets), reducing rotation overhead.

Disaster recovery for identity infrastructure requires replicating critical configuration to secondary regions. While Azure AD itself operates as a globally distributed service with automatic failover, organization-specific artifacts like Conditional Access policies, application registrations, and custom role definitions require explicit backup. Export these configurations through Microsoft Graph API (`GET /policies/conditionalAccessPolicies`, `GET /applications`) and store as Infrastructure-as-Code templates (Bicep, Terraform). During a tenant recovery scenario, redeploy these templates to reconstitute the identity governance layer. Managed identities tied to specific VM or container resources cannot be exported—rebuilding the compute resources automatically recreates their associated identities, but role assignments must be reapplied through automation scripts or deployment templates that reference the managed identity's principal ID.

The security boundary between tenant administrators and resource data remains subtle. A Global Administrator in Azure AD can reset user passwords, revoke sessions, and assign themselves arbitrary roles—effectively achieving full control over all resources in the tenant. Organizations requiring separation of duties should use Azure AD Privileged Identity Management (PIM) to time-box administrator access: eligible administrators activate their privileged roles only when needed, with activation requiring MFA and approval workflows, and the role assignment automatically expires after 1-8 hours. Audit logs capture all activation events, enabling security operations to monitor privileged access patterns and detect anomalous behavior. For ultimate separation, critical resources should reside in separate Azure AD tenants with distinct Global Administrator populations, preventing lateral movement between identity and infrastructure control planes.
