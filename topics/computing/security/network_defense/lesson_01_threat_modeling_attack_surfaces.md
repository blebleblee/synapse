# Lesson 1: Threat Modeling, Attack Surfaces, Kill Chain Analysis

## 1. First-Principles Intuition & Invariants

Every defensive posture begins with a question that is deceptively simple to ask and extraordinarily difficult to answer with rigor: *what are you actually defending, and against whom?* Without a disciplined answer, security spending becomes noise, detection rules become folklore, and incident response becomes improvisation. Threat modeling is the practice of turning that question into a structured, falsifiable engineering artifact — a living document that maps assets to adversaries, adversaries to capabilities, and capabilities to concrete attack paths that can be measured, monitored, and mitigated.

The historical failure mode of enterprise security was perimeter thinking: the assumption that the network boundary was a moat and that anything inside it was inherently trustworthy. This model collapsed under the weight of several converging realities — the proliferation of supply-chain implants, the normalization of remote access, the blurring of corporate and cloud infrastructure, and the sustained capability of nation-state actors who routinely dwell inside networks for months before triggering any observable effect. The 2020 SolarWinds intrusion remains the canonical autopsy: adversaries compromised the build pipeline of a trusted vendor, injected a backdoor into signed software updates, and established persistent footholds across eighteen thousand organizations before detection. No perimeter control would have caught it, because the attack entered through a trusted and authenticated software distribution channel. The lesson is not that defenses failed; it is that the wrong threat model was in force.

The first invariant of threat modeling is that it must be asset-centric, not technology-centric. A firewall rule is not a defense; it is a mechanism. A defense is the guarantee that a specific adversary cannot achieve a specific objective against a specific asset within a specific timeframe. This framing forces precision. It compels the defender to name the adversary, characterize their capability tier (script kiddie, financially motivated cybercriminal, advanced persistent threat), identify the crown-jewel assets (firmware signing keys, JTAG debug interfaces, HSM key material, network control planes), and reason about the asymmetry between attack cost and defense cost for each path.

The second invariant is that attack surfaces are not static. Every time a firmware engineer pushes a new build to a device fleet, every time a network operator adds a BGP peer, every time a CI/CD pipeline gains a new integration, the attack surface changes. Treating threat modeling as a one-time exercise produces a document that is accurate on its creation date and increasingly fictional thereafter. Industrial control system (ICS) environments suffer this acutely — legacy PLCs running unauthenticated Modbus over serial were never designed for IP reachability, but decades of digital transformation have slowly connected them to enterprise networks, often without revisiting the original threat model that assumed air-gapped isolation. The result is a surface that the original designers never contemplated.

The third invariant is threat intelligence coupling. A threat model built without empirical data about real adversary behavior is a thought experiment. When it is grounded in structured intelligence — MITRE ATT&CK technique prevalence, CISA Known Exploited Vulnerabilities (KEV) catalog data, vendor-specific PSIRT advisories, and sector-specific ISAC threat feeds — it becomes predictive. The model can answer: given observed adversary TTPs (Tactics, Techniques, and Procedures) against organizations in my sector over the past twelve months, which of my current control gaps represent the highest-probability exploitation paths?

This coupling between threat intelligence and architectural analysis is the core skill this lesson develops. By the end, you will be able to build a formal adversary model, enumerate an attack surface with mechanical precision, map observed threat intelligence onto the kill chain, and produce a quantified risk register that drives prioritized defensive investment.

---

## 2. Core Architecture & Mechanics

### Adversary Modeling: Capability, Intent, and Opportunity

The classical intelligence community framing of threat as the intersection of capability, intent, and opportunity translates directly into an engineering model. Capability describes what an adversary can do — their tool inventory, zero-day holdings, operational infrastructure, and human resources. Intent describes why they would target you — financial gain, espionage, sabotage, or ideological motivation. Opportunity describes what access the adversary can realistically obtain, given your exposure profile.

