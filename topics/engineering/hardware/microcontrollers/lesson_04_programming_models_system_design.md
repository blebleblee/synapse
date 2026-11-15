# Lesson 4: Programming Models, Real-Time Constraints, System Design

## 1. First-Principles Intuition & Invariants

The microcontroller sits at the intersection of determinism and chaos. Unlike general-purpose processors that can afford to speculate, predict, and prefetch with abandon, the microcontroller must guarantee that when a sensor signals an event, the response occurs within a bounded time window measured in microseconds or milliseconds. Miss that window, and the motor overshoots its position, the communication packet corrupts, or the safety interlock fails to engage. This fundamental requirement—temporal determinism—shapes every decision in embedded system design, from whether to write bare-metal code or deploy a real-time operating system, to how interrupt priorities get assigned, to which sleep mode the power management unit should enter during idle periods.

The programming model you select establishes the contract between hardware and software. Bare-metal programming exposes the raw silicon: every register, every interrupt vector, every clock cycle sits under direct programmer control. This approach offers maximum transparency and minimal overhead, but it demands that you construct your own task scheduling, synchronization primitives, and timing guarantees from first principles. The real-time operating system (RTOS) abstracts these concerns behind APIs for tasks, semaphores, mutexes, and message queues, trading a few kilobytes of flash and a predictable latency overhead for portability, maintainability, and faster development cycles.

Neither approach is universally superior. The bare-metal model excels in applications where code size must remain below eight kilobytes, where interrupt latency must stay below two microseconds, or where the application consists of a single control loop with minimal concurrency. The RTOS model shines when multiple concurrent tasks interact through complex synchronization patterns, when third-party middleware expects an RTOS abstraction layer, or when the team must partition development across multiple engineers working on independent modules. Understanding the invariants that govern timing, scheduling, and resource contention allows you to choose the appropriate model and implement it correctly.

Real-time constraints manifest in two forms: hard and soft. Hard real-time systems must meet every deadline without exception—an airbag controller that deploys twenty milliseconds late has failed catastrophically. Soft real-time systems tolerate occasional deadline misses as long as the average response time remains acceptable—a temperature sensor logging data every second can skip one sample without causing system failure. The distinction matters because hard real-time guarantees require worst-case execution time (WCET) analysis, priority inversion mitigation, and interrupt masking disciplines that would be overkill for soft real-time systems.

Worst-case execution time analysis forces you to account for the longest possible code path through each function, including cache misses, pipeline stalls, and wait states introduced by slow peripheral buses. On a Cortex-M4 running at 168 MHz with zero-wait-state flash and a single-cycle multiplier, a floating-point PID control loop might execute in 800 nanoseconds on average, but a cache miss could stretch that to 1.2 microseconds. If your control deadline is 1.0 microseconds, the average case passes but the worst case fails. WCET analysis exposes this gap before it causes field failures.

Interrupt latency defines the time between when a peripheral asserts an interrupt request line and when the first instruction of your interrupt service routine executes. This latency includes interrupt controller arbitration, context save overhead, and any critical section that might have temporarily disabled interrupts. On ARM Cortex-M processors, the hardware automatically stacks eight registers (R0–R3, R12, LR, PC, xPSR) in twelve clock cycles, then fetches the vector table entry and prefetches the ISR instruction. If the processor was executing from flash with wait states, that vector fetch might add another five cycles. If a higher-priority interrupt was already executing, you wait for that ISR to complete or reach a preemption point. If your code disabled interrupts using `__disable_irq()` or raised the `BASEPRI` register, you wait for that critical section to finish. The cumulative latency can easily reach tens of microseconds if critical sections are poorly managed.

Synchronization primitives—semaphores, mutexes, and critical sections—coordinate access to shared resources between tasks and interrupt contexts. A semaphore counts available resources: initializing a binary semaphore to one creates a lock, while initializing a counting semaphore to five models a buffer with five slots. A mutex adds priority inheritance, a mechanism that temporarily elevates the priority of a task holding a lock to match the priority of any higher-priority task waiting for that lock, thereby preventing priority inversion. A critical section disables interrupts or raises the interrupt priority mask to create an atomic region where no preemption can occur. Each primitive carries different overhead and different applicability constraints: you cannot block inside an ISR, so semaphores and mutexes are forbidden there, leaving only lock-free algorithms or deferred processing strategies.

Power management in microcontrollers exploits the fact that most embedded systems spend the majority of their time waiting for external events. Instead of burning milliamps in an idle loop polling peripheral status registers, the processor can enter a sleep mode that gates clocks to unused modules, drops the core voltage, or even powers down the CPU entirely while leaving the real-time clock and wake-up interrupt controller running. ARM Cortex-M processors define three sleep modes: sleep-on-exit (the processor sleeps immediately after exiting an ISR), sleep-now (the processor enters sleep when the `WFI` or `WFE` instruction executes), and deep sleep (an extended mode that may disable the PLL and high-speed oscillators). Transitioning between power states costs time and energy—waking from deep sleep might require 100 microseconds to restart the PLL and stabilize the clock—so the power management strategy must predict idle durations and select the deepest sleep mode that can wake up before the next deadline.

