# Operational Verification Labs: Ubiquiti

## Objective & Environment Setup

Ubiquiti network infrastructure deployments—spanning UniFi controllers, edge routers, switching fabrics, and wireless access points—demand rigorous operational verification protocols that extend far beyond superficial dashboard checks. This laboratory guide establishes a systematic diagnostic methodology for validating live state, profiling performance saturation boundaries, and orchestrating controlled fault injection scenarios across Ubiquiti network control planes and data planes. The practitioner executing these exercises will operate at the intersection of Linux network stack introspection, vendor-specific API interrogation, packet-level traffic analysis, and distributed system state reconciliation.

The verification workflow assumes a hybrid operational context: a UniFi Network Application controller (formerly "UniFi Controller") managing a distributed topology of UniFi devices, coupled with EdgeRouter or UXG gateway appliances providing routing, NAT, and perimeter security functions. The controller itself may run as a Docker container, a native systemd service, or a cloud-hosted instance; regardless of deployment model, the underlying verification primitives remain constant. The exercises prioritize direct kernel-level network stack inspection using `iproute2`, protocol-level traffic capture via `tcpdump`, and application-layer API validation against the UniFi controller's REST and WebSocket endpoints.

Before commencing diagnostic operations, the verification environment requires installation of the core Linux network analysis toolkit. On Debian-derived distributions managing UniFi controllers or gateway appliances, execute `apt-get install -y iproute2 ethtool tcpdump conntrack netcat-openbsd curl jq` to provision the foundational userspace utilities. The `iproute2` suite provides the modern `ip` and `ss` commands for interface configuration and socket state inspection, replacing deprecated `ifconfig` and `netstat` tools. The `ethtool` utility exposes per-interface hardware statistics, offload configurations, and PHY-level link state. The `tcpdump` packet analyzer, built atop the kernel's packet capture framework, enables live traffic dissection at arbitrary protocol layers. The `conntrack` command queries the Netfilter connection tracking subsystem, critical for diagnosing NAT state exhaustion and firewall rule interactions.

For UniFi controller installations running within Docker containers, prepend diagnostic commands with `docker exec -it <container_name>` to execute within the controller's network namespace. Cloud-hosted UniFi controllers (UniFi OS Console or hosted instances) restrict direct shell access, necessitating API-driven verification through the controller's REST interface. In such constrained environments, the practitioner pivots from direct kernel introspection to external observable validation: monitoring API response latencies, WebSocket frame rates, and downstream device connectivity through client-side tooling.

The verification labs assume an operational topology comprising at least one UniFi gateway appliance (UDM-Pro, UXG-Pro, or EdgeRouter), two or more UniFi switches providing layer-2 fabric connectivity, and a collection of UniFi access points serving wireless clients. The controller maintains persistent WebSocket connections to each adopted device, exchanging STUN-derived control plane messages and receiving telemetry streams. The exercises dissect this architecture from three complementary vantage points: the controller's application-layer state machine, the gateway's kernel routing and NAT subsystems, and the physical Ethernet interfaces mediating inter-device communication.

## Exercise 1: Live State & Internal Subsystem Inspection

The first operational verification exercise establishes baseline observability into the UniFi controller's internal state and the Linux network stack underpinning its communication fabric. The controller maintains an internal MongoDB database storing device configurations, client associations, historical statistics, and alarm state. While direct MongoDB access provides the ultimate ground truth, production verification workflows prioritize non-invasive inspection through the controller's REST API and kernel-level socket state enumeration.

Begin by enumerating all active network interfaces on the UniFi gateway appliance or controller host. The command `ip -s -d link show` produces detailed interface statistics, including transmit and receive byte counters, error conditions, and driver-specific parameters. On a UDM-Pro running UniFi OS, the primary WAN interface typically manifests as `eth8`, LAN switching interfaces appear as `eth0` through `eth7`, and the internal bridge interconnecting LAN ports surfaces as `br0`. The `-s` flag activates statistics display, revealing cumulative packet counts, dropped frames, and hardware error conditions. The `-d` flag appends driver-specific details, exposing offload engine configurations such as TCP segmentation offload (TSO), generic receive offload (GRO), and checksum computation delegation.

