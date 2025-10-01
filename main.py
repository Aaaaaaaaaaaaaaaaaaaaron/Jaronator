#!/usr/bin/env python3
import sys
import signal
import time
import Hobot.GPIO as GPIO

# ========================
# Pin configuration (BOARD numbering)
# ========================
PIN_X_IN1  = 22
PIN_X_IN2  = 23
PIN_Y_IN1  = 24
PIN_Y_IN2  = 25
PIN_Z_UP   = 29   # <<< anpassen
PIN_Z_DOWN = 31   # <<< anpassen
PIN_GRIP   = 7
PIN_GRIP2  = 16   # optional zweiter Pin
PIN_COIN   = 18   # <<< Coin-Sensor (Input)

ALL_OUT_PINS = [
    PIN_X_IN1, PIN_X_IN2,
    PIN_Y_IN1, PIN_Y_IN2,
    PIN_Z_UP,  PIN_Z_DOWN,
    PIN_GRIP,  PIN_GRIP2
]

# Grip state
grip_state = False

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

def move_x(direction, duration=0.5):
    stop_all()
    if direction == "left":
        GPIO.output(PIN_X_IN1, GPIO.HIGH)
    elif direction == "right":
        GPIO.output(PIN_X_IN2, GPIO.HIGH)
    time.sleep(duration)
    stop_all()

def move_y(direction, duration=0.5):
    stop_all()
    if direction == "forward":
        GPIO.output(PIN_Y_IN1, GPIO.HIGH)
    elif direction == "backward":
        GPIO.output(PIN_Y_IN2, GPIO.HIGH)
    time.sleep(duration)
    stop_all()

def move_z(direction, duration=0.5):
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
    GPIO.output(PIN_GRIP,  GPIO.HIGH if grip_state else GPIO.LOW)
    GPIO.output(PIN_GRIP2, GPIO.HIGH if grip_state else GPIO.LOW)
    print("Grip HIGH" if grip_state else "Grip LOW")

# ========================
def manual_mode():
    print("\nManual mode active")
    print("Keys: w=forward s=back a=left d=right x=z-axis g=grip q=quit")
    while True:
        key = input(">> ").strip().lower()
        if key == "q":
            stop_all()
            break
        elif key == "w":
            move_y("forward")
        elif key == "s":
            move_y("backward")
        elif key == "a":
            move_x("left")
        elif key == "d":
            move_x("right")
        elif key == "x":
            if grip_state:
                move_z("up")
            else:
                move_z("down")
        elif key == "g":
            toggle_grip()
        else:
            print("Invalid input")

def auto_mode():
    print("\nAuto mode selected.")
    print("Waiting for coin... (insert to start)")
    # Warten bis Muenze erkannt wird
    while True:
        if GPIO.input(PIN_COIN) == GPIO.HIGH:
            print("Coin detected! Auto mode starting...")
            break
        time.sleep(0.1)

    # Placeholder for ROS2 / Automat
    for i in range(3):
        print(f"Auto mode step {i+1}")
        move_x("right")
        move_y("forward")
        toggle_grip()
    print("Auto mode finished.")

# ========================
def main():
    GPIO.setmode(GPIO.BOARD)

    # Outputs
    for p in ALL_OUT_PINS:
        GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)

    # Coin input
    GPIO.setup(PIN_COIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    print("Gripper control with coin input")
    print("1) Manual mode")
    print("2) Auto mode (needs coin)")
    choice = input("Select mode (1/2): ").strip()

    try:
        if choice == "1":
            manual_mode()
        elif choice == "2":
            auto_mode()
        else:
            print("Invalid selection")
    finally:
        stop_all()
        cleanup()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
