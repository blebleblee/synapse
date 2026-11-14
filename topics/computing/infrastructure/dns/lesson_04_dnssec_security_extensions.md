# Lesson 4: DNSSEC Chain of Trust, Signature Validation, Key Management, DoH/DoT

## 1. First-Principles Intuition & Invariants

The Domain Name System was designed in 1983 for a world where the internet was a cooperative research network, and authenticity was enforced by social trust rather than cryptographic proof. RFC 882 and RFC 883 gave us a hierarchical, distributed database that could resolve human-readable names to machine-routable addresses at global scale, but they left the fundamental question of origin authentication entirely unanswered. A resolver receiving a response for `example.com` had no mechanism to verify that the answer came from the authoritative nameserver rather than from an adversary who had poisoned the intervening cache.

The attack surface this opened is not merely theoretical. In 2008, Dan Kaminsky demonstrated that the birthday paradox applied to UDP source port and transaction ID entropy made cache poisoning practical at scale: an attacker sending forged responses in parallel with a legitimate query has a non-negligible probability of winning the race before the authoritative answer arrives, injecting a malicious record that persists for the entire TTL of the poisoned entry. The vulnerability is structural, not incidental. UDP is connectionless and stateless, and the only authenticating data in a DNS response is a 16-bit transaction ID and the source port, giving an attacker a search space of approximately 2³² possibilities that a high-bandwidth adversary can exhaust in seconds. The Kaminsky disclosure forced mass emergency patching across every recursive resolver implementation in the world and made the case for DNSSEC with an urgency that years of RFC drafts had failed to achieve.

DNSSEC, formalized across RFC 4033, RFC 4034, and RFC 4035, solves the authentication problem by applying asymmetric cryptography to DNS zone data. The core invariant is straightforward: a zone operator generates a keypair, signs every Resource Record Set (RRSet) in the zone with the private key, and publishes both the signatures and the public key inside the zone itself. A validating resolver can verify those signatures using the public key without any out-of-band communication. The critical word in that sentence is "validating" — DNSSEC is an opt-in protocol, and a resolver that does not perform validation receives no security guarantee regardless of whether the zone is signed.

Understanding DNSSEC from first principles requires internalizing three invariants that govern the entire system. First, DNSSEC authenticates data, not channels. It does not encrypt DNS responses; a wiretapper can read every byte of a DNSSEC-validated exchange. What they cannot do is forge a response that a validating resolver will accept, because they do not possess the zone's private signing key. Second, DNSSEC is a chain, not a point. A validating resolver cannot simply trust a zone's public key because anyone can generate a keypair. Instead, it must receive a cryptographic delegation from the zone's parent, which must itself be trusted by its parent, all the way to the DNS root zone, whose trust anchor is distributed out-of-band to resolvers as a known-good public key. Break any link in that chain and validation fails. Third, DNSSEC is an authenticated denial-of-existence system. The original DNS had no authenticated way to say "this name does not exist," which left resolvers vulnerable to forged NXDOMAIN responses. DNSSEC introduces NSEC and NSEC3 records specifically to provide cryptographically signed proof that a queried name falls between two adjacent signed names in the zone's lexicographic ordering.

The cryptographic foundation of DNSSEC relies on digital signature algorithms registered in the IANA DNS Security Algorithm Numbers registry. Algorithm 8 is RSA/SHA-256, historically the most widely deployed choice. Algorithm 13, ECDSAP256SHA256, uses 256-bit elliptic curve keys over the NIST P-256 curve and has become the preferred modern choice because its signatures are dramatically smaller than RSA-2048 signatures (64 bytes versus 256 bytes) while providing equivalent security. Algorithm 15, Ed25519, uses the Bernstein Curve25519 construction and offers the smallest signatures (64 bytes), the fastest verification, and the strongest resistance to implementation-level timing attacks, making it the emerging best practice for newly signed zones as of 2024. The choice of algorithm propagates downstream into every signed record in the zone, so migration between algorithms requires careful key rollover planning, which we will address in detail in Section 3.

---

## 2. Core Architecture & Mechanics

### The Record Hierarchy: DNSKEY, RRSIG, DS, and NSEC

