"""
Footer label utility for creating consistent footer labels across UI components.
Provides a reusable footer with copyright text, datetime, license status, and close button.
"""

import customtkinter as ctk
from src.utils import DateTimeProvider
from src.licensing import LicenseManager
from src.licensing import LicenseActivationDialog
from src.licensing import show_license_details
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass


@dataclass
class FooterConfig:
    """Configuration for footer customization."""
    show_copyright: bool = True
    show_datetime: bool = True
    show_license_status: bool = True
    show_activate_button: bool = True
    show_close_button: bool = True  # Note: Close button is always visible regardless of this setting
    copyright_text: str = "© 2025 Vunf1"
    datetime_format: str = "default"  # "default", "short", "custom"
    custom_datetime: str = ""
    license_clickable: bool = True
    close_command: Optional[Callable] = None
    custom_padding: tuple = (6, 2, 6, 2)  # (left, top, right, bottom)
    custom_spacing: int = 20
    footer_height: int = 25  # Reduced default height for better proportions
    close_button_size: int = 24
    activate_button_height: int = 20


def add_footer_label(parent, config: Optional[FooterConfig] = None, **kwargs):
    """
    Add a customizable footer label to the given parent widget.
    
    Args:
        parent: The parent widget to add the footer to
        config: FooterConfig object for customization
        **kwargs: Override config values directly
    
    Returns:
        The footer frame widget for further customization if needed
    
    Note:
        The close button (X) is always visible regardless of configuration
        for user convenience and consistent UI behavior.
    """
    # Create default config and override with kwargs
    if config is None:
        config = FooterConfig()
    
    # Override config with kwargs
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    # Create footer frame to hold all elements - ensure it fills full width
    footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
    
    # Pack with proper fill and expansion to ensure full width coverage
    footer_frame.pack(side="bottom", pady=config.custom_padding[1:3], fill="x", expand=False, padx=0)
    
    # Set minimum height but allow expansion
    footer_frame.configure(height=config.footer_height)
    footer_frame.pack_propagate(True)  # Allow height to adjust to content
    
    # Force footer to update its layout and ensure proper width
    def force_footer_layout():
        """Force footer to update its layout and ensure proper width."""
        if parent.winfo_exists() and footer_frame.winfo_exists():
            try:
                # Force layout update
                footer_frame.update_idletasks()
                parent.update_idletasks()
                
                # Ensure footer takes full available width
                footer_frame.pack_configure(fill="x", expand=False)
                
            except Exception as e:
                pass  # Silently ignore layout errors
    
    # Bind to parent resize events
    parent.bind("<Configure>", lambda e: force_footer_layout())
    
    # Initial layout setup after a short delay to ensure parent has dimensions
    parent.after(50, force_footer_layout)
    
    # Create a centered row layout for all footer components
    # Main row container that centers all elements
    row_container = ctk.CTkFrame(footer_frame, fg_color="transparent")
    row_container.pack(expand=True, fill="both", pady=2)
    
    # Left side container for copyright and datetime
    left_container = ctk.CTkFrame(row_container, fg_color="transparent")
    left_container.pack(side="left", fill="y", padx=(8, 0))
    
    # Copyright label
    if config.show_copyright:
        copyright_label = ctk.CTkLabel(
            left_container, 
            text=config.copyright_text, 
            font=("Segoe UI Emoji", 10), 
            text_color="gray"
        )
        copyright_label.pack(side="left", padx=(0, 8))
    
    # Datetime label
    if config.show_datetime:
        datetime_label = ctk.CTkLabel(
            left_container, 
            text="", 
            font=("Segoe UI", 10), 
            text_color="gray"
        )
        datetime_label.pack(side="left", padx=(0, 8))
        
        def update_datetime():
            """Update datetime display based on config."""
            if config.datetime_format == "custom" and config.custom_datetime:
                datetime_label.configure(text=config.custom_datetime)
            elif config.datetime_format == "short":
                datetime_label.configure(text=DateTimeProvider.get_datetime().split()[0])  # Date only
            else:  # default
                datetime_label.configure(text=DateTimeProvider.get_datetime())
            
            if config.show_datetime:
                parent.after(1000, update_datetime)
        
        update_datetime()
    
    # Center container for license status and activate button
    center_container = ctk.CTkFrame(row_container, fg_color="transparent")
    center_container.pack(side="left", expand=True, fill="x", padx=(config.custom_spacing, 0))
    
    # License status label (center) - properly centered
    if config.show_license_status:
        license_status_label = ctk.CTkLabel(
            center_container, 
            text="", 
            font=("Segoe UI", 10, "bold"),
            text_color="gray",
            cursor="arrow"
        )
        license_status_label.pack(expand=True, fill="x")  # Remove side="left" for proper centering
        
        # License manager initialization
        license_manager = LicenseManager()
        
        def update_license_status():
            """Update the license status display."""
            try:
                status, is_valid = license_manager.get_license_status()
                
                # Get display text and color
                display_text = license_manager.get_status_display_text(status)
                status_color = license_manager.get_status_color(status)
                
                # Check if label is in pressed state (green color)
                current_color = license_status_label.cget("text_color")
                is_pressed = current_color == "#4CAF50"
                
                # Update the license status label
                if is_pressed and display_text not in ["NO LICENSE", "LICENSE ERROR", "BLOCKED"]:
                    final_color = "#4CAF50"  # Keep pressed state only for valid licenses
                else:
                    final_color = status_color  # Use status color for invalid/no license
                    if display_text in ["NO LICENSE", "LICENSE ERROR", "BLOCKED"]:
                        is_pressed = False
                
                license_status_label.configure(text=display_text, text_color=final_color)
                
                # Update cursor based on license status and config
                if config.license_clickable and display_text not in ["NO LICENSE", "LICENSE ERROR", "BLOCKED"]:
                    license_status_label.configure(cursor="hand2")
                else:
                    license_status_label.configure(cursor="arrow")
                
                # Show/hide activate button based on license status and config
                if config.show_activate_button:
                    if is_valid:
                        activate_button.pack_forget()
                    else:
                        activate_button.pack(side="left", padx=(8, 0))
                
            except Exception as e:
                print(f"Error updating license status: {e}")
                final_color = "#dc3545"
                license_status_label.configure(text="LICENSE ERROR", text_color=final_color)
                license_status_label.configure(cursor="arrow")
                
                if config.show_activate_button:
                    activate_button.pack(side="left", padx=(8, 0))
        
        # Hover effects for clickable license status
        if config.license_clickable:
            def on_enter(e):
                current_text = license_status_label.cget("text")
                if current_text in ["NO LICENSE", "LICENSE ERROR", "BLOCKED"]:
                    return
                
                current_color = license_status_label.cget("text_color")
                if current_color != "#4CAF50":
                    license_status_label.configure(text_color="#ffffff")
            
            def on_leave(e):
                current_text = license_status_label.cget("text")
                if current_text in ["NO LICENSE", "LICENSE ERROR", "BLOCKED"]:
                    return
                
                current_color = license_status_label.cget("text_color")
                if current_color != "#4CAF50":
                    license_status_label.configure(text_color="gray")
            
            license_status_label.bind("<Enter>", on_enter)
            license_status_label.bind("<Leave>", on_leave)
            
            # Make license status label clickable
            def show_license_details_window():
                current_text = license_status_label.cget("text")
                if current_text in ["NO LICENSE", "LICENSE ERROR", "BLOCKED"]:
                    return
                
                license_status_label.configure(text_color="#4CAF50")
                show_license_details(parent)
            
            license_status_label.bind("<Button-1>", lambda e: show_license_details_window())
        
        # Activate button
        if config.show_activate_button:
            def show_license_activation():
                try:
                    print("Opening license activation modal...")
                    
                    def on_license_activated(license_data):
                        if license_manager.save_license(license_data):
                            update_license_status()
                            print("License activated successfully!")
                        else:
                            print("Failed to save license")
                    
                    result = LicenseActivationDialog.show(parent, on_license_activated)
                    print(f"Modal result: {result}")
                    
                except Exception as e:
                    print(f"Error showing license activation: {e}")
                    import traceback
                    traceback.print_exc()
            
            activate_button = ctk.CTkButton(
                center_container,
                text="🔑 Activate",
                command=show_license_activation,
                font=("Segoe UI", 9),
                height=config.activate_button_height,
                fg_color="transparent",
                hover_color="#2b2b2b",
                text_color="#888888"
            )
            
            # Initial license status check
            update_license_status()
    
    # Right side container for close button
    right_container = ctk.CTkFrame(row_container, fg_color="transparent")
    right_container.pack(side="right", fill="y", padx=(0, 8))
    
    # Close button - ALWAYS visible for user convenience
    def close_action():
        """Handle close button action."""
        if config.close_command:
            config.close_command()
        else:
            # Default close behavior - find and close root window
            current = parent
            while hasattr(current, 'winfo_toplevel'):
                current = current.winfo_toplevel()
                if hasattr(current, 'destroy'):
                    current.destroy()
                    break
    
    close_button = ctk.CTkButton(
        right_container, 
        text="✕", 
        width=config.close_button_size, 
        height=config.close_button_size,
        font=("Segoe UI Emoji", 12, "bold"),
        fg_color="transparent",
        hover_color="#2b2b2b",
        text_color="#888888",
        corner_radius=config.close_button_size // 2,
        command=close_action
    )
    close_button.pack(side="right", padx=(3, 0))
    
    return footer_frame


