# Lesson 1: Licensing Foundations

## 1. First-Principles Intuition & Invariants

Every open source license is, at its mechanical core, a grant of permission layered on top of an existing copyright. This is the foundational invariant that practitioners must internalize before anything else makes sense: open source does not abolish copyright. It *uses* copyright. The entire apparatus — copyleft, permissive, dual licensing, compatibility matrices, contributor agreements — is a machine built on the fact that the moment a developer types source code into a buffer and saves it to disk, a non-negotiable, automatically-attached copyright interest springs into existence. That interest is what gives every open source license its teeth. Without copyright, there is nothing to license and nothing to enforce. The license is the lever; copyright is the fulcrum.

The Berne Convention of 1886, ratified by virtually every industrialized nation, established the principle of automatic copyright attachment. There is no registration step, no formal notice requirement, no filing fee. Fixation in a tangible medium of expression is sufficient. For software, "fixation" means the bytes exist on a non-volatile storage device — a disk, a flash cell, a network-attached object store. The author — defined by U.S. law as the natural person who created the work or, under the work-for-hire doctrine (17 U.S.C. § 101), the employer when the work is prepared within the scope of employment — holds the exclusive rights to reproduce, distribute, prepare derivative works, perform, and display. These five exclusive rights are the substrate on which every license operates. A license is a contractually or unilaterally granted waiver of some subset of these exclusivities, conditioned on the licensee meeting specified obligations.

This is why the distinction between "permissive" and "copyleft" is not a moral or philosophical categorization but a mechanical one about *which* exclusive rights are waived and under what conditions. A permissive license (MIT, BSD, ISC, Apache 2.0) grants near-universal permission to exercise all five exclusive rights — reproduce, distribute, prepare derivatives, perform, display — conditioned only on preserving attribution and, in the case of Apache 2.0, also granting a patent covenant. The licensee may create derivative works, close-source them, sell them, embed them in proprietary products. The license does not follow the derivative into the future. Copyleft licenses (GPLv2, GPLv3, AGPLv3, LGPL) grant the same reproduction and distribution rights but attach a *condition subsequent*: if you distribute a derivative work, you must license that derivative under the same copyleft terms. The GPL is not a restriction on use; it is a conditional permission. The condition is that downstream recipients receive the same freedoms you received. Richard Stallman articulated this as the Four Freedoms — freedom to run, study, redistribute, and modify — and the GPL is the legal instrument that enforces their propagation.

The most consequential invariant in this entire domain, and the one that causes the most production failures, is the derivative work boundary. A derivative work, under 17 U.S.C. § 101, is a work "based upon one or more preexisting works" — including revisions, recastings, transformations, or any other form in which a work may be recast, transformed, or adapted. For software, the boundary between "derivative work" and "mere aggregation" is the question that determines whether copyleft obligations attach. The Free Software Foundation's position, embodied in the GPL FAQ and tested (but never fully litigated to conclusion) in cases like *Jacobsen v. Katzer* and *Westinghouse v. Xiaomi*-adjacent disputes, is that static linking creates a derivative work but dynamic linking may or may not depending on the intimacy of the API boundary. The legal status of dynamic linking to GPL libraries from proprietary code remains, as a matter of black-letter law, unsettled. Practitioners must treat it as a risk-managed boundary, not a settled fact.

The second invariant is that licenses are not retroactively revocable in the general case. Once you distribute code under a license, that grant is perpetual and irrevocable for the version you distributed. The author can stop licensing *future* versions under different terms — this is the basis of dual licensing and the "license or commercial" model — but cannot claw back the grant already made. This is why MySQL could dual-license under GPLv2 and a commercial license simultaneously: each recipient chose which grant to operate under, and once they received GPLv2-licensed code, that grant persisted. The same mechanic powers Redis's 2018 BSD-to-SSPL transition (new versions only) and MongoDB's 2018 AGPL-to-SSPL transition.

