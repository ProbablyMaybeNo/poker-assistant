"""
Fast screen capture using MSS library.
Captures specific regions of the screen efficiently.
"""
import mss
import numpy as np
from PIL import Image
from typing import Tuple, Optional
from src.utils.logger import logger

class ScreenGrabber:
    """Efficient screen region capture."""
    
    def __init__(self):
        """Initialize screen grabber."""
        self.sct = mss.mss()
        self.last_capture = None
        self.capture_count = 0
    
    def capture_region(self, 
                       x: int, 
                       y: int, 
                       width: int, 
                       height: int) -> Optional[np.ndarray]:
        """
        Capture specific screen region.
        
        Args:
            x: Left coordinate
            y: Top coordinate
            width: Region width
            height: Region height
        
        Returns:
            Numpy array (BGR format) or None on error
        """
        try:
            # Define monitor region
            monitor = {
                "top": y,
                "left": x,
                "width": width,
                "height": height
            }
            
            # Capture screenshot
            screenshot = self.sct.grab(monitor)
            
            # Convert to numpy array (RGB)
            img = np.array(screenshot)
            
            # Convert RGB to BGR (OpenCV format)
            img = img[:, :, :3]  # Remove alpha channel
            img = img[:, :, ::-1]  # RGB to BGR
            
            self.last_capture = img
            self.capture_count += 1
            
            return img
            
        except Exception as e:
            logger.error(f"Error capturing region ({x},{y},{width},{height}): {e}")
            return None
    
    def capture_multiple_regions(self, regions: dict) -> dict:
        """
        Capture multiple regions efficiently.
        
        Args:
            regions: Dict of region_name -> (x, y, width, height)
        
        Returns:
            Dict of region_name -> numpy array
        """
        captures = {}
        
        for name, coords in regions.items():
            if len(coords) == 4:
                x, y, w, h = coords
                capture = self.capture_region(x, y, w, h)
                if capture is not None:
                    captures[name] = capture
                else:
                    logger.warning(f"Failed to capture region: {name}")
        
        return captures
    
    def save_capture(self, filepath: str, image: np.ndarray = None):
        """
        Save captured image to file.
        
        Args:
            filepath: Path to save image
            image: Image to save (uses last_capture if None)
        """
        if image is None:
            image = self.last_capture
        
        if image is None:
            logger.error("No image to save")
            return
        
        try:
            # Convert BGR to RGB for saving
            image_rgb = image[:, :, ::-1]
            pil_image = Image.fromarray(image_rgb)
            pil_image.save(filepath)
            logger.info(f"Saved capture to {filepath}")
        except Exception as e:
            logger.error(f"Error saving capture: {e}")
    
    def get_stats(self) -> dict:
        """
        Get capture statistics.
        
        Returns:
            Dict with capture stats
        """
        return {
            "total_captures": self.capture_count,
            "last_capture_shape": self.last_capture.shape if self.last_capture is not None else None
        }
    
    def __del__(self):
        """Cleanup."""
        if hasattr(self, 'sct'):
            self.sct.close()
