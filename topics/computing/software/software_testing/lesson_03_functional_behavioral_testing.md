# Lesson 3: Functional Behavioral Testing

## 1. First-Principles Intuition & Invariants

Every program is, at its core, a mathematical function: it consumes inputs drawn from some domain and produces outputs drawn from some codomain, while optionally mutating observable state. Functional behavioral testing is the discipline of reasoning rigorously about that mapping without reading the source. You treat the system as a black box, characterize the input space, partition it into equivalence classes, probe the boundaries where behavior changes, model the state machine that governs transitions, and generate test cases from that model with combinatorial precision. This is not a shortcut for people who cannot read code. It is the only method that scales: no matter how large a codebase grows, the behavioral specification remains the contract against which you test.

The foundational intuition is that the input domain of any real function is astronomically large. A function that accepts two 32-bit integers already has $2^{64}$ distinct input pairs. No test suite will ever be exhaustive, so the central engineering problem of functional testing is selecting the minimum set of inputs that maximizes fault detection. The theoretical basis for solving this problem comes from two observations that have held up across decades of industrial experience.

The first is the **uniform behavior hypothesis**: within a correctly identified equivalence class, the program exhibits the same behavior for every member. If a function misbehaves for one member of a class, it misbehaves for all of them. This is the invariant that makes equivalence partitioning useful. You need not test every 32-bit integer passed to a bounds-checking routine; you need one representative from "within range," one from "below range," and one from "above range." The practical leverage is enormous. The theoretical justification is that most faults correspond to incorrect predicates or missing branches in the implementation, and those faults affect all inputs that follow the same execution path through the predicate.

The second is the **boundary sensitivity hypothesis**: faults cluster at the edges of equivalence classes, not in their interiors. A developer who writes `if (n > 100)` when the specification demands `if (n >= 100)` has introduced a fault that is invisible for every input except `n = 100` itself. This observation, empirically validated across industrial codebases at IBM, Microsoft, and Google, transforms boundary value analysis from an academic heuristic into a production engineering requirement.

Together, these two invariants define the core contract of functional behavioral testing: partition the domain exhaustively, then sample each partition at its interior and its edges. Everything else — decision tables, state-based testing, combinatorial theory — is a systematic application of these two principles to increasingly complex input structures.

It is worth pausing on what "black box" actually means in a production context, because senior engineers sometimes conflate it with ignorance. Black-box testing does not mean you have no access to the specification; it means you derive test cases from the behavioral contract rather than from the implementation. In practice, the most dangerous form of specification-blind testing happens when engineers write tests after reading the code: they unconsciously replicate the developer's mental model, including its mistakes. A test derived from the specification independently of the implementation is structurally capable of catching faults that the developer did not know to guard against. This independence is a formal requirement in DO-178C (airborne software certification), IEC 61508 (functional safety), and ISO 26262 (automotive), not because regulators are pedantic, but because decades of incident investigation showed that implementation-derived tests miss systematic errors.

The core invariants you must maintain throughout any functional behavioral testing effort are therefore: the test oracle is the specification, never the implementation; equivalence classes must partition the input domain with no gaps and no overlaps; boundaries must be tested at the exact edge value and the values immediately adjacent; and the test suite must remain valid when the implementation is replaced, because a correct reimplementation should pass every test.

---

## 2. Core Architecture & Mechanics

### Equivalence Partitioning: Formal Construction

Equivalence partitioning begins with enumerating all input variables, then for each variable identifying the predicates in the specification that change behavior as the variable crosses a threshold. Each contiguous region in which the specification defines uniform behavior is a valid class. Each region in which the specification defines invalid or error behavior is an invalid class. Both types require test cases: valid classes verify correct behavior, and invalid classes verify that the system rejects, bounds-checks, or signals errors correctly.

Consider a concrete, non-trivial example: a Rust library function that parses an HTTP content-length header and returns a validated byte count.

