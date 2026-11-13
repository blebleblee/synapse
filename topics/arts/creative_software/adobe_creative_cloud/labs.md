# Operational Verification Labs: Adobe Creative Cloud Audio/Video Pipeline

## Objective & Creative Cloud Studio Pipeline Setup

This laboratory provides hands-on operational mastery over the professional audiovisual production pipeline spanning Adobe Premiere Pro, Adobe Audition, and Adobe After Effects. You will calibrate Mercury Playback GPU acceleration, execute surgical spectral audio restoration, establish lossless Dynamic Link round-tripping, ensure broadcast color compliance using Lumetri Scopes, and optimize multi-frame motion graphic rendering.

```
Creative Cloud Cross-Application Dynamic Link Pipeline:
[Premiere Pro NLE Assembly] ──(Dynamic Link)──▶ [Audition 32-Bit Float Multitrack Session]
             │                                                          │
             │                                            [Spectral Audio Restoration]
             │                                                          │
             │◀────────────── (Lossless Audio Mixdown) ─────────────────┘
             │
             ├──(Dynamic Link)──▶ [After Effects Motion Graphics (MFR)]
             │                                     │
             │◀────────────── (RGB+Alpha) ─────────┘
             ▼
[Adobe Media Encoder: ProRes 422 HQ Master / EBU R128 Compliant Delivery]
```

### Studio Hardware & Engine Setup

Configure application preferences before launching the workflow:
1. **GPU Renderer**: In Premiere Pro and After Effects, set Project Settings -> General -> **Renderer** to `Mercury Playback Engine GPU Acceleration (Metal / CUDA)`.
2. **Audio Hardware**: In Audition, set I/O buffer size to `256 samples` at $48,000\text{ Hz}$ (24-bit integer / 32-bit float broadcast standard).
3. **Media Cache & Scratch Disks**: Allocate fast NVMe storage for dedicated scratch and peak file caching.

---

## Exercise 1: Adobe Audition Spectral Frequency Display & Surgical Audio Repair

In this exercise, you will analyze frequency distribution using Audition's Spectral Frequency Display and surgically excise broadband noise and isolated acoustic artifacts without compromising dialogue formants.

### Step 1: Spectral Frequency Display Configuration

1. Open Adobe Audition and load a field dialogue recording contaminated with air conditioning HVAC hum and a transient cell-phone ring.
2. Press `Shift+D` to toggle the **Spectral Frequency Display** (showing Time on the x-axis, Frequency $0-24\text{ kHz}$ on the y-axis, and Amplitude represented by luminous heat color).
3. Go to `Settings -> Spectral Displays`:
   - Set **FFT Size**: `2048` or `4096` samples (provides sharp frequency resolution down to low-frequency fundamentals).
   - Set **Windowing Function**: `Blackman-Harris` (minimizes spectral leakage across adjacent frequency bins).

### Step 2: Noise Print Capture & Spectral Subtraction

1. Select a $300\text{ ms}$ segment of pure ambient background tone containing no speech.
2. Press `Shift+P` (**Capture Noise Print**).
3. Press `Cmd+A` to select the entire audio file, then press `Cmd+Shift+P` (**Noise Reduction Process**):
   - Set **Noise Reduction**: $65\%$ (avoids phasey "underwater" chirping artifacts).
   - Set **Reduce by**: $12\text{ dB}$.
   - Set **Spectral Decay Rate**: $65\%$.
   - Click **Apply**. Verify that the broadband HVAC floor drops from $-42\text{ dBFS}$ to below $-62\text{ dBFS}$ while speech consonants retain clarity.

### Step 3: Surgical Transient Healing

1. In the Spectral Display, locate the high-amplitude bright horizontal line corresponding to the $1.2\text{ kHz}$ telephone ring during speech.
2. Select the **Spot Healing Brush Tool** (`B`), set radius to $18\text{ px}$.
3. Paint directly across the offending harmonic lines. Observe that Audition interpolates ambient frequency tiles from immediately adjacent time frames, completely removing the ring with zero audible speech dropouts.

---

## Exercise 2: Premiere Pro to Audition Dynamic Link Audio Round-Tripping

In this exercise, you will round-trip an active multi-mic documentary timeline from Premiere Pro into Audition for multitrack mixing and return a pristine stem mixdown.

### Step 1: Exporting Sequence to Audition

1. In Premiere Pro, open a narrative sequence with dialogue tracks (A1-A2), sound effects (A3-A4), and stereo music bed (A5-A6).
2. Go to `Edit -> Edit in Adobe Audition -> Sequence`.
3. In the dialog box:
   - Name: `DOCU_MASTER_MIX`.
   - Selection: `Entire Sequence`.
   - Audio Handles: `1.00 seconds`.
   - Check: `Export Video via Dynamic Link` (allows real-time reference video playback inside Audition without rendering intermediate proxies).
   - Click **OK**. Audition launches and builds a phase-coherent 32-bit floating-point Multitrack Session.

### Step 2: Multitrack Bus Routing & Dialogue Leveling

1. In Audition's Multitrack View, create three dedicated Bus Tracks: `BUS_DX` (Dialogue), `BUS_FX` (Sound Effects), and `BUS_MX` (Music).
2. Route track outputs accordingly to their parent stem buses.
3. On `BUS_DX`, insert the **Vocal Leveler**:
   - Set Target RMS to $-18\text{ dBFS}$.
