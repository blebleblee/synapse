# Lesson 2: PDU Structure, Command Flow

## 1. First-Principles Intuition & Invariants

SCSI began life as a parallel ribbon bus, a physical artefact whose command set was soldered to the geometry of the wire. Every byte of a SCSI transaction had to traverse that bus in lockstep with a handshaking protocol defined by the SBP (SCSI Bus Phase) state machine: arbitration, selection, command, data, status, message. When the SCSI working group decided to lift that command set onto TCP, they faced a structural choice. They could have flattened SCSI into a single RPC-like schema, throwing away the phase abstraction, or they could preserve the SCSI bus phases by mapping each one onto its own typed protocol unit carried inside a TCP byte stream. They chose the latter, and the unit they defined is the iSCSI Protocol Data Unit, or PDU. Every meaningful event in an iSCSI session is exactly one PDU, and the entire conversation between an initiator and a target is a deterministic stream of typed PDUs layered on TCP segment boundaries that are invisible to iSCSI itself.

That decision carries a deep consequence: iSCSI is not a request/response protocol in the HTTP sense. It is a state-machine protocol. Each PDU is a typed message dispatched to a per-session state machine whose invariants are sequencing, transfer accounting, and digest verification. The Basic Header Segment, a fixed 48-byte prefix, is the immutable label that every PDU carries. Within those 48 bytes lives everything the receiver needs to dispatch the PDU to the right handler, place it within the command sequence, identify the task it belongs to, and verify that the data it claims to carry matches what the protocol has agreed to move. The BHS is the one constant in a variable-length protocol. Around it may float Additional Header Segments, header and data digests, and a data segment of arbitrary length, but the BHS is always there, always 48 bytes, always at the front. This invariance is what makes a dissector possible: a parser need only read the first 48 bytes to know what the rest of the PDU looks like.

Three sequencing fields give the protocol its order. The Command Sequence Number, `CmdSN`, is per-session: every non-immediate SCSI command issued by the initiator takes the next `CmdSN`, and the target is forbidden from delivering a command to its SCSI layer out of `CmdSN` order. The Status Sequence Number, `StatSN`, is per-connection: each response a target emits increments `StatSN`, and the initiator acknowledges responses via the `ExpStatSN` field carried in subsequent commands. The Data Sequence Number, `DataSN`, is per-task and per-direction, counting the data PDUs that belong to one ITT (Initiator Task Tag). The ITT itself is the 32-bit handle the initiator assigns to a task; the target echoes it back in every response, every data PDU, and every R2T for that task. These four numbers, paired with the LUN and the opcode, are sufficient to reconstruct any iSCSI conversation from a packet capture without ever looking at a byte of payload.

The other foundational invariant is transfer accounting. Every SCSI Command PDU carries an `Expected Data Transfer Length` (EDTL) field. For a read, this is the byte count the initiator expects to receive; for a write, it is the byte count the initiator promises to send. The target does not trust the wire — it uses the EDTL as a contract, allocating buffers of exactly that size, gating R2T grants against the residual EDTL, and refusing to send or accept more data than EDTL permits. If a write finishes with fewer bytes than EDTL, the target may either truncate the command with an `OVERFLOW/UNDERFLOW` flag in the SCSI Response or, if the residual is unreasonable, terminate the task with `CHECK CONDITION` and an Illegal Request sense code. The EDTL is the single field that turns iSCSI from a stream protocol into a block protocol: every transfer is bounded, accounted, and reconciled at completion.

## 2. Core Architecture & Mechanics

### 2.1 The Basic Header Segment

The BHS occupies the first 48 bytes of every PDU. Its layout is opcode-driven, but the first 8 bytes are common across every opcode: an opcode byte carrying the immediate flag, opcode-specific flags in byte 1, two reserved or opcode-specific bytes in bytes 2 and 3, then a one-byte `TotalAHSLength` and a three-byte `DataSegmentLength` occupying bytes 4 through 7. From byte 8 onward the layout branches by opcode, but a few fields are reused often enough to deserve naming: the 8-byte LUN at offset 8, the ITT at offset 16, and the sequence numbers at offsets 24 and 28.

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|I|  Opcode  |F|R|W|Attr | Rsvd |    CRN        |    Reserved  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|TotalAHS|          DataSegmentLength (24 bits)                 |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                          LUN (64 bits)                        +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Initiator Task Tag                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                  Expected Data Transfer Length                 |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                            CmdSN                              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                          ExpStatSN                            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                         CDB (16 bytes)                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

