# 🏎️ F1 Universal REV & Flag Light System

A DIY **Arduino + WS2812B/NeoPixel dynamic REV light and flag indicator system** for racing games.

The project uses a **48-LED addressable strip**, an Arduino, and game-specific Python telemetry adapters. Telemetry is received from the game through UDP, converted into a universal command format, and sent to the Arduino through USB serial.

The Arduino firmware is **universal** across all supported games.

## 🎮 Supported Games

* **F1 2020**
* **F1 22**
* **F1 25**
* **Assetto Corsa Competizione (ACC)**
* **Assetto Corsa (AC)**

Each game has its own Python telemetry adapter, while all games use the same Arduino firmware.

---

# ✨ Features

## 🔥 Dynamic REV / RPM Lights

* Dynamic RPM-based REV lights
* Automatic RPM scaling
* Dynamic maximum RPM / redline
* Outside-to-center illumination
* 40 dedicated REV LEDs
* Green → Yellow → Orange → Red progression
* Game-specific RPM telemetry
* Universal Arduino firmware
* Different RPM ranges can be used without changing the Arduino code

## 🟢 Shift Point Indicator

The system includes a **SHIFT** mode.

When the Python telemetry adapter detects that it is the appropriate time to shift:

```text
SHIFT
```

is sent to the Arduino.

The **LED REV section flashes** to indicate the shift point.

```text
████████████████████████████████████████
                SHIFT
████████████████████████████████████████
```


Supported:

* F1 2020
* F1 22
* F1 25
* Assetto Corsa Competizione
* Assetto Corsa

## 🚦 Race Start / Lights Out

Race-start functionality is supported where implemented by the individual telemetry adapter.

Current implementations include:

* **F1 22** — Lights Out
* **F1 25** — Lights Out

The Arduino can display start-light commands independently from the RPM system.

## 🟡 Flag System

Supported flag commands include:

* Yellow
* Red
* Green
* Blue

The outer LEDs are dedicated to flag indications.

Features include:

* Blinking yellow flag
* Blinking red flag
* Green flag indication
* Automatic green-flag timeout
* Independent flag and REV operation

Blue flags can be ignored by adapters where they are not required.

## 🛑 Safety Features

* Automatic LED shutdown when telemetry is lost
* Serial communication watchdog
* Automatic clearing of stale RPM data
* Game-independent Arduino firmware
* Python telemetry adapters separated from LED logic

---

# 💡 LED Layout

The system uses **48 WS2812B / NeoPixel LEDs**.

```text
LED 0 - 3       = LEFT FLAGS
LED 4 - 43      = REV / RPM
LED 44 - 47     = RIGHT FLAGS
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

### LED allocation

```text
48 LEDs
│
├── 4 × Left Flag LEDs
├── 40 × REV / RPM LEDs
└── 4 × Right Flag LEDs
```

The **40 center LEDs** are used for RPM and shift indication.

The **8 outer LEDs** are used for flags and race-start indications where supported.

---

# 🧠 System Architecture

Each game has its own telemetry parser.

```text
                         ┌───────────────┐
                         │   F1 2020     │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │  f1_rev.py    │
                         └───────┬───────┘
                                 │
                                 │
┌───────────────┐                │                ┌───────────────┐
│    F1 22      │                │                │    F1 25      │
└───────┬───────┘                │                └───────┬───────┘
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐        ┌────────────────┐       ┌───────────────┐
│ f122_rev.py   │───────►│    Arduino     │◄──────│ f125_rev.py   │
└───────────────┘        │    Universal   │       └───────────────┘
                         └───────┬────────┘
                                 │
                         ┌───────┴────────┐
                         │                │
                         ▼                ▼
                    ┌──────────┐     ┌──────────┐
                    │ 40 REV   │     │ 8 FLAGS  │
                    │   LEDs   │     │   LEDs   │
                    └──────────┘     └──────────┘
