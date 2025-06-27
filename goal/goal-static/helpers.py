import tkinter as tk
import customtkinter as ctk

import os, json

# Keeps track of active notifications to prevent overlapping
_active_notifications = []

def show_message_notification(title, message, duration=5000, icon="ℹ️", bg_color=None):
    temp_win = ctk.CTkToplevel()
    temp_win.overrideredirect(True)  # No border/title bar
    temp_win.attributes("-topmost", True)
    temp_win.attributes("-alpha", 0.0)  # Start invisible for fade-in

    # Toast size
    width, height = 300, 100
    margin = 20
    spacing = 10

    # Position (stacked if needed)
    temp_win.update_idletasks()
    screen_width = temp_win.winfo_screenwidth()
    screen_height = temp_win.winfo_screenheight()

    # Calculate Y position based on existing toasts
    y_offset = screen_height - height - margin
    for win in _active_notifications:
        y_offset -= (height + spacing)

    x = screen_width - width - margin
    temp_win.geometry(f"{width}x{height}+{x}+{y_offset}")

    # Save reference to manage stacking
    _active_notifications.append(temp_win)

    # Build content
    frame = ctk.CTkFrame(temp_win, corner_radius=10, fg_color=bg_color)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    icon_label = ctk.CTkLabel(frame, text=icon, font=("Segoe UI", 24))
    icon_label.pack(side="left", padx=(5, 10))

    text_frame = ctk.CTkFrame(frame, fg_color="transparent")
    text_frame.pack(side="left", fill="both", expand=True)

    ctk.CTkLabel(text_frame, text=title, font=("Segoe UI", 14, "bold")).pack(anchor="w")
    ctk.CTkLabel(text_frame, text=message, font=("Segoe UI", 12), wraplength=220).pack(anchor="w")

    # Fade in
    def fade_in(opacity=0.0):
        if opacity < 1.0:
            temp_win.attributes("-alpha", opacity)
            temp_win.after(20, lambda: fade_in(opacity + 0.1))
        else:
            temp_win.attributes("-alpha", 1.0)
            temp_win.after(duration, fade_out)

    # Fade out
    def fade_out(opacity=1.0):
        if opacity > 0:
            temp_win.attributes("-alpha", opacity)
            temp_win.after(20, lambda: fade_out(opacity - 0.1))
        else:
            try:
                _active_notifications.remove(temp_win)
            except ValueError:
                pass
            temp_win.destroy()

    fade_in()


def _save_teams_to_json(folder_desktop_path, teams):
    json_path = os.path.join(folder_desktop_path, "teams.json")
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(teams, f, indent=4, ensure_ascii=False)
        print(f"📁 Backup JSON criado: {json_path}")
    except Exception as e:
        print(f"❌ Falha ao criar backup JSON: {e}")  

