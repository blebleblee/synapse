# Lesson 2: Quantum Key Distribution Protocols

## 1. First-Principles Intuition & Invariants

Quantum Key Distribution represents a fundamental departure from the computational hardness assumptions that underpin classical public-key cryptography. Where RSA and elliptic curve systems rest on the conjectured difficulty of integer factorization or discrete logarithm problems—assumptions vulnerable to algorithmic breakthroughs and quantum computing advances—QKD protocols derive their security from the physical laws governing quantum mechanical systems. The security guarantee emerges not from mathematical complexity but from the information-theoretic impossibility of observing a quantum state without disturbing it, a consequence of the no-cloning theorem and Heisenberg's uncertainty principle.

The architectural motivation for QKD arises from recognizing that any symmetric encryption system, no matter how robust its cipher, collapses to the security of its key exchange mechanism. One-time pads provide information-theoretic security when keys are truly random, used only once, and distributed securely—but this final requirement has historically forced reliance on trusted couriers or computationally secure key establishment. Quantum key distribution solves this bootstrap problem by allowing two parties, traditionally named Alice and Bob, to establish a shared random key over a public quantum channel while detecting the presence of any eavesdropper, Eve, with arbitrarily high probability.

The fundamental invariant governing all QKD protocols is the measurement postulate of quantum mechanics: measuring a quantum system in one basis disturbs superpositions in non-commuting bases, and any attempt to extract information about both conjugate observables simultaneously introduces irreducible noise. When Alice encodes classical bits into quantum states drawn from non-orthogonal bases—such as rectilinear and diagonal photon polarizations—Eve cannot simultaneously extract complete information about both encodings without introducing detectable disturbances. The legitimate parties exploit this disturbance signature through basis reconciliation, sifting, and error rate analysis to bound Eve's information leakage and distill a provably secure key through privacy amplification.

The security proof structure for QKD protocols differs categorically from classical cryptographic reductions. Rather than reducing security to a hard problem, QKD security proofs establish that for any eavesdropping strategy Eve employs—whether individual attacks on each photon, collective measurements across multiple photons, or fully coherent attacks exploiting arbitrary entanglement—the quantum bit error rate (QBER) observed by Alice and Bob bounds Eve's mutual information with their sifted key. If the QBER remains below a protocol-specific threshold, typically around eleven percent for BB84 under individual attacks, privacy amplification via randomness extraction can compress the sifted key into a shorter final key about which Eve has exponentially vanishing information.

This information-theoretic foundation imposes stringent engineering requirements on practical QKD implementations. The quantum channel must preserve photon polarization or phase encoding with minimal decoherence, demanding single-mode fiber optics, free-space optical links with adaptive optics compensation, or satellite-based relay stations to overcome atmospheric absorption and turbulence. Photon sources must produce true single-photon states or weak coherent pulses with decoy state protocols to defeat photon number splitting attacks. Detectors must achieve high quantum efficiency while maintaining low dark count rates, with single-photon avalanche diodes or superconducting nanowire detectors operating at cryogenic temperatures. Synchronization between Alice and Bob requires sub-nanosecond timing resolution to correlate detection events with transmitted states across fiber delays or free-space propagation.

The classical authenticated channel required for basis reconciliation, error correction, and privacy amplification introduces a subtle but critical dependency: QKD does not solve the authentication problem but assumes an existing authenticated classical channel, typically secured through pre-shared symmetric keys or digital signatures. This bootstrapping is acceptable because authentication keys can be much shorter than encryption keys and can be refreshed using keys established through previous QKD sessions, creating a forward-secure ratcheting mechanism. However, the classical channel must resist man-in-the-middle attacks, as Eve controlling this channel could execute basis-dependent attacks or manipulate error correction information to weaken the final key.

## 2. Core Architecture & Mechanics

### BB84 Protocol: Four-State Polarization Encoding

The BB84 protocol, proposed by Charles Bennett and Gilles Brassard in 1984, encodes classical bits into single photons using two conjugate polarization bases: the rectilinear basis with horizontal (H) and vertical (V) polarizations, and the diagonal basis with 45-degree (D) and 135-degree (A) polarizations. Alice randomly chooses for each transmitted photon both a classical bit value—zero or one—and an encoding basis, either rectilinear or diagonal. The bit value determines the specific polarization within the chosen basis: in the rectilinear basis, zero maps to horizontal and one to vertical, while in the diagonal basis, zero maps to 45-degree and one to 135-degree polarization.

