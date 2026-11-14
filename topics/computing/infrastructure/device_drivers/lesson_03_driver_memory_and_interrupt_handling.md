# Lesson 3: Kernel Memory Management & Interrupt Handling in Device Drivers

Device drivers operate at the intersection of hardware and kernel software, managing resources under constraints that don't exist in user space: no paging protection, tight timing requirements, concurrent hardware events, and direct memory access from devices. This lesson dissects kernel memory allocation strategies and interrupt handling patterns that separate production-grade drivers from fragile prototypes.

## 1. Architectural Foundations & Invariants

### 1.1 The Kernel Memory Landscape

Unlike user space with its generous virtual memory and demand paging, kernel code runs in a constrained physical memory region where allocation failures are real and consequences are immediate. The kernel divides its address space into distinct zones, each serving specific hardware and allocation requirements.

```
Kernel Virtual Address Space Layout (x86_64)
┌─────────────────────────────────────┐ 0xFFFFFFFFFFFFFFFF
│   Fixmap & vsyscall                 │
├─────────────────────────────────────┤ 0xFFFFFFFF80000000
│   Direct mapping of all physical    │
│   RAM (PAGE_OFFSET)                 │ <- kmalloc operates here
│   - Physically contiguous           │
│   - Immediate access, no TLB miss   │
├─────────────────────────────────────┤
│   vmalloc/ioremap area              │ <- vmalloc operates here
│   - Virtually contiguous only       │
│   - Can map discontiguous pages     │
├─────────────────────────────────────┤
│   Kernel modules (.text, .data)     │
└─────────────────────────────────────┘
```

The direct mapping zone provides the fastest access because virtual-to-physical translation is a simple offset subtraction (`__pa()` macro). Hardware devices performing DMA must use physical addresses from this region, and most driver allocations target it through `kmalloc()`.

### 1.2 DMA Architecture & Cache Coherency

Direct Memory Access allows devices to transfer data to/from RAM without CPU intervention, but introduces coherency challenges. Modern architectures have evolved three principal DMA models:

**Coherent DMA**: Hardware automatically maintains cache coherency between CPU and device views of memory. Most x86_64 systems implement this through cache snooping—when a device writes to memory, it invalidates corresponding CPU cache lines. ARM and PowerPC systems often require explicit coherency domains.

**Streaming DMA**: One-directional transfers where the driver explicitly synchronizes ownership between CPU and device using barrier instructions and cache operations.

**Bounce Buffering**: Legacy or constrained devices that can only address limited physical memory ranges (e.g., 24-bit address bus). The kernel maintains intermediate buffers in addressable memory and copies data to/from the actual target.

```c
/*
 * DMA Addressing Capabilities
 * These bitmasks inform the DMA subsystem which physical addresses
 * your device can reach.
 */
#define DMA_BIT_MASK(n)  (((n) == 64) ? ~0ULL : ((1ULL << (n)) - 1))

// 32-bit device: can address 4GB
dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(32));

// Modern PCIe device: 64-bit addressing
dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(64));

// Legacy ISA device: 24-bit addressing (16MB)
dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(24));
```

The kernel's DMA mapping API abstracts these differences. You describe your transfer semantics, and the subsystem handles architecture-specific cache maintenance, IOMMU programming, and bounce buffer allocation.

### 1.3 Interrupt Context & Execution Models

Hardware interrupts preempt normal kernel execution, transferring control to registered handlers. The kernel maintains invariants that shape driver design:

**IRQ Context Rules**:
- Cannot sleep or schedule
- Cannot call functions that might sleep (`kmalloc(GFP_KERNEL)`, `mutex_lock()`, `copy_to_user()`)
- Stack space is limited (historically 4KB, now typically 8KB but still constrained)
- Should complete quickly (<1ms typical guideline)
- Interrupts may be disabled on the local CPU

**Process Context Rules**:
- Can sleep, schedule, and page fault
- Can use full suite of synchronization primitives
- Has larger stack and full preemption support

This dichotomy drives the split-handler model: interrupt handlers do minimal work (acknowledge hardware, grab data from device registers) while deferring complex processing to schedulable contexts.

```
Interrupt Execution Flow
══════════════════════════

Hardware event → CPU interrupt line → IDT/Vector table
    ↓
do_IRQ() [arch-specific entry]
    ↓
handle_irq() [generic layer]
    ↓
┌──────────────────────────────────────┐
│ Primary Handler (hardirq context)    │  <- Your handler
│ - IRQs disabled on local CPU         │
│ - Atomic context                     │
│ - Acknowledge hardware               │
│ - Schedule deferred work             │
└──────────────────────────────────────┘
    ↓
Return to interrupted context
    ↓
[Later, when kernel schedules deferred work]
    ↓
┌──────────────────────────────────────┐
│ Bottom Half (softirq/tasklet/work)   │
│ - IRQs enabled                       │
│ - Can acquire locks                  │
│ - Process bulk data                  │
└──────────────────────────────────────┘
```

### 1.4 Memory Allocation Cost Model

Understanding allocation overhead guides design decisions:

| Allocator | Latency | Contiguity | Max Size | Failure Mode |
|-----------|---------|------------|----------|--------------|
| `kmalloc()` | O(1) fast | Physical | ~4MB | Returns NULL immediately |
| `vmalloc()` | O(n) slow | Virtual only | ~memory size | Returns NULL, may stall reclaiming |
| `get_free_pages()` | O(log n) | Physical | 2^(MAX_ORDER-1) pages | Returns NULL |
| `dma_alloc_coherent()` | Slow | Physical | Architecture limited | Returns NULL |
| `alloc_pages()` | O(log n) | Physical | 2^(MAX_ORDER-1) pages | Returns NULL |

The buddy allocator underlying `kmalloc()` maintains free lists organized by power-of-two orders. Requesting 1KB actually allocates 1KB, but requesting 1025 bytes allocates 2KB. Internal fragmentation is inherent to the design.

