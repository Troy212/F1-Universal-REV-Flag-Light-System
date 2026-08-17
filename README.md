# F1 Universal REV & Flag Light System

A DIY **Arduino + WS2812B/NeoPixel dynamic REV light and flag indicator system** for F1 games.

The system uses a 48-LED addressable strip connected to an Arduino. Game telemetry is received through UDP by a game-specific Python program, processed into RPM, redline, and flag information, and then sent to the Arduino through USB serial.

The Arduino uses the same universal firmware for every supported game.

## Supported Games

* **F1 2020**
* **F1 22**
* **F1 25**

> **Important:** This version does not include race-start lights. The 8 outer LEDs are dedicated to flag indications.

---

# Features

### Dynamic REV / RPM System

* Dynamic RPM-based REV lights
* Dynamic maximum RPM / redline
* Game-specific telemetry adapters
* Automatic `MAXRPM` updates
* Works with different cars and RPM limits
* Outside-to-center REV illumination
* Green → Yellow → Orange → Red RPM progression
* 40 dedicated REV LEDs

### Flag System

* Yellow flag
* Red flag
* Green flag
* Blue flag ignored
* Blinking flag indicators
* Automatic green-flag timeout
* Independent flag and REV systems

### Safety / Connection Features

* Automatic LED shutdown when telemetry is lost
* Universal Arduino firmware
* Same LED layout for every supported game
* Game-specific Python telemetry parsers

---

# How Dynamic REV Works

Unlike a fixed RPM system, the REV LEDs do **not** assume one maximum RPM for every car.

The Python telemetry program obtains the appropriate RPM limit/redline information from the game's telemetry and sends it to the Arduino.

For example:

```text
Game telemetry
      │
      ├── Current RPM
      │
      └── Maximum RPM / redline
              │
              ▼
       Python game adapter
              │
              ├── RPM:8500
              │
              └── MAXRPM:15000
              │
              ▼
       Universal Arduino
              │
              ▼
          40 REV LEDs
```

The Arduino then calculates the REV LED position from:

```text
Current RPM
     ÷
Maximum RPM
```

This means the same Arduino firmware can work with different RPM limits without manually changing the Arduino code.

---

# Hardware

## Required

* Arduino Uno / Nano or compatible Arduino
* WS2812B / NeoPixel addressable LED strip
* 48 LEDs
* USB cable
* PC running a supported F1 game

---

# LED Layout

The 48 LEDs are divided into three sections:

```text
LED 0 - 3       = Left flag LEDs
LED 4 - 43      = 40 REV/RPM LEDs
LED 44 - 47     = Right flag LEDs
```

```text
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│ FLAGS          REV / RPM LIGHTS                  FLAGS      │
│                                                             │
│ 0 1 2 3     4 ---------------------- 43       44 45 46 47 │
│ ████████    ████████████████████████████       ████████   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Total

```text
48 LEDs
│
├── 4 Left Flag LEDs
├── 40 REV/RPM LEDs
└── 4 Right Flag LEDs
```

---

# Software Structure

```text
F1-REV-Light-System/
│
├── f1_rev.py
├── f122_rev.py
├── f125_rev.py
├── universal_arduino.ino
└── README.md
```

### `f1_rev.py`

Telemetry adapter for **F1 2020**.

Handles:

* RPM
* Dynamic maximum RPM
* Yellow flag
* Red flag
* Green flag
* Telemetry timeout

### `f122_rev.py`

Telemetry adapter for **F1 22**.

Handles:

* RPM
* Dynamic maximum RPM
* Yellow flag
* Red flag
* Green flag
* Telemetry timeout
* F1 22 UDP packet format

### `f125_rev.py`

Telemetry adapter for **F1 25**.

Handles:

* RPM
* Dynamic maximum RPM
* Yellow flag
* Red flag
* Green flag
* Telemetry timeout
* F1 25 UDP packet format

### `universal_arduino.ino`

Game-independent Arduino firmware.

It receives standardized commands from the Python programs and controls the 48 LEDs.

---

# System Architecture

```text
                       ┌──────────────┐
                       │   F1 2020    │
                       └──────┬───────┘
                              │ UDP
                              ▼
                       ┌──────────────┐
                       │  f1_rev.py   │
                       └──────┬───────┘
                              │
                              │
