import sys
import tkinter as tk
from typing import Optional
import customtkinter as ctk

import os, json

from assets.colors import COLOR_ERROR, COLOR_WARNING
from helpers.filenames import BASE_FOLDER_PATH, get_env

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
    Shows a modal, centered PIN prompt with a clean professional design.
    Returns True if the user enters `correct_pin`, False otherwise (or on Cancel).
    """
    correct_pin = get_env("PIN")
    while True:
        win = ctk.CTkToplevel(parent)
        win.overrideredirect(True)
        win.geometry("320x200")
        win.attributes("-topmost", True)
        win.grab_set()
        
        # Center the window on screen
        win.update_idletasks()
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width - 320) // 2
        y = (screen_height - 200) // 2
        win.geometry(f"320x200+{x}+{y}")

        # Main container with modern styling
        main_frame = ctk.CTkFrame(
            win, 
            fg_color=("gray95", "gray15"),
            corner_radius=16,
            border_width=2,
            border_color=("gray80", "gray30")
        )
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Header section
        header_frame = ctk.CTkFrame(
            main_frame,
            fg_color=("gray90", "gray20"),
            corner_radius=12
        )
        header_frame.pack(fill="x", padx=12, pady=(12, 8))

        # Title with icon
        title_label = ctk.CTkLabel(
            header_frame,
            text="🔐 Admin Access Required",
            font=("Segoe UI", 16, "bold"),
            text_color=("gray20", "gray90")
        )
        title_label.pack(pady=8)

        # Subtitle
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Please enter your PIN to continue",
            font=("Segoe UI", 12),
            text_color=("gray50", "gray60")
        )
        subtitle_label.pack(pady=(0, 8))

        # Input section
        input_frame = ctk.CTkFrame(
            main_frame,
            fg_color="transparent"
        )
        input_frame.pack(fill="x", padx=20, pady=8)

        # PIN entry with better styling
        entry = ctk.CTkEntry(
            input_frame,
            show="•",
            width=240,
            height=40,
            font=("Segoe UI", 14),
            placeholder_text="Enter PIN...",
            corner_radius=10,
            border_width=2,
            border_color=("gray70", "gray40")
        )
        entry.pack(pady=8)
        entry.after(50, entry.focus)  # Faster focus (was 100ms, now 50ms)

        # Small close button below input field
        close_btn = ctk.CTkButton(
            input_frame,
            text="✕",
            width=28,
            height=28,
            font=("Segoe UI", 12, "bold"),
            corner_radius=14,
            fg_color="transparent",
            hover_color=("gray90", "gray10"),
            text_color=("gray60", "gray40"),
            border_width=0
        )
        close_btn.pack(pady=(5, 0))

        # Buttons section
        buttons_frame = ctk.CTkFrame(
            main_frame,
            fg_color="transparent"
        )
        buttons_frame.pack(fill="x", padx=20, pady=(8, 16))

        # Submit button
        submit_btn = ctk.CTkButton(
            buttons_frame,
            text="Submit",
            width=100,
            height=36,
            font=("Segoe UI", 12, "bold"),
            corner_radius=10,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            command=lambda: None  # Will be set below
        )
        submit_btn.pack(side="left", padx=(0, 8))

        # Cancel button
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            width=100,
            height=36,
            font=("Segoe UI", 12),
            corner_radius=10,
            fg_color=("gray60", "gray25"),
            hover_color=("gray50", "gray35"),
            command=lambda: None  # Will be set below
        )
        cancel_btn.pack(side="right", padx=(8, 0))

        result: dict[str, Optional[str]] = {"value": None}
        
        def on_submit(event=None):
            result["value"] = entry.get().strip()
            win.destroy()
            
        def on_cancel(event=None):
            result["value"] = None
            win.destroy()
            
        def on_close(event=None):
            result["value"] = None
            win.destroy()

        # Bind events
        entry.bind("<Return>", on_submit)
        entry.bind("<Escape>", on_cancel)
        submit_btn.configure(command=on_submit)
        cancel_btn.configure(command=on_cancel)
        close_btn.configure(command=on_close)

        # Focus management
        win.focus_force()
        entry.focus_set()

        win.wait_window()

        if result["value"] is None:
            return False
        if result["value"] == correct_pin:
            return True

        show_message_notification(
            "🔒 Access Denied",
            "Incorrect PIN. Please try again.",
            icon="❌",
            bg_color=COLOR_ERROR
        )