```c
/*
 * Memory allocation strategy decision tree
 */
void *allocate_driver_buffer(size_t size, gfp_t flags)
{
    // Small, DMA-capable buffer needed immediately
    if (size <= PAGE_SIZE && (flags & __GFP_DMA)) {
        return kmalloc(size, flags);
    }
    
    // Large buffer, no DMA requirement, can tolerate latency
    if (size > PAGE_SIZE * 4 && !(flags & __GFP_DMA)) {
        return vmalloc(size);
    }
    
    // Large, physically contiguous for DMA
    if (size > PAGE_SIZE && (flags & __GFP_DMA)) {
        return dma_alloc_coherent(dev, size, &dma_handle, flags);
    }
    
    return kmalloc(size, flags);
}
```

## 2. Core Mechanics & Data Structures

### 2.1 Kernel Memory Allocators: kmalloc vs vmalloc

The `kmalloc()` family provides small, physically contiguous allocations from the SLAB/SLUB allocator (modern kernels use SLUB). Each allocation comes from per-CPU caches of commonly-sized objects, minimizing lock contention.

```c
#include <linux/slab.h>
#include <linux/gfp.h>

/*
 * GFP (Get Free Pages) flags control allocation behavior
 */
struct driver_context {
    void *command_buffer;
    void *data_buffer;
    struct work_struct deferred_work;
};

static int driver_probe(struct pci_dev *pdev, const struct pci_device_id *id)
{
    struct driver_context *ctx;
    
    // GFP_KERNEL: May sleep, reclaim pages, suitable for process context
    ctx = kmalloc(sizeof(*ctx), GFP_KERNEL);
    if (!ctx)
        return -ENOMEM;
    
    // Allocate DMA-capable buffer (must be in DMA zone)
    ctx->command_buffer = kmalloc(4096, GFP_KERNEL | GFP_DMA);
    if (!ctx->command_buffer) {
        kfree(ctx);
        return -ENOMEM;
    }
    
    // Zero-initialized allocation
    ctx->data_buffer = kzalloc(8192, GFP_KERNEL);
    if (!ctx->data_buffer) {
        kfree(ctx->command_buffer);
        kfree(ctx);
        return -ENOMEM;
    }
    
    pci_set_drvdata(pdev, ctx);
    return 0;
}

static irqreturn_t driver_irq_handler(int irq, void *dev_id)
{
    struct driver_context *ctx = dev_id;
    u32 *temp_buf;
    
    // GFP_ATOMIC: Cannot sleep, uses emergency reserves
    // Required in interrupt context
    temp_buf = kmalloc(512, GFP_ATOMIC);
    if (!temp_buf) {
        // Must handle gracefully—allocation can fail
        pr_err("Failed to allocate IRQ buffer\n");
        return IRQ_HANDLED;
    }
    
    // Process data...
    
    kfree(temp_buf);
    return IRQ_HANDLED;
}
```

The `vmalloc()` allocator handles large requests by mapping discontiguous physical pages into contiguous kernel virtual address space. This requires page table manipulation and TLB flushes, making it significantly slower than `kmalloc()`.

```c
#include <linux/vmalloc.h>

/*
 * Example: Large ring buffer for logging
 * DMA not required, size exceeds typical kmalloc limit
 */
#define RING_BUFFER_SIZE (16 * 1024 * 1024)  // 16MB

struct logging_device {
    void *ring_buffer;
    unsigned long write_offset;
    spinlock_t lock;
};

static int logging_init(struct logging_device *ldev)
{
    // vmalloc can satisfy large allocations that kmalloc cannot
    ldev->ring_buffer = vmalloc(RING_BUFFER_SIZE);
    if (!ldev->ring_buffer)
        return -ENOMEM;
    
    // Can also get zero-initialized memory
    // ldev->ring_buffer = vzalloc(RING_BUFFER_SIZE);
    
    ldev->write_offset = 0;
    spin_lock_init(&ldev->lock);
    
    pr_info("Allocated %zu MB ring buffer at %p (virtual)\n",
            RING_BUFFER_SIZE / (1024*1024), ldev->ring_buffer);
    
    return 0;
}

static void logging_cleanup(struct logging_device *ldev)
{
    vfree(ldev->ring_buffer);  // Note: vfree, not kfree
}

/*
 * Important: Cannot use vmalloc memory for DMA
 * Physical pages are discontiguous
 */
static int bad_dma_setup(struct device *dev, void *vmalloc_buf)
{
    dma_addr_t dma_handle;
    
    // This is WRONG—will cause data corruption or hardware faults
    // dma_handle = dma_map_single(dev, vmalloc_buf, 4096, DMA_TO_DEVICE);
    
    return -EINVAL;  // Don't do this
}
```

### 2.2 DMA Buffer Management

The DMA API provides two primary interfaces: coherent (consistent) mappings for bidirectional, long-lived buffers; and streaming mappings for one-shot, directional transfers.

#### 2.2.1 Coherent DMA Mappings

Coherent mappings establish permanent CPU-device shared memory. The kernel returns both a CPU-accessible virtual address and a device-usable physical (bus) address.

```c
#include <linux/dma-mapping.h>

struct dma_device_context {
    struct device *dev;
    
    // Descriptor ring (coherent mapping)
    void *descriptor_ring_cpu;      // CPU virtual address
    dma_addr_t descriptor_ring_dma; // Bus address for device
    size_t descriptor_ring_size;
    
    // Data buffers (streaming mappings)
    void *data_buffers[32];
    dma_addr_t data_buffers_dma[32];
};

static int setup_dma_resources(struct dma_device_context *dctx)
{
    int i;
    
    // Allocate coherent descriptor ring
    // Device and CPU both see the same view, no explicit sync needed
    dctx->descriptor_ring_size = PAGE_SIZE;
    dctx->descriptor_ring_cpu = dma_alloc_coherent(
        dctx->dev,
        dctx->descriptor_ring_size,
        &dctx->descriptor_ring_dma,
        GFP_KERNEL
    );
    
    if (!dctx->descriptor_ring_cpu)
        return -ENOMEM;
    
    // Write descriptor ring base address to device register
    writel(lower_32_bits(dctx->descriptor_ring_dma), 
           dctx->dev->mem_base + DESC_RING_ADDR_LO);
    writel(upper_32_bits(dctx->descriptor_ring_dma),
           dctx->dev->mem_base + DESC_RING_ADDR_HI);
    
    // Allocate streaming DMA buffers
    for (i = 0; i < 32; i++) {
        dctx->data_buffers[i] = kmalloc(4096, GFP_KERNEL);
        if (!dctx->data_buffers[i])
            goto cleanup_buffers;
        
        // Don't map yet—map when starting transfer
        dctx->data_buffers_dma[i] = 0;
    }
    
    return 0;
    
cleanup_buffers:
    while (--i >= 0)
        kfree(dctx->data_buffers[i]);
    dma_free_coherent(dctx->dev, dctx->descriptor_ring_size,
                      dctx->descriptor_ring_cpu, dctx->descriptor_ring_dma);
    return -ENOMEM;
}

static void teardown_dma_resources(struct dma_device_context *dctx)
{
    int i;
    
    // Unmap any active streaming mappings first
    for (i = 0; i < 32; i++) {
        if (dctx->data_buffers_dma[i]) {
            dma_unmap_single(dctx->dev, dctx->data_buffers_dma[i],
                           4096, DMA_FROM_DEVICE);
        }
        kfree(dctx->data_buffers[i]);
    }
    
    // Free coherent mapping
    dma_free_coherent(dctx->dev, dctx->descriptor_ring_size,
                      dctx->descriptor_ring_cpu, dctx->descriptor_ring_dma);
}
```

