# Lesson 1: Reconnaissance, Threat Modeling, and Attack Surface Analysis

## 1. First-Principles Intuition & Invariants

Every successful offensive security engagement begins not with a tool, but with a question: *what does the target look like from the outside?* Before a single packet is sent, before a single port scanner is invoked, the practitioner must develop a mental model of the system under examination that is as accurate as an architect's blueprint. This is not a philosophical luxury. It is an operational necessity, because the quality of that mental model determines the quality of every decision that follows. Reconnaissance is the discipline of building that model systematically, from first principles, with the rigor of an intelligence analyst and the technical depth of a systems engineer.

The foundational invariant of reconnaissance is information asymmetry. The defender, by default, possesses complete knowledge of their own environment: they know which services are running, which certificates are deployed, which software versions are installed. The attacker knows none of this at the start. Every reconnaissance technique is, in mechanical terms, a method for reducing that asymmetry. Passive reconnaissance reduces it without alerting the defender. Active reconnaissance reduces it faster, but at the cost of leaving traces. The practitioner's first strategic decision is always how much noise they can afford to generate, and that decision depends entirely on the rules of engagement and the threat model they are operating within.

Threat modeling introduces a second invariant: *adversarial thinking is systematic, not intuitive*. It is tempting to believe that experienced security practitioners simply *see* vulnerabilities through accumulated intuition. In practice, every effective threat model is the product of a structured decomposition process. The system is broken down into assets, trust boundaries, data flows, and entry points. Threats are enumerated against that structure using a formal taxonomy. Without this structure, assessments suffer from recency bias, where practitioners chase the vulnerability class they found in the last engagement rather than the one that actually applies to this system.

The third invariant is that attack surface area is not a fixed quantity. It is a function of system state, deployment configuration, and the ambient threat environment. A web application with a single exposed HTTPS endpoint has a dramatically different attack surface when it also runs an administrative API on a loopback interface that happens to be reachable via SSRF. The attack surface that matters is the attack surface visible from the attacker's current position, and that position can change as the engagement progresses. This concept of a *positional* attack surface is what distinguishes a sophisticated threat model from a naive checklist.

The historical context here is instructive. The structured approach to reconnaissance became formalized in military doctrine long before it entered the vocabulary of computer security. Sun Tzu's dictum that every battle is won before it is fought described an intelligence preparation process that modern red teams would recognize immediately. The NSA's Tailored Access Operations unit, as described in leaked documents, operated a formal target development pipeline with phases that map almost exactly to the PTES (Penetration Testing Execution Standard): intelligence gathering, threat modeling, vulnerability research, and exploitation. The lesson is that the most sophisticated offensive operations in history spent the majority of their effort in pre-exploitation phases, not in executing payloads.

For hardware security researchers and embedded engineers, this lesson carries additional weight. When the target is a firmware image running on an ARM Cortex-M microcontroller, or an ICS device communicating over Modbus TCP, there is no shodan query that reveals the attack surface and no CVE database entry that maps the vulnerability landscape. The practitioner must reconstruct the system architecture from physical artifacts: FCC filings, FCC ID lookups for RF emissions data, patent applications that describe internal bus topologies, and regulatory compliance documentation that often inadvertently reveals SoC vendors and software stacks. This kind of open-source intelligence work is reconnaissance in its purest form, and it demands the same rigor as any other phase of the engagement.

## 2. Core Architecture & Mechanics

### The Reconnaissance Execution Model

Reconnaissance is best understood as a layered pipeline. Each layer produces structured output that feeds into the next, and each layer operates at a different level of abstraction. The pipeline begins with open-source intelligence (OSINT) at the highest level of abstraction and terminates with service-level enumeration at the lowest. The practitioner moves through these layers sequentially, with the output of each pass constraining and focusing the work of the next.

