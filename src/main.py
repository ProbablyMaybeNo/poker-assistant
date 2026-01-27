"""
Main entry point for Poker AI Assistant.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import logger
from src.utils.config_loader import config_loader

def main():
    """Main application entry point."""
    logger.info("="*50)
    logger.info("Poker AI Assistant - Starting Up")
    logger.info("="*50)

    try:
        # Load configuration
        logger.info("Loading configuration...")
        settings = config_loader.load('settings.json')
        logger.info(f"Settings loaded successfully")

        logger.info("\nPhase 1 Complete: Environment Setup Successful!")
        logger.info("Next: Run Phase 2 to implement screen capture system")

    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        logger.error("Please ensure config files exist in config/ directory")
        return 1
    except Exception as e:
        logger.critical(f"Unexpected error during startup: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
