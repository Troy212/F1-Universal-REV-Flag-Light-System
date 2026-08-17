# F1 Universal REV & Flag Light System

A DIY **Arduino + WS2812B/NeoPixel REV light and flag indicator system** for F1 games.

The system uses a 48-LED addressable strip connected to an Arduino. Game telemetry is received through UDP by a Python program and converted into serial commands for the Arduino.

## Supported Games

* **F1 2020**
* **F1 22**
* **F1 25**

The Arduino firmware is **universal for all supported games**.

> **Important:** This project does **not** include race-start lights. The 8 outer LEDs are used only for flag indications.

---

# Features

* 🟢 Dynamic RPM/REV lights
* 🟡 Yellow RPM range
* 🟠 Orange RPM range
* 🔴 Redline
* 🔄 REV lights illuminate from the outside toward the center
* 🟡 Yellow flag
* 🔴 Red flag
* 🟢 Green flag
* 💡 Blinking flag indicators
* ⏱️ Green flag automatically turns off
* 🛑 LEDs automatically turn off when telemetry is lost
* 🎮 Separate Python telemetry programs for F1 2020, F1 22 and F1 25
* 🔧 One universal Arduino firmware for all supported games

---

# Hardware

## Required

* Arduino Uno/Nano or compatible Arduino
* WS2812B / NeoPixel addressable LED strip
* 48 LEDs
* USB cable
* PC running the supported F1 game

---

# LED Layout

The 48 LEDs are divided into two sections:

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

Python telemetry program for **F1 2020**.

### `f122_rev.py`

Python telemetry program for **F1 22**.

### `f125_rev.py`

Python telemetry program for **F1 25**.

### `universal_arduino.ino`

Universal Arduino firmware used by all supported games.

---

# How It Works

```text
F1 Game
   │
   │ UDP Telemetry
   ▼
Python Telemetry Script
   │
   │ USB Serial
   ▼
Arduino
   │
   ▼
48 LED Strip
```

For F1 2020:

```text
F1 2020
   ↓
f1_rev.py
   ↓
Arduino
   ↓
48 LEDs
```

For F1 22:

```text
F1 22
   ↓
f122_rev.py
   ↓
Arduino
   ↓
48 LEDs
```

For F1 25:

```text
F1 25
   ↓
f125_rev.py
   ↓
Arduino
   ↓
48 LEDs
```

---

# F1 Telemetry Configuration

The game must be configured to send UDP telemetry to the PC running the Python script.

For all supported games, this project uses:

```text
UDP Telemetry = On
UDP Broadcast = Off
IP Address    = 127.0.0.1
UDP Port      = 20777
Send Rate     = 60 Hz
```

`127.0.0.1` is used because the game and Python program are running on the same PC.

---

# F1 2020 Settings

In **F1 2020**, go to:

```text
Settings
→ Telemetry Settings
```

Use:

| Setting            | Value         |
| ------------------ | ------------- |
| UDP Telemetry      | **On**        |
| UDP Broadcast Mode | **Off**       |
| UDP IP Address     | **127.0.0.1** |
| UDP Port           | **20777**     |
| UDP Send Rate      | **60 Hz**     |
| UDP Format         | **2020**      |

### Final F1 2020 configuration

```text
UDP Telemetry       = On
UDP Broadcast       = Off
UDP IP Address      = 127.0.0.1
UDP Port            = 20777
UDP Send Rate       = 60 Hz
UDP Format          = 2020
```

Then run:

```bash
python f1_rev.py
```

You should see:

```text
Arduino connected on COM4
Waiting for F1 2020 telemetry...
```

Enter a driving session and the REV LEDs should respond to RPM.

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

### Final F1 22 configuration

```text
UDP Telemetry       = On
UDP Broadcast       = Off
UDP IP Address      = 127.0.0.1
UDP Port            = 20777
UDP Send Rate       = 60 Hz
UDP Format          = 2022
```

> **Important:** F1 22 must use the **2022 UDP telemetry format**. Do not use the F1 25 or 2026 format with `f122_rev.py`.

Then run:

```bash
python f122_rev.py
```

You should see:

```text
Arduino connected on COM4
Waiting for F1 22 telemetry...
```

Enter a driving session and the REV LEDs should respond to RPM.

### F1 22 Telemetry

The F1 22 Python program handles:

* 🟢 Engine RPM telemetry
* 🟡 Yellow flag detection
* 🔴 Red flag detection
* 🟢 Green flag detection
* ❌ Blue flag ignored
* 🛑 Automatic LED shutdown when telemetry is lost

The F1 22 program reads the game's **Car Telemetry**, **Car Status**, **Lap Data**, and **Session** telemetry packets.

The flag system can use both FIA flag information and marshal-zone information to detect track flags.

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
| UDP Format / Mode  | **F1 25**     |

