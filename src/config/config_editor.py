"""
Configuration editor utility for Stream Futebol Dashboard.
Allows users to view and modify configuration settings through a simple interface.
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import customtkinter as ctk
from .settings import AppConfig
from src.core.logger import get_logger

log = get_logger(__name__)

class ConfigEditor:
    """Configuration editor interface."""
    
    def __init__(self, parent: Optional[ctk.CTkBaseClass] = None) -> None:
        self.parent = parent
        self.config_file = Path("performance_config.json")
        self.current_config = self._load_current_config()
        self.setting_widgets: Dict[str, Dict[str, Any]] = {}
        
    def _load_current_config(self) -> Dict[str, Any]:
        """Load current configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        return loaded
                    return {}
            except Exception as e:
                log.warning("config_editor_load_failed", extra={"error": str(e), "path": str(self.config_file)})
                return {}
        return {}
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            log.info("config_editor_saved", extra={"path": str(self.config_file)})
        except Exception as e:
            log.error("config_editor_save_failed", extra={"error": str(e), "path": str(self.config_file)})
    
    def show_config_dialog(self) -> None:
        """Show configuration editing dialog."""
        if not self.parent:
            self.parent = ctk.CTk()
            self.parent.title("Configuration Editor")
            self.parent.geometry("600x500")
        
        # Create main frame
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Stream Futebol Dashboard Configuration",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_TITLE, "bold")
        )
        title_label.pack(pady=(10, 20))
        
        # Create scrollable frame for settings
        scroll_frame = ctk.CTkScrollableFrame(main_frame)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Window settings section
        self._create_section_header(scroll_frame, "Window Settings")
        self._create_setting(scroll_frame, "WINDOW_OPACITY", "Window Opacity", 0.0, 1.0, 0.05)
        self._create_setting(scroll_frame, "WINDOW_WIDTH", "Window Width", 200, 800, 10)
        self._create_setting(scroll_frame, "WINDOW_HEIGHT", "Window Height", 300, 800, 10)
        
        # Performance settings section
        self._create_section_header(scroll_frame, "Performance Settings")
        self._create_setting(scroll_frame, "UI_UPDATE_DEBOUNCE", "UI Update Debounce (ms)", 10, 200, 10)
        self._create_setting(scroll_frame, "ICON_CACHE_SIZE", "Icon Cache Size", 10, 200, 10)
        self._create_setting(scroll_frame, "WRITE_BUFFER_DELAY", "Write Buffer Delay (s)", 0.01, 1.0, 0.01)
        
        # Server health/watchdog settings
        self._create_section_header(scroll_frame, "Server Health & Watchdog")
        self._create_toggle(scroll_frame, "SERVER_HEALTH_CHECK_ENABLED", "Enable Server Health Checks")
        self._create_toggle(scroll_frame, "SERVER_WATCHDOG_ENABLED", "Enable Server Watchdog")
        
        # Animation settings section
        self._create_section_header(scroll_frame, "Animation Settings")
        self._create_setting(scroll_frame, "SPINNER_ANIMATION_INTERVAL", "Spinner Interval (ms)", 100, 1000, 50)
        self._create_setting(scroll_frame, "FADE_STEP_INTERVAL", "Fade Step Interval (ms)", 10, 100, 5)
        self._create_setting(scroll_frame, "LOADING_STEP_DELAY", "Loading Step Delay (ms)", 50, 500, 25)
        
        # Field settings section
        self._create_section_header(scroll_frame, "Field Settings")
        self._create_setting(scroll_frame, "MAX_FIELDS", "Maximum Fields", 5, 50, 1)
        self._create_setting(scroll_frame, "FIELD_CASCADE_OFFSET", "Cascade Offset", 20, 100, 5)
        self._create_setting(scroll_frame, "FIELD_GRID_SPACING", "Grid Spacing", 10, 50, 5)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            button_frame, 
            text="Save Configuration", 
            command=self._save_current_config
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame, 
            text="Reset to Defaults", 
            command=self._reset_to_defaults
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame, 
            text="Close", 
            command=self._close_dialog
        ).pack(side="right", padx=5)
        
        # Store widgets for later access (already populated by builders)
        
    def _create_section_header(self, parent: Any, text: str) -> None:
        """Create a section header."""
        header = ctk.CTkLabel(
            parent,
            text=text,
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_SUBTITLE, "bold"),
            text_color=AppConfig.COLORS["primary"]
        )
        header.pack(pady=(20, 10), anchor="w")
        
    def _create_setting(self, parent: Any, key: str, label: str, min_val: float, max_val: float, step: float) -> None:
        """Create a setting control."""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=5, pady=2)
        
        # Label
        label_widget = ctk.CTkLabel(frame, text=label, width=200)
        label_widget.pack(side="left", padx=5, pady=5)
        
        # Get current value
        current_value = getattr(AppConfig, key, 0.0)
        if key in self.current_config:
            current_value = self.current_config[key]
        
        # Slider
        slider = ctk.CTkSlider(
            frame, 
            from_=int(min_val * 100), 
            to=int(max_val * 100), 
            number_of_steps=int((max_val - min_val) / step),
            command=lambda v: self._update_setting_value(key, v / 100)
        )
        slider.set(int(current_value * 100))
        slider.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        
        # Value label
        value_label = ctk.CTkLabel(frame, text=f"{current_value:.2f}", width=80)
        value_label.pack(side="right", padx=5, pady=5)
        
        # Store widgets
        self.setting_widgets[key] = {
            'slider': slider,
            'value_label': value_label,
            'current_value': current_value
        }
        
        # Update value label when slider changes
        slider.configure(command=lambda v: self._update_setting_value(key, v / 100))
    
    def _create_toggle(self, parent: Any, key: str, label: str) -> None:
        """Create a boolean toggle control."""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=5, pady=2)

        label_widget = ctk.CTkLabel(frame, text=label)
        label_widget.pack(side="left", padx=5, pady=8)

        current_value = bool(self.current_config.get(key, getattr(AppConfig, key, False)))
        var = ctk.BooleanVar(value=current_value)

        def on_toggle() -> None:
            self.setting_widgets[key]['current_value'] = var.get()

        switch = ctk.CTkSwitch(frame, text="", variable=var, command=on_toggle)
        switch.pack(side="right", padx=5, pady=8)

        # Ensure the toggle is tracked for saving and resetting even if not touched
        self.setting_widgets[key] = {
            'current_value': current_value,
            'switch_var': var,
        }
        
    def _update_setting_value(self, key: str, value: float) -> None:
        """Update setting value and display."""
        if key in self.setting_widgets:
            self.setting_widgets[key]['current_value'] = value
            self.setting_widgets[key]['value_label'].configure(text=f"{value:.2f}")
    
    def _save_current_config(self) -> None:
        """Save current configuration values."""
        config = {}
        for key, widgets in self.setting_widgets.items():
            config[key] = widgets['current_value']
        
        self._save_config(config)
        self.current_config = config
        
    def _reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        # Remove config file to reset to defaults
        if self.config_file.exists():
            os.remove(self.config_file)
        
        # Reload current config (will be empty, so defaults will be used)
        self.current_config = {}
        
        # Update UI to show default values
        for key, widgets in self.setting_widgets.items():
            default_value = getattr(AppConfig, key, 0.0)
            widgets['slider'].set(default_value)
            widgets['value_label'].configure(text=f"{default_value:.2f}")
            widgets['current_value'] = default_value
        
        log.info("config_editor_reset_to_defaults")
    
    def _close_dialog(self) -> None:
        """Close the configuration dialog."""
        if self.parent:
            self.parent.destroy()

def show_config_editor(parent: Optional[ctk.CTkBaseClass] = None) -> ConfigEditor:
    """Show the configuration editor dialog."""
    editor = ConfigEditor(parent)
    editor.show_config_dialog()
    return editor

if __name__ == "__main__":
    # Test the configuration editor
    show_config_editor()