```rust
/// Parses the value of a Content-Length header field.
///
/// # Specification
/// - The input must be a non-empty ASCII decimal string with no leading zeros
///   (except the value "0" itself).
/// - The parsed value must fall in the range [0, 2^63 - 1] (i64::MAX).
/// - Surrounding whitespace is not permitted.
/// - Returns Ok(u64) on success, Err(ParseError) on any violation.
#[derive(Debug, PartialEq)]
pub enum ParseError {
    Empty,
    LeadingZero,
    NonDecimalCharacter(char),
    Overflow,
    TrailingWhitespace,
    LeadingWhitespace,
}

pub fn parse_content_length(s: &str) -> Result<u64, ParseError> {
    if s.is_empty() {
        return Err(ParseError::Empty);
    }
    if s.starts_with(' ') || s.starts_with('\t') {
        return Err(ParseError::LeadingWhitespace);
    }
    if s.ends_with(' ') || s.ends_with('\t') {
        return Err(ParseError::TrailingWhitespace);
    }
    let bytes = s.as_bytes();
    if bytes.len() > 1 && bytes[0] == b'0' {
        return Err(ParseError::LeadingZero);
    }
    let mut acc: u64 = 0;
    for c in s.chars() {
        if !c.is_ascii_digit() {
            return Err(ParseError::NonDecimalCharacter(c));
        }
        acc = acc
            .checked_mul(10)
            .and_then(|v| v.checked_add((c as u8 - b'0') as u64))
            .ok_or(ParseError::Overflow)?;
    }
    Ok(acc)
}
```

The equivalence partition table for this function looks like the following. Each row is a class with a representative input, the expected output, and the fault hypothesis it targets.

| Class ID | Description | Representative Input | Expected Result |
|---|---|---|---|
| EC-V1 | Valid single digit | `"7"` | `Ok(7)` |
| EC-V2 | Valid multi-digit, no leading zero | `"1048576"` | `Ok(1048576)` |
| EC-V3 | Valid boundary zero | `"0"` | `Ok(0)` |
| EC-V4 | Valid maximum (i64::MAX) | `"9223372036854775807"` | `Ok(9223372036854775807)` |
| EC-I1 | Empty string | `""` | `Err(Empty)` |
| EC-I2 | Leading whitespace | `" 42"` | `Err(LeadingWhitespace)` |
| EC-I3 | Trailing whitespace | `"42 "` | `Err(TrailingWhitespace)` |
| EC-I4 | Leading zero on non-zero value | `"007"` | `Err(LeadingZero)` |
| EC-I5 | Non-decimal character mid-string | `"12x4"` | `Err(NonDecimalCharacter('x'))` |
| EC-I6 | Overflow by one | `"9223372036854775808"` | `Err(Overflow)` |
| EC-I7 | Massively overflowing value | `"99999999999999999999"` | `Err(Overflow)` |

The test code for this partition table is direct and mechanical:

```rust
#[cfg(test)]
mod equivalence_partition_tests {
    use super::*;

    #[test]
    fn ec_v1_single_digit() {
        assert_eq!(parse_content_length("7"), Ok(7));
    }

    #[test]
    fn ec_v2_multi_digit_no_leading_zero() {
        assert_eq!(parse_content_length("1048576"), Ok(1_048_576));
    }

    #[test]
    fn ec_v3_valid_zero() {
        assert_eq!(parse_content_length("0"), Ok(0));
    }

    #[test]
    fn ec_v4_valid_maximum() {
        assert_eq!(
            parse_content_length("9223372036854775807"),
            Ok(9_223_372_036_854_775_807)
        );
    }

    #[test]
    fn ec_i1_empty_string() {
        assert_eq!(parse_content_length(""), Err(ParseError::Empty));
    }

    #[test]
    fn ec_i2_leading_whitespace() {
        assert_eq!(
            parse_content_length(" 42"),
            Err(ParseError::LeadingWhitespace)
        );
    }

    #[test]
    fn ec_i3_trailing_whitespace() {
        assert_eq!(
            parse_content_length("42 "),
            Err(ParseError::TrailingWhitespace)
        );
    }

    #[test]
    fn ec_i4_leading_zero_on_nonzero() {
        assert_eq!(parse_content_length("007"), Err(ParseError::LeadingZero));
    }

    #[test]
    fn ec_i5_non_decimal_character() {
        assert_eq!(
            parse_content_length("12x4"),
            Err(ParseError::NonDecimalCharacter('x'))
        );
    }

    #[test]
    fn ec_i6_overflow_by_one() {
        assert_eq!(
            parse_content_length("9223372036854775808"),
            Err(ParseError::Overflow)
        );
    }

    #[test]
    fn ec_i7_massive_overflow() {
        assert_eq!(
            parse_content_length("99999999999999999999"),
            Err(ParseError::Overflow)
        );
    }
}
```