For hardware security researchers and embedded engineers, adversary modeling must extend below the software abstraction layer. The threat actors relevant to this domain include nation-state implant teams capable of hardware supply-chain interdiction (documented in the NSA ANT catalog and later confirmed through academic research), firmware persistence actors who survive OS reinstalls by targeting UEFI/BIOS flash regions or BMC firmware, and financially motivated actors targeting embedded devices as botnet nodes or pivot points into industrial networks. Each of these actor classes has a distinct capability profile and attacks a distinct layer of the stack.

A practical adversary model for an embedded system might look like this:

```
Actor: Nation-State APT (Tier 1)
  Capability: Hardware implant fabrication, JTAG-based firmware extraction,
              side-channel analysis (DPA/SPA), supply chain access
  Intent:     Persistent surveillance, pre-positioned destructive capability
  Opportunity: Pre-deployment supply chain, exposed debug interfaces (JTAG/UART),
               unencrypted firmware update channels
  Priority Assets: Firmware signing keys, secure boot chain, comms encryption keys

Actor: Financially Motivated Actor (Tier 2)
  Capability: Public exploit tooling, known CVE weaponization, credential stuffing,
              botnet C2 infrastructure
  Intent:     Crypto mining, data exfiltration for resale, ransomware deployment
  Opportunity: Internet-exposed management interfaces, default credentials,
               unpatched services
  Priority Assets: Device compute, stored credentials, network pivot access
```

This structure forces you to reason about which controls are actually effective against which actors. Disabling JTAG and enforcing Secure Boot defeats the Tier 1 hardware adversary's physical access path; it has no effect on the Tier 2 actor exploiting CVE-2023-20198 on an exposed Cisco IOS XE management interface. Conflating these actor classes leads to either over-engineering against realistic threats or under-defending against nation-state capability.

### Attack Surface Enumeration

Attack surface enumeration is the systematic process of identifying every point at which an adversary can interact with a system to influence its state. The critical word is "every" — the surface must be comprehensive, because adversaries will find the entry point the defender forgot.

For networked systems, the surface decomposes into logical layers. At the network layer, the attack surface is defined by IP address space, exposed TCP/UDP port bindings, protocol parsers running on those ports, and the authentication gates (or absence thereof) protecting them. At the application layer, it includes every code path that processes external input: HTTP endpoints, SNMP OIDs, MQTT topics, Modbus register maps, and DNS query handlers. At the host layer, it includes local privilege escalation paths, kernel driver interfaces (`/dev/*`, ioctl surfaces), and scheduled job configurations. At the firmware layer, it includes update mechanisms, bootloader interfaces, hardcoded credentials, and cryptographic key storage.

The attack surface of a modern embedded device running a network-connected application is deeper than it appears. Consider a router running OpenWrt: the exposed surface includes the LuCI web interface (HTTP/HTTPS), SSH daemon, any enabled network services (dnsmasq, odhcp6c), the kernel's netfilter subsystem handling every inbound packet, the UCI configuration daemon, and the bootloader's recovery mode accessible over the serial console. A complete surface map requires both black-box network scanning and white-box source-level analysis.

```
+----------------------------------------------------------+
|                   ATTACK SURFACE MAP                      |
+----------------------------------------------------------+
|                                                          |
|  External Network          Firmware / Hardware           |
|  ┌─────────────────┐       ┌────────────────────────┐   |
|  │ TCP/UDP Ports   │       │ UART/Serial Console    │   |
|  │ Protocol Parsers│       │ JTAG Debug Interface   │   |
|  │ TLS Certificate │       │ SPI Flash (r/w)        │   |
|  │ Exposed APIs    │       │ U-Boot Recovery Mode   │   |
|  └────────┬────────┘       └────────────┬───────────┘   |
|           │                             │               |
|           ▼                             ▼               |
|  ┌─────────────────┐       ┌────────────────────────┐   |
|  │ Application     │       │ Kernel / OS Layer      │   |
|  │ Web UI / API    │       │ Syscall Surface        │   |
|  │ MQTT / AMQP     │       │ Driver ioctl()         │   |
|  │ SNMP / Netconf  │       │ /proc, /sys, /dev      │   |
|  └────────┬────────┘       └────────────┬───────────┘   |
|           │                             │               |
|           └─────────────┬───────────────┘               |
|                         ▼                               |
|              ┌──────────────────────┐                   |
|              │  Trust Boundary /    │                   |
|              │  Authentication Gate │                   |
|              └──────────────────────┘                   |
+----------------------------------------------------------+
```

