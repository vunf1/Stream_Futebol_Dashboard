"""
UI utilities for the Stream Futebol Dashboard application.

This module contains user interface components, styling utilities,
and UI-related helper functions.
"""

from .footer_label import add_footer_label
from .icons_provider import get_icon, get_icon_path

from .top_widget import TopWidget
from .score_ui import ScoreUI
from .timer_ui import TimerComponent

from .edit_teams_ui import TeamManagerWindow, EditTeamPopup
from .teamsUI.teams_ui import TeamInputManager

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
    'add_footer_label',
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
