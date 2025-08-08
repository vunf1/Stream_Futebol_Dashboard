import sys
import tkinter as tk
from typing import Optional
import customtkinter as ctk

import os, json

from assets.colors import COLOR_ERROR, COLOR_WARNING
from helpers.filenames import BASE_FOLDER_PATH, get_env
from helpers.make_drag_drop import make_it_drag_and_drop
from helpers.notification.toast import show_message_notification


def save_teams_to_json(teams):
    json_path = os.path.join(BASE_FOLDER_PATH, "teams.json")
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(teams, f, indent=4, ensure_ascii=False)
        print(f"📁 Backup JSON criado: {json_path}")
    except Exception as e:
        print(f"❌ Falha ao criar backup JSON: {e}")
        return
        
def load_teams_from_json():
    json_path = os.path.join(BASE_FOLDER_PATH, "teams.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            teams = json.load(f)
        print(f"📥 Backup JSON carregado: {json_path}")
        return teams
    except FileNotFoundError:
        print(f"⚠️ Arquivo de backup não encontrado: {json_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Falha ao decodificar JSON em '{json_path}': {e}")
        return False
    except Exception as e:
        print(f"❌ Erro ao carregar backup JSON: {e}")
        return False
    
def prompt_for_pin(parent):
    """
    Shows a modal, draggable PIN prompt under `parent`.
    Returns True if the user enters `correct_pin`, False otherwise (or on Cancel).
    """
    correct_pin=get_env("PIN")
    while True:
        win = ctk.CTkToplevel(parent, fg_color="black")
        win.overrideredirect(True)
        win.geometry("260x140")
        win.attributes("-topmost", True)
        win.grab_set()

        make_it_drag_and_drop(win)

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

        result: dict[str, Optional[str]] = {"value": None}
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