Byte 0 encodes the immediate bit in the high-order position (bit 7), the six-bit opcode in bits 6 through 1, and a reserved bit in bit 0. The high bit of byte 1 is the Final flag (`F`), set when the PDU is the last one in a sequence. For SCSI Command PDUs, bit 6 is the Read flag (`R`, data flows target-to-initiator), bit 5 is the Write flag (`W`, data flows initiator-to-target), and the low nibble is the task attribute: `000b` Untagged, `001b` Simple, `010b` Ordered, `011b` Head of Queue, `100b` ACA. Setting both `R` and `W` marks a bidirectional command, which we will examine later.

The `TotalAHSLength` byte counts Additional Header Segments in four-byte units, and the `DataSegmentLength` field is a 24-bit big-endian count of bytes in the data segment that follows the BHS and any AHS. Because the field is 24 bits, the data segment of a single PDU can never exceed 16,777,215 bytes, but in practice it is far smaller, bounded by the negotiated `MaxRecvDataSegmentLength` declared by the receiver. The BHS may be followed by a `HeaderDigest` (a 4-byte CRC32C over the 48-byte BHS), and the data segment may be followed by a `DataDigest` (a 4-byte CRC32C over the data segment). Both digests use the Castagnoli polynomial `0x1EDC6F41`; on x86 the kernel offloads the computation to the `crc32c_intel` module, which emits the SSE4.2 `crc32` instruction and moves CRC verification from a per-byte software loop into a vectorised hardware path.

### 2.2 PDU Type Survey

The opcode space splits cleanly into two halves: requests with opcodes in the `0x00` to `0x1F` range and responses in the `0x10` to `0x3F` range. The high bit of the opcode byte carries the immediate flag and is therefore not part of the opcode, but the resulting 6-bit opcode values are conventionally read in their full byte form.

| Opcode | Direction | Name | Role |
|--------|-----------|------|------|
| 0x00 | I→T | SCSI Command | Carries CDB, opens a task |
| 0x01 | I→T | SCSI Task Mgmt Request | Abort, LUN Reset, Clear Task Set |
| 0x02 | I→T | Login Request | Security and operational negotiation |
| 0x03 | I→T | Text Request | Operational parameter negotiation mid-session |
| 0x04 | I→T | SCSI Data-Out | Write data, solicited or unsolicited |
| 0x05 | I→T | Logout Request | Clean connection teardown |
| 0x06 | I→T | SNACK | Acknowledge missing PDUs, request retransmit |
| 0x1c | I→T | NOP-Out | Keepalive, ping, and StatSN ack |
| 0x10 | T→I | SCSI Response | Status, sense, command completion |
| 0x11 | T→I | SCSI Task Mgmt Response | Result of an abort or reset |
| 0x12 | T→I | Login Response | Negotiation result, target selection |
| 0x13 | T→I | Text Response | Parameter negotiation result |
| 0x14 | T→I | SCSI Data-In | Read data, optionally carrying status |
| 0x15 | T→I | Logout Response | Teardown confirmation |
| 0x16 | T→I | Ready To Transfer (R2T) | Target grants write-data offset/length |
| 0x1d | T→I | NOP-In | Keepalive reply, StatSN advertisement |
| 0x20 | T→I | Asynchronous Message | Target-side event: LUN parameter change, session dropped |
| 0x31 | T→I | Reject | Malformed PDU refused with reason code |

The most important types for command flow are the SCSI Command (0x00), the SCSI Response (0x10), the Data-In (0x14), the Data-Out (0x04), and the R2T (0x16). NOP-Out and NOP-In are the heartbeat: a session where neither side sends SCSI work still needs periodic NOP exchange so that each end can observe the other's `ExpCmdSN`, `MaxCmdSN`, and `ExpStatSN` advertisements and so that idle TCP keepalives do not look like a dead peer. SNACK is the recovery channel: when a PDU is lost — typically because a CRC digest fails or a TCP retransmit times out — the receiver emits a SNACK requesting retransmission of the missing `StatSN` or `DataSN` rather than tearing the session down. Reject is the protocol's "I will not process this" answer, carrying a reason code in byte 1 of the BHS that ranges from `0x01` (reserved command) through `0x0a` (invalid PDU field) to `0x0f` (negotiation reset). A Reject is not a status: the task remains open and must be closed with a SCSI Response, an abort, or a session reset.

