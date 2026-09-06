#!/usr/bin/env python3
"""
ExpirioBot - Windows Version without Tesseract requirement
This version allows manual date input for testing
"""

import cv2
import re
from datetime import datetime
import threading
import queue
import time
import tkinter as tk
from tkinter import Label, Entry, messagebox
from PIL import Image, ImageTk

# Mock Arm Device for Windows (without physical hardware)
class MockArmDevice:
    def __init__(self):
        print("⚠️  Mock Arm Device initialized (no physical arm connected)")
        
    def Arm_serial_servo_write(self, servo_id, position, duration):
        print(f"[MOCK ARM] Servo {servo_id} -> Position {position} (Duration: {duration}ms)")
    
    def __del__(self):
        print("Mock Arm Device cleaned up")

# Initialize the mock robotic arm
Arm = MockArmDevice()
time.sleep(0.1)

# Arm movement functions
def arm_clamp_block(enable):
    """Controls the robotic arm clamp to either hold or release an object."""
    position = 100 if enable else 10
    print(f"[MOCK] Clamp: {'CLOSE' if enable else 'OPEN'}")
    Arm.Arm_serial_servo_write(6, position, 400)
    time.sleep(0.5)

def arm_move(positions, s_time=500):
    """Moves the robotic arm to specified positions."""
    print(f"[MOCK] Moving arm to positions: {positions}")
    for i, pos in enumerate(positions):
        servo_id = i + 1
        adjusted_time = (
            int(s_time * 1.2) if servo_id == 5 else
            int(3 * s_time / 4) if servo_id == 1 else
            int(s_time)
        )
        Arm.Arm_serial_servo_write(servo_id, pos, adjusted_time)
        time.sleep(0.01)
    time.sleep(s_time / 1000)

# Predefined arm positions
p_front = [90, 75, 0, 30, 90]
p_right = [0, 75, 0, 30, 90]
p_right_top = [0, 75, 0, 60, 90]
p_left_top = [180, 75, 0, 60, 90]
p_left = [180, 75, 0, 30, 90]
p_top = [90, 80, 50, 50, 90]
p_rest = [90, 90, 0, 5, 90]

# Last processed date to prevent redundant processing
last_processed_date = None

def move_object(target, expired_count, valid_count):
    """
    Moves an object to the specified target location (left or right).
    """
    try:
        if target not in ['left', 'right']:
            print("Invalid target! Use 'left' or 'right'.")
            return

        print(f"\n🤖 Moving object to: {target.upper()}")
        
        # Pick up the object
        arm_clamp_block(0)
        arm_move(p_front, 1000)
        arm_clamp_block(1)
        arm_move(p_top, 1000)

        # Move to the target
        if target == 'left':
            arm_move(p_left, 1000)
            arm_clamp_block(0)
            arm_move(p_left_top, 500)
            expired_count.set(expired_count.get() + 1)
        elif target == 'right':
            arm_move(p_right, 1000)
            arm_clamp_block(0)
            arm_move(p_right_top, 500)
            valid_count.set(valid_count.get() + 1)

        # Return to the rest position
        arm_move(p_top, 1000)
        arm_move(p_rest, 1000)
        print("✅ Movement complete!\n")
    except Exception as e:
        print(f"Error during arm movement: {e}")

def process_manual_date(date_str, expired_count, valid_count):
    """Process manually entered date"""
    global last_processed_date
    
    # Try to parse the date
    pattern = r'\b\d{2}[./]\d{2}[./]\d{4}\b'
    match = re.search(pattern, date_str)
    
    if not match:
        return False, "Invalid date format! Use DD/MM/YYYY or DD.MM.YYYY"
    
    expiry_date = match.group(0)
    try:
        formatted_date = expiry_date.replace('.', '/')
        expiry_date_obj = datetime.strptime(formatted_date, "%d/%m/%Y")
        today = datetime.today()
        
        if last_processed_date is None or last_processed_date != expiry_date_obj:
            last_processed_date = expiry_date_obj
            
            if expiry_date_obj < today:
                target = "left"
                message = f"❌ EXPIRED! Date: {expiry_date}\nMoving to LEFT"
                print(message)
                move_object(target, expired_count, valid_count)
            else:
                target = "right"
                message = f"✅ VALID! Date: {expiry_date}\nMoving to RIGHT"
                print(message)
                move_object(target, expired_count, valid_count)
            
            return True, message
        else:
            return False, "Date already processed!"
            
    except ValueError:
        return False, "Invalid date format. Use DD/MM/YYYY"

