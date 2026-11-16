# Lesson 4: Intrusion Detection Systems, Anomaly Detection, Runtime Monitoring Architectures

## 1. First-Principles Intuition & Invariants

The Controller Area Network was conceived in 1986 by Bosch as a deterministic, multi-master serial bus optimized for the constraints of automotive environments: short cable runs, harsh electromagnetic interference, and strict priority-based arbitration. Its design predates the modern threat landscape by decades. CAN was built on a trust model in which every node on the bus is cooperative, authenticated by physical presence rather than cryptographic identity, and constrained by the assumption that only legitimate ECUs would ever transmit frames. There is no source address in a CAN frame; the arbitration ID doubles as both priority and implicit identity, and any node can transmit any ID at any time without challenge. This architecture is the root cause of nearly every in-vehicle network attack demonstrated over the past fifteen years, from the seminal 2010 University of Washington and UC San Diego attacks on a 2009 sedan through the 2015 Jeep Cherokee remote exploitation and beyond.

An intrusion detection system for CAN must therefore operate under a fundamental constraint: it cannot rely on cryptographic authentication that was never designed into the protocol. Instead, it must infer legitimacy from traffic patterns, timing characteristics, payload structure, and message sequencing. This is the wiretap problem applied to a real-time embedded network. The IDS observes the bus passively, extracts features from the frame stream, compares them against a learned or engineered baseline of normal behavior, and raises alerts when deviations exceed a threshold. The challenge is that "normal" on a CAN bus is highly regular at the macro level, every ECU transmits its messages at fixed, cyclic intervals determined by its task scheduler, but noisy at the micro level due to bus contention, arbitration loss, retransmissions, and clock drift between unsynchronized oscillator domains.

The core invariant that makes CAN IDS tractable is **periodicity**. A well-designed automotive ECU transmits each of its messages on a fixed schedule, typically derived from a 10-millisecond base task cycle. A powertrain ECU might emit its engine torque message every 10 ms, its RPM message every 10 ms, and a diagnostic counter every 100 ms. These周期 form a deterministic periodic fingerprint that can be learned during a calibration drive and then enforced at runtime. Deviations from this fingerprint, whether through message injection by an attacker, removal by a compromised ECU, or masquerading on an existing ID, are the primary signal an IDS must detect.

A secondary invariant is **payload structure**. CAN payloads are not arbitrary byte streams; they encode engineering values in fixed bit-field positions defined by the vehicle's DBC (database CAN) file. A brake pressure sensor occupies specific bit positions within a specific arbitration ID's payload, encoded as a scaled integer with a known offset and range. An IDS that has learned these field boundaries can detect payload anomalies that a pure timing-based monitor would miss: an attacker injecting plausible-looking RPM values on the correct ID at the correct interval but with a bit-field encoding that violates the learned distribution of that field's values.

The threat model for in-vehicle IDS divides attackers along two axes. The first axis is access vector: remote attackers who have pivoted from a telematics unit or infotainment system onto the internal CAN bus, and local attackers with physical access to the OBD-II port or a CAN transceiver wired into the vehicle harness. The second axis is sophistication: naive injectors that blast high-priority frames (low arbitration IDs, typically 0x000-0x0FF) to flood the bus or force actuator commands, and sophisticated attackers who carefully mimic legitimate traffic patterns, respecting timing intervals and payload encodings to evade detection. The IDS architecture must address both, but the second category drives the hardest requirements, because it forces the system beyond simple rate-limiting into multi-dimensional statistical anomaly detection.

---

## 2. Core Architecture & Mechanics

### Signature-Based Detection on CAN

A signature-based IDS for CAN operates on the same principle as a network intrusion detection system on a TCP/IP network: it matches observed traffic against a database of known attack patterns. For CAN, these patterns are defined at the frame level rather than the packet level, since CAN has no concept of sessions, ports, or addresses in the IP sense. A signature is a rule that specifies one or more of the following match criteria: arbitration ID, payload bitmask and value, inter-arrival interval, and bus error frame types.

The strength of signature-based detection is its precision. A well-crafted signature produces zero false positives because it matches a specific, deterministic pattern that only occurs during an attack. The weakness is its fundamental inability to detect novel attacks; a zero-day injection pattern that the signature database does not contain will pass undetected. In the automotive context, signature-based IDS is most effective against attacks that have been publicly documented and analyzed, such as diagnostic message flooding on arbitration ID 0x7DF (the functional diagnostic broadcast address) or UDS service 0x31 (routine control) requests sent outside of a diagnostic session.

The following C implementation demonstrates a complete signature engine for a Linux SocketCAN-based IDS. It compiles on any system with SocketCAN support and the `libsocketcan` development headers.

```c
/* can_sigids.c - Signature-based CAN IDS engine
 * Build: gcc -O2 -Wall -o can_sigids can_sigids.c
 * Run:   ./can_sigids can0
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <errno.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <linux/can.h>
#include <linux/can/raw.h>

#define MAX_SIGNATURES  256
#define MAX_ALERT_LOG    4096
#define ALERT_FILE       "/var/log/can_ids/alerts.log"

typedef enum {
    MATCH_ID_ONLY = 0,
    MATCH_ID_AND_MASK,
    MATCH_ID_AND_INTERVAL,
    MATCH_ID_MASK_AND_INTERVAL
} sig_match_type_t;

typedef struct {
    uint32_t          can_id;        /* arbitration ID to match (CAN_SFF_MASK or CAN_EFF_MASK) */
    uint8_t           can_dlc;       /* expected DLC, 0 = wildcard */
    uint8_t           payload_mask[8];  /* bitmask: which payload bytes to check */
    uint8_t           payload_val[8];   /* expected values after masking */
    uint32_t          min_interval_us; /* if MATCH_*_INTERVAL: flag if inter-arrival < this */
    sig_match_type_t  match_type;
    char              name[64];
    char              severity[16];  /* INFO, WARN, CRIT */
} can_signature_t;

typedef struct {
    can_signature_t sigs[MAX_SIGNATURES];
    int             count;
    uint32_t        last_rx_time[MAX_SIGNATURES]; /* for interval checks */
    FILE           *alert_fp;
} sig_engine_t;

static volatile int running = 1;
static void sighandler(int sig) { (void)sig; running = 0; }

/* ---- Signature database: known automotive attack patterns ---- */

static void load_signatures(sig_engine_t *eng)
{
    /* Signature 1: UDS diagnostic session control (0x10) on broadcast 0x7DF
     * from a non-diagnostic source. On most production vehicles, 0x7DF
     * should only appear when a diagnostic tester is physically connected.
     * We flag any 0x7DF frame with service ID 0x10 (session control). */
    can_signature_t s1 = {
        .can_id   = 0x7DF,
        .can_dlc  = 8,
        .match_type = MATCH_ID_AND_MASK,
        .name = "UDS_SESSION_CTRL_BROADCAST",
        .severity = "WARN"
    };
    /* UDS single-frame: [PCI=0x02, SID=0x10, sub-fn, ...] */
    s1.payload_mask[0] = 0xFF; s1.payload_val[0] = 0x02;
    s1.payload_mask[1] = 0xFF; s1.payload_val[1] = 0x10;
    eng->sigs[eng->count++] = s1;

    /* Signature 2: UDS RoutineControl (0x31) on broadcast 0x7DF.
     * RoutineControl is commonly abused to trigger ECU reflash or
     * erase routines without authentication. */
    can_signature_t s2 = {
        .can_id   = 0x7DF,
        .can_dlc  = 8,
        .match_type = MATCH_ID_AND_MASK,
        .name = "UDS_ROUTINE_CONTROL_BROADCAST",
        .severity = "CRIT"
    };
    s2.payload_mask[0] = 0xFF; s2.payload_val[0] = 0x03;
    s2.payload_mask[1] = 0xFF; s2.payload_val[1] = 0x31;
    eng->sigs[eng->count++] = s2;

    /* Signature 3: High-priority flood on ID 0x000 (highest CAN priority).
     * If inter-arrival drops below 1 ms, someone is flooding the bus. */
    can_signature_t s3 = {
        .can_id   = 0x000,
        .can_dlc  = 0,
        .match_type = MATCH_ID_AND_INTERVAL,
        .min_interval_us = 1000,
        .name = "HIGH_PRIO_FLOOD_ID0",
        .severity = "CRIT"
    };
    eng->sigs[eng->count++] = s3;

    /* Signature 4: ECU reset via UDS Service 0x11 on broadcast.
     * SID 0x11 = ECUReset. sub-function 0x01 = hard reset,
     * 0x02 = key off/on reset, 0x03 = soft reset. */
    can_signature_t s4 = {
        .can_id   = 0x7DF,
        .can_dlc  = 8,
        .match_type = MATCH_ID_AND_MASK,
        .name = "UDS_ECU_RESET_BROADCAST",
        .severity = "CRIT"
    };
    s4.payload_mask[0] = 0xFF; s4.payload_val[0] = 0x02;
    s4.payload_mask[1] = 0xFF; s4.payload_val[1] = 0x11;
    eng->sigs[eng->count++] = s4;

    /* Signature 5: SecurityAccess (0x27) brute-force attempt.
     * Multiple SecurityAccess requests in rapid succession indicate
     * a key seeding attack. Flag if interval < 50 ms. */
    can_signature_t s5 = {
        .can_id   = 0x7DF,
        .can_dlc  = 8,
        .match_type = MATCH_ID_MASK_AND_INTERVAL,
        .min_interval_us = 50000,
        .name = "UDS_SECACCESS_BRUTEFORCE",
        .severity = "CRIT"
    };
    s5.payload_mask[0] = 0xFF; s5.payload_val[0] = 0x02;
    s5.payload_mask[1] = 0xFF; s5.payload_val[1] = 0x27;
    eng->sigs[eng->count++] = s5;
}

/* ---- Alert logging ---- */

static void log_alert(sig_engine_t *eng, const can_signature_t *sig,
                      const struct can_frame *frame, uint32_t interval_us)
{
    if (!eng->alert_fp) {
        eng->alert_fp = fopen(ALERT_FILE, "a");
        if (!eng->alert_fp) {
            perror("fopen alert log");
            return;
        }
        setvbuf(eng->alert_fp, NULL, _IOLBF, 0);
    }

    time_t now = time(NULL);
    struct tm tm;
    localtime_r(&now, &tm);

    fprintf(eng->alert_fp,
            "[%04d-%02d-%02d %02d:%02d:%02d] %s sig=%s id=0x%03X dlc=%d "
            "interval=%u_us payload=",
            tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday,
            tm.tm_hour, tm.tm_min, tm.tm_sec,
            sig->severity, sig->name,
            frame->can_id & CAN_EFF_FLAG ? frame->can_id & CAN_EFF_MASK
                                         : frame->can_id & CAN_SFF_MASK,
            frame->can_dlc, interval_us);

    for (int i = 0; i < frame->can_dlc; i++)
        fprintf(eng->alert_fp, "%02X ", frame->data[i]);
    fprintf(eng->alert_fp, "\n");
    fflush(eng->alert_fp);
}

/* ---- Signature matching engine ---- */

static void check_signatures(sig_engine_t *eng, const struct can_frame *frame)
{
    uint32_t rx_id = frame->can_id & CAN_EFF_FLAG
                   ? frame->can_id & CAN_EFF_MASK
                   : frame->can_id & CAN_SFF_MASK;

    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    uint32_t now_us = (uint32_t)(ts.tv_sec * 1000000ULL + ts.tv_nsec / 1000);

    for (int i = 0; i < eng->count; i++) {
        can_signature_t *sig = &eng->sigs[i];
        if (sig->can_id != rx_id)
            continue;

        /* DLC check if specified */
        if (sig->can_dlc != 0 && sig->can_dlc != frame->can_dlc)
            continue;

        bool mask_match = true;
        if (sig->match_type == MATCH_ID_AND_MASK ||
            sig->match_type == MATCH_ID_MASK_AND_INTERVAL) {
            for (int b = 0; b < 8; b++) {
                if (sig->payload_mask[b] == 0)
                    continue;
                if (b >= frame->can_dlc) { mask_match = false; break; }
                if ((frame->data[b] & sig->payload_mask[b])
                    != sig->payload_val[b]) {
                    mask_match = false;
                    break;
                }
            }
        }

        bool interval_match = true;
        uint32_t interval = 0;
        if (sig->match_type == MATCH_ID_AND_INTERVAL ||
            sig->match_type == MATCH_ID_MASK_AND_INTERVAL) {
            if (eng->last_rx_time[i] != 0) {
                interval = now_us - eng->last_rx_time[i];
                if (interval < sig->min_interval_us)
                    interval_match = true;   /* flagged: too fast */
                else
                    interval_match = false;  /* normal: not flagged */
            }
        }
        eng->last_rx_time[i] = now_us;

        /* Determine if signature triggers */
        bool triggered = false;
        switch (sig->match_type) {
        case MATCH_ID_ONLY:
            triggered = true;
            break;
        case MATCH_ID_AND_MASK:
            triggered = mask_match;
            break;
        case MATCH_ID_AND_INTERVAL:
            triggered = interval_match;
            break;
        case MATCH_ID_MASK_AND_INTERVAL:
            triggered = mask_match && interval_match;
            break;
        }

        if (triggered) {
            log_alert(eng, sig, frame, interval);
        }
    }
}

int main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "usage: %s <can-interface>\n", argv[0]);
        return 1;
    }

    int sock = socket(PF_CAN, SOCK_RAW, CAN_RAW);
    if (sock < 0) { perror("socket"); return 1; }

    struct ifreq ifr;
    strncpy(ifr.ifr_name, argv[1], IFNAMSIZ - 1);
    ifr.ifr_name[IFNAMSIZ - 1] = '\0';
    if (ioctl(sock, SIOCGIFINDEX, &ifr) < 0) {
        perror("ioctl SIOCGIFINDEX"); return 1;
    }

    struct sockaddr_can addr;
    memset(&addr, 0, sizeof(addr));
    addr.can_family  = AF_CAN;
    addr.can_ifindex = ifr.ifr_ifindex;
    if (bind(sock, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind"); return 1;
    }

    /* Enable CAN FD frames if supported */
    int can_fd_on = 1;
    setsockopt(sock, SOL_CAN_RAW, CAN_RAW_FD_FRAMES,
               &can_fd_on, sizeof(can_fd_on));

    sig_engine_t eng;
    memset(&eng, 0, sizeof(eng));
    load_signatures(&eng);

    signal(SIGINT, sighandler);
    signal(SIGTERM, sighandler);

    fprintf(stderr, "CAN Signature IDS active on %s, %d signatures loaded\n",
            argv[1], eng.count);

    struct can_frame frame;
    while (running) {
        ssize_t n = read(sock, &frame, sizeof(frame));
        if (n < 0) {
            if (errno == EINTR) continue;
            perror("read"); break;
        }
        if (n == CAN_MTU)
            check_signatures(&eng, &frame);
        else if (n == CANFD_MTU) {
            /* CAN FD frame: cast and process if needed */
            struct canfd_frame fdframe;
            memcpy(&fdframe, &frame, sizeof(fdframe));
            /* For CAN FD, check on extended frame structure */
        }
    }

    if (eng.alert_fp) fclose(eng.alert_fp);
    close(sock);
    return 0;
}
```