Bob independently and randomly selects a measurement basis for each received photon, again choosing between rectilinear and diagonal. Quantum mechanics dictates that when Bob's measurement basis matches Alice's preparation basis, he deterministically recovers Alice's bit value—measuring a horizontal photon in the rectilinear basis always yields horizontal, and measuring a 45-degree photon in the diagonal basis always yields 45-degree. However, when the bases differ, Bob's measurement outcome becomes maximally random: a horizontal photon measured in the diagonal basis yields 45-degree or 135-degree with equal probability, revealing no information about Alice's original bit but irreversibly collapsing the quantum state.

The protocol execution unfolds in distinct phases that separate quantum transmission from classical post-processing. During the quantum phase, Alice generates a random bit sequence of length $N$, typically hundreds of thousands to millions of bits, and for each bit randomly selects a preparation basis. She encodes each bit-basis pair into a photon polarization state and transmits the photon to Bob over the quantum channel. Bob receives the photons, applies randomly chosen measurement bases, and records his measurement outcomes. Channel losses, detector inefficiencies, and dark counts mean that Bob successfully detects only a fraction of transmitted photons, typically ten to forty percent depending on channel quality and distance.

After quantum transmission completes, Alice and Bob engage in basis reconciliation over the authenticated classical channel. Bob announces which photon positions he successfully detected, and Alice confirms these positions. For each detected photon, Bob reveals his chosen measurement basis, and Alice discloses whether her preparation basis matched. Both parties retain only the measurement outcomes where their bases coincided, discarding all mismatched-basis results. This sifting process reduces the raw key length by approximately half in expectation, since bases match with probability one-half for random independent choices.

The sifted key would be identical between Alice and Bob in an ideal noiseless channel, but real implementations introduce errors from multiple sources: intrinsic channel noise causing polarization rotation, imperfect single-photon sources producing multi-photon states vulnerable to splitting attacks, detector dark counts registering false positives, and most critically, eavesdropping attempts. Alice and Bob sacrifice a random subset of their sifted key bits to estimate the quantum bit error rate by comparing values over the public channel. If the QBER exceeds the protocol's security threshold—typically eleven percent for BB84 against individual attacks—they abort the protocol, as the error rate suggests either excessive channel noise or active eavesdropping beyond the tolerable information leakage bound.

Assuming acceptable QBER, Alice and Bob perform information reconciliation through classical error correction protocols, typically cascade or low-density parity-check codes, exchanging parity information over the authenticated channel to correct discrepancies in their sifted keys. This error correction step leaks additional information to Eve—she learns all transmitted parity bits—further reducing the extractable secure key length. Privacy amplification follows, applying universal hash functions to compress the error-corrected key into a shorter final key about which Eve has exponentially small mutual information. The hash function selection and output length depend on bounds derived from the observed QBER and the amount of information leaked during error correction, typically using leftover hash lemma constructions or Trevisan's extractor.

```mermaid
flowchart TD
    subgraph Phase1 ["Phase 1: Quantum Transmission"]
        A1["Alice: Generate random bit string b[0..N-1]"]
        A2["Alice: Generate random basis string B_A[0..N-1]<br/>(R = Rectilinear, D = Diagonal)"]
        A3["Alice: For each i, encode b[i] in basis B_A[i]:<br/>R basis: 0→|H⟩, 1→|V⟩<br/>D basis: 0→|D⟩, 1→|A⟩"]
        A4["Alice: Transmit photon sequence"]
        B1["Bob: Generate random basis B_B[0..N-1]"]
        B2["Bob: Measure each photon in basis B_B[i]"]
        B3["Bob: Record measurement outcomes m[i]<br/>(subset detected due to losses)"]
        
        A1 --> A2 --> A3 --> A4
        A4 -->|"Quantum Channel"| B1
        B1 --> B2 --> B3
    end
    
    subgraph Phase2 ["Phase 2: Basis Reconciliation (Classical Authenticated Channel)"]
        B4["Bob: Send detection positions and<br/>measurement bases B_B to Alice"]
        A5["Alice: Send matching basis indicators to Bob"]
        S1["Both: Sift and keep only bits where B_A[i] = B_B[i]<br/>Sifted key length ≈ N/2 (expectation)"]
        
        B4 --> A5 --> S1
    end
    
    subgraph Phase3 ["Phase 3: Error Estimation"]
        B5["Bob: Send random sample positions to Alice"]
        A6["Alice: Send sample bit values to Bob"]
        B6["Bob: Send sample bit values to Alice"]
        E1["Both: Compute QBER = (# disagreements) / (sample size)"]
        E2{"QBER > threshold?"}
        E3["ABORT Protocol"]
        E4["Proceed to Error Correction"]
        
        B5 --> A6 --> B6 --> E1 --> E2
        E2 -->|Yes| E3
        E2 -->|No| E4
    end
    
    subgraph Phase4 ["Phase 4: Information Reconciliation & Privacy Amplification"]
        R1["Both: Exchange parity check syndromes"]
        R2["Both: Error correction using CASCADE or LDPC<br/>Reconciled key length: n_reconciled"]
        P1["Both: Privacy amplification<br/>Select universal hash function h with output length ℓ<br/>based on observed QBER, leaked information, and security parameter ε"]
        P2["Both: Final key K = h(reconciled_key)<br/>|K| = ℓ bits with Pr["I(Eve:K) > 0"] < ε"]
        
        R1 --> R2 --> P1 --> P2
    end
    
    Phase1 --> Phase2
    Phase2 --> Phase3
    E4 --> Phase4
```