def main():
    """Main function to initialize the system and GUI."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open camera.")
        cap = None

    root = tk.Tk()
    root.title("ExpirioBot - Manual Date Entry Mode")
    root.configure(bg="#2e2e2e")
    root.geometry("700x600")

    # Title
    title_label = tk.Label(root, text="🤖 ExpirioBot Control Panel", 
                          font=("Comfortaa", 16, "bold"), bg="#2e2e2e", fg="white")
    title_label.pack(pady=10)

    # Warning label
    warning = tk.Label(root, text="⚠️ MOCK MODE - Manual Date Entry", 
                      font=("Comfortaa", 10), bg="#2e2e2e", fg="yellow")
    warning.pack()

    # Video feed
    video_label = Label(root, bg="#2e2e2e")
    video_label.pack(pady=10)

    # Counters
    counter_frame = tk.Frame(root, bg="#2e2e2e")
    counter_frame.pack(pady=10)

    expired_count = tk.IntVar(value=0)
    valid_count = tk.IntVar(value=0)

    # Expired counter
    expired_frame = tk.Frame(counter_frame, bg="#2e2e2e")
    expired_frame.grid(row=0, column=0, padx=20)
    
    expired_label = tk.Label(expired_frame, textvariable=expired_count, 
                            font=("Comfortaa", 24, "bold"), fg="red", bg="#2e2e2e")
    expired_label.pack()
    tk.Label(expired_frame, text="❌ Expired Products", 
            font=("Comfortaa", 12), bg="#2e2e2e", fg="white").pack()

    # Valid counter
    valid_frame = tk.Frame(counter_frame, bg="#2e2e2e")
    valid_frame.grid(row=0, column=1, padx=20)
    
    valid_label = tk.Label(valid_frame, textvariable=valid_count, 
                          font=("Comfortaa", 24, "bold"), fg="green", bg="#2e2e2e")
    valid_label.pack()
    tk.Label(valid_frame, text="✅ Valid Products", 
            font=("Comfortaa", 12), bg="#2e2e2e", fg="white").pack()

    # Manual input section
    input_frame = tk.Frame(root, bg="#2e2e2e")
    input_frame.pack(pady=20)

    tk.Label(input_frame, text="Enter Expiry Date:", 
            font=("Comfortaa", 12), bg="#2e2e2e", fg="white").grid(row=0, column=0, padx=5)
    
    date_entry = Entry(input_frame, font=("Comfortaa", 12), width=15)
    date_entry.grid(row=0, column=1, padx=5)
    date_entry.insert(0, "DD/MM/YYYY")

    def check_date():
        date_str = date_entry.get()
        success, message = process_manual_date(date_str, expired_count, valid_count)
        if success:
            messagebox.showinfo("Result", message)
            date_entry.delete(0, tk.END)
            date_entry.insert(0, "DD/MM/YYYY")
        else:
            messagebox.showerror("Error", message)

    check_button = tk.Button(input_frame, text="Check Date", command=check_date, 
                            bg="#4caf50", fg="white", font=("Comfortaa", 12), padx=10)
    check_button.grid(row=0, column=2, padx=5)

    # Instructions
    instructions = tk.Label(root, 
        text="📝 Enter expiry date in DD/MM/YYYY format (e.g., 25/12/2024)\n"
             "The system will check if it's expired and simulate arm movement",
        font=("Comfortaa", 9), bg="#2e2e2e", fg="#888888", justify="center")
    instructions.pack(pady=10)

    def update_frame():
        """Updates the GUI with the latest video frame from the camera."""
        if cap is not None:
            ret, frame = cap.read()
            if ret:
                # Resize for display
                frame = cv2.resize(frame, (400, 300))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                video_label.imgtk = imgtk
                video_label.configure(image=imgtk)
        root.after(10, update_frame)

    # Bind Enter key to check date
    date_entry.bind('<Return>', lambda e: check_date())

    update_frame()
    root.mainloop()
    
    if cap:
        cap.release()

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("🤖 ExpirioBot - Manual Date Entry Mode")
        print("=" * 60)
        print("✅ Camera working")
        print("✅ GUI ready")
        print("⚠️  No Tesseract required (manual input)")
        print("⚠️  Mock arm mode (no physical hardware)")
        print("=" * 60)
        print("\nEnter dates in format: DD/MM/YYYY")
        print("Example: 25/12/2024 or 25.12.2024\n")
        main()
    finally:
        del Arm
        print("\n✅ Program Ended")
