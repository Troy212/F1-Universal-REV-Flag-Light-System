import socket
import serial
import struct
import time
import sys


# =========================================================
# F1 2020 UNIVERSAL REV / FLAG / SHIFT SYSTEM
# =========================================================


# =========================================================
# SETTINGS
# =========================================================

UDP_IP = "127.0.0.1"
UDP_PORT = 20777

ARDUINO_PORT = "COM4"
ARDUINO_BAUD = 9600

TELEMETRY_TIMEOUT = 3.0


# =========================================================
# DEBUG
# =========================================================

DEBUG = True


# =========================================================
# F1 2020 PACKET SIZES
# =========================================================

PACKET_HEADER_SIZE = 24

PACKET_SESSION_SIZE = 251
PACKET_LAP_SIZE = 1190
PACKET_EVENT_SIZE = 35
PACKET_TELEMETRY_SIZE = 1307
PACKET_STATUS_SIZE = 1344


# =========================================================
# CAR DATA
# =========================================================

CAR_TELEMETRY_SIZE = 58
CAR_STATUS_SIZE = 60


# =========================================================
# F1 2020 CAR TELEMETRY OFFSETS
# =========================================================

# Inside CarTelemetryData:
#
# speed        0
# throttle     2
# steer        6
# brake        10
# clutch       14
# gear         15
# engine RPM   16
# DRS          18
# rev percent  19
#
# Engine RPM = +16

ENGINE_RPM_OFFSET = 16


# =========================================================
# F1 2020 CAR STATUS OFFSETS
# =========================================================

# Inside CarStatusData:
#
# traction control       0
# ABS                    1
# fuel mix               2
# brake bias             3
# pit limiter            4
# fuel in tank           5
# fuel capacity          9
# fuel remaining         13
# max RPM                17
# idle RPM               19
#
# FIA flag = +42

MAX_RPM_OFFSET = 17
FIA_FLAG_OFFSET = 42


# =========================================================
# STATE
# =========================================================

current_flag = "NONE"

last_zone_flag = 0

track_length = 0

zones = []

last_telemetry_time = time.monotonic()

leds_off = False

game_paused = False

last_rpm = 0

last_max_rpm = 0

last_shift_state = False

last_shift_gear = 0


# =========================================================
# CONNECT ARDUINO
# =========================================================

try:

    arduino = serial.Serial(
        ARDUINO_PORT,
        ARDUINO_BAUD,
        timeout=1
    )

except serial.SerialException as e:

    print()
    print("==============================================")
    print("ERROR: Could not connect to Arduino")
    print("==============================================")
    print(f"Port: {ARDUINO_PORT}")
    print(f"Error: {e}")
    print()
    print("Check:")
    print("1. Arduino is connected")
    print("2. Correct COM port is selected")
    print("3. Arduino Serial Monitor is closed")
    print("4. SimHub is not using the COM port")
    print()
    sys.exit(1)


time.sleep(2)

print("==============================================")
print(" F1 2020 UNIVERSAL REV SYSTEM")
print("==============================================")
print(f"Arduino : {ARDUINO_PORT}")
print(f"Baud    : {ARDUINO_BAUD}")
print(f"UDP     : {UDP_IP}:{UDP_PORT}")
print("==============================================")
print("Arduino connected")
print("Waiting for F1 2020 telemetry...")
print()


# =========================================================
# UDP SOCKET
# =========================================================

sock = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM
)

sock.setsockopt(
    socket.SOL_SOCKET,
    socket.SO_REUSEADDR,
    1
)

sock.settimeout(0.2)

try:

    sock.bind(
        (UDP_IP, UDP_PORT)
    )

except OSError as e:

    print()
    print("==============================================")
    print("ERROR: UDP PORT COULD NOT BE OPENED")
    print("==============================================")
    print(f"IP   : {UDP_IP}")
    print(f"Port : {UDP_PORT}")
    print(f"Error: {e}")
    print()
    print("Make sure another telemetry program")
    print("is not already using UDP port 20777.")
    print()

    arduino.close()

    sys.exit(1)


# =========================================================
# SEND COMMAND TO ARDUINO
# =========================================================

def send(command):

    try:

        arduino.write(
            (command + "\n").encode("ascii")
        )

        if DEBUG:

            print(
                f"\n>>> ARDUINO: {command}"
            )

    except serial.SerialException as e:

        print()
        print("Arduino serial connection lost:")
        print(e)

        raise