```
┌─────────────────────────────────────────────────────────────┐
│                    RECONNAISSANCE PIPELINE                  │
│                                                             │
│  ┌────────────┐    ┌────────────┐    ┌────────────────────┐ │
│  │  OSINT /   │    │  PASSIVE   │    │  ACTIVE            │ │
│  │  SIGINT    │───▶│  DNS/IP    │───▶│  PORT/SERVICE      │ │
│  │  Layer     │    │  Recon     │    │  ENUMERATION       │ │
│  └────────────┘    └────────────┘    └────────────────────┘ │
│        │                 │                    │              │
│        ▼                 ▼                    ▼              │
│  ┌──────────┐    ┌──────────────┐    ┌────────────────────┐ │
│  │ Org/Org  │    │ IP Ranges,   │    │ Banner grabs,      │ │
│  │ Structure│    │ ASN, DNS     │    │ version strings,   │ │
│  │ Employees│    │ zones, certs │    │ TLS fingerprints   │ │
│  └──────────┘    └──────────────┘    └────────────────────┘ │
│                                               │              │
│                                               ▼              │
│                              ┌────────────────────────────┐  │
│                              │  THREAT MODEL + ATTACK     │  │
│                              │  SURFACE MAP               │  │
│                              └────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Passive Reconnaissance: DNS, Certificate Transparency, and ASN Analysis

The Domain Name System is one of the richest sources of passive intelligence available to an attacker because it was designed for availability and not for opacity. A single organization's DNS namespace can reveal its entire infrastructure topology: internal naming conventions exposed through misconfigured zone transfers, cloud provider migration patterns visible in CNAME chains, and subsidiary relationships encoded in reverse DNS records for entire IP blocks.

The practitioner begins DNS reconnaissance by enumerating all delegated name servers for the target domain, then querying each one independently for SOA, MX, TXT, and NS records. The TXT records alone can reveal extraordinary detail: SPF records enumerate all authorized mail sending infrastructure, DMARC records confirm whether the organization has enforced anti-spoofing controls (and whether a phishing-permissive `p=none` policy is in effect), and DKIM selectors published in DNS can identify third-party email providers and campaign management platforms.

```bash
# Authoritative NS enumeration
dig NS target.com +short

# Full zone data attempt (commonly blocked, but worth trying against secondary NSes)
dig AXFR target.com @ns1.target.com

# TXT record harvest for SPF/DKIM/DMARC analysis
dig TXT target.com +short
dig TXT _dmarc.target.com +short
dig TXT default._domainkey.target.com +short

# Subdomain brute-force using a curated wordlist
dnsx -d target.com -w /opt/wordlists/subdomains-top1million.txt -a -cname -resp -silent

# Passive subdomain enumeration via certificate transparency logs
subfinder -d target.com -all -recursive -silent -o subdomains.txt

# ASN lookup from known IP to pivot to full IP space
whois -h whois.radb.net -- '-i origin AS15169' | grep -Eo '([0-9.]+){4}/[0-9]+'
```

Certificate Transparency (CT) logs represent one of the most underutilized passive intelligence sources in the practitioner's arsenal. Under RFC 6962 and its successor RFC 9162, every publicly trusted TLS certificate must be submitted to an append-only, cryptographically verifiable log before browsers will trust it. The practical consequence is that every subdomain an organization has ever provisioned a certificate for is permanently recorded in a publicly queryable database. Tools like `crt.sh`, `certspotter`, and `censys` expose this data, and the results frequently include internal hostnames inadvertently given public certificates, development environments, staging systems, and third-party SaaS integrations that the organization may consider non-public.

The Autonomous System Number (ASN) pivot is equally powerful. Once a single IP address within the target's network space is identified, a BGP routing lookup reveals the ASN that owns that address block. From the ASN, the full set of announced prefixes is recoverable, giving the practitioner a complete map of the organization's routed IP space worldwide. This technique is particularly effective against large enterprises that have acquired subsidiaries, because the acquired company's IP space often retains its original ASN and legacy infrastructure with weaker security controls than the parent organization's primary network.

### Active Reconnaissance: Nmap, Banner Analysis, and Protocol Fingerprinting

Active reconnaissance begins where passive intelligence reaches its resolution limit. The practitioner now has a list of IP ranges and hostnames. The next objective is to determine which ports are listening on those hosts, what services are bound to those ports, and what software version and configuration is exposed.

Nmap's TCP scanning logic is worth understanding at the packet level, because the choice of scan technique determines both the accuracy of results and the visibility of the scan to network monitoring infrastructure. The default SYN scan (`-sS`) sends a TCP SYN to each target port and interprets the response according to the TCP state machine: a SYN-ACK indicates an open port (Nmap sends RST to prevent the connection completing), an RST indicates a closed port, and no response after retransmission indicates a filtered port. This technique leaves no completed TCP connections in the target's application logs, though it is visible to any IDS that tracks half-open connections.

The `-sV` service version detection flag causes Nmap to progress through a probe database of over 10,000 entries, sending protocol-specific payloads and matching responses against known version signatures. The accuracy of this process varies considerably by service: for well-characterized protocols like SSH and HTTP it is extremely reliable, but for custom embedded protocols or proprietary industrial control system communications it may produce only a generic `unknown` classification. In those cases, the practitioner must fall back to manual banner interaction using `netcat` or `socat` and interpret the response format directly.

```bash
# Phase 1: Fast host discovery across a CIDR block
nmap -sn -PE -PP -PM --min-hostgroup 64 --min-parallelism 100 192.168.1.0/24 -oG hosts_up.gnmap

