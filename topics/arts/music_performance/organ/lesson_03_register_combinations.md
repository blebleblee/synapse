# Lesson 3: Register Combinations

## 1. First-Principles Intuition & Invariants

The pipe organ's register system constitutes a real-time acoustic synthesis architecture governed by the same physical principles that underpin modern audio DSP: superposition of waveforms, harmonic series relationships, and psychoacoustic masking. Unlike electronic synthesizers that generate tones through oscillators and filters, the organ produces sound through coupled aerodynamic-acoustic systems—pipes driven by pressurized air—where each register (stop) activates a discrete rank of pipes tuned to specific harmonic relationships.

The fundamental invariant is **pitch-class alignment**: all pipes across different stops that respond to a single key press maintain strict harmonic relationships, typically expressed in feet of pipe length. An 8' (eight-foot) stop produces the written pitch, a 4' stop sounds one octave higher, a 16' stop sounds one octave lower, and mutation stops like the Nazard 2⅔' sound a perfect fifth above the octave. This fractional notation derives from the length of an open pipe required to produce a given pitch—an 8' pipe produces middle C at approximately 261.6 Hz. The system obeys the inverse relationship between pipe length and frequency:

```
f = v / (2L)
```

where `f` is frequency, `v` is the speed of sound in air (~343 m/s at 20°C), and `L` is the effective pipe length including end correction factors.

Each stop generates a characteristic harmonic spectrum determined by pipe construction. **Principal stops** (open metal flue pipes) produce a bright, harmonic-rich spectrum approximating a triangular wave with strong odd harmonics. **Flute stops** (often stopped or capped pipes) emphasize the fundamental and suppress higher harmonics, approaching a square wave filtered to primarily odd harmonics. **String stops** (narrow-scaled metal pipes) generate complex, slowly-developing harmonic content with prominent upper partials that create beating and interference patterns. **Reed stops** (brass resonators driven by vibrating brass tongues) produce sawtooth-like waveforms rich in both odd and even harmonics, with spectral energy distributed across a wide frequency range.

The acoustic principle governing register combination is **additive synthesis through spectral superposition**. When multiple stops are drawn, their acoustic outputs sum in the air column before the pipe foot and in the ambient space, creating a composite spectrum:

```
S_total(f) = Σ [A_i(f) · H_i(f)]
```

where `S_total(f)` is the composite frequency spectrum, `A_i(f)` is the amplitude response of stop `i`, and `H_i(f)` is the harmonic transfer function of that stop's pipe construction.

Critical to understanding register combination is **Rameau's harmonic synthesis principle**, formalized in the 18th century: combining stops at harmonic intervals (8' + 4' + 2⅔' + 2' + 1⅗' + 1⅓') reconstructs the natural harmonic series of a single complex tone, creating a **cornet** or **mixture** effect where the ear perceives not separate pitches but a single, brilliantly colored timbre. This exploits the psychoacoustic phenomenon of **virtual pitch perception**, where the brain reconstructs a fundamental frequency from its overtone series even when the fundamental is weak or absent.

