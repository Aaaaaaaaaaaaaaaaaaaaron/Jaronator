#!/usr/bin/env python3
import sys
import signal
import time
import Hobot.GPIO as GPIO
import tkinter as tk

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
    if direction == "hin":
        GPIO.output(PIN_X_IN1, GPIO.HIGH)
    elif direction == "weg":
        GPIO.output(PIN_X_IN2, GPIO.HIGH)
    time.sleep(duration)
    stop_all()

def move_y(direction, duration=0.5):
    stop_all()
    if direction == "weg":
        GPIO.output(PIN_Y_IN1, GPIO.HIGH)
    elif direction == "hin":
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
            move_y("weg")
        elif key == "s":
            move_y("hin")
        elif key == "a":
            move_x("hin")
        elif key == "d":
            move_x("weg")
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
    print("\nAuto mode placeholder for future ROS2 integration")

# ========================
def gui_mode():
    window = tk.Tk()
    window.title("Gripper Control GUI")
    window.geometry("400x400")
    window.configure(bg="#202020")

    def btn_move_y_weg():
        move_y("weg")

    def btn_move_y_hin():
        move_y("hin")

    def btn_move_x_hin():
        move_x("hin")

    def btn_move_x_weg():
        move_x("weg")

    def btn_z_axis():
        if grip_state:
            move_z("up")
        else:
            move_z("down")

    def btn_grip():
        toggle_grip()

    def btn_quit():
        stop_all()
        cleanup()
        window.destroy()

    tk.Label(window, text="Gripper Control", font=("Arial", 16), fg="white", bg="#202020").pack(pady=10)

    frame = tk.Frame(window, bg="#202020")
    frame.pack(pady=20)

    btn_font = ("Arial", 14)

    tk.Button(frame, text="Y weg (W)", width=12, height=2, command=btn_move_y_weg, font=btn_font).grid(row=0, column=1, padx=5, pady=5)
    tk.Button(frame, text="X hin (A)", width=12, height=2, command=btn_move_x_hin, font=btn_font).grid(row=1, column=0, padx=5, pady=5)
    tk.Button(frame, text="STOP", width=12, height=2, command=stop_all, font=btn_font, fg="red").grid(row=1, column=1, padx=5, pady=5)
    tk.Button(frame, text="X weg (D)", width=12, height=2, command=btn_move_x_weg, font=btn_font).grid(row=1, column=2, padx=5, pady=5)
    tk.Button(frame, text="Y hin (S)", width=12, height=2, command=btn_move_y_hin, font=btn_font).grid(row=2, column=1, padx=5, pady=5)

    tk.Button(window, text="Z-Achse (X)", width=16, height=2, command=btn_z_axis, font=btn_font).pack(pady=5)
    tk.Button(window, text="Grip (G)", width=16, height=2, command=btn_grip, font=btn_font).pack(pady=5)
    tk.Button(window, text="QUIT", width=16, height=2, command=btn_quit, font=btn_font, fg="red").pack(pady=10)

    window.mainloop()

# ========================
def main():
    GPIO.setmode(GPIO.BOARD)
    for p in ALL_PINS:
        GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)

    print("Gripper control with Z axis")
    print("1) Manual mode")
    print("2) Auto mode (ROS2 placeholder)")
    print("3) GUI mode")
    choice = input("Select mode (1/2/3): ").strip()

    try:
        if choice == "1":
            manual_mode()
        elif choice == "2":
            auto_mode()
        elif choice == "3":
            gui_mode()
        else:
            print("Invalid selection")
    finally:
        stop_all()
        cleanup()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