The third invariant is that copyright ownership and copyright licensing are distinct and non-overlapping operations. Only the copyright holder (or a holder of an exclusive license) can sue for infringement. Only the copyright holder can grant a license. A contributor who signs a Contributor License Agreement (CLA) does not assign copyright; they grant a perpetual, irrevocable, sublicensable license to the project holder, which permits the holder to relicense the combined work. A contributor who signs a Contributor License Agreement that includes an *assignment* clause transfers ownership entirely. The distinction matters for relicensing authority: only the holder of all rights, or a holder with sufficient sublicensing rights from all contributors, can change the license of the whole. This is why the Qt Project requires a "Qt Assignment" for non-LGPL contributions, and why the Free Software Foundation requires copyright assignment for contributions to GNU projects — it gives the FSF standing to enforce and the authority to relicense.

---

## 2. Core Architecture & Mechanics

The license compatibility problem is, mechanically, a graph reachability problem on a directed acyclic graph of permission grants. Each license is a node. Each directed edge `A → B` means "code licensed under A can be incorporated into a work that is distributed under B." The graph is not symmetric. MIT code can be incorporated into a GPL project and the combined result distributed under GPL, because the MIT grant is a subset of the GPL grant. The reverse is impossible: GPL code cannot be incorporated into a work distributed solely under MIT, because the GPL's condition subsequent — that derivatives must also be GPL — cannot be satisfied by an MIT distribution that imposes no such condition on its own downstream recipients. The MIT license is, in graph-theoretic terms, a sink: everything flows into it, but nothing copyleft flows out of it.

The complete compatibility matrix for the dominant production licenses is the following. This is the working reference a systems engineer needs when auditing a dependency tree:

| Downstream → / Upstream ↓ | MIT | BSD-2/3 | ISC | Apache-2.0 | LGPL-2.1 | LGPL-3.0 | GPL-2.0 | GPL-3.0 | AGPL-3.0 |
|---|---|---|---|---|---|---|---|---|---|
| MIT | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| BSD-2/3 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| ISC | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Apache-2.0 | ✓ | ✓ | ✓ | ✓ | ✗¹ | ✗¹ | ✗² | ✓³ | ✓³ |
| LGPL-2.1 | ✓ | ✓ | ✓ | ✗⁴ | ✓ | ✗⁵ | ✓ | ✗⁵ | ✗⁵ |
| LGPL-3.0 | ✓ | ✓ | ✓ | ✗⁴ | ✗⁵ | ✓ | ✗⁵ | ✓ | ✓ |
| GPL-2.0 | ✓ | ✓ | ✓ | ✗² | ✓ | ✗⁵ | ✓ | ✗⁵ | ✗⁵ |
| GPL-3.0 | ✓ | ✓ | ✓ | ✓³ | ✗⁵ | ✓ | ✗⁵ | ✓ | ✓ |
| AGPL-3.0 | ✓ | ✓ | ✓ | ✓³ | ✗⁵ | ✓ | ✗⁵ | ✓ | ✓ |

The critical annotations are: ¹ Apache 2.0 contains a patent retaliation clause and an explicit patent grant that GPLv2-era licenses do not have a mechanism to receive; the FSF considers Apache 2.0 incompatible with GPLv2 and LGPL-2.1. ² Same incompatibility in the reverse direction — GPLv2 cannot absorb Apache 2.0 code. ³ GPLv3 §13 and AGPLv3 §13 explicitly extend compatibility to Apache 2.0 by name. ⁴ LGPL-2.1 and LGPL-3.0 are derived from GPL-2.0 and GPL-3.0 respectively and inherit their Apache 2.0 incompatibility for the underlying GPL layer. ⁵ The GPLv2/GPLv3 incompatibility is the single most consequential fracture in the open source licensing landscape, caused by the "or later version" clause: GPLv2-only code cannot be combined with GPLv3-or-later code, because GPLv3 is a different license with terms (patent retaliation, anti-tivoization) that GPLv2-only authors did not authorize.

The mechanics of the derivative work boundary in compiled languages are the most operationally consequential element of this architecture. When a C program statically links against a GPL-licensed library, the resulting binary is, by the FSF's position, a single derivative work. Distributing that binary triggers GPL obligations on the entire combined work — source must be provided for the application, the library, and the build scripts. When the same program dynamically links (`dlopen`, `LD_PRELOAD`, or standard `-l` shared object resolution at runtime), the FSF's published position (GPL FAQ) is that this *still* creates a derivative work because the application and library form a "combined work" at runtime through the intimate communication of function calls and shared memory space. The FSF draws the line at "arm's length" protocols — pipes, sockets, command-line invocation of separate processes — which create aggregation, not derivation. This is why the LGPL exists: it permits dynamic linking from any license, including proprietary, while requiring that the LGPL library itself remain modifiable by the end user (through the "LGPL relink" requirement — you must provide object files sufficient to re-link against a modified version of the library).