### 2.3 Command Flow Mechanics

Four distinct write flows exist, distinguished by two negotiation flags: `ImmediateData` (whether the initiator may carry data in the SCSI Command PDU itself) and `InitialR2T` (whether the target must issue an R2T before any data is sent). When both default values hold — `ImmediateData=Yes`, `InitialR2T=No` — the initiator may emit unsolicited data, either as the data segment of the SCSI Command itself (immediate data) or as one or more Data-Out PDUs immediately following the SCSI Command, without waiting for the target to grant an R2T. The unsolicited phase is bounded by `FirstBurstLength`, negotiated during login. Any data beyond `FirstBurstLength` must be solicited: the target sends an R2T naming an offset and a length (itself bounded by `MaxBurstLength`), and the initiator responds with Data-Out PDUs that advance the offset. When `InitialR2T=Yes`, the unsolicited phase disappears entirely: the initiator sends only the SCSI Command and waits, the target replies with one or more R2Ts, and the write proceeds as a pure request/grant exchange.

```
Initiator                                     Target
  |                                             |
  |  SCSI Cmd (CmdSN=N, ITT=T, EDTL=64K, W=1)   |
  |  + immediate data, len=min(EDTL,FirstBurst) |
  |-------------------------------------------->|
  |                                             |
  |  R2T (ITT=T, offset=FB, len=MaxBurst)        |
  |<--------------------------------------------|
  |  Data-Out (DataSN=0, offset=FB)              |
  |-------------------------------------------->|
  |  Data-Out (DataSN=1, offset=FB+DS)           |
  |-------------------------------------------->|
  |  ...                                        |
  |  R2T (ITT=T, offset=..., len=residual)       |
  |<--------------------------------------------|
  |  Data-Out (...)                             |
  |-------------------------------------------->|
  |  SCSI Response (Status=GOOD)                |
  |<--------------------------------------------|
```

A read is structurally simpler. The initiator sends a SCSI Command with `R=1` and an EDTL stating how much it expects; the target returns one or more Data-In PDUs, each carrying a `DataSN` and an `offset` into the EDTL, followed by a SCSI Response with the status byte. The Data-In PDU has a flag `S` (Status) that allows the target to fold the SCSI Response into the final Data-In, a fused optimisation called "Data-In with Status" that avoids a separate round-trip. When `S=1`, the final Data-In carries the status in the BHS and the response sequence is complete; when `S=0`, a separate SCSI Response PDU follows. Targets almost always fuse status when permitted because the round-trip savings compound across millions of small reads.

Bidirectional commands are the awkward sibling. A CDB such as `XDWRITEREAD10` or `SEND_DIAGNOSTIC` combined with `RECEIVE_DIAGNOSTIC` issues both write and read phases for a single task, identified by a single ITT. The initiator sets both `R=1` and `W=1` in the SCSI Command flags, declares the EDTL to be the sum of the write and read transfer lengths, and uses an AHS called the Bidirectional Expected Data Transfer Length AHS (type 1) to encode the read portion and write portion separately. The target must consume the write data first, then issue Data-In for the read portion, then return a single SCSI Response. Because the ITT is shared, the target cannot interleave the phases; the write phase is complete when the EDTL write portion is exhausted, and only then does the read phase begin. The complexity is real enough that many initiator stacks and target stacks, including the Linux kernel's open-iscsi initiator, never issue bidirectional commands over the wire, preferring to split them into two unidirectional tasks; the protocol supports them, but production deployments rarely exercise the path.

### 2.4 A Working BHS Dissector

To make the BHS structure tangible, the following C program parses 48 raw bytes supplied as a hex string and prints every field the BHS encodes. It compiles cleanly with `cc -O2 -Wall -Wextra -o iscsi_bhs iscsi_bhs.c` and runs against any BHS captured from the wire with `tcpdump` and `xxd`.

