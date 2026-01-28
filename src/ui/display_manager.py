"""
Display Manager for Poker AI Assistant.
Handles the PyQt5 overlay window and painting.
"""
import sys
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush

class OverlaySignal(QObject):
    """Signals for overlay updates."""
    update_signal = pyqtSignal(object)

class PokerOverlay(QMainWindow):
    """Transparent overlay window."""
    
    def __init__(self, region_mapper):
        super().__init__()
        self.region_mapper = region_mapper
        self.decision = None
        self.game_state = None
        
        # Window setup
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Fullscreen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(0, 0, screen.width(), screen.height())
        
        self.show()
        
    def update_data(self, data):
        """Update display data."""
        self.decision = data.get('decision')
        self.game_state = data.get('game_state')
        self.repaint()
        
    def paintEvent(self, event):
        """Draw overlay elements."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. Draw HUD box in top-right or near table
        if self.decision:
            self._draw_hud(painter)
            
        # 2. Highlight cards if needed (optional)
        # 3. Draw debug info (optional)
        
    def _draw_hud(self, painter):
        """Draw main heads-up display."""
        # Config
        bg_color = QColor(0, 0, 0, 200)
        text_color = QColor(255, 255, 255)
        accent_color = QColor(0, 255, 0)  # Green for positive
        
        if self.decision.action == 'fold':
            accent_color = QColor(255, 0, 0)
        elif self.decision.action == 'raise':
            accent_color = QColor(0, 150, 255) # Blue
            
        # Position (e.g., top left corner)
        x, y = 50, 50
        w, h = 300, 180
        
        # Draw background
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(x, y, w, h, 10, 10)
        
        # Draw Side Bar
        painter.setBrush(QBrush(accent_color))
        painter.drawRoundedRect(x, y, 10, h, 10, 10)
        
        # Text Header (Action)
        painter.setPen(QPen(text_color))
        painter.setFont(QFont("Arial", 16, QFont.Bold))
        action_text = f"{self.decision.action.upper()}"
        if self.decision.amount_bb:
            action_text += f" {self.decision.amount_bb} BB"
        painter.drawText(x + 20, y + 30, action_text)
        
        # Text Details (Hand Strength)
        painter.setFont(QFont("Arial", 12))
        hand_text = f"Hand: {self.decision.hand_evaluation.description}"
        painter.drawText(x + 20, y + 60, hand_text)
        
        # Equity
        equity_text = f"Equity: {self.decision.equity:.1f}%"
        painter.drawText(x + 20, y + 85, equity_text)
        
        # Reasoning
        painter.setFont(QFont("Arial", 10))
        y_reason = y + 115
        for reason in self.decision.reasoning[:3]: # Limit lines
            painter.drawText(x + 20, y_reason, f"• {reason}")
            y_reason += 20

class DisplayManager:
    """Manages the PyQt application and overlay window."""
    
    def __init__(self, region_mapper):
        self.app = QApplication(sys.argv)
        self.overlay = PokerOverlay(region_mapper)
        self.signals = OverlaySignal()
        self.signals.update_signal.connect(self.overlay.update_data)
        
        # Start GUI thread loop in main thread, logic in background
        # Note: In this architecture, main.py will run the logic loop
        # and forcefully process events, or run logic in a thread.
        # Recommended: Logic in thread, GUI in main.
        
    def update_overlay(self, decision, game_state):
        """Thread-safe update trigger."""
        data = {
            'decision': decision,
            'game_state': game_state
        }
        self.signals.update_signal.emit(data)
        
    def process_events(self):
        """Process GUI events (if running in same thread loop)."""
        self.app.processEvents()