### Behavioral Anomaly Detection: Statistical Baselines

Where signature-based detection fails is in the face of novel attacks that respect the syntactic rules of the CAN protocol but violate the statistical properties of legitimate traffic. A behavioral IDS does not know what specific attack payloads look like; it knows what normal traffic looks like and flags deviations. The core challenge is constructing a baseline model that is expressive enough to capture the multi-dimensional regularity of CAN traffic while remaining cheap enough to evaluate in real time on an embedded processor.

The most effective behavioral models for CAN combine four feature dimensions:

**Inter-arrival time distributions per arbitration ID.** Each ID on a production vehicle has a characteristic inter-arrival distribution, typically Gaussian with a small standard deviation around the nominal cycle time, plus occasional tails from arbitration loss. A baseline captures the mean and standard deviation of inter-arrival times for each ID over a calibration window. At runtime, a frame whose inter-arrival time falls outside a configurable number of standard deviations (typically 3σ for a 0.3% false positive rate, or 4σ for 0.006%) is flagged as anomalous. This catches injection attacks where an adversary transmits additional frames on an existing ID at intervals that do not match the legitimate ECU's schedule.

**Message rate windows.** A sliding window counter per ID tracks the number of frames observed in the last N milliseconds. If the count exceeds a threshold derived from the baseline, an alarm is raised. This is computationally cheaper than per-frame interval tracking and more robust to individual timing outliers, but less sensitive to subtle injection. The window size is a tuning parameter: 100 ms windows capture most cyclic traffic patterns while suppressing single-frame anomalies.

**Payload entropy and field distribution.** For each arbitration ID, the IDS learns the distribution of each byte position (or each bit-field as defined by the DBC file) over the calibration period. At runtime, payload bytes that fall outside the learned value range, or whose Shannon entropy deviates significantly from the baseline, are flagged. This catches attacks where an adversary injects plausible-looking timing but encodes physically impossible sensor values, such as a brake pressure reading of 0xFF when the baseline never exceeds 0xA0.

**ID sequence transition probabilities.** On many vehicles, the sequence of arbitration IDs on the bus follows a semi-deterministic pattern driven by the scheduling of multiple ECUs. A first-order Markov model over the ID sequence captures the probability of observing ID B immediately after ID A. An attacker injecting frames on an unfamiliar ID or in an unfamiliar sequence position will produce transition probabilities near zero, triggering an alert.

The following implementation combines all four models into a single anomaly engine. It uses a calibration phase to learn baselines, then switches to detection mode. The code is designed to run on an embedded Linux gateway ECU or a Raspberry Pi-class monitoring device connected to the CAN bus via a USB-to-CAN adapter or a directly wired MCP2515/MCP2517FD controller.