# Phase 2: Full port SYN scan on discovered hosts, with timing profile T4
nmap -sS -p- -T4 --open -iL live_hosts.txt -oA full_ports

# Phase 3: Service version + default script scan on open ports
nmap -sV -sC -p 22,80,443,8080,8443,9090 --script=banner,http-headers,ssl-cert,ssh-hostkey \
     -iL live_hosts.txt -oA service_scan

# TLS fingerprinting via JARM (identifies server TLS stack implementation)
python3 jarm.py target.com 443

# Passive OS and service fingerprinting via p0f (zero-packet-sent)
p0f -i eth0 -p -o /tmp/p0f_output.log
```

TLS fingerprinting via tools like JARM is a technique that many practitioners overlook in favor of version scanning, but it carries significant intelligence value. JARM works by sending ten specifically crafted TLS ClientHello messages with varying cipher suite orderings and extension permutations, then hashing the server's ordered responses into a 62-character fingerprint. Because different TLS stacks (OpenSSL, BoringSSL, NSS, GnuTLS, Windows SChannel) respond to these probes in characteristically different ways, the JARM fingerprint often identifies the underlying server platform more reliably than the HTTP `Server` header, which can trivially be overwritten by configuration.

For embedded and IoT targets, the protocol fingerprinting problem is more complex. Many embedded systems communicate over protocols like Modbus RTU/TCP, DNP3, BACnet, CoAP, or MQTT, which are not in Nmap's standard service probe database or which require specialized client libraries to interact with meaningfully. The practitioner must use purpose-built tools.

```bash
# MQTT broker enumeration and authentication testing
mosquitto_sub -h target-ip -p 1883 -t '#' -v --username '' --password ''

# Modbus TCP device identification and register enumeration
mbtget -r1 -a1 -u1 target-ip

# BACnet device discovery and object enumeration
python3 -m bacpypes --ini BACpypes.ini

