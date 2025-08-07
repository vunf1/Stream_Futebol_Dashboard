import os, sys
import customtkinter as ctk
from tkinter import messagebox
from helpers.env_loader import SecureEnvLoader
from helpers.filenames import get_file_path
from helpers.notification.toast import show_message_notification
from helpers.helpers import load_teams_from_json, save_teams_to_json
from mainUI.teamsUI.autocomplete import Autocomplete
from database.mongodb import MongoTeamManager
from helpers.team_names import append_team_to_mongo
from assets.colors import COLOR_WARNING, COLOR_SUCCESS
from mainUI.edit_teams_ui import TeamManagerWindow
 

# ─── Decrypt & load ─────────────────────────────────────────
SecureEnvLoader().load()

class TeamInputManager(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        mongo,
        refresh_labels_cb,    # callback to run after saving
        instance
    ):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.parent = parent
        self.refresh_labels = refresh_labels_cb
        self.instance_number = instance

        self.mongo = mongo
        self._build_ui()

    def _write_field(self, filename: str, text: str):
        path = get_file_path(self.instance_number, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def _fetch_and_backup_teams(self):
        """
        Load all teams from MongoDB, write a local JSON backup,
        and return the dict of {name: abbreviation}.
        """
            
        try:
            teams = load_teams_from_json()
            if teams is False:
                teams = self.mongo.load_teams()
                save_teams_to_json(teams)
                return teams
            return teams
        except Exception as e:
            print(f"❌ Erro ao carregar equipas: {e}")
            return {} # Return empty dict on failure

    def _build_ui(self):
        self.pack(fill="x", padx=10)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x")
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        # Home team label
        ctk.CTkLabel(container, text="Nome Casa").grid(row=0, column=0, sticky="w", padx=5)
        self.home_name_entry = Autocomplete(
            container,
            lambda: self._fetch_and_backup_teams(),
            self._on_home_selected,
            "ex: SPORTING"
        ) 
        self.home_name_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=(0,10))

        ctk.CTkLabel(container, text="Sigla Casa").grid(row=2, column=0, sticky="w", padx=5)
        self.home_abbrev_entry = self._make_entry(container, row=3, column=0, placeholder="ex: SCP")

        # Away team label
        ctk.CTkLabel(container, text="Nome Fora").grid(row=0, column=1, sticky="w", padx=5)
        self.away_name_entry = Autocomplete(
            container,
            lambda: self._fetch_and_backup_teams(),
            self._on_away_selected,
            "ex: PORTO"
        )
        self.away_name_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=(0,10))

        ctk.CTkLabel(container, text="Sigla Fora").grid(row=2, column=1, sticky="w", padx=5)
        self.away_abbrev_entry = self._make_entry(container, row=3, column=1, placeholder="ex: FCP")
            
        # ——— Buttons ———
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        # Allow the frame to expand horizontally (and vertically if you like)
        btn_frame.pack(fill="x")

        # Tell the frame’s grid to share extra space equally between its two columns
        btn_frame.grid_rowconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(0, weight=1, uniform="btns")
        btn_frame.grid_columnconfigure(1, weight=1, uniform="btns")

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
                mongo=self.mongo
            )
        )
        save_btn.grid(row=0, column=0, sticky="nsew", padx=(0,5))
        edit_btn.grid(row=0, column=1, sticky="nsew", padx=(5,0))

    def _make_entry(self, parent, row, column, placeholder=""):
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder)
        entry.grid(row=row, column=column, sticky="ew", padx=5, pady=(0,10))
        return entry

    def _on_home_selected(self, name, abrev):
        self.home_abbrev_entry.delete(0, "end")
        self.home_abbrev_entry.insert(0, abrev)

    def _on_away_selected(self, name, abrev):
        self.away_abbrev_entry.delete(0, "end")
        self.away_abbrev_entry.insert(0, abrev)

    def _on_save(self):
        home_name  = self.home_name_entry.get().strip().upper()
        home_abrev = self.home_abbrev_entry.get().strip().upper()
        away_name  = self.away_name_entry.get().strip().upper()
        away_abrev = self.away_abbrev_entry.get().strip().upper()

        append_team_to_mongo(home_name,  home_abrev, self.instance_number)
        append_team_to_mongo(away_name,  away_abrev, self.instance_number)

        if not all([home_name, home_abrev, away_name, away_abrev]):
            show_message_notification(
                f"⚠️ Campo {self.instance_number} -  Aviso",
                "Alguns campos estão vazios. Campos vazios serão criados.",
                icon="⚠️", bg_color=COLOR_WARNING
            )

        try:
            self._write_field("home_name",  home_name)
            self._write_field("home_abbr", home_abrev)
            self._write_field("away_name",  away_name)
            self._write_field("away_abbr", away_abrev)

            self.refresh_labels()
            show_message_notification(
                f"✅ Campo {self.instance_number} - Gravado",
                "Informações da equipa foram guardadas",
                icon="✅", bg_color=COLOR_SUCCESS
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save team info:\n{e}")
            