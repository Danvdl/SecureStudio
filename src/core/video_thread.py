import cv2
import numpy as np
import pyvirtualcam
import logging
import time
from ultralytics import YOLO
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage
from src.utils.settings import settings_manager

class VideoWorker(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    status_signal = pyqtSignal(str) # Emits status updates to the UI
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.auto_blur_enabled = settings_manager.get("auto_blur")
        self.show_output = settings_manager.get("show_preview")
        self.target_classes = settings_manager.get("target_classes")
        self.conf_threshold = settings_manager.get("confidence_threshold")
        self.use_custom_model = settings_manager.get("use_custom_model")
        self.model_size = settings_manager.get("model_size")
        self.blur_style = settings_manager.get("blur_style")
        self.smooth_factor = settings_manager.get("smooth_factor")
        self.custom_classes = self._get_combined_classes()
        self.model = None 
        self.model_type = None # 'standard' or 'world'
        
        # Persistence State
        self.active_blurs = [] # List of dicts: {'box': [x1,y1,x2,y2], 'label': str, 'last_seen': time.time()}
        self.persistence_duration = 0.5 # Seconds to keep blur alive after detection loss

    def _get_combined_classes(self):
        # Combine checkbox selections with manual text input and deduplicate
        combined = settings_manager.get("security_classes_enabled") + settings_manager.get("custom_classes")
        return list(set(combined)) # Deduplicate

    def update_settings(self):
        self.target_classes = settings_manager.get("target_classes")
        self.conf_threshold = settings_manager.get("confidence_threshold")
        self.blur_style = settings_manager.get("blur_style")
        self.smooth_factor = settings_manager.get("smooth_factor")
        
        # Check if model needs reloading
        new_use_custom = settings_manager.get("use_custom_model")
        new_model_size = settings_manager.get("model_size")
        new_custom_classes = self._get_combined_classes()
        
        # Reload if mode changed OR size changed
        if new_use_custom != self.use_custom_model or new_model_size != self.model_size:
            self.use_custom_model = new_use_custom
            self.model_size = new_model_size
            self.model = None # Force reload
        elif self.use_custom_model and set(new_custom_classes) != set(self.custom_classes):
            self.custom_classes = new_custom_classes
            if self.model:
                logging.info(f"Updating custom classes: {self.custom_classes}")
                self.model.set_classes(self.custom_classes)

    def load_model(self):
        if self.use_custom_model:
            # Construct model name based on size: yolov8s-worldv2.pt, yolov8m-worldv2.pt, etc.
            model_name = f"yolov8{self.model_size}-worldv2.pt"
            
            if self.model_type != f'world-{self.model_size}':
                self.status_signal.emit(f"Loading YOLO-World {self.model_size.upper()} (Security Mode)...")
                logging.info(f"Loading {model_name}...")
                self.model = YOLO(model_name)
                self.model_type = f'world-{self.model_size}'
            
            # Set custom classes
            self.custom_classes = self._get_combined_classes()
            logging.info(f"Setting custom classes: {self.custom_classes}")
            if not self.custom_classes:
                # Fallback if nothing selected
                self.custom_classes = ["credit card"]
                
            self.model.set_classes(self.custom_classes)
            # World models often need lower confidence for custom prompts
            if self.conf_threshold > 0.3:
                logging.info("Lowering confidence threshold for World model to 0.2")
                self.conf_threshold = 0.2
        else:
            if self.model_type != 'standard':
                self.status_signal.emit("Loading Standard AI Model...")
                logging.info("Loading YOLOv8 Nano...")
                self.model = YOLO('yolov8n.pt')
                self.model_type = 'standard'

    def apply_blur_effect(self, img, x1, y1, x2, y2):
        # Ensure bounds
        h, w = img.shape[:2]
        y1, y2 = max(0, y1), min(h, y2)
        x1, x2 = max(0, x1), min(w, x2)
        
        if x2 <= x1 or y2 <= y1:
            return

        roi = img[y1:y2, x1:x2]
        
        if self.blur_style == "pixelate":
            # Pixelate
            h_roi, w_roi = roi.shape[:2]
            # Pixel size relative to ROI size, or fixed? Fixed is usually better for "censored" look.
            # Let's say 10x10 blocks.
            w_small = max(1, w_roi // 10)
            h_small = max(1, h_roi // 10)
            small = cv2.resize(roi, (w_small, h_small), interpolation=cv2.INTER_LINEAR)
            pixelated = cv2.resize(small, (w_roi, h_roi), interpolation=cv2.INTER_NEAREST)
            img[y1:y2, x1:x2] = pixelated
            
        elif self.blur_style == "solid":
            # Solid Black
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 0), -1)
            
        else: # "gaussian" or default
            # Heavy Gaussian Blur
            # Kernel size must be odd
            ksize = 51
            # Ensure ksize is not larger than ROI
            ksize = min(ksize, min(roi.shape[:2])) | 1 
            if ksize > 1:
                blurred = cv2.GaussianBlur(roi, (ksize, ksize), 0)
                img[y1:y2, x1:x2] = blurred

    def run(self):
        width = settings_manager.get("obs_width")
        height = settings_manager.get("obs_height")
        fps = settings_manager.get("fps")

        # 1. Load YOLO Model
        if self.model is None:
            self.load_model()

        # 2. Open Camera
        self.status_signal.emit("Connecting to Camera...")
        logging.info("Opening camera...")
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            logging.error("Error: Could not open video device.")
            self.status_signal.emit("Error: Camera Not Found")
            return
        logging.info("Camera opened successfully.")

        # Set resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        # 3. Initialize Virtual Camera
        self.status_signal.emit("Starting Virtual Camera...")
        try:
            cam = pyvirtualcam.Camera(width=width, height=height, fps=fps, fmt=pyvirtualcam.PixelFormat.BGR)
            logging.info(f"Virtual Camera Active: {cam.device}")
            self.status_signal.emit(f"Active: {cam.device}")
        except Exception as e:
            logging.error(f"Virtual Camera Error: {e}")
            logging.warning("Running in GUI-only mode (no OBS output).")
            self.status_signal.emit("Warning: Virtual Cam Failed (GUI Only)")
            cam = None

        logging.info("Starting video loop...")
        
        while self.running:
            try:
                ret, img = cap.read()
                if not ret:
                    logging.error("Failed to read frame from camera.")
                    self.status_signal.emit("Error: Camera Disconnected")
                    break
                
                # Resize to ensure it matches OBS/VirtualCam config
                img = cv2.resize(img, (width, height))
                display_img = img.copy() 
                current_time = time.time()

                # 4. Detection & Blur Logic
                if self.auto_blur_enabled:
                    # Reload model if needed (e.g. settings changed and model was set to None)
                    if self.model is None:
                        self.load_model()

                    # Run YOLO inference
                    results = self.model(img, verbose=False, conf=self.conf_threshold)
                    
                    # Collect new detections
                    new_detections = []
                    
                    for result in results:
                        for box in result.boxes:
                            cls_id = int(box.cls[0])
                            
                            # Logic for Standard vs World
                            should_blur = False
                            if self.use_custom_model:
                                # In World mode, we blur EVERYTHING detected because we only set specific classes
                                should_blur = True
                            else:
                                # In Standard mode, we check against the target list
                                if cls_id in self.target_classes:
                                    should_blur = True
                            
                            if should_blur:
                                x1, y1, x2, y2 = map(float, box.xyxy[0]) # Use float for smoothing
                                label = "BLURRED"
                                if self.use_custom_model and result.names:
                                    label = result.names[cls_id]
                                new_detections.append({'box': [x1, y1, x2, y2], 'label': label})

                    # Update Active Blurs (Persistence & Smoothing Logic)
                    next_active_blurs = []
                    used_old_indices = set()
                    
                    # Match new detections to old active blurs for smoothing
                    for det in new_detections:
                        # Find best match in active_blurs
                        best_iou = 0
                        best_idx = -1
                        dx1, dy1, dx2, dy2 = det['box']
                        det_area = (dx2 - dx1) * (dy2 - dy1)
                        
                        for i, old in enumerate(self.active_blurs):
                            if i in used_old_indices: continue
                            
                            ox1, oy1, ox2, oy2 = old['box']
                            
                            # Calculate IoU
                            ix1 = max(dx1, ox1)
                            iy1 = max(dy1, oy1)
                            ix2 = min(dx2, ox2)
                            iy2 = min(dy2, oy2)
                            
                            if ix2 > ix1 and iy2 > iy1:
                                intersection = (ix2 - ix1) * (iy2 - iy1)
                                old_area = (ox2 - ox1) * (oy2 - oy1)
                                union = det_area + old_area - intersection
                                iou = intersection / union if union > 0 else 0
                                
                                if iou > 0.3: # Threshold to consider it the same object
                                    if iou > best_iou:
                                        best_iou = iou
                                        best_idx = i
                        
                        if best_idx != -1:
                            # Match found, apply smoothing
                            old_box = self.active_blurs[best_idx]['box']
                            new_box = det['box']
                            
                            # Smooth: smoothed = old * factor + new * (1 - factor)
                            s_box = []
                            for o, n in zip(old_box, new_box):
                                val = o * self.smooth_factor + n * (1.0 - self.smooth_factor)
                                s_box.append(val)
                                
                            next_active_blurs.append({
                                'box': s_box,
                                'label': det['label'],
                                'last_seen': current_time
                            })
                            used_old_indices.add(best_idx)
                        else:
                            # No match, new object
                            next_active_blurs.append({
                                'box': det['box'],
                                'label': det['label'],
                                'last_seen': current_time
                            })
                            
                    # Add remaining old blurs (Persistence)
                    for i, old in enumerate(self.active_blurs):
                        if i not in used_old_indices:
                            if current_time - old['last_seen'] < self.persistence_duration:
                                next_active_blurs.append(old)
                    
                    self.active_blurs = next_active_blurs
                    
                    # Apply Blurs
                    for blur in self.active_blurs:
                        # Convert float box to int for drawing
                        x1, y1, x2, y2 = map(int, blur['box'])
                        
                        # Apply the selected blur effect
                        self.apply_blur_effect(img, x1, y1, x2, y2)
                            
                        # Draw Red Box for Director View (GUI)
                        cv2.rectangle(display_img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(display_img, blur['label'], (x1, y1-10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)

                # 5. Output to OBS Virtual Camera
                if cam:
                    cam.send(img)
                    cam.sleep_until_next_frame()
                else:
                    QThread.msleep(int(1000/fps)) 

                # 6. Output to GUI
                final_display = img if self.show_output else display_img
                rgb_image = cv2.cvtColor(final_display, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
                self.change_pixmap_signal.emit(qt_image)
            
            except Exception as e:
                logging.error(f"Error in video loop: {e}")
                # Don't break, just continue to next frame
                QThread.msleep(100)
        
        if cam:
            cam.close()
        cap.release()
        
        if cam:
            cam.close()
        cap.release()

    def stop(self):
        self.running = False