#### 2.2.2 Streaming DMA Mappings

Streaming mappings optimize for unidirectional transfers. The driver maps buffers immediately before use and unmaps afterward, allowing the kernel to perform necessary cache maintenance.

```c
/*
 * Streaming DMA example: Network packet transmission
 */
struct packet_descriptor {
    dma_addr_t buffer_addr;
    u32 length;
    u32 flags;
} __aligned(16);

static int transmit_packet(struct dma_device_context *dctx,
                          struct sk_buff *skb, int desc_idx)
{
    struct packet_descriptor *desc;
    dma_addr_t dma_addr;
    
    // Map SKB data for device access
    dma_addr = dma_map_single(dctx->dev, skb->data, skb->len, DMA_TO_DEVICE);
    if (dma_mapping_error(dctx->dev, dma_addr)) {
        pr_err("DMA mapping failed\n");
        return -ENOMEM;
    }
    
    // Write descriptor in coherent ring
    desc = &((struct packet_descriptor *)dctx->descriptor_ring_cpu)[desc_idx];
    desc->buffer_addr = dma_addr;
    desc->length = skb->len;
    desc->flags = DESC_FLAG_VALID | DESC_FLAG_INTERRUPT;
    
    // Ensure descriptor write completes before notifying device
    wmb();
    
    // Notify device: new descriptor available
    writel(desc_idx, dctx->dev->mem_base + DESC_TAIL_PTR);
    
    return 0;
}

static void transmit_complete(struct dma_device_context *dctx, int desc_idx)
{
    struct packet_descriptor *desc;
    
    desc = &((struct packet_descriptor *)dctx->descriptor_ring_cpu)[desc_idx];
    
    // Unmap after device finishes
    dma_unmap_single(dctx->dev, desc->buffer_addr, 
                    desc->length, DMA_TO_DEVICE);
    
    // Free the SKB
    dev_kfree_skb_irq(desc->private_skb);
}

/*
 * Bidirectional mapping: Device updates metadata
 */
static int start_block_io(struct dma_device_context *dctx, 
                          void *buffer, size_t len)
{
    dma_addr_t dma_addr;
    
    dma_addr = dma_map_single(dctx->dev, buffer, len, DMA_BIDIRECTIONAL);
    if (dma_mapping_error(dctx->dev, dma_addr))
        return -ENOMEM;
    
    // Program device registers
    writeq(dma_addr, dctx->dev->mem_base + BLK_DMA_ADDR);
    writel(len, dctx->dev->mem_base + BLK_DMA_LEN);
    writel(BLK_CMD_START, dctx->dev->mem_base + BLK_COMMAND);
    
    return 0;
}

static void complete_block_io(struct dma_device_context *dctx,
                             void *buffer, size_t len)
{
    dma_addr_t dma_addr;
    
    // Retrieve saved DMA address (in real driver, store in per-request struct)
    dma_addr = readq(dctx->dev->mem_base + BLK_DMA_ADDR);
    
    // Sync CPU cache before reading device-modified data
    dma_sync_single_for_cpu(dctx->dev, dma_addr, len, DMA_BIDIRECTIONAL);
    
    // Now safe to read buffer on CPU
    // process_data(buffer, len);
    
    // Unmap when completely done
    dma_unmap_single(dctx->dev, dma_addr, len, DMA_BIDIRECTIONAL);
}
```

#### 2.2.3 Scatter-Gather DMA

Modern devices support scatter-gather lists, allowing a single DMA operation to transfer discontiguous memory regions. This eliminates copying data into contiguous staging buffers.

```c
#include <linux/scatterlist.h>

struct sg_dma_request {
    struct scatterlist *sgl;
    int nents;              // Number of SG entries
    int mapped_nents;       // Entries after IOMMU coalescing
};

static int setup_sg_transfer(struct dma_device_context *dctx,
                             struct page **pages, int page_count)
{
    struct sg_dma_request *req;
    int i;
    
    req = kzalloc(sizeof(*req), GFP_KERNEL);
    if (!req)
        return -ENOMEM;
    
    // Allocate scatter-gather list
    req->sgl = kmalloc_array(page_count, sizeof(struct scatterlist), 
                            GFP_KERNEL);
    if (!req->sgl) {
        kfree(req);
        return -ENOMEM;
    }
    
    // Initialize SG list
    sg_init_table(req->sgl, page_count);
    
    // Populate with pages
    for (i = 0; i < page_count; i++) {
        sg_set_page(&req->sgl[i], pages[i], PAGE_SIZE, 0);
    }
    
    req->nents = page_count;
    
    // Map for DMA—may coalesce adjacent physical pages
    req->mapped_nents = dma_map_sg(dctx->dev, req->sgl, req->nents,
                                   DMA_BIDIRECTIONAL);
    if (req->mapped_nents == 0) {
        kfree(req->sgl);
        kfree(req);
        return -ENOMEM;
    }
    
    // Program device with resulting DMA addresses
    for_each_sg(req->sgl, sg, req->mapped_nents, i) {
        dma_addr_t addr = sg_dma_address(sg);
        unsigned int len = sg_dma_len(sg);
        
        // Write to device descriptor ring or registers
        program_device_sg_entry(dctx, i, addr, len);
    }
    
    return 0;
}

static void cleanup_sg_transfer(struct dma_device_context *dctx,
                               struct sg_dma_request *req)
{
    dma_unmap_sg(dctx->dev, req->sgl, req->nents, DMA_BIDIRECTIONAL);
    kfree(req->sgl);
    kfree(req);
}

/*
 * Example: DMA from user-space buffer (zero-copy I/O)
 */
static int start_user_dma(struct dma_device_context *dctx,
                         unsigned long user_addr, size_t len)
{
    struct page **pages;
    int page_count, pinned;
    
    page_count = (len + PAGE_SIZE - 1) >> PAGE_SHIFT;
    pages = kmalloc_array(page_count, sizeof(*pages), GFP_KERNEL);
    if (!pages)
        return -ENOMEM;
    
    // Pin user pages in memory
    mmap_read_lock(current->mm);
    pinned = get_user_pages(user_addr & PAGE_MASK, page_count,
                          FOLL_WRITE, pages, NULL);
    mmap_read_unlock(current->mm);
    
    if (pinned != page_count) {
        while (--pinned >= 0)
            put_page(pages[pinned]);
        kfree(pages);
        return -EFAULT;
    }
    
    // Setup and execute SG DMA
    setup_sg_transfer(dctx, pages, page_count);
    
    return 0;
}
```