┌──────────────┐              │              ┌──────────────┐
│    F1 22     │              │              │    F1 25     │
└──────┬───────┘              │              └──────┬───────┘
       │ UDP                   │                   │ UDP
       ▼                       ▼                   ▼
┌──────────────┐       ┌────────────────┐   ┌──────────────┐
│f122_rev.py   │       │ Universal      │   │f125_rev.py   │
└──────┬───────┘       │ Arduino        │   └──────┬───────┘
       │               │ Firmware       │           │
       └──────────────►│                │◄──────────┘
                       └───────┬────────┘
                               │
                               ▼
                         ┌───────────┐
                         │ 48 LEDs   │
                         └───────────┘
```

Every Python program converts its game's telemetry into the same Arduino command protocol.

---

# Telemetry Flow

```text
F1 Game
   │
   │ UDP telemetry
   ▼
Python Adapter
   │
   ├── Current RPM
   ├── Maximum RPM / redline
   ├── Flag state
   └── Telemetry status
   │
   │ USB Serial
   ▼
Arduino
   │
   ├── REV LEDs
   └── Flag LEDs
```

---

# F1 Telemetry Configuration

The supported games use:

```text
UDP Telemetry = On
UDP Broadcast = Off
IP Address    = 127.0.0.1
UDP Port      = 20777
Send Rate     = 60 Hz
```

`127.0.0.1` is used because the game and Python telemetry program are running on the same PC.

---

# F1 2020 Settings

In **F1 2020**, go to:

```text
Settings
→ Telemetry Settings
```

Configure:

| Setting            | Value         |
| ------------------ | ------------- |
| UDP Telemetry      | **On**        |
| UDP Broadcast Mode | **Off**       |
| UDP IP Address     | **127.0.0.1** |
| UDP Port           | **20777**     |
| UDP Send Rate      | **60 Hz**     |
| UDP Format         | **2020**      |

Final configuration:

```text
UDP Telemetry       = On
UDP Broadcast       = Off
UDP IP Address      = 127.0.0.1
UDP Port            = 20777
UDP Send Rate       = 60 Hz
UDP Format          = 2020
```

Run:

```bash
python f1_rev.py
```

Expected:

```text
Arduino connected on COM4
Waiting for F1 2020 telemetry...
```

Once you enter a driving session, the REV LEDs should respond dynamically to engine RPM.

---

# F1 22 Settings

In **F1 22**, go to:

```text
Settings
→ Telemetry Settings
```

Configure:

| Setting            | Value         |
| ------------------ | ------------- |
| UDP Telemetry      | **On**        |
| UDP Broadcast Mode | **Off**       |
| UDP IP Address     | **127.0.0.1** |
| UDP Port           | **20777**     |
| UDP Send Rate      | **60 Hz**     |
| UDP Format         | **2022**      |

Final configuration:

```text
UDP Telemetry       = On
UDP Broadcast       = Off
UDP IP Address      = 127.0.0.1
UDP Port            = 20777
UDP Send Rate       = 60 Hz
UDP Format          = 2022
```

> **Important:** F1 22 must use the **2022 UDP telemetry format**. Do not use the F1 25 or 2026 format with `f122_rev.py`.

Run:

```bash
python f122_rev.py
```

Expected:

```text
Arduino connected on COM4
Waiting for F1 22 telemetry...
```

---

# F1 25 Settings

In **F1 25**, go to:

```text
Settings
→ Telemetry Settings
```

Configure:

| Setting            | Value         |
| ------------------ | ------------- |
| UDP Telemetry      | **On**        |
| UDP Broadcast Mode | **Off**       |
| UDP IP Address     | **127.0.0.1** |
| UDP Port           | **20777**     |
| UDP Send Rate      | **60 Hz**     |
| UDP Mode           | **F1 25**     |

Use:

```text
F1 25
```

and **not**:

```text
F1 25: 2026 Season Pack
```

Final configuration:

```text
UDP Telemetry       = On
UDP Broadcast       = Off
UDP IP Address      = 127.0.0.1
UDP Port            = 20777
UDP Send Rate       = 60 Hz
UDP Mode            = F1 25
```

Run:

```bash
python f125_rev.py
```

Expected:

```text
Arduino connected on COM4
Waiting for F1 25 telemetry...
```

---

# Dynamic REV System

The REV system uses two values:

```text
Current RPM
Maximum RPM
```

Example:

```text
RPM:8500
MAXRPM:15000
```

The Arduino calculates:

```text
RPM percentage = Current RPM / Maximum RPM
```

For example:

```text
8500 / 15000 = 56.7%
```

The REV system then illuminates approximately:

```text
56.7% × 40 LEDs
```

which is approximately:

```text
23 LEDs
```

---

# Dynamic RPM Color Zones

The REV system progressively changes color as RPM increases.

| RPM Range | Color     |
| --------- | --------- |
| 0–60%     | 🟢 Green  |
| 60–75%    | 🟡 Yellow |
| 75–90%    | 🟠 Orange |
| 90–100%   | 🔴 Red    |

The exact LED transition is calculated dynamically from the current maximum RPM.

This means the color ranges automatically scale with the car's RPM range.

---

# Outside-to-Center Animation

The 40 REV LEDs illuminate from the outside toward the center.

```text
Low RPM

