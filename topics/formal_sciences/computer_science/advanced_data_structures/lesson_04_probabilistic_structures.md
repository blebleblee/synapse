# Lesson 04: Probabilistic Data Structures

## 1. First-Principles Intuition & Invariants

### 1.1 The Fundamental Trade-off

Probabilistic data structures abandon the guarantee of exactness in exchange for dramatic improvements in space efficiency and time complexity. This trade-off rests on a mathematical foundation: by accepting controlled uncertainty, we can represent information using space logarithmically or even sublinearly smaller than deterministic alternatives.

**Core Principle**: Use randomization and hashing to distribute information across a compact representation, accepting false positives (but never false negatives in certain structures) with quantifiable probability bounds.

**Mathematical Invariant**: For a probabilistic structure with error rate ε and input size n, space complexity typically scales as O(n log(1/ε)), independent of the universe size from which elements are drawn.

### 1.2 Information-Theoretic Limits

Consider the membership testing problem: determining whether an element belongs to a set S of n elements drawn from universe U where |U| >> n.

**Deterministic lower bound**: Perfect accuracy requires Ω(n log |U|) bits to distinguish between all possible sets.

**Probabilistic breakthrough**: With acceptable error probability ε, we need only Ω(n log(1/ε)) bits—completely independent of universe size.

This separation is profound: a Bloom filter testing membership in a set of 1 billion elements with 1% false positive rate requires approximately 1.2 GB, whether those elements are 32-bit integers or 256-bit cryptographic hashes.

### 1.3 Hash Function Role and Properties

Probabilistic structures depend critically on hash functions that approximate true randomness:

**Required properties**:
- **Uniformity**: Hash values must be uniformly distributed across output space
- **Independence**: Multiple hash functions (or derived hash values) must be pairwise independent
- **Determinism**: Same input always produces same output

**Practical reality**: True independence is computationally expensive. Most implementations use variants of the "double hashing" technique: h_i(x) = h1(x) + i·h2(x), trading theoretical independence for practical efficiency.

### 1.4 The Four Canonical Problems

Probabilistic structures address four fundamental query types:

1. **Membership testing**: "Is x in set S?" (Bloom filters, Cuckoo filters)
2. **Cardinality estimation**: "How many distinct elements have we seen?" (HyperLogLog, MinCount)
3. **Frequency estimation**: "How many times have we seen x?" (Count-Min Sketch, Count Sketch)
4. **Similarity estimation**: "How similar are sets A and B?" (MinHash, SimHash)

Each problem has an information-theoretic lower bound that probabilistic structures approach asymptotically.

## 2. Core Architecture & Mechanics

### 2.1 Bloom Filters

**Architecture**: A Bloom filter consists of:
- Bit array M of length m, initially all zeros
- k independent hash functions h₁, h₂, ..., h_k mapping elements to [0, m-1]

**Insertion protocol**:
```text
Insert(x):
    for i = 1 to k:
        M[h_i(x)] = 1
```

**Query protocol**:
```text
Query(x):
    for i = 1 to k:
        if M[h_i(x)] = 0:
            return False  // Definitely not in set
    return True          // Probably in set
```

**Mathematical analysis**:

After inserting n elements, the probability that a specific bit remains 0 is:

```text
P(bit = 0) = (1 - 1/m)^(kn) ≈ e^(-kn/m)
```

False positive probability for a query on element not in set:

```text
P(false positive) = (1 - e^(-kn/m))^k
```

**Optimal parameter selection**:

Given n elements and desired false positive rate ε:

```text
m = -n ln(ε) / (ln 2)²  ≈ 1.44 n log₂(1/ε)
k = (m/n) ln 2          ≈ 0.693 m/n
```

With optimal k, false positive rate becomes ε = (0.6185)^(m/n).

**Critical invariant**: Bloom filters guarantee no false negatives. If Query(x) returns False, x was definitely not inserted. This asymmetry is foundational to their utility.

### 2.2 Count-Min Sketch

**Architecture**: 
- Two-dimensional array C of dimensions d × w (depth × width)
- d independent hash functions h₁, h₂, ..., h_d mapping elements to [0, w-1]

