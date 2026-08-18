#include <Adafruit_NeoPixel.h>

#define LED_PIN 6
#define NUM_LEDS 48

// =====================================================
// LED LAYOUT
// =====================================================
//
// 0 - 3   = LEFT FLAG LEDs
// 4 - 43  = 40 RPM LEDs
// 44 - 47 = RIGHT FLAG LEDs
//

#define FLAG_LEFT_START  0
#define RPM_START        4
#define RPM_END          43
#define FLAG_RIGHT_START 44

Adafruit_NeoPixel strip(
  NUM_LEDS,
  LED_PIN,
  NEO_GRB + NEO_KHZ800
);


// =====================================================
// RPM
// =====================================================

int maxRPM = 12000;
int currentRPM = 0;


// =====================================================
// SHIFT LIGHT
// =====================================================

bool shiftActive = false;
bool shiftBlinkState = false;

unsigned long lastShiftBlink = 0;

const unsigned long SHIFT_BLINK_INTERVAL = 100;


// =====================================================
// FLAG STATE
// =====================================================

enum FlagType {
  FLAG_NONE,
  FLAG_YELLOW,
  FLAG_RED,
  FLAG_BLUE,
  FLAG_GREEN
};

FlagType currentFlag = FLAG_NONE;


// =====================================================
// TIMERS
// =====================================================

unsigned long lastBlink = 0;
unsigned long greenStart = 0;

bool blinkState = true;

const unsigned long BLINK_INTERVAL = 300;
const unsigned long GREEN_DURATION = 3000;


// =====================================================
// COMMUNICATION WATCHDOG
// =====================================================

unsigned long lastCommandTime = 0;

const unsigned long CONNECTION_TIMEOUT = 3000;


// =====================================================
// RACE START
// =====================================================

bool raceStartActive = false;

int startLights = 0;


// =====================================================
// SETUP
// =====================================================

void setup() {

  strip.begin();

  strip.setBrightness(80);

  strip.show();

  Serial.begin(9600);

  lastCommandTime = millis();
}


// =====================================================
// MAIN LOOP
// =====================================================

void loop() {

  // ===================================================
  // SERIAL COMMANDS
  // ===================================================

  if (Serial.available()) {

    String command =
      Serial.readStringUntil('\n');

    command.trim();

    lastCommandTime = millis();


    // =================================================
    // RPM
    // =================================================

    if (command.startsWith("RPM:")) {

      int rpm =
        command.substring(4).toInt();

      currentRPM = rpm;

      // RPM command automatically exits shift mode
      shiftActive = false;

      showRPM(rpm);
    }


    // =================================================
    // MAX RPM
    // =================================================

    else if (command.startsWith("MAXRPM:")) {

      int detectedRPM =
        command.substring(7).toInt();

      if (detectedRPM > 0) {

        maxRPM = detectedRPM;

        Serial.print("MAX RPM: ");
        Serial.println(maxRPM);

        if (!raceStartActive && !shiftActive) {

          showRPM(currentRPM);
        }
      }
    }


    // =================================================
    // SHIFT
    // =================================================

    else if (command == "SHIFT") {

      if (!raceStartActive) {

        shiftActive = true;

        shiftBlinkState = true;

        lastShiftBlink = millis();

        showShiftLights();
      }
    }


    // =================================================
    // SHIFT OFF
    // =================================================

    else if (command == "SHIFT_OFF") {

      shiftActive = false;

      shiftBlinkState = false;

      if (!raceStartActive) {

        showRPM(currentRPM);
      }
    }


    // =================================================
    // YELLOW FLAG
    // =================================================

    else if (command == "YELLOW") {

      if (!raceStartActive) {

        currentFlag = FLAG_YELLOW;

        blinkState = true;

        lastBlink = millis();

        showFlag();
      }
    }


    // =================================================
    // RED FLAG
    // =================================================

    else if (command == "RED") {

      if (!raceStartActive) {

        currentFlag = FLAG_RED;

        blinkState = true;

        lastBlink = millis();

        showFlag();
      }
    }


    // =================================================
    // BLUE FLAG
    // =================================================

    else if (command == "BLUE") {

      if (!raceStartActive) {

        currentFlag = FLAG_BLUE;

        blinkState = true;

        lastBlink = millis();

        showFlag();
      }
    }


    // =================================================
    // GREEN FLAG
    // =================================================

    else if (command == "GREEN") {

      if (!raceStartActive) {

        currentFlag = FLAG_GREEN;

        greenStart = millis();

        showFlag();
      }
    }


    // =================================================
    // NO FLAG
    // =================================================

    else if (command == "NONE") {

      currentFlag = FLAG_NONE;

      clearFlags();

      strip.show();
    }


    // =================================================
    // ALL OFF
    // =================================================

    else if (command == "OFF") {

      currentFlag = FLAG_NONE;

      raceStartActive = false;

      startLights = 0;

      currentRPM = 0;

      shiftActive = false;

      clearAll();

      strip.show();
    }


    // =================================================
    // RACE START LIGHTS
    // =================================================

    else if (command.startsWith("START:")) {

      int lights =
        command.substring(6).toInt();

      startRaceLights(lights);
    }


    // =================================================
    // LIGHTS OUT
    // =================================================

    else if (command == "LIGHTSOUT") {

      raceStartActive = false;

      startLights = 0;

      shiftActive = false;

      clearAll();

      strip.show();
    }
  }


  // ===================================================
  // COMMUNICATION TIMEOUT
  // ===================================================

  if (
    millis() - lastCommandTime >=
    CONNECTION_TIMEOUT
  ) {

    currentFlag = FLAG_NONE;

    raceStartActive = false;

    startLights = 0;

    currentRPM = 0;

    shiftActive = false;

    clearAll();

    strip.show();

    lastCommandTime = millis();
  }


  // ===================================================
  // SHIFT LIGHT BLINK
  // ===================================================

  if (shiftActive && !raceStartActive) {

    if (
      millis() - lastShiftBlink >=
      SHIFT_BLINK_INTERVAL
    ) {

      lastShiftBlink = millis();

      shiftBlinkState = !shiftBlinkState;

      showShiftLights();
    }
  }


  // ===================================================
  // GREEN FLAG TIMER
  // ===================================================

  if (currentFlag == FLAG_GREEN) {

    if (
      millis() - greenStart >=
      GREEN_DURATION
    ) {

      currentFlag = FLAG_NONE;

      clearFlags();

      strip.show();
    }
  }


  // ===================================================
  // BLINK FLAGS
  // ===================================================

  if (
    currentFlag == FLAG_YELLOW ||
    currentFlag == FLAG_RED ||
    currentFlag == FLAG_BLUE
  ) {

    if (
      millis() - lastBlink >=
      BLINK_INTERVAL
    ) {

      lastBlink = millis();

      blinkState = !blinkState;

      showFlag();
    }
  }
}


