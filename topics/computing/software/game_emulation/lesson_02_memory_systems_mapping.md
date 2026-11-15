# Lesson 2: Memory Systems in Emulation

## 1. First-Principles Intuition & Invariants

Every emulator is, at its core, a lie told so convincingly that the guest software never suspects it is not running on real hardware. Nowhere is that lie more elaborate, or more consequential to correctness and performance, than in memory. A CPU emulator can get away with imprecision in timing or minor inaccuracies in flag behavior and still run most software acceptably. Memory, however, is load-bearing infrastructure: get the address translation wrong by a single byte, model the memory-mapped I/O decode incorrectly, or miss a DMA completion interrupt, and the target program crashes, hangs, or produces visual corruption that is immediately obvious. Memory systems are where emulators succeed or fail.

To understand why this problem is hard, consider what a real CPU actually sees. From the processor's perspective, there is a flat address space: a range of integer-valued addresses, each resolving to a readable or writable unit of storage. What lies behind those addresses is entirely opaque to the processor itself. On a real SNES, address `$2100` does not point to RAM. It points to a hardware register in the Picture Processing Unit (PPU) that controls screen brightness. Writing `$0F` to it triggers a hardware event. Reading it back may return a completely different value, or nothing meaningful at all. The address space is a shared coordinate system through which the CPU, the PPU, the Audio Processing Unit (APU), the DMA controller, and cartridge hardware all communicate, each claiming sovereignty over different ranges and sometimes contesting the same range depending on hardware mode.

This is the foundational invariant of memory system emulation: **an address is not a location, it is a contract**. The emulator's job is to faithfully replicate that contract for every address in the guest's physical address space, handling reads, writes, and sometimes open-bus behavior where no hardware claims an address at all. Getting this right requires modeling the entire decode logic of the original system's address bus — the combinational logic gates that, in silicon, determined which chip's chip-select line went low when a given address appeared on the bus.

The problem space subdivides cleanly into four concerns that this lesson addresses in depth. First, address space translation: how the guest's logical address is mapped to something the host can service, whether that is a region of host RAM, a hardware register callback, or a cartridge ROM bank. Second, memory-mapped I/O: the discipline of making reads and writes to hardware register ranges trigger behavioral side effects, not mere data storage. Third, banking mechanisms: the techniques used by 8-bit and 16-bit era hardware to extend addressable memory far beyond what the address bus width could directly reach. Fourth, DMA and cache coherency: how bulk memory transfers interact with CPU execution and what correctness guarantees the emulator must preserve.

Underlying all four concerns is a performance constraint that makes the problem interesting from an engineering standpoint. Memory access is the single most frequent operation any emulated CPU performs. On a 65C816 running at 3.58 MHz executing a tight inner loop, memory reads and writes may occur several million times per emulated second. If each access dispatches through a naive chain of if-else conditionals to determine what hardware is being addressed, the host CPU will spend the majority of its cycles in that dispatch chain rather than in meaningful emulation work. The architecture of the memory system dispatcher is therefore not an implementation detail — it is a first-order performance determinant.

The classical solution, developed in early emulators and refined over three decades, is the **page table dispatch model**: a statically-sized array of handler pointers or direct memory pointers, indexed by the high bits of the guest address, that collapses the O(n) dispatch chain into an O(1) array lookup. This mirrors, non-coincidentally, what real hardware does in silicon. Address decoding in a physical system is combinational logic operating in nanoseconds; the page table is its software equivalent, trading memory for latency. Understanding why this model works, where it breaks down, and how to extend it to handle banking and MMIO side effects is the central technical thread of this lesson.

---

## 2. Core Architecture & Mechanics

### The Memory Dispatch Engine

The fundamental data structure of an emulator's memory subsystem is an array of fixed-size page descriptors, indexed by the upper bits of the guest address. For a 24-bit address space (as found on the SNES with its 65C816 processor), you might divide the space into 4 KB pages, yielding 4096 page slots (`2^24 / 2^12`). For a simpler 16-bit system like the Game Boy, 256 pages of 256 bytes each covers the entire `0x0000`–`0xFFFF` space. Each slot in this array carries enough information to service either a read or a write without any further branching.

The most cache-efficient representation stores two pointers per page: one for reads, one for writes. When both pointers address real host RAM, reads and writes are a single pointer dereference plus an offset — no function call overhead. When a page hosts MMIO registers, the pointer field instead stores a tagged value or null sentinel that triggers a fallback to a handler function. This design keeps the common case (RAM access) in the fastest possible path while still supporting arbitrarily complex behavior in the slow path.

