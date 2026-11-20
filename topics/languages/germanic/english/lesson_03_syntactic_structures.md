# Lesson 3: Syntactic Structures

## 1. First-Principles Intuition & Invariants

English syntax operates as a constrained generative system where linear word order encodes grammatical relationships that other Germanic languages express through rich morphological case marking. While German retains a four-case declension system and Dutch preserves vestiges of genitive marking, English has undergone radical analytic drift, stripping away inflectional morphology and replacing it with rigid positional templates and an elaborate auxiliary verb architecture. This structural transformation—accelerated during the Middle English period through contact with Norman French and subsequent case syncretism—has produced a language where syntactic position functions as the primary carrier of grammatical meaning. The subject-verb-object canonical order is not a stylistic preference but a grammatical necessity: "The dog bit the man" and "The man bit the dog" encode diametrically opposed semantic propositions through word order alone, whereas German könnte rely on case marking to disambiguate even under scrambled configurations.

The fundamental invariant governing English phrase structure is the **X-bar schema**, a universal template that projects syntactic categories into hierarchical constituent structures. Every phrasal category—whether noun phrase, verb phrase, adjective phrase, or prepositional phrase—conforms to a three-level architecture: the lexical head (X⁰), an intermediate projection (X′) that combines the head with its complement, and a maximal projection (XP) that hosts specifiers. This recursive scaffolding generates the tree structures that underlie every English sentence, from simple declaratives to complex embedded clauses with multiple levels of subordination.

English differs crucially from its West Germanic siblings in its impoverished verbal morphology. Modern German preserves distinct strong and weak conjugation classes, modal verb paradigms with stem-vowel ablaut, and productive participle formations. English has collapsed these distinctions into a minimal three-form system for most verbs: base form, past tense, and past participle. The verb "to walk" inflects as walk-walked-walked; even irregular verbs rarely exceed five distinct forms. This morphological poverty forces English to externalize tense, aspect, mood, and voice distinctions through auxiliary verb chains and periphrastic constructions. The perfect aspect requires the auxiliary "have" plus past participle; the progressive aspect demands "be" plus present participle; passive voice constructs emerge from "be" plus past participle; future tense arises through modal "will" or "shall" plus bare infinitive. A sentence like "The report will have been being written" stacks four auxiliary verbs in a rigid linear sequence that encodes future perfect progressive passive semantics—a configuration unthinkable without English's analytic compensatory mechanisms.

Case assignment in English operates through abstract structural positions rather than overt morphological marking. Nominative case is assigned to subjects in the specifier position of a finite tense phrase; accusative case is assigned to direct objects that serve as complements to transitive verbs; genitive case survives only in possessive constructions marked by clitic *'s* or prenominal possessive determiners. The pronominal system preserves a three-way case distinction—nominative "I/he/she/we/they," accusative "me/him/her/us/them," and genitive "my/his/her/our/their"—but this morphological residue exists as a frozen paradigm rather than a productive grammatical system. Prepositions govern accusative case objects, though this is visible only in pronouns: "between you and me" maintains case government where nouns show no morphological distinction.

Agreement systems in English have atrophied compared to other Germanic languages. Subject-verb agreement survives as a singular third-person present-tense suffix *-s* ("he walks" versus "they walk"), a minimal reflex of the elaborate person-number paradigms preserved in German and Icelandic. Adjectives show zero agreement with nouns in number, gender, or case—"the tall man" and "the tall women" use identical adjectival forms—whereas German requires adjectival endings that vary across strong, weak, and mixed declension patterns depending on the definiteness and case of the noun phrase. This agreement impoverishment reflects the broader morphological simplification that has reshaped English syntax, shifting grammatical weight from inflectional suffixes to functional heads and syntactic positions.

The architecture of the English clause is governed by two cardinal principles: **verb-second constraint in matrix clauses** (inherited from Proto-Germanic but now restricted to subject-verb inversion in questions and after fronted adverbs) and **head-initial directionality** (where syntactic heads precede their complements). Unlike German, which retains robust verb-second word order in main clauses and verb-final order in subordinate clauses, English has settled on a uniform SVO template across clause types, with subject-auxiliary inversion reserved for interrogatives and a handful of marked constructions. This positional rigidity interacts with a rich inventory of movement operations—wh-movement, subject-auxiliary inversion, tough-movement, raising, and extraposition—that permute underlying structures into surface linear orders while preserving the hierarchical relationships encoded in phrase structure trees.

## 2. Core Architecture & Mechanics

