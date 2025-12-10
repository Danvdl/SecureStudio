import cv2
import numpy as np
import pyvirtualcam
import logging
import time
import torch
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
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logging.info(f"Using inference device: {self.device}")
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
        # Each entry: {track_id: {'box': [x1,y1,x2,y2], 'velocity': [vx1,vy1,vx2,vy2], 'label': str, 'last_seen': time.time()}}
        self.active_blurs = {}
        self.persistence_duration = 0.5 # Seconds to keep blur alive after detection loss
        
        # Skip-Frame Detection: Run AI every N frames, interpolate in between
        self.detection_interval = 2  # Run detection every 2nd frame
        self.frame_counter = 0

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
                self.model.to(self.device)
                self.model_type = f'world-{self.model_size}'
            
            # Set custom classes
            self.custom_classes = self._get_combined_classes()
            logging.info(f"Setting custom classes: {self.custom_classes}")
            if not self.custom_classes:
                # Fallback if nothing selected
                self.custom_classes = ["credit card"]
                
            self.model.set_classes(self.custom_classes)
            # World models often need lower confidence for custom prompts
            # if self.conf_threshold > 0.3:
            #    logging.info("Lowering confidence threshold for World model to 0.2")
            #    self.conf_threshold = 0.2
        else:
            if self.model_type != 'standard':
                self.status_signal.emit("Loading Standard AI Model...")
                logging.info("Loading YOLOv8 Nano...")
                self.model = YOLO('yolov8n.pt')
                self.model.to(self.device)
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
            ksize = 25
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

                    self.frame_counter += 1
                    run_detection = (self.frame_counter % self.detection_interval == 0)
                    
                    # --- Skip-Frame: Only run AI every N frames ---
                    if run_detection:
                        # --- Downscale for fast inference (e.g., 640x360) ---
                        INFERENCE_WIDTH = 640
                        INFERENCE_HEIGHT = int(INFERENCE_WIDTH * (height / width)) # Maintain aspect ratio
                        
                        # 1. Create a smaller frame for the AI model
                        inference_img = cv2.resize(img, (INFERENCE_WIDTH, INFERENCE_HEIGHT))

                        # 2. Run YOLO inference on the smaller frame
                        # Use tracking (persist=True) for temporal consistency
                        results = self.model.track(inference_img, verbose=False, conf=self.conf_threshold, device=self.device, persist=True, tracker="bytetrack.yaml")
                        
                        # Calculate the scaling factors
                        scale_x = width / INFERENCE_WIDTH
                        scale_y = height / INFERENCE_HEIGHT

                        # Collect new detections
                        current_frame_ids = set()
                        
                        for result in results:
                            if result.boxes:
                                # Extract boxes, classes, and IDs (if available)
                                boxes = result.boxes.xyxy.cpu().numpy()
                                clss = result.boxes.cls.cpu().numpy()
                                ids = result.boxes.id.cpu().numpy() if result.boxes.id is not None else None
                                
                                for i, box in enumerate(boxes):
                                    cls_id = int(clss[i])
                                    track_id = int(ids[i]) if ids is not None else -1
                                    
                                    # Logic for Standard vs World
                                    should_blur = False
                                    if self.use_custom_model:
                                        # Strict Filter: Only blur if the detected name matches our custom list
                                        # This prevents "leaked" COCO classes (like 'bed') from appearing
                                        detected_name = result.names[cls_id]
                                        if detected_name in self.custom_classes:
                                            should_blur = True
                                    else:
                                        if cls_id in self.target_classes:
                                            should_blur = True
                                    
                                    if should_blur:
                                        # Get bounding box coordinates from the smaller image
                                        x1_small, y1_small, x2_small, y2_small = box
                                        
                                        # 3. Rescale coordinates to the original 1080p size
                                        x1 = x1_small * scale_x
                                        y1 = y1_small * scale_y
                                        x2 = x2_small * scale_x
                                        y2 = y2_small * scale_y
                                        
                                        new_box = [x1, y1, x2, y2]
                                        label = "BLURRED"
                                        if self.use_custom_model and result.names:
                                            label = result.names[cls_id]
                                        
                                        # If we have a track ID, use it for smoothing
                                        if track_id != -1:
                                            current_frame_ids.add(track_id)
                                            if track_id in self.active_blurs:
                                                # Get previous state
                                                old_data = self.active_blurs[track_id]
                                                old_box = old_data['box']
                                                old_velocity = old_data.get('velocity', [0, 0, 0, 0])
                                                
                                                # Calculate new velocity (change per frame)
                                                new_velocity = [n - o for o, n in zip(old_box, new_box)]
                                                
                                                # Adaptive smoothing: less smoothing when moving fast
                                                speed = sum(abs(v) for v in new_velocity) / 4
                                                adaptive_smooth = self.smooth_factor
                                                if speed > 20:  # Fast motion threshold
                                                    adaptive_smooth = max(0.1, self.smooth_factor - 0.3)
                                                
                                                # Smooth the box position
                                                s_box = []
                                                for o, n in zip(old_box, new_box):
                                                    val = o * adaptive_smooth + n * (1.0 - adaptive_smooth)
                                                    s_box.append(val)
                                                
                                                # Box size stabilization: prevent "breathing"
                                                old_w = old_box[2] - old_box[0]
                                                old_h = old_box[3] - old_box[1]
                                                new_w = s_box[2] - s_box[0]
                                                new_h = s_box[3] - s_box[1]
                                                
                                                # If size change is small (<5%), keep old size
                                                if abs(new_w - old_w) / max(old_w, 1) < 0.05:
                                                    center_x = (s_box[0] + s_box[2]) / 2
                                                    s_box[0] = center_x - old_w / 2
                                                    s_box[2] = center_x + old_w / 2
                                                if abs(new_h - old_h) / max(old_h, 1) < 0.05:
                                                    center_y = (s_box[1] + s_box[3]) / 2
                                                    s_box[1] = center_y - old_h / 2
                                                    s_box[3] = center_y + old_h / 2
                                                
                                                # Smooth velocity for prediction
                                                s_velocity = [ov * 0.5 + nv * 0.5 for ov, nv in zip(old_velocity, new_velocity)]
                                                
                                                self.active_blurs[track_id] = {
                                                    'box': s_box,
                                                    'velocity': s_velocity,
                                                    'label': label,
                                                    'last_seen': current_time
                                                }
                                            else:
                                                # New track
                                                self.active_blurs[track_id] = {
                                                    'box': new_box,
                                                    'velocity': [0, 0, 0, 0],
                                                    'label': label,
                                                    'last_seen': current_time
                                                }
                                        else:
                                            # Fallback for no ID
                                            temp_id = -1000 - i
                                            self.active_blurs[temp_id] = {
                                                'box': new_box,
                                                'velocity': [0, 0, 0, 0],
                                                'label': label,
                                                'last_seen': current_time
                                            }
                                            current_frame_ids.add(temp_id)
                    else:
                        # Non-detection frame: Predict positions using velocity
                        current_frame_ids = set(self.active_blurs.keys())
                        for tid, data in self.active_blurs.items():
                            if tid >= 0:  # Only predict for tracked objects
                                velocity = data.get('velocity', [0, 0, 0, 0])
                                # Apply velocity prediction
                                predicted_box = [b + v for b, v in zip(data['box'], velocity)]
                                data['box'] = predicted_box

                    # Prune old blurs (Persistence)
                    keys_to_remove = []
                    for tid, data in self.active_blurs.items():
                        if current_time - data['last_seen'] > self.persistence_duration:
                            keys_to_remove.append(tid)
                        elif tid < -900 and tid not in current_frame_ids:
                             # Remove temporary IDs immediately if not in current frame
                             keys_to_remove.append(tid)
                             
                    for k in keys_to_remove:
                        del self.active_blurs[k]
                    
                    # Apply Blurs
                    for blur in self.active_blurs.values():
                        # Convert float box to int for drawing
                        x1, y1, x2, y2 = map(int, blur['box'])
                        
                        # --- SMART ADDITION: Padding ---
                        # Add 15% padding to ensure coverage
                        pad_x = int((x2 - x1) * 0.15)
                        pad_y = int((y2 - y1) * 0.15)

                        x1 = max(0, x1 - pad_x)
                        y1 = max(0, y1 - pad_y)
                        x2 = min(width, x2 + pad_x)
                        y2 = min(height, y2 + pad_y)
                        # -------------------------------
                        
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
