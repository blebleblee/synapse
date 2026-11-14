# Lesson 3: Retrieval Protocols

## 1. First-Principles Intuition & Invariants

The act of retrieving electronic mail from a server is deceptively simple on its surface and deeply nuanced underneath. When a message arrives at a mail server's storage backend, it has already completed the delivery half of its journey, shepherded there by SMTP and its relay chain. The retrieval half — pulling that message down to a client, synchronizing read state across multiple devices, and correctly propagating mutations like deletions and flag changes back to the authoritative store — constitutes an entirely separate protocol domain with its own state machines, its own failure modes, and its own design philosophies.

Two protocols dominate this space: POP3, standardized in RFC 1939, and IMAP, standardized in RFC 3501 with subsequent extensions across dozens of additional RFCs. To understand why both exist, and why IMAP won the architectural argument while POP3 persists in specialized niches, you must start with the fundamental question every retrieval protocol must answer: *where does authoritative message state live?*

POP3 answers this question by punting it entirely to the client. Its design philosophy is download-and-delete. The server is a temporary holding area, a postal box you empty when you check it. Once messages are retrieved, they are removed from the server and the client owns them permanently. This model made perfect sense in the late 1980s and early 1990s, when users had a single workstation, disk storage on shared servers was expensive, and network connectivity was intermittent and slow. The simplicity is genuine: POP3's state machine has exactly three states — `AUTHORIZATION`, `TRANSACTION`, and `UPDATE` — and transitions between them in a strictly linear sequence. There is no concept of folders, no concept of persistent flags, and no concept of a session that could reconnect and find the mailbox in a known consistent state.

IMAP, originally conceived by Mark Crispin at Stanford in 1986 and refined through IMAP2, IMAP3, and finally IMAP4rev1, answers the same question the opposite way: authoritative state lives on the server, permanently, and clients are views into that state. This is the correct answer for a world where a user reads mail on a laptop, a phone, a tablet, and a webmail interface simultaneously. Every device sees the same mailbox, with the same folder hierarchy, the same read and unread counts, and the same flag states, because every device is talking to the same canonical store. The complexity this introduces is substantial. IMAP's state machine is non-linear, session-scoped, deeply stateful, and must handle concurrent modification by multiple clients against the same mailbox — problems that have no analogue in POP3 at all.

The core invariant that separates the two protocols is *message persistence*. In POP3, the server's responsibility for a message ends the moment it has been successfully transmitted to a client and the client has issued the `DELE` command. The protocol has no mechanism for the server to push state changes, no mechanism to reflect that another session deleted a message, and no mechanism to synchronize multiple concurrent clients. It was designed for a world that no longer exists. In IMAP, the server holds messages indefinitely, maintains their unique identifiers (UIDs) as monotonically increasing integers within a mailbox, and must correctly handle the case where a client reconnects after days of absence and needs to resynchronize only the delta of changes since its last session.

The UID invariant in IMAP deserves careful attention because it underpins every synchronization algorithm built on top of the protocol. Per RFC 3501, UIDs within a mailbox must be assigned in strictly ascending order, must never be reused, and must remain stable across sessions for as long as the message exists in the mailbox. The UID validity value, `UIDVALIDITY`, is a 32-bit unsigned integer that the server sets when a mailbox is created and must change if the UID namespace is ever reset — for example, after a catastrophic mailbox reconstruction from backup. Clients cache `UIDVALIDITY` alongside their local message stores and must discard their entire local cache and perform a full resync if `UIDVALIDITY` changes. This is not a theoretical edge case; it is a production failure mode you will encounter when operators perform mailbox migrations improperly. Any migration tool that does not preserve UIDs must rotate `UIDVALIDITY`, and clients that do not check `UIDVALIDITY` on reconnect will silently operate on a stale and incorrect local state.