**Update protocol**:
```text
Update(x, count):
    for i = 1 to d:
        C[i, h_i(x)] += count
```

**Query protocol**:
```text
Query(x):
    return min(C[i, h_i(x)] for i = 1 to d)
```

**Mathematical guarantees**:

With probability at least 1 - δ:

```text
count(x) ≤ Query(x) ≤ count(x) + ε·N
```

where N is the sum of all counts, given:

```text
w = ⌈e/ε⌉
d = ⌈ln(1/δ)⌉
```

**Intuition**: Each row provides an independent estimate of count(x), but hash collisions cause overestimation. The minimum across rows gives the tightest upper bound because it's least affected by collisions.

**Space complexity**: O((1/ε) log(1/δ)), independent of universe size or number of distinct elements.

### 2.3 HyperLogLog

**Architecture**:
- Array M of m registers (typically m = 2^b for some b)
- Hash function h producing uniform bit strings

**Algorithmic insight**: Uses the position of the first 1-bit in hashed values as a geometric distribution proxy for cardinality.

**Update protocol**:
```text
Add(x):
    v = h(x)                          // Hash to uniform bit string
    j = first_b_bits(v)               // Register index
    w = remaining_bits(v)
    M[j] = max(M[j], ρ(w))           // ρ(w) = position of first 1-bit
```

**Estimation protocol**:
```text
Estimate():
    raw_estimate = α_m · m² / Σ(2^(-M[j]))
    return apply_bias_correction(raw_estimate)
```

where α_m is a correction constant (α₁₆ ≈ 0.673, α₃₂ ≈ 0.697, α₆₄ ≈ 0.709, α_∞ = 1/(2 ln 2) ≈ 0.721).

**Mathematical foundation**:

The probability that ρ(h(x)) ≥ k is exactly 2^(-k). If we've seen n distinct elements, we expect:
- ~n/2 to have ρ ≥ 1
- ~n/4 to have ρ ≥ 2
- ~n/2^k to have ρ ≥ k

Maximum observed ρ grows as log₂(n). By partitioning into m registers and using harmonic mean, standard error becomes:

```text
σ = 1.04/√m
```

**Space-accuracy trade-off**: For 1% standard error, need only 10,000 registers × log₂(log₂(N)) bits, regardless of actual cardinality N.

### 2.4 Cuckoo Filters

**Architecture**:
- Array of b buckets, each holding up to s entries (typically s = 4)
- Two hash functions h₁(x) and h₂(x), or derived positions
- Each entry stores a fingerprint f(x) of c bits (typically c = 8 to 16)

**Key innovation**: Partial-key cuckoo hashing with the relocatable property:

```text
h₁(x) = hash(x)
h₂(x) = h₁(x) ⊕ hash(f(x))
```

This allows computing alternate position from fingerprint alone:

```text
alternate_index(i, f) = i ⊕ hash(f)
```

**Insertion protocol**:
```text
Insert(x):
    f = fingerprint(x)
    i₁ = h₁(x)
    i₂ = h₂(x)
    
    if bucket[i₁] or bucket[i₂] has space:
        add f to available bucket
        return True
    
    // Both buckets full - evict and relocate
    i = random_choice(i₁, i₂)
    for n iterations:
        randomly swap f with entry in bucket[i]
        i = alternate_index(i, f)
        if bucket[i] has space:
            add f to bucket[i]
            return True
    
    return False  // Filter full, need rebuild
```

**Query protocol**:
```text
Query(x):
    f = fingerprint(x)
    return f in bucket[h₁(x)] or f in bucket[h₂(x)]
```

**Deletion support**: Unlike Bloom filters, Cuckoo filters support deletion:

```text
Delete(x):
    f = fingerprint(x)
    if f in bucket[h₁(x)]:
        remove one copy of f from bucket[h₁(x)]
        return True
    if f in bucket[h₂(x)]:
        remove one copy of f from bucket[h₂(x)]
        return True
    return False
```

**False positive analysis**:

With c-bit fingerprints and load factor α:

```text
P(false positive) ≈ 2α/2^c
```

For 8-bit fingerprints at 95% load: ε ≈ 0.74%.

**Space efficiency**: Requires approximately 1.05 bits per element per 1% false positive rate, improving on Bloom filters (1.44 bits) while supporting deletions.

### 2.5 MinHash for Similarity Estimation

**Problem formulation**: Estimate Jaccard similarity J(A, B) = |A ∩ B| / |A ∪ B| for sets A and B.

**Architecture**:
- k independent hash functions h₁, h₂, ..., h_k mapping elements to comparable space
- For each set, store k signature values (minimum hash values)

**Signature construction**:
```text
CreateSignature(S):
    sig = []
    for i = 1 to k:
        sig[i] = min(h_i(x) for x in S)
    return sig
```

**Similarity estimation**:
```text
EstimateSimilarity(sig_A, sig_B):
    matches = count(i where sig_A[i] = sig_B[i])
    return matches / k
```

**Mathematical foundation**:

For any hash function h and sets A, B:

```text
P(min(h(A)) = min(h(B))) = |A ∩ B| / |A ∪ B| = J(A, B)
```

**Proof sketch**: The minimum hash value in A ∪ B comes from A ∩ B with probability |A ∩ B|/|A ∪ B|, and in that case, it's the minimum for both sets.

**Error bounds**: With k hash functions, estimated similarity J' has expected value J and standard error:

```text
σ = √(J(1-J)/k)
```

For 1% standard error estimating J ≈ 0.5, need k ≈ 2500 hash functions.

**Locality-Sensitive Hashing (LSH) application**: Group signature values into bands to create hash buckets where similar items collide with high probability while dissimilar items rarely collide.

## 3. High-Performance Implementation & Failure Modes

### 3.1 Hash Function Implementation

**Production requirements**:

1. **Speed**: Hash computation often dominates runtime
2. **Quality**: Poor distribution multiplies error rates
3. **Portability**: Results must be consistent across platforms

**Recommended choices**:

```c++
// Modern high-quality, fast hash functions
#include <cstdint>

// MurmurHash3 - excellent balance of speed and quality
uint32_t murmur3_32(const uint8_t* key, size_t len, uint32_t seed);

// xxHash - faster, good distribution
uint64_t xxhash64(const uint8_t* data, size_t len, uint64_t seed);

// For cryptographic applications requiring strong guarantees
uint64_t siphash(const uint8_t* data, size_t len, const uint8_t key[16]);
```

**Double hashing implementation**:

```c++
// Generate k hash values from two base hashes
class DoubleHasher {
    uint64_t h1, h2;
    uint32_t m;  // Table size
    
public:
    DoubleHasher(const void* key, size_t len, uint32_t table_size) 
        : m(table_size) {
        uint64_t hash[2];
        MurmurHash3_x64_128(key, len, 0, hash);
        h1 = hash[0];
        h2 = hash[1];
    }
    
    uint32_t get_hash(uint32_t i) const {
        return (h1 + i * h2) % m;
    }
};
```

**Critical warning**: Modulo bias matters. For power-of-two sizes, use bitwise AND. For arbitrary sizes with strong uniformity requirements, use rejection sampling or multiplication method.

### 3.2 Production Bloom Filter

