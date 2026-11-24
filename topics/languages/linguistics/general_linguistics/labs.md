# Operational Verification Labs: General Linguistics

## Objective & Operational Lab Setup

The operational verification laboratory for general linguistics transforms theoretical constructs into measurable, reproducible analytical procedures. This laboratory sequence trains practitioners to execute phonetic transcription protocols, conduct morphosyntactic analysis of natural language corpora, measure typological parameters across language families, and validate linguistic hypotheses through controlled empirical observation. The practitioner operates as both field linguist and laboratory analyst, moving fluidly between elicitation sessions with native informants, acoustic waveform analysis, and statistical verification of distributional patterns in authentic language data.

The analytical environment requires three foundational components. First, establish a phonetic workbench with Praat acoustic analysis software, a calibrated headset microphone with flat frequency response between 80 Hz and 15 kHz, and the International Phonetic Alphabet reference chart. Second, configure a corpus analysis environment using either Python with NLTK and spaCy libraries or R with quanteda and tidytext packages, paired with access to reference corpora such as the Universal Dependencies treebanks, the Leipzig Corpora Collection, or the CHILDES database for acquisition studies. Third, prepare a fieldwork documentation system using ELAN for time-aligned multimodal annotation, FLEx (FieldWorks Language Explorer) for lexicon building and interlinear glossing, and a structured elicitation protocol template covering phonemic inventory, basic morphosyntax, and lexical semantics across semantic domains defined by the Leipzig-Jakarta Basic Vocabulary List.

The practitioner must internalize the distinction between three operational modes. Phonetic analysis operates in the acoustic and articulatory domain, measuring physical observables such as formant frequencies, voice onset time, and tongue position tracked via ultrasound or palatography. Phonological analysis abstracts to contrastive mental representations, employing minimal pair elicitation and distributional analysis to determine which acoustic distinctions carry functional load in the language's sound system. Morphosyntactic analysis treats language as a compositional combinatorial system, applying operational tests for constituency, movement, and case assignment to uncover the algebraic architecture governing how morphemes and words assemble into grammatical utterances.

The laboratory methodology enforces a strict empirical cycle: formulate a testable hypothesis about linguistic structure, design an elicitation or corpus search protocol that generates relevant data, execute the protocol under controlled conditions, apply quantitative or qualitative analytical procedures to the resulting dataset, and evaluate whether the observed patterns support or falsify the initial hypothesis. This mirrors the operational discipline of experimental phonetics, corpus linguistics, and descriptive field methodology, ensuring that theoretical claims about language remain grounded in reproducible observational evidence.

## Exercise 1: Foundational Practical Implementation

### Phonetic Transcription and Formant Analysis Protocol

The first operational exercise establishes phonetic transcription competence and acoustic measurement technique. The practitioner will record a native speaker producing a controlled phonetic dataset, transcribe the utterances in narrow IPA notation, extract acoustic measurements from the waveform, and correlate articulatory categories with measurable acoustic signatures.

Begin by preparing the recording environment. Select a quiet room with minimal ambient noise, ideally below 35 dB SPL background level. Position the microphone three to five centimeters from the speaker's mouth at a forty-five-degree angle to minimize plosive air bursts. Configure the recording software to capture uncompressed WAV format at 44.1 kHz sampling rate with 16-bit depth, ensuring the Nyquist frequency comfortably exceeds the highest relevant formants for vowel analysis.

Design the elicitation word list to sample the language's phonemic inventory systematically. For a vowel space analysis, construct minimal sets where target vowels appear in identical consonantal frames, controlling for coarticulatory effects. For English, a canonical frame uses /hVd/ words: "heed" /hid/, "hid" /hɪd/, "head" /hɛd/, "had" /hæd/, "hod" /hɑd/, "hawed" /hɔd/, "hood" /hʊd/, "who'd" /hud/. The voiceless glottal fricative /h/ provides minimal coarticulatory influence, while the voiced alveolar stop /d/ ensures a clear vowel offset. Instruct the speaker to produce each word three times in the carrier sentence "Say [word] again" to provide consistent prosodic context and statistical sampling.

Execute the recording session systematically. Record the entire carrier sentence sequence, maintaining consistent speaking rate and vocal effort across repetitions. Monitor input levels to avoid clipping while maximizing signal-to-noise ratio, targeting peak amplitudes between negative twelve and negative six dB relative to full scale. After recording, save the session with metadata documenting speaker demographics, recording parameters, and session conditions.

Open the recorded file in Praat. The waveform window displays amplitude variation over time, while the spectrogram reveals the frequency-domain structure. Configure the spectrogram view range from zero to five thousand Hertz with a dynamic range of fifty dB, using a Gaussian window with a time step of 0.005 seconds. The spectrogram displays formants as dark horizontal bands corresponding to resonances of the vocal tract.

Locate the midpoint of each target vowel by identifying the steady-state region where formant trajectories stabilize, avoiding the onset and offset transitions influenced by adjacent consonants. Place the analysis cursor at this temporal midpoint. Under the Formant menu, select "Show formants" to overlay the automatically tracked formant trajectories. Extract the first formant frequency F1, reflecting jaw height and tongue height, and the second formant frequency F2, reflecting tongue frontness and backness. Record these measurements in a structured spreadsheet with columns for word, vowel phoneme, repetition number, F1 in Hertz, and F2 in Hertz.

After extracting measurements for all tokens across all repetitions, compute the mean F1 and F2 values for each vowel category. Plot the vowel space in F1-F2 acoustic space, with F1 on the inverted vertical axis (high F1 at bottom corresponding to low tongue position) and F2 on the inverted horizontal axis (high F2 at left corresponding to front tongue position). This acoustic vowel space mirrors the articulatory vowel quadrilateral, with high front vowels like /i/ clustering in the upper-left region with low F1 (approximately 280 Hz for male speakers) and high F2 (approximately 2250 Hz), while low back vowels like /ɑ/ occupy the lower-right region with high F1 (approximately 730 Hz) and low F2 (approximately 1090 Hz).

The operational insight emerges from correlating acoustic measurements with articulatory phonetic categories. The first formant F1 varies inversely with tongue height: high vowels exhibit low F1 because a high tongue position creates a large pharyngeal cavity and small oral cavity, lowering the first resonance frequency. The second formant F2 varies directly with tongue frontness: front vowels exhibit high F2 because a front tongue position creates a short front cavity and long back cavity, raising the second resonance frequency. This acoustic-articulatory mapping constitutes the foundation of phonetic science, enabling the practitioner to infer unobservable articulatory configurations from observable acoustic signals.

