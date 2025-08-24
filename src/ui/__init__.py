"""
UI utilities for the Stream Futebol Dashboard application.

This module contains user interface components, styling utilities,
and UI-related helper functions.
"""

from .footer_label import create_footer
from .icons_provider import get_icon, get_icon_path

from .top_widget import TopWidget
from .score_ui import ScoreUI
from .timer_ui import TimerComponent

from .edit_teams_ui import TeamManagerWindow, EditTeamPopup
from .teamsUI.teams_ui import TeamInputManager

# Simple Debounced Event Bus for coalescing frequent UI events
#
# Purpose:
# - Coalesce bursts of identical events (by name) into a single callback
# - Reduce jank by avoiding dozens of UI updates within a short interval
# - Thread-safe: can be called from worker threads
#
# Important:
# - Tk/CustomTk widgets must be updated from the main thread.
#   Subscribers should typically schedule UI work via root.after(0, ...).
# - Debounce is per event name. Last publisher wins within the window.
import threading
from typing import Callable, Dict


class DebouncedEventBus:
    """Lightweight, per-event debounce.

    - subscribe(event, callback): register a single callback for an event name
    - publish(event): schedule the callback after delay_ms (resetting any pending one)

    Callbacks run on a background Timer thread. If they touch UI, they must
    enqueue to the Tk mainloop (e.g., root.after(0, ...)).
    """

    def __init__(self, delay_ms: int = 50):
        self._delay = max(0, int(delay_ms)) / 1000.0
        self._lock = threading.Lock()
        self._callbacks: Dict[str, Callable[[], None]] = {}
        self._timers: Dict[str, threading.Timer] = {}

    def subscribe(self, event: str, callback: Callable[[], None]) -> None:
        """Register/replace the callback for an event name."""
        with self._lock:
            self._callbacks[event] = callback

    def publish(self, event: str) -> None:
        """Debounce: cancel any pending timer and schedule a new one."""
        with self._lock:
            cb = self._callbacks.get(event)
            if not cb:
                return
            if event in self._timers:
                try:
                    self._timers[event].cancel()
                except Exception:
                    pass
            t = threading.Timer(self._delay, cb)
            self._timers[event] = t
            t.daemon = True
            t.start()


# Global UI bus with default debounce from AppConfig
from src.config.settings import AppConfig
UI_EVENT_BUS = DebouncedEventBus(delay_ms=getattr(AppConfig, "UI_UPDATE_DEBOUNCE", 50))

# Penalty shootout dashboard
from .penalty import open_penalty_dashboard

# Window utilities and base classes - now imported from utils
from ..utils import (
    WindowConfig,
    center_window_on_screen,
    center_window_on_parent,
    configure_window,
    create_modal_dialog,
    create_popup_dialog,
    create_toast_window,
    create_main_window,
    apply_drag_and_drop,
    apply_window_styling,
    close_window_safely,
    top_centered_child_to_parent,
    BaseWindow,
    BaseMainWindow,
    BaseDialog,
    BasePopupDialog,
    BaseToastWindow,
    ModalDialog,
    PopupDialog,
    ToastWindow
)

__all__ = [
    'create_footer',
    'get_icon',
    'get_icon_path',

    'top_centered_child_to_parent',
    'TopWidget',
    'ScoreUI',
    'TimerComponent',

    'TeamManagerWindow',
    'EditTeamPopup',
    'TeamInputManager',
    
    # Penalty shootout
    'open_penalty_dashboard',
    
    # Window utilities
    'WindowConfig',
    'center_window_on_screen',
    'center_window_on_parent',
    'configure_window',
    'create_modal_dialog',
    'create_popup_dialog',
    'create_toast_window',
    'create_main_window',
    'apply_drag_and_drop',
    'apply_window_styling',
    'close_window_safely',
    
    # Window base classes
    'BaseWindow',
    'BaseMainWindow',
    'BaseDialog',
    'BasePopupDialog',
    'BaseToastWindow',
    'ModalDialog',
    'PopupDialog',
    'ToastWindow',
]
