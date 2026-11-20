# Lesson 3: Federation Protocols, Single Sign-On, Trust Frameworks

## 1. First-Principles Intuition & Invariants

Modern distributed systems cannot function under the naïve assumption that every service will maintain its own credential store and authentication boundary. The computational and security overhead of replicating user databases across dozens or hundreds of microservices, mobile applications, and third-party integrations becomes untenable at scale. Federation protocols emerged from the recognition that identity is not a property that can be replicated safely—it must be delegated, verified, and trusted through cryptographically bound assertions that traverse organizational and trust boundaries.

At the core of all federation architectures lies a fundamental security invariant: the separation of authentication from authorization. Authentication answers the question "who are you?" while authorization answers "what are you allowed to do?" Federation protocols explicitly decouple these concerns by introducing a trusted third party—the Identity Provider (IdP)—that performs the expensive, high-security operation of credential verification exactly once, then issues cryptographic proof tokens that downstream Service Providers (SPs) or Relying Parties (RPs) can verify independently without ever handling raw credentials. This architectural pattern eliminates credential sprawl, reduces attack surface area, and centralizes the enforcement of authentication policies such as multi-factor requirements, device trust signals, and anomaly detection.

The trust model underlying federation is transitive and rooted in public-key cryptography. When a Service Provider receives a cryptographic assertion from an Identity Provider, it must answer two questions before granting access: first, is this assertion structurally valid and properly signed by a key I trust? Second, does the assertion's claims set (user identity, email, group memberships, session lifetime) satisfy my authorization policy? The first question is resolved through signature verification using the IdP's public key, distributed either through X.509 certificate chains or JSON Web Key Sets (JWKS). The second requires the Service Provider to maintain an explicit trust boundary definition that maps external identity claims to internal access control decisions.

Federation introduces a critical temporal dimension absent from traditional username-password authentication: assertions carry explicit validity windows bounded by `NotBefore` and `NotAfter` timestamps. This transforms authentication from a point-in-time event into a time-boxed cryptographic lease. When a user authenticates to an Identity Provider at time $t_0$, the IdP issues an assertion valid from $t_0$ to $t_0 + \Delta t$, where $\Delta t$ represents the maximum session lifetime policy. Service Providers must validate that the current wall-clock time falls within this validity window before accepting the assertion. This design prevents replay attacks where an adversary captures a valid assertion and resubmits it hours or days later, but it also introduces clock synchronization as a critical operational dependency—skew exceeding the validity window will cause spurious authentication failures.

The design space for federation protocols is constrained by three competing requirements: security, usability, and protocol complexity. SAML (Security Assertion Markup Language) prioritizes enterprise security and rich metadata exchange at the cost of verbose XML serialization and complex signature canonicalization rules. OAuth 2.0 prioritizes developer usability and mobile-native flows by treating authorization as a first-class concern and authentication as an orthogonal problem, delegating the latter to vendor-specific extensions. OpenID Connect (OIDC) layers a standardized authentication protocol on top of OAuth 2.0's authorization framework, introducing the ID Token as a cryptographically signed proof of authentication while preserving OAuth's familiar redirect flows and JSON payloads.

Understanding federation requires internalizing the distinction between authentication flows and token structures. The flow defines the sequence of HTTP redirects, form POSTs, and backchannel API calls that move the user from the Service Provider through the Identity Provider and back again with a valid assertion. The token structure defines the serialization format, cryptographic binding, and claims schema that encode the user's identity and session parameters. SAML uses XML-based flows with XML-serialized assertions. OAuth 2.0 defines multiple flows (Authorization Code, Implicit, Client Credentials, Device Code) but remains agnostic to token format, though the industry has converged on JSON Web Tokens (JWT) for interoperability. OpenID Connect mandates JWT serialization for ID Tokens while preserving OAuth's flow flexibility.

Every federation protocol must solve the user-agent mediation problem: how does the Identity Provider's authentication event, occurring in the user's browser or mobile app, get securely communicated back to the Service Provider's backend server without exposing sensitive tokens to the user agent itself? SAML solves this through cryptographic assertions delivered via HTTP POST binding, where the assertion is embedded in a hidden form field that the user's browser automatically submits to the Service Provider. OAuth 2.0 introduces the authorization code—a short-lived, single-use nonce exchanged in the front channel (browser redirect) that the Service Provider's backend later swaps for an access token in the back channel (direct TLS connection to the IdP's token endpoint), ensuring the actual bearer token never transits the user's browser. OpenID Connect inherits this pattern, returning both an authorization code and an ID Token fragment depending on the response type.

