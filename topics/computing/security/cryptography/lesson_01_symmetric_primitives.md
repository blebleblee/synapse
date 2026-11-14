# Lesson 1: Symmetric Cryptography Primitives

## 1. First-Principles Intuition & Invariants

Cryptography, at its mechanical core, is the science of constructing functions that are easy to compute in one direction and computationally intractable to reverse without auxiliary secret information. Symmetric cryptography narrows this further: a single secret key both encrypts and decrypts, binding two parties together through shared state that an adversary must not possess. Understanding why symmetric primitives are designed the way they are requires beginning not with algorithms but with the adversarial model they were built to defeat.

The canonical adversary in modern symmetric cryptography is defined by the **IND-CPA** security notion — indistinguishability under chosen-plaintext attack. In this game, an adversary submits plaintexts of her choosing to an encryption oracle and receives ciphertexts in return. After polynomially many queries, she submits two messages of equal length and receives one encrypted at random. She wins if she can correctly identify which plaintext was encrypted with advantage non-negligibly greater than 1/2. A symmetric cipher is IND-CPA secure if no probabilistic polynomial-time adversary can win this game. This formalism has direct engineering consequences: any deterministic cipher encrypting the same plaintext to the same ciphertext is immediately IND-CPA broken, because the adversary simply re-encrypts her two challenge messages and matches the output. This is precisely why the Electronic Codebook mode of AES fails in practice, and why randomized IV-based modes exist.

The two structural pillars of block cipher design were articulated by Claude Shannon in his 1949 paper *Communication Theory of Secrecy Systems*: **confusion** and **diffusion**. Confusion describes the property that the relationship between the key and ciphertext should be as complex and non-linear as possible. Diffusion describes the property that each plaintext bit should influence as many ciphertext bits as possible, spreading statistical structure across the output. These are not abstract ideals but measurable constraints. A good S-box — the confusion engine of AES and DES — achieves nonlinearity close to the theoretical maximum for its input width, ensuring that linear and differential cryptanalysis find no exploitable algebraic shortcut. A good diffusion layer — the MixColumns and ShiftRows operations in AES — guarantees that after two rounds, every output byte depends on every input byte, a property quantified by the cipher's **branch number**.

The distinction between a **block cipher** and a **stream cipher** reflects two different philosophies for consuming entropy. A block cipher is a pseudorandom permutation: it maps a fixed-width block of bits to another block of bits under key control, with the defining invariant that the mapping is a bijection — every input maps to a unique output, and the inverse exists. AES-128 operates on 128-bit blocks, consuming 128 bits of plaintext and producing 128 bits of ciphertext in a single atomic operation. A stream cipher, by contrast, generates a keystream — a sequence of pseudorandom bits derived from key and nonce — which is XOR'd against the plaintext one bit or byte at a time. Stream ciphers like ChaCha20 are closer in spirit to a pseudorandom number generator seeded with key material. Neither model is universally superior: stream ciphers excel in environments where message length is unknown in advance, latency per byte must be minimal, and hardware parallelism is unavailable. Block ciphers, operated in appropriate modes, are the dominant primitive in protocol engineering because their security reductions are tighter and their hardware acceleration (AES-NI) is pervasive.

Key scheduling is the mechanism by which a human-scale secret — 128 or 256 bits of key material — is expanded into the per-round subkeys consumed by a cipher's round function. AES derives 11 round keys from a 128-bit master key through a process involving SubBytes application to the last word of each key column, a rotation, and XOR with round constants drawn from powers of 2 in GF(2⁸). The critical invariant of a sound key schedule is **avalanche**: flipping one bit in the master key must produce a radically different set of round keys. DES's key schedule was notably weak in this regard, producing round keys with high mutual correlation and enabling related-key attacks that informed the design philosophy of AES's more aggressive expansion. For embedded practitioners targeting devices with constrained flash, the AES key schedule's memory footprint matters: storing all 11 expanded round keys requires 176 bytes, but the schedule can be computed on-the-fly at the cost of additional cycles per block.

---

## 2. Core Architecture & Mechanics

### The AES Round Function