# CoAP resource discovery
coap-client -m get coap://target-ip/.well-known/core
```

### Threat Modeling: STRIDE and PASTA

With the information-gathering phase producing a structured picture of the target, threat modeling transforms that picture into a prioritized list of attack vectors. The two frameworks most widely used in production engagements are STRIDE and PASTA, and they operate at different levels of abstraction that make them complementary rather than competing.

STRIDE, developed at Microsoft in the late 1990s by Loren Kohnfelder and Praerit Garg, is a property-based enumeration framework. Each letter of the acronym names a threat class that violates one of six security properties: **S**poofing violates authentication, **T**ampering violates integrity, **R**epudiation violates non-repudiation, **I**nformation disclosure violates confidentiality, **D**enial of service violates availability, and **E**levation of privilege violates authorization. The practitioner applies STRIDE by decomposing the system into a Data Flow Diagram (DFD) and then systematically asking, for each element of the DFD, which STRIDE properties could be violated and by what mechanism.

The power of STRIDE lies in its systematic completeness. Because it forces the practitioner to consider all six threat properties against every DFD element, it surfaces threats that intuition would miss. Consider an ICS SCADA system with a historian server that writes process data to a time-series database. Intuitive threat modeling focuses on Tampering (an attacker modifying process values) and Denial of Service (disrupting control). STRIDE forces the practitioner to also consider Repudiation: if the historian's audit log is writable by the same process that writes telemetry data, then a compromised historian can retroactively falsify operational history, eliminating forensic evidence of a process manipulation attack.

PASTA (Process for Attack Simulation and Threat Analysis) operates at a higher level of abstraction than STRIDE. It is a seven-stage risk-centric framework that begins with business objectives and regulatory constraints, works down through technical scope definition and application decomposition, and arrives at a threat enumeration and risk scoring exercise that produces results in business-impact language. For practitioners who must communicate findings to non-technical stakeholders or who are operating within a formal risk management framework, PASTA's output is significantly more actionable than a raw STRIDE enumeration.

```
STRIDE per DFD Element - Example: IoT Firmware Update Service
┌──────────────────┬──────────┬────────────────────────────────────────────┐
│ DFD Element      │ Threat   │ Attack Vector                              │
├──────────────────┼──────────┼────────────────────────────────────────────┤
│ Update Server    │ Spoofing │ DNS hijack redirects device to rogue server│
│ TLS Channel      │ Tampering│ Downgrade to TLS 1.0, BEAST/POODLE         │
│ Firmware Package │ Tampering│ Unsigned payload accepted if sig check skip│
│ Update Client    │ EoP      │ Firmware runs as root, no privilege drop    │
│ Update Log       │ Repudiat.│ Log written by same process as installer   │
│ Update Server    │ DoS      │ OTA blocked by RST injection on TCP session│
│ Config File      │ InfoDisc │ Build metadata leaks private IP schema     │
└──────────────────┴──────────┴────────────────────────────────────────────┘
```

### Attack Surface Mapping: From Enumeration to Exploitability

Attack surface mapping is the synthesis step that connects the raw output of reconnaissance with the prioritized structure of the threat model. The objective is to produce a graph where nodes represent assets and edges represent trust relationships, with each edge annotated by the protocol, authentication mechanism, and directionality of data flow.

The concept of a trust boundary is central to this analysis. A trust boundary is any point in the system where data or execution crosses from an environment with one security context to an environment with a different security context. The kernel/userspace boundary is a trust boundary. The boundary between a container and its host is a trust boundary. The boundary between a device's bootloader and its operating system is a trust boundary. Every trust boundary is a potential vulnerability site, because trust boundary crossings require the receiving side to validate inputs that it did not generate, and input validation failures are the proximate cause of the overwhelming majority of exploitable vulnerabilities.

For hardware researchers specifically, the attack surface map must include physical interfaces that software-only assessments ignore entirely. JTAG and SWD debug interfaces, UART console headers, SPI and I²C buses connecting onboard peripherals, and USB enumeration surfaces are all part of the attack surface. A device that is completely hardened at the network layer may expose an unauthenticated root shell over a 3.3V UART header accessible with a $15 logic analyzer and a USB-UART adapter. The practitioner who ignores the physical attack surface has not performed a complete assessment.

```
Attack Surface Map - Embedded Gateway Device
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL INTERFACES                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │  WAN     │  │  HTTPS   │  │  MQTT/   │  │  OTA Update    │  │
│  │  ETH     │  │  Admin   │  │  TLS     │  │  Service       │  │
│  │  (eth0)  │  │  Portal  │  │  (8883)  │  │  (TCP 8888)    │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬────────┘  │
│       │              │              │                │            │
│  ═════╪══════════════╪══════════════╪════════════════╪═══════════│
│                 TRUST BOUNDARY (network→OS)                      │
│  ═════╪══════════════╪══════════════╪════════════════╪═══════════│
│       │              │              │                │            │
│  ┌────▼──────────────▼──────────────▼────────────────▼────────┐  │
│  │               Linux Kernel (OpenWrt 22.03)                 │  │
│  │        iptables rules, net namespaces, process model       │  │
│  └──────────────────────────────┬──────────────────────────── ┘  │
│                                 │                                 │
│  ═══════════════════════════════╪═════════════════════════════   │
│            TRUST BOUNDARY (kernel→hardware)                      │
│  ═══════════════════════════════╪═════════════════════════════   │
│                                 │                                 │
│  ┌─────────────┐  ┌─────────────▼──┐  ┌──────────────────────┐  │
│  │  JTAG/SWD   │  │  SoC (ARM      │  │  SPI Flash           │  │
│  │  Header     │  │  Cortex-A7)    │  │  (Firmware Storage)  │  │
│  │  [PHYSICAL] │  │                │  │  [PHYSICAL]          │  │
│  └─────────────┘  └────────────────┘  └──────────────────────┘  │
│                     PHYSICAL ATTACK SURFACE                      │
└─────────────────────────────────────────────────────────────────┘
```

## 3. High-Performance Optimization & Failure Modes

### Operational Workflow Optimization

The reconnaissance phase is where most engagements lose efficiency, and the loss almost always stems from the same root cause: sequential execution of tasks that are parallelizable. A practitioner who runs DNS enumeration, then certificate transparency queries, then ASN pivots, then port scanning in a strict sequence is leaving significant time on the table. A properly constructed reconnaissance workflow runs these phases concurrently, with each phase's output feeding a shared work queue that downstream phases consume asynchronously.

The tool `amass` from OWASP provides a framework for this kind of concurrent, multi-source enumeration, drawing simultaneously from DNS brute-force, certificate transparency APIs, Shodan, VirusTotal, and passive DNS databases. For target environments where speed is a constraint, the practitioner can configure `amass` with a custom resolvers list of fast public DNS servers and aggressive concurrency settings, completing subdomain enumeration that would take hours with sequential tools in under twenty minutes.

```bash
# amass enum with active DNS brute-force + passive OSINT sources
amass enum -active -d target.com -brute -w /opt/SecLists/Discovery/DNS/dns-Jhaddix.txt \
  -rf /opt/resolvers/valid_resolvers.txt -max-dns-queries 20000 \
  -o amass_output.txt -json amass_output.json

