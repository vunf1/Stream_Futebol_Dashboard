"""
General utilities for the Stream Futebol Dashboard application.

This module contains miscellaneous utility functions that provide
common functionality across the application.
"""

from .date_time_provider import DateTimeProvider
from .online_time_provider import (
    LocalTimeProvider,
    get_local_time_provider,
    get_current_utc_time,
    get_current_portugal_time,
    is_time_online,
    get_time_source_info
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
from .window_utils import (
    WindowConfig,
    center_window_on_screen,
    center_window_on_screen_with_offset,
    center_window_on_parent,
    configure_window,
    create_modal_dialog,
    create_popup_dialog,
    create_toast_window,
    create_main_window,
    apply_drag_and_drop,
    apply_window_styling,
    top_centered_child_to_parent,
    close_window_safely
)

__all__ = [
    # Time utilities
    'DateTimeProvider',
    'LocalTimeProvider',
    'get_local_time_provider',
    'get_current_utc_time',
    'get_current_portugal_time',
    'is_time_online',
    'get_time_source_info',
    
    # Window base classes
    'BaseWindow',
    'BaseMainWindow',
    'BaseDialog',
    'BasePopupDialog',
    'BaseToastWindow',
    'ModalDialog',
    'PopupDialog',
    'ToastWindow',
    
    # Window utilities
    'WindowConfig',
    'center_window_on_screen',
    'center_window_on_screen_with_offset',
    'center_window_on_parent',
    'configure_window',
    'create_modal_dialog',
    'create_popup_dialog',
    'create_toast_window',
    'create_main_window',
    'apply_drag_and_drop',
    'apply_window_styling',
    'top_centered_child_to_parent',
    'close_window_safely',
]