AES (Rijndael) operates on a 4×4 matrix of bytes called the **state**, representing the 128-bit block. Each of the 10 rounds (for AES-128) applies four transformations in sequence: SubBytes, ShiftRows, MixColumns, and AddRoundKey. The final round omits MixColumns to preserve the cipher's invertibility without additional complexity. Understanding the mechanical purpose of each layer is essential for both implementation and attack analysis.

```
AES-128 Round Function (Rounds 1–9)

State (4×4 byte matrix)
        │
        ▼
  ┌─────────────┐
  │  SubBytes   │  ← S-box substitution (non-linear, GF(2⁸) inversion)
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  ShiftRows  │  ← Row i cyclically shifted left by i bytes (diffusion)
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ MixColumns  │  ← Matrix multiply over GF(2⁸) (inter-byte diffusion)
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ AddRoundKey │  ← XOR with 128-bit round subkey (key injection)
  └─────────────┘
         │
       (next round)
```

SubBytes applies the AES S-box to each of the 16 bytes independently. The S-box is constructed as the composition of a multiplicative inverse in GF(2⁸) (with 0 mapping to itself) followed by an affine transformation over GF(2). The multiplicative inverse is the nonlinear heart of the cipher: no affine function over GF(2⁸) can approximate it closely, which directly defeats linear cryptanalysis. The affine layer then ensures the S-box has no fixed points and no opposite fixed points (bytes mapping to their own complement), eliminating trivially exploitable algebraic structure.

ShiftRows cyclically rotates each row of the state by 0, 1, 2, and 3 byte positions respectively. This is a byte-level transposition with zero computational cost on a 32-bit processor when the state is loaded as column-major words. Its diffusion contribution is subtle but critical: without it, MixColumns would operate on each column independently, and four independent 4-byte block ciphers in parallel would result rather than one 16-byte cipher.

MixColumns treats each column as a four-element vector over GF(2⁸) and multiplies it by a fixed 4×4 MDS matrix. The choice of this matrix is not arbitrary — it is an **MDS (Maximum Distance Separable)** matrix, meaning the minimum number of non-zero elements across any input-output pair of the linear map is maximized. For AES, the branch number of MixColumns is 5: any non-zero input column with *w* non-zero bytes produces an output column with at least 5−w non-zero bytes. Combined with ShiftRows, this ensures that after two full rounds, every output byte depends on every input byte — the **wide-trail strategy** that Daemen and Rijmen used to prove AES's resistance to differential and linear attacks.

### CBC and CTR Mode State Machines

A block cipher is a building block, not a protocol. Encrypting messages longer than 128 bits requires a **mode of operation** that specifies how the block cipher is applied across multiple blocks. The mode determines whether the scheme achieves IND-CPA security, whether it supports parallel processing, and what failure modes emerge from nonce or IV reuse.

```
CBC Mode (Cipher Block Chaining)

Encrypt:                        Decrypt:
 IV ──┐                          IV ──┐
      ▼                               ▼
P₁ → XOR → AES_K → C₁ → ──► C₁ → AES_K⁻¹ → XOR → P₁
                   │                           │
P₂ → XOR ─────────┘    C₁ ─► C₂ → AES_K⁻¹ → XOR → P₂
         → AES_K → C₂
```

In CBC mode, each plaintext block is XOR'd with the previous ciphertext block before encryption. The IV randomizes the first block, ensuring that two encryptions of the same message under the same key produce different ciphertexts. CBC achieves IND-CPA security when the IV is chosen uniformly at random and kept secret until after encryption begins — which is the precise source of the BEAST attack against TLS 1.0, where predictable IVs broke CBC's security in a chosen-plaintext context. CBC decryption is parallelizable (each C_i block can be decrypted independently given C_{i−1}), but encryption is strictly sequential. For firmware update pipelines and embedded flash programming, this sequentiality is a real throughput constraint.

CTR mode eliminates the sequential dependency entirely by transforming the block cipher into a stream cipher. A counter value concatenated with a nonce is encrypted to produce keystream blocks, which are XOR'd with plaintext blocks.

```
CTR Mode

Nonce‖Counter₀ → AES_K → K₀ ─► XOR P₀ → C₀
Nonce‖Counter₁ → AES_K → K₁ ─► XOR P₁ → C₁
Nonce‖Counter₂ → AES_K → K₂ ─► XOR P₂ → C₂
         (all AES_K calls are independent — fully parallelizable)
```

