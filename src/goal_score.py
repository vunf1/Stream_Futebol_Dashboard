# goal_score.py
# Standard library imports
import sys                    # System-specific parameters and functions
import time                   # Time utilities
from multiprocessing import Process, Queue, freeze_support  # Process management and multiprocessing support

# Third-party library imports
import customtkinter as ctk              # Modern tkinter-based UI toolkit

from src.ui.make_drag_drop import make_it_drag_and_drop
from .core import GameInfoStore, MongoTeamManager
from .utils import DateTimeProvider
from .ui import get_icon_path, add_footer_label, ScoreUI, TeamInputManager, TopWidget
from .notification import init_notification_queue, server_main
from .core import get_config
from .licensing import LicenseBlocker
from .config import AppConfig

# Global variable to track instance positions for cascade effect
_instance_positions = {}

class ScoreApp:
    def __init__(self, root, instance_number: int):
        self.root = root
        self.root.iconbitmap(get_icon_path("field"))
        self.root.title(f"{instance_number} Campo")
        
        # Configure window properties for fast loading
        window_config = AppConfig.get_window_config()
        self.root.geometry(f"{window_config['width']}x{window_config['height']}")
        self.root.attributes("-topmost", True)
        self.root.minsize(window_config['min_width'], window_config['min_height'])
        
        # Remove window border but keep taskbar icon
        self.root.overrideredirect(True)
        self.root.attributes("-toolwindow", False)  # Keep taskbar icon visible
        
        # Set dark theme for consistent appearance
        ctk.set_appearance_mode("dark")
        
        # Position the window using cascade logic
        self._position_window(instance_number)
        
        # Fast loading - minimal transparency effect
        self.opacity = AppConfig.WINDOW_OPACITY
        self.root.attributes("-alpha", self.opacity)  # Start with configured opacity
        
        # Show minimal loading indicator for fast loading FIRST
        self._show_fast_loading_indicator()
        
        self.instance_number = instance_number
        
        # Initialize attributes that will be set later
        from typing import Optional
        from src.core.gameinfo import GameInfoStore
        from src.core.mongodb import MongoTeamManager
        
        self.json: Optional[GameInfoStore] = None
        self.mongo: Optional[MongoTeamManager] = None
        self.decrement_buttons_enabled = False
        
        # Check license BEFORE initializing any components
        self._check_license_first()

    def _position_window(self, instance_number: int):
        """Position the window in center for first instance, cascade for subsequent ones"""
        global _instance_positions
        
        # Cache screen dimensions for faster access
        if not hasattr(self, '_screen_dimensions'):
            self._screen_dimensions = (self.root.winfo_screenwidth(), self.root.winfo_screenheight())
        
        screen_width, screen_height = self._screen_dimensions
        
        # Window dimensions from configuration
        window_config = AppConfig.get_window_config()
        window_width = window_config['width']
        window_height = window_config['height']
        
        if instance_number == 1:
            # First instance: center on screen
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
        else:
            # Fast cascade positioning
            if instance_number - 1 in _instance_positions:
                prev_x, prev_y = _instance_positions[instance_number - 1]
                x = prev_x + AppConfig.FIELD_CASCADE_OFFSET
                y = prev_y + AppConfig.FIELD_CASCADE_OFFSET
                
                # Quick boundary check
                if x + window_width > screen_width - AppConfig.SCREEN_BOUNDARY_MARGIN:
                    x = AppConfig.SCREEN_BOUNDARY_MARGIN
                if y + window_height > screen_height - AppConfig.SCREEN_BOUNDARY_MARGIN:
                    y = AppConfig.SCREEN_BOUNDARY_MARGIN
            else:
                # Fast grid positioning
                base_x = (screen_width - window_width) // 2
                base_y = (screen_height - window_height) // 2
                
                grid_col = (instance_number - 1) % 3
                grid_row = (instance_number - 1) // 3
                
                x = base_x + (grid_col * (window_width + AppConfig.FIELD_GRID_SPACING))
                y = base_y + (grid_row * (window_height + AppConfig.FIELD_GRID_SPACING))
                
                # Quick boundary check
                if x + window_width > screen_width - AppConfig.SCREEN_BOUNDARY_MARGIN:
                    x = AppConfig.SCREEN_BOUNDARY_MARGIN
                if y + window_height > screen_height - AppConfig.SCREEN_BOUNDARY_MARGIN:
                    y = AppConfig.SCREEN_BOUNDARY_MARGIN
        
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
                new_x = other_x + width + AppConfig.WINDOW_OVERLAP_ADJUSTMENT
                new_y = other_y + height + AppConfig.WINDOW_OVERLAP_ADJUSTMENT
                
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
        
        # Stop license blocker notification listener if it exists
        if hasattr(self, 'license_blocker'):
            self.license_blocker.stop_notification_listener()
        
        # Stop spinner animation and hide loading indicator
        if hasattr(self, 'spinner_active'):
            self.spinner_active = False
        
        # Remove this instance from position tracking
        if hasattr(self, 'instance_number') and self.instance_number in _instance_positions:
            del _instance_positions[self.instance_number]
        
        # Hide loading indicator if it exists
        self._hide_loading_indicator()
        
        # Destroy the window
        self.root.destroy()

    def _show_fast_loading_indicator(self):
        """Show a clean, professional loading screen while UI is being built"""
        # Set root window background to match loading theme
        self.root.configure(fg_color=AppConfig.COLORS["loading_bg"])
        
        # Create a full-screen loading overlay
        self.loading_frame = ctk.CTkFrame(
            self.root, 
            fg_color=AppConfig.COLORS["loading_bg"],
            corner_radius=0
        )
        self.loading_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Main loading container
        loading_container = ctk.CTkFrame(
            self.loading_frame,
            fg_color="transparent"
        )
        loading_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # App title
        app_title = ctk.CTkLabel(
            loading_container,
            text=AppConfig.APP_TITLE,
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_TITLE, "bold"),
            text_color=AppConfig.COLORS["text"]
        )
        app_title.pack(pady=(0, 20))
        
        # Loading spinner (animated dots)
        self.spinner_label = ctk.CTkLabel(
            loading_container,
            text="● ● ○",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_SUBTITLE),
            text_color=AppConfig.COLORS["spinner"]
        )
        self.spinner_label.pack(pady=(0, 15))
        
        # Status message
        self.status_label = ctk.CTkLabel(
            loading_container,
            text="Initializing...",
            font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_BODY),
            text_color=AppConfig.COLORS["text_secondary"]
        )
        self.status_label.pack()
        
        # Start spinner animation
        self._animate_spinner()

    def _animate_spinner(self):
        """Animate the loading spinner dots"""
        self.spinner_active = True
        spinner_states = ["● ○ ○", "○ ● ○", "○ ○ ●", "● ● ●"]
        current_state = 0
        
        def update_spinner():
            nonlocal current_state
            # Check if animation should continue
            if not hasattr(self, 'spinner_active') or not self.spinner_active:
                return
                
            if hasattr(self, 'spinner_label') and hasattr(self, 'loading_frame'):
                try:
                    # Check if widgets still exist and are valid
                    if (self.spinner_label.winfo_exists() and 
                        self.loading_frame.winfo_exists()):
                        self.spinner_label.configure(text=spinner_states[current_state])
                        current_state = (current_state + 1) % len(spinner_states)
                        # Continue animation
                        animation_config = AppConfig.get_animation_config()
                        self.root.after(animation_config['spinner_interval'], update_spinner)
                except:
                    # Widget was destroyed, stop animation
                    self.spinner_active = False
            else:
                # Stop animation if widgets don't exist
                self.spinner_active = False
        
        update_spinner()

    def _hide_loading_indicator(self):
        """Hide the loading indicator"""
        # Stop spinner animation
        if hasattr(self, 'spinner_active'):
            self.spinner_active = False
        
        if hasattr(self, 'loading_frame'):
            self.loading_frame.destroy()
            delattr(self, 'loading_frame')

    def _deferred_backup(self):
        """Defer the backup operation to avoid blocking UI"""
        if self.mongo:
            self.mongo.backup_to_json()

    def _fast_setup_ui(self):
        """Faster UI setup to ensure smooth loading"""
        try:
            # License already checked and valid, proceed with setup
            self._update_loading_message("Initializing database...")
            animation_config = AppConfig.get_animation_config()
            self.root.after(animation_config['loading_step_delay'], lambda: self._setup_step_1())
            
        except Exception as e:
            print(f"Error during UI setup: {e}")
            # Fallback: show UI immediately if there's an error
            self._hide_loading_indicator()
            self.root.attributes("-alpha", self.opacity)
    
    def _continue_app_setup(self):
        """Continue with the app setup after license validation"""
        self._update_loading_message("Initializing database...")
        animation_config = AppConfig.get_animation_config()
        self.root.after(animation_config['loading_step_delay'], lambda: self._setup_step_1())
    
    def _setup_step_1(self):
        """Step 1: Initialize database and basic components"""
        try:
            # Create a hidden container for all UI components
            self.ui_container = ctk.CTkFrame(
                self.root,
                fg_color="transparent"
            )
            # Keep it hidden initially
            self.ui_container.pack(fill="both", expand=True)
            self.ui_container.pack_forget()  # Hide it
            
            # Set root background to match loading theme initially
            self.root.configure(fg_color=AppConfig.COLORS["loading_bg"])
            
            self._update_loading_message("Building UI components...")
            animation_config = AppConfig.get_animation_config()
            self.root.after(animation_config['loading_step_delay'], lambda: self._setup_step_2())
        except Exception as e:
            print(f"Error in step 1: {e}")
            self._hide_loading_indicator()
            self.root.attributes("-alpha", self.opacity)
    
    def _setup_step_2(self):
        """Step 2: Build UI components"""
        try:
            # Add title label at the top
            title_label = ctk.CTkLabel(
                self.ui_container, 
                text=f"Campo {self.instance_number}", 
                font=(AppConfig.FONT_FAMILY_EMOJI, AppConfig.FONT_SIZE_SUBTITLE, "bold"),
                text_color="white"
            )
            title_label.pack(pady=(10, 5))
            
            self._update_loading_message("Loading score interface...")
            animation_config = AppConfig.get_animation_config()
            self.root.after(animation_config['loading_step_delay'], lambda: self._setup_step_3())
            
        except Exception as e:
            print(f"Error in step 2: {e}")
            self._hide_loading_indicator()
            self.root.attributes("-alpha", self.opacity)
    
    def _setup_step_3(self):
        """Step 3: Initialize score UI and team manager"""
        try:
            # Ensure components are initialized
            if not self.mongo or not self.json or not self.ui_container:
                print("❌ Components not initialized yet")
                return
            
            # Initialize components
            TopWidget(self.ui_container, self.instance_number, self.mongo, self.json)
            
            self.score_ui = ScoreUI(
                self.ui_container,
                self.instance_number,
                self.mongo,
                self.json
            )
            
            self._update_loading_message("Setting up team management...")
            animation_config = AppConfig.get_animation_config()
            self.root.after(animation_config['loading_step_delay'], lambda: self._setup_step_4())
            
        except Exception as e:
            print(f"Error in step 3: {e}")
            self._hide_loading_indicator()
            self.root.attributes("-alpha", self.opacity)
    
    def _setup_step_4(self):
        """Step 4: Finalize UI setup"""
        try:
            # Ensure components are initialized
            if not self.mongo or not self.json or not self.ui_container:
                print("❌ Components not initialized yet")
                return
                
            TeamInputManager(
                parent=self.ui_container,
                mongo=self.mongo,
                refresh_labels_cb=lambda: self.score_ui._update_labels(),
                instance=self.instance_number,
                json=self.json
            )
            
            add_footer_label(self.ui_container)
            
            # Make the body draggable
            self._make_body_draggable()
            
            self._update_loading_message("Finalizing...")
            animation_config = AppConfig.get_animation_config()
            self.root.after(animation_config['completion_delay'], self._complete_fast_loading)
            
        except Exception as e:
            print(f"Error in step 4: {e}")
            self._hide_loading_indicator()
            self.root.attributes("-alpha", self.opacity)

    def _complete_fast_loading(self):
        """Complete the fast loading process and show the UI"""
        try:
            # Show the UI container
            if self.ui_container:
                self.ui_container.pack(fill="both", expand=True)
            
            # Hide loading indicator
            self._hide_loading_indicator()
            
            # Keep the configured opacity for transparency
            self.root.attributes("-alpha", self.opacity)
            
            # Start periodic license checking to ensure app stays secure
            if hasattr(self, 'license_blocker'):
                self.license_blocker.start_periodic_check(AppConfig.LICENSE_CHECK_INTERVAL)
                print("Periodic license checking started")
            else:
                print("No license blocker found, skipping periodic checks")
            
            print(f"Campo {self.instance_number} loaded successfully!")
            
        except Exception as e:
            print(f"Error completing loading: {e}")
            # Fallback: show UI immediately if there's an error
            self._hide_loading_indicator()
            self.root.attributes("-alpha", self.opacity)
    
    def _fade_in_ui(self):
        """Fade in the UI smoothly"""
        # Hide loading indicator
        self._hide_loading_indicator()
        
        # Set root background to default theme
        self.root.configure(fg_color=("gray95", "gray15"))
        
        # Show the UI container
        if hasattr(self, 'ui_container') and self.ui_container:
            self.ui_container.pack(fill="both", expand=True)
        
        # Smooth fade transition
        self._smooth_fade_transition()
    
    def _smooth_fade_transition(self):
        """Smooth fade transition from loading to UI"""
        # Start with loading background
        self.root.configure(fg_color=AppConfig.COLORS["loading_bg"])
        
        # Gradually transition to final background (dark theme only)
        def fade_step(step=0):
            animation_config = AppConfig.get_animation_config()
            if step <= animation_config['fade_steps']:
                # Interpolate between loading color and final dark color
                progress = step / animation_config['fade_steps']
                r1, g1, b1 = 26, 26, 26  # #1a1a1a
                r2, g2, b2 = 43, 43, 43  # #2b2b2b (standard dark theme)
                
                r = int(r1 + (r2 - r1) * progress)
                g = int(g1 + (g2 - g1) * progress)
                b = int(b1 + (b2 - b1) * progress)
                
                color = f"#{r:02x}{g:02x}{b:02x}"
                self.root.configure(fg_color=color)
                
                # Continue fade
                self.root.after(animation_config['fade_step_interval'], lambda: fade_step(step + 1))
            else:
                # Set final background to match CustomTkinter dark theme exactly
                self.root.configure(fg_color="gray15")  # Use CustomTkinter's built-in dark theme
                # Keep the configured opacity for transparency
                self.root.attributes("-alpha", self.opacity)
                # Ensure window is focused and visible
                self.root.lift()
                self.root.focus_force()
        
        fade_step()

    def _update_loading_message(self, message: str):
        """Update the loading message to show current progress"""
        if hasattr(self, 'status_label') and hasattr(self, 'loading_frame'):
            try:
                if (self.status_label.winfo_exists() and 
                    self.loading_frame.winfo_exists()):
                    self.status_label.configure(text=message)
            except:
                # Widget was destroyed, ignore update
                pass

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

    def _check_license_first(self):
        """Check license and initialize GameInfoStore and MongoTeamManager if valid"""
        try:
            # Update loading message to show license check
            self._update_loading_message("Checking license...")
            
            self.license_blocker = LicenseBlocker(
                self.root,
                on_license_valid=self._on_license_activated
            )
            
            # Check license status
            if self.license_blocker.check_and_block():
                # License is valid, continue with setup
                print("License validated, proceeding with app setup...")
                self._initialize_components_after_license()
            else:
                # License is invalid, hide loading indicator and show blocking UI
                print("License validation failed, app is blocked.")
                self._hide_loading_indicator()
                # The license blocker will handle showing the blocking overlay
                # and license activation modal - app stays open but blocked
                return
                
        except Exception as e:
            print(f"Error checking license during initialization: {e}")
            # If license check fails, proceed with development mode
            print("License check failed, proceeding with development mode...")
            self._initialize_components_after_license()

    def _initialize_components_after_license(self):
        """Initialize components in parallel for faster startup"""
        import threading
        
        # Update loading message to show license validation success
        self._update_loading_message("License validated, initializing components...")
        
        # Start database connection in background
        def init_database():
            self.mongo = MongoTeamManager()
            # Trigger immediate backup for first run
            self.mongo.backup_to_json()
        
        # Start UI setup in parallel
        def init_ui():
            self.json = GameInfoStore(self.instance_number, debug=get_config("debug_mode"))
            self.decrement_buttons_enabled = True
        
        # Run both in parallel
        db_thread = threading.Thread(target=init_database, daemon=True)
        ui_thread = threading.Thread(target=init_ui, daemon=True)
        
        db_thread.start()
        ui_thread.start()
        
        # Wait for both to complete
        db_thread.join()
        ui_thread.join()
        
        # Continue with UI setup
        animation_config = AppConfig.get_animation_config()
        # Use a small delay for UI setup to ensure smooth transition
        self.root.after(100, self._fast_setup_ui)
    
    def _on_license_activated(self):
        """Handle successful license activation and continue with app setup"""
        print("License activated successfully, continuing with app setup...")
        # Remove any blocking UI
        if hasattr(self, 'license_blocker'):
            self.license_blocker._remove_blocking()
        
        # Clean up existing UI components to prevent duplication
        self._cleanup_existing_ui()
        
        # Show loading indicator again since it was hidden during license check
        self._show_fast_loading_indicator()
        
        # Update loading message to show license activation success
        self._update_loading_message("License activated, continuing setup...")
        
        # Continue with app setup
        self._initialize_components_after_license()

    def _cleanup_existing_ui(self):
        """Clean up existing UI components to prevent duplication during license reactivation"""
        try:
            # Clean up UI container if it exists
            if hasattr(self, 'ui_container') and self.ui_container:
                if self.ui_container.winfo_exists():
                    self.ui_container.destroy()
                self.ui_container = None
            
            # Clean up score UI if it exists
            if hasattr(self, 'score_ui'):
                delattr(self, 'score_ui')
            
            # Clean up any other UI components that might have been created
            # This prevents duplicate components when license is reactivated
            
            print("Existing UI components cleaned up")
            
        except Exception as e:
            print(f"Error cleaning up existing UI: {e}")


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
    dialog_config = AppConfig.get_dialog_config()
    window.geometry(f"{dialog_config['width']}x{dialog_config['height']}")
    window.resizable(False, False)
    make_it_drag_and_drop(window)
    # Remove window border but ensure visibility
    window.overrideredirect(True)
    window.attributes("-toolwindow", False)  # Keep taskbar icon visible
    window.attributes("-topmost", True)  # Ensure window appears on top
    
    # Set a visible background color for the borderless window
    window.configure(fg_color=AppConfig.COLORS["surface"])
    
    # Center the dialog window on screen
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    dialog_config = AppConfig.get_dialog_config()
    x = (screen_width - dialog_config['width']) // 2
    y = (screen_height - dialog_config['height']) // 2
    window.geometry(f"{dialog_config['expanded_width']}x{dialog_config['expanded_height']}+{x}+{y}")
    
    # Ensure window gets focus and is visible
    window.lift()
    window.focus_force()

    ctk.CTkLabel(window, text="Quantos campos queres abrir?", font=(AppConfig.FONT_FAMILY_EMOJI, AppConfig.FONT_SIZE_DIALOG_TITLE)).pack(pady=(20, 10))

    slider = ctk.CTkSlider(window, from_=AppConfig.MIN_FIELDS, to=AppConfig.MAX_FIELDS, number_of_steps=AppConfig.MAX_FIELDS-1, width=AppConfig.DIALOG_SLIDER_WIDTH)
    slider.set(AppConfig.DEFAULT_FIELDS)
    slider.pack()

    value_label = ctk.CTkLabel(window, text=str(AppConfig.DEFAULT_FIELDS), font=(AppConfig.FONT_FAMILY_EMOJI, AppConfig.FONT_SIZE_DIALOG_BODY))
    value_label.pack(pady=(5, 10))

    def update_label(value):
        value_label.configure(text=str(int(value)))

    slider.configure(command=update_label)

    ctk.CTkButton(window, text="Abrir", command=confirm).pack(pady=10)

    add_footer_label(window)
    window.mainloop()
    return result["value"]





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