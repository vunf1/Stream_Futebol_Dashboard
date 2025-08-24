"""
Window Utilities Module

This module consolidates all window positioning, configuration, and styling utilities
to eliminate code duplication across the application.
"""

import customtkinter as ctk
from customtkinter import CTkToplevel, CTkBaseClass
from typing import Optional, Tuple, Dict, Any, Callable, Union
from ..config.settings import AppConfig


class WindowConfig:
    """Configuration class for window settings."""
    
    # Common window configurations
    MODAL_DIALOG = {
        "overrideredirect": True,
        "topmost": True,
        "grab_set": True,
        "resizable": (False, False),
        "focus_force": True,
        "lift": True
    }
    
    POPUP_DIALOG = {
        "overrideredirect": True,
        "topmost": True,
        "grab_set": False,  # Disabled to prevent focus grab issues with autocomplete popups
        "resizable": (False, False),
        "focus_force": True,
        "lift": True,
        "transient": True
    }
    
    MAIN_WINDOW = {
        "overrideredirect": True,
        "topmost": True,
        "resizable": (False, False),
        "focus_force": True,
        "lift": True
    }
    
    TOAST_WINDOW = {
        "overrideredirect": True,
        "topmost": True,
        "resizable": (False, False)
    }


def center_window_on_screen(window: Union[ctk.CTk, CTkToplevel], width: int, height: int) -> None:
    """
    Center a window on the screen.
    
    Args:
        window: The window to center
        width: Window width
        height: Window height
    """
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


def center_window_on_screen_with_offset(window: Union[ctk.CTk, CTkToplevel], width: int, height: int, y_offset: int = 0) -> None:
    """
    Center a window on the screen with optional vertical offset.
    
    Args:
        window: The window to center
        width: Window width
        height: Window height
        y_offset: Vertical offset from center (positive = down, negative = up)
    """
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2 + y_offset
    
    # Ensure window stays within screen bounds
    if y < 0:
        y = 10  # Minimum 10px from top edge
    elif y + height > screen_height:
        y = screen_height - height - 10  # Minimum 10px from bottom edge
    
    window.geometry(f"{width}x{height}+{x}+{y}")
    window.update_idletasks()


def center_window_on_parent(child: CTkToplevel, parent: Union[ctk.CTk, CTkToplevel], 
                          child_width: int, child_height: int, 
                          y_offset: int = 20) -> None:
    """
    Center a child window at the top center of its parent window.
    
    Args:
        child: The child window to position
        parent: The parent window
        child_width: Child window width
        child_height: Child window height
        y_offset: Vertical offset from parent top (default: 20px)
    """
    # Set window relationship and focus
    child.transient(parent)  # type: ignore
    child.lift(parent)
    child.focus_force()

    # Ensure parent window is updated to get accurate dimensions
    parent.update_idletasks()
    
    # Get parent window position and dimensions
    px = parent.winfo_rootx()  # Use root coordinates for accurate positioning
    py = parent.winfo_rooty()
    p_width = parent.winfo_width()
    p_height = parent.winfo_height()
    
    # Calculate center position horizontally
    # Center the child window horizontally on the parent
    pos_x = px + (p_width - child_width) // 2
    
    # Position vertically at top with offset
    # This places the child window at the top center of the parent
    pos_y = py + y_offset
    
    # Ensure the child window stays within screen bounds
    screen_width = child.winfo_screenwidth()
    screen_height = child.winfo_screenheight()
    
    # Adjust X position if child would go off-screen
    if pos_x < 0:
        pos_x = 10  # Minimum 10px from left edge
    elif pos_x + child_width > screen_width:
        pos_x = screen_width - child_width - 10  # Minimum 10px from right edge
    
    # Adjust Y position if child would go off-screen
    if pos_y < 0:
        pos_y = 10  # Minimum 10px from top edge
    elif pos_y + child_height > screen_height:
        pos_y = screen_height - child_height - 10  # Minimum 10px from bottom edge
    
    # Apply the calculated position
    child.geometry(f"{child_width}x{child_height}+{pos_x}+{pos_y}")
    
    # Ensure the positioning took effect
    child.update_idletasks()


