#!/usr/bin/env python3
import sys
import signal
import time
import Hobot.GPIO as GPIO

# ========================
# Pin configuration (BOARD numbering)
# ========================
PIN_X_IN1  = 7   # green (togehter with other cable)
PIN_X_IN2  = 11  # yellow
PIN_GRIP   = 12  # orange 
PIN_Y_IN2  = 13  # red    
PIN_Z_UP   = 15  # brown
PIN_Z_DOWN = 16  # black
PIN_Y_IN1  = 18  # white 
PIN_GRIP2  = 22  # green (alone cable) 

ALL_PINS = [
    PIN_X_IN1, PIN_X_IN2,
    PIN_Y_IN1, PIN_Y_IN2,
    PIN_Z_UP,  PIN_Z_DOWN,
    PIN_GRIP,  PIN_GRIP2
]

# Track grip state
grip_state = False   # False = LOW (open), True = HIGH (closed)

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
    if direction == "hin":   # towards outfeed
        GPIO.output(PIN_X_IN1, GPIO.HIGH)
    elif direction == "weg": # away from outfeed
        GPIO.output(PIN_X_IN2, GPIO.HIGH)
    time.sleep(duration)
    stop_all()

def move_y(direction, duration=0.5):
    stop_all()
    if direction == "weg":   # away from outfeed
        GPIO.output(PIN_Y_IN1, GPIO.HIGH)
    elif direction == "hin": # towards outfeed
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
    print("Keys: w=y weg  s=y hin  a=x hin  d=x weg  x=z-axis  g=grip  q=quit")
    while True:
        key = input(">> ").strip().lower()
        if key == "q":
            stop_all()
            break
        elif key == "w":
            move_y("weg")
        elif key == "s":
            move_y("hin")
        elif key == "a":
            move_x("hin")
        elif key == "d":
            move_x("weg")
        elif key == "x":
            # Down if grip LOW, Up if grip HIGH
            if grip_state:
                move_z("up")
            else:
                move_z("down")
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

    print("Gripper control with Z axis")
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