Inspect the output carefully for non-zero values in the `RX errors`, `TX errors`, `dropped`, and `overruns` fields. Receive errors indicate malformed frames arriving at the physical layer, often symptomatic of duplex mismatch, cable degradation, or electromagnetic interference. Transmit errors suggest queue saturation or MAC-layer collisions, though collisions vanish in full-duplex switched Ethernet topologies. Dropped packet counters increment when the kernel's ingress buffer pools exhaust under high packet rates, a condition diagnosable through `ethtool -S <interface> | grep -i drop` to surface driver-level drop classifications.

Next, interrogate the controller's active socket state to validate its connectivity to managed devices. If the controller runs as a native systemd service or within a Docker container accessible via `docker exec`, execute `ss -tunap | grep java` to enumerate all TCP and UDP sockets owned by the Java-based UniFi controller process. The UniFi controller listens on TCP port 8080 for HTTP device communication, TCP port 8443 for HTTPS administrative access, TCP port 8843 for guest portal HTTPS, and UDP port 3478 for STUN-based device discovery and keep-alive. For each adopted UniFi device, expect an established TCP connection on port 8080 originating from the device's management IP address. The socket state should read `ESTAB`, indicating a fully established three-way handshake and bidirectional data flow.

The `ss` command's `-t` flag filters to TCP sockets, `-u` includes UDP, `-n` disables DNS resolution for numeric address display, `-a` shows all sockets (listening and established), and `-p` appends the owning process ID and name. A production UniFi controller managing fifty devices will exhibit at least fifty established TCP connections on port 8080, plus the listening sockets awaiting new device adoption attempts. If a device appears offline in the controller UI but `ss` reveals an established socket from its IP, the disconnection likely stems from application-layer protocol errors rather than network-layer connectivity loss.

To cross-validate controller reachability from a managed device, SSH into a UniFi switch or gateway and execute `nc -zv <controller_ip> 8080` to probe TCP connectivity. The `-z` flag enables zero-I/O mode, closing the connection immediately after successful handshake, while `-v` activates verbose output. A successful probe returns `Connection to <controller_ip> 8080 port [tcp/*] succeeded!`, confirming layer-4 reachability. Augment this with an HTTP-layer validation: `curl -k https://<controller_ip>:8443/status` should return the controller's software version JSON if the web server responds correctly. The `-k` flag disables certificate validation, necessary since UniFi controllers employ self-signed certificates by default.

The UniFi controller exposes a REST API on port 8443 under the `/proxy/network/api` path prefix. Authenticate by obtaining a session cookie through the `/api/login` endpoint, then query device state via `/api/s/default/stat/device`. The following shell script automates this workflow, retrieving the complete device inventory with adoption state, firmware versions, and uptime statistics:

```bash
#!/bin/bash
CONTROLLER="https://192.168.1.1:8443"
USERNAME="admin"
PASSWORD="password"

# Obtain session cookie
COOKIE=$(curl -k -s -c - -X POST \
  "${CONTROLLER}/api/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${USERNAME}\",\"password\":\"${PASSWORD}\"}" \
  | grep unifises | awk '{print $7}')

# Query device statistics
curl -k -s -b "unifises=${COOKIE}" \
  "${CONTROLLER}/proxy/network/api/s/default/stat/device" \
  | jq '.data[] | {name, model, version, state, uptime}'
```

The script employs `curl` with the `-k` flag to bypass certificate validation, `-s` for silent operation suppressing progress meters, and `-c -` to capture cookies to stdout. The login endpoint returns a JSON response containing metadata, but the essential session token resides in the `Set-Cookie` header, extracted via `grep` and `awk`. Subsequent API calls include this cookie via the `-b` flag, authenticating the request. The `/stat/device` endpoint returns a JSON array of all adopted devices, which `jq` filters to essential fields: device name, model designation, firmware version, adoption state, and uptime in seconds.

