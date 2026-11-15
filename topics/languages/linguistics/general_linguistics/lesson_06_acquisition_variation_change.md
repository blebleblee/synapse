# Lesson 6: Language Acquisition, Variation, Historical Change

## 1. First-Principles Intuition & Invariants

Language is not transmitted the way a file is copied. When a child acquires her first language, nothing is handed over intact from one mind to another. Instead, every generation reconstructs the grammatical system from scratch, using impoverished input and arriving, with remarkable consistency, at a richly structured competence that far outstrips what the evidence could strictly justify. This puzzle, which Chomsky crystallized as the *poverty of the stimulus*, is the opening invariant of any serious theory of language acquisition, and its implications radiate outward into every corner of linguistics — from how languages change to why they converge on the same typological patterns across continents.

The standard nativist answer to the poverty of the stimulus is **Universal Grammar (UG)**: a genetically endowed, species-specific faculty that constrains the hypothesis space a child must search when acquiring her language. On this view, children are not blank slates performing raw statistical induction over heard utterances. They bring to the task a narrowly structured set of possible grammars, and language acquisition consists of *parameter-setting* — selecting, on the basis of ambient data, which of a finite set of values a given parameter takes in the target language. The Head Direction Parameter, for instance, encodes whether a language consistently places heads before or after their complements: English sets it head-first (verb before object, preposition before noun phrase), Japanese sets it head-final. A child exposed to Japanese input encounters post-positional particles and verb-final order, and the parameter snaps into place. The elegance of parametric theory is that a small number of binary choices, properly ordered in an implicational hierarchy, can generate the typological diversity observed across the world's languages without requiring the child to independently learn each construction from scratch.

Yet UG and parameter-setting do not exhaust the story. Usage-based acquisition theory, developed by Tomasello and colleagues, argues that children build grammar from the bottom up: beginning with concrete, item-specific constructions extracted from high-frequency input, then gradually abstracting over those items to form productive schemas. On this account, early child language is densely tied to particular verbs and particular frames — a child who productively uses "want X" does not yet have a general transitive construction, only a slot-filling routine anchored to that specific verb. Abstraction and generalization are developmental achievements, not innate givens. The practitioner working in first-language acquisition research must hold both frameworks in productive tension. The nativist correctly identifies phenomena — subjacency violations that children never produce even without negative evidence, the binding principles governing coreference — that resist purely usage-based explanation. The usage-based theorist correctly identifies the role of token frequency, construction salience, and social-cognitive scaffolding in explaining the developmental *sequence* of acquisition. The working linguist's job is to design elicitation tasks, corpora, and experimental paradigms that can distinguish between these accounts at the level of specific constructions, specific ages, and specific languages.

The **Critical Period Hypothesis** adds a biological dimension to this picture. Eric Lenneberg observed in 1967 that language acquisition proceeds robustly and effortlessly when it begins in early childhood, but that exposure beginning after puberty produces systematically less complete acquisition, particularly in phonology and morphosyntax. The neuroscientific grounding is neural plasticity: the cortical circuits underlying phonological discrimination, prosodic parsing, and syntactic processing are sculpted by input during a window that closes progressively through childhood, with phonology closing earliest (by roughly age six to seven for accent-free L2 phonology) and syntactic processing following somewhat later. The case of Genie, the child isolated from language until age thirteen, is simultaneously heartbreaking and theoretically pivotal: her lexical acquisition proceeded but her morphosyntax remained severely impaired, suggesting that the two systems have partially independent critical windows.

For the second-language (L2) acquisition practitioner, the critical period creates a set of hard invariants that no amount of instruction can fully override for post-pubescent learners. These learners will reliably show **L1 transfer effects** — the systematic projection of first-language phonological categories, morphosyntactic structures, and pragmatic conventions onto the target language. Transfer is not random interference but a principled, predictable phenomenon: a Spanish speaker learning English will transfer the Spanish five-vowel system onto English's fourteen-vowel space, collapsing distinctions that English treats as contrastive (ship/sheep, bit/beat). A Japanese speaker will initially transfer the pro-drop parameter, expecting English to license null subjects as Japanese does. The practitioner conducting L2 research or designing L2 pedagogy must therefore construct careful cross-linguistic comparisons between source and target languages before predicting or diagnosing error patterns.