Automated surface enumeration begins with `nmap` for port and service discovery, followed by protocol-specific tooling. For web surfaces, `feroxbuster` performs recursive directory and endpoint brute-forcing against HTTP targets. For embedded firmware surfaces, `binwalk` extracts filesystem images from raw firmware blobs, after which `checksec` assesses binary hardening flags (NX, stack canaries, PIE, RELRO) across every extracted ELF binary. The gap between what `checksec` reports and what a modern hardened system should provide is a direct measure of attack surface exposure.

```bash
# Full port scan with service version fingerprinting and default script execution
nmap -sV -sC -p- --min-rate 5000 -oA surface_scan 192.168.1.1

# Extract and analyze firmware filesystem
binwalk -e --run-as=root firmware.bin
find _firmware.bin.extracted/ -type f -name "*.so" -o -name "*.elf" | \
  xargs -I{} checksec --file={}

# Enumerate HTTP attack surface recursively
feroxbuster --url http://192.168.1.1 --depth 3 --wordlist /usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt --output surface_http.txt

# Enumerate SNMP surface for exposed OIDs
snmpwalk -v2c -c public 192.168.1.1 1.3.6.1 2>/dev/null | head -100
```

The output of these commands feeds directly into the threat model's attack surface register. Each finding maps to an adversary capability: an open SNMP port with a default community string is an opportunity for a Tier 2 actor; an UART console accessible without authentication is an opportunity for a Tier 1 actor with physical access.

### MITRE ATT&CK: From Framework to Operational Intelligence