Bootloaders establish the bridge between reset and application code. At power-on, the ARM Cortex-M core fetches the initial stack pointer from address `0x0000_0000` and the reset vector from address `0x0000_0004`, then begins executing the reset handler. A simple application programs these vectors directly into flash and jumps straight into `main()`. A bootloader reserves the lower flash region for its own code, validates an application image stored at a higher address (often by checking a CRC or cryptographic signature), then remaps the vector table using the Vector Table Offset Register (`VTOR`) and performs a controlled jump into the application's reset handler. This indirection enables in-field firmware updates over UART, CAN, or USB without requiring an external programmer.

Hardware abstraction layers (HALs) isolate application logic from register-level hardware details, allowing code to port across different microcontroller families or vendors. A well-designed HAL defines abstract interfaces for GPIO, timers, UARTs, and SPI controllers, then provides vendor-specific implementations that map those interfaces to the actual hardware registers. ST's STM32 HAL, for example, wraps every peripheral in a handle structure containing initialization parameters, state flags, and function pointers, then provides `HAL_UART_Transmit()` and `HAL_UART_Receive()` functions that work identically across the STM32F0, STM32F4, and STM32H7 families despite radically different peripheral implementations. The abstraction costs a few percent in code size and execution time, but the portability gain often justifies the overhead.

The invariants that govern real-time system design reduce to three principles: determinism requires that every operation completes within a bounded time, concurrency requires that shared resources remain consistent despite preemption, and efficiency requires that the system meets its deadlines while minimizing power consumption and hardware cost. Every design decision—bare-metal versus RTOS, polling versus interrupts, cooperative versus preemptive scheduling, spinlock versus semaphore—trades off among these three dimensions.

## 2. Core Architecture & Mechanics

Bare-metal programming begins with the startup code, a short assembly routine that initializes the stack pointer, copies initialized data from flash to SRAM, zeros the BSS section, and calls `main()`. On ARM Cortex-M, the hardware automatically loads the stack pointer from the first word of flash and jumps to the reset handler at the second word, so the startup code need not perform these steps explicitly. However, the C runtime expects a valid stack and initialized data segments, so the reset handler must perform these tasks before calling any C functions.

A minimal Cortex-M startup file in ARM assembly begins by declaring the vector table as a read-only data section aligned to the required boundary (256 bytes for Cortex-M3/M4). The first entry holds the initial stack pointer, typically the top of SRAM. The second entry holds the address of the reset handler. Subsequent entries define handlers for NMI, hard fault, memory management fault, bus fault, usage fault, and the sixteen user-configurable interrupt channels. Unused vectors typically point to a default handler that enters an infinite loop, allowing a debugger to catch unexpected interrupts.

```
    .syntax unified
    .cpu cortex-m4
    .thumb

.global Reset_Handler
.global Default_Handler

    .section .isr_vector,"a",%progbits
    .type vector_table, %object

vector_table:
    .word _estack              /* Initial stack pointer */
    .word Reset_Handler        /* Reset handler */
    .word NMI_Handler          /* NMI handler */
    .word HardFault_Handler    /* Hard fault handler */
    .word MemManage_Handler    /* MPU fault handler */
    .word BusFault_Handler     /* Bus fault handler */
    .word UsageFault_Handler   /* Usage fault handler */
    .word 0                    /* Reserved */
    .word 0                    /* Reserved */
    .word 0                    /* Reserved */
    .word 0                    /* Reserved */
    .word SVC_Handler          /* SVCall handler */
    .word DebugMon_Handler     /* Debug monitor handler */
    .word 0                    /* Reserved */
    .word PendSV_Handler       /* PendSV handler */
    .word SysTick_Handler      /* SysTick handler */
    /* External interrupts */
    .word EXTI0_IRQHandler
    .word EXTI1_IRQHandler
    /* ... additional vectors ... */

    .section .text.Reset_Handler
    .type Reset_Handler, %function
Reset_Handler:
    ldr r0, =_sdata        /* Source address in flash */
    ldr r1, =_edata        /* End of data in SRAM */
    ldr r2, =_sbss         /* Start of BSS */
    ldr r3, =_ebss         /* End of BSS */
    ldr sp, =_estack       /* Initialize stack pointer */

    /* Copy data section from flash to SRAM */
copy_data:
    ldr r4, [r0], #4
    str r4, [r1], #4
    cmp r1, r2
    blt copy_data

    /* Zero BSS section */
    movs r4, #0
zero_bss:
    str r4, [r2], #4
    cmp r2, r3
    blt zero_bss

    bl SystemInit          /* Initialize clocks and PLLs */
    bl main                /* Enter application */
    b .                    /* Trap if main returns */

    .section .text.Default_Handler
    .type Default_Handler, %function
Default_Handler:
    b .                    /* Infinite loop */
```

The linker script defines memory regions and section placements. Flash starts at address `0x0800_0000` on STM32 microcontrollers, while SRAM starts at `0x2000_0000`. The script places the vector table at the beginning of flash, followed by program code, read-only data, and initialized data. The data section gets loaded into flash but linked to run from SRAM addresses, requiring the startup code to perform the copy. The BSS section consumes SRAM space but occupies zero bytes in the flash image.

```
MEMORY
{
    FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 512K
    SRAM (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
}

_estack = ORIGIN(SRAM) + LENGTH(SRAM);

SECTIONS
{
    .isr_vector :
    {
        . = ALIGN(4);
        KEEP(*(.isr_vector))
        . = ALIGN(4);
    } >FLASH

    .text :
    {
        . = ALIGN(4);
        *(.text)
        *(.text*)
        *(.rodata)
        *(.rodata*)
        . = ALIGN(4);
        _etext = .;
    } >FLASH

    .data :
    {
        . = ALIGN(4);
        _sdata = .;
        *(.data)
        *(.data*)
        . = ALIGN(4);
        _edata = .;
    } >SRAM AT>FLASH

    .bss :
    {
        . = ALIGN(4);
        _sbss = .;
        *(.bss)
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _ebss = .;
    } >SRAM
}
```

