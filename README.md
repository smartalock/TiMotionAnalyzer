# TiMotion Controller HLA

Logic2 High Level Analyzer for TiMotion UART desk protocol

Notes:

UART 9600 baud RX/TX between handset and controller

RJ50 10 pin cables

2. Black - unknown
4. Red - Sleep - floats high at 5V, handset to pull to GND to wake
7. Orange - GND
8. Yellow - RX (Controller -> Handset)
9. Green - TX (Handset -> Controller)
10. Blue +5V

All 10 pins connected to TVS diodes 9A1 (6V)

Pins 4, 5, 6 internally connected as pull high, handset can pull low via connected diode

Handset sends 5 byte packet to move desk

0xD8 0xD8 0x66|0x24 [BTN] [BTN]

Middle byte is the handset type/ID - TDH24P => 0x24

BTN is combination of

- 0x01 => DOWN
- 0x02 => UP
- 0x04 => "1"
- 0x08 => "2"
- 0x10 => "3"
- 0x20 => "4"
- 0x40 => "M"

Some handsets may have only single direction UART from controller --> handset, in which case handset can control height using pull downs on

6: UP (pull low to activate)
5: DOWN (pull low to activate)


Controller send several packet formats
0x9D 0x01 | 0x02 => currently unknown. 9d01 is 14 bytes 9d02 is 19 bytes

Other format

[3 byte checksum] [7 byte LCD display block] [6 byte status]

Checksum:
[0xaa 0xbb 0xcc] 8 bit sum with-out rollover bit - i.e. sum all numbers adds to multiple of 256 [these three bytes missing when desk in error state]

LCD Display Block:
[CHK] [DD] 00] [EE 00] [FF 00] - 7 bytes - 1st is 8 bit sum with rollover
CHK => (SUM(bytes) & 0xFF) + (SUM(bytes) >> 8)
DD/EE/FF are bits of 7 segment LED - a through to g https://en.wikipedia.org/wiki/Seven-segment_display
e.g. 
F9 => 'E'
3F => '0'
5B => '2'
4F => '3'
66 => '4'
73 => 'P'

     -----   0000 0001 
    |     |  0010 0000 (L)
    |     |  0000 0010 (R)
     -----   0100 0000
    |     |  0001 0000 (L)
    |     |  0000 0100 (R)
     -----   0000 1000

Status Block:
0x98 0x98 [STATE] [STATE] [HEIGHT] [HEIGHT] (bytes are repeated)
State:
STOPPED = 0
MOVING = 3
PROG_P1 = 7 (0x03 | 0x04)
PROG_P2 = B (0x03 | 0x08)
