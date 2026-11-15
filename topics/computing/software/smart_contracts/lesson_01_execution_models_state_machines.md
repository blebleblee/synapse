# Lesson 1: Execution Models, State Machines, Determinism

## 1. First-Principles Intuition & Invariants

Smart contracts represent a fundamental departure from traditional application execution models. Where conventional software runs on trusted servers under the control of a single operator, smart contracts execute within a distributed state machine replicated across thousands of independent validators. This shift in execution substrate introduces constraints that would be unthinkable in traditional computing: every operation must be deterministic, every instruction metered for resource consumption, and every state transition cryptographically verifiable by any participant in the network.

The core problem smart contract platforms solve is Byzantine consensus over computation. In classical distributed systems, consensus protocols like Raft or Paxos ensure agreement on ordered inputs—a sequence of log entries, database transactions, or message payloads. Smart contract platforms extend this further: they must achieve consensus not only on the order of transactions but on the precise outcome of arbitrary Turing-complete computation triggered by those transactions. A validator in Tokyo and a validator in São Paulo, running different CPU architectures, different operating system kernels, and different versions of the runtime environment, must arrive at byte-identical state after processing the same transaction. Any divergence, even a single bit flip in a register or a non-deterministic timestamp, would fork the blockchain into irreconcilable branches.

This requirement for universal determinism pervades every design decision in smart contract architecture. The execution model must eliminate all sources of non-determinism that plague traditional software: no system clock access, no random number generation from hardware entropy, no floating-point arithmetic (whose rounding behavior varies across CPU implementations), no concurrent thread scheduling, no network I/O with variable latency, and no interaction with the host operating system beyond a carefully controlled interface. The smart contract virtual machine becomes a hermetically sealed computation chamber where every opcode executes with mechanical precision, where the outcome of `ADD R1, R2, R3` depends solely on the values in those registers and never on cache line bounces, speculative execution rollbacks, or NUMA node topology.

The second foundational invariant is finite execution. In a replicated state machine, a single non-terminating computation would freeze every validator in the network indefinitely. Unlike traditional operating systems that can preempt runaway processes or impose wall-clock timeouts, smart contract platforms must guarantee halting before execution begins. The halting problem—proving whether an arbitrary program terminates—is undecidable in the general case, but smart contracts solve this through economic mechanism rather than static analysis. Every transaction carries a gas limit, a prepaid budget of computational steps. Each instruction consumes a fixed quantum of gas, and when the budget exhausts, execution terminates unconditionally. This transforms the halting problem into a solvency problem: any computation that can be paid for will eventually halt, either through successful completion or fuel starvation.

Gas metering serves dual purposes. First, it prevents denial-of-service attacks where malicious actors submit infinite loops to congest the network. Second, it creates a market for computational resources, ensuring that validators receive compensation proportional to the work they perform. The gas schedule—the mapping from opcodes to gas costs—must reflect the real-world computational expense of each operation. A simple integer addition might cost 3 gas, while a cryptographic hash requires 30 gas, and reading from persistent storage demands 200 gas. These costs are not arbitrary; they are calibrated through empirical benchmarking to ensure that expensive operations like `SHA3` or `SLOAD` cannot be exploited to exhaust validator resources while paying pennies in transaction fees.

The state machine itself is organized as a Merkle Patricia trie, a cryptographic accumulator that commits the entire world state into a single 32-byte root hash. Every account balance, every storage slot, and every deployed contract exists as a leaf in this trie. After executing a block of transactions, validators recompute this root hash independently. If their roots match, they achieved consensus on the state transition. If roots diverge, Byzantine fault detection protocols identify the faulty node. This cryptographic commitment allows light clients to verify state proofs without downloading the entire blockchain—a capability essential for scaling validation beyond high-performance server infrastructure.

## 2. Core Architecture & Mechanics

