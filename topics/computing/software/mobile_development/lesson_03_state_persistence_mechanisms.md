# Lesson 3: State Persistence Mechanisms

## 1. First-Principles Intuition & Invariants

Every mobile application exists in a state of perpetual negotiation with impermanence. Unlike a desktop process that can hold its entire working set in memory across days of uptime, a mobile application faces a hostile runtime contract: the OS may terminate it at any moment to reclaim memory, the user may switch away and never return, the battery may die mid-transaction, and the hardware itself may be replaced with all its local storage wiped clean. Persistence, therefore, is not a feature a mobile engineer bolts on at the end of a development cycle. It is the structural spine of the entire application architecture.

To reason about persistence correctly, you must first understand what you are actually preserving and why. The state of a mobile application decomposes into at least four conceptually distinct layers, each with different durability requirements, access patterns, and failure semantics. Ephemeral UI state — the scroll position of a list, whether a modal is expanded — has very different persistence requirements than a user's authentication credential, a half-composed message draft, or a local replica of a server-side dataset. Conflating these layers is the single most common design error in production mobile systems, and it manifests as either over-engineering (encrypting the scroll position to disk on every frame) or catastrophic data loss (storing authentication tokens only in memory that the OS silently reclaims).

At the physical layer, all persistence on a mobile device ultimately resolves to writes against a flash-backed block storage device managed by the mobile OS's kernel. iOS exposes this through the Data Volume of the APFS (Apple File System) container, which provides copy-on-write semantics, cryptographic volume encryption via the Secure Enclave, and hardware-enforced file data protection classes. Android's storage model is built on top of ext4 or f2fs partitions, with the f2fs (Flash-Friendly File System) being particularly relevant because its log-structured design minimizes write amplification against NAND flash — a property that matters enormously for battery life and storage longevity on constrained devices. Every abstraction you use — SQLite, SharedPreferences, Realm, NSUserDefaults — eventually serializes bytes into page-sized blocks (typically 4 KB) written through the OS's page cache and flushed to these underlying file systems.

This physical reality imposes two invariants that every senior engineer must internalize. The first is that all writes are initially volatile until they cross the fsync boundary. When you call `sqlite3_exec` or write to an `NSFileHandle`, the data lives in the kernel's page cache — it has not hit the flash controller's write buffer, and it certainly has not been committed to stable storage. A sudden power loss at this point means data loss. The second invariant is that flash storage does not behave like a magnetic disk: random small writes are extremely expensive relative to sequential writes, because the flash translation layer must perform erase-before-write operations on 128 KB to 512 KB erase blocks even to change a single byte. A database engine that issues hundreds of random 64-byte writes per transaction will not only perform poorly but will measurably degrade the device's storage hardware over time. These are not theoretical concerns — they are root causes of real production incidents.

The persistence abstractions available to mobile engineers exist on a spectrum defined by three axes: structural rigidity (schema-free key-value store versus fully typed relational schema), transactional guarantees (ACID versus eventual consistency), and access granularity (full object serialization versus column-level projection). Understanding where each tool sits on these axes, and why it sits there, is what separates engineers who reach for the first tool that works from engineers who make defensible architectural decisions.

---

## 2. Core Architecture & Mechanics

### The Storage Abstraction Hierarchy

The persistence stack on both iOS and Android can be understood as a layered hierarchy where each layer provides progressively richer semantics in exchange for progressively more structural overhead. Visualizing this hierarchy makes the tradeoffs concrete:

```
┌─────────────────────────────────────────────────────────────┐
│              Application Domain Layer                        │
│   (ViewModels, UseCases, Repositories, Domain Models)       │
├─────────────────────────────────────────────────────────────┤
│              Persistence Abstraction Layer                   │
│   SQLite/Room │ Realm/GRDB │ Keychain/Keystore │ Files      │
├─────────────────────────────────────────────────────────────┤
│              OS Storage Services Layer                       │
│   APFS Data Protection │ Scoped Storage │ Security Enclave  │
├─────────────────────────────────────────────────────────────┤
│              File System Layer                               │
│         APFS (iOS/macOS)  │  ext4 / f2fs (Android)         │
├─────────────────────────────────────────────────────────────┤
│              Block Device Layer                              │
│       Flash Translation Layer (FTL) + NAND Controller       │
└─────────────────────────────────────────────────────────────┘
```

Each layer in this stack introduces both capabilities and constraints. A decision made at the persistence abstraction layer — choosing Room over raw SQLite, for example — is a decision about how much of the SQL query planner you trust to optimize your access patterns versus how much control you need over index selection, `EXPLAIN QUERY PLAN` output, and WAL checkpoint behavior.

### Key-Value Stores: NSUserDefaults and SharedPreferences

The simplest persistence primitive on both platforms is the key-value store. `NSUserDefaults` on iOS stores its data as a property list (plist), serialized into XML or binary format and written to `Library/Preferences/<bundle-id>.plist` within the application's sandbox. When an application calls `synchronize()` (or when the system does so automatically), this entire file is serialized and written atomically using a write-to-temp-then-rename pattern that provides crash safety at the file level. The critical architectural detail is that `NSUserDefaults` holds its entire domain in memory once accessed. The initial `object(forKey:)` call triggers a full deserialization of the plist from disk into a mutable dictionary in the process's heap. Subsequent reads hit only this in-memory representation. This design is fast for small datasets but becomes a liability when engineers misuse `NSUserDefaults` to store large blobs, arrays of hundreds of objects, or binary data — not because the write is slow, but because the entire payload occupies heap memory and the full serialization cost is paid on every write-through cycle.

