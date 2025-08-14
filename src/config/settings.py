"""
Application configuration and settings for Apito Final.
"""
import os
from typing import Dict, Any

class AppConfig:
    """Application configuration class for Apito Final."""
    
    # MongoDB Configuration
    MONGO_URI = os.getenv("MONGO_URI", "")
    MONGO_DB = os.getenv("MONGO_DB", "")
    MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "")
    
    # Application Settings
    APP_TITLE = "Apito Final"
    APP_VERSION = "12.5.0"
    APP_AUTHOR = "Apito Final Team"
    
    # Window Configuration
    WINDOW_WIDTH = 420
    WINDOW_HEIGHT = 520
    WINDOW_MIN_WIDTH = 190
    WINDOW_MIN_HEIGHT = 255
    WINDOW_OPACITY = 0.85  # Default transparency level
    
    # UI Configuration
    THEME_MODE = "dark"
    COLOR_THEME = "blue"
    FONT_FAMILY = "Segoe UI"
    FONT_FAMILY_EMOJI = "Segoe UI Emoji"
    
    # Font Sizes
    FONT_SIZE_TITLE = 20
    FONT_SIZE_SUBTITLE = 16
    FONT_SIZE_BODY = 12
    FONT_SIZE_DIALOG_TITLE = 15
    FONT_SIZE_DIALOG_BODY = 13
    
    # Database Settings
    MAX_POOL_SIZE = 10
    RETRY_WRITES = True
    SERVER_SELECTION_TIMEOUT_MS = 5000
    CONNECT_TIMEOUT_MS = 10000
    SOCKET_TIMEOUT_MS = 10000
    
    # Score Management Settings
    MAX_SCORE = 999
    MIN_SCORE = 0
    DEFAULT_SCORE = 0
    
    # Team Management Settings
    MAX_TEAM_NAME_LENGTH = 50
    MAX_TEAM_ABBREVIATION_LENGTH = 10
    MIN_TEAM_NAME_LENGTH = 2
    
    # Field/Instance Settings
    MAX_FIELDS = 2
    MIN_FIELDS = 1
    DEFAULT_FIELDS = 1
    FIELD_CASCADE_OFFSET = 40
    FIELD_GRID_SPACING = 20
    
    # Dialog Window Settings
    DIALOG_WIDTH = 320
    DIALOG_HEIGHT = 200
    DIALOG_EXPANDED_WIDTH = 400  # License modal width
    DIALOG_EXPANDED_HEIGHT = 200
    DIALOG_SLIDER_WIDTH = 220
    
    # License Modal Settings
    LICENSE_MODAL_HEIGHT = 250
    LICENSE_MODAL_PADDING = 20
    LICENSE_MODAL_BUTTON_HEIGHT = 35
    LICENSE_MODAL_CLOSE_BUTTON_SIZE = 24
    
    # Timer Settings
    TIMER_UPDATE_INTERVAL = 1000  # milliseconds
    TIMER_MAX_TIME = 7200  # 2 hours in seconds
    TIMER_DEFAULT_TIME = 2700  # 45 minutes in seconds
    
    # Performance Settings
    UI_UPDATE_DEBOUNCE = 50  # milliseconds
    ICON_CACHE_SIZE = 50
    WRITE_BUFFER_DELAY = 0.1  # seconds
    WRITE_BUFFER_SIZE = 100
    
    # Animation and Timing Settings
    SPINNER_ANIMATION_INTERVAL = 150  # milliseconds
    FADE_STEP_INTERVAL = 10  # milliseconds
    FADE_STEPS = 5
    LOADING_STEP_DELAY = 50  # milliseconds
    LICENSE_CHECK_DELAY = 25  # milliseconds
    BACKUP_DELAY = 25  # milliseconds
    UI_SETUP_DELAY = 5  # milliseconds
    COMPLETION_DELAY = 100  # milliseconds
    
    # Notification Settings
    NOTIFICATION_POLL_INTERVAL = 80  # milliseconds
    TOAST_DISPLAY_TIME = 3000  # milliseconds
    
    # Security Settings
    ADMIN_PIN = os.getenv("PIN", "")
    LICENSE_CHECK_INTERVAL = 15000  # milliseconds (15 seconds)
    
    # Boundary and Spacing Settings
    SCREEN_BOUNDARY_MARGIN = 50
    WINDOW_OVERLAP_ADJUSTMENT = 20
    
    # File Export Settings
    EXPORT_FILE_EXTENSION = ".txt"
    EXPORT_ENCODING = "utf-8"
    EXPORT_UPDATE_INTERVAL = 1000  # milliseconds
    
    # Path and Directory Settings
    DESKTOP_FOLDER_NAME = "FUTEBOL-SCORE-DASHBOARD"
    SPECIAL_CONFIG_FOLDER = "special"
    CONFIG_SUBFOLDER = "config"
    FIELD_PREFIX = "Campo_"
    TEAMS_BACKUP_FILENAME = "teams.json"
    GAMEINFO_FILENAME = "gameinfo.json"
    
    # Environment File Settings
    ENV_ENCRYPTED_FILENAME = ".env.enc"
    SECRET_KEY_FILENAME = "secret.key"
    MEIPASS_ATTRIBUTE = "_MEIPASS"
    ENV_DIR_ENVVAR = "GOAL_ENV_DIR"
    
    # Backup Settings
    AUTO_BACKUP_ENABLED = True
    BACKUP_RETENTION_DAYS = 30
    BACKUP_FILE_PREFIX = "teams_backup_"
    
    # Debug Settings
    DEBUG_MODE = False  # Will be set in __init__ or class method
    LOG_LEVEL = "INFO"
    
    # UI Refresh Settings
    REFRESH_INTERVAL = 1.0  # seconds
    SEARCH_DEBOUNCE_MS = 300
    
    # Pagination Settings
    ITEMS_PER_PAGE = 25
    
    # Validation Settings
    REQUIRED_TEAM_FIELDS = ["name", "abbreviation"]
    REQUIRED_LICENSE_FIELDS = ["user", "email"]
    
    # Color Scheme
    COLORS = {
        "primary": "#4CAF50",
        "secondary": "#2196F3",
        "success": "#4CAF50",
        "warning": "#FF9800",
        "error": "#F44336",
        "info": "#2196F3",
        "background": "#1a1a1a",
        "surface": "#2b2b2b",
        "text": "#ffffff",
        "text_secondary": "#cccccc",
        "spinner": "#4CAF50",
        "loading_bg": "#1a1a1a"
    }
    
    # Legacy Color Constants (from colors.py)
    COLOR_PRIMARY = "#1E90FF"  # DodgerBlue - primary action & highlights
    COLOR_SECONDARY = "#6C757D"  # Gray - secondary text / disabled
    COLOR_ACCENT = "#17A2B8"  # Teal - accent elements
    COLOR_SUCCESS = "#28A745"  # Green - success / go
    COLOR_ERROR = "#DC3545"  # Red - errors / stop
    COLOR_WARNING = "#FFC107"  # Amber - caution / watch out
    COLOR_INFO = "#17A2B8"  # Teal - info / neutral notice
    COLOR_PAUSE = "#6C757D"  # Gray - paused / inactive
    COLOR_STOP = "#A0522D"  # Light Red - hard stop / end
    COLOR_BACKGROUND = "#000000"  # Black - default window background
    COLOR_SURFACE = "#FFFFFF"  # White - cards, panels
    COLOR_BORDER = "#CED4DA"  # Light gray - outlines, separators
    COLOR_HOVER = "#E2E6EA"  # Hover effect
    COLOR_ACTIVE = "#0056B3"  # DarkDodgerBlue - active/selected state
    COLOR_DISABLED = "#ADB5BD"  # Muted gray - disabled controls
    COLOR_TEXT_PRIMARY = "#212529"  # Almost black - main text
    COLOR_TEXT_SECONDARY = "#6C757D"  # Gray - secondary text
    COLOR_TEXT_DISABLE = "#ADB5BD"  # Muted - disabled text
    
    # File Stem Mappings (from filenames.py)
    BASE_FILE_STEMS = {
        'half': 'half',
        'home_score': 'home_score',
        'away_score': 'away_score',
        'home_name': 'home_name',
        'away_name': 'away_name',
        'home_abbr': 'home_abbr',
        'away_abbr': 'away_abbr',
        'max': 'max',
        'timer': 'timer',
        'extra': 'extra',
    }
    
    # Default Field State (from gameinfo.py)
    DEFAULT_FIELD_STATE = {
        "away_abbr": "",
        "away_name": "",
        "home_abbr": "",
        "home_name": "",
        "home_score": 0,
        "away_score": 0,
        "half": "1ª Parte",
        "timer": "00:00",
        "extra": "00:00",
        "max": "45:00",
    }
    
    @classmethod
    def validate_mongo_config(cls) -> bool:
        """Validate MongoDB configuration."""
        return all([cls.MONGO_URI, cls.MONGO_DB, cls.MONGO_COLLECTION])
    
    @classmethod
    def get_mongo_config(cls) -> Dict[str, Any]:
        """Get MongoDB configuration as dictionary."""
        return {
            "mongo_uri": cls.MONGO_URI,
            "database_name": cls.MONGO_DB,
            "collection_name": cls.MONGO_COLLECTION,
            "max_pool_size": cls.MAX_POOL_SIZE,
            "retry_writes": cls.RETRY_WRITES,
            "server_selection_timeout_ms": cls.SERVER_SELECTION_TIMEOUT_MS,
            "connect_timeout_ms": cls.CONNECT_TIMEOUT_MS,
            "socket_timeout_ms": cls.SOCKET_TIMEOUT_MS
        }
    
    @classmethod
    def get_window_config(cls) -> Dict[str, Any]:
        """Get window configuration as dictionary."""
        return {
            "width": cls.WINDOW_WIDTH,
            "height": cls.WINDOW_HEIGHT,
            "min_width": cls.WINDOW_MIN_WIDTH,
            "min_height": cls.WINDOW_MIN_HEIGHT,
            "opacity": cls.WINDOW_OPACITY
        }
    
    @classmethod
    def get_performance_config(cls) -> Dict[str, Any]:
        """Get performance configuration as dictionary."""
        return {
            "ui_update_debounce": cls.UI_UPDATE_DEBOUNCE,
            "icon_cache_size": cls.ICON_CACHE_SIZE,
            "write_buffer_delay": cls.WRITE_BUFFER_DELAY,
            "write_buffer_size": cls.WRITE_BUFFER_SIZE,
            "notification_poll_interval": cls.NOTIFICATION_POLL_INTERVAL
        }
    
    @classmethod
    def get_timer_config(cls) -> Dict[str, Any]:
        """Get timer configuration as dictionary."""
        return {
            "update_interval": cls.TIMER_UPDATE_INTERVAL,
            "max_time": cls.TIMER_MAX_TIME,
            "default_time": cls.TIMER_DEFAULT_TIME
        }
    
    @classmethod
    def get_dialog_config(cls) -> Dict[str, Any]:
        """Get dialog configuration as dictionary."""
        return {
            "width": cls.DIALOG_WIDTH,
            "height": cls.DIALOG_HEIGHT,
            "expanded_width": cls.DIALOG_EXPANDED_WIDTH,
            "expanded_height": cls.DIALOG_EXPANDED_HEIGHT,
            "slider_width": cls.DIALOG_SLIDER_WIDTH
        }
    
    @classmethod
    def get_animation_config(cls) -> Dict[str, Any]:
        """Get animation and timing configuration as dictionary."""
        return {
            "spinner_interval": cls.SPINNER_ANIMATION_INTERVAL,
            "fade_step_interval": cls.FADE_STEP_INTERVAL,
            "fade_steps": cls.FADE_STEPS,
            "loading_step_delay": cls.LOADING_STEP_DELAY,
            "license_check_delay": cls.LICENSE_CHECK_DELAY,
            "backup_delay": cls.BACKUP_DELAY,
            "ui_setup_delay": cls.UI_SETUP_DELAY,
            "completion_delay": cls.COMPLETION_DELAY
        }
    
    @classmethod
    def get_path_config(cls) -> Dict[str, Any]:
        """Get path and directory configuration as dictionary."""
        return {
            "desktop_folder_name": cls.DESKTOP_FOLDER_NAME,
            "special_config_folder": cls.SPECIAL_CONFIG_FOLDER,
            "config_subfolder": cls.CONFIG_SUBFOLDER,
            "field_prefix": cls.FIELD_PREFIX,
            "teams_backup_filename": cls.TEAMS_BACKUP_FILENAME,
            "gameinfo_filename": cls.GAMEINFO_FILENAME
        }
    
    @classmethod
    def get_file_stems_config(cls) -> Dict[str, str]:
        """Get file stem mappings configuration."""
        return cls.BASE_FILE_STEMS.copy()
    
    @classmethod
    def get_default_field_state(cls) -> Dict[str, Any]:
        """Get default field state configuration."""
        return cls.DEFAULT_FIELD_STATE.copy()
    
    @classmethod
    def is_debug_mode(cls) -> bool:
        """Check if debug mode is enabled."""
        return cls.DEBUG_MODE
    
    @classmethod
    def get_app_info(cls) -> Dict[str, str]:
        """Get application information."""
        return {
            "title": cls.APP_TITLE,
            "version": cls.APP_VERSION,
            "author": cls.APP_AUTHOR
        }
    
    @classmethod
    def get_optional_env(cls, name: str, default: str = "") -> str:
        """Get an optional environment variable with a default value."""
        try:
            value = os.getenv(name)
            if value is None:
                return default
            return value
        except Exception:
            return default
    
    @classmethod
    def initialize_config(cls):
        """Initialize configuration values that depend on environment variables."""
        try:
            cls.DEBUG_MODE = cls.get_optional_env("DEBUG_MODE", "False").lower() == "true"
        except Exception as e:
            print(f"Warning: Could not initialize DEBUG_MODE: {e}")
            cls.DEBUG_MODE = False


# Initialize configuration when module is imported
AppConfig.initialize_config()