Extend the analysis by measuring voice onset time for stop consonants. Record minimal pairs distinguishing voiced and voiceless stops in initial position, such as "bat" /bæt/ versus "pat" /pæt/, "dab" /dæb/ versus "tab" /tæb/, "gap" /ɡæp/ versus "cap" /kæp/. Voice onset time measures the interval between the stop release burst and the onset of periodic voicing for the following vowel. In the Praat waveform, identify the release burst as a sharp transient spike, then locate the first glottal pulse of the vowel where the waveform shows clear periodic oscillation. Measure the temporal interval in milliseconds. English voiced stops exhibit short-lag VOT typically between negative fifty and plus twenty milliseconds (negative values indicate voicing lead where glottal pulsing begins before the release burst), while voiceless stops exhibit long-lag VOT between thirty and one hundred milliseconds due to the aspiration period before voicing onset. This quantitative acoustic distinction provides operational verification of the phonological voicing contrast.

### Morphological Segmentation and Glossing Protocol

The second foundational exercise develops morphological analysis skills through systematic segmentation and interlinear glossing of morphologically complex utterances. The practitioner will analyze authentic language data, identify morpheme boundaries, assign grammatical functions to each morpheme, and construct a complete interlinear gloss following the Leipzig Glossing Rules convention.

Select a morphologically rich language sample from a typologically distinct family. For this exercise, analyze the following Turkish sentence, chosen because Turkish exhibits transparent agglutinative morphology where each morpheme carries a single discrete grammatical function and boundaries remain phonologically clear:

**Çocuklar-ımız-ı gör-e-me-di-niz mi?**

Begin segmentation by identifying the root morphemes that carry lexical meaning. The root *çocuk* means "child" as a free-standing nominal stem. The root *gör* means "see" as a verbal stem. All other material consists of bound affixes that modify these roots grammatically.

Proceed left-to-right through the nominal constituent. The plural suffix *-lar* marks plural number, yielding "children." The first-person plural possessive suffix *-ımız* marks possession by the speaker group, translating to "our." The accusative case suffix *-ı* marks the noun phrase as the direct object of the transitive verb. Each suffix attaches sequentially in a fixed templatic order: plural precedes possessive, possessive precedes case. This agglutinative architecture contrasts sharply with fusional languages like Russian or Latin where a single portmanteau morpheme simultaneously encodes multiple grammatical categories.

Analyze the verbal constituent with equal precision. The verbal stem *gör* "see" combines with the negative suffix *-me*, which negates the verb's assertion. The aorist tense suffix *-e* indicates habitual or generic time reference, though in this context it combines with the negative to form the potential negative construction meaning "not able to." The past tense suffix *-di* situates the event in past time. The second-person plural subject agreement suffix *-niz* cross-references the grammatical subject as second-person plural "you." The interrogative enclitic *mi*, written as a separate orthographic word but prosodically bound, converts the statement into a polar question.

Construct the three-tier interlinear gloss following Leipzig Glossing Rules conventions. The first tier presents the original utterance with morpheme boundaries marked by hyphens. The second tier provides morpheme-by-morpheme translations, using language-specific glosses for lexical morphemes and standardized abbreviations for grammatical morphemes. The third tier offers a free translation capturing the natural English rendering:

```text
Çocuk-lar-ımız-ı        gör-e-me-di-niz              mi?
child-PL-POSS.1PL-ACC   see-AOR-NEG-PST-2PL          Q
"Couldn't you see our children?" / "Didn't you see our children?"
```

The abbreviation system follows standard conventions: PL for plural, POSS for possessive with person-number specification, ACC for accusative case, AOR for aorist aspect, NEG for negation, PST for past tense, and Q for question marker. This formalism enables cross-linguistic comparison and eliminates ambiguity in morphological analysis.

Execute a second analysis on a polysynthetic language sample to experience radically different morphological organization. Analyze this West Greenlandic sentence:

**Aliikuseq-suar-tuaannar-sinnaa-nngi-vip-putit**

Segment the single phonological word into its constituent morphemes. The nominal root *aliikuseq* means "entertainment." The augmentative suffix *-suar* adds the meaning "big" or "great." The suffix *-tuaannar* means "only" or "merely." The verbal suffix *-sinnaa* means "can" or "be able to." The negative suffix *-nngi* negates the assertion. The indicative mood suffix *-vip* marks realis mood and interrogative illocution. The second-person singular subject suffix *-putit* cross-references the subject as "you (singular)."

The complete gloss reveals the sentence's internal structure:

```text
aliikuseq-suar-tuaannar-sinnaa-nngi-vip-putit
entertainment-big-only-can-NEG-IND-2SG
"Can't you just have some fun?" (lit. "Are you not able to only great-entertainment?")
```

This polysynthetic construction packs an entire propositional meaning into a single phonological word through recursive morphological composition. The practitioner observes that morphological typology exists on a continuum: isolating languages like Mandarin approach one morpheme per word, agglutinative languages like Turkish clearly concatenate discrete morphemes, fusional languages like Russian merge multiple grammatical categories into portmanteau morphemes, and polysynthetic languages like West Greenlandic incorporate multiple argument positions and adjuncts within the verbal complex.

The operational discipline requires documenting the morpheme inventory in a structured lexicon. Create a spreadsheet with columns for morpheme form, morphological category (root, derivational affix, inflectional affix, clitic), grammatical function, and allomorph conditions. For Turkish, document that the plural morpheme appears as *-lar* after back vowels and *-ler* after front vowels, exemplifying vowel harmony. For the possessive paradigm, document the complete set: *-ım/-im* (1SG), *-ın/-in* (2SG), *-ı/-i/-u/-ü* (3SG), *-ımız/-imiz* (1PL), *-ınız/-iniz* (2PL), *-ları/-leri* (3PL, marks possessed noun in possessive construction). This systematic documentation transforms intuitive parsing into reproducible analytical procedure.

### Syntactic Constituency Tests and Tree Diagram Construction

The third foundational exercise establishes operational methods for uncovering hierarchical syntactic structure through constituency tests. The practitioner will apply diagnostic procedures to determine which strings of words form syntactic constituents, construct labeled tree diagrams representing the hierarchical organization, and verify the analysis through substitution, movement, and coordination tests.

