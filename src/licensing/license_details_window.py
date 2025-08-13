"""
License Details Window
Shows detailed license information in a clean, simple UI.
"""

import customtkinter as ctk
from datetime import datetime, timezone
from typing import Optional, Dict
from .license_manager import LicenseManager
from ..ui.make_drag_drop import make_it_drag_and_drop
from ..config.settings import AppConfig


class LicenseDetailsWindow:
    """Window to display detailed license information."""
    
    def __init__(self, parent):
        self.parent = parent
        self.license_manager = LicenseManager()
        self.window = None
        
    def show(self):
        """Show the license details window."""
        if self.window is not None:
            self.window.focus_force()
            return
            
        # Create the window
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("License Details")
        self.window.geometry(f"{AppConfig.DIALOG_WIDTH}x{AppConfig.DIALOG_HEIGHT + 175}")
        self.window.resizable(False, False)
        
        # Set window background color to match main frame
        self.window.configure(fg_color=AppConfig.COLORS["surface"])
        
        # Remove window border
        self.window.overrideredirect(True)
        
        # Center the window on parent
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Make window appear on top
        self.window.attributes('-topmost', True)
        self.window.after(100, lambda: self.window.attributes('-topmost', False))
        
        # Configure window close event
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Make window draggable
        make_it_drag_and_drop(self.window)
        
        # Create the UI
        self._create_ui()
        
        # Load license data
        self._load_license_data()
        
    def _create_ui(self):
        """Create the user interface."""
        # Main container
        main_frame = ctk.CTkFrame(self.window, fg_color=AppConfig.COLORS["surface"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="License Information",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_SUBTITLE, "bold"),
            text_color=AppConfig.COLORS["text"]
        )
        title_label.pack(pady=(0, 10))
        
        # Scrollable content frame
        self.content_frame = ctk.CTkScrollableFrame(
            main_frame,
            fg_color="transparent",
            width=AppConfig.DIALOG_WIDTH - 20,
            height=AppConfig.DIALOG_HEIGHT + 50
        )
        self.content_frame.pack(fill="x", padx=5, pady=(0, 10))
        
        # Status section
        self._create_status_section(self.content_frame)
        
        # Details section
        self._create_details_section(self.content_frame)
        
        # Features section
        self._create_features_section(self.content_frame)
        
        # User information section
        self._create_user_section(self.content_frame)
        
        # Footer (fixed at bottom)
        self._create_footer(main_frame)
        
    def _create_status_section(self, parent):
        """Create the status section."""
        # Status frame
        status_frame = ctk.CTkFrame(parent, fg_color="transparent")
        status_frame.pack(fill="x", padx=15, pady=(15, 6))
        
        # Status label
        status_title = ctk.CTkLabel(
            status_frame,
            text="Status:",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_BODY, "bold"),
            text_color=AppConfig.COLORS["text_secondary"]
        )
        status_title.pack(anchor="w")
        
        # Status value
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Loading...",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_DIALOG_BODY, "bold"),
            text_color=AppConfig.COLORS["text"]
        )
        self.status_label.pack(anchor="w", pady=(3, 0))
        
    def _create_details_section(self, parent):
        """Create the details section."""
        # Details frame
        details_frame = ctk.CTkFrame(parent, fg_color="transparent")
        details_frame.pack(fill="x", padx=15, pady=6)
        
        # License Code
        code_title = ctk.CTkLabel(
            details_frame,
            text="License Code:",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_BODY, "bold"),
            text_color=AppConfig.COLORS["text_secondary"]
        )
        code_title.pack(anchor="w")
        
        self.code_label = ctk.CTkLabel(
            details_frame,
            text="Loading...",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_BODY),
            text_color=AppConfig.COLORS["text"]
        )
        self.code_label.pack(anchor="w", pady=(3, 0))
        
        # Expiration
        expires_title = ctk.CTkLabel(
            details_frame,
            text="Expires:",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_BODY, "bold"),
            text_color=AppConfig.COLORS["text_secondary"]
        )
        expires_title.pack(anchor="w", pady=(6, 0))
        
        self.expires_label = ctk.CTkLabel(
            details_frame,
            text="Loading...",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_BODY),
            text_color=AppConfig.COLORS["text"]
        )
        self.expires_label.pack(anchor="w", pady=(3, 0))
        
        # Issued Date
        issued_title = ctk.CTkLabel(
            details_frame,
            text="Issued:",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_BODY, "bold"),
            text_color=AppConfig.COLORS["text_secondary"]
        )
        issued_title.pack(anchor="w", pady=(6, 0))
        
        self.issued_label = ctk.CTkLabel(
            details_frame,
            text="Loading...",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_BODY),
            text_color=AppConfig.COLORS["text"]
        )
        self.issued_label.pack(anchor="w", pady=(5, 0))
        
    def _create_features_section(self, parent):
        """Create the features section."""
        # Features frame
        features_frame = ctk.CTkFrame(parent, fg_color="transparent")
        features_frame.pack(fill="x", padx=15, pady=6)
        
        # Features title
        features_title = ctk.CTkLabel(
            features_frame,
            text="Features:",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_BODY, "bold"),
            text_color=AppConfig.COLORS["text_secondary"]
        )
        features_title.pack(anchor="w")
        
        # Features list
        self.features_label = ctk.CTkLabel(
            features_frame,
            text="Loading...",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_BODY),
            text_color=AppConfig.COLORS["text"],
            wraplength=AppConfig.DIALOG_WIDTH - 50
        )
        self.features_label.pack(anchor="w", pady=(3, 0))
        
    def _create_user_section(self, parent):
        """Create the user information section."""
        # User info frame
        user_frame = ctk.CTkFrame(parent, fg_color="transparent")
        user_frame.pack(fill="x", padx=15, pady=6)
        
        # User info title
        user_title = ctk.CTkLabel(
            user_frame,
            text="User Information:",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_BODY, "bold"),
            text_color=AppConfig.COLORS["text_secondary"]
        )
        user_title.pack(anchor="w")
        
        # User name
        user_name_title = ctk.CTkLabel(
            user_frame,
            text="Name:",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_BODY, "bold"),
            text_color=AppConfig.COLORS["text_secondary"]
        )
        user_name_title.pack(anchor="w", pady=(6, 0))
        
        self.user_name_label = ctk.CTkLabel(
            user_frame,
            text="Loading...",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_BODY),
            text_color=AppConfig.COLORS["text"]
        )
        self.user_name_label.pack(anchor="w", pady=(3, 0))
        
        # Email
        email_title = ctk.CTkLabel(
            user_frame,
            text="Email:",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_BODY, "bold"),
            text_color=AppConfig.COLORS["text_secondary"]
        )
        email_title.pack(anchor="w", pady=(6, 0))
        
        self.email_label = ctk.CTkLabel(
            user_frame,
            text="Loading...",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_BODY),
            text_color=AppConfig.COLORS["text"]
        )
        self.email_label.pack(anchor="w", pady=(3, 0))
        
        # Company
        company_title = ctk.CTkLabel(
            user_frame,
            text="Company:",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_BODY, "bold"),
            text_color=AppConfig.COLORS["text_secondary"]
        )
        company_title.pack(anchor="w", pady=(6, 0))
        
        self.company_label = ctk.CTkLabel(
            user_frame,
            text="Loading...",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_BODY),
            text_color=AppConfig.COLORS["text"]
        )
        self.company_label.pack(anchor="w", pady=(5, 0))
        
    def _create_footer(self, parent):
        """Create the footer with close button and copyright."""
        # Footer frame - fixed at bottom
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", padx=6, pady=(10, 5))
        
        # Footer label (left side)
        footer = ctk.CTkLabel(
            footer_frame, 
            text="© 2025 Vunf1", 
            font=(AppConfig.FONT_FAMILY_EMOJI, 10), 
            text_color=AppConfig.COLORS["text_secondary"]
        )
        footer.pack(side="left")
        
        # Close button (X) - Modern transparent design
        close_button = ctk.CTkButton(
            footer_frame, 
            text="✕", 
            width=24, 
            height=24,
            font=(AppConfig.FONT_FAMILY_EMOJI, 12, "bold"),
            fg_color="transparent",
            hover_color=AppConfig.COLORS["surface"],
            text_color=AppConfig.COLORS["text_secondary"],
            corner_radius=12,
            command=self._on_close
        )
        close_button.pack(side="right", padx=(3, 0))
        
    def _load_license_data(self):
        """Load and display license data."""
        try:
            # Get license status and data
            status, is_valid = self.license_manager.get_license_status()
            
            # Get license data if available
            license_data = None
            if self.license_manager.license_file.exists():
                try:
                    encrypted_data = self.license_manager.license_file.read_bytes()
                    license_data = self.license_manager._decrypt_license_data(encrypted_data)
                except Exception as e:
                    print(f"Failed to decrypt license data: {e}")
            
            # Update status
            status_text = self.license_manager.get_status_display_text(status, license_data)
            status_color = self.license_manager.get_status_color(status)
            self.status_label.configure(text=status_text, text_color=status_color)
            
            if license_data:
                # Update license code
                code = license_data.get("code", "Unknown")
                self.code_label.configure(text=code)
                
                # Update expiration
                expires_at = license_data.get("expiresAt")
                if expires_at:
                    try:
                        if isinstance(expires_at, str):
                            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                        if expires_at.tzinfo is None:
                            expires_at = expires_at.replace(tzinfo=timezone.utc)
                        
                        # Format the date nicely
                        expires_text = expires_at.strftime("%B %d, %Y at %I:%M %p")
                        
                        # Check if expired
                        if datetime.now(timezone.utc) > expires_at:
                            expires_text += " (Expired)"
                            self.expires_label.configure(text_color=AppConfig.COLORS["error"])
                        else:
                            days_left = (expires_at - datetime.now(timezone.utc)).days
                            if days_left > 0:
                                expires_text += f" ({days_left} days left)"
                            else:
                                expires_text += " (Expires today)"
                            self.expires_label.configure(text_color=AppConfig.COLORS["success"])
                            
                        self.expires_label.configure(text=expires_text)
                    except Exception as e:
                        self.expires_label.configure(text=f"Error parsing date: {expires_at}")
                else:
                    self.expires_label.configure(text="No expiration date")
                
                # Update issued date
                issued_at = license_data.get("issuedAt")
                if issued_at:
                    try:
                        if isinstance(issued_at, str):
                            issued_at = datetime.fromisoformat(issued_at.replace('Z', '+00:00'))
                        if issued_at.tzinfo is None:
                            issued_at = issued_at.replace(tzinfo=timezone.utc)
                        
                        issued_text = issued_at.strftime("%B %d, %Y at %I:%M %p")
                        self.issued_label.configure(text=issued_text)
                    except Exception as e:
                        self.issued_label.configure(text=f"Error parsing date: {issued_at}")
                else:
                    self.issued_label.configure(text="Unknown")
                
                # Update features
                features = license_data.get("features", [])
                if features:
                    features_text = ", ".join(features).title()
                    self.features_label.configure(text=features_text)
                else:
                    self.features_label.configure(text="No features specified")
                
                # Update user information
                user_name = license_data.get("user", "Unknown User")
                self.user_name_label.configure(text=user_name)
                
                email = license_data.get("email", "No Email")
                self.email_label.configure(text=email)
                
                company = license_data.get("company", "No Company")
                self.company_label.configure(text=company)
                    
            else:
                # No license data available
                self.code_label.configure(text="No license found")
                self.expires_label.configure(text="N/A")
                self.issued_label.configure(text="N/A")
                self.features_label.configure(text="N/A")
                self.user_name_label.configure(text="N/A")
                self.email_label.configure(text="N/A")
                self.company_label.configure(text="N/A")
                
        except Exception as e:
            print(f"Error loading license data: {e}")
            self.status_label.configure(text="Error loading license", text_color=AppConfig.COLORS["error"])
            self.code_label.configure(text="Error")
            self.expires_label.configure(text="Error")
            self.issued_label.configure(text="Error")
            self.features_label.configure(text="Error")
            self.user_name_label.configure(text="Error")
            self.email_label.configure(text="Error")
            self.company_label.configure(text="Error")
    
    def _on_close(self):
        """Handle window close."""
        if self.window:
            self.window.destroy()
            self.window = None


def show_license_details(parent):
    """Show license details window."""
    window = LicenseDetailsWindow(parent)
    window.show()
    return window