After the startup code completes, execution reaches `main()`, where bare-metal applications typically initialize peripherals, configure interrupt priorities, and enter a superloop that polls flags set by interrupt service routines. This polling architecture, also called a foreground-background system, executes ISRs in the foreground with minimal latency while deferring complex processing to the background loop. The ISR sets a flag, updates a buffer, or increments a counter, then returns immediately. The main loop checks these flags and performs the corresponding processing when it detects a change.

```c
#include "stm32f4xx.h"

volatile uint32_t tick_count = 0;
volatile uint8_t adc_ready = 0;
uint16_t adc_value = 0;

void SysTick_Handler(void) {
    tick_count++;
}

void ADC_IRQHandler(void) {
    if (ADC1->SR & ADC_SR_EOC) {
        adc_value = ADC1->DR;
        adc_ready = 1;
    }
}

void delay_ms(uint32_t ms) {
    uint32_t start = tick_count;
    while ((tick_count - start) < ms);
}

int main(void) {
    SystemInit();
    
    /* Configure SysTick for 1 ms interrupts */
    SysTick_Config(SystemCoreClock / 1000);
    
    /* Enable ADC clock */
    RCC->APB2ENR |= RCC_APB2ENR_ADC1EN;
    
    /* Configure ADC1: 12-bit resolution, end-of-conversion interrupt */
    ADC1->CR1 = ADC_CR1_EOCIE;
    ADC1->CR2 = ADC_CR2_ADON;
    ADC1->SMPR2 = ADC_SMPR2_SMP0_2;  /* 84 cycles sampling time */
    ADC1->SQR3 = 0;  /* Channel 0 */
    
    NVIC_EnableIRQ(ADC_IRQn);
    NVIC_SetPriority(ADC_IRQn, 2);
    
    /* Enable GPIO clock and configure PA0 as analog input */
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;
    GPIOA->MODER |= GPIO_MODER_MODER0;
    
    while (1) {
        ADC1->CR2 |= ADC_CR2_SWSTART;  /* Start conversion */
        
        while (!adc_ready);  /* Wait for conversion */
        adc_ready = 0;
        
        /* Process ADC value */
        if (adc_value > 2048) {
            GPIOA->ODR |= GPIO_ODR_OD5;  /* Turn on LED */
        } else {
            GPIOA->ODR &= ~GPIO_ODR_OD5;  /* Turn off LED */
        }
        
        delay_ms(100);
    }
}
```

This bare-metal architecture works well for simple applications but becomes unwieldy as concurrency increases. If you need to sample three ADC channels, transmit data over UART, respond to button presses, and update an LCD display, the main loop grows into a tangled state machine where each iteration checks dozens of flags and updates multiple state variables. Critical timing constraints become difficult to verify because the loop iteration time depends on which flags are set and which code paths execute.

A cooperative scheduler provides structure without the overhead of a full RTOS. Tasks voluntarily yield control to other tasks by calling a scheduler function, which saves the current task's context and restores another task's context. Because tasks only switch at well-defined yield points, the scheduler need not worry about preemption or protect shared data structures with mutexes. However, a single long-running task can starve other tasks, making cooperative scheduling unsuitable for hard real-time systems.

A minimal cooperative scheduler maintains an array of task control blocks, each containing a stack pointer, a state flag, and a function pointer. The scheduler iterates through the array, executing each ready task until it yields or completes. Context switching on ARM Cortex-M reduces to saving and restoring the stack pointer, since the task function's local variables reside on its stack.

```c
#include <stdint.h>
#include <string.h>

#define MAX_TASKS 4
#define STACK_SIZE 512

typedef enum {
    TASK_READY,
    TASK_RUNNING,
    TASK_BLOCKED
} task_state_t;

typedef struct {
    uint32_t *stack_ptr;
    uint32_t stack[STACK_SIZE];
    void (*task_func)(void);
    task_state_t state;
} tcb_t;

tcb_t tasks[MAX_TASKS];
uint8_t current_task = 0;
uint8_t task_count = 0;

void scheduler_init(void) {
    memset(tasks, 0, sizeof(tasks));
    task_count = 0;
}

void task_create(void (*func)(void)) {
    if (task_count >= MAX_TASKS) return;
    
    tcb_t *tcb = &tasks[task_count];
    tcb->task_func = func;
    tcb->state = TASK_READY;
    
    /* Initialize stack with a fake context */
    tcb->stack_ptr = &tcb->stack[STACK_SIZE - 16];
    tcb->stack_ptr[8] = (uint32_t)func;  /* PC */
    tcb->stack_ptr[9] = 0x01000000;      /* xPSR with Thumb bit */
    
    task_count++;
}

void task_yield(void) {
    /* Save current context and switch to next ready task */
    uint8_t next = (current_task + 1) % task_count;
    while (next != current_task && tasks[next].state != TASK_READY) {
        next = (next + 1) % task_count;
    }
    if (next != current_task) {
        current_task = next;
    }
}

void scheduler_start(void) {
    if (task_count == 0) return;
    
    current_task = 0;
    tasks[0].state = TASK_RUNNING;
    
    /* Load first task's stack pointer and jump to it */
    __asm volatile (
        "ldr r0, =tasks \n"
        "ldr r1, [r0]   \n"  /* Load stack pointer */
        "ldmia r1!, {r4-r11} \n"
        "msr psp, r1 \n"
        "mov lr, #0xFFFFFFFD \n"  /* Return to Thread mode, use PSP */
        "bx lr \n"
    );
}
```