🟢                                🟢


Medium RPM

🟢🟢🟢🟡                    🟡🟢🟢🟢


High RPM

🟢🟢🟡🟡🟠🔴          🔴🟠🟡🟡🟢🟢


Redline

🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴
```

The system mirrors the REV display so both sides illuminate toward the center.

---

# Dynamic Maximum RPM

The Arduino accepts:

```text
MAXRPM:xxxx
```

Example:

```text
MAXRPM:15000
```

The Python telemetry adapter can update this value when necessary.

The Arduino does **not** need to know which game is running.

For example:

```text
F1 2020
    ↓
f1_rev.py
    ↓
MAXRPM:15000
```

or:

```text
F1 22
    ↓
f122_rev.py
    ↓
MAXRPM:15000
```

or:

```text
F1 25
    ↓
f125_rev.py
    ↓
MAXRPM:15000
```

The Arduino handles all three identically.

---

# Important Dynamic RPM Design

The game-specific Python programs are responsible for determining the appropriate maximum RPM value.

The Arduino only receives normalized information:

```text
RPM:current
MAXRPM:maximum
```

This separation keeps the Arduino firmware universal.

```text
Game-specific logic
        ↓
Python
        ↓
Standard command protocol
        ↓
Universal Arduino
```

This also makes future games easier to support.

---

# Flag System

The outer 8 LEDs are dedicated to flags.

```text
LEFT FLAGS                         RIGHT FLAGS