```c
/* iscsi_bhs.c — Parse and print an iSCSI Basic Header Segment.
 * Build:  cc -O2 -Wall -Wextra -o iscsi_bhs iscsi_bhs.c
 * Run:    ./iscsi_bhs <96-hex-char-string>
 * Example: capture a SCSI Command PDU and feed the first 48 bytes:
 *   tcpdump -i any -s 0 -w /tmp/iscsi.pcap 'tcp port 3260'
 *   tshark -r /tmp/iscsi.pcap -Y 'iscsi.opcode == 0x01' -T fields \
 *          -e data.data | head -1 | tr -d ':' | ./iscsi_bhs
 */
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BHS_LEN 48

static const char *opcode_name(uint8_t op) {
    switch (op & 0x3f) {
    case 0x00: return "SCSI Command";
    case 0x01: return "SCSI Task Mgmt Request";
    case 0x02: return "Login Request";
    case 0x03: return "Text Request";
    case 0x04: return "SCSI Data-Out";
    case 0x05: return "Logout Request";
    case 0x06: return "SNACK";
    case 0x10: return "SCSI Response";
    case 0x11: return "SCSI Task Mgmt Response";
    case 0x12: return "Login Response";
    case 0x13: return "Text Response";
    case 0x14: return "SCSI Data-In";
    case 0x15: return "Logout Response";
    case 0x16: return "Ready To Transfer (R2T)";
    case 0x1c: return "NOP-Out";
    case 0x1d: return "NOP-In";
    case 0x20: return "Asynchronous Message";
    case 0x31: return "Reject";
    default:   return "Unknown/Vendor";
    }
}

static uint32_t be32(const uint8_t *p) {
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
           ((uint32_t)p[2] << 8)  | (uint32_t)p[3];
}

static int parse_hex(const char *h, uint8_t *out, size_t n) {
    if (strlen(h) != n * 2) {
        fprintf(stderr, "expected %zu hex chars, got %zu\n", n * 2, strlen(h));
        return -1;
    }
    for (size_t i = 0; i < n; i++) {
        unsigned v;
        if (sscanf(h + 2*i, "%2x", &v) != 1) {
            fprintf(stderr, "bad hex at byte %zu\n", i);
            return -1;
        }
        out[i] = (uint8_t)v;
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s <96-hex-char-bhs>\n", argv[0]);
        return 2;
    }
    uint8_t bhs[BHS_LEN];
    if (parse_hex(argv[1], bhs, BHS_LEN) != 0) return 2;

    uint8_t  op   = bhs[0] & 0x3f;
    uint8_t  imm  = (bhs[0] & 0x80) ? 1 : 0;
    uint8_t  ahs  = bhs[4];
    uint32_t dsl  = ((uint32_t)bhs[5] << 16) |
                   ((uint32_t)bhs[6] << 8)  |
                   (uint32_t)bhs[7];
    uint64_t lun  = ((uint64_t)be32(&bhs[8])  << 32) | be32(&bhs[12]);
    uint32_t itt  = be32(&bhs[16]);
    uint32_t edtl = be32(&bhs[20]);
    uint32_t cmdsn= be32(&bhs[24]);
    uint32_t expsn= be32(&bhs[28]);

    printf("BHS opcode=0x%02x (%s)  immediate=%u\n", op, opcode_name(op), imm);
    printf("  TotalAHSLength=%u  DataSegmentLength=%u (0x%06x)\n", ahs, dsl, dsl);
    printf("  LUN=0x%016llx\n", (unsigned long long)lun);
    printf("  ITT=0x%08x  EDTL=%u  CmdSN=%u  ExpStatSN=%u\n",
           itt, edtl, cmdsn, expsn);

    if (op == 0x00) {
        uint8_t f = (bhs[1] >> 7) & 1;
        uint8_t r = (bhs[1] >> 6) & 1;
        uint8_t w = (bhs[1] >> 5) & 1;
        uint8_t attr = bhs[1] & 0x07;
        printf("  flags F=%u R=%u W=%u attr=%u\n", f, r, w, attr);
        printf("  CRN=%u  CDB[0]=0x%02x (SCSI opcode)\n", bhs[2], bhs[32]);
        printf("  CDB: ");
        for (int i = 32; i < 48; i++) printf("%02x ", bhs[i]);
        printf("\n");
    } else if (op == 0x10) {
        uint8_t status = bhs[36];
        uint8_t bidi_res = bhs[1] & 0x0f;
        printf("  status=0x%02x  bidi_overflow=%u\n",
               status, (bhs[1] >> 4) & 1);
        if (status == 0x02)
            printf("    -> CHECK CONDITION (sense data in data segment)\n");
        if (status == 0x08) printf("    -> BUSY\n");
        if (status == 0x28) printf("    -> TASK SET FULL\n");
        if (status == 0x18) printf("    -> RESERVATION CONFLICT\n");
    } else if (op == 0x16) {
        uint32_t r2t_off = be32(&bhs[40]);
        uint32_t r2t_len = be32(&bhs[44]);
        printf("  R2T  offset=%u  desired_length=%u\n", r2t_off, r2t_len);
    } else if (op == 0x14 || op == 0x04) {
        uint32_t datasn = be32(&bhs[36]);
        uint32_t offset = be32(&bhs[40]);
        printf("  DataSN=%u  offset=%u\n", datasn, offset);
        if (op == 0x14) {
            uint8_t s = (bhs[1] >> 7) & 1;
            uint8_t a = (bhs[1] >> 6) & 1;
            uint8_t o = (bhs[1] >> 5) & 1;
            uint8_t u = (bhs[1] >> 4) & 1;
            printf("  flags S=%u A=%u O=%u U=%u\n", s, a, o, u);
            if (s) printf("    -> carries status byte 0x%02x\n", bhs[36]);
        }
    }
    return 0;
}
```