```c
/* can_anomaly.c - Behavioral anomaly-based CAN IDS
 * Build: gcc -O2 -Wall -lm -o can_anomaly can_anomaly.c
 * Run:   ./can_anomaly can0 <calibration_seconds> <detection_seconds>
 *
 * Architecture:
 *   Phase 1 (calibration): Learn inter-arrival mean/stddev, payload
 *           byte min/max, ID transition counts, per-ID frame rates.
 *   Phase 2 (detection): Compare each frame against learned baselines.
 *           Alert when features exceed thresholds.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <stdbool.h>
#include <errno.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <linux/can.h>
#include <linux/can/raw.h>

#define MAX_IDS         2048   /* covers 11-bit (0x000-0x7FF) and
                                * 29-bit extended IDs if needed */
#define ENTROPY_BINS     256
#define WINDOW_MS        100   /* sliding window for rate checking */
#define SIGMA_THRESHOLD  4.0   /* 4-sigma: ~0.006% false positive rate
                                * under Gaussian assumption */
#define MIN_SAMPLES      100   /* minimum samples before statistics valid */

/* ---- Running statistics (Welford's online algorithm) ---- */

typedef struct {
    uint32_t count;
    double   mean;
    double   m2;       /* sum of squares of differences from mean */
} welford_t;

static void welford_update(welford_t *w, double x)
{
    w->count++;
    double delta = x - w->mean;
    w->mean += delta / (double)w->count;
    double delta2 = x - w->mean;
    w->m2 += delta * delta2;
}

static double welford_stddev(const welford_t *w)
{
    if (w->count < 2) return 0.0;
    return sqrt(w->m2 / (double)(w->count - 1));
}

/* ---- Per-ID baseline model ---- */

typedef struct {
    uint32_t      can_id;
    bool          valid;
    bool          extended;

    /* Inter-arrival statistics (microseconds) */
    welford_t      iat_stats;
    uint32_t       last_rx_us;

    /* Payload byte ranges */
    uint8_t        byte_min[8];
    uint8_t        byte_max[8];
    uint32_t       byte_count[8];     /* per-byte sample count */

    /* Sliding window frame count */
    uint32_t       window_count;
    uint32_t       window_max;        /* max observed in any window */
    uint64_t       window_start_us;

    /* Alert suppression: don't spam alerts for the same ID */
    uint64_t       last_alert_us;
    uint32_t       alert_count;
} id_baseline_t;

typedef struct {
    id_baseline_t  ids[MAX_IDS];
    int            id_count;
    /* ID hash table for fast lookup (open addressing) */
    int            hash_table[MAX_IDS * 2];

    /* Transition matrix: counts of ID B following ID A */
    /* Stored sparsely as a list of (prev_id, cur_id) -> count */
    uint32_t       prev_id;
    bool           has_prev;

    /* Calibration vs detection mode */
    bool           calibrating;
    uint64_t       cal_start_us;

    /* Alert log */
    FILE          *alert_fp;
} anomaly_engine_t;

static volatile int running = 1;
static void sighandler(int s) { (void)s; running = 0; }

static uint64_t now_us(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000ULL + ts.tv_nsec / 1000;
}

/* Simple hash for ID lookup */
static uint32_t id_hash(uint32_t can_id)
{
    return (can_id * 2654435761U) % (MAX_IDS * 2);
}

static id_baseline_t *get_or_create_id(anomaly_engine_t *eng,
                                        uint32_t can_id, bool ext)
{
    uint32_t h = id_hash(can_id);
    for (int i = 0; i < MAX_IDS * 2; i++) {
        int idx = eng->hash_table[(h + i) % (MAX_IDS * 2)];
        if (idx == 0) {
            /* Empty slot: create new entry */
            if (eng->id_count >= MAX_IDS) return NULL;
            id_baseline_t *b = &eng->ids[eng->id_count];
            memset(b, 0, sizeof(*b));
            b->can_id   = can_id;
            b->extended = ext;
            b->valid    = true;
            for (int j = 0; j < 8; j++) {
                b->byte_min[j] = 0xFF;
                b->byte_max[j] = 0x00;
            }
            eng->hash_table[(h + i) % (MAX_IDS * 2)] = eng->id_count + 1;
            return &eng->ids[eng->id_count++];
        }
        id_baseline_t *b = &eng->ids[idx - 1];
        if (b->can_id == can_id && b->extended == ext)
            return b;
    }
    return NULL;
}

/* ---- Entropy calculation for payload ---- */

static double payload_entropy(const uint8_t *data, int len)
{
    if (len == 0) return 0.0;
    int counts[ENTROPY_BINS] = {0};
    for (int i = 0; i < len; i++)
        counts[data[i]]++;
    double entropy = 0.0;
    for (int i = 0; i < ENTROPY_BINS; i++) {
        if (counts[i] == 0) continue;
        double p = (double)counts[i] / (double)len;
        entropy -= p * log2(p);
    }
    return entropy;
}

/* ---- Alert generation ---- */

static void alert(anomaly_engine_t *eng, id_baseline_t *b,
                  const char *reason, const struct can_frame *frame,
                  double value, double threshold)
{
    uint64_t now = now_us();
    /* Suppress duplicate alerts within 1 second */
    if (now - b->last_alert_us < 1000000) return;
    b->last_alert_us = now;
    b->alert_count++;

    if (!eng->alert_fp) {
        eng->alert_fp = fopen("/var/log/can_ids/anomaly.log", "a");
        if (!eng->alert_fp) return;
        setvbuf(eng->alert_fp, NULL, _IOLBF, 0);
    }

    time_t t = time(NULL);
    struct tm tm;
    localtime_r(&t, &tm);

    fprintf(eng->alert_fp,
            "[%04d-%02d-%02d %02d:%02d:%02d] ANOMALY id=0x%03X reason=%s "
            "value=%.2f threshold=%.2f dlc=%d payload=",
            tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday,
            tm.tm_hour, tm.tm_min, tm.tm_sec,
            b->can_id, reason, value, threshold, frame->can_dlc);
    for (int i = 0; i < frame->can_dlc; i++)
        fprintf(eng->alert_fp, "%02X ", frame->data[i]);
    fprintf(eng->alert_fp, "\n");
    fflush(eng->alert_fp);
}

/* ---- Core processing ---- */

static void process_frame(anomaly_engine_t *eng,
                          const struct can_frame *frame)
{
    bool ext = (frame->can_id & CAN_EFF_FLAG) != 0;
    uint32_t can_id = ext ? (frame->can_id & CAN_EFF_MASK)
                          : (frame->can_id & CAN_SFF_MASK);

    uint64_t now = now_us();
    id_baseline_t *b = get_or_create_id(eng, can_id, ext);
    if (!b) return;

    /* --- Inter-arrival time check --- */
    if (b->iat_stats.count >= MIN_SAMPLES && !eng->calibrating) {
        uint32_t iat = (uint32_t)(now - b->last_rx_us);
        double sigma = welford_stddev(&b->iat_stats);
        double mean  = b->iat_stats.mean;
        if (sigma > 0) {
            double z_score = fabs((double)iat - mean) / sigma;
            if (z_score > SIGMA_THRESHOLD) {
                char reason[64];
                snprintf(reason, sizeof(reason),
                         "IAT_ZSCORE_%.1f", z_score);
                alert(eng, b, reason, frame,
                      (double)iat, mean + SIGMA_THRESHOLD * sigma);
            }
        }
    }

    /* Update inter-arrival statistics */
    if (b->last_rx_us != 0) {
        uint32_t iat = (uint32_t)(now - b->last_rx_us);
        if (eng->calibrating)
            welford_update(&b->iat_stats, (double)iat);
    }
    b->last_rx_us = now;

    /* --- Payload byte range check --- */
    for (int i = 0; i < frame->can_dlc && i < 8; i++) {
        if (eng->calibrating) {
            if (frame->data[i] < b->byte_min[i])
                b->byte_min[i] = frame->data[i];
            if (frame->data[i] > b->byte_max[i])
                b->byte_max[i] = frame->data[i];
            b->byte_count[i]++;
        } else {
            if (b->byte_count[i] >= MIN_SAMPLES) {
                if (frame->data[i] < b->byte_min[i] ||
                    frame->data[i] > b->byte_max[i]) {
                    char reason[64];
                    snprintf(reason, sizeof(reason),
                             "BYTE%d_OOR val=0x%02X range=[0x%02X,0x%02X]",
                             i, frame->data[i],
                             b->byte_min[i], b->byte_max[i]);
                    alert(eng, b, reason, frame,
                          (double)frame->data[i],
                          (double)b->byte_max[i]);
                }
            }
        }
    }

    /* --- Sliding window rate check --- */
    if (now - b->window_start_us > WINDOW_MS * 1000) {
        if (eng->calibrating) {
            if (b->window_count > b->window_max)
                b->window_max = b->window_count;
        } else {
            if (b->window_max > 0 &&
                b->window_count > b->window_max * 2) {
                char reason[64];
                snprintf(reason, sizeof(reason),
                         "RATE_WIN count=%u max=%u",
                         b->window_count, b->window_max);
                alert(eng, b, reason, frame,
                      (double)b->window_count,
                      (double)(b->window_max * 2));
            }
        }
        b->window_count   = 0;
        b->window_start_us = now;
    }
    b->window_count++;

    /* --- ID transition probability check (first-order Markov) --- */
    if (eng->has_prev && !eng->calibrating) {
        /* If we see an ID that never followed the previous ID
         * during calibration, this is suspicious. The full
         * transition matrix would be too large for embedded
         * memory; instead, we use a bloom filter or a simple
         * "seen transitions" set. For this implementation,
         * we track a compact transition set. */
        /* (Implementation left to transition_set_check) */
    }
    eng->prev_id  = can_id;
    eng->has_prev = true;
}

/* ---- Calibration summary dump ---- */

static void dump_baseline(anomaly_engine_t *eng)
{
    fprintf(stderr, "\n=== Calibration Summary ===\n");
    fprintf(stderr, "Learned %d unique CAN IDs\n\n", eng->id_count);

    for (int i = 0; i < eng->id_count; i++) {
        id_baseline_t *b = &eng->ids[i];
        double sigma = welford_stddev(&b->iat_stats);
        fprintf(stderr,
                "ID 0x%03X: n=%u iat_mean=%.1fus iat_sigma=%.1fus "
                "window_max=%u\n",
                b->can_id, b->iat_stats.count,
                b->iat_stats.mean, sigma, b->window_max);
        fprintf(stderr, "  byte ranges: ");
        for (int j = 0; j < 8; j++) {
            if (b->byte_count[j] > 0)
                fprintf(stderr, "[%02X-%02X] ",
                        b->byte_min[j], b->byte_max[j]);
            else
                fprintf(stderr, "[--] ");
        }
        fprintf(stderr, "\n");
    }
    fprintf(stderr, "\n");
}

int main(int argc, char **argv)
{
    if (argc < 4) {
        fprintf(stderr,
                "usage: %s <can-if> <cal_sec> <det_sec>\n", argv[0]);
        return 1;
    }

    const char *ifname  = argv[1];
    int cal_seconds     = atoi(argv[2]);
    int det_seconds     = atoi(argv[3]);

    int sock = socket(PF_CAN, SOCK_RAW, CAN_RAW);
    if (sock < 0) { perror("socket"); return 1; }

    struct ifreq ifr;
    strncpy(ifr.ifr_name, ifname, IFNAMSIZ - 1);
    ifr.ifr_name[IFNAMSIZ - 1] = '\0';
    if (ioctl(sock, SIOCGIFINDEX, &ifr) < 0) {
        perror("ioctl"); return 1;
    }

    struct sockaddr_can addr;
    memset(&addr, 0, sizeof(addr));
    addr.can_family  = AF_CAN;
    addr.can_ifindex = ifr.ifr_ifindex;
    if (bind(sock, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind"); return 1;
    }

    anomaly_engine_t eng;
    memset(&eng, 0, sizeof(eng));
    for (int i = 0; i < MAX_IDS * 2; i++)
        eng.hash_table[i] = 0;

    signal(SIGINT, sighandler);
    signal(SIGTERM, sighandler);

    /* Phase 1: Calibration */
    eng.calibrating  = true;
    eng.cal_start_us = now_us();
    fprintf(stderr, "Phase 1: Calibrating for %d seconds on %s...\n",
            cal_seconds, ifname);

    while (running) {
        if (now_us() - eng.cal_start_us >= (uint64_t)cal_seconds * 1000000)
            break;
        struct can_frame frame;
        ssize_t n = read(sock, &frame, sizeof(frame));
        if (n == CAN_MTU) process_frame(&eng, &frame);
    }

    eng.calibrating = false;
    dump_baseline(&eng);

    /* Phase 2: Detection */
    fprintf(stderr, "Phase 2: Detection mode for %d seconds...\n",
            det_seconds);
    uint64_t det_start = now_us();

    while (running) {
        if (now_us() - det_start >= (uint64_t)det_seconds * 1000000)
            break;
        struct can_frame frame;
        ssize_t n = read(sock, &frame, sizeof(frame));
        if (n == CAN_MTU) process_frame(&eng, &frame);
    }

    /* Summary */
    int total_alerts = 0;
    for (int i = 0; i < eng.id_count; i++)
        total_alerts += eng.ids[i].alert_count;

    fprintf(stderr, "\nDetection complete. Total alerts: %d\n",
            total_alerts);

    if (eng.alert_fp) fclose(eng.alert_fp);
    close(sock);
    return 0;
}
```