```

Additional racing games use exactly the same architecture:

```text
Assetto Corsa Competizione
          ↓
      acc_rev.py
          ↓
          ├── RPM
          ├── MAXRPM
          └── SHIFT
          ↓
   Universal Arduino
```

```text
Assetto Corsa
          ↓
       ac_rev.py
          ↓
          ├── RPM
          ├── MAXRPM
          └── SHIFT
          ↓
   Universal Arduino
```

---

# 📁 Project Structure

```text
F1-REV-Light-System/
│
├── f1_rev.py
├── f122_rev.py
├── f125_rev.py
├── acc_rev.py
├── ac_rev.py
│
├── universal_arduino.ino
│
└── README.md
```

### Python adapters

| File          | Game                       |
| ------------- | -------------------------- |
| `f1_rev.py`   | F1 2020                    |
| `f122_rev.py` | F1 22                      |
| `f125_rev.py` | F1 25                      |
| `acc_rev.py`  | Assetto Corsa Competizione |
| `ac_rev.py`   | Assetto Corsa              |

---

# 🔄 How It Works

```text
                    RACING GAME
                         │
                         │ UDP / Telemetry
                         ▼
                ┌──────────────────┐
                │ Python Adapter   │
                └────────┬─────────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
             RPM       MAXRPM     SHIFT
              │          │          │
              └──────────┼──────────┘
                         │
                         │ USB Serial
                         ▼
                ┌──────────────────┐
                │ Universal Arduino│
                └────────┬─────────┘
                         │
                         ▼
                  48 × WS2812B LEDs
```

The Python programs handle **game-specific telemetry**.

The Arduino handles **LED rendering**.

This separation means adding another racing game does not require rewriting the Arduino firmware.

---

# 🔥 Dynamic REV System

The REV display uses:

```text
Current RPM
Maximum RPM
```

The Python adapter sends commands such as:

```text
RPM:8500
MAXRPM:15000
```

The Arduino calculates:

```text
RPM Percentage =
Current RPM / Maximum RPM
```

For example:

```text
8500 / 15000 = 56.7%
```

The 40 REV LEDs therefore display approximately:

```text
40 × 56.7% ≈ 23 LEDs
```

This allows the same REV display to work with different cars and RPM limits.

---

# 🎨 RPM Color Progression

The 40 REV LEDs use four color zones:

| RPM Range | Color     |
| --------- | --------- |
| 0–60%     | 🟢 Green  |
| 60–75%    | 🟡 Yellow |
| 75–90%    | 🟠 Orange |
| 90–100%   | 🔴 Red    |

Example:

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

The display illuminates **from both outside edges toward the center**.

---

# ⚡ Shift Point

When the game-specific Python adapter detects the appropriate shift point, it sends:

```text
SHIFT
```

The Arduino temporarily changes the REV section into a shift indicator.

```text
████████████████████████████████████████
████████████████████████████████████████
```

This gives a full-width visual warning to shift.

Supported games:

* F1 2020
* F1 22
* F1 25
* Assetto Corsa Competizione
* Assetto Corsa

The shift detection itself is handled by the individual Python adapter because each game exposes different telemetry.

---

# 🚦 Race Start / Lights Out

Some adapters provide race-start information.

### F1 22

* Start lights
* Lights Out
* RPM operation resumes after the start sequence

### F1 25

* Start lights
* Lights Out
* RPM operation resumes after the start sequence

The Arduino receives standardized start commands and handles the LED output.

---

# 🚩 Flag System

The outer LEDs are used for flags.

```text
LEFT FLAGS                         RIGHT FLAGS

0  1  2  3                         44 45 46 47
████████                           ████████
```

## Yellow

```text
YELLOW
```

The outer LEDs blink yellow.

## Red

```text
RED
```

The outer LEDs blink red.

## Green

```text
GREEN
```

The outer LEDs illuminate green temporarily.

## Blue

```text
BLUE
```

The Arduino supports the command, although individual game adapters may ignore blue flags.

## Clear

```text
NONE
```

Clears the active flag.

---

# 🛑 Telemetry Timeout

The Arduino includes a communication watchdog.

If no command is received for approximately **3 seconds**, the Arduino automatically turns all LEDs off.

```text
No telemetry
     ↓