Android's `SharedPreferences` is architecturally similar: an XML-backed key-value store loaded entirely into memory on first access, with `apply()` performing an asynchronous write to a background thread's queue and `commit()` performing a synchronous write that blocks the calling thread. The distinction between `apply()` and `commit()` is frequently misunderstood. Using `commit()` on the main thread is a correctness choice that engineers make when they need write durability before proceeding — for instance, before launching an Activity that depends on the value just written — but it carries a real risk of jank if the write is slow. Using `apply()` is correct for most use cases but means the value is committed to memory immediately while the disk write is deferred. If the process is killed before the background write completes, that write is lost. For the vast majority of UI preference data, this is acceptable. For anything that resembles state that must survive a force-kill, it is not.

The modern Android replacement, `DataStore` (specifically the Preferences DataStore backed by Protocol Buffers), solves the threading problems of `SharedPreferences` by operating entirely within Kotlin's coroutine and Flow model. Every read returns a `Flow<Preferences>` and every write suspends until the data is durably committed to disk. The underlying storage format is a serialized protobuf written atomically, and the entire API is designed to prevent the class of bugs where `SharedPreferences` data is inconsistently read from multiple threads. Here is a complete, production-grade implementation of a typed preferences repository using the Proto DataStore:

**`user_preferences.proto`**
```proto
syntax = "proto3";

option java_package = "com.example.app.datastore";
option java_multiple_files = true;

message UserPreferences {
  string auth_token = 1;
  int64 last_sync_epoch_ms = 2;
  bool onboarding_complete = 3;
  Theme selected_theme = 4;

  enum Theme {
    SYSTEM = 0;
    LIGHT = 1;
    DARK = 2;
  }
}
```

**`UserPreferencesRepository.kt`**
```kotlin
import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.core.DataStoreFactory
import androidx.datastore.core.Serializer
import com.example.app.datastore.UserPreferences
import com.google.protobuf.InvalidProtocolBufferException
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.catch
import java.io.File
import java.io.IOException
import java.io.InputStream
import java.io.OutputStream

object UserPreferencesSerializer : Serializer<UserPreferences> {
    override val defaultValue: UserPreferences = UserPreferences.getDefaultInstance()

    override suspend fun readFrom(input: InputStream): UserPreferences {
        return try {
            UserPreferences.parseFrom(input)
        } catch (e: InvalidProtocolBufferException) {
            throw androidx.datastore.core.CorruptionException("Cannot read proto.", e)
        }
    }

    override suspend fun writeTo(t: UserPreferences, output: OutputStream) {
        t.writeTo(output)
    }
}

class UserPreferencesRepository(context: Context) {

    private val dataStore: DataStore<UserPreferences> = DataStoreFactory.create(
        serializer = UserPreferencesSerializer,
        produceFile = {
            File("${context.filesDir.path}/datastore/user_prefs.pb")
        }
    )

    val userPreferencesFlow: Flow<UserPreferences> = dataStore.data
        .catch { exception ->
            if (exception is IOException) {
                emit(UserPreferences.getDefaultInstance())
            } else {
                throw exception
            }
        }

    suspend fun updateAuthToken(token: String) {
        dataStore.updateData { currentPreferences ->
            currentPreferences.toBuilder()
                .setAuthToken(token)
                .build()
        }
    }

    suspend fun markOnboardingComplete() {
        dataStore.updateData { currentPreferences ->
            currentPreferences.toBuilder()
                .setOnboardingComplete(true)
                .setLastSyncEpochMs(System.currentTimeMillis())
                .build()
        }
    }

    suspend fun setTheme(theme: UserPreferences.Theme) {
        dataStore.updateData { currentPreferences ->
            currentPreferences.toBuilder()
                .setSelectedTheme(theme)
                .build()
        }
    }
}
```

This implementation is correct because `updateData` is a suspending transaction that serializes concurrent writes: if two coroutines call `updateAuthToken` and `setTheme` simultaneously, they execute sequentially against the in-memory representation and the result is a single atomic write to disk. There is no equivalent of this guarantee in `SharedPreferences`.

### SQLite: The Embedded Relational Engine

SQLite is not a simplified database. It is one of the most rigorously tested and deployed pieces of software in human history, present on literally every Android and iOS device on the planet and running against a test suite that is orders of magnitude larger than its implementation source. Understanding its internal mechanics is prerequisite to using it correctly under production conditions.

SQLite's B-tree storage engine organizes all data — both tables and indexes — into B-tree structures stored within a single cross-platform database file. The fundamental unit of I/O is the **page**, which defaults to 4096 bytes, matching the typical OS virtual memory page and minimizing the number of syscalls required to load data from the kernel's page cache into the SQLite page cache. Each table is stored as a B-tree where the rows are ordered by their `rowid` (or by the declared `INTEGER PRIMARY KEY`). Each index is a separate B-tree containing the indexed column values as keys and the corresponding rowids as payloads. When SQLite executes a query like `SELECT * FROM messages WHERE thread_id = ? ORDER BY created_at DESC LIMIT 50`, the query planner's job is to determine whether it's cheaper to perform a full table scan through the messages B-tree, or to traverse the index B-tree on `thread_id`, retrieve the matching rowids, and then perform point lookups against the table B-tree. This second operation — index lookup followed by rowid retrieval — is called a **table scan with rowid lookup** in SQLite's EXPLAIN output, and its cost is proportional to the number of rows that match the predicate multiplied by the depth of both B-trees.