```c
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <assert.h>

/* Guest address space configuration for a 16-bit system (e.g. Game Boy).
   Page granularity: 256 bytes => 256 pages covering 0x0000-0xFFFF. */

#define PAGE_BITS       8
#define PAGE_SIZE       (1u << PAGE_BITS)          /* 256 bytes */
#define PAGE_COUNT      (0x10000u >> PAGE_BITS)    /* 256 pages */
#define PAGE_MASK       (PAGE_SIZE - 1)

/* A null read_ptr signals "MMIO or unmapped — call handler". */
typedef uint8_t (*mmio_read_fn) (void *ctx, uint16_t addr);
typedef void    (*mmio_write_fn)(void *ctx, uint16_t addr, uint8_t val);

typedef struct {
    uint8_t        *read_ptr;    /* Host pointer to backing byte[0] of page, or NULL */
    uint8_t        *write_ptr;   /* Host pointer to backing byte[0] of page, or NULL */
    mmio_read_fn    read_fn;     /* Called only when read_ptr == NULL */
    mmio_write_fn   write_fn;    /* Called only when write_ptr == NULL */
    void           *handler_ctx; /* Opaque context forwarded to handler functions */
} MemPage;

typedef struct {
    MemPage pages[PAGE_COUNT];
} MemMap;

/* ---------------------------------------------------------------------------
   Inline accessors — these are the hot path. The branch predictor will learn
   that read_ptr != NULL is the overwhelmingly common case for RAM-heavy code.
   --------------------------------------------------------------------------- */

static inline uint8_t mem_read8(const MemMap *map, uint16_t addr) {
    const MemPage *p = &map->pages[addr >> PAGE_BITS];
    if (__builtin_expect(p->read_ptr != NULL, 1))
        return p->read_ptr[addr & PAGE_MASK];
    return p->read_fn(p->handler_ctx, addr);
}

static inline void mem_write8(const MemMap *map, uint16_t addr, uint8_t val) {
    const MemPage *p = &map->pages[addr >> PAGE_BITS];
    if (__builtin_expect(p->write_ptr != NULL, 1))
        p->write_ptr[addr & PAGE_MASK] = val;
    else
        p->write_fn(p->handler_ctx, addr, val);
}

static inline uint16_t mem_read16_le(const MemMap *map, uint16_t addr) {
    /* Handles cross-page reads correctly without special-casing. */
    return (uint16_t)mem_read8(map, addr) |
           ((uint16_t)mem_read8(map, (uint16_t)(addr + 1)) << 8);
}

/* ---------------------------------------------------------------------------
   Map a region of host RAM into the guest address space.
   base and size must both be PAGE_SIZE-aligned.
   --------------------------------------------------------------------------- */
void mem_map_ram(MemMap *map,
                 uint16_t guest_base,
                 uint8_t  *host_ptr,
                 uint32_t  size,
                 int       writable) {
    assert((guest_base & PAGE_MASK) == 0);
    assert((size       & PAGE_MASK) == 0);

    uint32_t num_pages = size >> PAGE_BITS;
    uint32_t first_page = guest_base >> PAGE_BITS;

    for (uint32_t i = 0; i < num_pages; i++) {
        MemPage *p = &map->pages[first_page + i];
        p->read_ptr  = host_ptr + (i << PAGE_BITS);
        p->write_ptr = writable ? (host_ptr + (i << PAGE_BITS)) : NULL;
        p->read_fn   = NULL;
        p->write_fn  = NULL;
        p->handler_ctx = NULL;
    }
}

/* ---------------------------------------------------------------------------
   Map an MMIO region. Every access in [guest_base, guest_base+size) will
   dispatch through read_fn / write_fn.
   --------------------------------------------------------------------------- */
void mem_map_mmio(MemMap         *map,
                  uint16_t        guest_base,
                  uint32_t        size,
                  mmio_read_fn    rfn,
                  mmio_write_fn   wfn,
                  void           *ctx) {
    assert((guest_base & PAGE_MASK) == 0);
    assert((size       & PAGE_MASK) == 0);

    uint32_t num_pages = size >> PAGE_BITS;
    uint32_t first_page = guest_base >> PAGE_BITS;

    for (uint32_t i = 0; i < num_pages; i++) {
        MemPage *p = &map->pages[first_page + i];
        p->read_ptr  = NULL;
        p->write_ptr = NULL;
        p->read_fn   = rfn;
        p->write_fn  = wfn;
        p->handler_ctx = ctx;
    }
}
```

This structure is the skeleton every real-world emulator builds upon. The critical insight in `mem_read8` is the use of `__builtin_expect`: the branch predictor hint tells the compiler that `read_ptr != NULL` is the common case, keeping the fast RAM path in the fall-through (non-taken branch) direction of the conditional. On modern superscalar CPUs, this measurably reduces branch mispredictions in tight execution loops where the CPU is spending millions of cycles per second in this function.

### Address Space Layout and the Decode Model

Different guest architectures impose radically different address space topologies, and a good emulator implementation reflects the specific hardware decode logic of the target machine rather than a generic abstraction. Consider the contrast between the Game Boy and the SNES.

The original Game Boy's 65C816-less Sharp LR35902 operates over a plain 16-bit address space. The layout is fixed by hardware:

```
0x0000 - 0x3FFF : ROM Bank 0 (always mapped, 16 KB)
0x4000 - 0x7FFF : ROM Bank N (switchable via MBC, 16 KB)
0x8000 - 0x9FFF : Video RAM (VRAM, PPU-accessible)
0xA000 - 0xBFFF : External RAM (cartridge RAM, if present)
0xC000 - 0xCFFF : Work RAM Bank 0 (4 KB)
0xD000 - 0xDFFF : Work RAM Bank 1 (Game Boy Color: switchable)
0xE000 - 0xFDFF : Echo RAM (mirror of 0xC000-0xDDFF, discouraged)
0xFE00 - 0xFE9F : OAM (Object Attribute Memory, sprite table)
0xFEA0 - 0xFEFF : Unusable (prohibited region)
0xFF00 - 0xFF7F : I/O Registers (MMIO)
0xFF80 - 0xFFFE : High RAM (HRAM, 127 bytes)
0xFFFF          : Interrupt Enable register
```

Each region in this map has distinct behavioral semantics. The Echo RAM region at `0xE000`–`0xFDFF` mirrors Work RAM exactly; the hardware simply doesn't decode the `A13` address bit in that range. VRAM is accessible to the CPU only during certain PPU rendering phases — writing during other phases produces garbled results on hardware, and correct emulators either block the write or return `0xFF` on reads, depending on what the real hardware does. The prohibited region at `0xFEA0`–`0xFEFF` exhibits complex revision-dependent behavior on original Game Boy hardware versus Game Boy Color, behavior that some cartridges accidentally test.

The SNES address space is geometrically more complex because the 65C816 uses a 24-bit effective address (`[bank][address]`), and the mapping between those 24 bits and physical hardware differs by cartridge type. The two dominant cartridge ROM layouts, LoROM and HiROM, map ROM into the address space differently:

```
LoROM layout (simplified):
  Bank 0x00-0x3F, Addr 0x8000-0xFFFF  : ROM (lower 32 KB of each bank slot)
  Bank 0x00-0x3F, Addr 0x0000-0x1FFF  : Low RAM mirror
  Bank 0x00-0x3F, Addr 0x2100-0x21FF  : PPU registers (MMIO)
  Bank 0x00-0x3F, Addr 0x4300-0x43FF  : DMA registers (MMIO)
  Bank 0x7E-0x7F                       : 128 KB Work RAM

HiROM layout (simplified):
  Bank 0xC0-0xFF, Addr 0x0000-0xFFFF  : ROM (full 64 KB per bank slot)
  Bank 0x40-0x7D, Addr 0x0000-0xFFFF  : ROM mirrors
  Bank 0x7E-0x7F                       : 128 KB Work RAM
```

An emulator modeling both formats must configure its page tables differently at cartridge load time, reading the cartridge header to determine the mapping mode and then calling the appropriate initialization routine. The 24-bit SNES space with 4 KB pages produces 4096 page table entries (`2^24 / 2^12`), each independently configurable.

The architectural diagram below shows the signal path from CPU address generation through dispatch to backing storage:

```
                    ┌─────────────────────────────────┐
                    │          Emulated CPU Core        │
                    │   generates 16-bit or 24-bit      │
                    │   effective address (EA)          │
                    └────────────────┬────────────────-─┘
                                     │  EA
                                     ▼
                    ┌────────────────────────────────-──┐
                    │       MemMap Page Table            │
                    │  index = EA >> PAGE_BITS           │
                    │  page  = pages[index]              │
                    └──────┬──────────────┬─────────────┘
                           │              │
              read_ptr      │              │  read_ptr == NULL
              != NULL       │              │
                           ▼              ▼
              ┌────────────────┐    ┌─────────────────────┐
              │  Direct RAM    │    │  MMIO Handler Dispatch│
              │  Dereference   │    │  page.read_fn(ctx,EA) │
              │  O(1), ~1 ns   │    │  PPU / APU / DMA reg  │
              └────────────────┘    └──────────┬────────────┘
                                               │
                              ┌────────────────┴──────────────┐
                              │                               │
                    ┌─────────▼──────┐              ┌─────────▼──────┐
                    │   PPU Register │              │  DMA Register  │
                    │   Handler      │              │  Handler       │
                    │  (side effects)│              │ (triggers xfer)│
                    └────────────────┘              └────────────────┘
```

### Memory-Mapped I/O: Behavioral Contracts

