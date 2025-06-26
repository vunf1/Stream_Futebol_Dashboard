import json
import os
import sys
import customtkinter as ctk
import tkinter.messagebox as messagebox
from multiprocessing import Process
from typing import Optional
from team_names import append_team_to_json, load_teams_json
FOLDER_NAME = "OBS_MARCADOR_FUTEBOL"
ICON_BALL = "\u26BD"
ICON_MINUS = "\u268A"
ICON_WARN = "\u267B"

class ScoreApp:
    def __init__(self, root: ctk.CTk, instance_number: int):
        self.root = root
        add_footer_label(self.root)
        self.root.title(f"{instance_number} Campo")
        self.root.geometry("380x430")
        self.root.minsize(190, 195)

        self.instance_number = instance_number
        self.decrement_buttons_enabled = True

        # Paths
        self.folder_path = os.path.join(os.path.expanduser("~"), "Desktop", FOLDER_NAME)
        self.instance_folder = os.path.join(self.folder_path, f"Campo_{instance_number}")
        os.makedirs(self.instance_folder, exist_ok=True)

        self.casa_path = os.path.join(self.instance_folder, "golo_casa.txt")
        self.fora_path = os.path.join(self.instance_folder, "golo_fora.txt")

        self.casa_abrev = self.load_abbreviation("equipa_casa_abrev.txt", default="Casa")
        self.fora_abrev = self.load_abbreviation("equipa_fora_abrev.txt", default="Fora")
        self.teams_data = load_teams_json(self.folder_path)

        self.setup_ui()

    def load_abbreviation(self, filename, default=""):
        try:
            path = os.path.join(self.instance_folder, filename)
            with open(path, 'r', encoding='utf-8') as f:
                return f.read().strip() or default
        except FileNotFoundError:
            return default

    def setup_ui(self):
        self.create_team_input_ui()
        self.create_score_ui()
        self.create_control_buttons()

    def refresh_teams_data(self):
        self.teams_data = load_teams_json(self.folder_path)
        self.teams_list = list(self.teams_data.keys())

    def create_team_input_ui(self):
        self.refresh_teams_data()
        self.teams_list = list(self.teams_data.keys())  # Apenas nomes

        print(f"Equipas carregadas: {self.teams_list}")

        input_frame = ctk.CTkFrame(self.root)
        input_frame.pack(padx=10, pady=(0, 10))

        self.casa_nome_entry = self.create_combobox_entry(input_frame, "Nome Casa","ex: SPORTING", 0, 0)
        self.casa_abrev_entry = self.create_labeled_entry(input_frame, "Abrev.", "ex: SCP", 0, 0, offset=1)

        self.fora_nome_entry = self.create_combobox_entry(input_frame, "Nome Fora","ex: PORTO", 0, 1)
        self.fora_abrev_entry = self.create_labeled_entry(input_frame, "Abrev.", "ex: FCP", 0, 1, offset=1)

        ctk.CTkButton(self.root, text="Guardar Nomes", fg_color="gray", command=self.save_team_info).pack(pady=(0, 10))

    def create_combobox_entry(self, parent, label_text, label_placeholder, row, column):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=row, column=column, padx=5, pady=5)

        ctk.CTkLabel(frame, text=label_text).pack()

        entry = ctk.CTkEntry(frame, width=160, placeholder_text=label_placeholder)
        entry.pack()

        # Criação da frame de sugestões com largura definida
        suggestion_frame = ctk.CTkFrame(self.root, fg_color="#222222", corner_radius=6, width=160)
        suggestion_frame.place_forget()

        buttons = []

        def clear_suggestions():
            for btn in buttons:
                btn.destroy()
            buttons.clear()
            suggestion_frame.place_forget()

        def show_suggestions(event=None):
            clear_suggestions()

            # Reload data dynamically
            self.refresh_teams_data()
            self.teams_list = list(self.teams_data.keys())

            typed = entry.get().strip().lower()
            matches = [name for name in self.teams_list if typed in name.lower()]

            if matches:
                entry.update_idletasks()
                abs_x = entry.winfo_rootx() - self.root.winfo_rootx()
                abs_y = entry.winfo_rooty() - self.root.winfo_rooty() + entry.winfo_height()

                suggestion_frame.place(x=abs_x, y=abs_y)
                suggestion_frame.lift()

                for name in matches:
                    def select_name(n=name):
                        entry.delete(0, "end") # Clear the entry
                        entry.insert(0, n) # Insert the selected name
                        abrev = self.teams_data.get(n, "") # Get abbreviation from teams_data
                        abrev_fields = {
                            "Casa": self.casa_abrev_entry,
                            "Fora": self.fora_abrev_entry
                        }
                        for key in abrev_fields:
                            if key in label_text:
                                abrev_fields[key].delete(0, "end")
                                abrev_fields[key].insert(0, abrev)
                        clear_suggestions()

                    btn = ctk.CTkButton(
                        master=suggestion_frame,
                        text=name,
                        width=160,
                        height=28,
                        fg_color="#333333",
                        hover_color="#444444",
                        text_color="#FFFFFF",
                        anchor="w",
                        command=select_name
                    )
                    btn.pack(padx=2, pady=1)
                    buttons.append(btn)

        entry.bind("<KeyRelease>", show_suggestions) # Show suggestions on key release
        entry.bind("<FocusOut>", lambda e: self.root.after(100, clear_suggestions)) # Hide suggestions after focus out 

        return entry

    def create_labeled_entry(self, parent, label_text, placeholder, row, column, offset=0):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=row + offset, column=column, padx=5, pady=5)
        ctk.CTkLabel(frame, text=label_text).pack()
        entry = ctk.CTkEntry(frame, placeholder_text=placeholder)
        entry.pack()
        return entry
    def create_score_ui(self):
        labels_frame = ctk.CTkFrame(self.root)
        labels_frame.pack(padx=10, pady=10)

        self.casa_label = ctk.CTkLabel(labels_frame, font=("Segoe UI", 16))
        self.casa_label.pack(side="left", padx=10)

        self.fora_label = ctk.CTkLabel(labels_frame, font=("Segoe UI", 16))
        self.fora_label.pack(side="left", padx=10)

        self.update_labels()

        self.decrement_casa_button = self.create_score_buttons(
            self.casa_label, self.casa_path, lambda: self.casa_abrev, self.root, "Casa"
        )

        self.decrement_fora_button = self.create_score_buttons(
            self.fora_label, self.fora_path, lambda: self.fora_abrev, self.root, "Fora"
        )
    
    def create_control_buttons(self):
        toggle_frame = ctk.CTkFrame(self.root)
        toggle_frame.pack(padx=5, pady=5)
        ctk.CTkButton(toggle_frame, text="Block", command=self.toggle_decrement_buttons, fg_color="orange").pack(padx=2, pady=2, fill='both', expand=True)

        ctk.CTkButton(self.root, text=f"{ICON_WARN}  Zerar?", command=self.confirm_reset, fg_color="blue").pack(padx=10, pady=10)

    def create_score_buttons(self, label, file_path, prefix_func, parent, side):
        frame = ctk.CTkFrame(parent)
        frame.pack(padx=5, pady=5)

        ctk.CTkButton(
            frame,
            text=f"{ICON_BALL} {side}",
            fg_color="green",
            command=lambda: self.change_number(file_path, label, prefix_func(), 1)
        ).pack(side="left", padx=5)

        dec_button = ctk.CTkButton(
            frame,
            text=f"{ICON_MINUS} 1",
            fg_color="red",
            command=lambda: self.change_number(file_path, label, prefix_func(), -1)
        )
        dec_button.pack(side="left", padx=5)

        return dec_button

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

    def update_labels(self):
        self.casa_label.configure(text=f"{self.casa_abrev}: {self.read_number(self.casa_path)}")
        self.fora_label.configure(text=f"{self.fora_abrev}: {self.read_number(self.fora_path)}")

    def change_number(self, path: str, label, prefix: str, delta: int):
        new_value = max(0, self.read_number(path) + delta)
        self.write_number(path, new_value)
        label.configure(text=f"{prefix}: {new_value}")

    def toggle_decrement_buttons(self):
        self.decrement_buttons_enabled = not self.decrement_buttons_enabled
        state = "normal" if self.decrement_buttons_enabled else "disabled"
        self.decrement_casa_button.configure(state=state)
        self.decrement_fora_button.configure(state=state)

    def confirm_reset(self):
        if messagebox.askokcancel("Zerar", "Zerar Marcador?"):
            self.write_number(self.casa_path, 0)
            self.write_number(self.fora_path, 0)
            self.update_labels()

    def save_team_info(self):
        nome_casa = self.casa_nome_entry.get().strip().upper()
        abrev_casa = self.casa_abrev_entry.get().strip().upper()
        nome_fora = self.fora_nome_entry.get().strip().upper()
        abrev_fora = self.fora_abrev_entry.get().strip().upper()
        append_team_to_json(self.folder_path,nome_casa, abrev_casa)
        append_team_to_json(self.folder_path,nome_fora, abrev_fora)
        
        if not all([nome_casa, abrev_casa, nome_fora, abrev_fora]):
            messagebox.showwarning("Warning", "Some fields are empty. Empty files will still be created.")

        try:
            with open(os.path.join(self.instance_folder, "equipa_casa_nome.txt"), 'w', encoding='utf-8') as f:
                f.write(nome_casa)
            with open(os.path.join(self.instance_folder, "equipa_casa_abrev.txt"), 'w', encoding='utf-8') as f:
                f.write(abrev_casa)
            with open(os.path.join(self.instance_folder, "equipa_fora_nome.txt"), 'w', encoding='utf-8') as f:
                f.write(nome_fora)
            with open(os.path.join(self.instance_folder, "equipa_fora_abrev.txt"), 'w', encoding='utf-8') as f:
                f.write(abrev_fora)

            # Refresh UI with updated abbreviation values
            self.casa_abrev = abrev_casa or "Casa"
            self.fora_abrev = abrev_fora or "Fora"
            self.update_labels()

            messagebox.showinfo("Success", f"Team data saved to:\n{self.instance_folder}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save team info:\n{e}")

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
    window.title("Campos")
    window.geometry("320x200")
    window.resizable(False, False)

    ctk.CTkLabel(window, text="Quantos campos queres abrir?", font=("Segoe UI", 15)).pack(pady=(20, 10))

    slider = ctk.CTkSlider(window, from_=1, to=20, number_of_steps=19, width=220)
    slider.set(1)
    slider.pack()

    value_label = ctk.CTkLabel(window, text="1", font=("Segoe UI", 13))
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
        font=("Segoe UI", 11),
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
