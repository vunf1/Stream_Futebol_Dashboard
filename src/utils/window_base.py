"""
Window Base Classes

This module provides base classes for common window types to reduce code duplication.
"""

import customtkinter as ctk
from customtkinter import CTkToplevel, CTk, CTkFrame, CTkBaseClass
from typing import Optional, Dict, Any, Callable, Union, cast
from .window_utils import WindowConfig, configure_window, center_window_on_screen, center_window_on_parent


class BaseWindow:
    """Base class for all windows with common functionality."""
    
    def __init__(self, title: str, width: int, height: int, 
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize base window.
        
        Args:
            title: Window title
            width: Window width
            height: Window height
            config: Window configuration
        """
        self.title = title
        self.width = width
        self.height = height
        self.config = config or {}
        self.window: Optional[Union[CTk, CTkToplevel, CTkFrame]] = None
    
    def create_window(self) -> ctk.CTkBaseClass:
        """Create the window. Must be implemented by subclasses."""
        raise NotImplementedError
    
    def configure_window(self) -> None:
        """Configure the window with standard settings."""
        if self.window and self.config and isinstance(self.window, (ctk.CTk, ctk.CTkToplevel)):
            configure_window(self.window, self.config)
    
    def center_window(self) -> None:
        """Center the window on screen."""
        if self.window and isinstance(self.window, (ctk.CTk, ctk.CTkToplevel)):
            center_window_on_screen(self.window, self.width, self.height)
    
    def apply_styling(self, fg_color: Optional[str] = None, 
                     bg_color: Optional[str] = None) -> None:
        """Apply window styling."""
        if self.window:
            from .window_utils import apply_window_styling
            apply_window_styling(cast(CTkBaseClass, self.window), fg_color, bg_color)
    
    def apply_drag_and_drop(self) -> None:
        """Apply drag and drop functionality."""
        if self.window:
            from .window_utils import apply_drag_and_drop
            apply_drag_and_drop(self.window)


class BaseMainWindow(BaseWindow):
    """Base class for main application windows."""
    
    def __init__(self, title: str, width: int, height: int,
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(title, width, height, config or WindowConfig.MAIN_WINDOW)
    
    def create_window(self) -> ctk.CTk:
        """Create main application window."""
        self.window = ctk.CTk()
        self.window.title(self.title)
        self.window.geometry(f"{self.width}x{self.height}")
        
        self.configure_window()
        self.center_window()
        
        return self.window


class BaseDialog(BaseWindow):
    """Base class for dialog windows."""
    
    def __init__(self, parent: ctk.CTkBaseClass, title: str, width: int, height: int,
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(title, width, height, config or WindowConfig.MODAL_DIALOG)
        self.parent = parent
    
    def create_window(self) -> CTkToplevel:
        """Create dialog window."""
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title(self.title)
        self.window.geometry(f"{self.width}x{self.height}")
        
        self.configure_window()
        self.center_window()
        
        return self.window


class BasePopupDialog(BaseDialog):
    """Base class for popup dialog windows."""
    
    def __init__(self, parent: ctk.CTkBaseClass, title: str, width: int, height: int,
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(parent, title, width, height, config or WindowConfig.POPUP_DIALOG)
    
    def center_window(self) -> None:
        """Center the popup relative to its parent."""
        if self.window and isinstance(self.window, CTkToplevel):
            center_window_on_parent(cast(CTkToplevel, self.window), cast(Union[CTk, CTkToplevel], self.parent), self.width, self.height)


class BaseToastWindow(BaseWindow):
    """Base class for toast notification windows."""
    
    def __init__(self, width: int, height: int, config: Optional[Dict[str, Any]] = None):
        super().__init__("Toast", width, height, config or WindowConfig.TOAST_WINDOW)
    
    def create_window(self) -> CTkToplevel:
        """Create toast window."""
        self.window = ctk.CTkToplevel()
        self.window.geometry(f"{self.width}x{self.height}")
        
        self.configure_window()
        
        return self.window


class ModalDialog(CTkToplevel):
    """Enhanced modal dialog class with built-in configuration."""
    
    def __init__(self, parent: ctk.CTkBaseClass, title: str, width: int, height: int,
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        
        self.title(title)
        self.geometry(f"{width}x{height}")
        
        # Apply configuration
        base_config = WindowConfig.MODAL_DIALOG.copy()
        if config:
            base_config.update(config)
        
        configure_window(self, base_config, cast(Union[CTk, CTkToplevel], parent))
        center_window_on_screen(self, width, height)
    
    def show(self) -> None:
        """Show the dialog and wait for it to close."""
        self.grab_set()
        self.wait_window()


class PopupDialog(CTkToplevel):
    """Enhanced popup dialog class with built-in configuration."""
    
    def __init__(self, parent: ctk.CTkBaseClass, title: str, width: int, height: int,
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        
        self.title(title)
        self.geometry(f"{width}x{height}")
        
        # Apply configuration
        base_config = WindowConfig.POPUP_DIALOG.copy()
        if config:
            base_config.update(config)
        
        configure_window(self, base_config, cast(Union[CTk, CTkToplevel], parent))
        center_window_on_parent(self, cast(Union[CTk, CTkToplevel], parent), width, height)
    
    def show(self) -> None:
        """Show the popup and wait for it to close."""
        self.grab_set()
        self.wait_window()


class ToastWindow(CTkToplevel):
    """Enhanced toast window class with built-in configuration."""
    
    def __init__(self, width: int, height: int, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        
        self.geometry(f"{width}x{height}")
        
        # Apply configuration
        base_config = WindowConfig.TOAST_WINDOW.copy()
        if config:
            base_config.update(config)
        
        configure_window(self, base_config)
    
    def show(self, duration: int = 3000) -> None:
        """Show the toast for the specified duration."""
        self.after(duration, self.destroy)
        self.lift()
        self.focus_force()
