#!/usr/bin/env python3
import sys
import signal
import time
import Hobot.GPIO as GPIO

# ========================
# Pin configuration (BOARD numbering)
# ========================
PIN_X_IN1 = 11
PIN_X_IN2 = 12
PIN_Y_IN1 = 13
PIN_Y_IN2 = 15
PIN_GRIP  = 7   # gripper open/close
PIN_GRIP2  = 16
ALL_PINS = [PIN_X_IN1, PIN_X_IN2, PIN_Y_IN1, PIN_Y_IN2, PIN_GRIP, PIN_GRIP2]

# Track grip state ourselves
grip_state = False   # False = LOW, True = HIGH

# ========================
def cleanup():
    GPIO.cleanup()
    print("GPIO cleaned up")

def signal_handler(sig, frame):
    cleanup()
    sys.exit(0)

def stop_all():
    GPIO.output(PIN_X_IN1, GPIO.LOW)
    GPIO.output(PIN_X_IN2, GPIO.LOW)
    GPIO.output(PIN_Y_IN1, GPIO.LOW)
    GPIO.output(PIN_Y_IN2, GPIO.LOW)

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
    if direction == "up":
        GPIO.output(PIN_Y_IN1, GPIO.HIGH)
    elif direction == "down":
        GPIO.output(PIN_Y_IN2, GPIO.HIGH)
    time.sleep(duration)
    stop_all()

def toggle_grip():
    global grip_state
    grip_state = not grip_state
    GPIO.output(PIN_GRIP, GPIO.HIGH if grip_state else GPIO.LOW)
    GPIO.output(PIN_GRIP2, GPIO.HIGH if grip_state else GPIO.LOW)
    print("Grip HIGH" if grip_state else "Grip LOW")

# ========================
def manual_mode():
    print("\nManual mode active")
    print("Keys: w=up s=down a=left d=right g=grip q=quit")
    while True:
        key = input(">> ").strip().lower()
        if key == "q":
            stop_all()
            break
        elif key == "w":
            move_y("up")
        elif key == "s":
            move_y("down")
        elif key == "a":
            move_x("left")
        elif key == "d":
            move_x("right")
        elif key == "g":
            toggle_grip()
        else:
            print("Invalid input")

def auto_mode():
    print("\nAuto mode placeholder for future ROS2 integration")

# ========================
def main():
    GPIO.setmode(GPIO.BOARD)
    for p in ALL_PINS:
        GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)

    print("Gripper control")
    print("1) Manual mode")
    print("2) Auto mode (ROS2 placeholder)")
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
