@echo off
echo ========================================
echo BlurOBS Build Script
echo ========================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

:: Clean previous builds
echo Cleaning previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

:: Create assets folder if it doesn't exist
if not exist "assets" mkdir "assets"

:: Build the executable
echo.
echo Building BlurOBS executable...
echo This may take several minutes...
echo.

python -m PyInstaller BlurOBS.spec --clean

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Output: dist\BlurOBS.exe
echo.
echo To distribute:
echo 1. Copy dist\BlurOBS.exe to your distribution folder
echo 2. Users need OBS Virtual Camera installed
echo 3. Run BlurOBS.exe, then select "BlurOBS Virtual Camera" in OBS
echo.
pause