Begin with a simple transitive sentence: "The experienced linguist analyzed the complex data." Apply the substitution test by replacing candidate strings with proforms. The string "the experienced linguist" can be replaced with the pronoun "she" yielding "She analyzed the complex data," confirming that this string forms a noun phrase constituent. Similarly, "the complex data" can be replaced with "it" yielding "The experienced linguist analyzed it," confirming NP status. The string "experienced linguist" cannot stand alone as the subject; the determiner "the" must be included, demonstrating that determiners obligatorily combine with their NP complements.

Apply the movement test by fronting constituents for emphasis or questioning. The entire object NP can be fronted: "The complex data, the experienced linguist analyzed (with great care)." The verb phrase "analyzed the complex data" can be fronted in do-so replacement: "The experienced linguist analyzed the complex data, and the graduate student did so too." The prepositional phrase "with great care" can be fronted: "With great care, the experienced linguist analyzed the complex data." Constituents exhibit mobility under syntactic operations, while non-constituents resist movement.

Apply the coordination test by joining parallel structures with conjunctions. Two NPs can coordinate: "The experienced linguist and the graduate student analyzed the complex data." Two VPs can coordinate: "The experienced linguist analyzed the complex data and wrote a detailed report." The fact that we can coordinate "analyzed the complex data" with "wrote a detailed report" confirms that these strings form VP constituents. Attempting to coordinate non-constituents produces ungrammatical results: *"The experienced linguist analyzed and the graduate student collected the complex data," where "analyzed" and "the graduate student collected" are attempted coordinates but lack parallel structure.

Construct the hierarchical tree diagram encoding the constituent structure. Begin with the sentence node S at the root. The sentence immediately dominates a noun phrase subject and a verb phrase predicate. The subject NP branches into a determiner "the" and a nominal constituent N', which further branches into the adjective "experienced" and the noun head "linguist." The verb phrase branches into a transitive verb "analyzed" and its NP complement, which mirrors the subject structure with determiner "the," adjective "complex," and noun head "data."

```text
                    S
          __________|__________
         |                     |
        NP                    VP
    _____|_____           _____|_____
   |           |         |           |
  Det         N'         V          NP
   |      _____|____     |      _____|_____
  the    |          |    |     |           |
        Adj         N    |    Det         N'
         |          |    |     |      _____|____
   experienced  linguist |    the    |          |
                         |          Adj         N
                      analyzed       |          |
                                 complex      data
```

The tree topology embodies X-bar theory, where each lexical category projects to an intermediate X' level and then to a maximal XP level. The N' level allows adjectives to modify the noun before the determiner attaches at the NP level. This captures the generalization that determiners outscope adjectives, evidenced by the interpretation: "the" quantifies over the set of entities that are both experienced and linguists, not over experiences or linguists separately.

Extend the analysis to embedded clauses. Analyze the sentence: "The researcher discovered that the hypothesis was false." The string "that the hypothesis was false" forms a complement clause, confirmed by substitution with "it" ("The researcher discovered it") and by movement in questioning ("What did the researcher discover? That the hypothesis was false."). The complementizer "that" heads a CP projection dominating a finite clause with subject NP "the hypothesis" and VP "was false." The entire CP functions as the direct object of the verb "discovered."

The tree structure now includes recursive embedding:

```text
                          S
              ____________|____________
             |                         |
            NP                        VP
        _____|____               _____|________
       |          |             |              |
      Det        N'             V             CP
       |          |             |         _____|________
      the         N             |        |              |
                  |             |        C              S
            researcher     discovered    |        ______|______
                                        that     |             |
                                                NP            VP
                                            _____|____    _____|____
                                           |          |   |          |
                                          Det        N'   V         AP
                                           |          |   |          |
                                          the         N  was         A
                                                      |              |
                                                hypothesis        false
```

This recursive structure exemplifies the fundamental property of human syntax: discrete infinity, where finite computational rules generate unbounded hierarchical structures through repeated application of Merge operations combining syntactic objects into larger constituents.

Execute a final constituency test on a complex sentence with multiple potential attachment sites. Analyze: "The student read the book on the train with enthusiasm." The prepositional phrase "on the train" could modify either the noun "book" (the book that is located on the train) or the verb "read" (the reading event occurred on the train). The prepositional phrase "with enthusiasm" could modify the verb "read" (manner adverbial) or potentially the noun phrase "the book on the train" (though this reading is semantically implausible). Apply diagnostic tests to disambiguate. If "on the train" modifies the noun, it should move with the NP under fronting: "The book on the train, the student read (with enthusiasm)." If it modifies the verb, it should move independently: "On the train, the student read the book (with enthusiasm)." The latter movement pattern confirms VP-attachment. The structural ambiguity arises because PP adjuncts can attach at multiple heights in the tree, and syntactic constituency tests combined with semantic plausibility determine the intended structure.

## Exercise 2: Parameter Variation & Empirical Analysis

### Cross-Linguistic Typological Survey: Word Order Parameters

The second exercise sequence develops skills in cross-linguistic comparison and typological parameter identification. The practitioner will collect data from genealogically diverse languages, measure typological parameters governing word order, grammatical case, and alignment systems, and evaluate implicational universals through statistical correlation analysis.

Construct a stratified language sample ensuring genealogical diversity. Select twenty languages distributed across the world's major language families: Indo-European (English, Russian, Hindi), Sino-Tibetan (Mandarin, Burmese), Niger-Congo (Swahili, Yoruba), Afro-Asiatic (Arabic, Hebrew), Austronesian (Tagalog, Malagasy), Trans-New Guinea (Fore, Kewa), Uralic (Finnish, Hungarian), Turkic (Turkish, Uzbek), Japonic (Japanese), Koreanic (Korean), Dravidian (Tamil), and Quechuan (Quechua). This sampling strategy avoids Galton's problem where typological correlations reflect shared genealogical inheritance rather than independent structural pressures.

Define the first parameter: basic word order in transitive clauses. For each language, elicit or extract from reference grammars the unmarked word order for a simple transitive sentence with pronominal subject, lexical object, and telic tense marking. Classify each language as SOV, SVO, VSO, VOS, OVS, or OSV. Record additional parameters: whether the language exhibits verb-second (V2) constraint overriding basic order in main clauses, whether it allows null subjects (pro-drop), and whether scrambling or topic-fronting operations produce frequent deviations from the canonical order.