The **Write-Ahead Log (WAL)** mode is the single most impactful SQLite configuration change available on mobile. In the default journal mode, SQLite implements rollback by copying original page content into a rollback journal file before modifying the database pages in-place. Writers therefore block readers entirely during this process. WAL inverts this: writers append new page versions to a separate WAL file, while readers continue reading older versions from the original database file. Readers and writers do not block each other. The database file only reaches the new page versions when a WAL checkpoint operation copies them from the WAL file back into the database. This architecture is the reason that WAL mode produces dramatically better concurrency on mobile apps where a background sync thread is writing while the UI thread is reading. Enabling WAL mode and setting a sensible page cache are the first two configuration steps for any production SQLite deployment:

```swift
// iOS: Configuring SQLite for production via SQLite3 C API
import SQLite3
import Foundation

final class DatabaseConnection {

    private var db: OpaquePointer?
    private let dbURL: URL

    init(storeName: String) throws {
        let docDir = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        self.dbURL = docDir.appendingPathComponent("\(storeName).sqlite")
        try openAndConfigure()
    }

    private func openAndConfigure() throws {
        let flags = SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE | SQLITE_OPEN_FULLMUTEX
        guard sqlite3_open_v2(dbURL.path, &db, flags, nil) == SQLITE_OK else {
            throw PersistenceError.openFailed(String(cString: sqlite3_errmsg(db)))
        }

        // Enable WAL mode for concurrent read/write access
        try exec("PRAGMA journal_mode = WAL;")

        // 64 MB in-process page cache (4096 byte pages * 16384 pages)
        try exec("PRAGMA cache_size = -65536;")

        // Synchronous NORMAL: fsync on WAL checkpoints but not every commit.
        // Safe because WAL frames are written sequentially and WAL header
        // integrity prevents partial-frame corruption.
        try exec("PRAGMA synchronous = NORMAL;")

        // Store temporary tables in memory rather than on disk
        try exec("PRAGMA temp_store = MEMORY;")

        // Enable foreign key constraint enforcement (off by default in SQLite)
        try exec("PRAGMA foreign_keys = ON;")

        // Set a 5-second busy timeout before returning SQLITE_BUSY
        sqlite3_busy_timeout(db, 5000)

        try createSchema()
    }

    private func createSchema() throws {
        try exec("""
            CREATE TABLE IF NOT EXISTS messages (
                id          TEXT PRIMARY KEY NOT NULL,
                thread_id   TEXT NOT NULL,
                body        TEXT NOT NULL,
                created_at  INTEGER NOT NULL,
                is_read     INTEGER NOT NULL DEFAULT 0,
                sender_id   TEXT NOT NULL
            ) WITHOUT ROWID;

            CREATE INDEX IF NOT EXISTS idx_messages_thread_created
                ON messages(thread_id, created_at DESC);

            CREATE TABLE IF NOT EXISTS schema_migrations (
                version     INTEGER PRIMARY KEY NOT NULL,
                applied_at  INTEGER NOT NULL
            );
        """)
    }

    func queryMessages(threadId: String, limit: Int = 50) throws -> [[String: Any]] {
        let sql = """
            SELECT id, body, created_at, sender_id
            FROM messages
            WHERE thread_id = ?
            ORDER BY created_at DESC
            LIMIT ?;
        """
        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(db, sql, -1, &stmt, nil) == SQLITE_OK else {
            throw PersistenceError.prepareFailed(String(cString: sqlite3_errmsg(db)))
        }
        defer { sqlite3_finalize(stmt) }

        sqlite3_bind_text(stmt, 1, threadId, -1, SQLITE_TRANSIENT)
        sqlite3_bind_int(stmt, 2, Int32(limit))

        var results: [[String: Any]] = []
        while sqlite3_step(stmt) == SQLITE_ROW {
            results.append([
                "id":         String(cString: sqlite3_column_text(stmt, 0)),
                "body":       String(cString: sqlite3_column_text(stmt, 1)),
                "created_at": Int(sqlite3_column_int64(stmt, 2)),
                "sender_id":  String(cString: sqlite3_column_text(stmt, 3))
            ])
        }
        return results
    }

    @discardableResult
    private func exec(_ sql: String) throws -> Int32 {
        var errMsg: UnsafeMutablePointer<CChar>?
        let rc = sqlite3_exec(db, sql, nil, nil, &errMsg)
        if rc != SQLITE_OK {
            let msg = errMsg.map(String.init(cString:)) ?? "unknown error"
            sqlite3_free(errMsg)
            throw PersistenceError.execFailed(msg)
        }
        return rc
    }

    deinit {
        sqlite3_close_v2(db)
    }
}

enum PersistenceError: Error {
    case openFailed(String)
    case prepareFailed(String)
    case execFailed(String)
}
```

Notice the `WITHOUT ROWID` clause on the messages table. For tables whose primary key is a stable text identifier (a UUID, a server-assigned ID), `WITHOUT ROWID` eliminates the implicit integer rowid and stores the row data directly within the primary key B-tree, reducing one level of indirection on primary key lookups and shrinking the on-disk footprint for tables where the primary key column is the dominant identifier. This is a meaningful optimization for message tables in production chat applications where billions of rows accumulate over time.

### Room as a Type-Safe SQLite Abstraction

