# Lesson 2: Voice Leading in Jazz

## 1. First-Principles Intuition & Invariants

Voice leading is the connective tissue of jazz harmony. It governs how individual melodic lines within a chord progression move from one sonority to the next, operating at the intersection of counterpoint, acoustics, and cognitive psychology. At its foundation lies a deceptively simple principle: each note in a chord is a voice—an independent melodic strand—and the art of voice leading is the art of moving those strands between chords with the minimum necessary displacement while preserving harmonic clarity.

### The Counterpoint Heritage

Jazz voice leading inherits directly from the species counterpoint tradition codified by Fux and refined through common-practice harmony. The core invariants are:

- **Minimal motion principle.** Voices should move the shortest distance possible between chords. Common tones are retained; moving voices step rather than leap. This is not merely an aesthetic preference—it reflects the cognitive economy of the auditory system, which tracks melodic continuity more easily than discontinuity.
- **Contrary motion preference.** When two voices must move, they should preferentially move in opposite directions. This preserves the acoustic independence of voices and avoids the parallel perfect intervals that collapse multiple lines into a single perceived stream.
- **Dissonance resolution.** Dissonant intervals (tritones, sevenths, seconds, augmented intervals) resolve by step, typically downward. The classic case is the tritone of a dominant seventh chord: the 7th resolves downward by semitone to the 3rd of the next chord, and the 3rd resolves upward by semitone (or stays as a common tone) to the 7th of the next chord.

### The Guide-Tone Principle

A critical invariant distinguishes jazz voice leading from its common-practice ancestor: the **guide-tone principle**. The 3rd and 7th of any chord define its quality (major, minor, dominant, half-diminished). The root is typically supplied by the bassist, and the 5th is often omitted because it contributes no information about chord quality. Effective jazz voice leading therefore reduces to the movement of two voices—the 3rd and the 7th—between successive chords.

In a standard ii-V-I progression in C major (Dm7 → G7 → Cmaj7), the guide tones move with remarkable parsimony:

- **Dm7 → G7.** The 7th of Dm7 (C) resolves down by semitone to the 3rd of G7 (B). The 3rd of Dm7 (F) is retained as the 7th of G7 (F)—a common tone.
- **G7 → Cmaj7.** The 7th of G7 (F) resolves down by semitone to the 3rd of Cmaj7 (E). The 3rd of G7 (B) is retained as the 7th of Cmaj7 (B)—a common tone.

This creates a chain of semitone resolutions and common tones that threads through the entire progression with near-zero net displacement—the structural essence of parsimonious voice leading.

### The Mathematical Model: Voice Leading Spaces

The formal treatment of voice leading draws on geometrical music theory, particularly the work of Dmitri Tymoczko. The model is as follows:

A chord with n voices is an ordered point in ℝⁿ, where each coordinate is the pitch (in semitones or cents) of one voice. A **voice leading** from chord C = (c₁, c₂, ..., cₙ) to chord C′ = (c′₁, c′₂, ..., c′ₙ) is a vector v = (v₁, ..., vₙ) where c′ᵢ = cᵢ + vᵢ. The **size** of the voice leading is the L1 (taxicab) norm:

    ‖v‖₁ = Σᵢ |vᵢ|

The goal of parsimonious voice leading is to find the voice leading that minimizes this norm over all permutations of the target chord's pitch classes, allowing octave displacement. Two voice leadings are **path-equivalent** if they differ by a uniform transposition of all voices; they are **permutation-equivalent** if they differ by a reassignment of which voice moves where.

The **voice leading space** for n-voice chords is the orbifold ℝⁿ / (Sₙ × 𝕋), where Sₙ is the symmetric group (permutations of voices) and 𝕋 is the translation group (octave shifts). This space has the structure of an n-dimensional orbifold with singularities along the "walls" where two voices coincide. For practical jazz voice leading, we work in the 4-voice orbifold (for seventh chords) or the 5-voice orbifold (for chords with extensions).

Finding the minimal voice leading between two chords is an instance of the **assignment problem** in combinatorial optimization, solvable in O(n³) time via the Hungarian algorithm. For the small n (typically 4–6 voices) encountered in jazz, brute-force enumeration of all n! permutations is also tractable.

### Invariants Summary

The invariants of jazz voice leading, in order of priority:

1. **Guide