MITRE ATT&CK is a knowledge base of adversary behaviors organized as a matrix of tactics (the "why" of an action — the adversary's immediate technical goal) and techniques (the "how" — the specific method used to achieve that goal). The Enterprise ATT&CK matrix covers fourteen tactics from Reconnaissance through Impact. The ICS-specific matrix extends this to cover behaviors unique to industrial control systems, including Stage Capabilities for destructive effects on physical processes.

The power of ATT&CK is not in the matrix itself but in how it enables defenders to reason about detection coverage. Each technique has documented data sources — the telemetry streams that would surface it. Technique T1190 (Exploit Public-Facing Application) surfaces in web server logs, WAF events, and network flow anomalies. Technique T1059.004 (Unix Shell command execution) surfaces in process creation events, shell history, and auditd logs. When you map your existing detection rules against the ATT&CK matrix, the gaps between covered techniques and uncovered techniques reveal your blind spots with precision.

```python
#!/usr/bin/env python3
"""
attack_surface_coverage.py
Maps a set of detection rules against ATT&CK technique IDs
to produce a coverage gap report. Requires mitreattack-python.

Install: pip install mitreattack-python requests
"""

import json
import requests
from mitreattack.stix20 import MitreAttackData

# Fetch ATT&CK Enterprise STIX bundle (cache locally in production)
STIX_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
STIX_PATH = "enterprise-attack.json"

def fetch_stix(url: str, path: str) -> None:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)

def load_covered_techniques(rules_path: str) -> set[str]:
    """
    Parses a JSON file containing detection rules, each with an
    'attack_technique' field (e.g., 'T1190', 'T1059.004').
    """
    with open(rules_path) as f:
        rules = json.load(f)
    return {rule["attack_technique"] for rule in rules if "attack_technique" in rule}

def coverage_gap_report(stix_path: str, covered: set[str]) -> None:
    attack_data = MitreAttackData(stix_path)
    techniques = attack_data.get_techniques(remove_revoked_deprecated=True)

    print(f"{'Technique ID':<16} {'Name':<55} {'Covered'}")
    print("-" * 85)

    covered_count = 0
    for technique in sorted(techniques, key=lambda t: t.external_references[0].external_id):
        tid = technique.external_references[0].external_id
        name = technique.name
        is_covered = tid in covered
        if is_covered:
            covered_count += 1
        marker = "YES" if is_covered else "--- GAP ---"
        print(f"{tid:<16} {name[:54]:<55} {marker}")

    total = len(techniques)
    pct = (covered_count / total) * 100 if total else 0
    print(f"\nCoverage: {covered_count}/{total} techniques ({pct:.1f}%)")

if __name__ == "__main__":
    import sys
    import os

    if not os.path.exists(STIX_PATH):
        print("Fetching ATT&CK STIX bundle...")
        fetch_stix(STIX_URL, STIX_PATH)

    rules_file = sys.argv[1] if len(sys.argv) > 1 else "detection_rules.json"
    covered_techniques = load_covered_techniques(rules_file)
    coverage_gap_report(STIX_PATH, covered_techniques)
```

A sample `detection_rules.json` for testing:

```json
[
  {"id": "rule-001", "name": "Exploit Public-Facing App", "attack_technique": "T1190"},
  {"id": "rule-002", "name": "Unix Shell Exec",           "attack_technique": "T1059.004"},
  {"id": "rule-003", "name": "Valid Account Logon",       "attack_technique": "T1078"},
  {"id": "rule-004", "name": "Scheduled Task Creation",   "attack_technique": "T1053.005"},
  {"id": "rule-005", "name": "Data Exfil over C2",        "attack_technique": "T1041"}
]
```

Running this against the full ATT&CK Enterprise matrix will typically reveal that even mature organizations cover fewer than 30% of techniques. The gap report becomes the input to detection engineering prioritization.

### The Cyber Kill Chain: Mechanistic Stage Analysis

The Lockheed Martin Cyber Kill Chain models an intrusion as a linear progression of seven stages, each of which represents an adversary action that creates a defensive opportunity. Understanding each stage mechanistically — what system calls are made, what network connections are established, what filesystem artifacts are created — is what separates the practitioner from the theorist.

```
+---------------------------------------------------------------------+
|                    CYBER KILL CHAIN STAGES                          |
+---------------------------------------------------------------------+
|                                                                     |
|  [1] Reconnaissance → [2] Weaponization → [3] Delivery             |
|         ↓                      ↓                  ↓                |
|  OSINT, scanning       Exploit + payload    Phishing, drive-by,     |
|  cert transparency     assembly             supply chain, USB drop  |
|                                                                     |
|  [4] Exploitation → [5] Installation → [6] C2 → [7] Actions        |
|         ↓                   ↓               ↓          ↓            |
|  CVE trigger,          Backdoor, cron,  Beacon out,  Exfil,         |
|  memory corruption     LD_PRELOAD,      DNS tunnel,  lateral        |
|  ROP chain             firmware patch   HTTPS C2     movement,      |
|                                                                     |
|  Defender Break Points:                                             |
|  ◉ Stage 1: Reduce OSINT exposure, rate-limit scanners              |
|  ◉ Stage 3: Email gateway, TLS inspection, integrity verification   |
|  ◉ Stage 4: Patch cadence, WAF, exploit mitigations (NX, CFI)      |
|  ◉ Stage 5: File integrity monitoring, auditd, immutable rootfs     |
|  ◉ Stage 6: DNS RPZ, TLS certificate pinning, anomalous flow detect |
|  ◉ Stage 7: Data loss prevention, network segmentation, honeypots  |
+---------------------------------------------------------------------+
```

The kill chain's most important property for the defender is that disruption at any stage denies the adversary their ultimate objective. This is not equally true of all stages, however. Disruption at Stage 1 (Reconnaissance) is lowest-fidelity because reconnaissance activity is often indistinguishable from legitimate internet scanning. Disruption at Stage 6 (Command and Control) is highest-fidelity and highest-impact — an adversary who cannot beacon out cannot receive tasking, exfiltrate data, or propagate. This is why network egress controls and DNS monitoring are disproportionately valuable defensive investments compared to their cost.

For firmware and embedded environments, the kill chain requires extension. Stage 5 (Installation) can target the bootloader — a persistent implant written to the BIOS flash region, BMC firmware, or option ROM survives OS reinstallation and hard drive replacement. Detection at this stage requires firmware integrity measurement, which is architecturally achieved through the NIST SP 800-193 Platform Firmware Resiliency framework: the firmware must be protected (authenticated update, write-lock), detected (measured boot via TPM PCR extension), and recovered (a known-good fallback image stored in a protected region).

Measuring boot integrity with `tpm2-tools` on a Linux system:

```bash
# Read all PCR banks to establish baseline (run on known-good system)
tpm2_pcrread sha256 > pcr_baseline_$(date +%Y%m%d).txt

# On subsequent boots, compare against baseline
tpm2_pcrread sha256 > pcr_current.txt
diff pcr_baseline_*.txt pcr_current.txt

# PCR0: BIOS/UEFI firmware measurement
# PCR1: BIOS configuration
# PCR2: Option ROM code
# PCR4: MBR / bootloader
# PCR7: Secure Boot policy
# Any unexpected change to PCR0, PCR2, or PCR4 indicates firmware tampering.
```

A PCR value change outside of a planned firmware update constitutes a kill chain Stage 5 indicator and should trigger immediate isolation and forensic imaging of the affected system.

### Threat Intelligence Integration: Structured and Unstructured Feeds

Raw threat intelligence is high-volume and low-signal. The practitioner's challenge is ingesting it into a form that generates actionable detection logic within hours of a threat actor publishing new infrastructure or tooling. The structured exchange formats that enable this are STIX 2.1 (Structured Threat Information Expression) and TAXII 2.1 (Trusted Automated Exchange of Intelligence Information), which together define a data model for threat actors, campaigns, indicators of compromise (IoCs), attack patterns, and courses of action, plus a protocol for distributing that model in real time.

An IoC is the most atomic unit of threat intelligence: a file hash, IP address, domain name, URL, or certificate thumbprint associated with adversary activity. IoCs expire quickly — adversaries rotate infrastructure on timescales of hours to days — which is why behavioral indicators (TTPs from ATT&CK) have longer operational value than point IoCs. A firewall rule blocking a specific C2 IP address stops working the moment the adversary rotates to new infrastructure; a detection rule that flags outbound connections carrying the specific HTTP User-Agent string hardcoded in a commodity RAT continues to fire even after the IP changes.

```python
#!/usr/bin/env python3
"""
stix_ioc_extractor.py
Fetches a STIX 2.1 bundle from a TAXII 2.1 server and extracts
network-observable IoCs (IPs, domains, URLs) for firewall/DNS block.

Install: pip install taxii2-client stix2
"""

from taxii2client.v21 import Server, Collection
from stix2 import parse
import json

TAXII_SERVER   = "https://cti-taxii.mitre.org/taxii/"
COLLECTION_ID  = "95ecc380-afe9-11e4-9b6c-751b66dd541e"  # ATT&CK Enterprise
OUTPUT_FILE    = "network_iocs.json"

def extract_network_iocs(bundle_json: dict) -> list[dict]:
    iocs = []
    for obj in bundle_json.get("objects", []):
        if obj.get("type") != "indicator":
            continue
        pattern = obj.get("pattern", "")
        name    = obj.get("name", "unknown")
        created = obj.get("created", "")

        # Parse STIX2 patterns for network observables
        if "ipv4-addr:value" in pattern or "domain-name:value" in pattern or "url:value" in pattern:
            iocs.append({
                "id":      obj.get("id"),
                "name":    name,
                "pattern": pattern,
                "created": created,
                "valid_until": obj.get("valid_until", "indefinite"),
            })
    return iocs

def fetch_and_extract(server_url: str, collection_id: str) -> None:
    server     = Server(server_url)
    api_root   = server.api_roots[0]
    collection = Collection(f"{api_root.url}collections/{collection_id}/objects/")

    print(f"Fetching STIX bundle from {collection.url}...")
    bundle = collection.get_objects()

    iocs = extract_network_iocs(bundle)
    print(f"Extracted {len(iocs)} network-observable IoCs")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(iocs, f, indent=2)
    print(f"Written to {OUTPUT_FILE}")

if __name__ == "__main__":
    fetch_and_extract(TAXII_SERVER, COLLECTION_ID)
```

The extracted IoC list feeds directly into network controls: DNS RPZ (Response Policy Zone) entries for domain indicators, firewall ACL generation for IP indicators, and Suricata or Zeek signatures for URL and behavioral pattern indicators.

---

## 3. High-Performance Optimization & Failure Modes

### Risk Quantification: From Qualitative Heatmaps to FAIR Modeling

The traditional risk matrix — a 5x5 grid of likelihood versus impact rated on a 1-to-5 scale — is intuitive but analytically weak. It produces ordinal rankings that cannot be meaningfully aggregated, it hides variance, and it generates false precision. Two risks rated "High / High" can differ by multiple orders of magnitude in expected annual loss, but the matrix treats them identically. For security programs making capital allocation decisions, this imprecision has real costs.

The Factor Analysis of Information Risk (FAIR) framework addresses this by modeling risk as a probability distribution over loss magnitude, computed from the intersection of Threat Event Frequency (TEF), Vulnerability (the probability that a threat event results in a loss), and Loss Magnitude (the range of financial impact across primary and secondary loss factors). FAIR uses Monte Carlo simulation to propagate the uncertainty in each input through to a distribution of probable annual loss.

```python
#!/usr/bin/env python3
"""
fair_monte_carlo.py
Implements a simplified FAIR risk quantification model using
Monte Carlo simulation with PERT distributions for each input.

Scenario: Remote code execution on an internet-facing embedded device
          leading to exfiltration of sensitive operational data.

Install: pip install numpy scipy matplotlib
"""

import numpy as np
from scipy.stats import beta
import matplotlib.pyplot as plt

RNG  = np.random.default_rng(42)
RUNS = 100_000

def pert(low: float, mode: float, high: float, size: int) -> np.ndarray:
    """
    PERT distribution via Beta approximation.
    Commonly used in risk modeling for bounded, unimodal estimates.
    """
    mean  = (low + 4 * mode + high) / 6.0
    stdev = (high - low) / 6.0
    if stdev == 0:
        return np.full(size, mean)
    alpha = ((mean - low) / (high - low)) * ((mean - low) * (high - mean) / stdev**2 - 1)
    bta   = alpha * (high - mean) / (mean - low)
    alpha = max(alpha, 1e-6)
    bta   = max(bta, 1e-6)
    samples = beta.rvs(alpha, bta, size=size, random_state=RNG)
    return low + samples * (high - low)

# --- FAIR Inputs (USD, per-year frequencies) ---
# Threat Event Frequency: how often does the adversary attempt exploitation?
tef = pert(low=1.0, mode=4.0, high=12.0, size=RUNS)   # 1–12 times/year

# Vulnerability: probability a given attempt succeeds (0–1)
vuln = pert(low=0.05, mode=0.25, high=0.60, size=RUNS)

# Loss Event Frequency = TEF * Vulnerability
lef = tef * vuln

# Primary Loss: direct financial impact per loss event ($)
#   Incident response labor + forensics + device recall/reflash
primary_loss = pert(low=15_000, mode=75_000, high=250_000, size=RUNS)

# Secondary Loss: regulatory fines, reputational damage, customer notification
secondary_loss = pert(low=10_000, mode=50_000, high=500_000, size=RUNS)

total_loss_per_event = primary_loss + secondary_loss

# Annualized Loss Exposure (ALE) = LEF * Total Loss per Event
ale = lef * total_loss_per_event

# --- Reporting ---
p5, p50, p95 = np.percentile(ale, [5, 50, 95])
print(f"Annualized Loss Exposure (ALE) — Monte Carlo ({RUNS:,} runs)")
print(f"  5th percentile : ${p5:>12,.0f}")
print(f"  50th percentile: ${p50:>12,.0f}  (median)")
print(f"  95th percentile: ${p95:>12,.0f}")
print(f"  Mean           : ${ale.mean():>12,.0f}")

plt.figure(figsize=(10, 5))
plt.hist(ale, bins=200, color="#c0392b", edgecolor="none", alpha=0.85)
plt.axvline(p50,  color="white",   linestyle="--", linewidth=1.5, label=f"Median  ${p50:,.0f}")
plt.axvline(p95,  color="#e67e22", linestyle="--", linewidth=1.5, label=f"95th pct ${p95:,.0f}")
plt.xlabel("Annualized Loss Exposure (USD)")
plt.ylabel("Simulation Frequency")
plt.title("FAIR Monte Carlo: RCE on Internet-Facing Embedded Device")
plt.legend()
plt.tight_layout()
plt.savefig("fair_ale_distribution.png", dpi=150)
print("Distribution plot saved to fair_ale_distribution.png")
```

The output of a FAIR model is actionable in a way that a risk matrix never is. If the median ALE is $175,000 and a proposed control — say, moving the device management interface behind a VPN with hardware MFA — costs $40,000 per year in infrastructure and operational overhead, the security program can demonstrate a positive return with probability greater than the 5th percentile confidence interval. This is the language that capital allocation decisions require.

### Threat Model Maintenance and Failure Modes

A threat model that is not updated is a liability. The most common failure mode is calcification: the initial model is thorough, it is approved by stakeholders, it enters a documentation system, and it is never revisited. The organization's infrastructure evolves, new services are deployed, the adversary capability landscape shifts, and the threat model continues to reflect a system that no longer exists.

The correct engineering discipline is to treat threat model updates as part of the change management process. Every pull request that modifies a network-exposed service, every infrastructure change that adds a new external endpoint, and every vendor component update should trigger a threat model delta review. This does not require re-running the full threat modeling exercise; it requires answering three questions: Does this change add a new entry point? Does this change touch a trust boundary? Does this change grant elevated access to a new component or identity? A "yes" to any of these questions triggers a targeted surface re-enumeration and ATT&CK mapping for the affected component.

A second failure mode is the conflation of vulnerability scanning with threat modeling. A vulnerability scanner identifies known CVEs in deployed software versions. It does not reason about adversary capability tiers, it does not map attack paths across component boundaries, and it does not account for logic vulnerabilities or authentication design flaws that have no CVE. The Citrix Bleed vulnerability (CVE-2023-4966) produced a session token leak from a memory read overrun that bypassed multi-factor authentication entirely — a vulnerability that required understanding the interaction between the session management design and the memory handling bug to exploit. No scanner identified it as critical before exploitation was observed in the wild; the threat model for the application should have flagged session token storage in an overflowable buffer region as a high-severity design question during architectural review.

A third failure mode is intelligence isolation: threat intelligence consumed by a threat intelligence platform (TIP) but never actually driving changes to detection rules, firewall policy, or the threat model itself. Intelligence that does not change defender behavior is a sunk cost. The integration discipline is to maintain a closed-loop pipeline: new intelligence arrives, it is mapped to ATT&CK techniques, those techniques are checked against the coverage gap report, and any uncovered techniques with active exploitation evidence trigger detection engineering work items within a defined SLA — typically 72 hours for a technique confirmed exploited in the wild against organizations in your sector.

The practitioner who internalizes all three failure modes and builds processes that resist them has achieved the foundational competency that all subsequent defensive engineering depends on. The firewall rules, the detection signatures, the incident response playbooks — all of them are downstream outputs of the threat model. When the model is accurate, those outputs are correctly targeted. When the model is stale, the downstream controls are defending the wrong things, at the wrong priority, against the wrong adversary.