### Boundary Value Analysis: The Mechanics of Edge Sampling

Boundary value analysis (BVA) refines equivalence partitioning by mandating test cases at the boundary itself, the value immediately inside the valid class, and the value immediately outside. For a continuous integer domain with the valid range $[a, b]$, the canonical five-point BVA probe is: $a - 1$, $a$, $a + 1$, $b - 1$, $b$, $b + 1$. The rationale is that off-by-one errors in relational operators (`<` versus `<=`, `>` versus `>=`) are invisible at all points except the boundary itself and its immediate neighbors.

The extended boundary value technique, sometimes called "robustness BVA," additionally probes the minimum value of the type below $a - 1$ and the maximum value above $b + 1$. This surfaces faults in overflow guards and in code that attempts to cast between integer types without range checking. For the `parse_content_length` example, the numerical boundary of interest is the i64::MAX / u64 boundary at 9,223,372,036,854,775,807. The BVA probe set for that boundary is:

```rust
#[cfg(test)]
mod boundary_value_tests {
    use super::*;

    // Boundary: i64::MAX - 1 (inside valid class, one step below boundary)
    #[test]
    fn bva_max_minus_one() {
        assert_eq!(
            parse_content_length("9223372036854775806"),
            Ok(9_223_372_036_854_775_806)
        );
    }

    // Boundary: i64::MAX exactly (the boundary itself)
    #[test]
    fn bva_max_exact() {
        assert_eq!(
            parse_content_length("9223372036854775807"),
            Ok(9_223_372_036_854_775_807)
        );
    }

    // Boundary: i64::MAX + 1 (first value in invalid class)
    #[test]
    fn bva_max_plus_one() {
        assert_eq!(
            parse_content_length("9223372036854775808"),
            Err(ParseError::Overflow)
        );
    }

    // Boundary: 0 exactly (minimum valid value)
    #[test]
    fn bva_min_exact() {
        assert_eq!(parse_content_length("0"), Ok(0));
    }

    // Boundary: minimum valid class, one step above (single digit)
    #[test]
    fn bva_min_plus_one() {
        assert_eq!(parse_content_length("1"), Ok(1));
    }
}
```

This mechanical rigor matters enormously in parser code, cryptographic length fields, and protocol framing logic, precisely the contexts where your audience writes software daily. A missing `>=` versus `>` distinction in a TLS record length parser or a JVM bytecode verifier has historically been a critical vulnerability.

### Decision Tables: Specifying Multi-Condition Logic

When a system's output depends on the interaction of multiple independent boolean or enumerated conditions, equivalence partitioning of each variable independently is insufficient. The conditions interact, and the fault may live not in the handling of any single condition but in the combination. Decision tables are the structured method for capturing this interaction and generating tests that cover every distinct combination of condition states.

A decision table has four regions: the condition stub (naming each condition), the condition entries (the state of each condition for one test scenario), the action stub (naming the expected outcomes), and the action entries (which outcomes fire for each scenario). Each column is one rule, and the table is exhaustive when every combination of condition states appears in at least one column.

Consider a session authorization function in a web backend: it must check whether the requesting user is authenticated, whether the requested resource is owned by that user, and whether the resource's access policy is set to public. The expected behavior matrix is:

```
┌──────────────────────────────┬────┬────┬────┬────┬────┬────┬────┬────┐
│ Condition                    │ R1 │ R2 │ R3 │ R4 │ R5 │ R6 │ R7 │ R8 │
├──────────────────────────────┼────┼────┼────┼────┼────┼────┼────┼────┤
│ C1: User authenticated?      │  N │  N │  N │  N │  Y │  Y │  Y │  Y │
│ C2: User owns resource?      │  N │  N │  Y │  Y │  N │  N │  Y │  Y │
│ C3: Resource is public?      │  N │  Y │  N │  Y │  N │  Y │  N │  Y │
├──────────────────────────────┼────┼────┼────┼────┼────┼────┼────┼────
