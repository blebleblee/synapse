# Lesson 1: CPU Interpretation Techniques

## 1. First-Principles Intuition & Invariants

Game emulation sits at the intersection of digital archaeology, compiler theory, and high-performance systems programming. When we emulate a classic gaming console or handheld device, we are not merely replaying stored video frames or animation sequences. We are constructing a complete virtual machine that faithfully executes the original binary programs compiled for an entirely different processor architecture, memory model, and peripheral subsystem. The emulator must translate every machine instruction, maintain cycle-accurate timing, synchronize multiple coprocessors, and handle hardware quirks that the original game developers encoded into their software through years of intimate platform knowledge.

At the heart of every emulator lies the CPU interpreter, a software construct that models the fetch-decode-execute cycle of the target processor. The original hardware performed this cycle in silicon, with dedicated instruction decoders, arithmetic logic units, register files, and memory controllers clocked at tens or hundreds of megahertz. Our emulator must replicate this behavior in software running on a host processor with a fundamentally different instruction set architecture. A Super Nintendo Entertainment System ran on a customized 65816 processor at 3.58 MHz; a Game Boy Advanced contained an ARM7TDMI at 16.78 MHz; a PlayStation housed a MIPS R3000A at 33.87 MHz. Each of these architectures employed distinct register layouts, addressing modes, instruction encodings, and memory models. The emulator programmer must internalize these architectural differences and translate them into efficient host machine code that can sustain frame rates of 60 Hz or higher while maintaining functional equivalence.

The fundamental invariant of CPU emulation is the preservation of observable behavior. The emulated processor must produce identical register states, memory contents, and peripheral interactions as the original hardware when executing the same instruction stream under the same initial conditions. This requirement extends beyond simple functional correctness to encompass cycle-level timing accuracy. Classic game software often synchronized game logic, graphics rendering, and audio generation to precise CPU cycle counts, exploiting race conditions and hardware quirks to achieve effects that seemed impossible within the platform's documented capabilities. Emulators must therefore track not only architectural state but also micro-architectural timing, counting cycles consumed by memory accesses, branch mispredictions, and instruction pipeline stalls.

The interpreter approach to CPU emulation offers maximum flexibility and debugging transparency at the cost of execution speed. An interpreter models the target processor as a state machine consisting of program counter, register file, status flags, and memory interface. Each iteration of the emulation loop fetches the instruction byte sequence pointed to by the program counter, decodes the instruction opcode and operands, executes the corresponding operation by updating architectural state, and advances the program counter to the next instruction. This direct mapping between guest instructions and host code makes the interpreter trivial to debug, instrument, and verify for correctness. The cost is severe: each guest instruction requires dozens or hundreds of host instructions to fetch, decode, dispatch, and execute. Even with aggressive optimization, interpreters struggle to achieve more than a 10:1 slowdown ratio compared to native execution.

Dynamic recompilation, also known as just-in-time compilation or binary translation, amortizes interpretation overhead by compiling blocks of guest instructions into host machine code that can be cached and reused. When the emulator encounters a new program counter value, it disassembles a basic block of guest instructions, translates each instruction into an equivalent sequence of host instructions, and stores the resulting code block in a translation cache indexed by guest address. Subsequent executions of the same code block bypass the interpreter entirely, jumping directly to the cached host code. This approach can reduce the slowdown ratio to 2:1 or better, approaching native execution speed for tight loops that remain in the translation cache. The tradeoffs are increased complexity, higher memory consumption for the code cache, and challenges in handling self-modifying code, cycle-accurate timing, and architectural edge cases.

Hybrid approaches combine interpretation and dynamic recompilation to balance performance and accuracy. The emulator begins in interpreter mode, profiling execution patterns and identifying hot code paths. Once a basic block exceeds an execution frequency threshold, the dynamic recompiler translates it to host code. Cold code remains interpreted, avoiding the compilation overhead for rarely executed paths. This strategy proves particularly effective for game emulation, where the main game loop, sprite rendering routines, and audio mixing code dominate execution time, while initialization code, error handlers, and debug routines execute infrequently.