The generative capacity of English syntax derives from **phrase structure rules** that recursively expand categories into hierarchical constituent structures. The canonical clause architecture follows the schema **CP → C′ → TP → T′ → vP → v′ → VP**, where CP (complementizer phrase) hosts clause-type markers and extracted wh-elements, TP (tense phrase) encodes temporal anchoring and subject agreement, vP (light verb phrase) introduces external arguments and causative semantics, and VP (verb phrase) contains the lexical verb and its internal arguments. This layered architecture explains phenomena that appear arbitrary under surface analysis but follow from principled interactions between functional projections.

Consider the derivation of a simple transitive sentence: "The committee approved the proposal." The verb "approve" projects a VP with the direct object "the proposal" as its complement. This VP merges with a light verb head *v* that introduces the external argument "the committee" as its specifier, forming vP. The vP then merges with a tense head T bearing present-tense and third-person-singular features, projecting TP. The subject "the committee" moves from its base-generated position in Spec-vP to Spec-TP to satisfy the Extended Projection Principle, which requires all finite clauses to have an overt subject in the specifier of TP. The verb "approve" raises from V⁰ to v⁰ (to collect the external argument) and then to T⁰ (to realize tense and agreement morphology), surfacing as the inflected form "approved" in the linear string.

```text
                    TP
                   /  \
                  /    \
              DP[nom]   T′
         (the committee) |
                        / \
                       /   \
                     T⁰    vP
                  [+past]   |
                   approved / \
                           /   \
                       t(DP)   v′
                               |
                              / \
                             /   \
                           v⁰    VP
                          t(V)    |
                                 / \
                                /   \
                              V⁰    DP[acc]
                            t(V) (the proposal)
```

This tree structure captures several critical syntactic properties. First, the subject originates inside the vP as the specifier of the light verb projection, where it receives its thematic role (agent), but then moves to Spec-TP to satisfy case and agreement requirements—nominative case is assigned under Spec-Head agreement with the finite tense head. Second, the verb undergoes successive head movement through the functional spine, collecting inflectional features at each landing site. Third, the direct object remains in situ as the complement of VP, where it receives accusative case under government by the transitive verb head.

Auxiliary verb constructions reveal the hierarchical stacking of functional projections above the lexical VP. The auxiliary "have" occupies the head of an Aspect Phrase (AspP) that selects a VP headed by a past participle; the auxiliary "be" in progressive constructions occupies a lower Aspect head selecting a present participle VP; modal auxiliaries like "will" or "must" occupy a Modality Phrase (ModP) that selects a bare infinitive TP. These functional heads impose strict selectional requirements on their complements, generating the rigid ordering constraints visible in auxiliary chains: modals precede perfect "have," which precedes progressive "be," which precedes passive "be," which precedes the lexical verb.

The sentence "The document should have been being reviewed" instantiates this functional hierarchy:

```text
                         ModP
                        /    \
                       /      \
                   DP[nom]    Mod′
              (the document)   |
                              / \
                             /   \
                          Mod⁰   AspP(perf)
                         should    |
                                  / \
                                 /   \
                            Asp⁰(perf) AspP(prog)
                              have      |
                                       / \
                                      /   \
                                Asp⁰(prog)  VoiceP(pass)
                                   being      |
                                             / \
                                            /   \
                                      Voice⁰    VP
                                        been     |
                                                / \
                                               /   \
                                             V⁰    t(DP)
                                          reviewed
```

Each auxiliary head imposes categorial selection on its complement: the modal "should" selects a bare infinitive AspP; perfect "have" selects a past participle AspP; progressive "being" selects a present participle VoiceP; passive "been" selects a past participle VP. The subject "the document" originates as the internal argument of "review" (theme), moves to the specifier of passive VoiceP (where external argument is suppressed), and ultimately raises to Spec-ModP to receive nominative case. This explains why English prohibits sequences like *"should been having reviewed"—the selectional requirements of each functional head constrain the morphological form of its complement.

**Movement operations** permute underlying hierarchical structures into surface linear orders while leaving interpretive relationships intact. Wh-movement displaces interrogative phrases from their base-generated argument positions to the specifier of CP, creating long-distance dependencies that can span multiple clause boundaries. In the question "What did the committee approve?", the wh-element "what" originates as the direct object of "approve" but moves to Spec-CP, leaving behind a trace that marks its extraction site. Subject-auxiliary inversion accompanies this movement: the auxiliary "did" raises from T⁰ to C⁰, yielding the characteristic verb-second configuration of English matrix questions.

