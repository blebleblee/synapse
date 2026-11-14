# Lesson 3: Wireless Protocols Optimization

## 1. First-Principles Intuition & Invariants

Wireless networking is, at its physical core, a shared medium problem disguised as a point-to-point one. Every radio transmission propagates as an electromagnetic wave through a medium that is simultaneously owned by every other transmitter in range, governed by no deterministic access arbitration, and subject to attenuation laws that are fundamentally indifferent to your SLA. Understanding Ubiquiti's approach to wireless optimization begins not with the UniFi controller dashboard but with the physics it is fighting against, and with the precise mechanisms the 802.11 standard invented to impose order on that chaos.

The free-space path loss formula, $FSPL = 20\log_{10}(d) + 20\log_{10}(f) + 20\log_{10}\!\left(\frac{4\pi}{c}\right)$, establishes the invariant that signal attenuation scales with the square of both distance and carrier frequency. This is why 5 GHz 802.11ac and 802.11ax access points deliver dramatically higher throughput than their 2.4 GHz counterparts in open-plan offices yet lose to them the moment a concrete wall intervenes. The 2.4 GHz band penetrates building materials with roughly 3 dB less loss per obstruction than 5 GHz. For a kernel or infrastructure engineer accustomed to thinking in terms of cache hierarchy trade-offs, this is conceptually identical to the latency-bandwidth trade-off between L1 and DRAM: the faster medium has a shorter reach, and the design decision is always about matching medium to workload topology.

The 802.11 MAC layer solves the shared-medium collision problem through Distributed Coordination Function (DCF), which implements Carrier Sense Multiple Access with Collision Avoidance (CSMA/CA). Before transmitting, a station listens for a carrier and waits for the channel to be idle for a Distributed Interframe Space (DIFS) period, then backs off for a random number of slot times drawn from a contention window. This random backoff is the core invariant preventing simultaneous transmission and the primary source of overhead in dense environments: as station count rises, the probability of collision increases, contention windows grow, and the fraction of airtime consumed by backoff expands non-linearly. This is not a UniFi-specific problem; it is a property of 802.11 itself, and every optimization Ubiquiti exposes in its controller is ultimately an attempt to reduce contention window collisions, shorten interframe spacing, or schedule transmissions in a way that the base standard does not mandate.

Wi-Fi 5 (802.11ac) introduced Multi-User MIMO in the downlink direction and mandatory 256-QAM modulation, raising the theoretical maximum on an 80 MHz channel with four spatial streams to 1.73 Gbps. Wi-Fi 6 (802.11ax) reframed the problem entirely by introducing Orthogonal Frequency Division Multiple Access (OFDMA), which subdivides a single channel into Resource Units (RUs) that can be assigned to different stations simultaneously. Where 802.11ac serializes transmissions between stations, 802.11ax spatially and spectrally multiplexes them. For a dense deployment of 50+ clients, this is the difference between a highway with one lane and a highway where each vehicle is assigned its own lane width dynamically. Wi-Fi 6 also introduced Target Wake Time (TWT), which lets an AP schedule a client's radio sleep intervals, dramatically reducing the association overhead and beacon contention in IoT-heavy networks.

The invariant that governs every high-performance Ubiquiti deployment is this: **the bottleneck is almost never the AP hardware capability; it is airtime utilization and channel reuse**. Ubiquiti's U6 Pro, U6 Enterprise, and U6 Long-Range all implement 802.11ax with 4×4 MIMO on 5 GHz. Their differentiation is transmit power, antenna gain pattern, and the density of spatial streams they can sustain simultaneously. No amount of AP hardware investment recovers capacity lost to co-channel interference from adjacent APs on the same channel, excessive beacon overhead from misconfigured SSID proliferation, or sticky clients that refuse to roam off a distant AP because the RSSI threshold for probe responses is misconfigured.

---

## 2. Core Architecture & Mechanics

### The 802.11ax Frame Pipeline and OFDMA Scheduling

Understanding where Ubiquiti's firmware sits relative to the 802.11 standard requires a precise mental model of the transmit pipeline. When a packet arrives at the AP from the wired backhaul, it enters the driver's transmit queue, is classified by the QoS subsystem into one of four Access Categories (Voice, Video, Best Effort, Background), assigned an EDCA (Enhanced Distributed Channel Access) parameter set governing its contention window and AIFS, and then handed to the MAC sublayer for aggregation and PHY framing.