4. On `BUS_MX`, insert an EQ and duck $2.5\text{ dB}$ around $1.5\text{ kHz} - 3.5\text{ kHz}$ (speech intelligibility pocket) whenever dialogue is present.
5. Go to `Multitrack -> Export to Premiere Pro`. Select **Mixdown Session To** `Stereo Master`. Premiere Pro automatically imports the returned mixdown and places it onto a new linked audio track.

---

## Exercise 3: Color Pipeline & Broadcast-Safe Scopes in Lumetri Color

In this exercise, you will calibrate video luminance and chrominance levels in Premiere Pro to guarantee compliance with ITU-R BT.709 broadcast transmission specifications.

### Step 1: Lumetri Scopes Calibration

1. In Premiere Pro, open the **Color** workspace. Open the **Lumetri Scopes** panel (`Window -> Lumetri Scopes`).
2. Right-click inside the panel and enable:
   - **Waveform (YC / No Chroma)**: Evaluates luminance ($Y$) from $0\text{ IRE}$ (pure black) to $100\text{ IRE}$ (specular white).
   - **Vectorscope (HLS / YUV)**: Displays color saturation and hue angle relative to the $75\%$ broadcast color bars and the crucial **Skin Tone Line** (running at approximately $10:30$ o'clock).
   - **Parade (RGB)**: Displays red, green, and blue color channels side-by-side to detect color temperature cast.

### Step 2: Primary Grade & Broadcast Safe Clamping

1. Select a raw camera clip. In **Lumetri Color -> Basic Correction**:
   - Adjust **Temperature** and **Tint** until the RGB Parade peaks align evenly across a neutral white card.
   - Adjust **Blacks** until shadow floor sits at exactly $0-5\text{ IRE}$ (never dipping below $0\text{ IRE}$ into illegal sub-blacks).
   - Adjust **Whites** until highlights peak cleanly between $90-98\text{ IRE}$.
2. In **Effects**, search for and apply the **Broadcast Safe** video effect to the top Adjustment Layer:
   - **Standard**: `IRE (0 - 100)`.
   - **Maximum IRE**: `100.0`.
   - **Minimum IRE**: `0.0`.
3. Verify on the Waveform scope that high-luminance specular glints are cleanly clamped at $100\text{ IRE}$ without gamut-exceeding line smear.

---

## Exercise 4: After Effects Multi-Frame Rendering (MFR) & Alpha Master Export

In this exercise, you will optimize After Effects rendering performance using multi-frame threading and export a clean lower-third motion graphic with an uncompressed Alpha transparency channel.

### Step 1: Multi-Frame Rendering (MFR) Optimization

1. In After Effects, navigate to `Settings -> Memory & Performance`.
2. Verify **Enable Multi-Frame Rendering** is checked. Set CPU allocation to reserve $10\%$ for background operating system threads.
3. Open a complex motion graphic composition with nested 3D text layers, particle emitters, and camera depth-of-field blur.
4. Enable **Motion Blur** on the composition and all active layers. In Composition Settings -> Advanced, set **Shutter Angle** to $180.0^\circ$ (standard cinematic exposure blur).
5. Press `Space` to initiate RAM preview and observe multi-core utilization indicators across the green timeline cache bar.

### Step 2: Alpha Channel Master Export Pipeline

```
Alpha Channel Master Configuration:
[Composited Motion Graphic] ──▶ [After Effects Render Queue]
                                           │
                             [Format: Apple ProRes 4444]
                             [Channels: RGB + Alpha]
                             [Color Depth: Millions of Colors+]
                             [Color Premultiplication: Straight (Unmatted)]
                                           ▼
                             [Broadcast Master .mov with Transparency]
```

1. Select the composition and press `Cmd+M` to add it to the **Render Queue**.
2. Click **Output Module**:
   - **Format**: `QuickTime`.
   - **Video Codec**: `Apple ProRes 4444` (or `Avid DNxHR HQX with Alpha`).
   - **Channels**: `RGB + Alpha` (crucial: must contain the fourth transparency channel).
   - **Depth**: `Millions of Colors+` (the `+` denotes alpha channel encoding).
   - **Color**: `Straight (Unmatted)` to prevent dark halo fringing around semi-transparent edges.
3. Render the file and import it back into Premiere Pro. Overlay it onto a live video track and verify that transparent regions reveal the background video with clean edge blending.

---

## Post-Production Master Delivery Verification Checklist

Prior to broadcast or commercial digital distribution, verify these quality standards:

```
[ ] Video Gamut Compliance: Lumetri Scopes show zero luminance below 0 IRE or above 100 IRE.
[ ] Color Space Invariants: Output encoded strictly in Rec.709 with 1-1-1 NCLC color tags (or Rec.2020 for HDR).
[ ] Audio Integrated Loudness:
    - EBU R128 Television: -23.0 LUFS (±0.5 LUFS), Max True Peak -1.0 dBTP.
    - Web / Streaming (YouTube, Netflix): -14.0 LUFS to -16.0 LUFS, Max True Peak -1.0 dBTP.
[ ] Dialogue Gating & Intelligibility: Dialogue rests between -18 LUFS and -24 LUFS short-term.
[ ] Codec & Container: Master exported as Apple ProRes 422 HQ (or ProRes 4444 for graphics), 10-bit 4:2:2 chroma subsampling, 48 kHz / 24-bit uncompressed LPCM audio.
```
