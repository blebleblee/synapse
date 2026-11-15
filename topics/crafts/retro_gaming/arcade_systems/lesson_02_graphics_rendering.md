# Lesson 2: Graphics Rendering and Sprite Systems

## 1. First-Principles Intuition & Invariants

Before a single pixel appears on a CRT monitor, before a spaceship explodes or a ghost reverses direction, an extraordinary mechanical contract must be honored sixty times per second between the arcade hardware and the electron gun sweeping the display. Understanding that contract at its lowest level is what separates a practitioner who *uses* retro hardware from one who *commands* it.

The CRT is not a frame buffer in the modern sense. It is a timed projectile. An electron beam fires from a cathode, is steered by electromagnetic deflection coils, and strikes a phosphor coating on the inside of the glass. The glow produced at that point of impact is the pixel. The beam moves left to right across one horizontal line, then retraces rapidly to the left edge of the next line down — the horizontal blanking interval — and when it reaches the bottom of the screen it races back to the top-left corner entirely — the vertical blanking interval, or VBlank. These two blanking periods are not idle dead time. They are the most precious computational windows in all of classic arcade engineering. Everything the hardware cannot do while the beam is drawing — loading new sprite coordinates, swapping palette registers, acknowledging interrupts — must happen inside these brief intervals, or the visual result will be a torn, corrupted image called a *raster artifact*.

The standard North American NTSC timing, which governed the vast majority of arcade hardware from the mid-1970s through the late 1980s, runs at 60.0 Hz with 262 total scanlines per frame, of which approximately 224 are visible and 38 constitute the vertical blanking overhead. PAL territories ran at 50 Hz with 312 total scanlines. This is not a minor implementation detail. A game designed on NTSC timing that runs unmodified on a PAL board gains 20 extra milliseconds per frame — roughly 11 extra scanlines of VBlank — which completely changes the interrupt budget and can cause music engines to run audibly flat. Every competent arcade engineer understood this invariant from first principles and built timing compensation into their code from the start.

The fundamental graphics problem these engineers faced was economic. DRAM in 1979 was expensive per bit, and a fully realized frame buffer for even a 256×224 display at four bits per pixel would require 28,672 bytes of storage — an enormous sum when complete arcade PCBs were being manufactured for under $200 of parts. The solution was *tilemapping*: rather than storing the color value of every pixel individually, store a small library of reusable 8×8 pixel patterns called *tiles* in a dedicated ROM, and store only a reference index into that library in VRAM. A screen of 32×28 tiles requires only 896 bytes to describe its entire background, with the hardware reconstructing the actual pixel values by lookup in real time as the beam sweeps across each line. This one insight — indirection through a tile index — is the architectural nucleus from which all subsequent complexity grows.

The invariants that govern every system in this lesson follow directly from the physics of the CRT. Because the beam generates its display sequentially and unidirectionally from top-left to bottom-right, any data the rendering hardware needs for a given scanline must already be present in a register or latch by the time the beam reaches that scanline. This is not a soft guideline; it is a hard physical constraint with zero tolerance. The software and hardware co-design of every classic arcade board is, at its core, an exercise in scheduling data delivery ahead of an unforgiving, real-time deadline that arrives every 15.72 microseconds for NTSC horizontal sync.

---

## 2. Core Architecture & Mechanics

### The Video Signal Pipeline

The path from stored data to visible phosphor glow moves through several distinct hardware stages, each operating in tight coordination. It is worth tracing this pipeline concretely using the Namco Pac-Man hardware (1980) as a canonical example, since its schematics are exhaustively documented and its architecture represents the first full generation of purpose-built arcade graphics hardware.