## ⚠️ Important F1 25 UDP Mode

Select:

```text
F1 25
```

The `f125_rev.py` program in this repository is intended for the **F1 25 UDP telemetry format**, not the separate **2026 Season Pack UDP specification**.

### Final F1 25 configuration

```text
UDP Telemetry       = On
UDP Broadcast       = Off
UDP IP Address      = 127.0.0.1
UDP Port            = 20777
UDP Send Rate       = 60 Hz
UDP Format / Mode   = 2025
```

Then run:

```bash
python f125_rev.py
```

You should see:

```text
Arduino connected on COM4
Waiting for F1 25 telemetry...
```

Enter a driving session and the REV LEDs should respond to RPM.

---

# UDP Port

The project uses:

```text
20777
```

The Python programs listen on:

```python
UDP_IP = "127.0.0.1"
UDP_PORT = 20777
```

The game and Python program must use the same port.

```text
F1 Game
UDP Port: 20777
      │
      ▼
Python
UDP Port: 20777
```

If the game uses another port, change the Python configuration to match.

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

The default configuration is:

```cpp
#define LED_PIN 6
#define NUM_LEDS 48
```

If your LED data wire uses another Arduino pin, change `LED_PIN`.

---

# Arduino Serial Configuration

The Python programs communicate with the Arduino using:

```text
COM4
9600 baud
```

Python configuration:

```python
ARDUINO_PORT = "COM4"
ARDUINO_BAUD = 9600
```

If your Arduino is on another COM port, change it.

Example:

```python
ARDUINO_PORT = "COM5"
```

## Important

Close:

* Arduino Serial Monitor
* Arduino Serial Plotter
* SimHub
* Other Python scripts
* Any other program using the Arduino COM port

Otherwise Windows can show:

```text
PermissionError: [WinError 5] Access is denied
```

---

# REV / RPM System

The 40 center LEDs display engine RPM.

The LEDs illuminate:

```text
OUTSIDE → CENTER ← OUTSIDE
```

Example:

```text
Low RPM

🟢                                🟢


Medium RPM

🟢🟢🟢🟡                    🟡🟢🟢🟢


Near Redline

🟢🟢🟡🟡🟠🔴          🔴🟠🟡🟡🟢🟢
```

## RPM Colors

| RPM Stage | Color     |
| --------- | --------- |
| Low       | 🟢 Green  |
| Medium    | 🟡 Yellow |
| High      | 🟠 Orange |
| Redline   | 🔴 Red    |

The Arduino receives RPM commands such as:

```text
RPM:8500
```

---

# Automatic RPM Scaling

The Arduino supports:

```text
MAXRPM:xxxx
```

For example:

```text
MAXRPM:15000
```

This allows different cars with different RPM limits to use the same REV system.

The long-term goal is for the Python telemetry programs to automatically determine the appropriate maximum RPM from the car telemetry.

---

# Flag System

The outer 8 LEDs are used for flags.

```text
LEFT FLAGS                         RIGHT FLAGS

0  1  2  3                         44 45 46 47
████████                           ████████
```

Supported flags:

* Yellow
* Red
* Blue
* Green

---

# Yellow Flag

The 8 flag LEDs blink yellow.

```text
🟡🟡🟡🟡          🟡🟡🟡🟡
```

Command:

```text
YELLOW
```

---

# Red Flag

The 8 flag LEDs blink red.

```text
🔴🔴🔴🔴          🔴🔴🔴🔴
```

Command:

```text
RED
```

---

# Green Flag

The 8 flag LEDs illuminate green.

```text
🟢🟢🟢🟢          🟢🟢🟢🟢
```

Command:

```text
GREEN
```

The green indication automatically turns off after the configured duration.

---

# Clearing Flags

The Arduino accepts:

```text
NONE
```

to clear the current flag.

The RPM LEDs continue operating independently.

---

# Automatic LED Shutdown

If the Python program stops receiving telemetry for approximately **3 seconds**, the system sends:

```text
OFF
```

This turns off the LEDs.

This is useful when:

* The game is closed
* The game crashes
* UDP telemetry stops
* The Python program loses the connection
* A session ends

The REV LEDs therefore won't remain frozen at the last RPM value.

---

# Python Requirements

Install Python 3.

Then install PySerial:

```bash
pip install pyserial
```

Required package:

```text
pyserial
```

---

# Running F1 2020

1. Connect the Arduino.
2. Upload `universal_arduino.ino`.
3. Check the Arduino COM port.
4. Start F1 2020.
5. Enable UDP telemetry.
6. Use the F1 2020 settings shown above.
7. Run:

```bash
python f1_rev.py
```

8. Enter a driving session.
9. Drive the car.

The REV LEDs should respond to engine RPM.

