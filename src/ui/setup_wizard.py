"""
SecureStudio Setup Wizard

First-run setup wizard that:
1. Shows Terms and Conditions
2. Asks for consent to send debug logs
3. Creates desktop shortcut (optional)
4. Downloads the required AI model
"""

import os
import sys
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QTextEdit, QProgressBar, QPushButton, QMessageBox,
    QFrame, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont, QColor, QPalette

from src.utils.config import get_resource_path
from src.utils.settings import settings_manager


def create_desktop_shortcut():
    """Create a desktop shortcut for SecureStudio on Windows."""
    try:
        # Get desktop path
        desktop = Path.home() / "Desktop"
        
        # Get the executable path
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            exe_path = sys.executable
            icon_path = exe_path
            working_dir = Path(exe_path).parent
            arguments = ""
        else:
            # Running as script - use pythonw.exe to hide console
            python_dir = Path(sys.executable).parent
            pythonw_path = python_dir / "pythonw.exe"
            
            # Fall back to python.exe if pythonw doesn't exist
            if pythonw_path.exists():
                exe_path = str(pythonw_path)
            else:
                exe_path = sys.executable
            
            script_path = Path(__file__).parent.parent.parent / "run.py"
            working_dir = script_path.parent
            arguments = f'"{script_path}"'
            
            # Try to use an icon file if available
            icon_path = get_resource_path("assets/SecureStudio.ico")
            if not os.path.exists(icon_path):
                icon_path = ""  # No icon if .ico doesn't exist
        
        shortcut_path = desktop / "SecureStudio.lnk"
        
        # Use PowerShell to create shortcut (works without additional dependencies)
        import subprocess
        
        if getattr(sys, 'frozen', False):
            # For compiled exe - the exe itself contains the icon
            ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{exe_path}"
$Shortcut.WorkingDirectory = "{working_dir}"
$Shortcut.Description = "SecureStudio - AI Privacy Shield"
$Shortcut.IconLocation = "{exe_path},0"
$Shortcut.Save()
'''
        else:
            # For Python script - use pythonw.exe to hide console
            icon_line = f'$Shortcut.IconLocation = "{icon_path}"' if icon_path else ""
            ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{exe_path}"
$Shortcut.Arguments = {arguments}
$Shortcut.WorkingDirectory = "{working_dir}"
$Shortcut.Description = "SecureStudio - AI Privacy Shield"
{icon_line}
$Shortcut.Save()
'''
        
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logging.info(f"Desktop shortcut created: {shortcut_path}")
            return True, str(shortcut_path)
        else:
            logging.error(f"Failed to create shortcut: {result.stderr}")
            return False, result.stderr
            
    except Exception as e:
        logging.error(f"Failed to create desktop shortcut: {e}")
        return False, str(e)


