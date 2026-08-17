import socket
import serial
import struct
import time


# =========================================================
# F1 22 REV + FLAG SYSTEM
# =========================================================
#
# Arduino code is unchanged.
#
# Arduino commands used:
#
#   RPM:xxxx
#   MAXRPM:xxxx
#   YELLOW
#   RED
#   GREEN
#   NONE
#   OFF
#
# BLUE FLAG IS DISABLED.
#
# F1 22 UDP format:
#   2022
#
# UDP:
#   127.0.0.1:20777
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
# F1 22 PACKET CONSTANTS
# =========================================================

F1_22_FORMAT = 2022

PACKET_SESSION = 1
PACKET_LAP_DATA = 2
PACKET_EVENT = 3
PACKET_CAR_TELEMETRY = 6
PACKET_CAR_STATUS = 7


# F1 22 header is 24 bytes.
HEADER_SIZE = 24

# F1 22 CarTelemetryData is 60 bytes.
CAR_TELEMETRY_SIZE = 60

# F1 22 CarStatusData is 47 bytes.
CAR_STATUS_SIZE = 47

# F1 22 LapData is 43 bytes.
LAP_DATA_SIZE = 43


# =========================================================
# F1 22 DATA OFFSETS
# =========================================================

# Packet header:
#
# 0-1   packet format
# 2     game major version
# 3     game minor version
# 4     packet version
# 5     packet ID
# 6-13  session UID
# 14-17 session time
# 18-21 frame identifier
# 22    player car index
# 23    secondary player car index

PLAYER_CAR_OFFSET = 22


# CarTelemetryData:
#
# 0     speed
# 2     throttle
# 6     steer
# 10    brake
# 14    clutch
# 15    gear
# 16    engine RPM
# 18    DRS
# 19    rev lights percent
# 20    rev lights bit value

ENGINE_RPM_OFFSET = 16
REV_LIGHT_PERCENT_OFFSET = 19


# CarStatusData:
#
# 0 traction control
# 1 ABS
# 2 fuel mix
# 3 brake bias
# 4 pit limiter
# 5 tyre age
# 6 vehicle FIA flags

FIA_FLAG_OFFSET = 6

# After vehicleFiaFlags:
#
# ersStoreEnergy       4 bytes
# ersDeployMode        1 byte
# ersHarvestedMGUK     4 bytes
# ersHarvestedMGUH     4 bytes
# ersDeployed          4 bytes
# networkPaused        1 byte
#
# Therefore networkPaused = offset 23.

NETWORK_PAUSED_OFFSET = 23


# LapData:
#
# last lap time       0
# current lap time    4
# sector 1            8
# sector 2            10
# lap distance        12
#
LAP_DISTANCE_OFFSET = 12


# =========================================================
# F1 22 SESSION DATA
# =========================================================
#
# Header = 24
#
# weather                  24
# track temperature        25
# air temperature          26
# total laps               27
# track length             28-29
# session type             30
# track ID                 31
# formula                  32
# session time left        33-34
# session duration         35-36
# pit speed limit          37
# game paused              38
# spectating               39
# spectator car index     40
# SLI support              41
# num marshal zones        42
# marshal zones            43 onward
#
# Each MarshalZone:
#   float zone start       4 bytes
#   int8  zone flag        1 byte
#
# =========================================================

SESSION_GAME_PAUSED_OFFSET = 38
SESSION_NUM_MARSHAL_ZONES_OFFSET = 42
SESSION_MARSHAL_ZONES_OFFSET = 43

MARSHAL_ZONE_SIZE = 5
MAX_MARSHAL_ZONES = 21

TRACK_LENGTH_OFFSET = 28


# =========================================================
# FLAG VALUES FROM F1 22
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
# AUTOMATIC RPM
# =========================================================

estimated_max_rpm = 15000

last_maxrpm_time = 0

MIN_MAX_RPM = 10000
MAX_MAX_RPM = 20000

MAXRPM_UPDATE_INTERVAL = 2.0


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
print("YELLOW     : ENABLED")
print("RED        : ENABLED")
print("GREEN      : ENABLED")
print("BLUE       : DISABLED")
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

    except Exception as e:

        print(
            f"\nArduino error: {e}"
        )


# =========================================================
# TURN OFF ALL LEDs
# =========================================================