A DNSSEC-secured zone is built from four new record types that work in concert. Understanding each record's exact wire format and semantic role is a prerequisite for diagnosing validation failures in production.

A **DNSKEY** record publishes a zone's public key at the zone apex. Its wire format encodes three fields before the key material itself: a 16-bit Flags field, a one-byte Protocol field (always 3), and a one-byte Algorithm field. Within the Flags field, bit 7 (the Zone Key flag, value 256) must be set for the key to be used for zone signing, and bit 15 (the Secure Entry Point flag, value 1) conventionally marks a key as a Key Signing Key. The public key data follows as a base64-encoded blob whose length and structure depend on the algorithm. A zone typically carries two distinct DNSKEY records: the **Zone Signing Key** (ZSK) and the **Key Signing Key** (KSK).

The separation of ZSK and KSK is an architectural decision rooted in operational security and key rollover frequency. The ZSK signs every RRSet in the zone and is therefore used continuously by the signing infrastructure, making it desirable to keep it short-lived. A 1024-bit RSA ZSK might be rolled every 30 days. The KSK, by contrast, signs only the DNSKEY RRSet itself and is referenced by the parent zone's DS record. Because rolling the KSK requires coordinating a DS record update with the parent zone operator — an out-of-band process that may take hours or days — KSKs are intentionally long-lived, often 1–2 years. The DNSKEY RRSet thus contains both keys, the ZSK signs everything else, and the KSK signs the DNSKEY RRSet, creating a two-tier key hierarchy within the zone.

An **RRSIG** record provides the actual digital signature over an RRSet. Its wire format is rich: it carries the Type Covered field (the RRtype being signed), the Algorithm, the Labels count (used to detect wildcard expansion), the Original TTL, Signature Expiration and Inception timestamps as 32-bit Unix times, the Key Tag (a 16-bit checksum used to identify the signing DNSKEY), the Signer's Name, and finally the Signature itself. Every distinct RRSet in a signed zone — the SOA, every A record, every MX record, every NS delegation — carries its own RRSIG. This means a zone with 100,000 distinct RRSets carries 100,000 RRSIG records, roughly doubling the zone's storage and transfer footprint. The RRSIG's expiration timestamp is critical: validators check it against their local clock, which creates a time-synchronization dependency and means that signing infrastructure must refresh signatures before they expire, typically with a refresh window of 20–50% of the signature validity period.

A **DS** (Delegation Signer) record lives not in the signed zone but in the parent zone, at the delegation point for the child. It acts as the cryptographic link in the chain of trust. The DS record contains the Key Tag, Algorithm, and a digest of the child zone's KSK DNSKEY record. RFC 4034 originally defined SHA-1 as the only digest algorithm; RFC 4509 added SHA-256, and RFC 6605 added SHA-384. Modern deployments should use SHA-256 (Digest Type 2) at minimum, with SHA-384 (Digest Type 4) for high-security deployments. When a registrar publishes a DS record for a domain, they are asserting "I have verified this hash, and I vouch for the KSK it represents." The parent zone then signs the DS record with its own ZSK, extending the chain upward.

The chain of trust propagates as follows through a concrete validation walk:

```
Root Zone
  └── DNSKEY (KSK) ← trust anchor distributed to resolvers
  └── signs DS for .com
      .com Zone
        └── DNSKEY (KSK) signed by root DS
        └── signs DS for example.com
            example.com Zone
              └── DNSKEY (KSK) signed by .com DS
              └── DNSKEY (ZSK) signed by KSK
              └── A record for www signed by ZSK
```

A validating resolver working bottom-up follows this path: it fetches the RRSIG for the `www.example.com` A record and identifies the Key Tag of the signing ZSK. It fetches the DNSKEY RRSet for `example.com` and finds the ZSK, verifying the A record's RRSIG. It then needs to trust that DNSKEY RRSet, so it checks the RRSIG over the DNSKEY RRSet, finding it was signed by the KSK. To trust the KSK, it queries the parent `.com` zone for a DS record matching the KSK's digest. It finds and verifies the `.com`-signed DS record, then repeats the process up to the root, terminating when it matches a locally configured trust anchor. This is the validation chain in its mechanical entirety.

