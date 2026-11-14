# Lesson 3: Authentication, Authorization, Cryptography

## 1. First-Principles Intuition & Invariants

Trust is not a property of a system; it is a verdict rendered by a protocol. When a process, user, or device presents a credential to a service, it is making a claim about its identity, and the service is deciding whether that claim is consistent with evidence it can verify. This distinction—between a claim and a verified assertion—is the central invariant around which all of authentication, authorization, and cryptography orbit.

The confusion of authentication with authorization has caused more privilege escalation vulnerabilities than almost any other conceptual error in systems design. Authentication answers a narrow question: *who are you?* Authorization answers a different question: *what are you permitted to do?* The two must be enforced independently and at every layer of a system. A JWT that is cryptographically valid proves only that it was signed by a trusted issuer. It says nothing, by itself, about whether the subject encoded within it has permission to operate on the resource being requested. Collapsing these two concerns into a single check—common in legacy API designs—is the structural cause of Broken Object Level Authorization (BOLA), the top-ranked OWASP API risk for years running. The correct model treats authentication as producing an identity principal, and authorization as a separate policy evaluation that takes that principal plus the requested action plus the target resource as inputs.

Cryptography is the substrate on which both rest. Without it, authentication reduces to asking someone to tell you their password over a channel anyone can read, and authorization decisions can be forged by any party who can intercept and replay a token. The fundamental primitives break into three families by function: confidentiality (symmetric encryption with AES-GCM, asymmetric encryption with RSA-OAEP or ECIES), integrity and authenticity (MAC functions like HMAC-SHA256, authenticated encryption like ChaCha20-Poly1305, and digital signatures like Ed25519), and key derivation (PBKDF2, bcrypt, scrypt, and Argon2id for password hashing; HKDF for deterministic key expansion from high-entropy material).

A critical invariant that practitioners must internalize is that encryption does not imply authentication. AES-CBC in unauthenticated mode is malleable: an attacker who knows the plaintext structure can flip ciphertext bits to produce predictable plaintext mutations without knowing the key. This was exploited in CBC padding oracle attacks against ASP.NET, OpenSSL, and dozens of custom TLS implementations. The rule is absolute: always use authenticated encryption, meaning AEAD modes such as AES-256-GCM or ChaCha20-Poly1305, where the ciphertext carries a GCM authentication tag or a Poly1305 MAC that makes any ciphertext modification detectable before decryption occurs. The tag is not an append-on-after-thought; it is computed over the ciphertext and additional authenticated data (AAD) simultaneously during encryption, bound to the nonce and key, so the decryption primitive will reject any ciphertext that has been tampered with.

Key derivation from passwords is a separate and frequently misunderstood problem. A raw SHA-256 hash of a password is not a password hash in any security-meaningful sense. SHA-256 is designed to be fast—capable of billions of evaluations per second on modern GPUs—which makes it trivially brute-forceable. Password KDFs are intentionally slow and memory-hard. Argon2id, the winner of the Password Hashing Competition, operates with configurable time cost (iteration count), memory cost (kilobytes of RAM), and parallelism. The memory-hardness property forces an attacker to provision significant DRAM per cracking thread, which breaks the economics of GPU-accelerated cracking clusters far more effectively than time cost alone. For embedded and constrained environments where Argon2id is impractical due to memory limits, bcrypt with a work factor of 12 or higher remains acceptable; scrypt provides an intermediate memory-hard option tunable to tighter RAM budgets.

The nonce is another invariant with catastrophic failure modes on violation. In AES-256-GCM, the 96-bit nonce must never repeat under the same key. A single nonce reuse allows an attacker who observes two ciphertexts to XOR them together, canceling the keystream and recovering the XOR of the two plaintexts—a complete confidentiality break. It further allows full MAC key recovery via linear algebra over GF(2^128), which breaks integrity protection for all past and future messages under that key. This is not theoretical: the GCM nonce reuse attack has been demonstrated against TLS 1.2 implementations that failed to generate random nonces. The mitigation is deterministic nonce construction (a 96-bit counter concatenated with a fixed sender ID, as specified in RFC 5116) or generation via a cryptographically secure RNG, never from a source with any reuse probability.

## 2. Core Architecture & Mechanics

### The Credential Verification Pipeline

A production authentication system is a pipeline with discrete, ordered stages. Understanding the data structures and control flow at each stage is what separates practitioners who can audit and exploit these systems from those who can merely configure them.

