#include <Adafruit_NeoPixel.h>

#define LED_PIN 6
#define NUM_LEDS 48

// =====================================================
// LED LAYOUT
// =====================================================

// 0 - 3   = LEFT FLAG / START LIGHTS
// 4 - 43  = RPM
// 44 - 47 = RIGHT FLAG / START LIGHTS

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

      showRPM(rpm);
    }


    // =================================================
    // YELLOW FLAG
    // =================================================

    else if (command == "YELLOW") {

      // Don't overwrite race start lights

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

      clearAll();

      strip.show();
    }


    // =================================================
    // RACE START LIGHTS
    //
    // START:1
    // START:2
    // START:3
    // START:4
    // START:5
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

      clearAll();

      strip.show();
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
      }
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

    clearAll();

    strip.show();

    lastCommandTime = millis();
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
  // BLINK YELLOW / RED / BLUE
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

void showRPM(int rpm) {

  // Don't let RPM overwrite start lights

  if (raceStartActive) {

    return;
  }


  rpm = constrain(
    rpm,
    0,
    maxRPM
  );


  // ===================================================
  // 40 RPM LEDs
  //
  // OUTSIDE → CENTER
  //
  // LEFT       RIGHT
  //
  // 4   +   43
  // 5   +   42
  // 6   +   41
  // ...
  // 23  +   24
  // ===================================================

  const int totalPairs = 20;


  int pairs = map(
    rpm,
    0,
    maxRPM,
    0,
    totalPairs
  );


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
  // OUTSIDE → CENTER
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
    // =================================================

    else if (pair < 18) {

      color = strip.Color(
        255,
        70,
        0
      );
    }


    // =================================================
    // REDLINE
    // =================================================

    else {

      color = strip.Color(
        255,
        0,
        0
      );
    }


    // =================================================
    // BOTH SIDES
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
// RACE START LIGHTS
// =====================================================
//
// Uses ONLY the 8 flag LEDs.
//
// LEFT:
// 0 1 2 3
//
// RIGHT:
// 44 45 46 47
//
// START:1 = 2 LEDs
// START:2 = 4 LEDs
// START:3 = 6 LEDs
// START:4 = 8 LEDs
// START:5 = 8 LEDs
//
// LIGHTSOUT = all 8 OFF
// =====================================================

void startRaceLights(int lights) {

  lights = constrain(
    lights,
    0,
    5
  );


  raceStartActive = true;

  startLights = lights;


  // Clear ONLY flag LEDs

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
  //
  // F1's fifth stage keeps all 8 illuminated.
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

  // Race start has priority

  if (raceStartActive) {

    return;
  }


  // Clear only the 8 flag LEDs

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
  // LEFT 4
  // ===================================================

  for (int i = 0; i < 4; i++) {

    strip.setPixelColor(
      FLAG_LEFT_START + i,
      color
    );
  }


  // ===================================================
  // RIGHT 4
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
// CLEAR FLAG LEDs ONLY
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
// CLEAR ALL 48 LEDs
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