### The Zone Signing Process with BIND and OpenDNSSEC

In production, zone signing is performed either manually with BIND's `dnssec-keygen` and `dnssec-signzone` utilities, or automatically with a signing daemon like OpenDNSSEC. Manual signing is instructive for understanding the mechanics; automated signing is mandatory at any non-trivial scale.

To sign a zone manually using BIND's toolchain, the workflow begins by generating the KSK and ZSK keypairs:

```sh
# Generate a KSK using ECDSA P-256 (Algorithm 13)
dnssec-keygen -a ECDSAP256SHA256 -b 256 -f KSK -n ZONE example.com

# Generate a ZSK using ECDSA P-256 (Algorithm 13)
dnssec-keygen -a ECDSAP256SHA256 -b 256 -n ZONE example.com
```

Each invocation writes two files: a `.key` file containing the public DNSKEY record and a `.private` file containing the private key material in a structured text format. The `.private` file must never be stored on a machine accessible from the internet and in high-security deployments belongs in a Hardware Security Module (HSM) that exposes only a signing API. The `.key` files are included into the zone file before signing:

```sh
# Include key files into the zone, then sign
cat Kexample.com.+013+*.key >> /etc/bind/zones/example.com.zone

dnssec-signzone \
  -A \
  -3 $(head -c 1000 /dev/random | sha1sum | cut -b 1-16) \
  -N INCREMENT \
  -o example.com \
  -t \
  /etc/bind/zones/example.com.zone \
  Kexample.com.+013+*KSK.private \
  Kexample.com.+013+*ZSK.private
```

The `-3` flag enables NSEC3 with a randomly generated salt, replacing the default NSEC chain with hashed owner names. The output is a file named `example.com.zone.signed` containing every original record plus all generated RRSIG and NSEC3 records. The `-t` flag prints signing statistics, including the total number of RRSets signed and the signature validity window, which should be verified against operational expectations before the signed zone is loaded.

For production deployments, OpenDNSSEC provides a policy-driven signing daemon that handles key generation, HSM integration, automatic ZSK and KSK rollovers, and re-signing before expiry without operator intervention. Its configuration centers on a `kasp.xml` policy file that expresses key lifetimes, algorithm choices, signature validity periods, and rollover strategies declaratively. A representative policy for a medium-scale zone looks like this:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<KASP>
  <Policy name="default">
    <Description>Production DNSSEC policy with ECDSA P-256</Description>

    <Signatures>
      <Resign>PT2H</Resign>
      <Refresh>P3D</Refresh>
      <Validity>
        <Default>P14D</Default>
        <Denial>P14D</Denial>
      </Validity>
      <Jitter>PT12H</Jitter>
      <InceptionOffset>PT3600S</InceptionOffset>
    </Signatures>

    <Denial>
      <NSEC3>
        <OptOut/>
        <Resalt>P100D</Resalt>
        <Hash>
          <Algorithm>1</Algorithm>
          <Iterations>5</Iterations>
          <Salt length="8"/>
        </Hash>
      </NSEC3>
    </Denial>

    <Keys>
      <TTL>PT3600S</TTL>
      <RetireSafety>PT1H</RetireSafety>
      <PublishSafety>PT1H</PublishSafety>
      <Purge>P14D</Purge>

      <KSK>
        <Algorithm length="256">13</Algorithm>
        <Lifetime>P365D</Lifetime>
        <Repository>SoftHSM</Repository>
        <RFC5011rollovers/>
      </KSK>

      <ZSK>
        <Algorithm length="256">13</Algorithm>
        <Lifetime>P30D</Lifetime>
        <Repository>SoftHSM</Repository>
      </ZSK>
    </Keys>

    <Zone>
      <PropagationDelay>PT1H</PropagationDelay>
      <SOA>
        <TTL>PT3600S</TTL>
        <Minimum>PT300S</Minimum>
        <Serial>unixtime</Serial>
      </Zone>

    <Parent>
      <PropagationDelay>PT24H</PropagationDelay>
      <DS>
        <TTL>PT3600S</TTL>
      </DS>
      <SOA>
        <TTL>PT86400S</TTL>
        <Minimum>PT300S</Minimum>
      </SOA>
    </Parent>
  </Policy>
