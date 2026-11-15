# Lesson 4: Peripheral Emulation Architecture

## 1. First-Principles Intuition & Invariants

Every game console that ever shipped was, at its architectural core, a precisely engineered coalition of semi-autonomous hardware blocks communicating over shared buses. The CPU was rarely the most interesting component. The real complexity—and the reason emulation remains a genuinely hard problem decades after the hardware became obsolete—lived in the peripherals: the graphics chip rendering scanlines through hardware sprites and tile maps, the audio synthesizer modulating waveforms through operator tables, the controller polling circuitry sampling button matrices at deterministic intervals, and the cartridge memory mapper bank-switching between ROM pages in response to address-space probes. To emulate a game correctly, you must reproduce not just the computational output of each of these subsystems but the precise *timing relationships* between them, because the original software was written to exploit—and in many cases depend upon—those relationships with cycle-level precision.

The foundational invariant of peripheral emulation is **temporal fidelity under a unified clock domain**. Real hardware runs all subsystems from a single crystal oscillator. The NTSC NES master clock runs at 21.477272 MHz. The CPU derives its clock by dividing that master by 12, yielding roughly 1.789 MHz. The PPU (Picture Processing Unit) runs at master divided by 4, giving approximately 5.37 MHz. These ratios are fixed in silicon, and the consequence is that for every CPU cycle, the PPU advances exactly three cycles. Games written for this hardware do not abstract away these ratios—they exploit them. A programmer who wants to change a palette color mid-scanline writes the register at a specific cycle offset from the HSYNC signal, knowing that the PPU will sample that register between dot 257 and dot 320 of the visible line. If your emulator ticks the CPU and PPU independently and then synchronizes them loosely every frame, that write arrives at the wrong cycle, the wrong color appears on the wrong scanline, and the visual effect breaks. This is not a hypothetical—it describes the failure mode of every first-generation NES emulator written before the cycle-accurate era.

The implication is profound: peripheral emulation is fundamentally a problem of **cycle-accurate state machine co-simulation**. Each hardware block is a finite state machine with explicit inputs (register writes from the CPU, DMA requests, interrupt acknowledgments, and synchronization signals from other chips) and outputs (pixel colors on the dot clock, sample values on the audio sample rate, IRQ assertions to the CPU interrupt line). The emulator's job is to advance all of these state machines in lockstep, correctly routing every signal between them, while doing so fast enough to render sixty frames per second on modern hardware that runs at several gigahertz. The paradox at the heart of high-performance emulation is that the original hardware was slow by modern standards, but emulating it accurately requires an enormous amount of modern compute—not because the computations are expensive, but because the number of state transitions is enormous and their serialization constraints are strict.

Before dissecting each subsystem, it is worth establishing a second invariant: **hardware registers are side-effecting state transitions, not simple memory writes**. When the SNES CPU writes to address `$2101` (OBJ size and character address), it does not simply store a byte. It triggers an internal pipeline in the PPU that may latch the value, may ignore it depending on the current rendering phase, and may cause a DMA-visible state change that feeds back into the CPU bus. The same register at the same address, written with the same value at two different points in a frame, may produce completely different observable behavior. This rules out any emulation strategy that models registers as a flat array of bytes with a simple read/write interface. Every register write is a method call on a stateful object whose behavior is conditional on the global timeline of the frame. This insight shapes every design decision in a serious emulator, from data structure layout to the threading model to the save state serialization format.

A third invariant governs audio: **sample generation is a continuous process, not a frame-synchronous batch**. Modern audio APIs consume samples at a fixed rate—48000 Hz, typically—with a buffer that the host OS will drain and refill on a hardware interrupt. The original audio hardware generated samples continuously at its own native rate, which was derived from the same master clock as the CPU and PPU. The SNES SPC700 runs at 1.024 MHz, and the DSP that reads from its memory generates stereo 16-bit samples at 32000 Hz. An emulator that generates all audio samples for a frame in a batch at the end of that frame and then hands them to the OS audio API will produce audio that is functionally correct but temporally wrong: register writes that occurred 2 milliseconds into the frame are not reflected until the entire 16-millisecond batch is submitted. For most music this is imperceptible, but for sound effects triggered by game events that the player can see, the desynchronization between the visual frame and the audio batch produces a perceptible lag. The correct architecture generates audio samples *inline* as the emulation timeline advances, mirroring the hardware's continuous behavior.

---

## 2. Core Architecture & Mechanics

### The Graphics Pipeline: Scanline-Driven Rasterization

The graphics subsystems of classic consoles were purpose-built rasterizers designed to generate composite video signals in real time. Understanding their emulation requires understanding what they were actually doing: producing a pixel color on every dot clock, writing that color to a DAC, and driving the DAC output directly onto the analog video line. There was no framebuffer in the modern sense. There was no "render the scene, then display it." There was only "what color is dot N of scanline M," computed just-in-time by hardware finite state machines.

