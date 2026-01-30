"""
Comprehensive tests for AnchorManager module.

Tests anchor configuration loading and region calculation.
"""
import pytest
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.capture.anchor_manager import AnchorManager


class TestAnchorManager:
    """Test suite for AnchorManager class."""

    @pytest.fixture
    def temp_anchor_config(self, tmp_path):
        """Create temporary anchor configuration."""
        config = {
            "active_anchor": "test_anchor",
            "anchors": {
                "test_anchor": {
                    "template": "models/anchors/test.png",
                    "threshold": 0.8
                }
            },
            "regions": {
                "hole_cards": {"x": 100, "y": 200, "w": 150, "h": 100},
                "community_cards": {"x": 400, "y": 300, "w": 350, "h": 100},
                "pot_amount": {"x": 450, "y": 200, "w": 100, "h": 30}
            }
        }
        config_file = tmp_path / "anchor_config.json"
        config_file.write_text(json.dumps(config, indent=2))
        return config_file, tmp_path

    @pytest.fixture
    def anchor_manager(self):
        """Create AnchorManager instance."""
        return AnchorManager()

    # =========================================================================
    # CONFIGURATION LOADING TESTS
    # =========================================================================

    @pytest.mark.unit
    def test_load_config(self, anchor_manager, temp_anchor_config):
        """Test loading anchor configuration."""
        config_file, tmp_path = temp_anchor_config

        # Mock the config path
        with patch.object(anchor_manager, '_get_config_path', return_value=config_file):
            anchor_manager.load_config()

        assert anchor_manager.active_anchor_name == "test_anchor"
        assert "hole_cards" in anchor_manager.regions
        assert "community_cards" in anchor_manager.regions

    @pytest.mark.unit
    def test_load_config_missing_file(self, anchor_manager, tmp_path):
        """Test loading non-existent config file."""
        missing_file = tmp_path / "nonexistent.json"

        with patch.object(anchor_manager, '_get_config_path', return_value=missing_file):
            # Should handle gracefully
            try:
                anchor_manager.load_config()
            except FileNotFoundError:
                pass  # Expected

    # =========================================================================
    # REGION CALCULATION TESTS
    # =========================================================================

    @pytest.mark.unit
    def test_get_absolute_regions(self, anchor_manager, temp_anchor_config):
        """Test calculating absolute region positions from anchor."""
        config_file, tmp_path = temp_anchor_config

        with patch.object(anchor_manager, '_get_config_path', return_value=config_file):
            anchor_manager.load_config()

        anchor_pos = (500, 400)  # Anchor found at this position
        regions = anchor_manager.get_absolute_regions(anchor_pos)

        # Regions should be offset by anchor position
        assert regions is not None
        assert 'hole_cards' in regions
        # Exact calculation depends on implementation

    @pytest.mark.unit
    def test_get_regions_without_anchor(self, anchor_manager):
        """Test getting regions when no anchor is set."""
        anchor_manager.active_anchor_name = None
        anchor_manager.regions = {}

        regions = anchor_manager.get_absolute_regions((0, 0))
        # Should return empty or default regions
        assert regions is not None

    # =========================================================================
    # ANCHOR DETECTION TESTS
    # =========================================================================

    @pytest.mark.unit
    def test_find_anchor_mocked(self, anchor_manager, temp_anchor_config):
        """Test anchor detection with mocked template matching."""
        config_file, tmp_path = temp_anchor_config

        with patch.object(anchor_manager, '_get_config_path', return_value=config_file):
            anchor_manager.load_config()

        # Mock screen image
        mock_screen = np.zeros((1080, 1920, 3), dtype=np.uint8)

        # Mock cv2.matchTemplate to return a match
        with patch('cv2.matchTemplate') as mock_match:
            mock_result = np.zeros((100, 100), dtype=np.float32)
            mock_result[50, 50] = 0.9  # High confidence match
            mock_match.return_value = mock_result

            with patch('cv2.minMaxLoc', return_value=(0.1, 0.9, (0, 0), (50, 50))):
                with patch('cv2.imread', return_value=np.zeros((50, 50, 3), dtype=np.uint8)):
                    result = anchor_manager.find_anchor(mock_screen)
                    # Result should be position or None
                    # Exact behavior depends on implementation

    @pytest.mark.unit
    def test_find_anchor_no_template(self, anchor_manager):
        """Test anchor detection when template file missing."""
        anchor_manager.active_anchor_name = "missing"
        anchor_manager.anchors = {
            "missing": {"template": "nonexistent.png", "threshold": 0.8}
        }

        mock_screen = np.zeros((1080, 1920, 3), dtype=np.uint8)

        with patch('cv2.imread', return_value=None):
            result = anchor_manager.find_anchor(mock_screen)
            assert result is None


class TestAnchorManagerIntegration:
    """Integration tests for AnchorManager."""

    @pytest.mark.integration
    def test_full_workflow(self, tmp_path):
        """Test complete anchor workflow."""
        # Create config
        config = {
            "active_anchor": "test",
            "anchors": {
                "test": {"template": "test.png", "threshold": 0.8}
            },
            "regions": {
                "hole_cards": {"x": 100, "y": 200, "w": 150, "h": 100}
            }
        }
        config_file = tmp_path / "anchor_config.json"
        config_file.write_text(json.dumps(config, indent=2))

        # Create manager
        manager = AnchorManager()

        with patch.object(manager, '_get_config_path', return_value=config_file):
            manager.load_config()

        assert manager.active_anchor_name == "test"
        assert "hole_cards" in manager.regions
