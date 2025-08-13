"""
Footer label utility for creating consistent footer labels across UI components.
Provides a reusable footer with copyright text, datetime, license status, and close button.
"""

import customtkinter as ctk
from src.utils import DateTimeProvider
from src.licensing import LicenseManager
from src.licensing import LicenseActivationDialog
from src.licensing import show_license_details
from typing import Optional


def add_footer_label(parent, text: str = "© 2025 Vunf1"):
    """
    Add a footer label to the given parent widget.
    
    Args:
        parent: The parent widget to add the footer to
        text: The copyright text to display (default: "© 2025 Vunf1")
    
    Returns:
        The footer label widget for further customization if needed
    """
    # Create footer frame to hold label, license status, and close button
    footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
    footer_frame.pack(side="bottom", pady=(2,2), fill="x", padx=6)
    
    # Footer label (left side)
    footer = ctk.CTkLabel(footer_frame, text="", font=("Segoe UI Emoji", 10), text_color="gray")
    footer.pack(side="left")
    
    # License status label (center) - clickable
    license_status_label = ctk.CTkLabel(
        footer_frame, 
        text="", 
        font=("Segoe UI", 10, "bold"),
        text_color="gray",
        cursor="arrow"  # Default cursor, will be updated based on license status
    )
    license_status_label.pack(side="left", expand=True, fill="x", padx=(20, 0))
    
    # Add hover effect to make it clear it's clickable
    def on_enter(e):
        # Check if there's a license before allowing hover effects
        current_text = license_status_label.cget("text")
        if current_text == "NO LICENSE" or current_text == "LICENSE ERROR" or current_text == "BLOCKED":
            return  # Don't show hover effects for no license or error states
        
        # Only change to white if not in pressed state
        current_color = license_status_label.cget("text_color")
        if current_color != "#4CAF50":  # Not in pressed state
            license_status_label.configure(text_color="#ffffff")
    
    def on_leave(e):
        # Check if there's a license before allowing hover effects
        current_text = license_status_label.cget("text")
        if current_text == "NO LICENSE" or current_text == "LICENSE ERROR" or current_text == "BLOCKED":
            return  # Don't show hover effects for no license or error states
        
        # Only change back to gray if not in pressed state
        current_color = license_status_label.cget("text_color")
        if current_color != "#4CAF50":  # Not in pressed state
            license_status_label.configure(text_color="gray")
    
    license_status_label.bind("<Enter>", on_enter)
    license_status_label.bind("<Leave>", on_leave)
    
    # Make license status label clickable
    def show_license_details_window():
        """Show license details window when status label is clicked."""
        # Check if there's a license before allowing click
        current_text = license_status_label.cget("text")
        if current_text == "NO LICENSE" or current_text == "LICENSE ERROR" or current_text == "BLOCKED":
            return  # Don't allow click for no license or error states
        
        # Change color to indicate it's been pressed
        license_status_label.configure(text_color="#4CAF50")  # Green color for pressed state
        show_license_details(parent)
    
    license_status_label.bind("<Button-1>", lambda e: show_license_details_window())
    
    # Close button (X) - Modern transparent design
    # Find the root window to close the entire instance
    def close_instance():
        # Navigate up to find the root window
        current = parent
        while hasattr(current, 'winfo_toplevel'):
            current = current.winfo_toplevel()
            if hasattr(current, 'destroy'):
                current.destroy()
                break
    
    close_button = ctk.CTkButton(
        footer_frame, 
        text="✕", 
        width=24, 
        height=24,
        font=("Segoe UI Emoji", 12, "bold"),
        fg_color="transparent",
        hover_color="#2b2b2b",
        text_color="#888888",
        corner_radius=12,
        command=close_instance
    )
    close_button.pack(side="right", padx=(3, 0))

    # Initialize license manager
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
            # If pressed and license is valid, keep the green color; otherwise use the status color
            if is_pressed and display_text not in ["NO LICENSE", "LICENSE ERROR", "BLOCKED"]:
                final_color = "#4CAF50"  # Keep pressed state only for valid licenses
            else:
                final_color = status_color  # Use status color for invalid/no license
                # Reset pressed state if license becomes invalid
                if display_text in ["NO LICENSE", "LICENSE ERROR", "BLOCKED"]:
                    is_pressed = False
            
            license_status_label.configure(text=display_text, text_color=final_color)
            
            # Update cursor based on license status
            if display_text == "NO LICENSE" or display_text == "LICENSE ERROR" or display_text == "BLOCKED":
                license_status_label.configure(cursor="arrow")  # Normal cursor for no license
            else:
                license_status_label.configure(cursor="hand2")  # Hand cursor for valid license
            
            # Show/hide activate button based on license status
            if is_valid:
                # License is valid, hide the activate button
                activate_button.pack_forget()
            else:
                # License is invalid, show the activate button
                activate_button.pack(side="left", padx=(10, 0))
            
        except Exception as e:
            print(f"Error updating license status: {e}")
            # Check if label is in pressed state
            current_color = license_status_label.cget("text_color")
            is_pressed = current_color == "#4CAF50"
            
            # For errors, always show error color (no pressed state preservation)
            final_color = "#dc3545"
            license_status_label.configure(text="LICENSE ERROR", text_color=final_color)
            # Update cursor for error state
            license_status_label.configure(cursor="arrow")
            # Show activate button on error
            activate_button.pack(side="left", padx=(10, 0))
    
    def show_license_activation():
        """Show the license activation modal."""
        try:
            print("Opening license activation modal...")
            
            def on_license_activated(license_data):
                """Callback when license is successfully activated."""
                print(f"License activation callback received: {license_data}")
                # Save the license
                if license_manager.save_license(license_data):
                    # Update status immediately
                    update_license_status()
                    print("License activated successfully!")
                else:
                    print("Failed to save license")
            
            # Show the activation dialog
            print("Calling LicenseActivationDialog.show...")
            result = LicenseActivationDialog.show(parent, on_license_activated)
            print(f"Modal result: {result}")
            
        except Exception as e:
            print(f"Error showing license activation: {e}")
            import traceback
            traceback.print_exc()
    
    # Manual activation button (for testing) - add after function definition
    activate_button = ctk.CTkButton(
        footer_frame,
        text="🔑 Activate",
        command=show_license_activation,
        font=("Segoe UI", 9),
        height=20,
        fg_color="transparent",
        hover_color="#2b2b2b",
        text_color="#888888"
    )
    
    def refresh():
        """Refresh footer content."""
        footer.configure(text=f"{text} — {DateTimeProvider.get_datetime()}")
        parent.after(1000, refresh)
    
    # Initial license status check and button management
    update_license_status()
    
    # Start refresh loop
    refresh()
    
    return footer