// =====================================================
// RPM LIGHTS
// =====================================================
//
// 40 LEDs = 20 pairs.
//
// RPM progression:
//
// 0%  → 60%  = GREEN
// 60% → 80%  = YELLOW
// 80% → 90%  = ORANGE
// 90% → 100% = RED
//
// The colors are distributed across ALL 20 pairs.
//

void showRPM(int rpm) {

  // Don't overwrite race start lights

  if (raceStartActive) {

    return;
  }


  // Don't overwrite shift lights

  if (shiftActive) {

    return;
  }


  // Safety

  if (maxRPM <= 0) {

    maxRPM = 12000;
  }


  currentRPM = constrain(
    rpm,
    0,
    maxRPM
  );


  // ===================================================
  // RPM PERCENTAGE
  // ===================================================

  float rpmPercent =
    (float)currentRPM /
    (float)maxRPM;

  rpmPercent = constrain(
    rpmPercent,
    0.0,
    1.0
  );


  // ===================================================
  // 20 PAIRS
  // ===================================================

  const int totalPairs = 20;

  int pairs = (int)(
    rpmPercent *
    totalPairs
  );

  pairs = constrain(
    pairs,
    0,
    totalPairs
  );


  // ===================================================
  // CLEAR RPM LEDs
  // ===================================================

  for (
    int i = RPM_START;
    i <= RPM_END;
    i++
  ) {

    strip.setPixelColor(
      i,
      0
    );
  }


  // ===================================================
  // LIGHT PAIRS
  // ===================================================

  for (
    int pair = 0;
    pair < pairs;
    pair++
  ) {

    int leftLED =
      RPM_START + pair;

    int rightLED =
      RPM_END - pair;


    uint32_t color;


    // =================================================
    // GREEN
    //
    // PAIRS 0 - 11
    // 12 PAIRS
    // 60%
    // =================================================

    if (pair < 12) {

      color = strip.Color(
        0,
        255,
        0
      );
    }


    // =================================================
    // YELLOW
    //
    // PAIRS 12 - 15
    // 4 PAIRS
    // 20%
    // =================================================

    else if (pair < 16) {

      color = strip.Color(
        255,
        180,
        0
      );
    }


    // =================================================
    // ORANGE
    //
    // PAIRS 16 - 17
    // 2 PAIRS
    // 10%
    // =================================================

    else if (pair < 18) {

      color = strip.Color(
        255,
        70,
        0
      );
    }


    // =================================================
    // RED
    //
    // PAIRS 18 - 19
    // 2 PAIRS
    // 10%
    // =================================================

    else {

      color = strip.Color(
        255,
        0,
        0
      );
    }


    // =================================================
    // LEFT + RIGHT
    // =================================================

    strip.setPixelColor(
      leftLED,
      color
    );

    strip.setPixelColor(
      rightLED,
      color
    );
  }


  strip.show();
}


// =====================================================
// SHIFT LIGHTS
// =====================================================
//
// ALL 40 RPM LEDs blink together.
//
// ON  = all red
// OFF = all off
//
// This is triggered by:
// SHIFT
//
// And cancelled by:
// RPM:xxxx
// SHIFT_OFF
//