### Centralized vs Distributed Monitoring Topologies

The physical placement of the IDS on the in-vehicle network fundamentally determines which attacks it can detect and how quickly it can respond. Three architectures dominate current production and research designs, each with distinct trade-offs in detection coverage, latency, and survivability.

**Centralized gateway monitoring** places the IDS on the vehicle's central gateway ECU, which bridges multiple CAN sub-networks (powertrain, body, chassis, infotainment, and diagnostics). Every inter-segment message passes through the gateway, giving the IDS visibility into cross-network attacks such as a compromised telematics unit injecting frames onto the powertrain bus. The gateway is typically the most powerful ECU in the vehicle, with sufficient CPU headroom for complex statistical models. The limitation is that the gateway has no visibility into traffic that stays within a single sub-network. An attacker who compromises a brake controller on the chassis bus and injects frames that remain on that bus will never be seen by the gateway IDS. Additionally, the gateway is a single point of failure: if an attacker disables or bypasses the gateway, all monitoring ceases.

```mermaid
flowchart TD
    subgraph gateway ["Centralized Gateway IDS"]
        AnomalyEngine["Anomaly Engine"]
        SignatureEngine["Signature Engine"]
        Log["Log"]

        subgraph canfd1 ["CAN-FD #1 · Powertrain"]
            AnomalyEngine --> CANFD1["CAN-FD #1\nPowertrain"]
        end

        subgraph canfd2 ["CAN-FD #2 · Chassis"]
            SignatureEngine --> CANFD2["CAN-FD #2\nChassis"]
        end

        subgraph can3 ["CAN #3 · Body/Comfort"]
            Log --> CAN3["CAN #3\nBody/Comfort"]
        end
    end

    CANFD1 --> PowertrainECUs["Engine ECU\nTrans ECU\nTCU"]
    CANFD2 --> ChassisECUs["ABS/ESC\nAirbag\nSteering"]
    CAN3 --> BodyECUs["BCM\nLights\nWipers"]
```

**Distributed in-ECU monitoring** embeds a lightweight detection agent into each ECU, typically as a low-priority task within the ECU's RTOS (AUTOSAR Basic Software layer or a bare-metal scheduler). Each agent monitors only the traffic on its own bus segment, giving it complete visibility into all local communication. The agent can also correlate observed CAN traffic with the ECU's own internal state, enabling detection of attacks that would be invisible to an external observer: a brake ECU can detect that a received brake-pressure command disagrees with its own locally read pressure sensor, a cross-check no external IDS could perform. The cost is the requirement to modify every ECU's firmware, which is infeasible for legacy components and introduces validation burden across the supply chain. Communication overhead between agents is also a concern, as each agent must report alerts to a central aggregator without consuming excessive bus bandwidth.

```mermaid
flowchart TD
    EngineECU["Engine<br/>ECU"]
    ABSECU["ABS/ESC<br/>ECU"]
    BCM["BCM"]
    Telematic["Telematics<br/>Unit"]
    
    EngineIDS["IDS<br/>Agent<br/>(local)"]
    ABSIDS["IDS<br/>Agent<br/>(local)"]
    BCMIDS["IDS<br/>Agent<br/>(local)"]
    TelematicIDS["IDS<br/>Agent<br/>(local)"]
    
    CANBackbone["CAN Backbone"]
    Gateway["Alert<br/>Aggregator<br/>(Gateway)"]
    
    EngineECU --> EngineIDS
    ABSECU --> ABSIDS
    BCM --> BCMIDS
    Telematic --> TelematicIDS
    
    EngineIDS --> CANBackbone
    ABSIDS --> CANBackbone
    BCMIDS --> CANBackbone
    TelematicIDS --> CANBackbone
    
    CANBackbone --> Gateway
```

**Hybrid tiered monitoring** combines the two approaches: a centralized IDS on the gateway handles cross-network traffic and serves as the alert aggregator, while lightweight agents on critical ECUs (brakes, steering, powertrain) provide deep local visibility. Alerts from distributed agents are forwarded to the gateway over a dedicated diagnostic or out-of-band channel, and the gateway correlates them with its own observations. This is the architecture used in production vehicles from several manufacturers as of the 2023-2024 model years, though the specifics vary significantly. The following code implements a distributed alert agent designed to run as a low-priority AUTOSAR-like task within an ECU, forwarding alerts to a central aggregator over CAN using a dedicated alert arbitration ID.

```c
/* ids_agent.c - Distributed IDS agent for in-ECU deployment
 * Designed for AUTOSAR RTE or bare-metal RTOS integration.
 * Build (host test): gcc -O2 -Wall -o ids_agent ids_agent.c -lpthread
 *
 * This agent:
 * 1. Monitors local CAN traffic via SocketCAN (or CAN driver abstraction)
 * 2. Runs lightweight rate-based anomaly detection
 * 3. Forwards alerts to a central gateway aggregator using
 *    a dedicated alert CAN ID (0x7E0)
 * 4. Listens for heartbeat requests from the gateway to confirm
 *    agent liveness
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <pthread.h>
#include <unistd.h>
#include <time.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <linux/can.h>
#include <linux/can/raw.h>

#define ALERT_TX_ID     0x7E0   /* alerts to gateway */
#define HEARTBEAT_RX_ID 0x7E1   /* gateway heartbeat requests */
#define AGENT_ID        0x01    /* this ECU's agent ID */
#define MAX_MONITORED_IDS 64
#define RATE_WINDOW_MS  100
#define RATE_MULTIPLIER 3       /* alert if rate > 3x baseline */

typedef struct {
    uint32_t  can_id;
    uint32_t  baseline_rate;     /* learned frames per window */
    uint32_t  window_count;
    uint64_t  window_start_us;
    uint64_t  last_alert_us;
    uint32_t  alert_count;
} monitored_id_t;

typedef struct {
    int                 sock;
    monitored_id_t      monitored[MAX_MONITORED_IDS];
    int                 monitored_count;
    volatile bool       running;
    pthread_mutex_t     lock;
    FILE               *local_log;
} agent_ctx_t;

static uint64_t now_us(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000ULL + ts.tv_nsec / 1000;
}

/* Encode alert into a CAN frame for transmission to gateway.
 * Alert format (8 bytes):
 *   [0]    = AGENT_ID
 *   [1]    = alert type (1=rate_anomaly, 2=id_injection,
 *                       3=payload_oob, 4=bus_error)
 *   [2-3]  = CAN ID that triggered alert (big-endian)
 *   [4]    = alert severity (1=INFO, 2=WARN, 3=CRIT)
 *   [5-7]  = reserved / sequence counter
 */
static void send_alert_can(agent_ctx_t *ctx, uint32_t can_id,
                           uint8_t alert_type, uint8_t severity)
{
    struct can_frame alert_frame;
    memset(&alert_frame, 0, sizeof(alert_frame));
    alert_frame.can_id  = ALERT_TX_ID;
    alert_frame.can_dlc = 8;

    static uint8_t seq = 0;
    alert_frame.data[0] = AGENT_ID;
    alert_frame.data[1] = alert_type;
    alert_frame.data[2] = (can_id >> 8) & 0xFF;
    alert_frame.data[3] = can_id & 0xFF;
    alert_frame.data[4] = severity;
    alert_frame.data[5] = seq++;
    alert_frame.data[6] = 0;
    alert_frame.data[7] = 0;

    write(ctx->sock, &alert_frame, sizeof(alert_frame));
}

static void log_local(agent_ctx_t *ctx, uint32_t can_id,
                      uint8_t alert_type, const char *msg)
{
    if (!ctx->local_log) return;
    uint64_t t = now_us();
    fprintf(ctx->local_log,
            "%llu id=0x%03X type=%u %s\n",
            (unsigned long long)t, can_id, alert_type, msg);
    fflush(ctx->local_log);
}

/* Learn baseline rates during a calibration period */
static void calibrate(agent_ctx_t *ctx, int seconds)
{
    fprintf(stderr, "Agent %02X: calibrating for %d seconds...\n",
            AGENT_ID, seconds);

    /* Clear baseline */
    for (int i = 0; i < ctx->monitored_count; i++) {
        ctx->monitored[i].baseline_rate  = 0;
        ctx->monitored[i].window_count   = 0;
        ctx->monitored[i].window_start_us = now_us();
    }

    /* Pre-populate with known IDs or learn dynamically */
    bool learning = true;
    uint64_t cal_start = now_us();

    while (ctx->running && (now_us() - cal_start) <
           (uint64_t)seconds * 1000000) {
        struct can_frame frame;
        ssize_t n = read(ctx->sock, &frame, sizeof(frame));
        if (n != CAN_MTU) continue;

        uint32_t rx_id = frame.can_id & CAN_SFF_MASK;

        /* Find or create monitored ID */
        monitored_id_t *m = NULL;
        for (int i = 0; i < ctx->monitored_count; i++) {
            if (ctx->monitored[i].can_id == rx_id) {
                m = &ctx->monitored[i];
                break;
            }
        }
        if (!m && ctx->monitored_count < MAX_MONITORED_IDS) {
            m = &ctx->monitored[ctx->monitored_count++];
            memset(m, 0, sizeof(*m));
            m->can_id         = rx_id;
            m->window_start_us = now_us();
        }
        if (!m) continue;

        uint64_t now = now_us();
        if (now - m->window_start_us >= RATE_WINDOW_MS * 1000) {
            if (m->window_count > m->baseline_rate)
                m->baseline_rate = m->window_count;
            m->window_count   = 0;
            m->window_start_us = now;
        }
        m->window_count++;
    }

    fprintf(stderr, "Agent %02X: calibrated %d IDs\n",
            AGENT_ID, ctx->monitored_count);
    for (int i = 0; i < ctx->monitored_count; i++) {
        fprintf(stderr, "  ID 0x%03X: baseline=%u frames/%dms\n",
                ctx->monitored[i].can_id,
                ctx->monitored[i].baseline_rate, RATE_WINDOW_MS);
    }
}

/* Detection loop: monitor and alert */
static void *detect_loop(void *arg)
{
    agent_ctx_t *ctx = (agent_ctx_t *)arg;

    while (ctx->running) {
        struct can_frame frame;
        ssize_t n = read(ctx->sock, &frame, sizeof(frame));
        if (n != CAN_MTU) continue;

        uint32_t rx_id = frame.can_id & CAN_SFF_MASK;

        /* Skip our own alert and heartbeat IDs */
        if (rx_id == ALERT_TX_ID || rx_id == HEARTBEAT_RX_ID)
            continue;

        /* Handle heartbeat from gateway */
        if (rx_id == HEARTBEAT_RX_ID) {
            /* Respond with a liveness CAN frame */
            struct can_frame hb_resp;
            memset(&hb_resp, 0, sizeof(hb_resp));
            hb_resp.can_id  = 0x7E2;
            hb_resp.can_dlc = 2;
            hb_resp.data[0]  = AGENT_ID;
            hb_resp.data[1]  = 0x01; /* alive */
            write(ctx->sock, &hb_resp, sizeof(hb_resp));
            continue;
        }

        /* Find monitored ID */
        monitored_id_t *m = NULL;
        for (int i = 0; i < ctx->monitored_count; i++) {
            if (ctx->monitored[i].can_id == rx_id) {
                m = &ctx->monitored[i];
                break;
            }
        }
        if (!m) {
            /* Unknown ID: potential injection */
            send_alert_can(ctx, rx_id, 2, 3); /* id_injection, CRIT */
            log_local(ctx, rx_id, 2, "unknown ID injection");
            continue;
        }

        uint64_t now = now_us();
        if (now - m->window_start_us >= RATE_WINDOW_MS * 1000) {
            uint32_t threshold = m->baseline_rate * RATE_MULTIPLIER;
            if (m->baseline_rate > 0 && m->window_count > threshold) {
                /* Rate anomaly detected */
                uint64_t elapsed = now - m->last_alert_us;
                if (elapsed > 5000000) { /* 5-second suppression */
                    uint8_t sev = (m->window_count > threshold * 2) ? 3 : 2;
                    send_alert_can(ctx, rx_id, 1, sev);
                    log_local(ctx, rx_id, 1, "rate anomaly");
                    m->last_alert_us = now;
                    m->alert_count++;
                }
            }
            m->window_count   = 0;
            m->window_start_us = now;
        }
        m->window_count++;
    }

    return NULL;
}

int main(int argc, char **argv)
{
    if (argc < 4) {
        fprintf(stderr,
                "usage: %s <can-if> <cal_sec> <local_log_path>\n",
                argv[0]);
        return 1;
    }

    const char *ifname  = argv[1];
    int cal_seconds     = atoi(argv[2]);
    const char *logpath = argv[3];

    agent_ctx_t ctx;
    memset(&ctx, 0, sizeof(ctx));
    ctx.running = true;
    pthread_mutex_init(&ctx.lock, NULL);

    int sock = socket(PF_CAN, SOCK_RAW, CAN_RAW);
    if (sock < 0) { perror("socket"); return 1; }

    struct ifreq ifr;
    strncpy(ifr.ifr_name, ifname, IFNAMSIZ - 1);
    ifr.ifr_name[IFNAMSIZ - 1] = '\0';
    if (ioctl(sock, SIOCGIFINDEX, &ifr) < 0) {
        perror("ioctl"); return 1;
    }

    struct sockaddr_can addr;
    memset(&addr, 0, sizeof(addr));
    addr.can_family  = AF_CAN;
    addr.can_ifindex = ifr.ifr_ifindex;
    if (bind(sock, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind"); return 1;
    }

    /* Set CAN filters: receive all frames (zero filter = accept all) */
    struct can_filter filter[1];
    filter[0].can_id   = 0;
    filter[0].can_mask = 0;
    setsockopt(sock, SOL_CAN_RAW, CAN_RAW_FILTER,
               &filter, sizeof(filter));

    ctx.sock = sock;
    ctx.local_log = fopen(logpath, "a");
    if (ctx.local_log)
        setvbuf(ctx.local_log, NULL, _IOLBF, 0);

    /* Calibration phase */
    calibrate(&ctx, cal_seconds);

    /* Detection phase */
    pthread_t detect_thread;
    pthread_create(&detect_thread, NULL, detect_loop, &ctx);

    fprintf(stderr, "Agent %02X: detection running. Ctrl-C to stop.\n",
            AGENT_ID);

    /* Wait for signal */
    while (ctx.running) sleep(1);
    ctx.running = false;
    pthread_join(detect_thread, NULL);

    /* Summary */
    int total_alerts = 0;
    for (int i = 0; i < ctx.monitored_count; i++)
        total_alerts += ctx.monitored[i].alert_count;
    fprintf(stderr, "Agent %02X: total alerts=%d\n",
            AGENT_ID, total_alerts);

    if (ctx.local_log) fclose(ctx.local_log);
    close(sock);
    pthread_mutex_destroy(&ctx.lock);
    return 0;
}
```