### E91 Protocol: Entanglement-Based Distribution

The E91 protocol, proposed by Artur Ekert in 1991, exploits quantum entanglement rather than prepare-and-measure schemes. Alice and Bob each receive one photon from maximally entangled Bell pairs, typically the singlet state $|\Psi^-\rangle = \frac{1}{\sqrt{2}}(|HV\rangle - |VH\rangle)$, generated by a trusted or untrusted source. Each party randomly selects measurement bases from a set of three non-orthogonal polarization angles—for instance, 0°, 45°, and 90° for Alice, and 45°, 90°, and 135° for Bob. The overlapping angles allow basis reconciliation similar to BB84, while the non-overlapping angles enable security verification through Bell inequality violations.

When Alice and Bob measure in the same basis, their results exhibit perfect anti-correlation for the singlet state: if Alice measures horizontal, Bob measures vertical, and vice versa. By flipping one party's bits, they obtain correlated rather than anti-correlated keys. The critical security feature emerges when they measure in different bases: the correlations between their results violate classical local realism bounds quantified by the CHSH inequality. For the singlet state, the correlation function $E(a,b) = -\cos(2\theta)$ where $\theta$ is the angle between measurement bases, and the CHSH parameter $S = |E(a,b) - E(a,b') + E(a',b) + E(a',b')|$ reaches the Tsirelson bound of $2\sqrt{2} \approx 2.828$, exceeding the classical limit of two.

Any eavesdropping strategy Eve employs necessarily reduces entanglement between Alice's and Bob's photons, decreasing the observed Bell violation. If Alice and Bob measure a CHSH parameter above the classical bound, they certify that their systems share quantum correlations that Eve cannot fully possess—she cannot have pre-distributed classical correlation instructions reproducing quantum statistics without faster-than-light communication. This device-independent security feature represents E91's conceptual advantage: even with untrusted measurement apparatus, verifying Bell violations bounds Eve's information.

Practical E91 implementations face significant engineering challenges compared to BB84. Generating high-fidelity entangled photon pairs requires nonlinear optical processes such as spontaneous parametric down-conversion in beta-barium borate crystals or four-wave mixing in silicon photonic waveguides, with quantum state tomography verifying entanglement quality before protocol execution. Distributing entangled photons to separated parties over fiber or free-space links introduces decoherence from environmental interactions and polarization mode dispersion, degrading entanglement visibility. Synchronization becomes more complex, as Alice and Bob must coordinate measurements within the entanglement coherence time while compensating for differential path delays.

### B92 Protocol: Two-State Encoding

The B92 protocol, introduced by Bennett in 1992, minimizes the number of quantum states to two non-orthogonal polarizations, such as horizontal and 45-degree. Alice encodes bit zero as horizontal and bit one as 45-degree, transmitting photons in these states. Bob measures each photon in either the vertical or 135-degree basis—crucially, Bob's measurement bases are orthogonal to Alice's encoding states for one bit value but not the other. When Bob measures vertical and obtains a positive result, he conclusively knows Alice sent horizontal (bit zero), since 45-degree photons have zero amplitude along vertical. Similarly, detecting 135-degree proves Alice sent 45-degree (bit one). Inconclusive results, where Bob's measurement returns the opposite outcome, are discarded.

This protocol achieves security through ambiguous state discrimination: Eve cannot perfectly distinguish horizontal from 45-degree without introducing detectable errors, as these states are not orthogonal. The reduced state set compared to BB84 lowers the sifted key rate, since Bob's measurements yield conclusive results in only half the cases on average, and channel losses further reduce detection efficiency. However, B92's simplicity appeals to implementations constrained by source or detector complexity, particularly in integrated photonic circuits where generating four precisely controlled polarization states proves challenging.

### Photon Polarization Encoding and Basis Reconciliation

Physical realization of polarization-encoded QKD requires precise control over photon generation, transmission, and measurement. Alice employs either attenuated laser diodes producing weak coherent pulses with mean photon number around 0.1—approximating single-photon states at the cost of occasional multi-photon emissions—or true single-photon sources such as quantum dots, nitrogen-vacancy centers in diamond, or heralded photon pairs from parametric down-conversion. Polarization encoding uses Pockels cells, liquid crystal retarders, or waveplates to rotate photon polarization between horizontal, vertical, 45-degree, and 135-degree states with sub-nanosecond switching speeds to support megahertz repetition rates.

Transmission through single-mode optical fiber preserves polarization over distances up to 100 kilometers when using polarization-maintaining fiber, although birefringence and thermal fluctuations necessitate active polarization compensation using feedback-controlled motorized waveplates at the receiver. Free-space links offer lower loss for satellite-to-ground QKD, reaching 1000 kilometers with adaptive optics correcting atmospheric turbulence, but require precise pointing and tracking to maintain sub-microradian beam alignment.

Bob's measurement apparatus employs polarizing beam splitters to separate orthogonal polarization components, directing them to separate single-photon detectors. For two-basis protocols like BB84, Bob switches between rectilinear and diagonal measurement bases using Pockels cells or half-waveplates synchronized with Alice's transmission timing. Time-multiplexed schemes avoid active basis switching by splitting the incoming beam and simultaneously measuring in both bases, using photon arrival time to determine which basis applies for each detection event, at the cost of doubling detector count and dark count contributions.

Basis reconciliation over the classical channel occurs after quantum transmission concludes, with Bob announcing detection events by transmitting time-stamps or sequence numbers identifying successfully detected photons. Alice acknowledges which photons she transmitted and confirms basis matches. This exchange reveals to Eve which photons survived transmission and which bases Alice and Bob used, but not the actual bit values—Eve learns structure but not content, analogous to traffic analysis in network security. The authenticated classical channel typically runs over standard TCP/IP or dedicated cryptographic hardware, with message authentication codes computed using pre-shared symmetric keys to prevent man-in-the-middle attacks.

## 3. High-Performance Optimization & Failure Modes

Practical QKD systems must optimize secure key rate, the amount of certified secret key generated per second, which depends on photon transmission rate, channel loss, detector efficiency, error correction efficiency, and privacy amplification compression. The secure key rate formula for BB84 against individual attacks approximates:

$$R = q \cdot Q \cdot \left[ 1 - H_2(Q_{bit}) - f \cdot H_2(Q_{phase}) \right]$$

where $q$ is the probability of basis match (one-half for BB84), $Q$ is the overall gain including transmission and detection efficiency, $H_2(x) = -x\log_2(x) - (1-x)\log_2(1-x)$ is the binary Shannon entropy function, $Q_{bit}$ is the bit error rate, $Q_{phase}$ is the phase error rate (equal to $Q_{bit}$ for symmetric channels), and $f \geq 1$ is the error correction efficiency, typically ranging from 1.1 to 1.3 for modern LDPC codes. Channel loss dominates $Q$, with fiber attenuation of approximately 0.2 dB/km at 1550 nm wavelength translating to $Q = 10^{-0.02d}$ where $d$ is distance in kilometers, ignoring detector efficiency.

This loss scaling imposes fundamental distance limits: at 50 kilometers, fiber loss reduces transmission to one percent, while at 100 kilometers, transmission drops to 0.01 percent. Secure key rates fall below kilobits per second beyond 50 kilometers and approach zero near 150 kilometers for attenuated laser sources. True single-photon sources improve security by eliminating multi-photon vulnerabilities but do not overcome channel loss. Trusted repeater stations can extend range by performing independent QKD sessions across concatenated links, but this creates additional trust assumptions—each repeater must be physically secured, as compromised repeaters leak keys.

Quantum repeaters using entanglement purification and quantum error correction promise to overcome channel loss without trusted nodes, but current implementations remain at early research stages with limited fidelity and repetition rates. Alternative architectures employ satellite-based QKD, exploiting the reduced atmospheric absorption above 10 kilometers altitude and the absence of fiber loss through vacuum. The Chinese Micius satellite demonstrated 1000-kilometer QKD links with megahertz photon rates, establishing secure keys between ground stations separated by continental distances. Satellite links introduce different challenges: high relative velocity between satellite and ground station creates Doppler shifts requiring frequency tracking, and atmospheric turbulence necessitates adaptive optics with tip-tilt correction and higher-order wavefront compensation.

Decoy state protocols mitigate photon number splitting attacks against weak coherent pulse sources by randomly varying mean photon number between signal pulses, decoy pulses with lower intensity, and vacuum states. An eavesdropper performing photon number splitting cannot distinguish signal from decoy without measurement, causing detectable anomalies in decoy statistics. Alice and Bob analyze gain and error rates separately for each intensity level, using decoy state analysis to bound the single-photon contribution and detect multi-photon tampering. This technique recovers much of the performance and security of ideal single-photon sources while retaining the simplicity of laser diodes, making it standard in commercial QKD systems.

Detector vulnerabilities represent critical attack surfaces. Bright illumination attacks exploit the non-ideal behavior of avalanche photodiodes under strong continuous-wave illumination, disabling Geiger-mode operation and forcing linear detection where the output current becomes proportional to photon number. Eve injects bright classical light encoding her chosen bit values, and Bob's compromised detectors behave as classical photocurrent sensors, allowing Eve to control measurement outcomes while Bob remains unaware his detectors left the quantum regime. Countermeasures include optical power monitors detecting excess illumination, wavelength filtering to reject out-of-band light, and software monitoring for anomalous detection patterns.

Timing attacks exploit correlations between photon arrival time and detection efficiency. Certain detector models exhibit efficiency variations within a detection gate—for instance, efficiency rising then falling as the avalanche diode bias voltage settles after gate opening. Eve can shift photon arrival times within the gate to manipulate detection probabilities, biasing measurement outcomes toward states yielding higher efficiency. Mitigations require characterizing and calibrating detector timing response, randomizing gate timing, or using self-differencing detection schemes where efficiency variations cancel.

Trojan horse attacks involve Eve injecting bright probe pulses backward into Alice's encoding module, using reflected light to infer polarization settings. Alice's Pockels cell or liquid crystal modulator reflects a small fraction of incident light with polarization dependent on the applied voltage, leaking basis and bit information. Defenses install optical isolators blocking back-reflected light, monitor for unexpected photon arrivals on unused detectors, and use quantum non-demolition measurements or decoy verification on Alice's side to detect probing attempts.

Error correction efficiency critically impacts final key rate, as excess parity information leaked during reconciliation reduces the extractable secure key length. The cascade protocol iteratively corrects errors by partitioning the sifted key into blocks, computing parity for each block, and recursively subdividing blocks with incorrect parity until individual error positions are identified. While conceptually simple, cascade leaks approximately 1.2 times the Shannon entropy required to correct errors, limiting key rates. Low-density parity-check codes achieve near-Shannon-limit performance with leakage approaching 1.05 times Shannon entropy, and recent polar code constructions reach the finite-length optimal tradeoff between error correction capability and information leakage.

Privacy amplification must account for all information available to Eve: the observed QBER, parity information leaked during error correction, and potential side-channel leakage from implementation imperfections. Universal hashing constructs include Toeplitz matrices mapping $n$-bit input keys to $\ell$-bit output keys through matrix-vector multiplication over $GF(2)$, with $\ell$ chosen to ensure Eve's mutual information with the output becomes exponentially small in a security parameter. Trevisan's extractor offers deterministic construction with explicit security bounds but requires larger input key lengths. In practice, SHA-256 or SHA-3 often serve as privacy amplification functions, though their security relies on random oracle assumptions rather than proven universal hashing properties.

Continuous operation of QKD systems requires closed-loop stability control across multiple subsystems. Temperature stabilization maintains laser wavelength and detector bias voltage within millikelvin tolerance using thermoelectric coolers and PID feedback. Polarization drift compensation tracks birefringence changes in fiber links through pilot tone modulation or polarization scramblers with automated optimization. Clock synchronization between Alice and Bob employs GPS-disciplined oscillators or two-way time transfer achieving picosecond timing jitter, essential for correlating detection events with transmitted states at gigahertz repetition rates. These systems operate continuously, adapting to environmental variations and component aging while maintaining security certifications through real-time QBER monitoring and automated protocol abort thresholds.

Integration with existing network infrastructure positions QKD as a key generation service for symmetric encryption systems rather than a complete communication stack. Secure keys extracted from QKD feed into AES encryption for bulk data protection, with key refresh rates exceeding data transfer requirements to support one-time pad constructions for highest-security applications. Standardization efforts through ETSI and ITU-T define interoperability requirements, security certification procedures, and integration APIs, enabling multi-vendor deployments and quantum-secured VPNs spanning metropolitan and intercontinental scales.
