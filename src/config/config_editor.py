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

class ConfigEditor:
    """Configuration editor interface."""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.config_file = Path("performance_config.json")
        self.current_config = self._load_current_config()
        self.setting_widgets = {}  # Initialize setting_widgets
        
    def _load_current_config(self) -> Dict[str, Any]:
        """Load current configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
                return {}
        return {}
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print("Configuration saved successfully!")
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def show_config_dialog(self):
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
        
        # Store widgets for later access
        self.setting_widgets = {}
        
    def _create_section_header(self, parent, text: str):
        """Create a section header."""
        header = ctk.CTkLabel(
            parent,
            text=text,
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_SUBTITLE, "bold"),
            text_color=AppConfig.COLORS["primary"]
        )
        header.pack(pady=(20, 10), anchor="w")
        
    def _create_setting(self, parent, key: str, label: str, min_val: float, max_val: float, step: float):
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
            from_=min_val, 
            to=max_val, 
            number_of_steps=int((max_val - min_val) / step),
            command=lambda v: self._update_setting_value(key, v)
        )
        slider.set(current_value)
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
        slider.configure(command=lambda v: self._update_setting_value(key, v))
        
    def _update_setting_value(self, key: str, value: float):
        """Update setting value and display."""
        if key in self.setting_widgets:
            self.setting_widgets[key]['current_value'] = value
            self.setting_widgets[key]['value_label'].configure(text=f"{value:.2f}")
    
    def _save_current_config(self):
        """Save current configuration values."""
        config = {}
        for key, widgets in self.setting_widgets.items():
            config[key] = widgets['current_value']
        
        self._save_config(config)
        self.current_config = config
        
    def _reset_to_defaults(self):
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
        
        print("Configuration reset to defaults!")
    
    def _close_dialog(self):
        """Close the configuration dialog."""
        if self.parent:
            self.parent.destroy()

def show_config_editor(parent=None):
    """Show the configuration editor dialog."""
    editor = ConfigEditor(parent)
    editor.show_config_dialog()
    return editor

if __name__ == "__main__":
    # Test the configuration editor
    show_config_editor()