Preemptive scheduling allows the operating system to interrupt a running task and switch to another task without requiring explicit yield calls. This capability requires timer interrupts and context save/restore logic that preserves all CPU registers, not just the stack pointer. ARM Cortex-M processors simplify preemptive context switches by automatically stacking R0–R3, R12, LR, PC, and xPSR on interrupt entry, leaving only R4–R11 to be saved manually. The PendSV exception, designed specifically for context switching, runs at the lowest interrupt priority, ensuring that all other ISRs complete before the context switch occurs.

A minimal preemptive scheduler uses SysTick to generate periodic timer interrupts, typically at 1 kHz. The SysTick ISR increments a tick counter, decrements sleep timers for blocked tasks, and sets the PendSV exception if a task becomes ready. The PendSV handler saves R4–R11 and the current stack pointer, selects the next ready task, restores its R4–R11 and stack pointer, then returns. The hardware automatically restores R0–R3, R12, LR, PC, and xPSR, resuming the new task.

```c
#include "stm32f4xx.h"

typedef struct {
    uint32_t *stack_ptr;
    uint32_t stack[STACK_SIZE];
    uint32_t sleep_ticks;
    task_state_t state;
    uint8_t priority;
} tcb_preemptive_t;

tcb_preemptive_t tasks_preemptive[MAX_TASKS];
uint8_t current_task_idx = 0;
uint32_t system_tick = 0;

void SysTick_Handler(void) {
    system_tick++;
    
    /* Decrement sleep counters */
    for (uint8_t i = 0; i < task_count; i++) {
        if (tasks_preemptive[i].state == TASK_BLOCKED && tasks_preemptive[i].sleep_ticks > 0) {
            tasks_preemptive[i].sleep_ticks--;
            if (tasks_preemptive[i].sleep_ticks == 0) {
                tasks_preemptive[i].state = TASK_READY;
                SCB->ICSR |= SCB_ICSR_PENDSVSET_Msk;  /* Trigger context switch */
            }
        }
    }
}

__attribute__((naked)) void PendSV_Handler(void) {
    __asm volatile (
        /* Save current context */
        "mrs r0, psp \n"
        "stmdb r0!, {r4-r11} \n"
        "ldr r1, =current_task_idx \n"
        "ldr r2, [r1] \n"
        "ldr r3, =tasks_preemptive \n"
        "add r3, r3, r2, lsl #6 \n"  /* Offset to current TCB */
        "str r0, [r3] \n"            /* Save stack pointer */
        
        /* Select next task (simplified round-robin) */
        "ldr r2, =task_count \n"
        "ldr r2, [r2] \n"
        "ldr r0, [r1] \n"
        "add r0, r0, #1 \n"
        "udiv r4, r0, r2 \n"
        "mls r0, r4, r2, r0 \n"  /* r0 = r0 % task_count */
        "str r0, [r1] \n"
        
        /* Load next context */
        "ldr r3, =tasks_preemptive \n"
        "add r3, r3, r0, lsl #6 \n"
        "ldr r0, [r3] \n"
        "ldmia r0!, {r4-r11} \n"
        "msr psp, r0 \n"
        "bx lr \n"
    );
}

void task_sleep(uint32_t ticks) {
    tasks_preemptive[current_task_idx].sleep_ticks = ticks;
    tasks_preemptive[current_task_idx].state = TASK_BLOCKED;
    SCB->ICSR |= SCB_ICSR_PENDSVSET_Msk;
}
```

Commercial RTOS implementations like FreeRTOS extend this foundation with priority-based scheduling, inter-task communication through queues and mailboxes, and synchronization primitives. FreeRTOS defines tasks as C functions that never return, running in an infinite loop and yielding control through API calls like `vTaskDelay()`, `xQueueReceive()`, or `xSemaphoreTake()`. The scheduler maintains separate ready queues for each priority level, always running the highest-priority ready task.

Priority inversion occurs when a high-priority task blocks waiting for a resource held by a low-priority task, and a medium-priority task preempts the low-priority task, preventing it from releasing the resource. The high-priority task, despite its urgency, remains blocked indefinitely while the medium-priority task executes. FreeRTOS mitigates priority inversion through priority inheritance: when a high-priority task blocks on a mutex held by a low-priority task, the kernel temporarily elevates the low-priority task to the blocking task's priority, allowing it to complete and release the mutex before medium-priority tasks can preempt it.

Semaphores and mutexes differ in ownership and usage patterns. A semaphore counts available resources and supports multiple concurrent users—a counting semaphore initialized to three allows three tasks to acquire it before the fourth task blocks. Binary semaphores, initialized to zero or one, signal events or implement simple locks. Mutexes, in contrast, support only one owner at a time and enforce ownership rules: the task that takes a mutex must be the task that gives it back. This ownership tracking enables priority inheritance and deadlock detection.