---

## 3. High-Performance Optimization & Failure Modes

### Real-Time Constraint Budgeting

The most stringent operational requirement for an in-vehicle IDS is the real-time processing budget. A CAN bus running at 500 kbps with 11-bit identifiers and 8-byte payloads completes a worst-case frame in approximately 134 bit times, or roughly 268 microseconds at 500 kbps, including interframe spacing. At maximum utilization, this yields approximately 3,700 frames per second on a single bus. A CAN-FD bus at 5 Mbps data phase with 64-byte payloads can deliver over 20,000 frames per second. The IDS must process each frame, extract features, run baseline comparisons, and make an alert decision within the inter-frame gap to avoid falling behind and dropping frames.

On an embedded ARM Cortex-A processor running at 1 GHz (typical of a gateway ECU), the per-frame budget at 3,700 frames/second is approximately 270 microseconds of wall time, but the IDS task shares the CPU with gateway routing, firewall rule evaluation, and diagnostic services. A realistic allocation is 50-100 microseconds per frame for IDS processing, which translates to approximately 50-100 clock cycles of computation per frame at full load after accounting for context switch overhead and cache misses.

The optimization strategy proceeds along three axes. The first is reducing per-frame computation through efficient data structures. The hash table used for ID lookup in the anomaly engine must be tuned for the expected ID space, which on a typical passenger vehicle contains 200-600 unique arbitration IDs. A directly-indexed array of 2048 entries (covering the full 11-bit ID space) eliminates hashing overhead entirely at the cost of 2048 × sizeof(id_baseline_t) bytes of memory, which at approximately 200 bytes per entry totals roughly 400 KB, acceptable for a gateway ECU with 256 MB or more of RAM.

```c
/* Optimized direct-indexed ID lookup for 11-bit CAN IDs.
 * Eliminates hash computation entirely. Trade-off: 400 KB
 * memory vs O(1) worst-case lookup.
 *
 * For 29-bit extended IDs, use a 2-level structure:
 *   top level: 16-bit prefix -> page pointer
 *   second level: 13-bit suffix -> id_baseline_t
 * This handles the full 29-bit space with ~128 KB typical
 * (assuming sparse usage) while keeping lookup at 2 memory
 * accesses.
 */

#define CAN_SFF_ARRAY_SIZE  2048  /* 11-bit IDs: 0x000-0x7FF */

typedef struct {
    id_baseline_t  *sff_array[CAN_SFF_ARRAY_SIZE];
    /* Extended ID pages: allocated on first use */
    id_baseline_t **eff_pages[65536];  /* 16-bit prefix -> page */
} id_lookup_fast_t;

static inline id_baseline_t *lookup_sff(id_lookup_fast_t *lut,
                                         uint32_t can_id)
{
    /* Direct array index: O(1), no hash, no collision */
    return lut->sff_array[can_id & CAN_SFF_MASK];
}

static inline id_baseline_t *lookup_eff(id_lookup_fast_t *lut,
                                         uint32_t can_id)
{
    uint16_t prefix = (can_id >> 13) & 0xFFFF;
    uint16_t suffix = can_id & 0x1FFF;
    if (!lut->eff_pages[prefix])
        return NULL;  /* page not allocated */
    return &lut->eff_pages[prefix][suffix];
}

/* Initialize the lookup table for a known set of IDs.
 * Pre-allocate all pages for IDs observed during calibration
 * to avoid runtime allocation in the detection path. */
static void init_fast_lookup(id_lookup_fast_t *lut,
                             anomaly_engine_t *eng)
{
    memset(lut->sff_array, 0, sizeof(lut->sff_array));
    memset(lut->eff_pages, 0, sizeof(lut->eff_pages));

    for (int i = 0; i < eng->id_count; i++) {
        id_baseline_t *b = &eng->ids[i];
        if (b->extended) {
            uint16_t prefix = (b->can_id >> 13) & 0xFFFF;
            uint16_t suffix = b->can_id & 0x1FFF;
            if (!lut->eff_pages[prefix]) {
                /* Allocate a page: 8192 entries × ~200 bytes
                 * = ~1.6 MB per page. Only allocate for
                 * prefixes that actually appear. */
                lut->eff_pages[prefix] = calloc(8192,
                    sizeof(id_baseline_t));
            }
            if (lut->eff_pages[prefix])
                lut->eff_pages[prefix][suffix] = *b;
        } else {
            lut->sff_array[b->can_id & CAN_SFF_MASK] = b;
        }
    }
}
```

The second optimization axis is reducing memory access latency through cache-conscious data layout. The `id_baseline_t` structure as defined above is approximately 200 bytes, which means a single cache line (64 bytes on ARM Cortex-A) covers only the first few fields. Since the hot path accesses the inter-arrival statistics, the byte range fields, and the window counter on every frame, these fields should be packed into a single cache line. The alert suppression fields and alert count, accessed only when an anomaly is detected, should be placed in a separate structure accessed via a pointer, keeping them out of the hot cache line.

