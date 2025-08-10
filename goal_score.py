# goal_score.py
# Standard library imports
from datetime import datetime
import os                     # File system operations
import re                     # Regular expressions
import sys                    # System-specific parameters and functions
import time                   # Time utilities
from multiprocessing import Manager, Process, Queue, freeze_support  # Process management and multiprocessing support
from typing import Optional   # Type hint for optional values

# Third-party library imports
import customtkinter as ctk              # Modern tkinter-based UI toolkit
import tkinter.messagebox as messagebox  # Standard tkinter message boxes

from assets.colors import COLOR_ERROR
from database.gameinfo import GameInfoStore
from helpers.date_time_provider import DateTimeProvider
from helpers.icons_provider import get_icon_path
from helpers.make_drag_drop import make_it_drag_and_drop
from helpers.notification.toast import (init_notification_queue)  # Notification queue initializer and toast display
from helpers.config_manager import get_config

from mainUI.score_ui import ScoreUI          # Main scoring interface class

from mainUI.teamsUI.teams_ui import TeamInputManager # Team name management UI

from database.mongodb import MongoTeamManager        # MongoDB-backed team manager
from helpers.notification.notification_server import server_main # Background notification server entry point
import customtkinter as ctk

from widgets.top_widget import TopWidget

FOLDER_NAME = "FUTEBOL-SCORE-DASHBOARD"
ICON_BALL = "\u26BD"
ICON_MINUS = "\u268A"
ICON_WARN = "\u267B"

class ScoreApp:
    def __init__(self, root, instance_number: int):
        self.root = root
        self.root.iconbitmap(get_icon_path("field"))
        self.root.title(f"{instance_number} Campo")
        
        # Configure window properties for smooth loading
        self.root.geometry("420x460")
        self.root.attributes("-topmost", True)
        self.root.minsize(190, 195)
        
        # Add smooth loading attributes
        self.root.attributes("-alpha", 0.0)  # Start transparent
        self.root.update_idletasks()
        
        # Show loading indicator
        self._show_loading_indicator()
        
        self.instance_number = instance_number
        self.json = GameInfoStore(instance_number, debug=get_config("debug_mode"))
        self.decrement_buttons_enabled = True
        self.mongo = MongoTeamManager()
        self.mongo.backup_to_json()  # Backup teams to JSON on startup

        # Defer UI setup for smooth loading
        self.root.after(50, self._deferred_setup_ui)

    def _show_loading_indicator(self):
        """Show a loading indicator while UI is being built"""
        self.loading_frame = ctk.CTkFrame(
            self.root, 
            fg_color=("gray95", "gray15"),
            corner_radius=16,
            border_width=2,
            border_color=("gray80", "gray30")
        )
        self.loading_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Loading icon and text
        loading_icon = ctk.CTkLabel(
            self.loading_frame,
            text="⚽",
            font=("Segoe UI Emoji", 32),
            text_color=("gray40", "gray60")
        )
        loading_icon.pack(pady=(20, 10))
        
        loading_label = ctk.CTkLabel(
            self.loading_frame,
            text="Loading Stream Futebol Dashboard...",
            font=("Segoe UI", 14, "bold"),
            text_color=("gray20", "gray90")
        )
        loading_label.pack(pady=(0, 15))
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            self.loading_frame,
            text="Initializing components...",
            font=("Segoe UI", 11),
            text_color=("gray50", "gray60")
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Simple progress bar
        self.progress_bar = ctk.CTkProgressBar(self.loading_frame)
        self.progress_bar.pack(pady=(0, 20), padx=20)
        self.progress_bar.set(0.3)  # Show initial progress
        
        # Animate the loading icon
        self._animate_loading_icon(loading_icon)

    def _animate_loading_icon(self, icon_label):
        """Subtle animation for the loading icon"""
        def animate():
            if hasattr(self, 'loading_frame') and self.loading_frame.winfo_exists():
                # Simple rotation effect by changing the emoji
                current_text = icon_label.cget("text")
                if current_text == "⚽":
                    icon_label.configure(text="🏈")
                elif current_text == "🏈":
                    icon_label.configure(text="🏀")
                elif current_text == "🏀":
                    icon_label.configure(text="⚽")
                
                # Continue animation
                self.root.after(800, animate)
        
        animate()

    def _animate_progress(self):
        """Animate the progress bar - simplified version"""
        # No animation needed - just show static progress
        pass

    def _hide_loading_indicator(self):
        """Hide the loading indicator"""
        if hasattr(self, 'loading_frame'):
            self.loading_frame.destroy()
            delattr(self, 'loading_frame')

    def _deferred_setup_ui(self):
        """Deferred UI setup to ensure smooth loading"""
        try:
            # Update loading message
            self._update_loading_message("Building UI components...")
            
            # Complete progress bar
            if hasattr(self, 'progress_bar'):
                self.progress_bar.set(0.6)
            
            # Build UI components
            self._update_loading_message("Initializing top widget...")
            TopWidget(self.root, self.instance_number, self.mongo, self.json)
            
            self._update_loading_message("Setting up score interface...")
            # 2) ScoreUI 
            self.score_ui = ScoreUI(
                self.root,                # no keyword
                self.instance_number,
                self.mongo,
                self.json
            )
            
            self._update_loading_message("Configuring team management...")
            # 3) TeamInputManager
            TeamInputManager(
                parent=self.root,
                mongo=self.mongo,
                refresh_labels_cb=lambda: self.score_ui._update_labels(),
                instance=self.instance_number,
                json=self.json
            )
            
            self._update_loading_message("Finalizing setup...")
            add_footer_label(self.root)
            
            # Complete progress
            if hasattr(self, 'progress_bar'):
                self.progress_bar.set(1.0)
            
            # Hide loading indicator and start fade-in
            self.root.after(200, self._complete_loading)
            
        except Exception as e:
            print(f"Error during UI setup: {e}")
            # Fallback: show UI immediately if there's an error
            self._hide_loading_indicator()
            self.root.attributes("-alpha", 1.0)

    def _update_loading_message(self, message: str):
        """Update the loading message to show current progress"""
        if hasattr(self, 'loading_frame') and self.loading_frame.winfo_exists():
            # Find and update the subtitle label
            for child in self.loading_frame.winfo_children():
                if isinstance(child, ctk.CTkLabel) and "Initializing components" in child.cget("text"):
                    child.configure(text=message)
                    break

    def _complete_loading(self):
        """Complete the loading process and start fade-in"""
        # Hide loading indicator
        self._hide_loading_indicator()
        
        # Smooth fade-in effect
        self._fade_in_ui()

    def _fade_in_ui(self):
        """Smooth fade-in effect for the UI"""
        def fade_step(alpha=0.0):
            if alpha < 1.0:
                alpha = min(1.0, alpha + 0.08)  # Smoother increment
                self.root.attributes("-alpha", alpha)
                self.root.after(16, lambda: fade_step(alpha))  # 60 FPS animation
        
        fade_step()