Critical sections protect short code sequences that manipulate shared data structures by temporarily disabling interrupts or raising the interrupt priority mask. On ARM Cortex-M, the `BASEPRI` register masks interrupts below a specified priority threshold, allowing high-priority interrupts like motor control or communication protocol timing to continue while blocking lower-priority interrupts. Critical sections must remain short—typically under ten microseconds—to avoid increasing interrupt latency for time-critical peripherals.

```c
#include "FreeRTOS.h"
#include "task.h"
#include "semphr.h"
#include "queue.h"

SemaphoreHandle_t adc_semaphore;
QueueHandle_t uart_queue;
volatile uint16_t shared_adc_value;

void ADC_Task(void *pvParameters) {
    while (1) {
        /* Wait for ADC semaphore from ISR */
        if (xSemaphoreTake(adc_semaphore, portMAX_DELAY) == pdTRUE) {
            /* Enter critical section to read shared variable */
            taskENTER_CRITICAL();
            uint16_t local_value = shared_adc_value;
            taskEXIT_CRITICAL();
            
            /* Process value and send to UART task */
            xQueueSend(uart_queue, &local_value, 0);
        }
    }
}

void UART_Task(void *pvParameters) {
    uint16_t value;
    char buffer[16];
    
    while (1) {
        /* Block waiting for queue data */
        if (xQueueReceive(uart_queue, &value, portMAX_DELAY) == pdTRUE) {
            snprintf(buffer, sizeof(buffer), "ADC: %u\r\n", value);
            HAL_UART_Transmit(&huart2, (uint8_t*)buffer, strlen(buffer), HAL_MAX_DELAY);
        }
    }
}

void ADC_IRQHandler(void) {
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    
    if (ADC1->SR & ADC_SR_EOC) {
        shared_adc_value = ADC1->DR;
        xSemaphoreGiveFromISR(adc_semaphore, &xHigherPriorityTaskWoken);
        portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
    }
}

int main(void) {
    HAL_Init();
    SystemClock_Config();
    
    adc_semaphore = xSemaphoreCreateBinary();
    uart_queue = xQueueCreate(10, sizeof(uint16_t));
    
    xTaskCreate(ADC_Task, "ADC", 128, NULL, 2, NULL);
    xTaskCreate(UART_Task, "UART", 256, NULL, 1, NULL);
    
    vTaskStartScheduler();
    
    while (1);  /* Should never reach here */
}
```

Timing analysis for real-time systems combines static code analysis with dynamic measurement. Static analysis determines the worst-case execution time by examining all possible code paths, counting instruction cycles, and accounting for pipeline stalls, cache misses, and wait states. Dynamic measurement captures actual execution times using hardware timers or debug trace facilities like ARM CoreSight ETM, providing statistical distributions but not absolute guarantees.

The Data Watchpoint and Trace (DWT) unit in ARM Cortex-M3/M4/M7 processors includes a cycle counter register (`DWT->CYCCNT`) that increments on every CPU clock cycle. Wrapping critical functions with DWT reads measures their execution time to single-cycle precision.

```c
void timing_init(void) {
    /* Enable DWT and cycle counter */
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
    DWT->CYCCNT = 0;
}

void timing_test(void) {
    uint32_t start = DWT->CYCCNT;
    
    /* Function under test */
    control_loop();
    
    uint32_t cycles = DWT->CYCCNT - start;
    uint32_t microseconds = (cycles * 1000000) / SystemCoreClock;
}
```

Interrupt latency measurements require external instrumentation because the CPU cannot timestamp its own interrupt entry without introducing overhead that distorts the measurement. A logic analyzer or oscilloscope connected to a GPIO pin toggled at the start of the ISR captures the true latency from peripheral event to ISR execution. Setting the GPIO high in the ISR prologue and low in the epilogue measures ISR execution time, revealing whether the ISR violates its timing budget.

Power management strategies balance energy consumption against wake-up latency. ARM Cortex-M processors support the Wait For Interrupt (`WFI`) and Wait For Event (`WFE`) instructions, which halt instruction execution until an interrupt or event occurs. The Nested Vectored Interrupt Controller (NVIC) automatically wakes the processor when any enabled interrupt triggers, restoring full-speed execution within a few clock cycles. Deeper sleep modes disable the high-speed oscillator and PLL, reducing current consumption from milliamps to microamps but requiring hundreds of microseconds to milliseconds for clock restart and stabilization.

STM32 microcontrollers define multiple sleep modes: Sleep mode stops the CPU but leaves all peripherals running, Stop mode halts the high-speed clock and enters low-power voltage regulation, and Standby mode powers down nearly everything except the RTC and backup registers. Selecting the appropriate mode requires predicting the duration of the idle period—if the next task will wake within 100 microseconds, the overhead of entering and exiting Stop mode exceeds the energy saved, making Sleep mode more efficient.

```c
void enter_sleep_mode(uint32_t idle_ticks) {
    if (idle_ticks < 10) {
        /* Overhead too high, just WFI */
        __WFI();
    } else if (idle_ticks < 1000) {
        /* Enter Sleep mode */
        HAL_PWR_EnterSLEEPMode(PWR_MAINREGULATOR_ON, PWR_SLEEPENTRY_WFI);
    } else {
        /* Enter Stop mode */
        HAL_PWR_EnterSTOPMode(PWR_LOWPOWERREGULATOR_ON, PWR_STOPENTRY_WFI);
        SystemClock_Config();  /* Reconfigure clocks after wake */
    }
}
```