For Android, the Room persistence library sits directly atop SQLite's C library and generates type-safe Java/Kotlin DAOs at compile time. Room is not an ORM in the heavyweight sense — it does not attempt to manage relationships through lazy-loaded object graphs or maintain an identity map across the entire session. It is better understood as a compile-time-verified query layer that maps annotated Kotlin data classes to SQL tables and annotated interface methods to prepared statements. The compile-time query verification is the feature that earns Room its place in production codebases: a typo in a `@Query` annotation fails the build, not the user's runtime experience.

```kotlin
// Complete Room implementation for a messaging feature

import androidx.room.*
import kotlinx.coroutines.flow.Flow

@Entity(
    tableName = "messages",
    indices = [Index(value = ["thread_id", "created_at"])]
)
data class MessageEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "thread_id") val threadId: String,
    @ColumnInfo(name = "body") val body: String,
    @ColumnInfo(name = "created_at") val createdAt: Long,
    @ColumnInfo(name = "is_read") val isRead: Boolean = false,
    @ColumnInfo(name = "sender_id") val senderId: String
)

data class MessagePreview(
    val threadId: String,
    val body: String,
    val createdAt: Long,
    val unreadCount: Int
)

@Dao
interface MessageDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMessages(messages: List<MessageEntity>)

    @Query("""
        SELECT * FROM messages
        WHERE thread_id = :threadId
        ORDER BY created_at DESC
        LIMIT :limit
    """)
    fun observeMessages(threadId: String, limit: Int = 50): Flow<List<MessageEntity>>

    @Query("""
        SELECT
            thread_id,
            body,
            MAX(created_at) AS created_at,
            SUM(CASE WHEN is_read = 0 THEN 1 ELSE 0 END) AS unreadCount
        FROM messages
        GROUP BY thread_id
        ORDER BY created_at DESC
    """)
    fun observeThreadPreviews(): Flow<List<MessagePreview>>

    @Query("""
        UPDATE messages
        SET is_read = 1
        WHERE thread_id = :threadId AND is_read = 0
    """)
    suspend fun markThreadRead(threadId: String): Int

    @Query("DELETE FROM messages WHERE thread_id = :threadId")
    suspend fun deleteThread(threadId: String)

    @Transaction
    suspend fun replaceThread(threadId: String, messages: List<MessageEntity>) {
        deleteThread(threadId)
        insertMessages(messages)
    }
}

@Database(
    entities = [MessageEntity::class],
    version = 2,
    exportSchema = true
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun messageDao(): MessageDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getInstance(context: android.content.Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "app_database.db"
                )
                .addMigrations(MIGRATION_1_2)
                .setJournalMode(JournalMode.WRITE_AHEAD_LOGGING)
                .build()
                .also { INSTANCE = it }
            }
        }
    }
}

val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(database: SupportSQLiteDatabase) {
        database.execSQL("""
            ALTER TABLE messages ADD COLUMN sender_id TEXT NOT NULL DEFAULT ''
        """)
        database.execSQL("""
            CREATE INDEX IF NOT EXISTS idx_messages_thread_created
            ON messages(thread_id, created_at DESC)
        """)
    }
}

class Converters {
    @TypeConverter
    fun fromTimestamp(value: Long?): java.util.Date? = value?.let { java.util.Date(it) }

    @TypeConverter
    fun dateToTimestamp(date: java.util.Date?): Long? = date?.time
}
```

The `observeMessages` DAO method returns a `Flow<List<MessageEntity>>` rather than a one-shot `suspend` function. Room implements this by registering an invalidation tracker on the underlying SQLite table: whenever a write transaction commits against the `messages` table, Room's invalidation tracker fires, the coroutine collecting the flow receives a new emission, and the query re-executes. The UI remains continuously synchronized with the database state without any polling. This is the architecture that enables the unidirectional data flow pattern — database writes from any source (UI action, background sync, push notification handler) automatically propagate to all active observers.

### Realm: Object-Oriented MVCC Persistence

Realm is architecturally distinct from SQLite in a way that matters for how you reason about it. Rather than mapping objects to rows in B-tree tables and translating between object graphs and relational rows at runtime, Realm stores data as a column-oriented object graph in a memory-mappable binary file format. The Realm file is mapped directly into the process's virtual address space via `mmap`. When you access a Realm object's property, the runtime reads the value directly from the memory-mapped file pages, with zero deserialization. There is no copy from the kernel's page cache into a separately allocated buffer in the heap. The data is already there, at a virtual address your process can dereference.

Realm's concurrency model is built around MVCC (Multi-Version Concurrency Control), the same fundamental mechanism used by PostgreSQL and LMDB. Each read transaction operates against a consistent snapshot identified by a monotonically increasing version number. When a write transaction commits, Realm allocates new page slots for the modified objects and updates the root pointer atomically. Reader transactions holding older version references continue to see their consistent snapshot. The Realm runtime performs a background process called "compaction" to reclaim the space consumed by old versions that are no longer referenced by any active transaction.