void showShiftLights() {

  if (raceStartActive) {

    return;
  }


  // ===================================================
  // CLEAR RPM SECTION
  // ===================================================

  for (
    int i = RPM_START;
    i <= RPM_END;
    i++
  ) {

    strip.setPixelColor(
      i,
      0
    );
  }


  // ===================================================
  // SHIFT ON
  // ===================================================

  if (shiftBlinkState) {

    for (
      int i = RPM_START;
      i <= RPM_END;
      i++
    ) {

      strip.setPixelColor(
        i,
        strip.Color(
          255,
          0,
          0
        )
      );
    }
  }


  strip.show();
}


// =====================================================
// RACE START LIGHTS
// =====================================================

void startRaceLights(int lights) {

  lights = constrain(
    lights,
    0,
    5
  );

  raceStartActive = true;

  startLights = lights;

  shiftActive = false;

  clearFlags();


  // ===================================================
  // START 1
  // ===================================================

  if (lights >= 1) {

    strip.setPixelColor(
      FLAG_LEFT_START + 0,
      strip.Color(255, 0, 0)
    );

    strip.setPixelColor(
      FLAG_RIGHT_START + 0,
      strip.Color(255, 0, 0)
    );
  }


  // ===================================================
  // START 2
  // ===================================================

  if (lights >= 2) {

    strip.setPixelColor(
      FLAG_LEFT_START + 1,
      strip.Color(255, 0, 0)
    );

    strip.setPixelColor(
      FLAG_RIGHT_START + 1,
      strip.Color(255, 0, 0)
    );
  }


  // ===================================================
  // START 3
  // ===================================================

  if (lights >= 3) {

    strip.setPixelColor(
      FLAG_LEFT_START + 2,
      strip.Color(255, 0, 0)
    );

    strip.setPixelColor(
      FLAG_RIGHT_START + 2,
      strip.Color(255, 0, 0)
    );
  }


  // ===================================================
  // START 4
  // ===================================================

  if (lights >= 4) {

    strip.setPixelColor(
      FLAG_LEFT_START + 3,
      strip.Color(255, 0, 0)
    );

    strip.setPixelColor(
      FLAG_RIGHT_START + 3,
      strip.Color(255, 0, 0)
    );
  }


  // ===================================================
  // START 5
  // ===================================================

  if (lights >= 5) {

    for (int i = 0; i < 4; i++) {

      strip.setPixelColor(
        FLAG_LEFT_START + i,
        strip.Color(255, 0, 0)
      );

      strip.setPixelColor(
        FLAG_RIGHT_START + i,
        strip.Color(255, 0, 0)
      );
    }
  }


  strip.show();
}


// =====================================================
// FLAG DISPLAY
// =====================================================

void showFlag() {

  if (raceStartActive) {

    return;
  }

  clearFlags();


  // ===================================================
  // BLINK OFF
  // ===================================================

  if (
    !blinkState &&
    (
      currentFlag == FLAG_YELLOW ||
      currentFlag == FLAG_RED ||
      currentFlag == FLAG_BLUE
    )
  ) {

    strip.show();

    return;
  }


  uint32_t color;


  // ===================================================
  // YELLOW
  // ===================================================

  if (currentFlag == FLAG_YELLOW) {

    color = strip.Color(
      255,
      180,
      0
    );
  }


  // ===================================================
  // RED
  // ===================================================

  else if (currentFlag == FLAG_RED) {

    color = strip.Color(
      255,
      0,
      0
    );
  }


  // ===================================================
  // BLUE
  // ===================================================

  else if (currentFlag == FLAG_BLUE) {

    color = strip.Color(
      0,
      0,
      255
    );
  }


  // ===================================================
  // GREEN
  // ===================================================

  else if (currentFlag == FLAG_GREEN) {

    color = strip.Color(
      0,
      255,
      0
    );
  }


  else {

    return;
  }


  // ===================================================
  // LEFT FLAGS
  // ===================================================

  for (int i = 0; i < 4; i++) {

    strip.setPixelColor(
      FLAG_LEFT_START + i,
      color
    );
  }


  // ===================================================
  // RIGHT FLAGS
  // ===================================================

  for (int i = 0; i < 4; i++) {

    strip.setPixelColor(
      FLAG_RIGHT_START + i,
      color
    );
  }


  strip.show();
}


// =====================================================
// CLEAR FLAGS
// =====================================================

void clearFlags() {

  for (int i = 0; i < 4; i++) {

    strip.setPixelColor(
      FLAG_LEFT_START + i,
      0
    );

    strip.setPixelColor(
      FLAG_RIGHT_START + i,
      0
    );
  }
}


// =====================================================
// CLEAR ALL
// =====================================================

void clearAll() {

  for (
    int i = 0;
    i < NUM_LEDS;
    i++
  ) {

    strip.setPixelColor(
      i,
      0
    );
  }
}