FreeRTOS integrates tickless idle, a power management strategy that predicts the duration until the next scheduled task and enters an appropriate sleep mode, reprogramming the SysTick timer to generate the next interrupt at the precise wake-up time rather than at the next millisecond tick.

Bootloaders enable in-field firmware updates by reserving a portion of flash for bootloader code, another portion for the application, and often a third portion for staging incoming firmware images. On reset, the bootloader checks whether a firmware update request is pending—indicated by a magic value in backup SRAM or EEPROM—validates the staged image's integrity using a CRC or cryptographic signature, erases the application region, copies the new image into place, clears the update flag, and finally remaps the vector table and jumps to the new application's reset handler.

The Vector Table Offset Register (`VTOR`) allows the bootloader to redirect interrupt vectors to the application's vector table without physically moving the application to address zero. After validating the application image, the bootloader sets `VTOR` to the application's base address, loads the application's initial stack pointer, and jumps to its reset vector.

```c
#define APP_ADDRESS 0x08008000

typedef void (*pFunction)(void);

void jump_to_application(void) {
    uint32_t app_stack = *(volatile uint32_t*)APP_ADDRESS;
    uint32_t app_reset = *(volatile uint32_t*)(APP_ADDRESS + 4);
    
    /* Validate stack pointer is in SRAM range */
    if ((app_stack & 0xFFF00000) != 0x20000000) {
        return;  /* Invalid application */
    }
    
    /* Disable interrupts */
    __disable_irq();
    
    /* Disable SysTick */
    SysTick->CTRL = 0;
    
    /* Clear all pending interrupts */
    for (uint8_t i = 0; i < 8; i++) {
        NVIC->ICPR[i] = 0xFFFFFFFF;
    }
    
    /* Remap vector table */
    SCB->VTOR = APP_ADDRESS;
    
    /* Set stack pointer */
    __set_MSP(app_stack);
    
    /* Jump to application */
    pFunction app_entry = (pFunction)app_reset;
    app_entry();
}
```

Firmware update protocols must defend against corruption from power loss or transmission errors. A dual-bank flash architecture maintains two complete copies of the application, allowing the bootloader to fall back to the previous version if the new image fails validation. The bootloader updates a bank select flag only after the new image passes all checks, ensuring that even if power fails during the update process, the device reboots into a functional application.

Hardware abstraction layers decouple application logic from hardware-specific register programming by defining device-independent interfaces and implementing them with vendor-specific drivers. A GPIO abstraction might define `gpio_set_output()`, `gpio_set_input()`, and `gpio_read()` functions, then provide separate implementations for STM32, NXP LPC, and Atmel SAM microcontrollers. The application calls the abstract functions, while conditional compilation or runtime function pointers select the appropriate implementation.

```c
/* hal_gpio.h - Hardware abstraction */
typedef enum {
    GPIO_MODE_INPUT,
    GPIO_MODE_OUTPUT,
    GPIO_MODE_ALTERNATE
} gpio_mode_t;

typedef struct {
    void *port;
    uint8_t pin;
} gpio_pin_t;

void gpio_init(gpio_pin_t *pin, gpio_mode_t mode);
void gpio_write(gpio_pin_t *pin, uint8_t value);
uint8_t gpio_read(gpio_pin_t *pin);

/* hal_gpio_stm32.c - STM32 implementation */
void gpio_init(gpio_pin_t *pin, gpio_mode_t mode) {
    GPIO_TypeDef *port = (GPIO_TypeDef*)pin->port;
    uint8_t pos = pin->pin;
    
    switch (mode) {
        case GPIO_MODE_INPUT:
            port->MODER &= ~(3U << (pos * 2));
            break;
        case GPIO_MODE_OUTPUT:
            port->MODER &= ~(3U << (pos * 2));
            port->MODER |= (1U << (pos * 2));
            break;
        case GPIO_MODE_ALTERNATE:
            port->MODER &= ~(3U << (pos * 2));
            port->MODER |= (2U << (pos * 2));
            break;
    }
}

void gpio_write(gpio_pin_t *pin, uint8_t value) {
    GPIO_TypeDef *port = (GPIO_TypeDef*)pin->port;
    if (value) {
        port->BSRR = (1U << pin->pin);
    } else {
        port->BSRR = (1U << (pin->pin + 16));
    }
}

/* Application code - hardware independent */
gpio_pin_t led = { .port = GPIOA, .pin = 5 };
gpio_init(&led, GPIO_MODE_OUTPUT);
gpio_write(&led, 1);
```

The abstraction allows the application to compile and run on different hardware targets by linking against the appropriate HAL implementation, but the cost is indirection—every GPIO operation now incurs a function call and register pointer dereference. For performance-critical paths, the HAL can provide inline functions or macros that expand to direct register access, sacrificing portability for speed.

## 3. High-Performance Optimization & Failure Modes

Optimizing real-time systems demands a shift in perspective from maximizing throughput to minimizing worst-case latency and jitter. A general-purpose algorithm that averages 50 microseconds but occasionally spikes to 500 microseconds fails in a hard real-time system with a 100-microsecond deadline, while a slower algorithm that consistently completes in 80 microseconds succeeds. Predictability trumps average-case performance.

Interrupt prioritization directly controls latency and preemption behavior. ARM Cortex-M processors support up to 256 priority levels, though most implementations use 8 or 16 levels. Lower numeric values represent higher priorities, with priority zero being the highest. Assigning priorities requires understanding which interrupts have the tightest timing constraints and which can tolerate additional latency. A motor control PWM update interrupt might run at priority one, a UART receive interrupt at priority three, and a general-purpose timer at priority five.

