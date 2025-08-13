"""
License Blocker
Prevents application usage when licenses are invalid and shows blocking messages.
"""

import customtkinter as ctk
from typing import Callable, Optional
from .license_manager import LicenseManager, LicenseStatus

class LicenseBlocker:
    """Blocks application usage when licenses are invalid."""
    
    def __init__(self, parent, on_license_valid: Optional[Callable] = None):
        """
        Initialize the license blocker.
        
        Args:
            parent: Parent widget to block
            on_license_valid: Optional callback to execute when license becomes valid
        """
        self.parent = parent
        self.license_manager = LicenseManager()
        self.blocking_frame = None
        self.is_blocked = False
        self.on_license_valid = on_license_valid
        self._listener_active = True
        
        # Start listening for license activation notifications from other instances
        self._start_license_notification_listener()
        
    def _start_license_notification_listener(self):
        """Start listening for license activation notifications from other instances."""
        def check_for_license_updates():
            try:
                # Check if listener should continue
                if not self._listener_active:
                    return
                
                # Check if license status has changed (e.g., another instance activated it)
                if self.is_blocked:
                    # First check the signal file from other instances
                    if self._check_license_activation_signal():
                        print("License activation signal detected from another instance, checking status...")
                        # Small delay to ensure the license file is fully written
                        self.parent.after(500, self._check_and_continue_if_valid)
                        return
                    
                    # Also check direct license status
                    status, is_valid = self.license_manager.get_license_status()
                    if is_valid:
                        print("License became valid (detected by direct check), unblocking...")
                        self._remove_blocking()
                        if self.on_license_valid:
                            self.on_license_valid()
                        return
                
                # Continue listening if still active
                if self._listener_active:
                    self.parent.after(1000, check_for_license_updates)  # Check every second
            except Exception as e:
                print(f"Error in license notification listener: {e}")
                # Continue listening even if there's an error
                if self._listener_active:
                    self.parent.after(1000, check_for_license_updates)
        
        # Start the listener
        self.parent.after(1000, check_for_license_updates)
    
    def stop_notification_listener(self):
        """Stop the notification listener."""
        self._listener_active = False
        print("License notification listener stopped")
    
    def _check_license_activation_signal(self) -> bool:
        """Check if another instance has activated a license."""
        try:
            import os
            import tempfile
            
            temp_dir = tempfile.gettempdir()
            signal_file = os.path.join(temp_dir, "license_activated_signal")
            
            if os.path.exists(signal_file):
                # Check if the signal file is recent (within last 10 seconds)
                import time
                current_time = time.time()
                
                try:
                    with open(signal_file, 'r') as f:
                        signal_time = float(f.read().strip())
                    
                    # If signal is recent, consider it valid
                    if current_time - signal_time < 10:
                        return True
                    else:
                        # Remove old signal file
                        os.remove(signal_file)
                except (ValueError, IOError):
                    # Remove corrupted signal file
                    try:
                        os.remove(signal_file)
                    except:
                        pass
                        
            return False
            
        except Exception as e:
            print(f"Error checking license activation signal: {e}")
            return False
    
    def _check_and_continue_if_valid(self):
        """Check license status and continue if valid."""
        try:
            # Clean up the signal file first
            self._cleanup_license_activation_signal()
            
            status, is_valid = self.license_manager.get_license_status()
            if is_valid:
                print("License confirmed valid after signal detection, unblocking...")
                self._remove_blocking()
                if self.on_license_valid:
                    self.on_license_valid()
            else:
                print("License still invalid after signal detection, continuing to listen...")
        except Exception as e:
            print(f"Error checking license status after signal: {e}")
    
    def _cleanup_license_activation_signal(self):
        """Clean up the license activation signal file."""
        try:
            import os
            import tempfile
            
            temp_dir = tempfile.gettempdir()
            signal_file = os.path.join(temp_dir, "license_activated_signal")
            
            if os.path.exists(signal_file):
                os.remove(signal_file)
                print("License activation signal file cleaned up")
                
        except Exception as e:
            print(f"Error cleaning up license activation signal: {e}")
    
    def check_and_block(self) -> bool:
        """
        Check license status and block if invalid.
        
        Returns:
            True if app should continue, False if blocked
        """
        try:
            print("=== License Check Started ===")
            status, is_valid = self.license_manager.get_license_status()
            print(f"License status: {status}, is_valid: {is_valid}")
            
            # Get detailed license info for debugging
            license_details = self.license_manager.get_license_details()
            if license_details:
                print("License details:")
                for key, value in license_details.items():
                    if key != "_debug":  # Skip internal debug info
                        print(f"  {key}: {value}")
                if "_debug" in license_details:
                    print("Debug info:")
                    for key, value in license_details["_debug"].items():
                        print(f"    {key}: {value}")
            else:
                print("No license details available")
            
            if is_valid:
                # License is valid, remove any blocking
                print("License is valid, removing blocking and continuing...")
                self._remove_blocking()
                return True
            else:
                # License is invalid, show blocking
                print(f"License is invalid (status: {status}), showing blocking UI...")
                self._show_blocking(status)
                return False
                
        except Exception as e:
            print(f"Error checking license: {e}")
            import traceback
            traceback.print_exc()
            self._show_blocking("not_found")
            return False
    
    def _show_blocking(self, status: LicenseStatus):
        """Show blocking overlay for invalid license."""
        if self.is_blocked:
            return
            
        self.is_blocked = True
        
        # Create blocking overlay
        self.blocking_frame = ctk.CTkFrame(
            self.parent,
            fg_color="#1a1a1a"  # Dark background instead of rgba
        )
        self.blocking_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Center content frame
        content_frame = ctk.CTkFrame(
            self.blocking_frame,
            fg_color="#2b2b2b",
            corner_radius=15
        )
        content_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Status icon
        if status in ["active", "trial"]:
            icon_text = "✅"
            icon_color = "#28a745"
        else:
            icon_text = "❌"
            icon_color = "#dc3545"
        
        icon_label = ctk.CTkLabel(
            content_frame,
            text=icon_text,
            font=("Segoe UI Emoji", 48),
            text_color=icon_color
        )
        icon_label.pack(pady=(30, 20))
        
        # Status title
        status_text = self.license_manager.get_status_display_text(status)
        title_label = ctk.CTkLabel(
            content_frame,
            text=status_text,
            font=("Segoe UI", 24, "bold"),
            text_color="white"
        )
        title_label.pack(pady=(0, 10))
        
        # Status description
        description = self._get_status_description(status)
        desc_label = ctk.CTkLabel(
            content_frame,
            text=description,
            font=("Segoe UI", 14),
            text_color="gray",
            wraplength=400
        )
        desc_label.pack(pady=(0, 30))
        
        # Action buttons
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(pady=(0, 30))
        
        if status in ["expired", "trial_expired", "blocked", "not_found"]:
            # Show activation button
            activate_button = ctk.CTkButton(
                button_frame,
                text="Activate License",
                command=self._activate_license,
                font=("Segoe UI", 14, "bold"),
                height=40,
                fg_color="#007bff",
                hover_color="#0056b3"
            )
            activate_button.pack(side="left", padx=(0, 10))
        
        # Exit button
        exit_button = ctk.CTkButton(
            button_frame,
            text="Exit Application",
            command=self._exit_app,
            font=("Segoe UI", 14),
            height=40,
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        exit_button.pack(side="left")
        
        # Make blocking frame modal
        self.blocking_frame.focus_set()
        self.blocking_frame.grab_set()
    
    def _remove_blocking(self):
        """Remove blocking overlay."""
        if self.blocking_frame and self.blocking_frame.winfo_exists():
            self.blocking_frame.destroy()
            self.blocking_frame = None
        self.is_blocked = False
        
        # Stop the notification listener since we're no longer blocked
        self.stop_notification_listener()
    
    def _get_status_description(self, status: LicenseStatus) -> str:
        """Get description text for a given status."""
        descriptions = {
            "active": "Your license is active and valid. You have full access to all features.",
            "trial": "You are using a trial version. Some features may be limited.",
            "expired": "Your license has expired. Please renew to continue using the application.",
            "trial_expired": "Your trial period has expired. Please purchase a license to continue.",
            "blocked": "Your license has been blocked. Please contact support for assistance.",
            "not_found": "No valid license found. Please activate a license to continue."
        }
        return descriptions.get(status, "Unknown license status.")
    
    def _activate_license(self):
        """Show license activation dialog."""
        try:
            from .license_modal import LicenseActivationDialog
            
            def on_license_activated(license_data):
                """Callback when license is successfully activated."""
                print(f"🔍 License activation callback received data: {license_data}")
                print(f"🔍 License data keys: {list(license_data.keys()) if isinstance(license_data, dict) else 'NOT A DICT'}")
                print(f"🔍 expiresAt field in callback: {license_data.get('expiresAt', 'MISSING') if isinstance(license_data, dict) else 'NOT A DICT'}")
                print(f"🔍 max_devices field in callback: {license_data.get('max_devices', 'MISSING') if isinstance(license_data, dict) else 'NOT A DICT'}")
                
                # Save the license
                if self.license_manager.save_license(license_data):
                    # Remove blocking and continue
                    self._remove_blocking()
                    print("License activated successfully!")
                    
                    # Broadcast license activation to other instances
                    self._broadcast_license_activation()
                    
                    # Execute callback to continue app setup if provided
                    if self.on_license_valid:
                        print("Executing license valid callback...")
                        self.on_license_valid()
                else:
                    print("Failed to save license")
            
            # Show the activation dialog
            LicenseActivationDialog.show(self.parent, on_license_activated)
            
        except Exception as e:
            print(f"Error showing license activation: {e}")
            import traceback
            traceback.print_exc()
    
    def _broadcast_license_activation(self):
        """Broadcast license activation to other instances."""
        try:
            # Create a temporary file or use a shared mechanism to signal other instances
            # This is a simple approach using a file-based signal
            import os
            import tempfile
            
            # Create a temporary file in a known location that other instances can check
            temp_dir = tempfile.gettempdir()
            signal_file = os.path.join(temp_dir, "license_activated_signal")
            
            # Write a timestamp to indicate when the license was activated
            import time
            with open(signal_file, 'w') as f:
                f.write(str(time.time()))
            
            print(f"License activation broadcasted to other instances via signal file: {signal_file}")
            
        except Exception as e:
            print(f"Error broadcasting license activation: {e}")
    
    def _exit_app(self):
        """Exit the application."""
        try:
            # Navigate up to find the root window
            current = self.parent
            while hasattr(current, 'winfo_toplevel'):
                current = current.winfo_toplevel()
                if hasattr(current, 'destroy'):
                    current.destroy()
                    break
        except Exception as e:
            print(f"Error exiting app: {e}")
            import sys
            sys.exit(0)
    
    def refresh_status(self):
        """Refresh license status and update blocking if needed."""
        return self.check_and_block()
    
    def is_application_blocked(self) -> bool:
        """Check if the application is currently blocked."""
        return self.is_blocked

    def start_periodic_check(self, interval_ms: int = 30000):
        """
        Start periodic license checking to ensure app stays blocked if license becomes invalid.
        
        Args:
            interval_ms: Check interval in milliseconds (default: 30 seconds)
        """
        def periodic_check():
            if not self.is_blocked:
                # Only check if not currently blocked
                status, is_valid = self.license_manager.get_license_status()
                if not is_valid:
                    print("License became invalid during runtime, blocking app...")
                    self._show_blocking(status)
            
            # Schedule next check
            self.parent.after(interval_ms, periodic_check)
        
        # Start the periodic check
        self.parent.after(interval_ms, periodic_check)

    def debug_license_status(self):
        """Debug method to test and display license validation details."""
        print("\n" + "="*60)
        print("LICENSE BLOCKER DEBUG")
        print("="*60)
        print(f"Parent widget: {self.parent}")
        print(f"Is blocked: {self.is_blocked}")
        print(f"Has callback: {self.on_license_valid is not None}")
        
        # Test license validation
        self.license_manager.test_license_validation()
        
        print("="*60 + "\n")