3 seconds
     ↓
OFF
     ↓
All LEDs OFF
```

This prevents the LEDs from becoming stuck displaying an old RPM or flag state.

---

# 🎮 Game Support

## F1 2020

### Supported

* UDP telemetry
* Dynamic RPM
* Dynamic maximum RPM
* REV lights
* Green RPM range
* Yellow RPM range
* Orange RPM range
* Redline
* Outside-to-center animation
* Shift point detection
* Yellow flag
* Red flag
* Green flag
* Telemetry timeout

### Adapter

```text
f1_rev.py
```

---

# F1 22

### Supported

* UDP telemetry
* Dynamic RPM
* Dynamic maximum RPM
* REV lights
* Green RPM range
* Yellow RPM range
* Orange RPM range
* Redline
* Outside-to-center animation
* Shift point detection
* Yellow flag
* Red flag
* Green flag
* Lights Out
* Automatic telemetry timeout
* Universal Arduino

### Adapter

```text
f122_rev.py
```

### UDP Format

Use:

```text
2022
```

Do not use:

```text
2025
2026
```

---

# F1 25

### Supported

* UDP telemetry
* Dynamic RPM
* Dynamic maximum RPM
* REV lights
* Green RPM range
* Yellow RPM range
* Orange RPM range
* Redline
* Outside-to-center animation
* Shift point detection
* Flag system
* Lights Out
* Automatic telemetry timeout
* Universal Arduino

### Adapter

```text
f125_rev.py
```

### UDP Mode

Use:

```text
F1 25
```

Do not use the separate:

```text
F1 25: 2026 Season Pack
```

telemetry mode.

---

# Assetto Corsa Competizione

Assetto Corsa Competizione uses its own telemetry adapter.

### Supported

* RPM telemetry
* Dynamic RPM scaling
* Maximum RPM
* REV lights
* Green RPM range
* Yellow RPM range
* Orange RPM range
* Redline
* Outside-to-center animation
* Shift point indication
* Universal Arduino

### Adapter

```text
acc_rev.py
```

ACC does not require the F1 telemetry configuration.

The ACC adapter communicates with the game's telemetry system and converts the data into the universal Arduino command protocol.

---

# Assetto Corsa

Assetto Corsa also uses its own telemetry adapter.

### Supported

* RPM telemetry
* Dynamic RPM scaling
* Maximum RPM
* REV lights
* Green RPM range
* Yellow RPM range
* Orange RPM range
* Redline
* Outside-to-center animation
* Shift point indication
* Universal Arduino

### Adapter

```text
ac_rev.py
```

The Assetto Corsa adapter converts AC telemetry into the same universal Arduino commands used by the other supported games.

---

# 🔌 Universal Arduino

The Arduino firmware is game-independent.

It does not need to know whether the telemetry comes from:

```text
F1 2020
F1 22
F1 25
ACC
Assetto Corsa
```

It only receives standardized commands.

For example:

```text
RPM:8500
MAXRPM:15000
```

or:

```text
SHIFT
```

or:

```text
YELLOW
```

This keeps all game-specific logic inside Python.

---

# 📡 Universal Command Protocol

The Arduino understands:

| Command       | Function                  |
| ------------- | ------------------------- |
| `RPM:xxxx`    | Set current RPM           |
| `MAXRPM:xxxx` | Set maximum RPM           |
| `SHIFT`       | Activate shift indication |
| `YELLOW`      | Yellow flag               |
| `RED`         | Red flag                  |
| `BLUE`        | Blue flag                 |
| `GREEN`       | Green flag                |
| `NONE`        | Clear flag                |
| `OFF`         | Turn everything off       |
| `START:x`     | Display start lights      |
| `LIGHTSOUT`   | Clear start lights        |

Example:

```text
MAXRPM:15000
RPM:8500
```

Then:

```text
SHIFT
```

when the shift point is reached.

---

# 🛠️ Hardware

## Required

* Arduino Uno / Nano or compatible Arduino
* WS2812B / NeoPixel LED strip
* 48 LEDs
* USB cable
* PC
* Supported racing game

---

# 🔧 Arduino Configuration

Default:

```cpp
#define LED_PIN 6
#define NUM_LEDS 48
```

The LED strip data line should be connected to:

```text
Arduino D6
```

unless `LED_PIN` is changed.

Install the Arduino library:

```text
Adafruit NeoPixel
```

Then upload:

```text
universal_arduino.ino
```

---

# 🔌 Serial Configuration

Default Arduino serial connection:

```text
COM4
9600 baud
```

Python configuration:

```python
ARDUINO_PORT = "COM4"
ARDUINO_BAUD = 9600
```

If Windows assigns another COM port, change it accordingly.

Example:

```python
ARDUINO_PORT = "COM5"
```

### Important

Only one application should use the Arduino's COM port at a time.

Close:

* Arduino Serial Monitor
* Arduino Serial Plotter
* SimHub
* Other telemetry scripts
* Serial terminal programs

Otherwise Windows may show:

```text
PermissionError: [WinError 5] Access is denied
```

---

# 📦 Python Requirements

Install Python 3.

For the F1 adapters, install:

```bash
pip install pyserial
```

Individual adapters may have additional requirements depending on the telemetry interface they use.

---

# ▶️ Running the Project

## F1 2020

```bash
python f1_rev.py
```

## F1 22

```bash
python f122_rev.py
```

## F1 25

```bash
python f125_rev.py
```

## Assetto Corsa Competizione

```bash
python acc_rev.py
```

## Assetto Corsa

```bash
python ac_rev.py
```

Only run the adapter for the game currently being played.

---

# 🌐 F1 UDP Configuration

For the F1 games:

```text
UDP Telemetry = On
UDP Broadcast = Off
IP Address    = 127.0.0.1
UDP Port      = 20777
Send Rate     = 60 Hz
```

## F1 2020

```text
UDP Format = 2020
```

## F1 22

```text
UDP Format = 2022
```

## F1 25

```text
UDP Mode = F1 25
```

For F1 25, do not select the separate 2026 Season Pack telemetry mode when using `f125_rev.py`.

---

# 🧪 Troubleshooting

## No Telemetry

Check:

```text
Game running
      ↓