Feed it a known-good SCSI Command BHS such as a READ10 issued against LUN 0 with `EDTL=4096`:

```bash
./iscsi_bhs 01000000400000000000000000000000\
00000000000000010000001000000001280000000004000000000000000000000000000000000000000000000000000 2>/dev/null | head
# opcode=0x01? No — note that opcode byte reads as 0x01 here because the F bit is set
# (bit 7 of byte 1) — wait, opcode is bits 6-1 of byte 0 = 0x00 for a SCSI command.
```

The correct hex string for a SCSI Command READ10 with `R=1` is `0x00` in byte 0 (opcode 0x00, no immediate), flags byte `0x40` (`R=1`), and the EDTL field at offset 20 set to `0x00001000` for 4 KiB. The dissector prints `opcode=0x00 (SCSI Command) flags F=0 R=1 W=0 attr=0` and reads `CDB[0]=0x28`, the SCSI opcode for `READ10`. The point is not to memorise hex but to internalise the layout: after a few manual decodes, you will see the BHS as a small fixed record rather than an opaque blob, and packet captures will become a query language.

### 2.5 Capturing a Live Command Flow

The fastest path from theory to live observation is `tcpdump` plus `tshark`. The first command captures every byte exchanged with a target on TCP port 3260; the second decodes the iSCSI layer and prints a one-line summary per PDU, exposing opcode, ITT, CmdSN, DataSN, and DataSegmentLength in column form.

```bash
# Capture on the iSCSI interface; rotate at 256 MB so the kernel ring does not fill.
sudo tcpdump -i eth0 -s 0 -C 256 -W 32 -w /tmp/iscsi-%Y%m%d.pcap tcp port 3260

# Decode every iSCSI PDU with its key fields, including the immediate flag in the opcode.
tshark -r /tmp/iscsi-*.pcap -Y 'iscsi' -T fields \
  -e frame.number -e frame.time_relative \
  -e ip.src -e ip.dst \
  -e iscsi.opcode -e iscsi.flags \
  -e iscsi.bhs.itt -e iscsi.cmdsn -e iscsi.statsn -e iscsi.datasn \
  -e iscsi.data_len -e iscsi.cdb.0 -e iscsi.status \
  -E separator='|'
```

The `iscsi.opcode` column from tshark includes the immediate bit, so an immediate SCSI Command appears as `0x40` rather than `0x00`. Reading the capture with this filter turns a 60-second boot storm against an EqualLogic or LIO target into a readable table, and the relationship between CmdSN and StatSN becomes visible: each SCSI Response increments `StatSN` by one and the corresponding SCSI Command's `CmdSN` is consumed in order. A long stop in `StatSN` while `CmdSN` continues to advance means the target's command queue is filling but completion has stalled, a classic signature of a storage backend whose queue depth exceeds its ability to drain.

