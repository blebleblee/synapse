# Lesson 1: Foundations & Kernel/System Invariants

## Curriculum Roadmap

This lesson establishes the theoretical foundation for eBPF, a critical component of modern cloud-native infrastructure. By the end of this lesson, you will understand the first-principles problem space, execution boundaries, and non-negotiable system invariants that underpin eBPF's design and operation.

## 1. First-Principles Problem Space & Execution Boundaries

The eBPF ecosystem operates within the Linux kernel, a complex, multi-threaded, and multi-process environment. To grasp the fundamental mechanisms and trade-offs, it is essential to understand the problem space and execution boundaries.

The eBPF problem space revolves around the need for a programmable, yet secure, and efficient, data plane. This requires a novel approach to kernel programming, one that leverages the strengths of both traditional kernel code and user-space applications. The eBPF problem space can be decomposed into three primary components:

*   **Programmability**: eBPF must provide a flexible and expressive programming model, allowing developers to write high-performance, low-latency, and efficient code.
*   **Security**: eBPF must ensure the integrity and confidentiality of kernel data, preventing unauthorized access and ensuring the trustworthiness of kernel operations.
*   **Efficiency**: eBPF must optimize kernel performance, minimizing overhead and maximizing throughput, while maintaining the programmability and security guarantees.

To address these challenges, eBPF introduces a novel execution model, which we will explore in the following sections.

### Execution Boundaries

The eBPF execution model is built around the concept of a **program**, which is a self-contained, compiled, and verified unit of code that executes within the kernel. Programs are executed in a sandboxed environment, isolated from the rest of the kernel, ensuring the security and integrity of kernel data.

The eBPF execution boundaries are defined by the following components:

*   **Programs**: Self-contained units of code that execute within the kernel.
*   **Maps**: Data structures that store program state and metadata.
*   **XDP**: The eBPF execution environment, which provides a sandboxed environment for program execution.

### eBPF Execution Model

The eBPF execution model is based on the following key components:

*   **Program Loading**: Programs are loaded into the kernel using the `bpf` command.
*   **Program Execution**: Programs are executed within the kernel, using the `bpf` instruction set.
*   **Program Verification**: Programs are verified for correctness and security using the `bpf` verifier.

The eBPF execution model is designed to provide a flexible and efficient programming model, while ensuring the security and integrity of kernel data.

## 2. Fundamental System Guarantees & Non-Negotiable Invariants

The eBPF ecosystem relies on a set of fundamental system guarantees and non-negotiable invariants, which ensure the correctness and security of kernel operations. These guarantees and invariants are critical to the eBPF design and operation.

### System Guarantees

The eBPF ecosystem relies on the following system guarantees:

*   **Program Integrity**: Programs are executed within a sandboxed environment, ensuring the integrity of kernel data.
*   **Program Confidentiality**: Programs have access to kernel data, but are prevented from accessing unauthorized data.
*   **Program Efficiency**: Programs are optimized for performance, minimizing overhead and maximizing throughput.

### Non-Negotiable Invariants

The eBPF ecosystem relies on the following non-negotiable invariants:

*   **Program Verification**: Programs are verified for correctness and security before execution.
*   **Program Isolation**: Programs are executed within a sandboxed environment, preventing unauthorized access to kernel data.
*   **Program Execution Order**: Programs are executed in a predictable and deterministic order, ensuring the correctness of kernel operations.

These system guarantees and non-negotiable invariants are critical to the eBPF design and operation, ensuring the correctness, security, and efficiency of kernel operations.

## 3. High-Level Process & Subsystem Architecture

The eBPF ecosystem consists of several high-level processes and subsystems, which work together to provide a programmable, secure, and efficient data plane. The following Mermaid diagram illustrates the high-level architecture of the eBPF ecosystem:

```mermaid
graph LR
    subgraph eBPF Ecosystem
        direction TB
        Program[Program] -->|Load|> bpf[Loader]
        bpf -->|Execute|> XDP[XDP]
        XDP -->|Verify|> Verifier[Verifier]
        Verifier -->|Map|> Map[Map]
        Map -->|Program|> Program
    end
```

This diagram illustrates the key components of the eBPF ecosystem, including programs, maps, XDP, and the verifier. The eBPF ecosystem is designed to provide a flexible and efficient programming model, while ensuring the security and integrity of kernel data.

### Exercises

1.  Write a simple eBPF program that loads a map and executes a function.
2.  Explain the role of the verifier in ensuring program correctness and security.
3.  Describe the execution order of programs within the eBPF ecosystem.

### Solutions

1.  The solution to exercise 1 is provided in the following code snippet:

    ```c
#include <linux/bpf.h>

struct bpf_map_def SEC("maps") my_map = {
    .type = BPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(__u32),
    .value_size = sizeof(__u32),
    .max_entries = 1,
};

SEC("bpf")
int bpf_prog(struct bpf_ctx *ctx) {
    __u32 *value = bpf_map_lookup_elem(&my_map, &ctx->key);
    if (value)
        *value = 42;
    return 0;
}
```

2.  The solution to exercise 2 is provided in the following explanation:

    The verifier ensures program correctness and security by checking the program's syntax, semantics, and behavior. The verifier checks the program's use of maps, functions, and other kernel resources, ensuring that the program does not access unauthorized data or execute unauthorized operations.

3.  The solution to exercise 3 is provided in the following explanation:

    The execution order of programs within the eBPF ecosystem is determined by the `bpf` instruction set and the `XDP` execution environment. Programs are executed in a predictable and deterministic order, ensuring the correctness of kernel operations. The execution order is determined by the program's load order, execution order, and verification order.