### 2.3 Interrupt Handling Architecture

The Linux interrupt subsystem has evolved from simple top-half/bottom-half splits to a sophisticated framework supporting nested interrupt controllers, per-CPU interrupt affinity, and threaded handlers.

#### 2.3.1 Primary Interrupt Handlers

The primary handler executes in hardirq context with strict constraints. It must acknowledge the hardware interrupt, capture volatile state, and return quickly.

```c
#include <linux/interrupt.h>

struct device_state {
    void __iomem *mmio_base;
    spinlock_t lock;
    
    // Interrupt statistics
    atomic_t interrupt_count;
    atomic_t spurious_count;
    
    // Deferred work
    struct tasklet_struct rx_tasklet;
    struct work_struct tx_workqueue;
};

/*
 * Primary interrupt handler—minimal work only
 */
static irqreturn_t device_irq_handler(int irq, void *dev_id)
{
    struct device_state *state = dev_id;
    u32 int_status;
    irqreturn_t ret = IRQ_NONE;
    
    // Read interrupt status register
    int_status = readl(state->mmio_base + REG_INT_STATUS);
    if (!int_status)
        return IRQ_NONE;  // Spurious or shared IRQ
    
    // Acknowledge interrupt immediately
    writel(int_status, state->mmio_base + REG_INT_ACK);
    
    atomic_inc(&state->interrupt_count);
    
    // Handle critical events inline
    if (int_status & INT_FATAL_ERROR) {
        // Log and disable device
        writel(0, state->mmio_base + REG_CONTROL);
        pr_crit("Device fatal error: 0x%08x\n", int_status);
        ret = IRQ_HANDLED;
    }
    
    // Schedule deferred processing for bulk work
    if (int_status & INT_RX_COMPLETE) {
        tasklet_schedule(&state->rx_tasklet);
        ret = IRQ_HANDLED;
    }
    
    if (int_status & INT_TX_COMPLETE) {
        schedule_work(&state->tx_workqueue);
        ret = IRQ_HANDLED;
    }
    
    return ret;
}

/*
 * Request IRQ with appropriate flags
 */
static int device_request_irq(struct pci_dev *pdev, struct device_state *state)
{
    int ret;
    
    // IRQF_SHARED: IRQ may be shared with other devices
    // Name appears in /proc/interrupts
    ret = request_irq(pdev->irq, device_irq_handler,
                     IRQF_SHARED, "mydevice", state);
    if (ret) {
        dev_err(&pdev->dev, "Failed to request IRQ %d: %d\n",
                pdev->irq, ret);
        return ret;
    }
    
    return 0;
}

/*
 * MSI/MSI-X setup for modern devices
 */
static int device_setup_msi(struct pci_dev *pdev, struct device_state *state)
{
    int nvec, ret, i;
    struct msix_entry msix_entries[4];
    
    // Try MSI-X first (supports per-vector affinity)
    for (i = 0; i < 4; i++)
        msix_entries[i].entry = i;
    
    nvec = pci_enable_msix_range(pdev, msix_entries, 1, 4);
    if (nvec > 0) {
        for (i = 0; i < nvec; i++) {
            ret = request_irq(msix_entries[i].vector,
                            device_irq_handler, 0,
                            "mydevice-msix", state);
            if (ret) {
                while (--i >= 0)
                    free_irq(msix_entries[i].vector, state);
                pci_disable_msix(pdev);
                return ret;
            }
        }
        dev_info(&pdev->dev, "Using MSI-X with %d vectors\n", nvec);
        return 0;
    }
    
    // Fall back to MSI
    nvec = pci_enable_msi_range(pdev, 1, 1);
    if (nvec > 0) {
        ret = request_irq(pdev->irq, device_irq_handler, 0,
                         "mydevice-msi", state);
        if (ret) {
            pci_disable_msi(pdev);
            return ret;
        }
        dev_info(&pdev->dev, "Using MSI\n");
        return 0;
    }
    
    // Fall back to legacy INTx
    return device_request_irq(pdev, state);
}
```

#### 2.3.2 Tasklets: Lightweight Deferred Processing

Tasklets execute in softirq context—interrupts are enabled, but the tasklet itself cannot sleep. They're scheduled per-CPU and run at the next softirq processing point.