</KASP>
```

The `Resign` interval of two hours means OpenDNSSEC re-evaluates the zone every two hours for signatures approaching expiry. The `Refresh` interval of three days means signatures are refreshed when they have fewer than three days of validity remaining, well within the 14-day validity window. The `Jitter` of 12 hours randomizes refresh timing across a large fleet of zones to prevent synchronized signing bursts from overloading an HSM. The `PropagationDelay` values for both the zone and parent account for the time DNS changes take to propagate through secondary nameservers and caching infrastructure, and OpenDNSSEC uses these values to schedule rollover state transitions safely.

### Authenticated Denial: NSEC vs. NSEC3

Authenticated denial of existence is one of the subtler and more operationally consequential aspects of DNSSEC. The original NSEC (Next Secure) record answers the question "does this name exist?" by encoding the zone's complete ordered name list as a chain: each NSEC record at a given name points to the next name in canonical ordering and lists the RRtypes present at the current name. A query for a nonexistent name `ghost.example.com` returns an NSEC record proving that the lexicographic gap between, say, `ftp.example.com` and `mail.example.com` contains no names, alongside its RRSIG.

The fatal operational flaw of NSEC is zone enumeration. By walking the NSEC chain — querying each next-name in sequence — an attacker can reconstruct the complete list of names in a zone without ever needing access to the zone file or zone transfer privileges. For zones with sensitive internal structure (think `vpn.corp.example.com`, `staging-db.example.com`), this is an unacceptable information leak. NSEC3, defined in RFC 5155, addresses this by hashing owner names before including them in the chain. Instead of `ftp.example.com` → `mail.example.com`, the NSEC3 chain links `H(ftp.example.com)` → `H(mail.example.com)`, where H is an iterated SHA-1 hash with a zone-specific salt. An attacker who obtains the NSEC3 chain cannot reverse the hashes to recover the original names without an offline dictionary attack against each hash.

The iterations parameter in NSEC3 controls how many additional SHA-1 iterations are applied beyond the base hash, with higher values increasing the cost of offline dictionary attacks. However, RFC 9276 (published 2022) recommends setting iterations to 0 and relying on the salt alone, because high iteration counts impose validation overhead on every recursive resolver that processes NSEC3 records while providing only marginal additional protection against modern GPU-accelerated dictionary attacks. The salt should still be changed periodically (the `Resalt` parameter in the OpenDNSSEC policy above is set to 100 days) to invalidate any precomputed rainbow tables.

### Validation in a Recursive Resolver: Unbound's State Machine

The resolver-side of DNSSEC is where the cryptographic machinery meets the operational network. Unbound, the most widely deployed validating resolver in production infrastructure, implements the DNSSEC validation state machine described in RFC 4035 Section 5. When Unbound receives a response with the AD (Authenticated Data) bit set by a nameserver, it does not simply trust that bit — it performs independent validation using the RRSIG records and its own trust anchor store.

Enabling DNSSEC validation in Unbound requires minimal configuration, but the trust anchor is the essential element:

```ini
# /etc/unbound/unbound.conf

server:
    verbosity: 1
    interface: 127.0.0.1
    port: 53
    do-ip4: yes
    do-ip6: yes
    do-udp: yes
    do-tcp: yes

    # Hardened validation settings
    harden-glue: yes
    harden-dnssec-stripped: yes
    harden-below-nxdomain: yes
    harden-referral-path: yes
    harden-algo-downgrade: no
    use-caps-for-id: yes

    # Trust anchor for the DNS root
    auto-trust-anchor-file: "/var/lib/unbound/root.key"

    # Cache sizing for a production resolver (adjust to available RAM)
    msg-cache-size: 128m
    rrset-cache-size: 256m
    neg-cache-size: 32m

    # RFC 5011 automated trust anchor update
    root-hints: "/etc/unbound/root.hints"

    # Aggressive negative caching using NSEC/NSEC3 (RFC 8198)
    aggressive-nsec: yes

    # Prefetch popular records before TTL expiry
    prefetch: yes
    prefetch-key: yes