The tonal coherence invariant demands that any stop combination must either:
1. Reinforce the harmonic series (unison and octave stops: 16' + 8' + 4' + 2')
2. Complete the harmonic series (adding mutations: 8' + 4' + 2⅔' forms pitches 1, 2, 3 of the series)
3. Provide contrasting but non-interfering timbres (8' Principal + 8' Flute blends foundational colors)

Violating this principle—combining, for instance, a 16' stop with a 2⅔' mutation without intermediate octaves—creates **registrational holes** where missing harmonics render the combination thin or unstable, analogous to aliasing artifacts in undersampled digital signals.

The organ's wind system introduces a constraint absent in electronic synthesis: **shared air supply impedance**. All pipes draw from a common wind chest maintained at constant pressure (typically 75-150mm water column, or ~735-1470 Pa). Activating many stops simultaneously increases total airflow demand, potentially causing pressure drop unless the wind system is sized appropriately. This creates a dependency graph where stop combinations must respect aggregate flow capacity, enforcing a form of resource contention management.

## 2. Core Architecture & Mechanics

The organ's registration system implements a hierarchical switching matrix coupling player input (keys, pedals) to acoustic output (pipes) through mechanical, electro-pneumatic, or direct-electric action. Understanding this requires examining three architectural layers: the stop mechanism, the windchest routing system, and the pipe array.

### Stop Control Layer

Each stop is a binary control that gates an entire rank of pipes. In **mechanical slider-chest** organs (the dominant design from medieval times through the 19th century), each stop physically moves a wooden slider—a perforated board positioned between the pallet box and the pipe feet. When drawn, the slider's holes align with pipe feet, allowing wind to reach them when a key opens the corresponding pallet. The data structure is elegant: a two-dimensional matrix where rows are keys (61 for manual, 32 for pedal) and columns are stops (typically 8-80 per manual).

```
Pipe[key][stop] = Pallet[key] AND Slider[stop]
```

This implements a logical AND gate in physical hardware—a pipe sounds only when both its key's pallet is open (controlled by the player) and its stop's slider is pulled (the registration selection).

Modern **electro-pneumatic** organs replace mechanical sliders with electrically-controlled pneumatic valves, introducing a three-stage architecture:

```mermaid
graph LR
    A["Key Contact"] -->|"12V DC"| B["Stop Magnet"]
    B -->|"Opens Pilot Valve"| C["Pneumatic Primary"]
    C -->|"High Pressure Air"| D["Pipe Valve"]
    D -->|"Wind Chest Pressure"| E["Pipe Resonates"]
    
    F["Stop Tablet"] -->|"Enable Signal"| B
```

This architecture decouples control logic from acoustic elements, allowing consoles to be located remotely from the organ chamber and enabling **combination actions**—programmable memory systems storing and recalling stop configurations.

### Windchest Topology

The windchest is the critical interface between wind supply and pipes. **Slider chests** provide one pallet per key, feeding all stops for that key through a common plenum. **Unit chests** (common in theater organs) assign individual valves to each pipe, enabling **unification**—deriving multiple stops from a single rank by tapping it at different pitches. A single rank of 61 pipes might appear as both an 8' stop and a 4' stop, with the 4' stop playing pipes 12 semitones higher in the rank.

The **pitman chest** uses individual pneumatic or electromagnetic actuators for each pipe, organizing them in a grid:

```
Chest[manual][key][stop] = Electromagnet[stop * 61 + key]
```

This provides maximum flexibility but introduces electrical complexity proportional to the product of keys and stops.

### Harmonic Registration Algebra

The acoustically meaningful parameter for each stop is its **pitch rank**, expressed in feet. The standard ranks form a geometric series:

```
Rank_freq = Base_freq · 2^(n/12)
```

where `n` is the semitone offset from 8' pitch. Common ranks:

| Rank | Ratio to 8' | Harmonic | Interval |
|------|-------------|----------|----------|
| 16'  | 1:2         | -12      | Octave below |
| 8'   | 1:1         | 0        | Unison |
| 4'   | 2:1         | +12      | Octave above |
| 2⅔'  | 3:1         | +19      | Twelfth (octave + fifth) |
| 2'   | 4:1         | +24      | Two octaves |
| 1⅗'  | 5:1         | +28      | Two octaves + major third |
| 1⅓'  | 6:1         | +31      | Two octaves + fifth |

A **mixture stop** combines multiple high-pitched ranks (typically 2', 1⅓', 1', ⅔') in a single draw control, breaking into multiple pipes per key. A four-rank mixture at 2' might have composition:

```
Key range  | Rank 1 | Rank 2 | Rank 3 | Rank 4
-----------|--------|--------|--------|--------
C1-B1      | 2'     | 1⅓'    | 1'     | ⅔'
C2-B2      | 2⅔'    | 2'     | 1⅓'    | 1'
C3-B3      | 4'     | 2⅔'    | 2'     | 1⅓'
C4-C5      | 5⅓'    | 4'     | 2⅔'    | 2'
```

This **breaking pattern** prevents excessive brightness in the treble by shifting the mixture composition downward in higher octaves, maintaining spectral balance across the keyboard.

### Registration State Machine

A complete registration at any instant can be represented as a bit vector:

```python
class Registration:
    def __init__(self, num_stops: int):
        self.stops = [False] * num_stops  # Binary state array
        self.metadata = []  # [(stop_idx, pitch_rank, timbre_family)]
    
    def draw_stop(self, idx: int):
        """Activate a stop - equivalent to pulling stop knob"""
        self.stops[idx] = True
    
    def compute_effective_pitch_ranks(self) -> dict[float, list[int]]:
        """Group active stops by pitch rank for harmonic analysis"""
        pitch_map = {}
        for idx, active in enumerate(self.stops):
            if active:
                rank = self.metadata[idx][1]
                if rank not in pitch_map:
                    pitch_map[rank] = []
                pitch_map[rank].append(idx)
        return pitch_map
    
    def validate_harmonic_coherence(self) -> tuple[bool, str]:
        """Check for registration holes or unbalanced combinations"""
        ranks = sorted(self.compute_effective_pitch_ranks().keys())
        
        # Check for mutation stops without octave support
        mutations = [r for r in ranks if r not in [16, 8, 4, 2, 1]]
        unisons = [r for r in ranks if r in [16, 8, 4, 2, 1]]
        
        if mutations and not unisons:
            return False, "Mutation stops require octave support"
        
        # Check for extreme pitch gaps
        for i in range(len(ranks) - 1):
            if ranks[i+1] / ranks[i] > 4:  # More than two octaves gap
                return False, f"Large harmonic gap between {ranks[i]}' and {ranks[i+1]}'"
        
        return True, "Registration harmonically coherent"
```

This state machine captures the essential logic organists internalize: registrations build from foundational octave-related stops (the **plenum**) and may add mutations and reeds for color, but must maintain spectral continuity.

## 3. Acoustic Coupling & Interference Phenomena

The organ's physical implementation introduces acoustic effects absent in digital synthesis. Pipes do not operate as isolated oscillators but as coupled resonators sharing a common acoustic space, wind supply, and often physical structure. These interactions create emergent phenomena that define the instrument's sonic character.

### Wind System Dynamics

The wind system maintains pressure through a feedback loop: bellows or blowers supply air to a reservoir (weighted bellows or spring-loaded bellows), which buffers transient demand. The governing equation for reservoir pressure under load is:

```
dP/dt = (Q_supply - Q_demand) / C_reservoir
```

where `P` is pressure, `Q_supply` is blower flow rate, `Q_demand` is aggregate pipe consumption, and `C_reservoir` is the pneumatic capacitance of the reservoir (volume/elasticity).

When many stops are drawn simultaneously, `Q_demand` spikes, potentially exceeding `Q_supply`. If reservoir capacitance is insufficient, pressure drops, causing:
- **Pitch sag**: All pipes drop in frequency proportional to √(P_actual/P_nominal)
- **Attack slowdown**: Pipes take longer to speak as reduced pressure slows transient buildup
- **Timbre shift**: Harmonic spectra change as pipe resonance conditions vary with pressure

Professional organ design sizes wind systems for worst-case demand plus 20-30% margin. The aggregate flow requirement is:

```
Q_total = Σ [n_pipes_i · A_i · v_i]
```

where `n_pipes_i` is the number of pipes in rank `i`, `A_i` is the cross-sectional area of those pipes, and `v_i` is the wind velocity (typically 5-15 m/s depending on voicing). A large organ (80 stops, ~5000 pipes) might require 300-500 cubic feet per minute at 100mm water column pressure.

### Acoustic Beating and Tuning Systems

Organs are typically tuned to equal temperament (12-TET), dividing the octave into 12 equal logarithmic steps. Each semitone represents a frequency ratio of 2^(1/12) ≈ 1.05946. However, pipes in different stops may exhibit slight tuning discrepancies due to temperature variation, mechanical drift, or intentional **celeste** voicing (where two stops at nominal 8' pitch are tuned slightly apart to create beating).

When two frequencies f₁ and f₂ are sounded simultaneously, they create a beat frequency:

```
f_beat = |f₁ - f₂|
```

A celeste stop tuned 2-4 Hz sharp relative to a principal creates a shimmering, undulating effect exploited in Romantic organ music. Conversely, unintentional tuning drift creates unpleasant, slow beating that sounds as instability.

### Acoustic Masking and Critical Bands

The ear's frequency resolution follows a **critical bandwidth** curve approximated by:

```
CB(f) = 25 + 75[1 + 1.4(f/1000)²]^0.69  Hz
```

Sounds within a critical band mask each other, with the louder sound dominating perception. In organ registration, this manifests as:

1. **Low-frequency masking**: A loud 16' Bourdon (stopped bass pipes) can mask subtle 8' flutes, reducing perceived clarity
2. **Reed dominance**: Reeds (Trumpet 8', Oboe 8') have high spectral density and mask flue stops at the same pitch
3. **Mixture integration**: Properly balanced mixtures are perceived as timbral enrichment of 8' tone rather than separate high pitches because their component ranks fall within the critical bands of the 8' fundamental's upper partials

The **Fletcher-Munson equal-loudness contours** further complicate balance: human hearing is less sensitive to low and very high frequencies at moderate volumes. Organs compensate through **scaling**—bass pipes are proportionally wider (larger diameter:length ratio) to increase power, and high-pitched pipes are voiced more gently.

### Resonance and Acoustic Feedback

Large organ chambers exhibit room modes—standing wave patterns at frequencies where:

```
f_mode = (c/2) · √[(m/L_x)² + (n/L_y)² + (p/L_z)²]
```

for integers m, n, p and room dimensions L_x, L_y, L_z. Certain frequencies are reinforced, others attenuated. Experienced organists account for this when selecting registrations, avoiding stop combinations that excite problematic room modes or that are excessively absorbed at key musical frequencies.

## 4. Registrational Taxonomy & Historical Practice

Organ registration evolved over five centuries, each era developing distinct aesthetic principles that reflect both musical style and mechanical capabilities.

### Baroque Principal Chorus (Werkprinzip)

North German and Dutch organs (Schnitger, van Hagerbeer) organized stops into **Werks**—independent divisions with complete principal choruses. A typical Hauptwerk (main manual) would include:

- **8' Principal** (foundation)
- **8' Octave** 
- **4' Octave** (first overtone reinforcement)
- **Quinte 2⅔'** (adds third harmonic)
- **2' Octave** (fourth harmonic)
- **Mixture IV-VI ranks** (8th, 10th, 12th, 15th harmonics)

The resulting **plenum** creates a blazing, unison-reinforced sound ideal for contrapuntal textures where each voice must remain distinct yet fuse into a cohesive ensemble. This registration exploits spectral clarity: each harmonic rank occupies a different critical band, and the mixture's breaking ensures no frequency region becomes overloaded.

Bach's organ works assume this registration architecture. The Prelude and Fugue in E-flat Major BWV 552 ("St. Anne") demands the full plenum for the prelude's majestic ascending scales, exploiting the mixture's brilliant attack transients and the 16' Principal's foundational weight.

### French Classical Terraced Dynamics (Registration as Orchestration)

French organs (Clicquot, Thierry) featured fewer mixture stops but rich solo reed batteries: Trompette, Cromorne, Cornet. Registration followed the **Grand Jeu** (full organ with reeds) and **Plein Jeu** (principals and mixtures without reeds) paradigm, with **récit** stops (enclosed in a swell box with shutters) enabling dynamic gradation.

Couperin and de Grigny composed **pièces** specifying exact registrations:

- **Plein Jeu**: 8' Montre, 4' Prestant, Mixture, Cymbale
- **Grand Jeu**: All principals + Trompette, Clairon, Cornet
- **Cromorne en taille**: Solo 8' Cromorne (reed) in tenor register against 8' Bourdon accompaniment
- **Récit de Nazard**: Solo 2⅔' Nasard (flute mutation) on récit manual

This treats the organ as an orchestra, assigning timbres to structural roles rather than building composite textures.

### Romantic Symphonic Registration

19th-century organs (Cavaillé-Coll, Willis) introduced:

- **High wind pressure** (up to 250mm vs. 75mm Baroque) enabling powerful reeds and loud flue stops
- **Enclosed divisions** (Swell, Choir, Solo) with expression pedals for continuous dynamic control
- **Orchestral imitation stops**: Vox Humana, Orchestral Oboe, French Horn, Cello

Registration became **additive crescendo** building from solo flutes through strings and principals to reeds and mixtures, mimicking orchestral scoring. Franck and Widor composed for this palette, specifying gradual addition of stops across phrases to create dynamic arcs impossible on Baroque organs.

The **crescendo pedal**, introduced in the late 19th century, mechanically adds stops in a pre-programmed sequence, automating the build from pianissimo to fortissimo.

### Neo-Baroque and Modern Eclecticism

20th-century organ reform (Orgelbewegung) returned to mechanical action and lower wind pressures while retaining some symphonic resources. Modern instruments blend capabilities:

- Baroque-style principal choruses for clarity in counterpoint
- Romantic-style swell divisions for expressive accompaniment
- Contemporary solo stops (Rankett, Sordun) for timbral variety

Registration practices today emphasize historically-informed choices while exploiting the full tonal palette. A performance of Messiaen's "Dieu parmi nous" might use:

- **Foundation**: 8' + 4' Principals for rhythmic drive
- **Harmonic reinforcement**: Mixtures adding brilliance without harshness
- - **Color**: Isolated reed or mutation stops for thematic statements
- **Dynamic shaping**: Expression