---

# Running F1 22

1. Connect the Arduino.
2. Upload `universal_arduino.ino`.
3. Check the Arduino COM port.
4. Start F1 22.
5. Enable UDP telemetry.
6. Set **UDP Format = 2022**.
7. Use the F1 22 settings shown above.
8. Run:

```bash
python f122_rev.py
```

9. Enter a driving session.
10. Drive the car.

The same Arduino firmware is used.

---

# Running F1 25

1. Connect the Arduino.
2. Upload `universal_arduino.ino`.
3. Check the Arduino COM port.
4. Start F1 25.
5. Enable UDP telemetry.
6. Select **F1 25**, not **F1 25: 2026 Season Pack**.
7. Use the F1 25 settings shown above.
8. Run:

```bash
python f125_rev.py
```

9. Enter a driving session.
10. Drive the car.

The same Arduino firmware is used.

---

# Arduino Command Protocol

The universal Arduino understands:

| Command       | Function            |
| ------------- | ------------------- |
| `RPM:xxxx`    | Update REV/RPM LEDs |
| `MAXRPM:xxxx` | Set maximum RPM     |
| `YELLOW`      | Yellow flag         |
| `RED`         | Red flag            |
| `BLUE`        | Blue flag           |
| `GREEN`       | Green flag          |
| `NONE`        | Clear flag          |
| `OFF`         | Turn all LEDs off   |

There are **no race-start commands** in this version.

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

Also make sure the correct UDP format is selected.

For F1 22:

```text
✅ 2022
❌ 2025
❌ 2026
```

For F1 25:

```text
✅ 2025
❌ 2026
```

---

## Arduino COM port error

If you see:

```text
PermissionError: [WinError 5] Access is denied
```

close Arduino Serial Monitor and any other software using the Arduino.

---

## REV lights are not responding

Check:

1. UDP telemetry is enabled.
2. Correct UDP format is selected.
3. UDP port is `20777`.
4. IP address is `127.0.0.1`.
5. Correct Python script is running.
6. Arduino is connected to the correct COM port.
7. LED power and data connections are correct.

---

## Flags are not detected

The Arduino supports:

```text
YELLOW
RED
BLUE
GREEN
```

but **flag detection is handled by the game-specific Python program**.

Different F1 games expose flag information differently, so the Python telemetry parser must correctly interpret that game's telemetry.

The Arduino itself only displays the command it receives.

---

# Universal Arduino Design

The Arduino firmware is completely game-independent.

```text
             F1 2020
                │
                ▼
           f1_rev.py
                │
                │
                ▼
        ┌───────────────┐
        │   Universal   │
        │    Arduino    │
        └───────┬───────┘
                │
                ▼
             48 LEDs
                ▲
                │
        ┌───────┴───────┐
        │               │
     F1 22           F1 25
        │               │
        ▼               ▼
   f122_rev.py    f125_rev.py
```

This means future racing games can be supported by creating another Python telemetry adapter without changing the Arduino firmware.

For example:

```text
Assetto Corsa
      ↓
assetto_corsa.py
      ↓
RPM / Flags
      ↓
Universal Arduino
```

---

# Project Status

## F1 2020

* [x] UDP telemetry
* [x] RPM/REV lights
* [x] Outside-to-center REV animation
* [x] Green/yellow/orange/red RPM progression
* [x] Flag system
* [x] Automatic telemetry timeout
* [x] Universal Arduino

## F1 22

* [x] UDP telemetry
* [x] RPM/REV lights
* [x] Outside-to-center REV animation
* [x] Green/yellow/orange/red RPM progression
* [x] Yellow flag
* [x] Red flag
* [x] Green flag
* [x] Blue flag disabled
* [x] Automatic telemetry timeout
* [x] Universal Arduino
* [x] F1 22 UDP format

## F1 25

* [x] UDP telemetry
* [x] RPM/REV lights
* [x] Outside-to-center REV animation
* [x] Universal Arduino
* [x] Flag system
* [x] Automatic telemetry timeout
* [x] F1 25 UDP mode

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

**48 LEDs total:**

* 4 left flag LEDs
* 40 REV/RPM LEDs
* 4 right flag LEDs

---

# Telemetry Documentation

For F1 2020, the telemetry configuration follows the F1 2020 UDP telemetry specification.

For F1 22, use the **F1 22 UDP telemetry format (`2022`)**.

For F1 25, use the **F1 25 UDP mode** and not the separate **2026 Season Pack UDP mode**.

EA provides the F1 telemetry specifications through its F1 Game Info Hub.

---

# License

This is a personal/community DIY sim-racing project.

F1, F1 2020, F1 22, F1 25 and related game assets are trademarks of their respective owners. This project is not affiliated with or endorsed by EA, Codemasters, or Formula 1.