```c
/*
 * Tasklet for RX packet processing
 * Runs in softirq context: IRQs enabled, cannot sleep
 */
static void rx_tasklet_func(unsigned long data)
{
    struct device_state *state = (struct device_state *)data;
    u32 rx_status;
    int packets_processed = 0;
    
    // Process received packets
    while (packets_processed < 64) {  // Budget to prevent starvation
        struct sk_buff *skb;
        dma_addr_t dma_addr;
        unsigned int len;
        
        rx_status = readl(state->mmio_base + REG_RX_STATUS);
        if (!(rx_status & RX_PACKET_READY))
            break;
        
        len = rx_status & RX_LEN_MASK;
        dma_addr = readq(state->mmio_base + REG_RX_DMA_ADDR);
        
        // Unmap DMA buffer
        dma_unmap_single(&state->pdev->dev, dma_addr, len, DMA_FROM_DEVICE);
        
        // Allocate SKB and copy data
        skb = netdev_alloc_skb(state->netdev, len);
        if (skb) {
            memcpy(skb_put(skb, len), state->rx_buffer, len);
            skb->protocol = eth_type_trans(skb, state->netdev);
            netif_rx(skb);  // Submit to network stack
        } else {
            state->netdev->stats.rx_dropped++;
        }
        
        packets_processed++;
    }
    
    // Re-enable RX interrupts
    writel(INT_RX_ENABLE, state->mmio_base + REG_INT_ENABLE);
}

static void device_init_tasklet(struct device_state *state)
{
    tasklet_init(&state->rx_tasklet, rx_tasklet_func, 
                (unsigned long)state);
}

static void device_cleanup_tasklet(struct device_state *state)
{
    tasklet_kill(&state->rx_tasklet);  // Wait for completion
}
```

#### 2.3.3 Workqueues: Schedulable Context

Workqueues run in process context, allowing them to sleep, acquire mutexes, and perform I/O. They're appropriate for lengthy operations that cannot complete in interrupt or softirq context.

```c
#include <linux/workqueue.h>

/*
 * Work handler for TX completion cleanup
 * Runs in process context: can sleep, full preemption
 */
static void tx_work_func(struct work_struct *work)
{
    struct device_state *state = container_of(work, struct device_state,
                                             tx_workqueue);
    int i;
    
    mutex_lock(&state->tx_lock);  // Can acquire mutex (sleepable)
    
    // Process completed TX descriptors
    for (i = 0; i < state->tx_ring_size; i++) {
        struct tx_descriptor *desc = &state->tx_ring[i];
        
        if (!(desc->status & TX_COMPLETE))
            continue;
        
        // Unmap and free SKB
        dma_unmap_single(&state->pdev->dev, desc->dma_addr,
                        desc->len, DMA_TO_DEVICE);
        dev_kfree_skb(desc->skb);
        
        desc->status = 0;
        state->tx_available++;
    }
    
    mutex_unlock(&state->tx_lock);
    
    // Wake TX queue if it was stopped
    if (netif_queue_stopped(state->netdev) && 
        state->tx_available >= TX_WAKE_THRESHOLD) {
        netif_wake_queue(state->netdev);
    }
}

static void device_init_workqueue(struct device_state *state)
{
    INIT_WORK(&state->tx_workqueue, tx_work_func);
}

/*
 * Using dedicated workqueue for isolation
 */
static struct workqueue_struct *device_wq;

static int __init device_module_init(void)
{
    // Create dedicated single-threaded workqueue
    device_wq = create_singlethread_workqueue("mydevice_wq");
    if (!device_wq)
        return -ENOMEM;
    
    return 0;
}

static void __exit device_module_exit(void)
{
    destroy_workqueue(device_wq);  // Waits for pending work
}

static void device_schedule_work(struct device_state *state)
{
    queue_work(device_wq, &state->tx_workqueue);
}
```

#### 2.3.4 Threaded IRQ Handlers

Modern kernels support threaded interrupt handlers, which run in a dedicated kernel thread context. This simplifies driver design by eliminating the need for explicit tasklets or workqueues.

```c
/*
 * Threaded IRQ handler pattern
 * Primary handler runs in hardirq context (fast path)
 * Thread handler runs in process context (slow path)
 */
static irqreturn_t device_irq_quick(int irq, void *dev_id)
{
    struct device_state *state = dev_id;
    u32 int_status;
    
    int_status = readl(state->mmio_base + REG_INT_STATUS);
    if (!int_status)
        return IRQ_NONE;
    
    // Disable interrupts at device level
    writel(0, state->mmio_base + REG_INT_ENABLE);
    
    // Acknowledge hardware
    writel(int_status, state->mmio_base + REG_INT_ACK);
    
    // Store status for thread handler
    state->pending_int_status = int_status;
    
    // Return IRQ_WAKE_THREAD to invoke thread handler
    return IRQ_WAKE_THREAD;
}

static irqreturn_t device_irq_thread(int irq, void *dev_id)
{
    struct device_state *state = dev_id;
    u32 int_status = state->pending_int_status;
    
    // Process in thread context—can sleep, acquire mutex, etc.
    if (int_status & INT_RX_COMPLETE) {
        mutex_lock(&state->rx_lock);
        process_received_data(state);
        mutex_unlock(&state->rx_lock);
    }
    
    if (int_status & INT_TX_COMPLETE) {
        mutex_lock(&state->tx_lock);
        cleanup_transmitted_buffers(state);
        mutex_unlock(&state->tx_lock);
    }
    
    // Re-enable interrupts
    writel(INT_ENABLE_MASK, state->mmio_base + REG_INT_ENABLE);
    
    return IRQ_HANDLED;
}

static int device_request_threaded_irq(struct pci_dev *pdev,
                                      struct device_state *state)
{
    int ret;
    
    ret = request_threaded_irq(
        pdev->irq,
        device_irq_quick,      // Fast primary handler
        device_irq_thread,     // Threaded handler
        IRQF_SHARED | IRQF_ONESHOT,  // ONESHOT: mask IRQ until thread completes
        "mydevice",
        state
    );
    
    return ret;
}
```

### 2.4 Synchronization in Interrupt Context

Race conditions between interrupt handlers and process-context code require careful synchronization. The kernel provides primitives with varying semantics and performance characteristics.

