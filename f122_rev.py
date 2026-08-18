import socket
import serial
import struct
import time


# =========================================================
# F1 22 REV + FLAG SYSTEM
# =========================================================

UDP_IP = "127.0.0.1"
UDP_PORT = 20777

ARDUINO_PORT = "COM4"
ARDUINO_BAUD = 9600

TELEMETRY_TIMEOUT = 3.0

# Added: Arduino heartbeat
HEARTBEAT_INTERVAL = 1.0


# =========================================================
# F1 22 PACKET CONSTANTS
# =========================================================

F1_22_FORMAT = 2022

PACKET_SESSION = 1
PACKET_LAP_DATA = 2
PACKET_EVENT = 3
PACKET_CAR_TELEMETRY = 6
PACKET_CAR_STATUS = 7

HEADER_SIZE = 24

CAR_TELEMETRY_SIZE = 60
CAR_STATUS_SIZE = 47
LAP_DATA_SIZE = 43


# =========================================================
# F1 22 DATA OFFSETS
# =========================================================

PLAYER_CAR_OFFSET = 22

ENGINE_RPM_OFFSET = 16
REV_LIGHT_PERCENT_OFFSET = 19

FIA_FLAG_OFFSET = 6

NETWORK_PAUSED_OFFSET = 23

LAP_DISTANCE_OFFSET = 12


# =========================================================
# F1 22 SESSION DATA
# =========================================================

SESSION_GAME_PAUSED_OFFSET = 38
SESSION_NUM_MARSHAL_ZONES_OFFSET = 42
SESSION_MARSHAL_ZONES_OFFSET = 43

MARSHAL_ZONE_SIZE = 5
MAX_MARSHAL_ZONES = 21

TRACK_LENGTH_OFFSET = 28


# =========================================================
# FLAG VALUES
# =========================================================

FLAG_NONE = 0
FLAG_GREEN = 1
FLAG_BLUE = 2
FLAG_YELLOW = 3
FLAG_RED = 4


# =========================================================
# STATE
# =========================================================

current_flag = "NONE"

last_fia_flag = None
last_zone_flag = None

last_rpm = -1

last_telemetry_time = time.monotonic()

leds_off = False

game_paused = False

last_lap_distance = None

track_length = 0

marshal_zones = []


# =========================================================
# ADDED STATE
# =========================================================

# Arduino heartbeat
last_heartbeat_time = time.monotonic()

# Shift light state
shift_active = False

# Race start state
race_start_active = False

# Last event
last_event_code = None

# Last start-light count
last_start_light_count = -1


# =========================================================
# AUTOMATIC RPM
# =========================================================
#
# Current RPM:
#   rpm
#
# Detected car maximum RPM:
#   car_max_rpm
#
# =========================================================

car_max_rpm = 15000

last_maxrpm_time = 0

MIN_MAX_RPM = 10000
MAX_MAX_RPM = 20000

MAXRPM_UPDATE_INTERVAL = 2.0

highest_rpm_seen = 0


# =========================================================
# CONNECT ARDUINO
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

sock.bind(
    (
        UDP_IP,
        UDP_PORT
    )
)


print()
print("==============================")
print("       F1 22 REV SYSTEM")
print("==============================")
print()
print("UDP Format : 2022")
print("UDP Port   : 20777")
print()
print("REV        : ENABLED")
print("AUTO RPM   : ENABLED")
print("SHIFT      : ENABLED")
print("YELLOW     : ENABLED")
print("RED        : ENABLED")
print("GREEN      : ENABLED")
print("BLUE       : ENABLED")
print("START      : ENABLED")
print("LIGHTS OUT : ENABLED")
print()
print("Waiting for F1 22 telemetry...")
print("Drive the car.")
print()


# =========================================================
# SEND COMMAND TO ARDUINO
# =========================================================

def send(command):

    try:

        arduino.write(
            (command + "\n").encode()
        )

        arduino.flush()

    except Exception as e:

        print(
            f"\nArduino error: {e}"
        )


# =========================================================
# ARDUINO HEARTBEAT
# =========================================================
#
# Added so the Arduino watchdog does not shut the LEDs off
# simply because RPM/flags did not change.
#
# =========================================================