Both encryption and decryption in CTR mode are identical operations (keystream XOR), and both are fully parallelizable. Random access decryption — seeking to byte offset *n* in a ciphertext without decrypting preceding blocks — is trivially supported by computing the counter value for the target block directly. This property is exploited in full-disk encryption (dm-crypt, VeraCrypt) and embedded firmware storage where random read access to encrypted flash is required. The catastrophic failure mode of CTR is nonce reuse: if the same (key, nonce) pair generates the same keystream for two distinct plaintexts P₁ and P₂, an adversary who observes both ciphertexts C₁ and C₂ recovers C₁ XOR C₂ = P₁ XOR P₂, which leaks substantial plaintext information through statistical analysis and known-plaintext correlation.

### GCM: Authenticated Encryption with Associated Data

GCM (Galois/Counter Mode) extends CTR mode with a polynomial authentication tag computed over GF(2¹²⁸). This provides **AEAD** — authenticated encryption with associated data — combining confidentiality and integrity in a single primitive. The authentication tag is computed by evaluating a polynomial whose coefficients are the ciphertext blocks, with a secret hash key H derived by encrypting the zero block under the cipher key. GCM's authentication is multiplicative over GF(2¹²⁸), which enables hardware acceleration via carry-less multiplication (the CLMUL instruction on x86 and the `pmull` instruction on ARM), making GCM the dominant AEAD construction in TLS 1.3, IPsec, and secure boot chains.

```
GCM Authentication Tag Computation

H = AES_K(0¹²⁸)                   (hash subkey)
J₀ = Nonce‖0³¹1                   (pre-counter block)

T = GHASH_H(AAD ‖ Ciphertext) XOR AES_K(J₀)

GHASH is a polynomial evaluation:
  X₀ = 0
  Xᵢ = (Xᵢ₋₁ XOR Aᵢ) · H  over GF(2¹²⁸)
```

The critical invariant of GCM is that **nonce uniqueness is a hard security requirement, not a performance hint**. If a (key, nonce) pair is reused, an adversary recovers the authentication subkey H from the two observed tags, completely defeating integrity. This is the nonce-misuse attack demonstrated by Joux in 2006. In practice, embedded systems with stateless or battery-less RTC clocks face a genuine risk of nonce reuse after power cycles, motivating the use of nonce-misuse-resistant AEADs like AES-GCM-SIV or the Synthetic IV construction in production firmware.

### ChaCha20-Poly1305 as an Alternative Stream Construction

ChaCha20 is a 512-bit block stream cipher based on the ARX (Add-Rotate-XOR) design paradigm: no S-boxes, no field arithmetic, only 32-bit additions, bitwise rotations, and XOR. Its internal state is a 4×4 matrix of 32-bit words, initialized with a 256-bit key, a 32-bit counter, and a 96-bit nonce. Twenty rounds of the quarter-round function (four ARX operations mixing two word pairs) produce the keystream block.

```c
/* ChaCha20 quarter-round — the atomic diffusion primitive */
static inline void quarterround(uint32_t s[16], int a, int b, int c, int d) {
    s[a] += s[b]; s[d] ^= s[a]; s[d] = ROL32(s[d], 16);
    s[c] += s[d]; s[b] ^= s[c]; s[b] = ROL32(s[b], 12);
    s[a] += s[b]; s[d] ^= s[a]; s[d] = ROL32(s[d], 8);
    s[c] += s[d]; s[b] ^= s[c]; s[b] = ROL32(s[b], 7);
}
```

ChaCha20's design is optimal for microcontrollers lacking AES-NI hardware acceleration. On Cortex-M4, ChaCha20-Poly1305 outperforms AES-128-GCM by roughly 3x in cycles-per-byte because the ARX operations map directly to the M4's native 32-bit barrel shifter and ALU with no table lookups — eliminating the cache-timing side-channel risk that plagues software AES on processors without hardware acceleration.

---

## 3. High-Performance Optimization & Failure Modes

### AES-NI Pipeline Exploitation