The choice of interpretation strategy interacts deeply with the architectural characteristics of the target processor. Complex Instruction Set Computing (CISC) architectures like the x86 or 68000 families feature variable-length instruction encodings, multiple addressing modes per instruction, and rich memory-to-memory operations. These characteristics complicate dynamic recompilation because instruction boundaries are not statically determinable, and each instruction may compile to dozens of host instructions. Reduced Instruction Set Computing (RISC) architectures like MIPS, ARM, and PowerPC employ fixed-length instruction encodings, load-store memory models, and orthogonal register-immediate-register operations. These properties simplify both interpretation and dynamic recompilation, making RISC processors attractive targets for high-performance emulation.


## 2. Core Architecture & Mechanics

The interpreter core implements the classic von Neumann cycle: fetch instruction from memory at the program counter address, decode the instruction opcode and operands, execute the instruction by updating processor state, and advance the program counter. For concreteness, consider a simplified interpreter for the 6502 processor, the CPU that powered the Nintendo Entertainment System, Commodore 64, and Apple II. The 6502 employs an 8-bit accumulator, two 8-bit index registers X and Y, an 8-bit stack pointer, an 8-bit status register containing carry, zero, interrupt disable, decimal mode, break, overflow, and negative flags, and a 16-bit program counter addressing 64 KB of memory.