The `BASEPRI` register provides a finer-grained alternative to disabling all interrupts. Setting `BASEPRI` to a nonzero value masks interrupts at or below that priority level while allowing higher-priority interrupts to preempt the critical section. This approach preserves responsiveness for time-critical interrupts while protecting shared data from lower-priority tasks.

```c
void critical_section_example(void) {
    uint32_t basepri_save;
    
    /* Save current BASEPRI and mask priorities 3 and below */
    __asm volatile (
        "mrs %0, basepri \n"
        "mov r1, %1 \n"
        "msr basepri, r1 \n"
        : "=r" (basepri_save)
        : "i" (3 << (8 - __NVIC_PRIO_BITS))
        : "r1", "memory"
    );
    
    /* Critical section - priorities 0-2 can still interrupt */
    shared_data++;
    
    /* Restore BASEPRI */
    __asm volatile (
        "msr basepri, %0 \n"
        :
        : "r" (basepri_save)
        : "memory"
    );
}
```

Interrupt service routines must minimize execution time to reduce latency for other interrupts and maintain system responsiveness. The best practice defers complex processing to task context by setting a flag, posting a semaphore, or writing to a queue, then returning immediately. The ISR captures time-critical data or acknowledges hardware events, while a dedicated task performs filtering, protocol parsing, or state machine updates.

Lock-free algorithms eliminate blocking synchronization by using atomic operations to coordinate access to shared data. ARM Cortex-M provides the LDREX and STREX instructions for load-exclusive and store-exclusive, implementing a load-link/store-conditional pattern. These instructions allow a task to read a value, compute a new value, and write it back only if no other task modified the location in the interim. If another task intervened, the store fails and the operation retries.

```c
uint32_t atomic_increment(volatile uint32_t *value) {
    uint32_t result, tmp;
    
    __asm volatile (
        "1: \n"
        "   ldrex %0, [%2] \n"      /* Load exclusive */
        "   add %0, %0, #1 \n"      /* Increment */
        "   strex %1, %0, [%2] \n"  /* Store exclusive */
        "   cmp %1, #0 \n"          /* Check if store succeeded */
        "   bne 1b \n"              /* Retry if failed */
        : "=&r" (result), "=&r" (tmp)
        : "r" (value)
        : "cc", "memory"
    );
    
    return result;
}
```

Stack overflow constitutes a silent killer in embedded systems. Each task requires its own stack, and if a deep call chain or large local variable exceeds the allocated space, the stack overwrites adjacent memory, corrupting other task stacks or global variables. FreeRTOS provides stack watermarking, filling unused stack space with a known pattern (typically `0xA5`) and periodically checking how much unused space remains. Tasks that consistently approach their stack limit require larger allocations.

Memory fragmentation plagues systems that dynamically allocate and free memory of varying sizes. After thousands of allocations and deallocations, free memory fragments into small, noncontiguous blocks, and allocation requests for moderately sized objects fail despite sufficient total free memory. Real-time systems often avoid dynamic allocation entirely, preallocating all memory at startup. FreeRTOS offers multiple heap allocation schemes: heap_1 never frees memory, heap_2 provides free but no coalescing, heap_4 provides free with coalescing but nondeterministic time, and heap_5 allows multiple noncontiguous memory regions.

Watchdog timers provide last-resort fault recovery by resetting the processor if software fails to periodically service the watchdog. A correctly functioning system refreshes the watchdog counter every 100 milliseconds; if a bug causes an infinite loop or a deadlock, the watchdog times out and forces a reset. The independent watchdog (IWDG) on STM32 runs from a separate low-speed oscillator and continues operating even if the main clock fails.

```c
void watchdog_init(void) {
    /* Enable write access to IWDG registers */
    IWDG->KR = 0x5555;
    
    /* Set prescaler to 32 (40 kHz / 32 = 1.25 kHz) */
    IWDG->PR = IWDG_PR_PR_2;
    
    /* Set reload value for 1 second timeout (1250 counts) */
    IWDG->RLR = 1250;
    
    /* Start watchdog */
    IWDG->KR = 0xCCCC;
}

void watchdog_refresh(void) {
    IWDG->KR = 0xAAAA;
}
```

Hard faults indicate severe errors like executing invalid opcodes, accessing unmapped memory, or violating MPU constraints. The hard fault handler receives a stacked exception frame containing the values of R0–R3, R12, LR, PC, and xPSR at the time of the fault. By examining the saved PC, you determine which instruction triggered the fault. The fault status registers (`CFSR`, `HFSR`, `DFSR`, `AFSR`, `MMFAR`, `BFAR`) provide additional diagnostic information: precise or imprecise bus faults, access violations, divide-by-zero exceptions, and unaligned memory accesses.