def configure_window(window: Union[ctk.CTk, CTkToplevel], config: Dict[str, Any], 
                    parent: Optional[Union[ctk.CTk, CTkToplevel]] = None) -> None:
    """
    Apply window configuration settings.
    
    Args:
        window: The window to configure
        config: Configuration dictionary
        parent: Parent window (required for transient setting)
    """
    if config.get("overrideredirect"):
        window.overrideredirect(True)
    
    if config.get("topmost"):
        window.attributes("-topmost", True)
    
    if config.get("grab_set"):
        window.grab_set()
    
    if config.get("resizable"):
        resizable = config["resizable"]
        if isinstance(resizable, (list, tuple)) and len(resizable) == 2:
            window.resizable(bool(resizable[0]), bool(resizable[1]))
        else:
            window.resizable(bool(resizable), bool(resizable))
    
    if config.get("focus_force"):
        window.focus_force()
    
    if config.get("lift"):
        if parent:
            window.lift(parent)
        else:
            window.lift()
    
    if config.get("transient") and parent:
        window.transient(parent)  # type: ignore


def create_modal_dialog(parent: Union[ctk.CTk, CTkToplevel], title: str, width: int, height: int,
                       config: Optional[Dict[str, Any]] = None) -> CTkToplevel:
    """
    Create a modal dialog window with standard configuration.
    
    Args:
        parent: Parent window
        title: Dialog title
        width: Dialog width
        height: Dialog height
        config: Optional custom configuration
        
    Returns:
        Configured CTkToplevel window
    """
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry(f"{width}x{height}")
    
    # Apply configuration
    base_config = WindowConfig.MODAL_DIALOG.copy()
    if config:
        base_config.update(config)
    
    configure_window(dialog, base_config, parent)
    center_window_on_screen(dialog, width, height)
    
    return dialog


def create_popup_dialog(parent: Union[ctk.CTk, CTkToplevel], title: str, width: int, height: int,
                       config: Optional[Dict[str, Any]] = None) -> CTkToplevel:
    """
    Create a popup dialog window with standard configuration.
    
    Args:
        parent: Parent window
        title: Dialog title
        width: Dialog width
        height: Dialog height
        config: Optional custom configuration
        
    Returns:
        Configured CTkToplevel window
    """
    popup = ctk.CTkToplevel(parent)
    popup.title(title)
    popup.geometry(f"{width}x{height}")
    
    # Apply configuration
    base_config = WindowConfig.POPUP_DIALOG.copy()
    if config:
        base_config.update(config)
    
    configure_window(popup, base_config, parent)
    center_window_on_parent(popup, parent, width, height)
    
    return popup


def create_toast_window(width: int, height: int, 
                      config: Optional[Dict[str, Any]] = None) -> CTkToplevel:
    """
    Create a toast notification window.
    
    Args:
        width: Toast width
        height: Toast height
        config: Optional custom configuration
        
    Returns:
        Configured CTkToplevel window
    """
    toast = ctk.CTkToplevel()
    toast.geometry(f"{width}x{height}")
    
    # Apply configuration
    base_config = WindowConfig.TOAST_WINDOW.copy()
    if config:
        base_config.update(config)
    
    configure_window(toast, base_config)
    
    return toast


def create_main_window(title: str, width: int, height: int,
                     config: Optional[Dict[str, Any]] = None) -> ctk.CTk:
    """
    Create a main application window with standard configuration.
    
    Args:
        title: Window title
        width: Window width
        height: Window height
        config: Optional custom configuration
        
    Returns:
        Configured CTk window
    """
    window = ctk.CTk()
    window.title(title)
    window.geometry(f"{width}x{height}")
    
    # Apply configuration
    base_config = WindowConfig.MAIN_WINDOW.copy()
    if config:
        base_config.update(config)
    
    configure_window(window, base_config)
    center_window_on_screen(window, width, height)
    
    return window