```
Wired Backhaul
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│                    AP Linux Kernel                       │
│  ┌──────────┐    ┌──────────────┐    ┌────────────────┐ │
│  │  netdev  │───▶│  mac80211    │───▶│  ath11k/mt76   │ │
│  │  RX/TX   │    │  subsystem   │    │  driver layer  │ │
│  └──────────┘    └──────────────┘    └────────┬───────┘ │
└───────────────────────────────────────────────│─────────┘
                                                │
                                     ┌──────────▼──────────┐
                                     │  Radio Firmware     │
                                     │  (closed, QCA/MTK)  │
                                     │                     │
                                     │  OFDMA Scheduler    │
                                     │  MU-MIMO Beamformer │
                                     │  AMPDU Aggregator   │
                                     └──────────┬──────────┘
                                                │
                                     ┌──────────▼──────────┐
                                     │  PHY / RF Chain     │
                                     │  4×4 MIMO Antennas  │
                                     └─────────────────────┘
```

The mac80211 subsystem in the Linux kernel implements the common 802.11 MAC logic shared across all wireless drivers, including frame aggregation (A-MPDU, A-MSDU), rate control, and power save buffering. Ubiquiti's APs run a customized Linux-based OS (OpenWrt-derived on older UniFi hardware, a proprietary stack on newer U6 models) where mac80211 interacts with vendor-specific firmware for the actual RF scheduling. This split-MAC architecture means that OFDMA Resource Unit allocation and MU-MIMO precoding matrix computation happen entirely within the radio firmware, below the visibility horizon of the administrator. What you can influence from the UniFi controller flows down through configuration APIs that instruct the firmware on channel width, transmit power policy, minimum RSSI thresholds, and BSS color assignment.

### MIMO Spatial Streams and the Beamforming State Machine

MIMO exploits multipath propagation rather than fighting it. In a traditional single-antenna system, multipath reflections arrive at the receiver with different phases and cause destructive interference, manifesting as the signal fading you observe when a laptop RSSI drops 10 dB simply by rotating the device on a desk. In a 4×4 MIMO system, those same multipath reflections are treated as independent spatial channels. The AP transmits distinct data streams through each antenna with precisely calculated phase offsets, and the receiver reconstructs the streams by solving a matrix equation over the channel impulse response matrix $H$.

Explicit beamforming, standardized in 802.11ac and refined in 802.11ax, requires the client to transmit a sounding frame, the AP to respond with an NDP (Null Data Packet), and the client to feed back a compressed Beamforming Feedback Matrix (BFM) that describes its view of the channel. The AP then applies this matrix as a precoder, steering signal energy toward the client and minimizing interference toward other clients. This sounding handshake happens every few hundred milliseconds in a mobile environment, which is non-trivial overhead. In a UniFi deployment, the firmware manages sounding intervals adaptively, backing off the sounding frequency for stationary clients and accelerating it when RSSI variance indicates client movement.

```
Timeline of MU-MIMO Downlink Transmission (802.11ax):

AP ──► NDPA (sounding announcement) ──────────────────────────────────►
AP ──► NDP  (null data packet)       ──────────────────────────────────►

Client A ◄────────────────────────────────── BFM Report (compressed)
Client B ◄────────────────────────────────── BFM Report (compressed)
Client C ◄────────────────────────────────── BFM Report (compressed)

AP computes precoder W from {BFM_A, BFM_B, BFM_C}
              │
              ▼
AP ──► MU-PPDU [stream_A | stream_B | stream_C] (simultaneous)
              │             │             │
              ▼             ▼             ▼
          Client A      Client B      Client C
```

The spatial separation achieved by this precoder is what allows three clients to share the same frequency resource simultaneously without destructive interference. The precoder quality degrades if the channel estimate fed back is stale, which is why MU-MIMO throughput collapses in environments with high client mobility or a large number of legacy clients that do not support beamforming feedback.

### Channel Planning and Co-Channel Interference

The 5 GHz band, as defined by the FCC and ETSI regulatory domains, provides 25 non-overlapping 20 MHz channels in the UNII-1 through UNII-3 bands. Bonding these into 80 MHz channels for 802.11ac/ax reduces that to five or six non-overlapping channels. When you deploy more APs than you have non-overlapping channels, co-channel interference is structurally unavoidable. Two APs on the same channel defer to each other via CSMA/CA, effectively halving the available airtime for each. At three APs on the same channel, the contention overhead begins to dominate throughput.