Modern x86 processors expose six AES instructions: `aesenc`, `aesenclast`, `aesdec`, `aesdeclast`, `aeskeygenassist`, and `aesimc`. A single `aesenc` instruction executes one AES round on an XMM register in a single clock cycle with 4-cycle latency on most Intel microarchitectures. The critical optimization in high-throughput AES-GCM implementations is **interleaving eight independent AES pipelines** to hide this 4-cycle latency through instruction-level parallelism.

```c
/*
 * AES-128-CTR encryption: 8-block interleaved pipeline for throughput.
 * Assumes key schedule in expanded_key[11], input in src, output in dst.
 * block_count must be a multiple of 8 for this path.
 */
#include <immintrin.h>
#include <stdint.h>
#include <string.h>

void aes128_ctr_encrypt_8x(const __m128i expanded_key[11],
                             const uint8_t *src,
                             uint8_t       *dst,
                             uint64_t       block_count,
                             uint64_t       nonce_hi,
                             uint64_t      *counter)
{
    __m128i b0, b1, b2, b3, b4, b5, b6, b7;

    for (uint64_t i = 0; i < block_count; i += 8) {
        /* Load 8 counter blocks */
        b0 = _mm_set_epi64x((int64_t)nonce_hi, (int64_t)(*counter + 0));
        b1 = _mm_set_epi64x((int64_t)nonce_hi, (int64_t)(*counter + 1));
        b2 = _mm_set_epi64x((int64_t)nonce_hi, (int64_t)(*counter + 2));
        b3 = _mm_set_epi64x((int64_t)nonce_hi, (int64_t)(*counter + 3));
        b4 = _mm_set_epi64x((int64_t)nonce_hi, (int64_t)(*counter + 4));
        b5 = _mm_set_epi64x((int64_t)nonce_hi, (int64_t)(*counter + 5));
        b6 = _mm_set_epi64x((int64_t)nonce_hi, (int64_t)(*counter + 6));
        b7 = _mm_set_epi64x((int64_t)nonce_hi, (int64_t)(*counter + 7));
        *counter += 8;

        /* Initial key whitening */
        b0 = _mm_xor_si128(b0, expanded_key[0]);
        b1 = _mm_xor_si128(b1, expanded_key[0]);
        b2 = _mm_xor_si128(b2, expanded_key[0]);
        b3 = _mm_xor_si128(b3, expanded_key[0]);
        b4 = _mm_xor_si128(b4, expanded_key[0]);
        b5 = _mm_xor_si128(b5, expanded_key[0]);
        b6 = _mm_xor_si128(b6, expanded_key[0]);
        b7 = _mm_xor_si128(b7, expanded_key[0]);

        /* Rounds 1–9: interleaved to fill 4-cycle aesenc latency */
        for (int r = 1; r <= 9; r++) {
            b0 = _mm_aesenc_si128(b0, expanded_key[r]);
            b1 = _mm_aesenc_si128(b1, expanded_key[r]);
            b2 = _mm_aesenc_si128(b2, expanded_key[r]);
            b3 = _mm_aesenc_si128(b3, expanded_key[r]);
            b4 = _mm_aesenc_si128(b4, expanded_key[r]);
            b5 = _mm_aesenc_si128(b5, expanded_key[r]);
            b6 = _mm_aesenc_si128(b6, expanded_key[r]);
            b7 = _mm_aesenc_si128(b7, expanded_key[r]);
        }

        /* Final round (no MixColumns) */
        b0 = _mm_aesenclast_si128(b0, expanded_key[10]);
        b1 = _mm_aesenclast_si128(b1, expanded_key[10]);
        b2 = _mm_aesenclast_si128(b2, expanded_key[10]);
        b3 = _mm_aesenclast_si128(b3, expanded_key[10]);
        b4 = _mm_aesenclast_si128(b4, expanded_key[10]);
        b5 = _mm_aesenclast_si128(b5, expanded_key[10]);
        b6 = _mm_aesenclast_si128(b6, expanded_key[10]);
        b7 = _mm_aesenclast_si128(b7, expanded_key[10]);

        /* XOR keystream with plaintext */
        __m128i p0, p1, p2, p3, p4, p5, p6, p7;
        p0 = _mm_loadu_si128((__m128i *)(src + (i+0)*16));
        p1 = _mm_loadu_si128((__m128i *)(src + (i+1)*16));
        p2 = _mm_loadu_si128((__m128i *)(src + (i+2)*16));
        p3 = _mm_loadu_si128((__m128i *)(src + (i+3)*16));
        p4 = _mm_loadu_si128((__m128i *)(src + (i+4)*16));
        p5 = _mm_loadu_si128((__m128i *)(src + (i+5)*16));
        p6 = _mm_loadu_si128((__m128i *)(src + (i+6)*16));
        p7 = _mm_loadu_si128((__m128i *)(src + (i+7)*16));

        _mm_storeu_si128((__m128i *)(dst + (i+0)*16), _mm_xor_si128(b0, p0));
        _mm_storeu_si128((__m128i *)(dst + (i+1)*16), _mm_xor_si128(b1, p1));
        _mm_storeu_si128((__m128i *)(dst + (i+2)*16), _mm_xor_si128(b2, p2));
        _mm_storeu_si128((__m128i *)(dst + (i+3)*16), _mm_xor_si128(b3, p3));
        _mm_storeu_si128((__m128i *)(dst + (i+4)*16), _mm_xor_si128(b4, p4));
        _mm_storeu_si128((__m128i *)(dst + (i+5)*16), _mm_xor_si128(b5, p5));
        _mm_storeu_si128((__m128i *)(dst + (i+6)*16), _mm_xor_si128(b6, p6));
        _mm_storeu_si128((__m128i *)(dst + (i+7)*16), _mm_xor_si128(b7, p7));
    }
}
```