# =========================================================
# SEND MAX RPM
# =========================================================

def send_max_rpm(rpm):

    global last_max_rpm

    rpm = int(rpm)

    if rpm <= 0:

        return


    # Don't repeatedly send identical values

    if rpm == last_max_rpm:

        return


    last_max_rpm = rpm

    send(
        f"MAXRPM:{rpm}"
    )

    print(
        f"\nMAX RPM: {rpm}"
    )


# =========================================================
# TURN EVERYTHING OFF
# =========================================================

def turn_off():

    global current_flag
    global leds_off
    global last_shift_state

    current_flag = "NONE"

    last_shift_state = False

    send(
        "OFF"
    )

    leds_off = True


# =========================================================
# SET FLAG
# =========================================================

def set_flag(flag):

    global current_flag
    global leds_off

    if current_flag == flag:

        return


    current_flag = flag

    send(
        flag
    )

    leds_off = False

    print(
        f"\nFLAG: {flag}"
    )


# =========================================================
# CLEAR FLAG
# =========================================================

def clear_flag():

    global current_flag

    if current_flag != "NONE":

        current_flag = "NONE"

        send(
            "NONE"
        )

        print(
            "\nFLAG CLEARED"
        )


# =========================================================
# SHIFT COMMAND
# =========================================================

def set_shift(active):

    global last_shift_state

    active = bool(active)

    if active == last_shift_state:

        return


    last_shift_state = active


    if active:

        send(
            "SHIFT"
        )

        print(
            "\n>>> SHIFT POINT"
        )

    else:

        send(
            "SHIFT_OFF"
        )


# =========================================================
# RESET FLAG STATE
# =========================================================

def reset_flags():

    global current_flag
    global last_zone_flag

    current_flag = "NONE"

    last_zone_flag = 0


# =========================================================
# PROCESS SESSION PACKET
# =========================================================

def process_session(data):

    global track_length
    global zones
    global game_paused

    if len(data) != PACKET_SESSION_SIZE:

        return


    # Track length

    track_length = struct.unpack_from(
        "<H",
        data,
        28
    )[0]


    # -----------------------------------------------------
    # NOTE:
    #
    # Your original pause offset was retained here because
    # this is part of your existing F1 2020 implementation.
    # -----------------------------------------------------

    paused = data[38]


    if paused == 1:

        if not game_paused:

            game_paused = True

            turn_off()

            print(
                "\nGAME PAUSED - LEDs OFF"
            )

    else:

        if game_paused:

            game_paused = False

            print(
                "\nGAME RESUMED"
            )


    # =====================================================
    # MARSHAL ZONES
    # =====================================================

    num_zones = data[41]

    if num_zones > 21:

        num_zones = 21


    zones = []


    for i in range(num_zones):

        zone_offset = (
            42 +
            i * 5
        )


        if zone_offset + 5 > len(data):

            break


        zone_start = struct.unpack_from(
            "<f",
            data,
            zone_offset
        )[0]


        zone_flag = struct.unpack_from(
            "<b",
            data,
            zone_offset + 4
        )[0]


        zones.append(
            (
                zone_start,
                zone_flag
            )
        )


# =========================================================
# PROCESS TELEMETRY PACKET
# =========================================================

