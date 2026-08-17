import socket
import serial
import struct
import time


# =========================================================
# SETTINGS
# =========================================================

UDP_IP = "127.0.0.1"
UDP_PORT = 20777

ARDUINO_PORT = "COM4"
ARDUINO_BAUD = 9600

# Turn LEDs off after 3 seconds without telemetry
TELEMETRY_TIMEOUT = 3.0


# =========================================================
# CONNECT ARDUINO
# =========================================================

arduino = serial.Serial(
    ARDUINO_PORT,
    ARDUINO_BAUD,
    timeout=1
)

time.sleep(2)

print("Arduino connected on COM4")
print("Waiting for F1 2020 telemetry...")


# =========================================================
# UDP
# =========================================================

sock = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM
)

# Short timeout allows us to detect
# when telemetry stops.

sock.settimeout(0.2)

sock.bind(
    (UDP_IP, UDP_PORT)
)


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


# =========================================================
# SEND TO ARDUINO
# =========================================================

def send(command):

    arduino.write(
        (command + "\n").encode()
    )


# =========================================================
# TURN EVERYTHING OFF
# =========================================================

def turn_off():

    global current_flag
    global leds_off

    current_flag = "NONE"

    send("OFF")

    leds_off = True


# =========================================================
# SET FLAG
# =========================================================

def set_flag(flag):

    global current_flag
    global leds_off

    if current_flag != flag:

        current_flag = flag

        send(flag)

        leds_off = False

        print(
            f"\n{flag} FLAG"
        )


# =========================================================
# MAIN LOOP
# =========================================================