```swift
// iOS: Complete Realm implementation with schema migration

import RealmSwift
import Foundation

// MARK: - Domain Models

class Message: Object {
    @Persisted(primaryKey: true) var id: String = UUID().uuidString
    @Persisted var threadId: String = ""
    @Persisted var body: String = ""
    @Persisted var createdAt: Date = Date()
    @Persisted var isRead: Bool = false
    @Persisted var senderId: String = ""

    // Backlink: automatically maintained inverse relationship
    @Persisted(originProperty: "messages") var thread: LinkingObjects<Thread>
}

class Thread: Object {
    @Persisted(primaryKey: true) var id: String = UUID().uuidString
    @Persisted var title: String = ""
    @Persisted var participantIds: List<String>
    @Persisted var messages: List<Message>
    @Persisted var lastActivityAt: Date = Date()
}

// MARK: - Migration

let realmMigration = RealmMigration { migration, oldSchemaVersion in
    if oldSchemaVersion < 2 {
        // Migration from schema v1: Thread.participantCount (Int) removed,
        // replaced with participantIds (List<String>)
        migration.enumerateObjects(ofType: Thread.className()) { oldObject, newObject in
            newObject?["participantIds"] = List<String>()
        }
    }
    if oldSchemaVersion < 3 {
        migration.enumerateObjects(ofType: Message.className()) { oldObject, newObject in
            // Populate senderId from a legacy authorName string field
            let authorName = oldObject?["authorName"] as? String ?? ""
            newObject?["senderId"] = authorName.lowercased().replacingOccurrences(of: " ", with: "_")
        }
    }
}

// MARK: - Configuration

func buildRealmConfiguration() -> Realm.Configuration {
    return Realm.Configuration(
        fileURL: FileManager.default
            .urls(for: .documentDirectory, in: .userDomainMask)
            .first!
            .appendingPathComponent("app.realm"),
        schemaVersion: 3,
        migrationBlock: realmMigration,
        objectTypes: [Message.self, Thread.self]
    )
}

// MARK: - Repository

final class MessageRepository {
    private let configuration: Realm.Configuration

    init(configuration: Realm.Configuration = buildRealmConfiguration()) {
        self.configuration = configuration
    }

    private func openRealm() throws -> Realm {
        return try Realm(configuration: configuration)
    }

    func insertMessages(_ messages: [Message]) throws {
        let realm = try openRealm()
        try realm.write {
            realm.add(messages, update: .modified)
        }
    }

    func observeMessages(inThread threadId: String) -> AnyPublisher<[Message], Never> {
        // Realm Results are live-queried: the token fires on every commit
        // that affects the filtered set.
        let realm = try! openRealm()
        let results = realm.objects(Message.self)
            .filter("threadId == %@", threadId)
            .sorted(byKeyPath: "createdAt", ascending: false)

        return results.collectionPublisher
            .map { Array($0) }
            .catch { _ in Just([]) }
            .eraseToAnyPublisher()
    }

    func markThreadRead(threadId: String) throws {
        let realm = try openRealm()
        let unread = realm.objects(Message.self)
            .filter("threadId == %@ AND isRead == false", threadId)
        try realm.write {
            unread.setValue(true, forKey: "isRead")
        }
    }
}
```

The `update: .modified` strategy in `realm.add(_:update:)` is worth careful attention. Rather than blindly overwriting every property of an existing object (`.all`), `.modified` performs a property-level diff and only records a change if the new value differs from the stored value. This is a significant optimization because Realm's change notification system notifies observers at property granularity — an observer watching a `Message` object's `isRead` property will not receive a spurious notification just because the message was re-inserted with the same values. This matters enormously in sync-heavy applications where server polling may re-deliver objects that have not actually changed.

### The iOS Keychain and Android Keystore: Secure Credential Storage

No discussion of persistence is complete without addressing secure storage, because the temptation to store sensitive data — authentication tokens, cryptographic keys, personally identifiable information — in `UserDefaults`, `SharedPreferences`, or plain SQLite rows is exactly the mistake that produces credential theft via backup extraction, filesystem forensics, or jailbreak/root-based attacks.

On iOS, the Keychain is a SQLite database (`keychain-2.db`) managed by the `securityd` daemon and stored outside the application's sandbox in a protected system location. Access to Keychain items is mediated by the Security framework through `SecItemAdd`, `SecItemCopyMatching`, `SecItemUpdate`, and `SecItemDelete`. Items stored with `kSecAttrAccessible` set to `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` are encrypted with a key derived from the user's passcode and bound to the device's UID, stored in the Secure Enclave. Even if the raw `keychain-2.db` file is extracted from a device backup (which is possible for unencrypted backups), the cryptographic material needed to decrypt its contents is physically inaccessible without the Secure Enclave of the original device. This is a hardware security guarantee, not a software policy.