The NES PPU provides the clearest illustration. The visible picture is 256 dots wide by 240 scanlines tall. Beyond the visible area, the PPU generates horizontal blanking (HBLANK) and vertical blanking (VBLANK) periods that together define the full 341-dot-by-262-line frame (for NTSC). During VBLANK, the CPU is free to update PPU memory—OAM (Object Attribute Memory), nametable data, palette entries—without corrupting the visible picture. During active rendering, those same bus cycles are consumed by the PPU itself to fetch tile data and sprite attributes for the current and upcoming scanlines. The PPU's internal timing is a 341-cycle state machine per scanline. Cycles 1–256 render pixels, cycles 257–320 evaluate sprites for the *next* scanline (the sprite evaluation pipeline is pipelined one scanline ahead), and cycles 321–340 prefetch the first two tile columns of the next scanline.

The emulation data structure must reflect this pipeline structure. A naïve implementation represents the PPU as a function called once per scanline, which reads nametable memory, renders all 256 pixels, and returns. This is sufficient for many games but fails for any game that modifies PPU registers mid-scanline to produce split-screen effects, palette cycling, or raster scrolling. The cycle-accurate PPU must instead model a dot-by-dot state machine. The key internal registers are the current VRAM address (a 15-bit register, labeled `v` in the community documentation), the temporary VRAM address (`t`), the fine X scroll register, and the write toggle for the dual-write registers `$2005`/$`2006`. These are not programmer-visible registers in the traditional sense; they are internal pipeline latches that the PPU microcode updates on specific dot boundaries and that CPU writes to `$2005` and `$2006` can partially overwrite under specific conditions.

```c
typedef struct {
    uint16_t v;           /* current VRAM address (15-bit) */
    uint16_t t;           /* temporary VRAM address (15-bit) */
    uint8_t  fine_x;      /* fine X scroll (3-bit) */
    uint8_t  write_latch; /* shared write toggle for $2005/$2006 */
    uint8_t  ppuctrl;     /* $2000: NMI enable, sprite size, etc.  */
    uint8_t  ppumask;     /* $2001: render enable, color emphasis  */
    uint8_t  ppustatus;   /* $2002: VBL flag, sprite overflow, S0  */

    /* Internal pixel pipeline shift registers and latches */
    uint16_t bg_shift_lo; /* background pattern data, low plane    */
    uint16_t bg_shift_hi; /* background pattern data, high plane   */
    uint8_t  at_shift_lo; /* attribute (palette select) shift regs */
    uint8_t  at_shift_hi;
    uint8_t  at_latch_lo; /* latches fed into the shift regs       */
    uint8_t  at_latch_hi;
    uint8_t  nt_byte;     /* nametable byte fetched this dot       */
    uint8_t  pt_lo;       /* pattern table low byte fetch latch    */
    uint8_t  pt_hi;       /* pattern table high byte fetch latch   */

    /* Sprite evaluation state */
    uint8_t  oam_primary[256];    /* primary OAM: 64 sprites x 4 bytes  */
    uint8_t  oam_secondary[32];   /* secondary OAM: 8 sprites x 4 bytes */
    uint8_t  sp_shift_lo[8];      /* per-slot sprite pattern low planes  */
    uint8_t  sp_shift_hi[8];      /* per-slot sprite pattern high planes */
    uint8_t  sp_attribute[8];     /* per-slot sprite attribute bytes     */
    int16_t  sp_x_counter[8];     /* per-slot X position down-counters   */
    uint8_t  sprite_count;        /* sprites found for current scanline  */
    uint8_t  sp0_on_next;         /* sprite-zero present in secondary OAM*/

    uint16_t dot;         /* current dot position (0–340)         */
    int16_t  scanline;    /* current scanline (-1 to 260)         */
    uint64_t frame;       /* total frame counter                  */

    uint8_t  palette_ram[32];     /* internal palette memory             */
    uint8_t  ciram[2048];         /* 2KB internal VRAM (nametables)      */

    uint32_t framebuffer[256 * 240]; /* RGBA output for display           */
} NES_PPU;
```

The tick function advances this state machine by one dot. The rendering logic for a single visible dot extracts the appropriate bit from the background shift registers using `fine_x` as a bit selector, checks all eight active sprite slots to find the front-most non-transparent sprite pixel (respecting sprite priority), applies the priority multiplexer logic to determine whether the background or sprite pixel wins, and writes the result through the palette RAM to the framebuffer. Crucially, the same tick function also performs the VRAM fetches—nametable byte, attribute byte, pattern table low, pattern table high—on the specific dot boundaries where the hardware performs them, loading the latches and shift registers in the correct pipeline order. This fidelity is what allows mid-scanline register writes to take effect at the correct pixel.