while True:

    try:

        # =================================================
        # RECEIVE TELEMETRY
        # =================================================

        try:

            data, address = sock.recvfrom(
                2048
            )

        except socket.timeout:

            # ---------------------------------------------
            # No telemetry
            # ---------------------------------------------

            if (
                time.monotonic()
                - last_telemetry_time
                >= TELEMETRY_TIMEOUT
            ):

                if not leds_off:

                    turn_off()

                    print(
                        "\nNo F1 telemetry for 3 seconds - LEDs OFF"
                    )

            continue


        # =================================================
        # TELEMETRY RECEIVED
        # =================================================

        last_telemetry_time = time.monotonic()

        leds_off = False


        if len(data) < 24:

            continue


        # =================================================
        # HEADER
        # =================================================

        packet_id = data[5]

        player_car = data[22]


        # =================================================
        # PACKET 6
        # CAR TELEMETRY
        # =================================================

        if packet_id == 6:

            if len(data) != 1307:

                continue


            car_offset = (
                24 +
                player_car * 58
            )


            # engineRPM = +16

            rpm_offset = (
                car_offset + 16
            )


            if rpm_offset + 2 > len(data):

                continue


            rpm = struct.unpack_from(
                "<H",
                data,
                rpm_offset
            )[0]


            # ---------------------------------------------
            # Don't send RPM while paused
            # or during start lights.
            #
            # Arduino also protects the start sequence.
            # ---------------------------------------------

            if not game_paused:

                send(
                    f"RPM:{rpm}"
                )


                print(
                    f"\rRPM: {rpm:5} | FLAG: {current_flag}",
                    end=""
                )


        # =================================================
        # PACKET 1
        # SESSION DATA
        # =================================================

        elif packet_id == 1:

            if len(data) != 251:

                continue


            # -------------------------------------------------
            # Track length
            # -------------------------------------------------

            track_length = struct.unpack_from(
                "<H",
                data,
                28
            )[0]


            # -------------------------------------------------
            # GAME PAUSED
            #
            # m_gamePaused = byte 38
            # -------------------------------------------------

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


            # -------------------------------------------------
            # Number of marshal zones
            # -------------------------------------------------

            num_zones = data[41]


            if num_zones > 21:

                num_zones = 21


            zones = []


            # -------------------------------------------------
            # Marshal zones
            # -------------------------------------------------

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


        # =================================================
        # PACKET 2
        # LAP DATA
        # =================================================

        elif packet_id == 2:

            if len(data) != 1190:

                continue


            lap_offset = (
                24 +
                player_car * 53
            )


            if lap_offset + 53 > len(data):

                continue


            lap_distance = struct.unpack_from(
                "<f",
                data,
                lap_offset + 20
            )[0]


            if track_length <= 0:

                continue


            lap_fraction = (
                lap_distance /
                track_length
            )


            lap_fraction %= 1.0


            # =================================================
            # FIND ACTIVE MARSHAL ZONE
            # =================================================

            active_flag = 0


            if len(zones) > 0:

                sorted_zones = sorted(
                    zones,
                    key=lambda x: x[0]
                )


                for i in range(
                    len(sorted_zones)
                ):

                    start = sorted_zones[i][0]


                    if (
                        i + 1
                        < len(sorted_zones)
                    ):

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


            # =================================================
            # FLAG LOGIC
            #
            # 1 = GREEN
            # 2 = BLUE
            # 3 = YELLOW
            # 4 = RED
            # =================================================

            if not game_paused:

                # ---------------------------------------------
                # YELLOW
                # ---------------------------------------------

                if active_flag == 3:

                    if last_zone_flag != 3:

                        last_zone_flag = 3

                        set_flag("YELLOW")


                # ---------------------------------------------
                # RED
                # ---------------------------------------------

                elif active_flag == 4:

                    if last_zone_flag != 4:

                        last_zone_flag = 4

                        set_flag("RED")


                # ---------------------------------------------
                # BLUE
                # ---------------------------------------------

                elif active_flag == 2:

                    if last_zone_flag != 2:

                        last_zone_flag = 2

                        set_flag("BLUE")


                # ---------------------------------------------
                # GREEN
                # ---------------------------------------------

                elif active_flag == 1:

                    if last_zone_flag != 1:

                        last_zone_flag = 1

                        set_flag("GREEN")


                # ---------------------------------------------
                # NO FLAG
                # ---------------------------------------------

                else:

                    if last_zone_flag != 0:

                        last_zone_flag = 0


                        if current_flag in (
                            "YELLOW",
                            "GREEN",
                            "BLUE"
                        ):

                            current_flag = "NONE"

                            send("NONE")

                            print(
                                "\nFLAG CLEARED"
                            )


        # =================================================
        # PACKET 3
        # EVENT DATA
        #
        # F1 2020 race start events
        # =================================================

        elif packet_id == 3:

            if len(data) != 35:

                continue


            # -------------------------------------------------
            # Event code
            #
            # Header = 24 bytes
            # Event code = bytes 24-27
            # Event data = byte 28 onward
            # -------------------------------------------------

            event_code = data[24:28]


            # =================================================
            # START LIGHTS
            #
            # STLG
            #
            # Byte 28 = number of red lights
            # =================================================

            if event_code == b"STLG":

                number_of_lights = data[28]


                if number_of_lights > 5:

                    number_of_lights = 5


                if number_of_lights > 0:

                    print(
                        f"\nSTART LIGHTS: {number_of_lights}"
                    )


                    send(
                        f"START:{number_of_lights}"
                    )


            # =================================================
            # LIGHTS OUT
            #
            # LGOT
            # =================================================

            elif event_code == b"LGOT":

                print(
                    "\nLIGHTS OUT!"
                )


                send(
                    "LIGHTSOUT"
                )


        # =================================================
        # PACKET 7
        # CAR STATUS
        # =================================================

        elif packet_id == 7:

            if len(data) != 1344:

                continue


            car_offset = (
                24 +
                player_car * 60
            )


            # vehicleFiaFlags = +42

            fia_offset = (
                car_offset + 42
            )


            if fia_offset >= len(data):

                continue


            fia_flag = struct.unpack_from(
                "<b",
                data,
                fia_offset
            )[0]


            if not game_paused:

                # ---------------------------------------------
                # RED
                # ---------------------------------------------

                if fia_flag == 4:

                    set_flag("RED")


                # ---------------------------------------------
                # YELLOW
                # ---------------------------------------------

                elif fia_flag == 3:

                    set_flag("YELLOW")


                # ---------------------------------------------
                # GREEN
                # ---------------------------------------------

                elif fia_flag == 1:

                    set_flag("GREEN")


                # ---------------------------------------------
                # NONE
                # ---------------------------------------------

                elif fia_flag == 0:

                    if current_flag == "GREEN":

                        current_flag = "NONE"

                        send("NONE")

                        print(
                            "\nFLAG CLEARED"
                        )


    # =====================================================
    # CTRL + C
    # =====================================================

    except KeyboardInterrupt:

        print(
            "\nStopping..."
        )

        send("OFF")

        break