The cryptographic foundation of federation is asymmetric signatures, not shared secrets. When an Identity Provider signs a SAML assertion or JWT, it uses its private key to produce a digital signature over the canonical representation of the token's claims. Service Providers possess only the corresponding public key, distributed through SAML metadata XML files or OIDC JWKS endpoints. This asymmetry is critical: a compromised Service Provider cannot forge tokens because it never possessed the private signing key. Contrast this with symmetric HMAC signatures, where both parties share a secret key—any party capable of verifying a token can also forge one, making credential compromise catastrophic.

Federation trust boundaries are not binary but hierarchical and compositional. An enterprise may operate an internal Identity Provider (Active Directory Federation Services, Okta, Azure AD) that itself federates with external IdPs through protocol bridging or identity brokering. In this topology, the enterprise IdP acts as a Service Provider when authenticating users against the external IdP, then acts as an Identity Provider when issuing assertions to internal applications. This chaining introduces transitive trust risks: if the external IdP is compromised, all downstream Service Providers trusting the enterprise IdP may be affected. Protocol designers mitigate this through audience restriction claims (`aud` in JWT, `<AudienceRestriction>` in SAML) that cryptographically bind each token to a specific intended recipient, preventing token substitution attacks where a token issued for application A is maliciously resubmitted to application B.

## 2. Core Architecture & Mechanics

The SAML 2.0 architecture revolves around three primary entities: the User Agent (browser), the Service Provider (SP), and the Identity Provider (IdP). When a user attempts to access a protected resource at the Service Provider, the SP generates an AuthnRequest—an XML document specifying the authentication requirements, binding protocol, and assertion consumer service URL—then redirects the user's browser to the IdP's Single Sign-On (SSO) endpoint with the AuthnRequest embedded as a query parameter or POST body. The IdP validates the AuthnRequest, authenticates the user (potentially reusing an existing SSO session cookie), constructs a SAML Response containing one or more signed Assertions, and returns the user to the SP's Assertion Consumer Service (ACS) endpoint via HTTP POST binding.

The SAML Assertion itself is a nested XML structure containing three critical sections: the `<Issuer>` identifying the IdP, the `<Subject>` identifying the authenticated user through a NameID element, and zero or more `<AttributeStatement>` elements carrying claims like email, group memberships, and entitlements. The entire Assertion is wrapped in an `<Assertion>` element bearing an `ID` attribute (a unique nonce preventing replay), `IssueInstant` timestamp, and `<Conditions>` element specifying validity windows through `NotBefore` and `NotAfter` attributes. Critically, the Assertion includes an audience restriction limiting which Service Providers may consume it, typically set to the SP's entity ID extracted from SAML metadata.

```xml
<saml:Assertion xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                ID="_8e8dc5f69a98cc4c1ff3427e5ce34606fd672f91e6"
                Version="2.0"
                IssueInstant="2024-01-15T14:23:37Z">
  <saml:Issuer>https://idp.example.com/saml/metadata</saml:Issuer>
  <ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
    <ds:SignedInfo>
      <ds:CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>
      <ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>
      <ds:Reference URI="#_8e8dc5f69a98cc4c1ff3427e5ce34606fd672f91e6">
        <ds:Transforms>
          <ds:Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>
          <ds:Transform Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>
        </ds:Transforms>
        <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
        <ds:DigestValue>JKz8xQc5vPVT5rJ+9bZ8WqFw7dk=</ds:DigestValue>
      </ds:Reference>
    </ds:SignedInfo>
    <ds:SignatureValue>MXdZ7bKnB5...</ds:SignatureValue>
    <ds:KeyInfo>
      <ds:X509Data>
        <ds:X509Certificate>MIIDXTCCAkWgAwIBAgIJ...</ds:X509Certificate>
      </ds:X509Data>
    </ds:KeyInfo>
  </ds:Signature>
  <saml:Subject>
    <saml:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">
      user@example.com
    </saml:NameID>
    <saml:SubjectConfirmation Method="urn:oasis:names:tc:SAML:2.0:cm:bearer">
      <saml:SubjectConfirmationData NotOnOrAfter="2024-01-15T14:28:37Z"
                                     Recipient="https://sp.example.com/saml/acs"
                                     InResponseTo="_49585b8e6e4e0ab6a59a4b9e5"/>
    </saml:SubjectConfirmation>
  </saml:Subject>
  <saml:Conditions NotBefore="2024-01-15T14:23:37Z"
                   NotAfter="2024-01-15T14:28:37Z">
    <saml:AudienceRestriction>
      <saml:Audience>https://sp.example.com/saml/metadata</saml:Audience>
    </saml:AudienceRestriction>
  </saml:Conditions>
  <saml:AuthnStatement AuthnInstant="2024-01-15T14:23:37Z"
                       SessionIndex="_be9c1cc4-3afc-4a8a-934d-0bce41b3c3f2">
    <saml:AuthnContext>
      <saml:AuthnContextClassRef>
        urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport
      </saml:AuthnContextClassRef>
    </saml:AuthnContext>
  </saml:AuthnStatement>
  <saml:AttributeStatement>
    <saml:Attribute Name="email">
      <saml:AttributeValue>user@example.com</saml:AttributeValue>
    </saml:Attribute>
    <saml:Attribute Name="groups">
      <saml:AttributeValue>engineering</saml:AttributeValue>
      <saml:AttributeValue>security-team</saml:AttributeValue>
    </saml:Attribute>
  </saml:AttributeStatement>
</saml:Assertion>
```