```c
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>

#define MEMORY_SIZE 65536

typedef struct {
    uint8_t A;          // Accumulator
    uint8_t X;          // X index register
    uint8_t Y;          // Y index register
    uint8_t SP;         // Stack pointer (offset into 0x0100-0x01FF)
    uint16_t PC;        // Program counter
    
    // Status register flags
    bool C;             // Carry
    bool Z;             // Zero
    bool I;             // Interrupt disable
    bool D;             // Decimal mode (not used in NES)
    bool B;             // Break command
    bool V;             // Overflow
    bool N;             // Negative
    
    uint8_t memory[MEMORY_SIZE];
    uint64_t cycles;    // Cycle counter for timing
} CPU6502;

// Status register pack/unpack
static uint8_t cpu_get_status(CPU6502 *cpu) {
    return (cpu->C << 0) | (cpu->Z << 1) | (cpu->I << 2) | 
           (cpu->D << 3) | (cpu->B << 4) | (1 << 5) |  // Bit 5 always 1
           (cpu->V << 6) | (cpu->N << 7);
}

static void cpu_set_status(CPU6502 *cpu, uint8_t status) {
    cpu->C = (status >> 0) & 1;
    cpu->Z = (status >> 1) & 1;
    cpu->I = (status >> 2) & 1;
    cpu->D = (status >> 3) & 1;
    cpu->B = (status >> 4) & 1;
    cpu->V = (status >> 6) & 1;
    cpu->N = (status >> 7) & 1;
}

// Memory access functions
static uint8_t mem_read(CPU6502 *cpu, uint16_t addr) {
    return cpu->memory[addr];
}

static void mem_write(CPU6502 *cpu, uint16_t addr, uint8_t value) {
    cpu->memory[addr] = value;
}

// Stack operations (6502 stack lives in 0x0100-0x01FF, grows downward)
static void stack_push(CPU6502 *cpu, uint8_t value) {
    mem_write(cpu, 0x0100 | cpu->SP, value);
    cpu->SP--;
}

static uint8_t stack_pop(CPU6502 *cpu) {
    cpu->SP++;
    return mem_read(cpu, 0x0100 | cpu->SP);
}

// Update zero and negative flags based on result
static void update_zn_flags(CPU6502 *cpu, uint8_t value) {
    cpu->Z = (value == 0);
    cpu->N = (value & 0x80) != 0;
}

// Addressing mode resolution
static uint16_t addr_immediate(CPU6502 *cpu) {
    return cpu->PC++;
}

static uint16_t addr_zero_page(CPU6502 *cpu) {
    return mem_read(cpu, cpu->PC++);
}

static uint16_t addr_zero_page_x(CPU6502 *cpu) {
    return (mem_read(cpu, cpu->PC++) + cpu->X) & 0xFF;
}

static uint16_t addr_zero_page_y(CPU6502 *cpu) {
    return (mem_read(cpu, cpu->PC++) + cpu->Y) & 0xFF;
}

static uint16_t addr_absolute(CPU6502 *cpu) {
    uint8_t lo = mem_read(cpu, cpu->PC++);
    uint8_t hi = mem_read(cpu, cpu->PC++);
    return (hi << 8) | lo;
}

static uint16_t addr_absolute_x(CPU6502 *cpu, bool *page_crossed) {
    uint8_t lo = mem_read(cpu, cpu->PC++);
    uint8_t hi = mem_read(cpu, cpu->PC++);
    uint16_t base = (hi << 8) | lo;
    uint16_t addr = base + cpu->X;
    if (page_crossed) {
        *page_crossed = ((base ^ addr) & 0x100) != 0;
    }
    return addr;
}

static uint16_t addr_absolute_y(CPU6502 *cpu, bool *page_crossed) {
    uint8_t lo = mem_read(cpu, cpu->PC++);
    uint8_t hi = mem_read(cpu, cpu->PC++);
    uint16_t base = (hi << 8) | lo;
    uint16_t addr = base + cpu->Y;
    if (page_crossed) {
        *page_crossed = ((base ^ addr) & 0x100) != 0;
    }
    return addr;
}

static uint16_t addr_indirect_x(CPU6502 *cpu) {
    uint8_t ptr = (mem_read(cpu, cpu->PC++) + cpu->X) & 0xFF;
    uint8_t lo = mem_read(cpu, ptr);
    uint8_t hi = mem_read(cpu, (ptr + 1) & 0xFF);
    return (hi << 8) | lo;
}

static uint16_t addr_indirect_y(CPU6502 *cpu, bool *page_crossed) {
    uint8_t ptr = mem_read(cpu, cpu->PC++);
    uint8_t lo = mem_read(cpu, ptr);
    uint8_t hi = mem_read(cpu, (ptr + 1) & 0xFF);
    uint16_t base = (hi << 8) | lo;
    uint16_t addr = base + cpu->Y;
    if (page_crossed) {
        *page_crossed = ((base ^ addr) & 0x100) != 0;
    }
    return addr;
}

// Instruction implementations
static void op_lda(CPU6502 *cpu, uint16_t addr) {
    cpu->A = mem_read(cpu, addr);
    update_zn_flags(cpu, cpu->A);
}

static void op_ldx(CPU6502 *cpu, uint16_t addr) {
    cpu->X = mem_read(cpu, addr);
    update_zn_flags(cpu, cpu->X);
}

static void op_ldy(CPU6502 *cpu, uint16_t addr) {
    cpu->Y = mem_read(cpu, addr);
    update_zn_flags(cpu, cpu->Y);
}

static void op_sta(CPU6502 *cpu, uint16_t addr) {
    mem_write(cpu, addr, cpu->A);
}

static void op_adc(CPU6502 *cpu, uint16_t addr) {
    uint8_t operand = mem_read(cpu, addr);
    uint16_t result = cpu->A + operand + (cpu->C ? 1 : 0);
    
    cpu->C = result > 0xFF;
    cpu->V = ((~(cpu->A ^ operand) & (cpu->A ^ result)) & 0x80) != 0;
    cpu->A = result & 0xFF;
    update_zn_flags(cpu, cpu->A);
}

static void op_sbc(CPU6502 *cpu, uint16_t addr) {
    uint8_t operand = mem_read(cpu, addr);
    uint16_t result = cpu->A - operand - (cpu->C ? 0 : 1);
    
    cpu->C = result < 0x100;
    cpu->V = (((cpu->A ^ operand) & (cpu->A ^ result)) & 0x80) != 0;
    cpu->A = result & 0xFF;
    update_zn_flags(cpu, cpu->A);
}

static void op_jmp(CPU6502 *cpu, uint16_t addr) {
    cpu->PC = addr;
}

static void op_jsr(CPU6502 *cpu, uint16_t addr) {
    uint16_t ret_addr = cpu->PC - 1;
    stack_push(cpu, (ret_addr >> 8) & 0xFF);
    stack_push(cpu, ret_addr & 0xFF);
    cpu->PC = addr;
}

static void op_rts(CPU6502 *cpu) {
    uint8_t lo = stack_pop(cpu);
    uint8_t hi = stack_pop(cpu);
    cpu->PC = ((hi << 8) | lo) + 1;
}

static void op_bne(CPU6502 *cpu, int8_t offset) {
    if (!cpu->Z) {
        uint16_t old_pc = cpu->PC;
        cpu->PC += offset;
        cpu->cycles += 1;
        if ((old_pc ^ cpu->PC) & 0x100) {
            cpu->cycles += 1;  // Page boundary crossed
        }
    }
}

// Main interpreter loop
void cpu_reset(CPU6502 *cpu) {
    memset(cpu, 0, sizeof(CPU6502));
    cpu->SP = 0xFF;
    cpu->I = true;
    uint8_t lo = mem_read(cpu, 0xFFFC);
    uint8_t hi = mem_read(cpu, 0xFFFD);
    cpu->PC = (hi << 8) | lo;
}

int cpu_step(CPU6502 *cpu) {
    uint8_t opcode = mem_read(cpu, cpu->PC++);
    uint64_t start_cycles = cpu->cycles;
    bool page_crossed = false;
    
    switch (opcode) {
        // LDA variants
        case 0xA9: cpu->cycles += 2; op_lda(cpu, addr_immediate(cpu)); break;
        case 0xA5: cpu->cycles += 3; op_lda(cpu, addr_zero_page(cpu)); break;
        case 0xB5: cpu->cycles += 4; op_lda(cpu, addr_zero_page_x(cpu)); break;
        case 0xAD: cpu->cycles += 4; op_lda(cpu, addr_absolute(cpu)); break;
        case 0xBD: 
            cpu->cycles += 4; 
            op_lda(cpu, addr_absolute_x(cpu, &page_crossed));
            if (page_crossed) cpu->cycles += 1;
            break;
        case 0xB9:
            cpu->cycles += 4;
            op_lda(cpu, addr_absolute_y(cpu, &page_crossed));
            if (page_crossed) cpu->cycles += 1;
            break;
        case 0xA1: cpu->cycles += 6; op_lda(cpu, addr_indirect_x(cpu)); break;
        case 0xB1:
            cpu->cycles += 5;
            op_lda(cpu, addr_indirect_y(cpu, &page_crossed));
            if (page_crossed) cpu->cycles += 1;
            break;
            
        // STA variants
        case 0x85: cpu->cycles += 3; op_sta(cpu, addr_zero_page(cpu)); break;
        case 0x95: cpu->cycles += 4; op_sta(cpu, addr_zero_page_x(cpu)); break;
        case 0x8D: cpu->cycles += 4; op_sta(cpu, addr_absolute(cpu)); break;
        case 0x9D: cpu->cycles += 5; op_sta(cpu, addr_absolute_x(cpu, NULL)); break;
        case 0x99: cpu->cycles += 5; op_sta(cpu, addr_absolute_y(cpu, NULL)); break;
        case 0x81: cpu->cycles += 6; op_sta(cpu, addr_indirect_x(cpu)); break;
        case 0x91: cpu->cycles += 6; op_sta(cpu, addr_indirect_y(cpu, NULL)); break;
        
        // ADC variants
        case 0x69: cpu->cycles += 2; op_adc(cpu, addr_immediate(cpu)); break;
        case 0x65: cpu->cycles += 3; op_adc(cpu, addr_zero_page(cpu)); break;
        case 0x6D: cpu->cycles += 4; op_adc(cpu, addr_absolute(cpu)); break;
        
        // Control flow
        case 0x4C: cpu->cycles += 3; op_jmp(cpu, addr_absolute(cpu)); break;
        case 0x20: cpu->cycles += 6; op_jsr(cpu, addr_absolute(cpu)); break;
        case 0x60: cpu->cycles += 6; op_rts(cpu); break;
        case 0xD0: cpu->cycles += 2; op_bne(cpu, (int8_t)mem_read(cpu, cpu->PC++)); break;
        
        // Register transfers
        case 0xAA: cpu->cycles += 2; cpu->X = cpu->A; update_zn_flags(cpu, cpu->X); break;
        case 0x8A: cpu->cycles += 2; cpu->A = cpu->X; update_zn_flags(cpu, cpu->A); break;
        case 0xE8: cpu->cycles += 2; cpu->X++; update_zn_flags(cpu, cpu->X); break;
        case 0xC8: cpu->cycles += 2; cpu->Y++; update_zn_flags(cpu, cpu->Y); break;
        
        default:
            fprintf(stderr, "Unimplemented opcode: 0x%02X at PC=0x%04X\n", opcode, cpu->PC - 1);
            return -1;
    }
    
    return cpu->cycles - start_cycles;
}

void cpu_run(CPU6502 *cpu, uint64_t target_cycles) {
    while (cpu->cycles < target_cycles) {
        if (cpu_step(cpu) < 0) {
            break;
        }
    }
}
```