# Convenience functions for common footer configurations
def add_simple_footer(parent, copyright_text: str = "© 2025 Vunf1", close_command: Optional[Callable] = None):
    """Add a simple footer with just copyright and close button. Close button is always visible."""
    config = FooterConfig(
        show_copyright=True,
        show_datetime=False,
        show_license_status=False,
        show_activate_button=False,
        show_close_button=True,  # Always True - close button is always visible
        copyright_text=copyright_text,
        close_command=close_command
    )
    return add_footer_label(parent, config)


def add_license_footer(parent, copyright_text: str = "© 2025 Vunf1", close_command: Optional[Callable] = None):
    """Add a footer with copyright, license status, and close button. Close button is always visible."""
    config = FooterConfig(
        show_copyright=True,
        show_datetime=False,
        show_license_status=True,
        show_activate_button=True,
        show_close_button=True,  # Always True - close button is always visible
        copyright_text=copyright_text,
        close_command=close_command
    )
    return add_footer_label(parent, config)


def add_full_footer(parent, copyright_text: str = "© 2025 Vunf1", close_command: Optional[Callable] = None):
    """Add a full footer with all features enabled. Close button is always visible."""
    config = FooterConfig(
        show_copyright=True,
        show_datetime=True,
        show_license_status=True,
        show_activate_button=True,
        show_close_button=True,  # Always True - close button is always visible
        copyright_text=copyright_text,
        close_command=close_command
    )
    return add_footer_label(parent, config)


# Legacy function for backward compatibility
def add_footer_label_legacy(parent, text: str = "© 2025 Vunf1"):
    """Legacy function for backward compatibility."""
    return add_footer_label(parent, FooterConfig(copyright_text=text))
