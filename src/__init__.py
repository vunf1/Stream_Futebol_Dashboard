"""
Helpers package for the Stream Futebol Dashboard application.

This package contains organized utility modules grouped by functionality:
- core: Essential utilities and configuration management
- ui: User interface components and styling
- licensing: Complete licensing system
- notification: Notification and toast system
- performance: Performance monitoring tools
- security: Security and encryption utilities
- utils: General utility functions
"""

# Core utilities
from .core import (
    ConfigManager,
    SecureEnvLoader,
    get_config,
    MongoTeamManager,
    GameInfoStore,
)

# UI utilities
from .ui import (
    add_footer_label,
    get_icon,
    get_icon_path,
    make_it_drag_and_drop,
    top_centered_child_to_parent,
    TopWidget,
    ScoreUI,
    TimerComponent,
    TeamManagerWindow,
    EditTeamPopup,
)

# Licensing system
from .licensing import (
    LicenseManager,
    LicenseValidator,
    LicenseModal,
    LicenseActivationDialog,
    LicenseBlocker,
    show_license_details,
    integrate_licensing,
    check_license_status,
    get_license_display_info,
    is_license_valid,
    force_license_check,
)

# Notification system
from .notification import (
    server_main,
    init_notification_queue,
)

# Performance utilities
from .performance import (
    time_ui_update,
    time_json_operation,
)

# General utilities
from .utils import (
    DateTimeProvider,
    OnlineTimeProvider,
    get_current_utc_time,
    get_current_portugal_time,
    is_time_online,
    get_time_source_info,
)

__all__ = [
    # Core
    'ConfigManager',
    'SecureEnvLoader',
    'get_config',
    'MongoTeamManager',
    'GameInfoStore',
    
    # UI
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
    
    # Licensing
    'LicenseManager',
    'LicenseValidator',
    'LicenseModal',
    'LicenseActivationDialog',
    'LicenseBlocker',
    'show_license_details',
    'integrate_licensing',
    'check_license_status',
    'get_license_display_info',
    'is_license_valid',
    'force_license_check',
    
    # Notification
    'server_main',
    'init_notification_queue',
    
    # Performance
    'time_ui_update',
    'time_json_operation',
    
    # Utils
    'DateTimeProvider',
    'OnlineTimeProvider',
    'get_current_utc_time',
    'get_current_portugal_time',
    'is_time_online',
    'get_time_source_info',
]

__version__ = "2.0.0"
__author__ = "Stream Futebol Dashboard Team"