SAML signature verification requires XML canonicalization to eliminate semantically irrelevant whitespace and namespace prefix variations before hashing. The Service Provider extracts the `<ds:DigestValue>` from the signature's `<Reference>` element, canonicalizes the referenced XML subtree (the Assertion identified by the URI fragment matching the Assertion's ID attribute), computes the SHA-256 hash, and verifies it matches the embedded digest. Next, it canonicalizes the `<SignedInfo>` block, computes RSA-SHA256 over the result using the IdP's public key extracted from the embedded X.509 certificate, and verifies the signature matches `<ds:SignatureValue>`. Only after cryptographic validation succeeds does the SP extract claims from the AttributeStatement and evaluate authorization policies.

The OAuth 2.0 Authorization Code flow decouples authentication from resource access by introducing two distinct token types: the authorization code (a short-lived nonce) and the access token (a bearer credential for API access). The flow begins when the client application (Service Provider equivalent) redirects the user to the authorization server's (Identity Provider equivalent) `/authorize` endpoint with parameters including `client_id`, `redirect_uri`, `response_type=code`, `scope`, and `state` (a CSRF token). The authorization server authenticates the user, obtains consent for the requested scopes, and redirects back to the client's `redirect_uri` with an authorization code and the original state value as query parameters.

```text
GET /authorize?
  response_type=code&
  client_id=s6BhdRkqt3&
  redirect_uri=https%3A%2F%2Fclient.example.com%2Fcallback&
  scope=openid%20profile%20email&
  state=af0ifjsldkj&
  code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&
  code_challenge_method=S256
  HTTP/1.1
Host: idp.example.com
```

The client receives the authorization code in the front channel but cannot use it directly to access protected resources. Instead, the client's backend server makes a direct HTTPS POST request to the authorization server's `/token` endpoint, exchanging the code for an access token. This backchannel request includes the authorization code, the client's credentials (`client_id` and `client_secret`), and the original `redirect_uri` for validation. The authorization server verifies the code has not been used previously (single-use property), validates the client credentials, and returns a JSON payload containing an access token, token type (typically `Bearer`), expiration time, and optionally a refresh token.

```text
POST /token HTTP/1.1
Host: idp.example.com
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=SplxlOBeZQQYbYS6WxSbIA&
redirect_uri=https%3A%2F%2Fclient.example.com%2Fcallback&
client_id=s6BhdRkqt3&
client_secret=7Fjfp0ZBr1KtDRbnfVdmIw&
code_verifier=dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk
```