A second invariant that systems architects must internalize is the distinction between sequence numbers and UIDs in IMAP. Sequence numbers are session-relative, 1-based ordinal positions of messages in the current mailbox view. They are mutable: if another session deletes message 3, messages 4 through N are renumbered. UIDs are permanent identifiers. Well-engineered clients use UIDs for all persistent references and treat sequence numbers only as a performance hint for bulk operations. The existence of two parallel addressing systems for the same set of messages is a source of real bugs in both client and server implementations, particularly around the semantics of `EXPUNGE` responses, which we will examine in depth in section three.

## 2. Core Architecture & Mechanics

### The POP3 State Machine

POP3's state machine is a strict sequential pipeline. Every TCP connection begins in the `AUTHORIZATION` state, where the server issues a greeting banner and the client must authenticate before accessing any messages. POP3 offers three authentication mechanisms: the plaintext `USER`/`PASS` command pair, the APOP challenge-response mechanism using MD5 (deprecated and cryptographically broken), and the `AUTH` extension command for SASL mechanisms including PLAIN, LOGIN, and CRAM-MD5. In any production deployment you must require TLS — either STARTTLS over port 110 or implicit TLS over port 995 — before allowing any credential exchange. The POP3S implicit TLS model on port 995 is preferable because it eliminates the STARTTLS downgrade attack surface entirely.

After successful authentication, the connection moves to the `TRANSACTION` state. Here the client can issue `STAT` to get the message count and total octets in the maildrop, `LIST` to retrieve per-message size information, `RETR n` to download a specific message, `DELE n` to mark it for deletion, and `UIDL n` to retrieve the server-assigned unique identifier for a message. The `UIDL` command, defined in RFC 1939 as an optional extension, is the key mechanism that allows POP3 clients to implement leave-on-server behavior: by recording which UIDs have been downloaded, a client can skip messages it has already retrieved without deleting them. This is POP3's only concession to multi-session behavior, and it is fragile — `UIDL` identifiers are server-defined strings with no standardized format and no guarantees of stability across server restarts.

The critical behavior of the `TRANSACTION` state is that *no changes are committed until the session terminates normally*. `DELE` commands mark messages for deletion but do not execute them. The `QUIT` command triggers the transition to the `UPDATE` state, where the server processes all pending deletions atomically and closes the connection. If the TCP connection drops before `QUIT` is issued, the server discards all pending `DELE` marks and the mailbox is left unmodified. This is a correct and intentional behavior: it prevents partial deletions from corrupting the maildrop when the network fails mid-session. The implication for operators is that a POP3 client that crashes after downloading all messages but before issuing `QUIT` will re-download the entire maildrop on its next connection. Mail delivery systems that feed into POP3 drops must be designed to handle this duplicate-delivery behavior idempotently at the application layer.

```
POP3 TCP Session on Port 995 (Implicit TLS):

  CLIENT                        SERVER
    |                             |
    |<--- TLS Handshake --------->|
    |<--- +OK Greeting -----------|
    |---- AUTH PLAIN <base64> --->|
    |<--- +OK Authenticated ------|  [AUTHORIZATION → TRANSACTION]
    |---- STAT ------------------>|
    |<--- +OK 3 8192 -------------|
    |---- UIDL ------------------>|
    |<--- +OK                     |
    |     1 abc123def             |
    |     2 xyz789ghi             |
    |     3 qwe456jkl             |
    |     . ----------------------|
    |---- RETR 2 --------------->|
    |<--- +OK 2730 octets --------|
    |<--- [RFC 5322 message] -----|
    |     . ----------------------|
    |---- DELE 2 --------------->|
    |<--- +OK Message deleted ----|
    |---- QUIT ------------------>|
    |<--- +OK Goodbye ------------|  [TRANSACTION → UPDATE → closed]
```

### The IMAP State Machine

IMAP's state machine is substantially more complex. A connection passes through `NOT AUTHENTICATED`, `AUTHENTICATED`, `SELECTED`, and `LOGOUT` states, but unlike POP3, the transitions are not strictly linear and the protocol supports interleaved, pipelined commands within a session. Each command is prefixed with a client-generated tag — an arbitrary alphanumeric string — that associates commands with their responses. This allows clients to pipeline multiple commands without waiting for each to complete, though some commands impose synchronization barriers.