For gateway appliances running EdgeOS (EdgeRouter series) rather than UniFi OS, the verification workflow shifts to EdgeOS-specific tooling. SSH into the EdgeRouter and execute `show interfaces` to enumerate all physical and logical interfaces with their operational states. This command surfaces not only Ethernet ports but also VLAN sub-interfaces, PPPoE sessions, and VPN tunnels. Follow with `show firewall statistics` to inspect per-rule packet and byte counters, validating that traffic flows through expected firewall chains. The `show nat statistics` command reveals source NAT (SNAT) and destination NAT (DNAT) translation counts, critical for diagnosing masquerading misconfigurations.

EdgeOS routers maintain a connection tracking table in kernel memory, queryable via `sudo conntrack -L` (the EdgeOS `show` commands wrap this utility). Each entry represents a tracked flow with source and destination tuples, protocol state, and remaining timeout. Under high load, the connection tracking table may saturate, causing new flows to fail. Verify current utilization with `sudo conntrack -C`, which returns the count of active tracked connections. Compare this against the maximum table size exposed via `sysctl net.netfilter.nf_conntrack_max`. If utilization approaches the maximum, consider increasing the limit through `sysctl -w net.netfilter.nf_conntrack_max=<new_value>` or optimizing timeout parameters.

The final live state inspection involves packet-level traffic capture to validate correct protocol framing and absence of transmission anomalies. On the controller host, execute `tcpdump -i any -n port 8080 -c 100 -w /tmp/unifi_control.pcap` to capture one hundred packets traversing any interface on port 8080, writing the raw PCAP file to `/tmp/unifi_control.pcap`. The `-i any` directive captures across all interfaces, essential when the controller bridges multiple networks. The `-n` flag disables DNS resolution, preventing capture distortion from resolver queries. The `-c 100` limit prevents indefinite capture, while `-w` specifies the output file.

Transfer the PCAP file to a workstation equipped with Wireshark and open it for analysis. Filter the display to `tcp.stream eq 0` to isolate a single TCP conversation between the controller and a device. The packet sequence should reveal a three-way handshake (SYN, SYN-ACK, ACK), followed by HTTP-framed JSON messages exchanging device telemetry and configuration updates. Inspect the TCP window scaling options in the handshake to confirm that both endpoints negotiate appropriate receive window sizes; inadequate windows throttle throughput on high-latency links. Verify that no retransmissions occur by filtering `tcp.analysis.retransmission`, as retransmissions indicate packet loss or out-of-order delivery.

For wireless traffic analysis, configure a UniFi access point to mirror all packets to a designated monitoring port by enabling the "Port Mirroring" feature within the UniFi controller's device settings. Direct the mirrored traffic to a Linux host running `tcpdump -i <mirror_interface> -w /tmp/wireless_traffic.pcap`, capturing all 802.11 management frames, control frames, and data frames traversing the access point's radios. This enables offline analysis of client association handshakes, authentication exchanges, and roaming events without injecting a monitoring device into the wireless medium.

## Exercise 2: Benchmarking & Saturation Profiling

The second verification exercise quantifies the performance boundaries and saturation characteristics of the UniFi network infrastructure under synthetic load. Unlike live state inspection, which observes passive operation, benchmarking actively drives the system toward its design limits to validate headroom, identify bottlenecks, and characterize degradation modes. The practitioner orchestrates traffic generators, measures key performance indicators, and correlates observed saturation with underlying kernel and hardware constraints.

Begin by establishing a baseline throughput measurement for the primary data plane: the gateway appliance's routing and NAT engine. On a client host connected to the LAN segment, install `iperf3` via `apt-get install -y iperf3` and launch a server instance with `iperf3 -s -p 5201`. On a second client host positioned beyond the gateway's WAN interface (or simulate this by placing the server on the WAN side), execute `iperf3 -c <server_ip> -p 5201 -t 60 -P 8` to initiate a sixty-second throughput test using eight parallel TCP streams. The `-t 60` parameter sustains the test for one minute, allowing TCP congestion control to stabilize. The `-P 8` flag spawns eight concurrent streams, exercising the gateway's ability to distribute flows across multiple CPU cores.