This interpreter demonstrates the fundamental structure common to all emulator cores. The `CPU6502` structure captures architectural state: registers, flags, and memory. Each instruction implementation operates on this state, reading operands from memory through addressing mode functions and updating registers according to the instruction semantics. The `cpu_step` function implements the fetch-decode-execute cycle, dispatching opcodes to their corresponding handler functions and tracking cycle counts for timing accuracy.

Addressing modes deserve particular attention because they represent one of the primary sources of complexity in instruction interpretation. The 6502 supports thirteen addressing modes, each specifying a different method for computing the effective address of an instruction's operand. Immediate addressing treats the operand byte as a literal value. Zero-page addressing uses an 8-bit address to access the first 256 bytes of memory, saving one byte and one cycle compared to absolute addressing. Indexed addressing adds the value of an index register to a base address, enabling array access and table lookups. Indirect addressing reads a 16-bit pointer from memory and uses that pointer as the effective address, supporting dynamic dispatch and function pointers. The indexed indirect and indirect indexed modes combine these mechanisms for complex data structure access.

Page boundary crossing detection is critical for cycle-accurate emulation. When an indexed addressing mode adds an index register to a base address such that the result crosses a 256-byte page boundary, the 6502 hardware requires an additional clock cycle to propagate the carry into the high byte of the address. The emulator detects this condition by XORing the base and effective addresses and testing bit 8. If the bit differs, a page crossing occurred and the cycle count increments. Store instructions and instructions that modify memory always consume the extra cycle, while read-only instructions only pay the penalty on crossing.