```c++
class BloomFilter {
    std::vector<uint64_t> bits;  // Use 64-bit words for efficient access
    uint64_t m;                   // Bit array size
    uint32_t k;                   // Number of hash functions
    uint64_t n_inserted;          // Track actual insertions
    
    static constexpr uint64_t WORD_BITS = 64;
    
    uint32_t optimal_k(uint64_t m, uint64_t n) const {
        return std::max(1u, static_cast<uint32_t>(
            std::round((m / static_cast<double>(n)) * std::log(2))
        ));
    }
    
public:
    // Constructor with false positive rate
    BloomFilter(uint64_t expected_elements, double fpr) 
        : n_inserted(0) {
        m = std::ceil(-expected_elements * std::log(fpr) / 
                      (std::log(2) * std::log(2)));
        k = optimal_k(m, expected_elements);
        bits.resize((m + WORD_BITS - 1) / WORD_BITS, 0);
    }
    
    void insert(const void* key, size_t len) {
        uint64_t h[2];
        MurmurHash3_x64_128(key, len, 0, h);
        
        for (uint32_t i = 0; i < k; ++i) {
            uint64_t pos = (h[0] + i * h[1]) % m;
            bits[pos / WORD_BITS] |= (1ULL << (pos % WORD_BITS));
        }
        ++n_inserted;
    }
    
    bool query(const void* key, size_t len) const {
        uint64_t h[2];
        MurmurHash3_x64_128(key, len, 0, h);
        
        for (uint32_t i = 0; i < k; ++i) {
            uint64_t pos = (h[0] + i * h[1]) % m;
            if ((bits[pos / WORD_BITS] & (1ULL << (pos % WORD_BITS))) == 0) {
                return false;
            }
        }
        return true;
    }
    
    double current_fpr() const {
        // Estimate actual FPR based on bit saturation
        uint64_t set_bits = 0;
        for (uint64_t word : bits) {
            set_bits += __builtin_popcountll(word);
        }
        double saturation = set_bits / static_cast<double>(m);
        return std::pow(saturation, k);
    }
    
    // Serialization support
    std::vector<uint8_t> serialize() const {
        std::vector<uint8_t> data;
        // Header: m, k, n_inserted
        // Body: bit array
        // Implementation details omitted for brevity
        return data;
    }
};
```

**Performance optimizations**:

1. **SIMD operations**: For large filters, vectorize bit checking across multiple positions simultaneously
2. **Cache-aware layout**: Group bits likely to be accessed together
3. **Blocked Bloom filters**: Divide into cache-line-sized blocks to improve locality

### 3.3 Production Count-Min Sketch

```c++
class CountMinSketch {
    std::vector<std::vector<uint64_t>> counts;
    uint32_t depth;   // d
    uint32_t width;   // w
    uint64_t total;   // N
    
public:
    CountMinSketch(double epsilon, double delta) {
        width = std::ceil(std::exp(1.0) / epsilon);
        depth = std::ceil(std::log(1.0 / delta));
        counts.resize(depth, std::vector<uint64_t>(width, 0));
        total = 0;
    }
    
    void update(const void* key, size_t len, int64_t count) {
        if (count < 0 && total < static_cast<uint64_t>(-count)) {
            // Handle underflow
            throw std::runtime_error("Negative count would underflow");
        }
        
        for (uint32_t i = 0; i < depth; ++i) {
            uint64_t hash = xxhash64(
                static_cast<const uint8_t*>(key), len, i
            );
            uint32_t pos = hash % width;
            
            if (count > 0) {
                counts[i][pos] += count;
            } else {
                counts[i][pos] -= (-count);
            }
        }
        total += count;
    }
    
    uint64_t query(const void* key, size_t len) const {
        uint64_t min_count = UINT64_MAX;
        
        for (uint32_t i = 0; i < depth; ++i) {
            uint64_t hash = xxhash64(
                static_cast<const uint8_t*>(key), len, i
            );
            uint32_t pos = hash % width;
            min_count = std::min(min_count, counts[i][pos]);
        }
        
        return min_count;
    }
    
    // Heavy hitters: elements with count > threshold
    std::vector<std::pair<uint64_t, uint64_t>> heavy_hitters(
        double threshold
    ) const {
        // Requires additional tracking structure (e.g., heap)
        // Implementation depends on specific use case
        return {};
    }
    
    // Point query with error bound
    std::pair<uint64_t, uint64_t> query_with_bound(
        const void* key, size_t len
    ) const {
        uint64_t estimate = query(key, len);
        double epsilon = std::exp(1.0) / width;
        uint64_t error_bound = std::ceil(epsilon * total);
        return {estimate, error_bound};
    }
};
```

**Conservative Update variant**:

To reduce overestimation for point queries, use conservative update:

```c++
void conservative_update(const void* key, size_t len, int64_t count) {
    // First find minimum current value
    uint64_t min_val = query(key, len);
    
    // Only update counters at or below minimum + count
    for (uint32_t i = 0; i < depth; ++i) {
        uint64_t hash = xxhash64(
            static_cast<const uint8_t*>(key), len, i
        );
        uint32_t pos = hash % width;
        counts[i][pos] = std::max(counts[i][pos], min_val + count);
    }
}
```

This maintains theoretical guarantees while improving practical accuracy.

### 3.4 Production HyperLogLog

```c++
class HyperLogLog {
    std::vector<uint8_t> registers;
    uint8_t precision;  // b in [4, 16]
    uint32_t m;         // 2^b
    double alpha_m;
    
    static uint8_t count_leading_zeros(uint64_t val, uint8_t max_bits) {
        if (val == 0) return max_bits;
        return std::min(static_cast<uint8_t>(__builtin_clzll(val) + 1), 
                       max_bits);
    }
    
    static double compute_alpha(uint32_t m) {
        if (m >= 128) return 0.7213 / (1.0 + 1.079 / m);
        if (m >= 64) return 0.709;
        if (m >= 32) return 0.697;
        if (m >= 16) return 0.673;
        return 0.5;  // Not recommended
    }
    
public:
    explicit HyperLogLog(uint8_t precision) 
        : precision(precision), m(1u << precision) {
        if (precision < 4 || precision > 16) {
            throw std::invalid_argument("Precision must be in [4, 16]");
        }
        registers.resize(m, 0);
        alpha_m = compute_alpha(m);
    }
    
    void add(const void* key, size_t len) {
        uint64_t hash = xxhash64(
            static_cast<const uint8_t*>(key), len, 0
        );
        
        // First b bits select register
        uint32_t j = hash & ((1u << precision) - 1);
        
        // Remaining bits used for leading zero count
        uint64_t w = hash >> precision;
        uint8_t leading_zeros = count_leading_zeros(w, 64 - precision);
        
        registers[j] = std::max(registers[j], leading_zeros);
    }
    
    uint64_t estimate() const {
        double raw_estimate = compute_raw_estimate();
        
        // Small range correction
        if (raw_estimate <= 2.5 * m) {
            uint32_t zeros = std::count(registers.begin(), 
                                       registers.end(), 0);
            if (zeros != 0) {
                return std::round(m * std::log(m / static_cast<double>(zeros)));
            }
        }
        
        // Large range correction (2^32 threshold)
        if (raw_estimate > (1ULL << 32) / 30.0) {
            return std::round(-4294967296.0 * std::log(1.0 - raw_estimate / 4294967296.0));
        }
        
        return std::round(raw_estimate);
    }
    
    double compute_raw_estimate() const {
        double sum = 0.0;
        for (uint8_t reg : registers) {
            sum += std::pow(2.0, -reg);
        }
        return alpha_m * m * m / sum;
    }
    
    // Merge with another HLL (for distributed counting)
    void merge(const HyperLogLog& other) {
        if (precision != other.precision) {
            throw std::invalid_argument("Cannot merge HLLs with different precision");
        }
        for (uint32_t i = 0; i < m; ++i) {
            registers[i] = std::max(registers[i], other.registers[i]);
        }
    }
    
    double relative_error() const {
        return 1.04 / std::sqrt(m);
    }
};
```

**HyperLogLog++ improvements**:

1. **Sparse representation**: For low cardinalities, store only non-zero registers in sorted list
2. **64-bit hash function**: Extends range before large corrections needed
3. **Empirical bias correction**: Use lookup tables derived from Monte Carlo simulation

### 3.5 Failure Modes and Mitigation

**Bloom Filter saturation**:

```text
Symptom: False positive rate increases beyond design target
Cause: Inserted more elements than capacity (n >> expected_n)
Detection: Monitor bit saturation ratio
Mitigation: Rebuild with larger filter or implement scaling Bloom filter
```

Scaling Bloom filter implementation:

```c++
class ScalingBloomFilter {
    std::vector<std::unique_ptr<BloomFilter>> filters;
    uint64_t base_size;
    double fpr;
    double scale_factor;
    
public:
    ScalingBloomFilter(uint64_t initial_size, double fpr, 
                       double scale = 2.0)
        : base_size(initial_size), fpr(fpr), scale_factor(scale) {
        add_filter();
    }
    
    void add_filter() {
        uint64_t size = base_size * std::pow(scale_factor, filters.size());
        // Tighten FPR for each layer to maintain overall FPR
        double layer_fpr = fpr * std::pow(0.5, filters.size() + 1);
        filters.push_back(
            std::make_unique<BloomFilter>(size, layer_fpr)
        );
    }
    
    void insert(const void* key, size_t len) {
        auto& current = filters.back();
        if (current->current_fpr() > fpr * 0.5) {
            add_filter();
        }
        filters.back()->insert(key, len);
    }
    
    bool query(const void* key, size_t len) const {
        for (const auto& filter : filters) {
            if (filter->query(key, len)) return true;
        }
        return false;
    }
};
```

**Hash function collision attacks**:

```text
Symptom: Degraded performance or inflated error rates
Cause: Adversarial input designed to cause hash collisions
Detection: Monitor distribution statistics
Mitigation: Use cryptographic hash (SipHash) with secret key
```

**Count-Min Sketch underflow**:

```text
Symptom: Negative counts or incorrect decrements
Cause: Deleting elements never inserted, or hash collision with actual elements
Detection: Check for negative values (impossible in uint representation)
Mitigation: Use signed integers and validate operations, or use Count Sketch variant
```

**HyperLogLog precision mismatch**:

```text
Symptom: Cannot merge HLL instances
Cause: Different precision parameters across distributed components
Detection: Explicit precision check before merge
Mitigation: Standardize precision across system, or implement precision conversion
```

**Cuckoo filter insertion failure**:

```text
Symptom: Insert returns false despite low load factor
Cause: Pathological hash patterns create local clustering
Detection: Track insertion failure rate
Mitigation: Rebuild with new hash seed, or implement automatic rehashing
```

**Memory alignment issues**:

```text
Symptom: Performance degradation or crashes on certain architectures
Cause: Unaligned memory access in bit manipulation
Detection: Address sanitizer, valgrind
Mitigation: Ensure word-aligned access, use std::aligned_alloc
```

### 3.6 Testing and Validation

**Statistical validation framework**:

```c++
class ProbabilisticStructureTest {
public:
    struct TestResult {
        double theoretical_error;
        double measured_error;
        double confidence_interval;
        bool passed;
    };
    
    static TestResult validate_bloom_filter(
        uint64_t n, double target_fpr, uint32_t trials = 10000
    ) {
        BloomFilter bf(n, target_fpr);
        
        // Insert n random elements, track them
        std::unordered_set<uint64_t> inserted;
        for (uint64_t i = 0; i < n; ++i) {
            uint64_t val = random_uint64();
            bf.insert(&val, sizeof(val));
            inserted.insert(val);
        }
        
        // Test false positive rate
        uint32_t false_positives = 0;
        for (uint32_t i = 0; i < trials; ++i) {
            uint64_t val = random_uint64();
            if (inserted.count(val) == 0 && bf.query(&val, sizeof(val))) {
                ++false_positives;
            }
        }
        
        double measured_fpr = false_positives / static_cast<double>(trials);
        double std_error = std::sqrt(target_fpr * (1 - target_fpr) / trials);
        double confidence = 2.576 * std_error;  // 99% CI
        
        return {
            target_fpr,
            measured_fpr,
            confidence,
            std::abs(measured_fpr - target_fpr) <= confidence
        };
    }
    
    static TestResult validate_hyperloglog(
        uint8_t precision, uint64_t cardinality
    ) {
        HyperLogLog hll(precision);
        
        for (uint64_t i = 0; i < cardinality; ++i) {
            hll.add(&i, sizeof(i));
        }
        
        uint64_t estimate = hll.estimate();
        double relative_error = std::abs(
            static_cast<double>(estimate) / cardinality - 1.0
        );
        double theoretical_error = hll.relative_error();
        
        // Should be within 3 standard errors with high probability
        return {
            theoretical_error,
            relative_error,
            3 * theoretical_error,
            relative_error <= 3 * theoretical_error
        };
    }
};
```

