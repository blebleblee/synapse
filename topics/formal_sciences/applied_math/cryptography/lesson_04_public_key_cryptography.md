# Lesson 4: Public-Key Cryptography

## 1. First-Principles Intuition & Invariants

Public-key cryptography represents one of the most profound revolutions in applied mathematics and information security, fundamentally altering the landscape of secure communication by solving a problem that had plagued cryptographic systems since antiquity: the key distribution problem. In classical symmetric cryptography, two parties wishing to communicate securely must first establish a shared secret key through some secure channel, creating a circular dependency that limited the scalability and practicality of cryptographic systems. The breakthrough insight of Diffie, Hellman, Merkle, Rivest, Shamir, Adleman, and ElGamal in the 1970s and early 1980s was to exploit asymmetry in computational complexity, constructing mathematical functions that are efficient to compute in one direction but computationally infeasible to invert without special trapdoor information.

The foundational invariant underlying all public-key cryptosystems is the existence of trapdoor one-way functions. A function $f: X \to Y$ is called one-way if for any $x \in X$, computing $f(x)$ is efficient (polynomial time in the size of the input), but for a randomly chosen $y \in \text{im}(f)$, finding any preimage $x$ such that $f(x) = y$ is computationally infeasible (requires superpolynomial or exponential time). The trapdoor property adds an additional structure: there exists auxiliary information $t$ (the trapdoor) such that given $t$ and $y$, computing a preimage becomes efficient. This asymmetry allows the construction of key pairs where the public key enables encryption (evaluation of $f$) while the private key enables decryption (inversion of $f$ using the trapdoor).

The security of public-key cryptosystems rests not on information-theoretic secrecy—indeed, an adversary with unbounded computational resources can always recover the plaintext by exhaustive search or by solving the underlying hard problem—but rather on computational hardness assumptions. These assumptions assert that certain mathematical problems require superpolynomial time to solve on average for problem instances of cryptographic size. The three foundational hardness assumptions that underpin modern public-key cryptography are the integer factorization problem, the discrete logarithm problem in finite cyclic groups, and the elliptic curve discrete logarithm problem. Each assumption has been subjected to decades of cryptanalytic scrutiny, and while no formal proof of hardness exists (indeed, such a proof would resolve major open questions in complexity theory), the absence of efficient classical algorithms despite sustained effort provides empirical confidence in their intractability.

The integer factorization problem asks: given a composite integer $n = pq$ where $p$ and $q$ are large primes, recover the factors $p$ and $q$. While multiplication is trivially efficient, requiring $O((\log n)^2)$ bit operations using schoolbook methods or $O(\log n \log \log n)$ using fast multiplication algorithms, the best known classical factoring algorithms such as the General Number Field Sieve have subexponential complexity $O(\exp(c (\log n)^{1/3} (\log \log n)^{2/3}))$ for some constant $c \approx 1.923$. This superpolynomial gap between multiplication and factorization forms the security foundation for RSA cryptography.

The discrete logarithm problem (DLP) operates in the multiplicative group of a finite field or more generally in any finite cyclic group $G = \langle g \rangle$ of order $q$. Given $g$ and $h \in G$, the DLP asks for the exponent $x \in \mathbb{Z}_q$ such that $h = g^x$. While exponentiation via repeated squaring requires only $O(\log x)$ group operations, computing discrete logarithms in generic groups requires $O(\sqrt{q})$ group operations using Pollard's rho or baby-step giant-step algorithms, and in finite fields the best known algorithms again have subexponential complexity matching the number field sieve. The DLP underlies both the Diffie-Hellman key exchange and ElGamal encryption.