The authorization server's response encodes the access token as an opaque string or, increasingly, as a signed JWT. When structured as a JWT, the access token becomes self-contained and verifiable by resource servers without requiring back-channel validation calls to the authorization server on every API request.

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InJzYS0yMDQ4In0.eyJpc3MiOiJodHRwczovL2lkcC5leGFtcGxlLmNvbSIsInN1YiI6IjI0ODI4OTc2MTAwMSIsImF1ZCI6Imh0dHBzOi8vYXBpLmV4YW1wbGUuY29tIiwiZXhwIjoxNzM2OTU2MTAwLCJpYXQiOjE3MzY5NTI1MDAsInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwiLCJjbGllbnRfaWQiOiJzNkJoZFJrcXQzIn0.signature_bytes",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "tGzv3JOkF0XG5Qx2TlKWIA",
  "scope": "openid profile email"
}
```

OpenID Connect extends OAuth 2.0 by introducing the ID Token, a JWT specifically encoding authentication event metadata rather than authorization grants. When a client requests the `openid` scope during the authorization flow, the authorization server returns both an access token (for API access) and an ID Token (for authentication proof) in the token endpoint response. The ID Token contains standard claims including `iss` (issuer), `sub` (subject identifier), `aud` (audience—the client's client_id), `exp` (expiration), `iat` (issued-at), and optionally `nonce` (client-provided nonce for replay protection). Additional claims such as `email`, `email_verified`, `name`, and `picture` are included when the client requests corresponding scopes.

```text
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InJzYS0yMDQ4In0.eyJpc3MiOiJodHRwczovL2lkcC5leGFtcGxlLmNvbSIsInN1YiI6IjI0ODI4OTc2MTAwMSIsImF1ZCI6InM2QmhkUmtxdDMiLCJleHAiOjE3MzY5NTYxMDAsImlhdCI6MTczNjk1MjUwMCwibm9uY2UiOiJuLTBTNl9XekEyTWoiLCJlbWFpbCI6InVzZXJAZXhhbXBsZS5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwibmFtZSI6IkpvaG4gRG9lIiwicGljdHVyZSI6Imh0dHBzOi8vZXhhbXBsZS5jb20vcGhvdG8uanBnIn0.signature_bytes
```

Decoding the base64url-encoded payload reveals the claims structure. The client validates the ID Token by verifying the signature using the issuer's public key fetched from the JWKS endpoint (typically `https://idp.example.com/.well-known/jwks.json`), confirming the `iss` matches the expected issuer URL, verifying `aud` contains the client's `client_id`, checking `exp` exceeds the current Unix timestamp, and optionally validating the `nonce` matches the value sent in the original authorization request.

```json
{
  "iss": "https://idp.example.com",
  "sub": "248289761001",
  "aud": "s6BhdRkqt3",
  "exp": 1736956100,
  "iat": 1736952500,
  "nonce": "n-0S6_WzA2Mj",
  "email": "user@example.com",
  "email_verified": true,
  "name": "John Doe",
  "picture": "https://example.com/photo.jpg"
}
```

The JSON Web Token structure consists of three base64url-encoded segments separated by periods: the JOSE header, the payload (claims set), and the cryptographic signature. The JOSE header specifies the signing algorithm (`alg`) and key identifier (`kid`) referencing a specific public key in the issuer's JWKS. The payload contains the claims set as a flat JSON object mapping claim names to values. The signature is computed by concatenating the encoded header, a period, and the encoded payload, then applying the specified signature algorithm using the issuer's private key.

```text
Header (base64url encoded):
{
  "alg": "RS256",
  "typ": "JWT",
  "kid": "rsa-2048"
}

Payload (base64url encoded):
{
  "iss": "https://idp.example.com",
  "sub": "248289761001",
  "aud": "https://api.example.com",
  "exp": 1736956100,
  "iat": 1736952500,
  "scope": "openid profile email"
}

Signature:
RSASSA-PKCS1-v1_5 using SHA-256 over:
  base64url(header) + "." + base64url(payload)
  using the issuer's RSA private key
```

The JWKS endpoint returns a JSON object containing an array of public keys, each identified by a `kid` (key ID) matching the `kid` in JWT headers. Clients cache this keyset and refresh it periodically or on verification failure (to handle key rotation). Each key entry specifies the key type (`kty`), algorithm (`alg`), usage (`use`), and the actual key material as an RSA modulus (`n`) and exponent (`e`) for RSA keys, or `x` and `y` coordinates for elliptic curve keys.

```json
{
  "keys": [
    {
      "kty": "RSA",
      "use": "sig",
      "kid": "rsa-2048",
      "alg": "RS256",
      "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtV...",
      "e": "AQAB"
    },
    {
      "kty": "RSA",
      "use": "sig",
      "kid": "rsa-2048-new",
      "alg": "RS256",
      "n": "xjlCRBqkOL6xKZhm91M1AIdHLhSzW65LqLLuMp2TOkGVGN4wCMPdN7m...",
      "e": "AQAB"
    }
  ]
}
```