Monitor the gateway's CPU utilization during the test via `ssh <gateway_ip> "top -b -n 5 | grep Cpu"` to capture five snapshots of CPU usage. Alternatively, for EdgeOS routers, use `show system processes extensive` to display per-core utilization. A properly scaled gateway should exhibit CPU usage distributing across all cores, with no single core saturating at 100% while others remain idle. Single-core saturation indicates a flow processing bottleneck where the kernel's Receive Packet Steering (RPS) or Receive Flow Steering (RFS) mechanisms fail to distribute interrupts and packet processing across the available CPU topology.

The iperf3 output reports achieved throughput in megabits per second, along with TCP retransmission counts and congestion window evolution. A UDM-Pro with a 10 Gbps WAN port should sustain line-rate bidirectional traffic when routing between LAN and WAN segments, provided the CPU architecture supports hardware offload engines. If throughput plateaus below hardware limits, inspect offload configurations with `ethtool -k <interface>` to verify that TSO, GRO, and checksum offload remain enabled. Disabled offload forces the CPU to perform segmentation and validation in software, drastically reducing throughput.

Next, benchmark the NAT session establishment rate by generating a high volume of short-lived TCP connections. Install `hping3` on a client host and execute `hping3 -S -p 80 --flood --rand-source <wan_target_ip>` to flood the gateway with SYN packets from randomized source IPs. The `--flood` flag maximizes packet rate, while `--rand-source` forces each packet to appear as a new connection, stressing the connection tracking subsystem. Monitor the gateway's conntrack table utilization with `watch -n 1 "ssh <gateway_ip> 'sudo conntrack -C'"` to observe real-time growth. If the conntrack table saturates, new connections will fail silently, manifesting as intermittent connectivity from client devices.

The UniFi controller itself introduces a control plane performance dimension: its capacity to process telemetry streams from managed devices without inducing processing delays. Construct a synthetic load by simulating multiple device adoption cycles. If the lab environment includes spare UniFi access points, initiate rapid adoption sequences by factory-resetting devices and triggering simultaneous adoption attempts. Alternatively, script repeated API calls to the `/api/s/default/stat/device` endpoint from multiple concurrent clients, measuring response latencies under load.

Deploy the following Python script to generate sustained API query load against the controller:

```python
#!/usr/bin/env python3
import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor

CONTROLLER = "https://192.168.1.1:8443"
USERNAME = "admin"
PASSWORD = "password"
NUM_THREADS = 20
NUM_REQUESTS = 100

session = requests.Session()
session.verify = False

# Authenticate once
login_data = {"username": USERNAME, "password": PASSWORD}
session.post(f"{CONTROLLER}/api/login", json=login_data)

def query_devices():
    start = time.time()
    response = session.get(f"{CONTROLLER}/proxy/network/api/s/default/stat/device")
    latency = time.time() - start
    return latency, response.status_code

latencies = []
with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
    futures = [executor.submit(query_devices) for _ in range(NUM_REQUESTS)]
    for future in futures:
        latency, status = future.result()
        latencies.append(latency)
        print(f"Status: {status}, Latency: {latency:.3f}s")

print(f"\nMean latency: {statistics.mean(latencies):.3f}s")
print(f"Median latency: {statistics.median(latencies):.3f}s")
print(f"P95 latency: {sorted(latencies)[int(len(latencies)*0.95)]:.3f}s")
print(f"P99 latency: {sorted(latencies)[int(len(latencies)*0.99)]:.3f}s")
```

This script spawns twenty threads, each issuing one hundred device query requests, totaling two thousand API calls. The script measures per-request latency from initiation to response receipt, accumulating the measurements into a distribution. Post-execution, the script computes mean, median, 95th percentile (P95), and 99th percentile (P99) latencies. Healthy controllers exhibit P95 latencies below 200 milliseconds under normal load. If P95 exceeds one second, the controller's Java Virtual Machine may suffer garbage collection pauses, insufficient heap memory, or database query inefficiencies.

