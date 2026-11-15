# Lesson 5: Bootloaders, Flash Memory Management, Over-the-Air Updates

## 1. First-Principles Intuition & Invariants

When a microcontroller or embedded processor emerges from reset, it possesses no comprehension of its purpose, no awareness of the application firmware awaiting execution in non-volatile memory, and no capacity to validate whether that firmware remains uncorrupted or authentic. The bootloader occupies this critical vacuum between hardware initialization and application execution, serving as the system's first software guardian and the arbiter of trust. Unlike desktop or server systems where BIOS, UEFI, or bootloaders operate within rich ecosystems of standardized interfaces and abundant memory, embedded bootloaders must perform their duties within punishing resource constraints—often fewer than 16 kilobytes of code space, executing from internal SRAM before external DRAM controllers initialize, and making irreversible decisions about system security with no opportunity for human intervention.

The bootloader's responsibilities extend far beyond simple program loading. It must traverse a multi-stage boot sequence that begins with immutable ROM code burned into silicon at fabrication time, progresses through increasingly complex validation and initialization stages, and culminates in a controlled handoff to application firmware that may reside tens of megabytes away in external flash memory. Each stage operates under progressively relaxed constraints as more system resources become available, yet each stage also introduces new attack surfaces and failure modes that subsequent stages must either mitigate or accept as inherited risk.

Flash memory management represents the bootloader's most intricate physical challenge. NAND and NOR flash technologies impose fundamentally different programming constraints than the byte-addressable RAM that dominates software engineering intuition. Whereas SRAM and DRAM permit arbitrary read-modify-write operations at byte granularity, flash memory demands block erasure before reprogramming, exhibits finite write endurance measured in thousands or millions of cycles per physical cell, and suffers from bit error rates that increase with age and cumulative program-erase cycles. The bootloader must navigate these constraints while presenting a coherent storage abstraction to higher-level firmware update mechanisms, balancing wear across physical blocks to maximize device lifespan, and maintaining atomic update semantics despite the reality that power failures can interrupt multi-second erase operations with no hardware-level transaction support.

Over-the-air update mechanisms layer additional complexity atop this foundation. A field-deployed device receiving firmware updates over cellular, Wi-Fi, or Bluetooth Low Energy networks must download potentially megabytes of data through unreliable transport protocols, validate cryptographic signatures without exposing signing keys to extraction, and perform atomic switchover to new firmware images while preserving rollback capability if the new image proves defective. The bootloader architect must reconcile conflicting requirements: update images should be encrypted to prevent intellectual property theft, yet decryption requires symmetric keys stored somewhere in non-volatile memory; signature verification demands public-key cryptography, yet RSA or elliptic curve operations consume milliseconds of CPU time and kilobytes of code space; A/B partition schemes enable safe rollback but consume double the flash capacity of single-image designs.

The invariants governing robust bootloader design emerge from these tensions. First, the principle of immutable trust anchors: every secure boot chain must root its trust in code or keys that attackers cannot modify, typically ROM burned at silicon fabrication or one-time-programmable fuses. Second, the principle of monotonic version enforcement: firmware updates must advance a hardware-backed version counter that prevents adversaries from reverting to older images containing known vulnerabilities. Third, the principle of atomic state transitions: the system must never enter a partially-updated state where corruption or power loss leaves the device unbootable; this demands either full-image validation before activation or wear-leveling schemes that maintain multiple valid images simultaneously. Fourth, the principle of fail-safe defaults: when signature verification fails, version checks detect rollback attacks, or corruption detection algorithms trigger, the bootloader must halt execution rather than blindly launching potentially compromised code.

These invariants manifest differently across the embedded landscape. A safety-critical automotive ECU performing over-the-air updates at 70 miles per hour must guarantee that failed updates never brick the vehicle, demanding redundant boot partitions and elaborate watchdog timer configurations. A battery-powered IoT sensor node might accept weaker security guarantees in exchange for milliwatt-level power budgets during update reception, using lightweight hash functions instead of public-key cryptography. A high-reliability industrial controller might forego over-the-air updates entirely, requiring physical access and JTAG connections to ensure that only authorized personnel with physical custody can modify firmware. Yet beneath this diversity, the fundamental tension persists: balancing security, reliability, resource efficiency, and field serviceability within the physics of flash memory and the economics of embedded hardware.

Understanding bootloaders requires confronting the reality that most catastrophic embedded failures originate not in application bugs but in boot sequence defects. A corrupted bootloader renders the device unrecoverable without specialized hardware tools. An improperly configured memory protection unit allows application code to overwrite bootloader regions. A race condition in the flash driver causes wear-leveling metadata corruption after a power-cycle at precisely the wrong millisecond. These failures defy traditional software debugging because they occur before logging subsystems initialize, before UART consoles activate, and often before stack pointers point to valid RAM. The bootloader engineer must cultivate paranoia bordering on obsession: every register write must be verified, every flash sector must be checksummed, every control flow decision must assume adversarial input, and every state machine must include explicit error states even when "that can't possibly happen."

The following sections dissect the mechanisms through which robust bootloaders achieve these guarantees, beginning with the multi-stage boot sequence that initializes hardware from unknown reset states, progressing through linker script architectures that partition code and data across heterogeneous memory regions, examining flash wear-leveling algorithms that extend device lifespan, and culminating in A/B partition schemes and rollback mechanisms that enable safe field updates. Each section balances theoretical models against silicon-level implementation constraints, providing complete register configurations, executable code fragments, and oscilloscope-verifiable timing diagrams that translate abstract security principles into working embedded systems.


## 2. Core Architecture & Mechanics

### Multi-Stage Boot Sequence: From Silicon Reset to Application Handoff

The boot sequence begins at the moment transistors stabilize following power-on or external reset assertion. On ARM Cortex-M processors, hardware loads the initial stack pointer from flash address `0x00000000` and the reset vector from address `0x00000004`, then begins instruction fetch from that vector address. This seemingly trivial operation embeds profound implications: the processor unconditionally trusts whatever values reside at these addresses, executing them with maximum privilege before any software-based security mechanisms activate. Attackers who gain write access to these locations achieve complete system compromise, motivating the immutable ROM bootloader pattern deployed in modern secure microcontrollers.

The STM32H7 series exemplifies contemporary multi-stage architecture. Upon reset, the CPU begins executing immutable ROM code burned into silicon at fabrication time, residing at address `0x1FF00000` in the system memory region. This first-stage bootloader, typically 32 to 64 kilobytes, implements minimal functionality: it samples dedicated boot configuration pins (`BOOT0`, `BOOT1`) to determine whether execution should proceed to user flash at `0x08000000`, system memory bootloader at `0x1FF00000`, or embedded SRAM at `0x20000000` for development. The ROM bootloader cannot be corrupted by software bugs or malicious attacks because it exists in mask ROM rather than field-programmable memory, establishing an immutable trust anchor for subsequent stages.

If boot pins indicate user flash execution, the ROM bootloader validates a second-stage bootloader residing in the first sectors of flash memory. On secure-boot-enabled devices like the STM32H7B3, this validation involves computing a SHA-256 hash over the secondary bootloader image and comparing against a hash stored in one-time-programmable flash regions or efuses. The ROM bootloader also verifies that cryptographic signatures embedded in the flash image match public keys provisioned during manufacturing. Only after these checks succeed does the ROM code transfer control to address `0x08000000`, where the second-stage bootloader begins execution.

The second-stage bootloader operates under relaxed constraints compared to ROM code. With validated execution authority and access to the full flash address space, it performs hardware initialization tasks impossible in ROM: configuring the memory protection unit (MPU) to isolate bootloader regions from application access, initializing external SDRAM controllers that expand available memory from kilobytes to megabytes, and activating peripheral clocks for UARTs, SPI controllers, and USB interfaces that enable field updates. A typical second-stage bootloader on ARM Cortex-M7 allocates its first 64 kilobytes of flash to bootloader code and reserves the subsequent 128 kilobytes for update staging buffers, leaving the remainder for dual application images in an A/B partition scheme.

Before transferring control to application firmware, the second-stage bootloader must solve a critical problem: how to cleanly transition execution from bootloader context to application context when both reside in the same address space and share peripheral hardware. The naive approach—jumping directly to the application's reset vector—fails catastrophically because the bootloader has already configured stack pointers, vector tables, and peripheral registers that the application expects to initialize itself. The correct handoff sequence involves five critical steps executed in strict order.

First, the bootloader disables all interrupt sources to prevent handlers from executing during the context switch. On ARM Cortex-M, this requires writing to the NVIC (Nested Vectored Interrupt Controller) ICER registers to clear all pending interrupt enables:

```c
// Disable all interrupts in NVIC
for (uint32_t i = 0; i < 8; i++) {
    NVIC->ICER[i] = 0xFFFFFFFF;  // Clear all enables
    NVIC->ICPR[i] = 0xFFFFFFFF;  // Clear all pending flags
}
```

Second, the bootloader resets critical peripherals to their power-on default states. Leaving UART baud rate generators or SPI clock dividers configured causes subtle bugs when application code re-initializes them assuming reset values:

```c
// Reset UART1 peripheral to default state
RCC->APB2RSTR |= RCC_APB2RSTR_USART1RST;
RCC->APB2RSTR &= ~RCC_APB2RSTR_USART1RST;
```

Third, the bootloader relocates the vector table to point to the application's interrupt vectors. ARM processors store the Vector Table Offset Register (VTOR) at address `0xE000ED08`, which must be updated to the application's base address:

```c
// Relocate vector table to application base
#define APP_BASE_ADDRESS 0x08040000
SCB->VTOR = APP_BASE_ADDRESS;
```

Fourth, the bootloader loads the application's initial stack pointer from the first word of the application image, then loads the application's reset vector from the second word. This mirrors the hardware reset sequence but occurs under software control:

```c
uint32_t app_stack_ptr = *(volatile uint32_t *)APP_BASE_ADDRESS;
uint32_t app_reset_vector = *(volatile uint32_t *)(APP_BASE_ADDRESS + 4);
```

Fifth and finally, the bootloader sets the main stack pointer register and performs an absolute jump to the application reset handler. On ARM Cortex-M, this requires inline assembly because C provides no standardized way to directly manipulate the stack pointer:

```c
__asm volatile (
    "MSR MSP, %0\n"      // Load main stack pointer
    "BX %1\n"            // Branch to reset vector
    : : "r" (app_stack_ptr), "r" (app_reset_vector)
);
```

This handoff sequence must execute atomically with interrupts disabled because a timer interrupt firing between vector table relocation and stack pointer update would cause the processor to load an interrupt handler address from the new vector table while still using the old stack pointer, resulting in stack corruption and immediate hard fault.

### Linker Script Architecture: Memory Region Partitioning and Section Placement

Linker scripts serve as the bootloader architect's primary tool for enforcing memory isolation between boot stages and application code. Unlike application firmware that typically occupies contiguous address ranges, bootloader systems must partition flash and RAM into protected regions with precisely controlled boundaries, alignment requirements, and access permissions. The GNU linker script language, though syntactically archaic, provides the expressive power necessary to encode these constraints as compile-time guarantees.

A production-grade bootloader linker script begins by defining memory regions corresponding to physical hardware layout. The `MEMORY` directive establishes named regions with starting addresses and lengths that match the microcontroller's memory map:

```ld
MEMORY
{
    ROM_BOOT (rx)   : ORIGIN = 0x08000000, LENGTH = 64K
    ROM_APP_A (rx)  : ORIGIN = 0x08010000, LENGTH = 256K
    ROM_APP_B (rx)  : ORIGIN = 0x08050000, LENGTH = 256K
    ROM_CONFIG (r)  : ORIGIN = 0x08090000, LENGTH = 4K
    RAM (rwx)       : ORIGIN = 0x20000000, LENGTH = 128K
    RAM_SHARED (rw) : ORIGIN = 0x20020000, LENGTH = 4K
}
```

This configuration reserves the first 64 kilobytes of flash for bootloader code (`ROM_BOOT`), allocates two 256-kilobyte slots for A/B application images, and dedicates 4 kilobytes to persistent configuration parameters like boot counters and update flags. The shared RAM region at `0x20020000` provides a communication mechanism for passing parameters from bootloader to application without requiring flash writes.

Section placement directives map compiler-generated sections to these memory regions while enforcing alignment constraints critical for flash programming. Flash controllers typically require that write operations target aligned boundaries—often 8-byte or 16-byte alignment—and that erase operations target entire 2-kilobyte or 4-kilobyte sectors. The linker script encodes these constraints:

```ld
SECTIONS
{
    .boot_vectors :
    {
        . = ALIGN(8);
        KEEP(*(.boot_vectors))
        . = ALIGN(8);
    } > ROM_BOOT

    .boot_text :
    {
        . = ALIGN(8);
        *(.boot_text)
        *(.boot_text.*)
        . = ALIGN(8);
    } > ROM_BOOT

    .boot_rodata :
    {
        . = ALIGN(8);
        *(.boot_rodata)
        *(.boot_rodata.*)
        . = ALIGN(8);
    } > ROM_BOOT

    .boot_data :
    {
        . = ALIGN(8);
        _boot_data_load = LOADADDR(.boot_data);
        _boot_data_start = .;
        *(.boot_data)
        *(.boot_data.*)
        _boot_data_end = .;
        . = ALIGN(8);
    } > RAM AT > ROM_BOOT
}
```

The `.boot_data` section demonstrates a critical technique: the `AT > ROM_BOOT` directive stores initialized data in flash while the `> RAM` destination specifies that this data resides in RAM at runtime. The bootloader's startup code must explicitly copy data from `_boot_data_load` (flash address) to `_boot_data_start` (RAM address) before accessing global variables:

```c
extern uint32_t _boot_data_load[];
extern uint32_t _boot_data_start[];
extern uint32_t _boot_data_end[];

void bootloader_copy_data(void) {
    uint32_t *src = _boot_data_load;
    uint32_t *dst = _boot_data_start;
    while (dst < _boot_data_end) {
        *dst++ = *src++;
    }
}
```

Application image sections require additional metadata to support integrity checking and version comparison. The linker script embeds structured headers immediately following the vector table:

```ld
.app_header : ALIGN(8)
{
    KEEP(*(.app_header))
    LONG(ABSOLUTE(_app_text_start));
    LONG(ABSOLUTE(_app_text_end));
    LONG(ABSOLUTE(_app_data_start));
    LONG(ABSOLUTE(_app_data_end));
} > ROM_APP_A
```

This header enables the bootloader to locate application code and data boundaries at runtime without hardcoding addresses, supporting position-independent validation algorithms. The `LONG()` directive emits 32-bit absolute addresses that the bootloader reads to compute CRC32 checksums over the entire image.

Memory protection unit (MPU) configuration depends critically on linker-script-defined boundaries. ARM Cortex-M7 MPU regions must be naturally aligned and sized as powers of two, constraints that the linker script enforces through careful section ordering:

```ld
.mpu_bootloader : ALIGN(64K)
{
    _bootloader_mpu_start = .;
    *(.boot_text)
    *(.boot_rodata)
    . = ALIGN(64K);
    _bootloader_mpu_end = .;
} > ROM_BOOT
```

The bootloader's MPU initialization code uses these linker-defined symbols to configure region protection:

```c
extern uint32_t _bootloader_mpu_start[];
extern uint32_t _bootloader_mpu_end[];

void bootloader_configure_mpu(void) {
    uint32_t region_size = (uint32_t)_bootloader_mpu_end - 
                          (uint32_t)_bootloader_mpu_start;
    
    // Compute log2(region_size) - 1 for SIZE field
    uint32_t size_field = 30 - __builtin_clz(region_size);
    
    MPU->RBAR = (uint32_t)_bootloader_mpu_start | MPU_RBAR_VALID_Msk | 0;
    MPU->RASR = MPU_RASR_ENABLE_Msk |
                (size_field << MPU_RASR_SIZE_Pos) |
                (0x06 << MPU_RASR_AP_Pos) |  // Read-only, privileged
                MPU_RASR_XN_Msk;             // Execute never
}
```

This configuration marks the bootloader region as read-only even to privileged code, preventing corruption from runaway pointers or stack overflows in application code.

### Flash Memory Architecture: NOR vs NAND Physical Constraints

Flash memory technologies impose fundamentally different operational constraints that bootloader designs must accommodate at the lowest levels. NOR flash provides byte-addressable read access with typical random read latencies of 70 to 150 nanoseconds, enabling direct code execution through memory-mapped interfaces without copying to RAM. Write operations require explicit programming commands and occur at granularities of 8, 16, or 32 bits depending on bus width, with typical programming times of 10 to 300 microseconds per word. Critically, NOR flash cells can be programmed from logical `1` to logical `0` bit-by-bit, but resetting bits from `0` to `1` requires block erasure affecting 64 kilobytes to 256 kilobytes simultaneously, with erase times spanning 0.5 to 3 seconds.

NAND flash trades NOR's random access capability for higher density and lower cost, storing data in pages of 2048 or 4096 bytes that must be read or written atomically. NAND prohibits direct code execution; firmware must reside in executable memory like SRAM or NOR flash while NAND serves purely as storage. Page programming takes 200 to 700 microseconds, while block erasure (affecting 64 or 128 pages) requires 2 to 5 milliseconds. NAND flash exhibits higher raw bit error rates than NOR—typically 1 bit error per 10^7 to 10^8 read operations on fresh devices—necessitating error correction codes (ECC) that add overhead bytes to every page.

The bootloader's flash driver must abstract these differences while preserving their physical implications. For NOR flash, the driver implements a state machine that sequences through unlock, command write, address write, and data write phases required by Common Flash Interface (CFI) protocols. The AMD/Spansion command sequence illustrates the complexity:

```c
void nor_flash_program_word(uint32_t address, uint16_t data) {
    volatile uint16_t *flash = (volatile uint16_t *)0x08000000;
    
    flash[0x555] = 0xAA;    // Unlock cycle 1
    flash[0x2AA] = 0x55;    // Unlock cycle 2
    flash[0x555] = 0xA0;    // Program command
    
    volatile uint16_t *target = (volatile uint16_t *)address;
    *target = data;
    
    // Poll data toggle bit until programming completes
    uint16_t status1, status2;
    do {
        status1 = *target;
        status2 = *target;
    } while ((status1 ^ status2) & 0x40);  // DQ6 toggles while busy
    
    if ((status2 & 0x20) && ((status2 ^ *target) & 0x80)) {
        // Programming failed, reset required
        flash[0x555] = 0xF0;
    }
}
```

