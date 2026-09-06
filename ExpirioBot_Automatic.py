#!/usr/bin/env python3
"""
ExpirioBot - Automatic Version with EasyOCR
Automatically detects expiry dates from camera using OCR
"""

import cv2
import easyocr
import re
from datetime import datetime
import threading
import queue
import time
import tkinter as tk
from tkinter import Label
from PIL import Image, ImageTk
import numpy as np

# Initialize EasyOCR Reader (English only for speed)
print("🔄 Loading EasyOCR model (first time may take 1-2 minutes)...")
reader = easyocr.Reader(['en'], gpu=False)
print("✅ EasyOCR loaded!")

# Mock Arm Device for Windows
class MockArmDevice:
    def __init__(self):
        print("⚠️  Mock Arm Device initialized (no physical arm connected)")
        
    def Arm_serial_servo_write(self, servo_id, position, duration):
        print(f"[MOCK ARM] Servo {servo_id} -> Position {position} (Duration: {duration}ms)")
    
    def __del__(self):
        print("Mock Arm Device cleaned up")

Arm = MockArmDevice()
time.sleep(0.1)

def arm_clamp_block(enable):
    """Controls the robotic arm clamp."""
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

# Arm positions
p_front = [90, 75, 0, 30, 90]
p_right = [0, 75, 0, 30, 90]
p_right_top = [0, 75, 0, 60, 90]
p_left_top = [180, 75, 0, 60, 90]
p_left = [180, 75, 0, 30, 90]
p_top = [90, 80, 50, 50, 90]
p_rest = [90, 90, 0, 5, 90]

last_processed_date = None
queue_lock = threading.Lock()

def move_object(target, processing_event, producer_allowed_event):
    """Moves object to left (expired) or right (valid)."""
    processing_event.clear()
    producer_allowed_event.clear()
    try:
        if target not in ['left', 'right']:
            print("Invalid target!")
            return

        print(f"\n🤖 Moving object to: {target.upper()}")
        
        arm_clamp_block(0)
        arm_move(p_front, 1000)
        arm_clamp_block(1)
        arm_move(p_top, 1000)

        if target == 'left':
            arm_move(p_left, 1000)
            arm_clamp_block(0)
            arm_move(p_left_top, 500)
        elif target == 'right':
            arm_move(p_right, 1000)
            arm_clamp_block(0)
            arm_move(p_right_top, 500)

        arm_move(p_top, 1000)
        arm_move(p_rest, 1000)
        print("✅ Movement complete!\n")
    except Exception as e:
        print(f"Error during arm movement: {e}")
    finally:
        producer_allowed_event.set()
        processing_event.set()

