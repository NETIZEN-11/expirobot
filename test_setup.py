#!/usr/bin/env python3
"""Test script to check ExpirioBot dependencies"""

import sys

print("=" * 60)
print("ExpirioBot Dependency Checker")
print("=" * 60)

errors = []
warnings = []

# Test 1: Python version
print("\n1. Checking Python version...")
print(f"   Python {sys.version}")
if sys.version_info >= (3, 7):
    print("   ✅ Python version OK")
else:
    errors.append("Python 3.7+ required")

# Test 2: OpenCV
print("\n2. Checking OpenCV...")
try:
    import cv2
    print(f"   ✅ OpenCV {cv2.__version__} installed")
except ImportError:
    errors.append("OpenCV not installed")
    print("   ❌ OpenCV not found")

# Test 3: Pytesseract
print("\n3. Checking pytesseract...")
try:
    import pytesseract
    print("   ✅ pytesseract installed")
except ImportError:
    errors.append("pytesseract not installed")
    print("   ❌ pytesseract not found")

# Test 4: PIL/Pillow
print("\n4. Checking Pillow...")
try:
    from PIL import Image
    print("   ✅ Pillow installed")
except ImportError:
    errors.append("Pillow not installed")
    print("   ❌ Pillow not found")

# Test 5: Tesseract executable
print("\n5. Checking Tesseract OCR executable...")
tesseract_found = False
tesseract_path = None

paths_to_check = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Tesseract-OCR\tesseract.exe",
    r"C:\Users\Nitesh-PC\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
]

import os
for path in paths_to_check:
    if os.path.exists(path):
        tesseract_found = True
        tesseract_path = path
        print(f"   ✅ Tesseract found at: {path}")
        break

if not tesseract_found:
    # Try using system PATH
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        print("   ✅ Tesseract found in system PATH")
        tesseract_found = True
    except:
        errors.append("Tesseract OCR executable not found")
        print("   ❌ Tesseract executable not found")
        print("   💡 Download from: https://sourceforge.net/projects/tesseract-ocr.mirror/")

# Test 6: Camera
print("\n6. Checking camera access...")
try:
    import cv2
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"   ✅ Camera working! Resolution: {frame.shape[1]}x{frame.shape[0]}")
        else:
            warnings.append("Camera opened but cannot read frames")
            print("   ⚠️  Camera opened but cannot read frames")
        cap.release()
    else:
        warnings.append("Cannot open camera")
        print("   ⚠️  Cannot open camera (may not be connected)")
except Exception as e:
    warnings.append(f"Camera error: {e}")
    print(f"   ⚠️  Camera error: {e}")

# Test 7: tkinter
print("\n7. Checking tkinter (GUI)...")
try:
    import tkinter as tk
    print("   ✅ tkinter available")
except ImportError:
    errors.append("tkinter not installed")
    print("   ❌ tkinter not found")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

if errors:
    print("\n❌ ERRORS (Must fix):")
    for i, error in enumerate(errors, 1):
        print(f"   {i}. {error}")

if warnings:
    print("\n⚠️  WARNINGS (Optional):")
    for i, warning in enumerate(warnings, 1):
        print(f"   {i}. {warning}")

if not errors:
    print("\n✅ All critical dependencies are installed!")
    print("   You can run ExpirioBot_Windows.py")
    if tesseract_path:
        print(f"\n📝 Tesseract path for your code:")
        print(f"   pytesseract.pytesseract.tesseract_cmd = r'{tesseract_path}'")
else:
    print("\n❌ Please install missing dependencies before running ExpirioBot")

print("=" * 60)