The execution lifecycle of a smart contract transaction proceeds through distinct phases, each governed by strict invariants that maintain system integrity. Understanding this lifecycle requires examining the virtual machine architecture, the transaction data structure, and the state transition function that bridges them.

### Transaction Structure and Validation

A transaction is an atomic state transition request consisting of a sender address, recipient address, value transfer amount, gas limit, gas price, nonce, and optional payload data. The nonce—a monotonically increasing counter—prevents replay attacks by ensuring each transaction executes exactly once in a specific order. Before execution begins, the transaction undergoes intrinsic validation: the signature must be cryptographically valid under secp256k1 elliptic curve verification, the nonce must match the sender's current nonce, and the sender's balance must cover both the value transfer and the maximum possible gas expenditure (`gasLimit * gasPrice`).

This pre-execution validation is critical because it prevents invalid transactions from consuming validator resources. A transaction with an incorrect signature never enters the virtual machine; it is rejected at the mempool layer. This creates a clear separation between syntactic validity—the transaction is well-formed and properly signed—and semantic validity—the transaction successfully completes its intended computation without reverting.

### Virtual Machine Register Architecture

The Ethereum Virtual Machine (EVM), the canonical smart contract execution substrate, operates as a stack-based machine with 256-bit word size. Unlike register-based architectures like x86-64 or ARM, where operations reference named registers (`MOV RAX, RBX`), the EVM manipulates an operand stack through instructions like `ADD`, `MUL`, and `DUP`. This design choice simplifies the instruction set at the cost of increased stack manipulation overhead. A simple expression like `(a + b) * c` requires multiple stack gymnastics: push `a`, push `b`, add (consuming two stack items, producing one), push `c`, multiply.

The machine state consists of several distinct memory regions, each with different gas cost characteristics. The stack holds up to 1024 elements and supports only the topmost 16 elements for direct access through `SWAP` and `DUP` instructions. Temporary memory is a linear byte array that expands dynamically but clears between transaction boundaries. Persistent storage is a key-value mapping from 256-bit keys to 256-bit values, maintained in the Merkle Patricia trie and surviving across transactions. Reading from storage costs 200 gas for a cold access (first read of a slot in the transaction) and 100 gas for warm access (subsequent reads), while writing to storage costs 20,000 gas for setting a zero slot to non-zero, 5,000 gas for modifying an existing non-zero value, and refunds 15,000 gas for clearing a slot back to zero.

```
┌─────────────────────────────────────────────┐
│         EVM Execution Environment           │
├─────────────────────────────────────────────┤
│  Program Counter (PC)                       │
│  Gas Available                              │
│  Stack (256-bit words, max depth 1024)      │
│  Memory (byte array, word-addressed)        │
│  Storage (persistent key-value trie)        │
│  Call Data (immutable input payload)        │
│  Return Data (output from last call)        │
└─────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────┐
│       Instruction Dispatch Loop             │
├─────────────────────────────────────────────┤
│  1. Fetch opcode at PC                      │
│  2. Deduct gas cost for operation           │
│  3. Execute state transition                │
│  4. Increment PC                            │
│  5. Check stack depth < 1024                │
│  6. Check gas remaining > 0                 │
│  7. If success: continue                    │
│     If revert: rollback state               │
│     If out-of-gas: halt with error          │
└─────────────────────────────────────────────┘
```

### State Transition Function Mechanics

The state transition function `Υ(σ, T) → σ'` takes the current world state `σ` and a transaction `T`, producing the next state `σ'`. This function is deterministic and pure: given identical inputs, it always produces identical outputs regardless of when or where it executes. The function proceeds through initialization, execution, and finalization phases.

Initialization establishes the execution context. The sender's nonce increments by one, preventing replay of this transaction. The intrinsic gas cost—a base fee of 21,000 gas plus additional costs for non-zero bytes in the transaction payload—is deducted from the gas limit. If the transaction carries a payload and the recipient is not a contract account (lacks bytecode), the transaction creates a new contract. The contract's address is deterministically derived from the sender address and nonce using `keccak256(rlp([sender, nonce]))[:20]`, ensuring no collision with existing addresses.

