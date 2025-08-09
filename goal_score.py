# goal_score.py
# Standard library imports
from datetime import datetime
import os                     # File system operations
import re                     # Regular expressions
import sys                    # System-specific parameters and functions
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
        
        self.root.geometry("420x460")
        self.root.attributes("-topmost", True)
        self.root.minsize(190, 195)
        self.instance_number = instance_number
        self.json = GameInfoStore(instance_number, debug=True)
        self.decrement_buttons_enabled = True
        self.mongo = MongoTeamManager()
        self.mongo.backup_to_json()  # Backup teams to JSON on startup

        self.setup_ui()

    def setup_ui(self):
        TopWidget(self.root, self.instance_number, self.mongo, self.json)
        # 2)  ScoreUI 
        self.score_ui = ScoreUI(
            self.root,                # no keyword
            self.instance_number,
            self.mongo,
            self.json
        )
        # 3) TeamInputManager
        TeamInputManager(
            parent=self.root,
            mongo=self.mongo,
            refresh_labels_cb=lambda: self.score_ui._update_labels(),
            instance=self.instance_number,
            json=self.json
        )
        add_footer_label(self.root)

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

    procs = []
    for i in range(1, count + 1):
        p = Process(target=child_entry, args=(i, q))
        p.start()
        procs.append(p)

    for p in procs:
        p.join()
        
if __name__ == '__main__':
    freeze_support()
    main()