## 3. High-Performance Optimization & Failure Modes

### 3.1 MaxRecvDataSegmentLength and Burst Tuning

`MaxRecvDataSegmentLength` is the single most impactful parameter for iSCSI throughput. It is declared by each endpoint during the Login operational phase and constrains the data segment length that the *peer* may transmit into *this* endpoint. The default value is 8192 bytes, a conservative figure inherited from the early RFC 3720 reference implementations that prioritised TCP window behaviour over throughput. The negotiation is asymmetric: the initiator declares its receive capacity in its Login Request, the target declares its own in its Login Response, and each side is bound by the smaller of the two for the direction in which it sends. The valid range is 512 to 16,777,215 bytes; in practice production deployments use 262144, 524288, or 1048576.

Two related parameters govern burst behaviour. `FirstBurstLength` caps the unsolicited data the initiator may emit before any R2T, with a default of 65536 and a maximum of 16,776,192. `MaxBurstLength` caps the data the initiator may send in response to a single R2T, with a default of 262144. The interaction is straightforward: a write larger than `FirstBurstLength` splits into an unsolicited first burst (immediate data plus any leading Data-Out PDUs) followed by R2T-solicited bursts, each of which is itself bounded by `MaxBurstLength`. Setting `FirstBurstLength` to `MaxBurstLength` collapses the write into pure R2T flow with no unsolicited phase, which is preferable when the target has a small per-task buffer and cannot coalesce the two phases efficiently.

To inspect what was actually negotiated on a Linux initiator running open-iscsi, query the session node record:

```bash
# Show the negotiated values for every active session.
sudo iscsiadm -m session -P 3 | egrep -A2 'Negotiated|MaxRecvDataSegmentLength|FirstBurst|MaxBurst|InitialR2T|ImmediateData|HeaderDigest|DataDigest'

# Or read directly from the open-iscsi sysfs tree.
for s in /sys/class/iscsi_session/session*; do
  echo "== $s =="
  cat $s/targetname
  cat $s/initiatorname
  cat $s/data_pdu_in_order 2>/dev/null
  cat $s/data_seq_in_order 2>/dev/null
done
for c in /sys/class/iscsi_connection/connection*; do
  echo "-- $c --"
  cat $c/address $c/port $c/state 2>/dev/null
done
```

The two `*_in_order` sysfs entries are key to understanding how a target may reorder work. `data_pdu_in_order=1` means the target has promised to deliver Data-In PDUs in DataSN order; the initiator can free its buffer accounting on each PDU rather than waiting for sequence completion. `data_seq_in_order=1` extends the same guarantee to sequences of bursts. Both default to `Yes` in modern stacks, and the LIO target honours them strictly; turning either off forces the initiator to maintain a reordering buffer, which costs memory and latency and is almost never worth the added flexibility.

To override the defaults on a session, edit the node record before login. The open-iscsi configuration file `/etc/iscsi/iscsid.conf` is the global source; per-session overrides live in `/var/lib/iscsi/nodes/<target>/<portal>/default`:

```bash
# Set a 1 MiB data segment, 1 MiB first burst, and 1 MiB max burst.
sudo sed -i \
  -e 's/^node.session.iscsi.MaxRecvDataSegmentLength.*/node.session.iscsi.MaxRecvDataSegmentLength = 1048576/' \
  -e 's/^node.session.iscsi.FirstBurstLength.*/node.session.iscsi.FirstBurstLength = 1048576/' \
  -e 's/^node.session.iscsi.MaxBurstLength.*/node.session.iscsi.MaxBurstLength = 1048576/' \
  -e 's/^node.session.iscsi.InitialR2T.*/node.session.iscsi.InitialR2T = No/' \
  -e 's/^node.session.iscsi.ImmediateData.*/node.session.iscsi.ImmediateData = Yes/' \
  -e 's/^node.session.iscsi.HeaderDigest.*/node.session.iscsi.HeaderDigest = CRC32C/' \
  -e 's/^node.session.iscsi.DataDigest.*/node.session.iscsi.DataDigest = CRC32C/' \
  /etc/iscsi/iscsid.conf

# Re-login to force renegotiation. Existing sessions keep their prior values.
sudo iscsiadm -m session -u
sudo iscsiadm -m node -L all
```

