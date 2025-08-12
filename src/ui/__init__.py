"""
UI utilities for the Stream Futebol Dashboard application.

This module contains user interface components, styling utilities,
and UI-related helper functions.
"""

from .footer_label import add_footer_label
from .icons_provider import get_icon, get_icon_path
from .make_drag_drop import make_it_drag_and_drop
from .top_c_child_parent import top_centered_child_to_parent
from .top_widget import TopWidget
from .score_ui import ScoreUI
from .timer_ui import TimerComponent
from .edit_teams_ui import TeamManagerWindow, EditTeamPopup
from .teamsUI.teams_ui import TeamInputManager

__all__ = [
    'add_footer_label',
    'get_icon',
    'get_icon_path',
    'make_it_drag_and_drop',
    'top_centered_child_to_parent',
    'TopWidget',
    'ScoreUI',
    'TimerComponent',
    'TeamManagerWindow',
    'EditTeamPopup',
    'TeamInputManager',
]