Telemetry enabled
      ↓
Correct telemetry format
      ↓
Correct UDP port
      ↓
Correct Python adapter
```

For F1:

```text
127.0.0.1:20777
```

Make sure the selected Python program matches the game.

---

## Telemetry Is Working but LEDs Are Off

Check:

1. Arduino is connected.
2. Correct COM port is configured.
3. Arduino baud rate is `9600`.
4. `universal_arduino.ino` is uploaded.
5. Adafruit NeoPixel library is installed.
6. LED data line is connected to the correct pin.
7. LED strip has sufficient power.
8. Arduino and LED power supply share a common ground.
9. No other application is using the COM port.

---

## REV Lights Do Not Change

Verify that the Python adapter is sending:

```text
RPM:xxxx
```

and:

```text
MAXRPM:xxxx
```

For example:

```text
RPM:9000
MAXRPM:15000
```

The Arduino uses these two values to calculate the REV position.

---

## Shift Lights Do Not Activate

The Python adapter must send:

```text
SHIFT
```

when the game's telemetry reaches the configured shift condition.

Shift detection is handled by the game-specific Python adapter.

---

## LEDs Turn Off During Driving

If all LEDs turn off after approximately 3 seconds, telemetry or serial commands are no longer reaching the Arduino.

Check:

```text
Python telemetry
       ↓
Python processing
       ↓
Serial connection
       ↓