# Comprehensive Terms and Conditions
TERMS_AND_CONDITIONS = """
SECURESTUDIO - TERMS AND CONDITIONS OF USE
Version 1.0 | Effective Date: December 2025

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PLEASE READ THESE TERMS AND CONDITIONS CAREFULLY BEFORE USING SECURESTUDIO.

By downloading, installing, copying, or otherwise using SecureStudio ("the Software"), you acknowledge that you have read, understood, and agree to be bound by these Terms and Conditions ("Terms"). If you do not agree to these Terms, you must not use the Software.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. DEFINITIONS

1.1 "Software" refers to SecureStudio, including all associated files, libraries, AI models, documentation, updates, and any derivative works.

1.2 "User" or "You" refers to any individual or entity that downloads, installs, or uses the Software.

1.3 "Developer" refers to the creators and maintainers of SecureStudio.

1.4 "AI Models" refers to the machine learning models used by the Software for object detection, including but not limited to YOLOv8 and YOLO-World models.

1.5 "Content" refers to any video, audio, images, or other media processed by the Software.

1.6 "Stream" refers to any live or recorded broadcast where the Software is used.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2. LICENSE GRANT

2.1 Subject to your compliance with these Terms, the Developer grants you a limited, non-exclusive, non-transferable, revocable license to:
    (a) Download and install the Software on devices you own or control;
    (b) Use the Software for personal, educational, or commercial purposes;
    (c) Create derivative works for personal use only.

2.2 This license does not grant you any rights to:
    (a) Sell, sublicense, or redistribute the Software for profit;
    (b) Remove or alter any proprietary notices or labels;
    (c) Use the Software for any illegal purpose;
    (d) Reverse engineer, decompile, or disassemble the Software except as permitted by law.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3. THIRD-PARTY COMPONENTS AND LICENSES

3.1 The Software incorporates the following third-party components:

    (a) Ultralytics YOLOv8/YOLO-World - Licensed under AGPL-3.0
        Your use of these AI models is subject to the terms of the AGPL-3.0 license.
        Full license: https://www.gnu.org/licenses/agpl-3.0.html

    (b) PyQt6 - Licensed under GPL v3
        GUI framework subject to GPL v3 license terms.
        
    (c) OpenCV - Licensed under Apache 2.0
        Computer vision library for image processing.
        
    (d) PyVirtualCam - Licensed under MIT
        Virtual camera interface library.

3.2 You acknowledge and agree to comply with all applicable third-party license terms.

3.3 The AI models are downloaded from Ultralytics' servers. You accept Ultralytics' terms of service when downloading these models.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4. PRIVACY AND DATA HANDLING

4.1 LOCAL PROCESSING
    (a) All video and image processing occurs locally on your device.
    (b) No video content, images, or frames are transmitted to external servers.
    (c) The Software does not record, store, or transmit your stream content.

4.2 DIAGNOSTIC DATA (OPT-IN)
    If you choose to enable diagnostic data sharing:
    (a) Anonymous error logs and crash reports may be collected;
    (b) Application usage statistics (features used, performance metrics);
    (c) System information (OS version, GPU type, available memory);
    (d) No personally identifiable information is collected;
    (e) No video, audio, or image data is ever transmitted.

4.3 DATA RETENTION
    (a) Diagnostic data is retained for a maximum of 90 days;
    (b) You may request deletion of your diagnostic data at any time;
    (c) Local settings and preferences are stored only on your device.

4.4 OPT-OUT
    You may disable diagnostic data sharing at any time through the Settings menu.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5. AI AND MACHINE LEARNING DISCLAIMER

5.1 ACCURACY LIMITATIONS
    (a) The AI models are not 100% accurate and may produce false positives or false negatives;
    (b) Detection accuracy varies based on lighting, camera quality, object size, and other factors;
    (c) The Software should not be relied upon as the sole method of privacy protection.

5.2 NO GUARANTEE OF DETECTION
    (a) The Developer does not guarantee that all sensitive objects will be detected;
    (b) Some objects may be partially detected or missed entirely;
    (c) New or unusual objects may not be recognized by the AI models.

5.3 RECOMMENDED PRACTICES
    (a) Always verify the output preview before going live;
    (b) Use additional privacy measures when handling sensitive content;
    (c) Conduct test runs to understand the Software's behavior with your setup.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6. USER RESPONSIBILITIES AND CONDUCT

6.1 CONTENT RESPONSIBILITY
    (a) You are solely responsible for all content that appears in your streams;
    (b) You must comply with all applicable laws regarding content broadcasting;
    (c) You must not use the Software to facilitate illegal activities.

6.2 PROHIBITED USES
    You agree NOT to use the Software to:
    (a) Circumvent detection for illegal purposes;
    (b) Process content depicting illegal activities;
    (c) Violate the privacy rights of others without consent;
    (d) Broadcast content that violates platform terms of service;
    (e) Create deepfakes or manipulated media for malicious purposes.

6.3 AGE REQUIREMENT
    You must be at least 18 years old, or the age of majority in your jurisdiction, to use this Software.

6.4 COMPLIANCE
    You agree to comply with all applicable local, state, national, and international laws and regulations.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

7. DISCLAIMER OF WARRANTIES

7.1 THE SOFTWARE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO:
    (a) IMPLIED WARRANTIES OF MERCHANTABILITY;
    (b) FITNESS FOR A PARTICULAR PURPOSE;
    (c) NON-INFRINGEMENT;
    (d) ACCURACY OR RELIABILITY OF RESULTS.

7.2 THE DEVELOPER DOES NOT WARRANT THAT:
    (a) The Software will meet your requirements;
    (b) The Software will be uninterrupted, timely, secure, or error-free;
    (c) The results obtained from the Software will be accurate or reliable;
    (d) Any errors in the Software will be corrected.

7.3 NO ADVICE OR INFORMATION, WHETHER ORAL OR WRITTEN, OBTAINED FROM THE DEVELOPER SHALL CREATE ANY WARRANTY NOT EXPRESSLY STATED IN THESE TERMS.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

8. LIMITATION OF LIABILITY

8.1 TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT SHALL THE DEVELOPER BE LIABLE FOR ANY:
    (a) INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES;
    (b) LOSS OF PROFITS, REVENUE, DATA, OR BUSINESS OPPORTUNITIES;
    (c) PRIVACY BREACHES RESULTING FROM SOFTWARE MALFUNCTION;
    (d) MISSED DETECTIONS OR FALSE POSITIVES;
    (e) DAMAGES ARISING FROM UNAUTHORIZED ACCESS TO YOUR SYSTEM;
    (f) DAMAGES RESULTING FROM INTERRUPTION OF SERVICE.

8.2 THE TOTAL LIABILITY OF THE DEVELOPER SHALL NOT EXCEED THE AMOUNT YOU PAID FOR THE SOFTWARE (IF ANY), OR $100 USD, WHICHEVER IS LESS.

8.3 SOME JURISDICTIONS DO NOT ALLOW THE EXCLUSION OF CERTAIN WARRANTIES OR LIMITATION OF LIABILITY, SO SOME OF THE ABOVE LIMITATIONS MAY NOT APPLY TO YOU.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

9. INDEMNIFICATION

9.1 You agree to indemnify, defend, and hold harmless the Developer from and against any and all claims, damages, losses, costs, and expenses (including reasonable attorney fees) arising from:
    (a) Your use or misuse of the Software;
    (b) Your violation of these Terms;
    (c) Your violation of any applicable laws or regulations;
    (d) Your violation of any third-party rights;
    (e) Content you broadcast using the Software.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

10. UPDATES AND MODIFICATIONS

10.1 SOFTWARE UPDATES
    (a) The Developer may release updates, patches, or new versions at any time;
    (b) Updates may be required for continued use of the Software;
    (c) New features may be added or removed without notice.

10.2 TERMS MODIFICATIONS
    (a) The Developer reserves the right to modify these Terms at any time;
    (b) Material changes will be communicated through the Software or website;
    (c) Continued use after changes constitutes acceptance of modified Terms;
    (d) If you disagree with changes, you must stop using the Software.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

11. TERMINATION

11.1 LICENSE TERMINATION
    (a) Your license terminates automatically if you violate these Terms;
    (b) The Developer may terminate your license at any time for any reason;
    (c) Upon termination, you must cease all use and destroy all copies.

11.2 SURVIVAL
    Sections 7 (Disclaimer), 8 (Limitation of Liability), 9 (Indemnification), and 13 (Governing Law) shall survive termination.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

12. INTELLECTUAL PROPERTY

12.1 The Software, including its code, design, graphics, and documentation, is protected by copyright and other intellectual property laws.

12.2 "SecureStudio" name and logo are trademarks of the Developer.

12.3 Nothing in these Terms grants you any rights to the Developer's intellectual property except the limited license expressly granted.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

13. GOVERNING LAW AND DISPUTE RESOLUTION

13.1 These Terms shall be governed by and construed in accordance with applicable laws, without regard to conflict of law principles.

13.2 Any disputes arising from these Terms or the Software shall first be attempted to be resolved through good-faith negotiation.

13.3 If negotiation fails, disputes shall be resolved through binding arbitration in accordance with applicable arbitration rules.

13.4 You waive any right to participate in class action lawsuits against the Developer.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

14. GENERAL PROVISIONS

14.1 ENTIRE AGREEMENT
    These Terms constitute the entire agreement between you and the Developer regarding the Software.

14.2 SEVERABILITY
    If any provision is found unenforceable, the remaining provisions shall continue in effect.

14.3 WAIVER
    Failure to enforce any right or provision shall not constitute a waiver.

14.4 ASSIGNMENT
    You may not assign these Terms without the Developer's written consent.

14.5 CONTACT
    For questions about these Terms, please contact the Developer through the official project repository.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

15. ACKNOWLEDGMENT

BY CLICKING "I ACCEPT" OR BY USING THE SOFTWARE, YOU ACKNOWLEDGE THAT:

• You have read and understood these Terms and Conditions;
• You agree to be bound by these Terms and Conditions;
• You are of legal age to enter into this agreement;
• You accept full responsibility for your use of the Software;
• You understand the limitations of AI-based detection;
• You will verify the Software's output before broadcasting.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Last Updated: December 2025
Version: 1.0

© 2025 SecureStudio. All rights reserved.
"""


