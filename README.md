# BlurOBS

**AI-Powered Privacy Shield for OBS Studio**

BlurOBS automatically detects and blurs sensitive content (faces, phones, credit cards, documents) in real-time before it reaches your stream.

---

##  Quick Start

### For Users (Pre-built Release)

1. **Download** `BlurOBS.exe` from [Releases](../../releases)
2. **Install OBS Virtual Camera** (included with OBS Studio 26.0+)
3. **Run** `BlurOBS.exe`
4. **In OBS**: Add a Video Capture Device → Select "OBS Virtual Camera" or "BlurOBS"

### For Developers

```bash
# Clone the repository
git clone https://github.com/Danvdl/BlurOBS.git
cd BlurOBS

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python run.py
```

---

##  Features

- **Real-time Object Detection** - YOLOv8/YOLO-World AI models
- **Smart Tracking** - Objects stay blurred even during fast motion
- **Security Mode** - Detect credit cards, IDs, documents
- **Nudity Filtering** - Detect and blur exposed skin/nudity (Security Mode)
- **Multiple Blur Styles** - Gaussian, Pixelate, Solid black
- **GPU Acceleration** - CUDA support for NVIDIA GPUs
- **1080p Support** - Full HD output with optimized performance

---

##  Settings

| Setting | Description |
|---------|-------------|
| **Standard Mode** | Blur common objects (phones, laptops, faces) |
| **Security Mode** | Custom detection (credit cards, documents, nudity) |
| **Blur Style** | Gaussian / Pixelate / Solid |
| **Smoothing** | Reduce jitter (0.0 - 0.9) |
| **Confidence** | Detection sensitivity (0.1 - 0.9) |

---

##  Building from Source

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable (Windows)
build.bat

# Or manually:
pyinstaller BlurOBS.spec --clean
```

Output: `dist/BlurOBS.exe`

---

##  System Requirements

- **OS:** Windows 10/11
- **OBS:** OBS Studio 26.0+ (for virtual camera support)
- **GPU:** NVIDIA GPU with CUDA (optional, for acceleration)
- **RAM:** 4GB minimum, 8GB recommended

---

##  Troubleshooting

**"Virtual Camera Failed"**
- Ensure OBS is installed with Virtual Camera feature
- Try running OBS once to initialize the virtual camera

**"Camera Not Found"**
- Close other apps using the camera
- Check camera permissions in Windows Settings

**Low FPS**
- Enable GPU acceleration (requires NVIDIA + CUDA)
- Reduce resolution in settings
- Switch to Standard Mode (faster than Security Mode)

---

##  Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Webcam    │────▶│  BlurOBS    │────▶│  OBS Studio │
│             │     │  (AI + Blur)│     │  (Virtual   │
└─────────────┘     └─────────────┘     │   Camera)   │
                                        └─────────────┘
```

| Component | Technology |
|-----------|------------|
| **Detection** | YOLOv8 / YOLO-World |
| **Tracking** | ByteTrack |
| **GUI** | PyQt6 |
| **Virtual Cam** | pyvirtualcam |

---

##  License

MIT License - See [LICENSE](LICENSE) for details.

##  Credits

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [PyVirtualCam](https://github.com/letmaik/pyvirtualcam)
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)

### Phase 3: The "Streamer Experience" (UX) - **Implemented**
**Goal:** Features that make the app safe and trustworthy for live broadcasting.

**The "Confidence" Switch:**
*   Add a logic check: If the Local Tracker confidence drops below 50% (object moves too fast), instantly revert to the YOLO Box (safety fallback).

**Class Selector:**
*   Add a simple "Settings" menu in PyQt6 allowing the user to toggle what to blur: [x] Cell Phones, [ ] Faces, [ ] Credit Cards (Custom trained YOLO model required for cards).

**The Panic Button:**
*   Global Hotkey (F12): Instantly blurs the entire screen and pauses the camera.

### Phase 4: Packaging & Release
**Goal:** A distributable .exe file.

**Dependency Handling:**
*   Create a `requirements.txt` locking exact versions of `ultralytics` and `pyqt6`.

**Compilation:**
*   Use Nuitka to compile the Python source into a standalone executable.
*   Command: `nuitka --standalone --enable-plugin=pyqt6 --follow-imports main.py`

## Prerequisites
Before running the application, ensure you have the following installed:
*   OBS Studio (Version 26.0+): Required for the generic "OBS Virtual Camera" driver.
*   Python 3.10 or 3.11.
*   A Webcam.
*   **Replicate API Token**: You need a Replicate account and API token for the cloud masking feature.

## Installation
1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Set your Replicate API Token (Optional, for precise masking):
    *   Edit `main.py` and replace the token, or set the environment variable `REPLICATE_API_TOKEN`.
3.  Run the application:
    ```bash
    python main.py
    ```