Ubiquiti's Auto RF feature, accessed through the controller's RF Environment panel, runs a background scan of RSSI levels and neighboring channel utilization and then adjusts channel assignments and transmit power to minimize overlap. The underlying algorithm implements a variant of graph coloring: APs are nodes, edges represent proximity (co-interference potential), and channel assignments are colors. The goal is to maximize the minimum chromatic distance between adjacent APs. Auto RF is not a substitute for deliberate manual channel planning; it is a convergence mechanism that reduces the operational burden of ongoing drift correction as the RF environment changes over weeks and months.

```
Correct 5 GHz Channel Allocation (80 MHz channels, 6-AP floor plan):

  [AP-1: ch 36]      [AP-2: ch 149]     [AP-3: ch 36]
       │                   │                   │
       └────── ~20m ───────┘────── ~20m ───────┘

  [AP-4: ch 149]     [AP-5: ch 100]     [AP-6: ch 149]
       │                   │                   │
       └────── ~20m ───────┘────── ~20m ───────┘

Co-channel pairs: AP-1/AP-3, AP-2/AP-4/AP-6
Mitigated by: transmit power reduction, directional antenna tilt
```

The DFS (Dynamic Frequency Selection) channels in the UNII-2 and UNII-2e bands (100–144) add spectrum at the cost of mandatory radar detection. When a Ubiquiti AP operating on a DFS channel detects a radar pulse pattern, it must vacate the channel within 10 seconds and not return for 30 minutes. For latency-sensitive workloads like VoIP or real-time collaboration, DFS channel instability is operationally significant. The mitigation is to designate a dedicated fallback channel in Auto RF configuration and ensure that client devices support 802.11k neighbor reports, so roaming to an adjacent AP on a stable channel is fast when a DFS event triggers.

### 802.11r Fast BSS Transition and the Roaming State Machine

Client roaming is one of the most poorly understood and most consequential aspects of enterprise wireless operation. The 802.11 standard places roaming decisions entirely in the client device, not the AP. An AP cannot force a client to roam; it can only refuse to respond to probe requests below a configured RSSI threshold (minimum RSSI gating), signal to the client that a better AP exists via 802.11k/v neighbor reports and BSS Transition Management frames, and ensure that the re-association handshake completes as quickly as possible once the client decides to roam.

The standard 802.11i re-association process without Fast BSS Transition involves a full 802.1X/EAP authentication round-trip back to the RADIUS server, consuming anywhere from 50 ms to 300 ms depending on RADIUS server location, network RTT, and EAP method. For WPA2-Enterprise deployments, this latency causes audible glitches in VoIP calls and visible stalls in real-time screen-sharing applications. 802.11r addresses this by pre-caching the PMK (Pairwise Master Key) keying material in a Mobility Domain, allowing re-association to complete in a single round-trip between the client and the target AP.

```
Roaming Event Timeline: 802.11r Fast BSS Transition

Client                 Source AP (AP-1)         Target AP (AP-2)
  │                          │                        │
  │── Probe Request ─────────►                        │
  │◄─ Probe Response ────────│ (includes Neighbor     │
  │   (RSSI: -78 dBm)        │  Report via 802.11k)   │
  │                          │                        │
  │── FT Auth Request ───────│────────────────────────►
  │◄─ FT Auth Response ──────│────────────────────────│
  │                          │                        │
  │── Reassoc Request ───────────────────────────────►│
  │◄─ Reassoc Response ──────────────────────────────│
  │                          │                        │
  │  Total: ~15–30 ms        │   (vs. 150–300 ms      │
  │                          │    without 802.11r)    │
```

Ubiquiti implements the full 802.11k/r/v trifecta in its U6 access point family. The UniFi controller's Site configuration exposes these as BSS Transition, 802.11r, and 802.11k toggles. Critically, 802.11r compatibility is not universal across client firmware stacks: some legacy Android devices and older Windows 10 builds mishandle the FT authentication state machine and fail to associate at all when 802.11r is active on the SSID. The operationally safe deployment pattern is to run 802.11r on enterprise SSIDs used by known-compatible clients and leave it disabled on guest or IoT SSIDs with heterogeneous client populations.

---

## 3. High-Performance Optimization & Failure Modes

### Baseline Diagnostics with UniFi CLI and SSH

Before tuning any parameter, you need ground-truth measurements. Ubiquiti APs expose a rich diagnostic surface over SSH, accessible by enabling the SSH daemon in the site's Advanced Configuration settings and authenticating with the site credentials. The AP runs a minimal Linux environment with a custom `mca-cli` (Microchip Configuration Agent CLI) that provides structured JSON output for all wireless metrics.