# Modern Dark Theme Stylesheet
WIZARD_STYLE = """
QWizard {
    background-color: #0d1117;
}
QWizardPage {
    background-color: #0d1117;
    color: #e6edf3;
}
QLabel {
    color: #e6edf3;
}
QLabel#title {
    font-size: 28px;
    font-weight: bold;
    color: #58a6ff;
}
QLabel#subtitle {
    font-size: 14px;
    color: #8b949e;
    margin-bottom: 20px;
}
QLabel#section {
    font-size: 16px;
    font-weight: bold;
    color: #58a6ff;
    margin-top: 10px;
}
QTextEdit {
    background-color: #161b22;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 12px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 12px;
    selection-background-color: #388bfd;
}
QTextEdit:focus {
    border: 1px solid #58a6ff;
}
QCheckBox {
    color: #e6edf3;
    spacing: 10px;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid #30363d;
    background-color: #161b22;
}
QCheckBox::indicator:checked {
    background-color: #238636;
    border-color: #238636;
}
QCheckBox::indicator:hover {
    border-color: #58a6ff;
}
QProgressBar {
    border: none;
    border-radius: 8px;
    text-align: center;
    background-color: #161b22;
    color: #e6edf3;
    font-weight: bold;
    height: 24px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #238636, stop:1 #2ea043);
    border-radius: 8px;
}
QPushButton {
    background-color: #238636;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 14px;
}
QPushButton:hover {
    background-color: #2ea043;
}
QPushButton:pressed {
    background-color: #238636;
}
QPushButton:disabled {
    background-color: #21262d;
    color: #484f58;
}
QPushButton#secondary {
    background-color: #21262d;
    border: 1px solid #30363d;
}
QPushButton#secondary:hover {
    background-color: #30363d;
    border-color: #8b949e;
}
QFrame#card {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px;
}
QFrame#highlight {
    background-color: #161b22;
    border: 1px solid #238636;
    border-radius: 8px;
    padding: 16px;
}
"""