# Shodan CLI for passive service intelligence on discovered IP space
shodan search "net:198.51.100.0/24" --fields ip_str,port,org,product,version \
  --separator ',' > shodan_services.csv

# Masscan for rapid port discovery at high packet rates across IP range
masscan -p1-65535 198.51.100.0/24 --rate=50000 --open-only \
  -oG masscan_output.gnmap --router-mac AA:BB:CC:DD:EE:FF

# Merge masscan results for targeted nmap service scan
grep "open" masscan_output.gnmap | awk '{print $2}' | sort -u > masscan_live.txt
nmap -sV -sC --script=default,safe --open -p $(grep "Ports:" masscan_output.gnmap | \
  grep -oP '\d+/open' | cut -d/ -f1 | sort -un | tr '\n' ',' | sed 's/,$//') \
  -iL masscan_live.txt -oA targeted_service_scan
```

### Failure Mode: False Confidence from Incomplete Enumeration

The most dangerous failure mode in the reconnaissance phase is not false positives but false negatives: the practitioner believes the enumeration is complete when significant attack surface remains undiscovered. This failure mode has several common causes that the experienced practitioner must actively defend against.

The first is reliance on a single DNS enumeration technique. Certificate transparency logs and DNS brute-force are complementary, not substitutes. CT logs reveal every hostname that has ever had a public certificate, but they miss internal hostnames accessible only over VPN and subdomains served over HTTP without TLS. DNS brute-force covers more of the namespace than CT logs but is bounded by wordlist quality. The practitioner who uses only one technique will systematically miss whatever the other would have found.

The second cause is treating the IPv4 scan as the complete network picture. Organizations that have adopted IPv6 natively or in dual-stack configurations present an entirely separate address space that most practitioners fail to enumerate. IPv6 addresses are not sequentially scannable in the way IPv4 ranges are, because a /64 subnet contains 2⁶⁴ addresses. The correct approach is to identify IPv6 prefixes from AAAA DNS records, router advertisement messages captured on-network, and ASN routing table lookups, then target specific addresses rather than attempting exhaustive scans.

The third cause is ignoring cloud metadata and third-party SaaS integrations. Modern organizations run significant workloads across AWS, GCP, Azure, and specialized SaaS platforms, and the attack surface of those workloads is often dramatically weaker than the organization's core infrastructure. A single misconfigured S3 bucket, an Elasticsearch cluster with no authentication bound to a cloud-provider public IP, or an OAuth application with overly permissive scopes can represent a critical vulnerability that never appears in a traditional infrastructure scan.

```bash
# Cloud storage bucket enumeration (AWS S3, GCS, Azure Blob)
# Using cloud_enum for multi-provider bucket discovery
python3 cloud_enum.py -k target-orgname -k targetorg -k target_org \
  --disable-azure --quickscan -l cloud_enum_output.txt

