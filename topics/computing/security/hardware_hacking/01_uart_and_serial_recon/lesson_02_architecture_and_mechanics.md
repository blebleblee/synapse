# Lesson 2: Protocol Mechanics & Bus Framing

## 1. Clock Synchronization & Signal Timing Diagrams

In the realm of UART (Universal Asynchronous Receiver/Transmitter) and serial communication, clock synchronization is paramount. UART operates asynchronously, meaning that the transmitter and receiver do not share a common clock signal. Instead, they rely on predefined baud rates to synchronize their operations. The baud rate specifies the number of bits per second that can be transmitted over the serial line. For instance, a baud rate of 9600 indicates that 9600 bits are transmitted per second.

The derivation of baud rates is rooted in the physical characteristics of the communication medium and the capabilities of the hardware. Common baud rates include 1200, 2400, 4800, 9600, 19200, 38400, 57600, and 115200. The choice of baud rate depends on the application's requirements for data rate and the tolerance for errors. Higher baud rates allow for faster data transmission but require more precise timing and synchronization.

Clock polarities, specifically the polarity of the clock signal, are another critical aspect of UART communication. UART does not use a clock signal explicitly; instead, it relies on the start and stop bits to synchronize the transmission and reception of data. However, in some variants of UART, such as SPI (Serial Peripheral Interface), clock polarity and phase (CPOL and CPHA) are defined to specify the timing relationship between the data and the clock signal. In UART, the absence of a clock signal means that the receiver must detect the start bit to synchronize with the incoming data stream.

Setup and hold times are essential timing parameters that ensure reliable data transmission. The setup time is the duration before the clock edge during which the data must be stable. The hold time is the duration after the clock edge during which the data must remain stable. These times are crucial to prevent metastability and ensure that the receiver correctly samples the data bits.

To illustrate these concepts, consider the following ASCII timing diagram for a UART transmission at 9600 baud with 8 data bits, no parity, and 1 stop bit:

```
Time (us)  0    1    2    3    4    5    6    7    8    9    10   11   12   13   14   15   16   17   18   19   20
           +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
           |    |    |    |    |    |    |    |    |    |    |    |    |    |    |    |    |    |    |    |    |
           +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
Start Bit  +----+--------------------------------------------------------------------------------------------+
           |    |                                                                                             |
           +----+                                                                                             +
Data Bits  +----+----+----+----+----+----+----+----+---------------------------------------------------------+
           |    |    |    |    |    |    |    |    |                                                         |
           +----+----+----+----+----+----+----+----+                                                         +
Stop Bit   +--------------------------------------------------------------------------------------------+----+
           |                                                                                            |    |
           +--------------------------------------------------------------------------------------------+----+
```

In this diagram, each time unit represents 104.167 microseconds (1/9600 seconds). The start bit is a low signal that indicates the beginning of a data frame. The data bits follow the start bit, and the stop bit is a high signal that indicates the end of the data frame. The receiver must detect the falling edge of the start bit to synchronize with the incoming data stream and sample the data bits at the correct times.

## 2. Frame Architecture & Bit-Level Encodings

The architecture of a UART frame is defined by the number of data bits, parity bits, and stop bits. A typical UART frame consists of a start bit, followed by the data bits, an optional parity bit, and one or more stop bits. The start bit is a single low bit that signals the beginning of a data frame. The data bits represent the actual data being transmitted, and the number of data bits can vary from 5 to 9. The parity bit is an optional bit used for error detection, and it can be either even or odd. The stop bit is a high bit that signals the end of a data frame, and it can be one, one and a half, or two bits long.

The bit-level encoding of a UART frame is critical for reliable data transmission. The start bit is always a low signal, and the stop bit is always a high signal. The data bits can be either high or low, depending on the value being transmitted. The parity bit, if present, is calculated based on the data bits and the parity mode. In even parity mode, the parity bit is set to ensure that the total number of high bits in the frame (including the start and stop bits) is even. In odd parity mode, the parity bit is set to ensure that the total number of high bits in the frame is odd.

To illustrate the bit-level encoding of a UART frame, consider the following example:

```
Data: 0x48 (0100 1000 in binary)
Baud Rate: 9600
Data Bits: 8
Parity: None
Stop Bits: 1

Frame: Start Bit + Data Bits + Stop Bit
       0         + 0100 1000 + 1
       0100 1000 1
```

In this example, the data byte 0x48 (0100 1000 in binary) is transmitted as a UART frame with 8 data bits, no parity, and 1 stop bit. The start bit is a low signal (0), followed by the 8 data bits (0100 1000), and the stop bit is a high signal (1).

## 3. Bus Transaction Lifecycle

The lifecycle of a UART bus transaction involves the end-to-end trace of a read/write command across the physical wire. A UART transaction begins with the transmitter sending a start bit to signal the beginning of a data frame. The receiver detects the falling edge of the start bit to synchronize with the incoming data stream. The transmitter then sends the data bits, and the receiver samples the data bits at the correct times based on the baud rate and setup/hold times. If a parity bit is present, the transmitter sends the parity bit, and the receiver checks the parity bit for error detection. Finally, the transmitter sends the stop bit to signal the end of the data frame.

To illustrate the lifecycle of a UART bus transaction, consider the following example:

```
Time (us)  0    1    2    3    4    5    6    7    8    9    10   11   12   13   14   15   16   17   18   19   20
           +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
           |    |    |    |    |    |    |    |    |    |    |    |    |    |    |    |    |    |    |    |    |
           +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
Start Bit  +----+--------------------------------------------------------------------------------------------+
           |    |                                                                                             |
           +----+                                                                                             +
Data Bits  +----+----+----+----+----+----+----+----+---------------------------------------------------------+
           |    |    |    |    |    |    |    |    |                                                         |
           +----+----+----+----+----+----+----+----+                                                         +
Stop Bit   +--------------------------------------------------------------------------------------------+----+
           |                                                                                            |    |
           +--------------------------------------------------------------------------------------------+----+
```

In this example, the transmitter sends a start bit to signal the beginning of a data frame. The receiver detects the falling edge of the start bit to synchronize with the incoming data stream. The transmitter then sends the data bits, and the receiver samples the data bits at the correct times based on the baud rate and setup/hold times. Finally, the transmitter sends the stop bit to signal the end of the data frame.

The lifecycle of a UART bus transaction is a critical aspect of reliable data transmission. The transmitter and receiver must synchronize their operations based on the baud rate and timing parameters to ensure that the data is transmitted and received correctly. Any deviation from the expected timing can result in errors and data corruption.

In conclusion, the mechanics and bus framing of UART and serial communication involve clock synchronization, signal timing diagrams, frame architecture, and bit-level encodings. Understanding these concepts is essential for embedded security engineers and hardware reverse engineers to design, implement, and analyze UART and serial communication systems. By mastering the lifecycle of a UART bus transaction, engineers can ensure reliable data transmission and detect and prevent errors in the communication process.
