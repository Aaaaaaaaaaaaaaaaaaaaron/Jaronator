#!/usr/bin/env python3
import sys
import signal
import time
import select
import Hobot.GPIO as GPIO

# ========================
# Pin configuration (BOARD numbering)
# ========================
PIN_X_IN1 = 11
PIN_X_IN2 = 12
PIN_Y_IN1 = 13
PIN_Y_IN2 = 15
PIN_Z_UP = 18
PIN_Z_DOWN = 22
PIN_GRIP = 7
PIN_GRIP2 = 16
PIN_COIN = 37

# Stop-taster mit externen Pull-Ups (aktiv LOW)
PIN_STOP_X_LEFT = 31  # war 29
PIN_STOP_Y_FORWARD = 29  # war 31
PIN_STOP_X_RIGHT = 26

ALL_PINS = [
    PIN_X_IN1, PIN_X_IN2, PIN_Y_IN1, PIN_Y_IN2,
    PIN_Z_UP, PIN_Z_DOWN, PIN_GRIP, PIN_GRIP2
]

grip_state = False

# Motor-Richtungsblockaden
block_x_left = False
block_x_right = False
block_y_forward = False

# ========================
def cleanup():
    GPIO.cleanup()
    print("GPIO cleaned up")

def signal_handler(sig, frame):
    cleanup()
    sys.exit(0)

def stop_all():
    for p in [PIN_X_IN1, PIN_X_IN2, PIN_Y_IN1, PIN_Y_IN2, PIN_Z_UP, PIN_Z_DOWN]:
        GPIO.output(p, GPIO.LOW)

def move_x(direction, duration=0.2):
    if direction == "left" and block_x_left:
        print("X LEFT blockiert!")
        return stop_all()
    if direction == "left":
        GPIO.output(PIN_X_IN1, GPIO.HIGH)
    elif direction == "right":
        GPIO.output(PIN_X_IN2, GPIO.HIGH)
    time.sleep(duration)
    stop_all()

def move_y(direction, duration=0.2):
    if direction == "forward" and block_y_forward:
        print("Y FORWARD blockiert!")
        return
    if direction == "backward" and block_x_right:  # angepassen!!
        print("X RIGHT blockiert!")
        return stop_all()
    if direction == "forward":
        GPIO.output(PIN_Y_IN1, GPIO.HIGH)
    elif direction == "backward":
        GPIO.output(PIN_Y_IN2, GPIO.HIGH)
    time.sleep(duration)
    stop_all()

def move_z(direction, duration=0.2):
    stop_all()
    if direction == "up":
        GPIO.output(PIN_Z_UP, GPIO.HIGH)
    elif direction == "down":
        GPIO.output(PIN_Z_DOWN, GPIO.HIGH)
    time.sleep(duration)
    stop_all()

def toggle_grip():
    global grip_state
    grip_state = not grip_state
    GPIO.output(PIN_GRIP, GPIO.HIGH if grip_state else GPIO.LOW)
    GPIO.output(PIN_GRIP2, GPIO.HIGH if grip_state else GPIO.LOW)
    print("Grip HIGH" if grip_state else "Grip LOW")

# ========================
# Stop-Taster Ueberwachung
# ========================
def check_stop_buttons():
    global block_x_left, block_x_right, block_y_forward
    # Aktuelle Tasterzustaende
    x_left = GPIO.input(PIN_STOP_X_LEFT)
    y_forward = GPIO.input(PIN_STOP_Y_FORWARD)
    x_right = GPIO.input(PIN_STOP_X_RIGHT)
    # Blockaden setzen oder loesen
    block_x_left = (x_left == 0)
    block_y_forward = (y_forward == 0)
    block_x_right = (x_right == 0)

# ========================
def manual_mode():
    print("\nManual mode active")
    print("Keys: w=forward s=back a=left d=right v=z-axis g=grip y=down x=up q=quit")
    while True:
        check_stop_buttons()
        time.sleep(0.05)
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            key = input(">> ").strip().lower()
            if key == "q":
                stop_all()
                break
            elif key == "w":
                move_x("left")
            elif key == "s":
                move_x("right")
            elif key == "a":
                move_y("forward")
            elif key == "d":
                move_y("backward")
            elif key == "v":
                if grip_state:
                    move_z("up")
                else:
                    move_z("down")
            elif key == "g":
                toggle_grip()
            elif key == "y":
                move_z("down")
            elif key == "x":
                move_z("up")
            else:
                print("Invalid input")

def auto_mode():
    print("\nAuto mode started after coin insert")
    move_y("forward")
    move_z("down")
    toggle_grip()
    move_z("up")
    move_y("backward")

# ========================
def main():
    GPIO.cleanup()
    GPIO.setmode(GPIO.BOARD)
    for p in ALL_PINS:
        GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PIN_COIN, GPIO.IN)
    # Stop-Taster Eingange (externe Pull-Ups)
    GPIO.setup(PIN_STOP_X_LEFT, GPIO.IN)
    GPIO.setup(PIN_STOP_Y_FORWARD, GPIO.IN)
    GPIO.setup(PIN_STOP_X_RIGHT, GPIO.IN)

    print("1) Manual mode")
    print("2) Auto mode ")
    choice = input("Select mode (1/2): ").strip()
    try:
        if choice == "1":
            manual_mode()
        elif choice == "2":
            print("Waiting for coin...")
            last_state = 0
            while True:
                state = GPIO.input(PIN_COIN)
                if state == 1 and last_state == 0:
                    auto_mode()
                last_state = state
                time.sleep(0.05)
        else:
            print("Invalid selection")
    finally:
        stop_all()
        cleanup()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