Execution dispatches to the contract bytecode with a fresh execution context. The program counter starts at zero, the stack is empty, memory is zeroed, and storage reflects the contract's persistent state. The interpreter enters a fetch-decode-execute loop, advancing the program counter after each instruction. Control flow instructions like `JUMP` and `JUMPI` modify the program counter non-sequentially, but jumps are constrained to `JUMPDEST` markers, preventing mid-instruction jumps that could bypass validation or create gadgets for exploitation.

Gas metering occurs before each instruction executes. The interpreter checks that sufficient gas remains to cover the operation's static cost and any dynamic expansion costs (memory growth, storage modifications). If gas suffices, the instruction proceeds; if gas is exhausted, execution halts immediately with an out-of-gas exception. This reverses all state changes made during the transaction—storage modifications, balance transfers, and contract creations—as if the transaction never occurred. The only persistent effect is that the sender pays gas for computation performed up to the out-of-gas point, preventing attackers from consuming validator resources without economic consequence.

Finalization reconciles gas accounting and applies remaining state changes. Unused gas returns to the sender as a refund. The transaction fee—consumed gas multiplied by gas price—transfers from the sender to the block proposer (miner or validator) as compensation for including the transaction. Storage refunds apply if the transaction deleted storage slots, clearing state from the trie. These refunds cap at 50% of total gas consumed to prevent exploitation where transactions deliberately trigger refunds to execute nearly-free computation.

### Determinism Constraints in Practice

Achieving determinism requires eliminating every source of environmental variation. The most obvious constraint is banning system clock access. Contracts cannot call `time()`, `clock_gettime()`, or query CPU timestamp counters. Instead, they access block timestamp—a consensus value agreed upon by validators, coarsely grained to seconds and manipulable by miners within a narrow window. Applications requiring precise timing must design around this limitation, using block numbers as a monotonic clock and tolerating validator-induced jitter.

Random number generation presents another challenge. Contracts cannot invoke `getrandom()` or read from `/dev/urandom` because these would produce different values on each validator. Naive solutions like hashing the block hash create predictability vulnerabilities: miners can manipulate block hashes by withholding blocks if the resulting random value is unfavorable. Robust randomness requires external oracles—trusted services that provide verifiable random functions (VRFs) with cryptographic proofs that the random value was generated honestly and cannot be predicted or biased. Chainlink VRF, for instance, combines block data with a secret key held by the oracle, producing a random value alongside a proof that validators can verify without learning the secret.

Floating-point arithmetic is prohibited entirely. IEEE 754 floating-point operations exhibit platform-dependent rounding behavior, especially for transcendental functions like `sin()` and `log()`. Even simple addition of three floating-point numbers can produce different results depending on whether the CPU executes `(a + b) + c` or `a + (b + c)` due to associativity violations under finite precision. Smart contracts use fixed-point arithmetic instead, representing fractional values as scaled integers. A decimal value like `3.14159` becomes `314159` with an implicit scaling factor of `10^5`. Addition and subtraction work identically to integer operations, while multiplication requires dividing by the scale factor afterward to maintain precision: `(a * b) / 10^5`.

External system calls are forbidden. Contracts cannot open files, spawn processes, or invoke OS APIs. The only interface to the outside world is the blockchain itself: contracts read transaction payloads, query block metadata (number, timestamp, proposer address), and call other contracts through message-passing opcodes like `CALL` and `DELEGATECALL`. This isolation ensures that execution depends solely on blockchain state, never on ephemeral system conditions like disk latency, network congestion, or CPU cache behavior.

## 3. High-Performance Optimization & Failure Modes

Writing gas-efficient contracts demands understanding the cost model's asymmetries and exploiting opcodes with favorable gas-to-utility ratios. The difference between a naive implementation and an optimized one can mean 10x variation in transaction costs, directly impacting protocol viability at scale.