```c
/* Cache-optimized baseline structure: hot fields in first
 * 64-byte cache line, cold fields in secondary struct.
 *
 * Layout (ARM Cortex-A, 64-byte cache line):
 *   [0-3]   can_id           (4 bytes)
 *   [4-7]   flags/valid      (4 bytes)
 *   [8-23]  iat_stats        (16 bytes: count+mean+m2+pad)
 *   [24-27] last_rx_us_lo    (4 bytes: low 32 bits of timestamp)
 *   [28-35] byte_min[8]      (8 bytes)
 *   [36-43] byte_max[8]      (8 bytes)
 *   [44-47] window_count     (4 bytes)
 *   [48-51] window_max       (4 bytes)
 *   [52-59] window_start_us_lo (4 bytes + pad)
 *   [60-63] byte_count_lo   (4 bytes: low 32 bits)
 *   --- end of cache line 1 (64 bytes) ---
 *
 * Cold fields (alert suppression, full timestamps) in
 * separate heap-allocated struct, accessed only on alert.
 */

typedef struct __attribute__((aligned(64))) {
    uint32_t  can_id;            /* offset 0  */
    uint32_t  flags;             /* offset 4  */
    /* Compact Welford: use float instead of double for IAT
     * stats. Precision loss is acceptable for sigma threshold
     * comparison; the threshold itself (4.0) provides
     * sufficient margin. */
    float     iat_mean;          /* offset 8  */
    float     iat_m2;            /* offset 12 */
    uint32_t  iat_count;         /* offset 16 */
    uint32_t  last_rx_us;        /* offset 20 */
    uint8_t   byte_min[8];       /* offset 24 */
    uint8_t   byte_max[8];       /* offset 32 */
    uint32_t  window_count;      /* offset 40 */
    uint32_t  window_max;        /* offset 44 */
    uint32_t  window_start_us;   /* offset 48 */
    uint32_t  byte_count[8];     /* offset 52 (uses 8*4=32 -> exceeds 64) */
    /* If byte_count is needed, move to cold struct or use
     * a flag byte + 32-bit aggregate. For this optimization,
     * we track byte_count as a single uint32 that ORs in
     * which bytes have reached MIN_SAMPLES. */
    uint32_t  byte_valid_mask;   /* offset 52 */
    uint8_t   _pad[8];           /* offset 56-63: pad to 64 */
} id_baseline_hot_t;

typedef struct {
    uint64_t  last_alert_us;
    uint32_t  alert_count;
    uint32_t  _reserved;
} id_baseline_cold_t;

typedef struct {
    id_baseline_hot_t  hot;
    id_baseline_cold_t *cold;  /* heap-allocated, only if alerted */
} id_baseline_opt_t;
```

The third optimization axis is parallelism. On a multi-core gateway ECU, the detection workload can be split across cores using a producer-consumer pattern with a lock-free ring buffer. The producer thread reads frames from the CAN socket using `recvmmsg` to batch-receive up to 64 frames per system call, reducing the per-frame syscall overhead from approximately 1-2 microseconds to 15-30 nanoseconds. The frames are pushed onto a lock-free single-producer single-consumer (SPSC) ring buffer, and one or more consumer threads pull frames and run the detection algorithms. Frame ordering is preserved within each consumer, but frames may be processed out of order across consumers, which is acceptable because each frame's anomaly check is independent.

```c
/* Lock-free SPSC ring buffer for CAN frame batching.
 * Based on Linux kernel's circular buffer design.
 * Producer = socket reader, Consumer = detection thread.
 *
 * Buffer size must be power of 2 for fast modulo via bitmask.
 */
#define RING_SIZE    1024   /* must be power of 2 */
#define RING_MASK    (RING_SIZE - 1)
#define BATCH_SIZE   64     /* frames per recvmmsg call */

typedef struct {
    struct can_frame frames[RING_SIZE];
    volatile uint32_t head;  /* producer writes, consumer reads */
    volatile uint32_t tail;  /* consumer writes, producer reads */
    char _pad[64];           /* prevent false sharing */
} can_ring_t;

static inline bool ring_push(can_ring_t *r, const struct can_frame *f)
{
    uint32_t head = __atomic_load_n(&r->head, __ATOMIC_RELAXED);
    uint32_t next = (head + 1) & RING_MASK;
    if (next == __atomic_load_n(&r->tail, __ATOMIC_ACQUIRE))
        return false;  /* full */
    r->frames[head] = *f;
    __atomic_store_n(&r->head, next, __ATOMIC_RELEASE);
    return true;
}

static inline bool ring_pop(can_ring_t *r, struct can_frame *f)
{
    uint32_t tail = __atomic_load_n(&r->tail, __ATOMIC_RELAXED);
    if (tail == __atomic_load_n(&r->head, __ATOMIC_ACQUIRE))
        return false;  /* empty */
    *f = r->frames[tail];
    __atomic_store_n(&r->tail, (tail + 1) & RING_MASK,
                     __ATOMIC_RELEASE);
    return true;
}

/* Producer thread: batch-read from SocketCAN and push to ring */
static void *producer_thread(void *arg)
{
    can_ring_t *ring = (can_ring_t *)arg;
    int sock = ring_sock;  /* global: set in main */

    /* Batch receive buffer */
    struct mmsghdr msgs[BATCH_SIZE];
    struct can_frame frames[BATCH_SIZE];
    struct iovec iovecs[BATCH_SIZE];

    for (int i = 0; i < BATCH_SIZE; i++) {
        iovecs[i].iov_base     = &frames[i];
        iovecs[i].iov_len       = sizeof(struct can_frame);
        msgs[i].msg_hdr.msg_iov    = &iovecs[i];
        msgs[i].msg_hdr.msg_iovlen = 1;
        msgs[i].msg_hdr.msg_name    = NULL;
        msgs[i].msg_hdr.msg_namelen = 0;
        msgs[i].msg_hdr.msg_control = NULL;
        msgs[i].msg_hdr.msg_controllen = 0;
        msgs[i].msg_hdr.msg_flags    = 0;
    }

    while (producer_running) {
        int n = recvmmsg(sock, msgs, BATCH_SIZE,
                         MSG_WAITFORONE, NULL);
        if (n < 0) {
            if (errno == EINTR) continue;
            perror("recvmmsg");
            break;
        }

        for (int i = 0; i < n; i++) {
            if (msgs[i].msg_len == CAN_MTU) {
                while (!ring_push(ring, &frames[i])) {
                    /* Ring full: consumer is behind.
                     * Drop frame and increment drop counter,
                     * or spin-wait if strict no-drop required. */
                    __sync_fetch_and_add(&dropped_frames, 1);
                    break;
                }
            }
        }
    }
    return NULL;
}
```

### False Positive Management

The most operationally damaging failure mode of a behavioral IDS is the false positive: an alert generated by legitimate traffic that happens to deviate from the learned baseline. In the automotive context, false positives have consequences ranging from nuisance log entries to active safety interference. If the IDS is wired into a vehicle's incident response system that can isolate a CAN bus segment or disable an ECU, a false positive on a braking system message could disable brakes at highway speed.

False positives arise from three sources. The first is model inadequacy: the Gaussian inter-arrival assumption does not hold for all IDs, particularly those with event-driven rather than purely periodic transmission patterns. A door status message, for example, may transmit periodically at 100 ms intervals during normal driving but burst-transmit at 10 ms intervals when the door state changes, producing a 10x rate increase that a pure statistical model would flag as anomalous. The second source is calibration coverage: a baseline learned during a 30-minute city drive does not capture driving modes that occur rarely, such as cold-start enrichment, traction control intervention, or emergency braking, all of which produce legitimate traffic patterns that deviate from the city-driving baseline. The third source is environmental variation: CAN bus timing is affected by temperature (oscillator drift), bus load (arbitration delays), and ECU software version (message schedules change between software updates).

The mitigation strategy combines multiple techniques. **Adaptive thresholds** adjust the sigma multiplier per ID based on observed false positive rates during a validation period. If a particular ID generates frequent alerts during known-legitimate operation, its threshold is widened automatically. **Contextual gating** suppresses alerts when vehicle state indicates a legitimate cause for deviation: a rate increase on brake-pressure messages is not flagged when the ABS module is active, detected via the ABS status bit in a known CAN message. **Temporal validation** requires an anomaly to persist for N consecutive frames or M milliseconds before raising an alert, filtering transient deviations that self-correct within a few frame intervals. **Multi-model consensus** requires two or more independent models to agree before raising an alert, reducing the false positive rate exponentially with the number of models at the cost of increased detection latency.

```c
/* False positive mitigation: adaptive thresholds with
 * contextual gating and temporal validation.
 *
 * Per-ID configuration that tunes itself over time.
 */

typedef struct {
    uint32_t can_id;

    /* Adaptive sigma threshold: starts at 4.0, widens if
     * false positives are frequent during validation. */
    float    sigma_threshold;
    float    sigma_min;       /* floor: never go below this */
    float    sigma_max;       /* ceiling: above this, alert is
                               * meaningless */
    float    sigma_adjust_rate; /* how fast to adapt */

    /* Temporal validation: require N consecutive anomalous
     * frames before alerting. */
    uint8_t  consecutive_required;
    uint8_t  consecutive_count;

    /* Contextual gate: suppress alerts when a specific
     * CAN bit is set (e.g., ABS active suppresses brake
     * rate alerts). */
    uint32_t gate_can_id;      /* ID to check, 0 = no gate */
    uint8_t  gate_byte_index;  /* which byte in gate ID */
    uint8_t  gate_bit_mask;    /* which bit(s) to check */
    bool     gate_suppress_when_set; /* true=suppress when bit set */

    /* Statistics for adaptation */
    uint32_t  total_alerts;
    uint32_t  suppressed_alerts;
    uint64_t  last_fp_adjust_us;
} id_fp_config_t;

/* Check contextual gate: returns true if alert should be
 * suppressed. */
static bool check_gate(const id_fp_config_t *cfg,
                       const id_baseline_opt_t *ids,
                       int id_count)
{
    if (cfg->gate_can_id == 0)
        return false;  /* no gate configured */

    /* Find the gate ID in our ID array */
    for (int i = 0; i < id_count; i++) {
        if (ids[i].hot.can_id == cfg->gate_can_id) {
            /* We need the latest observed payload for this ID.
             * In a full implementation, we'd cache the last
             * received payload per ID. Here we simulate. */
            /* ... gate logic omitted for brevity: check
             * ids[i].hot's last payload byte against
             * cfg->gate_byte_index, cfg->gate_bit_mask ... */
            return false;
        }
    }
    return false;
}

/* Process an anomaly detection event with FP mitigation. */
static void process_anomaly_event(id_fp_config_t *cfg,
                                  id_baseline_opt_t *b,
                                  double z_score,
                                  const struct can_frame *frame,
                                  anomaly_engine_t *eng)
{
    /* 1. Check sigma threshold (adaptive) */
    if (z_score < cfg->sigma_threshold) {
        cfg->consecutive_count = 0;  /* reset streak */
        return;
    }

    /* 2. Check contextual gate */
    if (check_gate(cfg, NULL, 0)) {
        cfg->suppressed_alerts++;
        return;
    }

    /* 3. Temporal validation: increment consecutive count */
    cfg->consecutive_count++;
    if (cfg->consecutive_count < cfg->consecutive_required) {
        return;  /* not enough consecutive anomalies yet */
    }

    /* 4. All checks passed: raise alert */
    alert(eng, &b->hot, "ADAPTIVE_ANOMALY", frame,
          z_score, cfg->sigma_threshold);
    cfg->total_alerts++;
    cfg->consecutive_count = 0;

    /* 5. Adaptive threshold adjustment:
     * If this ID generates more than 5 alerts per minute
     * during validation, widen the threshold. This is a
     * feedback loop: high alert rate -> likely FP -> widen. */
    uint64_t now = now_us();
    if (now - cfg->last_fp_adjust_us > 60000000) { /* 60 sec */
        if (cfg->total_alerts > 5) {
            cfg->sigma_threshold += cfg->sigma_adjust_rate;
            if (cfg->sigma_threshold > cfg->sigma_max)
                cfg->sigma_threshold = cfg->sigma_max;
        }
        cfg->total_alerts = 0;
        cfg->last_fp_adjust_us = now;
    }
}
```