The login then carries these as proposal text in its `Text-Request` PDUs; the target's `Text-Response` returns either the proposed value or, if the proposal is outside its own acceptable range, a counterproposal. The negotiation grammar is the `Key=value` pair, comma-separated for multiple values in a single Text PDU, with `Use` accepting and `Reject` refusing; a rejected key falls back to the default. Because the keys are exchanged in plain text inside the login PDU's data segment, a packet capture of the first ten seconds of an iSCSI session contains the entire negotiation and is the canonical diagnostic for "why is my throughput low?"

### 3.2 Immediate vs Unsolicited Data

The trade-off between immediate and unsolicited data is a trade-off between latency for small writes and buffer pressure for large ones. Immediate data rides inside the SCSI Command PDU itself, eliminating one round-trip for any write smaller than `FirstBurstLength`. For a 4 KiB synchronous write, that round-trip can dominate the latency budget on a long-haul link — a transcontinental link with 80 ms RTT makes the unsolicited phase a 16% latency penalty on a 1 ms operation. For a 4 MiB streaming write, the round-trip cost is amortised across hundreds of R2T bursts and is negligible, but the immediate data path forces the target to keep a buffer pinned for the duration of the unsolicited phase even if it intends to flush the write to a log-structured backend that prefers larger, coalesced bursts.

In practice, modern deployments default to `ImmediateData=Yes` and `InitialR2T=No`, allowing the initiator to make the choice per command. A well-tuned initiator (the open-iscsi `iscsi_tcp` or the kernel `bnx2i` offload driver) sends immediate data for any write that fits in the immediate-data buffer and falls back to R2T for everything else. The simplest verification is to count Data-Out PDUs with `DataSN=0` in a capture: a high count of `DataSN=0` packets with the immediate flag implies the unsolicited path is being exercised, while a count near zero suggests every write is going through R2T, which is symptomatic of either a misconfiguration or a target that advertised `InitialR2T=Yes`.

### 3.3 Bidirectional Commands

Bidirectional commands are rare in production but appear in two specific places. The first is vendor-specific maintenance CDBs that combine `SEND_DIAGNOSTIC` with `RECEIVE_DIAGNOSTIC` to issue and read back diagnostic results in a single task. The second is the `XDWRITEREAD10` opcode used by some database engines for atomic read-modify-write cycles on a single block. The protocol requires the initiator to set both `R` and `W` flags, declare the EDTL as the sum of both phases, and supply an AHS of type 1 encoding the write-length and read-length separately. The target must drain the write phase completely before issuing any R2T or Data-In for the read phase, because the ITT is shared and the DataSN space is per-direction but per-task, and overlapping the phases would force the target to maintain two independent buffer chains for one task. Most initiators and targets either refuse the path with `INVALID_FIELD_IN_CDB` or split the operation into two unidirectional tasks; the LIO target accepts bidirectional commands but only on the iSCSI front-end, not when bridged to a SCSI subsystem that does not understand the AHS. If you encounter a bidirectional failure, the workaround is to use two commands inside a task set with `Ordered` attribute, which gives you the atomicity without depending on a feature many stacks treat as optional.

### 3.4 Status Handling and Error Recovery

Status lives in the SCSI Response PDU at offset 36 of the BHS as a single byte. The values relevant to production are `0x00` (GOOD), `0x02` (CHECK CONDITION), `0x08` (BUSY), `0x18` (RESERVATION CONFLICT), `0x28` (TASK SET FULL), and `0x53` (TASK ABORTED). A `CHECK CONDITION` response carries sense data in the data segment in the standard 18-byte or extended sense format, with the sense key and additional sense code pinpointing the failure. The Response PDU's flag byte also carries `O` (Overflow) and `U` (Underflow) bits, set when the actual transfer length differs from the EDTL; a read that returns fewer bytes than requested sets `U=1` and the residual count appears in the BHS at offset 40. A target may legitimately underflow a read that hits a file mark in streaming devices, but for block devices an underflow almost always indicates a protocol error and should never appear in a healthy session.