```c
static inline void ppu_tick(NES_PPU *ppu, NES_Mapper *mapper)
{
    int16_t sl  = ppu->scanline;
    uint16_t dot = ppu->dot;
    bool rendering = (ppu->ppumask & 0x18) != 0; /* BG or sprite enable */

    /* ------------------------------------------------------------------ */
    /* Visible scanlines (0–239) and pre-render scanline (261 / -1)        */
    /* ------------------------------------------------------------------ */
    if ((sl >= 0 && sl <= 239) || sl == 261) {

        /* Background pipeline: shift registers clock every visible dot */
        if (rendering && ((dot >= 2 && dot <= 257) || (dot >= 322 && dot <= 337))) {
            ppu->bg_shift_lo <<= 1;
            ppu->bg_shift_hi <<= 1;
            ppu->at_shift_lo  = (uint8_t)((ppu->at_shift_lo << 1) | ppu->at_latch_lo);
            ppu->at_shift_hi  = (uint8_t)((ppu->at_shift_hi << 1) | ppu->at_latch_hi);
        }

        /* VRAM fetch cycle groups (each group is 8 dots: NT, AT, PT_lo, PT_hi) */
        if (rendering && (dot >= 1 && dot <= 256) || (dot >= 321 && dot <= 336)) {
            switch ((dot - 1) & 7) {
                case 1: /* Nametable byte */
                    ppu_reload_shifters(ppu);
                    ppu->nt_byte = ppu_read(mapper, 0x2000 | (ppu->v & 0x0FFF));
                    break;
                case 3: /* Attribute byte */
                    {
                        uint16_t at_addr = 0x23C0
                            | (ppu->v & 0x0C00)
                            | ((ppu->v >> 4) & 0x38)
                            | ((ppu->v >> 2) & 0x07);
                        uint8_t  at_byte = ppu_read(mapper, at_addr);
                        uint8_t  shift   = ((ppu->v >> 4) & 4) | (ppu->v & 2);
                        ppu->at_latch_lo = (at_byte >> shift) & 1;
                        ppu->at_latch_hi = (at_byte >> shift) >> 1 & 1;
                    }
                    break;
                case 5: /* Pattern table low plane */
                    {
                        uint16_t pt_base = (ppu->ppuctrl & 0x10) ? 0x1000 : 0x0000;
                        uint8_t  fine_y  = (ppu->v >> 12) & 7;
                        ppu->pt_lo = ppu_read(mapper, pt_base + (uint16_t)ppu->nt_byte * 16 + fine_y);
                    }
                    break;
                case 7: /* Pattern table high plane */
                    {
                        uint16_t pt_base = (ppu->ppuctrl & 0x10) ? 0x1000 : 0x0000;
                        uint8_t  fine_y  = (ppu->v >> 12) & 7;
                        ppu->pt_hi = ppu_read(mapper, pt_base + (uint16_t)ppu->nt_byte * 16 + fine_y + 8);
                        ppu_increment_coarse_x(ppu); /* coarse X increment */
                    }
                    break;
            }
        }

        /* Y increment at dot 256 */
        if (rendering && dot == 256) ppu_increment_y(ppu);
        /* Copy t horizontal bits to v at dot 257 */
        if (rendering && dot == 257) ppu_copy_horizontal(ppu);
        /* Copy t vertical bits to v during pre-render scanline dots 280–304 */
        if (rendering && sl == 261 && dot >= 280 && dot <= 304) ppu_copy_vertical(ppu);

        /* Output pixel for visible scanlines */
        if (sl >= 0 && sl <= 239 && dot >= 1 && dot <= 256) {
            ppu_output_pixel(ppu, dot - 1, sl);
        }
    }

    /* ------------------------------------------------------------------ */
    /* VBLANK: set flag at scanline 241, dot 1                             */
    /* ------------------------------------------------------------------ */
    if (sl == 241 && dot == 1) {
        ppu->ppustatus |= 0x80; /* VBL flag set */
        /* NMI is asserted to CPU here if NMI_enable bit is set */
    }
    if (sl == 261 && dot == 1) {
        ppu->ppustatus &= ~0xE0; /* Clear VBL, sprite-0, sprite overflow */
    }

    /* Advance dot and scanline counters */
    if (++ppu->dot == 341) {
        ppu->dot = 0;
        if (++ppu->scanline == 262) {
            ppu->scanline = 0;
            ++ppu->frame;
        }
    }
}
```

The SNES PPU scales this complexity considerably. It introduces eight distinct background modes (Mode 7 being the affine-transformed pseudo-3D floor used in F-Zero and Super Mario Kart), hardware windows that can mask layers with any boolean combination, color math that blends layers using per-pixel add or subtract operations, and a high-resolution mode that doubles horizontal resolution to 512 pixels using alternating fields. Each of these features must be modeled as a continuation of the same dot-by-dot state machine approach, with the HDMA (Horizontal DMA) system layered on top to allow the CPU to update PPU registers once per scanline from a table in RAM, enabling per-scanline scroll values, color math coefficients, and window positions that produce effects impossible through direct CPU writes.