The **Interlanguage** concept, proposed by Selinker in 1972, offers the practitioner a productive reframing: a learner's L2 grammar at any point in development is not a defective approximation of the target, but a *systematic linguistic system in its own right* — with its own phonology, morphology, and syntax, governed by rules that are neither fully L1 nor fully L2. Interlanguages are permeable (they admit new evidence), variable (they show free alternation between competing forms at transitional stages), and susceptible to *fossilization* (a subset of non-target features may stabilize permanently, even under continued exposure and instruction). The practical implication is that diagnosing a learner's interlanguage accurately — by collecting spontaneous production data, metalinguistic judgments, and processing-time measurements — is more informative than scoring surface-level accuracy, because it reveals which underlying parameter values the learner has set and which remain anchored to the L1.

Moving from the individual to the community, **sociolinguistic variation** establishes a second set of invariants. William Labov's foundational insight, demonstrated in his 1963 Martha's Vineyard study and the subsequent New York City department store study, is that linguistic variation is not noise but *social signal*. Speakers do not vary randomly in their use of phonological, lexical, or morphosyntactic variants; they vary in patterned ways that correlate with social categories — class, age, ethnicity, gender, network density, and community of practice — and these correlations encode the social meanings that linguistic features carry within a community. The variable (r) in post-vocalic position in New York City was not merely a phonetic detail: its presence or absence indexed social prestige, class aspiration, and stylistic register, and Labov demonstrated that speakers deployed it differently across formal and informal speech contexts in ways that tracked their position in the social hierarchy with remarkable precision.

The practitioner working in variationist sociolinguistics must master the **variable rule** framework: formalizing a linguistic variable (such as the presence vs. absence of a final coronal stop in consonant clusters, as in "bes' man" for "best man") and running multivariate logistic regression — typically using the Goldvarb/Varbrul or Rbrul software environment — to quantify the independent contribution of each factor group (preceding phonological context, following phonological context, morphological status of the cluster, speech rate, social class, ethnicity) to the probability of selecting one variant over another. The regression model assigns each factor group an effect weight between zero and one, centered on the overall input probability of the variant. The practitioner interprets the resulting factor weights not as causal forces but as statistical summaries of constraint hierarchies operating simultaneously within the grammar. A well-fitted variable rule model isolates which factor groups are significant, confirms that the constraints operate in the same direction across communities or styles, and can be used to compare variable rules across speakers to establish whether a change is in progress.

**Language change** is the third invariant domain. Languages do not change because speakers become careless or corrupt the system; they change because every act of acquisition is a reconstruction, and every reconstruction introduces systematic small biases. The actuation problem — why a change begins at a particular time and place — remains the hardest problem in historical linguistics, but the **transmission and diffusion** distinction offered by Labov sheds light on the mechanism: changes transmitted within a community through normal child acquisition tend to be regular and exceptionless because they propagate through the parametric resetting mechanism, while changes diffused across communities through adult contact tend to be lexically diffuse and socially conditioned because adult speakers can only imperfectly reset parameters they have already acquired.