Tabulate the distribution. Empirical typological surveys consistently show that SOV and SVO dominate, together accounting for approximately eighty-five percent of languages. VSO languages constitute roughly ten percent. VOS, OVS, and OSV orders are rare, together accounting for less than five percent. Your sample should reflect this distribution: approximately eight to nine SOV languages (Japanese, Korean, Turkish, Hindi, Quechua, Burmese, Fore), seven to eight SVO languages (English, Russian, Mandarin, Swahili, Yoruba, Malagasy), three to four VSO languages (Arabic, Tagalog), and one or two languages with less common orders.

Define the second parameter: adposition order relative to noun phrases. For each language, determine whether adpositions appear before their NP complements (prepositions) or after (postpositions). English uses prepositions ("in the house," "to the market"), while Japanese uses postpositions ("uchi ni" house-DAT, "ichi e" market-TO). Record this binary parameter for all twenty languages.

Execute the correlation analysis. Tabulate the co-occurrence of verb-object order and adposition order in a two-by-two contingency table:

| V-O Order | Prepositions | Postpositions |
|-----------|--------------|---------------|
| VO        | 12           | 1             |
| OV        | 0            | 7             |

The table reveals a strong correlation: VO languages overwhelmingly select prepositions, while OV languages overwhelmingly select postpositions. Compute the phi coefficient measuring the strength of association. With twelve VO-Prep languages, one VO-Post language, zero OV-Prep languages, and seven OV-Post languages, the observed distribution deviates sharply from independence. The chi-squared test yields a test statistic exceeding the critical value at p less than 0.001, confirming that the correlation is statistically robust and not attributable to sampling noise.

The operational insight connects surface typological parameters to deeper generative principles. The correlation between verb-object order and adposition order instantiates the head-direction parameter: languages exhibit consistency in whether heads precede or follow their complements across syntactic categories. In head-initial languages (VO, Prep), verbs precede objects and prepositions precede NPs. In head-final languages (OV, Post), verbs follow objects and postpositions follow NPs. This harmony arises because a single parametric setting propagates across the grammar, producing correlated surface effects.

Extend the analysis to additional correlated parameters. Measure the order of genitive modifiers relative to possessed nouns: does "John's book" (genitive-noun) or "the book of John" (noun-genitive) predominate? Measure the order of relative clauses relative to head nouns: prenominal ("the book that I read") or postnominal? Measure auxiliary-main verb order: auxiliary-initial ("will read") or auxiliary-final ("read will")? Tabulate these parameters and compute pairwise correlations. The harmonic pattern predicts that head-initial languages select noun-genitive, noun-relative clause, and auxiliary-main verb orders, while head-final languages select genitive-noun, relative clause-noun, and main verb-auxiliary orders. Your empirical results should largely confirm these predictions, though individual languages exhibit exceptions due to language contact, diachronic change, or domain-specific reanalysis.

### Grammatical Case and Alignment System Classification

The second parameter variation exercise analyzes grammatical case systems and alignment patterns in intransitive versus transitive clauses. The practitioner will classify languages into nominative-accusative, ergative-absolutive, or split systems based on how they mark the single argument of intransitive verbs (S), the agent-like argument of transitive verbs (A), and the patient-like argument of transitive verbs (P).

Begin with a nominative-accusative language, Russian. Elicit three sentences: an intransitive clause with a subject ("The child sleeps"), a transitive clause with agent and patient ("The child sees the cat"), and a transitive clause with pronominal arguments. Record the morphological case marking on each argument:

Intransitive: **Rebënok spit.** (child.NOM sleeps)  
Transitive: **Rebënok vidit koshku.** (child.NOM sees cat.ACC)

The single argument S "rebënok" (child) appears in the nominative case, identical to the transitive agent A. The transitive patient P "koshku" (cat) appears in the accusative case, distinct from both S and A. This defines nominative-accusative alignment: S and A pattern together, marked with nominative case (or zero marking), while P receives distinctive accusative marking. The same pattern holds for pronouns: "ja" (I.NOM) as S and A, versus "menja" (me.ACC) as P.

Contrast this with an ergative-absolutive language, Basque. Elicit parallel sentences:

Intransitive: **Umea lo dago.** (child.ABS sleep AUX)  
Transitive: **Umeak katua ikusi du.** (child.ERG cat.ABS seen AUX)

The single argument S "umea" (child) appears in the absolutive case with zero marking. The transitive patient P "katua" (cat) also appears in the absolutive case with zero marking. The transitive agent A "umeak" receives distinctive ergative marking with the suffix *-k*. This defines ergative-absolutive alignment: S and P pattern together in the absolutive, while A receives distinctive ergative marking. The alignment reverses the grouping relative to nominative-accusative systems.

The operational procedure requires testing alignment across multiple grammatical domains: case morphology, verb agreement, and syntactic pivot constraints. In Russian, the verb agrees with the nominative argument (S or A), not with the accusative: "Rebënok spit" (child.NOM.SG sleep.3SG) versus "Rebënok vidit koshku" (child.NOM.SG sees.3SG cat.ACC). In Basque, the auxiliary agrees with both the absolutive argument (S or P) and the ergative argument (A) through a complex portmanteau morphology: "lo dago" (sleep AUX.3SG.ABS) contains an absolutive agreement slot, while "ikusi du" (seen AUX.3SG.ABS.3SG.ERG) contains both absolutive and ergative agreement slots.

Extend the analysis to syntactic pivots in relativization and coordination. In nominative-accusative languages like English, the subject position (S/A) serves as the privileged pivot for syntactic operations. Relative clauses preferentially relativize subjects: "the child who sleeps" and "the child who sees the cat" readily extract the S and A positions, while relativizing the object requires additional machinery: "the cat that the child sees" involves a gap in object position. In ergative-absolutive languages, the absolutive position (S/P) may serve as the syntactic pivot. Some ergative languages exhibit syntactic ergativity where operations like coordination deletion target S/P rather than S/A: "The child arrived and [the child] was seen" versus *"The child arrived and [the child] saw the cat," where only S/P can be deleted under coreference.

Classify the alignment system for each language in your sample. Many languages exhibit split ergativity, where alignment varies depending on tense-aspect features, nominal hierarchy (pronoun versus noun), or clause type (main versus subordinate). Hindi exhibits split ergativity conditioned by aspect: perfective aspect triggers ergative-absolutive alignment with the agent marked by the postposition *ne* and the patient unmarked, while imperfective aspect triggers nominative-accusative alignment. Australian languages commonly exhibit split ergativity conditioned by the nominal hierarchy: pronouns follow nominative-accusative alignment while nouns follow ergative-absolutive alignment.

