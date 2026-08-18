
import time
import serial

from pyaccsharedmemory import accSharedMemory


# =========================================================
# ASSETTO CORSA COMPETIZIONE
# RPM / REV LIGHT SYSTEM
# =========================================================
#
# ACC -> Python -> Arduino -> WS2812B
#
# Arduino commands used:
#
#   RPM:xxxx
#   MAXRPM:xxxx
#   OFF
#
# No flags.
# No UDP.
# No event processing.
# No manual memory offsets.
#
# Uses PyAccSharedMemory to read:
#
#   Physics.rpm
#   Statics.max_rpm
# =========================================================


# =========================================================
# SETTINGS
# =========================================================

ARDUINO_PORT = "COM4"
ARDUINO_BAUD = 9600

TELEMETRY_TIMEOUT = 3.0

READ_INTERVAL = 0.01


# =========================================================
# CONNECT TO ARDUINO
# =========================================================

try:

    arduino = serial.Serial(
        ARDUINO_PORT,
        ARDUINO_BAUD,
        timeout=1
    )

except Exception as e:

    print("Could not connect to Arduino.")
    print(e)

    input("\nPress Enter to exit...")

    raise SystemExit


time.sleep(2)

print(
    f"Arduino connected on {ARDUINO_PORT}"
)


# =========================================================
# CONNECT TO ACC SHARED MEMORY
# =========================================================

try:

    acc = accSharedMemory()

except Exception as e:

    print()
    print("Could not initialize ACC shared memory.")
    print(e)
    print()
    print("Make sure Assetto Corsa Competizione is running.")
    print()

    try:
        arduino.close()
    except:
        pass

    input("Press Enter to exit...")

    raise SystemExit


# =========================================================
# STATE
# =========================================================

last_rpm = -1

last_max_rpm = -1

last_telemetry_time = time.monotonic()

leds_off = False

last_connection_state = None


# =========================================================
# SEND COMMAND TO ARDUINO
# =========================================================

def send(command):

    try:

        arduino.write(
            (command + "\n").encode()
        )

    except Exception as e:

        print(
            f"\nArduino error: {e}"
        )


# =========================================================
# TURN OFF LEDs
# =========================================================

def turn_off():

    global last_rpm
    global leds_off

    last_rpm = -1

    send("OFF")

    leds_off = True


# =========================================================
# MAIN LOOP
# =========================================================

print()
print("==============================")
print("       ACC REV SYSTEM")
print("==============================")
print()
print("Shared Memory : ENABLED")
print("RPM           : ENABLED")
print("Dynamic MaxRPM: ENABLED")
print("Flags         : DISABLED")
print()
print("Waiting for ACC telemetry...")
print("Start a session and drive.")
print()


while True:

    try:

        # =================================================
        # READ ACC SHARED MEMORY
        # =================================================

        sm = acc.read_shared_memory()


        # =================================================
        # NO TELEMETRY
        # =================================================

        if sm is None:

            if (
                time.monotonic()
                - last_telemetry_time
                >= TELEMETRY_TIMEOUT
            ):

                if not leds_off:

                    turn_off()

                    print(
                        "\nNo ACC telemetry for "
                        "3 seconds - LEDs OFF"
                    )

            time.sleep(
                READ_INTERVAL
            )

            continue


        # =================================================
        # TELEMETRY RECEIVED
        # =================================================

        last_telemetry_time = time.monotonic()

        leds_off = False


        # =================================================
        # READ RPM
        # =================================================

        rpm = int(
            sm.Physics.rpm
        )


        # =================================================
        # READ MAX RPM
        # =================================================

        max_rpm = int(
            sm.Static.max_rpm
        )


        # =================================================
        # SEND MAX RPM
        # =================================================

        if (
            max_rpm > 0
            and
            max_rpm != last_max_rpm
        ):

            send(
                f"MAXRPM:{max_rpm}"
            )

            last_max_rpm = max_rpm

            print(
                f"\nMAX RPM: {max_rpm}"
            )


        # =================================================
        # SEND RPM
        # =================================================

        if rpm != last_rpm:

            send(
                f"RPM:{rpm}"
            )

            last_rpm = rpm


            # ---------------------------------------------
            # STATUS DISPLAY
            # ---------------------------------------------

            print(
                f"\rRPM: {rpm:5} | "
                f"MAX RPM: {max_rpm:5}",
                end="",
                flush=True
            )


        # =================================================
        # LOOP RATE
        # =================================================

        time.sleep(
            READ_INTERVAL
        )


    # =====================================================
    # CTRL + C
    # =====================================================

    except KeyboardInterrupt:

        print(
            "\n\nStopping..."
        )

        turn_off()

        time.sleep(
            0.2
        )

        break


    # =====================================================
    # TELEMETRY ERROR
    # =====================================================

    except Exception as e:

        print(
            f"\nTelemetry error: {e}"
        )

        time.sleep(
            0.05
        )


# =========================================================
# CLEANUP
# =========================================================

try:

    acc.close()

except:

    pass


try:

    arduino.close()

except:

    pass


print("ACC REV system stopped.")

