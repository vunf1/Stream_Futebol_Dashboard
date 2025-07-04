import sys
import tkinter as tk
import customtkinter as ctk

import os, json

from colors import COLOR_ERROR, COLOR_WARNING
from helpers.notification import display_notification, show_message_notification


def save_teams_to_json(folder_desktop_path, teams):
    json_path = os.path.join(folder_desktop_path, "teams.json")
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(teams, f, indent=4, ensure_ascii=False)
        print(f"📁 Backup JSON criado: {json_path}")
    except Exception as e:
        print(f"❌ Falha ao criar backup JSON: {e}")  

def prompt_for_pin(parent, correct_pin):
    """
    Shows a modal, draggable PIN prompt under `parent`.
    Returns True if the user enters `correct_pin`, False otherwise (or on Cancel).
    """
    while True:
        win = ctk.CTkToplevel(parent, fg_color="black")
        win.overrideredirect(True)
        win.geometry("260x140")
        win.attributes("-topmost", True)
        win.grab_set()

        # Make draggable
        def start_move(e):
            win._drag_x = e.x
            win._drag_y = e.y
        def do_move(e):
            if hasattr(win, "_drag_x"):
                x = e.x_root - win._drag_x
                y = e.y_root - win._drag_y
                win.geometry(f"+{x}+{y}")
        win.bind("<Button-1>", start_move)
        win.bind("<B1-Motion>", do_move)

        # Body
        body = ctk.CTkFrame(win, fg_color="black", corner_radius=12)
        body.pack(fill="both", expand=True)

        ctk.CTkLabel(
            body,
            text="Admin Access",
            font=("Segoe UI", 14, "bold"),
            text_color="white"
        ).pack(pady=(5,10))

        entry = ctk.CTkEntry(body, show="*", width=200)
        entry.pack(pady=(0,15))
        entry.after(100, entry.focus)

        result = {"value": None}
        def on_submit(event=None):
            result["value"] = entry.get().strip()
            win.destroy()
        def on_cancel():
            result["value"] = None
            win.destroy()

        entry.bind("<Return>", on_submit)

        btns = ctk.CTkFrame(body, fg_color="transparent")
        btns.pack()
        ctk.CTkButton(btns, text="Submit", width=80, corner_radius=8,
                      command=on_submit).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Cancel", width=80, corner_radius=8,
                      fg_color="#555555", hover_color="#444444",
                      command=on_cancel).pack(side="left", padx=5)

        win.wait_window()

        if result["value"] is None:
            return False
        if result["value"] == correct_pin:
            return True

        show_message_notification(
            "🔒 Acesso Negado",
            "PIN incorreto. Tenta novamente.",
            icon="❌",
            bg_color=COLOR_ERROR
        )