**Step 1: Access AP diagnostic shell**

```bash
ssh admin@<ap-ip>
```

**Step 2: Dump the AP's current radio statistics**

```bash
mca-cli-op stat
```

This returns a JSON blob containing per-radio channel, transmit power, channel utilization (tx, rx, and interference percentages), noise floor, and connected station count. The fields most critical to initial triage are `channel_utilization` (target below 60%), `noise` (target above -95 dBm on 5 GHz), and `num_sta`.

**Step 3: Inspect per-client signal and data rates**

```bash
mca-dump | python3 -c "
import sys, json
data = json.load(sys.stdin)
for vap in data.get('vap_table', []):
    for sta in vap.get('sta_table', []):
        print(f\"{sta['mac']} RSSI:{sta['rssi']} TX:{sta.get('tx_rate',0)} RX:{sta.get('rx_rate',0)} MCS:{sta.get('tx_mcs','?')} SS:{sta.get('tx_nss','?')}\")
"
```

**Step 4: Check for channel interference scan results**

```bash
iwlist ra0 scan | grep -E 'Address|Channel|Signal'
```

**Step 5: Verify 802.11r/k/v negotiation on a connected client**

```bash
iwinfo ra0 assoclist
```

The `iwinfo` output shows the capabilities exchanged during association, including whether the client negotiated HT/VHT/HE (the 802.11n/ac/ax capability classes), beamforming support, and spatial stream count. A client showing `HE` capability confirms 802.11ax association; `VHT` indicates 802.11ac fallback; `HT` indicates legacy 802.11n. Clients associating at HT when you expect HE are either out of driver or firmware date, or are connecting on 2.4 GHz where your AP may not advertise 6 GHz capabilities.

### EDCA and QoS Parameter Tuning

Wi-Fi QoS is implemented through EDCA (Enhanced Distributed Channel Access), which assigns each of the four Access Categories a distinct AIFSN (Arbitration Interframe Space Number), minimum contention window ($CW_{min}$), maximum contention window ($CW_{max}$), and TXOP (Transmission Opportunity) limit. The AP advertises these parameters to clients in its beacons, and both the AP and clients use them to govern their own transmission discipline.

| Access Category | Traffic Type    | AIFSN | CW_min | CW_max | TXOP (µs) |
|-----------------|-----------------|-------|--------|--------|-----------|
| AC_VO           | Voice           | 2     | 3      | 7      | 1504      |
| AC_VI           | Video           | 2     | 7      | 15     | 3008      |
| AC_BE           | Best Effort     | 3     | 15     | 1023   | 0         |
| AC_BK           | Background      | 7     | 15     | 1023   | 0         |

The defaults above follow the 802.11e standard. Voice traffic gets the smallest contention window and shortest interframe space, meaning it wins channel access races against bulk data traffic. The UniFi controller exposes EDCA parameter overrides in the WLAN configuration under Advanced Options. The practical use case for tuning these is a network carrying both VoIP and high-bandwidth file transfer: if file transfer traffic is not properly tagged at Layer 3 (DSCP) and mapped to AC_BK, it competes with voice at AC_BE, inflating jitter.

Ubiquiti's controller implements automatic DSCP-to-AC mapping. Packets arriving from the wired side with DSCP 46 (EF/Expedited Forwarding) are mapped to AC_VO; DSCP 34 and 36 (AF41/AF42, commonly used by video conferencing codecs) map to AC_VI. This mapping only works correctly when the upstream switching infrastructure preserves DSCP markings end-to-end, which requires that inter-VLAN routing happens on a switch or router configured not to remarking DSCP to zero at trust boundaries. Verifying DSCP preservation is therefore a prerequisite before any EDCA tuning exercise is meaningful.

### Minimum RSSI Gating and Band Steering

Sticky client behavior, where a device continues associating with a distant AP rather than roaming to a closer one, is structurally the most common cause of underperformance in multi-AP deployments. The underlying cause is that 802.11 clients use RSSI thresholds for roaming decisions that were calibrated for home networks, where there is typically one AP. In an enterprise with 20 APs, a client holding a -78 dBm connection to AP-1 while AP-7 is two meters away at -55 dBm consumes airtime at MCS 3 (single stream) when it could be transmitting at MCS 11 (four stream HE). The aggregate capacity impact of five such clients is measurable.