```c
/*
 * Spinlock: Protects data accessed from interrupt and process context
 */
struct shared_device_data {
    spinlock_t lock;
    u32 register_cache;
    int pending_requests;
    struct list_head request_queue;
};

/*
 * Process context: Disable local IRQs before acquiring
 */
static void update_from_process_context(struct shared_device_data *data)
{
    unsigned long flags;
    
    // spin_lock_irqsave: Disable local IRQs, save state, acquire lock
    spin_lock_irqsave(&data->lock, flags);
    
    data->register_cache = readl(data->mmio + REG_STATUS);
    data->pending_requests++;
    
    spin_unlock_irqrestore(&data->lock, flags);
}

/*
 * Interrupt context: Already has IRQs disabled on this CPU
 */
static irqreturn_t device_irq_with_spinlock(int irq, void *dev_id)
{
    struct shared_device_data *data = dev_id;
    
    // spin_lock: Just acquire lock, IRQs already disabled
    spin_lock(&data->lock);
    
    data->register_cache = readl(data->mmio + REG_INT_STATUS);
    data->pending_requests--;
    
    spin_unlock(&data->lock);
    
    return IRQ_HANDLED;
}

/*
 * Producer-consumer pattern with lock-free ring buffer
 * Single producer (IRQ), single consumer (kthread)
 */
#define RING_SIZE 256
#define RING_MASK (RING_SIZE - 1)

struct lockfree_ring {
    struct event_data events[RING_SIZE];
    unsigned long head;  // Producer writes here (atomic)
    unsigned long tail;  // Consumer reads here (atomic)
};

static int ring_produce(struct lockfree_ring *ring, struct event_data *event)
{
    unsigned long head = atomic_long_read(&ring->head);
    unsigned long next_head = (head + 1) & RING_MASK;
    
    // Check if ring is full
    if (next_head == atomic_long_read(&ring->tail))
        return -ENOSPC;
    
    // Write data
    ring->events[head] = *event;
    
    // Memory barrier ensures data write completes before updating head
    smp_wmb();
    
    // Advance head
    atomic_long_set(&ring->head, next_head);
    
    return 0;
}

static int ring_consume(struct lockfree_ring *ring, struct event_data *event)
{
    unsigned long tail = atomic_long_read(&ring->tail);
    unsigned long head = atomic_long_read(&ring->head);
    
    // Check if ring is empty
    if (tail == head)
        return -ENODATA;
    
    // Read data
    *event = ring->events[tail];
    
    // Memory barrier ensures data read completes before updating tail
    smp_rmb();
    
    // Advance tail
    atomic_long_set(&ring->tail, (tail + 1) & RING_MASK);
    
    return 0;
}
```

## 3. High-Performance Optimization & Failure Modes

### 3.1 Memory Access Patterns & Cache Optimization

Modern CPUs feature deep cache hierarchies. Access patterns that exploit spatial and temporal locality deliver order-of-magnitude performance improvements.

```c
/*
 * Cache-aligned structures for hot-path data
 * L1 cache line is typically 64 bytes
 */
#define CACHE_LINE_SIZE 64

struct __aligned(CACHE_LINE_SIZE) tx_queue {
    // Hot fields accessed every packet
    u32 head;
    u32 tail;
    spinlock_t lock;
    
    // Padding to prevent false sharing with next structure
    u8 pad1[CACHE_LINE_SIZE - sizeof(u32) - sizeof(u32) - sizeof(spinlock_t)];
    
    // Warm fields accessed less frequently
    u32 size;
    struct tx_descriptor *descriptors;
    dma_addr_t descriptors_dma;
    
    u8 pad2[CACHE_LINE_SIZE - sizeof(u32) - sizeof(void*) - sizeof(dma_addr_t)];
} ____cacheline_aligned;

/*
 * Bad: False sharing between producer and consumer
 */
struct bad_ring {
    u32 producer_index;  // CPU 0 writes
    u32 consumer_index;  // CPU 1 writes
    // Both on same cache line—continuous cache line bouncing
};

/*
 * Good: Separate cache lines
 */
struct good_ring {
    u32 producer_index;
    u8 pad1[CACHE_LINE_SIZE - sizeof(u32)];
    u32 consumer_index;
    u8 pad2[CACHE_LINE_SIZE - sizeof(u32)];
} ____cacheline_aligned;

/*
 * Batch processing to amortize overhead
 */
static void process_rx_ring_batched(struct device_state *state)
{
    struct rx_descriptor *desc;
    struct sk_buff *skb_batch[32];
    int batch_count = 0;
    int i;
    
    // Accumulate a batch
    while (batch_count < 32) {
        desc = &state->rx_ring[state->rx_head];
        if (!(desc->status & RX_COMPLETE))
            break;
        
        // Prefetch next descriptor to hide latency
        prefetch(&state->rx_ring[(state->rx_head + 1) & RX_RING_MASK]);
        
        skb_batch[batch_count++] = desc->skb;
        state->rx_head = (state->rx_head + 1) & RX_RING_MASK;
    }
    
    // Process batch—better cache locality, amortized overhead
    for (i = 0; i < batch_count; i++) {
        netif_receive_skb(skb_batch[i]);
    }
}

/*
 * Use per-CPU variables to eliminate cache bouncing
 */
struct device_percpu_stats {
    u64 packets;
    u64 bytes;
    u64 errors;
} ____cacheline_aligned;

static DEFINE_PER_CPU(struct device_percpu_stats, device_stats);

static void record_packet_percpu(int len)
{
    struct device_percpu_stats *stats = this_cpu_ptr(&device_stats);
    
    stats->packets++;
    stats->bytes += len;
    // No lock needed—each CPU has its own copy
}

static void aggregate_stats(struct device_state *state)
{
    struct device_percpu_stats *stats;
    int cpu;
    
    state->total_packets = 0;
    state->total_bytes = 0;
    
    for_each_possible_cpu(cpu) {
        stats = per_cpu_ptr(&device_stats, cpu);
        state->total_packets += stats->packets;
        state->total_bytes += stats->bytes;
    }
}
```

### 3.2 Interrupt Mitigation Strategies

High-throughput devices can generate millions of interrupts per second. Interrupt coalescing reduces overhead by batching events.