class ModelDownloadThread(QThread):
    """Background thread to download AI models."""
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, model_name: str):
        super().__init__()
        self.model_name = model_name
        self.cancelled = False
    
    def run(self):
        try:
            self.progress_signal.emit(10, "Initializing AI framework...")
            
            from ultralytics import YOLO
            
            self.progress_signal.emit(30, f"Downloading {self.model_name}...")
            self.progress_signal.emit(50, "This may take a moment...")
            
            model = YOLO(self.model_name)
            
            self.progress_signal.emit(90, "Verifying model integrity...")
            
            if model is not None:
                self.progress_signal.emit(100, "Model ready!")
                self.finished_signal.emit(True, "AI Model downloaded successfully!")
            else:
                self.finished_signal.emit(False, "Model verification failed")
                
        except Exception as e:
            logging.error(f"Model download failed: {e}")
            self.finished_signal.emit(False, f"Download failed: {str(e)}")


class WelcomePage(QWizardPage):
    """Welcome page with logo and introduction."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("")
        self.setSubTitle("")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 20, 40, 20)
        
        # Spacer
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Logo
        logo_container = QHBoxLayout()
        logo_label = QLabel()
        logo_path = get_resource_path("assets/SS_LOGO.jpg")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            pixmap = pixmap.scaledToWidth(350, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_container.addWidget(logo_label)
        layout.addLayout(logo_container)
        
        # Title
        title = QLabel("Welcome to SecureStudio")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("AI-Powered Privacy Shield for Live Streaming")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Features card
        features_frame = QFrame()
        features_frame.setObjectName("card")
        features_layout = QVBoxLayout(features_frame)
        features_layout.setSpacing(12)
        
        features_title = QLabel("This setup wizard will help you:")
        features_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #e6edf3;")
        features_layout.addWidget(features_title)
        
        features = [
            ("•", "Review and accept the Terms & Conditions"),
            ("•", "Configure your privacy preferences"),
            ("•", "Download the required AI detection model"),
            ("•", "Get ready to protect your streams!")
        ]
        
        for icon, text in features:
            row = QHBoxLayout()
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("color: #238636; font-size: 16px; font-weight: bold;")
            icon_label.setFixedWidth(24)
            row.addWidget(icon_label)
            text_label = QLabel(text)
            text_label.setStyleSheet("color: #8b949e; font-size: 13px;")
            row.addWidget(text_label)
            row.addStretch()
            features_layout.addLayout(row)
        
        layout.addWidget(features_frame)
        
        # Spacer
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Footer
        footer = QLabel("Click 'Next' to continue with the setup")
        footer.setStyleSheet("color: #8b949e; font-size: 12px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)


class TermsPage(QWizardPage):
    """Terms and Conditions acceptance page."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("")
        self.setSubTitle("")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 20, 40, 20)
        
        # Header
        title = QLabel("Terms and Conditions")
        title.setObjectName("title")
        layout.addWidget(title)
        
        subtitle = QLabel("Please read the following terms carefully before proceeding")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)
        
        # Terms text
        terms_edit = QTextEdit()
        terms_edit.setPlainText(TERMS_AND_CONDITIONS)
        terms_edit.setReadOnly(True)
        terms_edit.setMinimumHeight(320)
        layout.addWidget(terms_edit)
        
        # Accept section
        accept_frame = QFrame()
        accept_frame.setObjectName("highlight")
        accept_layout = QVBoxLayout(accept_frame)
        
        # Accept checkbox
        self.accept_checkbox = QCheckBox("I have read, understood, and agree to the Terms and Conditions")
        self.accept_checkbox.setStyleSheet("font-weight: bold;")
        self.accept_checkbox.stateChanged.connect(self.completeChanged)
        accept_layout.addWidget(self.accept_checkbox)
        
        layout.addWidget(accept_frame)
        
        # Register field
        self.registerField("terms_accepted*", self.accept_checkbox)
    
    def isComplete(self):
        return self.accept_checkbox.isChecked()