```
NES PPU Rendering Pipeline (per dot, visible region)

  VRAM                       Shift Registers              Pixel Output
  ────                       ───────────────              ────────────
  NT fetch ──► nt_byte ──┐
  AT fetch ──► at_byte ──┤
  PT_lo fetch ──► pt_lo ─┤──► reload at dot&7==7 ──► bg_shift_lo[15:0] ──┐
  PT_hi fetch ──► pt_hi ─┘                            bg_shift_hi[15:0] ──┤
                                                       at_shift_lo[7:0]  ──┤──► Mux(fine_x) ──► bg_pixel (2+2 bit)
                                                       at_shift_hi[7:0]  ──┘

  OAM secondary ──► sp_shift_lo[7:0] [0..7] ──┐
                    sp_shift_hi[7:0] [0..7] ──┤──► X counter expire ──► sp_pixel (2+2 bit)
                    sp_attribute[7]  [0..7] ──┘

  bg_pixel + sp_pixel ──► Priority Mux ──► Palette RAM index ──► RGBA output
```

### The Audio Subsystem: Continuous Waveform Generation

Audio synthesis chips in classic consoles were wavetable or FM synthesizers running at audio rates, generating samples that were mixed and output continuously. The emulator must generate these samples in synchrony with the CPU timeline, not as a post-process batch, because the CPU writes to audio registers in between samples and those writes must be reflected immediately in subsequent samples.

The NES APU contains five synthesis channels: two pulse wave generators, one triangle wave generator, one noise generator using a linear-feedback shift register (LFSR), and one DPCM (Delta-modulated PCM) sample playback channel. Each channel is a small state machine. The pulse channels, for example, maintain a timer that counts down at the CPU clock rate; when it reaches zero, it reloads from a period register and clocks a phase counter into an 8-step waveform table that selects the duty cycle. The output of each channel is a 4-bit unsigned integer, and the five outputs are mixed through a non-linear lookup table that approximates the actual resistor DAC behavior of the original chip.

```c
typedef struct {
    uint16_t timer_period;   /* 11-bit reload value */
    uint16_t timer_counter;  /* current countdown   */
    uint8_t  duty_cycle;     /* 0–3: selects waveform table row  */
    uint8_t  duty_pos;       /* position in 8-step waveform      */
    uint8_t  length_counter; /* silence when zero                */
    bool     length_halt;    /* also doubles as envelope loop    */
    bool     constant_vol;   /* constant volume vs. envelope     */
    uint8_t  volume;         /* constant volume or envelope period*/
    uint8_t  env_counter;    /* envelope decay counter (0–15)    */
    uint8_t  env_divider;    /* envelope clock divider           */
    bool     env_start;      /* set on register write, clears envelope*/
    /* Sweep unit */
    bool     sweep_enable;
    uint8_t  sweep_period;
    bool     sweep_negate;
    uint8_t  sweep_shift;
    uint8_t  sweep_divider;
    bool     sweep_reload;
    int      channel_index;  /* 0 for pulse1, 1 for pulse2 (negation differs) */
} APU_Pulse;

static const uint8_t DUTY_TABLE[4][8] = {
    {0, 1, 0, 0, 0, 0, 0, 0},  /* 12.5% */
    {0, 1, 1, 0, 0, 0, 0, 0},  /* 25%   */
    {0, 1, 1, 1, 1, 0, 0, 0},  /* 50%   */
    {1, 0, 0, 1, 1, 1, 1, 1},  /* 75% (negated 25%) */
};

static uint8_t apu_pulse_output(const APU_Pulse *p)
{
    if (p->length_counter == 0) return 0;
    if (DUTY_TABLE[p->duty_cycle][p->duty_pos] == 0) return 0;
    if (p->timer_period < 8) return 0;  /* muted: period too short */
    return p->constant_vol ? p->volume : p->env_counter;
}

static void apu_pulse_tick_timer(APU_Pulse *p)
{
    if (p->timer_counter == 0) {
        p->timer_counter = p->timer_period;
        p->duty_pos = (p->duty_pos + 1) & 7;
    } else {
        --p->timer_counter;
    }
}
```

The APU clocks its timer units at the CPU clock rate (every CPU cycle for the triangle channel, every other CPU cycle for pulse and noise). The length counter and envelope units are clocked by the frame sequencer, a secondary timer running at either 240 Hz (4-step mode) or 192 Hz (5-step mode) that divides the CPU clock by approximately 7457. The final mixed audio output must be sampled at the host audio rate (48000 Hz), which is not commensurate with the CPU clock rate (1789773 Hz). The standard solution is to run the APU state machine at full CPU clock resolution, accumulate samples into a ring buffer, and then apply a high-quality resampling filter (typically a windowed-sinc low-pass filter) when draining samples to the OS audio API. This approach correctly handles all register write timing, since writes are processed at their exact CPU-clock position before the samples are downsampled.