def preprocess_image(frame):
    """Preprocess frame for better OCR."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Apply adaptive thresholding for better text detection
    processed = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    return processed

def extract_expiry_date_easyocr(frame):
    """Extract expiry date using EasyOCR."""
    try:
        # Preprocess the image
        processed = preprocess_image(frame)
        
        # Perform OCR
        results = reader.readtext(processed, detail=0)
        
        # Combine all text
        text = " ".join(results)
        print(f"📝 Detected text: {text}")
        
        # Search for date patterns
        patterns = [
            r'\b\d{2}[./\-]\d{2}[./\-]\d{4}\b',  # DD/MM/YYYY
            r'\b\d{2}[./\-]\d{2}[./\-]\d{2}\b',   # DD/MM/YY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                expiry_date = match.group(0)
                print(f"✅ Expiry Date Found: {expiry_date}")
                return expiry_date
        
        print("❌ No expiry date found in text")
        return None
        
    except Exception as e:
        print(f"OCR Error: {e}")
        return None

def process_frames(frame_queue_container, processing_event, producer_allowed_event, 
                   expired_count, valid_count, status_label):
    """Process frames from queue to detect expiry dates."""
    global last_processed_date
    
    while True:
        processing_event.wait()
        with queue_lock:
            current_queue = frame_queue_container[0]

        if not current_queue.empty():
            frame = current_queue.get()
            
            status_label.config(text="🔍 Scanning for expiry date...")
            
            expiry_date = extract_expiry_date_easyocr(frame)
            
            if expiry_date:
                try:
                    formatted_date = expiry_date.replace('.', '/').replace('-', '/')
                    expiry_date_obj = datetime.strptime(formatted_date, "%d/%m/%Y")
                    today = datetime.today()
                    
                    if last_processed_date is None or last_processed_date != expiry_date_obj:
                        last_processed_date = expiry_date_obj
                        
                        if expiry_date_obj < today:
                            target = "left"
                            print(f"❌ EXPIRED! Date: {expiry_date}")
                            status_label.config(text=f"❌ EXPIRED: {expiry_date}", fg="red")
                            expired_count.set(expired_count.get() + 1)
                        else:
                            target = "right"
                            print(f"✅ VALID! Date: {expiry_date}")
                            status_label.config(text=f"✅ VALID: {expiry_date}", fg="green")
                            valid_count.set(valid_count.get() + 1)

                        producer_allowed_event.clear()
                        processing_event.clear()
                        
                        with queue_lock:
                            frame_queue_container[0] = queue.Queue(maxsize=10)
                        
                        move_object(target, processing_event, producer_allowed_event)
                        status_label.config(text="✅ Ready to scan", fg="white")
                        
                except ValueError as e:
                    print(f"Invalid date format: {e}")
                    status_label.config(text="⚠️ Invalid date format", fg="yellow")
            else:
                status_label.config(text="⏳ No date detected, keep scanning...", fg="yellow")

def capture_frames(cap, frame_queue_container, producer_allowed_event):
    """Continuously capture frames from camera."""
    while True:
        producer_allowed_event.wait()
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        with queue_lock:
            current_queue = frame_queue_container[0]
            if current_queue.full():
                try:
                    current_queue.get_nowait()
                except queue.Empty:
                    pass
            current_queue.put(frame)
        time.sleep(0.5)  # Capture every 0.5 seconds for OCR processing

def main():
    """Main function."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open camera")
        return

    root = tk.Tk()
    root.title("ExpirioBot - Automatic OCR Mode")
    root.configure(bg="#2e2e2e")
    root.geometry("750x650")

    # Title
    title = tk.Label(root, text="🤖 ExpirioBot - Automatic Detection", 
                    font=("Comfortaa", 16, "bold"), bg="#2e2e2e", fg="white")
    title.pack(pady=10)

    # Status
    status_label = tk.Label(root, text="✅ Ready to scan", 
                           font=("Comfortaa", 11), bg="#2e2e2e", fg="white")
    status_label.pack()

    # Warning
    warning = tk.Label(root, text="⚠️ AUTOMATIC MODE - Show product expiry date to camera", 
                      font=("Comfortaa", 10), bg="#2e2e2e", fg="yellow")
    warning.pack(pady=5)

    # Video feed
    video_label = Label(root, bg="#2e2e2e")
    video_label.pack(pady=10)

    # Counters
    counter_frame = tk.Frame(root, bg="#2e2e2e")
    counter_frame.pack(pady=10)

    expired_count = tk.IntVar(value=0)
    valid_count = tk.IntVar(value=0)

    # Expired
    exp_frame = tk.Frame(counter_frame, bg="#2e2e2e")
    exp_frame.grid(row=0, column=0, padx=30)
    tk.Label(exp_frame, textvariable=expired_count, font=("Comfortaa", 28, "bold"), 
            fg="red", bg="#2e2e2e").pack()
    tk.Label(exp_frame, text="❌ Expired Products", font=("Comfortaa", 12), 
            bg="#2e2e2e", fg="white").pack()

    # Valid
    val_frame = tk.Frame(counter_frame, bg="#2e2e2e")
    val_frame.grid(row=0, column=1, padx=30)
    tk.Label(val_frame, textvariable=valid_count, font=("Comfortaa", 28, "bold"), 
            fg="green", bg="#2e2e2e").pack()
    tk.Label(val_frame, text="✅ Valid Products", font=("Comfortaa", 12), 
            bg="#2e2e2e", fg="white").pack()

    frame_queue_container = [queue.Queue(maxsize=10)]
    processing_event = threading.Event()
    producer_allowed_event = threading.Event()

    producer_thread = None
    consumer_thread = None

    def start_program():
        """Start automatic detection."""
        nonlocal producer_thread, consumer_thread
        processing_event.set()
        producer_allowed_event.set()
        status_label.config(text="🔍 Scanning started...", fg="cyan")

        if producer_thread is None or not producer_thread.is_alive():
            producer_thread = threading.Thread(
                target=capture_frames, 
                args=(cap, frame_queue_container, producer_allowed_event)
            )
            producer_thread.daemon = True
            producer_thread.start()

        if consumer_thread is None or not consumer_thread.is_alive():
            consumer_thread = threading.Thread(
                target=process_frames, 
                args=(frame_queue_container, processing_event, producer_allowed_event, 
                     expired_count, valid_count, status_label)
            )
            consumer_thread.daemon = True
            consumer_thread.start()

    def stop_program():
        """Stop scanning."""
        producer_allowed_event.clear()
        processing_event.clear()
        status_label.config(text="⏸️ Scanning paused", fg="orange")

    def update_frame():
        """Update video feed."""
        ret, frame = cap.read()
        if ret:
            frame = cv2.resize(frame, (500, 375))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            video_label.imgtk = imgtk
            video_label.configure(image=imgtk)
        root.after(10, update_frame)

    # Buttons
    button_frame = tk.Frame(root, bg="#2e2e2e")
    button_frame.pack(pady=15)

    start_btn = tk.Button(button_frame, text="▶️ Start Scanning", command=start_program, 
                         bg="#4caf50", fg="white", font=("Comfortaa", 12, "bold"), 
                         padx=20, pady=10)
    start_btn.grid(row=0, column=0, padx=10)

    stop_btn = tk.Button(button_frame, text="⏸️ Stop", command=stop_program, 
                        bg="#f44336", fg="white", font=("Comfortaa", 12, "bold"), 
                        padx=20, pady=10)
    stop_btn.grid(row=0, column=1, padx=10)

    # Instructions
    info = tk.Label(root, 
        text="💡 Hold product with expiry date clearly visible to camera\n"
             "System will automatically detect and sort expired/valid products",
        font=("Comfortaa", 9), bg="#2e2e2e", fg="#aaaaaa", justify="center")
    info.pack(pady=5)

    update_frame()
    root.mainloop()
    cap.release()

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("🤖 ExpirioBot - Automatic OCR Mode")
        print("=" * 60)
        print("✅ Using EasyOCR for text detection")
        print("✅ Camera will automatically scan expiry dates")
        print("⚠️ Mock arm mode (no physical hardware)")
        print("=" * 60)
        main()
    finally:
        del Arm
        print("\n✅ Program Ended")
