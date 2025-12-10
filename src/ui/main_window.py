from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, 
    QGroupBox, QStatusBar, QMainWindow, QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon
from src.core.video_thread import VideoWorker
from src.ui.styles import DARK_THEME
from src.ui.settings_dialog import SettingsDialog
from src.utils.config import get_resource_path

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BlurOBS - AI Privacy Shield")
        
        # Set Window Icon
        icon_path = get_resource_path("assets/BLUROBS_ICON.png")
        self.setWindowIcon(QIcon(icon_path))

        self.resize(1000, 800)
        self.setStyleSheet(DARK_THEME)
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main Layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- Header ---
        header_layout = QHBoxLayout()
        
        # Logo
        logo_label = QLabel()
        logo_path = get_resource_path("assets/BLUROBS.png")
        logo_pixmap = QPixmap(logo_path)
        if not logo_pixmap.isNull():
             logo_pixmap = logo_pixmap.scaledToHeight(40, Qt.TransformationMode.SmoothTransformation)
             logo_label.setPixmap(logo_pixmap)
             header_layout.addWidget(logo_label)

        title_label = QLabel("BlurOBS Studio")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        header_layout.addWidget(title_label)
        
        # Settings Button
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setFixedWidth(100)
        self.settings_btn.clicked.connect(self.open_settings)
        header_layout.addWidget(self.settings_btn)
        
        main_layout.addLayout(header_layout)

        # --- Video Preview Area ---
        video_frame = QFrame()
        video_frame.setStyleSheet("background-color: #000; border: 2px solid #333; border-radius: 8px;")
        video_layout = QVBoxLayout(video_frame)
        video_layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel("Initializing Camera...")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("color: #666;")
        # Prevent the label from expanding the window; let it fit the available space
        self.image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        video_layout.addWidget(self.image_label)
        
        main_layout.addWidget(video_frame, stretch=1)

        # --- Controls Section ---
        controls_layout = QHBoxLayout()
        
        # Privacy Controls Group
        privacy_group = QGroupBox("Privacy Controls")
        privacy_layout = QVBoxLayout()
        
        self.check_box = QCheckBox("Enable Auto-Censor")
        self.check_box.setChecked(True)
        self.check_box.setToolTip("Automatically detects and blurs selected objects in the video feed.")
        self.check_box.stateChanged.connect(self.toggle_blur)
        privacy_layout.addWidget(self.check_box)
        
        privacy_group.setLayout(privacy_layout)
        controls_layout.addWidget(privacy_group)

        # View Controls Group
        view_group = QGroupBox("Director View")
        view_layout = QVBoxLayout()
        
        self.preview_check = QCheckBox("Show Output Preview (Blurred)")
        self.preview_check.setToolTip("Switch between the debug view (with red boxes) and the final output view.")
        self.preview_check.stateChanged.connect(self.toggle_preview)
        view_layout.addWidget(self.preview_check)
        
        view_group.setLayout(view_layout)
        controls_layout.addWidget(view_group)
        
        # Action Buttons (Future expansion)
        # action_layout = QVBoxLayout()
        # self.restart_btn = QPushButton("Restart Camera")
        # action_layout.addWidget(self.restart_btn)
        # action_layout.addStretch()
        # controls_layout.addLayout(action_layout)

        main_layout.addLayout(controls_layout)

        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # --- Video Thread ---
        self.thread = VideoWorker()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.status_signal.connect(self.update_status)
        self.thread.start()

    def toggle_blur(self, state):
        self.thread.auto_blur_enabled = (state == 2) # 2 is Checked

    def toggle_preview(self, state):
        self.thread.show_output = (state == 2)

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            # Reload settings in the worker thread
            self.thread.update_settings()
            self.status_bar.showMessage("Settings Updated")

    def update_status(self, message):
        self.status_bar.showMessage(message)

    def update_image(self, qt_image):
        pixmap = QPixmap.fromImage(qt_image)
        # Scale while keeping aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()