def heartbeat():

    global last_heartbeat_time

    now = time.monotonic()

    if (
        now - last_heartbeat_time
        >= HEARTBEAT_INTERVAL
    ):

        try:

            arduino.write(
                b"PING\n"
            )

            arduino.flush()

        except Exception as e:

            print(
                f"\nArduino heartbeat error: {e}"
            )

        last_heartbeat_time = now


# =========================================================
# STARTUP LED TEST
# =========================================================

def startup_led_test():

    print()
    print("==============================")
    print("      ARDUINO LED TEST")
    print("==============================")

    print()
    print("Testing GREEN...")

    send("OFF")

    time.sleep(0.5)

    send("GREEN")

    time.sleep(1)


    print("Testing YELLOW...")

    send("YELLOW")

    time.sleep(1)


    print("Testing RED...")

    send("RED")

    time.sleep(1)


    print("Testing BLUE...")

    send("BLUE")

    time.sleep(1)


    print("Testing RPM...")

    send("MAXRPM:12000")

    send("RPM:6000")

    time.sleep(1)


    print("Testing SHIFT...")

    send("SHIFT")

    time.sleep(1)


    print("Turning LEDs OFF...")

    send("OFF")

    time.sleep(0.5)

    print()
    print("LED TEST FINISHED.")
    print()


startup_led_test()


# =========================================================
# TURN OFF ALL LEDs
# =========================================================

def turn_off():

    global current_flag
    global leds_off
    global last_rpm
    global last_fia_flag
    global last_zone_flag
    global shift_active
    global race_start_active
    global last_start_light_count

    current_flag = "NONE"

    last_rpm = -1

    last_fia_flag = None
    last_zone_flag = None

    shift_active = False

    race_start_active = False

    last_start_light_count = -1

    send("NONE")
    send("OFF")

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

    if flag in (
        "YELLOW",
        "RED",
        "GREEN",
        "BLUE"
    ):

        send(flag)

        leds_off = False

        print(
            f"\n{flag} FLAG"
        )

    else:

        send("NONE")

        leds_off = False

        print(
            "\nFLAG CLEARED"
        )


# =========================================================
# SHIFT LIGHTS
# =========================================================
#
# Uses F1 22 revLightsPercent.
#
# 95%+ = SHIFT
# below 95% = SHIFT_OFF
#
# =========================================================

def process_shift(rev_percent):

    global shift_active

    if game_paused:
        return

    if race_start_active:
        return

    if rev_percent >= 95:

        if not shift_active:

            shift_active = True

            send("SHIFT")

            print(
                f"\nSHIFT LIGHT ON "
                f"({rev_percent}%)"
            )

    else:

        if shift_active:

            shift_active = False

            send("SHIFT_OFF")

            print(
                f"\nSHIFT LIGHT OFF "
                f"({rev_percent}%)"
            )


# =========================================================
# READ F1 22 HEADER
# =========================================================

def read_header(data):

    if len(data) < HEADER_SIZE:

        return None


    try:

        packet_format = struct.unpack_from(
            "<H",
            data,
            0
        )[0]

        game_major = data[2]

        game_minor = data[3]

        packet_version = data[4]

        packet_id = data[5]

        player_car = data[
            PLAYER_CAR_OFFSET
        ]


        return (
            packet_format,
            game_major,
            game_minor,
            packet_version,
            packet_id,
            player_car
        )


    except Exception:

        return None


# =========================================================
# PROCESS SESSION
# =========================================================

def process_session(data):

    global track_length
    global marshal_zones
    global game_paused


    if len(data) < (
        SESSION_MARSHAL_ZONES_OFFSET
    ):

        return


    # -----------------------------------------------------
    # GAME PAUSED
    # -----------------------------------------------------

    paused = data[
        SESSION_GAME_PAUSED_OFFSET
    ]


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


    # -----------------------------------------------------
    # TRACK LENGTH
    # -----------------------------------------------------

    track_length = struct.unpack_from(
        "<H",
        data,
        TRACK_LENGTH_OFFSET
    )[0]


    # -----------------------------------------------------
    # NUMBER OF MARSHAL ZONES
    # -----------------------------------------------------

    number_of_zones = data[
        SESSION_NUM_MARSHAL_ZONES_OFFSET
    ]


    number_of_zones = min(
        number_of_zones,
        MAX_MARSHAL_ZONES
    )


    zones = []


    for i in range(number_of_zones):

        offset = (
            SESSION_MARSHAL_ZONES_OFFSET
            + i * MARSHAL_ZONE_SIZE
        )


        if len(data) < (
            offset
            + MARSHAL_ZONE_SIZE
        ):

            break


        zone_start = struct.unpack_from(
            "<f",
            data,
            offset
        )[0]


        zone_flag = struct.unpack_from(
            "<b",
            data,
            offset + 4
        )[0]


        zones.append(
            (
                zone_start,
                zone_flag
            )
        )


    marshal_zones = zones