The `SELECTED` state is where the meaningful work occurs. When a client issues `SELECT INBOX` or `SELECT "Sent"`, the server responds with a set of untagged responses that describe the current mailbox state: the number of messages (`* N EXISTS`), the number of recent messages (`* N RECENT`), the UID validity value, the UID next value (the UID that will be assigned to the next arriving message), and the flags the mailbox supports. The client must process all of these before issuing any further commands, because they establish the reference frame against which all subsequent sequence number and UID references are interpreted.

```
IMAP4rev1 Session Flow (Post-TLS):

  CLIENT                              SERVER
    |                                   |
    |<--- * OK [CAPABILITY ...] Ready---|
    |---- A001 LOGIN user pass -------->|
    |<--- A001 OK LOGIN completed ------|  [→ AUTHENTICATED]
    |---- A002 SELECT INBOX ----------->|
    |<--- * 247 EXISTS                  |
    |<--- * 3 RECENT                    |
    |<--- * OK [UNSEEN 244]             |
    |<--- * OK [UIDVALIDITY 1704067200] |
    |<--- * OK [UIDNEXT 2891]           |
    |<--- * FLAGS (\Answered \Flagged   |
    |             \Deleted \Seen \Draft)|
    |<--- A002 OK [READ-WRITE] SELECT   |  [→ SELECTED]
    |---- A003 UID FETCH 2888:2890      |
    |          (FLAGS BODY.PEEK[]  ---->|
    |<--- * 245 FETCH (UID 2888         |
    |           FLAGS (\Seen) ...)      |
    |<--- * 246 FETCH (UID 2889         |
    |           FLAGS () ...)           |
    |<--- * 247 FETCH (UID 2890         |
    |           FLAGS (\Recent) ...)    |
    |<--- A003 OK UID FETCH completed --|
    |---- A004 UID STORE 2889           |
    |          +FLAGS (\Seen) --------->|
    |<--- * 246 FETCH (FLAGS (\Seen)) --|
    |<--- A004 OK STORE completed ------|
    |---- A005 LOGOUT ----------------->|
    |<--- * BYE IMAP4rev1 server -------|
    |<--- A005 OK LOGOUT completed -----|
```

The `FETCH` command is IMAP's workhorse. It accepts either sequence number sets or, with the `UID FETCH` variant, UID sets, and returns structured message data items. The data item grammar is rich: `ENVELOPE` returns parsed header fields as a parenthesized list; `BODY.PEEK[HEADER.FIELDS (From Subject Date)]` returns specific header fields without setting the `\Seen` flag; `BODY[]` returns the complete RFC 5322 message and implicitly sets `\Seen`; `BODY[TEXT]` returns only the body without headers; and `RFC822.SIZE` returns the message's octet count. For high-performance clients that need to synchronize large mailboxes efficiently, `BODY.PEEK[HEADER]` combined with `FLAGS` and `UID` in a single `FETCH` command reduces round trips dramatically — the client fetches enough metadata to render a message list without downloading any message bodies.

### Flag Semantics and Persistent State

IMAP's flag system is the mechanism by which user actions — reading a message, flagging it for follow-up, drafting a reply — are persisted on the server and reflected to other clients. The protocol defines five system flags: `\Seen` indicates the message has been read; `\Answered` indicates the user has replied; `\Flagged` marks a message for special attention; `\Deleted` marks a message for expungement but does not remove it immediately; and `\Draft` indicates the message is a draft. The `\Recent` flag is special and server-managed: it marks messages that arrived since the last session that selected the mailbox, and no client can set or clear it directly.