```

The `harden-dnssec-stripped` directive is critical: it causes Unbound to reject responses that arrive without DNSSEC records when the zone is known to be signed, defeating a stripping attack where a man-in-the-middle removes all RRSIG records from a response to force a downgrade to unsigned resolution. The `aggressive-nsec` directive enables RFC 8198 Aggressive Negative Caching, which allows Unbound to synthesize NXDOMAIN responses for names covered by cached NSEC/NSEC3 records without issuing additional upstream queries, significantly reducing latency for negative responses in signed zones.

The `auto-trust-anchor-file` parameter points to a file initialized with the IANA root zone KSK and updated automatically via RFC 5011's trust anchor rollover mechanism. The root KSK was first rolled in 2018 — the first such rollover in the DNS root's history — and RFC 5011 allows validating resolvers to automatically track KSK rollovers by monitoring the introduction of new DNSKEY records with the SEP flag in a signed zone they already trust. Without RFC 5011 support, a root KSK rollover would require manual updates to every validating resolver globally, which at internet scale is operationally infeasible.

To verify that a resolver is performing DNSSEC validation, the `drill` and `delv` tools provide signature chain output that `dig +dnssec` does not:

```sh
# Verify full chain of trust with drill
drill -S -k /var/lib/unbound/root.key www.example.com

# Perform local DNSSEC validation with delv (BIND's validation tool)
delv @127.0.0.1 +rtrace +vtrace www.example.com A

# Check a deliberately broken zone (should return SERVFAIL with AD=0)
dig @127.0.0.1 +dnssec www.dnssec-failed.org A

# Inspect the full RRSIG record for a live zone
dig @8.8.8.8 +dnssec +multiline cloudflare.com DNSKEY
```

The `dnssec-failed.org` domain is a deliberately misconfigured test zone maintained by ICANN that any correctly validating resolver should return `SERVFAIL` for, providing a quick sanity check that validation is active.

---

## 3. High-Performance Optimization & Failure Modes

### Key Rollover Mechanics and the Double-Signature Window

Key rollover is the operationally riskiest phase of DNSSEC management. The fundamental challenge is that DNS caching means changes do not propagate atomically: at any given moment during a rollover, some resolvers hold the old key in cache while others have fetched the new one. If a zone operator removes the old signing key before all cached copies expire, resolvers that still hold the old key will fail to validate signatures created with the new key. This window of dangerous inconsistency determines the minimum safe rollover timeline.

ZSK rollover follows the pre-publication method described in RFC 6781. The process works as follows. First, the new ZSK is published in the DNSKEY RRSet alongside the old ZSK, without yet being used to sign any records. The zone operator waits for the DNSKEY TTL to expire across all caching resolvers — this is the propagation delay, typically equal to the DNSKEY TTL plus the maximum expected resolver cache time, conservatively 1–2 hours. Second, the new ZSK begins signing all RRSets. At this point, the zone carries signatures from both keys to handle resolvers that cached the old ZSK before the new one propagated. The operator waits for the maximum zone RRSet TTL to pass, ensuring all cached signatures from the old ZSK have expired. Third, the old ZSK is removed from the DNSKEY RRSet, and signing continues exclusively with the new ZSK.

KSK rollover is more involved because it requires parent interaction. The double-DS method is the safer approach: the new KSK is published and the new DS record is submitted to the parent zone, then the operator waits for both old and new DS records to be simultaneously resolvable, then the old KSK is retired. The minimum safe timeline for a KSK rollover accounting for parent zone DS TTL, caching resolver hold times, and secondary nameserver propagation is typically 48–72 hours for a ccTLD or gTLD delegation. Attempting to accelerate this timeline is the single most common cause of DNSSEC-induced outages.

The operational state machine for a ZSK rollover can be visualized as:

```
State 1: ACTIVE
  DNSKEY: [ZSK-old, KSK]
  Signs:  ZSK-old → all RRSets
  Wait:   publish new ZSK, hold for DNSKEY TTL propagation

