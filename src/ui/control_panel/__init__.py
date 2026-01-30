"""
Control Panel UI module for Poker Assistant.

Provides a dockable control panel window with:
- Manual card input with dropdown selectors
- Real-time statistics display
- Calibration controls
- System tray integration
"""

from .main_panel import ControlPanelWindow
from .system_tray import SystemTrayManager

__all__ = ['ControlPanelWindow', 'SystemTrayManager']