The elliptic curve discrete logarithm problem (ECDLP) transplants the DLP to the group of rational points on an elliptic curve over a finite field. Given an elliptic curve $E$ over $\mathbb{F}_q$ and points $P, Q \in E(\mathbb{F}_q)$ where $Q = nP$ for some integer $n$, the ECDLP asks for $n$. The critical distinction from the finite field DLP is that no subexponential algorithm is known for the ECDLP; the best known attacks remain generic algorithms requiring $O(\sqrt{\# E(\mathbb{F}_q)})$ operations. This square-root security level permits dramatically smaller key sizes for equivalent security levels, making elliptic curve cryptography the standard for modern constrained environments.

Before delving into specific cryptosystems, we must establish the mathematical foundations rigorously. Let $\mathbb{Z}_n$ denote the ring of integers modulo $n$, and let $\mathbb{Z}_n^*$ denote its group of units (elements coprime to $n$). By Euler's theorem, for any $a \in \mathbb{Z}_n^*$, we have $a^{\phi(n)} \equiv 1 \pmod{n}$ where $\phi(n) = \#\mathbb{Z}_n^*$ is Euler's totient function. When $n = pq$ is a product of distinct primes, $\phi(n) = (p-1)(q-1)$ since $\mathbb{Z}_n^* \cong \mathbb{Z}_p^* \times \mathbb{Z}_q^*$ by the Chinese Remainder Theorem. This isomorphism is the algebraic foundation of RSA.

The security parameter concept is central to cryptographic analysis. A cryptosystem has security parameter $k$ if the best known attack requires $O(2^k)$ operations. For RSA with modulus $n$, the security parameter is approximately $k \approx (\log_2 n)^{1/3} (\log \log_2 n)^{2/3}$ due to the number field sieve complexity. For discrete logarithm systems in prime fields $\mathbb{F}_p$, similar subexponential bounds apply. For elliptic curves over $\mathbb{F}_q$, the security parameter is approximately $k \approx \frac{1}{2} \log_2 q$ due to Pollard's rho algorithm, permitting much smaller parameters: a 256-bit elliptic curve provides roughly 128 bits of security, comparable to a 3072-bit RSA modulus.

## 2. Core Architecture & Mechanics

### RSA Cryptosystem

The RSA cryptosystem, published by Rivest, Shamir, and Adleman in 1978, instantiates public-key encryption and digital signatures through exponentiation in $\mathbb{Z}_n^*$ where $n = pq$ is a product of large primes. The security relies on the assumed hardness of factoring $n$; anyone who factors $n$ can compute $\phi(n)$ and thereby derive the private key.

**Key Generation.** The RSA key generation algorithm proceeds through the following steps. First, select two large random primes $p$ and $q$ of approximately equal bit length, typically each at least 1024 bits for modern security standards (2048 or 4096 bits being more common). Compute the modulus $n = pq$ and the totient $\phi(n) = (p-1)(q-1)$. Choose a public exponent $e \in \mathbb{Z}_{\phi(n)}^*$ such that $\gcd(e, \phi(n)) = 1$. The value $e = 65537 = 2^{16} + 1$ is the de facto standard choice, being large enough to resist certain attacks while having only two bits set, permitting extremely efficient exponentiation. Compute the private exponent $d \equiv e^{-1} \pmod{\phi(n)}$ using the extended Euclidean algorithm. The public key is the pair $(n, e)$ and the private key is $(n, d)$, or more completely $(p, q, d, d_p, d_q, q_{\text{inv}})$ where the additional values enable Chinese Remainder Theorem acceleration.

The public key $(n, e)$ can be distributed freely. The private key $(n, d)$ must be kept secret, and the primes $p$ and $q$ must be destroyed or protected with equivalent security since their knowledge permits immediate reconstruction of $d$.

**Encryption and Decryption.** To encrypt a message $m \in \mathbb{Z}_n^*$ (with $0 < m < n$ and $\gcd(m, n) = 1$), the sender computes the ciphertext:

$$c \equiv m^e \pmod{n}$$

To decrypt, the legitimate receiver uses the private exponent to compute:

$$m \equiv c^d \pmod{n}$$

The correctness of RSA decryption follows from Euler's theorem. Since $ed \equiv 1 \pmod{\phi(n)}$, there exists an integer $k$ such that $ed = 1 + k\phi(n)$. For any $m \in \mathbb{Z}_n^*$, we have:

$$c^d \equiv (m^e)^d \equiv m^{ed} \equiv m^{1 + k\phi(n)} \equiv m \cdot (m^{\phi(n)})^k \equiv m \cdot 1^k \equiv m \pmod{n}$$

where we applied Euler's theorem $m^{\phi(n)} \equiv 1 \pmod{n}$ in the penultimate step.

A subtlety arises for messages $m$ not coprime to $n$. If $\gcd(m, n) > 1$, then $m$ is a multiple of $p$ or $q$, immediately revealing a factor of $n$. However, we can verify that decryption still works correctly even in this case. Suppose $m \equiv 0 \pmod{p}$ but $m \not\equiv 0 \pmod{q}$. Then $m^{ed} \equiv 0 \equiv m \pmod{p}$ trivially. For the reduction modulo $q$, since $\gcd(m, q) = 1$, we have $m^{q-1} \equiv 1 \pmod{q}$ by Fermat's little theorem, and since $ed \equiv 1 \pmod{p-1}$ and $ed \equiv 1 \pmod{q-1}$ (both divide $\phi(n)$), we obtain $m^{ed} \equiv m \pmod{q}$. By the Chinese Remainder Theorem, $m^{ed} \equiv m \pmod{n}$. Thus RSA decryption is correct for all messages in $\mathbb{Z}_n$, though messages revealing factors are negligibly rare.

**Chinese Remainder Theorem Optimization.** Direct exponentiation modulo $n$ requires $O(\log d)$ multiplications of integers with $O(\log n)$ bits, yielding complexity $O((\log n)^3)$ per exponentiation using naive methods or $O((\log n)^2 \log \log n)$ using fast multiplication. The Chinese Remainder Theorem provides a factor-of-four speedup. Compute:

$$m_p \equiv c^{d_p} \pmod{p}, \quad m_q \equiv c^{d_q} \pmod{q}$$

where $d_p \equiv d \pmod{p-1}$ and $d_q \equiv d \pmod{q-1}$. Then reconstruct $m$ via:

$$m \equiv m_q + q \cdot [(m_p - m_q) \cdot q_{\text{inv}} \bmod p] \pmod{n}$$

where $q_{\text{inv}} \equiv q^{-1} \pmod{p}$. Since exponentiation complexity is superlinear in bit length, two exponentiations with half-length exponents are significantly faster than one full-length exponentiation.

**Textbook RSA Vulnerabilities and Padding.** The raw RSA transformation $m \mapsto m^e \bmod n$ is deterministic and multiplicatively homomorphic: $\text{Enc}(m_1) \cdot \text{Enc}(m_2) \equiv \text{Enc}(m_1 m_2) \pmod{n}$. This creates numerous vulnerabilities. If the same message is encrypted to multiple recipients with the same exponent $e$ but different moduli, Håstad's broadcast attack using the Chinese Remainder Theorem can recover the message. If $m^e < n$ (small message, small exponent), then $c = m^e$ as an integer, permitting recovery by taking the $e$-th root over the integers. The determinism enables dictionary attacks and breaks semantic security.

Modern RSA implementations mandate padding schemes that randomize and structure messages. The PKCS#1 v1.5 padding scheme prepends structured randomness to the message, though it has been shown vulnerable to adaptive chosen-ciphertext attacks. The current standard is Optimal Asymmetric Encryption Padding (OAEP), which applies a pair of random oracles (hash functions modeled as random functions) to mask the message and padding, achieving CCA2 security in the random oracle model. The transformation is:

$$m \to (m \| 0^{k_1}) \oplus G(r) \| r \oplus H((m \| 0^{k_1}) \oplus G(r))$$

where $r$ is random, $G$ and $H$ are hash functions with appropriate output lengths, and $\oplus$ denotes bitwise XOR. The padded message is then RSA-encrypted. OAEP ensures that even identical messages produce different ciphertexts and that the scheme is non-malleable.

### Diffie-Hellman Key Exchange

The Diffie-Hellman protocol, published in 1976, enables two parties to establish a shared secret over an insecure channel without any prior shared information, solving the key distribution problem that had constrained symmetric cryptography. The protocol operates in any finite cyclic group, though it is most commonly instantiated in the multiplicative group $\mathbb{F}_p^*$ of a prime field or in an elliptic curve group.

**Protocol Execution.** Fix public parameters: a large prime $p$ and a generator $g$ of a large prime-order subgroup of $\mathbb{F}_p^*$. To avoid small subgroup attacks, we typically choose a safe prime $p = 2q + 1$ where $q$ is also prime, ensuring that $\mathbb{F}_p^*$ has order $2q$ with only trivial small subgroups. Alice selects a private exponent $a \in \mathbb{Z}_q$ uniformly at random and computes her public value:

$$A \equiv g^a \pmod{p}$$

Bob independently selects $b \in \mathbb{Z}_q$ and computes:

$$B \equiv g^b \pmod{p}$$

Alice and Bob exchange $A$ and $B$ over the insecure channel. Alice computes:

$$K_A \equiv B^a \equiv (g^b)^a \equiv g^{ab} \pmod{p}$$

Bob computes:

$$K_B \equiv A^b \equiv (g^a)^b \equiv g^{ab} \pmod{p}$$

Both parties obtain the same shared secret $K = g^{ab} \bmod p$. This shared secret can then be fed into a key derivation function to produce symmetric encryption keys.

**Computational Diffie-Hellman Problem.** An eavesdropper observing the transcript sees $g$, $p$, $A = g^a$, and $B = g^b$. To compute the shared secret $g^{ab}$, the eavesdropper faces the Computational Diffie-Hellman (CDH) problem: given $g$, $g^a$, and $g^b$, compute $g^{ab}$. The CDH problem is believed to be hard, though it is potentially easier than the discrete logarithm problem. Indeed, if an adversary can solve the DLP to recover $a$ from $g^a$, they immediately solve CDH by computing $(g^b)^a$. The converse reduction is not known; CDH may be strictly easier than DLP.

A weaker problem is the Decisional Diffie-Hellman (DDH) problem: distinguish $(g, g^a, g^b, g^{ab})$ from $(g, g^a, g^b, g^c)$ where $c$ is random. DDH hardness implies that the shared secret is indistinguishable from random, providing semantic security. However, DDH is false in certain groups, notably those admitting efficient bilinear pairings, which compute $e(g^a, g^b) = e(g, g)^{ab}$ enabling DDH solution.

**Man-in-the-Middle Vulnerability.** The basic Diffie-Hellman protocol provides no authentication. An active adversary can intercept Alice's transmission of $A$, substitute their own value $A'$, establish a shared secret with Bob, decrypt and re-encrypt all traffic, and remain undetected. This man-in-the-middle attack is fundamental and requires integration with authentication mechanisms—digital signatures, pre-shared symmetric keys, or public-key infrastructure—to achieve authenticated key exchange. Modern protocols such as Station-to-Station (STS) augment Diffie-Hellman with digital signatures on the exchanged exponentials to provide authentication and forward secrecy.

### ElGamal Encryption

The ElGamal cryptosystem, introduced by Taher ElGamal in 1985, provides a public-key encryption scheme based directly on the Diffie-Hellman problem. It operates in any finite cyclic group but is most commonly instantiated in $\mathbb{F}_p^*$ or elliptic curve groups.

**Key Generation.** Fix public parameters $p$ (large prime) and $g$ (generator of a prime-order subgroup of size $q$). The key owner selects a private key $x \in \mathbb{Z}_q$ uniformly at random and computes the public key:

$$h \equiv g^x \pmod{p}$$

The public key is $(p, g, h)$ and the private key is $x$.

**Encryption.** To encrypt a message $m \in \mathbb{F}_p^*$, the sender selects an ephemeral random exponent $y \in \mathbb{Z}_q$ and computes the ciphertext pair:

$$(c_1, c_2) \equiv (g^y, m \cdot h^y) \pmod{p}$$

The first component $c_1 = g^y$ is an ephemeral public key for the encryption session. The second component $c_2$ is the message masked by the shared secret $h^y = g^{xy}$.

**Decryption.** The legitimate receiver uses the private key $x$ to compute the shared secret from $c_1$:

$$s \equiv c_1^x \equiv (g^y)^x \equiv g^{xy} \equiv h^y \pmod{p}$$

Then recover the message:

$$m \equiv c_2 \cdot s^{-1} \equiv c_2 \cdot (c_1^x)^{-1} \pmod{p}$$

Correctness follows immediately: $c_2 / c_1^x = (m \cdot h^y) / (g^y)^x = m \cdot g^{xy} / g^{xy} = m$.

**Security and Ciphertext Expansion.** ElGamal encryption is probabilistic due to the random ephemeral exponent $y$, ensuring that encrypting the same message twice produces different ciphertexts. This provides semantic security (IND-CPA) under the DDH assumption. However, the ciphertext is twice the size of the plaintext, representing significant bandwidth overhead compared to RSA. Moreover, ElGamal is multiplicatively homomorphic: 

$$\text{Enc}(m_1) \cdot \text{Enc}(m_2) = (g^{y_1}, m_1 h^{y_1}) \cdot (g^{y_2}, m_2 h^{y_2}) = (g^{y_1 + y_2}, m_1 m_2 h^{y_1 + y_2}) = \text{Enc}(m_1 m_2)$$

This homomorphism enables certain cryptographic protocols but breaks non-malleability and CCA2 security. Chosen-ciphertext security requires additional structure such as the Fujisaki-Okamoto transformation or integration with symmetric authentication.

### Elliptic Curve Cryptography

Elliptic curve cryptography (ECC) transplants discrete logarithm-based cryptosystems from finite fields to the group of rational points on an elliptic curve, achieving equivalent security with dramatically reduced key sizes due to the absence of subexponential attacks.

**Elliptic Curves over Finite Fields.** An elliptic curve $E$ over a field $K$ is the set of projective solutions to a Weierstrass equation:

$$E: y^2 = x^3 + ax + b$$

where $a, b \in K$ satisfy the non-singularity condition $4a^3 + 27b^2 \neq 0$ (ensuring the cubic has distinct roots). For cryptographic applications, we work over finite fields $K = \mathbb{F}_q$ where $q = p^n$ for prime $p$. The case $p > 3$ with $n = 1$ (prime fields) is most common, though binary fields $\mathbb{F}_{2^n}$ were historically popular for hardware efficiency.

The set of rational points $E(\mathbb{F}_q)$ consists of affine solutions $(x, y) \in \mathbb{F}_q \times \mathbb{F}_q$ satisfying the curve equation, together with a point at infinity $\mathcal{O}$ serving as the identity element. The group law on $E(\mathbb{F}_q)$ is defined geometrically: to add points $P$ and $Q$, draw the line through them (the tangent if $P = Q$), find its third intersection with the curve, and reflect across the $x$-axis. Algebraically, for $P = (x_1, y_1)$ and $Q = (x_2, y_2)$ with $P \neq \pm Q$:

$$\lambda = \frac{y_2 - y_1}{x_2 - x_1}, \quad x_3 = \lambda^2 - x_1 - x_2, \quad y_3 = \lambda(x_1 - x_3) - y_1$$

then $P + Q = (x_3, y_3)$. For point doubling $P = Q$:

$$\lambda = \frac{3x_1^2 + a}{2y_1}$$

The group $E(\mathbb{F}_q)$ is abelian, and by Hasse's theorem its order satisfies:

$$|q + 1 - \# E(\mathbb{F}_q)| \leq 2\sqrt{q}$$

For cryptographic use, we require $\# E(\mathbb{F}_q) = hq_0$ where $q_0$ is a large prime and $h$ (the cofactor) is small. The large prime-order subgroup $\langle G \rangle$ of order $q_0$ is used for cryptographic operations.

**Elliptic Curve Discrete Logarithm Problem.** Given points $P$ and $Q = nP$ on an elliptic curve $E(\mathbb{F}_q)$, the ECDLP asks for the integer $n$. Generic attacks such as Pollard's rho algorithm require $O(\sqrt{q_0})$ group operations for a group of prime order $q_0$, and no better algorithm is known for general elliptic curves. This provides security parameter $k \approx \frac{1}{2} \log_2 q_0$. Consequently, a 256-bit curve (with $q \approx 2^{256}$) provides approximately 128 bits of security, equivalent to 3072-bit RSA or discrete log in $\mathbb{F}_p$ with $p \approx 2^{3072}$.

Certain special curves admit faster attacks. Supersingular curves (those with $\# E(\mathbb{F}_q) = q + 1$) over $\mathbb{F}_q$ admit the MOV attack, using Weil or Tate pairings to reduce ECDLP to DLP in the extension field $\mathbb{F}_{q^k}$ for small embedding degree $k$, making the problem tractable via number field sieve methods. Anomalous curves (those with $\# E(\mathbb{F}_p) = p$) over prime fields $\mathbb{F}_p$ admit the Smart attack using $p$-adic logarithms to solve ECDLP in polynomial time. Cryptographic curves must avoid these structures.

**Standardized Curves and Coordinate Systems.** Widely used curves include the NIST P-256, P-384, and P-521 curves (prime fields with specific Weierstrass coefficients chosen for security and efficiency), and Curve25519 and Curve448 (Montgomery curves selected by Bernstein for simple, fast, side-channel resistant implementations). Curve25519 operates over $\mathbb{F}_p$ with $p = 2^{255} - 19$ and has the Montgomery form:

$$v^2 = u^3 + 486662u^2 + u$$

Montgomery curves permit efficient arithmetic using only $u$-coordinates, avoiding expensive $v$-coordinate computation and field inversions in the main scalar multiplication loop.

**ECDH and ECDSA.** Elliptic curve Diffie-Hellman (ECDH) operates identically to finite field Diffie-Hellman, replacing exponentiation with scalar multiplication. Fix a curve $E(\mathbb{F}_q)$ and base point $G$ of prime order $n$. Alice chooses private key $a \in \mathbb{Z}_n$ and publishes $A = aG$. Bob chooses $b$ and publishes $B = bG$. The shared secret is $K = abG$, computed by Alice as $aB$ and by Bob as $bA$. The security relies on the ECDLP hardness.

The Elliptic Curve Digital Signature Algorithm (ECDSA) is the elliptic curve analogue of DSA. To sign a message $m$ with private key $d$ and public key $Q = dG$, select random $k \in \mathbb{Z}_n$, compute $R = kG = (x_R, y_R)$, and set:

$$r \equiv x_R \pmod{n}, \quad s \equiv k^{-1}(H(m) + dr) \pmod{n}$$

where $H$ is a cryptographic hash function. The signature is $(r, s)$. Verification computes:

$$u_1 \equiv s^{-1} H(m) \pmod{n}, \quad u_2 \equiv s^{-1} r \pmod{n}, \quad R' = u_1 G + u_2 Q$$

and accepts if $x_{R'} \equiv r \pmod{n}$. Correctness follows from:

$$u_1 G + u_2 Q = s^{-1}(H(m) G + r d G) = s^{-1}(H(m) + dr) G = k G = R$$

Security requires that the ephemeral exponent $k$ be chosen uniformly at random and never reused; reuse or bias in $k$ permits private key recovery from two signatures.

### Trapdoor Functions and Hardness Assumptions

The abstract framework of trapdoor one-way functions formalizes the common structure underlying public-key cryptosystems. A trapdoor function family is a triple of algorithms $(\text{Gen}, f, f^{-1})$ where:

- $\text{Gen}(1^k)$ generates a public key $pk$ and trapdoor $td$ on input security parameter $k$
- $f_{pk}: D_{pk} \to R_{pk}$ is efficiently computable given $pk$
- $f^{-1}_{td}: R_{pk} \to D_{pk}$ is efficiently computable given $td$, satisfying $f^{-1}_{td}(f_{pk}(x)) = x$ for all $x \in D_{pk}$

The one-wayness property requires that for any probabilistic polynomial-time adversary $\mathcal{A}$:

$$\Pr[x' = x : (pk, td) \gets \text{Gen}(1^k), x \gets D_{pk}, y = f_{pk}(x), x' \gets \mathcal{A}(pk, y)] = \text{negl}(k)$$

where $\text{negl}(k)$ denotes a negligible function, one that vanishes faster than any inverse polynomial.

RSA instantiates a trapdoor function family with $f_{pk}(m) = m^e \bmod n$ where $pk = (n, e)$ and $td = d$. The one-wayness assumption is that inverting $f_{pk}$ without the trapdoor is as hard as factoring $n$. More precisely, the RSA problem asks: given $(n, e, c)$ where $c = m^e \bmod n$ for random $m$, compute $m$. While it is unknown whether solving the RSA problem is equivalent to factoring (it is conceivable that inversion is possible without factoring), extensive cryptanalysis has found no separation.

The discrete logarithm assumption in group $G = \langle g \rangle$ of prime order $q$ asserts that for any PPT adversary $\mathcal{A}$:

$$\Pr[x' = x : x \gets \mathbb{Z}_q, h = g^x, x' \gets \mathcal{A}(g, q, h)] = \text{negl}(\log q)$$

The exponential map $x \mapsto g^x$ is a homomorphism $\mathbb{Z}_q \to G$, efficiently computable but presumed hard to invert. This assumption justifies both Diffie-Hellman and ElGamal security.

The elliptic curve discrete logarithm assumption is the analogue for elliptic curve groups: given $G$ and $Q = nG$ on curve $E(\mathbb{F}_p)$ with $G$ of prime order $q$, finding $n$ requires time exponential in $\log q$. The absence of index calculus attacks on generic elliptic curves makes this assumption particularly robust.

## 3. High-Performance Optimization & Failure Modes

### Modular Exponentiation and Scalar Multiplication Algorithms

The dominant computational cost in RSA, Diffie-Hellman, and ElGamal is modular exponentiation, while for elliptic curve systems it is scalar multiplication. Both admit significant algorithmic optimization.

**Binary Exponentiation.** The naive approach to computing $g^x \bmod n$ by repeated multiplication requires $x - 1$ multiplications. Binary exponentiation reduces this to $O(\log x)$ by processing the binary representation of $x$ from most significant to least significant bit. Write $x = \sum_{i=0}^{k-1} x_i 2^i$ where $x_i \in \{0, 1\}$. Then:

$$g^x = g^{\sum_i x_i 2^i} = \prod_{i : x_i = 1} g^{2^i}$$

The values $g^{2^i}$ are computed iteratively by squaring: $g^{2^{i+1}} = (g^{2^i})^2$. The algorithm maintains an accumulator initialized to $1$, squares it at each step, and multiplies by $g$ when the corresponding bit is $1$. This requires at most $\lfloor \log_2 x \rfloor$ squarings and at most $\lfloor \log_2 x \rfloor$ multiplications, for a total of at most $2 \lfloor \log_2 x \rfloor$ operations.

**Windowed Methods.** For very large exponents, windowed methods precompute small powers and process multiple bits per iteration. Fix window size $w$ and precompute $g^1, g^2, \ldots, g^{2^w - 1}$. Partition the exponent $x$ into $w$-bit windows and scan from most significant to least significant window. At each window, square $w$ times and multiply by the precomputed value corresponding to the window bits. This reduces the number of multiplications at the cost of storage and initial precomputation. Optimal window size depends on the balance between memory and computation; $w = 4$ or $w = 5$ is typical.

**Montgomery Multiplication.** Modular reduction is the bottleneck in each multiplication. Montgomery multiplication replaces trial division with simpler operations by working in a transformed domain. Fix modulus $n$ and choose $R > n$ coprime to $n$ (typically $R = 2^k$ for machine word alignment). The Montgomery representation of $a$ is $\bar{a} = aR \bmod n$. Montgomery multiplication computes $\bar{a} \cdot \bar{b} = abR \bmod n$ from $\bar{a}$ and $\bar{b}$ efficiently. Precompute $n' \equiv -n^{-1} \pmod{R}$. The Montgomery reduction of $T$ (with $0 \leq T < nR$) is:

$$\text{REDC}(T) = (T + ((T \bmod R) \cdot n' \bmod R) \cdot n) / R$$

This produces $TR^{-1} \bmod n$ using only shifts and additions (for $R = 2^k$) rather than expensive divisions. Modular exponentiation converts the base to Montgomery form, performs all intermediate operations in Montgomery form, and converts the result back. The speedup is typically 20-50% for large moduli.

**Sliding Window and Non-Adjacent Form.** For scalar multiplication on elliptic curves, the analogue of binary exponentiation processes the scalar bit-by-bit, doubling and conditionally adding at each step. The sliding window method scans the scalar from left to right, skipping runs of zeros and processing maximal odd windows. Non-adjacent form (NAF) represents the scalar using digits $\{-1, 0, 1\}$ with no adjacent nonzero digits, minimizing the number of additions. For scalar $n$, the NAF representation has average density of nonzero digits $1/3$, compared to $1/2$ for binary, reducing additions by one-third.

**Fixed-Base and Variable-Base Multiplication.** When the base point $G$ is fixed (as in signature verification $u_1 G + u_2 Q$), precomputation methods achieve substantial speedups. Compute and store multiples $\{iG : i \in S\}$ for an appropriate set $S$. At runtime, decompose the scalar $n$ to express $nG$ as a sum of precomputed points, requiring only point additions. For variable bases (as in Diffie-Hellman shared secret computation), windowed methods and NAF provide the best performance without large storage.

**Side-Channel Resistance.** Naive implementations leak secret exponents through timing, power consumption, and electromagnetic emanations. Timing attacks exploit the fact that conditional branches (multiply when bit is $1$, skip when bit is $0$) create measurable timing differences, permitting exponent recovery. Constant-time implementations ensure that the execution path is independent of secret data: always perform both square and multiply operations, using conditional moves to select the correct result rather than conditional branches. For elliptic curves, unified formulas that use the same operations for addition and doubling prevent distinguishing operations. Montgomery ladder is a particularly elegant constant-time scalar multiplication algorithm that maintains two points differing by the original base point, ensuring that each iteration performs one doubling and one addition independent of the scalar bits.

Power analysis attacks measure instantaneous power consumption to infer operations. Simple power analysis (SPA) directly observes operation sequences, while differential power analysis (DPA) uses statistical methods to correlate power traces with key bits. Countermeasures include point blinding (adding a random multiple of a known point before computation), scalar blinding (adding a random multiple of the group order to the scalar), and masking (splitting secrets into random shares processed independently).

### Parameter Selection and Validation

**RSA Modulus Generation.** The primes $p$ and $q$ must resist factorization attacks. They should be approximately equal in size (say $|p - q| > 2^{k/2 - 100}$ for a $k$-bit modulus) to prevent Fermat factorization, but not too close to prevent ECM attacks on near-factors. They must not be weak primes: $p - 1$ and $q - 1$ should have large prime factors to resist Pollard's $p - 1$ algorithm, and $p + 1$ and $q + 1$ should also have large prime factors to resist Williams' $p + 1$ algorithm. Strong primes are generated by requiring $p - 1$ to have a large prime factor $r$, and $r - 1$ to have a large prime factor. However, modern guidance from NIST deprecates strong prime requirements for sufficiently large moduli (2048 bits or more), as the cost of ECM and number field sieve attacks dominates.

The public exponent $e = 3$ was once common for encryption efficiency but is now avoided due to vulnerability to cube-root attacks when unpadded messages satisfy $m^3 < n$. The standard $e = 65537$ provides a good balance. The private exponent $d$ must satisfy $d > n^{1/4}$ to prevent Wiener's attack, which recovers $d$ from the public key using continued fraction approximations of $e/n$ when $d$ is too small.

**Discrete Log Parameter Generation.** For finite field Diffie-Hellman, the modulus $p$ should be a safe prime $p = 2q + 1$ where $q$ is also prime, or more generally $p - 1$ should have a large prime factor $q$ with the generator $g$ chosen to have order $q$. This prevents small subgroup attacks where an adversary forces the computation into a subgroup of smooth order, permitting discrete log computation by Pohlig-Hellman reduction. The Logjam attack exploited widespread use of 1024-bit primes and precomputation of discrete log infrastructure for common primes, underscoring the importance of unique, randomly generated parameters or transition to larger sizes (2048-bit minimum).

**Elliptic Curve Selection.** Cryptographic curves must satisfy several criteria. The curve order $\# E(\mathbb{F}_q)$ must be divisible by a large prime $n$ (ideally $\# E(\mathbb{F}_q) = hn$ with small cofactor $h \in \{1, 4, 8\}$). The curve must not be anomalous ($\# E(\mathbb{F}_p) \neq p$) or supersingular (embedding degree $k$ must be large, typically $k > (\log p) / 6$). The curve must have large discriminant to avoid CM field attacks. The curve parameters should be generated verifiably randomly (nothing-up-my-sleeve numbers) or via a transparent deterministic process to prevent hidden structural weaknesses, addressing concerns raised by the Dual EC DRBG backdoor.

Twist security is an additional concern: the quadratic twist of an elliptic curve (obtained by replacing $b$ with $\xi b$ for non-square $\xi$) should also have nearly prime order to prevent invalid curve attacks where an adversary provides a point on the twist rather than the curve, potentially leaking key bits through small subgroups. Curve25519 and Curve448 were explicitly designed for twist security.

### Quantum Threats and Post-Quantum Transition

Shor's algorithm, announced in 1994, demonstrated that a quantum computer can factor integers and solve discrete logarithms in polynomial time, specifically $O((\log n)^3)$ for factoring and $O((\log n)^2 \log \log n)$ for discrete log using the quantum Fourier transform. This breakthrough renders RSA, Diffie-Hellman, and elliptic curve cryptography completely insecure against adversaries with large-scale fault-tolerant quantum computers.

The quantum factoring algorithm exploits periodicity in the function $f(x) = a^x \bmod n$. For $a$ coprime to $n$, the sequence $a^0, a^1, a^2, \ldots \bmod n$ is periodic with period dividing $\phi(n)$. Quantum phase estimation finds this period $r$ in polynomial time. If $r$ is even and $a^{r/2} \not\equiv -1 \pmod{n}$, then $\gcd(a^{r/2} - 1, n)$ yields a nontrivial factor. Repeating with random $a$ factors $n$ with high probability.

For discrete logarithms, Shor's algorithm finds the period of $f(x, y) = g^x h^{-y}$ where $h = g^k$ is the target. The period is $(k, 1)$, and quantum Fourier transform on two registers recovers $k$ in polynomial time.

The best current estimates suggest that factoring a 2048-bit RSA modulus requires a quantum computer with approximately $20$ million noisy qubits or $4000$ logical qubits with realistic error rates and surface code error correction. Breaking 256-bit elliptic curve cryptography requires fewer resources, approximately $2000$ logical qubits. While such machines do not exist today, rapid progress in quantum computing hardware motivates urgent transition to post-quantum cryptography.

**Post-Quantum Hardness Assumptions.** Post-quantum cryptography relies on problems believed hard for both classical and quantum computers. Leading candidates include lattice-based cryptography (relying on the shortest vector problem and learning with errors), code-based cryptography (relying on syndrome decoding), multivariate polynomial cryptography (solving systems of multivariate quadratic equations), and hash-based signatures (relying on collision resistance and second-preimage resistance of cryptographic hash functions).

The NIST Post-Quantum Cryptography Standardization process selected CRYSTALS-Kyber for public-key encryption and key encapsulation, CRYSTALS-Dilithium and FALCON for digital signatures, and SPHINCS+ as a stateless hash-based signature alternative. These schemes offer conjectured quantum resistance with reasonable performance, though typically with larger key and ciphertext sizes than classical systems.

Hybrid approaches, combining classical and post-quantum schemes, provide defense-in-depth during the transition: a hybrid key exchange establishes a shared secret using both Diffie-Hellman and Kyber, deriving the session key from both contributions. This ensures security if either scheme remains secure, mitigating uncertainty about post-quantum algorithm maturity.

The threat model includes harvest-now-decrypt-later attacks, where an adversary records encrypted traffic today and decrypts it once a quantum computer becomes available. Data with long-term confidentiality requirements necessitates immediate transition to post-quantum cryptography, even before quantum computers exist, to protect against retroactive decryption. Forward secrecy (ephemeral key exchange) limits exposure by ensuring that compromise of long-term keys does not decrypt past sessions, but does not protect against quantum attacks on the key exchange itself. Only post-quantum key exchange mechanisms provide security against this threat.