State 2: DUAL-PUBLISH
  DNSKEY: [ZSK-old, ZSK-new, KSK]
  Signs:  ZSK-old → all RRSets (ZSK-new present but not signing)
  Wait:   DNSKEY TTL + propagation delay (~2h)

State 3: DUAL-SIGN
  DNSKEY: [ZSK-old, ZSK-new, KSK]
  Signs:  ZSK-old → all RRSets AND ZSK-new → all RRSets
  Wait:   maximum RRSet TTL across zone (~24h for most zones)

State 4: ACTIVE-NEW
  DNSKEY: [ZSK-new, KSK]
  Signs:  ZSK-new → all RRSets
  Wait:   verify no validation failures, then retire ZSK-old
```

OpenDNSSEC automates this state machine based on the policy timing parameters defined in `kasp.xml`. Manually managed zones relying on `dnssec-signzone` require an operator-driven checklist, and production incidents consistently trace back to operators skipping the propagation wait in State 2 or the TTL wait in State 3.

### NSEC3 Iteration Count and Validation Performance

Signing infrastructure and validating resolvers both feel the performance cost of NSEC3. Each NSEC3 validation requires the resolver to hash the queried name with the zone's iteration count and salt, compare the result against the returned NSEC3 owner name, and verify the RRSIG over the NSEC3 RRSet. With the iteration count at 0 (as RFC 9276 recommends), a single SHA-1 invocation per name is negligible on modern hardware. At legacy iteration counts of 100 or more, still seen in production zones configured before the RFC 9276 guidance, validation overhead on a high-throughput resolver becomes measurable. At 100 iterations per NSEC3 lookup, a resolver handling 100,000 NXDOMAIN responses per second for a zone with that NSEC3 configuration performs 10 million SHA-1 iterations per second solely for NSEC3 validation, an entirely avoidable cost.

Auditing live zones for NSEC3 iteration counts can be done directly:

```sh
# Check NSEC3PARAM record for a zone's current iteration count
dig +short example.com NSEC3PARAM

# Output format: algorithm flags iterations salt
# Example: 1 0 5 AB12CD34EF56 (algorithm 1=SHA-1, 5 iterations)
# Modern best practice: 1 0 0 - (0 iterations, no salt shown as -)
```

Zones still carrying iteration counts above 10 should be treated as a performance and security hygiene issue and scheduled for re-signing with updated parameters.

### Signature Expiry and Clock Skew Failures

The most operationally insidious DNSSEC failure mode is signature expiry. RRSIG records carry hard expiration timestamps, and a validating resolver that receives an expired RRSIG returns `SERVFAIL` unconditionally. This means a zone whose signing infrastructure fails silently — an OpenDNSSEC daemon that stopped processing, an HSM that became inaccessible, a cron job that failed without alerting — will appear fully functional to non-validating resolvers and completely broken to validating ones. The failure is invisible to operators checking with `dig` from an unvalidating client.

Monitoring RRSIG expiry requires explicit probing. The following script checks the minimum remaining validity across all RRSIG records for a zone and alerts when the margin drops below a threshold:

```python
#!/usr/bin/env python3
"""
rrsig_expiry_check.py - Monitor DNSSEC signature expiry for a zone.
Exits with code 2 (CRITICAL) if min expiry is below critical_hours,
code 1 (WARNING) if below warning_hours, code 0 (OK) otherwise.
"""

import subprocess
import sys
import re
from datetime import datetime, timezone, timedelta

ZONE = "example.com"
NAMESERVER = "127.0.0.1"
WARNING_HOURS = 72
CRITICAL_HOURS = 24

def parse_rrsig_expiry(rrsig_line: str) -> datetime | None:
    """
    Extract the signature expiration timestamp from an RRSIG record.
    RRSIG wire format field 5 is the expiration in YYYYMMDDHHmmSS format.
    """
    parts = rrsig_line.split()
    # RRSIG rdata: type alg labels ottl expiry inception keytag signer sig
    # After 'RRSIG': covered alg labels ottl expiry inception keytag signer sig
    # dig output: name ttl class RRSIG covered alg labels ottl expiry inception ...
    for i, part in enumerate(parts):
        if part == "RRSIG":
            expiry_str = parts[i + 5]
            try:
                return datetime.strptime(expiry_str, "%Y%m%d%H%M%S").replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                return None
    return None