Endianness handling is essential when emulating processors with different byte orders than the host machine. The 6502 is little-endian: multi-byte values store the least significant byte at the lowest memory address. Modern x86-64 and ARM processors are also little-endian, simplifying emulation on these platforms. However, older PowerPC Macintosh systems and some network protocols use big-endian ordering, requiring explicit byte swapping when loading 16-bit addresses from memory. The interpreter performs this conversion in the addressing mode functions by reading low and high bytes separately and combining them with bitwise operations.

The transition from interpretation to dynamic recompilation requires constructing an intermediate representation that captures the semantics of guest instructions in a form amenable to host code generation. A basic block represents a straight-line sequence of instructions with a single entry point and single exit point, terminated by a branch, jump, or return instruction. The dynamic recompiler disassembles a basic block starting from the current program counter, translating each guest instruction into a sequence of operations in the intermediate representation. These operations might include register reads and writes, arithmetic and logical operations, memory loads and stores, and control flow instructions.

```c
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>

#define MAX_IR_OPS 1024
#define CODE_CACHE_SIZE (1024 * 1024)

typedef enum {
    IR_LOAD_IMM,      // dest = immediate
    IR_LOAD_MEM,      // dest = memory[addr]
    IR_STORE_MEM,     // memory[addr] = src
    IR_ADD,           // dest = src1 + src2
    IR_SUB,           // dest = src1 - src2
    IR_AND,           // dest = src1 & src2
    IR_OR,            // dest = src1 | src2
    IR_XOR,           // dest = src1 ^ src2
    IR_CMP,           // compare src1 and src2, set flags
    IR_BRANCH,        // conditional branch
    IR_JUMP,          // unconditional jump
    IR_CALL,          // function call
    IR_RETURN,        // return from function
} IROpcode;

typedef enum {
    REG_A,            // Accumulator
    REG_X,            // X index
    REG_Y,            // Y index
    REG_SP,           // Stack pointer
    REG_FLAGS,        // Status flags
    REG_TEMP0,        // Temporary registers
    REG_TEMP1,
    REG_TEMP2,
    REG_TEMP3,
} IRRegister;

typedef struct {
    IROpcode opcode;
    IRRegister dest;
    IRRegister src1;
    IRRegister src2;
    uint16_t immediate;
    uint16_t target_pc;
} IROperation;

typedef struct {
    uint16_t guest_pc;
    IROperation ops[MAX_IR_OPS];
    int op_count;
    void *host_code;
    size_t code_size;
} BasicBlock;

typedef struct {
    BasicBlock *blocks;
    int block_count;
    int block_capacity;
    uint8_t *code_buffer;
    size_t code_offset;
} JITCompiler;

JITCompiler *jit_create(void) {
    JITCompiler *jit = calloc(1, sizeof(JITCompiler));
    jit->block_capacity = 256;
    jit->blocks = calloc(jit->block_capacity, sizeof(BasicBlock));
    
    // Allocate executable memory for generated code
    jit->code_buffer = mmap(NULL, CODE_CACHE_SIZE,
                            PROT_READ | PROT_WRITE | PROT_EXEC,
                            MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    return jit;
}

BasicBlock *jit_find_block(JITCompiler *jit, uint16_t guest_pc) {
    for (int i = 0; i < jit->block_count; i++) {
        if (jit->blocks[i].guest_pc == guest_pc) {
            return &jit->blocks[i];
        }
    }
    return NULL;
}

BasicBlock *jit_allocate_block(JITCompiler *jit, uint16_t guest_pc) {
    if (jit->block_count >= jit->block_capacity) {
        jit->block_capacity *= 2;
        jit->blocks = realloc(jit->blocks, jit->block_capacity * sizeof(BasicBlock));
    }
    BasicBlock *block = &jit->blocks[jit->block_count++];
    memset(block, 0, sizeof(BasicBlock));
    block->guest_pc = guest_pc;
    return block;
}

void jit_emit_ir(BasicBlock *block, IROperation op) {
    if (block->op_count < MAX_IR_OPS) {
        block->ops[block->op_count++] = op;
    }
}

void jit_translate_block(JITCompiler *jit, CPU6502 *cpu, uint16_t start_pc) {
    BasicBlock *block = jit_allocate_block(jit, start_pc);
    uint16_t pc = start_pc;
    
    // Simplified translation: LDA #$42, STA $200, RTS
    while (block->op_count < MAX_IR_OPS) {
        uint8_t opcode = cpu->memory[pc++];
        
        switch (opcode) {
            case 0xA9: {  // LDA immediate
                uint8_t value = cpu->memory[pc++];
                IROperation op = {
                    .opcode = IR_LOAD_IMM,
                    .dest = REG_A,
                    .immediate = value
                };
                jit_emit_ir(block, op);
                break;
            }
            
            case 0x8D: {  // STA absolute
                uint8_t lo = cpu->memory[pc++];
                uint8_t hi = cpu->memory[pc++];
                uint16_t addr = (hi << 8) | lo;
                IROperation op = {
                    .opcode = IR_STORE_MEM,
                    .src1 = REG_A,
                    .immediate = addr
                };
                jit_emit_ir(block, op);
                break;
            }
            
            case 0x60:  // RTS
                jit_emit_ir(block, (IROperation){ .opcode = IR_RETURN });
                return;
                
            case 0x4C: {  // JMP absolute
                uint8_t lo = cpu->memory[pc++];
                uint8_t hi = cpu->memory[pc++];
                uint16_t target = (hi << 8) | lo;
                jit_emit_ir(block, (IROperation){
                    .opcode = IR_JUMP,
                    .target_pc = target
                });
                return;
            }
            
            default:
                return;  // Stop at unimplemented instruction
        }
    }
}
```

