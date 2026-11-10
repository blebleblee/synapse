# Hands-On Operational Lab: Cryptography  
*Formal Sciences | Applied Mathematics*  

---

## Objective & Prerequisites  
**Objective**: Gain hands-on proficiency in symmetric-key cryptography using OpenSSL, with emphasis on *operational verification*, *system state inspection*, *fault injection*, and *debugging*—all grounded in formal cryptographic principles.  

**Prerequisites**:  
1. Linux/macOS system with OpenSSL installed (check via `openssl version`).  
2. Basic familiarity with shell commands and cryptographic concepts (e.g., symmetric encryption, CBC mode).  
3. Understanding of the following formal concepts:  
   - *Initialization Vector (IV)*: Random nonce for block cipher mode  
   - *Ciphertext Integrity*: How modifications propagate in CBC mode  
   - *Key Management*: Password-based key derivation (PBKDF2)  

> 💡 **Why this matters**: Cryptography is a *formal system* where operational correctness depends on precise mathematical constraints. This lab bridges theory and practice by verifying cryptographic operations against formal specifications.

---

## Exercise 1: Exploration & System State Inspection  
*Inspect your cryptographic environment and verify system readiness.*  

**Step 1**: Confirm OpenSSL installation and version  
```shell
openssl version
```
**Expected Output**:  
`OpenSSL 3.0.0  15 Jan 2024` *(or similar version)*  

**Step 2**: List available ciphers (critical for mode selection)  
```shell
openssl cipher -list
```
**Expected Output**:  
`AES-256-CBC`  
`AES-128-CBC`  
`DES-CBC`  
*(...other standard ciphers)*  

**Step 3**: Verify IV handling in CBC mode  
```shell
openssl enc -aes-256-cbc -help | grep IV
```
**Expected Output**:  
`-iv <IV>` *: Initialization vector (16 bytes for AES)*  

> ✅ **Formal Verification**:  
> The output confirms OpenSSL implements *block cipher modes* (CBC) with *explicit IV requirements*. This aligns with the **formal definition** of CBC:  
> $$C_i = E(K, P_i \oplus IV)$$  
> where $C_i$ = ciphertext block, $P_i$ = plaintext block, $IV$ = initialization vector, $E$ = block cipher.

---

## Exercise 2: Building & Deploying / Modeling Scenario  
*Encrypt/decrypt a message using AES-256-CBC with a password-based key.*  

**Step 1**: Create a plaintext file  
```shell
echo "This is a secret message" > plaintext.txt
```

**Step 2**: Encrypt with a *password* (not a key file)  
```shell
openssl enc -aes-256-cbc -in plaintext.txt -out ciphertext.txt -pass pass:my_secret_password
```
**Expected Output**:  
`ciphertext.txt` (binary file, 16 bytes larger than plaintext)  

**Step 3**: Decrypt the ciphertext  
```shell
openssl enc -aes-256-cbc -d -in ciphertext.txt -out decrypted.txt -pass pass:my_secret_password
```
**Expected Output**:  
`decrypted.txt` contains: `This is a secret message`  

**Step 4**: Verify integrity of decrypted output  
```shell
cat decrypted.txt
```
**Expected Output**:  
`This is a secret message` *(exact original content)*  

> 🔍 **Formal Workflow Analysis**:  
> 1. **Key Derivation**: Password `my_secret_password` → PBKDF2 → 256-bit key (via `openssl`'s built-in key derivation)  
> 2. **IV Handling**: OpenSSL auto-generates a 16-byte IV (stored in ciphertext header)  
> 3. **CBC Operation**:  
>    $$C_0 = E(K, P_0 \oplus IV)$$  
>    $$C_1 = E(K, P_1 \oplus C_0)$$  
>    *(No IV leakage; IV is encrypted with key)*  

> 💡 **Why this works**: The system adheres to the **formal CBC security model** where IVs are *random* and *never reused*.

---

## Exercise 3: Fault Injection, Failure Analysis & Debugging  
*Intentionally break the system and analyze failure modes.*  

**Step 1**: Corrupt ciphertext (add 1 byte)  
```shell
cat ciphertext.txt | tr -d '\0' | head -c $(expr 100 - 1) > corrupted_ciphertext.txt
```
*(This removes the last byte of `ciphertext.txt`)*  

**Step 2**: Attempt decryption with correct password  
```shell
openssl enc -aes-256-cbc -d -in corrupted_ciphertext.txt -out failed_decrypt.txt -pass pass:my_secret_password
```
**Expected Output**:  
`error: bad decrypt` *(or similar)*  

**Step 3**: Analyze failure cause  
```shell
openssl enc -aes-256-cbc -d -in corrupted_ciphertext.txt -pass pass:my_secret_password 2>&1 | grep -i error
```
**Expected Output**:  
`error: bad decrypt`  

**Step 4**: Inject wrong password (failure mode)  
```shell
openssl enc -aes-256-cbc -d -in ciphertext.txt -out wrong_decrypt.txt -pass pass:wrong_password
```
**Expected Output**:  
`error: bad decrypt` *(no plaintext output)*  

> 🧠 **Formal Failure Analysis**:  
> In CBC mode, **a single byte modification in ciphertext** corrupts *all subsequent blocks* due to:  
> $$P_i = D(K, C_i) \oplus C_{i-1}$$  
> This is a *formal consequence* of the chaining mechanism. The system fails *without* revealing plaintext—consistent with **semantic security**.  
>   
> **Root Cause**: IV reuse or ciphertext tampering violates the *formal CBC security invariant*:  
> $$\forall i, \quad C_i \text{ must be independent of } C_j \text{ for } j \neq i$$

---

## Challenge Lab: Independent Problem for Socratic Discussion with the AI Tutor  
**Problem**:  
> *In AES-CBC mode, if an attacker modifies the second byte of the ciphertext (after the IV), what is the effect on the decrypted plaintext? How does this demonstrate the security trade-off between ciphertext integrity and key management?*  

**Socratic Discussion Prompt**:  
1. **Formalize the attack**: Write the CBC decryption equations for blocks $P_0$ and $P_1$ after modification.  
2. **Quantify the impact**: How many bytes of plaintext are corrupted?  
3. **Security trade-off**: Why is IV randomness *critical* here? What happens if IVs are reused?  
4. **Real-world implication**: How would this affect a system using TLS 1.2 (which uses CBC)?  

> 💡 **Why this works for Socratic learning**:  
> This problem forces students to:  
> - Apply formal definitions (CBC chaining)  
> - Trace error propagation (mathematically)  
> - Connect theory to real-world systems (TLS)  
> - Understand *why* IVs must be *random* and *unique* (a formal requirement in CBC)  

**AI Tutor Guidance**:  
> *When discussing, ask: "What is the mathematical condition that ensures the IV is secure?"*  
> *Answer*: The IV must be *uniformly random* and *never reused* (formalized as $\forall i, \text{IV}_i \neq \text{IV}_j$ for $i \neq j$).

---

> 📚 **Formal Science Insight**:  
> Cryptography is a *formal system* where operational correctness depends on **mathematical constraints** (e.g., IV uniqueness in CBC). This lab demonstrates how *small deviations* (e.g., 1-byte corruption) violate formal security invariants—proving that *operational* security requires **rigorous adherence to formal specifications**.  

> ✅ **Lab Completion**: Pass all exercises → You have mastered *operational cryptography* as a formal science.  

*Professor of Mathematics and Formal Logic*  
*Department of Applied Mathematics*