```
Client                 Load Balancer          Auth Service            Resource Server
  |                        |                      |                        |
  |-- POST /token -------->|                      |                        |
  |   {username, password} |-- forward ---------->|                        |
  |                        |                      |-- lookup(username) --> [User Store]
  |                        |                      |<-- {hash, salt, alg} --|
  |                        |                      |                        |
  |                        |                      |-- Argon2id.Verify()    |
  |                        |                      |   (candidate_pw,       |
  |                        |                      |    stored_hash)        |
  |                        |                      |                        |
  |                        |                      |-- sign(JWT, ES256_key) |
  |<-- {access_token,  ----|<-- {access_token} ---|                        |
  |     refresh_token}     |                      |                        |
  |                        |                      |                        |
  |-- GET /api/resource -->|-- forward (w/ JWT) ->|-- verify(JWT) -------->|
  |                        |                      |   (sig, expiry, iss)   |
  |                        |                      |-- authorize(sub, res) ->|
  |                        |                      |   policy eval          |
  |<-- 200 OK -------------|<-- 200 OK -----------|<-- resource payload ---|
```

The user store must never hold plaintext passwords or reversible encodings. The stored record for a credential looks like a serialized Argon2id parameter set alongside the hash output:

```
$argon2id$v=19$m=65536,t=3,p=4$<base64_salt>$<base64_hash>
```

This encoded format carries the algorithm identifier, version, memory parameter `m` in kilobytes, time cost `t`, parallelism `p`, the random salt, and the derived hash. The Argon2id variant combines the data-independent memory access of Argon2i (resistance against side-channel cache timing attacks) with the data-dependent memory access of Argon2d (resistance against GPU cracking) in a two-pass hybrid. During verification, the same parameters are extracted from the stored string, the candidate password is run through Argon2id with those parameters and salt, and the output is compared to the stored hash using a constant-time comparison function. The constant-time comparison is mandatory: a byte-by-byte short-circuit comparison leaks the hash value through a timing side channel measurable over a network.

### JWT Internals and the ES256 Signing Path

A JSON Web Token is three base64url-encoded segments separated by dots: header, payload, signature. The header specifies the algorithm and key identifier; the payload carries the claims (subject, issuer, audience, expiry, issued-at, and any custom claims); the signature is computed over the UTF-8 encoding of `header.payload`. The choice of algorithm is not cosmetic. HS256 uses HMAC-SHA256 with a shared symmetric key, which means every service that needs to verify tokens must possess the signing key—making the signing key a high-value lateral movement target. ES256 uses ECDSA over P-256 with SHA-256: the signer holds a private scalar, and verifiers need only the corresponding public key point. RS256 uses PKCS#1 v1.5 RSA signatures, which carry an infamous historical vulnerability in some implementations: the Bleichenbacher signature forgery, exploitable when a verifier uses a naive bignum comparison rather than a constant-time forward verification. EdDSA with Ed25519 (the `EdDSA` algorithm in JWA) is the strongest choice for new systems: its signing and verification are deterministic (no randomness required, eliminating the nonce reuse failure mode that broke ECDSA in Sony's PS3 firmware signing), and it is fast and constant-time by construction in reference implementations.

The most dangerous JWT vulnerability is the `alg: none` attack. Early JWT libraries that allowed the algorithm to be specified by the token header—and that accepted a valid token with no signature when `alg` was set to `none`—allowed a complete authentication bypass: an attacker strips the signature, sets `alg: none`, and forges any claims they want. The fix is to never read the algorithm from the token; the verifier must specify the expected algorithm explicitly and reject any token that does not match.

A less obvious but equally dangerous variant is the algorithm confusion attack between RS256 and HS256. If a system normally uses RS256, its public key is public. An attacker can take that public key, re-sign a forged payload using HMAC-SHA256 with the public key as the HMAC secret, and set `alg: HS256` in the header. A vulnerable library will switch to symmetric verification, treat the public key as the HMAC key, verify successfully, and grant access. The mitigation is the same: pin the expected algorithm in the verifier, never derive it from the token.

```c
/* Constant-time memory comparison for credential verification.
   Returns 0 if equal, non-zero otherwise. Never short-circuits. */
int ct_memcmp(const void *a, const void *b, size_t len) {
    const unsigned char *pa = (const unsigned char *)a;
    const unsigned char *pb = (const unsigned char *)b;
    unsigned char diff = 0;
    for (size_t i = 0; i < len; i++) {
        diff |= pa[i] ^ pb[i];
    }
    return (int)diff;
}
```

The accumulator `diff` collects all bit differences with OR, ensuring the loop always runs the full length regardless of where a mismatch occurs. This is a minimal safe implementation; production code should use `CRYPTO_memcmp` from OpenSSL or `timingsafe_bcmp` from libc where available, as the compiler cannot optimize those away.

### OAuth2 and OIDC State Machine