This intermediate representation abstracts away the specifics of both guest and host instruction sets, providing a common substrate for optimization passes. Register allocation maps guest registers and temporary values onto host registers, minimizing memory traffic. Constant folding evaluates operations on compile-time constants. Dead code elimination removes operations whose results are never used. Common subexpression elimination identifies redundant computations and reuses their results.

The final stage generates native machine code for the host processor. On x86-64, this involves emitting sequences of ModR/M-encoded instructions that load guest register values from a context structure, perform the required operations using host registers, and store results back to the context. The generated code must adhere to the host platform's calling convention, preserving callee-saved registers and maintaining stack alignment. For ARM hosts, the code generator emits ARM or Thumb instructions with their specific encoding requirements and branch distance limitations.


## 3. High-Performance Optimization & Failure Modes

Performance optimization in CPU emulation begins with minimizing the overhead of the interpreter loop itself. The naive switch-statement dispatch shown earlier incurs a branch misprediction penalty on every iteration because the branch predictor cannot reliably anticipate the next instruction opcode. Threaded interpretation addresses this by replacing the switch statement with an indirect jump through a jump table. Each instruction handler ends with a fetch of the next opcode and an indirect jump through the jump table, allowing the processor's return stack buffer to predict the next handler address.

```c
#include <stdint.h>
#include <stdio.h>

typedef struct {
    uint8_t A, X, Y, SP;
    uint16_t PC;
    bool C, Z, I, D, B, V, N;
    uint8_t memory[65536];
    uint64_t cycles;
} CPU6502;

// Declare handler prototypes
typedef void (*InstructionHandler)(CPU6502 *cpu, void **jump_table);

static void handler_lda_imm(CPU6502 *cpu, void **jump_table);
static void handler_sta_abs(CPU6502 *cpu, void **jump_table);
static void handler_jmp_abs(CPU6502 *cpu, void **jump_table);
static void handler_invalid(CPU6502 *cpu, void **jump_table);

// Macro to fetch next instruction and dispatch
#define NEXT_INSTRUCTION() do { \
    uint8_t opcode = cpu->memory[cpu->PC++]; \
    InstructionHandler handler = (InstructionHandler)jump_table[opcode]; \
    handler(cpu, jump_table); \
} while(0)

static void handler_lda_imm(CPU6502 *cpu, void **jump_table) {
    cpu->A = cpu->memory[cpu->PC++];
    cpu->Z = (cpu->A == 0);
    cpu->N = (cpu->A & 0x80) != 0;
    cpu->cycles += 2;
    NEXT_INSTRUCTION();
}

static void handler_sta_abs(CPU6502 *cpu, void **jump_table) {
    uint8_t lo = cpu->memory[cpu->PC++];
    uint8_t hi = cpu->memory[cpu->PC++];
    uint16_t addr = (hi << 8) | lo;
    cpu->memory[addr] = cpu->A;
    cpu->cycles += 4;
    NEXT_INSTRUCTION();
}

static void handler_jmp_abs(CPU6502 *cpu, void **jump_table) {
    uint8_t lo = cpu->memory[cpu->PC++];
    uint8_t hi = cpu->memory[cpu->PC++];
    cpu->PC = (hi << 8) | lo;
    cpu->cycles += 3;
    NEXT_INSTRUCTION();
}

static void handler_invalid(CPU6502 *cpu, void **jump_table) {
    fprintf(stderr, "Invalid opcode at PC=0x%04X\n", cpu->PC - 1);
}

void cpu_run_threaded(CPU6502 *cpu) {
    void *jump_table[256];
    
    // Initialize jump table
    for (int i = 0; i < 256; i++) {
        jump_table[i] = handler_invalid;
    }
    jump_table[0xA9] = handler_lda_imm;
    jump_table[0x8D] = handler_sta_abs;
    jump_table[0x4C] = handler_jmp_abs;
    
    // Start execution
    NEXT_INSTRUCTION();
}
```