For wireless performance benchmarking, position a client device at varying distances from a UniFi access point and execute throughput tests at each location. Use `iperf3` as before, but augment measurements with RSSI and noise floor readings captured from the client's wireless interface. On Linux clients, retrieve these metrics via `iw dev <interface> link` to display the current RSSI, transmit bitrate, and associated BSSID. Plot throughput against RSSI to construct a performance curve, identifying the threshold below which throughput collapses due to excessive retransmissions.

The UniFi controller's WebSocket telemetry stream represents another saturation vector. Each adopted device maintains a persistent WebSocket connection, streaming real-time statistics at approximately one message per second. Open the UniFi controller UI in a web browser and activate the browser's developer console. Navigate to the Network tab and filter to WebSocket connections. Observe the frame rate and message sizes exchanged between the browser and controller. A controller managing one hundred devices must multiplex telemetry from all devices to each connected UI session, potentially saturating its WebSocket message queue under multiple concurrent administrative sessions.

Benchmark switch fabric performance by configuring VLAN trunking between two UniFi switches and routing large file transfers across VLANs through the gateway. The gateway's inter-VLAN routing engine must inspect each packet's layer-3 header and forward accordingly, potentially introducing latency compared to purely layer-2 switched traffic. Use `dd` and `nc` to construct a synthetic large file transfer: on one host, execute `dd if=/dev/zero bs=1M count=10000 | nc <remote_host> 9999` to stream 10 GB of zeroed data. On the remote host, receive with `nc -l 9999 > /dev/null`. Measure throughput via the transfer duration and compare against direct switch-to-switch throughput to quantify the gateway's inter-VLAN routing overhead.

Finally, stress-test the gateway's firewall ruleset by generating traffic patterns that exercise complex rule chains. UniFi gateways implement stateful packet filtering via Netfilter, processing each packet against sequential rule chains. A ruleset with hundreds of rules introduces linear processing overhead, as each packet traverses the chain until a matching rule terminates evaluation. Construct a worst-case scenario by placing the most frequently matched rule at the end of the chain, forcing every packet to evaluate all preceding rules. Benchmark the throughput delta between an empty ruleset and a maximally complex ruleset to quantify per-rule processing cost.

## Exercise 3: Fault Injection & Recovery Analysis

The third verification exercise transitions from passive observation and active benchmarking to deliberate fault injection, assessing the infrastructure's resilience under adverse conditions. Practitioners orchestrate controlled failures—link disconnections, process terminations, configuration corruption—and measure the system's detection latency, failover behavior, and recovery completeness. This exercise validates that monitoring alarms trigger correctly, that redundant paths activate transparently, and that stateful subsystems reconverge without administrative intervention.

Begin with a layer-1 fault injection: physically disconnect the WAN uplink from the gateway appliance while monitoring the controller's alarm subsystem and client connectivity. On a UDM-Pro, the WAN interface typically manifests as a dedicated SFP+ or RJ45 port. Disconnect the cable and immediately commence observation through multiple vantage points. First, execute `ip link show <wan_interface>` on the gateway to confirm that the kernel detects the link-down event, transitioning the interface's operational state to `NO-CARRIER`. The detection latency depends on the Ethernet PHY's link monitoring interval, typically converging within one to three seconds.

Simultaneously, monitor the UniFi controller UI for alarm generation. The controller should raise a "WAN Down" alarm within ten seconds, reflecting the gateway's reporting cycle. If the alarm fails to appear, verify that the gateway's device heartbeat to the controller remains intact by checking `ss -tunap | grep 8080` on the gateway. A persistent established socket confirms that the control plane remains functional despite data plane failure, as the gateway likely falls back to LAN-side management reachability.