```c
/* High-quality blip buffer resampling: accumulate one CPU-rate sample */
void apu_mix_sample(APU_State *apu, NES_BlipBuf *blip)
{
    /* Non-linear mixing lookup table (pre-computed from DAC equations) */
    static float pulse_table[31];
    static float tnd_table[203];
    static bool tables_initialized = false;
    if (!tables_initialized) {
        for (int i = 0; i < 31; ++i)
            pulse_table[i] = i == 0 ? 0.0f : 95.52f / (8128.0f / i + 100.0f);
        for (int i = 0; i < 203; ++i)
            tnd_table[i]   = i == 0 ? 0.0f : 163.67f / (24329.0f / i + 100.0f);
        tables_initialized = true;
    }

    uint8_t p1  = apu_pulse_output(&apu->pulse1);
    uint8_t p2  = apu_pulse_output(&apu->pulse2);
    uint8_t tri = apu_triangle_output(&apu->triangle);
    uint8_t nse = apu_noise_output(&apu->noise);
    uint8_t dmc = apu->dmc.output_level;

    float out = pulse_table[p1 + p2] + tnd_table[3 * tri + 2 * nse + dmc];
    blip_add_delta(blip, apu->clock_cycle, (int)(out * 32767.0f) - apu->last_output);
    apu->last_output = (int)(out * 32767.0f);
}
```

The Game Boy APU adds a wave channel that plays back a 32-nibble user-defined waveform stored in Wave RAM, plus a noise channel with configurable LFSR polynomial. The SNES introduces an eight-channel DSP using the BRR (Bit Rate Reduction) compressed sample format and pitch modulation, where the output of one channel can modulate the pitch counter of the next channel, enabling FM synthesis-like effects using the sample playback hardware. Each of these designs requires the same architectural commitment: tick the synthesis state machine at full hardware clock rate, generate samples inline, and downsample to the host rate through a high-quality filter.

### Input: Polling vs. Interrupt-Driven Latching

Classic console input is architecturally simple but precision-sensitive. The NES controller is a parallel-in serial-out shift register (a 4021 IC) containing eight latches, one per button. The CPU strobes the latch line by writing bit 0 of register `$4016` high and then low, which causes the 4021 to sample all eight buttons simultaneously into its parallel input. The CPU then reads bit 0 of `$4016` or `$4017` eight times in succession, each read clocking out the next button state from the serial output. This protocol is entirely polled—the controller never interrupts the CPU—and the accuracy requirement is simply that the latch strobe happens before the game reads the serial bits. Because the strobe and read sequence is always a tight loop in the game code, it always completes within a few hundred CPU cycles, well within the 29780-cycle VBLANK window where most games perform input polling.

The complexity in input emulation arises not from the serial protocol itself but from two hardware behaviors that some games depend upon: the serial shift register continues to advance with each read even if more than eight reads are performed (the register wraps, returning all ones after the eighth bit), and the DPCM IRQ on the NES can fire mid-read, corrupting the button state if the game does not disable IRQs during the read sequence. A complete input emulator must model the shift register explicitly as a byte being shifted out bit by bit, not as a simple array of eight values returned in sequence, because the number of reads before the next strobe is variable and observable.

```c
typedef struct {
    uint8_t  shift_reg;      /* current state of the shift register */
    uint8_t  latch;          /* latched button state from last strobe */
    bool     strobe;         /* current state of the strobe line      */
} NES_Controller;

/* Called when CPU writes $4016 */
void controller_write(NES_Controller *c, uint8_t data)
{
    bool new_strobe = (data & 1) != 0;
    if (c->strobe && !new_strobe) {
        /* Falling edge: latch current button state into shift register */
        c->shift_reg = c->latch;
    }
    c->strobe = new_strobe;
}

/* Called when CPU reads $4016 (controller 1) */
uint8_t controller_read(NES_Controller *c)
{
    uint8_t bit;
    if (c->strobe) {
        /* While strobe is held high, D0 always reflects button A */
        bit = (c->latch >> 7) & 1;
    } else {
        /* Shift register: D0 = MSB, then shift left */
        bit = (c->shift_reg >> 7) & 1;
        c->shift_reg = (uint8_t)(c->shift_reg << 1) | 1;  /* fills with 1 after 8 reads */
    }
    return 0x40 | bit;  /* bits 2–7 reflect the open bus value on real hardware */
}
```

The SNES extends this to a two-byte serial protocol per controller (12 buttons plus 4 padding bits) and introduces an *automatic joypad read* feature: the SNES hardware can automatically strobe and read all four controller ports into internal registers at the start of each VBLANK, freeing the CPU from manual polling. Games that use this feature read their button states from the auto-read registers (`$4218`–`$421F`) rather than bit-banging `$4016`/`$4017`. The emulator must track whether the auto-read is in progress (it takes 4224 master clock cycles to complete) and return stale data from those registers if read during the auto-read window, exactly as the hardware does.