### Storage Layout Optimization

Storage is the most expensive resource in the EVM. Reading a cold storage slot costs 200 gas, while warm access costs 100 gas. Writing is even more expensive: setting a zero slot to non-zero consumes 20,000 gas, while modifying an existing non-zero value costs 5,000 gas. These costs dwarf arithmetic operations—an `ADD` instruction costs 3 gas—making storage access the bottleneck in most contracts.

Packing multiple values into a single 256-bit storage slot amortizes these costs dramatically. Solidity supports struct packing: if a struct contains variables that collectively fit within 256 bits, the compiler allocates them contiguously in a single slot. A struct with `uint128 a; uint128 b;` occupies one slot, while `uint256 a; uint128 b;` spans two slots because `a` alone fills the first slot. Reading both values from the one-slot struct costs 200 gas (one cold `SLOAD`), while the two-slot struct costs 400 gas (two cold `SLOAD`s).

Bit manipulation extends packing efficiency further. Encoding boolean flags as individual bits in a `uint256` allows storing 256 booleans per slot. Setting bit `i` involves reading the slot, computing `value | (1 << i)`, and writing back—costing 5,200 gas (cold read + warm write) compared to 20,200 gas per boolean stored in separate slots. For infrequently accessed flags, this optimization is a 3.9x reduction.

Transient storage, introduced in EIP-1153, provides even cheaper ephemeral storage that clears after transaction completion. Useful for reentrancy locks and temporary state, transient storage costs 100 gas per access regardless of read or write, compared to 5,000+ gas for persistent storage modifications. Migrating locks from persistent to transient storage can reduce gas costs by 98% for high-frequency operations.

### Memory Expansion and Call Data Tricks

Memory expands dynamically as contracts access higher addresses, but expansion is not free. The first 724 bytes of memory cost 3 gas per 32-byte word. Beyond that, a quadratic term penalizes large allocations: the total cost is `3 * words + (words^2 / 512)`. A contract needing 10 KB of memory pays approximately 3,000 gas in linear costs plus 600 gas in quadratic overhead. This quadratic penalty discourages excessive memory use and incentivizes streaming algorithms that process data in small chunks rather than materializing large intermediate buffers.

Call data is immutable input provided by the transaction sender. Reading call data costs 3 gas per byte, far cheaper than loading from storage. Contracts can exploit this asymmetry by encoding lookup tables or configuration parameters in call data rather than storage. A contract performing signature verification can receive the precomputed elliptic curve points in call data instead of loading them from storage, trading a modest increase in transaction payload size for dramatic gas savings during execution.

The `CALLDATACOPY` opcode bulk-copies call data to memory at a cost of 3 gas per 32-byte word plus memory expansion costs. This is cheaper than iterating through call data with `CALLDATALOAD` in a loop because the single opcode avoids repeated stack manipulation and jump overhead. However, if the contract only needs a small fraction of the call data, selective `CALLDATALOAD` is more efficient than copying the entire payload into memory and paying expansion costs.

### Reentrancy and State Consistency

Reentrancy occurs when a contract calls an external contract that calls back into the original contract before the first call completes. This interleaving can violate state invariants if the contract updates balances or ownership before making the external call. The DAO hack of 2016, which drained $60 million in Ether, exploited precisely this pattern: a withdrawal function transferred funds before updating the user's balance, allowing the attacker to recursively call withdraw and drain the contract before the balance updated.

The checks-effects-interactions pattern defends against reentrancy by structuring functions into three phases. First, validate preconditions: does the user have sufficient balance? Second, update contract state to reflect the operation: deduct the withdrawal amount from the user's balance. Third, perform external interactions: transfer funds to the user. By updating state before external calls, the contract ensures that a reentrant call sees the updated balance and fails the precondition check.