```
+------------------+     +------------------+     +--------------------+
|   Tile ROM       |     |   Sprite ROMs    |     |   Color PROMs      |
| (4 KB, 2bpp gfx) |     | (4 KB, 2bpp gfx) |     | (256×4 bit lookup) |
+--------+---------+     +--------+---------+     +---------+----------+
         |                        |                          |
         v                        v                          v
+--------+---------+     +--------+-----------+   +---------+----------+
| Tile Address Mux |     | Sprite Line Buffer |   |  Palette Index Mux |
| (VRAM row/col    |     | (dual-ported line  |   |  (selects pen from  |
|  → tile index)   |     |  buffer, 2 lines)  |   |   color PROM bank) |
+--------+---------+     +--------+-----------+   +---------+----------+
         |                        |                          |
         +------------------------+                          |
                        |                                    |
                        v                                    |
              +---------+----------+                         |
              |  Pixel Priority    +<------------------------+
              |  Arbitration Logic |
              |  (sprite vs tile   |
              |   vs background)   |
              +---------+----------+
                        |
                        v
              +---------+----------+
              |  DAC / RGB Output  |
              |  (resistor ladder  |
              |   or dedicated IC) |
              +--------------------+
```

The Tile Address Mux reads the current horizontal and vertical position counters, divides them by eight to identify which tile cell the beam is currently crossing, reads the tile index byte out of VRAM, then fetches the corresponding 8-byte row of pixel data from the Tile ROM. All of this must complete within the time it takes the beam to cross eight horizontal pixels — roughly 450 nanoseconds on standard NTSC hardware. The logic was implemented entirely in TTL discrete chips in the earliest boards, with the Z80 or 6809 CPU playing no role whatsoever in this rendering loop. The CPU's only job is to write the correct data into VRAM and sprite registers before the beam needs them.

### VRAM Organization and Tile Encoding

VRAM layout on classic hardware is almost always a flat array of tile indices organized in row-major order, with the topmost left tile at address 0x4000 on Pac-Man or 0x9800 on the original Donkey Kong. The tile index value — typically one byte — is used as an address into the tile ROM. Each 8×8 tile in a 2bpp (two bits per pixel) encoding occupies 16 bytes of ROM: eight rows of eight pixels, with the two bit-planes either interleaved or packed into consecutive bytes depending on the board design.

A 2bpp tile can represent four distinct values per pixel. Those values are not colors directly; they are *palette indices*. The hardware takes each pixel's 2-bit value, combines it with a 2-bit *color attribute* stored in a parallel attribute VRAM plane, and uses the combined 4-bit value to address a color PROM. The color PROM maps that 4-bit index to actual RGB voltage levels. This two-stage indirection is precisely what allows a single tile graphic to appear in multiple colorways across the screen without storing multiple copies of the tile geometry in ROM.

On the Pac-Man hardware, the color PROM is a 256×4-bit Texas Instruments 74S287, whose output drives a resistor ladder DAC producing the analog RGB signal. The hardware supports 16 distinct colors drawn from a larger master palette, and each color cell in the tilemap attribute plane selects which 4-color sub-palette a tile uses. This is a fundamental constraint practitioners must internalize: the palette is not infinitely flexible. The number of simultaneous on-screen colors is bounded by the PROM dimensions and the attribute bit-width, not by any aesthetic consideration.

### Sprite Architecture and the Line Buffer Problem

Sprites are where the engineering complexity escalates dramatically, because a sprite can appear at any arbitrary (x, y) pixel coordinate rather than the fixed grid positions of the tile layer. The hardware must determine, for each pixel the beam visits, whether any active sprite contributes a non-transparent pixel at that coordinate — and it must resolve this question faster than the beam moves.

The classic solution, used on virtually every arcade board from Galaga (1981) onward, is the *sprite line buffer*, sometimes called a *sprite scanline renderer*. The concept works in two phases operating on alternating scanlines. During the time the beam draws scanline N, dedicated sprite rendering logic is simultaneously computing which sprites intersect scanline N+1 and writing their pixel colors into a secondary line buffer (or the second half of a ping-pong buffer). When the beam moves to scanline N+1, it reads from that pre-computed buffer rather than performing lookups on the fly.

