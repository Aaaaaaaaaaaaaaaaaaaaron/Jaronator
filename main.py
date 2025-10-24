#!/usr/bin/env python3
import sys
import signal
import time
import os
import tkinter as tk
from PIL import Image, ImageTk
import Hobot.GPIO as GPIO
import select

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
#PIN_GRIP2 = 16
PIN_COIN = 37
# Stop-taster (aktiv LOW)
PIN_STOP_X_LEFT = 31
PIN_STOP_Y_FORWARD = 29
PIN_STOP_X_RIGHT = 26
PIN_STOP_Z_UP = 36
PIN_STOP_Z_DOWN = 16 


ALL_PINS = [
    PIN_X_IN1, PIN_X_IN2, PIN_Y_IN1, PIN_Y_IN2,
    PIN_Z_UP, PIN_Z_DOWN, PIN_GRIP, #PIN_GRIP2
]

# Zustandsvariablen
grip_state = False
block_x_left = False
block_x_right = False
block_y_forward = False
block_z_up = False
block_z_down = False

_counter = 0
_COUNTER_MIN = 0
_COUNTER_MAX = 9
_BLOCK_THRESHOLD = 9
_UNLOCK_THRESHOLD = 8

# ========================
# GPIO / Bewegungsfunktionen
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
    global _counter
    check_stop_buttons()
    if direction == "right" and _counter >= _BLOCK_THRESHOLD:
        print("X BACKWARD blockiert!")
        return
    if direction == "left" and block_x_left:
        print("X FORWARD blockiert!")
        return
    stop_all()
    if direction == "left":
        GPIO.output(PIN_X_IN1, GPIO.HIGH)
    elif direction == "right":
        GPIO.output(PIN_X_IN2, GPIO.HIGH)
    time.sleep(duration)
    stop_all()

def move_y(direction, duration=0.2):
    check_stop_buttons()
    if direction == "forward" and block_y_forward:
        print("Y LEFT blockiert!")
        return
    if direction == "backward" and block_x_right :
        print("Y RIGHT blockiert!")
        return
    stop_all()
    if direction == "forward":
        GPIO.output(PIN_Y_IN1, GPIO.HIGH)
    elif direction == "backward":
        GPIO.output(PIN_Y_IN2, GPIO.HIGH)
    time.sleep(duration)
    stop_all()

def move_z(direction, duration=0.2):
    stop_all()
    check_stop_buttons()
    if direction == "up"and not block_z_up:
        GPIO.output(PIN_Z_UP, GPIO.HIGH)
    elif direction == "down" and not block_z_down:
        GPIO.output(PIN_Z_DOWN, GPIO.HIGH)
    time.sleep(duration)
    stop_all()

def toggle_grip():
    global grip_state
    grip_state = not grip_state
    GPIO.output(PIN_GRIP, GPIO.HIGH if grip_state else GPIO.LOW)
    #GPIO.output(PIN_GRIP2, GPIO.HIGH if grip_state else GPIO.LOW)
    print("Grip HIGH" if grip_state else "Grip LOW")

def arm_setup():
    global _counter
    while not block_x_left:
        move_x("left", 0.25)
        check_stop_buttons()
        _counter = 0
        time.sleep(0.005)

def check_stop_buttons():
    global block_x_left, block_x_right, block_y_forward, block_z_up, block_z_down
    x_left = GPIO.input(PIN_STOP_X_LEFT)
    y_forward = GPIO.input(PIN_STOP_Y_FORWARD)
    x_right = GPIO.input(PIN_STOP_X_RIGHT)
    z_up = GPIO.input(PIN_STOP_Z_UP)
    z_down = GPIO.input(PIN_STOP_Z_DOWN)
    block_x_left = (x_left == 0)
    block_y_forward = (y_forward == 0)
    block_x_right = (x_right == 0)
    block_z_up = (z_up == 0)
    block_z_down = (z_down == 0)


