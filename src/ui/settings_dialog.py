from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QCheckBox, QPushButton, QLabel, 
    QGridLayout, QGroupBox, QDialogButtonBox, QRadioButton, QButtonGroup,
    QLineEdit, QWidget, QSlider, QComboBox, QHBoxLayout
)
from PyQt6.QtCore import Qt
from src.utils.settings import settings_manager, AVAILABLE_CLASSES, SECURITY_CLASSES
from src.utils.logger import log_event

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(500, 650)
        self.setStyleSheet(parent.styleSheet() if parent else "")
        
        layout = QVBoxLayout(self)
        
        # --- Model Selection ---
        model_group = QGroupBox("Detection Mode")
        model_layout = QVBoxLayout()
        
        self.mode_group = QButtonGroup(self)
        self.radio_standard = QRadioButton("Standard (Fast - Predefined Objects)")
        self.radio_custom = QRadioButton("Security / Custom (Slower - Custom Prompts)")
        
        self.mode_group.addButton(self.radio_standard)
        self.mode_group.addButton(self.radio_custom)
        
        if settings_manager.get("use_custom_model"):
            self.radio_custom.setChecked(True)
        else:
            self.radio_standard.setChecked(True)
            
        self.radio_standard.toggled.connect(self.toggle_mode_ui)
        
        model_layout.addWidget(self.radio_standard)
        model_layout.addWidget(self.radio_custom)
        
        # Model Size Selector
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("AI Model Size:"))
        self.size_combo = QComboBox()
        self.size_combo.addItem("Small (Fastest - Recommended)", "s")
        self.size_combo.addItem("Medium (Balanced - Higher CPU Usage)", "m")
        self.size_combo.addItem("Large (Most Accurate - High CPU Usage)", "l")
        
        # Set current index
        current_size = settings_manager.get("model_size")
        index = self.size_combo.findData(current_size)
        if index >= 0:
            self.size_combo.setCurrentIndex(index)
            
        size_layout.addWidget(self.size_combo)
        model_layout.addLayout(size_layout)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # --- Sensitivity (Confidence) ---
        sens_group = QGroupBox("Sensitivity")
        sens_layout = QVBoxLayout()
        
        self.conf_label = QLabel()
        current_conf = settings_manager.get("confidence_threshold")
        self.conf_slider = QSlider(Qt.Orientation.Horizontal)
        self.conf_slider.setRange(1, 99)
        self.conf_slider.setValue(int(current_conf * 100))
        self.conf_slider.valueChanged.connect(self.update_conf_label)
        self.update_conf_label(self.conf_slider.value())
        
        sens_layout.addWidget(self.conf_label)
        sens_layout.addWidget(self.conf_slider)
        sens_group.setLayout(sens_layout)
        layout.addWidget(sens_group)

        # --- Visual Settings (Blur & Smoothing) ---
        visual_group = QGroupBox("Visual Settings")
        visual_layout = QVBoxLayout()
        
        # Blur Style
        blur_layout = QHBoxLayout()
        blur_layout.addWidget(QLabel("Blur Style:"))
        self.blur_combo = QComboBox()
        self.blur_combo.addItem("Pixelate (Mosaic)", "pixelate")
        self.blur_combo.addItem("Gaussian (Soft)", "gaussian")
        self.blur_combo.addItem("Solid Black (Censor)", "solid")
        
        current_style = settings_manager.get("blur_style")
        idx = self.blur_combo.findData(current_style)
        if idx >= 0: self.blur_combo.setCurrentIndex(idx)
        
        blur_layout.addWidget(self.blur_combo)
        visual_layout.addLayout(blur_layout)
        
        # Smoothing
        self.smooth_label = QLabel()
        current_smooth = settings_manager.get("smooth_factor")
        self.smooth_slider = QSlider(Qt.Orientation.Horizontal)
        self.smooth_slider.setRange(0, 90) # 0.0 to 0.9
        self.smooth_slider.setValue(int(current_smooth * 100))
        self.smooth_slider.valueChanged.connect(self.update_smooth_label)
        self.update_smooth_label(self.smooth_slider.value())
        
        visual_layout.addWidget(self.smooth_label)
        visual_layout.addWidget(self.smooth_slider)
        
        visual_group.setLayout(visual_layout)
        layout.addWidget(visual_group)

        # --- Standard Object Detection Settings ---
        self.obj_group = QGroupBox("Standard Objects")
        obj_layout = QGridLayout()
        
        self.checkboxes = {}
        current_targets = settings_manager.get("target_classes")
        
        row, col = 0, 0
        for cls_id, name in AVAILABLE_CLASSES.items():
            cb = QCheckBox(name)
            cb.setChecked(cls_id in current_targets)
            self.checkboxes[cls_id] = cb
            obj_layout.addWidget(cb, row, col)
            
            col += 1
            if col > 1:
                col = 0
                row += 1
                
        self.obj_group.setLayout(obj_layout)
        layout.addWidget(self.obj_group)
        
        # --- Custom / Security Settings ---
        self.custom_group = QGroupBox("Security Objects & Custom Prompts")
        custom_layout = QVBoxLayout()
        
        # 1. Security Checkboxes
        sec_grid = QGridLayout()
        self.sec_checkboxes = {}
        current_sec = settings_manager.get("security_classes_enabled")
        
        row, col = 0, 0
        for name in SECURITY_CLASSES:
            cb = QCheckBox(name.title())
            cb.setChecked(name in current_sec)
            self.sec_checkboxes[name] = cb
            sec_grid.addWidget(cb, row, col)
            
            col += 1
            if col > 1:
                col = 0
                row += 1
        
        custom_layout.addLayout(sec_grid)
        
        # 2. Custom Text Input
        custom_layout.addWidget(QLabel("Other (comma separated):"))
        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("e.g. confidential paper, sticky note")
        current_custom = settings_manager.get("custom_classes")
        self.custom_input.setText(", ".join(current_custom))
        custom_layout.addWidget(self.custom_input)
        
        self.custom_group.setLayout(custom_layout)
        layout.addWidget(self.custom_group)
        
        # Initial UI State
        self.toggle_mode_ui()

        # --- Buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def update_conf_label(self, value):
        self.conf_label.setText(f"Confidence Threshold: {value}% (Lower = More Sensitive)")

    def update_smooth_label(self, value):
        self.smooth_label.setText(f"Motion Smoothing: {value}% (Higher = Less Jitter, More Lag)")

    def toggle_mode_ui(self):
        is_standard = self.radio_standard.isChecked()
        self.obj_group.setVisible(is_standard)
        self.custom_group.setVisible(not is_standard)

    def accept(self):
        # Save settings
        
        # 1. Mode
        use_custom = self.radio_custom.isChecked()
        settings_manager.set("use_custom_model", use_custom)
        
        # 1b. Model Size
        size = self.size_combo.currentData()
        settings_manager.set("model_size", size)
        
        # 2. Confidence
        conf = self.conf_slider.value() / 100.0
        settings_manager.set("confidence_threshold", conf)
        
        # 2b. Visuals
        settings_manager.set("blur_style", self.blur_combo.currentData())
        settings_manager.set("smooth_factor", self.smooth_slider.value() / 100.0)
        
        # 3. Standard Targets
        new_targets = []
        for cls_id, cb in self.checkboxes.items():
            if cb.isChecked():
                new_targets.append(cls_id)
        settings_manager.set("target_classes", new_targets)
        
        # 4. Security Checkboxes
        new_sec = []
        for name, cb in self.sec_checkboxes.items():
            if cb.isChecked():
                new_sec.append(name)
        settings_manager.set("security_classes_enabled", new_sec)

        # 5. Custom Prompts
        raw_text = self.custom_input.text()
        custom_list = [x.strip() for x in raw_text.split(",") if x.strip()]
        settings_manager.set("custom_classes", custom_list)
        
        # Log settings change event
        log_event("SETTINGS", "Settings saved",
                  mode="security" if use_custom else "standard",
                  model_size=size,
                  confidence=conf,
                  blur_style=self.blur_combo.currentData(),
                  target_count=len(new_targets),
                  security_classes=len(new_sec),
                  custom_classes=len(custom_list))
        
        super().accept()
        
        settings_manager.set("target_classes", new_targets)
        super().accept()