This architecture has a direct consequence for the maximum number of sprites per scanline. Because the sprite renderer has only one horizontal period (roughly 63.5 microseconds for NTSC) to evaluate all active sprites and populate the line buffer for the next scanline, there is a hard limit on how many sprites can be processed in that window given the ROM access speeds of the era. Namco's Galaga hardware can process eight sprites per scanline. Attempting to exceed this limit — placing more than eight sprite objects within a single horizontal band of eight pixels — produces the classic *sprite flicker* artifact seen in home ports of the era, where software engineers would cycle sprite visibility across frames to simulate a larger object count at the cost of ghostly transparency.

### Sprite Multiplexing in Practice

Sprite multiplexing is the technique of reusing the hardware's fixed pool of sprite registers across multiple logical objects by exploiting their vertical positions. If the hardware provides 32 sprite slots, but your game logic requires 64 visible objects, you can in principle assign each hardware slot to a different logical object on each frame, as long as no two logical objects that share a slot ever occupy the same scanlines simultaneously. The constraint is spatial: objects in the top half of the screen never conflict with objects in the bottom half, so you can multiplex freely between halves.

The implementation discipline required is strict. Sprite registers must be updated during VBlank, before the beam begins the active display area. On a Z80-based system like the one powering Galaga, the VBlank interrupt service routine must complete the full sprite register update pass within approximately 1,200 Z80 clock cycles at 6 MHz — leaving essentially no room for game logic inside the ISR itself. Practitioners who ignore this budget and allow sprite register writes to spill into the active display period will see corrupted sprite positions on the first scanline the write raced against, producing a characteristic horizontal tear in the affected sprite.

The mid-frame raster interrupt is a more sophisticated multiplexing technique that extends the technique from vertical regions to arbitrary scanline boundaries. Rather than a single VBlank interrupt, the hardware (or a software-driven counter) fires a CPU interrupt at a specific programmable scanline. The ISR can then rewrite sprite registers midway through the frame, allowing the same hardware slot to show a completely different sprite in the top half versus the bottom half of the screen. Konami's hardware from 1983 onward and later Capcom's CPS-1 architecture both exploit midframe register writes to achieve object densities that would otherwise require far more hardware sprite slots.

### Color Palettes and CLUT Architecture

The Color Look-Up Table — CLUT — is the bridge between the compact indexed pixel data stored in ROM and the actual voltages delivered to the monitor. Its design determines the visual richness of the entire system within the constraints of affordable hardware.

On early single-board designs like Pac-Man, the CLUT is burnt into a bipolar PROM and is effectively immutable at runtime. The 32 colors Pac-Man can display are fixed at manufacturing time. By contrast, the Namco Pole Position (1982) and later Taito hardware introduced *RAM-based palettes*, where the CPU can write new RGB values into palette RAM at runtime. This seemingly small change opened the door to color cycling (animating flames or water by rotating palette entries while the tile data remains static), fade-to-black effects (scaling all RGB values uniformly toward zero across VBlank), and dynamic color reassignment for game state changes (a shield flashing red when hit by decrementing its palette entry toward red over successive frames).

The palette architecture on the Nintendo VS. System and later NES-derived hardware demonstrates how far this indirection can be pushed. The hardware maintains two 16-entry sub-palettes: one for backgrounds and one for sprites. Each tilemap attribute byte selects one of four palette groups for its 2×2 tile region, and each sprite's attribute byte independently selects its own palette group. The CPU can rewrite any entry in palette RAM during VBlank, enabling 25 simultaneously visible colors (with one transparent entry shared across both palettes) from a master set of 64 possible colors. The constraint — that all tiles in a 2×2 block share the same palette group — is the direct origin of the visible palette blocking artifacts in NES games, where you sometimes see a 16×16 pixel region with inconsistent color boundaries that betray the hardware's attribute granularity.

### Collision Detection on Classic Hardware

Modern practitioners accustomed to software AABB intersection tests are often surprised to discover that early arcade hardware implemented collision detection as a *hardware pixel coincidence circuit*: a dedicated logic gate array that fires an interrupt or sets a status register when any non-transparent sprite pixel overlaps any non-transparent pixel from another sprite or the background tilemap.