```c
void HardFault_Handler(void) {
    __asm volatile (
        "tst lr, #4 \n"
        "ite eq \n"
        "mrseq r0, msp \n"
        "mrsne r0, psp \n"
        "b hard_fault_handler_c \n"
    );
}

void hard_fault_handler_c(uint32_t *hardfault_args) {
    uint32_t stacked_r0 = hardfault_args[0];
    uint32_t stacked_r1 = hardfault_args[1];
    uint32_t stacked_r2 = hardfault_args[2];
    uint32_t stacked_r3 = hardfault_args[3];
    uint32_t stacked_r12 = hardfault_args[4];
    uint32_t stacked_lr = hardfault_args[5];
    uint32_t stacked_pc = hardfault_args[6];
    uint32_t stacked_psr = hardfault_args[7];
    
    uint32_t cfsr = SCB->CFSR;
    uint32_t hfsr = SCB->HFSR;
    uint32_t dfsr = SCB->DFSR;
    uint32_t afsr = SCB->AFSR;
    uint32_t bfar = SCB->BFAR;
    uint32_t mmfar = SCB->MMFAR;
    
    /* Log or transmit diagnostic information */
    /* Trigger debugger breakpoint or reset */
    __BKPT(0);
    
    while (1);
}
```

Cache coherency issues emerge on higher-end Cortex-M7 processors with data cache. DMA transfers bypass the CPU cache, writing directly to SRAM, so cached data becomes stale. Before initiating a DMA receive, you must invalidate the destination buffer's cache lines to force the CPU to fetch fresh data from SRAM after the transfer completes. Before initiating a DMA transmit, you must clean (write back) the source buffer's cache lines to ensure the DMA controller reads the latest data.

```c
void dma_receive_with_cache(uint8_t *buffer, uint16_t length) {
    /* Invalidate cache for the receive buffer */
    SCB_InvalidateDCache_by_Addr((uint32_t*)buffer, length);
    
    /* Configure and start DMA */
    HAL_UART_Receive_DMA(&huart1, buffer, length);
    
    /* Wait for completion */
    while (huart1.RxState != HAL_UART_STATE_READY);
}

void dma_transmit_with_cache(uint8_t *buffer, uint16_t length) {
    /* Clean cache for the transmit buffer */
    SCB_CleanDCache_by_Addr((uint32_t*)buffer, length);
    
    /* Configure and start DMA */
    HAL_UART_Transmit_DMA(&huart1, buffer, length);
}
```

Clock domain crossing introduces metastability when a signal generated in one clock domain gets sampled by logic running in another clock domain. If the signal transitions near the sampling clock edge, the flip-flop may enter a metastable state, outputting an intermediate voltage that eventually resolves to logic high or low, but unpredictably. Double-register synchronizers mitigate this risk by cascading two flip-flops, allowing the first to potentially enter metastability while the second samples a stable value.

Peripheral bus contention reduces determinism when multiple DMA channels or bus masters simultaneously access memory. ARM Cortex-M processors include a bus matrix that arbitrates access to flash, SRAM, and peripherals, but heavy DMA traffic can stall the CPU. Placing time-critical code in tightly-coupled memory (TCM), a dedicated SRAM region with zero-wait-state access, isolates it from bus contention.

Real-time deadline analysis combines task execution times, interrupt latencies, and scheduling overhead into a mathematical model that proves whether all deadlines can be met. Rate Monotonic Analysis (RMA) assigns priorities inversely proportional to task periods, proving that if the CPU utilization stays below approximately 69 percent for N tasks, all deadlines will be met. Earliest Deadline First (EDF) assigns priority dynamically based on the absolute deadline of each task's current job, achieving 100 percent utilization under ideal conditions but requiring more complex runtime overhead.

Power management failures arise when the system enters deep sleep before disabling peripherals that generate wake events. If a UART receiver is active when the processor enters Stop mode, an incoming byte might trigger a wake event before the clock stabilizes, corrupting the received data. The safe sequence disables the peripheral, flushes pending events, enters sleep, wakes up, restabilizes clocks, and re-enables the peripheral.

Temperature-dependent crystal drift affects timer accuracy over environmental conditions. A 20 ppm crystal might drift by 200 microseconds per second at temperature extremes, causing a 1-second timer to expire 800 microseconds early or late over a 4-second interval. Temperature-compensated crystal oscillators (TCXO) reduce drift to 1 ppm or less, but cost and power consumption increase. Software compensation reads an on-chip temperature sensor and adjusts timer reload values using a calibration table.

Bootloader security requires cryptographic verification to prevent malicious firmware installation. A secure boot process validates the firmware image's digital signature using an asymmetric key stored in write-protected flash or one-time-programmable memory before allowing execution. ARM TrustZone-M partitions the microcontroller into secure and non-secure domains, isolating cryptographic keys and signature verification code from application code that might contain vulnerabilities.

Flash wear leveling extends the lifetime of firmware update mechanisms by distributing erase cycles across multiple physical blocks. Flash memory endures 10,000 to 100,000 erase cycles per block; repeatedly erasing and rewriting the same application region during development or frequent updates can exhaust that block. A wear-leveling bootloader rotates firmware images across multiple flash banks or sectors, tracking erase counts in nonvolatile metadata.

The convergence of these techniques—careful interrupt priority assignment, minimal ISR execution time, lock-free data structures where appropriate, stack overflow detection, watchdog supervision, comprehensive fault handlers, cache coherency management, clock domain synchronization, deadline analysis, and secure boot—transforms the microcontroller from a simple instruction executor into a reliable, deterministic real-time system. Mastery requires not just understanding each mechanism in isolation, but recognizing how they interact: how priority inheritance prevents deadlocks that would trigger the watchdog, how cache cleaning ensures DMA transfers read correct data, how bootloader design affects firmware update reliability, and how power management interacts with peripheral wake sources. The embedded systems engineer architects these interactions, transforming hardware constraints into predictable, maintainable, and robust designs.