```text
                      CP
                     /  \
                    /    \
                 WH       C′
                (what)     |
                          / \
                         /   \
                       C⁰    TP
                      did     |
                             / \
                            /   \
                        DP[nom]  T′
                   (the committee) |
                                  / \
                                 /   \
                              t(C)   vP
                                      |
                                     / \
                                    /   \
                                t(DP)   v′
                                        |
                                       / \
                                      /   \
                                    v⁰    VP
                                   t(V)    |
                                          / \
                                         /   \
                                       V⁰    t(WH)
                                    approve
```

Wh-movement obeys strict locality constraints formalized as **islands**: extractions from within coordinate structures, adjunct clauses, and complex noun phrases produce ungrammaticality. The coordinate structure constraint blocks *"What did the committee approve the budget and t?"—wh-extraction cannot target one conjunct of a coordination while leaving the other intact. The adjunct island constraint rules out *"Why did the committee approve the proposal because t?"—extraction from within a causal adjunct violates island constraints. The complex noun phrase constraint prohibits *"What did the committee discuss the proposal that included t?"—extraction from within a relative clause embedded inside a direct object DP is illicit.

**Case assignment** in English follows structural configurations rather than morphological marking on nouns. Nominative case is assigned to subjects in Spec-TP under Spec-Head agreement with a finite tense head; accusative case is assigned to direct objects under government by a transitive verb or preposition; genitive case is assigned within DP through the possessive clitic *'s* or prenominal possessive determiners. Exceptional case marking (ECM) constructions reveal that case assignment can cross clause boundaries when the embedded clause is non-finite. In "The committee believes [him to be qualified]," the pronoun "him" appears in accusative case despite functioning as the subject of the infinitival clause—it receives case from the matrix verb "believes" rather than from the non-finite T⁰ head "to," which lacks case-assigning capacity.

Passivization alters case-assignment geometry by suppressing the external argument and promoting the internal argument to subject position. In "The proposal was approved by the committee," the theme argument "the proposal" originates as the direct object of "approve" but cannot receive accusative case because the passive Voice head absorbs the verb's case-assigning capacity. The DP "the proposal" must therefore move to Spec-TP to receive nominative case, yielding the derived subject configuration. The demoted agent surfaces as an optional by-phrase adjunct, marking its non-structural status—passive subjects are syntactic subjects but not thematic agents.

**Agreement systems** in English operate through Spec-Head configurations where a functional head bearing phi-features (person, number, gender) enters into an Agree relation with a goal DP bearing matching features. Subject-verb agreement arises when T⁰ probes its c-command domain for a DP bearing nominative case and establishes an Agree relation that values the phi-features on both elements. In "The committee approves the proposal," the third-person-singular features on T⁰ are valued by the subject DP "the committee," triggering the overt reflex *-s* on the verb. Plural subjects block this morphological realization: "The committees approve the proposal" shows zero marking because plural agreement in English is phonologically null.

Agreement fails to obtain across certain configurational boundaries. Expletive constructions like "There are three proposals on the table" display agreement between the finite verb "are" and the post-verbal associate "three proposals" despite the expletive "there" occupying the canonical subject position. This configuration reveals that agreement is a structural relation between T⁰ and the closest DP bearing phi-features, not a surface positional relation between the first DP and the verb.

**Subordination** in English is mediated by complementizer heads that select clause types and encode embedding relationships. Finite declarative complements are introduced by the overt complementizer "that" or by a null C⁰ head: "The committee believes (that) the proposal has merit." Interrogative complements are introduced by the complementizer "if" or "whether": "The committee asked whether the proposal had merit." Infinitival complements lack overt complementizers but project a CP headed by a null C⁰ that selects a TP headed by the infinitival marker "to": "The committee expects [CP ∅ [TP PRO to approve the proposal]]." The embedded subject position is occupied by a null pronoun PRO, whose interpretation is controlled by the matrix subject—PRO in this configuration is understood as coreferential with "the committee."

Relative clauses constitute a distinct subordination type where a CP modifies a noun phrase head. Restrictive relative clauses in English are introduced by relative pronouns ("who," "which," "that") that originate as arguments or adjuncts within the relative clause and move to Spec-CP: "The proposal [CP which [TP the committee approved t]]." Non-restrictive relative clauses, set off by comma intonation, provide supplementary information and are introduced by wh-pronouns only: "The proposal, which the committee approved, will be implemented." The distribution of "that" versus wh-pronouns as relative clause introducers is governed by syntactic position: "that" is blocked in non-subject extractions and in non-restrictive relatives, while wh-pronouns are licensed in all positions.