For compiled languages with more opaque module boundaries — Go's static compilation model, Rust's crate linkage, or WebAssembly modules — the boundary is murkier. Go compiles all dependencies into a single static binary, so any GPL dependency in a Go program makes the entire binary a derivative work under the FSF's interpretation. Rust's `cargo` build similarly produces a monolithic binary when using the default `rlib` static linkage. The dynamic boundary question that exists in C/C++ with `dlopen` does not have a clean analog in these ecosystems, which is why Go and Rust projects overwhelmingly prefer permissive (MIT, Apache 2.0, BSD) or weak-copyleft (MPL-2.0) dependencies over strong copyleft.

The Software Package Data Exchange (SPDX) standard, maintained by the Linux Foundation, is the production mechanism for machine-readable license declarations. Every source file should carry an SPDX-License-Identifier line as its first or second comment, and every package manifest (Cargo.toml, package.json, pyproject.toml, go.mod) should declare a license field resolvable to an SPDX identifier. The SPDX identifier set is the canonical vocabulary — `MIT`, `Apache-2.0`, `GPL-2.0-only`, `GPL-2.0-or-later`, `GPL-3.0-only`, `GPL-3.0-or-later`, `LGPL-2.1-or-later`, `AGPL-3.0-only`, `BSD-3-Clause`, `ISC`, `MPL-2.0`, `BSD-2-Clause`, `Unlicense`, `0BSD`. Composite expressions use `AND`, `OR`, and `WITH` (for exceptions like `GPL-3.0-only WITH GCC-exception-3.1`). A real permissive header looks like this:

```c
// SPDX-License-Identifier: Apache-2.0
// Copyright (c) [Year] [Entity Name]. All rights reserved.
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
```

A real GPLv3 header, in the FSF-recommended short form, looks like this:

```c
// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) [Year] [Author Name]
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

The `GPL-3.0-or-later` SPDX identifier is the critical field. The "or later" clause, which originates in the GPL's own preamble, grants the recipient the option to apply any later version of the GPL published by the FSF. Code licensed `GPL-2.0-only` — without the "or any later version" language — is permanently locked to GPLv2 and cannot be combined with GPLv3 code. This is why the Linux kernel, which is GPLv2-only by explicit decision of Linus Torvalds (documented in the kernel's `COPYING` file), cannot absorb GPLv3-licensed contributions. The kernel's position is structurally incompatible with the entire GPLv3 ecosystem. Any project that pulls in kernel-derived code inherits this lock. The practical consequence is that kernel-side systems work and userspace GPLv3 work (GCC, Bash, Glibc-adjacent) live in separate legal universes that cannot commingle at the source level.

Dual licensing exploits the fact that the copyright holder is not bound by the license they grant. The holder owns the copyright and may grant any number of non-exclusive licenses under any terms they choose simultaneously. The MySQL model, established by MySQL AB (later acquired by Sun, then Oracle) and replicated by Monty Program (MariaDB), Couchbase, and Qt (via The Qt Company), distributes the same source under GPLv2-or-later to the community and under a proprietary commercial license to paying customers. The community version carries copyleft obligations; the commercial version does not. The same bytes, two legal destinies. The mechanism requires that the dual-licensing entity hold either the complete copyright or, through CLAs, a sufficiently broad sublicensing right from all contributors. MySQL's Contributor Agreement grants MySQL AB a "perpetual, irrevocable, non-exclusive, worldwide, royalty-free, sublicensable" license — the word "sublicensable" is what makes dual licensing legally possible, because it permits MySQL AB to re-license the contribution under the commercial terms.

The Qt Project's model adds a wrinkle: Qt is dual-licensed under LGPL-3.0-or-later / GPL-3.0-or-later for open source use and under The Qt Company Commercial License for proprietary use. The LGPL choice means that dynamic linking from a proprietary application is permitted without a commercial license, *provided* the user can relink against a modified Qt. The commercial license is for developers who want to statically link Qt or who cannot meet the LGPL's relinking obligations. This is a more nuanced equilibrium than pure GPL dual licensing because the LGPL version itself already permits a substantial class of proprietary use — the commercial license is sold on the basis of static linking convenience and indemnification, not on the basis of permission to use at all.

The CLA landscape has two dominant instruments: the Apache Software Foundation CLA (a permissive grant model — contributors retain their copyright but grant Apache a broad license) and the Google/Harmony CLAs (used by Kubernetes, Istio, and most CNCF projects — a similar permissive grant with an explicit patent grant). The GNU Project uses a stricter "Copyright Assignment" form that transfers ownership to the FSF, which is why the FSF can relicense GNU software at will. The distinction between a CLA (license grant) and an assignment (ownership transfer) determines who has enforcement standing and who can relicense. A project that has accepted contributions under only a permissive CLA, without assignment, may not be able to change its license to a more restrictive one without re-obtaining consent from every contributor. This is what stalled the Redis relicensing conversation for years before the 2024 move to AGPL-plus-commercial dual licensing, which required a fork (Valkey) by contributors who refused the new terms and had the legal right to continue under the old BSD.

---

## 3. High-Performance Optimization & Failure Modes

The operational reality of license compliance in a production codebase is a dependency-graph traversal problem. A modern microservice may have 800 transitive dependencies in its lock file, each carrying one or more licenses, and the engineer responsible for shipping that service must verify that the composition is distributable. Manual review is infeasible at this scale. The production toolchain for this work is `scancode-toolkit` (the most thorough open-source scanner, which performs literal string matching against a database of license texts and produces structured JSON output), `license-expression` (a Python library for parsing and evaluating SPDX expressions), the `reuse` tool (the FSFE's compliance checker that validates SPDX headers across a repository), and commercial offerings like FOSSA and Black Duck that perform the same work at enterprise scale with continuous integration hooks.

The workflow, executed against a real repository, proceeds as follows. First, install the toolchain and run a scan of the source tree to detect declared and detected licenses:

```bash
pip install scancode-toolkit license-expression reuse
scancode --license --copyright --info --json-pp scan-results.json ./src
reuse lint
```

The `scancode` output is a structured report identifying, per file, the detected license (with a confidence score), the copyright holders, and any SPDX identifiers present in the file header. The `reuse lint` command checks whether every file has a valid SPDX-License-Identifier line and whether the repository's `LICENSES/` directory contains the full text of every referenced license — the requirement of the REUSE Specification, which is the de facto compliance standard for projects like the Linux kernel, KDE, and the FSFE's own infrastructure.

For a Rust project, `cargo` does not propagate license fields transitively with full fidelity, so the practitioner must use `cargo-about` or `cargo-deny` to materialize the full license tree:

```bash
cargo install cargo-about cargo-deny
cargo about generate about.hbs > license-report.html
cargo deny check licenses
```

The `cargo-deny` configuration, in `deny.toml`, is where the practitioner encodes the project's license policy as a declarative allowlist. A real configuration for a project that accepts permissive licenses and MPL-2.0 but rejects strong copyleft in dependencies looks like this:

```toml
[licenses]
allow = [
    "MIT",
    "Apache-2.0",
    "Apache-2.0 WITH LLVM-exception",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "Unicode-DFS-2016",
    "Unlicense",
    "Zlib",
    "MPL-2.0",
]
confidence-threshold = 0.8
exceptions = [
    { name = "unicode-normalization", allow = ["MIT", "Unicode-DFS-2016"] },
]
```

The `confidence-threshold` field is the score below which a license detection is treated as ambiguous and flagged for manual review. The default is 0.8, meaning scancode's matcher must be at least 80% confident in its classification. Lowering this threshold produces false positives; raising it produces false negatives. For a production build pipeline, the threshold should be set high enough to require manual review of any ambiguous dependency — the cost of a misclassified GPL dependency shipping inside a proprietary binary is not a lint warning; it is a legal exposure that can force a product recall or an emergency relicensing negotiation.

The most consequential failure mode in this domain is copyleft contamination of a permissively-licensed or proprietary tree. The scenario: an engineer adds a dependency on a small utility library, the dependency tree resolves, the build passes, and the binary ships. Three months later, an audit reveals the utility library was GPLv2-only. The binary is now, under the FSF's interpretation, a derivative work of GPLv2-only code and its distribution is a copyright infringement unless the entire combined work is released under GPLv2. The remediation is either to remove the dependency and rebuild, to negotiate a separate commercial license with the library's holder, or to accept the copyleft obligation and open-source the combined work. The first is almost always the correct production answer, and the reason that `cargo-deny`, `licensefinder` (for Ruby and Node ecosystems), and `pip-licenses` exist as continuous-integration gates is to prevent this contamination from reaching a shipped binary in the first place. The gate should fail the build, not produce a warning.

A subtler failure mode is the "viral" propagation of copyleft through transitive dependencies in ecosystems with weak metadata. NPM's `package.json` license field was, until the SPDX-only reform of recent years, a free-text field that accepted arbitrary strings — "BSD", "MIT-like", "see LICENSE", "GPL" — which made automated classification unreliable. The `license-checker` and `license-auditor` tools attempt to resolve these to SPDX identifiers but cannot resolve ambiguity in free-text fields. A transitive dependency declaring `license: "GPL"` in its package.json, with no SPDX identifier and no COPYING file in the tarball, is an unresolvable risk that must be treated as GPL-contaminating until the upstream maintainer is contacted and clarifies. The practitioner's response is to pin or remove the dependency, not to ship and hope.

The AGPL's network-use clause (§13 of AGPLv3) creates the single most operationally consequential failure mode in modern SaaS engineering. The AGPL extends the GPL's "distribution" trigger — the event that activates copyleft obligations — to cover *network interaction*. If a user interacts with the software over a network (e.g., a web application), that interaction triggers the source-disclosure obligation even though no binary distribution occurred. For a SaaS company that builds on an AGPL-licensed component, this means the company must provide the complete corresponding source of the entire modified AGPL'd work — including the application's own modifications — to every user who interacts with it over the network. MongoDB's original AGPL licensing was the canonical example: SaaS providers who used MongoDB as a data store were, by the FSF's reading, potentially obligated to disclose the source of their entire application. This is why MongoDB moved to the Server Side Public License (SSPL) in 2018 — to clarify and extend the network-use trigger — and why almost every major cloud provider either negotiates a separate commercial license or avoids AGPL/SSPL software in user-facing stacks. The production rule for AGPL in a SaaS codebase is binary: either you are willing to open-source the entire dependent stack, or you do not use AGPL-licensed dependencies. There is no middle path.

The dynamic-linking boundary, discussed in the mechanics section, is a live failure mode in containerized deployment. A Docker image that bundles a proprietary application binary alongside a GPL-licensed shared library, loaded via `LD_LIBRARY_PATH` or `ldconfig`, is distributing a combined work in the FSF's interpretation. The container is the distribution vehicle; the binary and the library execute in the same address space. The fact that the library is loaded at runtime rather than linked at build time does not, in the FSF's published position, escape the derivative work classification. The production-safe pattern is to run GPL-licensed services in separate containers (or separate processes communicating over Unix sockets or TCP) and to ensure that the proprietary application communicates with them over a network or IPC boundary — the "arm's length" protocol that the FSF considers aggregation rather than derivation. This is the architecture that Redis and PostgreSQL deployments in commercial products have used for years: the database runs in its own container, the application communicates over the network, and no copyleft obligation propagates to the application.

The final failure mode is relicensing risk. A project that a company depends on may relicense to a more restrictive license in a future version. The company's existing use, under the previously-granted license, persists (the license is irrevocable for the version received), but new versions may be unavailable under the old terms. The production mitigation is vendoring — pinning a specific version of the dependency and maintaining the vendored copy — or forking. The Valkey fork of Redis, the OpenSearch fork of Elasticsearch, the OpenTofu fork of Terraform, and the fork of HashiCorp's MPL-licensed products after the BSL transition are all instances of this pattern: the community preserves the last version under the permissive license and continues development independently. The legal predicate for forking is the persistence of the original license grant: the company cannot prevent the fork of the version released under the old license, only the use of the new version under the new terms. A practitioner evaluating a dependency should assess not only its current license but the holder's demonstrated willingness to maintain permissive terms — a holder that has relicensed once is a holder that may relicense again.
