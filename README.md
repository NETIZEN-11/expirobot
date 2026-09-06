***

# The ExpirioBot

![Dofbot Pi](https://raw.githubusercontent.com/YahboomTechnology/dofbot-Pi/refs/heads/main/DOFBOT_Pi_Yahboom.jpg)

## Overview

ExpirioBot is an automated robotic system designed to identify and sort products based on their expiry dates. The system utilizes computer vision to capture images of products, extract expiry dates using Optical Character Recognition (OCR), and control a robotic arm to move expired or valid products to designated locations.

## Features

- **OCR-Based Expiry Date Detection**: Extract expiry dates from product labels using `Tesseract OCR`
- **Robotic Arm Sorting**: A robotic arm sorts products into `expired` and `valid` categories
- **Real-Time Video Feed**: Displays a live feed of the camera input
- **Counters for Products**: Tracks the number of expired and valid products in real-time
- **Threaded Architecture**: Ensures smooth operation with concurrent frame capturing and processing
- **Cross-Platform**: Runs on Raspberry Pi (with hardware) and Windows (mock mode)
- **Configurable**: All settings managed through config file, no hardcoded values
- **Modular Design**: Clean separation of concerns with shared modules

## Requirements

### Hardware (Raspberry Pi Version)
- DOFBOT-Pi robotic arm
- Processing Computer (Raspberry Pi 4 or equivalent recommended)
- Camera (USB or Pi Camera)

### Software
- `Python 3.7+`
- `OpenCV (cv2)`
- `Pillow (PIL)`
- `Pytesseract`
- `tkinter` (usually built-in)
- `numpy`
- `Arm_Lib` (custom library for controlling the robotic arm - Raspberry Pi only)
- `Tesseract OCR` installed on your system (required for OCR modes)

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/EdwinAbdonShayo/ExpirioBot.git
cd ExpirioBot
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Tesseract OCR

**Windows:**
- Download installer from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
- Or use winget: `winget install UB-Mannheim.TesseractOCR`

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update && sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

### 4. Install Arm Library (Raspberry Pi only)
```bash
cd py_install
pip install -e .
cd ..
```

## Repository Structure

```
ExpirioBot/
│
├── ExpirioBot.py                    # Main script for Raspberry Pi with DOFBOT arm
├── ExpirioBot_Windows.py            # Windows version with Tesseract OCR (mock arm)
├── ExpirioBot_NoTesseract.py        # Windows version with manual date entry (no Tesseract needed)
├── requirements.txt                 # Python dependencies
├── .gitignore                       # Git ignore rules
├── README.md                        # This file
│
├── expiriobot/                      # Main package
│   ├── __init__.py                  # Package initialization
│   ├── config.py                    # Configuration management
│   ├── arm_control.py               # Robotic arm control (physical + mock)
│   ├── ocr_processor.py             # OCR processing and date extraction
│   ├── camera.py                    # Camera management
│   └── gui.py                       # GUI components
│
├── py_install/                      # Arm_Lib package for Raspberry Pi
│   ├── setup.py                     # Package setup
│   └── Arm_Lib/                     # Arm library source
│       ├── __init__.py
│       └── Arm_Lib.py
│
└── tests/                           # Test files
    ├── test_setup.py                # Dependency checker
    ├── test_config.py               # Config tests
    └── test_ocr_processor.py        # OCR processor tests
```

## Usage

### For Raspberry Pi (Original Hardware)

1. **Connect Hardware**:
   - Attach the camera and ensure it is accessible
   - Connect the DOFBOT robotic arm to the system

2. **Run the Program**:
   ```bash
   python3 ExpirioBot.py
   ```

3. **Control Through the GUI**:
   - `Start`: Begin capturing and processing frames
   - `Stop`: Pause the system
   - View live video feed and counters for expired and valid products

### For Windows (Without Physical Hardware)

#### Option 1: Manual Date Entry (No Tesseract Required) - **RECOMMENDED FOR TESTING**
```bash
python ExpirioBot_NoTesseract.py
```
- ✅ Works without Tesseract OCR installation
- ✅ Live camera preview
- ✅ Manual date input for testing
- ✅ Mock arm simulation (console output)
- Enter dates in format: DD/MM/YYYY (e.g., 25/12/2024)

#### Option 2: Full OCR Version (Tesseract Required)
```bash
python ExpirioBot_Windows.py
```
- Requires Tesseract OCR installation
- Automatic date extraction from camera
- Mock arm simulation

### Key Functions
- `arm_clamp_block(enable)`: Controls the clamp of the robotic arm (servo 6)
- `arm_move(p, s_time)`: Moves the arm to specified positions
- `preprocess_image(frame)`: Prepares the image for OCR processing
- `extract_expiry_date(image_path)`: Extracts the expiry date from the image using OCR
- `process_frames(...)`: Processes frames from the queue
- `capture_frames(...)`: Captures frames from the camera

## Configuration

All configurable settings are in `expiriobot/config.py`. You can customize:

### Arm Positions
```python
# In config.py or via environment variables
ARM_POSITIONS = {
    "front": [90, 75, 0, 30, 90],
    "left": [180, 75, 0, 30, 90],
    "right": [0, 75, 0, 30, 90],
    # ... more positions
}
```

### Camera Settings
```bash
export EXPIRIOBOT_CAMERA_INDEX=1  # Use camera index 1
```

### Tesseract Path
```bash
export EXPIRIOBOT_TESSERACT_PATH="/usr/bin/tesseract"
```

### Mock Arm Mode
```bash
export EXPIRIOBOT_MOCK_ARM=true
```

## Customization

1. **Modify Predefined Arm Positions**:
   - Update positions in `expiriobot/config.py` (`ArmConfig.positions`)

2. **Change Thresholds for Image Preprocessing**:
   - Edit `OCRConfig.threshold_value` in `expiriobot/config.py`

3. **Extend OCR Patterns**:
   - Modify `OCRConfig.date_patterns` in `expiriobot/config.py` to handle additional date formats

4. **Add New Camera Resolutions**:
   - Modify `CameraConfig` in `expiriobot/config.py`

## Running Tests

```bash
# Check dependencies
python tests/test_setup.py

# Run unit tests
pytest tests/
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Camera Not Detected | Ensure camera is connected and accessible through OpenCV. Check camera index in config. |
| Robotic Arm Not Responding | Verify arm is powered, correctly configured & Arm_Lib is installed (Raspberry Pi). |
| OCR Not Extracting Dates | Check Tesseract installation. Ensure image has clear, legible text. Adjust preprocessing thresholds. |
| Windows smbus Error | Use `ExpirioBot_Windows.py` or `ExpirioBot_NoTesseract.py` which have mock arm support |
| Import Errors | Run `pip install -r requirements.txt` and ensure `py_install` is installed for Raspberry Pi |
| Tesseract Not Found | Install Tesseract OCR and ensure it's in PATH, or set `EXPIRIOBOT_TESSERACT_PATH` |

## Development

### Code Style
```bash
# Format code
black expiriobot/ tests/

# Lint
flake8 expiriobot/ tests/

# Type check
mypy expiriobot/
```

### Adding New Features
1. Add configuration to `expiriobot/config.py`
2. Implement core logic in appropriate module (`arm_control.py`, `ocr_processor.py`, etc.)
3. Update entry points (`ExpirioBot.py`, `ExpirioBot_Windows.py`, `ExpirioBot_NoTesseract.py`)
4. Add tests in `tests/`

## Acknowledgments

- OpenCV for image processing
- Tesseract OCR for text extraction
- DOFBOT for providing a reliable robotic arm solution
- tkinter for GUI development
- Yahboom Technology for Arm_Lib

## The Team

- [Sakina](https://github.com/saki3110)
- [Ishan](https://github.com/ishan23310)  
- [Hans](https://github.com/gt663) 
- [Edwin](https://edwinshayo.com)

*For any inquiries or issues, reach out to any of the above*

***