MMIO handling is where emulation departs most sharply from the fiction that memory is just storage. Every hardware register in a retro system has a unique behavioral contract: some are write-only (reading them returns open-bus or a fixed value), some are read-only (writes are silently ignored or trigger different behavior than you'd expect), some have side effects on write that change hardware state instantaneously, and some are split across multiple bytes where writing the low byte "latches" a value that is committed only when the high byte is written.

The SNES PPU register `$2116`/`$2117` illustrates this clearly. These two registers form a 16-bit VRAM address port. Writing to `$2116` sets the low byte of the VRAM address; writing to `$2117` sets the high byte. The combined value determines where subsequent reads or writes through `$2118`/`$2119` land in VRAM, and after each such access the VRAM address auto-increments by a configurable step (1, 32, 128, or 256 words). An emulator that models these as naive byte-writable memory will produce immediate graphical corruption because it misses the address-latching state machine and the auto-increment mechanism.

The correct model for MMIO is a device struct with explicit register state, accessed through typed handler functions:

```c
#include <stdint.h>

/* Simplified SNES PPU VRAM port state. */
typedef struct {
    uint16_t vram_addr;        /* Current VRAM word address */
    uint8_t  vram_incr_mode;   /* 0 = increment after $2118/$2119 low, 1 = after high */
    uint8_t  vram_incr_step;   /* 0=1, 1=32, 2=128, 3=256 words */
    uint8_t  addr_latch_low;   /* Latched low byte pending high-byte write */
    uint16_t vram[32768];      /* 64 KB VRAM as 32K words */
    uint8_t  read_prefetch[2]; /* VRAM read prefetch buffer (low, high byte) */
} PPUState;

static uint16_t vram_step_table[4] = { 1, 32, 128, 256 };

/* Prefetch the word at the current VRAM address into the read buffer. */
static void ppu_vram_prefetch(PPUState *ppu) {
    uint16_t w = ppu->vram[ppu->vram_addr & 0x7FFF];
    ppu->read_prefetch[0] = (uint8_t)(w & 0xFF);
    ppu->read_prefetch[1] = (uint8_t)(w >> 8);
}

void ppu_write(PPUState *ppu, uint16_t reg, uint8_t val) {
    switch (reg) {
        case 0x2116:  /* VMADDL: VRAM address low byte */
            ppu->vram_addr = (ppu->vram_addr & 0xFF00) | val;
            ppu_vram_prefetch(ppu);
            break;
        case 0x2117:  /* VMADDH: VRAM address high byte */
            ppu->vram_addr = (ppu->vram_addr & 0x00FF) | ((uint16_t)val << 8);
            ppu_vram_prefetch(ppu);
            break;
        case 0x2118:  /* VMDATAL: VRAM data write low byte */
            ppu->vram[ppu->vram_addr & 0x7FFF] =
                (ppu->vram[ppu->vram_addr & 0x7FFF] & 0xFF00) | val;
            if (ppu->vram_incr_mode == 0)
                ppu->vram_addr += vram_step_table[ppu->vram_incr_step & 3];
            break;
        case 0x2119:  /* VMDATAH: VRAM data write high byte */
            ppu->vram[ppu->vram_addr & 0x7FFF] =
                (ppu->vram[ppu->vram_addr & 0x7FFF] & 0x00FF) | ((uint16_t)val << 8);
            if (ppu->vram_incr_mode == 1)
                ppu->vram_addr += vram_step_table[ppu->vram_incr_step & 3];
            break;
        default:
            break;
    }
}

uint8_t ppu_read(PPUState *ppu, uint16_t reg) {
    uint8_t result = 0;
    switch (reg) {
        case 0x2139:  /* VMDATALREAD: VRAM data read low, increment if mode 0 */
            result = ppu->read_prefetch[0];
            if (ppu->vram_incr_mode == 0) {
                ppu->vram_addr += vram_step_table[ppu->vram_incr_step & 3];
                ppu_vram_prefetch(ppu);
            }
            break;
        case 0x213A:  /* VMDATAHREAD: VRAM data read high, increment if mode 1 */
            result = ppu->read_prefetch[1];
            if (ppu->vram_incr_mode == 1) {
                ppu->vram_addr += vram_step_table[ppu->vram_incr_step & 3];
                ppu_vram_prefetch(ppu);
            }
            break;
        default:
            result = 0xFF;  /* Open bus */
            break;
    }
    return result;
}
```

The prefetch buffer is a hardware detail that many early emulators missed entirely. On real SNES hardware, reading `$2139` or `$213A` does not return the value at the current VRAM address — it returns whatever was prefetched into the internal buffer the last time the address was set or the last read was performed. The actual VRAM read happens as a side effect of the address write or the previous data read, not the current one. Games that relied on this behavior for fast VRAM inspection produced incorrect data in emulators that lacked the prefetch model.

### Banking Mechanisms

The banked memory model emerged as a hardware solution to a software problem: the programs being written for 8-bit systems in the mid-1980s had grown larger than the address space could directly accommodate. An 8-bit CPU with a 16-bit address bus can directly reach 64 KB. By the mid-1980s, RPGs and adventure games routinely exceeded this limit for ROM data alone, before accounting for RAM and MMIO.

The hardware solution was Memory Bank Controllers (MBCs on the Game Boy, mappers on the NES, the SuperFX chip's SRAM addressing on the SNES). The principle is uniform: designate one portion of the address space as a fixed "home bank" that always maps to the first section of ROM, and designate another portion as a "switchable window" that can be redirected to any bank of the larger physical ROM by writing a bank-select value to a specific address range. The CPU cannot access more than 64 KB at once, but it can reconfigure which 64 KB slice of a multi-megabyte ROM it is operating on between accesses.

The Game Boy's MBC1 controller illustrates the mechanism well. MBC1 supports up to 2 MB of ROM organized as 128 banks of 16 KB each. The fixed bank at `0x0000`–`0x3FFF` always maps to bank 0. The switchable bank at `0x4000`–`0x7FFF` maps to whichever bank is selected by the game's bank register writes. Writing to the address range `0x2000`–`0x3FFF` sets the lower 5 bits of the ROM bank number; writing to `0x4000`–`0x5FFF` sets bits 5–6, allowing the full 7-bit bank number to be constructed.

```c
#include <stdint.h>
#include <string.h>
#include <assert.h>

#define ROM_BANK_SIZE     0x4000u    /* 16 KB per ROM bank */
#define MAX_ROM_BANKS     128
#define ERAM_BANK_SIZE    0x2000u    /* 8 KB per external RAM bank */
#define MAX_ERAM_BANKS    4

typedef struct {
    const uint8_t *rom;              /* Full ROM image, contiguous in host memory */
    uint32_t       rom_size;         /* Total ROM size in bytes */
    uint8_t        eram[MAX_ERAM_BANKS][ERAM_BANK_SIZE]; /* External (cartridge) RAM */

    uint8_t  rom_bank_lo;    /* Lower 5 bits of active ROM bank (register 1) */
    uint8_t  rom_bank_hi;    /* Upper 2 bits of active ROM bank (register 2) */
    uint8_t  mode;           /* 0 = ROM banking mode, 1 = RAM banking mode */
    uint8_t  eram_enabled;   /* Whether ERAM reads/writes are enabled */
    uint8_t  eram_bank;      /* Active ERAM bank (in RAM banking mode) */
} MBC1State;

/* Compute the effective ROM bank number applying MBC1 rules.
   Bank 0 is not selectable for the switchable window; it aliases to bank 1. */
static uint8_t mbc1_effective_rom_bank(const MBC1State *mbc) {
    uint8_t bank = (mbc->rom_bank_lo & 0x1F);
    if (bank == 0) bank = 1;  /* 0 -> 1 aliasing */
    if (mbc->mode == 0)
        bank |= (mbc->rom_bank_hi & 0x03) << 5;
    return bank;
}

uint8_t mbc1_read(const MBC1State *mbc, uint16_t addr) {
    if (addr < 0x4000) {
        /* Fixed bank 0 */
        return mbc->rom[addr];
    } else if (addr < 0x8000) {
        /* Switchable bank window */
        uint32_t offset = (uint32_t)mbc1_effective_rom_bank(mbc) * ROM_BANK_SIZE
                          + (addr - 0x4000u);
        if (offset < mbc->rom_size)
            return mbc->rom[offset];
        return 0xFF;  /* Out-of-range: open bus */
    } else if (addr >= 0xA000 && addr < 0xC000) {
        if (!mbc->eram_enabled) return 0xFF;
        uint8_t bank = (mbc->mode == 1) ? (mbc->rom_bank_hi & 0x03) : 0;
        return mbc->eram[bank][addr - 0xA000u];
    }
    return 0xFF;
}

void mbc1_write(MBC1State *mbc, uint16_t addr, uint8_t val) {
    if (addr < 0x2000) {
        /* ERAM enable: lower nibble 0x0A enables, anything else disables */
        mbc->eram_enabled = ((val & 0x0F) == 0x0A) ? 1 : 0;
    } else if (addr < 0x4000) {
        /* ROM bank number low 5 bits */
        mbc->rom_bank_lo = val & 0x1F;
    } else if (addr < 0x6000) {
        /* ROM bank upper 2 bits, or RAM bank number */
        mbc->rom_bank_hi = val & 0x03;
    } else if (addr < 0x8000) {
        /* Banking mode select */
        mbc->mode = val & 0x01;
    } else if (addr >= 0xA000 && addr < 0xC000) {
        if (!mbc->eram_enabled) return;
        uint8_t bank = (mbc->mode == 1) ? (mbc->rom_bank_hi & 0x03) : 0;
        mbc->eram[bank][addr - 0xA000u] = val;
    }
}

/* After any bank register write, rebuild the MemMap page table entries
   for the switchable window 0x4000-0x7FFF to point directly into the ROM
   image at the newly selected bank. This keeps the hot path O(1). */
void mbc1_remap(MemMap *map, MBC1State *mbc) {
    uint32_t bank_offset = (uint32_t)mbc1_effective_rom_bank(mbc) * ROM_BANK_SIZE;
    /* ROM is read-only: write_ptr remains NULL, triggering mbc1_write on stores */
    mem_map_ram(map, 0x4000,
                (uint8_t *)mbc->rom + bank_offset,
                ROM_BANK_SIZE,
                0 /* read-only */);
}
```

The architectural trick in `mbc1_remap` is what separates a performant emulator from a naive one. Rather than routing every access in `0x4000`–`0x7FFF` through the MMIO handler indefinitely, the emulator recomputes the page table entries to point the `read_ptr` directly at the correct offset in the host's ROM image every time a bank switch occurs. Bank switches are rare — they happen at scene transitions, not in tight rendering loops — so the remapping cost amortizes to essentially zero. All the ROM reads in between, which vastly outnumber the bank switches, hit the O(1) direct dereference path.

### DMA Transfer Mechanics

Direct Memory Access controllers are a critical component of performance-oriented hardware designs because they offload bulk data movement from the CPU to dedicated silicon. The SNES DMA system is particularly instructive because it supports both general-purpose DMA (GPDMA) for bulk transfers and HDMA (H-Blank DMA) for per-scanline effects, and both interact with CPU execution in ways that emulators must model precisely.

SNES GPDMA operates on eight channels, each configurable through registers in `$4300`–`$43FF`. A transfer specifies a CPU-bus source address, a PPU-bus destination B-bus address, a byte count, and a transfer unit pattern (1 byte, 2 bytes, or a 4-byte pattern). When the game writes `1` to the `MDMAEN` register at `$420B`, all channels with their corresponding bit set execute synchronously: the CPU is halted for the duration of the DMA transfer, which completes at a rate of roughly 8 master cycles per byte.

The emulator must accurately account for this halt time because game code timing assumptions depend on it. A game that fires GPDMA during V-Blank to upload a tileset to VRAM expects the CPU to be unavailable for the transfer duration. If the emulator executes the DMA instantaneously, subsequent code may execute far earlier than expected relative to the PPU's scanline counter, causing logic errors in games that read the V-Blank status flag immediately after a DMA.

```c
#include <stdint.h>

/* SNES DMA channel register layout (one entry per channel 0-7). */
typedef struct {
    uint8_t  control;       /* $4300+n: transfer direction, unit pattern, addr mode */
    uint8_t  b_bus_addr;    /* $4301+n: B-Bus (PPU-bus) destination register */
    uint16_t a_bus_addr;    /* $4302+n / $4303+n: A-Bus source address */
    uint8_t  a_bus_bank;    /* $4304+n: A-Bus source bank */
    uint16_t byte_count;    /* $4305+n / $4306+n: 0x0000 means 65536 bytes */
} DMAChannel;

/* Transfer unit patterns indexed by bits 0-2 of the control register. */
static const uint8_t dma_unit_patterns[8][4] = {
    {0, 0, 0, 0},   /* 0: 1 reg, 1 byte  (write to B+0 repeatedly) */
    {0, 1, 0, 1},   /* 1: 2 regs, 2 bytes (B+0, B+1 alternating) */
    {0, 0, 0, 0},   /* 2: 1 reg, 2 bytes  (write to B+0 twice) */
    {0, 0, 1, 1},   /* 3: 2 regs, 4 bytes (B+0 x2, B+1 x2) */
    {0, 1, 2, 3},   /* 4: 4 regs, 4 bytes */
    {0, 1, 0, 1},   /* 5: same as pattern 1 */
    {0, 0, 0, 0},   /* 6: same as pattern 2 */
    {0, 0, 1, 1},   /* 7: same as pattern 3 */
};
static const uint8_t dma_unit_lengths[8] = {1, 2, 2, 4, 4, 2, 2, 4};

/* Execute all GPDMA channels selected in `enable_mask`.
   Returns the number of master clock cycles consumed (8 per byte + overhead).
   Caller must add this to the CPU cycle counter to advance the clock. */
uint32_t dma_execute_gpdma(MemMap         *map,
                            PPUState       *ppu,
                            DMAChannel      channels[8],
                            uint8_t         enable_mask) {
    uint32_t total_cycles = 0;

    for (int ch = 0; ch < 8; ch++) {
        if (!(enable_mask & (1u << ch))) continue;

        DMAChannel *c = &channels[ch];
        int direction    = (c->control >> 7) & 1;  /* 0 = A->B, 1 = B->A */
        int addr_mode    = (c->control >> 3) & 3;  /* 0=incr,2=decr,3=fixed */
        int pattern_idx  = c->control & 7;

        uint32_t count = c->byte_count ? c->byte_count : 65536u;
        uint8_t  unit_len = dma_unit_lengths[pattern_idx];

        /* DMA overhead: 8 cycles per channel activated. */
        total_cycles += 8;

        for (uint32_t i = 0; i < count; i++) {
            uint8_t  reg_offset = dma_unit_patterns[pattern_idx][i & 3];
            uint16_t b_reg      = 0x2100u | (uint16_t)(c->b_bus_addr + reg_offset);
            uint32_t a_full     = ((uint32_t)c->a_bus_bank << 16) | c->a_bus_addr;

            if (!direction) {
                /* A-Bus -> B-Bus (CPU RAM -> PPU register) */
                uint8_t byte = mem_read8(map, (uint16_t)(a_full & 0xFFFF));
                ppu_write(ppu, b_reg, byte);
            } else {
                /* B-Bus -> A-Bus (PPU register -> CPU RAM) */
                uint8_t byte = ppu_read(ppu, b_reg);
                mem_write8(map, (uint16_t)(a_full & 0xFFFF), byte);
            }

            /* Advance A-Bus address per addressing mode. */
            if (addr_mode == 0)       c->a_bus_addr++;
            else if (addr_mode == 2)  c->a_bus_addr--;
            /* mode 3 = fixed: no change */

            total_cycles += 8;  /* 8 master cycles per byte transferred */
        }

        /* Clear byte count register after transfer (hardware behavior). */
        c->byte_count = 0;
    }
    return total_cycles;
}
```

HDMA is architecturally different. Rather than consuming the CPU for a bulk transfer, HDMA fires once per H-Blank (at the end of each scanline), reading a small amount of data from a table in RAM and writing it to PPU registers. This is how SNES games achieve per-scanline raster effects: color gradient backgrounds, Mode 7 affine parameter updates, window position animations. The HDMA table format uses a "line count" byte followed by register data; the emulator must process this table pointer once per scanline during the H-Blank period in correct synchronization with the PPU's scanline counter.

---

## 3. High-Performance Optimization & Failure Modes

### Cache-Optimal Page Table Layout

The page table's performance characteristics are dominated by cache behavior. With 4096 entries of 40 bytes each (two 8-byte pointers, two 8-byte function pointers, one 8-byte context pointer, plus padding to alignment), the full SNES page table occupies 160 KB. That does not fit in L1 cache (typically 32–64 KB), nor in L2 cache on some microarchitectures. If the emulated code accesses address space regions that scatter across many non-contiguous pages — common in ROM-intensive games that jump between code, data, and MMIO heavily — the memory system dispatcher will suffer L2 or even L3 cache misses, adding 10–40 ns per access.

The mitigation is page table compression. Rather than a flat array indexed by the full page number, use a two-level structure where the first level (indexed by the top N bits) holds second-level pointers. Pages that map to identical behaviors — large ROM regions where every page points into a contiguous host buffer — can share a second-level entry, keeping the working set of live second-level entries small enough to stay resident in L1. The trade-off is an extra indirection for every access; whether this wins depends on the cache miss rate of the flat layout on the specific workload.

An alternative that many production emulators use is the **JIT write-barrier table**: a second, parallel array of single bytes (one per page), each encoding whether the page is writable and whether it contains JIT-compiled code. When the JIT recompiles a guest basic block and stores native code into a host buffer, it marks the corresponding guest pages in this table. Any write to those pages invalidates the cached translation. This keeps the byte-granularity invalidation data in a compact 4096-byte structure that fits trivially in L1 cache.

### Open Bus and Floating Bus Behavior

A subtle but game-breaking failure mode in emulators that model memory as fully populated is the absence of open-bus behavior. On real hardware, the CPU's data bus retains the last value driven onto it after a cycle completes. When the CPU reads from an unmapped address (one where no hardware asserts a value onto the data bus), it reads whatever value was last driven — typically the high byte of the address or the last instruction byte, depending on the CPU revision and bus capacitance. Some SNES games, particularly those doing indirect vector reads or hardware detection routines, expect specific open-bus return values. An emulator that returns `0x00` or `0xFF` from unmapped reads will fail these tests.

The correct implementation maintains a `uint8_t last_bus_value` field in the memory system state, updated after every CPU data bus cycle with the byte that was driven. Unmapped reads return `last_bus_value` without modification. For the SNES specifically, the MDR (Memory Data Register) behavior is documented in detail in Anomie's register doc and must be followed precisely for the handful of games that depend on it.

### VRAM Access Timing Violations

A category of emulation bugs that is particularly difficult to detect through normal testing involves VRAM timing. On the real SNES PPU, VRAM is on the PPU's private bus. The CPU can only access it through the port registers `$2118`/`$2119`/`$2139`/`$213A`, and even then only during specific PPU states. During active rendering (H-Active of non-V-Blank scanlines), the PPU has exclusive access to VRAM, and CPU writes are either ignored or corrupted by the hardware. Emulators that allow unrestricted VRAM writes at any time will display correctly for most commercial software (which correctly gates VRAM access to V-Blank) but will misemulate the pathological behavior that some accuracy test ROMs specifically probe.

The timing-accurate solution tracks the PPU's current state (pre-render, active, H-Blank, V-Blank) with a master-clock counter and gates VRAM access in `ppu_write` based on that state:

```c
typedef enum {
    PPU_STATE_VBLANK,
    PPU_STATE_HBLANK,
    PPU_STATE_ACTIVE,
    PPU_STATE_PRERENDER
} PPURenderState;

/* Approximate SNES master clock cycles per scanline: 1364. 
   V-Blank starts at scanline 225 (NTSC), runs to 262.
   H-Blank occupies roughly the last 212 cycles of each scanline. */
#define MASTER_CYCLES_PER_LINE  1364
#define HBLANK_START_CYCLE       1096
#define VBLANK_START_LINE        225
#define TOTAL_LINES_NTSC         262

static inline PPURenderState ppu_render_state(uint32_t master_cycle) {
    uint32_t line  = (master_cycle / MASTER_CYCLES_PER_LINE) % TOTAL_LINES_NTSC;
    uint32_t hcyc  =  master_cycle % MASTER_CYCLES_PER_LINE;

    if (line >= VBLANK_START_LINE)      return PPU_STATE_VBLANK;
    if (hcyc >= HBLANK_START_CYCLE)     return PPU_STATE_HBLANK;
    return PPU_STATE_ACTIVE;
}

/* Gated VRAM write: silently drops writes during active rendering. */
void ppu_vram_write_gated(PPUState *ppu, uint32_t master_cycle,
                           uint16_t reg, uint8_t val) {
    PPURenderState state = ppu_render_state(master_cycle);
    if (state == PPU_STATE_ACTIVE) return;  /* VRAM locked during active display */
    ppu_write(ppu, reg, val);
}
```

### DMA and CPU Interleaving on HDMA

HDMA is processed during H-Blank. If game code is simultaneously running in WRAM (which shares the A-Bus with HDMA) and HDMA fires, there is a bus contention scenario. The SNES resolves this by pausing the CPU for HDMA cycles, similar to how GPDMA halts the CPU. Emulators that execute HDMA and CPU cycles in strict sequential order without modeling bus contention will produce correct results for typical games but will fail accuracy tests that measure the exact timing of CPU operations relative to HDMA. The correct approach runs the master clock as the arbiter: for each master clock cycle, the scheduler determines whether the cycle belongs to the CPU, HDMA, GPDMA, or the PPU, and dispatches accordingly.

### Practical Validation Against Hardware

The authoritative way to validate an emulator's memory system is to run published test ROMs against known hardware captures. For the SNES, Blargg's test ROMs and the more recent higan test suite cover hundreds of edge cases including open-bus reads, VRAM timing, MBC interaction, and DMA behavior. Each test ROM produces a visual or memory-based pass/fail result that can be automated in a CI pipeline. For the Game Boy, the `mooneye-gb` test suite provides exhaustive coverage of MBC1 through MBC5, timing edge cases, and power-on state.

A practical CI workflow compiles the emulator, runs each test ROM headlessly with a fixed number of emulated cycles or until the test ROM writes a result byte to a known memory address, reads the pass/fail status from guest RAM, and reports failures. This workflow catches regressions in memory system correctness with the same rigor applied to any other software system: automatically, against a defined ground truth, on every commit.

```c
/* Headless test harness: run test ROM until it signals completion.
   Many test ROMs signal pass/fail by writing 0x01 (pass) or 0x00 (fail)
   to a fixed address, or halt the CPU with specific register values. */
int run_test_rom(const char *rom_path, uint32_t max_cycles, uint16_t result_addr) {
    uint8_t rom_data[1024 * 1024];
    uint8_t wram[8192];
    MemMap  map;
    MBC1State mbc;

    memset(&map,  0, sizeof(map));
    memset(&mbc,  0, sizeof(mbc));
    memset(wram,  0, sizeof(wram));

    FILE *f = fopen(rom_path, "rb");
    if (!f) return -1;
    size_t rom_size = fread(rom_data, 1, sizeof(rom_data), f);
    fclose(f);

    mbc.rom      = rom_data;
    mbc.rom_size = (uint32_t)rom_size;
    mbc.rom_bank_lo = 1;

    /* Map fixed ROM bank 0 at 0x0000. */
    mem_map_ram(&map, 0x0000, rom_data, ROM_BANK_SIZE, 0);
    /* Map initial switchable bank at 0x4000. */
    mbc1_remap(&map, &mbc);
    /* Map Work RAM at 0xC000. */
    mem_map_ram(&map, 0xC000, wram, sizeof(wram), 1);

    /* Execute guest CPU for up to max_cycles (CPU core not shown). */
    /* ... cpu_run(&cpu, &map, max_cycles) ... */

    return mem_read8(&map, result_addr);
}
```

The memory system of an emulator is not auxiliary infrastructure — it is the medium through which every other subsystem communicates, the fabric that makes the lie of emulation hold together. Building it correctly, efficiently, and with rigorous attention to the behavioral contracts of the original hardware is the difference between a curiosity and an emulator that games actually trust with their state.