def apply_drag_and_drop(window: Union[ctk.CTk, CTkToplevel, ctk.CTkFrame]) -> None:
    """
    Apply drag and drop functionality to a window or frame.
    
    Args:
        window: The window or frame to make draggable
    """
    drag_state = {"offset_x": 0, "offset_y": 0, "is_dragging": False}

    def _start_drag(event):
        # Calculate offset between pointer and top-left corner of window
        # Use root coordinates for accurate positioning
        if isinstance(window, (ctk.CTk, CTkToplevel)):
            drag_state["offset_x"] = event.x_root - window.winfo_rootx()
            drag_state["offset_y"] = event.y_root - window.winfo_rooty()
        else:
            # For frames, get the parent window's root position
            parent = window.winfo_toplevel()
            if isinstance(parent, (ctk.CTk, CTkToplevel)):
                drag_state["offset_x"] = event.x_root - parent.winfo_rootx()
                drag_state["offset_y"] = event.y_root - parent.winfo_rooty()
        drag_state["is_dragging"] = True

    def _on_drag(event):
        if not drag_state["is_dragging"]:
            return
            
        # New window position to keep pointer at same offset
        new_x = event.x_root - drag_state["offset_x"]
        new_y = event.y_root - drag_state["offset_y"]
        # For frames, we need to move the parent window
        if isinstance(window, (ctk.CTk, CTkToplevel)):
            window.geometry(f"+{new_x}+{new_y}")
        else:
            # For frames, move the parent window
            parent = window.winfo_toplevel()
            if isinstance(parent, (ctk.CTk, CTkToplevel)):
                parent.geometry(f"+{new_x}+{new_y}")

    def _stop_drag(event):
        drag_state["is_dragging"] = False

    # Store the bound functions so they can be unbound later
    if not hasattr(window, '_drag_bindings'):
        window._drag_bindings = []
    
    # Bind events and store references
    bindings = [
        ("<Button-1>", _start_drag),
        ("<B1-Motion>", _on_drag),
        ("<ButtonRelease-1>", _stop_drag)
    ]
    
    for event, callback in bindings:
        window.bind(event, callback, add=True)
        window._drag_bindings.append((event, callback))
    
    # Bind to window destruction to clean up
    def _cleanup_drag_bindings():
        try:
            if hasattr(window, '_drag_bindings'):
                for event, callback in window._drag_bindings:
                    try:
                        window.unbind(event, callback)
                    except:
                        pass  # Event might already be unbound
                delattr(window, '_drag_bindings')
        except:
            pass  # Window might already be destroyed
    
    window.bind("<Destroy>", lambda e: _cleanup_drag_bindings(), add=True)


def apply_window_styling(window: ctk.CTkBaseClass, 
                        fg_color: Optional[str] = None,
                        bg_color: Optional[str] = None) -> None:
    """
    Apply standard window styling.
    
    Args:
        window: The window to style
        fg_color: Foreground color (defaults to AppConfig surface color)
        bg_color: Background color
    """
    if fg_color is None:
        fg_color = AppConfig.COLORS.get("surface", "#FFFFFF")
    
    window.configure(fg_color=fg_color)
    if bg_color:
        window.configure(bg_color=bg_color)


# Legacy function for backward compatibility
def top_centered_child_to_parent(win: CTkToplevel, parent: Union[ctk.CTk, CTkToplevel], 
                                child_w: int, child_h: int, y_offset: int = 20) -> None:
    """
    Configure stacking, focus and position of a child Toplevel window centered
    at the top of its parent.

    Args:
        win: The child CTkToplevel window.
        parent: The parent CTk window.
        child_w: Desired child window width.
        child_h: Desired child window height.
        y_offset: Vertical offset from the top of the parent.
    """
    center_window_on_parent(win, parent, child_w, child_h, y_offset)


def close_window_safely(window: ctk.CTkBaseClass) -> None:
    """
    Safely close a window with proper cleanup.
    
    Args:
        window: The window to close
    """
    try:
        if window and hasattr(window, 'destroy'):
            window.destroy()
    except Exception as e:
        print(f"Warning: Error closing window: {e}")