0  1  2  3                         44 45 46 47
████████                           ████████
```

The flag system is independent of the REV LEDs.

---

# Yellow Flag

Command:

```text
YELLOW
```

The 8 outer LEDs blink yellow.

```text
🟡🟡🟡🟡          🟡🟡🟡🟡
```

---

# Red Flag

Command:

```text
RED
```

The 8 outer LEDs blink red.

```text
🔴🔴🔴🔴          🔴🔴🔴🔴
```

---

# Green Flag

Command:

```text
GREEN
```

The 8 outer LEDs illuminate green.

```text
🟢🟢🟢🟢          🟢🟢🟢🟢
```

The green indication automatically turns off after the configured duration.

---

# Blue Flag

The Arduino supports the command:

```text
BLUE
```

However, the current F1 telemetry implementation does not use blue flags.

Therefore:

```text
Blue flag = ignored
```

---

# Clearing Flags

The Python programs can send:

```text
NONE
```

to clear the active flag.

The REV LEDs continue operating independently.

---

# Automatic Telemetry Shutdown

If telemetry is not received for approximately **3 seconds**, the system automatically turns the LEDs off.

The system sends:

```text
OFF
```

This protects against the REV display becoming frozen at the last telemetry value.

It is useful when:

* The game is closed
* The game crashes
* UDP telemetry stops
* The Python program stops
* The session ends
* The Arduino connection is interrupted

---

# Arduino Setup

Install the Arduino library:

```text
Adafruit NeoPixel
```

Upload:

```text
universal_arduino.ino
```

Default configuration:

```cpp
#define LED_PIN 6
#define NUM_LEDS 48
```

If the LED data wire is connected to another Arduino pin, change:

```cpp
#define LED_PIN 6
```

to the appropriate pin.

---

# Arduino Serial Configuration

The Python programs communicate with the Arduino through USB serial.

Default:

```text
COM4
9600 baud
```

Python configuration:

```python
ARDUINO_PORT = "COM4"
ARDUINO_BAUD = 9600
```

If Windows assigns another COM port:

```python
ARDUINO_PORT = "COM5"
```

For example.

## Important

Close any application using the Arduino COM port, including:

* Arduino Serial Monitor
* Arduino Serial Plotter
* SimHub
* Other Python telemetry scripts
* Other serial terminal software

Otherwise Windows may report:

```text
PermissionError: [WinError 5] Access is denied
```

---

# Arduino Command Protocol

The universal Arduino understands the following commands:

| Command       | Function             |
| ------------- | -------------------- |
| `RPM:xxxx`    | Update current RPM   |
| `MAXRPM:xxxx` | Update maximum RPM   |
| `YELLOW`      | Activate yellow flag |
| `RED`         | Activate red flag    |
| `BLUE`        | Activate blue flag   |
| `GREEN`       | Activate green flag  |
| `NONE`        | Clear flag           |
| `OFF`         | Turn all LEDs off    |

Example:

```text
MAXRPM:15000
RPM:8500
```

The Arduino calculates the REV position dynamically.

---

# Example Dynamic REV Sequence

Suppose the telemetry reports:

```text
MAXRPM:15000
```

At:

```text
RPM:6000
```

the REV display is approximately:

```text
40%
```

At:

```text
RPM:9000
```

the REV display is approximately:

```text
60%
```

At:

```text
RPM:12000
```

the REV display is approximately:

```text
80%
```

At:

```text
RPM:15000
```

the REV display is:

```text
100%
```

The actual number of LEDs is calculated from the 40 available REV LEDs.

---

# Python Requirements

Install Python 3.

Install PySerial:

```bash
pip install pyserial
```

Required package:

```text
pyserial
```

The telemetry programs otherwise use Python's standard networking functionality unless additional dependencies are included by a particular implementation.

---

# Running F1 2020

1. Connect the Arduino.
2. Upload `universal_arduino.ino`.
3. Check the Arduino COM port.
4. Start F1 2020.
5. Enable UDP telemetry.
6. Configure the UDP settings.
7. Run:

```bash
python f1_rev.py
```

8. Enter a driving session.
9. Drive the car.

The Python program receives telemetry and sends:

```text
RPM
MAXRPM
FLAG
```

information to the Arduino.

---

# Running F1 22

1. Connect the Arduino.
2. Upload `universal_arduino.ino`.
3. Check the Arduino COM port.
4. Start F1 22.
5. Enable UDP telemetry.
6. Set UDP format to **2022**.
7. Configure port `20777`.
8. Run:

```bash
python f122_rev.py
```

9. Enter a driving session.
10. Drive the car.

The Arduino firmware does not change.

---

# Running F1 25

1. Connect the Arduino.
2. Upload `universal_arduino.ino`.
3. Check the Arduino COM port.
4. Start F1 25.
5. Enable UDP telemetry.
6. Select the **F1 25** UDP mode.
7. Do not select the separate 2026 Season Pack mode.
8. Configure port `20777`.
9. Run:

```bash
python f125_rev.py
```

10. Enter a driving session.
11. Drive the car.

The same Arduino firmware is used.

---

# Troubleshooting

## `Waiting for telemetry...`

Check:

```text
UDP Telemetry = On
UDP Broadcast = Off
IP Address    = 127.0.0.1
UDP Port      = 20777
```

Also verify the correct telemetry format.

### F1 2020

```text
2020
```

### F1 22

```text
2022
```

### F1 25

```text
F1 25
```

Do not use the 2026 Season Pack telemetry mode with the F1 25 adapter.

---

# REV Lights Are Not Responding

Check:

1. UDP telemetry is enabled.
2. The correct Python program is running.
3. The correct telemetry format is selected.
4. UDP port is `20777`.
5. IP address is `127.0.0.1`.
6. Arduino is connected.
7. Python is using the correct COM port.
8. Arduino baud rate is `9600`.
9. The LED data line is connected correctly.
10. The LED strip has an adequate power supply and common ground with the Arduino.

---

# REV Lights Use the Wrong RPM Range

The dynamic system depends on the Python adapter providing the correct:

```text
MAXRPM
```

Check that the Python program is sending a value such as:

```text
MAXRPM:15000
```

The Arduino does not identify the game or vehicle.

It simply uses:

```text
Current RPM
      ÷
