"""
License Activation Modal
Modal window for entering and validating license codes.
"""

import customtkinter as ctk
from typing import Callable, Optional
from helpers.license_validator import LicenseValidator

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
        
    def show(self):
        """Show the license activation modal."""
        try:
            # Create modal window
            self.modal_window = ctk.CTkToplevel(self.parent)
            self.modal_window.title("License Activation")
            self.modal_window.geometry("400x300")
            self.modal_window.resizable(False, False)
            
            # Ensure modal is on top of ALL applications
            self.modal_window.lift()
            self.modal_window.attributes('-topmost', True)
            
            # Make modal grab all input (modal behavior)
            self.modal_window.grab_set()
            self.modal_window.transient(self.parent)
            
            # Additional window management attributes
            self.modal_window.attributes('-toolwindow', False)  # Keep in taskbar
            self.modal_window.attributes('-alpha', 1.0)  # Full opacity
            
            # Create UI components
            self._create_ui()
            
            # Position modal in center of parent
            self._center_modal()
            
            # Make modal focus and ensure it's visible
            self.modal_window.focus_set()
            self.modal_window.focus_force()
            
            # Additional focus management
            self.modal_window.grab_release()  # Release grab temporarily
            self.modal_window.grab_set()      # Re-grab to ensure focus
            self.modal_window.focus_set()     # Set focus again
            
            print(f"Modal window created: {self.modal_window}")
            print(f"Modal geometry: {self.modal_window.geometry()}")
            print(f"Modal visible: {self.modal_window.winfo_viewable()}")
            
            # Force update to ensure visibility
            self.modal_window.update()
            self.modal_window.update_idletasks()
            
            print(f"After update - Modal visible: {self.modal_window.winfo_viewable()}")
            
            # Start periodic focus enforcement to keep modal on top
            self._enforce_topmost()
            
            # Bind events to ensure modal stays on top
            self._bind_topmost_events()
            
            # Don't use wait_window() - let the modal handle its own lifecycle
            # The modal will close itself when license is activated or cancelled
            
            return self.result
            
        except Exception as e:
            print(f"Error creating modal: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _center_modal(self):
        """Center the modal on the parent window."""
        try:
            if not self.modal_window:
                return
                
            # Get parent window position and size
            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()
            
            # Get modal size
            modal_width = 400
            modal_height = 300
            
            # Calculate center position
            x = parent_x + (parent_width - modal_width) // 2
            y = parent_y + (parent_height - modal_height) // 2
            
            # Ensure modal is on screen
            x = max(0, x)
            y = max(0, y)
            
            # Position modal
            self.modal_window.geometry(f"{modal_width}x{modal_height}+{x}+{y}")
            
        except Exception as e:
            print(f"Error centering modal: {e}")
            # Fallback to center of screen
            if self.modal_window:
                self.modal_window.geometry("400x300+100+100")
    
    def _create_ui(self):
        """Create the modal UI components."""
        if not self.modal_window:
            return
            
        # Main frame
        main_frame = ctk.CTkFrame(self.modal_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Enter License Code", 
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack(pady=(20, 10))
        
        # Description
        desc_label = ctk.CTkLabel(
            main_frame,
            text="Please enter your license code to activate the application.",
            font=("Segoe UI", 12),
            text_color="gray"
        )
        desc_label.pack(pady=(0, 20))
        
        # License code entry
        code_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        code_frame.pack(fill="x", pady=(0, 10))
        
        code_label = ctk.CTkLabel(code_frame, text="License Code:", font=("Segoe UI", 12))
        code_label.pack(anchor="w")
        
        self.code_entry = ctk.CTkEntry(
            code_frame,
            placeholder_text="Enter your license code here...",
            font=("Segoe UI", 12),
            height=35
        )
        self.code_entry.pack(fill="x", pady=(5, 0))
        
        # Error label
        self.error_label = ctk.CTkLabel(
            main_frame,
            text="",
            font=("Segoe UI", 11),
            text_color="#dc3545"
        )
        self.error_label.pack(pady=(5, 0))
        
        # Buttons frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))
        
        # Submit button
        self.submit_button = ctk.CTkButton(
            button_frame,
            text="Activate License",
            command=self._activate_license,
            font=("Segoe UI", 12, "bold"),
            height=35,
            fg_color="#28a745",
            hover_color="#218838"
        )
        self.submit_button.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Cancel button
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._cancel,
            font=("Segoe UI", 12),
            height=35,
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        cancel_button.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        # Progress bar (hidden by default)
        self.progress_bar = ctk.CTkProgressBar(main_frame)
        self.progress_bar.pack(fill="x", pady=(10, 0))
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()  # Hide initially
        
        # Bind Enter key to submit
        self.code_entry.bind("<Return>", lambda e: self._activate_license())
        
        # Focus on code entry
        self.code_entry.focus()
    
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
            from helpers.license_manager import LicenseManager
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
                # Show error
                error_msg = license_data.get("error", "License validation failed")
                self._show_error(error_msg)
                self._show_progress(False)
                self.submit_button.configure(state="normal")
                self.code_entry.configure(state="normal")
                
        except Exception as e:
            self._show_error(f"An error occurred: {str(e)}")
            self._show_progress(False)
            self.submit_button.configure(state="normal")
            self.code_entry.configure(state="normal")
    
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

    def _enforce_topmost(self):
        """Periodically enforce that the modal stays on top of all applications."""
        if not self.modal_window or not self.modal_window.winfo_exists():
            return
            
        try:
            # Ensure modal is still on top
            self.modal_window.lift()
            self.modal_window.attributes('-topmost', True)
            
            # Windows-specific: Force window to front
            try:
                self.modal_window.wm_state('normal')  # Ensure window is not minimized
                self.modal_window.deiconify()  # Show window if it was hidden
            except:
                pass  # Ignore if not supported
            
            # Schedule next enforcement
            self.modal_window.after(100, self._enforce_topmost)
            
        except Exception as e:
            print(f"Error enforcing topmost: {e}")
            # Stop enforcement on error
            pass

    def _bind_topmost_events(self):
        """Bind events to ensure the modal stays on top."""
        if not self.modal_window:
            return
            
        # Bind focus out event
        self.modal_window.bind("<FocusOut>", lambda e: self._enforce_topmost())
        
        # Bind click event
        self.modal_window.bind("<Button-1>", lambda e: self._enforce_topmost())

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
