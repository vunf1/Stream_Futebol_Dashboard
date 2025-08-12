import customtkinter as ctk
from typing import Optional, Callable, Any
from customtkinter import CTkFrame, CTkButton, CTkLabel, CTkToplevel

from src.ui import add_footer_label
from src.ui import get_icon
from src.core import GameInfoStore
from src.core import MongoTeamManager

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
        self._was_running: bool = False
        self.mongo = mongo
        self.json = json
        
        # Defer UI initialization for smooth loading
        self.parent.after(75, self._deferred_init_top_grid)  # Faster (was 150ms, now 75ms)

    def _deferred_init_top_grid(self):
        """Deferred UI initialization to ensure smooth loading"""
        try:
            self._init_top_grid()
        except Exception as e:
            print(f"Error initializing TopWidget: {e}")
            # Fallback: initialize immediately if there's an error
            self._init_top_grid()

    def _init_top_grid(self):
        # Create header frame and pack into parent
        header = CTkFrame(self.parent, fg_color="transparent")
        header.pack(fill="x", padx=6, pady=3)  # Reduced padding from 10,5 to 6,3
        
        # Configure grid for equal columns
        for col in range(6):
            header.grid_columnconfigure(col, weight=1, uniform="col")
        bg = ctk.ThemeManager.theme["CTkFrame"]["fg_color"]
        icon = get_icon("stopwatch", 34)
        # Create the "Open Timer" button
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
        

        icon = get_icon("reload", 68)
        # Create the "Open Timer" button
        open_timer_btn = CTkButton(
            header,
            image=icon,
            text="",
            fg_color="transparent",
            corner_radius=20,
            command=self.mongo.backup_to_json,  # Backup teams to JSON
            hover_color=bg,  
        )
        open_timer_btn.grid(row=0, column=3, columnspan=2, sticky="nsew")

    def _open_timer_window(self):
        win = CTkToplevel(self.parent)
        
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-toolwindow", True)
        # make_it_drag_and_drop(win) # This line was removed from imports, so it's removed here.
        self._timer_window = win  
        
        # Lazy import to avoid circular dependency
        from src.ui import TimerComponent
        
        # Instantiate the TimerComponent in the Toplevel
        tc = TimerComponent(win, self.instance_number, self.json)
        self._timer_component = tc

        # Check if timer was running before
        if self._was_running:
            tc.start_timer()