# ========================
# Modi
# ========================
def manual_mode():
    global _counter
    print("\nManual mode active (Touchscreen oder Konsole)")
    arm_setup()
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
                if _counter > _COUNTER_MIN:
                    _counter -= 1
            elif key == "s":
                if _counter < _BLOCK_THRESHOLD:
                    move_x("right")
                    _counter += 1
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
# GUI-Klasse
# ========================
class GripperGUI:
    def __init__(self):
        signal.signal(signal.SIGINT, signal_handler)
        self.setup_gpio()
        self.window = tk.Tk()
        self.window.title("Gripper Control Menu")
        self.window.geometry("960x540")
        self.bg = None
        bg_path = "/app/jaronator/background/"
        bg_file = None
        if os.path.isdir(bg_path):
            for file in os.listdir(bg_path):
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    bg_file = os.path.join(bg_path, file)
                    break
        if bg_file:
            img = Image.open(bg_file)
            img = img.resize((960, 540))
            self.bg = ImageTk.PhotoImage(img)
            bg_label = tk.Label(self.window, image=self.bg)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        else:
            self.window.configure(bg="#202020")
        arm_setup()
        self.show_main_menu()
        self.window.mainloop()

    def _decrement_counter(self):
        global _counter
        if _counter > _COUNTER_MIN:
            _counter -= 1

    def _increment_counter(self):
        global _counter
        if _counter < _BLOCK_THRESHOLD:
            _counter += 1

    def setup_gpio(self):
        #GPIO.cleanup()
        GPIO.setmode(GPIO.BOARD)
        for p in ALL_PINS:
            GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_COIN, GPIO.IN)
        GPIO.setup(PIN_STOP_X_LEFT, GPIO.IN)
        GPIO.setup(PIN_STOP_Y_FORWARD, GPIO.IN)
        GPIO.setup(PIN_STOP_X_RIGHT, GPIO.IN)
        GPIO.setup(PIN_STOP_Z_UP, GPIO.IN)
        GPIO.setup(PIN_STOP_Z_DOWN, GPIO.IN)

    def clear_window(self):
        for widget in self.window.winfo_children():
            widget.destroy()

    def arm_setup(self):
        global _counter
        _counter = 0
        while not block_x_left:
            move_x("left", 0.25)
            check_stop_buttons()
            time.sleep(0.005)

    def show_main_menu(self):
        self.clear_window()
        if self.bg:
            bg_label = tk.Label(self.window, image=self.bg)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        else:
            self.window.configure(bg="#202020")
        btn_font = ("Arial", 14)
        tk.Label(self.window, text="Gripper Control - Hauptmenue", font=("Arial", 18), bg="#202020", fg="white").pack(pady=40)
        tk.Button(self.window, text="Automatik Mode", width=20, height=2, font=btn_font, command=self.start_auto_mode).pack(pady=10)
        tk.Button(self.window, text="Kamera Mode (Coming Soon)", width=20, height=2, font=btn_font, command=self.start_camera_mode).pack(pady=10)
        tk.Button(self.window, text="Manual Mode", width=20, height=2, font=btn_font, command=self.start_manual_mode).pack(pady=10)
        tk.Button(self.window, text="EXIT", width=20, height=2, font=btn_font, fg="red", command=self.exit_program).pack(pady=40)

    def show_mode_screen(self, mode_name, start_function):
        self.clear_window()
        if self.bg:
            bg_label = tk.Label(self.window, image=self.bg)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        else:
            self.window.configure(bg="#202020")
        tk.Label(self.window, text=mode_name, font=("Arial", 18), bg="#202020", fg="white").pack(pady=30)
        tk.Button(self.window, text="Start", width=20, height=2, font=("Arial", 14), command=start_function).pack(pady=10)
        tk.Button(self.window, text="Zurueck zum Menu", width=20, height=2, font=("Arial", 14), command=self.show_main_menu).pack(pady=20)
        tk.Button(self.window, text="EXIT", width=20, height=2, font=("Arial", 14), fg="red", command=self.exit_program).pack(pady=40)

    # >>> start_auto_mode ist Kopie von start_manual_mode mit Zwischenbildschirm und Coin-Wartefunktion <<<
    def start_auto_mode(self):
        self.show_mode_screen("Automatik Mode", self.run_auto_as_manual)

    def start_manual_mode(self):
        self.show_mode_screen("Manual Mode", self.run_manual_mode)

    def start_camera_mode(self):
        self.show_mode_screen("Kamera Mode", lambda: print("Kamera Mode folgt spaeter."))

    def run_auto_mode(self):
        self.clear_window()
        tk.Label(self.window, text="Automatik laeuft...", font=("Arial", 16), bg="#202020", fg="white").pack(pady=30)
        self.window.update()
        run_manual_mode()

    def run_manual_mode(self):
        self.clear_window()
        tk.Label(self.window, text="Manual Mode aktiv", font=("Arial", 18), bg="#202020", fg="white").pack(pady=10)
        btn_font = ("Arial", 14)
        frame = tk.Frame(self.window, bg="#202020")
        frame.pack(pady=10)
        tk.Button(frame, text="Left", width=10, height=2, font=btn_font, command=lambda: move_y("forward")).grid(row=1, column=0, padx=10, pady=10)
        tk.Button(frame, text="Right", width=10, height=2, font=btn_font, command=lambda: move_y("backward")).grid(row=1, column=2, padx=10, pady=10)
        tk.Button(frame, text="Forward", width=10, height=2, font=btn_font, command=lambda: [move_x("left"), self._decrement_counter()]).grid(row=0, column=1, padx=10, pady=10)
        tk.Button(frame, text="Backward", width=10, height=2, font=btn_font, command=lambda: [move_x("right"), self._increment_counter()]).grid(row=2, column=1, padx=10, pady=10)
        tk.Button(frame, text="Up", width=10, height=2, font=btn_font, command=lambda: move_z("up")).grid(row=0, column=3, padx=10, pady=10)
        tk.Button(frame, text="Down", width=10, height=2, font=btn_font, command=lambda: move_z("down")).grid(row=2, column=3, padx=10, pady=10)
        tk.Button(frame, text="Grip", width=10, height=2, font=btn_font, command=toggle_grip).grid(row=1, column=3, padx=10, pady=10)
        tk.Button(self.window, text="Zurueck", width=20, height=2, font=btn_font, command=self.show_main_menu).pack(pady=20)
        tk.Button(self.window, text="EXIT", width=20, height=2, font=btn_font, fg="red", command=self.exit_program).pack(pady=10)

    # >>> NEU: run_auto_as_manual mit Zwischenbildschirm und Coin-Wartefunktion <<<
    def run_auto_as_manual(self):
        global _counter
        self.clear_window()
        tk.Label(self.window, text="Automatik Mode - Warte auf Coin...", font=("Arial", 16), bg="#202020", fg="white").pack(pady=20)
        btn_font = ("Arial", 14)
        tk.Button(self.window, text="Zurueck zum Menu", width=20, height=2, font=btn_font, command=self.show_main_menu).pack(pady=10)
        self.window.update()
        # Warten auf Coin Detection (negative Flanke)
        while GPIO.input(PIN_COIN) != 0:
            self.window.update()
            time.sleep(0.05)
        # Coin erkannt, Buttons freigegeben
        tk.Label(self.window, text="Coin erkannt - Automatik startet!", font=("Arial", 16), bg="#202020", fg="white").pack(pady=10)
        self.window.update()
        while True:
            #gleicher code wie manuel mode hier rein:
            #self.clear_window()
            tk.Label(self.window, text="Manual Mode aktiv", font=("Arial", 18), bg="#202020", fg="white").pack(pady=10)
            btn_font = ("Arial", 14)
            frame = tk.Frame(self.window, bg="#202020")
            frame.pack(pady=10)
            tk.Button(frame, text="Left", width=10, height=2, font=btn_font, command=lambda: move_y("forward")).grid(row=1, column=0, padx=10, pady=10)
            tk.Button(frame, text="Right", width=10, height=2, font=btn_font, command=lambda: move_y("backward")).grid(row=1, column=2, padx=10, pady=10)
            tk.Button(frame, text="Forward", width=10, height=2, font=btn_font, command=lambda: [move_x("left"), self._decrement_counter()]).grid(row=0, column=1, padx=10, pady=10)
            tk.Button(frame, text="Backward", width=10, height=2, font=btn_font, command=lambda: [move_x("right"), self._increment_counter()]).grid(row=2, column=1, padx=10, pady=10)
            tk.Button(frame, text="Up", width=10, height=2, font=btn_font, command=lambda: move_z("up")).grid(row=0, column=3, padx=10, pady=10)
            tk.Button(frame, text="Down", width=10, height=2, font=btn_font, command=lambda: move_z("down")).grid(row=2, column=3, padx=10, pady=10)
            tk.Button(frame, text="Grip", width=10, height=2, font=btn_font, command=toggle_grip).grid(row=1, column=3, padx=10, pady=10)
            tk.Button(self.window, text="ZurÃ¼ck", width=20, height=2, font=btn_font, command=self.show_main_menu).pack(pady=20)
            tk.Button(self.window, text="EXIT", width=20, height=2, font=btn_font, fg="red", command=self.exit_program).pack(pady=10)
            
            
            self.window.update()
            # Wechsel zum Zwischenbildschirm, falls Grip betatigt
            if grip_state:
                self.clear_window()
                while not block_z_up:
                    move_x("up")
                while not _counter == 9:
                    move_x("right")
                    self._increment_counter()
                while not block_y_forward:
                    move_y("forward")
                
                
                toggle_grip()
                tk.Label(self.window, text="Danke fÃ¼rs Spielen- Warte auf neuen Coin...", font=("Arial", 16), bg="#202020", fg="white").pack(pady=20)
                tk.Button(self.window, text="Zurueck zum Menu", width=20, height=2, font=btn_font, command=self.show_main_menu).pack(pady=10)
                self.window.update()
                # <<< Ende Zwischenbildschirm - warte auf Coin Detection >>> 
                while GPIO.input(PIN_COIN) != 0:
                    self.window.update()
                    time.sleep(0.05)
                tk.Label(self.window, text="Neuer Coin erkannt - Automatik setzt fort!", font=("Arial", 16), bg="#202020", fg="white").pack(pady=10)
                self.window.update()

    # ===================================================
    def exit_program(self):
        stop_all()
        cleanup()
        self.window.destroy()

# ========================
# Start GUI
# ========================
if __name__ == "__main__":
    GripperGUI()