The pixel-coincidence approach is elegant in its simplicity and deeply tied to the line buffer architecture. Because the sprite renderer is already writing pixel values into the line buffer, the collision detection hardware can monitor that write operation: if a write attempts to place a pixel into a buffer cell that already contains a non-transparent value from an earlier sprite, that cell is doubly occupied, and the hardware sets a collision flag. The CPU reads this flag in the next VBlank and responds with game logic (explosion spawning, health decrement, sound trigger).

This hardware collision system has a characteristic failure mode that experienced practitioners know well: it is *screen-bound*. If two sprite objects overlap at coordinates outside the visible display area — if one of them has drifted off-screen due to a coordinate wrapping error — the hardware collision circuit cannot detect the overlap, because there is no line buffer for off-screen pixels. Games relying purely on hardware collision will silently fail to detect hits on off-screen objects. The correct engineering response, used by virtually every professional arcade title from 1982 onward, is a hybrid approach: use hardware collision as the first-pass fast path for on-screen objects and validate it with a simple CPU-side bounding-box check that guards against the off-screen edge case.

---

## 3. High-Performance Optimization & Failure Modes

### VBlank Budget Analysis and ISR Discipline

The single most consequential optimization a practitioner working with classic arcade hardware can perform is a disciplined accounting of the VBlank budget. On a 6 MHz Z80 system with NTSC timing, VBlank lasts approximately 1,200 to 1,400 instruction cycles, depending on the exact board timing. Every cycle spent on game logic inside the VBlank ISR is a cycle unavailable for the register writes that the display hardware requires. The professional practice is to perform all display-critical writes first — sprite X/Y registers, sprite tile indices, palette updates — and then return from the ISR, deferring game logic to the main loop running during active display time when the CPU has no hardware register deadlines.

A useful diagnostic technique is to toggle a spare output pin or write a known value to an unused VRAM address at the entry and exit of the VBlank ISR, then observe that signal on a logic analyzer or oscilloscope synchronized to the vertical sync pulse. The resulting pulse width, converted to cycles, is the actual ISR cost. If this pulse approaches the full VBlank window, the system is at risk of register write corruption under load, and the ISR must be restructured.

### Tile Cache Coherency and Dirty Region Management

When a game needs to update the tilemap — redrawing a score display, animating a tile-based waterfall, clearing a destroyed wall section — writing every tile in the affected region during a single VBlank can easily overflow the cycle budget. The robust solution is *dirty region tracking*: the game logic maintains a bitfield or list of tilemap cells that have been modified during the current frame, and the VBlank ISR iterates only through dirty cells rather than the full tilemap. For a 32×28 tilemap, a 896-bit dirty flag array costs 112 bytes and reduces worst-case VBlank write cost from 896 VRAM writes to only the actually-changed cells.

The failure mode of naive full-tilemap updates is subtle: on boards where VRAM writes consume additional bus cycles (due to wait states inserted by the video hardware to prevent CPU-video bus conflicts), iterating the entire 896-byte tilemap can cost upward of 4,000 cycles — well over the VBlank window. The symptom is not a clean visual tear but rather a jagged, stochastic corruption pattern on the topmost scanlines, because the VBlank window closed mid-write and the display hardware resumed scanning while the CPU was still in mid-update. The corruption pattern will shift with game state as the dirty region changes, making it look intermittent and confusing to diagnose without a scope.

### Sprite Coordinate Systems and Off-Screen Conventions

A persistent source of bugs in arcade sprite systems is the relationship between the sprite coordinate register and the visible display boundary. On many hardware platforms, the coordinate (0, 0) in the sprite register does not correspond to the top-left corner of the visible screen; instead, there is a hardware offset — typically 16 pixels on both axes — so that a sprite at register value (16, 16) appears at the top-left corner of the display. This convention allows sprite hardware to represent an object partially off-screen at the top and left edges without using negative numbers in unsigned registers.