**Coordination** conjoins constituents of like syntactic category through coordinating conjunctions ("and," "or," "but") that head Coordination Phrases (ConjP). Coordination obeys the **Law of Coordination of Likes**, which requires that conjoined elements share the same categorial status: VPs conjoin with VPs, NPs with NPs, APs with APs, but cross-category coordination is illicit. The sentence "The committee [VP approved the proposal] and [VP scheduled the meeting]" conjoins two VPs under a higher ConjP; each VP projects its own internal argument structure and tense-agreement relations. Coordination of unlike categories produces ungrammaticality: *"The committee approved the proposal and quickly"—a VP cannot conjoin with an AdvP.

Gapping constructions elide repeated material under coordination: "The committee approved the proposal, and the board ∅ the budget." The elided VP in the second conjunct is licensed by structural parallelism with the first conjunct, but English gapping is subject to strict directionality constraints—forward gapping (ellipsis in the second conjunct) is grammatical, while backward gapping (ellipsis in the first conjunct) is marginal or ungrammatical: *"The committee ∅ the proposal, and the board approved the budget."

**Argument structure** defines the mapping between thematic roles (agent, theme, goal, experiencer, instrument) and syntactic positions. English verbs impose strict argument structure templates that constrain both the number and syntactic realization of their arguments. Intransitive verbs like "sleep" select a single external argument (agent) that maps to subject position: "The child sleeps." Transitive verbs like "approve" select an external argument (agent) and an internal argument (theme), mapping to subject and direct object positions: "The committee approved the proposal." Ditransitive verbs like "give" select an external argument (agent), a theme, and a goal, mapping to subject, direct object, and indirect object positions in the double-object construction: "The committee gave the board the proposal."

Dative alternation reveals the interaction between argument structure and syntactic configuration. Ditransitive verbs permit two distinct realizations: the double-object construction ("The committee gave the board the proposal") and the prepositional dative construction ("The committee gave the proposal to the board"). These alternants impose different c-command relations and binding possibilities. In the double-object frame, the indirect object c-commands the direct object, licensing anaphoric binding: "The committee gave each board member their proposal." In the prepositional dative frame, the direct object c-commands into the PP, licensing binding in the opposite direction: "The committee gave each proposal to its corresponding board member."

Unaccusative verbs like "arrive" and "fall" select a single internal argument (theme) that originates in object position but moves to subject position because the verb lacks an external argument. This underlying object status explains their behavior in existential constructions: "There arrived three delegates" is grammatical because "arrive" allows its internal argument to remain in post-verbal position under expletive insertion, whereas transitive and unergative verbs block this configuration: *"There approved the committee the proposal."

Causative alternations systematically relate intransitive and transitive verbs through the addition of a causative external argument. Inchoative verbs like "break" appear in both intransitive ("The vase broke") and transitive causative ("The child broke the vase") frames. The intransitive variant contains only a theme argument that maps to subject position; the transitive variant introduces a causative agent that maps to subject position while the theme argument surfaces as direct object. This alternation is mediated by the light verb head *v*, which introduces causative semantics and the external argument—the intransitive frame lacks the vP layer, projecting directly from VP to TP.

## 3. High-Performance Optimization & Failure Modes

Mastery of English syntactic structures requires internalization of movement diagnostics, constituency tests, and binding principles that distinguish grammatical from ungrammatical derivations. Native speakers possess tacit knowledge of these constraints but must render them explicit to achieve analytical precision in parsing complex sentences, identifying structural ambiguities, and diagnosing syntactic ill-formedness.

**Constituency tests** identify the hierarchical grouping of words into phrasal units. The substitution test replaces a putative constituent with a proform: if "the committee" can be replaced by "they," it forms a constituent DP. The movement test displaces a putative constituent: if "approved the proposal" can be fronted in "Approved the proposal, the committee certainly did," it forms a VP constituent. The coordination test conjoins like constituents: "The committee approved the proposal and scheduled the meeting" confirms that both VPs are constituents of the same category. The ellipsis test omits repeated material: "The committee approved the proposal, and the board did too" confirms that "approved the proposal" forms a VP that can be elided under identity with the antecedent.