# =========================================================
# PROCESS LAP DATA
# =========================================================

def process_lap_data(
    data,
    player_car
):

    global last_lap_distance


    offset = (
        HEADER_SIZE
        + player_car * LAP_DATA_SIZE
    )


    if len(data) < (
        offset
        + LAP_DISTANCE_OFFSET
        + 4
    ):

        return


    try:

        last_lap_distance = struct.unpack_from(
            "<f",
            data,
            offset + LAP_DISTANCE_OFFSET
        )[0]

    except Exception:

        return


# =========================================================
# GET CURRENT MARSHAL ZONE
# =========================================================

def get_current_zone_flag():

    if (
        last_lap_distance is None
        or track_length <= 0
        or not marshal_zones
    ):

        return FLAG_NONE


    distance_fraction = (
        last_lap_distance
        / track_length
    )


    while distance_fraction < 0:

        distance_fraction += 1.0


    while distance_fraction >= 1.0:

        distance_fraction -= 1.0


    selected_flag = FLAG_NONE

    selected_start = -1.0


    for (
        zone_start,
        zone_flag
    ) in marshal_zones:


        if zone_start <= distance_fraction:

            if zone_start >= selected_start:

                selected_start = zone_start

                selected_flag = zone_flag


    if selected_flag == FLAG_GREEN:

        return FLAG_GREEN


    if selected_flag == FLAG_YELLOW:

        return FLAG_YELLOW


    if selected_flag == FLAG_RED:

        return FLAG_RED


    return FLAG_NONE


# =========================================================
# PROCESS FLAGS
# =========================================================

def process_flags(fia_flag):

    global last_fia_flag
    global last_zone_flag


    if fia_flag == FLAG_YELLOW:

        fia_result = "YELLOW"

    elif fia_flag == FLAG_RED:

        fia_result = "RED"

    elif fia_flag == FLAG_GREEN:

        fia_result = "GREEN"

    elif fia_flag == FLAG_BLUE:

        fia_result = "BLUE"

    else:

        fia_result = "NONE"


    zone_flag = get_current_zone_flag()


    if zone_flag == FLAG_YELLOW:

        zone_result = "YELLOW"

    elif zone_flag == FLAG_RED:

        zone_result = "RED"

    elif zone_flag == FLAG_GREEN:

        zone_result = "GREEN"

    else:

        zone_result = "NONE"


    # -----------------------------------------------------
    # FLAG PRIORITY
    #
    # RED
    # YELLOW
    # BLUE
    # GREEN
    # NONE
    # -----------------------------------------------------

    if (
        fia_result == "RED"
        or zone_result == "RED"
    ):

        result = "RED"


    elif (
        fia_result == "YELLOW"
        or zone_result == "YELLOW"
    ):

        result = "YELLOW"


    elif fia_result == "BLUE":

        result = "BLUE"


    elif (
        fia_result == "GREEN"
        or zone_result == "GREEN"
    ):

        result = "GREEN"


    else:

        result = "NONE"


    if (
        fia_flag != last_fia_flag
        or zone_flag != last_zone_flag
    ):

        last_fia_flag = fia_flag

        last_zone_flag = zone_flag

        print(
            f"\nFIA FLAG VALUE: {fia_flag} | "
            f"ZONE FLAG: {zone_flag}"
        )

        set_flag(
            result
        )


# =========================================================
# PROCESS CAR TELEMETRY
# =========================================================

