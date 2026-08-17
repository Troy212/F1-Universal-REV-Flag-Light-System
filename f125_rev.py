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

TELEMETRY_TIMEOUT = 3.0


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

print("Arduino connected on COM4")


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
    (UDP_IP, UDP_PORT)
)


print("Waiting for F1 25 telemetry...")
print("Drive the car.")


# =========================================================
# STATE
# =========================================================

current_flag = "NONE"

last_flag = 0

last_telemetry_time = time.monotonic()

leds_off = False

game_paused = False

race_start_active = False

last_start_lights = 0


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
    global race_start_active
    global last_start_lights

    current_flag = "NONE"

    race_start_active = False

    last_start_lights = 0

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
# UDP HEADER
# =========================================================

def read_header(data):

    if len(data) < 29:

        return None


    packet_format = struct.unpack_from(
        "<H",
        data,
        0
    )[0]


    game_year = data[2]

    packet_version = data[5]

    packet_id = data[6]

    player_car = data[27]


    return (
        packet_format,
        game_year,
        packet_version,
        packet_id,
        player_car
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

        last_telemetry_time = time.monotonic()

        leds_off = False


        # =================================================
        # READ HEADER
        # =================================================

        header = read_header(data)

        if header is None:

            continue


        (
            packet_format,
            game_year,
            packet_version,
            packet_id,
            player_car
        ) = header


        # =================================================
        # DEBUG FORMAT
        # =================================================

        # Only print once when useful

        if packet_id == 6:

            print(
                f"\nPacket ID: {packet_id} | "
                f"Format: {packet_format} | "
                f"Size: {len(data)} | "
                f"Player: {player_car}"
            )


        # =================================================
        # F1 25 / 2026
        # =================================================

        if packet_format not in (
            2025,
            2026
        ):

            continue


        # =================================================
        # PACKET 1
        #
        # SESSION
        # =================================================

        if packet_id == 1:

            # We only need basic pause handling here.

            if len(data) >= 44:

                # m_gamePaused is after the first session
                # fields in the F1 UDP session packet.

                paused = data[43]


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


        # =================================================
        # PACKET 3
        #
        # EVENT
        # =================================================

        elif packet_id == 3:

            if len(data) < 33:

                continue


            event_code = data[29:33]


            # =============================================
            # START LIGHTS
            # =============================================

            if event_code == b"STLG":

                if len(data) >= 34:

                    number_of_lights = data[33]

                    number_of_lights = max(
                        0,
                        min(
                            number_of_lights,
                            5
                        )
                    )


                    if number_of_lights > 0:

                        race_start_active = True

                        last_start_lights = (
                            number_of_lights
                        )


                        print(
                            f"\nSTART LIGHTS: "
                            f"{number_of_lights}"
                        )


                        send(
                            f"START:{number_of_lights}"
                        )


            # =============================================
            # LIGHTS OUT
            # =============================================

            elif event_code == b"LGOT":

                race_start_active = False

                last_start_lights = 0

                print(
                    "\nLIGHTS OUT!"
                )


                send(
                    "LIGHTSOUT"
                )


            # =============================================
            # RED FLAG
            # =============================================

            elif event_code == b"RDFL":

                if not game_paused:

                    set_flag("RED")


            # =============================================
            # SESSION ENDED
            # =============================================

            elif event_code == b"SEND":

                turn_off()

                print(
                    "\nSESSION ENDED - LEDs OFF"
                )


        # =================================================
        # PACKET 6
        #
        # CAR TELEMETRY
        #
        # Used for RPM
        # =================================================

        elif packet_id == 6:

            # F1 25 Car Telemetry:
            #
            # Header = 29
            # CarTelemetryData = 60
            #
            # Packet size = 1352

            if len(data) < 29:

                continue


            CAR_TELEMETRY_SIZE = 60


            car_offset = (
                29 +
                (
                    player_car *
                    CAR_TELEMETRY_SIZE
                )
            )


            if (
                car_offset + 60
                > len(data)
            ):

                continue


            # =================================================
            # ENGINE RPM
            #
            # CarTelemetryData:
            #
            # 0  speed
            # 2  throttle
            # 6  steer
            # 10 brake
            # 14 clutch
            # 15 gear
            # 16 engine RPM
            # =================================================

            rpm = struct.unpack_from(
                "<H",
                data,
                car_offset + 16
            )[0]


            # =================================================
            # SEND RPM
            # =================================================

            if (
                not game_paused
                and
                not race_start_active
            ):

                send(
                    f"RPM:{rpm}"
                )


                print(
                    f"\rRPM: {rpm:5} | "
                    f"FLAG: {current_flag}",
                    end=""
                )


        # =================================================
        # PACKET 7
        #
        # CAR STATUS
        #
        # THIS IS WHERE FIA FLAGS ARE READ
        # =================================================

        elif packet_id == 7:

            # F1 25:
            #
            # Header = 29
            # CarStatusData = 55
            #
            # Packet size = 1239

            if len(data) < 29:

                continue


            CAR_STATUS_SIZE = 55


            car_offset = (
                29 +
                (
                    player_car *
                    CAR_STATUS_SIZE
                )
            )


            if (
                car_offset + 55
                > len(data)
            ):

                continue


            # =================================================
            # CAR STATUS STRUCTURE
            #
            # Offset 0:
            # tractionControl
            #
            # 1:
            # antiLockBrakes
            #
            # 2:
            # fuelMix
            #
            # 3:
            # frontBrakeBias
            #
            # 4:
            # pitLimiterStatus
            #
            # 5-8:
            # fuelInTank
            #
            # 9-12:
            # fuelCapacity
            #
            # 13-16:
            # fuelRemainingLaps
            #
            # 17-18:
            # maxRPM
            #
            # 19-20:
            # idleRPM
            #
            # 21:
            # maxGears
            #
            # 22:
            # drsAllowed
            #
            # 23-24:
            # drsActivationDistance
            #
            # 25:
            # actualTyreCompound
            #
            # 26:
            # visualTyreCompound
            #
            # 27:
            # tyresAgeLaps
            #
            # 28:
            # vehicleFiaFlags
            # =================================================


            FIA_FLAG_OFFSET = 28


            fia_flag = struct.unpack_from(
                "<b",
                data,
                car_offset + FIA_FLAG_OFFSET
            )[0]


            # =================================================
            # NETWORK PAUSED
            #
            # Later in CarStatusData
            # =================================================

            NETWORK_PAUSED_OFFSET = 54


            network_paused = data[
                car_offset +
                NETWORK_PAUSED_OFFSET
            ]


            if network_paused == 1:

                if not game_paused:

                    game_paused = True

                    turn_off()

                    print(
                        "\nNETWORK PAUSED - LEDs OFF"
                    )

                continue


            if game_paused:

                continue


            if race_start_active:

                continue


            # =================================================
            # FIA FLAG DEBUG
            # =================================================

            if fia_flag != last_flag:

                print(
                    f"\nFIA FLAG VALUE: "
                    f"{fia_flag}"
                )


            # =================================================
            # FLAG VALUES
            #
            # -1 = invalid / unknown
            #  0 = none
            #  1 = green
            #  2 = blue
            #  3 = yellow
            # =================================================

            if fia_flag == 3:

                if last_flag != 3:

                    last_flag = 3

                    set_flag(
                        "YELLOW"
                    )


            elif fia_flag == 2:

                if last_flag != 2:

                    last_flag = 2

                    set_flag(
                        "BLUE"
                    )


            elif fia_flag == 1:

                if last_flag != 1:

                    last_flag = 1

                    set_flag(
                        "GREEN"
                    )


            elif fia_flag == 0:

                if last_flag != 0:

                    last_flag = 0


                    if current_flag in (
                        "YELLOW",
                        "BLUE",
                        "GREEN"
                    ):

                        current_flag = "NONE"

                        send(
                            "NONE"
                        )

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