These tests disambiguate structural ambiguity. The sentence "The committee approved the proposal in the conference room" permits two parses: one where the PP "in the conference room" modifies the VP (specifying the location of approval), and another where it modifies the NP "the proposal" (specifying a property of the proposal itself). Coordination disambiguates: "The committee approved [the proposal in the conference room] and [the budget in the boardroom]" forces NP-attachment, while "The committee [approved the proposal] and [scheduled the meeting] in the conference room" forces VP-attachment.

**Binding theory** governs the distribution and interpretation of anaphors (reflexives like "himself"), pronouns ("him"), and referring expressions ("the committee"). Principle A requires that anaphors be bound within their local domain—typically the minimal finite clause or DP containing the anaphor and a subject. The sentence "The committee criticized itself" is grammatical because the reflexive "itself" is bound by the local subject "the committee" within the same finite clause. Principle B requires that pronouns be free within their local domain—they cannot be coreferential with a c-commanding DP in the same clause. The sentence *"The committee criticized it" is ungrammatical under the intended reading where "it" refers to "the committee"; instead, "it" must refer to some other contextually salient entity. Principle C requires that referring expressions be free everywhere—they cannot be bound by any c-commanding DP, regardless of clause boundaries. The sentence *"It criticized the committee" is ungrammatical if "it" is intended to be coreferential with "the committee."

These binding principles interact with movement operations to produce locality effects. In "The committee expects [itself to be criticized]," the reflexive "itself" is bound by "the committee" across a clause boundary because the embedded clause is non-finite and lacks an intervening subject that would block binding. By contrast, *"The committee expects [that itself will be criticized]" is ungrammatical because the finite embedded clause introduces a binding domain boundary that prevents the matrix subject from binding into the embedded subject position.

**Island constraints** delimit the domains from which wh-movement and other displacement operations can extract material. The complex noun phrase constraint prohibits extraction from within relative clauses and complement clauses embedded inside DPs. The sentence *"What did you meet the student who wrote t?" is ungrammatical because "what" cannot be extracted from the relative clause modifying "student." The adjunct island constraint blocks extraction from within adjunct clauses: *"What did you leave before reading t?" is ungrammatical because "what" cannot be extracted from the temporal adjunct "before reading." The coordinate structure constraint prevents extraction from one conjunct of a coordination: *"What did you approve t and reject the budget?" is ungrammatical because "what" cannot be extracted from the first conjunct while leaving the second conjunct intact.

These island constraints are not arbitrary stipulations but derive from deeper principles governing the cyclic and local nature of syntactic computation. Movement proceeds in successive-cyclic fashion, passing through intermediate landing sites at the edge of each phase (CP and vP). Adjuncts and specifiers of non-phasal projections fail to provide escape hatches for movement, trapping extracted elements inside islands. Coordination creates a symmetry constraint: both conjuncts must participate equally in any syntactic operation affecting the coordinate structure, blocking asymmetric extraction from one conjunct alone.

**Garden-path effects** arise when linear word order misleads the incremental parser into adopting a structural analysis that must be revised upon encountering disambiguating material. The sentence "The horse raced past the barn fell" initially parses "raced" as the main verb of a simple active clause, but the appearance of "fell" forces reanalysis: "raced past the barn" is a reduced relative clause modifying "horse," and "fell" is the true main verb. Native speakers experience conscious processing difficulty because the preferred main-verb analysis must be abandoned in favor of the dispreferred reduced-relative analysis. Such sentences are grammatical but computationally costly, revealing the interaction between syntactic competence and performance limitations.

**Heavy NP shift** and **extraposition** permute the canonical SVO order to accommodate processing preferences and information structure. Heavy NP shift post-poses complex direct objects to clause-final position: "The committee approved yesterday [all of the proposals that had been submitted by the subcommittees]" moves the lengthy direct object rightward to avoid center-embedding. Extraposition post-poses sentential subjects and complements: "It is obvious [that the proposal has merit]" extracts the finite complement clause from subject position, replacing it with the expletive "it." These operations are optional and stylistically conditioned, applying more readily when the displaced constituent is syntactically complex or informationally new.

**Ellipsis phenomena**—including VP ellipsis, sluicing, gapping, and stripping—omit syntactically present but phonologically null material under identity with an antecedent. VP ellipsis deletes a VP that is structurally present but unpronounced: "The committee approved the proposal, and the board did [VP approve the proposal] too." The elided VP is recoverable from the antecedent VP in the first clause, and crucially, the auxiliary "did" survives in the T⁰ position, indicating that ellipsis targets the VP complement of T⁰ rather than the entire TP. Sluicing elides the TP complement of an interrogative C⁰: "The committee approved something, but I don't know what [TP the committee approved t]." The wh-element "what" moves to Spec-CP, and the entire TP is elided under recoverability from the antecedent clause.

