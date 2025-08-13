"""
License Activation Modal
Modal window for entering and validating license codes.
"""

import customtkinter as ctk
from typing import Callable, Optional
from .license_validator import LicenseValidator
from ..ui.window_utils import apply_drag_and_drop
from ..config.settings import AppConfig

class LicenseModal:
    """Modal window for license activation."""
    
    def __init__(self, parent, on_license_activated: Callable[[dict], None]):
        """
        Initialize the license modal.
        
        Args:
            parent: Parent window
            on_license_activated: Callback function when license is successfully activated
        """
        self.parent = parent
        self.on_license_activated = on_license_activated
        self.validator = LicenseValidator()
        self.modal_window: Optional[ctk.CTkToplevel] = None
        self.result = None
        self._modal_x = 0
        self._modal_y = 0
        
    def show(self):
        """Show the license activation modal."""
        try:
            # Create modal window using window utilities
            from ..ui import create_modal_dialog
            self.modal_window = create_modal_dialog(
                self.parent, 
                "License Activation", 
                AppConfig.DIALOG_EXPANDED_WIDTH, 
                AppConfig.LICENSE_MODAL_HEIGHT
            )
            
            # Configure additional properties
            self.modal_window.configure(fg_color=("gray95", "gray15"))
            self.modal_window.attributes('-alpha', 0.0)  # Hide temporarily
            
            # Create UI components in background
            self._create_ui()
            
            # Ensure all widgets are fully rendered before showing
            self.modal_window.update()
            
            # Now show the fully prepared window by restoring alpha
            self.modal_window.attributes('-alpha', 1.0)
            
            # Make window draggable
            apply_drag_and_drop(self.modal_window)
            
            # Focus on code entry
            self.code_entry.focus_set()
            
            # Wait for the modal to be closed
            self.modal_window.wait_window()
            
            return self.result
            
        except Exception as e:
            print(f"Error creating modal: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _calculate_position(self):
        """Calculate modal position to center it on the parent window."""
        try:
            # Use window utilities for positioning
            from src.ui.window_utils import center_window_on_parent
            center_window_on_parent(
                self.modal_window, 
                self.parent, 
                AppConfig.DIALOG_EXPANDED_WIDTH, 
                AppConfig.LICENSE_MODAL_HEIGHT
            )
        except Exception as e:
            print(f"Error calculating modal position: {e}")
            # Fallback to center of screen
            from src.ui.window_utils import center_window_on_screen
            center_window_on_screen(
                self.modal_window,
                AppConfig.DIALOG_EXPANDED_WIDTH,
                AppConfig.LICENSE_MODAL_HEIGHT
            )
    
    def _create_ui(self):
        """Create the modal UI components."""
        if not self.modal_window:
            return
            
        try:
            # Configure modal window appearance before creating widgets
            self.modal_window.configure(fg_color=("gray95", "gray15"))
            
            # Disable window updates during widget creation to prevent flickering
            self.modal_window.update_idletasks()
            
            # Main container frame
            main_frame = ctk.CTkFrame(self.modal_window)
            main_frame.pack(fill="both", expand=True, padx=AppConfig.LICENSE_MODAL_PADDING, pady=AppConfig.LICENSE_MODAL_PADDING)
            
            # Content frame (non-scrollable) - removed expand to allow proper positioning
            content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            content_frame.pack(fill="x", pady=(20, 0))
            
            # Description (now the main title)
            desc_label = ctk.CTkLabel(
                content_frame,
                text="Please enter your license code to activate the application.",
                font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_DIALOG_BODY),
                text_color="gray"
            )
            desc_label.pack(pady=(10, 10))
            
            # License code entry
            code_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            code_frame.pack(fill="x", pady=(0, 5))
            
            self.code_entry = ctk.CTkEntry(
                code_frame,
                placeholder_text="Enter your license code here...",
                font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_DIALOG_BODY),
                height=AppConfig.LICENSE_MODAL_BUTTON_HEIGHT,
                state="normal"  # Ensure entry is enabled
            )
            self.code_entry.pack(fill="x", pady=(5, 0))
            
            # Error label
            self.error_label = ctk.CTkLabel(
                content_frame,
                text="",
                font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_DIALOG_BODY),
                text_color=AppConfig.COLOR_ERROR
            )
            self.error_label.pack(pady=(5, 0))
            
            # Progress bar (hidden by default)
            self.progress_bar = ctk.CTkProgressBar(content_frame)
            self.progress_bar.pack(fill="x", pady=(10, 0))
            self.progress_bar.set(0)
            self.progress_bar.pack_forget()  # Hide initially
            
            # Buttons frame - positioned right after content
            button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            button_frame.pack(fill="x", pady=(0, 0))
            
            # Submit button - centered
            self.submit_button = ctk.CTkButton(
                button_frame,
                text="Activate License",
                command=self._activate_license,
                font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_DIALOG_BODY, "bold"),
                height=AppConfig.LICENSE_MODAL_BUTTON_HEIGHT,
                fg_color=AppConfig.COLOR_SUCCESS,
                hover_color=AppConfig.COLOR_ACTIVE
            )
            self.submit_button.pack(expand=True, padx=100)
            
            # Footer - positioned right after button
            footer_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            footer_frame.pack(fill="x", pady=(0, 0), padx=6)
            
            # Footer label (left side)
            footer_label = ctk.CTkLabel(
                footer_frame, 
                text="© 2025 Vunf1", 
                font=(AppConfig.FONT_FAMILY_EMOJI, 10), 
                text_color="gray"
            )
            footer_label.pack(side="left")
            
            # Close button (X) - Modern transparent design
            close_button = ctk.CTkButton(
                footer_frame, 
                text="✕", 
                width=AppConfig.LICENSE_MODAL_CLOSE_BUTTON_SIZE,
                height=AppConfig.LICENSE_MODAL_CLOSE_BUTTON_SIZE,
                font=(AppConfig.FONT_FAMILY_EMOJI, 12, "bold"),
                fg_color="transparent",
                hover_color=AppConfig.COLOR_SURFACE,
                text_color=AppConfig.COLOR_TEXT_SECONDARY,
                corner_radius=12,
                command=self._cancel
            )
            close_button.pack(side="right", padx=(3, 0))
            
            # Bind Enter key to submit
            self.code_entry.bind("<Return>", lambda e: self._activate_license())
            
            # Focus on code entry
            self.code_entry.focus_set()
            
        except Exception as e:
            print(f"ERROR in _create_ui: {e}")
            import traceback
            traceback.print_exc()
    
    def _activate_license(self):
        """Activate the license with the entered code."""
        code = self.code_entry.get().strip()
        
        if not code:
            self._show_error("Please enter a license code.")
            return
        
        # Show progress
        self._show_progress(True)
        self.submit_button.configure(state="disabled")
        self.code_entry.configure(state="disabled")
        
        # Validate license
        try:
            # Get machine hash from LicenseManager
            from .license_manager import LicenseManager
            license_manager = LicenseManager()
            machine_hash = license_manager.get_machine_hash()
            
            # Try to validate against MongoDB first, fallback to mock validation
            license_data, status = self.validator.validate_license_code(code, machine_hash)
            
            if status in ["active", "trial"]:
                # Success - call callback and close modal
                self.result = license_data
                self.on_license_activated(license_data)
                if self.modal_window:
                    print("License activated successfully, closing modal...")
                    self.modal_window.destroy()
            else:
                # Show error and re-enable input
                error_msg = license_data.get("error", "License validation failed")
                self._show_error(error_msg)
                self._show_progress(False)
                self.submit_button.configure(state="normal")
                self.code_entry.configure(state="normal")
                self.code_entry.focus_set()  # Re-focus on entry
                
        except Exception as e:
            self._show_error(f"An error occurred: {str(e)}")
            self._show_progress(False)
            self.submit_button.configure(state="normal")
            self.code_entry.configure(state="normal")
            self.code_entry.focus_set()  # Re-focus on entry
    
    def _show_error(self, message: str):
        """Show an error message."""
        self.error_label.configure(text=message)
        self.error_label.pack(pady=(5, 0))
    
    def _show_progress(self, show: bool):
        """Show or hide the progress bar."""
        if show:
            self.progress_bar.pack(fill="x", pady=(10, 0))
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
    
    def _cancel(self):
        """Cancel the license activation."""
        if self.modal_window:
            print("Cancelling license activation, closing modal...")
            self.modal_window.destroy()

    # Removed complex topmost enforcement methods that could interfere with text input

class LicenseActivationDialog:
    """Simplified dialog for license activation."""
    
    @staticmethod
    def show(parent, on_license_activated: Callable[[dict], None]) -> Optional[dict]:
        """
        Show license activation dialog.
        
        Args:
            parent: Parent window
            on_license_activated: Callback when license is activated
            
        Returns:
            License data if activated, None if cancelled
        """
        modal = LicenseModal(parent, on_license_activated)
        return modal.show()
