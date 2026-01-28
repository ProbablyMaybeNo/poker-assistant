
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from src.utils.logger import logger

class CardDetector:
    """
    Identifies playing cards using template matching.
    Uses separate templates for Ranks (A, K, Q...) and Suits (h, d, c, s).
    """
    
    def __init__(self, templates_dir: str):
        self.templates_dir = Path(templates_dir)
        self.rank_templates: Dict[str, np.ndarray] = {}
        self.suit_templates: Dict[str, np.ndarray] = {}
        self.load_templates()
        
    def load_templates(self):
        """Load rank and suit templates from disk."""
        rank_dir = self.templates_dir / "ranks"
        suit_dir = self.templates_dir / "suits"
        
        # Load Ranks
        if rank_dir.exists():
            for f in rank_dir.glob("*.png"):
                img = cv2.imread(str(f), cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    self.rank_templates[f.stem] = img
        
        # Load Suits
        if suit_dir.exists():
            for f in suit_dir.glob("*.png"):
                img = cv2.imread(str(f), cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    self.suit_templates[f.stem] = img
                    
        logger.info(f"Loaded {len(self.rank_templates)} ranks and {len(self.suit_templates)} suits")

    def detect_card(self, card_image: np.ndarray) -> Optional[str]:
        """
        Identify a single card image.
        
        Args:
            card_image: BGR image of a single card
            
        Returns:
            String representing card (e.g. 'Ah', 'Td') or None if unknown
        """
        if card_image is None or card_image.size == 0:
            return None
            
        # Preprocess
        gray = cv2.cvtColor(card_image, cv2.COLOR_BGR2GRAY)
        
        # We process the top corner for rank and suit as per build_template_db logic
        # Crop roughly where we expect them
        h, w = gray.shape
        roi_w = int(w * 0.45)
        roi_h = int(h * 0.65) # Extended to cover suit
        roi = gray[0:roi_h, 0:roi_w]
        
        # Identify Rank
        best_rank = self._match_template(roi, self.rank_templates)
        
        # Identify Suit
        # Suit is usually below the rank. We can search the whole ROI or split.
        best_suit = self._match_template(roi, self.suit_templates)
        
        if best_rank and best_suit:
            return f"{best_rank}{best_suit}"
            
        return None
        
    def _match_template(self, image: np.ndarray, templates: Dict[str, np.ndarray]) -> Optional[str]:
        """Find best matching template."""
        best_score = -1.0
        best_label = None
        
        for label, template in templates.items():
            # Template matching requires template <= image
            if template.shape[0] > image.shape[0] or template.shape[1] > image.shape[1]:
                continue
                
            res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            
            if max_val > best_score:
                best_score = max_val
                best_label = label
                
        # Threshold?
        # Debugging: Print scores to see why it fails
        if best_score > 0.1:
             print(f"DEBUG: Best match for ROI: {best_label} with score {best_score:.4f}")
        
        if best_score > 0.85:  # Confidence threshold
            return best_label
            
        return None

if __name__ == "__main__":
    # Test
    project_root = Path(__file__).parent.parent.parent
    detector = CardDetector(str(project_root / "models" / "templates"))
