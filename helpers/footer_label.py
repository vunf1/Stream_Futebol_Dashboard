"""
Footer label utility for creating consistent footer labels across UI components.
Provides a reusable footer with copyright text, datetime, and close button.
"""

import customtkinter as ctk
from helpers.date_time_provider import DateTimeProvider


def add_footer_label(parent, text: str = "© 2025 Vunf1"):
    """
    Add a footer label to the given parent widget.
    
    Args:
        parent: The parent widget to add the footer to
        text: The copyright text to display (default: "© 2025 Vunf1")
    
    Returns:
        The footer label widget for further customization if needed
    """
    # Create footer frame to hold both label and close button
    footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
    footer_frame.pack(side="bottom", pady=(2,2), fill="x", padx=6)
    
    # Footer label
    footer = ctk.CTkLabel(footer_frame, text="", font=("Segoe UI Emoji", 10), text_color="gray")
    footer.pack(side="left")
    
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

    def refresh():
        footer.configure(text=f"{text} — {DateTimeProvider.get_datetime()}")
        parent.after(1000, refresh)

    refresh()
    return footer