This code implements AMD's data toggle algorithm, polling bit 6 which oscillates while programming circuits operate. Bit 5 indicates timeout errors requiring explicit reset commands. The bootloader must execute this polling loop with interrupts disabled because servicing an interrupt mid-program could exceed the programming window, corrupting the cell.

Block erasure demands even more careful orchestration because erase times span hundreds of milliseconds to seconds during which the processor cannot fetch instructions from the erasing flash bank. Multi-bank flash architectures solve this by allowing code execution from one bank while erasing another:

```c
typedef enum {
    FLASH_BANK_1 = 0,
    FLASH_BANK_2 = 1
} flash_bank_t;

void nor_flash_erase_sector(flash_bank_t bank, uint32_t sector) {
    volatile uint16_t *flash = (volatile uint16_t *)0x08000000;
    uint32_t sector_address = (bank == FLASH_BANK_1) ? 
                              0x08000000 : 0x08080000;
    sector_address += (sector * 0x10000);  // 64KB sectors
    
    // Ensure code executes from opposite bank
    if (bank == FLASH_BANK_1) {
        __attribute__((section(".bank2_code")))
        void erase_sequence(void) {
            flash[0x555] = 0xAA;
            flash[0x2AA] = 0x55;
            flash[0x555] = 0x80;
            flash[0x555] = 0xAA;
            flash[0x2AA] = 0x55;
            ((volatile uint16_t *)sector_address)[0] = 0x30;
        }
        erase_sequence();
    }
    
    // Poll status with timeout
    uint32_t timeout = 3000000;  // 3 second timeout
    volatile uint16_t *status_addr = (volatile uint16_t *)sector_address;
    while (timeout-- > 0) {
        uint16_t status = *status_addr;
        if ((status & 0x80) == 0x80) break;  // DQ7 high when complete
        if (status & 0x20) {  // DQ5 set indicates timeout
            flash[0x555] = 0xF0;  // Reset command
            return;
        }
    }
}
```