### Save State Serialization

Save state serialization is the process of capturing the complete emulator state at an arbitrary point in execution and writing it to a binary image that can be restored later, resuming execution as if uninterrupted. The requirement is total state capture: every register, every memory cell, every timer counter, every DMA position, every pipeline latch, and every audio envelope phase. Missing any field means the restored state diverges from the original execution within a few cycles, producing graphical corruption, audio glitches, or outright crashes.

The architectural challenge is that emulator state is spread across dozens of loosely coupled structs. A save state system built by manually enumerating fields is fragile—adding a new field to any struct requires updating the serializer, and forgetting to do so introduces a subtle corruption bug that may not manifest until the restored state is dozens of frames old. The robust solution is to build the state structs as plain-old-data (POD) types with no pointers and no virtual dispatch, then use a versioned block format where each subsystem emits a tagged, length-prefixed binary block containing its entire struct. The loader verifies block identity, checks the length against the known struct size for the declared version, and can zero-initialize fields that are present in the struct but absent from the file (forward-compatible extension).

```c
#define SAVE_STATE_MAGIC   0x4B53544154452020ULL  /* "KSTATE  " */
#define SAVE_STATE_VERSION 4

typedef struct __attribute__((packed)) {
    uint64_t magic;
    uint32_t version;
    uint32_t num_blocks;
    uint32_t total_size;
    uint32_t crc32;
} SaveStateHeader;

typedef struct __attribute__((packed)) {
    uint32_t block_id;    /* FourCC: 'CPU0', 'PPU0', 'APU0', 'MAP0', etc. */
    uint32_t version;
    uint32_t data_size;
    uint32_t reserved;
} SaveStateBlockHeader;

/* Each subsystem implements these two functions */
typedef void (*SerializeFn)(const void *component, uint8_t *out_buf, uint32_t buf_size);
typedef void (*DeserializeFn)(void *component, const uint8_t *in_buf, uint32_t buf_size, uint32_t saved_version);

typedef struct {
    uint32_t    block_id;
    void       *component;
    uint32_t    current_size;
    SerializeFn   serialize;
    DeserializeFn deserialize;
} SaveStateEntry;
```

A subtle but critical requirement is that **pointer-based structures must be rebuilt from serialized data, not saved as raw pointers**. Mapper implementations often maintain pointers into their PRG and CHR ROM arrays to implement the fast bank-switched read path. These pointers are runtime virtual addresses that will be invalid in a different process or even a different run of the same process (ASLR). The save state must record the logical bank indices, not the pointer values, and the deserializer must recompute the pointers from those indices after loading. Similarly, any function pointers used in hot-path dispatch tables (read/write handlers that vary by mapper state) must be regenerated by re-running the mapper initialization logic after restoring the mapper register state.

The timing-sensitive fields deserve particular attention. Saving the PPU's `dot` and `scanline` counters is straightforward, but the relationship between the CPU cycle counter and the PPU cycle counter must be preserved exactly. The NES has a quirk where the pre-render scanline is one dot shorter on odd frames during rendering, to account for the half-clock offset between CPU and PPU timing. This "skip dot" behavior means the total number of PPU dots per frame is not constant, and a save state taken near the end of a frame on an odd frame will have a different expected cycle alignment than one taken at the same scanline/dot position on an even frame. The frame parity flag must be part of the serialized state.

```c
/* Complete NES system save state - all fields POD, no pointers */
typedef struct __attribute__((packed)) {
    /* CPU (6502) */
    uint16_t cpu_pc;
    uint8_t  cpu_a, cpu_x, cpu_y, cpu_sp, cpu_p;
    uint64_t cpu_cycle_count;
    uint8_t  cpu_irq_pending;
    uint8_t  cpu_nmi_pending;
    uint8_t  cpu_halt;          /* set during OAM DMA or DPCM stall */
    uint8_t  cpu_odd_cycle;     /* toggled each CPU cycle; affects APU clocking */

    /* RAM */
    uint8_t  wram[2048];

    /* PPU registers and pipeline */
    NES_PPU  ppu;               /* the full NES_PPU struct from earlier, POD */

    /* APU */
    APU_State apu;

    /* Controllers */
    NES_Controller ctrl[2];

    /* Mapper bank indices (not pointers) */
    uint8_t  prg_bank[4];       /* up to 4 switchable 8KB PRG banks */
    uint8_t  chr_bank[8];       /* up to 8 switchable 1KB CHR banks */
    uint8_t  mapper_registers[16]; /* mapper-specific register state */
    uint8_t  mapper_irq_counter;
    uint8_t  mapper_irq_latch;
    uint8_t  mapper_irq_enable;
    uint8_t  mapper_chr_rom_mode;
    uint8_t  mapper_prg_rom_mode;
    uint8_t  frame_parity;       /* odd/even frame for skip-dot logic */
} NES_SaveState;
```

---

## 3. High-Performance Optimization & Failure Modes