Placing a sprite with an X register value of zero does not hide it off-screen to the left; it places it 16 pixels to the left of the visible area, still potentially intersecting the display. The correct way to hide a sprite is to push its Y coordinate below the visible display boundary (typically a value of 240 or greater for NTSC 224-line displays), which forces the sprite line renderer to skip it for all visible scanlines. Writing zero to both coordinates and expecting invisibility is a beginner error that produces phantom sprites clustering in the top-left corner of the screen.

### Palette Contention and Color Bleed

When the CPU writes new values to RAM-based palette registers during the active display period rather than during VBlank, the result is a horizontal line of incorrect color at the exact scanline where the write occurred. This color bleed artifact is distinct from sprite tearing: it affects the entire horizontal extent of the display at the write scanline, manifesting as a one-to-three pixel stripe of wrong color that moves vertically in sync with the game's palette update code. The fix is invariably the same — gate all palette writes behind a VBlank semaphore — but diagnosing the root cause requires knowing that this artifact pattern is the specific signature of an out-of-VBlank palette write rather than a hardware fault.

The more insidious version of this failure occurs when the palette write itself is *inside* the VBlank ISR but runs near the end of the VBlank window. If other ISR tasks overrun their cycle budget and push the palette writes past the VBlank deadline, the writes occur on the first visible scanline instead. The color bleed then appears only as a one-pixel stripe at the very top of the screen, which is easy to miss on a CRT with mild overscan but will be glaringly obvious on a properly aligned monitor or in emulator frame capture. Measuring ISR timing with a scope is the only reliable way to catch this condition before it reaches a production board.

### Multiplexing Failure: The Scanline Racing Bug

When implementing mid-frame raster interrupts for sprite multiplexing, the most dangerous failure mode is a race between the raster interrupt firing time and the actual beam position. If the interrupt fires one or two scanlines earlier or later than expected — due to CPU interrupt latency, an interrupt being briefly masked by another ISR, or a timer drift caused by a CPU wait state — the sprite register rewrite will execute at the wrong scanline. The sprite that should switch between top-half and bottom-half assignments at scanline 112 will instead switch at scanline 113 or 111, producing a one-pixel horizontal glitch line in the affected sprite where it briefly shows the wrong tile or color.

The mitigation strategy used by Konami's engineers was to place the raster interrupt trigger point two to four scanlines *before* the actual visual transition point, then poll the hardware beam position counter inside the ISR until the counter reaches the exact target scanline before executing the register write. This converts the imprecise interrupt-latency problem into a precise, synchronous wait. The polling loop wastes CPU cycles but eliminates the race entirely and results in a pixel-perfect transition regardless of interrupt latency variation. The cycle cost of the polling loop is bounded and predictable, making it safe to include in the VBlank budget analysis.

### Emulator Validation as Diagnostic Ground Truth

For practitioners working on original hardware, cycle-accurate emulators such as MAME in its `-debug` mode serve as an indispensable reference instrument. MAME's debugger exposes the beam position registers (`hblank` and `vblank` state), the full VRAM contents as a tile viewer, sprite register values per-frame, and palette RAM dumps — none of which are directly observable on a physical PCB without specialized equipment. Cross-referencing physical board behavior against MAME's cycle-accurate simulation allows precise isolation of whether an artifact is caused by software logic (which emulates identically) or a hardware fault such as a failing VRAM chip or a marginal PROM read (which emulates cleanly while the physical board misfires).

The workflow is: reproduce the artifact in MAME to confirm it is software-rooted, then trace through the MAME debugger to the exact cycle where the incorrect register write or tilemap update occurs. Once the precise code path and cycle offset are known from the emulator, verify the fix on physical hardware with a scope confirming ISR timing. This emulator-to-hardware loop is the most efficient diagnostic methodology available to the advanced practitioner, and it exploits the full depth of documentation that four decades of MAME development have produced.