def process_telemetry(data, player_car):

    global last_rpm

    if len(data) != PACKET_TELEMETRY_SIZE:

        return


    if player_car >= 22:

        return


    car_offset = (
        PACKET_HEADER_SIZE +
        player_car * CAR_TELEMETRY_SIZE
    )


    rpm_offset = (
        car_offset +
        ENGINE_RPM_OFFSET
    )


    if rpm_offset + 2 > len(data):

        return


    rpm = struct.unpack_from(
        "<H",
        data,
        rpm_offset
    )[0]


    last_rpm = rpm


    if not game_paused:

        send(
            f"RPM:{rpm}"
        )


    # =====================================================
    # SUGGESTED GEAR
    # =====================================================
    #
    # F1 2020 stores suggestedGear at the end of the
    # telemetry packet.
    #
    # Offset:
    #
    # 24 + (22 × 58)
    # + 4
    # + 1
    # + 1
    #
    # m_mfdPanelIndex
    # m_mfdPanelIndexSecondaryPlayer
    # m_suggestedGear
    #
    # Packet ends with:
    #
    # uint8  m_mfdPanelIndex
    # uint8  m_mfdPanelIndexSecondaryPlayer
    # int8   m_suggestedGear
    #

    suggested_gear_offset = (
        PACKET_HEADER_SIZE +
        (22 * CAR_TELEMETRY_SIZE) +
        2
    )


    if (
        suggested_gear_offset >=
        len(data)
    ):

        return


    suggested_gear = struct.unpack_from(
        "<b",
        data,
        suggested_gear_offset
    )[0]


    # =====================================================
    # SHIFT LOGIC
    # =====================================================
    #
    # suggestedGear > 0 means the game recommends
    # changing up.
    #

    if not game_paused:

        if suggested_gear > 0:

            set_shift(True)

        else:

            set_shift(False)


    # =====================================================
    # DEBUG
    # =====================================================

    if DEBUG:

        max_rpm_display = (
            last_max_rpm
            if last_max_rpm > 0
            else 0
        )


        if max_rpm_display > 0:

            rpm_percent = (
                rpm /
                max_rpm_display
            ) * 100.0

            rpm_percent = min(
                rpm_percent,
                100.0
            )

        else:

            rpm_percent = 0


        print(
            f"\rRPM: {rpm:5} | "
            f"MAX: {max_rpm_display:5} | "
            f"LOAD: {rpm_percent:6.2f}% | "
            f"GEAR: {suggested_gear:2} | "
            f"FLAG: {current_flag}",
            end="",
            flush=True
        )


# =========================================================
# PROCESS CAR STATUS
# =========================================================

def process_status(data, player_car):

    if len(data) != PACKET_STATUS_SIZE:

        return


    if player_car >= 22:

        return


    car_offset = (
        PACKET_HEADER_SIZE +
        player_car * CAR_STATUS_SIZE
    )


    # =====================================================
    # ACTUAL MAX RPM
    # =====================================================

    max_rpm_offset = (
        car_offset +
        MAX_RPM_OFFSET
    )


    if max_rpm_offset + 2 <= len(data):

        max_rpm = struct.unpack_from(
            "<H",
            data,
            max_rpm_offset
        )[0]


        if max_rpm > 0:

            send_max_rpm(
                max_rpm
            )


    # =====================================================
    # FIA FLAG
    # =====================================================

    fia_offset = (
        car_offset +
        FIA_FLAG_OFFSET
    )


    if fia_offset >= len(data):

        return


    fia_flag = struct.unpack_from(
        "<b",
        data,
        fia_offset
    )[0]


    if game_paused:

        return


    # =====================================================
    # FIA FLAG VALUES
    # =====================================================

    if fia_flag == 4:

        set_flag(
            "RED"
        )


    elif fia_flag == 3:

        set_flag(
            "YELLOW"
        )


    elif fia_flag == 1:

        set_flag(
            "GREEN"
        )


    elif fia_flag == 0:

        if current_flag == "GREEN":

            clear_flag()


# =========================================================
# PROCESS LAP DATA
# =========================================================

def process_lap(data, player_car):

    global last_zone_flag

    if len(data) != PACKET_LAP_SIZE:

        return


    if player_car >= 22:

        return


    if track_length <= 0:

        return


    lap_offset = (
        PACKET_HEADER_SIZE +
        player_car * 53
    )


    if lap_offset + 53 > len(data):

        return


    # Current lap distance around track

    lap_distance = struct.unpack_from(
        "<f",
        data,
        lap_offset + 20
    )[0]


    lap_fraction = (
        lap_distance /
        track_length
    )


    lap_fraction %= 1.0


    # =====================================================
    # FIND ACTIVE MARSHAL ZONE
    # =====================================================

    active_flag = 0


    if zones:

        sorted_zones = sorted(
            zones,
            key=lambda x: x[0]
        )


        for i in range(
            len(sorted_zones)
        ):

            start = sorted_zones[i][0]


            if i + 1 < len(sorted_zones):

                end = (
                    sorted_zones[i + 1][0]
                )

            else:

                end = 1.0


            if (
                lap_fraction >= start
                and
                lap_fraction < end
            ):

                active_flag = (
                    sorted_zones[i][1]
                )

                break


    # =====================================================
    # FLAG LOGIC
    # =====================================================

    if game_paused:

        return


    # -----------------------------------------------------
    # YELLOW
    # -----------------------------------------------------

    if active_flag == 3:

        if last_zone_flag != 3:

            last_zone_flag = 3

            set_flag(
                "YELLOW"
            )


    # -----------------------------------------------------
    # RED
    # -----------------------------------------------------

    elif active_flag == 4:

        if last_zone_flag != 4:

            last_zone_flag = 4

            set_flag(
                "RED"
            )


    # -----------------------------------------------------
    # BLUE
    # -----------------------------------------------------

    elif active_flag == 2:

        if last_zone_flag != 2:

            last_zone_flag = 2

            set_flag(
                "BLUE"
            )


    # -----------------------------------------------------
    # GREEN
    # -----------------------------------------------------

    elif active_flag == 1:

        if last_zone_flag != 1:

            last_zone_flag = 1

            set_flag(
                "GREEN"
            )


    # -----------------------------------------------------
    # NO FLAG
    # -----------------------------------------------------

    else:

        if last_zone_flag != 0:

            last_zone_flag = 0

            clear_flag()