Reentrancy guards provide a complementary defense by preventing nested calls entirely. A boolean state variable `locked` initializes to `false`. At function entry, the contract checks `require(!locked)` and then sets `locked = true`. Before returning, the function resets `locked = false`. Any reentrant call encounters the `require(!locked)` check while `locked = true` and reverts. Modern implementations use transient storage for the lock to avoid the 5,000-gas write penalty, reducing the overhead to 200 gas total (100 gas transient read + 100 gas transient write).

### Gas Limit Dynamics and Batching

Transactions carry individual gas limits, but blocks enforce an aggregate gas limit that caps total computation per block. Ethereum mainnet targets 15 million gas per 12-second block, equating to 1.25 million gas per second of sustained throughput. Operations that exhaust this budget must be redesigned as incremental algorithms that split work across multiple transactions.

Consider a contract managing an array of 10,000 elements where an administrative function must iterate through all elements and apply an update. If each iteration costs 5,000 gas (reading from storage, performing computation, writing back), the total cost is 50 million gas—exceeding the per-block limit by 3.3x. A naive implementation would revert out-of-gas partway through iteration, leaving the array in an inconsistent state with only the first few thousand elements updated.

Pagination solves this by accepting a start index and batch size, processing only a subset of elements per transaction. An administrative address calls the function repeatedly with `start = 0, batchSize = 100`, then `start = 100, batchSize = 100`, until all elements are processed. Each transaction costs 500,000 gas—comfortably within block limits—and the contract tracks progress in a storage variable to resume from the last processed index. The tradeoff is latency: instead of atomic completion in one block, the operation spans multiple blocks and remains vulnerable to frontrunning between batches if not carefully designed.

Merkle proofs enable non-interactive batching by committing to large datasets off-chain and verifying membership on-chain. A contract managing a whitelist of 1 million addresses cannot store all addresses in contract storage—the cost would be prohibitive at 20,000 gas per address, totaling 20 billion gas. Instead, the contract stores a single 32-byte Merkle root. Users prove membership by submitting the address and a Merkle proof (a sequence of hashes tracing from the leaf to the root). The contract recomputes the root from the proof and address, verifying it matches the stored root. Verification costs approximately 1,000 gas per proof level, so a tree of depth 20 (sufficient for 1 million leaves) validates in 20,000 gas—a million-fold improvement over naive storage.

### Halting and Partial Failure Recovery

Out-of-gas exceptions abort execution and revert all state changes, but the transaction still consumes gas up to the failure point. This creates denial-of-service vulnerabilities if an attacker can repeatedly force gas exhaustion in another user's transactions. A contract with an unbounded loop over user-submitted data allows attackers to submit payloads that exceed gas limits, causing legitimate users' transactions to fail and burn their gas budgets without accomplishing useful work.

Defensive programming constrains unbounded operations through sentinel values and early returns. Instead of iterating until a condition is met, the contract iterates for a fixed maximum count and returns early if the target is found. A function searching an array for a specific value might loop through 100 elements maximum, returning early if found or signaling failure if not found within 100 iterations. This trades completeness (the value might exist beyond element 100) for guaranteed halting within a known gas budget.

Try-catch blocks, introduced in Solidity 0.6, allow contracts to recover from external call failures without reverting the entire transaction. When calling an untrusted external contract, wrapping the call in a try block allows the contract to catch reverts, out-of-gas exceptions, and assertion failures from the callee. The catch block can log the failure, return a default value, or attempt an alternative code path. This isolation prevents cascading failures where one malicious contract causes unrelated transactions to revert.

Gas estimation tools simulate transaction execution off-chain to predict gas consumption before submitting to the network. The `eth_estimateGas` RPC method runs the transaction in a sandboxed environment and returns the gas used. Wallets and DApps multiply this estimate by 1.2–1.5x as a safety margin to account for state changes between estimation and execution. Without this buffer, transactions estimated at 99,000 gas might fail at 101,000 gas if storage costs increase due to concurrent activity, wasting users' fees and degrading application reliability.
