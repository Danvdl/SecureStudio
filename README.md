# SecureStudio

**AI-Powered Privacy Shield for OBS Studio**

SecureStudio automatically detects and blurs sensitive content (faces, phones, credit cards, documents) in real-time before it reaches your stream.

---

## 🚀 Quick Start

### For Users (Pre-built Release)

1. **Download** `SecureStudio.exe` from [Releases](../../releases)
2. **Install OBS Virtual Camera** (included with OBS Studio 26.0+)
3. **Run** `SecureStudio.exe` and complete the setup wizard
4. **In OBS**: Add a Video Capture Device → Select "OBS Virtual Camera"

### For Developers

```bash
# Clone the repository
git clone https://github.com/Danvdl/SecureStudio.git
cd SecureStudio

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python run.py
```

---

## 🎯 Features

- **Real-time Object Detection** - YOLOv8/YOLO-World AI models
- **Smart Tracking** - Objects stay blurred even during fast motion
- **Security Mode** - Detect credit cards, IDs, documents
- **Nudity Filtering** - Detect and blur exposed skin/nudity (Security Mode)
- **Multiple Blur Styles** - Gaussian, Pixelate, Solid black
- **GPU Acceleration** - CUDA support for NVIDIA GPUs
- **1080p Support** - Full HD output with optimized performance

---

## ⚙️ Settings

| Setting | Description |
|---------|-------------|
| **Standard Mode** | Blur common objects (phones, laptops, faces) |
| **Security Mode** | Custom detection (credit cards, documents, nudity) |
| **Blur Style** | Gaussian / Pixelate / Solid |
| **Smoothing** | Reduce jitter (0.0 - 0.9) |
| **Confidence** | Detection sensitivity (0.1 - 0.9) |

---

## 🔧 Building from Source

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable (Windows)
build.bat

# Or manually:
pyinstaller SecureStudio.spec --clean
```

Output: `dist/SecureStudio.exe`

---

## 📋 System Requirements

- **OS:** Windows 10/11
- **OBS:** OBS Studio 26.0+ (for virtual camera support)
- **GPU:** NVIDIA GPU with CUDA (optional, for acceleration)
- **RAM:** 4GB minimum, 8GB recommended

---

## 📝 Logging

SecureStudio includes a comprehensive logging system for debugging and event tracking.

**Log Location:** `%USERPROFILE%\.securestudio\logs\`

| Log File | Purpose |
|----------|---------|
| `debug.log` | All application events (verbose) |
| `error.log` | Warnings and errors only |
| `events.log` | User actions and app events |

**Debug Mode:** Run with `--debug` flag for verbose console output:
```bash
python run.py --debug
```

---

## �🐛 Troubleshooting

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

## 🏗️ Architecture

```
┌─────────────┐     ┌───────────────┐     ┌─────────────┐
│   Webcam    │────▶│ SecureStudio  │────▶│  OBS Studio │
│             │     │  (AI + Blur)  │     │  (Virtual   │
└─────────────┘     └───────────────┘     │   Camera)   │
                                        └─────────────┘
```

| Component | Technology |
|-----------|------------|
| **Detection** | YOLOv8 / YOLO-World |
| **Tracking** | ByteTrack |
| **GUI** | PyQt6 |
| **Virtual Cam** | pyvirtualcam |

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

## 🙏 Credits

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [PyVirtualCam](https://github.com/letmaik/pyvirtualcam)
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)



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