```swift
import Security
import Foundation

struct KeychainManager {

    enum KeychainError: Error {
        case duplicateItem
        case itemNotFound
        case unexpectedData
        case unhandledError(OSStatus)
    }

    static func store(token: String, forAccount account: String) throws {
        guard let data = token.data(using: .utf8) else {
            throw KeychainError.unexpectedData
        }
        let query: [String: Any] = [
            kSecClass as String:            kSecClassGenericPassword,
            kSecAttrAccount as String:      account,
            kSecAttrAccessible as String:   kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
            kSecValueData as String:        data
        ]
        let status = SecItemAdd(query as CFDictionary, nil)
        if status == errSecDuplicateItem {
            try update(token: token, forAccount: account)
        } else if status != errSecSuccess {
            throw KeychainError.unhandledError(status)
        }
    }

    static func retrieve(forAccount account: String) throws -> String {
        let query: [String: Any] = [
            kSecClass as String:        kSecClassGenericPassword,
            kSecAttrAccount as String:  account,
            kSecReturnData as String:   true,
            kSecMatchLimit as String:   kSecMatchLimitOne
        ]
        var item: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &item)
        guard status == errSecSuccess else {
            if status == errSecItemNotFound { throw KeychainError.itemNotFound }
            throw KeychainError.unhandledError(status)
        }
        guard let data = item as? Data, let token = String(data: data, encoding: .utf8) else {
            throw KeychainError.unexpectedData
        }
        return token
    }

    private static func update(token: String, forAccount account: String) throws {
        guard let data = token.data(using: .utf8) else { throw KeychainError.unexpectedData }
        let query: [String: Any] = [
            kSecClass as String:        kSecClassGenericPassword,
            kSecAttrAccount as String:  account
        ]
        let attributes: [String: Any] = [kSecValueData as String: data]
        let status = SecItemUpdate(query as CFDictionary, attributes as CFDictionary)
        guard status == errSecSuccess else {
            throw KeychainError.unhandledError(status)
        }
    }

    static func delete(forAccount account: String) throws {
        let query: [String: Any] = [
            kSecClass as String:        kSecClassGenericPassword,
            kSecAttrAccount as String:  account
        ]
        let status = SecItemDelete(query as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else {
            throw KeychainError.unhandledError(status)
        }
    }
}
```

On Android, the equivalent hardware-backed system is the Android Keystore, which stores cryptographic key material in a Trusted Execution Environment (TEE) or dedicated secure hardware (StrongBox) and never allows that material to be exported from the secure boundary. You do not store raw secret values in the Keystore the way you store them in the iOS Keychain. Instead, you generate or import a symmetric key, and you use the EncryptedSharedPreferences or EncryptedFile abstractions from the Jetpack Security library, which handle the AES-256-GCM encryption and key management on your behalf:

```kotlin
import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

class SecureCredentialStore(context: Context) {

    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .setUserAuthenticationRequired(false)
        .build()

    private val encryptedPrefs = EncryptedSharedPreferences.create(
        context,
        "secure_credentials",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    fun storeAuthToken(token: String) {
        encryptedPrefs.edit()
            .putString(KEY_AUTH_TOKEN, token)
            .apply()
    }

    fun retrieveAuthToken(): String? {
        return encryptedPrefs.getString(KEY_AUTH_TOKEN, null)
    }

    fun clearCredentials() {
        encryptedPrefs.edit().clear().apply()
    }

    companion object {
        private const val KEY_AUTH_TOKEN = "auth_token"
    }
}
```

The key scheme `AES256_SIV` for key encryption provides deterministic encryption — the same plaintext preference key always produces the same ciphertext — which is necessary because `EncryptedSharedPreferences` must be able to look up values by their encrypted key name. The `AES256_GCM` scheme for values provides non-deterministic encryption with authentication, which is both necessary for semantic security (the same token stored twice produces different ciphertexts) and sufficient for data authentication (a tampered ciphertext fails MAC verification before decryption).

---

## 3. High-Performance Optimization & Failure Modes

### Schema Migration: The Most Dangerous Moment in Persistence

No aspect of mobile persistence causes more production incidents than schema migration. Unlike server-side databases where you can run a migration script on a managed fleet under controlled conditions, mobile schema migrations execute on millions of heterogeneous devices, running arbitrary versions of your app, upgrading through potentially non-linear version paths, with no network connection, no rollback mechanism, and the full expectation from the user that their data is intact when the app reopens. The constraints are severe enough that migration strategy must be a first-class design concern from day one, not a retrofitted afterthought.

The fundamental tension in mobile schema migration is between migration fidelity and migration time. A migration that transforms a denormalized text column into a normalized foreign key relationship might require reading every row, parsing the text, inserting into a new table, and updating the original row. On a table with five million rows on a three-year-old device, this migration might take twenty seconds during which the app is blocked and the user is staring at a launch screen. The practical solution is to design migrations as additive operations wherever possible. Adding a nullable column requires a single O(1) `ALTER TABLE` statement in SQLite, regardless of the number of rows in the table. Renaming a column in SQLite versions prior to 3.25.0 requires a full table rebuild. Splitting a table requires migrating data row by row.

The Room migration framework enforces explicit, versioned migration paths — if you bump `version` from 2 to 3 and don't provide a `Migration(2, 3)` object, the build may succeed but the runtime will throw an `IllegalStateException` when the database is first opened on a device running schema version 2. This is by design. Room also provides `fallbackToDestructiveMigration()` as an escape hatch for development environments, which drops and recreates the entire database when no migration path exists. Using this in a production build is equivalent to silently deleting all user data on upgrade — it is never acceptable unless the data is fully replaceable from a server and the user experience is designed around that assumption.

A production-grade migration strategy for a maturing application should adopt the expand-contract pattern. During the **expand** phase, you add new columns, tables, and indexes alongside the existing schema, never removing anything. The application code is deployed to write data in both the old and new formats simultaneously. During the **contract** phase — a subsequent release — you remove the deprecated columns and tables that are now fully replaced. This guarantees that rollbacks are safe (the previous app version still functions against the expanded schema) and that no single migration must perform a destructive transformation.