def process_car_telemetry(
    data,
    player_car
):

    global last_rpm
    global car_max_rpm
    global last_maxrpm_time
    global highest_rpm_seen


    # -----------------------------------------------------
    # PLAYER CAR OFFSET
    # -----------------------------------------------------

    car_offset = (
        HEADER_SIZE
        + player_car * CAR_TELEMETRY_SIZE
    )


    if len(data) < (
        car_offset
        + CAR_TELEMETRY_SIZE
    ):

        return


    # -----------------------------------------------------
    # CURRENT ENGINE RPM
    # -----------------------------------------------------

    rpm = struct.unpack_from(
        "<H",
        data,
        car_offset + ENGINE_RPM_OFFSET
    )[0]


    # -----------------------------------------------------
    # REV LIGHT PERCENTAGE
    # -----------------------------------------------------

    rev_percent = data[
        car_offset
        + REV_LIGHT_PERCENT_OFFSET
    ]


    # -----------------------------------------------------
    # KEEP HIGHEST RPM SEEN
    # -----------------------------------------------------

    if rpm > highest_rpm_seen:

        highest_rpm_seen = rpm


    # -----------------------------------------------------
    # SEND CURRENT RPM
    # -----------------------------------------------------

    if not game_paused:

        if rpm != last_rpm:

            send(
                f"RPM:{rpm}"
            )

            last_rpm = rpm


            print(
                f"\rRPM: {rpm:5} | "
                f"MAX RPM: {car_max_rpm:5} | "
                f"REV: {rev_percent:3}% | "
                f"PEAK: {highest_rpm_seen:5} | "
                f"FLAG: {current_flag}     ",
                end=""
            )


    # =====================================================
    # ADDED SHIFT LIGHT SYSTEM
    # =====================================================

    process_shift(
        rev_percent
    )


    # =====================================================
    # AUTOMATIC MAX RPM DETECTION
    # =====================================================

    if (
        rev_percent >= 95
        and rpm >= MIN_MAX_RPM
    ):

        estimated_max = int(
            rpm * 100
            / rev_percent
        )


        estimated_max = max(
            MIN_MAX_RPM,
            min(
                MAX_MAX_RPM,
                estimated_max
            )
        )


        # -------------------------------------------------
        # Smooth detected RPM
        # -------------------------------------------------

        car_max_rpm = int(
            car_max_rpm * 0.90
            + estimated_max * 0.10
        )


        now = time.monotonic()


        # -------------------------------------------------
        # Send MAXRPM
        # -------------------------------------------------

        if (
            now - last_maxrpm_time
            >= MAXRPM_UPDATE_INTERVAL
        ):

            send(
                f"MAXRPM:{car_max_rpm}"
            )

            last_maxrpm_time = now


            print(
                f"\nMAX RPM UPDATED: "
                f"{car_max_rpm}"
            )


# =========================================================
# PROCESS CAR STATUS
# =========================================================

def process_car_status(
    data,
    player_car
):

    car_offset = (
        HEADER_SIZE
        + player_car * CAR_STATUS_SIZE
    )


    if len(data) < (
        car_offset
        + CAR_STATUS_SIZE
    ):

        return


    # -----------------------------------------------------
    # NETWORK PAUSED
    # -----------------------------------------------------

    network_paused = data[
        car_offset
        + NETWORK_PAUSED_OFFSET
    ]


    if network_paused == 1:

        if not game_paused:

            turn_off()

            print(
                "\nNETWORK PAUSED - LEDs OFF"
            )

        return


    # -----------------------------------------------------
    # FIA FLAG
    # -----------------------------------------------------

    fia_flag = struct.unpack_from(
        "<b",
        data,
        car_offset + FIA_FLAG_OFFSET
    )[0]


    process_flags(
        fia_flag
    )


# =========================================================
# PROCESS EVENT
# =========================================================