# S3 bucket policy verification on discovered buckets
aws s3api get-bucket-acl --bucket discovered-bucket-name --no-sign-request

# Identify exposed cloud metadata from SSRF-susceptible endpoints
curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/ \
  --max-time 2 --connect-timeout 1

# Google Cloud metadata equivalent
curl -s -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/ \
  --max-time 2
```

### Failure Mode: Threat Model Scope Creep and Missing Crown Jewels

The STRIDE analysis fails in a predictable way when the Data Flow Diagram is drawn at the wrong level of abstraction. If the DFD is too high-level, trust boundaries collapse into single nodes and the analysis misses the intra-component trust issues where many real vulnerabilities live. If the DFD is too granular, the analysis becomes unmanageable and practitioners lose sight of the high-value assets that make the exercise worthwhile in the first place.

The mitigation is a two-pass DFD construction process. The first pass draws the system at the component level, identifying major services, data stores, external actors, and the trust boundaries between them. This pass is used to identify the crown jewels: the assets whose compromise would constitute a critical security failure. The second pass zooms into the components that handle those crown jewels and constructs a more detailed DFD of their internal architecture. STRIDE is applied with full rigor to this second-pass DFD, while the first-pass DFD is used to ensure coverage of the full system without drowning in unnecessary detail.

For embedded systems, crown jewels often include the cryptographic key material stored in OTP fuses or secure enclaves, the firmware signing verification logic in the bootloader, and the network credentials provisioned at manufacturing time. A threat model that does not specifically analyze the trust chain from hardware root of trust through bootloader to operating system has not addressed the most critical attack surface on the device.

### Failure Mode: Reconnaissance Overrun and Alert Fatigue Induction

Active reconnaissance that is too aggressive creates two problems simultaneously: it alerts the defender, potentially triggering an incident response that terminates the engagement, and it generates so much data that the practitioner loses the ability to reason about it clearly. The experienced practitioner manages scan intensity as a first-class parameter, not an afterthought.

Nmap's timing templates (`-T1` through `-T5`) provide coarse control, but production-grade stealth scanning requires direct control over interpacket delay, source port randomization, decoy address injection, and fragmentation. For engagements where stealth is a hard requirement, the practitioner distributes scans across multiple egress IPs and time-of-day windows, uses non-standard source ports that blend with legitimate traffic patterns, and limits scan rate to stay below the threshold of the target's rate-limiting IDS signatures.

```bash
# Low-and-slow stealth scan with decoys and source port spoofing
nmap -sS -T1 --scan-delay 2000ms --max-retries 1 \
  -D RND:5 --source-port 53 \
  -p 80,443,8080,8443,22,21,25,110,143,3389,5900 \
  --randomize-hosts target.com -oA stealth_scan

# Fragment packets to evade signature-based detection
nmap -sS -f --mtu 24 -p 80,443 target.com

# Idle scan using zombie host (completely blind from target's perspective)
nmap -sI zombie-host.example.com:80 -p 80,443,8443 target.com
```

The discipline of reconnaissance and threat modeling is ultimately the discipline of building an accurate mental model before committing to action. Every hour spent in systematic information gathering and structured threat analysis is an hour of exploitation work made more precise, more efficient, and less likely to cause unintended damage in the target environment. The practitioner who treats reconnaissance as a box to check before the "real work" begins has fundamentally misunderstood the craft. In every serious offensive engagement, the reconnaissance phase is the work, and everything that follows is its execution.