def turn_off():

    global current_flag
    global leds_off
    global last_rpm
    global last_fia_flag
    global last_zone_flag

    current_flag = "NONE"

    last_rpm = -1

    last_fia_flag = None
    last_zone_flag = None

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
        "GREEN"
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


    # F1 can report negative distance before
    # the start/finish line.

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


    # -----------------------------------------------------
    # Only GREEN / YELLOW / RED are used.
    # BLUE is intentionally ignored.
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # FIA FLAG
    # -----------------------------------------------------

    if fia_flag == FLAG_YELLOW:

        fia_result = "YELLOW"

    elif fia_flag == FLAG_RED:

        fia_result = "RED"

    elif fia_flag == FLAG_GREEN:

        fia_result = "GREEN"

    else:

        # Includes NONE, BLUE and invalid.
        fia_result = "NONE"


    # -----------------------------------------------------
    # MARSHAL ZONE
    # -----------------------------------------------------

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
    # PRIORITY
    #
    # RED
    # YELLOW
    # GREEN
    # NONE
    #
    # This prevents a green marshal zone from overriding
    # a yellow/red FIA condition.
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


    elif (
        fia_result == "GREEN"
        or zone_result == "GREEN"
    ):

        result = "GREEN"


    else:

        result = "NONE"


    # -----------------------------------------------------
    # SEND WHEN FLAG SOURCE CHANGES
    # -----------------------------------------------------

    if (
        fia_flag != last_fia_flag
        or zone_flag != last_zone_flag
    ):

        last_fia_flag = fia_flag

        last_zone_flag = zone_flag

        # Debug information.

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
    global estimated_max_rpm
    global last_maxrpm_time


    # -----------------------------------------------------
    # Player car offset
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
    # ENGINE RPM
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
    # SEND RPM
    # -----------------------------------------------------

    if not game_paused:

        if rpm != last_rpm:

            send(
                f"RPM:{rpm}"
            )

            last_rpm = rpm

            print(
                f"\rRPM: {rpm:5} | "
                f"FLAG: {current_flag}     ",
                end=""
            )


    # -----------------------------------------------------
    # AUTOMATIC MAX RPM
    # -----------------------------------------------------
    #
    # F1 22 does not provide maxRPM in CarStatusData.
    # revLightsPercent is therefore used to estimate it.
    #
    # -----------------------------------------------------

    if (
        rev_percent >= 95
        and rpm >= MIN_MAX_RPM
    ):

        estimated = int(
            rpm * 100
            / rev_percent
        )


        estimated = max(
            MIN_MAX_RPM,
            min(
                MAX_MAX_RPM,
                estimated
            )
        )


        estimated_max_rpm = int(
            estimated_max_rpm * 0.90
            + estimated * 0.10
        )


        now = time.monotonic()


        if (
            now - last_maxrpm_time
            >= MAXRPM_UPDATE_INTERVAL
        ):

            send(
                f"MAXRPM:{estimated_max_rpm}"
            )

            last_maxrpm_time = now


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

    # F1 22 header is 24 bytes.
    #
    # Event code therefore begins at byte 24.

    if len(data) < 28:

        return


    event_code = data[
        24:28
    ]


    # -----------------------------------------------------
    # RED FLAG
    # -----------------------------------------------------

    if event_code == b"RDFL":

        if not game_paused:

            set_flag(
                "RED"
            )


# =========================================================
# MAIN LOOP
# =========================================================

while True:

    try:

        # =================================================
        # RECEIVE UDP
        # =================================================

        try:

            data, address = sock.recvfrom(
                2048
            )


        except socket.timeout:

            # ---------------------------------------------
            # NO TELEMETRY FOR 3 SECONDS
            # ---------------------------------------------

            if (
                time.monotonic()
                - last_telemetry_time
                >= TELEMETRY_TIMEOUT
            ):

                if not leds_off:

                    turn_off()

                    print(
                        "\nNo telemetry for 3 seconds - LEDs OFF"
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


        # -------------------------------------------------
        # Make sure player index is valid.
        # -------------------------------------------------

        if player_car > 21:

            continue


        # =================================================
        # DEBUG PACKET
        # =================================================

        if packet_id == PACKET_CAR_TELEMETRY:

            # Only useful packet information.
            #
            # Uncomment the next print if you need it.
            #
            # print(
            #     f"\nPacket ID: {packet_id} | "
            #     f"Format: {packet_format} | "
            #     f"Size: {len(data)} | "
            #     f"Player: {player_car}"
            # )

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