**Sound change** — the systematic, regular, exceptionless shift of phonological categories over time — is the most precisely understood type of linguistic change, and the **Comparative Method** is its master tool. When cognates across related languages show systematic correspondences — Latin *p* : Gothic *f* : Old English *f* (Latin *pater*, Gothic *fadar*, Old English *fæder*) — the comparative linguist does not conclude that one language borrowed from another or that the correspondence is accidental. She applies the Comparative Method: assembles cognate sets across the daughter languages, establishes regular correspondences, reconstructs the proto-phoneme that would account for all the reflexes via known or plausible natural processes, and builds the proto-language in a bottom-up fashion from the evidence. Grimm's Law — the systematic shift of Proto-Indo-European (PIE) voiceless stops to fricatives, voiced stops to voiceless stops, and aspirated voiced stops to voiced fricatives in the Germanic branch — is the paradigm case: it is exceptionless within its domain (exceptions are explained by Verner's Law, which conditions the outcome by PIE accent placement), and it transformed Germanic phonology in a single coherent push-chain or drag-chain fashion.

**Grammaticalization** is the diachronic process by which lexical material is progressively recruited into the grammatical system, losing phonological substance, semantic specificity, and distributional freedom while gaining obligatoriness and grammatical scope. The English *going to* future is the practitioner's canonical case: a spatial motion verb followed by a purposive infinitive ("She is going to town to buy bread") grammaticalized over the Early Modern period into a tense-aspect marker ("It's going to rain"), losing its locative semantics, condensing phonologically to *gonna* in informal speech, and extending from intentional agents to inanimate subjects that cannot literally go anywhere. Grammaticalization is unidirectional (lexical to grammatical, not the reverse, with marginal exceptions), is accompanied by phonological reduction, semantic bleaching, and syntactic bonding, and tends to follow cross-linguistically recurrent pathways. The implication for the practitioner is that the grammaticalization pathway a construction follows is not arbitrary: body-part nouns become spatial grams, motion verbs become future markers, verbs of possession become perfectives.

**Typological universals** establish the boundary conditions within which all human languages operate. Greenberg's 1963 investigation of a forty-five-language sample produced implicational universals of the form "If a language has property X, it also has property Y": if a language is Verb-Object, it will typically be Preposition-Noun (English, French, Swahili); if it is Object-Verb, it will typically be Noun-Postposition (Japanese, Turkish, Basque). These universals are not absolute but statistical, admitting exceptions while revealing overwhelming tendencies that reflect the same cognitive and articulatory constraints operating independently across unrelated language families. The practitioner working in linguistic typology uses probability samples — balanced by genealogical and areal independence to avoid spurious confirmation — rather than convenience samples, and interprets both absolute universals and implicational tendencies as constraints on the design space of human language that any adequate theory of UG, language processing, or language change must explain.

---

## 2. Core Architecture & Mechanics

### The L1 Acquisition Mechanism: From Input to Grammar

The acquisition mechanism operates across four interacting components that the practitioner must keep analytically distinct: the *input processor*, which extracts distributional and prosodic information from the ambient speech stream; the *parameter-setting device*, which maps analyzed input onto parametric choices constrained by UG; the *lexical acquisition system*, which builds form-meaning pairings through joint attention, referential disambiguation, and fast-mapping; and the *morphophonological learning component*, which acquires the allomorphic and prosodic adaptations specific to the target language.

```
INPUT (Ambient Speech Stream)
        │
        ▼
┌───────────────────────────────────────────────────┐
│          PROSODIC / STATISTICAL BOOTSTRAPPING     │
│  - Distributional analysis (phoneme boundaries)  │
│  - Prosodic packaging (clause, phrase detection) │
│  - Mutual information → morpheme segmentation    │
└───────────────────────────┬───────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────┐
│          SYNTACTIC PARAMETER-SETTING              │
│  UG-constrained hypothesis space                 │
│  Head Direction ← [head-first | head-final]      │
│  Pro-Drop      ← [+null subject | −null subject] │
│  Wh-movement   ← [overt | covert]                │
│  V2 constraint ← [obligatory | absent]           │
└───────────────────────────┬───────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────┐
│          LEXICAL / CONSTRUCTIONAL LAYER           │
│  Item-specific schemas → abstract constructions  │
│  Token frequency drives entrenchment             │
│  Type frequency drives abstraction               │
└───────────────────────────┬───────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────┐
│          MORPHOPHONOLOGICAL COMPONENT             │
│  Allomorphy rules (irregular → regular shift)    │
│  Stress/tone assignment                          │
│  Phonotactic repair strategies                   │
└───────────────────────────┬───────────────────────┘
                            │
                            ▼
              INTERNALIZED GRAMMAR (I-Language)
```