```kotlin
// Expand phase: add new columns, preserve old ones
val MIGRATION_3_4 = object : Migration(3, 4) {
    override fun migrate(database: SupportSQLiteDatabase) {
        // Add normalized sender table (expand)
        database.execSQL("""
            CREATE TABLE IF NOT EXISTS senders (
                id   TEXT PRIMARY KEY NOT NULL,
                name TEXT NOT NULL,
                avatar_url TEXT
            )
        """)
        // Add FK column to messages (nullable during transition)
        database.execSQL("ALTER TABLE messages ADD COLUMN sender_fk TEXT REFERENCES senders(id)")
        // Backfill new FK from existing denormalized sender_id column
        // This is safe because sender_id was always a stable string identifier
        database.execSQL("""
            INSERT OR IGNORE INTO senders (id, name, avatar_url)
            SELECT DISTINCT sender_id, sender_id, NULL FROM messages
        """)
        database.execSQL("UPDATE messages SET sender_fk = sender_id")
    }
}

// Contract phase: remove old column (requires table rebuild in SQLite)
val MIGRATION_4_5 = object : Migration(4, 5) {
    override fun migrate(database: SupportSQLiteDatabase) {
        // SQLite requires full table rebuild to drop a column
        database.execSQL("""
            CREATE TABLE messages_new (
                id          TEXT PRIMARY KEY NOT NULL,
                thread_id   TEXT NOT NULL,
                body        TEXT NOT NULL,
                created_at  INTEGER NOT NULL,
                is_read     INTEGER NOT NULL DEFAULT 0,
                sender_fk   TEXT NOT NULL REFERENCES senders(id)
            )
        """)
        database.execSQL("""
            INSERT INTO messages_new (id, thread_id, body, created_at, is_read, sender_fk)
            SELECT id, thread_id, body, created_at, is_read, sender_fk FROM messages
        """)
        database.execSQL("DROP TABLE messages")
        database.execSQL("ALTER TABLE messages_new RENAME TO messages")
        database.execSQL("""
            CREATE INDEX idx_messages_thread_created ON messages(thread_id, created_at DESC)
        """)
    }
}
```

This two-phase approach means that the contract migration — the expensive table rebuild — executes in a separate app release from the expand migration. Users who skip the intermediate release (which is common on mobile, where version adoption curves are notoriously long-tailed) will execute both migrations in sequence during a single cold start. You must account for this: test your migration chain from the oldest supported schema version to the current one, not just from N-1 to N.

### State Restoration Under Process Death

iOS and Android handle app lifecycle termination differently, but both platforms expect applications to restore their UI state seamlessly after the OS has killed the process. Getting this wrong produces one of the most user-visible bugs in mobile development: the user switches away from your app to take a phone call, returns three hours later, and instead of continuing where they left off, they're staring at an empty launch screen with their unsaved draft vanished.

On iOS, the state restoration system built into UIKit allows view controllers to encode their state into an `NSUserActivity` or via the `encodeRestorableState(with:)` / `decodeRestorableState(with:)` APIs. The key architectural principle is that state restoration should reconstruct the navigation stack and UI state from lightweight identifiers that point to durable data, not by serializing the entire object graph into the restoration archive. A message composition view controller should save the `threadId` it was composing into, the cursor position, and any unsaved draft text. It should reconstitute the thread data by querying the database using the restored `threadId`. Embedding entire model objects into the restoration archive is fragile because schema changes will break deserialization across app updates.

```swift
// iOS: NSUserActivity-based state restoration for a composition view

import UIKit

class MessageComposerViewController: UIViewController {

    var threadId: String?
    private var draftTextView = UITextView()

    override func viewDidLoad() {
        super.viewDidLoad()
        userActivity = NSUserActivity(activityType: "com.example.app.composeMessage")
        userActivity?.isEligibleForHandoff = false
        userActivity?.needsSave = true
    }

    override func updateUserActivityState(_ activity: NSUserActivity) {
        super.updateUserActivityState(activity)
        activity.addUserInfoEntries(from: [
            "threadId": threadId ?? "",
            "draftText": draftTextView.text ?? "",
            "cursorOffset": draftTextView.selectedRange.location
        ])
    }

    override func restoreUserActivityState(_ activity: NSUserActivity) {
        super.restoreUserActivityState(activity)
        guard let info = activity.userInfo else { return }
        threadId = info["threadId"] as? String
        let draftText = info["draftText"] as? String ?? ""
        let cursorOffset = info["cursorOffset"] as? Int ?? 0
        draftTextView.text = draftText
        if let pos = draftTextView.position(
            from: draftTextView.beginningOfDocument,
            offset: cursorOffset
        ) {
            draftTextView.selectedTextRange = draftTextView.textRange(from: pos, to: pos)
        }
    }
}
```

On Android, the equivalent mechanism is the `ViewModel` and `SavedStateHandle` combination. `ViewModel` survives configuration changes (screen rotation, theme changes) because it is scoped to the lifecycle of the entire Activity's backstage, not the Activity instance itself. `SavedStateHandle` extends this to survive process death by serializing its contents into the Activity's saved instance state Bundle, which the OS preserves even after killing the process. The key distinction is that only small, parcelable values should live in `SavedStateHandle` — identifiers, primitive UI state — while the actual content is loaded from the Room database using those identifiers.