def get_zone_rrsigs(zone: str, ns: str) -> list[datetime]:
    result = subprocess.run(
        ["dig", f"@{ns}", "+dnssec", "+noall", "+answer", zone, "SOA"],
        capture_output=True, text=True, timeout=10
    )
    expiries = []
    for line in result.stdout.splitlines():
        if "RRSIG" in line:
            ts = parse_rrsig_expiry(line)
            if ts:
                expiries.append(ts)
    return expiries

now = datetime.now(timezone.utc)
expiries = get_zone_rrsigs(ZONE, NAMESERVER)

if not expiries:
    print(f"UNKNOWN: No RRSIG records found for {ZONE}")
    sys.exit(3)

min_expiry = min(expiries)
hours_remaining = (min_expiry - now).total_seconds() / 3600

if hours_remaining < CRITICAL_HOURS:
    print(f"CRITICAL: Minimum RRSIG expiry in {hours_remaining:.1f}h ({min_expiry.isoformat()})")
    sys.exit(2)
elif hours_remaining < WARNING_HOURS:
    print(f"WARNING: Minimum RRSIG expiry in {hours_remaining:.1f}h ({min_expiry.isoformat()})")
    sys.exit(1)
else:
    print(f"OK: Minimum RRSIG expiry in {hours_remaining:.1f}h ({min_expiry.isoformat()})")
    sys.exit(0)
```

This script integrates directly into Nagios, Icinga, or any monitoring system that interprets exit codes. In production, it should probe multiple RRtypes (SOA, A, MX, NS) and all RRSIG records for the zone apex to catch partial signing failures where only some RRtypes have expired signatures. Clock skew between the signing host and validating resolvers is a related failure vector: if the signing host's clock drifts forward, it generates signatures whose inception time is in the future from the resolver's perspective, causing `RRSIG_BEFORE_INCEPTION` validation failures. NTP synchronization with multiple stratum-2 sources and a maximum allowed drift of under 100 seconds is a hard dependency for any DNSSEC-enabled zone.

### DNS-over-TLS and DNS-over-HTTPS: Transport Authentication

DNSSEC authenticates data at the record level but does nothing to protect the transport channel. A passive observer watching the wire can still enumerate every query a client makes, correlate DNS lookups with browsing behavior, and perform timing attacks based on query patterns. This is precisely the problem that DNS-over-TLS (DoT, RFC 7858) and DNS-over-HTTPS (DoH, RFC 8484) address, using entirely different architectural approaches.

DoT establishes a TLS 1.3 session between the DNS client and resolver on TCP port 853. The DNS messages flow over this TLS session using the same length-prefixed wire format used for DNS-over-TCP, with a 2-byte big-endian length prefix before each message. The resolver authenticates to the client via its TLS certificate, which the client validates against either a system certificate store or a pinned certificate hash. From an infrastructure standpoint, DoT is relatively straightforward to deploy on Unbound:

```ini
# /etc/unbound/unbound.conf additions for DoT

server:
    # Listen on 853 for DoT in addition to 53
    interface: 0.0.0.0@853
    interface: 0.0.0.0@53

    # TLS configuration
    tls-service-key: "/etc/unbound/tls/server.key"
    tls-service-pem: "/etc/unbound/tls/server.pem"
    tls-port: 853

    # Enforce minimum TLS version
    tls-min-version: "TLSv1.3"
    tls-ciphers: "TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256"

    # SPKI pin validation for clients that use certificate pinning
    # (populate with: openssl x509 -in server.pem -pubkey -noout |
    #  openssl pkey -pubin -outform DER | openssl dgst -sha256 -binary | base64)
    tls-additional-port: 853