The UniFi controller's minimum RSSI setting instructs the AP to drop probe request responses and disassociate clients that fall below a configured threshold. The recommended value for a dense office deployment with APs every 10–15 meters is -72 dBm. Setting this too aggressively (e.g., -65 dBm) causes clients on the periphery of an AP's coverage cell to oscillate between disassociation and re-association if no adjacent AP has sufficient signal, producing a black hole rather than solving the sticky client problem. The correct prerequisite for minimum RSSI enforcement is a site survey confirming that at least -72 dBm coverage from an adjacent AP exists everywhere in the coverage area before the minimum threshold is enforced.

Band steering addresses the complementary problem: dual-band clients that persist on 2.4 GHz when 5 GHz coverage is available. The controller's band steering mechanism monitors probe requests from dual-band clients and suppresses 2.4 GHz probe responses while answering 5 GHz probes, steering the client to the less congested band. This works for clients that probe both bands simultaneously, which is true of most 802.11ac and later devices, but fails for clients that probe 2.4 GHz only until they receive a successful response. The fallback behavior for such clients is a configurable holddown timer after which the 2.4 GHz probe response is unblocked.

### Diagnosing and Mitigating CCI with RF Environment Data

The controller's RF Environment panel presents a visual heat map of neighboring network RSSI levels per channel. The raw data behind it is accessible via the controller's REST API, which allows you to build automated monitoring pipelines.

**Step 1: Retrieve controller auth token**

```bash
curl -s -c cookies.txt -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"<password>"}' \
  "https://<controller-ip>/api/auth/login"
```

**Step 2: Query RF scan data for a site**

```bash
curl -s -b cookies.txt \
  "https://<controller-ip>/proxy/network/api/s/<site-id>/stat/spectrumscan" \
  | python3 -c "
import sys, json
scans = json.load(sys.stdin)
for ap in scans.get('data', []):
    print(f\"AP: {ap['mac']}\")
    for entry in ap.get('table', []):
        if entry.get('rssi', -100) > -80:
            print(f\"  CH:{entry['channel']:4d} RSSI:{entry['rssi']:4d} dBm  {entry.get('essid','<hidden>')}\")
"
```

**Step 3: Identify APs on conflicting channels and correlate with throughput logs**

```bash
curl -s -b cookies.txt \
  "https://<controller-ip>/proxy/network/api/s/<site-id>/stat/device" \
  | python3 -c "
import sys, json
devices = json.load(sys.stdin)
for d in devices.get('data', []):
    if d.get('type') == 'uap':
        for r in d.get('radio_table_stats', []):
            util = r.get('channel_utilization', 0)
            if util > 60:
                print(f\"HIGH UTIL: {d['name']} radio {r['name']} ch:{r.get('channel')} util:{util}%\")
"
```

Output identifying APs with channel utilization above 60% pinpoints the APs that require manual channel reassignment or transmit power reduction. Reducing transmit power on a high-density AP shrinks its coverage footprint, which reduces the number of APs it interferes with on the same channel. The tradeoff is that client devices, which cannot reduce their transmit power to match, may now transmit at a power level the AP can hear but the AP's lower power setting means the AP's downlink to peripheral clients becomes marginal. This asymmetry, the near-far problem, is the reason transmit power reduction must always be paired with AP density: you need a closer AP to cover the cells you are vacating.

### AMPDU Aggregation and Throughput Floors

A-MPDU (Aggregate MAC Protocol Data Unit) aggregation is the single most impactful MAC-layer optimization in 802.11n/ac/ax. Without aggregation, every 1500-byte Ethernet frame requires its own 802.11 frame exchange sequence, including interframe spacing, acknowledgement, and backoff. At 20 µs per exchange, 1000 frames per second consumes 20 ms per second, or 2% of airtime, purely in overhead. With A-MPDU, up to 64 (802.11ac) or 256 (802.11ax) frames are bundled into a single PHY transmission, and a Block ACK covers the entire aggregate, reducing per-frame overhead by roughly an order of magnitude.

AMPDU aggregation is enabled automatically when the client and AP negotiate HT, VHT, or HE capability. The failure mode is a client that negotiates HT capability but has AMPDU disabled in its driver, or an AP-side maximum AMPDU length that is set conservatively for compatibility with legacy equipment. On Ubiquiti APs, the AMPDU configuration is not directly exposed through the UniFi controller GUI but is accessible through the AP SSH shell.

**Step 1: Check current AMPDU configuration on the AP radio**

```bash
iwpriv ra0 show agg_policy
iwpriv ra0 show ba_decline
```