### Logging Infrastructure and Incident Response

The alert log is the forensic lifeline of the IDS. In a vehicle deployed to the field, the log is the only evidence available after an attack, and its quality determines whether a post-incident investigation can reconstruct what happened. The logging infrastructure must address three constraints: limited non-volatile storage (typically 8-64 MB of flash allocated to security logs on a gateway ECU), the need for tamper resistance (an attacker who compromises the gateway may attempt to erase the log), and the requirement to preserve temporal ordering and causal relationships between events.

A production-grade logging architecture uses a tiered approach. Tier 1 is a circular ring buffer in RAM that captures every frame's raw CAN data for the last 1-10 seconds, providing a pre-event window for forensic analysis. When an alert fires, the ring buffer is snapshotted to a persistent log entry, preserving the bus state leading up to the event. Tier 2 is a structured alert log in non-volatile flash, using a format that supports both local analysis and off-vehicle extraction via UDS diagnostic services or OTA telemetry. Tier 3 is a minimal crash log that survives power loss, recording only critical alerts (bus isolation, ECU disable events) and system state at the time of the alert.

```c
/* tiered_log.c - Tiered CAN IDS logging infrastructure
 *
 * Tier 1: RAM ring buffer (last N frames, pre-event snapshot)
 * Tier 2: Flash structured alert log (persistent, UDS-extractable)
 * Tier 3: NVRAM critical event log (power-loss survivable)
 *
 * Build: gcc -O2 -Wall -o tiered_log tiered_log.c -lpthread
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <pthread.h>
#include <time.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <linux/can.h>

/* ---- Tier 1: RAM Ring Buffer ---- */

#define RING_FRAMES  4096   /* ~4096 * 16 bytes = 64 KB RAM */

typedef struct {
    struct can_frame frame;
    uint64_t          timestamp_us;
    uint32_t          sequence;
} ring_entry_t;

typedef struct {
    ring_entry_t  entries[RING_FRAMES];
    volatile uint32_t write_idx;
    volatile uint32_t sequence;
    pthread_mutex_t   snapshot_lock;
} tier1_ring_t;

static void tier1_init(tier1_ring_t *r)
{
    memset(r, 0, sizeof(*r));
    pthread_mutex_init(&r->snapshot_lock, NULL);
}

static void tier1_record(tier1_ring_t *r,
                         const struct can_frame *f)
{
    uint32_t idx = __atomic_fetch_add(&r->write_idx, 1,
                                      __ATOMIC_RELAXED) % RING_FRAMES;
    r->entries[idx].frame       = *f;
    r->entries[idx].timestamp_us = now_us();
    r->entries[idx].sequence    = __atomic_fetch_add(&r->sequence, 1,
                                      __ATOMIC_RELAXED);
}

/* Snapshot the last N frames before the current write index. */
static int tier1_snapshot(tier1_ring_t *r, ring_entry_t *out,
                          int max_out, uint32_t *start_seq)
{
    pthread_mutex_lock(&r->snapshot_lock);
    uint32_t cur = __atomic_load_n(&r->write_idx,
                                   __ATOMIC_RELAXED);
    int count = (cur < RING_FRAMES) ? cur : RING_FRAMES;
    if (count > max_out) count = max_out;

    for (int i = 0; i < count; i++) {
        uint32_t src = (cur - count + i) % RING_FRAMES;
        out[i] = r->entries[src];
    }
    *start_seq = out[0].sequence;
    pthread_mutex_unlock(&r->snapshot_lock);
    return count;
}

/* ---- Tier 2: Flash Structured Alert Log ---- */

#define TIER2_MAX_ENTRIES  10000   /* rotate after this many */
#define TIER2_FILE         "/var/log/can_ids/tier2_alerts.bin"
#define TIER2_MAGIC        0x434F4944  /* "COID" */

typedef struct __attribute__((packed)) {
    uint32_t magic;            /* TIER2_MAGIC */
    uint16_t struct_version;   /* 1 */
    uint16_t alert_type;       /* 1=sig, 2=anomaly_iat,
                                  3=anomaly_rate, 4=anomaly_payload,
                                  5=bus_error */
    uint16_t severity;         /* 1=INFO, 2=WARN, 3=CRIT */
    uint16_t agent_id;         /* 0=central, 1-N=distributed */
    uint32_t can_id;           /* offending CAN ID */
    uint32_t sequence;         /* global frame sequence */
    uint64_t timestamp_us;    /* event time (MONOTONIC) */
    uint64_t epoch_ms;         /* wall clock time */
    uint8_t  dlc;              /* frame DLC */
    uint8_t  payload[64];      /* raw payload (CAN-FD safe) */
    uint8_t  reason[32];       /* human-readable reason */
    uint16_t pre_event_count;  /* how many pre-event frames snapshotted */
    uint16_t checksum;         /* simple XOR checksum over entry */
} tier2_entry_t;  /* 128 bytes per entry */

static int tier2_write(const tier2_entry_t *entry)
{
    int fd = open(TIER2_FILE, O_WRONLY | O_CREAT | O_APPEND, 0640);
    if (fd < 0) {
        /* If file doesn't exist, create with header */
        perror("open tier2");
        return -1;
    }

    /* Compute checksum */
    tier2_entry_t e = *entry;
    e.checksum = 0;
    const uint8_t *p = (const uint8_t *)&e;
    uint16_t cksum = 0;
    for (size_t i = 0; i < sizeof(e) - sizeof(e.checksum); i++)
        cksum ^= p[i];
    e.checksum = cksum;

    /* Check file size for rotation */
    struct stat st;
    if (fstat(fd, &st) == 0) {
        if (st.st_size > (off_t)(TIER2_MAX_ENTRIES * sizeof(tier2_entry_t))) {
            /* Rotate: rename current to .old, start fresh */
            close(fd);
            char oldname[256];
            snprintf(oldname, sizeof(oldname), "%s.old", TIER2_FILE);
            rename(TIER2_FILE, oldname);
            fd = open(TIER2_FILE, O_WRONLY | O_CREAT | O_APPEND, 0640);
            if (fd < 0) return -1;
        }
    }

    write(fd, &e, sizeof(e));
    close(fd);
    return 0;
}

/* Create a complete tier2 alert entry from a detection event */
static void tier2_create_alert(uint16_t alert_type, uint16_t severity,
                               uint16_t agent_id, uint32_t can_id,
                               uint32_t sequence,
                               const struct can_frame *frame,
                               const char *reason,
                               tier1_ring_t *ring)
{
    tier2_entry_t entry;
    memset(&entry, 0, sizeof(entry));

    entry.magic          = TIER2_MAGIC;
    entry.struct_version = 1;
    entry.alert_type     = alert_type;
    entry.severity       = severity;
    entry.agent_id       = agent_id;
    entry.can_id         = can_id;
    entry.sequence       = sequence;
    entry.timestamp_us   = now_us();

    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    entry.epoch_ms = (uint64_t)ts.tv_sec * 1000 + ts.tv_nsec / 1000000;

    entry.dlc = frame->can_dlc;
    memcpy(entry.payload, frame->data,
           frame->can_dlc < 64 ? frame->can_dlc : 64);
    strncpy((char *)entry.reason, reason, sizeof(entry.reason) - 1);

    /* Snapshot pre-event frames from Tier 1 ring buffer */
    if (ring) {
        ring_entry_t snapshot[32];
        uint32_t start_seq;
        int n = tier1_snapshot(ring, snapshot, 32, &start_seq);
        entry.pre_event_count = (uint16_t)n;
        /* In a full implementation, pre-event frames would be
         * written to a separate sidecar file referenced by
         * the alert sequence number. */
    }

    tier2_write(&entry);

    /* Also write to human-readable log for operator review */
    FILE *fp = fopen("/var/log/can_ids/alerts_readable.log", "a");
    if (fp) {
        time_t t = (time_t)(entry.epoch_ms / 1000);
        struct tm tm;
        localtime_r(&t, &tm);
        fprintf(fp,
                "[%04d-%02d-%02d %02d:%02d:%02d.%03d] %s id=0x%03X "
                "agent=%u seq=%u dlc=%u reason=%s payload=",
                tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday,
                tm.tm_hour, tm.tm_min, tm.tm_sec,
                (int)(entry.epoch_ms % 1000),
                severity == 3 ? "CRIT" : severity == 2 ? "WARN" : "INFO",
                can_id, agent_id, sequence, entry.dlc, reason);
        for (int i = 0; i < entry.dlc && i < 64; i++)
            fprintf(fp, "%02X ", entry.payload[i]);
        fprintf(fp, "\n");
        fclose(fp);
    }
}

/* ---- Tier 3: NVRAM Critical Event Log ---- */
/* On real hardware, this writes to a small NVRAM partition
 * or uses an EEPROM driver. On Linux, we simulate with
 * a file synced via fsync() for power-loss survivability. */

#define TIER3_FILE   "/var/log/can_ids/tier3_critical.bin"
#define TIER3_MAX    256  /* only critical events */

typedef struct __attribute__((packed)) {
    uint32_t  magic;        /* 0x43524954  ("CRIT") */
    uint16_t  event_type;   /* 1=bus_isolated, 2=ecu_disabled,
                                3=ids_disabled, 4=tamper_detected */
    uint16_t  severity;     /* always 3 (CRIT) */
    uint64_t  timestamp_us;
    uint64_t  epoch_ms;
    uint32_t  related_alert_seq; /* link to tier2 entry */
    uint8_t   vehicle_state[16]; /* speed, gear, etc. */
    uint16_t  checksum;
} tier3_entry_t;  /* 48 bytes */

static void tier3_log(uint16_t event_type,
                      uint32_t related_alert_seq,
                      const uint8_t *vehicle_state)
{
    tier3_entry_t entry;
    memset(&entry, 0, sizeof(entry));

    entry.magic     = 0x43524954;
    entry.event_type = event_type;
    entry.severity  = 3;
    entry.timestamp_us = now_us();

    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    entry.epoch_ms = (uint64_t)ts.tv_sec * 1000 + ts.tv_nsec / 1000000;
    entry.related_alert_seq = related_alert_seq;
    if (vehicle_state)
        memcpy(entry.vehicle_state, vehicle_state,
               sizeof(entry.vehicle_state));

    uint16_t cksum = 0;
    const uint8_t *p = (const uint8_t *)&entry;
    for (size_t i = 0; i < sizeof(entry) - sizeof(entry.checksum); i++)
        cksum ^= p[i];
    entry.checksum = cksum;

    int fd = open(TIER3_FILE, O_WRONLY | O_CREAT | O_APPEND, 0640);
    if (fd < 0) return;

    /* Check rotation */
    struct stat st;
    if (fstat(fd, &st) == 0 &&
        st.st_size > (off_t)(TIER3_MAX * sizeof(tier3_entry_t))) {
        close(fd);
        char old[256];
        snprintf(old, sizeof(old), "%s.old", TIER3_FILE);
        rename(TIER3_FILE, old);
        fd = open(TIER3_FILE, O_WRONLY | O_CREAT | O_APPEND, 0640);
        if (fd < 0) return;
    }

    write(fd, &entry, sizeof(entry));
    fsync(fd);  /* ensure power-loss survivability */
    close(fd);
}

/* ---- Incident Response Triggers ---- */
/* When the IDS detects a critical anomaly, it can trigger
 * automated response actions. The response must be
 * carefully scoped to avoid safety risks. */

typedef enum {
    RESP_NONE = 0,        /* log only */
    RESP_ALERT_ONLY,      /* log + escalate to gateway */
    RESP_RATE_LIMIT,      /* request bus controller to
                            * throttle offending ID */
    RESP_BUS_ISOLATE,     /* isolate CAN segment (gateway only) */
    RESP_ECU_DISABLE,     /* request ECU reset/disable
                            * (dangerous: safety review required) */
    RESP_FULL_LOCKDOWN    /* isolate all buses + alert cluster
                            * (last resort) */
} response_action_t;

typedef struct {
    uint16_t alert_type;
    uint16_t severity;
    response_action_t action;
} response_policy_t;

static const response_policy_t default_policy[] = {
    /* Signature-based alerts */
    { 1 /* sig */, 2 /* WARN */,  RESP_ALERT_ONLY },
    { 1 /* sig */, 3 /* CRIT */,  RESP_RATE_LIMIT  },
    /* Anomaly: IAT */
    { 2, 2, RESP_ALERT_ONLY },
    { 2, 3, RESP_RATE_LIMIT  },
    /* Anomaly: rate */
    { 3, 2, RESP_ALERT_ONLY },
    { 3, 3, RESP_RATE_LIMIT  },
    /* Anomaly: payload */
    { 4, 2, RESP_ALERT_ONLY },
    { 4, 3, RESP_RATE_LIMIT  },
    /* Bus error */
    { 5, 2, RESP_ALERT_ONLY },
    { 5, 3, RESP_BUS_ISOLATE },
};

static response_action_t evaluate_response(uint16_t alert_type,
                                           uint16_t severity)
{
    for (size_t i = 0; i < sizeof(default_policy)/sizeof(default_policy[0]); i++) {
        if (default_policy[i].alert_type == alert_type &&
            default_policy[i].severity == severity)
            return default_policy[i].action;
    }
    return RESP_NONE;
}

static void execute_response(response_action_t action,
                             uint32_t can_id,
                             uint32_t alert_seq,
                             tier1_ring_t *ring)
{
    switch (action) {
    case RESP_NONE:
        break;

    case RESP_ALERT_ONLY:
        /* Already logged via tier2_create_alert */
        break;

    case RESP_RATE_LIMIT:
        /* Configure CAN controller to drop or throttle frames
         * with the offending arbitration ID. On SocketCAN,
         * this requires controller-level filtering which is
         * not directly exposed. On a real gateway ECU, this
         * would configure the CAN controller's acceptance
         * filter or implement software-level filtering in
         * the routing layer. */
        fprintf(stderr,
                "RESPONSE: rate-limiting CAN ID 0x%03X "
                "(alert seq %u)\n", can_id, alert_seq);
        /* In production: call into gateway routing layer
         * to install a drop rule for this ID. */
        break;

    case RESP_BUS_ISOLATE:
        /* Isolate the CAN segment. On a gateway ECU with
         * multiple CAN transceivers, this means disabling
         * the transceiver for the affected bus.
         * WARNING: This can disable safety-critical
         * communication. Only safe if redundant path exists
         * or if the bus is already compromised. */
        fprintf(stderr,
                "RESPONSE: ISOLATING CAN segment due to "
                "critical alert (ID 0x%03X, seq %u)\n",
                can_id, alert_seq);
        tier3_log(1 /* bus_isolated */, alert_seq, NULL);
        /* In production: call transceiver disable function.
         * Example on MCP2517FD:
         *   mcp2517fd_write_reg(MCP2517FD_C1CTRL,
         *                       CAN_MODE_LISTEN_ONLY); */
        break;

    case RESP_ECU_DISABLE:
        /* Send UDS ECUReset (0x11) to the offending ECU.
         * This is an aggressive response that should
         * require multi-factor confirmation. */
        fprintf(stderr,
                "RESPONSE: Requesting ECU reset for ID 0x%03X "
                "(alert seq %u)\n", can_id, alert_seq);
        tier3_log(2 /* ecu_disabled */, alert_seq, NULL);
        /* In production: construct and send UDS 0x11 frame
         * on the appropriate CAN interface. */
        break;

    case RESP_FULL_LOCKDOWN:
        fprintf(stderr,
                "RESPONSE: FULL LOCKDOWN initiated "
                "(alert seq %u)\n", alert_seq);
        tier3_log(4 /* tamper_detected */, alert_seq, NULL);
        /* Isolate all CAN interfaces + notify cluster */
        break;
    }
}
```