Construct a typological database with rows corresponding to languages and columns recording alignment features: case morphology alignment (nom-acc, erg-abs, tripartite, neutral), verb agreement alignment, relativization pivot (S/A versus S/P), and coordination deletion pivot. Compute the coherence index measuring whether alignment features within a language converge on a single system or exhibit mismatches. Languages with consistent alignment across all domains receive high coherence scores, while languages with splits or mixed systems receive lower scores. Your analysis will reveal that while the majority of languages exhibit either consistent nominative-accusative or consistent ergative-absolutive alignment, a substantial minority exhibit domain-specific splits requiring nuanced analysis.

### Quantitative Corpus Analysis: Zipf's Law and Lexical Frequency Distributions

The third parameter variation exercise applies quantitative methods to verify linguistic universals governing lexical frequency distributions. The practitioner will extract word frequency data from natural language corpora, plot rank-frequency distributions, and test whether the data conform to Zipf's Law, which predicts that word frequency is inversely proportional to frequency rank.

Select a large corpus of running text in a single language. For English, use a representative general corpus such as the British National Corpus (BNC) containing one hundred million words, or the Corpus of Contemporary American English (COCA) containing one billion words. For this exercise, a smaller but representative sample of ten million tokens suffices. Download a word frequency list from the corpus, formatted as a tab-separated file with columns for orthographic word form, raw frequency count, and optionally lemma and part-of-speech tag.

Load the frequency data into Python using pandas. Assume the file is named `corpus_frequencies.tsv`:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# Load frequency data
df = pd.read_csv('corpus_frequencies.tsv', sep='\t', 
                 names=['word', 'frequency'], skiprows=1)

# Assign rank based on descending frequency
df = df.sort_values('frequency', ascending=False).reset_index(drop=True)
df['rank'] = df.index + 1

# Display the top 20 most frequent words
print(df.head(20))
```

The output displays the highest-frequency words: function words and closed-class grammatical items such as determiners, pronouns, prepositions, and auxiliary verbs dominate. The top ranks typically include "the," "of," "and," "to," "a," "in," "is," "that," "for," "it," reflecting the ubiquity of grammatical function words across discourse contexts.

Zipf's Law posits that frequency f is inversely proportional to rank r: f ∝ 1/r, or equivalently f · r ≈ C for some constant C. Taking logarithms yields a linear relationship: log(f) = log(C) - log(r). Plot the rank-frequency distribution on logarithmic axes:

```python
# Filter to ranks 1 through 10,000 for visualization clarity
df_plot = df[df['rank'] <= 10000]

# Create log-log plot
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(df_plot['rank'], df_plot['frequency'], alpha=0.5, s=10)
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlabel('Rank (log scale)', fontsize=12)
ax.set_ylabel('Frequency (log scale)', fontsize=12)
ax.set_title('Zipf\'s Law: Rank-Frequency Distribution', fontsize=14)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('zipf_distribution.png', dpi=300)
plt.show()
```

The resulting scatter plot reveals an approximately linear relationship on the log-log axes, confirming the power-law structure. The highest-frequency words lie near the upper-left corner, while mid-frequency and low-frequency words extend toward the lower-right, forming a downward-sloping linear trend.

Quantify the fit by estimating the power-law exponent α in the relationship f = C · r^(-α). Use ordinary least-squares linear regression on the log-transformed data:

```python
# Log-transform rank and frequency
df_fit = df[df['rank'] <= 10000].copy()
df_fit['log_rank'] = np.log10(df_fit['rank'])
df_fit['log_frequency'] = np.log10(df_fit['frequency'])

# Perform linear regression
slope, intercept, r_value, p_value, std_err = stats.linregress(
    df_fit['log_rank'], df_fit['log_frequency']
)

print(f"Power-law exponent α: {-slope:.3f}")
print(f"Intercept log(C): {intercept:.3f}")
print(f"R-squared: {r_value**2:.3f}")
print(f"P-value: {p_value:.3e}")