Next, observe client behavior during the WAN outage. Internal LAN-to-LAN communication should continue uninterrupted, as the layer-2 switching fabric operates independently of WAN reachability. However, clients attempting to reach internet destinations will experience connection timeouts. Validate this by pinging an external IP from a LAN client while capturing ICMP traffic with `tcpdump -i <lan_interface> icmp`. The gateway should respond with ICMP Destination Unreachable messages if its routing table lacks a default route, or silently drop packets if firewall rules block ICMP generation.

Restore the WAN link and measure reconvergence time. The gateway's DHCP client (if WAN uses DHCP) must renegotiate an IP address, re-establish default routing, and update DNS resolvers. Measure the interval from cable reconnection to successful internet connectivity by scripting a continuous ping to an external target: `ping -i 0.5 8.8.8.8 | ts '[%Y-%m-%d %H:%M:%S]'` timestamps each ICMP reply, enabling precise identification of the first successful response post-reconnection. Typical reconvergence completes within ten to fifteen seconds, dominated by DHCP DORA handshake latency.

For environments employing dual-WAN configurations with automatic failover, inject a fault by degrading the primary WAN's quality rather than fully disconnecting it. Many UniFi gateways support failover triggered by latency or packet loss thresholds. Configure the primary WAN's failover policy to activate upon 5% packet loss sustained over thirty seconds. Induce controlled packet loss by introducing a Linux-based middlebox between the gateway and upstream ISP router, running `tc qdisc add dev <wan_interface> root netem loss 5%` to stochastically drop 5% of outbound packets. Monitor the gateway's routing table with `watch -n 1 "ip route show table main"` to observe the default route migrating from the primary to secondary WAN interface.

The failover event should complete transparently from the client perspective, with active TCP connections surviving the transition through the gateway's stateful NAT migration. However, real-world failovers often expose corner cases: long-lived TCP sessions may stall if the new WAN path exhibits asymmetric routing, and UDP-based protocols lacking flow state may experience transient failures. Validate session continuity by maintaining an SSH connection to an external host during failover and confirming that the session remains interactive throughout.

Next, inject a controller-level fault by terminating the UniFi controller process and observing device behavior. If the controller runs under systemd, execute `systemctl stop unifi` to gracefully halt the service. Adopted devices will detect the controller absence when their TCP keep-alive probes fail, typically within two minutes dictated by TCP keepalive parameters. Despite losing controller connectivity, devices continue forwarding traffic autonomously, as their last-applied configurations persist in local non-volatile storage. Wireless clients remain associated, switches continue learning MAC addresses, and the gateway maintains its routing table.

However, dynamic operations requiring controller coordination will fail: new client adoptions stall, administrative UI access becomes unavailable, and devices cannot retrieve configuration updates. Simulate a configuration change requirement during the outage by attempting to modify a firewall rule through the CLI on the gateway itself. On EdgeOS routers, configuration persists locally and commits independently of controller state, but UniFi OS gateways tightly couple configuration management to the controller, preventing local overrides.

Restart the controller via `systemctl start unifi` and measure the re-adoption latency for each device. Devices periodically retry controller discovery via UDP broadcasts on port 10001, falling back to DNS-based discovery if a `unifi` A record exists in the local DNS zone. Upon successful reconnection, devices synchronize their configurations with the controller, downloading any pending updates. Monitor the controller's MongoDB access logs to observe the burst of database read operations as devices re-register and reconcile state.

Introduce a configuration corruption fault by manually editing the controller's database. If running the controller in Docker, execute `docker exec -it <container_name> mongo --port 27117` to attach to the embedded MongoDB instance. Query the `device` collection with `db.device.find({"name": "Switch-Office"})` to retrieve a specific device's document. Modify a critical field such as the `ip` address to an invalid value: `db.device.update({"name": "Switch-Office"}, {$set: {"ip": "999.999.999.999"}})`. Restart the controller and observe the resulting behavior. The controller may fail to communicate with the device, raising persistent "Unreachable" alarms, or it may self-heal by rediscovering the device's actual IP through ARP table inspection.