Maximum RPM
```

to calculate the REV position.

---

# Flags Are Not Detected

Flag detection is handled by the game-specific Python telemetry adapter.

The Arduino only displays the command it receives:

```text
YELLOW
RED
GREEN
BLUE
NONE
```

Different F1 games expose flag information differently, so each Python adapter must interpret its game's telemetry correctly.

---

# Arduino COM Port Error

If you see:

```text
PermissionError: [WinError 5] Access is denied
```

close:

```text
Arduino Serial Monitor
Arduino Serial Plotter
SimHub
Other Python scripts
Serial terminal programs
```

Then restart the Python program.

---

# Telemetry Timeout

If the LEDs turn off after several seconds, this normally means the Python program stopped receiving telemetry.

Check:

```text
Game running
      ↓
UDP telemetry enabled
      ↓
127.0.0.1
      ↓
Port 20777
      ↓
Correct Python adapter
```

The timeout is intentional and prevents stale RPM/flag information from remaining displayed.

---

# Universal Arduino Architecture

The Arduino firmware is completely game-independent.

```text
F1 2020 ──► f1_rev.py ─────┐
                            │
F1 22 ────► f122_rev.py ────┼──► Universal Arduino ──► 48 LEDs
                            │
F1 25 ────► f125_rev.py ────┘
```

Each Python adapter performs the game-specific work.

The Arduino receives the same standardized commands regardless of the game.

---

# Why Use Dynamic REV?

A fixed RPM configuration assumes every car has the same RPM range.

That is not ideal for a universal sim-racing system.

With dynamic RPM:

```text
Current RPM
     │
     ▼
Game telemetry
     │
     ├── Maximum RPM
     │
     ▼
Python adapter
     │
     ▼
Universal Arduino
```

The REV display automatically scales to the configured maximum RPM.

This makes the system more suitable for different cars and future telemetry implementations.

---

# Future Game Support

The universal Arduino architecture allows additional racing games to be added without rewriting the Arduino firmware.

For example:

```text
Assetto Corsa
      ↓
assetto_corsa.py
      ↓
RPM + MAXRPM + FLAGS
      ↓
Universal Arduino
      ↓
48 LEDs
```

A future adapter only needs to convert the game's telemetry into the existing command protocol.

---

# Project Status

## F1 2020

* [x] UDP telemetry
* [x] RPM/REV lights
* [x] Dynamic RPM scaling
* [x] Dynamic maximum RPM
* [x] Outside-to-center REV animation
* [x] Green RPM range
* [x] Yellow RPM range
* [x] Orange RPM range
* [x] Redline
* [x] Yellow flag
* [x] Red flag
* [x] Green flag
* [x] Automatic telemetry timeout
* [x] Universal Arduino

## F1 22

* [x] UDP telemetry
* [x] RPM/REV lights
* [x] Dynamic RPM scaling
* [x] Dynamic maximum RPM
* [x] Outside-to-center REV animation
* [x] Green RPM range
* [x] Yellow RPM range
* [x] Orange RPM range
* [x] Redline
* [x] Yellow flag
* [x] Red flag
* [x] Green flag
* [x] Blue flag ignored
* [x] Automatic telemetry timeout
* [x] F1 22 UDP format
* [x] Universal Arduino

## F1 25

* [x] UDP telemetry
* [x] RPM/REV lights
* [x] Dynamic RPM scaling
* [x] Dynamic maximum RPM
* [x] Outside-to-center REV animation
* [x] Green RPM range
* [x] Yellow RPM range
* [x] Orange RPM range
* [x] Redline
* [x] Flag system
* [x] Automatic telemetry timeout
* [x] F1 25 UDP mode
* [x] Universal Arduino

---

# Hardware Layout

```text
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│ FLAGS          REV / RPM LIGHTS                  FLAGS      │
│                                                             │
│ 0 1 2 3     4 ---------------------- 43       44 45 46 47 │
│ ████████    ████████████████████████████       ████████   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 48 LEDs Total

```text
4 × Left Flag
40 × REV / RPM
4 × Right Flag
```

---

# Telemetry Documentation

The telemetry adapters are designed around the UDP telemetry formats provided for the respective F1 games.

For:

```text
F1 2020 → F1 2020 UDP format
F1 22   → F1 22 / 2022 UDP format
F1 25   → F1 25 UDP mode
```

The F1 25 adapter is intended for the **F1 25 telemetry mode**, not the separate 2026 Season Pack telemetry specification.

---

# License

This is a personal/community DIY sim-racing project.

F1, F1 2020, F1 22, F1 25 and related game assets are trademarks of their respective owners.

This project is not affiliated with or endorsed by **EA, Codemasters, or Formula 1**.