These ellipsis operations are tightly constrained by syntactic identity conditions: the elided material must be structurally identical to its antecedent up to vehicle change (substitution of pronouns for coreferential DPs) and focus marking. Semantic identity is insufficient—two VPs with the same meaning but different syntactic structures cannot license ellipsis. The sentence "The committee approved the proposal, and the board did [VP reject the proposal] too" is ungrammatical because the elided VP "reject the proposal" is not syntactically identical to the antecedent VP "approve the proposal."

**Negation scope** interacts with quantifier interpretation and polarity item licensing. Negation in English is realized through the negator "not," which adjoins to TP and c-commands its scope domain. In "The committee did not approve every proposal," negation can take scope over the universal quantifier "every proposal," yielding a reading where none of the proposals were approved, or the universal can scope over negation, yielding a reading where not all proposals were approved but some were. Surface position does not uniquely determine scope: both readings are available from the same linear string, disambiguated only by prosodic focus and contextual interpretation.

Negative polarity items like "any" and "ever" are licensed only within the c-command domain of negation: "The committee did not approve any proposals" is grammatical because "any" is c-commanded by "not," but *"Any proposals, the committee did not approve" is ungrammatical because topicalization moves "any proposals" outside the scope of negation, stranding the polarity item in an unlicensed position. This constraint reveals that polarity item licensing is a syntactic dependency subject to c-command requirements, not a purely semantic phenomenon.

**Subject-auxiliary inversion** in English applies in a restricted set of environments: matrix questions, conditional clauses with fronted adjuncts, and after negative adverbs. The inversion operation raises T⁰ to C⁰, yielding the verb-second configuration: "Did the committee approve the proposal?" fronts the auxiliary "did" from its base position in T⁰ to the C⁰ head position, creating the characteristic interrogative word order. Inversion fails in embedded questions when the complementizer "if" or "whether" occupies C⁰: "The board asked whether the committee approved the proposal" blocks inversion because C⁰ is already filled. Inversion also applies after fronted negative adverbs: "Never had the committee approved a proposal so quickly" triggers subject-auxiliary inversion because the fronted adverb "never" occupies Spec-CP, and T⁰-to-C⁰ movement creates the required verb-second configuration.

**Do-support** inserts the dummy auxiliary "do" as a last-resort mechanism to satisfy morphological requirements when T⁰ lacks an overt auxiliary. In questions and negations with lexical verbs, T⁰ raises to C⁰ (in questions) or hosts the negator "not" (in negations), but lexical verbs cannot raise from V⁰ to T⁰ in modern English—only auxiliaries can undergo this movement. When T⁰ is left stranded without phonological content, "do" is inserted to support tense and agreement morphology: "The committee approved the proposal" becomes "Did the committee approve the proposal?" where "did" carries the past tense feature that would otherwise be stranded on T⁰. This operation is obligatory in environments where T⁰ must be pronounced—questions, negations, and emphatic affirmatives—but is blocked when an auxiliary is present: *"Did the committee have approved the proposal?" is ungrammatical because "have" already occupies T⁰, making "do"-insertion unnecessary and illicit.

The acquisition of English syntax by non-native speakers is systematically impeded by transfer effects from the learner's first language. Speakers of pro-drop languages like Spanish and Italian over-omit subjects in English finite clauses, producing errors like *"Is obvious that the proposal has merit" by transferring the null-subject parameter setting from their L1. Speakers of verb-final languages like German and Dutch produce errors in embedded clause word order, generating sentences like *"The committee said that it the proposal approved" by transferring the verb-final subordinate clause order from their L1. Speakers of languages with richer agreement morphology produce errors in English subject-verb agreement, over-generalizing or under-applying the third-person singular *-s* suffix.

Diagnostic fluency in English syntax requires systematic application of movement tests, binding diagnostics, and constituency probes to adjudicate between competing structural analyses. When faced with ambiguous sentences, deploy coordination, substitution, and ellipsis tests to force disambiguation. When analyzing long-distance dependencies, trace the path of moved elements through intermediate landing sites and verify that each movement step obeys locality and island constraints. When parsing complex auxiliary chains, identify the hierarchical embedding of functional projections and verify that each auxiliary head selects the correct complement category. Mastery of these analytic techniques transforms passive comprehension into active structural diagnosis, enabling precise identification of syntactic ill-formedness and principled explanation of grammaticality judgments.
