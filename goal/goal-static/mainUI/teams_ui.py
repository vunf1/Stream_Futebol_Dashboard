# teams_ui.py

import os
import customtkinter as ctk
from tkinter import messagebox
from helpers.notification import show_message_notification
from helpers.helpers import save_teams_to_json
from mongodb import MongoTeamManager
from team_names import append_team_to_mongo
from colors import COLOR_WARNING, COLOR_SUCCESS
from mainUI.edit_teams_ui import TeamManagerWindow
class TeamInputManager(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        field_folder: str,
        refresh_labels_cb,    # callback to run after saving
        instance
    ):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.parent = parent
        self.field_folder = field_folder
        self.refresh_labels = refresh_labels_cb
        self.instance_number = instance

        self.mongo = MongoTeamManager()
        self._build_ui()

    def _fetch_and_backup_teams(self):
        """
        Load all teams from MongoDB, write a local JSON backup,
        and return the dict of {name: abbreviation}.
        """
        try:
            teams = self.mongo.load_teams()
            save_teams_to_json(self.field_folder, teams)
            return teams
        except Exception as e:
            print(f"❌ Erro ao carregar equipas do MongoDB: {e}")
            return {}
        
    def _build_ui(self):
        # Pack this frame
        self.pack(fill="x", padx=10, pady=(0,10))

        # Load teams for autocomplete
        teams = self._fetch_and_backup_teams()
        self.team_names = list(teams.keys())

        # Container for grid layout
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x")

        # Configure two columns
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        # ——— Home team inputs ———
        ctk.CTkLabel(container, text="Nome Casa").grid(row=0, column=0, sticky="w", padx=5)
        self.home_name_entry = self._make_combobox(
            container, row=1, column=0,
            placeholder="ex: SPORTING",
            target_abbrev="home"
        )
        ctk.CTkLabel(container, text="Sigla Casa").grid(row=2, column=0, sticky="w", padx=5)
        self.home_abbrev_entry = self._make_entry(container, row=3, column=0, placeholder="ex: SCP")

        # ——— Away team inputs ———
        ctk.CTkLabel(container, text="Nome Fora").grid(row=0, column=1, sticky="w", padx=5)
        self.away_name_entry = self._make_combobox(
            container, row=1, column=1,
            placeholder="ex: PORTO",
            target_abbrev="away"
        )
        ctk.CTkLabel(container, text="Sigla Fora").grid(row=2, column=1, sticky="w", padx=5)
        self.away_abbrev_entry = self._make_entry(container, row=3, column=1, placeholder="ex: FCP")

        # ——— Buttons frame ———
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(5,10))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Guardar",
            fg_color="gray",
            command=self._on_save
        )
        edit_btn = ctk.CTkButton(
            btn_frame,
            text="Editar",
            fg_color="orange",
            command=lambda: TeamManagerWindow(
                parent=self.parent,
                mongo=self.mongo,
                pin=os.getenv("PIN")
            )
        )

        # pack side by side
        save_btn.pack(side="left", expand=True, padx=5)
        edit_btn.pack(side="left", expand=True, padx=5)

    def _make_entry(self, parent, row, column, placeholder=""):
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder)
        entry.grid(row=row, column=column, sticky="ew", padx=5, pady=(0,10))
        return entry

    def _make_combobox(self, parent, row, column, placeholder, target_abbrev):
        """
        Creates an entry with a suggestion dropdown.
        target_abbrev: 'home' or 'away' to know which abbrev field to fill.
        """
        frame = ctk.CTkFrame(parent)
        frame.grid(row=row, column=column, sticky="ew", padx=5, pady=(0,10))

        entry = ctk.CTkEntry(frame, placeholder_text=placeholder)
        entry.pack(fill="x")

        suggestion_frame = ctk.CTkFrame(self.parent, fg_color="#222222", corner_radius=6)
        buttons = []

        def clear_suggestions():
            for btn in buttons:
                btn.destroy()
            buttons.clear()
            suggestion_frame.place_forget()

        def show_suggestions(event=None):
            clear_suggestions()
            text = entry.get().strip().lower()
            teams = self._fetch_and_backup_teams()
            matches = [n for n in teams if text in n.lower()]
            if not matches:
                return

            # position below the entry
            entry.update_idletasks()
            x = entry.winfo_rootx() - self.parent.winfo_rootx()
            y = entry.winfo_rooty() - self.parent.winfo_rooty() + entry.winfo_height()
            suggestion_frame.place(x=x, y=y)

            for name in matches:
                def select(n=name):
                    entry.delete(0, "end")
                    entry.insert(0, n)
                    abrev = teams[n]
                    if target_abbrev == "home":
                        self.home_abbrev_entry.delete(0, "end")
                        self.home_abbrev_entry.insert(0, abrev)
                    else:
                        self.away_abbrev_entry.delete(0, "end")
                        self.away_abbrev_entry.insert(0, abrev)
                    clear_suggestions()

                btn = ctk.CTkButton(
                    suggestion_frame,
                    text=name,
                    anchor="w",
                    fg_color="#333333",
                    hover_color="#444444",
                    command=select
                )
                btn.pack(fill="x", padx=2, pady=1)
                buttons.append(btn)

        entry.bind("<KeyRelease>", show_suggestions)
        entry.bind("<FocusOut>", lambda e: self.parent.after(100, clear_suggestions))

        return entry

    def _on_save(self):
        home_name  = self.home_name_entry.get().strip().upper()
        home_abrev = self.home_abbrev_entry.get().strip().upper()
        away_name  = self.away_name_entry.get().strip().upper()
        away_abrev = self.away_abbrev_entry.get().strip().upper()

        append_team_to_mongo(home_name,  home_abrev, self.instance_number)
        append_team_to_mongo(away_name,  away_abrev, self.instance_number)

        if not all([home_name, home_abrev, away_name, away_abrev]):
            show_message_notification(f"⚠️ Campo {self.instance_number} -  Aviso","Alguns campos estão vazios. Campos vazios serão criados.",icon="⚠️", bg_color=COLOR_WARNING)

        try:
            base = self.field_folder
            with open(os.path.join(base, "equipa_casa_nome.txt"),  "w") as f: f.write(home_name)
            with open(os.path.join(base, "equipa_casa_abrev.txt"), "w") as f: f.write(home_abrev)
            with open(os.path.join(base, "equipa_fora_nome.txt"),  "w") as f: f.write(away_name)
            with open(os.path.join(base, "equipa_fora_abrev.txt"), "w") as f: f.write(away_abrev)

            # Update any UI labels that depend on these values
            self.refresh_labels()
            show_message_notification(f"✅Campo {self.instance_number} -  Gravado","Informações da equipa foram guardadas",icon="✅", bg_color=COLOR_SUCCESS)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save team info:\n{e}")