class PrivacyPage(QWizardPage):
    """Privacy preferences page."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("")
        self.setSubTitle("")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 20, 40, 20)
        
        # Header
        title = QLabel("Privacy Preferences")
        title.setObjectName("title")
        layout.addWidget(title)
        
        subtitle = QLabel("Help us improve SecureStudio by sharing anonymous diagnostics")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)
        
        # Info card
        info_frame = QFrame()
        info_frame.setObjectName("card")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(16)
        
        # What we collect
        collect_title = QLabel("What we collect (if enabled):")
        collect_title.setObjectName("section")
        info_layout.addWidget(collect_title)
        
        collect_items = [
            "• Error messages and crash reports",
            "• Application performance metrics",
            "• Feature usage statistics",
            "• System info (OS, GPU type)"
        ]
        for item in collect_items:
            label = QLabel(item)
            label.setStyleSheet("color: #8b949e; margin-left: 20px;")
            info_layout.addWidget(label)
        
        # Separator
        info_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        
        # What we DON'T collect
        no_collect_title = QLabel("What we NEVER collect:")
        no_collect_title.setObjectName("section")
        no_collect_title.setStyleSheet("color: #238636; font-size: 16px; font-weight: bold;")
        info_layout.addWidget(no_collect_title)
        
        no_collect_items = [
            "• Video or image data from your camera",
            "• Content from your streams",
            "• Personal information or identifiers",
            "• Anything that could identify you"
        ]
        for item in no_collect_items:
            label = QLabel(item)
            label.setStyleSheet("color: #8b949e; margin-left: 20px;")
            info_layout.addWidget(label)
        
        layout.addWidget(info_frame)
        
        layout.addStretch()
        
        # Consent checkbox frame
        consent_frame = QFrame()
        consent_frame.setObjectName("highlight")
        consent_layout = QVBoxLayout(consent_frame)
        
        self.consent_checkbox = QCheckBox("Yes, I want to help improve SecureStudio by sharing anonymous diagnostics")
        self.consent_checkbox.setChecked(True)
        self.consent_checkbox.setStyleSheet("font-weight: bold;")
        consent_layout.addWidget(self.consent_checkbox)
        
        note = QLabel("You can change this setting at any time in the app settings.")
        note.setStyleSheet("color: #8b949e; font-size: 11px; margin-top: 5px;")
        consent_layout.addWidget(note)
        
        layout.addWidget(consent_frame)
        
        # Desktop shortcut option
        shortcut_frame = QFrame()
        shortcut_frame.setObjectName("card")
        shortcut_layout = QVBoxLayout(shortcut_frame)
        
        shortcut_title = QLabel("Installation Options")
        shortcut_title.setObjectName("section")
        shortcut_layout.addWidget(shortcut_title)
        
        self.shortcut_checkbox = QCheckBox("Create a desktop shortcut for SecureStudio")
        self.shortcut_checkbox.setChecked(True)
        self.shortcut_checkbox.setStyleSheet("margin-top: 8px;")
        shortcut_layout.addWidget(self.shortcut_checkbox)
        
        shortcut_note = QLabel("Adds a shortcut to your desktop for easy access.")
        shortcut_note.setStyleSheet("color: #8b949e; font-size: 11px; margin-left: 28px;")
        shortcut_layout.addWidget(shortcut_note)
        
        layout.addWidget(shortcut_frame)
        
        # Register fields
        self.registerField("share_logs", self.consent_checkbox)
        self.registerField("create_shortcut", self.shortcut_checkbox)


class DownloadPage(QWizardPage):
    """Model download page."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("")
        self.setSubTitle("")
        
        self.download_complete = False
        self.download_thread = None
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 20, 40, 20)
        
        # Header
        title = QLabel("Download AI Model")
        title.setObjectName("title")
        layout.addWidget(title)
        
        subtitle = QLabel("SecureStudio needs to download the AI detection model")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)
        
        # Model info card
        model_frame = QFrame()
        model_frame.setObjectName("card")
        model_layout = QVBoxLayout(model_frame)
        model_layout.setSpacing(12)
        
        model_title = QLabel("YOLO-World v2 (Small)")
        model_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #58a6ff;")
        model_layout.addWidget(model_title)
        
        model_details = [
            ("Size:", "~25 MB"),
            ("Type:", "Real-time object detection"),
            ("Features:", "Custom object detection with text prompts"),
        ]
        
        for label, value in model_details:
            row = QHBoxLayout()
            label_widget = QLabel(label)
            label_widget.setStyleSheet("color: #8b949e;")
            label_widget.setFixedWidth(80)
            row.addWidget(label_widget)
            value_widget = QLabel(value)
            value_widget.setStyleSheet("color: #e6edf3;")
            row.addWidget(value_widget)
            row.addStretch()
            model_layout.addLayout(row)
        
        note = QLabel("Additional models can be downloaded later from Settings if needed.")
        note.setStyleSheet("color: #8b949e; font-size: 11px; margin-top: 10px; font-style: italic;")
        model_layout.addWidget(note)
        
        layout.addWidget(model_frame)
        
        layout.addStretch()
        
        # Progress section
        progress_frame = QFrame()
        progress_frame.setObjectName("card")
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setSpacing(12)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        progress_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Click the button below to download the AI model")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #8b949e;")
        progress_layout.addWidget(self.status_label)
        
        # Download button
        self.download_btn = QPushButton("Download Model")
        self.download_btn.setMinimumHeight(48)
        self.download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_btn.clicked.connect(self.start_download)
        progress_layout.addWidget(self.download_btn)
        
        layout.addWidget(progress_frame)
    
    def initializePage(self):
        self.check_existing_model()
    
    def check_existing_model(self):
        try:
            home = Path.home()
            possible_paths = [
                home / ".cache" / "ultralytics" / "yolov8s-worldv2.pt",
                home / "AppData" / "Roaming" / "Ultralytics" / "yolov8s-worldv2.pt",
                Path("yolov8s-worldv2.pt"),
            ]
            
            for path in possible_paths:
                if path.exists():
                    self.download_complete = True
                    self.progress_bar.setValue(100)
                    self.status_label.setText("Model already downloaded!")
                    self.status_label.setStyleSheet("color: #238636; font-weight: bold;")
                    self.download_btn.setText("Model Ready")
                    self.download_btn.setEnabled(False)
                    self.completeChanged.emit()
                    return
        except Exception:
            pass
    
    def start_download(self):
        self.download_btn.setEnabled(False)
        self.download_btn.setText("Downloading...")
        self.status_label.setStyleSheet("color: #58a6ff;")
        
        self.download_thread = ModelDownloadThread("yolov8s-worldv2.pt")
        self.download_thread.progress_signal.connect(self.on_progress)
        self.download_thread.finished_signal.connect(self.on_finished)
        self.download_thread.start()
    
    def on_progress(self, percent, message):
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)
    
    def on_finished(self, success, message):
        if success:
            self.download_complete = True
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: #238636; font-weight: bold;")
            self.download_btn.setText("Download Complete")
            self.completeChanged.emit()
        else:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: #f85149;")
            self.download_btn.setText("Retry Download")
            self.download_btn.setEnabled(True)
    
    def isComplete(self):
        return self.download_complete


