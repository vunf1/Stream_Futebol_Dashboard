import json
import os
import sys
import customtkinter as ctk
import tkinter.messagebox as messagebox
from multiprocessing import Process
from typing import Optional
from colors import COLOR_ERROR, COLOR_INFO, COLOR_PAUSE, COLOR_STOP, COLOR_SUCCESS, COLOR_WARNING
from helpers import _save_teams_to_json, show_message_notification
from mongodb import MongoTeamManager
from team_names import append_team_to_mongo, load_teams_json
from dotenv import load_dotenv
import re
from mainUI.teams_ui import TeamInputManager
from mainUI.timer_ui import TimerWidget



FOLDER_NAME = "OBS_MARCADOR_FUTEBOL"
ICON_BALL = "\u26BD"
ICON_MINUS = "\u268A"
ICON_WARN = "\u267B"

class ScoreApp:
    def __init__(self, root: ctk.CTk, instance_number: int):
        self.root = root
        self.root.iconbitmap("assets/icons/field.ico")
        add_footer_label(self.root)
        self.root.title(f"{instance_number} Campo")
        self.root.geometry("380x520")
        self.root.minsize(190, 195)
        load_dotenv()
        self.instance_number = instance_number
        self.decrement_buttons_enabled = True

        self.pin = os.getenv("PIN")
        # Paths
        self.folder_desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", FOLDER_NAME)
        self.field_folder = os.path.join(self.folder_desktop_path, f"Campo_{instance_number}")
        os.makedirs(self.field_folder, exist_ok=True)

        self.casa_goal_path = os.path.join(self.field_folder, "golo_casa.txt")
        self.fora_goal_path = os.path.join(self.field_folder, "golo_fora.txt")

        self.casa_abrev = self.load_abbreviation("equipa_casa_abrev.txt", default="Casa")
        self.fora_abrev = self.load_abbreviation("equipa_fora_abrev.txt", default="Fora")
        self.half = os.path.join(self.field_folder, "parte.txt")

        self.teams_data = load_teams_json(self.folder_desktop_path)
        self.mongo = MongoTeamManager()


        self.setup_ui()



    def setup_ui(self):
        TeamInputManager(parent=self.root,field_folder=self.field_folder,refresh_labels_cb=self.update_labels)

        #self.create_team_input_ui()
        self.create_score_ui()
        self.create_half_control_buttons() 
        TimerWidget(self.root, self.field_folder)
        #TimerWidget(self.root, self.field_folder)
        #TimerWidget(self.root, self.field_folder).show()
        self.create_control_buttons()

    def load_abbreviation(self, filename, default=""):
        try:
            path = os.path.join(self.field_folder, filename)
            with open(path, 'r', encoding='utf-8') as f:
                return f.read().strip() or default
        except FileNotFoundError:
            return default

    def refresh_teams_data(self):
        self.teams_data = self._fetch_and_backup_teams()
        self.teams_list = list(self.teams_data.keys())

    def _fetch_and_backup_teams(self):
        try:
            teams = self.mongo.load_teams()
            _save_teams_to_json(self.folder_desktop_path, teams)
            return teams
        except Exception as e:
            print(f"❌ Erro ao carregar equipas do MongoDB: {e}")
            return {}
        
    def create_half_control_buttons(self):
        frame = ctk.CTkFrame(self.root)
        frame.pack(padx=10, pady=10)

        self.selected_half = None  # Store current selection

        def write_half(value):
            try:
                with open(self.half, "w", encoding="utf-8") as f:
                    f.write(str(value))
                show_message_notification("Atualizado", f"parte.txt definido para {value} no campo {self.instance_number}.", icon="✅", bg_color=COLOR_SUCCESS)
                update_button_colors(value)
            except Exception as e:
                print(f"❌ Falha ao escrever em parte.txt:\n{e}")

        # Create buttons with reference
        self.btn_half1 = ctk.CTkButton(frame, text="⏱ 1ª Parte", fg_color="gray", command=lambda: write_half("1ª Parte"))
        self.btn_half2 = ctk.CTkButton(frame, text="⏱ 2ª Parte", fg_color="gray", command=lambda: write_half("2ª Parte"))

        self.btn_half1.pack(side="left", padx=5)
        self.btn_half2.pack(side="left", padx=5)

        def update_button_colors(selected):
            self.selected_half = selected
            # Toggle colors
            if selected == "1ª Parte":
                self.btn_half1.configure(fg_color="green")
                self.btn_half2.configure(fg_color="gray")
            else:
                self.btn_half1.configure(fg_color="gray")
                self.btn_half2.configure(fg_color="green")


    def create_score_ui(self):
        labels_frame = ctk.CTkFrame(self.root)
        labels_frame.pack(padx=10, pady=(10, 5))

        self.casa_label = ctk.CTkLabel(labels_frame, font=("Segoe UI Emoji", 16))
        self.casa_label.pack(side="left", padx=10)

        self.fora_label = ctk.CTkLabel(labels_frame, font=("Segoe UI Emoji", 16))
        self.fora_label.pack(side="left", padx=10)

        self.update_labels()

        # Wrap both button groups in a single frame to align them side by side
        button_row = ctk.CTkFrame(self.root)
        button_row.pack(padx=10, pady=10)

        self.decrement_casa_button = self.create_score_buttons(
            self.casa_label, self.casa_goal_path, lambda: self.casa_abrev, button_row, "Casa"
        )

        self.decrement_fora_button = self.create_score_buttons(
            self.fora_label, self.fora_goal_path, lambda: self.fora_abrev, button_row, "Fora"
        )
    

    def create_score_buttons(self, label, file_path, prefix_func, parent, side):
        frame = ctk.CTkFrame(parent)
        frame.pack(side="left", padx=5, pady=5)  # 👈 horizontal alignment of buttons

        ctk.CTkButton(
            frame,
            text=f"{ICON_BALL} {side}",
            fg_color="green",
            command=lambda: self.change_number(file_path, label, prefix_func(), 1)
        ).pack(padx=5, pady=2)

        dec_button = ctk.CTkButton(
            frame,
            text=f"{ICON_MINUS} 1",
            fg_color="red",
            command=lambda: self.change_number(file_path, label, prefix_func(), -1)
        )
        dec_button.pack(padx=5, pady=2)

        return dec_button
    
    def update_labels(self):
        # reload the latest abbreviations from the files
        self.casa_abrev = self.load_abbreviation("equipa_casa_abrev.txt", default="Casa")
        self.fora_abrev = self.load_abbreviation("equipa_fora_abrev.txt", default="Fora")

        # now update the labels
        self.casa_label.configure(
            text=f"{self.casa_abrev}: {self.read_number(self.casa_goal_path)}"
        )
        self.fora_label.configure(
            text=f"{self.fora_abrev}: {self.read_number(self.fora_goal_path)}"
        )


    def change_number(self, path: str, label, prefix: str, delta: int):
        new_value = max(0, self.read_number(path) + delta)
        self.write_number(path, new_value)
        label.configure(text=f"{prefix}: {new_value}")

    def create_control_buttons(self):
        button_frame = ctk.CTkFrame(self.root)
        button_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkButton(button_frame, text="Block", command=self.toggle_decrement_buttons, fg_color="purple").pack(side="left", expand=True, padx=5)
        ctk.CTkButton(button_frame, text=f"{ICON_WARN} Zerar", command=self.confirm_reset, fg_color="blue").pack(side="left", expand=True, padx=5)
    
    def read_number(self, path: str) -> int:
        try:
            with open(path, 'r') as f:
                return max(0, int(f.read().strip()))
        except Exception:
            self.write_number(path, 0)
            return 0

    def write_number(self, path: str, value: int):
        with open(path, 'w') as f:
            f.write(str(value))


    def toggle_decrement_buttons(self):
        self.decrement_buttons_enabled = not self.decrement_buttons_enabled
        state = "normal" if self.decrement_buttons_enabled else "disabled"
        self.decrement_casa_button.configure(state=state)
        self.decrement_fora_button.configure(state=state)

    def confirm_reset(self):
        if messagebox.askokcancel("Zerar", "Zerar Marcador?"):
            self.write_number(self.casa_goal_path, 0)
            self.write_number(self.fora_goal_path, 0)
            self.update_labels()


def start_instance(instance_number: int):
    root = ctk.CTk()
    app = ScoreApp(root, instance_number)
    root.mainloop()

def ask_instance_count_ui() -> int:
    result = {"value": None}

    def confirm():
        result["value"] = int(slider.get())
        window.destroy()

    window = ctk.CTk()
    window.iconbitmap("assets/icons/dice.ico")
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
    footer = ctk.CTkLabel(
        parent,
        text=text,
        font=("Segoe UI Emoji", 11),
        text_color="gray"
    )
    footer.pack(side="bottom", pady=(5, 5))

def main():
    ctk.set_appearance_mode("system")

    instance_count = ask_instance_count_ui()
    if not instance_count:
        sys.exit()

    processes = []
    for i in range(1, instance_count + 1):
        p = Process(target=start_instance, args=(i,))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    main()