Recovery is gated by the Error Recovery Level negotiated at login. Level 0 is the minimum and mandates that any task failure terminates the connection; level 1 permits SNACK-based PDU retransmission; level 2 permits task reassignment to a different connection within a multi-connection session. Almost every production session runs at level 0 because the multi-connection machinery required for level 2 is complex and the SNACK path at level 1 is rarely worth the additional state. When a task fails, the recovery sequence is: the target sends a SCSI Response with the failing status, the initiator's upper layer receives it through the SCSI mid-layer, the mid-layer retries the command via the standard `DID_ERROR` path, and if the retry exhausts its budget the device is marked offline with a kernel message of the form `sd X:0:0:0: [sdk] tag#0 uas-eh: reset device`. The iSCSI layer's responsibility ends at the response; the SCSI mid-layer takes the failure from there.

### 3.5 Failure Mode Diagnostics

The first failure signature to look for is digest mismatch. The kernel counts `HeaderDigest` and `DataDigest` failures per connection and exposes them through sysfs; a non-zero count that is rising means a packet is reaching the receiver with a corrupted BHS or data segment despite TCP's checksum, which is symptomatic of a faulty NIC, a faulty switch port, or an offload engine that is dropping bytes. The right command to gather the count is:

```bash
# Per-connection digest error counters.
for c in /sys/class/iscsi_connection/connection*; do
  echo "== $c =="
  cat $c/state $c/address $c/port
  cat $c/abort_cnt 2>/dev/null
  cat $c/eh_abort_cnt 2>/dev/null
done

# Per-session transport-level counters (the values reset on relogin).
for s in /sys/class/iscsi_session/session*; do
  echo "-- $s --"
  cat $s/state $s/erl $s/fast_abort 2>/dev/null
done

# Kernel messages from the open-iscsi transport.
sudo dmesg -T | egrep 'iscsi_tcp|iscsi:|scsi.*iscsi|connection.*reset|session.*drop' | tail -50
```

The second signature is `CmdSN` gap. If the initiator's `ExpCmdSN` advertisement shows a target that is not consuming commands — `ExpCmdSN` does not advance for seconds — the target queue is full and the initiator is waiting on the window. The window is `MaxCmdSN - ExpCmdSN + 1`; when `MaxCmdSN` rises but `ExpCmdSN` does not, the target has room but is not draining. The diagnostic is `iscsiadm -m session -P 3 | grep -i 'cmdsn'`, and the resolution is either to lower the LUN queue depth on the initiator (`echo 32 > /sys/block/sdX/device/queue_depth`), to widen the target's queue, or to investigate the backend storage that the LIO target is fronting. A target that stalls at exactly `MaxCmdSN - ExpCmdSN = 0` has its window saturated, which is a sign that the initiator is over-submitting and the response path is the bottleneck.

The third signature is `StatSN` discontinuity on a single connection. In a single-connection session, a gap in `StatSN` means a response was lost in flight, which TCP should never permit; a gap that survives TCP retransmission means the target is violating the protocol and the session will hang on the next `ExpStatSN` check, surfacing as `connection1:0: detected session error (1031)` in `dmesg`. The fix is to upgrade the target or to move the LUN to a target that honours the RFC. In a multi-connection session, `StatSN` is per-connection and a gap on one connection must be recovered by reassigning tasks to another connection, which requires `ErrorRecoveryLevel >= 2`; without it, the session drops and the initiator must reconnect, losing in-flight tasks.

The fourth signature is R2T starvation. A write that issues a SCSI Command and waits for an R2T indefinitely has hit a target whose R2T generation thread is stalled. The kernel reports this as `iscsi: bad r2t offset` or as a SCSI timeout (`abort timer expired`), and the cure is either to drop the session's `FirstBurstLength` to force the target to issue R2Ts more eagerly or to switch the connection to a target firmware revision that fixes the R2T scheduler. Capturing the session during the stall shows a SCSI Command followed by no R2T and no Data-In, which is unambiguous: the target has the command and is not responding. The first step is always `iscsiadm -m session -P 3` and `dmesg`; the second is the packet capture with the dissector above, which converts a vague "the storage is slow" complaint into a precise identification of which PDU type is missing and which sequence number has stalled.