def process_event(data):

    global last_event_code
    global race_start_active
    global last_start_light_count
    global shift_active


    if len(data) < 28:

        return


    event_code = data[
        24:28
    ]


    # -----------------------------------------------------
    # Prevent repeated processing
    # -----------------------------------------------------

    event_string = event_code.decode(
        "ascii",
        errors="ignore"
    )


    # =====================================================
    # SESSION START
    # =====================================================

    if event_string == "SSTA":

        if last_event_code != event_string:

            print(
                "\nSESSION STARTED"
            )

        last_event_code = event_string

        return


    # =====================================================
    # SESSION END
    # =====================================================

    if event_string == "SEND":

        if last_event_code != event_string:

            print(
                "\nSESSION ENDED"
            )

            turn_off()

        last_event_code = event_string

        return


    # =====================================================
    # START LIGHTS
    # =====================================================
    #
    # F1 22 STLG event contains the number of start lights
    # in the event data.
    #
    # Byte 28 = number of lights.
    #
    # =====================================================

    if event_string == "STLG":

        if len(data) >= 29:

            start_light_count = data[28]

            start_light_count = max(
                0,
                min(
                    5,
                    start_light_count
                )
            )


            if (
                start_light_count
                !=
                last_start_light_count
            ):

                last_start_light_count = (
                    start_light_count
                )

                race_start_active = True

                shift_active = False

                send(
                    f"START:{start_light_count}"
                )


                print(
                    f"\nRACE START LIGHTS: "
                    f"{start_light_count}"
                )


        last_event_code = event_string

        return


    # =====================================================
    # LIGHTS OUT
    # =====================================================

    if event_string == "LGOT":

        race_start_active = False

        last_start_light_count = -1

        shift_active = False

        print(
            "\nLIGHTS OUT!"
        )

        send(
            "LIGHTSOUT"
        )

        last_event_code = event_string

        return


    # =====================================================
    # RED FLAG EVENT
    # =====================================================

    if event_string == "RDFL":

        race_start_active = False

        shift_active = False

        print(
            "\nRED FLAG EVENT"
        )

        set_flag(
            "RED"
        )

        last_event_code = event_string

        return


    # =====================================================
    # DEFAULT EVENT
    # =====================================================

    last_event_code = event_string


# =========================================================
# MAIN LOOP
# =========================================================

while True:

    try:

        # =================================================
        # ARDUINO HEARTBEAT
        # =================================================

        heartbeat()


        # =================================================
        # RECEIVE UDP
        # =================================================

        try:

            data, address = sock.recvfrom(
                2048
            )


        except socket.timeout:

            if (
                time.monotonic()
                - last_telemetry_time
                >= TELEMETRY_TIMEOUT
            ):

                if not leds_off:

                    turn_off()

                    print(
                        "\nNo telemetry for "
                        f"{TELEMETRY_TIMEOUT} seconds "
                        "- LEDs OFF"
                    )

            continue


        # =================================================
        # TELEMETRY RECEIVED
        # =================================================

        last_telemetry_time = (
            time.monotonic()
        )

        leds_off = False


        # =================================================
        # READ HEADER
        # =================================================

        header = read_header(
            data
        )


        if header is None:

            continue


        (
            packet_format,
            game_major,
            game_minor,
            packet_version,
            packet_id,
            player_car
        ) = header


        # =================================================
        # ONLY F1 22
        # =================================================

        if packet_format != F1_22_FORMAT:

            continue


        if player_car > 21:

            continue


        # =================================================
        # CAR TELEMETRY
        # =================================================

        if packet_id == PACKET_CAR_TELEMETRY:

            process_car_telemetry(
                data,
                player_car
            )


        # =================================================
        # SESSION
        # =================================================

        elif packet_id == PACKET_SESSION:

            process_session(
                data
            )


        # =================================================
        # LAP DATA
        # =================================================

        elif packet_id == PACKET_LAP_DATA:

            process_lap_data(
                data,
                player_car
            )


        # =================================================
        # EVENT
        # =================================================

        elif packet_id == PACKET_EVENT:

            process_event(
                data
            )


        # =================================================
        # CAR STATUS
        # =================================================

        elif packet_id == PACKET_CAR_STATUS:

            process_car_status(
                data,
                player_car
            )


    # =====================================================
    # CTRL + C
    # =====================================================

    except KeyboardInterrupt:

        print(
            "\nStopping..."
        )

        turn_off()

        time.sleep(0.2)

        break


    # =====================================================
    # TELEMETRY ERROR
    # =====================================================

    except Exception as e:

        print(
            f"\nTelemetry error: {e}"
        )

        time.sleep(0.05)


# =========================================================
# CLEANUP
# =========================================================

try:

    sock.close()

except:

    pass


try:

    arduino.close()

except:

    pass