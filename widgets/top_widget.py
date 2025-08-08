import customtkinter as ctk
from customtkinter import CTkFrame, CTkButton, CTkLabel, CTkToplevel

from assets.icons.icons_provider import get_icon
from database.mongodb import MongoTeamManager
from helpers.make_drag_drop import make_it_drag_and_drop
from assets.colors import COLOR_ERROR
from helpers.top_c_child_parent import top_centered_child_to_parent
from mainUI.timer_ui import TimerComponent

class TopWidget:
    def __init__(self, parent, instance_number: int, mongo: MongoTeamManager ):
        """
        Widget launcher for opening a borderless, draggable TimerComponent window.

        Args:
            parent: The CTk parent window.
            field_folder: Path to the folder where timer files are stored.
            instance_number: Identifier for the timer instance.
        """
        self.parent = parent
        self.instance_number = instance_number
        self._timer_window: CTkToplevel | None      = None
        self._timer_component: TimerComponent | None = None
        self._was_running: bool                     = False
        self.mongo = mongo
        self._init_top_grid()

    def _init_top_grid(self):
        # Create header frame and pack into parent
        header = CTkFrame(self.parent, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=5)
        
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
        if self._timer_window and self._timer_window.winfo_exists():
            tc = self._timer_component
            if tc:
                self._was_running = tc.timer_running
            self._timer_window.destroy()
        
        win = CTkToplevel(self.parent)
        
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-toolwindow", True)
        make_it_drag_and_drop(win)
        self._timer_window = win  
        
        header = CTkFrame(win, fg_color="transparent")
        header.pack(fill="x", pady=(2, 0), padx=2)

        #icon = get_icon("stopwatch", 34)
        #icon_lbl = ctk.CTkLabel(header, image=icon, text="")
        #icon_lbl.pack(side="left", padx=(2, 5), pady=2)
        title_lbl = CTkLabel(
            header,
            text=f"Campo – {self.instance_number}",
            font=("Arial", 14),
            text_color="red"
        )
        title_lbl.pack(side="left", expand=True)

        close_btn = CTkButton(
            header,
            text="✕",
            width=20, height=20,
            fg_color="transparent",
            hover_color=COLOR_ERROR,
            text_color="black",
            command=win.destroy
        )
        close_btn.pack(side="right", padx=5)

        # Instantiate the TimerComponent in the Toplevel
        tc = TimerComponent(win, self.instance_number)
        self._timer_component = tc

        # 4) Se antes estava a correr
        if self._was_running:
            tc.start_timer()

        child_w, child_h = 900, 120
        # Center the child window at the top of the parent
        top_centered_child_to_parent(win, self.parent, child_w, child_h)