For wireless-specific fault injection, simulate RF interference by introducing a rogue access point on the same channel as a production UniFi AP. Configure the rogue AP to broadcast beacon frames at maximum power and transmit continuous data traffic to saturate the channel. From a client device, execute `iw dev <interface> scan` to enumerate visible BSSIDs and their signal strengths. The production AP should exhibit degraded throughput due to increased medium contention and collision backoff. Capture the RF environment with `tcpdump -i <monitor_interface> -e -s0 -w /tmp/interference.pcap` in monitor mode to visualize overlapping transmissions.

Test the gateway's routing reconvergence under BGP session failure if the deployment employs BGP for WAN redundancy. Access the gateway's CLI and administratively disable the BGP neighbor session with `set protocols bgp <asn> neighbor <peer_ip> shutdown`. Commit the configuration and observe the routing table purging learned routes from that peer. Validate that traffic immediately shifts to alternate paths by tracing a packet's route with `traceroute -n <external_ip>`. Re-enable the BGP session and confirm that routes re-populate and traffic reverts to the original path, subject to BGP path selection policies.

Finally, simulate a cascading failure scenario: simultaneously disconnect the WAN uplink, terminate the controller process, and introduce packet loss on the LAN fabric by running `tc qdisc add dev br0 root netem loss 2%` on the gateway's bridge interface. This multi-domain fault stresses the infrastructure's ability to degrade gracefully, maintaining partial functionality rather than collapsing entirely. Observe that despite the controller's absence and WAN failure, LAN-to-LAN communication persists, though with elevated latency and occasional retransmissions due to the induced packet loss. This exercise confirms that the architecture exhibits fail-safe properties, where individual component failures do not propagate into total system unavailability.

## Diagnostic Cheat Sheet & Verification Checklist

This consolidated reference distills the essential diagnostic commands and verification workflows into a practitioner-ready checklist, enabling rapid troubleshooting and methodical pre-production validation. The checklist organizes commands by operational domain: network stack introspection, controller API validation, device connectivity verification, and performance boundary testing.

**Network Stack Introspection**

- Display all interfaces with statistics: `ip -s -d link show`
- Show detailed socket state for controller: `ss -tunap | grep java`
- Enumerate connection tracking entries: `sudo conntrack -L | wc -l`
- Query maximum conntrack table size: `sysctl net.netfilter.nf_conntrack_max`
- Inspect interface hardware offload settings: `ethtool -k eth0`
- Display per-interface driver-level statistics: `ethtool -S eth0`
- Capture traffic on specific port to PCAP: `tcpdump -i any -n port 8080 -w /tmp/capture.pcap`
- Monitor real-time packet rate on interface: `watch -n 1 "ethtool -S eth0 | grep rx_packets"`

**UniFi Controller API Validation**

- Authenticate and retrieve device list:

```bash
COOKIE=$(curl -k -s -c - -X POST https://192.168.1.1:8443/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | grep unifises | awk '{print $7}')
curl -k -s -b "unifises=${COOKIE}" \
  https://192.168.1.1:8443/proxy/network/api/s/default/stat/device \
  | jq '.data[] | {name, state, uptime}'
```

- Query active client associations: `curl -k -s -b "unifises=${COOKIE}" https://192.168.1.1:8443/proxy/network/api/s/default/stat/sta | jq '.data[].hostname'`
- Retrieve controller system information: `curl -k https://192.168.1.1:8443/status | jq`
- Force device reconnection via API: `curl -k -b "unifises=${COOKIE}" -X POST https://192.168.1.1:8443/proxy/network/api/s/default/cmd/devmgr -d '{"cmd":"force-provision","mac":"<device_mac>"}'`

**Device Connectivity Verification**

- Test TCP reachability to controller from device: `nc -zv <controller_ip> 8080`
- Validate HTTP response from controller: `curl -k -I https://<controller_ip>:8443`
- Check device-side controller IP resolution: `nslookup unifi`
- Trace packet path to controller: `traceroute -n <controller_ip>`
- Verify STUN port accessibility: `nc -u -zv <controller_ip> 3478`
- Test DNS resolution from gateway: `dig @8.8.8.8 google.com +short`

**EdgeOS Router Commands**

