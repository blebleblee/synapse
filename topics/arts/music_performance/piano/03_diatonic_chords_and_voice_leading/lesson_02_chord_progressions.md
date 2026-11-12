# Lesson 2: Common Chord Progressions

## 1. First-Principles Intuition & Invariants

In the realm of diatonic harmony, the interplay of chords within a scale is governed by a set of principles that underpin the emotional and structural integrity of music. These principles are deeply rooted in the physics of sound, the mathematics of frequency ratios, and the psychological responses of listeners. To understand common chord progressions, we must first delve into the foundational concepts of diatonic scales and the harmonic functions they afford.

A diatonic scale, whether major or minor, consists of seven distinct pitches that are related by specific intervals. In the context of Western music, the major scale is constructed from a sequence of whole and half steps: W-W-H-W-W-W-H. This sequence of intervals gives rise to a set of seven diatonic chords, each built on a scale degree and characterized by its unique harmonic function. These chords are typically denoted using Roman numerals, which correspond to their respective scale degrees: I, ii, iii, IV, V, vi, and vii°.

The harmonic function of a chord is determined by its relationship to the tonic chord (I), which serves as the tonal center of the scale. The tonic chord provides a sense of resolution and stability, while other chords create tension and movement towards this resolution. The most common chord progressions exploit these harmonic functions to create a compelling and emotionally resonant musical journey.

Consider the I-IV-V-I progression, a staple in popular music and classical forms alike. This progression leverages the dominant function of the V chord, which naturally resolves to the tonic I chord. The IV chord, being a subdominant, provides a contrasting yet harmonically stable pivot point. The sequence of intervals between these chords—perfect fourth, perfect fifth, and perfect fifth—creates a sense of forward motion and resolution, making it a powerful tool for composers and performers.

To explore the mathematical underpinnings of these chord progressions, we can examine the frequency ratios that define each chord. In equal temperament, the frequency of a note is determined by the formula \( f_n = f_0 \cdot 2^{n/12} \), where \( f_0 \) is the frequency of the reference pitch (typically A4 at 440 Hz) and \( n \) is the number of half steps from the reference pitch. For example, the frequency of the note C4 (middle C) is \( 261.63 \) Hz, while the frequency of the note G4 (the fifth scale degree of C major) is \( 392.00 \) Hz. The ratio of these frequencies is \( \frac{392.00}{261.63} \approx 1.5 \), which corresponds to a perfect fifth. This ratio is a fundamental building block of diatonic harmony and contributes to the consonant and pleasing nature of common chord progressions.

The emotional impact of chord progressions is also influenced by the way chords are voiced and the intervals between their notes. A chord voicing refers to the specific arrangement of notes within a chord, and different voicings can emphasize different harmonic functions and create distinct textures. For example, in a C major chord (C-E-G), the root position places the root note C in the bass, while the first inversion places the third E in the bass. The choice of voicing can affect the perceived stability or tension of a chord, and thus the overall emotional trajectory of a progression.

## 2. Core Architecture & Mechanics

To dissect the internal data structures and algorithms that govern chord progressions, we can employ a conceptual framework that models the relationships between chords and their harmonic functions. This framework can be visualized using a directed graph, where each node represents a chord and each edge represents a transition between chords. The weight of each edge can be determined by the harmonic function of the destination chord relative to the source chord.

Consider the following directed graph, which represents a simplified model of common chord progressions in the key of C major:

```mermaid
graph TD;
    C -->| "IV" | F;
    F -->| "V" | G;
    G -->| "I" | C;
    C -->| "vi" | Am;
    F -->| "vi" | Am;
    G -->| "vi" | Am;
    C -->| "iii" | Em;
    F -->| "iii" | Em;
    G -->| "iii" | Em;
    C -->| "ii" | Dm;
    F -->| "ii" | Dm;
    G -->| "ii" | Dm;
```

In this graph, each node represents a diatonic chord, and each directed edge represents a common transition between chords. The edges are labeled with the Roman numeral notation of the destination chord, and the graph is organized in a way that highlights the harmonic functions of each chord. For example, the edge from C (I) to G (V) represents a dominant function, while the edge from G (V) to C (I) represents a tonic function.

To further illustrate the mechanics of chord progressions, we can examine the internal data structures that represent chords and their voicings. A chord can be represented as a set of notes, where each note is defined by its pitch class and octave. For example, the C major chord can be represented as the set {C4, E4, G4}. A voicing of a chord can be represented as a permutation of this set, where the order of notes reflects the desired harmonic emphasis. For example, the first inversion of the C major chord can be represented as the set {E4, G4, C5}.

The algorithms that govern chord progressions can be modeled as functions that generate sequences of chords based on a set of rules or constraints. For example, a simple algorithm for generating a I-IV-V-I progression in the key of C major can be defined as follows:

1. Start with the tonic chord C (I).
2. Transition to the subdominant chord F (IV).
3. Transition to the dominant chord G (V).
4. Transition back to the tonic chord C (I).

This algorithm can be extended to include additional chords and more complex progressions by incorporating additional rules and constraints. For example, a more sophisticated algorithm might include rules for modulating to a different key, incorporating secondary dominants, or using modal interchange chords.

## 3. High-Performance Optimization & Failure Modes

In the context of chord progressions, high-performance optimization and failure modes can be understood in terms of the efficiency and effectiveness of the algorithms that generate and manipulate chord sequences. To optimize the performance of these algorithms, we can employ a variety of techniques, such as memoization, dynamic programming, and heuristic search.

Memoization is a technique that involves storing the results of expensive function calls and reusing them when the same inputs occur again. In the context of chord progressions, memoization can be used to store the results of chord transitions and avoid redundant calculations. For example, if the algorithm has already computed the set of chords that can follow a given chord, it can reuse this set instead of recalculating it.

Dynamic programming is a technique that involves breaking down a complex problem into a set of simpler subproblems and solving each subproblem only once. In the context of chord progressions, dynamic programming can be used to efficiently generate chord sequences by storing the results of previously computed subproblems and reusing them to solve larger problems. For example, when generating a progression that includes a modulation to a different key, dynamic programming can be used to store the results of chord transitions in the new key and reuse them to generate the full progression.

Heuristic search is a technique that involves using problem-specific knowledge to guide the search for solutions. In the context of chord progressions, heuristic search can be used to generate progressions that meet specific criteria, such as a particular emotional tone or a specific harmonic function. For example, a heuristic search algorithm might prioritize transitions that create tension and resolution in a specific way, or that incorporate specific chords to create a desired mood.

Understanding the failure modes of these algorithms is also crucial for optimizing their performance. Common failure modes include infinite loops, incorrect chord transitions, and suboptimal progressions. To mitigate these issues, it is important to implement robust validation checks and to continuously refine the algorithms based on feedback and analysis of their performance.