def start_instance(instance_number: int):
    """
    Starts a new instance of the ScoreApp GUI application.

    Args:
        instance_number (int): The identifier for the application instance.

    This function creates a new custom Tkinter (CTk) root window, initializes the ScoreApp
    with the given instance number, and starts the main event loop.
    """
    root = ctk.CTk()
    app = ScoreApp(root, instance_number)
    root.mainloop()

def ask_instance_count_ui() -> int:
    result: dict[str, int] = {"value": 0}

    def confirm():
        result["value"] = int(slider.get())
        window.destroy()

    window = ctk.CTk()
    window.iconbitmap(get_icon_path("dice"))
    window.title("Campos")
    window.geometry("320x200")
    window.resizable(False, False)

    ctk.CTkLabel(window, text="Quantos campos queres abrir?", font=("Segoe UI Emoji", 15)).pack(pady=(20, 10))

    slider = ctk.CTkSlider(window, from_=1, to=20, number_of_steps=19, width=220)
    slider.set(1)
    slider.pack()

    value_label = ctk.CTkLabel(window, text="1", font=("Segoe UI Emoji", 13))
    value_label.pack(pady=(5, 10))

    def update_label(value):
        value_label.configure(text=str(int(value)))

    slider.configure(command=update_label)

    ctk.CTkButton(window, text="Abrir", command=confirm).pack(pady=10)

    add_footer_label(window)
    window.mainloop()
    return result["value"]


def add_footer_label(parent, text: str = "© 2025 Vunf1"):
    footer = ctk.CTkLabel(parent, text="", font=("Segoe UI Emoji", 11), text_color="gray")
    footer.pack(side="bottom", pady=(5,5))

    def refresh():
        footer.configure(text=f"{text} — {DateTimeProvider.get_datetime()}")
        parent.after(1000, refresh)

    refresh()
    return footer


def child_entry(instance_number, notification_queue):
    """
    Initialize notification queue in this child process, then start the ScoreApp instance.
    """
    init_notification_queue(notification_queue)
    start_instance(instance_number)



def main():
    ctk.set_appearance_mode("system")

    count = ask_instance_count_ui()
    if not count:
        sys.exit()

    # Use a simple Queue (lighter/faster than Manager().Queue())
    q = Queue()
    init_notification_queue(q)

    # Start the notification server (daemon ok)
    p_notify = Process(target=server_main, args=(q,), daemon=True)
    p_notify.start()

    # Optimized batch process creation
    procs = []
    batch_size = 3
    for i in range(1, count + 1):
        p = Process(target=child_entry, args=(i, q))
        p.start()
        procs.append(p)
        
        # Batch delay for better resource management
        if i % batch_size == 0 and i < count:
            time.sleep(0.05)  # Reduced delay for faster startup

    for p in procs:
        p.join()
        
if __name__ == '__main__':
    freeze_support()
    main()