```kotlin
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class MessageComposerViewModel(
    private val savedStateHandle: SavedStateHandle,
    private val messageDao: MessageDao
) : ViewModel() {

    // threadId survives both configuration changes and process death
    private val threadId: StateFlow<String?> = savedStateHandle.getStateFlow("thread_id", null)

    val messages: StateFlow<List<MessageEntity>> = threadId
        .flatMapLatest { id ->
            if (id != null) messageDao.observeMessages(id) else kotlinx.coroutines.flow.flowOf(emptyList())
        }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = emptyList()
        )

    // Draft text also survives process death via SavedStateHandle
    var draftText: String
        get() = savedStateHandle["draft_text"] ?: ""
        set(value) { savedStateHandle["draft_text"] = value }

    fun setThread(threadId: String) {
        savedStateHandle["thread_id"] = threadId
    }

    fun sendMessage(body: String) {
        val id = threadId.value ?: return
        viewModelScope.launch {
            val message = MessageEntity(
                id = java.util.UUID.randomUUID().toString(),
                threadId = id,
                body = body,
                createdAt = System.currentTimeMillis(),
                senderId = "current_user"
            )
            messageDao.insertMessages(listOf(message))
            draftText = ""
        }
    }
}
```

### Index Strategy and Query Performance Diagnosis

A SQLite database without correctly designed indexes is a database that scans every row on every query above a trivially small table size. The asymptotic behavior of a full table scan is O(N) where N is the number of rows, while a B-tree index lookup is O(log N). On a messages table with two million rows, the difference between a covered index query and a full table scan is roughly twenty-one comparisons versus two million row reads — a factor of approximately one hundred thousand in the best case. On a constrained mobile device with a limited page cache and slow flash I/O, this translates directly to query latencies that the user experiences as frozen UI.

The correct diagnostic tool for SQLite query performance is the `EXPLAIN QUERY PLAN` statement, which reveals what strategy the query planner chose without executing the query. The output tells you whether the planner selected a table scan (`SCAN TABLE messages`), a B-tree index search (`SEARCH TABLE messages USING INDEX`), or a covering index (where all columns needed by the query are present in the index itself, eliminating the need to touch the table at all). A covering index is the highest performance outcome because the planner can satisfy the entire query from the index pages without ever touching the table pages.

For the query pattern `SELECT id, body, created_at FROM messages WHERE thread_id = ? ORDER BY created_at DESC LIMIT 50`, the optimal index is a compound index on `(thread_id, created_at DESC)`. This index allows the planner to seek directly to the first entry matching the given `thread_id`, then scan the index entries in descending `created_at` order, applying the LIMIT without reading beyond the fiftieth row. Because `id` and `body` are not in the index, the planner must still perform a rowid lookup for each result row. Adding those columns to the index — `CREATE INDEX idx_covering ON messages(thread_id, created_at DESC, id, body)` — creates a covering index that eliminates the rowid lookup entirely. The tradeoff is increased index storage size and increased write cost, which is worthwhile for read-heavy query patterns on large tables.

You can run `EXPLAIN QUERY PLAN` from the command line against any SQLite file to validate your index strategy during development:

```bash
# Attach to the app's SQLite file extracted via adb or Xcode's device log
sqlite3 /path/to/app_database.db

sqlite> EXPLAIN QUERY PLAN
   ...> SELECT id, body, created_at
   ...> FROM messages
   ...> WHERE thread_id = 'thread_abc'
   ...> ORDER BY created_at DESC
   ...> LIMIT 50;

-- Expected output with correct index:
-- QUERY PLAN
-- `--SEARCH TABLE messages USING INDEX idx_messages_thread_created (thread_id=?)

sqlite> .quit
```

If the output shows `SCAN TABLE messages` instead, the planner either found no applicable index or determined that the selectivity of the predicate was too low to make the index beneficial — which can happen when the statistics in `sqlite_stat1` are stale. Running `ANALYZE` after bulk inserts refreshes these statistics and can cause the planner to adopt a more efficient strategy.

### Write Amplification and Transaction Batching

The final failure mode that consistently manifests in production systems is unbatched writes. An application that inserts one hundred messages into SQLite using one hundred individual `INSERT` statements wrapped in one hundred separate implicit transactions will pay the full transaction overhead — journal write, data write, fsync on the WAL frame, WAL file growth — one hundred times. The same one hundred inserts wrapped in a single explicit `BEGIN TRANSACTION` / `COMMIT` block pay that overhead exactly once. On a modern device this is the difference between approximately five hundred milliseconds and five milliseconds.

The pattern emerges subtly in systems that process streaming data: a background sync operation that receives a paginated API response and inserts each page's worth of records one-by-one inside a loop. The fix is mechanically simple — accumulate the records across all pages and commit the entire batch in a single transaction — but it requires the developer to understand that the implicit transaction overhead exists and is non-trivial. For Room, this means collecting all `MessageEntity` objects into a list and calling `insertMessages(messages)` once rather than iterating and calling `insertMessage(message)` in a loop. For raw SQLite, it means explicit transaction management around any loop that issues write statements.

Write batching also interacts with Realm's notification system in a consequential way. If you insert one hundred objects in one hundred separate write transactions, Realm fires its change notification mechanism one hundred times, and any registered observer (a `Results` collection bound to a table view, for example) will receive one hundred invalidation signals, each triggering a UI diff and reload. A single write transaction containing all one hundred objects produces a single notification with a precisely computed diff of exactly which index paths were inserted — a vastly more efficient path through the UI update machinery.

These patterns — batched writes, covering indexes, additive migrations, secure credential storage, and type-safe query layers — are not independent optimizations. They are the interlocking practices of an engineering discipline that treats persistence as the structural invariant of the application rather than an implementation detail. The state your application manages outlives every version of the code that created it, and every architectural decision you make about how that state is stored, migrated, and secured is a commitment that your users will hold you to for as long as they carry your app on their device.