Proof Key for Code Exchange (PKCE, pronounced "pixie") mitigates authorization code interception attacks in public clients (mobile apps, single-page applications) that cannot securely store a client secret. Before initiating the authorization flow, the client generates a high-entropy random string called the `code_verifier` (43-128 characters), computes its SHA-256 hash, and base64url-encodes the result to produce the `code_challenge`. The client includes `code_challenge` and `code_challenge_method=S256` in the authorization request. When exchanging the authorization code for tokens, the client sends the original `code_verifier`. The authorization server recomputes the hash and verifies it matches the `code_challenge` from the initial request, ensuring the token request originates from the same client instance that initiated the authorization flow even if the authorization code is intercepted.

Federation across organizational boundaries requires establishing trust through metadata exchange and certificate validation. In SAML deployments, administrators exchange metadata XML files containing entity IDs, endpoint URLs, and X.509 certificates. The IdP's metadata specifies its SSO endpoint URL and signing certificate, while the SP's metadata lists its Assertion Consumer Service (ACS) URLs and entity ID. Both parties import the counterparty's metadata into their configuration, establishing the cryptographic trust anchor. OpenID Connect simplifies this through discovery: the client fetches the IdP's metadata from a well-known URL (`https://idp.example.com/.well-known/openid-configuration`) returning a JSON document specifying authorization, token, JWKS, and userinfo endpoints along with supported scopes, response types, and signing algorithms.

```json
{
  "issuer": "https://idp.example.com",
  "authorization_endpoint": "https://idp.example.com/authorize",
  "token_endpoint": "https://idp.example.com/token",
  "userinfo_endpoint": "https://idp.example.com/userinfo",
  "jwks_uri": "https://idp.example.com/.well-known/jwks.json",
  "response_types_supported": ["code", "token", "id_token", "code id_token"],
  "subject_types_supported": ["public", "pairwise"],
  "id_token_signing_alg_values_supported": ["RS256", "ES256"],
  "scopes_supported": ["openid", "profile", "email", "address", "phone"],
  "claims_supported": ["sub", "name", "email", "email_verified", "picture"]
}
```

Token introspection provides a mechanism for resource servers to validate opaque access tokens issued by an authorization server. The resource server makes an authenticated POST request to the authorization server's introspection endpoint, sending the access token. The response indicates whether the token is active and, if so, returns associated metadata including `scope`, `client_id`, `username`, `exp`, and token type. This pattern centralizes token validation logic at the authorization server but introduces latency and availability dependencies on every API request unless the resource server caches introspection results (trading freshness for performance).