Computed goto, a GNU C extension, further improves threaded interpretation by using labels as first-class values. Instead of calling through function pointers, each handler ends with a goto through a label pointer, eliminating function call overhead and allowing the compiler to optimize across handler boundaries.

Register caching represents another critical optimization for interpreted emulation. Rather than storing guest registers in memory and loading them on every instruction, the emulator maps frequently-used guest registers to host registers that persist across multiple guest instructions. On x86-64, the accumulator might reside in RAX, the X register in RBX, and the Y register in RCX. The program counter and status flags remain in memory due to their less frequent access patterns. The compiler's register allocator must balance the benefit of caching against the pressure on the host's register file, which is also needed for temporary values during instruction execution.

Dynamic recompilation optimization focuses on eliminating redundant operations and specializing generated code for common cases. Consider a tight loop that reads array elements and accumulates them into the accumulator. The naive translation loads the accumulator from memory at the start of each guest instruction and stores it back after each instruction. An optimizing compiler recognizes that the accumulator value flows through multiple instructions without being observed externally, allowing the intermediate stores to be eliminated and the value to remain in a host register throughout the basic block.

Flag computation optimization recognizes that many guest architectures compute status flags after every arithmetic operation, but few instructions actually test those flags. The emulator can defer flag computation by recording the operation that would produce the flags and only computing them when a branch or flag-testing instruction executes. This technique, known as lazy flag evaluation, eliminates flag computation for dead flags that never affect control flow.