OAuth2 is a delegation protocol, not an authentication protocol. It defines four grant types, of which the Authorization Code flow with PKCE is the only one appropriate for user-facing applications in 2024. The state machine is worth tracing at the byte level because every state transition is an attack surface.

```
                   ┌─────────────────────────────────────────┐
                   │           AUTHORIZATION SERVER           │
                   │                                          │
  User-Agent       │  /authorize          /token             │  Resource Server
      │            │      │                   │              │       │
      │──(1)GET ──────────>│                  │              │       │
      │  ?response_type    │                  │              │       │
      │   =code            │                  │              │       │
      │  &client_id        │                  │              │       │
      │  &redirect_uri     │                  │              │       │
      │  &state=<rand>     │                  │              │       │
      │  &code_challenge   │                  │              │       │
      │   =S256(verifier)  │                  │              │       │
      │                    │──(authenticate)──>              │       │
      │<──(2)redirect ─────│                  │              │       │
      │   ?code=<authz_code│                  │              │       │
      │   &state=<rand>    │                  │              │       │
      │                    │                  │              │       │
      │──(3)POST /token ───────────────────>  │              │       │
      │   code=<authz_code>│                  │              │       │
      │   code_verifier    │                  │              │       │
      │   client_id        │                  │── verify ────>       │
      │                    │                  │   S256(verifier)     │
      │                    │                  │   == stored          │
      │                    │                  │   challenge          │
      │<──(4){access_token,│<─────────────────│              │       │
      │       id_token,    │                  │              │       │
      │       refresh_token│                  │              │       │
      │──(5)GET /resource ──────────────────────────────────────────>│
      │   Authorization:   │                  │              │       │
      │   Bearer <token>   │                  │              │       │
      │<──(6)200 ──────────────────────────────────────────────────<─│
```

PKCE (Proof Key for Code Exchange, RFC 7636) closes the authorization code interception attack. The client generates a random 32-byte `code_verifier`, computes `code_challenge = BASE64URL(SHA256(code_verifier))`, and sends the challenge at step 1. When it exchanges the authorization code at step 3, it sends the raw verifier. The authorization server verifies that `S256(verifier) == stored_challenge` before issuing tokens. An attacker who intercepts the authorization code from the redirect URI cannot exchange it without the verifier, which never traversed the redirect channel.

The `state` parameter at step 1 is a CSRF defense: the client generates a random value, stores it in session, includes it in the authorization request, and validates that the value returned in the redirect matches what it stored. Without it, an attacker can initiate an OAuth flow as themselves, capture the redirect with the authorization code, and trick a victim's browser into completing the flow, binding the attacker's identity to the victim's session (login CSRF).

### Key Derivation with HKDF

For session keys, encryption keys, and MAC keys derived from a master secret, HKDF (RFC 5869) is the standard. It operates in two phases over HMAC-SHA-256. The extract phase takes a potentially non-uniform input key material (IKM) and an optional salt, producing a pseudorandom key (PRK) of fixed length. The expand phase stretches that PRK into an output key of arbitrary length, mixed with an application-specific `info` label that domain-separates different derived keys.

```c
#include <openssl/kdf.h>
#include <openssl/params.h>
#include <string.h>
#include <stdint.h>
#include <stdio.h>

/*
 * Derive a 32-byte session key from master secret using HKDF-SHA256.
 * ikm:  input key material (e.g., ECDH shared secret)
 * salt: random salt (should be 32 bytes of CSPRNG output)
 * info: domain separation label (e.g., "session-key-v1")
 * out:  output buffer, must be 32 bytes
 */
int hkdf_derive_session_key(const uint8_t *ikm,  size_t ikm_len,
                             const uint8_t *salt, size_t salt_len,
                             const char   *info,
                             uint8_t      *out,   size_t out_len) {
    EVP_KDF      *kdf  = EVP_KDF_fetch(NULL, "HKDF", NULL);
    EVP_KDF_CTX  *kctx = EVP_KDF_CTX_new(kdf);
    EVP_KDF_free(kdf);

    OSSL_PARAM params[5];
    params[0] = OSSL_PARAM_construct_utf8_string("digest", "SHA2-256", 0);
    params[1] = OSSL_PARAM_construct_octet_string("key",
                    (void *)ikm, ikm_len);
    params[2] = OSSL_PARAM_construct_octet_string("salt",
                    (void *)salt, salt_len);
    params[3] = OSSL_PARAM_construct_octet_string("info",
                    (void *)info, strlen(info));
    params[4] = OSSL_PARAM_construct_end();

    int rc = EVP_KDF_derive(kctx, out, out_len, params);
    EVP_KDF_CTX_free(kctx);
    return rc > 0 ? 0 : -1;
}
```

The `info` label is what makes HKDF domain