- Display all interfaces and status: `show interfaces`
- Show routing table: `show ip route`
- Inspect NAT translations: `show nat translations`
- Display firewall rule statistics: `show firewall statistics`
- Monitor connection tracking table: `show conntrack table`
- Verify BGP neighbor status (if applicable): `show ip bgp summary`
- Test connectivity with source interface: `ping 8.8.8.8 source-address <wan_ip>`

**Performance Boundary Testing**

- Baseline LAN-to-WAN throughput: `iperf3 -c <remote_server> -p 5201 -t 60 -P 8`
- Measure NAT session establishment rate: `hping3 -S -p 80 --flood --rand-source <wan_ip>`
- Benchmark inter-VLAN routing: `iperf3 -c <vlan_host> -t 30` with source in different VLAN
- Stress-test controller API: Execute Python concurrent request script above
- Monitor CPU utilization during load: `ssh <gateway_ip> "top -b -n 5 | grep Cpu"`
- Observe conntrack growth under load: `watch -n 1 "ssh <gateway_ip> 'sudo conntrack -C'"`

**Wireless Diagnostics**

- Scan for visible SSIDs and channels: `iw dev wlan0 scan | grep -E 'SSID|freq|signal'`
- Display current association details: `iw dev wlan0 link`
- Monitor real-time signal strength: `watch -n 1 "iw dev wlan0 station dump"`
- Capture 802.11 management frames (requires monitor mode): `tcpdump -i wlan0mon -e -s0 subtype beacon`

**Fault Injection Recovery Validation**

- Verify link-down detection latency: Disconnect cable, measure time until `ip link show` reflects `NO-CARRIER`
- Confirm controller alarm generation: Check UI for "WAN Down" or device unreachable alarms within 15 seconds
- Measure WAN failover convergence: `watch -n 1 "ip route show table main | grep default"`
- Validate device autonomous operation: Terminate controller, confirm continued forwarding
- Test configuration persistence: Reboot device, SSH in, verify running config matches last controller sync

**Pre-Production Verification Checklist**

Execute this sequence prior to declaring a UniFi deployment production-ready:

1. Confirm all devices display "Connected" state in controller UI with firmware versions synchronized to target release
2. Validate controller accessibility from all VLANs via `curl -k https://<controller_ip>:8443/status` from test host in each VLAN
3. Execute `ip -s link show` on gateway, verify zero errors and drops on all active interfaces
4. Run `ss -tunap | grep 8080` on controller, confirm established TCP session for each adopted device
5. Perform `iperf3` throughput test across WAN interface, verify achievement of ≥95% line rate
6. Query `sudo conntrack -C` on gateway under representative load, confirm utilization <70% of `nf_conntrack_max`
7. Inject WAN link failure via cable disconnect, verify alarm generation within 15 seconds and reconvergence within 30 seconds post-restoration
8. Test dual-WAN failover (if configured) by degrading primary link with `tc netem loss 10%`, confirm automatic failover and session continuity
9. Capture 60 seconds of traffic with `tcpdump` on each interface, analyze in Wireshark for retransmissions >0.5%
10. Execute wireless roaming test: associate client to AP-1, walk to AP-2's coverage area, verify seamless handoff without session interruption
11. Validate firewall ruleset by attempting explicitly blocked traffic patterns, confirm drops logged correctly
12. Terminate and restart controller, measure device re-adoption time (target: <120 seconds for all devices)
13. Stress-test controller API with concurrent request script, verify P95 latency <200ms under 20 concurrent sessions
14. Review controller logs for recurring errors: `tail -f /var/log/unifi/server.log | grep -i error`
15. Document baseline performance metrics: achieved throughput, typical CPU utilization, conntrack table size under normal load

This verification framework ensures that the deployed UniFi infrastructure operates within design parameters, exhibits predictable behavior under fault conditions, and maintains sufficient headroom for future growth. Practitioners executing these exercises acquire deep operational intuition, enabling rapid diagnosis of production anomalies through systematic elimination of hypotheses grounded in verifiable kernel and application state.
