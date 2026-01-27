
import sys
import os
import json
import cv2
import numpy as np
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QLineEdit, QMessageBox, QComboBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap

# Add project root to path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.capture.window_finder import WindowFinder
from src.capture.screen_grabber import ScreenGrabber
from src.detection.card_detector import CardDetector
from src.utils.logger import logger

class TemplateCreatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Poker AI - Template Creator")
        self.setGeometry(100, 100, 500, 400)
        
        self.config_path = Path(project_root) / "config" / "regions.json"
        self.templates_dir = Path(project_root) / "models" / "card_templates"
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        self.calibration_data = self.load_config()
        self.finder = None
        self.grabber = ScreenGrabber()
        self.detector = None
        
        # Try to load detector
        try: 
            templates_path = Path(project_root) / "models" / "templates"
            if templates_path.exists():
                self.detector = CardDetector(str(templates_path))
        except Exception as e:
            logger.error(f"Could not init detector: {e}")

        if self.calibration_data:
            self.finder = WindowFinder(window_title=self.calibration_data["window"]["title"])
        
        self.current_left_card = None
        self.current_right_card = None
        
        self.init_ui()
        
    def load_config(self):
        if not self.config_path.exists():
            QMessageBox.critical(self, "Error", "regions.json not found! Run calibration first.")
            return None
        with open(self.config_path, "r") as f:
            return json.load(f)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Instruction
        layout.addWidget(QLabel("1. Select source seat (where cards are).\n2. Click 'Capture' when cards are dealt.\n3. Enter labels (e.g. As, Td) and Save."))
        
        # Region Selector
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Capture Source:"))
        self.combo_regions = QComboBox()
        
        # Populate with calibration regions
        if self.calibration_data and "regions" in self.calibration_data:
            region_keys = sorted(self.calibration_data["regions"].keys())
            # Prioritize hero_cards
            if "hero_cards" in region_keys:
                region_keys.remove("hero_cards")
                region_keys.insert(0, "hero_cards")
            self.combo_regions.addItems(region_keys)
            
        target_layout.addWidget(self.combo_regions)
        layout.addLayout(target_layout)
        
        # Capture Button
        self.btn_capture = QPushButton("Capture From Selected Region")
        self.btn_capture.clicked.connect(self.capture_cards)
        self.btn_capture.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        layout.addWidget(self.btn_capture)
        
        # Cards Display Area
        cards_layout = QHBoxLayout()
        
        # Left Card
        left_layout = QVBoxLayout()
        self.lbl_left_img = QLabel("Left Card")
        self.lbl_left_img.setAlignment(Qt.AlignCenter)
        self.lbl_left_img.setFixedSize(100, 140)
        self.lbl_left_img.setStyleSheet("border: 1px solid #ccc; background-color: #eee;")
        
        self.input_left = QLineEdit()
        self.input_left.setPlaceholderText("e.g. As")
        self.input_left.setAlignment(Qt.AlignCenter)
        
        left_layout.addWidget(self.lbl_left_img)
        left_layout.addWidget(self.input_left)
        
        # Right Card
        right_layout = QVBoxLayout()
        self.lbl_right_img = QLabel("Right Card")
        self.lbl_right_img.setAlignment(Qt.AlignCenter)
        self.lbl_right_img.setFixedSize(100, 140)
        self.lbl_right_img.setStyleSheet("border: 1px solid #ccc; background-color: #eee;")
        
        self.input_right = QLineEdit()
        self.input_right.setPlaceholderText("e.g. Kh")
        self.input_right.setAlignment(Qt.AlignCenter)
        
        right_layout.addWidget(self.lbl_right_img)
        right_layout.addWidget(self.input_right)
        
        cards_layout.addLayout(left_layout)
        cards_layout.addLayout(right_layout)
        layout.addLayout(cards_layout)
        
        # Save Button
        self.btn_save = QPushButton("Save Templates")
        self.btn_save.clicked.connect(self.save_templates)
        self.btn_save.setEnabled(False)
        layout.addWidget(self.btn_save)
        
        # Status
        self.lbl_status = QLabel("Ready")
        layout.addWidget(self.lbl_status)

    def capture_cards(self):
        if not self.finder:
            self.lbl_status.setText("Error: Window Finder not init")
            return
            
        found = self.finder.find_window()
        if not found:
            self.lbl_status.setText("Error: Game Window not found!")
            return
            
        # Get window position for offset
        rect = self.finder.get_window_rect()
        if not rect:
             self.lbl_status.setText("Error: Could not get window rect")
             return
        win_x, win_y, _, _ = rect

        # Get selected region
        region_name = self.combo_regions.currentText()
        if not region_name or region_name not in self.calibration_data["regions"]:
            self.lbl_status.setText(f"Error: Invalid region {region_name}")
            return
            
        target_region = self.calibration_data["regions"][region_name]
        rx, ry, rw, rh = target_region["x"], target_region["y"], target_region["width"], target_region["height"]
        
        if rw <= 0 or rh <= 0:
            self.lbl_status.setText("Error: Invalid region dims")
            return
        
        # Calculate absolute capture coordinates
        abs_x = win_x + rx
        abs_y = win_y + ry
        
        # Capture
        capture_img = self.grabber.capture_region(abs_x, abs_y, rw, rh)
        
        # DEBUG: Save full capture to see what we are grabbing
        cv2.imwrite("debug_last_capture_full.png", capture_img)
        print(f"DEBUG: Saved full capture to debug_last_capture_full.png. Size: {capture_img.shape}")

        if capture_img is None:
            self.lbl_status.setText("Failed to capture screen!")
            return
            
        # Split logic
        mid_x = rw // 2
        self.current_left_card = capture_img[:, :mid_x]
        self.current_right_card = capture_img[:, mid_x:]
        
        # Display
        self.display_image(self.current_left_card, self.lbl_left_img)
        self.display_image(self.current_right_card, self.lbl_right_img)
        
        # Auto-detect if detector is available
        if hasattr(self, 'detector') and self.detector:
             pred_left = self.detector.detect_card(self.current_left_card)
             if pred_left:
                 self.input_left.setText(pred_left)
                 
             pred_right = self.detector.detect_card(self.current_right_card)
             if pred_right:
                 self.input_right.setText(pred_right)

        self.btn_save.setEnabled(True)
        self.lbl_status.setText(f"Captured from {region_name}! Check labels & Save.")
        self.input_left.setFocus()

    def display_image(self, cv_img, label):
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        label.setPixmap(pixmap.scaled(label.width(), label.height(), Qt.KeepAspectRatio))

    def save_templates(self):
        saved_count = 0
        
        # Save Left
        name_l = self.input_left.text().strip()
        if name_l and self.current_left_card is not None:
            path = self.templates_dir / f"{name_l}.png"
            cv2.imwrite(str(path), self.current_left_card)
            saved_count += 1
            
        # Save Right
        name_r = self.input_right.text().strip()
        if name_r and self.current_right_card is not None:
            path = self.templates_dir / f"{name_r}.png"
            cv2.imwrite(str(path), self.current_right_card)
            saved_count += 1
            
        if saved_count > 0:
            self.lbl_status.setText(f"Saved {saved_count} templates!")
            self.input_left.clear()
            self.input_right.clear()
            self.btn_save.setEnabled(False)
            self.lbl_left_img.clear()
            self.lbl_right_img.clear()
            self.lbl_left_img.setText("Saved")
            self.lbl_right_img.setText("Saved")
        else:
            self.lbl_status.setText("Nothing to save (names empty)")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TemplateCreatorApp()
    window.show()
    sys.exit(app.exec_())