class FinishPage(QWizardPage):
    """Setup complete page."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("")
        self.setSubTitle("")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 20, 40, 20)
        
        layout.addStretch()
        
        # Success header
        success_icon = QLabel("Setup Complete")
        success_icon.setStyleSheet("font-size: 32px; font-weight: bold; color: #238636;")
        success_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(success_icon)
        
        # Title
        title = QLabel("You're All Set!")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("SecureStudio is ready to protect your privacy")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Quick start card
        guide_frame = QFrame()
        guide_frame.setObjectName("card")
        guide_layout = QVBoxLayout(guide_frame)
        guide_layout.setSpacing(12)
        
        guide_title = QLabel("Quick Start Guide")
        guide_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #58a6ff;")
        guide_layout.addWidget(guide_title)
        
        steps = [
            ("1.", "SecureStudio will open with your webcam feed"),
            ("2.", "In OBS, add a 'Video Capture Device' source"),
            ("3.", "Select 'OBS Virtual Camera' as the device"),
            ("4.", "Objects will be automatically detected and blurred!"),
        ]
        
        for num, text in steps:
            row = QHBoxLayout()
            num_label = QLabel(num)
            num_label.setStyleSheet("color: #238636; font-weight: bold; font-size: 14px;")
            num_label.setFixedWidth(24)
            row.addWidget(num_label)
            text_label = QLabel(text)
            text_label.setStyleSheet("color: #e6edf3; font-size: 13px;")
            row.addWidget(text_label)
            row.addStretch()
            guide_layout.addLayout(row)
        
        layout.addWidget(guide_frame)
        
        # Tip
        tip_frame = QFrame()
        tip_frame.setObjectName("highlight")
        tip_layout = QHBoxLayout(tip_frame)
        
        tip_icon = QLabel("Tip:")
        tip_icon.setStyleSheet("font-size: 13px; font-weight: bold; color: #58a6ff;")
        tip_layout.addWidget(tip_icon)
        
        tip_text = QLabel("Use the Settings button to customize what gets detected and blurred!")
        tip_text.setStyleSheet("color: #e6edf3; font-size: 12px;")
        tip_text.setWordWrap(True)
        tip_layout.addWidget(tip_text)
        
        layout.addWidget(tip_frame)
        
        layout.addStretch()


class SetupWizard(QWizard):
    """Main setup wizard dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("SecureStudio Setup")
        self.setFixedSize(650, 620)
        self.setStyleSheet(WIZARD_STYLE)
        
        # Remove default pixmap areas
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)
        
        # Add pages
        self.addPage(WelcomePage())
        self.addPage(TermsPage())
        self.addPage(PrivacyPage())
        self.addPage(DownloadPage())
        self.addPage(FinishPage())
        
        # Button text
        self.setButtonText(QWizard.WizardButton.NextButton, "Next  ->")
        self.setButtonText(QWizard.WizardButton.BackButton, "<-  Back")
        self.setButtonText(QWizard.WizardButton.FinishButton, "Launch SecureStudio")
        self.setButtonText(QWizard.WizardButton.CancelButton, "Exit")
    
    def accept(self):
        settings_manager.set("setup_complete", True)
        settings_manager.set("terms_accepted", True)
        settings_manager.set("share_diagnostic_logs", self.field("share_logs"))
        
        # Create desktop shortcut if requested
        if self.field("create_shortcut"):
            success, result = create_desktop_shortcut()
            if success:
                logging.info(f"Desktop shortcut created: {result}")
            else:
                logging.warning(f"Failed to create desktop shortcut: {result}")
        
        logging.info("Setup wizard completed")
        super().accept()
    
    def reject(self):
        reply = QMessageBox.question(
            self,
            "Exit Setup",
            "SecureStudio requires initial setup to run.\n\nAre you sure you want to exit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            super().reject()


def needs_setup() -> bool:
    """Check if setup wizard needs to be shown."""
    return not settings_manager.get("setup_complete", False)


def run_setup_wizard(app) -> bool:
    """Run the setup wizard."""
    wizard = SetupWizard()
    result = wizard.exec()
    return result == QWizard.DialogCode.Accepted