NAND flash drivers must implement bad block management because NAND manufacturers guarantee only that the first block contains no defects; subsequent blocks may ship defective or develop defects during service life. The bootloader maintains a bad block table (BBT) in reserved pages, scanning for factory-marked bad blocks (indicated by non-0xFF bytes in the first page's spare area) during first boot:

```c
#define NAND_PAGE_SIZE 2048
#define NAND_SPARE_SIZE 64
#define NAND_PAGES_PER_BLOCK 64

typedef struct {
    uint16_t physical_block;
    uint8_t is_bad;
} block_table_entry_t;

block_table_entry_t bad_block_table[2048];

void nand_scan_bad_blocks(void) {
    for (uint16_t block = 0; block < 2048; block++) {
        uint32_t page_address = block * NAND_PAGES_PER_BLOCK;
        
        uint8_t spare_area[NAND_SPARE_SIZE];
        nand_read_spare(page_address, spare_area);
        
        // Check bad block marker at spare byte 0
        if (spare_area[0] != 0xFF) {
            bad_block_table[block].is_bad = 1;
        } else {
            bad_block_table[block].is_bad = 0;
        }
        bad_block_table[block].physical_block = block;
    }
}
```

Error correction codes (ECC) protect against bit errors that accumulate as NAND cells age. BCH (Bose-Chaudhuri-Hocquenghem) codes correct multiple bit errors per page using syndrome calculation implemented in hardware ECC engines or software:

```c
#define BCH_ECC_BYTES 13  // Corrects 8-bit errors per 512-byte chunk

void nand_write_page_with_ecc(uint32_t page_addr, const uint8_t *data) {
    uint8_t ecc_code[BCH_ECC_BYTES];
    
    // Enable hardware ECC engine
    NAND_ECC->CR = NAND_ECC_CR_ENABLE | NAND_ECC_CR_BCH8;
    
    // Write page data, ECC calculated automatically
    for (uint16_t i = 0; i < NAND_PAGE_SIZE; i++) {
        NAND_DATA_REG = data[i];
    }
    
    // Read generated ECC from hardware
    for (uint8_t i = 0; i < BCH_ECC_BYTES; i++) {
        ecc_code[i] = NAND_ECC->DATA[i];
    }
    
    // Write ECC to spare area
    nand_write_spare(page_addr, ecc_code, BCH_ECC_BYTES);
}
```

Reading requires comparing stored ECC against recalculated ECC to detect and correct errors:

```c
typedef enum {
    ECC_NO_ERROR = 0,
    ECC_CORRECTED = 1,
    ECC_UNCORRECTABLE = 2
} ecc_status_t;

ecc_status_t nand_read_page_with_ecc(uint32_t page_addr, uint8_t *data) {
    uint8_t stored_ecc[BCH_ECC_BYTES];
    
    // Read page data
    NAND_ECC->CR = NAND_ECC_CR_ENABLE | NAND_ECC_CR_BCH8;
    for (uint16_t i = 0; i < NAND_PAGE_SIZE; i++) {
        data[i] = NAND_DATA_REG;
    }
    
    // Read stored ECC from spare area
    nand_read_spare(page_addr, stored_ecc, BCH_ECC_BYTES);
    
    // Compare against hardware-calculated ECC
    uint32_t error_count = NAND_ECC->SR & NAND_ECC_SR_ERROR_MASK;
    
    if (error_count == 0) {
        return ECC_NO_ERROR;
    } else if (error_count <= 8) {
        // Hardware corrects errors automatically
        return ECC_CORRECTED;
    } else {
        return ECC_UNCORRECTABLE;
    }
}
```

### Wear Leveling: Flash Endurance Management Algorithms

Flash memory cells physically degrade with each program-erase cycle as charge trapping in gate oxides shifts threshold voltages. Consumer-grade NOR flash typically withstands 100,000 cycles per block before retention failures appear, while industrial-grade parts reach 1 million cycles. NAND flash exhibits lower endurance—10,000 to 100,000 cycles for multi-level cell (MLC) NAND, 100,000 cycles for single-level cell (SLC)—but benefits from higher density that enables more aggressive wear leveling.

Static wear leveling distributes writes uniformly across all blocks regardless of logical access patterns. The bootloader maintains a block usage table tracking erase counts for every physical block:

```c
typedef struct {
    uint32_t erase_count;
    uint16_t logical_block;
    uint8_t status;  // FREE, ALLOCATED, BAD
} physical_block_info_t;

physical_block_info_t block_info[2048];

uint16_t wear_level_allocate_block(uint16_t logical_block) {
    // Find physical block with minimum erase count
    uint32_t min_erase_count = UINT32_MAX;
    uint16_t min_block = 0;
    
    for (uint16_t i = 0; i < 2048; i++) {
        if (block_info[i].status == BLOCK_FREE &&
            block_info[i].erase_count < min_erase_count) {
            min_erase_count = block_info[i].erase_count;
            min_block = i;
        }
    }
    
    // Allocate block and update metadata
    block_info[min_block].logical_block = logical_block;
    block_info[min_block].status = BLOCK_ALLOCATED;
    block_info[min_block].erase_count++;
    
    return min_block;
}
```

Dynamic wear leveling improves upon static algorithms by relocating cold data—blocks written once during manufacturing and rarely modified—to high-cycle physical blocks, freeing low-cycle blocks for hot data. The bootloader periodically scans for erase count imbalances exceeding configurable thresholds:

```c
void wear_level_rebalance(void) {
    uint32_t max_erase_count = 0;
    uint32_t min_erase_count = UINT32_MAX;
    uint16_t max_block = 0, min_block = 0;
    
    // Find blocks with maximum and minimum erase counts
    for (uint16_t i = 0; i < 2048; i++) {
        if (block_info[i].status != BLOCK_BAD) {
            if (block_info[i].erase_count > max_erase_count) {
                max_erase_count = block_info[i].erase_count;
                max_block = i;
            }
            if (block_info[i].erase_count < min_erase_count) {
                min_erase_count = block_info[i].erase_count;
                min_block = i;
            }
        }
    }
    
    // If imbalance exceeds threshold, swap contents
    if ((max_erase_count - min_erase_count) > WEAR_LEVEL_THRESHOLD) {
        uint8_t temp_buffer[NAND_PAGE_SIZE * NAND_PAGES_PER_BLOCK];
        
        // Copy min block to temp buffer
        for (uint16_t page = 0; page < NAND_PAGES_PER_BLOCK; page++) {
            nand_read_page(min_block * NAND_PAGES_PER_BLOCK + page,
                          &temp_buffer[page * NAND_PAGE_SIZE]);
        }
        
        // Copy max block to min block
        for (uint16_t page = 0; page < NAND_PAGES_PER_BLOCK; page++) {
            uint8_t page_data[NAND_PAGE_SIZE];
            nand_read_page(max_block * NAND_PAGES_PER_BLOCK + page, page_data);
            nand_write_page(min_block * NAND_PAGES_PER_BLOCK + page, page_data);
        }
        
        // Copy temp buffer to max block
        nand_erase_block(max_block);
        for (uint16_t page = 0; page < NAND_PAGES_PER_BLOCK; page++) {
            nand_write_page(max_block * NAND_PAGES_PER_BLOCK + page,
                           &temp_buffer[page * NAND_PAGE_SIZE]);
        }
        
        // Swap logical mappings
        uint16_t temp_logical = block_info[min_block].logical_block;
        block_info[min_block].logical_block = block_info[max_block].logical_block;
        block_info[max_block].logical_block = temp_logical;
    }
}
```

This rebalancing occurs during idle periods or scheduled maintenance windows, typically triggered when erase count spread exceeds 1000 cycles. The algorithm trades increased write amplification (two block copies plus one erase) for extended overall device lifespan.

For bootloader-specific scenarios where configuration parameters change infrequently but must persist across power cycles, a simplified circular buffer approach suffices. The bootloader reserves a dedicated flash sector for persistent state and appends new records sequentially:

```c
#define CONFIG_SECTOR_BASE 0x08090000
#define CONFIG_SECTOR_SIZE 0x1000
#define CONFIG_RECORD_SIZE 32

typedef struct {
    uint32_t magic;
    uint32_t version;
    uint32_t crc32;
    uint8_t boot_slot;
    uint8_t rollback_count;
    uint8_t padding[18];
} config_record_t;

void config_write(const config_record_t *record) {
    uint32_t current_addr = CONFIG_SECTOR_BASE;
    
    // Find first free record slot
    while (current_addr < (CONFIG_SECTOR_BASE + CONFIG_SECTOR_SIZE)) {
        uint32_t magic = *(volatile uint32_t *)current_addr;
        if (magic == 0xFFFFFFFF) {
            // Found free slot, program record
            nor_flash_program_buffer(current_addr, (uint8_t *)record,
                                    CONFIG_RECORD_SIZE);
            return;
        }
        current_addr += CONFIG_RECORD_SIZE;
    }
    
    // Sector full, erase and start from beginning
    nor_flash_erase_sector(FLASH_BANK_1, 18);  // Sector 18 is config
    nor_flash_program_buffer(CONFIG_SECTOR_BASE, (uint8_t *)record,
                            CONFIG_RECORD_SIZE);
}
```

Each configuration write consumes 32 bytes of the 4-kilobyte sector, providing 128 updates before triggering erasure. At one update per reboot, this supports 128,000 reboot cycles before the sector reaches 1000 erase cycles, far below endurance limits.

### Secure Boot Chains: Cryptographic Validation and Root of Trust

Secure boot transforms the bootloader from simple initialization code into a cryptographic validation engine that enforces trust chains from immutable ROM through application firmware. The chain begins with a root public key provisioned during manufacturing, stored in one-time-programmable flash or efuses that attackers cannot modify without destroying the device. This public key validates the signature on the second-stage bootloader, which in turn validates application firmware signatures using keys embedded in its own verified image.

RSA signature verification exemplifies the computational intensity secure boot demands. A 2048-bit RSA signature verification requires modular exponentiation $s^e \bmod n$ where $s$ represents the signature, $e$ the public exponent (typically 65537), and $n$ the 2048-bit modulus. Computing this on a 200 MHz Cortex-M7 without hardware acceleration consumes 50 to 150 milliseconds, delaying boot by unacceptable intervals for latency-sensitive systems.

Hardware cryptographic accelerators mitigate this cost. The STM32H7 includes a PKA (Public Key Accelerator) that performs modular exponentiation in dedicated silicon:

```c
typedef struct {
    uint8_t modulus[256];     // 2048-bit RSA modulus
    uint8_t exponent[4];      // Public exponent (typically 65537)
    uint8_t signature[256];   // 2048-bit signature to verify
    uint8_t hash[32];         // SHA-256 hash of signed data
} rsa_verify_params_t;

bool rsa_verify_signature_hw(const rsa_verify_params_t *params) {
    // Enable PKA clock
    RCC->AHB2ENR |= RCC_AHB2ENR_PKAEN;
    
    // Load modulus into PKA RAM
    for (uint16_t i = 0; i < 256; i++) {
        PKA_RAM[PKA_MODULUS_OFFSET + i] = params->modulus[i];
    }
    
    // Load exponent
    for (uint8_t i = 0; i < 4; i++) {
        PKA_RAM[PKA_EXPONENT_OFFSET + i] = params->exponent[i];
    }
    
    // Load signature
    for (uint16_t i = 0; i < 256; i++) {
        PKA_RAM[PKA_SIGNATURE_OFFSET + i] = params->signature[i];
    }
    
    // Start modular exponentiation
    PKA->CR = PKA_CR_MODE_RSA_VERIFY | PKA_CR_START;
    
    // Wait for completion (typically 10-20ms)
    while (!(PKA->SR & PKA_SR_PROCENDF)) {
        __NOP();
    }
    
    // Read result and compare against hash
    uint8_t result[32];
    for (uint8_t i = 0; i < 32; i++) {
        result[i] = PKA_RAM[PKA_RESULT_OFFSET + 256 - 32 + i];
    }
    
    return memcmp(result, params->hash, 32) == 0;
}
```

This hardware-accelerated verification completes in 10 to 20 milliseconds, reducing boot delay by 80% compared to software implementations. The bootloader invokes this verification before every stage transition:

```c
typedef struct {
    uint32_t magic;
    uint32_t version;
    uint32_t image_size;
    uint8_t sha256_hash[32];
    uint8_t rsa_signature[256];
} image_header_t;

bool verify_application_image(uint32_t image_base) {
    const image_header_t *header = (const image_header_t *)image_base;
    
    // Verify magic number
    if (header->magic != 0x41505021) {  // "APP!"
        return false;
    }
    
    // Compute SHA-256 over image data
    uint8_t computed_hash[32];
    sha256_compute((uint8_t *)(image_base + sizeof(image_header_t)),
                   header->image_size, computed_hash);
    
    // Compare against header hash
    if (memcmp(computed_hash, header->sha256_hash, 32) != 0) {
        return false;
    }
    
    // Verify RSA signature using root public key
    rsa_verify_params_t verify_params = {
        .exponent = {0x01, 0x00, 0x01, 0x00},  // 65537
        .hash = {0},  // Copy computed_hash
        .signature = {0},  // Copy header->rsa_signature
        .modulus = {0}  // Copy from OTP region
    };
    
    memcpy(verify_params.hash, computed_hash, 32);
    memcpy(verify_params.signature, header->rsa_signature, 256);
    otp_read_root_public_key(verify_params.modulus, 256);
    
    return rsa_verify_signature_hw(&verify_params);
}
```

Elliptic curve cryptography (ECC) offers comparable security with smaller key sizes and faster verification. A 256-bit ECDSA signature provides security equivalent to 3072-bit RSA while completing verification in 5 to 10 milliseconds:

```c
typedef struct {
    uint8_t public_key_x[32];  // P-256 curve point X coordinate
    uint8_t public_key_y[32];  // P-256 curve point Y coordinate
    uint8_t signature_r[32];   // ECDSA signature R component
    uint8_t signature_s[32];   // ECDSA signature S component
    uint8_t message_hash[32];  // SHA-256 hash of signed message
} ecdsa_verify_params_t;

bool ecdsa_verify_signature_hw(const ecdsa_verify_params_t *params) {
    // Configure PKA for ECDSA verification on NIST P-256 curve
    PKA->CR = PKA_CR_MODE_ECDSA_VERIFY | PKA_CR_START;
    
    // Load curve parameters (P-256 domain parameters)
    const uint8_t p256_prime[32] = {
        0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x01,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF,
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF
    };
    
    memcpy(&PKA_RAM[PKA_ECC_PRIME_OFFSET], p256_prime, 32);
    memcpy(&PKA_RAM[PKA_ECC_PUBKEY_X_OFFSET], params->public_key_x, 32);
    memcpy(&PKA_RAM[PKA_ECC_PUBKEY_Y_OFFSET], params->public_key_y, 32);
    memcpy(&PKA_RAM[PKA_ECC_SIG_R_OFFSET], params->signature_r, 32);
    memcpy(&PKA_RAM[PKA_ECC_SIG_S_OFFSET], params->signature_s, 32);
    memcpy(&PKA_RAM[PKA_ECC_HASH_OFFSET], params->message_hash, 32);
    
    PKA->CR |= PKA_CR_START;
    
    while (!(PKA->SR & PKA_SR_PROCENDF)) {
        __NOP();
    }
    
    // Check verification result
    return (PKA->SR & PKA_SR_ECDSA_VERIFY_OK) != 0;
}
```

Monotonic version counters prevent rollback attacks where adversaries revert firmware to older versions containing known vulnerabilities. The bootloader maintains a hardware-backed counter in OTP memory that increments with each legitimate update:

```c
#define OTP_VERSION_BASE 0x1FF07000
#define MAX_VERSION_SLOTS 32

uint32_t otp_read_version_counter(void) {
    uint32_t version = 0;
    for (uint8_t i = 0; i < MAX_VERSION_SLOTS; i++) {
        uint32_t slot_value = *(volatile uint32_t *)(OTP_VERSION_BASE + i * 4);
        if (slot_value != 0xFFFFFFFF) {
            version = slot_value;
        }
    }
    return version;
}

bool otp_increment_version(uint32_t new_version) {
    uint32_t current_version = otp_read_version_counter();
    
    if (new_version <= current_version) {
        return false;  // Prevent rollback
    }
    
    // Find next empty OTP slot
    for (uint8_t i = 0; i < MAX_VERSION_SLOTS; i++) {
        uint32_t slot_addr = OTP_VERSION_BASE + i * 4;
        if (*(volatile uint32_t *)slot_addr == 0xFFFFFFFF) {
            // Program new version into OTP
            otp_program_word(slot_addr, new_version);
            return true;
        }
    }
    
    return false;  // OTP exhausted
}
```

Each version update consumes one 32-bit OTP word, providing 32 updates before exhausting the counter. Production systems balance security against OTP capacity by incrementing versions only for security-critical updates, not routine bug fixes.

### A/B Partition Schemes: Atomic Update and Rollback

A/B partition architectures maintain two complete firmware images—designated A and B slots—allowing atomic switchover between versions. At any moment, one slot contains the active running firmware while the other remains inactive, available for update reception. The bootloader selects which slot to boot based on persistent metadata stored in a dedicated configuration region:

```c
typedef enum {
    SLOT_A = 0,
    SLOT_B = 1
} boot_slot_t;

typedef struct {
    uint32_t magic;            // 0x424F4F54 ("BOOT")
    boot_slot_t active_slot;
    boot_slot_t update_slot;
    uint32_t slot_a_version;
    uint32_t slot_b_version;
    uint8_t slot_a_valid;
    uint8_t slot_b_valid;
    uint8_t rollback_count;
    uint8_t max_rollbacks;
    uint32_t crc32;
} boot_metadata_t;

boot_metadata_t *boot_meta = (boot_metadata_t *)0x08090000;
```

The bootloader's slot selection algorithm prioritizes the slot marked active, falling back to the alternate slot if validation fails:

```c
uint32_t select_boot_slot(void) {
    // Verify metadata integrity
    uint32_t computed_crc = crc32_compute((uint8_t *)boot_meta,
                                         sizeof(boot_metadata_t) - 4);
    if (computed_crc != boot_meta->crc32) {
        // Metadata corrupted, default to slot A
        return SLOT_A_BASE_ADDRESS;
    }
    
    // Try active slot first
    uint32_t active_base = (boot_meta->active_slot == SLOT_A) ?
                           SLOT_A_BASE_ADDRESS : SLOT_B_BASE_ADDRESS;
    
    if (verify_application_image(active_base)) {
        boot_meta->rollback_count = 0;  // Reset on successful boot
        return active_base;
    }
    
    // Active slot failed, try alternate
    uint32_t alternate_base = (boot_meta->active_slot == SLOT_A) ?
                              SLOT_B_BASE_ADDRESS : SLOT_A_BASE_ADDRESS;
    
    if (verify_application_image(alternate_base)) {
        boot_meta->rollback_count++;
        
        if (boot_meta->rollback_count < boot_meta->max_rollbacks) {
            boot_meta->active_slot = (boot_meta->active_slot == SLOT_A) ?
                                     SLOT_B : SLOT_A;
            config_write((config_record_t *)boot_meta);
            return alternate_base;
        }
    }
    
    // Both slots invalid, enter recovery mode
    enter_recovery_mode();
    return 0;  // Never reached
}
```

Update reception writes new firmware to the inactive slot without disturbing the running system. The application firmware communicates with the bootloader through a shared RAM region:

```c
#define SHARED_RAM_BASE 0x20020000

typedef enum {
    UPDATE_CMD_NONE = 0,
    UPDATE_CMD_PREPARE = 1,
    UPDATE_CMD_WRITE = 2,
    UPDATE_CMD_FINALIZE = 3,
    UPDATE_CMD_ACTIVATE = 4
} update_command_t;

typedef struct {
    volatile update_command_t command;
    volatile uint32_t offset;
    volatile uint32_t length;
    volatile uint8_t data[4096];
    volatile uint32_t result;
} update_interface_t;

update_interface_t *update_iface = (update_interface_t *)SHARED_RAM_BASE;

void bootloader_process_update_commands(void) {
    switch (update_iface->command) {
    case UPDATE_CMD_PREPARE:
        // Erase inactive slot
        uint32_t inactive_base = (boot_meta->active_slot == SLOT_A) ?
                                 SLOT_B_BASE_ADDRESS : SLOT_A_BASE_ADDRESS;
        for (uint32_t sector = 0; sector < 64; sector++) {
            nor_flash_erase_sector(FLASH_BANK_1, sector + 16);
        }
        update_iface->result = 0;
        break;
        
    case UPDATE_CMD_WRITE:
        // Program data to inactive slot
        uint32_t write_addr = inactive_base + update_iface->offset;
        nor_flash_program_buffer(write_addr, (uint8_t *)update_iface->data,
                                update_iface->length);
        update_iface->result = 0;
        break;
        
    case UPDATE_CMD_FINALIZE:
        // Verify inactive slot
        if (verify_application_image(inactive_base)) {
            boot_meta->update_slot = (boot_meta->active_slot == SLOT_A) ?
                                     SLOT_B : SLOT_A;
            if (boot_meta->update_slot == SLOT_B) {
                boot_meta->slot_b_valid = 1;
            } else {
                boot_meta->slot_a_valid = 1;
            }
            config_write((config_record_t *)boot_meta);
            update_iface->result = 0;
        } else {
            update_iface->result = 1;  // Verification failed
        }
        break;
        
    case UPDATE_CMD_ACTIVATE:
        // Switch active slot and reboot
        boot_meta->active_slot = boot_meta->update_slot;
        config_write((config_record_t *)boot_meta);
        NVIC_SystemReset();
        break;
    }
    
    update_iface->command = UPDATE_CMD_NONE;
}
```

Application code invokes updates through this interface:

```c
bool application_update_firmware(const uint8_t *image, uint32_t size) {
    // Prepare update
    update_iface->command = UPDATE_CMD_PREPARE;
    while (update_iface->command != UPDATE_CMD_NONE) { __NOP(); }
    
    // Write image in 4KB chunks
    for (uint32_t offset = 0; offset < size; offset += 4096) {
        uint32_t chunk_size = (size - offset > 4096) ? 4096 : (size - offset);
        
        memcpy((void *)update_iface->data, &image[offset], chunk_size);
        update_iface->offset = offset;
        update_iface->length = chunk_size;
        update_iface->command = UPDATE_CMD_WRITE;
        
        while (update_iface->command != UPDATE_CMD_NONE) { __NOP(); }
        
        if (update_iface->result != 0) {
            return false;
        }
    }
    
    // Finalize and verify
    update_iface->command = UPDATE_CMD_FINALIZE;
    while (update_iface->command != UPDATE_CMD_NONE) { __NOP(); }
    
    if (update_iface->result != 0) {
        return false;
    }
    
    // Activate new image
    update_iface->command = UPDATE_CMD_ACTIVATE;
    
    // System will reboot into new firmware
    return true;
}
```

Rollback mechanisms protect against defective updates that pass signature verification but exhibit runtime failures. The application firmware implements a health check protocol that marks the current boot successful after completing critical initialization:

```c
void application_mark_boot_successful(void) {
    update_iface->command = UPDATE_CMD_MARK_SUCCESSFUL;
    while (update_iface->command != UPDATE_CMD_NONE) { __NOP(); }
}
```

The bootloader tracks boot attempts and automatically reverts to the previous slot if the application fails to mark itself successful within a timeout:

```c
void bootloader_monitor_application_health(void) {
    uint32_t timeout_ms = 30000;  // 30 second timeout
    uint32_t elapsed_ms = 0;
    
    while (elapsed_ms < timeout_ms) {
        if (update_iface->command == UPDATE_CMD_MARK_SUCCESSFUL) {
            boot_meta->rollback_count = 0;
            config_write((config_record_t *)boot_meta);
            update_iface->command = UPDATE_CMD_NONE;
            return;
        }
        
        delay_ms(100);
        elapsed_ms += 100;
    }
    
    // Timeout expired without success marker, trigger rollback
    boot_meta->active_slot = (boot_meta->active_slot == SLOT_A) ?
                             SLOT_B : SLOT_A;
    boot_meta->rollback_count++;
    config_write((config_record_t *)boot_meta);
    
    NVIC_SystemReset();
}
```

This watchdog-style mechanism ensures that devices remain bootable even when updates introduce critical runtime faults.

### Over-the-Air Update Protocols: Delta Updates and Resume Capability

Transmitting complete firmware images over bandwidth-constrained wireless links consumes excessive energy and time. A 512-kilobyte firmware image transmitted over a 250 kbps Bluetooth Low Energy connection requires 16 seconds of continuous radio operation, draining milliamp-hours from battery-powered devices. Delta updates address this by transmitting only binary differences between old and new firmware versions, reducing update size by 70% to 90% for typical incremental releases.

Binary diff algorithms like bsdiff compute byte-level differences between source and target files, generating patch files containing insertion, deletion, and copy operations:

```c
typedef enum {
    DIFF_OP_COPY = 0,
    DIFF_OP_INSERT = 1,
    DIFF_OP_SKIP = 2
} diff_operation_t;

typedef struct {
    diff_operation_t operation;
    uint32_t length;
    uint32_t source_offset;  // For COPY operations
    uint8_t data[0];         // For INSERT operations
} diff_entry_t;

void apply_binary_diff(const uint8_t *old_image, uint32_t old_size,
                      const uint8_t *patch, uint32_t patch_size,
                      uint8_t *new_image) {
    const uint8_t *patch_ptr = patch;
    uint8_t *output_ptr = new_image;
    
    while (patch_ptr < (patch + patch_size)) {
        const diff_entry_t *entry = (const diff_entry_t *)patch_ptr;
        
        switch (entry->operation) {
        case DIFF_OP_COPY:
            memcpy(output_ptr, &old_image[entry->source_offset], entry->length);
            output_ptr += entry->length;
            patch_ptr += sizeof(diff_entry_t);
            break;
            
        case DIFF_OP_INSERT:
            memcpy(output_ptr, entry->data, entry->length);
            output_ptr += entry->length;
            patch_ptr += sizeof(diff_entry_t) + entry->length;
            break;
            
        case DIFF_OP_SKIP:
            output_ptr += entry->length;
            patch_ptr += sizeof(diff_entry_t);
            break;
        }
    }
}
```

Applying patches requires reading the old firmware image from one slot while writing the reconstructed image to the update slot:

```c
bool ota_apply_delta_update(const uint8_t *patch, uint32_t patch_size) {
    uint32_t old_base = (boot_meta->active_slot == SLOT_A) ?
                        SLOT_A_BASE_ADDRESS : SLOT_B_BASE_ADDRESS;
    uint32_t new_base = (boot_meta->active_slot == SLOT_A) ?
                        SLOT_B_BASE_ADDRESS : SLOT_A_BASE_ADDRESS;
    
    // Allocate buffer for reconstructed image
    uint8_t *new_image = malloc(256 * 1024);
    if (!new_image) return false;
    
    // Apply patch
    apply_binary_diff((uint8_t *)old_base, 256 * 1024,
                     patch, patch_size, new_image);
    
    // Erase and program update slot
    for (uint32_t sector = 0; sector < 64; sector++) {
        nor_flash_erase_sector(FLASH_BANK_2, sector);
    }
    
    for (uint32_t offset = 0; offset < 256 * 1024; offset += 4096) {
        nor_flash_program_buffer(new_base + offset,
                                &new_image[offset], 4096);
    }
    
    free(new_image);
    
    // Verify new image
    return verify_application_image(new_base);
}
```

Resume capability handles interrupted downloads by storing update progress in persistent metadata. The bootloader tracks which chunks have been successfully written:

```c
#define UPDATE_TOTAL_CHUNKS 128
#define UPDATE_CHUNK_SIZE 4096

typedef struct {
    uint32_t magic;
    uint32_t total_size;
    uint16_t chunks_received;
    uint8_t chunk_bitmap[UPDATE_TOTAL_CHUNKS / 8];
    uint32_t crc32;
} update_progress_t;

update_progress_t *update_progress = (update_progress_t *)0x08091000;

bool ota_receive_chunk(uint16_t chunk_index, const uint8_t *data) {
    // Check if chunk already received
    uint16_t byte_index = chunk_index / 8;
    uint8_t bit_mask = 1 << (chunk_index % 8);
    
    if (update_progress->chunk_bitmap[byte_index] & bit_mask) {
        return true;  // Already have this chunk
    }
    
    // Write chunk to update slot
    uint32_t update_base = (boot_meta->active_slot == SLOT_A) ?
                           SLOT_B_BASE_ADDRESS : SLOT_A_BASE_ADDRESS;
    uint32_t chunk_addr = update_base + (chunk_index * UPDATE_CHUNK_SIZE);
    
    nor_flash_program_buffer(chunk_addr, data, UPDATE_CHUNK_SIZE);
    
    // Mark chunk received
    update_progress->chunk_bitmap[byte_index] |= bit_mask;
    update_progress->chunks_received++;
    
    // Update progress metadata
    update_progress->crc32 = crc32_compute((uint8_t *)update_progress,
                                          sizeof(update_progress_t) - 4);
    config_write((config_record_t *)update_progress);
    
    // Check if update complete
    return (update_progress->chunks_received == UPDATE_TOTAL_CHUNKS);
}
```

After connection loss and re-establishment, the update protocol queries the bootloader for missing chunks:

```c
void ota_resume_update(void) {
    for (uint16_t chunk = 0; chunk < UPDATE_TOTAL_CHUNKS; chunk++) {
        uint16_t byte_index = chunk / 8;
        uint8_t bit_mask = 1 << (chunk % 8);
        
        if (!(update_progress->chunk_bitmap[byte_index] & bit_mask)) {
            // Request missing chunk from server
            ota_request_chunk(chunk);
        }
    }
}
```

This resume mechanism reduces the probability of update failure due to transient connectivity issues, critical for devices operating in challenging RF environments.


## 3. High-Performance Optimization & Failure Modes

### Boot Time Optimization: Execution Profiling and Parallelization

Boot latency accumulates across every stage of the boot sequence, from ROM execution through second-stage initialization to application handoff. Safety-critical and real-time systems impose strict boot time budgets—automotive ECUs must complete boot within 200 milliseconds to meet ISO 26262 requirements, while industrial controllers must restore operation within seconds of power restoration to maintain process control. Optimizing boot time requires measuring execution time for every boot stage with microsecond precision, identifying bottlenecks, and parallelizing independent initialization tasks.

The bootloader instruments critical sections using the ARM Cortex-M Data Watchpoint and Trace (DWT) cycle counter, a 32-bit hardware register that increments on every CPU clock cycle:

```c
static inline void dwt_init(void) {
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT = 0;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
}

static inline uint32_t dwt_get_cycles(void) {
    return DWT->CYCCNT;
}

static inline uint32_t dwt_cycles_to_us(uint32_t cycles) {
    return cycles / (SystemCoreClock / 1000000);
}
```

Instrumenting the signature verification path reveals that RSA operations dominate boot time:

```c
void boot_performance_profile(void) {
    uint32_t t0, t1;
    
    t0 = dwt_get_cycles();
    sha256_compute(image_base, image_size, hash_output);
    t1 = dwt_get_cycles();
    printf("SHA-256: %lu us\n", dwt_cycles_to_us(t1 - t0));
    
    t0 = dwt_get_cycles();
    rsa_verify_signature_hw(&verify_params);
    t1 = dwt_get_cycles();
    printf("RSA verify: %lu us\n", dwt_cycles_to_us(t1 - t0));
    
    t0 = dwt_get_cycles();
    flash_copy_to_ram(data_start, data_load, data_size);
    t1 = dwt_get_cycles();
    printf("Data copy: %lu us\n", dwt_cycles_to_us(t1 - t0));
}
```

Typical profiles on a 400 MHz Cortex-M7 reveal:
- SHA-256 over 256 KB: 12 milliseconds
- RSA-2048 verification: 18 milliseconds  
- Flash-to-RAM copy (8 KB): 150 microseconds
- Total signature validation: 30+ milliseconds

Switching from RSA to ECDSA reduces cryptographic overhead by 60%:

```c
t0 = dwt_get_cycles();
ecdsa_verify_signature_hw(&ecdsa_params);
t1 = dwt_get_cycles();
printf("ECDSA verify: %lu us\n", dwt_cycles_to_us(t1 - t0));
// Output: ECDSA verify: 7200 us
```

Further optimization exploits DMA (Direct Memory Access) to parallelize flash-to-RAM copying with CPU-bound cryptographic operations. While the CPU computes SHA-256 hashes, DMA concurrently transfers initialized data from flash to RAM:

```c
void boot_parallel_init(void) {
    // Configure DMA to copy .data section from flash to RAM
    DMA1_Stream0->PAR = (uint32_t)_boot_data_load;
    DMA1_Stream0->M0AR = (uint32_t)_boot_data_start;
    DMA1_Stream0->NDTR = (_boot_data_end - _boot_data_start) / 4;
    DMA1_Stream0->CR = DMA_SxCR_CHSEL_0 |      // Channel 0
                       DMA_SxCR_PL_1 |         // Priority high
                       DMA_SxCR_MSIZE_1 |      // 32-bit memory
                       DMA_SxCR_PSIZE_1 |      // 32-bit peripheral
                       DMA_SxCR_MINC |         // Memory increment
                       DMA_SxCR_PINC |         // Peripheral increment
                       DMA_SxCR_DIR_0;         // Memory-to-memory
    
    // Start DMA transfer
    DMA1_Stream0->CR |= DMA_SxCR_EN;
    
    // Compute hash while DMA operates
    sha256_compute(image_base, image_size, hash_output);
    
    // Wait for DMA completion
    while (!(DMA1->LISR & DMA_LISR_TCIF0)) { __NOP(); }
    
    // Verify signature
    ecdsa_verify_signature_hw(&ecdsa_params);
}
```

This parallelization reduces total initialization time by the duration of the data copy, typically 100 to 500 microseconds for small bootloaders.

Clock configuration profoundly impacts boot time because flash memory access speed depends on CPU frequency and wait states. Running at maximum frequency (400 MHz) requires configuring 4 wait states for flash access, while lower frequencies (100 MHz) permit zero wait states. The bootloader optimizes by executing signature verification at reduced frequency, then switching to maximum frequency for application handoff:

```c
void boot_optimize_clock_sequence(void) {
    // Start at 64 MHz with 0 wait states for fast flash reads
    RCC->CFGR &= ~RCC_CFGR_HPRE;
    RCC->CFGR |= RCC_CFGR_HPRE_DIV1;
    FLASH->ACR &= ~FLASH_ACR_LATENCY;
    FLASH->ACR |= FLASH_ACR_LATENCY_0WS;
    
    // Perform signature verification (dominated by PKA, not flash access)
    ecdsa_verify_signature_hw(&ecdsa_params);
    
    // Switch to 400 MHz with 4 wait states for application execution
    FLASH->ACR &= ~FLASH_ACR_LATENCY;
    FLASH->ACR |= FLASH_ACR_LATENCY_4WS;
    RCC->PLLCFGR = /* 400 MHz PLL configuration */;
    RCC->CR |= RCC_CR_PLLON;
    while (!(RCC->CR & RCC_CR_PLLRDY)) { __NOP(); }
    RCC->CFGR |= RCC_CFGR_SW_PLL;
}
```

This frequency ramping reduces flash read overhead during signature verification while delivering maximum performance to application code.

### Failure Mode Analysis: Bricking Prevention and Recovery

Catastrophic bootloader failures—those that prevent the device from booting any valid firmware—transform expensive hardware into electronic waste. The bootloader architect must anticipate and mitigate failure modes spanning hardware faults, software bugs, and adversarial attacks.

Power failure during flash erasure represents the most common bricking scenario. NOR flash erase operations span hundreds of milliseconds to seconds, during which power loss leaves the sector partially erased with unpredictable bit patterns. If this sector contains bootloader code or critical metadata, the device cannot boot. The solution employs redundant metadata stored in independent sectors:

```c
#define METADATA_SECTOR_A 0x08090000
#define METADATA_SECTOR_B 0x08092000

boot_metadata_t *read_valid_metadata(void) {
    boot_metadata_t *meta_a = (boot_metadata_t *)METADATA_SECTOR_A;
    boot_metadata_t *meta_b = (boot_metadata_t *)METADATA_SECTOR_B;
    
    uint32_t crc_a = crc32_compute((uint8_t *)meta_a,
                                   sizeof(boot_metadata_t) - 4);
    uint32_t crc_b = crc32_compute((uint8_t *)meta_b,
                                   sizeof(boot_metadata_t) - 4);
    
    bool valid_a = (meta_a->magic == 0x424F4F54) && (crc_a == meta_a->crc32);
    bool valid_b = (meta_b->magic == 0x424F4F54) && (crc_b == meta_b->crc32);
    
    if (valid_a && valid_b) {
        // Both valid, return newer version
        return (meta_a->slot_a_version > meta_b->slot_a_version) ? meta_a : meta_b;
    } else if (valid_a) {
        return meta_a;
    } else if (valid_b) {
        return meta_b;
    } else {
        // Both corrupted, enter factory reset
        return NULL;
    }
}
```

Updating metadata follows a careful sequence that ensures at least one valid copy survives power loss:

```c
void write_metadata_atomic(const boot_metadata_t *new_meta) {
    boot_metadata_t *meta_a = (boot_metadata_t *)METADATA_SECTOR_A;
    boot_metadata_t *meta_b = (boot_metadata_t *)METADATA_SECTOR_B;
    
    // Determine which sector is older
    if (meta_a->slot_a_version <= meta_b->slot_a_version) {
        // Update sector A
        nor_flash_erase_sector(FLASH_BANK_1, 18);
        nor_flash_program_buffer(METADATA_SECTOR_A, (uint8_t *)new_meta,
                                sizeof(boot_metadata_t));
    } else {
        // Update sector B
        nor_flash_erase_sector(FLASH_BANK_1, 19);
        nor_flash_program_buffer(METADATA_SECTOR_B, (uint8_t *)new_meta,
                                sizeof(boot_metadata_t));
    }
}
```

This alternating update scheme guarantees that power loss during metadata writes leaves at least one readable copy.

Bootloader corruption demands hardware-level recovery mechanisms because software cannot repair itself. Production devices incorporate dedicated recovery modes triggered by external signals:

```c
typedef enum {
    BOOT_MODE_NORMAL = 0,
    BOOT_MODE_RECOVERY = 1,
    BOOT_MODE_DFU = 2
} boot_mode_t;

boot_mode_t detect_boot_mode(void) {
    // Sample recovery pin (e.g., button held during power-on)
    GPIO_InitTypeDef gpio_init = {
        .Pin = GPIO_PIN_0,
        .Mode = GPIO_MODE_INPUT,
        .Pull = GPIO_PULLUP
    };
    HAL_GPIO_Init(GPIOA, &gpio_init);
    
    if (HAL_GPIO_ReadPin(GPIOA, GPIO_PIN_0) == GPIO_PIN_RESET) {
        return BOOT_MODE_RECOVERY;
    }
    
    // Check if bootloader integrity failed
    if (!verify_bootloader_image()) {
        return BOOT_MODE_DFU;
    }
    
    return BOOT_MODE_NORMAL;
}
```

Recovery mode activates a minimal USB DFU (Device Firmware Update) bootloader residing in immutable ROM:

```c
void enter_dfu_mode(void) {
    // Initialize USB peripheral
    USB_OTG_FS->GCCFG |= USB_OTG_GCCFG_PWRDWN;
    USB_OTG_FS->GUSBCFG |= USB_OTG_GUSBCFG_FDMOD;
    
    // Enumerate as DFU device (class 0xFE, subclass 0x01)
    usb_device_descriptor_t desc = {
        .bLength = 18,
        .bDescriptorType = USB_DESC_TYPE_DEVICE,
        .bcdUSB = 0x0200,
        .bDeviceClass = 0xFE,
        .bDeviceSubClass = 0x01,
        .bDeviceProtocol = 0x02,
        .bMaxPacketSize0 = 64,
        .idVendor = 0x0483,
        .idProduct = 0xDF11,
        .bcdDevice = 0x0200,
        .iManufacturer = 1,
        .iProduct = 2,
        .iSerialNumber = 3,
        .bNumConfigurations = 1
    };
    
    usb_set_device_descriptor(&desc);
    
    // Process DFU commands indefinitely
    while (1) {
        dfu_process_commands();
    }
}
```

This ROM-based DFU provides a last-resort recovery mechanism accessible even when all user flash regions are corrupted.

Version mismatch between bootloader and application can cause subtle failures. If the bootloader expects metadata in one format but the application writes a different format, the system enters an inconsistent state. Versioning the shared RAM interface prevents this:

```c
#define SHARED_INTERFACE_VERSION 2

typedef struct {
    uint32_t magic;
    uint16_t interface_version;
    uint16_t bootloader_version;
    // Interface fields...
} shared_interface_t;

bool validate_interface_version(void) {
    shared_interface_t *iface = (shared_interface_t *)SHARED_RAM_BASE;
    
    if (iface->interface_version != SHARED_INTERFACE_VERSION) {
        // Version mismatch, clear shared RAM
        memset((void *)SHARED_RAM_BASE, 0, 4096);
        iface->magic = 0x53484152;  // "SHAR"
        iface->interface_version = SHARED_INTERFACE_VERSION;
        iface->bootloader_version = BOOTLOADER_VERSION;
        return false;
    }
    
    return true;
}
```

The bootloader clears incompatible interface versions, forcing the application to reinitialize with correct parameters.

Timing attacks against signature verification can leak cryptographic key material by measuring execution time variations correlated with secret data. Constant-time implementations prevent this by ensuring that code paths through cryptographic primitives take identical time regardless of input:

```c
// Vulnerable: early exit leaks information
bool memcmp_vulnerable(const uint8_t *a, const uint8_t *b, size_t len) {
    for (size_t i = 0; i < len; i++) {
        if (a[i] != b[i]) return false;  // Early exit timing leak
    }
    return true;
}

// Constant-time: always checks full length
bool memcmp_constant_time(const uint8_t *a, const uint8_t *b, size_t len) {
    volatile uint8_t result = 0;
    for (size_t i = 0; i < len; i++) {
        result |= (a[i] ^ b[i]);
    }
    return (result == 0);
}
```

All cryptographic comparisons in the bootloader must use constant-time implementations to prevent side-channel attacks.

Electromagnetic fault injection attacks attempt to corrupt cryptographic computations by inducing voltage glitches during signature verification. The bootloader defends by performing critical operations multiple times and comparing results:

```c
bool rsa_verify_with_redundancy(const rsa_verify_params_t *params) {
    bool result1 = rsa_verify_signature_hw(params);
    bool result2 = rsa_verify_signature_hw(params);
    bool result3 = rsa_verify_signature_hw(params);
    
    // Require majority voting
    uint8_t vote_count = result1 + result2 + result3;
    return (vote_count >= 2);
}
```

This redundancy forces attackers to precisely time multiple glitches, exponentially increasing attack difficulty.

Flash wear-out after exceeding endurance limits causes incremental failures. The bootloader detects impending failure by monitoring bit error rates and relocating critical data before corruption becomes uncorrectable:

```c
typedef struct {
    uint32_t read_count;
    uint32_t corrected_errors;
    uint32_t uncorrectable_errors;
} block_health_t;

block_health_t health_table[2048];

void monitor_flash_health(uint16_t block) {
    health_table[block].read_count++;
    
    ecc_status_t status = nand_read_page_with_ecc(
        block * NAND_PAGES_PER_BLOCK, temp_buffer);
    
    if (status == ECC_CORRECTED) {
        health_table[block].corrected_errors++;
        
        // Check if approaching failure threshold
        float error_rate = (float)health_table[block].corrected_errors /
                          health_table[block].read_count;
        
        if (error_rate > 0.01) {  // 1% error rate threshold
            // Relocate block contents to healthy block
            relocate_block_data(block);
            mark_block_retired(block);
        }
    } else if (status == ECC_UNCORRECTABLE) {
        health_table[block].uncorrectable_errors++;
        // Immediate relocation required
        relocate_block_data(block);
        mark_block_retired(block);
    }
}
```

Proactive block retirement extends device lifespan by preventing catastrophic data loss from worn-out flash cells.

The ultimate anti-bricking mechanism involves manufacturing devices with two independent flash banks, where bank 0 contains immutable factory firmware and bank 1 contains field-updateable firmware. If all update attempts fail, the bootloader reverts to bank 0:

```c
typedef enum {
    BANK_FACTORY = 0,
    BANK_FIELD = 1
} flash_bank_select_t;

void final_fallback_boot(void) {
    // Try field firmware first
    if (verify_application_image(BANK_FIELD_BASE)) {
        boot_application(BANK_FIELD_BASE);
    }
    
    // Fall back to factory firmware
    if (verify_application_image(BANK_FACTORY_BASE)) {
        boot_application(BANK_FACTORY_BASE);
    }
    
    // Both failed, halt with diagnostic LED pattern
    while (1) {
        HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_5);
        delay_ms(100);
    }
}
```

This factory firmware may implement only core functionality, but it ensures the device remains serviceable even after catastrophic field update failures.

### Real-World Deployment Considerations

Production bootloader deployment demands rigorous testing across temperature extremes, supply voltage variations, and RF interference scenarios that laboratory conditions rarely replicate. Automotive bootloaders must survive -40°C to +125°C temperature ranges where flash programming times increase by 3x at low temperatures and bit error rates rise at high temperatures. Industrial bootloaders must tolerate supply voltage sags during motor starts and surges during inductive load switching, requiring careful power supply sequencing and brown-out detection:

```c
void bootloader_power_monitoring(void) {
    // Enable brown-out detector at 2.8V threshold
    PWR->CR1 &= ~PWR_CR1_PLS;
    PWR->CR1 |= PWR_CR1_PLS_LEV5;  // 2.8V threshold
    PWR->CR1 |= PWR_CR1_PVDE;      // Enable detector
    
    // Check supply voltage before flash operations
    if (PWR->CSR1 & PWR_CSR1_PVDO) {
        // Voltage below threshold, abort flash write
        return;
    }
    
    // Proceed with flash operation
    nor_flash_program_buffer(address, data, length);
}
```

Field testing reveals edge cases impossible to anticipate through specification review. One automotive bootloader exhibited rare corruption after firmware updates performed immediately following cold starts at -30°C. Investigation traced the failure to flash charge pump settling time: the flash controller's internal voltage multiplier required 500 additional microseconds to stabilize at extreme temperatures, but the bootloader began programming after only 200 microseconds. Adding temperature-dependent delays resolved the issue:

```c
void flash_wait_ready_temperature_compensated(void) {
    int16_t temperature = read_die_temperature();
    uint32_t wait_us = 200;
    
    if (temperature < -20) {
        wait_us = 800;  // Extended wait for cold starts
    } else if (temperature < 0) {
        wait_us = 500;
    }
    
    delay_us(wait_us);
    
    while (!(FLASH->SR & FLASH_SR_BSY)) {
        __NOP();
    }
}
```

Manufacturing test coverage must verify bootloader operation under fault injection: power interruption during each boot phase, corrupted metadata, invalid signatures, and exhausted version counters. Automated test fixtures cycle power randomly during update sequences, statistically validating that the bootloader recovers gracefully from any possible interruption point:

```python
# Manufacturing test fixture pseudocode
def stress_test_bootloader(device, iterations=1000):
    for i in range(iterations):
        device.start_firmware_update(test_image)
        
        # Randomly interrupt update
        time.sleep(random.uniform(0, 5.0))
        device.power_off()
        time.sleep(0.1)
        device.power_on()
        
        # Verify device boots successfully
        assert device.heartbeat_detected(timeout=30)
        
        # Verify correct firmware version running
        version = device.read_firmware_version()
        assert version in [ORIGINAL_VERSION, TEST_VERSION]
```

This statistical validation provides confidence that field deployments will survive power failures occurring at arbitrary times during update processes.

Security audits examine bootloader implementations for cryptographic weaknesses, side-channel vulnerabilities, and privilege escalation paths. Common findings include:

1. **Insufficient entropy during key generation:** Using predictable seeds for random number generators allows attackers to reproduce session keys.
2. **Signature verification bypass through fault injection:** Skipping signature checks under carefully timed power glitches.
3. **Debug interface exposure:** Leaving JTAG or SWD enabled in production devices permits memory extraction.
4. **Rollback counter overflow:** Failing to halt updates after version counters exhaust their range.

Addressing these findings requires defense-in-depth approaches that layer multiple countermeasures:

```c
void bootloader_security_hardening(void) {
    // Disable debug interfaces in production
    DBGMCU->CR = 0;
    
    // Enable all security features
    FLASH->OPTCR |= FLASH_OPTCR_RDP_LEVEL2;  // Read protection level 2
    FLASH->OPTCR |= FLASH_OPTCR_SPRMOD;      // Secure memory mode
    
    // Verify security state before proceeding
    if ((FLASH->OPTCR & FLASH_OPTCR_RDP) != FLASH_OPTCR_RDP_LEVEL2) {
        // Security downgrade detected, halt
        while (1) { __NOP(); }
    }
    
    // Perform signature verification with redundancy
    for (uint8_t attempt = 0; attempt < 3; attempt++) {
        if (!rsa_verify_signature_hw(&verify_params)) {
            // Verification failed, halt immediately
            while (1) { __NOP(); }
        }
    }
}
```

The intersection of security and safety creates unique challenges for bootloaders in medical devices and autonomous vehicles, where software updates must satisfy both cybersecurity requirements (validated cryptographic signatures) and functional safety requirements (fail-safe defaults, fault detection). These systems implement dual validation where cryptographic correctness gates functional safety checks:

```c
bool bootloader_validate_safety_critical_update(uint32_t image_base) {
    // First validate cryptographic signature
    if (!ecdsa_verify_signature_hw(&ecdsa_params)) {
        return false;
    }
    
    // Then validate functional safety checksums
    const image_header_t *header = (const image_header_t *)image_base;
    
    // Compute CRC-32C (Castagnoli) over safety-critical regions
    uint32_t computed_crc = crc32c_compute(
        (uint8_t *)(image_base + header->safety_code_offset),
        header->safety_code_length);
    
    if (computed_crc != header->safety_code_crc) {
        return false;
    }
    
    // Verify safety version monotonically increases
    if (header->safety_version <= boot_meta->safety_version) {
        return false;
    }
    
    return true;
}
```

This dual validation ensures that both security adversaries and random hardware faults cannot compromise safety-critical functionality.

The bootloader architect must balance theoretical security properties against practical field serviceability. Excessively rigid security policies can brick devices when legitimate firmware updates encounter unexpected conditions—for example, version counters that exhaust their OTP capacity or signature validation that fails due to cosmic ray bit flips in flash memory. Deployments incorporate manual recovery procedures accessible through physical security mechanisms:

```c
bool check_manual_recovery_mode(void) {
    // Require physical access (button pressed for 10 seconds)
    uint32_t button_hold_time = 0;
    
    while (HAL_GPIO_ReadPin(RECOVERY_PORT, RECOVERY_PIN) == GPIO_PIN_RESET) {
        delay_ms(100);
        button_hold_time += 100;
        
        if (button_hold_time >= 10000) {
            // Authenticated physical presence, allow unsigned firmware
            return true;
        }
    }
    
    return false;
}
```

This escape hatch permits authorized personnel with physical device access to recover bricked units while maintaining security against remote attacks.

Modern bootloaders increasingly incorporate telemetry to diagnose field failures. Persistent logs track boot attempts, verification failures, and rollback events:

```c
typedef struct {
    uint32_t timestamp;
    uint8_t boot_slot;
    uint8_t verification_result;
    uint8_t rollback_count;
    uint8_t failure_reason;
} boot_log_entry_t;

#define BOOT_LOG_SIZE 64
boot_log_entry_t boot_log[BOOT_LOG_SIZE];
uint8_t boot_log_index = 0;

void bootloader_log_event(uint8_t slot, uint8_t result, uint8_t reason) {
    boot_log_entry_t *entry = &boot_log[boot_log_index];
    
    entry->timestamp = HAL_GetTick();
    entry->boot_slot = slot;
    entry->verification_result = result;
    entry->rollback_count = boot_meta->rollback_count;
    entry->failure_reason = reason;
    
    boot_log_index = (boot_log_index + 1) % BOOT_LOG_SIZE;
    
    // Persist log to flash periodically
    if (boot_log_index % 8 == 0) {
        flash_write_log_buffer(boot_log, sizeof(boot_log));
    }
}
```

These logs assist field support teams in diagnosing whether update failures stem from network connectivity issues, corrupted downloads, or defective firmware images.

The bootloader represents the embedded system's most critical software component, executing with maximum privilege before any security policies activate, and determining whether devices worth hundreds or thousands of dollars remain functional after field updates. Its correctness and robustness determine whether over-the-air update capabilities deliver competitive advantages or catastrophic warranty costs. Every line of bootloader code must be written with the understanding that bugs cannot be patched through normal update mechanisms—a corrupted bootloader renders the update mechanism itself nonfunctional, leaving only expensive hardware-level recovery procedures. This section has dissected the mechanisms through which production bootloaders achieve the necessary reliability, from multi-stage boot sequences that progressively validate each layer to wear-leveling algorithms that extend flash lifespan, from A/B partition schemes that enable safe rollback to cryptographic validation that roots trust in immutable silicon. Armed with these techniques and mindful of their failure modes, the bootloader architect can design systems that balance security, reliability, and field serviceability within the unforgiving constraints of embedded hardware.
