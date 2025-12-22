# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for SecureStudio

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect ultralytics data files (model configs, etc.)
ultralytics_datas = collect_data_files('ultralytics')

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include default YOLO models
        ('yolov8n.pt', '.'),
        ('yolov8s-worldv2.pt', '.'),
        # Include assets
        ('assets', 'assets'),
        # Include tracker config
    ] + ultralytics_datas,
    hiddenimports=[
        'ultralytics',
        'ultralytics.engine',
        'ultralytics.engine.model',
        'ultralytics.engine.results',
        'ultralytics.models',
        'ultralytics.models.yolo',
        'ultralytics.trackers',
        'ultralytics.trackers.byte_tracker',
        'ultralytics.utils',
        'torch',
        'torchvision',
        'cv2',
        'numpy',
        'PIL',
        'pyvirtualcam',
        'lapx',
        'lap',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
    ] + collect_submodules('ultralytics'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SecureStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',  # Optional: Add an icon
)
