import os
import json
import tkinter.messagebox as messagebox
import customtkinter as ctk

def append_team_to_json(instance_folder: str, name: str, abrev: str):
    json_path = os.path.join(instance_folder, "teams.json")
    data = {}

    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    if name in data:
        current_abrev = data[name]["abrev"]
        if current_abrev != abrev:
            root = ctk.CTk()
            root.withdraw() 
            result = messagebox.askyesno(
                title="Team Exists",
                message=f"Team '{name}' already exists with abbreviation '{current_abrev}'.\nDo you want to keep the existing abbreviation?"
            )
            root.destroy()
            if not result:
                messagebox.showinfo("Cancelled", "Operation cancelled.")
                return
            else:
                messagebox.showinfo("Merged", "Keeping existing abbreviation.")
                return

    data[name] = {"abrev": abrev}

    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        messagebox.showinfo("Saved", f"Team '{name}' saved.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to write JSON: {e}")

def load_teams_data(instance_folder: str):
    json_path = os.path.join(instance_folder, "teams.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}
