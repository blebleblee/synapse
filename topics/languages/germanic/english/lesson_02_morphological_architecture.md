# Lesson 2: Morphological Architecture

## 1. First-Principles Intuition & Invariants

Every language must solve a fundamental combinatorial problem: how does a finite lexicon express an effectively infinite range of meanings, relationships, and temporal states? Syntax provides one answer by arranging words in meaningful sequences, but morphology provides the deeper answer by building words themselves from smaller, meaningful units. English solves this problem in a way that is historically unusual among the world's major languages and analytically deceptive for the advanced practitioner, because its surface simplicity conceals a layered architecture of extraordinary complexity.

To understand English morphology at the level this masterclass demands, you must abandon the casual intuition that English "doesn't have much grammar" compared to German or Russian. What English lost through centuries of contact-driven erosion was not morphological richness per se but *inflectional* morphological richness. Its derivational morphology, by contrast, is baroque in its depth, drawing simultaneously on three distinct etymological strata — the Germanic substrate, the Norse superstrate from Viking settlement, and the Norman-Latin-Greek superstratum deposited after 1066 — each stratum bringing its own set of affixes, combinatorial rules, and phonological constraints. The practitioner who masters English morphology is effectively learning three parallel systems that coexist in uneasy, productive tension.

The foundational invariant of English morphology is the distinction between **inflection** and **derivation**. Inflection is the grammatically mandatory modification of a word to signal its syntactic role within a sentence: number on nouns (*dog* → *dogs*), tense and agreement on verbs (*walk* → *walked*, *walks*), comparison on adjectives (*fast* → *faster* → *fastest*). Crucially, inflection does not change a word's lexical identity or its category: *dogs* is still a noun, still means "canine animal," and would appear as a single entry in a theoretical lexicon. Derivation, by contrast, creates new lexical items, often crossing category boundaries: the verb *decide* yields the noun *decision*, which yields the adjective *decisive*, which yields the adverb *decisively*, which yields the verb *de-decisivize* (marginal, but not impossible). Each step creates a word that a speaker must learn as a new entry, even if the derivational relationship is transparent.

This distinction matters enormously for language production. When a native speaker inflects a word, they are applying a rule that is in most cases entirely productive and automatic. When they derive a word, they are navigating a constraint-laden system where productivity is partial, historical accidents block otherwise expected forms, and semantic drift means the derived word no longer perfectly predicts its meaning from its parts. Understanding where the boundary between these two systems lies — and where it blurs — is the first architectural principle the practitioner must internalize.

The second invariant is the concept of the **morpheme** as the minimal unit of meaning. Morphemes are not syllables, not letters, not phonemes. The word *unbreakable* contains three morphemes: the prefix *un-* (negation), the root *break* (the lexical anchor), and the suffix *-able* (capacity or susceptibility). Crucially, morphemes surface with varying phonological shapes called **allomorphs** depending on their phonological environment. The English plural morpheme, orthographically rendered as *-s* or *-es*, has three phonologically conditioned allomorphs: /s/ after voiceless non-sibilant consonants (*cats*, *clocks*), /z/ after voiced segments and all vowels (*dogs*, *trees*, *bees*), and /ɪz/ after sibilants (*buses*, *churches*, *judges*). This allomorphic conditioning is not a spelling rule; it is a phonological rule that the speaker applies below the level of conscious awareness. The practitioner must recognize that every regular English inflection exhibits this kind of allomorphic structure, and that the written form is a consistently misleading guide to the phonological reality.

The third invariant concerns what linguists call **base morphology** and the concept of **lexical phonology**. English affixes do not attach freely to any stem. They operate in ordered strata, and the stratum to which an affix belongs determines what phonological and semantic changes it can trigger. Level I (or Class I) affixes — largely the Latinate suffixes such as *-ity*, *-ion*, *-ous*, *-ive*, *-al* — attach early in the derivational process, before stress is computed, and they actively influence stress placement and trigger consonant alternations. Level II (or Class II) affixes — largely the Germanic suffixes such as *-ness*, *-hood*, *-ful*, *-less*, *-ly* — attach after stress is set and are phonologically inert, leaving the base word's stress and phonological shape intact. This difference explains why *personal* → *personality* shifts stress (Level I: *-ity* recalculates everything), while *happy* → *happiness* does not (Level II: *-ness* attaches to what is already there). Knowing this layering is not academic pedantry; it is the master key to predicting how English words sound and behave before you have ever encountered them.