```

DoH takes a fundamentally different approach: DNS messages are carried as the bodies of HTTPS requests to a standard HTTPS endpoint, typically at a path like `/dns-query`. The request method can be GET (with the DNS message base64url-encoded as a `dns` query parameter) or POST (with the DNS message as the raw request body, Content-Type `application/dns-message`). DoH traffic is visually indistinguishable from any other HTTPS traffic to a port-443 observer, which makes it both maximally privacy-preserving and maximally resistant to network-level blocking.

Configuring Unbound to serve DoH requires a frontend proxy, since Unbound natively speaks DNS-over-TCP/UDP and needs an HTTP/2 terminator in front of it for DoH. The standard production pattern uses `nginx` or Cloudflare's `dnsproxy` as the HTTPS frontend forwarding to Unbound on a loopback DoT or DNS-over-TCP socket:

```nginx
# /etc/nginx/sites-available/doh-proxy

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name dns.example.com;

    ssl_certificate     /etc/ssl/certs/dns.example.com.pem;
    ssl_certificate_key /etc/ssl/private/dns.example.com.key;
    ssl_protocols       TLSv1.3;
    ssl_ciphers         TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256;

    # RFC 8484 DoH endpoint
    location /dns-query {
        proxy_pass         http://127.0.0.1:8053;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;

        # Required Content-Type for DoH
        proxy_set_header   Accept application/dns-message;

        # Disable response buffering - DNS responses are small and latency-sensitive
        proxy_buffering    off;
        proxy_read_timeout 10s;
        proxy_send_timeout 10s;

        # RFC 8484 requires HTTP/2 support
        # Allow both GET and POST methods
        limit_except GET POST {
            deny all;
        }
    }

    # Health check endpoint for load balancers
    location /health {
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }
}
```

For the DoH backend on port 8053, `dnsdist` provides a production-grade DNS load balancer and protocol translator with native DoH support, capable of accepting DoH and forwarding to Unbound as standard DNS, with per-client rate limiting, query filtering, and observability built in:

```lua
-- /etc/dnsdist/dnsdist.conf

-- Accept DoH on port 8053 from nginx proxy
addDOHLocal("127.0.0.1:8053",
  "/etc/ssl/certs/dns.example.com.pem",
  "/etc/ssl/private/dns.example.com.key",
  {"/dns-query"},
  {
    reusePort = true,
    maxConcurrentTCPConnections = 2000,
    tcpFastOpen = true,
  }
)

-- Forward to local Unbound validator
newServer({
  address = "127.0.0.1:53",
  name = "unbound-local",
  checkName = "dns.example.com",
  healthCheckMode = "active",
  maxCheckFailures = 3,
  rise = 2,
})

-- Rate limiting: max 100 queries/sec per source IP
addAction(MaxQPSIPRule(100), DropAction())

-- Log queries for observability (disable in production unless needed)
-- addAction(AllRule(), LogAction("/var/log/dnsdist/queries.log", false, true, true))

-- Set ECS on forwarded queries for geolocation-aware backends
setECS(true)
```

The fundamental architectural difference between DoT and DoH carries operational implications beyond protocol mechanics. DoT uses a dedicated port (853) that network operators can inspect, block, or monitor at the firewall level, which some enterprise and government network operators require for compliance and audit purposes. DoH uses port 443 and cannot be distinguished from HTTPS traffic without TLS inspection, making it effectively uncensorable at the transport layer. This is a feature for end-user privacy and an operational challenge for network administrators who need visibility into DNS traffic for security monitoring, threat intelligence correlation, and regulatory compliance. The deployment decision between DoT and DoH is therefore as much a network governance decision as a technical one.

DNSSEC and encrypted DNS transport are complementary, not redundant. DoT/DoH ensures that the query path between client and resolver is confidential and authenticated to the correct resolver. DNSSEC ensures that the resolver-to-authoritative path produces responses that cannot be forged, regardless of whether the transport between resolver and client is encrypted. A fully hardened DNS stack deploys both: DNSSEC validation at the recursive resolver, DoT or DoH between client and resolver, and monitoring for RRSIG expiry, key rollover state, and validation failure rates. Neither mechanism alone provides end-to-end cryptographic integrity, but together they close the two principal attack surfaces that have made DNS the most reliably exploitable layer of the internet stack for forty years.
