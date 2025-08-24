import customtkinter as ctk
from typing import Optional, Callable, Any
from customtkinter import CTkFrame, CTkButton, CTkLabel, CTkToplevel

from src.ui import get_icon
from src.core import GameInfoStore
from src.core import MongoTeamManager
from src.core.logger import get_logger

class TopWidget:
    def __init__(self, parent, instance_number: int, mongo: MongoTeamManager, json: GameInfoStore):
        """
        Widget launcher for opening a borderless, draggable TimerComponent window.

        Args:
            parent: The CTk parent window.
            field_folder: Path to the folder where timer files are stored.
            instance_number: Identifier for the timer instance.
        """
        self.parent = parent
        self.instance_number = instance_number
        self._timer_window: CTkToplevel | None = None
        self._timer_component: Optional[Any] = None  # Will be TimerComponent when imported
        self.mongo = mongo
        self.json = json
        self._log = get_logger(__name__)
        
        # Defer UI initialization for smooth loading
        self.parent.after(75, self._deferred_init_top_grid)  # Faster (was 150ms, now 75ms)

    def _deferred_init_top_grid(self):
        """Deferred UI initialization to ensure smooth loading"""
        try:
            self._init_top_grid()
        except Exception as e:
            try:
                self._log.error("topwidget_init_error", exc_info=True)
            except Exception:
                pass
            # Fallback: initialize immediately if there's an error
            self._init_top_grid()

    def _init_top_grid(self):
        # Create header frame and pack into parent
        header = CTkFrame(self.parent, fg_color="transparent")
        header.pack(fill="x", padx=6, pady=3)  # Reduced padding from 10,5 to 6,3
        
        # Configure grid for equal columns
        for col in range(8):
            header.grid_columnconfigure(col, weight=1, uniform="col")
        bg = ctk.ThemeManager.theme["CTkFrame"]["fg_color"]
        
        # Create the "Open Timer" button
        icon = get_icon("stopwatch", 45)
        open_timer_btn = CTkButton(
            header,
            image=icon,
            text="",
            fg_color="transparent",
            corner_radius=20,
            command=self._open_timer_window,
            hover_color=bg,  
        )
        open_timer_btn.grid(row=0, column=1, columnspan=2, sticky="nsew")
        
        # Create the "Penalty Shootout" button
        icon = get_icon("penalties_btn", 84)
        penalty_btn = CTkButton(
            header,
            image=icon,
            text="",
            fg_color="transparent",
            corner_radius=20,
            command=self._open_penalty_window,
            hover_color=bg,  
        )
        penalty_btn.grid(row=0, column=3, columnspan=2, sticky="nsew")

        # Create the "Edit Teams" button
        icon = get_icon("gear", 68)
        edit_btn = CTkButton(
            header,
            image=icon,
            text="",
            fg_color="transparent",
            corner_radius=20,
            command=self._open_team_manager,
            hover_color=bg,
        )
        edit_btn.grid(row=0, column=5, columnspan=2, sticky="nsew")

    def _open_timer_window(self):
        # Check if timer window is already open for this instance
        if self._timer_window is not None and self._timer_window.winfo_exists():
            # Window exists, bring it to focus
            self._timer_window.lift()
            self._timer_window.focus_force()
            return
        
        # Create timer window as non-modal popup
        win = ctk.CTkToplevel(self.parent)
        win.title(f"Timer - Campo {self.instance_number}")
        win.geometry("960x85")
        win.attributes("-toolwindow", True)
        
        # Ensure window is non-modal and doesn't block parent
        win.transient(self.parent)  # Make it a transient window (non-modal)
        win.grab_release()  # Ensure no grab is set
        
        # Apply window configuration without modal behavior
        from src.utils import configure_window, center_window_on_parent
        non_modal_config = {
            "overrideredirect": True,
            "topmost": True,
            "grab_set": False,  # Non-modal
            "resizable": (False, False),
            "focus_force": True,
            "lift": True,
            "transient": True
        }
        configure_window(win, non_modal_config, self.parent)
        center_window_on_parent(win, self.parent, 960, 85)
        
        # Apply drag and drop to the window
        from src.utils import apply_drag_and_drop
        apply_drag_and_drop(win)
        
        # Handle window close event to clean up references
        def on_window_close():
            self._timer_window = None
            self._timer_component = None
        
        win.protocol("WM_DELETE_WINDOW", on_window_close)
        
        self._timer_window = win
        
        # Lazy import to avoid circular dependency
        from src.ui import TimerComponent
        
        # Instantiate the TimerComponent in the Toplevel with close callback
        tc = TimerComponent(win, self.instance_number, self.json, on_close_callback=on_window_close)
        self._timer_component = tc

    def _open_penalty_window(self):
        """Open penalty shootout dashboard window"""
        try:
            from src.ui.penalty import open_penalty_dashboard
            open_penalty_dashboard(self.parent, self.instance_number)
        except Exception as e:
            try:
                self._log.error("penalty_open_error", exc_info=True)
            except Exception:
                pass
            # Fallback: show error message
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", f"Failed to open penalty dashboard: {e}")

    def _open_team_manager(self):
        """Open the Team Manager window"""
        try:
            from src.ui.edit_teams_ui import TeamManagerWindow
            TeamManagerWindow(parent=self.parent, mongo=self.mongo)
        except Exception as e:
            try:
                self._log.error("team_manager_open_error", exc_info=True)
            except Exception:
                pass