The `\Deleted` flag deserves particular attention because its semantics differ from every other flag in a subtle but critical way. Setting `\Deleted` does not remove the message from the mailbox. The message remains accessible to `FETCH`, its sequence number does not change, and other sessions can still read it. Only the `EXPUNGE` command actually removes messages bearing `\Deleted` from the mailbox. When `EXPUNGE` executes, the server emits one `* N EXPUNGE` untagged response for each deleted message, where `N` is the sequence number of the message at the time of its removal. Because each expunge shifts the sequence numbers of all subsequent messages downward, the server emits multiple `EXPUNGE` responses in reverse sequence number order to preserve the mapping. A client that processes these responses out of order or fails to adjust its local sequence number map will corrupt its understanding of the mailbox state. This is one of the most common sources of bugs in IMAP client implementations, and it is why robust clients use UID-based addressing for everything and treat the sequence number renumbering from `EXPUNGE` as a housekeeping detail rather than a primary addressing mechanism.

User-defined keywords — called user flags in RFC 3501 — extend the flag namespace beyond the system flags. These are server-defined string labels like `$Forwarded`, `$Junk`, `$NotJunk`, or `Mailchimp` and are used heavily by mail clients and spam filtering systems. The server advertises which keywords are defined for a mailbox in the `FLAGS` response during `SELECT`. Adding a new keyword flag creates it permanently in the mailbox's flag set. The number of supported keywords is server-dependent, and operators running Dovecot or Cyrus must be aware of per-mailbox keyword limits (typically 26 for Dovecot in the default `mbox` format, expandable in `Maildir++` and `dbox` storage).

### Mailbox Synchronization Models: QRESYNC and Conditional STORE

Naive IMAP synchronization is expensive. A client that reconnects after being offline must issue `SELECT`, read the `EXISTS` count, then issue a full `UID SEARCH ALL` or `UID FETCH 1:* FLAGS` to discover what has changed. For a mailbox with 50,000 messages, `UID FETCH 1:* FLAGS` returns 50,000 `FETCH` responses. The bandwidth and latency cost of this operation is unacceptable on mobile connections.