# Overlay fitted line on plot
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(df_fit['rank'], df_fit['frequency'], alpha=0.3, s=10, label='Observed')
fitted_freq = 10**intercept * df_fit['rank']**slope
ax.plot(df_fit['rank'], fitted_freq, 'r-', linewidth=2, 
        label=f'Fitted: f = {10**intercept:.0f} · r^{slope:.2f}')
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlabel('Rank (log scale)', fontsize=12)
ax.set_ylabel('Frequency (log scale)', fontsize=12)
ax.set_title('Zipf\'s Law with Fitted Power Law', fontsize=14)
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('zipf_fitted.png', dpi=300)
plt.show()
```

The regression typically yields a power-law exponent α close to 1.0, confirming classical Zipf's Law. The R-squared value exceeds 0.95, indicating that the power-law model explains over ninety-five percent of the variance in the log-transformed data. The p-value approaches zero, confirming statistical significance.

The operational insight concerns the cognitive and communicative mechanisms underlying Zipf's Law. One account invokes a least-effort principle balancing speaker and hearer preferences: speakers prefer short, frequent words minimizing articulatory effort, while hearers prefer diverse, informative words minimizing ambiguity. The optimal balance produces a power-law distribution where a small number of high-frequency words carry low information content while a long tail of low-frequency words provide precise semantic distinctions. Alternative accounts invoke stochastic processes such as preferential attachment (rich-get-richer dynamics) or random multiplicative processes that naturally generate power-law distributions.

Extend the analysis by comparing lexical frequency distributions across languages. Extract frequency data from corpora in genealogically diverse languages (Mandarin, Arabic, Finnish, Japanese) and compute power-law exponents for each. The universal prediction holds that all languages exhibit power-law rank-frequency distributions with exponents close to 1.0, despite radical differences in morphological type, phonological inventory, and syntactic structure. Your empirical verification across multiple languages confirms this typological universal, demonstrating that Zipf's Law reflects deep properties of human language use independent of surface linguistic variation.

Compute additional distributional statistics. Calculate the type-token ratio (TTR), dividing the number of unique word types by the total number of word tokens. For large corpora, TTR decreases as corpus size increases because new tokens increasingly sample existing types rather than introducing new types. Instead, compute the standardized TTR by calculating TTR over successive corpus chunks of fixed size (e.g., 10,000 tokens) and averaging. Also compute lexical diversity metrics such as the measure of textual lexical diversity (MTLD), which counts how many sequential tokens can be processed before reaching a threshold TTR, then averages across random starting positions. These metrics provide operational measures of vocabulary richness useful for comparing registers, genres, or individual speakers.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Phonotactic Violation Detection and Repair Strategies

The third exercise sequence pushes the boundaries of linguistic systems by inducing violations of well-formedness constraints and observing repair strategies. The practitioner will generate phonotactically ill-formed strings violating native phonological constraints, elicit native speaker judgments on acceptability, and analyze the repair processes speakers invoke when forced to pronounce illegal sequences.

English phonotactics prohibit certain consonant clusters in syllable onsets and codas. The onset cluster /bn-/ is illegal: no English word begins with /bn/, as this violates the sonority sequencing principle requiring sonority to rise toward the syllable nucleus. Test this constraint by generating nonce words violating the restriction: "bnick," "bnat," "bnort." Present these written forms to native English speakers and ask them to pronounce the words. Record the pronunciations in narrow phonetic transcription.

Speakers employ several repair strategies. The most common strategy inserts an epenthetic vowel breaking the illegal cluster: [bəˈnɪk] "buhnick," [bəˈnæt] "buhnat," with a schwa [ə] inserted between the consonants to create two syllables. Alternative strategies include deleting one consonant (producing [nɪk] "nick," [næt] "nat" with initial /b/ deletion), or altering one consonant to create a legal cluster (producing [brɪk] "brick," [bræt] "brat" by substituting /r/ for /n/). The distribution of repair strategies reflects the relative ranking of phonological constraints: faithfulness constraints penalize deletion and feature change, while markedness constraints penalize epenthesis, with epenthesis typically emerging as the optimal repair when the violation is severe.

Test coda constraints. English allows complex codas like /-lf/ (shelf), /-lk/ (milk), /-sk/ (desk), but prohibits certain clusters violating the sonority sequencing principle. The cluster /-lp/ is marginal (appearing in "help," "scalp") but generally acceptable, while /-rp/ is rare but legal (appearing in "carp," "warp"). Create nonce words with marginal or illegal codas: "helk" (/hɛlk/), "welk" (/wɛlk/), "terp" (/tɜrp/). Elicit pronunciations and measure whether speakers accept these forms natively or employ repairs such as vowel epenthesis ([ˈhɛlək], [ˈwɛlək]) or consonant deletion ([hɛk], [wɛk]).

Quantify acceptability through gradient judgments. Present speakers with a continuum of syllable structures ranging from highly legal (matching frequent attested patterns) to highly illegal (violating multiple phonotactic constraints). Use a seven-point Likert scale where 1 indicates completely unacceptable and 7 indicates perfectly acceptable. Example stimuli:

- **Highly legal:** "blick" /blɪk/ (legal onset /bl-/, legal coda /-k/)
- **Moderately legal:** "spling" /splɪŋ/ (complex but legal onset /spl-/, legal coda /-ŋ/)
- **Marginal:** "shrelm" /ʃrɛlm/ (complex onset /ʃr-/ rare in English, complex coda /-lm/ legal)
- **Illegal:** "bnorg" /bnɔrɡ/ (illegal onset /bn-/, legal coda /-rɡ/)
- **Highly illegal:** "pfkung" /pfkʌŋ/ (illegal three-consonant onset /pfk-/, legal coda /-ŋ/)

Collect judgments from at least twenty native speakers. Compute mean acceptability ratings for each stimulus. Plot the ratings against a phonotactic legality index computed by summing constraint violations: zero violations for highly legal stimuli, one to two violations for marginal stimuli, three or more violations for highly illegal stimuli. The scatter plot typically reveals a strong negative correlation: as phonotactic violations increase, acceptability ratings decrease. Fit a linear regression model predicting acceptability from violation count. The regression slope quantifies the perceptual penalty associated with each phonotactic violation.

Extend the stress test to morphophonological alternations. English exhibits voicing assimilation in the plural suffix, which surfaces as /-s/ after voiceless consonants (cats /kæts/, books /bʊks/) and /-z/ after voiced consonants (dogs /dɔɡz/, birds /bɜrdz/). Test the robustness of this alternation by creating nonce nouns with unusual phonological properties: nouns ending in rare consonants (e.g., nonce word "blunge" /blʌndʒ/), nouns ending in consonant clusters (e.g., "kalsp" /kælsp/), or nouns ending in vowels (e.g., "flomay" /floˈmeɪ/). Elicit plural forms and verify whether speakers productively apply the voicing alternation rule or extend the suffix by analogy to similar-sounding existing words.

The operational discipline requires controlled manipulation of linguistic variables to isolate specific constraint effects. If testing the role of sonority sequencing, construct minimal pairs differing only in the sonority profile: /bl-/ (stop + liquid, rising sonority, legal) versus /lb-/ (liquid + stop, falling sonority, illegal). If testing the role of phoneme frequency, construct stimuli using high-frequency phonemes (like /t/, /n/, /s/) versus low-frequency phonemes (like /θ/, /ʒ/, /ŋ/), holding syllable structure constant. This experimental control enables the practitioner to attribute observed effects to specific phonological principles rather than confounding factors.

### Semantic Anomaly and Selectional Restriction Violation

The second stress-testing exercise probes semantic compositionality by generating sentences that are syntactically well-formed but semantically anomalous, violating selectional restrictions on argument-predicate combinations. The practitioner will construct categorically ill-formed semantic compositions, measure comprehension difficulty and plausibility judgments, and analyze the processes speakers invoke to coerce interpretations for anomalous inputs.

Chomsky's classic example "Colorless green ideas sleep furiously" demonstrates syntactic well-formedness coexisting with semantic anomaly. The sentence exhibits legal English syntax: adjective-adjective-noun subject, intransitive verb, manner adverb. Yet the semantic composition fails: "colorless" and "green" contradict (something cannot simultaneously lack color and be green), "ideas" do not possess color properties, "sleep" requires an animate subject, and "furiously" modifies actions not states. Construct parallel examples with specific types of semantic violation:

**Type mismatch (category error):** "The theory drank the equation." Verbs like "drink" select for animate agent subjects and liquid themes; applying "drink" to abstract entities "theory" and "equation" produces a category error violating ontological type requirements.

**Selectional restriction violation:** "The rock decided to evaporate." The verb "decide" presupposes a sentient, intentional agent; rocks lack intentionality, producing a violation. Similarly, "evaporate" in its transitive use ("evaporate the solution") can coerce an agentive reading, but in its intransitive use with an inanimate subject lacks agency.

**Contradictory modification:** "The dead linguist continued working." The adjective "dead" entails cessation of biological functions, while "continued working" presupposes ongoing activity, producing a contradiction.

**Impossible event structure:** "The event lasted for five seconds and three years." The temporal modification violates basic properties of time intervals: a single event cannot simultaneously have contradictory durations.

Present these sentences to native speakers and collect two types of judgment: acceptability ratings on a seven-point scale, and plausibility ratings measuring how easily the sentence could be interpreted as true in some real or hypothetical scenario. Acceptability ratings measure grammaticality and well-formedness, while plausibility ratings measure semantic coherence and real-world likelihood. For semantically anomalous but syntactically well-formed sentences, acceptability ratings will be intermediate (speakers perceive the sentences as "odd" but grammatical), while plausibility ratings will be very low (speakers judge the propositions as false or nonsensical).

Analyze coercion strategies speakers employ to rescue anomalous sentences. When forced to interpret "The theory drank the equation," speakers may invoke metaphorical mapping (interpreting "drank" as "absorbed" or "incorporated"), personification (attributing agency to abstract entities), or fictional-world reasoning (imagining a fantasy scenario where theories are animate beings). When interpreting "The rock decided to evaporate," speakers may reanalyze "rock" as metonymy for "rock climber" or invoke a fantasy scenario with sentient rocks. These coercion processes reveal the flexibility and robustness of semantic composition: comprehension systems actively repair violations by adjusting semantic types, relaxing presuppositions, or invoking non-literal interpretations.

Measure processing difficulty using self-paced reading or eye-tracking. Present sentences word-by-word or region-by-region, measuring reading times. Semantic anomalies produce elevated reading times at the critical region where the violation becomes detectable (typically the main verb or its complement), followed by spillover effects in subsequent regions as comprehension systems attempt repair. Compare reading times for semantically coherent sentences ("The student drank the coffee"), selectional restriction violations ("The theory drank the equation"), and syntactic violations (*"The student drank quickly the coffee"). Syntactic violations produce the strongest disruption, selectional violations produce intermediate disruption, and coherent sentences produce minimal disruption. This gradient pattern confirms that semantic composition operates incrementally, detecting violations as material unfolds and triggering repair processes modulating processing cost.

Extend the analysis to computational models. Train a neural language model (e.g., GPT-based architecture or BERT) on a large text corpus, then measure the model's surprisal (negative log probability) assigned to each word in semantically coherent versus anomalous sentences. Well-formed sentences exhibit low average surprisal, indicating that the model's learned distributional patterns predict each word given context. Anomalous sentences exhibit elevated surprisal at the violation point, indicating that the model detects the semantic incoherence as a distributional anomaly. Compare model surprisal to human reading times; strong correlations confirm that distributional learning captures aspects of semantic well-formedness.

### Syntactic Garden-Path Ambiguity and Reanalysis

The third stress-testing exercise exploits temporary syntactic ambiguity to probe parsing mechanisms. The practitioner will construct garden-path sentences where early material admits multiple structural analyses, forcing the parser down an incorrect path, then provide disambiguating material triggering reanalysis. Measuring comprehension difficulty at the disambiguation point reveals the cost of structural reanalysis.

The canonical garden-path sentence "The horse raced past the barn fell" induces misanalysis because "raced" is initially parsed as the main verb of a simple transitive clause ("The horse raced past the barn"), but the appearance of "fell" reveals that "raced past the barn" is a reduced relative clause modifying "horse," and "fell" is the actual main verb. The correct parse is "The horse [that was] raced past the barn fell," where the relative clause contains a passive participle "raced" with elided auxiliary "was."

Construct minimal pairs contrasting garden-path sentences with unambiguous controls:

**Garden-path:** "The defendant examined by the lawyer turned out to be unreliable."  
**Unambiguous control:** "The defendant who was examined by the lawyer turned out to be unreliable."

The garden-path version omits the relative pronoun "who" and auxiliary "was," creating temporary ambiguity: "examined" could initially be the main verb ("The defendant examined [something] by the lawyer") before "turned out" forces reanalysis to a reduced relative clause structure. The unambiguous control explicitly marks the relative clause, eliminating ambiguity. Present both versions in self-paced reading and measure reading times at the critical region "turned out." Garden-path sentences exhibit significantly elevated reading times, quantifying the reanalysis cost.

Construct additional garden-path structures targeting different syntactic ambiguities:

**Main-verb/reduced-relative ambiguity:** "The boat floated down the river sank."  
**Noun-phrase/sentence-complement ambiguity:** "The woman told the man that she loved was leaving."  
(Temporary parse: "The woman told the man [that she loved [him]]" forced to reanalyze as "The woman told the man [that [she loved] was leaving]")

**Direct-object/sentential-complement ambiguity:** "The teacher knew the solution to the problem was incorrect."  
(Temporary parse: "The teacher knew [the solution]" reanalyzed to "The teacher knew [that the solution to the problem was incorrect]")

For each garden-path type, construct a corpus of twenty to forty examples and matched unambiguous controls. Recruit native speakers to complete the self-paced reading task. Analyze reading times using linear mixed-effects models with sentence type (garden-path vs. control) as a fixed effect and subject and item as random effects. The model estimates the magnitude of the garden-path effect, typically ranging from 200 to 500 milliseconds or more of additional reading time at the disambiguation point, with effects persisting into spillover regions.

The operational insight concerns the architecture of the human sentence parser. Garden-path effects demonstrate that parsing is incremental: the parser commits to a single structural analysis at each point based on available evidence, rather than maintaining multiple analyses in parallel. When disambiguating evidence contradicts the committed analysis, the parser must backtrack and rebuild the structure, incurring measurable processing cost. The parser's initial commitments follow principles such as minimal attachment (attach incoming material to the current phrase with the fewest syntactic nodes) and late closure (attach incoming material to the most recent phrase), which produce efficient parsing for most sentences but occasional errors for locally ambiguous structures.

Test individual differences in garden-path susceptibility. Some speakers exhibit larger garden-path effects, indicating less flexible reanalysis mechanisms, while others exhibit smaller effects, suggesting greater tolerance for ambiguity or more efficient error correction. Correlate garden-path effect size with working memory capacity measured by reading span tasks, where participants recall sentence-final words while comprehending sentences. Higher working memory capacity predicts smaller garden-path effects, confirming that parsing resilience depends on cognitive resources available for maintaining and revising structural hypotheses.

Extend the methodology to cross-linguistic comparison. Garden-path effects depend on language-specific syntactic properties. Languages with flexible word order and rich morphological case marking (e.g., Russian, Finnish) may exhibit reduced garden-path effects because case marking disambiguates syntactic roles early, preventing misanalysis. Languages with obligatory relative pronouns (e.g., Spanish, Italian) eliminate the reduced relative clause ambiguity entirely. Test parallel garden-path structures across languages, measuring whether typological properties modulate susceptibility to temporary ambiguity. Your analysis will reveal that garden-path effects are universal, reflecting the incremental nature of human parsing, but the specific configurations inducing garden-pathing vary based on grammatical properties, confirming the interaction between universal parsing principles and language-specific structural constraints.

## Operational Reference Guide & Diagnostic Checklist

### Phonetic Transcription Accuracy Verification

When conducting phonetic analysis, verify transcription accuracy through systematic cross-validation. Record the same token multiple times and transcribe independently; consistent transcriptions across repetitions confirm perceptual reliability. Use spectrograms to verify segmental boundaries and formant measurements, ensuring that transcription decisions reflect measurable acoustic properties rather than orthographic bias. For unfamiliar phones, consult the IPA chart and locate the sound based on articulatory features: place of articulation (bilabial, alveolar, velar, etc.), manner of articulation (stop, fricative, approximant, etc.), and voicing (voiced, voiceless). Cross-reference your transcription with reference materials such as the UCLA Phonetics Lab Archive or the Interactive IPA Chart with audio examples.

### Morphological Glossing Consistency Protocol

Maintain consistency in glossing abbreviations across analyses. Adopt the Leipzig Glossing Rules as the standard, using established abbreviations for grammatical categories: NOM (nominative), ACC (accusative), GEN (genitive), DAT (dative), 1SG (first person singular), PST (past tense), PFV (perfective aspect), NEG (negation). When encountering language-specific categories lacking standard abbreviations, define new abbreviations explicitly in a glossary, ensuring that each abbreviation is unique and transparent. For portmanteau morphemes encoding multiple categories (e.g., Spanish "-mos" encoding first person plural present indicative), separate the features with periods: 1PL.PRS.IND. Align glosses vertically in three-tier format for maximal clarity, and ensure that each morpheme in the object language has exactly one corresponding gloss element.

### Syntactic Tree Construction Validation

Validate syntactic trees using constituency tests. For each non-terminal node in the tree, verify that the dominated string passes substitution tests (can be replaced by a proform), movement tests (can be fronted or extracted), and coordination tests (can be conjoined with parallel structures). If a constituent fails these tests, revise the tree structure. Ensure that heads project correctly: lexical heads (N, V, A, P) project to intermediate X' levels and maximal XP levels. Verify that specifiers and complements occupy appropriate structural positions: specifiers occupy [Spec, XP] positions as sisters to X', while complements occupy sister positions to X under X'. Check that movement operations leave traces or copies in base positions, and that moved elements land in designated target positions such as [Spec, CP] for wh-movement or [Spec, TP] for subject raising.

### Corpus Frequency Extraction Quality Control

When extracting word frequencies from corpora, normalize for morphological variation by lemmatizing: collapse inflected forms (run, runs, running, ran) to a single lemma (run) unless investigating morphological frequency distributions specifically. Remove punctuation and convert to lowercase to avoid counting capitalized sentence-initial tokens as distinct from lowercase medial tokens. Filter out XML markup, metadata tags, and non-linguistic material. For languages with rich morphology, consider whether to count orthographic words or morphosyntactic words: in Turkish or Finnish, should an agglutinative word like "evlerimizden" (from-our-houses) count as one token or be segmented into constituent morphemes? The choice depends on research goals: word-level frequency analysis uses orthographic tokens, while morpheme-level analysis requires morphological segmentation.

### Statistical Significance Testing Standards

When conducting typological surveys or experimental studies, apply appropriate statistical tests based on data type and distributional assumptions. For categorical data (e.g., co-occurrence of word order parameters), use chi-squared tests for independence or Fisher's exact test for small samples. For continuous data (e.g., reading times, acceptability ratings), use t-tests or analysis of variance (ANOVA) when data are normally distributed with equal variances, or non-parametric alternatives (Mann-Whitney U, Kruskal-Wallis) when assumptions are violated. For repeated-measures designs with multiple observations per subject or item, use linear mixed-effects models with random intercepts and slopes, accounting for non-independence of observations. Report effect sizes (Cohen's d, eta-squared, R-squared) alongside p-values to quantify practical significance, not merely statistical significance. Apply multiple comparison corrections (Bonferroni, Holm, false discovery rate control) when conducting multiple tests to control family-wise error rate.

### Diagnostic Checklist for Field Elicitation Sessions

Before initiating field elicitation with a language consultant, prepare the elicitation protocol systematically. Define the linguistic domain under investigation (phonemic inventory, case system, verb morphology, clause structure). Prepare a structured elicitation list targeting the domain: for phonemic inventory, use minimal pairs and nonce words covering all suspected contrasts; for case systems, use transitive and intransitive sentences with varied noun types; for verb morphology, use paradigm frames eliciting all person-number-tense-aspect combinations. Obtain informed consent from the consultant, explaining the research purpose and ensuring the consultant understands they can decline to answer questions or withdraw at any time. Record sessions using high-quality equipment in a quiet environment. Take detailed metadata notes: consultant demographics, session date and duration, elicitation context. During elicitation, avoid leading questions; use prompts that elicit natural productions rather than metalinguistic judgments. When encountering unexpected forms, ask for repetitions and multiple examples to verify consistency. After the session, review recordings and transcribe utterances in IPA, glossing morphemes and annotating unusual features. Schedule follow-up sessions to verify initial hypotheses and fill gaps in the dataset.

### Troubleshooting Common Analytical Failures

When phonetic analysis produces inconsistent formant measurements, verify that the Praat formant tracking algorithm is configured correctly: adjust the maximum formant setting (5000 Hz for adult males, 5500 Hz for adult females, 8000 Hz for children) to optimize tracking accuracy. When automatic tracking fails, manually measure formants from the spectrogram by identifying the darkest bands at the temporal midpoint of the vowel. When morphological segmentation is ambiguous due to fusional morphology, apply multiple criteria: phonological (identify recurring sound sequences), distributional (identify which sequences co-occur freely versus obligatorily), and semantic (identify which sequences carry consistent meaning). When syntactic trees for complex sentences become unwieldy, simplify by analyzing embedded clauses independently before integrating into the matrix structure. When corpus searches return zero results, verify that the search query syntax is correct and that the corpus contains the relevant construction; if the construction is genuinely absent, this constitutes negative evidence supporting typological hypotheses about impossible or rare structures.