**Benchmark framework**:

```c++
struct BenchmarkResults {
    double insert_ns;
    double query_ns;
    size_t memory_bytes;
    double actual_error;
};

template<typename Structure>
BenchmarkResults benchmark_structure(
    Structure& structure,
    const std::vector<uint64_t>& elements,
    uint32_t query_trials = 100000
) {
    auto start = std::chrono::high_resolution_clock::now();
    
    for (uint64_t elem : elements) {
        structure.insert(&elem, sizeof(elem));
    }
    
    auto insert_end = std::chrono::high_resolution_clock::now();
    
    for (uint32_t i = 0; i < query_trials; ++i) {
        uint64_t elem = elements[i % elements.size()];
        volatile bool result = structure.query(&elem, sizeof(elem));
        (void)result;
    }
    
    auto query_end = std::chrono::high_resolution_clock::now();
    
    double insert_time = std::chrono::duration<double, std::nano>(
        insert_end - start
    ).count() / elements.size();
    
    double query_time = std::chrono::duration<double, std::nano>(
        query_end - insert_end
    ).count() / query_trials;
    
    return {
        insert_time,
        query_time,
        structure.memory_usage(),
        structure.measured_error()
    };
}
```

## 4. Summary & Verification Matrix

### 4.1 Comparative Analysis

| Structure | Space | Insert | Query | Deletions | False Positives | False Negatives |
|-----------|-------|--------|-------|-----------|-----------------|-----------------|
| Bloom Filter | O(n log(1/ε)) | O(k) | O(k) | No | ε | Never |
| Cuckoo Filter | O(n log(1/ε)) | O(k) amortized | O(1) | Yes | ε | Never |
| Count-Min Sketch | O((1/ε) log(1/δ)) | O(log(1/δ)) | O(log(1/δ)) | Yes* | N/A | N/A |
| HyperLogLog | O(ε⁻² log log(n)) | O(1) | O(m) | N/A | N/A | N/A |
| MinHash | O(k log(n)) | O(k) | O(k) | Rebuild | N/A | N/A |

*Count-Min Sketch supports decrements but can accumulate error

### 4.2 Selection Criteria Decision Tree

**Membership testing**:
- Need deletions? → Cuckoo Filter
- Never delete, minimal space? → Bloom Filter
- Deletions rare, cryptographic resistance? → Blocked Bloom Filter with rebuild

**Frequency estimation**:
- Guaranteed overestimate acceptable? → Count-Min Sketch
- Need unbiased estimates? → Count Sketch (bidirectional)
- Heavy hitters only? → Space-Saving Algorithm + Count-Min

**Cardinality estimation**:
- Single machine? → HyperLogLog
- Distributed merging required? → HyperLogLog with merge support
- Extremely low memory? → LogLog or MinCount

**Set similarity**:
- Full pairwise comparison? → MinHash with LSH
- Continuous streaming? → SimHash
- Weighted Jaccard? → Weighted MinHash

### 4.3 Parameter Selection Guidelines

**Bloom Filter sizing**:
```text
Given: n elements, target FPR ε
Calculate:
    m = ⌈-n ln(ε) / (ln 2)²⌉ bits
    k = ⌈(m/n) ln 2⌉ hash functions
    
Example: n=1M, ε=0.01
    m ≈ 9.6M bits ≈ 1.2 MB
    k ≈ 7 hash functions
```

**Count-Min Sketch sizing**:
```text
Given: accuracy ε, confidence 1-δ
Calculate:
    w = ⌈e/ε⌉ counters wide
    d = ⌈ln(1/δ)⌉ rows deep
    
Example: ε=0.001, δ=0.05
    w ≈ 2718 counters
    d = 3 rows
    Total: ~32 KB (uint32_t counters)
```

**HyperLogLog sizing**:
```text
Given: target relative error σ
Calculate:
    m = ⌈(1.04/σ)²⌉ registers
    b = ⌈log₂(m)⌉ precision bits
    
Example: σ=0.01 (1%)
    m ≈ 10,816 → use m=16,384 (2¹⁴)
    b = 14
    Memory: 16 KB (6-bit registers)
```

