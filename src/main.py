"""
Main entry point for Poker AI Assistant.
Integrates capture, detection, strategy, and UI.
"""
import sys
import time
import threading
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal, QObject

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import logger
from src.utils.config_loader import config_loader
from src.capture.window_finder import WindowFinder
from src.capture.screen_grabber import ScreenGrabber
from src.capture.anchor_manager import AnchorManager
from src.capture.region_mapper import RegionMapper
from src.detection.card_detector import CardDetector
from src.detection.game_state import GameStateTracker
from src.strategy.decision_engine import DecisionEngine
from src.ui.display_manager import DisplayManager

class GameLoop(QThread):
    """Background thread for game logic."""
    update_signal = pyqtSignal(object)  # Emits (decision, game_state)
    
    def __init__(self):
        super().__init__()
        self.running = True
        
        # Initialize components
        self.window_finder = WindowFinder()
        self.screen_grabber = ScreenGrabber()
        self.anchor_manager = AnchorManager()
        self.region_mapper = RegionMapper()
        self.card_detector = CardDetector()
        self.tracker = GameStateTracker()
        self.decision_engine = DecisionEngine()
        
        # Load config
        self.anchor_manager.load_config()
        if not self.anchor_manager.active_anchor_name:
            logger.warning("No active anchor found. Please run tools/calibrate_anchors.py")

    def run(self):
        """Main game loop."""
        logger.info("Game Logic Thread Started")
        
        while self.running:
            try:
                # 1. Find Window
                rect = self.window_finder.find_window("PokerStars") # Make configurable
                if not rect:
                    time.sleep(2)
                    continue
                
                # 2. Capture Screen (focusing on window area for efficiency)
                # For simplicity, we might capture full screen or use rect if ScreenGrabber supports it
                # Assuming full screen capture for now to look for anchor
                screen = self.screen_grabber.capture_screen() 
                
                # 3. Find Anchor & Update Regions
                anchor_pos = self.anchor_manager.find_anchor(screen)
                if not anchor_pos:
                    # logger.debug("Anchor not found")
                    time.sleep(0.5)
                    continue
                
                # Update absolute regions based on anchor
                # Note: AnchorManager.find_anchor returns (x, y, w, h)
                # We typically need just (x, y) for get_absolute_regions
                ax, ay, aw, ah = anchor_pos
                regions = self.anchor_manager.get_absolute_regions((ax, ay))
                self.region_mapper.update_regions(regions)
                
                # 4. Detect Cards & State
                # Extract regions for detection
                hole_cards_img = self.screen_grabber.extract_region(screen, regions.get('hole_cards'))
                community_img = self.screen_grabber.extract_region(screen, regions.get('community_cards'))
                
                if hole_cards_img is None:
                    continue
                
                hole_cards = self.card_detector.detect_hand(hole_cards_img)
                community_cards = self.card_detector.detect_hand(community_img)
                
                # TODO: Implement Pot/Stack OCR here
                pot_size = 0.0
                stack_size = 100.0
                current_bet = 0.0
                
                # 5. Update Game State
                game_state = self.tracker.update_state(
                    hole_cards=hole_cards,
                    community_cards=community_cards,
                    pot_size=pot_size,
                    stack_size=stack_size,
                    current_bet=current_bet
                )
                
                # 6. Make Decision
                decision = self.decision_engine.decide(game_state)
                
                # 7. Update UI
                self.update_signal.emit({
                    'decision': decision,
                    'game_state': game_state
                })
                
                # Pace the loop
                time.sleep(1.0) # Adjust based on performance needs
                
            except Exception as e:
                logger.error(f"Error in game loop: {e}")
                time.sleep(1)

    def stop(self):
        self.running = False
        self.wait()

def main():
    """Main application entry point."""
    logger.info("="*50)
    logger.info("Poker AI Assistant - Starting Up")
    logger.info("="*50)
    
    try:
        # Initialize UI Manager (creates QApplication)
        # Note: We don't verify WindowFinder etc here, GameLoop handles it
        display_manager = DisplayManager(None) # RegionMapper passed to overlay if needed
        
        # Start Game Logic Thread
        game_thread = GameLoop()
        game_thread.update_signal.connect(display_manager.update_overlay)
        game_thread.start()
        
        # Start UI Event Loop
        sys.exit(display_manager.app.exec_())
        
    except Exception as e:
        logger.critical(f"Critical error: {e}")
        return 1

if __name__ == "__main__":
    main()