This 8-block interleave is not stylistic — it is mechanically necessary. With a 4-cycle latency and 1-cycle throughput on `aesenc`, executing blocks sequentially leaves three pipeline slots idle per instruction. Eight independent pipelines fill those slots, sustaining near-peak throughput of approximately 0.7 cycles per byte on Skylake-class hardware. Intel's OpenSSL AES-GCM implementation uses exactly this pattern to achieve multi-gigabyte-per-second throughput on a single core.

### Timing Side-Channels in Table-Driven AES

Software AES implementations that use pre-computed lookup tables (the classic "T-table" approach) are vulnerable to cache-timing attacks. The T-table implementation merges SubBytes and MixColumns into four 256-entry tables of 32-bit words, reducing each round to 16 table lookups and XOR operations. The problem is that table access latency depends on whether the cache line containing the target entry is hot or cold — and the cache line accessed is determined by a byte of the intermediate state, which is a function of the secret key. Bernstein's 2005 remote timing attack on AES demonstrated that an adversary making remote connections can statistically recover key bytes from cache-timing variance measured over millions of connections.

The mitigations are well-defined. When AES-NI is available, use it unconditionally: the hardware instruction is constant-time by design, with no data-dependent memory accesses. When AES-NI is unavailable — common on older ARM Cortex-M devices, some RISC-V targets, and legacy embedded systems — the correct approach is a **bit-sliced** implementation, where multiple AES states are processed in parallel with each bit position of all states packed into a CPU word. The SubBytes computation becomes a sequence of bitwise logical operations implementing the S-box's boolean function, with no memory lookups whatsoever. The penalty is code complexity and reduced single-stream throughput, but the constant-time invariant is preserved.

Verifying constant-time behavior requires tooling beyond code review. `ctgrind` (a Valgrind plugin) instruments memory taint propagation to flag branches or memory addresses that depend on secret data. `dudect` performs statistical hypothesis testing on timing samples, measuring whether execution time distributions differ based on input values. For hardware security researchers validating firmware on physical targets, differential power analysis (DPA) on an oscilloscope probing the device's VCC rail can reveal key material through the correlation between power consumption and Hamming weight of intermediate AES states — a threat model that neither AES-NI nor bit-slicing alone defeats without additional masking countermeasures.

### ECB Mode: The Practical Failure of Codebook Encryption