```text
POST /introspect HTTP/1.1
Host: idp.example.com
Content-Type: application/x-www-form-urlencoded
Authorization: Basic czZCaGRSa3F0MzpnWDFmQmF0M2JW

token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

```json
{
  "active": true,
  "scope": "openid profile email",
  "client_id": "s6BhdRkqt3",
  "username": "user@example.com",
  "token_type": "Bearer",
  "exp": 1736956100,
  "iat": 1736952500,
  "sub": "248289761001",
  "aud": "https://api.example.com"
}
```

## 3. High-Performance Optimization & Failure Modes

Federation protocols introduce multiple network round-trips that compound latency, particularly for SAML where XML parsing, canonicalization, and signature verification impose significant CPU overhead. High-performance deployments cache parsed SAML metadata and precompute canonicalized signature templates to avoid redundant XML processing on every assertion. IdP signing keys change infrequently (measured in months or years), so Service Providers should cache the IdP's public key or certificate rather than parsing it from every assertion's `<KeyInfo>` block. When an assertion fails signature verification due to key rotation, the SP should refresh its cached key and retry verification once before rejecting the assertion, implementing a two-strike policy that balances security and availability.

OAuth 2.0's backchannel token exchange reduces front-channel attack surface but introduces IdP availability as a critical path dependency. If the authorization server's token endpoint experiences downtime or elevated latency during the code-to-token exchange, user authentication fails even though the user successfully authenticated at the IdP. Production deployments must implement aggressive timeouts (typically 5-10 seconds) on token endpoint requests and return user-visible errors that distinguish network failures from authentication failures, enabling users to retry rather than assuming their credentials were rejected. Client-side circuit breakers that detect sustained token endpoint failures can temporarily redirect users to error pages explaining the service degradation rather than subjecting them to repeated timeout experiences.

JWT signature verification scales horizontally because it requires only the issuer's public key, which can be cached and replicated across all resource server instances without coordination. The computational bottleneck is RSA signature verification, which requires modular exponentiation over large integers (typically 2048 or 4096 bits). A single-core Intel Xeon can verify approximately 10,000 RSA-2048 signatures per second using OpenSSL. Deployments exceeding this throughput should consider elliptic curve signatures (ES256) offering equivalent security with 256-bit keys and verification throughput exceeding 30,000 operations per second due to faster point multiplication on elliptic curves. The tradeoff is compatibility: older libraries and hardware security modules may lack ES256 support, and mixed-algorithm deployments require resource servers to support both RSA and ECDSA verification paths.

Token lifetime policies create a fundamental tension between security and user experience. Short-lived access tokens (5-15 minutes) minimize the blast radius of token theft but require frequent token refreshes, introducing latency and increasing load on the authorization server's token endpoint. Long-lived tokens (hours or days) reduce refresh overhead but extend the window during which a stolen token remains valid. Refresh tokens resolve this tension by issuing short-lived access tokens paired with long-lived refresh tokens stored securely on the client. When an access token expires, the client exchanges the refresh token for a new access token without user interaction. This pattern confines the high-security refresh token to backchannel communication while allowing the access token to be sent in front-channel API requests where interception risk is higher.

Refresh token rotation further hardens this pattern by issuing a new refresh token with each access token refresh and immediately invalidating the old refresh token. If an attacker steals a refresh token and uses it before the legitimate client's next refresh, the authorization server detects the anomaly when the legitimate client attempts to use the now-invalid old refresh token. The server responds by invalidating the entire token family (all tokens issued from the original authorization code), forcing the user to reauthenticate. This mechanism detects refresh token theft within one refresh cycle (typically 15 minutes) at the cost of complexity and potential false positives if network errors cause the client to retry a refresh request after the authorization server already issued a new token.

JWKS key rotation introduces eventual consistency challenges. When an authorization server rotates signing keys, it must continue publishing the old public key in its JWKS for at least the maximum token lifetime to allow resource servers to validate tokens signed with the old key before expiration. A typical rotation process involves adding the new key to JWKS (step 1), waiting for resource servers to refresh their cached keyset (typically 24 hours based on JWKS HTTP cache headers), switching the authorization server to sign new tokens with the new key (step 2), waiting for all tokens signed with the old key to expire (step 3, typically 1 hour), and finally removing the old key from JWKS (step 4). This four-phase process spans days, during which the JWKS contains multiple keys. Resource servers must iterate through all keys with matching `kid` values when verifying signatures, falling back to trying all keys if no `kid` match exists.

Audience validation failures represent a common operational failure mode caused by misconfiguration or multi-tenant deployments. When a Service Provider expects its entity ID in the SAML assertion's `<AudienceRestriction>` but the IdP populates it with a different value (or omits it entirely), every authentication attempt fails with cryptic "audience validation failed" errors. Diagnosing this requires decoding the raw SAML assertion or JWT payload, extracting the actual `aud` claim, and comparing it against the Service Provider's expected audience configuration. In multi-tenant SaaS platforms where a single Service Provider serves multiple customer organizations, each with their own IdP, the Service Provider must dynamically determine the expected audience based on the authenticating user's tenant context—a mapping often stored in a tenant configuration database keyed by IdP entity ID.

Clock skew causes spurious token validation failures when the Service Provider's system clock diverges from the Identity Provider's clock beyond the token's validity window. A token issued at `t=100` with a 5-minute validity window (`NotBefore=100`, `NotAfter=400`) will be rejected by a Service Provider whose clock reads `t=405`. Production deployments typically implement clock skew tolerance of 60-180 seconds, treating tokens as valid if the current time falls within `[NotBefore - tolerance, NotAfter + tolerance]`. This grace period prevents transient failures due to minor clock drift but introduces a replay window during which an expired token remains acceptable. The tolerance value should be set based on observed clock drift between systems, measured through NTP daemon statistics (`ntpq -p`). Organizations using virtualized infrastructure must ensure hypervisor clock synchronization because virtual machine clock skew can exceed tolerance thresholds during live migration or high CPU contention.

Single Sign-On session management introduces logout complexity absent from monolithic applications. When a user clicks "logout" in a Service Provider application, the local session can be terminated immediately, but the IdP's SSO session may persist, allowing the user to reauthenticate to other Service Providers without re-entering credentials. SAML Single Logout (SLO) addresses this by having the Service Provider send a `<LogoutRequest>` to the IdP, which then propagates logout requests to all other Service Providers participating in the SSO session. This requires the IdP to maintain a session registry mapping SSO sessions to active Service Provider sessions—a stateful operation complicating horizontal scaling. If any Service Provider in the logout chain fails to respond or rejects the logout request, the protocol provides no defined recovery mechanism, potentially leaving some Service Providers with active sessions after the user believes they logged out globally.

OAuth 2.0 lacks a standardized logout mechanism altogether. OpenID Connect introduces RP-Initiated Logout where the client redirects the user to the IdP's `end_session_endpoint` with an `id_token_hint` parameter containing the original ID Token. The IdP terminates its SSO session and optionally redirects back to the client's `post_logout_redirect_uri`. This pattern handles only browser-based logout; mobile and native applications with background access tokens have no mechanism to revoke tokens unless the authorization server exposes a non-standard revocation endpoint. OAuth 2.0 Token Revocation (RFC 7009) standardizes this, allowing clients to POST a token to the revocation endpoint for immediate invalidation, but authorization servers must implement active token blacklists or short-lived tokens to enforce revocation for JWTs validated offline by resource servers.

SAML signature wrapping attacks exploit XML parsing ambiguities where an attacker copies a validly signed assertion into a malicious SAML response, adds a second assertion containing different claims (a forged user identity), and relies on discrepancies between XML signature validation and claim extraction logic. The signature verifier validates the original assertion correctly, but the claim extractor processes the forged assertion if it appears earlier in document order. Mitigating this requires defensive parsing: after signature verification succeeds, extract the signed element by traversing the signature's `<Reference URI>` to the exact signed subtree, then extract claims exclusively from that subtree, ignoring any other assertion elements in the document. Modern SAML libraries implement this by default, but custom implementations and legacy parsers remain vulnerable.

JWT algorithm confusion attacks exploit applications that accept tokens signed with symmetric algorithms (HS256) but validate them using an asymmetric public key. An attacker obtains the IdP's public key (public information), forges a JWT header specifying `"alg": "HS256"`, signs the payload using HMAC-SHA256 with the public key as the secret, and submits the token to a Service Provider that blindly uses the public key for validation. The Service Provider treats the public key as an HMAC secret, successfully validates the forged signature, and grants access. Preventing this requires strict algorithm whitelisting: reject any token whose `alg` header does not match the expected algorithm configured for that issuer, never allowing the token's header to dictate the verification algorithm. Additionally, configure JWKS entries with explicit `alg` fields and reject tokens whose `alg` header mismatches the `alg` in the corresponding JWKS key entry.

Token substitution attacks occur when an attacker intercepts a token issued for one resource server and submits it to a different resource server. If both resource servers accept tokens from the same issuer without validating the `aud` claim, the attacker gains unauthorized cross-service access. A token issued for `https://api.payments.example.com` with `"scope": "payment:initiate"` should be rejected by `https://api.users.example.com` even if both trust the same IdP. Audience validation must be exact-match or prefix-match depending on resource hierarchy: a token with `"aud": "https://api.example.com"` may be accepted by `https://api.example.com/users` and `https://api.example.com/payments` if they share a trust boundary, but `https://different-api.example.com` must reject it. The authorization server must issue tokens with the narrowest possible audience, ideally the specific resource server or API gateway hostname, and resource servers must reject tokens lacking their hostname in the `aud` claim array.

Phishing-resistant authentication in federation requires binding the authentication event to client context beyond username and password. SAML and OpenID Connect support authentication context classes that indicate the authentication method: password, multi-factor, hardware token, biometric, or certificate-based. Service Providers can request specific authentication context classes in their authorization requests (`<RequestedAuthnContext>` in SAML, `acr_values` parameter in OIDC), and the IdP includes the actual method used in the assertion (`<AuthnContextClassRef>` in SAML, `acr` claim in OIDC ID Tokens). High-security Service Providers should enforce minimum authentication context requirements, rejecting assertions authenticated with weak methods even if the signature is valid. This requires maintaining a policy mapping of authentication context class URIs to acceptable security levels and evaluating it during token validation before establishing a local session.