The sequence is not strictly linear — there is extensive feedback between layers — but the directionality of the dominant data flow is bottom-up: speech segmentation precedes syntactic analysis, and syntactic analysis precedes the acquisition of morphophonological alternations conditioned by syntactic context. The practitioner designing acquisition studies must intervene at a specific layer rather than treating "language acquisition" as a monolithic process. A preferential looking paradigm testing subject-relative versus object-relative clauses probes the syntactic layer directly; a word segmentation task using the head-turn preference procedure probes prosodic bootstrapping; a wug test (Berko's 1958 methodology of presenting novel nonsense morphemes) isolates the morphophonological productive rule system from rote lexical memory.

### The Variationist Variable Rule Model

The working architecture of Labovian variationist analysis is a multivariate logistic regression over a coded corpus of naturalistic speech tokens. The practitioner's workflow proceeds from data collection through coding through analysis through interpretation, and each transition involves irreversible decisions that must be made with explicit theoretical motivation.

```
NATURALISTIC SPEECH DATA
(Sociolinguistic interview / corpus)
            │
            ▼
    TOKEN EXTRACTION
    Identify all tokens of the variable
    (e.g., every potential site for (t/d)-deletion)
            │
            ▼
    FACTOR GROUP CODING
    ┌──────────────────────────────────────────┐
    │  LINGUISTIC FACTOR GROUPS                │
    │  · Preceding phonological segment        │
    │  · Following phonological segment        │
    │  · Grammatical status (monomorpheme /   │
    │    regular past / irregular past)        │
    │  · Syllable stress                       │
    ├──────────────────────────────────────────┤
    │  SOCIAL FACTOR GROUPS                    │
    │  · Speaker age cohort                    │
    │  · Social class / education level        │
    │  · Ethnicity / community of practice     │
    │  · Speech style (formal / informal)      │
    └──────────────────────────────────────────┘
            │
            ▼
    VARBRUL / Rbrul REGRESSION
    Input probability (P₀): overall rate
    Factor weights (Fₙ): per-factor contribution
    Log-likelihood, χ², step-up/step-down
    selection of significant factor groups
            │
            ▼
    CONSTRAINT HIERARCHY
    Rank factor groups by range (max − min weight)
    Identify knockouts (absolute constraints)
    Map against cross-variety comparisons
            │
            ▼
    INTERPRETATION
    Change in progress? → age-grading vs. apparent time
    Social indexicality? → first- vs. second-order variables
    Community contact? → diffusion vs. transmission pattern
```

The critical analytical decision in the variable rule framework is the **envelope of variation**: the analyst must define precisely which tokens are included in the variable and which are categorically excluded. For (t/d)-deletion, tokens before a following vowel where deletion would create a hiatus are often categorically resistant and should be excluded from the analysis because including categorical environments inflates the apparent effect weight of the following-phonological-context factor group. Getting the envelope wrong produces misleading factor weights and incorrect constraint hierarchies.

The practitioner must also decide between **apparent time** and **real time** inference. Apparent time is the methodological convention of treating synchronic age differences in a community as a proxy for change over time: if younger speakers use a novel variant at higher rates than older speakers in the same community at the same point in real time, the analyst infers that the variant is spreading. Apparent time is efficient but carries the assumption of *age-grading stability* — that speakers' grammars do not substantially shift after adolescence. Real time studies, which revisit the same community after a generation, can confirm or disconfirm apparent-time inferences and have occasionally shown that what looked like change in progress was instead a stable age-graded pattern.

### The Comparative Method: Operational Architecture

The Comparative Method is the core analytical engine of historical linguistics, and its operational architecture is a strict sequence of steps that the practitioner must execute in order, because later steps presuppose the outputs of earlier ones.

```
COGNATE SET ASSEMBLY
Identify probable cognates across daughter languages
using semantic plausibility and gross phonological
similarity (not regular correspondence — that comes later)
            │
            ▼
CORRESPONDENCE SET EXTRACTION
For each cognate set, extract the correspondence
of segments in the same structural position:

  Latin    Greek    Sanskrit   Gothic    Old Irish
  p        p        p          f         [ø/h]
  (pater)  (patēr)  (pitā)     (fadar)   (athir)

            │
            ▼
REGULARITY TEST
Does the correspondence hold across all cognate sets
sharing the same structural context? Exceptions
require conditioning environments or borrowing hypotheses.
            │
            ▼
PROTO-PHONEME RECONSTRUCTION
Choose the proto-phoneme that accounts for all reflexes
via natural, attested processes. Prefer the derivation
requiring fewer marked processes. Mark as *p, *b, etc.

  PIE *p → Latin p, Greek p, Sanskrit p, Germanic f
  (Grimm's Law: voiceless stop → fricative in Germanic)

            │
            ▼
PROTO-LANGUAGE ASSEMBLY
Reconstruct proto-morphology (inflectional endings,
ablaut grades) and proto-syntax from the daughter
evidence, using the same correspondence logic.
            │
            ▼
SUBGROUPING
Shared innovations (not retentions) define subgroups:
If Latin and Celtic share a feature not found in
Germanic or Sanskrit, it is a shared innovation
defining an Italo-Celtic node — unless it is
independently natural enough to have arisen twice.
```

The practitioner must maintain a strict distinction between **shared retentions** (symplesiomorphies, in the cladistic analogy) and **shared innovations** (synapomorphies). Two languages sharing a conservative feature that the proto-language already had do not thereby form a subgroup; it is shared *departure from* the proto-language state that counts as evidence of common ancestry after the proto-language broke up. This distinction is what prevents the analyst from grouping all languages that conserved the PIE consonant system into a single subgroup against languages that underwent Grimm's Law.

### Grammaticalization: The Formal Pathway

Grammaticalization proceeds along four simultaneous dimensions that the practitioner can operationalize as measurable variables in a diachronic corpus study.

| Dimension | Early Stage | Late Stage | Measurement Proxy |
|---|---|---|---|
| **Semantic bleaching** | Full lexical meaning | Abstract grammatical meaning | Semantic map coverage; corpus collocate analysis |
| **Phonological reduction** | Full prosodic word | Clitic or affix | Syllable count; vowel reduction rate |
| **Syntactic bonding** | Free distributional item | Fixed-position bound item | Intervening-material tests; word-order freedom |
| **Obligatorification** | Optional element | Grammatically required element | Corpus omission rate across registers |

The practitioner studying an in-progress grammaticalization in a corpus — say, the development of *be like* as a quotative in English (*She was like, "I can't believe it"*) — codes each token for its position on each of these four dimensions, then plots the distribution of tokens in the corpus across time, genre, age-of-speaker, and formality to establish the trajectory. A grammaticalizing form characteristically shows earlier bleaching and syntactic bonding before phonological reduction, because the semantic and distributional changes are driven by analogical extension into new contexts, while phonological reduction follows the increased token frequency that results from wider distribution.

---

## 3. High-Performance Optimization & Failure Modes

### Optimizing L2 Acquisition Research

The most consequential methodological failure in L2 acquisition research is **confounding proficiency and exposure**. Studies that compare groups of learners by years of instruction implicitly assume that instruction time is a uniform commodity, when in fact it is the most heterogeneous variable in the field: a hundred hours of immersion exposure differs from a hundred hours of formal grammar instruction in ways that affect phonological, lexical, and morphosyntactic acquisition asymmetrically. The practitioner designing an L2 acquisition study must measure proficiency directly — using validated instruments such as the LexTALE for vocabulary size, an elicited imitation task for morphosyntactic proficiency, and a word list recording for accent rating — and treat these as continuous covariates rather than sorting learners into categorical groups that paper over internal variance.

**Fossilization diagnosis** is a second high-failure area. The practitioner must distinguish between *stabilization* (a form that has not changed for a period of time but may still respond to focused instruction or input enhancement) and *fossilization proper* (a form that is permanently fixed and no longer acquirable). The diagnostic criterion is responsiveness to explicit negative feedback combined with focused input enhancement delivered over a sufficient duration (typically six to eight weeks of intensive instruction). A form that does not shift under these conditions qualifies as fossilized. Without this test, analysts frequently mislabel as fossilized what is merely a stable but responsive interlanguage feature, leading to unwarranted pessimism in pedagogical contexts.

The **interface hypothesis**, developed by Sorace, provides a sharper tool for predicting where fossilization is likely to occur. It distinguishes between purely internal linguistic features (deep morphosyntax, phonology proper) and **interface features** that require the integration of syntactic computation with discourse pragmatics, information structure, or lexical semantics. Interface features are systematically harder to acquire for post-critical-period learners because they require two computational systems to coordinate rather than one, and because L1 discourse conventions are deeply entrenched. The practical implication is that the practitioner should focus diagnostic attention on structures like definiteness marking (syntax-pragmatics interface), subject drop in [−pro-drop] L2s, and the placement of focus particles — not because these are individually important but because they are diagnostic of the interface vulnerability that characterizes near-native but non-native grammars.

### Failure Modes in Variationist Analysis

The variable rule regression is a powerful tool but prone to three specific failure modes that the practitioner must actively defend against. The first is **factor group collinearity**: when two factor groups are correlated with each other in the data — say, speech style (formal/informal) and grammatical status of the cluster (past tense marker vs. monomorpheme) — the regression cannot cleanly separate their contributions. The factor weights for both groups will be unstable, shifting dramatically with small changes in the data or the coding. The practitioner should test for collinearity by running the model with and without the suspected correlated factor groups and comparing the resulting weights for all other factors. If the weights change substantially, collinearity is distorting the analysis and the correlated factors must either be collapsed or analyzed in separate subsets of the data.

The second failure mode is **database size insufficiency**. Logistic regression requires a minimum number of tokens per factor cell to produce stable weight estimates — the standard heuristic is a minimum of five tokens per cell, but thirty or more per cell produces reliably interpretable weights. Analysts working with small speech communities or rare constructions frequently find that their factor groups are underpowered: they have forty tokens total and eight factor cells, leaving five tokens per cell, which produces weights whose confidence intervals span most of the zero-to-one range. The mitigation is to collapse factor groups to their theoretically most motivated distinction (e.g., collapsing five following-segment categories into [+sonorant] versus [−sonorant]) before running the final model.

The third failure mode is **apparent time misreading**. When a community shows a change in progress via apparent time inference, the practitioner must check whether the change is **from above** (socially salient, entering via conscious prestige adoption, spreading through the class hierarchy from the top down) or **from below** (socially unmarked, spreading through the community below the level of conscious awareness, correlated with local identity). The two patterns have opposite social indexicalities and opposite sociolinguistic implications: change from above is typically borrowed from a prestige variety and may stabilize or recede as the social relationship to that variety changes; change from below is internally generated and tends to be more robust. The diagnostic is the **style-shifting pattern**: if speakers with high social prestige lead the change and show the greatest style-shifting (more of the new form in informal speech, less in formal), it is from above; if younger working-class or ethnic-minority speakers lead and show the least style-shifting, it is from below.

### Optimization in Historical Reconstruction: Avoiding the Comparative Method's Failure Modes

The Comparative Method fails predictably in three scenarios that the practitioner must recognize and mitigate. **Borrowing** masquerades as genetic inheritance when lexical items travel between neighboring languages at high rates. The classic mitigation is to weight basic vocabulary — the Swadesh list of body parts, low numbers, pronouns, universal natural categories — over cultural vocabulary, because basic vocabulary resists borrowing more strongly than terms for artifacts, institutions, or flora and fauna. Pronouns are particularly resistant because they are closed-class and deeply entrenched in the morphological system. If a proposed cognate set is clustered in cultural vocabulary and shows irregular correspondences, borrowing is the more parsimonious explanation than inheritance.

**Areal diffusion** — the spread of typological features across geographically contiguous languages through long-term contact, regardless of genetic relationship — is the second failure mode. The South Asian Sprachbund (India, Pakistan, Bangladesh, Sri Lanka) comprises languages from four unrelated families (Indo-Aryan, Dravidian, Munda, Tibeto-Burman) that have converged on shared features: retroflex consonants, verb-final order, the semantics of evidential morphology, and certain patterns of head-marking. A naive genetic analysis would group them together on the basis of these shared features; the comparative linguist avoids this error by checking whether the shared features are also found in the closest genetic relatives of each language *outside* the Sprachbund area. If Dravidian languages outside India's typological core do not share the feature, the feature is areally acquired, not genetically inherited.

**Morphological reconstruction** carries a subtler failure mode: the practitioner must distinguish between reconstructing a proto-morpheme and reconstructing its *syntactic distribution*. PIE can be reconstructed with a subjunctive mood morpheme on the evidence of Sanskrit, Latin, Greek, and Celtic cognates, but the syntactic contexts triggering the subjunctive varied substantially across daughter languages and cannot be uniformly attributed to PIE without independent evidence. The practitioner should reconstruct morphological categories bottom-up from daughter evidence, but mark syntactic reconstructions with lower confidence and always provide the daughter-language distribution that motivates them.

### Grammaticalization Traps

The practitioner analyzing an apparent grammaticalization in corpus data must resist the **teleological fallacy**: assuming that because grammaticalization has a cross-linguistically common endpoint (lexical verb → tense marker, noun → case affix), the trajectory of a specific construction in a specific language is *necessarily* headed toward that endpoint. Many grammaticalizations stall, reverse (through degrammaticalization, which is rare but attested), or fork into multiple partially-grammaticalized variants coexisting in complementary distribution. The correct analytical posture is to describe the trajectory evidenced in the data and invoke cross-linguistic parallels as *explanatory background*, not as predictions about the construction's future behavior.

**Register bias in diachronic corpora** is the most practically consequential methodological failure in grammaticalization studies. Early stages of grammaticalization frequently appear first in spoken, informal, or colloquial registers that are systematically underrepresented in written historical corpora. The practitioner dating the onset of a grammaticalization from written sources should treat the first attestation as an upper bound on the true date of emergence, not the date itself. The *going to* future, for instance, appears in English written sources in the late fifteenth century, but its phonological reduction to *gonna* in informal speech likely preceded the written evidence by decades. When a diachronic corpus includes letters, legal depositions, and dramatic dialogue alongside formal prose, the practitioner should stratify the analysis by register and expect that the grammaticalized form will show higher rates and earlier dates in the more informal strata.

The final optimization principle governing all three domains — acquisition, variation, and change — is that **the unit of analysis must match the theoretical claim**. Acquisition claims are claims about the mental grammars of individual speakers and must be supported by individual-level data, not community-level aggregates. Variation claims are claims about structured heterogeneity in a speech community and require speaker-and-token-level data with appropriate random effects modeling to account for by-speaker and by-item variance. Historical change claims are claims about grammars across time and require that the diachronic corpus be sampled, coded, and analyzed with the same care that synchronic corpora receive — without the assumption, fatal to many diachronic studies, that frequency in the corpus is a direct proxy for frequency in the spoken language of the period. Each of these mismatches between unit of analysis and theoretical claim has derailed entire research programs; identifying and correcting them is the practitioner's highest-order methodological obligation.