**Cuckoo Filter sizing**:
```text
Given: n elements, target FPR ε, load factor α
Calculate:
    fingerprint_bits = ⌈log₂(1/ε) + log₂(2α)⌉
    num_buckets = ⌈n/(α·bucket_size)⌉
    
Example: n=1M, ε=0.01, α=0.95, bucket_size=4
    fingerprint_bits = 8
    num_buckets ≈ 263,158
    Memory: ~2.1 MB
```

### 4.4 Verification Checklist

**Implementation validation**:
- [ ] Hash function quality verified (chi-square test, avalanche)
- [ ] Parameter calculations match theoretical requirements
- [ ] No integer overflow in size calculations
- [ ] Memory allocation checked for alignment requirements
- [ ] Serialization format documented and versioned

**Correctness testing**:
- [ ] False positive rate within confidence intervals
- [ ] No false negatives (for membership structures)
- [ ] Error bounds hold under Monte Carlo testing
- [ ] Deletion correctness verified (if supported)
- [ ] Merge correctness verified (if supported)

**Performance validation**:
- [ ] Insert/query latency measured and documented
- [ ] Memory usage matches theoretical predictions
- [ ] Cache miss rates analyzed for hot paths
- [ ] Concurrent access patterns tested (if applicable)
- [ ] Serialization/deserialization overhead measured

**Robustness testing**:
- [ ] Behavior under saturation documented
- [ ] Hash collision resistance validated
- [ ] Numerical stability checked (no underflow/overflow)
- [ ] Error accumulation measured for long-running instances
- [ ] Recovery mechanisms implemented for failure modes

### 4.5 Advanced Topics and Extensions

**Learned probabilistic structures**:

Recent research combines machine learning with probabilistic structures. Learned Bloom filters use ML models to predict set membership, falling back to traditional Bloom filter only for uncertain cases. This can reduce false positive rates by 30-70% for clustered data distributions.

**Streaming algorithms**:

Count-Min Sketch extends to quantile estimation (q-digest), entropy estimation (sketch-based), and graph stream processing. The core insight—maintaining compressed summaries with bounded error—applies broadly.

**Quantum probabilistic structures**:

Quantum Bloom filters achieve quadratic space savings using quantum superposition, though practical implementations remain theoretical.

**Differential privacy**:

Adding calibrated noise to probabilistic structures (particularly sketches) enables privacy-preserving analytics. The inherent approximation provides natural privacy amplification.

### 4.6 Production Deployment Considerations

**Monitoring and observability**:

```python
class ProbabilisticStructureMetrics:
    """Metrics to expose for monitoring"""
    
    def __init__(self, structure):
        self.structure = structure
        self.metrics = {
            'size_bytes': structure.memory_usage(),
            'elements_inserted': structure.count(),
            'theoretical_error': structure.theoretical_error(),
            'saturation_ratio': structure.saturation(),
            'collision_rate': 0.0  # Requires instrumentation
        }
    
    def update_metrics(self):
        # Update metrics periodically
        self.metrics['size_bytes'] = self.structure.memory_usage()
        self.metrics['elements_inserted'] = self.structure.count()
        
        # Alert if saturation exceeds threshold
        if self.metrics['saturation_ratio'] > 0.8:
            alert("Probabilistic structure near capacity")
```

**Versioning and migration**:

Serialize format version and parameters with the data structure to enable safe deserialization and migration paths when upgrading to improved algorithms.

**Distributed considerations**:

For distributed systems, choose structures that support commutativity (HyperLogLog merge, Count-Min Sketch addition). Implement coordination-free aggregation where possible.

**Cost-benefit analysis**:

Before deploying, quantify the trade-off:
- Memory saved vs. deterministic structure
- Error rate impact on downstream decisions
- Performance improvement vs. implementation complexity

Probabilistic structures excel when exact answers are unnecessary and approximate answers suffice for decision-making within acceptable error bounds.