Arduino
```

---

# 🏁 Project Status

| Feature           | F1 2020 | F1 22 | F1 25 | ACC |  AC |
| ----------------- | :-----: | :---: | :---: | :-: | :-: |
| UDP / Telemetry   |    ✅    |   ✅   |   ✅   |  ✅  |  ✅  |
| RPM REV Lights    |    ✅    |   ✅   |   ✅   |  ✅  |  ✅  |
| Dynamic RPM       |    ✅    |   ✅   |   ✅   |  ✅  |  ✅  |
| Dynamic MAX RPM   |    ✅    |   ✅   |   ✅   |  ✅  |  ✅  |
| Green RPM         |    ✅    |   ✅   |   ✅   |  ✅  |  ✅  |
| Yellow RPM        |    ✅    |   ✅   |   ✅   |  ✅  |  ✅  |
| Orange RPM        |    ✅    |   ✅   |   ✅   |  ✅  |  ✅  |
| Redline           |    ✅    |   ✅   |   ✅   |  ✅  |  ✅  |
| Outside → Center  |    ✅    |   ✅   |   ✅   |  ✅  |  ✅  |
| Shift Point       |    ✅    |   ✅   |   ✅   |  ✅  |  ✅  |
| Flag System       |    ✅    |   ✅   |   ✅   |  —  |  —  |
| Lights Out        |    —    |   ✅   |   ✅   |  —  |  —  |
| Telemetry Timeout |    ✅    |   ✅   |   ✅   |  ✅  |  ✅  |
| Universal Arduino |    ✅    |   ✅   |   ✅   |  ✅  |  ✅  |

---

# 🚀 Future Expansion

The universal architecture makes it possible to add more racing games without changing the Arduino firmware.

For example:

```text
iRacing
   ↓
iracing_rev.py
   ↓
RPM / MAXRPM / SHIFT
   ↓
Universal Arduino
```

or:

```text
Le Mans Ultimate
   ↓
lmu_rev.py
   ↓
RPM / MAXRPM / SHIFT
   ↓
Universal Arduino
```

A new adapter only needs to convert the game's telemetry into the existing command protocol.

---

# 🧩 Design Philosophy

The project is split into two layers:

### Game Layer

Python handles:

```text
Telemetry
RPM
Maximum RPM
Shift point
Flags
Race state
```

### Hardware Layer

Arduino handles:

```text
LED rendering
RPM visualization
Shift flashing
Flag lighting
Start lights
Timeout protection
```

This makes the system easier to maintain and expand.

---

# 📊 Universal Data Flow

```text
┌─────────────────────────────┐
│         Racing Game        │
└──────────────┬──────────────┘
               │
               │ Telemetry
               ▼
┌─────────────────────────────┐
│       Python Adapter        │
│                             │
│ RPM                         │
│ MAXRPM                      │
│ SHIFT                       │
│ FLAGS                       │
│ RACE STATE                  │
└──────────────┬──────────────┘
               │
               │ USB Serial
               ▼
┌─────────────────────────────┐
│     Universal Arduino       │
│                             │
│  RPM Renderer               │
│  Shift Indicator            │
│  Flag Renderer              │
│  Start Lights               │
│  Safety Watchdog            │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       48 × WS2812B          │
│                             │
│  4 │ 40 REV │ 4             │
│ FLAGS │ RPM │ FLAGS         │
└─────────────────────────────┘
```

---

# 📜 License

This is a personal/community DIY sim-racing project.

F1, F1 2020, F1 22, F1 25, Assetto Corsa, Assetto Corsa Competizione and related game assets are trademarks of their respective owners.

This project is **not affiliated with, endorsed by, or sponsored by EA, Codemasters, Formula 1, Kunos Simulazioni, or 505 Games**.

---

# ❤️ Credits

Built as a DIY sim-racing hardware project using:

* Arduino
* Adafruit NeoPixel
* WS2812B LEDs
* Python
* UDP telemetry
* USB serial communication

Designed to provide a single **universal REV, shift and flag light system** across multiple racing games.
