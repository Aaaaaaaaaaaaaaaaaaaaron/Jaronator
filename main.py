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
    if direction == "up" and not block_z_up:
        GPIO.output(PIN_Z_UP, GPIO.HIGH)
    elif direction == "down" and not block_z_down:
        GPIO.output(PIN_Z_DOWN, GPIO.HIGH)
    time.sleep(duration)
    stop_all()

def toggle_grip():
    global grip_state
    grip_state = not grip_state
    GPIO.output(PIN_GRIP, GPIO.HIGH if grip_state else GPIO.LOW)
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
# GUI-Klasse
# ========================
class GripperGUI:
    def __init__(self):
        signal.signal(signal.SIGINT, signal_handler)
        self.setup_gpio()
        self.window = tk.Tk()
        self.window.title("Gripper Control Menu")
        self.window.geometry("1920x1080")
        self.bg = None
        self.bg_label = None  # persistent background
        self.load_background()
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
        GPIO.setmode(GPIO.BOARD)
        for p in ALL_PINS:
            GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_COIN, GPIO.IN)
        GPIO.setup(PIN_STOP_X_LEFT, GPIO.IN)
        GPIO.setup(PIN_STOP_Y_FORWARD, GPIO.IN)
        GPIO.setup(PIN_STOP_X_RIGHT, GPIO.IN)
        GPIO.setup(PIN_STOP_Z_UP, GPIO.IN)
        GPIO.setup(PIN_STOP_Z_DOWN, GPIO.IN)

    def load_background(self):
        bg_path = "/app/jaronator/background/"
        bg_file = None
        if os.path.isdir(bg_path):
            for file in os.listdir(bg_path):
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    bg_file = os.path.join(bg_path, file)
                    break
        if bg_file:
            img = Image.open(bg_file)
            img = img.resize((1920, 1080))
            self.bg = ImageTk.PhotoImage(img)
            if self.bg_label is None:
                self.bg_label = tk.Label(self.window, image=self.bg)
                self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            else:
                self.bg_label.configure(image=self.bg)
        else:
            self.window.configure(bg="#202020")

    def clear_window(self):
        # nur Widgets lÃ¶schen, Hintergrund bleibt
        for widget in self.window.winfo_children():
            if widget != self.bg_label:
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
        btn_font = ("Noto Sans Display", 18, "bold")
        tk.Button(self.window, text="Automatik Mode", width=30, height=3, font=btn_font, bg="black", fg="white", command=self.start_auto_mode).place(x=772, y=130)
        tk.Button(self.window, text="Kamera Mode", width=30, height=3, font=btn_font, bg="black", fg="white", command=self.start_camera_mode).place(x=772, y=330)
        tk.Button(self.window, text="Manual Mode", width=30, height=3, font=btn_font, bg="black", fg="white", command=self.start_manual_mode).place(x=772, y=530)
        tk.Button(self.window, text="EXIT", width=20, height=2, font=("Noto Sans Display", 18, "bold"), fg="red", bg="black", command=self.exit_program).place(relx=1.0, rely=1.0, anchor="se", x=-150, y=-150)

    def show_mode_screen(self, mode_name, start_function):
        self.clear_window()
        tk.Label(self.window, text=mode_name, width=30, height=3, font=("Noto Sans Display", 18, "bold"), bg="black", fg="white").place(x=772, y=130)
        tk.Button(self.window, text="Start", width=30, height=3, font=("Noto Sans Display", 18, "bold"), bg="black", fg="white", command=start_function).place(x=772, y=330)
        tk.Button(self.window, text="Zurueck zum Menu", width=30, height=3, font=("Noto Sans Display", 18, "bold"), bg="black", fg="white", command=self.show_main_menu).place(x=772, y=530)
        tk.Button(self.window, text="EXIT", width=20, height=2, font=("Noto Sans Display", 18, "bold"), fg="red", bg="black", command=self.exit_program).place(relx=1.0, rely=1.0, anchor="se", x=-150, y=-150)

    def start_auto_mode(self):
        self.show_mode_screen("Automatik Mode", self.run_auto_as_manual)

    def start_manual_mode(self):
        self.show_mode_screen("Manual Mode", self.run_manual_mode)

    def start_camera_mode(self):
        self.show_mode_screen("Kamera Mode", lambda: print("Kamera Mode folgt spaeter."))

    def run_manual_mode(self):
        self.clear_window()
        tk.Label(self.window, text="Manual Mode aktiv", width=30, height=2, anchor="center", font=("Noto Sans Display", 18, "bold"), bg="black", fg="white").place(x=100, y=100)
        btn_font = ("Noto Sans Display", 14, "bold")
        tk.Button(self.window, text="Left", width=30, height=3, font=btn_font, bg="black", fg="white", command=lambda: move_y("forward")).place(x=520, y=250)
        tk.Button(self.window, text="Right", width=30, height=3, font=btn_font, bg="black", fg="white", command=lambda: move_y("backward")).place(x=1120, y=250)
        tk.Button(self.window, text="Forward", width=30, height=3, font=btn_font, bg="black", fg="white", command=lambda: [move_x("left"), self._decrement_counter()]).place(x=820, y=100)
        tk.Button(self.window, text="Backward", width=30, height=3, font=btn_font, bg="black", fg="white", command=lambda: [move_x("right"), self._increment_counter()]).place(x=820, y=400)
        tk.Button(self.window, text="Up", width=30, height=3, font=btn_font, bg="black", fg="white", command=lambda: move_z("up")).place(x=1500, y=100)
        tk.Button(self.window, text="Down", width=30, height=3, font=btn_font, bg="black", fg="white", command=lambda: move_z("down")).place(x=1500, y=400)
        tk.Button(self.window, text="Grip", width=30, height=3, font=btn_font, bg="black", fg="white", command=toggle_grip).place(x=1500, y=250)
        tk.Button(self.window, text="Zurueck", width=30, height=3, font=btn_font, bg="black", fg="white", command=self.show_main_menu).place(x=820, y=750)
        tk.Button(self.window, text="EXIT", width=20, height=2, font=("Noto Sans Display", 18, "bold"), fg="red", bg="black", command=self.exit_program).place(relx=1.0, rely=1.0, anchor="se", x=-100, y=-100)

    def run_auto_as_manual(self):
        global _counter
        self.clear_window()
        tk.Label(self.window, text="Automatik Mode - Warte auf Coin...", font=("Noto Sans Display", 18, "bold"), bg="black", fg="white").pack(pady=20)
        tk.Button(self.window, text="Zurueck zum Menu", width=20, height=2, font=("Noto Sans Display", 18, "bold"), bg="black", fg="white", command=self.show_main_menu).pack(pady=10)
        self.window.update()
        # Warten auf Coin
        last_state = GPIO.input(PIN_COIN)
        while True:
            current_state = GPIO.input(PIN_COIN)
            if last_state == 0 and current_state == 1:
                print("Positive Flanke erkannt")
                break
            last_state = current_state
            self.window.update()
            time.sleep(0.05)
        tk.Label(self.window, text="Coin erkannt - Automatik startet!", font=("Noto Sans Display", 18, "bold"), bg="black", fg="white").pack(pady=10)
        
        self.window.update()
        time.sleep(3)
        
        
        
        self.clear_window()
        btn_font = ("Noto Sans Display", 14, "bold")
        tk.Button(self.window, text="Left",  width=30, height=3, font=btn_font, bg="black", fg="white", bd=0, highlightthickness=0, command=lambda: move_y("forward")).place(x=520, y=250)
        tk.Button(self.window, text="Right",  width=30, height=3, font=btn_font, bg="black", fg="white", bd=0, highlightthickness=0, command=lambda: move_y("backward")).place(x=1120, y=250)
        tk.Button(self.window, text="Forward",  width=30, height=3, font=btn_font, bg="black", fg="white", bd=0, highlightthickness=0, command=lambda: [move_x("left"), self._decrement_counter()]).place(x=820, y=100)
        tk.Button(self.window, text="Backward",  width=30, height=3, font=btn_font, bg="black", fg="white", bd=0, highlightthickness=0, command=lambda: [move_x("right"), self._increment_counter()]).place(x=820, y=400)
        tk.Button(self.window, text="Up",  width=30, height=3, font=btn_font, bg="black", fg="white", bd=0, highlightthickness=0, command=lambda: move_z("up")).place(x=1500, y=100)
        tk.Button(self.window, text="Down",  width=30, height=3, font=btn_font, bg="black", fg="white", bd=0, highlightthickness=0, command=lambda: move_z("down")).place(x=1500, y=400)
        tk.Button(self.window, text="Grip",  width=30, height=3, font=btn_font, bg="black", fg="white", bd=0, highlightthickness=0, command=toggle_grip).place(x=1500, y=250)
        tk.Button(self.window, text="Zurueck", width=30, height=3, font=btn_font, bg="black", fg="white", bd=0, highlightthickness=0, command=self.show_main_menu).place(x=820, y=750)
        tk.Button(self.window, text="EXIT", width=20, height=2, font=("Noto Sans Display", 18, "bold"), fg="red", bg="black", bd=0, highlightthickness=0, command=self.exit_program).place(relx=1.0, rely=1.0, anchor="se", x=-100, y=-100)
           
        while True:
         #gleicher code wie manuel mode hier rein:
            #self.clear_window()
            # Steuerbuttons genau wie in run_auto_as_manual

            
            self.window.update()
            # Wechsel zum Zwischenbildschirm, falls Grip betatigt
            if grip_state:
                self.clear_window()
                self.window.update()
                while not block_z_up:
                    move_z("up")
                while not _counter == 9:
                    move_x("right")
                    self._increment_counter()
                while not block_y_forward:
                    move_y("forward")
                
                
                toggle_grip()
                tk.Label(self.window, text="Danke fÃ¼rs Spielen", font=("Noto Sans Display", 18, "bold"), bg="black", fg="white").pack(pady=20)
                tk.Button(self.window, text="ZurÃ¼ck zum Menu", width=30, height=3, font=("Noto Sans Display", 18, "bold"),bg="black", fg="white", command=self.show_main_menu).pack(pady=10)
                self.window.update()
                break
                #break
        
        

    def exit_program(self):
        stop_all()
        cleanup()
        self.window.destroy()

# ========================
# Start GUI
# ========================
if __name__ == "__main__":
    GripperGUI()
