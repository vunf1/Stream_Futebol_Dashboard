"""
Window Utilities Examples

This module demonstrates how to use the new window utilities to replace
redundant code patterns found throughout the codebase.
"""

import customtkinter as ctk
from .window_utils import (
    create_modal_dialog,
    create_popup_dialog,
    create_toast_window,
    create_main_window,
    center_window_on_screen,
    configure_window,
    WindowConfig
)
from .window_base import ModalDialog, PopupDialog, ToastWindow


def example_old_modal_dialog(parent):
    """
    OLD WAY - Redundant code pattern found in multiple files:
    
    # This pattern is repeated in:
    # - src/ui/edit_teams_ui.py
    # - src/licensing/license_modal.py
    # - src/licensing/license_details_window.py
    # - src/core/helpers.py
    """
    # OLD CODE (redundant):
    """
    dlg = ctk.CTkToplevel(parent)
    dlg.title("Confirm Deletion")
    dlg.geometry("400x200")
    dlg.grab_set()
    dlg.attributes("-topmost", True)
    
    # Center the dialog
    dlg.update_idletasks()
    x = (dlg.winfo_screenwidth() // 2) - (400 // 2)
    y = (dlg.winfo_screenheight() // 2) - (200 // 2)
    dlg.geometry(f"400x200+{x}+{y}")
    """
    
    # NEW WAY - Using window utilities:
    dlg = create_modal_dialog(parent, "Confirm Deletion", 400, 200)
    return dlg


def example_old_popup_dialog(parent):
    """
    OLD WAY - Redundant popup pattern:
    
    # This pattern is repeated in:
    # - src/ui/edit_teams_ui.py (EditTeamPopup)
    # - src/ui/teamsUI/autocomplete.py
    """
    # OLD CODE (redundant):
    """
    popup = ctk.CTkToplevel(parent)
    popup.title("Edit Team")
    popup.geometry("400x320")
    popup.grab_set()
    popup.attributes("-topmost", True)
    
    # Center the popup
    popup.update_idletasks()
    x = (popup.winfo_screenwidth() // 2) - (400 // 2)
    y = (popup.winfo_screenheight() // 2) - (320 // 2)
    popup.geometry(f"400x320+{x}+{y}")
    """
    
    # NEW WAY - Using window utilities:
    popup = create_popup_dialog(parent, "Edit Team", 400, 320)
    return popup


def example_old_toast_window():
    """
    OLD WAY - Redundant toast pattern:
    
    # This pattern is repeated in:
    # - src/notification/toast.py
    # - src/notification/notification_server.py
    """
    # OLD CODE (redundant):
    """
    toast = ctk.CTkToplevel()
    toast.geometry(f"{width}x{height}")
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)
    """
    
    # NEW WAY - Using window utilities:
    toast = create_toast_window(300, 100)
    return toast


def example_old_main_window():
    """
    OLD WAY - Redundant main window pattern:
    
    # This pattern is repeated in:
    # - src/goal_score.py
    """
    # OLD CODE (redundant):
    """
    window = ctk.CTk()
    window.title("Campos")
    window.geometry(f"{width}x{height}")
    window.overrideredirect(True)
    window.attributes("-topmost", True)
    window.resizable(False, False)
    apply_drag_and_drop(window)
    
    # Center the window
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")
    """
    
    # NEW WAY - Using window utilities:
    window = create_main_window("Campos", 600, 400)
    return window


def example_using_base_classes():
    """
    Using the new base classes for cleaner code:
    """
    
    # Using ModalDialog class
    class ConfirmDialog(ModalDialog):
        def __init__(self, parent, message):
            super().__init__(parent, "Confirm", 400, 200)
            
            # Add content
            label = ctk.CTkLabel(self, text=message)
            label.pack(pady=20)
            
            # Add buttons
            btn_frame = ctk.CTkFrame(self)
            btn_frame.pack(pady=20)
            
            ctk.CTkButton(btn_frame, text="OK", command=self.destroy).pack(side="left", padx=10)
            ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=10)
    
    # Using PopupDialog class
    class EditDialog(PopupDialog):
        def __init__(self, parent, title):
            super().__init__(parent, title, 400, 300)
            
            # Add form content
            form_frame = ctk.CTkFrame(self)
            form_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            ctk.CTkLabel(form_frame, text="Name:").pack(anchor="w")
            ctk.CTkEntry(form_frame).pack(fill="x", pady=(0, 10))
            
            ctk.CTkButton(form_frame, text="Save", command=self.destroy).pack(pady=10)
    
    # Using ToastWindow class
    class NotificationToast(ToastWindow):
        def __init__(self, message):
            super().__init__(300, 80)
            
            ctk.CTkLabel(self, text=message).pack(pady=20)
    
    return ConfirmDialog, EditDialog, NotificationToast


def example_custom_configuration():
    """
    Example of using custom configuration with the utilities:
    """
    
    # Custom configuration for a special dialog
    custom_config = {
        "overrideredirect": True,
        "topmost": True,
        "grab_set": True,
        "resizable": (True, True),  # Allow resizing
        "focus_force": True,
        "lift": True
    }
    
    # Create dialog with custom config
    dialog = create_modal_dialog(
        parent=None,  # No parent for screen-centered dialog
        title="Custom Dialog",
        width=500,
        height=300,
        config=custom_config
    )
    
    return dialog


def example_migration_guide():
    """
    Migration guide for replacing old patterns:
    """
    
    migration_examples = {
        "old_modal_pattern": """
        # OLD:
        dlg = ctk.CTkToplevel(parent)
        dlg.title("Title")
        dlg.geometry("400x200")
        dlg.grab_set()
        dlg.attributes("-topmost", True)
        dlg.update_idletasks()
        x = (dlg.winfo_screenwidth() // 2) - (400 // 2)
        y = (dlg.winfo_screenheight() // 2) - (200 // 2)
        dlg.geometry(f"400x200+{x}+{y}")
        
        # NEW:
        dlg = create_modal_dialog(parent, "Title", 400, 200)
        """,
        
        "old_popup_pattern": """
        # OLD:
        popup = ctk.CTkToplevel(parent)
        popup.title("Title")
        popup.geometry("400x320")
        popup.grab_set()
        popup.attributes("-topmost", True)
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (400 // 2)
        y = (popup.winfo_screenheight() // 2) - (320 // 2)
        popup.geometry(f"400x320+{x}+{y}")
        
        # NEW:
        popup = create_popup_dialog(parent, "Title", 400, 320)
        """,
        
        "old_toast_pattern": """
        # OLD:
        toast = ctk.CTkToplevel()
        toast.geometry(f"{width}x{height}")
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        
        # NEW:
        toast = create_toast_window(width, height)
        """,
        
        "old_main_window_pattern": """
        # OLD:
        window = ctk.CTk()
        window.title("Title")
        window.geometry(f"{width}x{height}")
        window.overrideredirect(True)
        window.attributes("-topmost", True)
        window.resizable(False, False)
        apply_drag_and_drop(window)
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")
        
        # NEW:
        window = create_main_window("Title", width, height)
        """
    }
    
    return migration_examples