### Timing Architecture: The Scheduler vs. Catch-Up Models

There are two fundamental approaches to synchronizing multiple emulated components, and the choice between them drives significant tradeoffs in accuracy, performance, and code complexity.

The **catch-up model** (also called the lazy evaluation or just-in-time model) runs the CPU for a fixed quantum—typically until the end of the current scanline—then fast-forwards the PPU and APU state machines to match the CPU's current cycle count. This model is easy to implement because each subsystem has a simple "run until cycle N" function that iterates an inner loop. It fails for any game that relies on the interleaving of CPU and PPU behavior within a scanline, because the PPU is advanced as a batch *after* all the CPU writes have already occurred. Any mid-scanline register write that should affect pixels at a specific dot column will instead affect all subsequent pixels in the entire catch-up batch.

The **interleaved tick model** advances all subsystems one minimal unit at a time—typically one master clock cycle, or the LCM of their clock divisors—ensuring that CPU writes are visible to the PPU with cycle-level accuracy. The NES master clock approach runs three PPU ticks for every CPU tick, interleaved in the execution loop:

```c
void nes_run_frame(NES_State *nes)
{
    /* One NTSC frame = 29780 CPU cycles (even frame, rendering on) */
    uint32_t cpu_cycles_this_frame = 0;
    uint32_t target = 29780;

    while (cpu_cycles_this_frame < target) {
        /* Advance CPU by one instruction */
        uint32_t cpu_cycles_taken = cpu_step(&nes->cpu, &nes->bus);
        cpu_cycles_this_frame += cpu_cycles_taken;

        /* Advance PPU by 3x CPU cycles */
        for (uint32_t i = 0; i < cpu_cycles_taken * 3; ++i) {
            ppu_tick(&nes->ppu, &nes->mapper);
            /* Check for NMI assertion from PPU and inject into CPU */
            if (nes->ppu.nmi_line && !nes->cpu.nmi_pending) {
                nes->cpu.nmi_pending = true;
            }
        }

        /* Advance APU by CPU cycles (APU runs at CPU clock rate) */
        for (uint32_t i = 0; i < cpu_cycles_taken; ++i) {
            apu_tick(&nes->apu);
            apu_mix_sample(&nes->apu, &nes->blip);
        }
    }

    /* Flush blip buffer to host audio at the end of the frame */
    blip_end_frame(&nes->blip, cpu_cycles_this_frame);
}
```

The interleaved model has a significant performance cost: `ppu_tick` is called ~89,000 times per frame (341 dots × 262 scanlines = 89342), and `apu_tick` is called ~29780 times. At 60 fps, that is approximately 5.4 million PPU ticks and 1.8 million APU ticks per second. Each tick must be a tightly optimized function—ideally inlined by the compiler, with hot paths that avoid branches on the common case (a visible dot during active rendering). Profile-guided optimization and careful struct layout to maximize cache line utilization are essential. The PPU struct should be sized to fit in as few cache lines as possible, and the most frequently accessed fields (shift registers, counters, the current dot and scanline) should be laid out first.

### Hardware Edge Cases and Failure Modes

The most consequential failure modes in peripheral emulation are not gross inaccuracies but subtle timing bugs that affect a small number of games—the ones that pushed the hardware to its limits and whose developers therefore exploited behavior that most games never encountered.

**The sprite zero hit flag** on the NES is a prime example. This flag is set when a non-transparent pixel of sprite zero (the first entry in OAM) overlaps a non-transparent background pixel during rendering. Dozens of games use this flag as a raster timing signal—they spin in a tight loop reading `$2002` until the sprite zero hit bit goes high, then immediately write to the scroll register to implement a status bar that is scrolled independently from the play field. The flag is set on the specific dot where the overlap occurs, and reading `$2002` clears the VBLANK flag but not the sprite zero hit flag. An emulator that sets this flag at the end of the entire scanline (batch mode) will cause the loop to unblock at the wrong moment, shifting the status bar by up to 341 pixel columns. The fix requires setting the flag at the exact dot of the collision, which requires the dot-by-dot PPU model.

**The APU length table lookup** is another subtle trap. The length counter values are not stored as raw durations in the register; the register value is an index into a 32-entry lookup table that maps to the actual length counter value. This table is defined in the original hardware and must be reproduced exactly:

```c
static const uint8_t APU_LENGTH_TABLE[32] = {
    10, 254, 20, 2,  40, 4,  80, 6,
    160, 8, 60, 10, 14, 12, 26, 14,
    12, 16, 24, 18, 48, 20, 96, 22,
    192, 24, 72, 26, 16, 28, 32, 30
};
```

The values in this table are specific to the hardware design and cannot be derived from first principles; they were chosen to provide musically useful durations at the NTSC frame rate. Any deviation—even a single incorrect entry—will cause one or more notes in one or more games to terminate at the wrong time, producing an audible glitch.