---

## 2. Core Architecture & Mechanics

### The Inflectional System: What Remains After Attrition

Old English was a fully synthetic language, meaning it packed enormous grammatical information into the word itself through case, gender, number, and mood inflections on nouns, adjectives, and verbs simultaneously. Modern English has shed nearly all of this, but the remnants that survive are not random debris — they are the highest-frequency, most grammatically load-bearing pieces of the system, and they are irregular precisely because frequency of use shields words from analogical leveling. What remains is a compact but non-trivial inflectional paradigm.

**Nominal Inflection: Number and the Genitive**

The English noun has two grammatical categories: number (singular vs. plural) and a vestigial genitive case (the *'s* clitic). The regular plural is formed by suffixation of the allomorphic set described above, but the irregular plurals deserve careful taxonomy. The *umlaut* plurals — *man/men*, *woman/women*, *foot/feet*, *tooth/teeth*, *goose/geese*, *mouse/mice*, *louse/lice* — are direct survivals of the Proto-Germanic phenomenon of *i*-mutation, in which a following *\*i* or *\*j* in the plural suffix caused vowel raising or fronting in the root, after which the suffix itself was lost. The vowel alternation is now the only mark of plurality, an extraordinary case of morphological fossilization. Similarly, the *-en* plurals (*oxen*, *children*, *brethren*) preserve a Germanic weak noun plural suffix that was once highly productive and is now a closed, non-productive class.

The full noun inflection paradigm, presented across the principal noun classes, illustrates the asymmetry between regular and irregular behavior:

| Noun Class | Singular | Plural | Mechanism |
|---|---|---|---|
| Regular (Type I) | *dog* | *dogs* /dɒɡz/ | Voiced suffix after voiced seg. |
| Regular (Type II) | *cat* | *cats* /kæts/ | Voiceless suffix after voiceless seg. |
| Regular (Type III) | *church* | *churches* /tʃɜːtʃɪz/ | Epenthetic vowel after sibilant |
| Umlaut Plural | *foot* | *feet* | Vocalic alternation, no suffix |
| Zero Plural | *sheep* | *sheep* | No change (OE weak neuter) |
| *-en* Plural | *ox* | *oxen* | Archaic suffix class |
| Latinate Plural | *cactus* | *cacti* | Borrowed Latin second-declension |
| Greek Plural | *criterion* | *criteria* | Borrowed Greek neuter |
| French Plural | *bureau* | *bureaux* | Borrowed French masculine |

The Latinate, Greek, and French irregulars occupy a fascinating zone: educated registers of English prefer *data/criteria/phenomena* as plurals, while popular usage increasingly treats them as singular mass nouns (*the data is*, *a criteria*). This is not degradation; it is the normal analogical regularization process by which borrowed morphological classes are absorbed into the dominant paradigm. The practitioner must know both registers and control which they deploy according to audience and context.

**Verbal Inflection: The Strong/Weak Division**

The English verb carries tense (past vs. non-past), a third-person singular present marker (*-s*), two participial forms, and two infinitival constructions. The critical architectural division runs between **weak verbs** (past formed by dental suffix: *walk/walked*, *love/loved*, *fade/faded*) and **strong verbs** (past formed by **ablaut**, a systematic vowel alternation inherited from Proto-Germanic's Indoeuropean vowel grades).

The strong verb ablaut classes are seven in number, each defined by the vowel pattern of its principal parts. Knowing these classes allows the practitioner to look at an unfamiliar strong verb and predict its past tense before memorizing it, because the classes represent phonological rules, not arbitrary facts.

| Ablaut Class | Infinitive | Simple Past | Past Participle | Additional Examples |
|---|---|---|---|---|
| Class I | *ride* /raɪd/ | *rode* /roʊd/ | *ridden* /ˈrɪdən/ | *write, bite, drive, strive* |
| Class II | *freeze* /friːz/ | *froze* /froʊz/ | *frozen* /ˈfroʊzən/ | *choose, lose (< *leosan)* |
| Class III | *bind* /baɪnd/ | *bound* /baʊnd/ | *bound* /baʊnd/ | *find, grind, wind, sing, drink* |
| Class IV | *bear* /bɛər/ | *bore* /bɔːr/ | *borne* /bɔːrn/ | *tear, wear, swear, steal* |
| Class V | *speak* /spiːk/ | *spoke* /spoʊk/ | *spoken* /ˈspoʊkən/ | *give, eat, see, tread* |
| Class VI | *shake* /ʃeɪk/ | *shook* /ʃʊk/ | *shaken* /ˈʃeɪkən/ | *stand, take, draw* |
| Class VII | *hold* /hoʊld/ | *held* /hɛld/ | *held* /hɛld/ | *fall, grow, blow, know* |

Notice that Class III includes both *bind/bound/bound* and *sing/sang/sung*, because the original Indo-European short-vowel grades were conditioned differently before clusters. Class VII is a reduplicating class in Proto-Germanic whose reduplication was replaced by vowel alternation in later West Germanic, which is why it looks least systematic today. The practical upshot: an advanced practitioner encountering *smite/smote/smitten*, *strive/strove/striven*, or *weave/wove/woven* should immediately recognize Class I or V patterns rather than treating each pair as an isolated irregularity.

**Full Verbal Paradigm: "Speak" (Strong Class V)**

The complete paradigm across all inflected forms, presented here for a representative strong verb:

| Form | Surface Form | Allomorph/Notes |
|---|---|---|
| Infinitive | *speak* | base form |
| Present 1sg | *I speak* | zero inflection |
| Present 2sg | *you speak* | zero inflection |
| Present 3sg | *he/she/it speaks* | /s/ suffix |
| Present 1pl | *we speak* | zero inflection |
| Present 2pl | *you speak* | zero inflection |
| Present 3pl | *they speak* | zero inflection |
| Simple Past (all persons) | *spoke* | Class V ablaut |
| Present Participle | *speaking* | *-ing* suffix |
| Past Participle | *spoken* | ablaut + *-en* suffix |
| Infinitive (to-inf.) | *to speak* | with particle *to* |

The morphological parsimony here is radical: a modern English verb distinguishes only two synthetic tense forms (*speak/spoke*) where Latin distinguished six indicative tenses plus subjunctive and infinitival forms with full person-number agreement. English compensates through **periphrastic constructions** — the progressive (*is speaking*), the perfect (*has spoken*), the pluperfect (*had spoken*), the future (*will speak*), and modal combinations (*would have been speaking*) — that build complex temporal and aspectual meaning from free grammatical morphemes rather than from bound suffixes. The morphology of these auxiliaries is itself a study: *be*, *have*, *will*, *shall*, *can*, *may*, *must* each carry their own suppletive or defective paradigms, the most complex of which is *be* with its eight distinct forms (*am, is, are, was, were, be, been, being*).

### Derivational Morphology: The Stratified System

The derivational system is best understood as a set of **word-formation rules** organized into the two strata described in Section 1, with compounding operating as a third, largely stratum-independent mechanism.

**The Level I (Latinate) Stratum**

Level I suffixes derive from Latin and Greek roots absorbed into English through French after the Norman Conquest and through Renaissance learned borrowings. They exhibit two defining properties: they can trigger **stress shift** in the base, and they can trigger **consonant alternations** that were phonologically conditioned in Latin but survive in English as fossilized morphological alternations.

Consider the *-ity* suffix: *sane* → *sanity*, *obscene* → *obscenity*, *dense* → *density*, *electric* → *electricity*. In each case, stress moves to the syllable immediately preceding the suffix (the **antepenultimate stress rule** that *-ity* imposes). The same suffix triggers the velar softening alternation: *electric* /ɪˈlɛktrɪk/ → *electricity* /ɪˌlɛkˈtrɪsɪti/, where the final /k/ of *electric* alternates to /s/ before the front vowel environment created by *-ity*. This is not a synchronic phonological rule that applies freely in English — /k/ before front vowels does not automatically become /s/ — but it is a systematic morphological alternation that must be learned as a property of the Level I affix set.

The chart below maps the major Level I suffixes alongside their stress and phonological behavior:

| Suffix | Category Change | Stress Effect | Example Set |
|---|---|---|---|
| *-ity* | Adj → N | Stress to pre-suffix syllable | *fertile/fertility*, *sane/sanity* |
| *-ion/-tion/-sion* | V → N | Stress to pre-suffix syllable | *decide/decision*, *expand/expansion* |
| *-ive* | V/N → Adj | Stress shift possible | *decide/decisive*, *act/active* |
| *-al* | N → Adj | Often preserves base stress | *nature/natural*, *person/personal* |
| *-ous* | N → Adj | Variable | *fame/famous*, *peril/perilous* |
| *-ify* | Adj/N → V | Preserves base stress | *pure/purify*, *class/classify* |
| *-ic* | N → Adj | Penultimate stress rule | *atom/atomic*, *rhythm/rhythmic* |

The consonant alternation set that Level I morphology activates is a closed, learnable system derived from Latin phonology:

The velar stops alternate before high front vowels: *opaque* → *opacity*, *electric* → *electricity*, *critic* → *criticism*. The alveolar nasal alternates before the *-tion* suffix: *act* → *action*, *construct* → *construction*, *permit* → *permission* (where the */t/* of *permit* undergoes palatalization to yield /ʃ/). These alternations, invisible at the level of casual usage, are the phonological signature of the Latinate stratum and must be internalized by any practitioner who wants to build Latinate vocabulary productively rather than memorizing each form in isolation.

**The Level II (Germanic) Stratum**

Level II suffixes are largely Germanic in origin and phonologically inert in the precise sense that they never cause stress shift or consonant alternations in their base. The base word appears with its full, unmodified phonological form, and the suffix is simply concatenated. This is why *happy* → *happiness* leaves *happy* intact, while *happy* → *happily* simply replaces the final /ɪ/ with /ɪlɪ/ without any deeper restructuring.

The Level II suffixes form productive, transparent paradigm sets:

| Suffix | Category Change | Productivity | Example Set |
|---|---|---|---|
| *-ness* | Adj → N | Fully productive | *sadness, happiness, oddness, wokeness* |
| *-hood* | N → N | Semi-productive | *childhood, neighborhood, falsehood* |
| *-ship* | N → N | Semi-productive | *friendship, hardship, craftsmanship* |
| *-dom* | N/Adj → N | Low-moderate | *kingdom, freedom, boredom, stardom* |
| *-ful* | N → Adj | Productive | *handful, careful, hopeful, stressful* |
| *-less* | N → Adj | Productive | *hopeless, careless, restless, ruthless* |
| *-ly* | Adj → Adv | Fully productive | *quickly, clearly, softly, obviously* |
| *-ward(s)* | N → Adv/Adj | Productive | *northward, inward, forward, backward* |
| *-ish* | Adj/N → Adj | Productive | *reddish, childish, oafish, tallish* |

The productiveness of *-ness* is worth emphasizing as a practitioner's tool. Because it attaches at Level II after all phonological computation is complete, and because it converts any adjective to an abstract noun with complete transparency, it functions as an emergency derivation strategy in English: any adjective, including nonce adjectives and adjectives derived through other processes, can be nominalized via *-ness*. Writers exploit this constantly (*the shruginess of his response*, *the unputdownableness of the novel*), and understanding its combinatorial freedom tells you exactly why it feels natural in contexts where *-ity* would sound forced or simply fail to form.

**Level I Prefixes and their Stacking Behavior**

Prefixes in English are largely stratum-agnostic in their ability to attach, but they carry strict semantic domains. The negating prefixes alone constitute a system worth mastering in full:

*un-* (Germanic, Level II) negates adjectives and reverses the action of verbs: *unhappy*, *unlucky*, *undo*, *unpack*. It is fully productive on adjectives derived from past participles: *undefeated*, *unverified*, *unprocessed*. *in-/im-/ir-/il-* (Latinate, Level I) negates adjectives of Latin origin and undergoes assimilation to the following consonant's place of articulation: *inappropriate*, *impossible*, *irrational*, *illegal*. This assimilation is itself a relic of Latin morphophonology imported wholesale. *non-* (Latinate, Level I) negates without connotation of contrariety: *non-standard*, *non-linear*, *non-profit*. *dis-* (Latinate, Level I) expresses reversal, removal, or negation: *disappear*, *dismantle*, *dishonest*. The practitioner must know that *un-* and *dis-* are not interchangeable: *undressed* implies a previous state of being dressed that was reversed, while *misdressed* (using *mis-*) implies incorrectness in the dressing. These connotational gradations are not stylistic choices; they are semantic facts.

### Compounding: Germanic Productivity Unleashed

Compounding is the morphological process English has historically valued most, particularly in its Germanic register, and it operates with a freedom unavailable in Romance languages. English compounds form by juxtaposing two or more free morphemes, with the rightmost element (the **head**) determining the grammatical category and the leftmost element(s) functioning as modifiers. This is the **right-headedness principle**, and it applies with overwhelming consistency: a *blackbird* is a bird, a *doorknob* is a knob, a *software engineer* is an engineer.

The semantic relationships between the modifier and head in a compound are not marked grammatically but inferred from encyclopedic knowledge — which is both English compounding's greatest strength and its greatest interpretive challenge. Consider the following:

*snowball* = a ball *made of* snow  
*snowfall* = snow *that falls* (snowfall is an event, not a thing made of snow)  
*snow leopard* = a leopard *characterized/associated with* snow  
*snowplow* = a device *that plows* snow  
*snowblind* = blind *because of* snow  

Each compound instantiates a different semantic relationship between the two elements, yet all are formed by exactly the same morphological operation. The semantic relationship must be inferred contextually, which means compounding's productivity is paired with interpretive ambiguity that speakers resolve pragmatically rather than morphologically.

The phonological signature of a compound, as opposed to an adjective-noun or noun-noun phrase, is **primary stress on the first element**: *a GREENhouse* (compound, a specific structure) versus *a green HOUSE* (phrase, a house that happens to be green). This prosodic distinction is functional and testable:

```
Compound:         [GREEN·house]  → Primary stress left
Phrase:           [green HOUSE]  → Primary stress right (on head noun)

Compound:         [BLACK·board]  → a specific classroom surface
Phrase:           [black BOARD]  → any board that is black in color
```

Compounds also undergo further compounding without limit, producing the recursive structures that characterize technical English in science, law, and computing: *aircraft carrier*, *aircraft carrier construction*, *aircraft carrier construction cost overrun*. The head noun *overrun* carries the primary lexical content; every element to its left modifies it, and the nesting structure is recoverable from encyclopedic knowledge and context, not from morphological marking.

---

## 3. High-Performance Optimization & Failure Modes

### Allomorphic Conditioning and Production Accuracy

The most pervasive failure mode in advanced English production is not grammatical but morphophonological: treating allomorphic variation as free variation rather than conditioned alternation. The plural, the third-person singular present, and the past tense of regular verbs all use the same three-way alternation (/s/, /z/, /ɪz/ and their voiced/voiceless/epenthetic analogs), and collapsing them to a single phonetic form produces subtle but pervasive signals of non-native production. The practitioner must implement automatic conditioning:

After voiced stops, fricatives, liquids, and all vowels, use the voiced allomorph: *dogs* /z/, *rooms* /z/, *cars* /z/, *trees* /z/. After voiceless stops and fricatives that are not sibilants, use the voiceless allomorph: *cats* /s/, *cliffs* /s/, *lengths* /s/. After sibilants (/s, z, ʃ, ʒ, tʃ, dʒ/), insert the epenthetic vowel: *buses* /ɪz/, *pages* /ɪdʒɪz/. The rule is: match voicing to the final segment of the stem; insert a vowel to break up a sibilant cluster.

An equally critical site of failure is the **past tense allomorphy** of regular weak verbs. The dental suffix has three allomorphs: /t/ after voiceless non-alveolar consonants (*walked*, *stopped*, *laughed*), /d/ after voiced segments and all vowels (*loved*, *faded*, *jogged*), and /ɪd/ after alveolar stops /t/ and /d/ themselves (*wanted*, *landed*, *faded*). The epenthetic vowel appears specifically to prevent homorganic cluster formation: *\*wantd* would involve two adjacent alveolar stops, which are impossible to perceive distinctly in running speech. Producing *wanted* as /ˈwɒntd/ rather than /ˈwɒntɪd/ deletes a syllable and signals morphological breakdown.

### Blocking, Gaps, and Lexical Accidents

The most consequential failure mode in derivational morphology is not over-application but **under-application caused by blocking**. Blocking is the phenomenon whereby an already-existing word prevents the derivation of an otherwise expected form. The classic cases: *stealer* is blocked by *thief*, *curer* is blocked by *healer* and *doctor*, *filler* as a nonce form is blocked in many contexts by *padding* or *content*. More precisely, an existing lexical item in the same semantic slot as a would-be derived form suppresses the derived form from achieving currency, even if the derivation is structurally impeccable.

This creates productive asymmetries that trap even fluent writers. English forms agent nouns freely with *-er* (Germanic) and *-or* (Latinate), but the choice between them is not predictable from the verb alone: *actor*, not *\*acter*; *translator*, not *\*translater*; *speaker*, not *\*speakor*. The rule is stratum-based: Latinate roots strongly prefer *-or*, Germanic roots strongly prefer *-er*, but historical accidents mean some Latinate verbs (*translate*, *act*) entered English through routes that set their agent noun suffix before the rule could apply transparently. The only reliable strategy is to learn the derivational family of high-frequency Latinate verbs as a cluster: the verb *act* in its Latinate paradigm gives *actor*, *action*, *active*, *actuality*, *actuate*, *activation*. Knowing the cluster is more productive than knowing any single member in isolation.

The inverse of blocking is the **derivational gap**, where a structurally expected form simply does not exist for idiosyncratic historical reasons. English has no standard noun derived from *speak* by the *-tion* suffix (*\*speakion* is impossible because the verb is Germanic, not Latinate), so the gap is filled by the unrelated noun *speech*, a Germanic form from a different root entirely. Similarly, there is no standard adjective *\*speakable* in widespread use, though the negative *unspeakable* exists (another asymmetry: negation sometimes licenses a form that the affirmative version blocks). The practitioner navigating technical writing must recognize these gaps as features of the lexicon's historical stratification, not errors, and must maintain a repertoire of cross-stratum synonyms (*speak/discourse*, *begin/commence*, *ask/inquire*, *help/assist*) to route around them when register demands.

### Morphological Parsing as an Active Skill

The highest-level performance skill in English morphology is **real-time parsing of unfamiliar polysyllabic words** by stratum, root, and affix. A specialist encountering the word *antidisestablishmentarianism* for the first time can fully parse it without prior exposure: *anti-* (against, Level I prefix) + *dis-* (reversal, Level I prefix) + *establish* (Level II verb, root) + *-ment* (Level II nominalizer) + *-arian* (Level I person/adherent suffix) + *-ism* (Level I doctrine suffix). The word means "opposition to the doctrine of removing the Church of England's established status." Each morpheme contributes exactly its standard meaning; no semantic drift complicates the parse. This compositional transparency is the system working as designed.

The practitioner should cultivate this skill through explicit **morpheme mapping** of academic and technical vocabulary. When encountering *teleological*, parse: *telos* (Greek root: end, purpose) + *-logy* (Greek root: study, discourse) + *-ical* (Level I adjectivizing suffix). When encountering *epistemological*, parse: *episteme* (Greek root: knowledge) + *-logy* + *-ical*. When encountering *phenomenological*, parse: *phainomenon* (Greek root: that which appears) + *-logy* + *-ical*. The suffix cluster *-logical* is a single combinatorial unit attaching to Greek nominal roots to yield adjectives meaning "pertaining to the systematic study of X." Recognizing this cluster multiplies vocabulary acquisition by an order of magnitude, because one rule covers *biological*, *geological*, *psychological*, *sociological*, *anthropological*, *methodological*, and every other member of an open class.

### The Productivity Paradox and Register Control

A sophisticated failure mode unique to advanced practitioners is **over-productivity**: applying a generative rule beyond its actual scope because the rule is correctly identified but its domain boundaries are not. Level II *-ness* is fully productive — but *-ity* is not, and attempting to derive *\*oddity* from *odd* when the actual form is *oddness* (or recognizing that *oddity* does exist but with a semantic drift toward "a strange thing" rather than "the quality of being odd") requires knowing that two suffixes can in principle apply but diverge semantically. *Happiness* and *\*happity* illustrate this: *-ity* simply cannot attach to Germanic *happy*, and the attempt yields an unacceptable form. Level I suffixes are constrained to Level I bases; attaching *-ity* to a Germanic adjective crashes the morphological derivation.

The practical workflow for controlling this is explicit stratum-tagging of your active vocabulary. When you learn a new adjective, determine which stratum it belongs to: if it has Latin or Greek roots, it will accept Level I suffixes and generate Level I derivational families. If it has Germanic or Old English roots, it uses Level II. For hybrid cases (words that have been in English long enough to develop morphological ambiguity), consult the established derivational family rather than generating novel forms. This discipline prevents the production of non-words while dramatically accelerating accurate vocabulary generation in technical and academic registers, where the Latinate stratum dominates and its derivational regularities are both more systematic and more directly learnable than the apparent irregularity of English morphology's surface suggests.