# =========================================================
# PROCESS EVENT PACKET
# =========================================================

def process_event(data):

    if len(data) != PACKET_EVENT_SIZE:

        return


    event_code = data[
        24:28
    ]


    # =====================================================
    # START LIGHTS
    # =====================================================

    if event_code == b"STLG":

        number_of_lights = data[28]


        if number_of_lights > 5:

            number_of_lights = 5


        if number_of_lights > 0:

            print(
                f"\nSTART LIGHTS: "
                f"{number_of_lights}"
            )


            send(
                f"START:{number_of_lights}"
            )


    # =====================================================
    # LIGHTS OUT
    # =====================================================

    elif event_code == b"LGOT":

        print(
            "\nLIGHTS OUT!"
        )


        send(
            "LIGHTSOUT"
        )


# =========================================================
# MAIN LOOP
# =========================================================

try:

    while True:

        try:

            data, address = sock.recvfrom(
                2048
            )


        except socket.timeout:

            # =================================================
            # TELEMETRY TIMEOUT
            # =================================================

            if (
                time.monotonic()
                -
                last_telemetry_time
                >= TELEMETRY_TIMEOUT
            ):

                if not leds_off:

                    turn_off()

                    print(
                        "\n"
                        "No F1 telemetry for "
                        "3 seconds - LEDs OFF"
                    )


            continue


        # =====================================================
        # TELEMETRY RECEIVED
        # =====================================================

        last_telemetry_time = (
            time.monotonic()
        )


        leds_off = False


        # =====================================================
        # MINIMUM HEADER SIZE
        # =====================================================

        if len(data) < PACKET_HEADER_SIZE:

            continue


        # =====================================================
        # CHECK TELEMETRY FORMAT
        # =====================================================

        packet_format = struct.unpack_from(
            "<H",
            data,
            0
        )[0]


        if packet_format != 2020:

            if DEBUG:

                print(
                    f"\nWARNING: "
                    f"Received telemetry format "
                    f"{packet_format}, "
                    f"expected 2020"
                )

            continue


        # =====================================================
        # PACKET HEADER
        # =====================================================

        packet_id = data[5]

        player_car = data[22]


        if player_car >= 22:

            continue


        # =====================================================
        # PACKET 1
        # SESSION
        # =====================================================

        if packet_id == 1:

            process_session(
                data
            )


        # =====================================================
        # PACKET 2
        # LAP DATA
        # =====================================================

        elif packet_id == 2:

            process_lap(
                data,
                player_car
            )


        # =====================================================
        # PACKET 3
        # EVENT
        # =====================================================

        elif packet_id == 3:

            process_event(
                data
            )


        # =====================================================
        # PACKET 6
        # CAR TELEMETRY
        # =====================================================

        elif packet_id == 6:

            process_telemetry(
                data,
                player_car
            )


        # =====================================================
        # PACKET 7
        # CAR STATUS
        # =====================================================

        elif packet_id == 7:

            process_status(
                data,
                player_car
            )


# =========================================================
# CTRL + C
# =========================================================

except KeyboardInterrupt:

    print(
        "\n\nStopping F1 2020 telemetry..."
    )


# =========================================================
# CLEANUP
# =========================================================

finally:

    try:

        arduino.write(
            b"OFF\n"
        )

        time.sleep(0.1)

    except:

        pass


    try:

        arduino.close()

    except:

        pass


    try:

        sock.close()

    except:

        pass


    print(
        "Arduino and UDP connection closed."
    )