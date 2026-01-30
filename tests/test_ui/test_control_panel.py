"""
Tests for Control Panel UI components.

Uses pytest-qt for PyQt5 testing.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# Skip if PyQt5 not available
pytest.importorskip("PyQt5")


class TestControlPanelWindow:
    """Test suite for ControlPanelWindow."""

    @pytest.fixture
    def qapp(self):
        """Create QApplication for testing."""
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app

    @pytest.fixture
    def control_panel(self, qapp):
        """Create ControlPanelWindow instance."""
        from src.ui.control_panel import ControlPanelWindow
        panel = ControlPanelWindow()
        yield panel
        panel.close()

    @pytest.mark.ui
    def test_panel_creation(self, control_panel):
        """Test control panel window creation."""
        assert control_panel is not None
        assert control_panel.windowTitle() == "POKER ASSISTANT CONTROL PANEL"

    @pytest.mark.ui
    def test_panel_has_start_button(self, control_panel):
        """Test control panel has start/stop button."""
        assert control_panel.start_stop_btn is not None

    @pytest.mark.ui
    def test_panel_has_card_selectors(self, control_panel):
        """Test control panel has card selector widgets."""
        assert control_panel.hand_selector is not None
        assert control_panel.community_selector is not None

    @pytest.mark.ui
    def test_panel_has_action_display(self, control_panel):
        """Test control panel has action display."""
        assert control_panel.action_display is not None

    @pytest.mark.ui
    def test_panel_has_statistics(self, control_panel):
        """Test control panel has statistics panel."""
        assert control_panel.statistics_panel is not None

    @pytest.mark.ui
    def test_start_stop_toggle(self, control_panel):
        """Test start/stop button toggle."""
        initial_state = control_panel.is_running()
        control_panel._on_start_stop_clicked()
        assert control_panel.is_running() != initial_state

    @pytest.mark.ui
    def test_set_running_state(self, control_panel):
        """Test setting running state programmatically."""
        control_panel.set_running(True)
        assert control_panel.is_running() is True

        control_panel.set_running(False)
        assert control_panel.is_running() is False


class TestSystemTrayManager:
    """Test suite for SystemTrayManager."""

    @pytest.fixture
    def qapp(self):
        """Create QApplication for testing."""
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app

    @pytest.fixture
    def tray_manager(self, qapp):
        """Create SystemTrayManager instance."""
        from src.ui.control_panel import SystemTrayManager
        manager = SystemTrayManager()
        yield manager

    @pytest.mark.ui
    def test_tray_creation(self, tray_manager):
        """Test system tray manager creation."""
        assert tray_manager is not None

    @pytest.mark.ui
    def test_tray_set_running(self, tray_manager):
        """Test setting running state on tray."""
        tray_manager.set_running(True)
        assert tray_manager.is_running() is True

        tray_manager.set_running(False)
        assert tray_manager.is_running() is False

    @pytest.mark.ui
    def test_tray_show_hide(self, tray_manager):
        """Test tray icon show/hide."""
        tray_manager.show()
        tray_manager.hide()
        # Should not raise errors


class TestActionDisplayWidget:
    """Test suite for ActionDisplayWidget."""

    @pytest.fixture
    def qapp(self):
        """Create QApplication for testing."""
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app

    @pytest.fixture
    def action_widget(self, qapp):
        """Create ActionDisplayWidget instance."""
        from src.ui.control_panel.widgets import ActionDisplayWidget
        widget = ActionDisplayWidget()
        yield widget

    @pytest.mark.ui
    def test_widget_creation(self, action_widget):
        """Test action display widget creation."""
        assert action_widget is not None

    @pytest.mark.ui
    def test_update_from_decision(self, action_widget):
        """Test updating widget from decision."""
        mock_decision = MagicMock()
        mock_decision.action = 'raise'
        mock_decision.amount_bb = 3.0
        mock_decision.confidence = 85
        mock_decision.reasoning = ['Strong hand', 'Good position']

        # Should not raise errors
        action_widget.update_from_decision(mock_decision)


class TestCardSelectorWidget:
    """Test suite for CardSelectorWidget."""

    @pytest.fixture
    def qapp(self):
        """Create QApplication for testing."""
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app

    @pytest.fixture
    def card_selector(self, qapp):
        """Create CardSelectorWidget instance."""
        from src.ui.control_panel.widgets import CardSelectorWidget
        widget = CardSelectorWidget()
        yield widget

    @pytest.mark.ui
    def test_widget_creation(self, card_selector):
        """Test card selector widget creation."""
        assert card_selector is not None

    @pytest.mark.ui
    def test_get_selected_card(self, card_selector):
        """Test getting selected card."""
        card = card_selector.get_card()
        # Should return card string or None
        assert card is None or isinstance(card, str)