**Step 2: Verify that Block ACK sessions are established with high-throughput clients**

```bash
mca-dump | python3 -c "
import sys, json
data = json.load(sys.stdin)
for vap in data.get('vap_table', []):
    for sta in vap.get('sta_table', []):
        if sta.get('tx_rate', 0) < 50000:
            print(f\"LOW RATE: {sta['mac']} tx_rate:{sta['tx_rate']} kbps MCS:{sta.get('tx_mcs','?')}\")
"
```

A client consistently transmitting below 50 Mbps on a 5 GHz 802.11ax AP when it is physically within 10 meters with clear line of sight is a signal worth investigating. The root causes in order of frequency are: the client is not transmitting at HE capability (check `iwinfo` assoclist), AMPDU is not aggregating (check for Block ACK session establishment), the client is competing with high channel utilization (check `channel_utilization`), or the client's MCS table is capped by a misconfigured rate control policy on the AP.

### Failure Mode: Hidden Node and RTS/CTS Overhead

The hidden node problem occurs when two clients can both hear the AP but cannot hear each other. Without a mechanism for mutual awareness, they both sense the channel as idle and transmit simultaneously, causing a collision at the AP. The 802.11 RTS/CTS (Request to Send/Clear to Send) mechanism addresses this by requiring each client to announce its intent to transmit via a short RTS frame, which the AP acknowledges with a CTS frame that also silences all stations in the AP's range. Any station that cannot hear the original transmitter but can hear the AP's CTS will defer. The cost is two additional frame exchanges per data transmission, adding roughly 50 µs of overhead per packet.

The UniFi controller exposes an RTS/CTS threshold parameter: packets larger than the threshold trigger RTS/CTS. Setting this to 2347 bytes (the maximum) effectively disables RTS/CTS; setting it to 256 bytes enables it for nearly all packets. In a dense environment with verified hidden node problems (diagnosed by a sharp increase in retry rates visible in `mca-cli-op stat` while channel utilization remains moderate), lowering the RTS/CTS threshold to 500–800 bytes often recovers 15–25% of effective throughput by eliminating the collision retries that would otherwise consume far more airtime than the RTS/CTS overhead itself.

The measurement invariant to track is the **retry rate** per radio, available in controller statistics as `tx_retries / tx_packets`. A retry rate above 10% on a lightly loaded AP is a strong indicator of either a hidden node condition or a client with poor SNR being held by sticky association. These two root causes produce identical symptoms at the aggregate metric level and require the per-client signal data from `mca-dump` to disambiguate.

### Production Tuning Reference

Assembling the above mechanics into a coherent deployment workflow requires translating physical RF constraints into controller configuration parameters. The following table captures the specific knobs, their recommended values for high-density enterprise environments, and the first-principles reason each value is correct.

| Parameter | Recommended Value | Rationale |
|---|---|---|
| Channel Width (5 GHz) | 80 MHz | Maximum MCS index; 160 MHz only viable if fewer than 4 APs share the floor |
| Minimum RSSI | -72 dBm | Prevents sticky clients; requires validated adjacent AP coverage |
| Transmit Power (5 GHz) | Medium (17–20 dBm) | Reduces co-channel interference footprint; matched to AP density |
| Band Steering | Enabled | Moves dual-band clients to less congested 5 GHz |
| 802.11r | Enabled on enterprise SSID | Reduces roaming latency to <30 ms |
| 802.11k | Enabled | Provides neighbor report to accelerate client roam decisions |
| 802.11v BSS Transition | Enabled | AP-initiated steering for persistent sticky clients |
| SSID Count per Radio | ≤ 3 | Each SSID adds beacon overhead; >4 measurably degrades airtime |
| DTIM Period | 3 (video), 1 (voice) | Higher DTIM = longer sleep, lower wake overhead; tradeoff with latency |
| RTS/CTS Threshold | 500 bytes (high-density) | Mitigates hidden node at cost of modest overhead |
| Auto RF | Enabled with manual override | Handles drift; manual baseline ensures correct initial state |

The overarching operational discipline for a Ubiquiti deployment is to treat RF as a resource to be allocated, not a medium to be maximized. The instinct to maximize transmit power and channel width in every AP is exactly wrong in a dense environment: it maximizes interference range and minimizes channel reuse. Correct tuning is conservative on power, deliberate on channel assignment, and aggressive only on client throughput per unit of airtime consumed. Every parameter in the table above serves that goal, and every failure mode described in this lesson traces back to a violation of it.