**Mapper IRQ timing** represents the most complex class of edge cases. Memory mappers (the MMC3 is the most pervasive example) generate IRQs by counting PPU A12 line transitions—that is, by detecting when the PPU switches from accessing address space below `$1000` to above `$1000` or vice versa. This line transitions when the PPU fetches pattern table data for sprites versus background tiles, since the two pattern tables occupy different banks of CHR memory. The IRQ fires when the counter reaches zero, and games use this to split the screen mid-frame: when the IRQ fires at exactly the right scanline, the IRQ handler switches the mapper banks, changing which CHR data the PPU reads for the bottom half of the screen. If the A12 edge detection counts incorrectly—if, for example, the emulator counts sprite fetches in the wrong phase of the pipeline—the IRQ fires one or two scanlines early or late, and the bank switch appears at the wrong position on screen. This is one of the reasons why cycle-accurate sprite evaluation, specifically the sprite fetch ordering during dots 257–320, matters for correctness even in games that do not use mid-scanline effects directly.

**Audio filter modeling** is the final major source of divergence. The NES's audio output passes through a series of hardware RC filters before reaching the cartridge edge connector and ultimately the TV. There is a high-pass filter with a cutoff around 90 Hz (formed by the coupling capacitor between the APU and the cartridge port), a second high-pass filter at around 440 Hz (formed by the console's output coupling capacitor), and a low-pass filter at approximately 14 kHz (formed by the output cable capacitance). These filters affect the timbre of every sound in every game. An emulator that outputs the raw APU sample values without these filters will produce audio that is technically correct at the register level but sounds perceptibly thinner and harsher than the original hardware. Implementing these filters as first-order IIR filters in the audio mixing pipeline is a ten-line code change that makes an enormous perceptual difference:

```c
typedef struct {
    float cap;      /* capacitor charge, models filter state */
} HighPassFilter;

typedef struct {
    float cap;
} LowPassFilter;

static inline float hp_filter(HighPassFilter *f, float sample, float charge_factor)
{
    float out = sample - f->cap;
    f->cap = sample - out * charge_factor;
    return out;
}

static inline float lp_filter(LowPassFilter *f, float sample, float charge_factor)
{
    f->cap += (sample - f->cap) * charge_factor;
    return f->cap;
}

/* charge_factor values computed from RC time constant and sample rate:
 * factor = exp(-2 * pi * cutoff_hz / sample_rate)
 * HP1 (90 Hz at 44100):  exp(-2 * pi * 90 / 44100)  ≈ 0.98726
 * HP2 (440 Hz at 44100): exp(-2 * pi * 440 / 44100) ≈ 0.93905
 * LP  (14kHz at 44100):  exp(-2 * pi * 14000/44100) ≈ 0.13353
 * Note: LPF charge factor is (1 - decay), so pass (1 - 0.13353) = 0.86647
 */
float nes_filter_sample(NES_AudioFilter *af, float raw)
{
    float s = hp_filter(&af->hp1, raw,  0.98726f);
    s       = hp_filter(&af->hp2, s,    0.93905f);
    s       = lp_filter(&af->lp,  s,    0.86647f);
    return s;
}
```

**Save state rewind** is a performance challenge that exposes a deeper architectural tension. Many modern emulators implement frame rewind—the ability to hold a button and step backward in time, frame by frame. The naïve implementation takes a full save state every frame and stores them in a ring buffer. For the NES, a full save state is on the order of 25 KB (mostly the WRAM, PPU VRAM, and frame buffer); at 60 fps, a 10-second rewind window requires 600 save states totaling approximately 15 MB, which is entirely practical. For the SNES, the state is larger (128 KB WRAM, 64 KB VRAM, 128 KB audio RAM, work RAM), making 10 seconds of rewind roughly 100 MB before compression. The standard mitigation is delta compression: rather than storing the full state each frame, store a full state every N frames and store only the XOR difference from the previous state for intermediate frames. Because most of WRAM is unchanged between adjacent frames, the XOR delta is sparse and compresses well with a simple run-length encoder. Rewinding then requires seeking to the most recent full state at or before the target frame and replaying the deltas forward, which must be completed in under 16 milliseconds to maintain the interactive feel.

The ultimate measure of a peripheral emulator's quality is not whether it passes a standard compatibility test suite but whether it reproduces the temporal relationships between subsystems with sufficient fidelity that software written to exploit those relationships behaves exactly as it did on hardware. This is an asymptotic goal—full cycle accuracy across all edge cases requires essentially re-implementing the chip in RTL and synthesizing it—but the gap between a well-engineered software emulator and that ideal has narrowed to the point where the remaining differences are audible only on test hardware with an oscilloscope. The architectural decisions in this lesson—dot-accurate PPU rendering, inline APU sample generation, explicit shift-register input modeling, versioned save state serialization, and hardware filter emulation—represent the minimum investment required to close that gap to commercial and preservation-grade accuracy.
