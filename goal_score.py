# goal_score.py
# Standard library imports
import sys                    # System-specific parameters and functions
import time                   # Time utilities
from multiprocessing import Process, Queue, freeze_support  # Process management and multiprocessing support

# Third-party library imports
import customtkinter as ctk              # Modern tkinter-based UI toolkit

from database.gameinfo import GameInfoStore
from helpers.date_time_provider import DateTimeProvider
from helpers.icons_provider import get_icon_path
from helpers.notification.toast import init_notification_queue  # Notification queue initializer and toast display
from helpers.config_manager import get_config

from mainUI.score_ui import ScoreUI          # Main scoring interface class
from mainUI.teamsUI.teams_ui import TeamInputManager # Team name management UI
from database.mongodb import MongoTeamManager        # MongoDB-backed team manager
from helpers.notification.notification_server import server_main # Background notification server entry point
from widgets.top_widget import TopWidget

# Global variable to track instance positions for cascade effect
_instance_positions = {}

class ScoreApp:
    def __init__(self, root, instance_number: int):
        self.root = root
        self.root.iconbitmap(get_icon_path("field"))
        self.root.title(f"{instance_number} Campo")
        
        # Configure window properties for fast loading
        self.root.geometry("420x520")  # Increased height to better accommodate all elements
        self.root.attributes("-topmost", True)
        self.root.minsize(190, 255)  # Adjusted minimum size
        
        # Remove window border but keep taskbar icon
        self.root.overrideredirect(True)
        self.root.attributes("-toolwindow", False)  # Keep taskbar icon visible
        
        # Position the window using cascade logic
        self._position_window(instance_number)
        
        # Fast loading - minimal transparency effect
        self.root.attributes("-alpha", 0.95)  # Start almost visible
        
        # Show minimal loading indicator for fast loading
        self._show_fast_loading_indicator()
        
        self.instance_number = instance_number
        self.json = GameInfoStore(instance_number, debug=get_config("debug_mode"))
        self.decrement_buttons_enabled = True
        self.mongo = MongoTeamManager()
        
        # Defer backup operation to avoid blocking UI
        self.root.after(100, self._deferred_backup)
        
        # Faster UI setup with minimal delay
        self.root.after(10, self._fast_setup_ui)

    def _position_window(self, instance_number: int):
        """Position the window in center for first instance, cascade for subsequent ones"""
        global _instance_positions
        
        # Cache screen dimensions for faster access
        if not hasattr(self, '_screen_dimensions'):
            self._screen_dimensions = (self.root.winfo_screenwidth(), self.root.winfo_screenheight())
        
        screen_width, screen_height = self._screen_dimensions
        
        # Window dimensions (constants for faster access)
        window_width = 420
        window_height = 520
        
        if instance_number == 1:
            # First instance: center on screen
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
        else:
            # Fast cascade positioning
            if instance_number - 1 in _instance_positions:
                prev_x, prev_y = _instance_positions[instance_number - 1]
                x = prev_x + 40
                y = prev_y + 40
                
                # Quick boundary check
                if x + window_width > screen_width - 50:
                    x = 50
                if y + window_height > screen_height - 50:
                    y = 50
            else:
                # Fast grid positioning
                base_x = (screen_width - window_width) // 2
                base_y = (screen_height - window_height) // 2
                
                grid_col = (instance_number - 1) % 3
                grid_row = (instance_number - 1) // 3
                
                x = base_x + (grid_col * (window_width + 20))
                y = base_y + (grid_row * (window_height + 20))
                
                # Quick boundary check
                if x + window_width > screen_width - 50:
                    x = 50
                if y + window_height > screen_height - 50:
                    y = 50
        
        # Store position and apply immediately
        _instance_positions[instance_number] = (x, y)
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Quick overlap check only for instances > 1
        if instance_number > 1:
            self._quick_overlap_check(instance_number, x, y, window_width, window_height)

    def _quick_overlap_check(self, instance_number: int, x: int, y: int, width: int, height: int):
        """Quick overlap check for faster positioning"""
        global _instance_positions
        
        # Only check the most recent instance for overlap
        if instance_number - 1 in _instance_positions:
            other_x, other_y = _instance_positions[instance_number - 1]
            
            # Quick overlap detection
            if (x < other_x + width and x + width > other_x and 
                y < other_y + height and y + height > other_y):
                
                # Simple adjustment
                new_x = other_x + width + 20
                new_y = other_y + height + 20
                
                # Update position
                _instance_positions[instance_number] = (new_x, new_y)
                self.root.geometry(f"{width}x{height}+{new_x}+{new_y}")

    def _adjust_for_overlap(self, instance_number: int, x: int, y: int, width: int, height: int):
        """Adjust window position if it overlaps with existing windows"""
        # This method is kept for compatibility but simplified
        pass

    def _on_closing(self):
        """Handle window closing event"""
        global _instance_positions
        
        # Remove this instance from position tracking
        if hasattr(self, 'instance_number') and self.instance_number in _instance_positions:
            del _instance_positions[self.instance_number]
            self._hide_loading_indicator()
        
        # Destroy the window
        self.root.destroy()

    def _show_fast_loading_indicator(self):
        """Show a minimal loading indicator while UI is being built"""
        self.loading_frame = ctk.CTkFrame(
            self.root, 
            fg_color=("gray95", "gray15"),
            corner_radius=8,
            border_width=1,
            border_color=("gray80", "gray30")
        )
        self.loading_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Simple loading icon and text
        loading_icon = ctk.CTkLabel(
            self.loading_frame,
            text="⚽",
            font=("Segoe UI Emoji", 24),
            text_color=("gray40", "gray60")
        )
        loading_icon.pack(pady=(15, 8))
        
        loading_label = ctk.CTkLabel(
            self.loading_frame,
            text="Loading...",
            font=("Segoe UI", 12, "bold"),
            text_color=("gray20", "gray90")
        )
        loading_label.pack(pady=(0, 15))
        
        # Store reference for updates
        self.loading_label = loading_label

    # Animation methods removed for faster startup

    def _hide_loading_indicator(self):
        """Hide the loading indicator"""
        if hasattr(self, 'loading_frame'):
            self.loading_frame.destroy()
            delattr(self, 'loading_frame')

    def _deferred_backup(self):
        """Defer the backup operation to avoid blocking UI"""
        self.mongo.backup_to_json()

    def _fast_setup_ui(self):
        """Faster UI setup to ensure smooth loading"""
        try:
            # Update loading message
            self._update_loading_message("Building UI...")
            
            # Build UI components in parallel where possible
            self._update_loading_message("Initializing components...")
            
            # Add title label at the top
            title_label = ctk.CTkLabel(
                self.root, 
                text=f"Campo {self.instance_number}", 
                font=("Segoe UI Emoji", 16, "bold"),
                text_color="white"
            )
            title_label.pack(pady=(10, 5))
            
            # Initialize components
            TopWidget(self.root, self.instance_number, self.mongo, self.json)
            
            self.score_ui = ScoreUI(
                self.root,
                self.instance_number,
                self.mongo,
                self.json
            )
            
            TeamInputManager(
                parent=self.root,
                mongo=self.mongo,
                refresh_labels_cb=lambda: self.score_ui._update_labels(),
                instance=self.instance_number,
                json=self.json
            )
            
            add_footer_label(self.root)
            
            # Make the body draggable
            self._make_body_draggable()
            
            # Hide loading indicator immediately
            self.root.after(50, self._complete_fast_loading)
            
        except Exception as e:
            print(f"Error during UI setup: {e}")
            # Fallback: show UI immediately if there's an error
            self._hide_loading_indicator()
            self.root.attributes("-alpha", 1.0)

    def _complete_fast_loading(self):
        """Complete the fast loading process"""
        # Hide loading indicator
        self._hide_loading_indicator()
        
        # Make window fully visible immediately
        self.root.attributes("-alpha", 1.0)

    def _update_loading_message(self, message: str):
        """Update the loading message to show current progress"""
        if hasattr(self, 'loading_label') and self.loading_label.winfo_exists():
            self.loading_label.configure(text=message)

    def _make_body_draggable(self):
        """Make the window body draggable"""
        def on_mouse_down(event):
            self.root.x = event.x
            self.root.y = event.y

        def on_mouse_move(event):
            deltax = event.x - self.root.x
            deltay = event.y - self.root.y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")

        # Bind mouse events to the root window for dragging
        self.root.bind("<Button-1>", on_mouse_down)
        self.root.bind("<B1-Motion>", on_mouse_move)

    # Old loading methods removed for faster startup

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
    try:
        window.iconbitmap(get_icon_path("dice"))
    except:
        pass  # Silently ignore icon loading errors
    window.title("Campos")
    window.geometry("320x200")
    window.resizable(False, False)
    
    # Remove window border but ensure visibility
    window.overrideredirect(True)
    window.attributes("-toolwindow", False)  # Keep taskbar icon visible
    window.attributes("-topmost", True)  # Ensure window appears on top
    
    # Set a visible background color for the borderless window
    window.configure(fg_color="#2b2b2b")
    
    # Center the dialog window on screen
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - 320) // 2
    y = (screen_height - 200) // 2
    window.geometry(f"320x200+{x}+{y}")
    
    # Ensure window gets focus and is visible
    window.lift()
    window.focus_force()

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
    # Create footer frame to hold both label and close button
    footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
    footer_frame.pack(side="bottom", pady=(5,5), fill="x", padx=10)
    
    # Footer label
    footer = ctk.CTkLabel(footer_frame, text="", font=("Segoe UI Emoji", 11), text_color="gray")
    footer.pack(side="left")
    
    # Close button (X) - Modern transparent design
    close_button = ctk.CTkButton(
        footer_frame, 
        text="✕", 
        width=28, 
        height=28,
        font=("Segoe UI Emoji", 14, "bold"),
        fg_color="transparent",
        hover_color="#2b2b2b",
        text_color="#888888",
        corner_radius=14,
        command=lambda: parent.destroy()
    )
    close_button.pack(side="right", padx=(5, 0))

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

    # Fast batch process creation
    procs = []
    batch_size = 5  # Increased batch size for faster startup
    
    for i in range(1, count + 1):
        p = Process(target=child_entry, args=(i, q))
        p.start()
        procs.append(p)
        
        # Minimal delay only between batches
        if i % batch_size == 0 and i < count:
            time.sleep(0.02)  # Minimal delay for faster startup

    # Wait for all processes to complete
    for p in procs:
        p.join()
        
if __name__ == '__main__':
    freeze_support()
    main()