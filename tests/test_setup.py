#!/usr/bin/env python3
"""Test script to check ExpirioBot dependencies"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 60)
print("ExpirioBot Dependency Checker")
print("=" * 60)

errors = []
warnings = []

# Test 1: Python version
print("\n1. Checking Python version...")
print(f"   Python {sys.version}")
if sys.version_info >= (3, 7):
    print("   [OK] Python version OK")
else:
    errors.append("Python 3.7+ required")

# Test 2: OpenCV
print("\n2. Checking OpenCV...")
try:
    import cv2
    print(f"   [OK] OpenCV {cv2.__version__} installed")
except ImportError:
    errors.append("OpenCV not installed")
    print("   [ERROR] OpenCV not found")

# Test 3: Pytesseract
print("\n3. Checking pytesseract...")
try:
    import pytesseract
    print("   [OK] pytesseract installed")
except ImportError:
    errors.append("pytesseract not installed")
    print("   [ERROR] pytesseract not found")

# Test 4: PIL/Pillow
print("\n4. Checking Pillow...")
try:
    from PIL import Image
    print("   [OK] Pillow installed")
except ImportError:
    errors.append("Pillow not installed")
    print("   [ERROR] Pillow not found")

# Test 5: Tesseract executable
print("\n5. Checking Tesseract OCR executable...")
tesseract_found = False
tesseract_path = None

# Use the config module to find tesseract
try:
    from expiriobot.config import get_config
    cfg = get_config()
    if cfg.ocr.tesseract_cmd and os.path.exists(cfg.ocr.tesseract_cmd):
        tesseract_found = True
        tesseract_path = cfg.ocr.tesseract_cmd
        print(f"   [OK] Tesseract found at: {tesseract_path}")
    else:
        # Try system PATH
        import shutil
        tesseract_path = shutil.which("tesseract")
        if tesseract_path:
            tesseract_found = True
            print(f"   [OK] Tesseract found in system PATH: {tesseract_path}")
except Exception as e:
    warnings.append(f"Config check failed: {e}")
    print(f"   [WARN] Config check failed: {e}")

if not tesseract_found:
    # Try common paths as fallback
    paths_to_check = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/opt/homebrew/bin/tesseract",
    ]
    for path in paths_to_check:
        if os.path.exists(path):
            tesseract_found = True
            tesseract_path = path
            print(f"   [OK] Tesseract found at: {path}")
            break

if not tesseract_found:
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        print("   [OK] Tesseract found in system PATH")
        tesseract_found = True
    except:
        warnings.append("Tesseract OCR executable not found (optional for manual mode)")
        print("   [WARN] Tesseract executable not found (optional for manual mode)")
        print("   [INFO] Download from: https://github.com/UB-Mannheim/tesseract/wiki")

# Test 6: Camera
print("\n6. Checking camera access...")
try:
    import cv2
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"   [OK] Camera working! Resolution: {frame.shape[1]}x{frame.shape[0]}")
        else:
            warnings.append("Camera opened but cannot read frames")
            print("   [WARN] Camera opened but cannot read frames")
        cap.release()
    else:
        warnings.append("Cannot open camera")
        print("   [WARN] Cannot open camera (may not be connected)")
except Exception as e:
    warnings.append(f"Camera error: {e}")
    print(f"   [WARN] Camera error: {e}")

# Test 7: tkinter
print("\n7. Checking tkinter (GUI)...")
try:
    import tkinter as tk
    print("   [OK] tkinter available")
except ImportError:
    errors.append("tkinter not installed")
    print("   [ERROR] tkinter not found")

# Test 8: ExpirioBot modules
print("\n8. Checking ExpirioBot modules...")
try:
    from expiriobot.config import get_config, Config
    from expiriobot.arm_control import create_arm_controller, MockArmDevice
    from expiriobot.ocr_processor import create_ocr_processor
    from expiriobot.camera import create_camera_manager
    from expiriobot.gui import ExpirioBotGUI
    print("   [OK] All ExpirioBot modules imported successfully")
except ImportError as e:
    errors.append(f"ExpirioBot module import failed: {e}")
    print(f"   [ERROR] ExpirioBot module import failed: {e}")

# Test 9: Arm_Lib (for Raspberry Pi)
print("\n9. Checking Arm_Lib (Raspberry Pi only)...")
try:
    from Arm_Lib import Arm_Device
    print("   [OK] Arm_Lib available")
except ImportError:
    warnings.append("Arm_Lib not installed (required for Raspberry Pi with physical arm)")
    print("   [WARN] Arm_Lib not installed (required for Raspberry Pi with physical arm)")
    print("   [INFO] Install with: cd py_install && pip install -e .")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

if errors:
    print("\n[ERROR] ERRORS (Must fix):")
    for i, error in enumerate(errors, 1):
        print(f"   {i}. {error}")

if warnings:
    print("\n[WARN] WARNINGS (Optional):")
    for i, warning in enumerate(warnings, 1):
        print(f"   {i}. {warning}")

if not errors:
    print("\n[OK] All critical dependencies are installed!")
    print("   You can run:")
    print("   - python ExpirioBot_NoTesseract.py (Windows, no Tesseract needed)")
    if tesseract_found:
        print("   - python ExpirioBot_Windows.py (Windows with OCR)")
    print("   - python ExpirioBot.py (Raspberry Pi with DOFBOT)")
    if tesseract_path:
        print(f"\n[INFO] Tesseract path detected: {tesseract_path}")
else:
    print("\n[ERROR] Please install missing dependencies before running ExpirioBot")

print("=" * 60)

# Exit with error code if critical errors
sys.exit(1 if errors else 0)