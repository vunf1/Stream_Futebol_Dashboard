"""
UI utilities for the Stream Futebol Dashboard application.

This module contains user interface components, styling utilities,
and UI-related helper functions.
"""

from .footer_label import add_footer_label
from .icons_provider import get_icon, get_icon_path

from .top_c_child_parent import top_centered_child_to_parent
from .top_widget import TopWidget
from .score_ui import ScoreUI
from .timer_ui import TimerComponent
from .colors import (
    COLOR_ACTIVE, COLOR_BORDER, COLOR_SUCCESS, COLOR_ERROR,
    COLOR_PAUSE, COLOR_STOP, COLOR_WARNING, COLOR_INFO
)
from .edit_teams_ui import TeamManagerWindow, EditTeamPopup
from .teamsUI.teams_ui import TeamInputManager

# Window utilities and base classes
from .window_utils import (
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
    top_centered_child_to_parent as legacy_top_centered_child_to_parent
)

from .window_base import (
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
    'COLOR_ACTIVE', 'COLOR_BORDER', 'COLOR_SUCCESS', 'COLOR_ERROR',
    'COLOR_PAUSE', 'COLOR_STOP', 'COLOR_WARNING', 'COLOR_INFO',
    'TeamManagerWindow',
    'EditTeamPopup',
    'TeamInputManager',
    
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
    'legacy_top_centered_child_to_parent',
    
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