```c
/*
 * Adaptive interrupt moderation
 * Adjust coalescing thresholds based on load
 */
#define IRQ_COAL_USECS_LOW  10    // High load: coalesce aggressively
#define IRQ_COAL_USECS_HIGH 200   // Low load: coalesce less, reduce latency
#define LOAD_THRESHOLD      10000 // Packets per second

struct irq_moderation {
    unsigned int coal_usecs;
    unsigned int coal_frames;
    unsigned long last_update;
    unsigned long packet_count;
};

static void update_irq_moderation(struct device_state *state)
{
    struct irq_moderation *mod = &state->irq_mod;
    unsigned long now = jiffies;
    unsigned long pps;
    
    // Calculate packets per second
    if (time_after(now, mod->last_update + HZ)) {
        pps = mod->packet_count;
        mod->packet_count = 0;
        mod->last_update = now;
        
        // High load: increase coalescing
        if (pps > LOAD_THRESHOLD) {
            mod->coal_usecs = IRQ_COAL_USECS_LOW;
            mod->coal_frames = 64;
        } else {
            // Low load: reduce latency
            mod->coal_usecs = IRQ_COAL_USECS_HIGH;
            mod->coal_frames = 8;
        }
        
        // Program device registers
        writel(mod->coal_usecs, state->mmio + REG_IRQ_COAL_USECS);
        writel(mod->coal_frames, state->mmio + REG_IRQ_COAL_FRAMES);
    }
}

/*
 * NAPI: New API for polling under load
 * Kernel framework that switches between interrupt and polling modes
 */
#include <linux/netdevice.h>

struct napi_device {
    struct napi_struct napi;
    struct device_state *state;
};

static int device_napi_poll(struct napi_struct *napi, int budget)
{
    struct napi_device *ndev = container_of(napi, struct napi_device, napi);
    struct device_state *state = ndev->state;
    int work_done = 0;
    
    // Process up to 'budget' packets
    while (work_done < budget) {
        struct rx_descriptor *desc;
        
        desc = &state->rx_ring[state->rx_head];
        if (!(desc->status & RX_COMPLETE))
            break;
        
        process_rx_descriptor(state, desc);
        work_done++;
        
        state->rx_head = (state->rx_head + 1) & RX_RING_MASK;
    }
    
    // If we processed fewer than budget, no more work available
    if (work_done < budget) {
        napi_complete(napi);  // Exit polling mode
        
        // Re-enable interrupts
        writel(INT_RX_ENABLE, state->mmio + REG_INT_ENABLE);
    }
    
    return work_done;
}

static irqreturn_t device_napi_irq(int irq, void *dev_id)
{
    struct napi_device *ndev = dev_id;
    struct device_state *state = ndev->state;
    
    // Disable device interrupts
    writel(0, state->mmio + REG_INT_ENABLE);
    
    // Schedule NAPI poll
    if (napi_schedule_prep(&ndev->napi)) {
        __napi_schedule(&ndev->napi);
    }
    
    return IRQ_HANDLED;
}

static void device_init_napi(struct net_device *netdev,
                            struct napi_device *ndev,
                            struct device_state *state)
{
    ndev->state = state;
    netif_napi_add(netdev, &ndev->napi, device_napi_poll, 64);
    napi_enable(&ndev->napi);
}
```

### 3.3 Memory Pressure & OOM Scenarios

Kernel memory allocation failures require graceful handling. Unlike user space, the kernel cannot overcommit and hope the OOM killer saves you.

```c
/*
 * Handling allocation failures in IRQ context
 */
static irqreturn_t device_irq_with_fallback(int irq, void *dev_id)
{
    struct device_state *state = dev_id;
    struct rx_buffer *rxbuf;
    
    // Try atomic allocation
    rxbuf = kmalloc(sizeof(*rxbuf), GFP_ATOMIC);
    if (!rxbuf) {
        // Use pre-allocated emergency buffer
        rxbuf = &state->emergency_rxbuf;
        atomic_inc(&state->emergency_buffer_uses);
    }
    
    // Process interrupt with buffer
    process_rx_data(state, rxbuf);
    
    // Free if not emergency buffer
    if (rxbuf != &state->emergency_rxbuf)
        kfree(rxbuf);
    
    return IRQ_HANDLED;
}

/*
 * Memory pool for deterministic allocation
 */
#include <linux/mempool.h>

struct buffer_pool {
    mempool_t *pool;
    struct kmem_cache *cache;
};

static int init_buffer_pool(struct buffer_pool *bp)
{
    // Create slab cache for fixed-size objects
    bp->cache = kmem_cache_create(
        "device_buffers",
        4096,              // Object size
        0,                 // Alignment (0 = default)
        SLAB_HWCACHE_ALIGN,
        NULL               // Constructor
    );
    if (!bp->cache)
        return -ENOMEM;
    
    // Create mempool backed by slab cache
    // Guarantees 32 objects always available
    bp->pool = mempool_create(32, mempool_alloc_slab, 
                             mempool_free_slab, bp->cache);
    if (!bp->pool) {
        kmem_cache_destroy(bp->cache);
        return -ENOMEM;
    }
    
    return 0;
}

static void *alloc_from_pool(struct buffer_pool *bp, gfp_t flags)
{
    // Guaranteed to succeed if pool has reserves
    return mempool_alloc(bp->pool, flags);
}

static void free_to_pool(struct buffer_pool *bp, void *buf)
{
    mempool_free(buf, bp->pool);
}

static void destroy_buffer_pool(struct buffer_pool *bp)
{
    mempool_destroy(bp->pool);
    kmem_cache_destroy(bp->cache);
}

/*
 * Graceful degradation under memory pressure
 */
static int device_handle_rx_packet(struct device_state *state)
{
    struct sk_buff *skb;
    unsigned int len = 1500;
    
    // Try normal allocation
    skb = netdev_alloc_skb(state->netdev, len);
    if (!skb) {
        // Fall back to emergency pool
        skb = alloc_from_pool(&state->buffer_pool, GFP_ATOMIC);
        if (!skb) {
            // Last resort: drop packet, increment counter
            state->netdev->stats.rx_dropped++;
            return -ENOMEM;
        }
        atomic_inc(&state->emergency_allocations);
    }
    
    // Process packet...
    
    return 0;
}
```

### 3.4 Debugging Interrupt and Memory Issues

Production issues with interrupts and DMA often manifest as rare, transient failures. Systematic instrumentation exposes root causes.