Memory access optimization addresses the high cost of bounds checking and endianness conversion on every load and store. The emulator can map guest memory directly into host virtual address space, allowing guest loads and stores to compile to native host memory instructions. This approach requires careful handling of memory-mapped I/O regions, which must trap to emulation handlers for peripheral device access. The code generator emits conditional branches around I/O regions or uses hardware page protection to catch I/O accesses via page faults.

Self-modifying code detection poses a fundamental challenge for cached compiled code. If the guest program writes to memory that has been compiled into the code cache, the cached version becomes stale and must be invalidated. Conservative approaches check every memory write against code cache addresses and invalidate affected blocks, incurring significant overhead. Write-protect-based approaches use memory protection to mark compiled code pages read-only; writes trigger a page fault that invalidates the affected block and temporarily allows the write. Hash-based approaches store hashes of compiled blocks and check them periodically, trading detection latency for lower per-write overhead.

Cycle-accurate timing becomes increasingly difficult as optimization aggressiveness increases. Interpreters naturally track cycles by incrementing a counter after each instruction, but dynamically compiled code that optimizes away memory accesses and reorders instructions cannot maintain the same cycle-level accuracy. Hybrid approaches insert cycle checkpoint instructions at basic block boundaries and before I/O operations, accepting some timing drift within straight-line code blocks while maintaining accuracy at observable synchronization points.

The emulator must handle architectural corner cases that real hardware implements through complex state machines but which appear as single instructions in the ISA specification. The 6502 decimal mode, enabled by the D flag, causes arithmetic instructions to operate on binary-coded decimal values rather than pure binary. Each 4-bit nibble represents a decimal digit from 0 to 9, and operations must detect and correct invalid results. The implementation requires additional conditional logic and table lookups, significantly complicating the add and subtract instruction handlers.

Interrupt handling introduces asynchronous control flow that cuts across the sequential execution model. Hardware interrupts, triggered by peripheral devices or timer expiration, force the processor to save state and jump to an interrupt handler vector. The emulator must check for pending interrupts between instructions and, if the interrupt enable flag permits, push the program counter and status flags onto the stack and jump to the interrupt handler. Non-maskable interrupts cannot be disabled and must be checked on every instruction, while maskable interrupts only trigger when the interrupt disable flag is clear.

Debugging support for emulated code requires bidirectional mapping between guest and host addresses. When the emulator encounters a bug, the developer needs to inspect guest register state, step through guest instructions, and set breakpoints at guest addresses. Source-level debugging further requires mapping guest addresses to original source code lines, necessitating integration with debug symbol formats like DWARF or PDB. The emulator exposes a debug interface that accepts commands to read and write guest state, set hardware and software breakpoints, and single-step execution.

Performance profiling identifies hotspots in guest code by sampling the program counter at regular intervals or instrumenting the emulator to count basic block execution frequencies. The profiler presents results as a histogram of guest addresses sorted by execution time or instruction count, allowing the developer to focus optimization effort on the most frequently executed code. Integration with the guest's debug symbols enables source-level profiling that attributes time to specific functions and source lines.

Validation and conformance testing ensure the emulator faithfully reproduces the behavior of real hardware. Test ROM images exercise every instruction, addressing mode, and flag combination, comparing results against known-good reference implementations or hardware measurements. Timing validation runs cycle-counting test programs that measure instruction durations and compare against documented cycle counts. Regression testing runs complete game ROM images and compares emulator state traces against reference recordings, detecting subtle behavioral differences that manifest as graphical glitches or gameplay bugs.

The final consideration in high-performance emulation is the tradeoff between accuracy and speed. Cycle-accurate emulators faithfully reproduce every clock cycle of the original hardware, maintaining precise synchronization between the CPU, graphics, audio, and peripheral timers. This accuracy comes at the cost of significant computational overhead, often requiring host processors several orders of magnitude faster than the original hardware. Fast emulators sacrifice timing precision to achieve real-time or faster-than-real-time performance, introducing timing drift and behavioral differences that most games tolerate but which break timing-sensitive software. The emulator designer must understand the target audience and application domain to select the appropriate point along the accuracy-performance spectrum.