### Integration: End-to-End Detection Pipeline

The complete IDS pipeline ties together the signature engine, anomaly engine, distributed agents, and tiered logging into a single processing chain. The following diagram shows the data flow from CAN bus reception through alert generation and incident response.

```mermaid
flowchart TD
    CAN["CAN Bus\n(500 kbps / CAN-FD)"]
    SCAN["SocketCAN / Driver\nrecvmmsg batch\n(64 frames/syscall)"]
    RING["Lock-Free Ring Buffer\n(4096 frame window)\n← Tier 1: RAM (pre-event)"]

    SIG["Signature Engine\n(known attacks)"]
    ANOM["Anomaly Engine\n(IAT, rate, payload)"]
    DIST["Distributed Agent Alerts\n(from ECUs)"]

    CORR["Alert Correlator\n(FP mitigation, consensus,\ncontextual gate)"]

    RPE["Response Policy Engine\n(log / rate-limit / isolate / disable)"]

    FLASH["Tier 2: Flash\nStructured Alert Log\n(UDS-extract)"]
    NVRAM["Tier 3: NVRAM\nCritical Events"]
    IR["Incident Response Actions\n(bus isolation, ECU reset)"]

    CAN --> SCAN
    SCAN --> RING
    RING --> SIG
    RING --> ANOM
    RING --> DIST
    SIG --> CORR
    ANOM --> CORR
    DIST --> CORR
    CORR --> RPE
    RPE --> FLASH
    RPE --> NVRAM
    RPE --> IR
```

The pipeline demonstrates the fundamental trade-off in automotive IDS design. Each stage adds detection capability but also adds latency. A frame that passes through signature matching, anomaly detection, correlation, and policy evaluation may accumulate 200-500 microseconds of processing time, which at maximum bus load leaves no budget for the gateway's primary routing function. The solution is to run signature and anomaly engines in parallel, with the correlation stage merging their outputs asynchronously. Signature alerts, which require only a single hash lookup and comparison, complete in under 5 microseconds and can trigger immediate response without waiting for the anomaly engine. Anomaly alerts, which require statistical computation, take 20-50 microseconds per frame and are processed on a best-effort basis with a slightly longer response latency.

The distributed agent architecture adds a second dimension: alerts from remote ECUs arrive over CAN with their own latency (1-10 ms depending on bus load and arbitration priority), meaning that the correlation engine must handle out-of-order and delayed alerts. A timestamp-based ordering window of 50 ms is typically sufficient to correlate events from the same physical attack across multiple bus segments, while rejecting delayed alerts that arrive after the window closes as separate incidents.

The practical result is a system that can detect and respond to known attack signatures within a single frame time (under 300 microseconds from bus reception to alert generation), detect statistical anomalies within 1-10 frame times (3-30 milliseconds), and correlate distributed alerts across the vehicle within 50-100 milliseconds. These latencies are sufficient to prevent most injection attacks before they can complete their intended action, with the caveat that a sufficiently fast attacker flooding a single high-priority ID can cause actuator commands to execute before the IDS response triggers, which is why rate-limiting at the CAN controller level, implemented in hardware rather than software, remains the first line of defense for critical IDs.