```c
/*
 * Interrupt debugging infrastructure
 */
struct irq_debug_info {
    atomic64_t total_interrupts;
    atomic64_t spurious_interrupts;
    atomic64_t irq_latency_sum;  // Nanoseconds
    ktime_t last_irq_time;
    
    // Histogram: IRQ processing time distribution
    atomic_t latency_buckets[10];  // <1us, <10us, <100us, ...
};

static irqreturn_t device_irq_instrumented(int irq, void *dev_id)
{
    struct device_state *state = dev_id;
    struct irq_debug_info *dbg = &state->irq_debug;
    ktime_t start, end, delta;
    u64 latency_ns;
    int bucket;
    
    start = ktime_get();
    
    // Measure time since last IRQ
    if (dbg->last_irq_time) {
        delta = ktime_sub(start, dbg->last_irq_time);
        latency_ns = ktime_to_ns(delta);
        atomic64_add(latency_ns, &dbg->irq_latency_sum);
    }
    
    // Process interrupt
    irqreturn_t ret = device_irq_handler(irq, dev_id);
    
    end = ktime_get();
    dbg->last_irq_time = end;
    
    if (ret == IRQ_NONE) {
        atomic64_inc(&dbg->spurious_interrupts);
    } else {
        atomic64_inc(&dbg->total_interrupts);
        
        // Calculate processing time and update histogram
        delta = ktime_sub(end, start);
        latency_ns = ktime_to_ns(delta);
        
        bucket = ilog2(latency_ns / 1000);  // Log scale buckets
        if (bucket >= 10) bucket = 9;
        atomic_inc(&dbg->latency_buckets[bucket]);
    }
    
    return ret;
}

/*
 * Expose stats via debugfs
 */
#include <linux/debugfs.h>

static int irq_stats_show(struct seq_file *m, void *v)
{
    struct device_state *state = m->private;
    struct irq_debug_info *dbg = &state->irq_debug;
    u64 total, spurious, avg_interval;
    int i;
    
    total = atomic64_read(&dbg->total_interrupts);
    spurious = atomic64_read(&dbg->spurious_interrupts);
    
    seq_printf(m, "Total interrupts: %llu\n", total);
    seq_printf(m, "Spurious interrupts: %llu (%.2f%%)\n",
              spurious, (spurious * 100.0) / (total + spurious));
    
    if (total > 0) {
        avg_interval = atomic64_read(&dbg->irq_latency_sum) / total;
        seq_printf(m, "Average IRQ interval: %llu us\n", 
                  avg_interval / 1000);
    }
    
    seq_printf(m, "\nProcessing time distribution:\n");
    for (i = 0; i < 10; i++) {
        int count = atomic_read(&dbg->latency_buckets[i]);
        if (count > 0) {
            seq_printf(m, "  %5lu-%5lu us: %d\n",
                      (1UL << i), (1UL << (i + 1)), count);
        }
    }
    
    return 0;
}

static int irq_stats_open(struct inode *inode, struct file *file)
{
    return single_open(file, irq_stats_show, inode->i_private);
}

static const struct file_operations irq_stats_fops = {
    .open = irq_stats_open,
    .read = seq_read,
    .llseek = seq_lseek,
    .release = single_release,
};

static void device_create_debugfs(struct device_state *state)
{
    state->debugfs_dir = debugfs_create_dir("mydevice", NULL);
    if (!state->debugfs_dir)
        return;
    
    debugfs_create_file("irq_stats", 0444, state->debugfs_dir,
                       state, &irq_stats_fops);
}

/*
 * DMA mapping verification
 */
#ifdef CONFIG_DMA_API_DEBUG
static void verify_dma_mapping(struct device *dev, dma_addr_t addr, size_t len)
{
    // Kernel DMA debugging will catch:
    // - Unmapped DMA addresses
    // - Use-after-unmap
    // - Double-unmap
    // - Leaks
    
    // Enable via: CONFIG_DMA_API_DEBUG=y
    // Runtime: echo 1 > /sys/kernel/debug/dma-api/disabled
}
#endif

/*
 * Catch interrupt storms
 */
static irqreturn_t device_irq_with_storm_detection(int irq, void *dev_id)
{
    struct device_state *state = dev_id;
    unsigned long now = jiffies;
    
    if (time_after(now, state->irq_storm_check + HZ)) {
        // Check IRQ rate over last second
        if (state->irq_count_last_sec > 100000) {
            dev_warn(state->dev, 
                    "IRQ storm detected: %lu/sec, disabling\n",
                    state->irq_count_last_sec);
            
            // Disable device interrupts
            writel(0, state->mmio + REG_INT_ENABLE);
            return IRQ_HANDLED;
        }
        
        state->irq_count_last_sec = 0;
        state->irq_storm_check = now;
    }
    
    state->irq_count_last_sec++;
    
    return device_irq_handler(irq, dev_id);
}
```

### 3.5 Production Checklist

**Memory Management**:
- Always check return values from allocation functions
- Use appropriate GFP flags for context (GFP_KERNEL vs GFP_ATOMIC)
- Pair every allocation with a free on all code paths
- Consider mempool for critical allocations
- Align frequently-accessed structures to cache lines
- Avoid false sharing between CPUs

**DMA**:
- Call `dma_set_mask_and_coherent()` during probe
- Always check `dma_mapping_error()` after mapping
- Pair `dma_map_*()` with `dma_unmap_*()` on all paths
- Use correct direction flags (TO_DEVICE, FROM_DEVICE, BIDIRECTIONAL)
- Call `dma_sync_*()` before CPU or device access to bidirectional buffers
- Never free memory with active DMA mappings

**Interrupts**:
- Request IRQs late in probe, after data structures initialized
- Free IRQs early in remove, before destroying data structures
- Keep primary handlers fast (<100 microseconds typical)
- Use threaded IRQs or workqueues for lengthy processing
- Disable interrupts at device level before freeing IRQ
- Use `free_irq()` or `devm_free_irq()`, never just unregister

**Synchronization**:
- Use `spin_lock_irqsave()` from process context
- Use `spin_lock()` from interrupt context
- Hold spinlocks for minimal duration
- Never sleep with a spinlock held
- Document lock ordering to prevent deadlocks
- Consider RCU for read-mostly data structures

**Debugging**:
- Enable `CONFIG_DEBUG_ATOMIC_SLEEP` during development
- Use `CONFIG_DMA_API_DEBUG` to catch DMA bugs
- Implement debugfs statistics for production troubleshooting
- Add tracepoints for performance analysis
- Test memory allocation failures with fault injection

This lesson has covered the mechanical foundations of driver memory management and interrupt handling. You've seen how DMA mappings bridge hardware and kernel memory models, how interrupt handling splits between atomic and schedulable contexts, and how synchronization primitives prevent races. The patterns shown here—memory pools, batched processing, adaptive coalescing, instrumentation—separate drivers that survive production load from those that fail under stress. Master these mechanics and you control the hardware-kernel boundary with precision.