ECB mode's IND-CPA failure is not merely theoretical. Encrypting each plaintext block independently with the same key means identical plaintext blocks produce identical ciphertext blocks. The classical demonstration is encrypting a bitmap image: the global structure — outlines, regions of uniform color — survives encryption because adjacent blocks with identical pixel values map to identical ciphertext blocks. For offensive practitioners, ECB mode in authentication tokens or session identifiers creates a **block-level oracle**: if a token contains a user identifier at a known block boundary, an attacker can substitute ciphertext blocks from one token into another, forging a token for an arbitrary user without knowing the key.

The detection of ECB mode in black-box systems is a standard reconnaissance technique. Submitting a crafted input containing repeated 16-byte blocks — four repetitions of `"AAAAAAAAAAAAAAAA"` for example — and observing whether the ciphertext contains repeated 16-byte blocks confirms ECB mode in a single query. This is the foundation of the **byte-at-a-time ECB decryption** attack: by carefully controlling the offset of a secret suffix or prefix relative to block boundaries, an attacker can recover the secret one byte at a time using 128 encryption oracle queries per byte.

### CBC Padding Oracle Attacks

CBC mode with PKCS#7 padding is vulnerable to the **padding oracle attack** when the decryption endpoint leaks whether the padding is valid — through an error message, a timing difference, or any distinguishable behavior. The attack is a classic example of an IND-CCA (chosen-ciphertext) break: even though CBC-with-random-IV achieves IND-CPA security, it fails catastrophically under adaptive chosen-ciphertext queries because the mode provides no ciphertext integrity.

The attack recovers the plaintext of any CBC-encrypted block C_n by manipulating the preceding ciphertext block C_{n−1}. For each byte position in the last block, the attacker modifies bytes in C_{n−1} to force a valid padding value and uses the oracle response to deduce the intermediate decryption state byte — which, XOR'd with the original C_{n−1} byte, yields the plaintext. The total query cost is at most 256 queries per byte, or 4096 queries for a full 16-byte block. The POODLE attack (2014) applied this principle to SSL 3.0's weaker padding scheme, and the original Vaudenay padding oracle from 2002 exploited it against CBC in J2EE application servers. The correct engineering response is unambiguous: use an AEAD mode (AES-GCM, ChaCha20-Poly1305, AES-GCM-SIV) that authenticates before decrypting, or apply MAC-then-encrypt with a constant-time MAC comparison. Separating encryption from authentication and placing them in a composition that leaks oracle information is a fundamental design error, not an implementation bug.

### Nonce Management in Embedded and Distributed Systems

Nonce uniqueness is the single most operationally difficult invariant to enforce in real-world deployments. The threat is not theoretical negligence but concrete system failure modes: a device that loses power before persisting its nonce counter, a firmware image deployed to ten thousand devices from the same factory key with the same nonce seed, or a distributed system where two nodes generate the same random nonce under a birthday-bound collision. For a 96-bit GCM nonce generated randomly, the birthday bound places a collision probability of 2^{-32} at 2^{32} messages — approximately four billion messages — which is reachable in high-throughput embedded telemetry systems over their operational lifetime.

Sound nonce management strategies for embedded targets follow a clear hierarchy of robustness. A hardware counter stored in NVM with write-ahead logging provides the strongest guarantee: the nonce is incremented before each encryption operation and committed to persistent storage before the plaintext is consumed. If NVM wear is a concern, a hierarchical scheme — a persistent epoch counter combined with a session counter in RAM — reduces write frequency while maintaining the uniqueness invariant across power cycles. For systems where none of these are available, AES-GCM-SIV (RFC 8452) provides **nonce-misuse resistance**: even if a nonce is reused, the adversary learns only whether two messages are identical, rather than gaining keystream and tag-forging capability. The SIV construction synthesizes a deterministic nonce from a PRF over the message itself, trading the random-access property of standard GCM for a catastrophic-failure boundary that embedded engineers can tolerate.

The practitioner summary is this: symmetric cryptography primitives are individually well-understood and well-analyzed, but their security properties are fragile under misuse in precisely the ways that production systems tend to misuse them — deterministic nonces, unauthenticated modes, software implementations with timing side-channels, and incorrect padding handling. The discipline of applied symmetric cryptography is not selecting the right primitive but enforcing the right usage invariants across the entire software and hardware stack.