RFC 7162 defines `QRESYNC` (Quick Resynchronization) to solve this problem. `QRESYNC` requires that the server support `CONDSTORE` (RFC 7162's predecessor mechanism) which introduces the concept of a `MODSEQ` — a 64-bit modification sequence number that the server increments monotonically with every flag change or message deletion. Every `FETCH` response can include the `MODSEQ` value at the time of the message's last modification. A client records the highest `MODSEQ` it has seen after each session. On reconnect, it passes this `MODSEQ` value to the server via the `QRESYNC` parameter of the `SELECT` command, and the server responds with only the changes — new messages, expunged UIDs, and flag changes — that occurred since that `MODSEQ`. For a mailbox where three messages arrived and two flags changed since the last sync, `QRESYNC` delivers five responses regardless of total mailbox size.

The `CONDSTORE` extension also defines `UID STORE` with `UNCHANGEDSINCE` to implement optimistic concurrency control at the flag level. If two clients simultaneously try to clear `\Flagged` on the same message, the second one to execute will fail with a `MODIFIED` response code rather than silently overwriting the first client's change. This turns flag mutation into a compare-and-swap operation and is the correct foundation for any multi-client mail application that needs to avoid lost updates.

### The IDLE Push Mechanism

Standard IMAP is a pull protocol. A client must poll the server — typically with a `NOOP` command or by reissuing `SELECT` — to discover new messages. For near-real-time push notification without long polling, RFC 2177 defines the `IDLE` command.

When a client issues `IDLE`, it enters a passive listening state where the server retains the connection but the client sends no further commands until it issues `DONE`. While in `IDLE`, the server pushes unsolicited untagged responses whenever the mailbox state changes: `* N EXISTS` when a new message arrives, `* N EXPUNGE` when a message is removed, and `* N FETCH (FLAGS (...))` when flags change. The client can terminate `IDLE` at any time by sending the literal string `DONE\r\n`, after which the server completes the `IDLE` command and the session returns to normal `SELECTED` state.

The IDLE mechanism has an important operational constraint: connections idle long enough will be killed by NAT gateways, load balancers, or firewall conntrack tables whose TCP timeout thresholds are typically between 5 and 30 minutes. RFC 2177 addresses this by recommending that clients reissue `DONE` and `IDLE` every 29 minutes to reset the connection's idle timer at the network layer. Well-implemented IMAP clients — Thunderbird, Apple Mail, and K-9 Mail among them — all implement this 29-minute IDLE renewal cycle. Servers that implement IDLE must correctly handle the race condition where a new message arrives between the client sending `DONE` and the server acknowledging the end of the IDLE command: the server must buffer any unsolicited responses that occur during this window and deliver them before or alongside the IDLE completion response.

For infrastructure architects deploying Dovecot, the `imap_idle_notify_interval` configuration parameter controls how frequently the server sends a `* OK [TIMEOUT]` keepalive to prevent the connection from being classified as idle by intermediate network equipment. Setting this between 2 and 10 minutes is appropriate for most deployment environments. Under heavy load, IDLE connections are persistent TCP sessions that consume file descriptors, memory in the connection context, and CPU for event demultiplexing. A Dovecot deployment serving 10,000 concurrent IDLE connections requires careful tuning of `max_connections`, the `imap_max_userip_connections` limit, and the system's `net.core.somaxconn` and file descriptor limits.

## 3. High-Performance Optimization & Failure Modes

### Storage Backend Selection and Its Impact on Protocol Performance

The choice of mailbox storage format is not a deployment afterthought; it determines the performance envelope of every IMAP operation at scale. The three dominant formats — `mbox`, `Maildir`, and Dovecot's native `dbox` — have fundamentally different read/write characteristics that interact with IMAP semantics in ways that are not obvious from their documentation alone.

The `mbox` format stores all messages in a mailbox as a single file, separated by `From ` lines. Every IMAP operation that modifies flags requires rewriting the file from the modification point to end-of-file, because flags are stored as `X-Status` and `X-Keywords` headers embedded within each message's RFC 5322 representation. For a 2 GB INBOX with 50,000 messages, setting `\Seen` on message 100 of 50,000 requires rewriting approximately 1.98 GB of data. Locking semantics compound the problem: `mbox` uses `fcntl` advisory locks or `dotlock` files to serialize access, which means two concurrent IMAP sessions attempting to modify the same mailbox will serialize entirely, eliminating any parallelism benefit from multiple connections. Modern infrastructure should not use `mbox` for IMAP backends. Its continued presence in Dovecot's supported format list is a compatibility concession, not an endorsement.

`Maildir`, specified informally by D.J. Bernstein and codified in various server implementations, stores each message as an individual file within a directory structure consisting of `new/`, `cur/`, and `tmp/` subdirectories. Flags are encoded in the filename itself via a standardized suffix convention: a message marked as read and flagged would have a filename ending in `:2,FS`. This design means flag changes are atomic rename operations, and concurrent access from multiple processes requires no explicit locking — the directory entry rename is atomic at the POSIX filesystem level, and two concurrent flag changes on different messages do not interfere with each other. The weakness of `Maildir` becomes apparent at scale: a mailbox with 100,000 messages in `cur/` creates a directory with 100,000 entries. Listing this directory to compute `EXISTS` requires a full `readdir` traversal, which scales as O(N) in the number of messages and can take seconds on a loaded filesystem. `ext4` with `dir_index` (htree) and `large_dir` features enabled mitigates this substantially, but it does not eliminate it. Servers using `Maildir` for large mailboxes must maintain a Dovecot index — the `dovecot.index`, `dovecot.index.cache`, and `dovecot.index.log` files — to avoid this O(N) traversal on every `SELECT`.

Dovecot's `dbox` format, available in single-dbox (`sdbox`) and multi-dbox (`mdbox`) variants, is purpose-designed for IMAP semantics. `sdbox` stores one message per file like Maildir but stores flags, UIDs, and metadata in a Dovecot-specific binary header rather than in the filename. `mdbox` stores multiple messages per file in a structured binary format and maintains a separate metadata index, which dramatically reduces inode consumption and improves sequential read performance for clients fetching entire messages. `mdbox` also supports a lazy-expunge mechanism: deleted messages are moved to a hidden `DUMPSTER` mailbox rather than unlinked immediately, allowing accidental deletion recovery without a separate backup system. For high-volume deployments handling millions of messages, `mdbox` provides the best balance of IMAP operational latency, storage efficiency, and backup-friendliness.

### IMAP Namespace Configuration and Shared Mailbox Architecture

RFC 2342 defines the IMAP namespace extension, which allows a server to expose multiple mailbox hierarchies to a single authenticated client. The personal namespace contains the user's own mailboxes (typically with an empty prefix or `INBOX.` prefix). The shared namespace and the other-users namespace expose mailboxes owned by other accounts — shared calendars, distribution list archives, public folders — that the authenticated user has been granted access to. For infrastructure architects building collaborative mail systems, the namespace configuration in Dovecot's `namespace` blocks in `dovecot.conf` is the mechanism that makes shared mailboxes discoverable to clients without requiring manual subscription management.

```
# dovecot.conf: Personal, shared, and public namespace configuration

namespace inbox {
  type = private
  separator = /
  prefix =
  inbox = yes
  location =
}

namespace shared {
  type = shared
  separator = /
  prefix = shared/%%u/
  location = maildir:/var/mail/shared/%%u/:INDEX=~/shared/%%u/
  subscriptions = no
  list = children
}

namespace public {
  type = public
  separator = /
  prefix = public/
  location = maildir:/var/mail/public/:INDEXPVT=~/public/
  subscriptions = yes
  list = yes
}
```

The `INDEXPVT` parameter in the public namespace definition is architecturally important: it instructs Dovecot to store per-user private metadata — specifically the `\Seen` flag — in the user's home directory index rather than in the shared message store. Without `INDEXPVT`, marking a message as read in a public mailbox would mark it as read for all users, which violates every reasonable expectation of flag semantics. With `INDEXPVT`, the message file on disk is shared and the flag state is stored per-user in private index files, correctly modeling the semantic that "I have read this message" is personal state, not a property of the message itself.

### IMAP ACL and Authorization Boundaries

RFC 4314 defines the IMAP ACL (Access Control List) extension, which allows fine-grained permission assignment on individual mailboxes. The rights string uses a compact character encoding: `l` for lookup (seeing the mailbox in `LIST`), `r` for read (issuing `SELECT` and `FETCH`), `s` for persistent `\Seen` flag storage, `w` for write (setting flags other than `\Seen` and `\Deleted`), `i` for insert (`APPEND` and `COPY` into the mailbox), `p` for post (delivering via `LMTP`), `k` for create-child (creating subfolders), `x` for delete-mailbox, `t` for mark-deleted (setting `\Deleted`), and `e` for expunge.

A shared mailbox where members should read messages and mark them read but not delete them would be assigned rights `lrsi`. A service account used by an archival system that only appends messages would receive `lip`. Correctly scoping ACL rights prevents the class of incidents where a misconfigured mail client with write access accidentally expunges a shared archive. In Dovecot, ACLs are configured via the `acl` plugin with either filesystem ACL files (`dovecot-acl` per-mailbox files) or the `acl_global_file` for server-wide policies.

### Diagnosing Synchronization Failures in Production

Mailbox synchronization failures manifest in several characteristic patterns that are distinguishable at the protocol level.

The `UIDVALIDITY` mismatch scenario occurs after mailbox migrations or restores from backup that do not preserve UIDs. A client that cached `UIDVALIDITY = 1704067200` reconnects and finds `UIDVALIDITY = 1704500000`. The correct behavior is to discard the local message cache and perform a full resync, issuing `UID FETCH 1:* FLAGS` to rebuild the local message list. The incorrect behavior — which you will find in some older mobile clients — is to map UIDs from the old `UIDVALIDITY` namespace to the new one positionally, corrupting the local store. When debugging client complaints of "messages appearing in the wrong folders" or "read messages reappearing as unread" after a migration, `UIDVALIDITY` mismatch is the first thing to check. Dovecot logs the `UIDVALIDITY` for each `SELECT` operation at `info` log level, and you can confirm it with `doveadm mailbox status -u user@domain uidvalidity INBOX`.

```bash
# Inspect mailbox status including UIDVALIDITY and message count
doveadm mailbox status -u alice@example.com \
  "messages unseen recent uidvalidity uidnext" INBOX

# Force a full index rebuild when indexes are corrupt
doveadm force-resync -u alice@example.com INBOX

# Check IMAP session state for a connected user
doveadm who -1 | grep alice@example.com

# Dump the raw IMAP protocol exchange for a user session (Dovecot rawlog)
# Add to conf.d/10-logging.conf:
# mail_log_prefix = "%s(%u)<%{pid}><%{session}>: "
# protocol imap { rawlog_dir = /var/log/dovecot/rawlog/%u }

# Verify message UID assignments in a mailbox
doveadm fetch -u alice@example.com "uid flags" mailbox INBOX | head -40

# Check for mailboxes with elevated message counts (potential loop delivery)
doveadm mailbox status -u alice@example.com "messages" "*" | sort -k2 -rn | head -10
```

The duplicate message scenario is a different failure mode. It presents as a client showing the same message twice with different sequence numbers but identical message-id headers. The root cause is typically a delivery loop — an LMTP or Sieve filter that re-delivers messages to the same mailbox — or a client that appended a message to `Sent` after the server already stored it via the `FCC` mechanism. Use `doveadm fetch` with `hdr message-id` to identify duplicate message-ids, then inspect delivery logs in Postfix or Exim to trace where the duplicate was introduced.

IMAP `EXPUNGE` sequence number desynchronization is a subtler failure that occurs when a client processes unsolicited `EXPUNGE` responses incorrectly. The scenario: a client has selected a mailbox with 1,000 messages. While the client is idle (or in `IDLE`), another session deletes messages 50, 51, and 52. When the first client's session becomes active again, the server delivers `* 50 EXPUNGE`, `* 50 EXPUNGE`, `* 50 EXPUNGE` — three expunges all at sequence 50, because after the first expunge shifts message 51 down to position 50, the second expunge also refers to position 50. A client that naively treats these as three distinct addresses (50, 51, 52) will corrupt its local sequence number map and subsequently `FETCH` wrong messages. This is an RFC compliance bug, and you can trigger it deliberately in a test environment to validate client behavior.

```bash
# Use openssl s_client to exercise IMAP directly for debugging
openssl s_client -connect mail.example.com:993 -quiet

# After TLS handshake, manually drive the session:
# A001 LOGIN testuser@example.com password
# A002 SELECT INBOX
# A003 NOOP
# A004 UID FETCH 2888 (FLAGS ENVELOPE RFC822.SIZE)
# A005 UID STORE 2888 +FLAGS (\Deleted)
# A006 EXPUNGE
# A007 LOGOUT

# Capture and analyze an IMAP session with Wireshark (post-TLS decryption with session key log):
# SSLKEYLOGFILE=/tmp/tls.keys thunderbird &
# wireshark -o "tls.keylog_file:/tmp/tls.keys" -i eth0 -f "tcp port 993"
```

### Scaling IMAP Infrastructure for Thousands of Concurrent Sessions

At scale, IMAP infrastructure faces two distinct bottlenecks: connection state memory and storage I/O throughput. Each IMAP session in Dovecot maintains in memory a parsed copy of the mailbox index, the current `SELECTED` mailbox's flag and UID maps, and the pending response queue. For a user with a 50,000-message INBOX, the in-memory index representation is roughly 2–4 MB per session. At 10,000 concurrent sessions, this is 20–40 GB of memory consumed purely for index state, before accounting for Dovecot's process model overhead.

Dovecot's default process model spawns a separate `imap` process per authenticated user connection. This provides strong isolation — a crashing IMAP process does not affect other sessions — but imposes per-process overhead of approximately 1–2 MB of base memory plus index memory. Switching to the `imap` service's `service_count = 0` and `process_min_avail` settings to pre-fork a pool of IMAP processes reduces fork overhead for high-connection-rate deployments. The `auth_cache_size` parameter controls how long credential verification results are cached; setting this to 10M or 100M reduces LDAP or SQL authentication latency for clients that frequently reconnect.

Storage I/O scaling for `Maildir` backends typically hits the directory enumeration bottleneck first. When Dovecot's index is fresh and consistent with the filesystem, `SELECT` requires only reading the index file, not traversing the directory. Keeping indexes warm requires that the `dovecot-indexer-worker` service runs continuously and processes index update events from the `dovecot-indexer` service. For deployments where multiple Dovecot front-end servers share a common NFS or Ceph storage backend, the index locking mechanism must be tuned appropriately: `mmap_disable = yes` and `lock_method = dotlock` are necessary on NFS to avoid cache coherency bugs from memory-mapped index files, at the cost of slightly higher lock latency.

For the highest-throughput deployments — multi-tenant mail services handling hundreds of thousands of active users — the architecture shifts from monolithic Dovecot installations to director proxy clusters. Dovecot Director (or its successor, Dovecot Pro's `director` process) provides consistent hashing across a pool of IMAP backend nodes, ensuring that all sessions for a given user are routed to the same backend server. This matters because IMAP's guarantee of consistent session state depends on all concurrent connections for a user sharing the same in-memory index. Routing the same user's IMAP sessions to different backends without shared locking would produce index corruption. The director layer enforces the invariant that a user's sessions converge to a single backend, while still allowing the backend pool to grow horizontally as the user base scales.

```
Dovecot Director Architecture:

  ┌─────────────────────────────────────────────────────┐
  │                   Load Balancer                      │
  │            (HAProxy / F5 / Cloud LB)                 │
  │         Port 993 (IMAPS) / Port 143 (IMAP)           │
  └───────────────────┬─────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ Director │  │ Director │  │ Director │
  │  Proxy 1 │  │  Proxy 2 │  │  Proxy 3 │
  │ (Active) │  │ (Active) │  │ (Active) │
  └────┬─────┘  └────┬─────┘  └────┬─────┘
       │              │              │
       └──────────────┼──────────────┘
                      │
        (Consistent Hash Ring: user→backend)
                      │
        ┌─────────────┼─────────────┐
        │             │             │
  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │  IMAP    │  │  IMAP    │  │  IMAP    │
  │ Backend 1│  │ Backend 2│  │ Backend 3│
  │ (dbox)   │  │ (dbox)   │  │ (dbox)   │
  └────┬─────┘  └────┬─────┘  └────┬─────┘
       │              │              │
       └──────────────┼──────────────┘
                      │
  ┌────────────────────────────────────────┐
  │      Shared Storage Layer              │
  │   (Ceph RBD / NFS v4.1 / GlusterFS)   │
  │   Maildir++ or mdbox per-user stores   │
  └────────────────────────────────────────┘
```

The key operational test for a director cluster is verifying that the consistent hash ring correctly reassigns users when a backend is added or removed. When a backend fails, Dovecot Director redistributes its user assignments to the remaining backends. The first connection after redistribution will find a cold index on the new backend and must rebuild it from the filesystem. This index cold-start latency — which can be several seconds for large mailboxes on NFS — is the primary SLA concern during backend failures. Maintaining warm standbys with pre-built indexes via `dovecot-replicator` service (which uses a custom replication protocol to push index updates between backends) reduces this cold-start penalty to near zero for the highest-tier users.

The retrieval protocol layer is ultimately the client-visible face of a mail system's reliability contract. The correctness of UID assignment, the fidelity of flag synchronization, the efficiency of delta sync via `QRESYNC`, and the responsiveness of `IDLE` push notifications determine whether users experience their mail system as a reliable workspace or an unreliable source of confusion. Getting these mechanics right requires understanding both the protocol state machines at the RFC level and the storage backend behaviors that determine whether those state machines can operate at the performance their semantics demand.
