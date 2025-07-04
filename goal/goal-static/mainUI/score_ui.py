# score_field_ui.py

import os
import customtkinter as ctk
import tkinter.messagebox as messagebox
from colors import COLOR_SUCCESS, COLOR_WARNING
from helpers.helpers import save_teams_to_json
from helpers.notification import prompt_notification, show_message_notification

BUTTON_PAD = dict(padx=5, pady=5)

class ScoreUI:
    def __init__(
        self,
        parent: ctk.CTk,
        instance_number: int,
        mongo,
        desktop_folder: str,
        field_folder: str,
        half_file: str,
        casa_goal_file: str,
        fora_goal_file: str,
    ):
        self.parent = parent
        self.instance = instance_number
        self.mongo = mongo
        self.desktop = desktop_folder
        self.field_folder = field_folder
        os.makedirs(self.field_folder, exist_ok=True)

        self.half_file = half_file
        self.casa_file = casa_goal_file
        self.fora_file = fora_goal_file

        self.decrement_enabled = True

        # initial data
        self._refresh_teams()
        self.load_names()
        self.load_abbrevs()
        
        # build UI
        self._build_half_controls()
        self._build_score_section()
        self._build_bottom_controls()

    # ——— Data —————————————————————————————————————————————————————————
    def load_names(self):
        """Read full team names (or fall back to abbreviation)."""
        def read_or_default(fname, default):
            path = os.path.join(self.field_folder, fname)
            try:
                text = open(path, "r", encoding="utf-8").read().strip()
                return text or default
            except FileNotFoundError:
                return default

        # these default to the abbreviations you already loaded
        self.casa_name = read_or_default("equipa_casa_nome.txt", "Casa")
        self.fora_name = read_or_default("equipa_fora_nome.txt", "Fora")

    def _refresh_teams(self):
        try:
            self.teams = self.mongo.load_teams()
            save_teams_to_json(self.desktop, self.teams)
        except Exception as e:
            print(f"❌ Erro ao carregar equipas: {e}")
            self.teams = {}

    def load_abbrevs(self):
        def read_or_default(fname, default):
            path = os.path.join(self.field_folder, fname)
            try:
                text = open(path, "r", encoding="utf-8").read().strip()
                return text or default
            except FileNotFoundError:
                return default

        self.casa_abbr = read_or_default("equipa_casa_abrev.txt", "Casa")
        self.fora_abbr = read_or_default("equipa_fora_abrev.txt", "Fora")

    # ——— Half-Time Controls —————————————————————————————————————————————

    def _build_half_controls(self):
        frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        frame.pack(**BUTTON_PAD)

        def write_half(part):
            try:
                with open(self.half_file, "w", encoding="utf-8") as f:
                    f.write(part)
                show_message_notification(
                    f"✅ Campo {self.instance} – Atualizado",
                    f"Definido para {part}.",
                    icon="✅", bg_color=COLOR_SUCCESS
                )
                self._highlight_half(part)
            except Exception as e:
                print(f"❌ Erro parte.txt: {e}")

        # create the two buttons
        self.half_buttons = {}
        for part in ("1ª Parte", "2ª Parte"):
            btn = ctk.CTkButton(
                frame,
                text=f"⏱ {part}",
                command=lambda p=part: write_half(p),
                fg_color="gray",
                width=100
            )
            btn.pack(side="left", **BUTTON_PAD)
            self.half_buttons[part] = btn

        # now load the saved half and highlight it
        saved = self._load_half()
        if saved in self.half_buttons:
            self._highlight_half(saved)

    def _highlight_half(self, selected):
        self.selected_half = selected
        for part, btn in self.half_buttons.items():
            btn.configure(fg_color="green" if part == selected else "gray")

    def _load_half(self) -> str:
        """Read the currently saved half from disk, or return empty string."""
        try:
            with open(self.half_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return ""

    # ——— Score Section ——————————————————————————————————————————————————

    def _build_score_section(self):
        container = ctk.CTkFrame(self.parent, fg_color="transparent")
        container.pack(**BUTTON_PAD)

        # Casa stack
        casa_frame = ctk.CTkFrame(container, fg_color="transparent")
        casa_frame.pack(side="left", padx=20)
        self.casa_name_lbl = ctk.CTkLabel(
            casa_frame,
            text=self.casa_name,
            font=("Segoe UI Emoji", 14, "bold")
        )
        self.casa_name_lbl.pack()
        self.casa_lbl = ctk.CTkLabel(
            casa_frame,
            text="",
            font=("Segoe UI Emoji", 24)
        )
        self.casa_lbl.pack()

        # Fora stack
        fora_frame = ctk.CTkFrame(container, fg_color="transparent")
        fora_frame.pack(side="left", padx=20)
        self.fora_name_lbl = ctk.CTkLabel(
            fora_frame,
            text=self.fora_name,
            font=("Segoe UI Emoji", 14, "bold")
        )
        self.fora_name_lbl.pack()
        self.fora_lbl = ctk.CTkLabel(
            fora_frame,
            text="",
            font=("Segoe UI Emoji", 24)
        )
        self.fora_lbl.pack()

        # initial values
        self.update_labels()

    def update_labels(self):
       # reload both abbreviations and full names
        self.load_abbrevs()
        self.load_names()

        self.casa_lbl.configure(
            text=f"{self.casa_abbr}: {self._read(self.casa_file)}"
        )
        self.fora_lbl.configure(
            text=f"{self.fora_abbr}: {self._read(self.fora_file)}"
        )

        # and in case the full names changed on disk:
        self.casa_name_lbl.configure(text=self.casa_name)
        self.fora_name_lbl.configure(text=self.fora_name)

    # ——— Read/Write Score —————————————————————————————————————————————————

    def _read(self, path):
        try:
            return max(0, int(open(path).read().strip()))
        except:
            self._write(path, 0)
            return 0

    def _write(self, path, val):
        with open(path, "w") as f:
            f.write(str(val))

    def _change(self, path, label, prefix, delta):
        new = max(0, self._read(path) + delta)
        self._write(path, new)
        label.configure(text=f"{prefix}: {new}")

    # ——— Bottom Controls ————————————————————————————————————————————————

    def _build_bottom_controls(self):
        frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        frame.pack(fill="x", **BUTTON_PAD)

        ctk.CTkButton(
            frame, text="🔒 Block", fg_color="purple",
            command=self._toggle_decrement
        ).pack(side="left", expand=True, **BUTTON_PAD)

        ctk.CTkButton(
            frame, text="♻️ Zerar", fg_color="blue",
            command=self._confirm_reset
        ).pack(side="left", expand=True, **BUTTON_PAD)

    def _toggle_decrement(self):
        self.decrement_enabled = not getattr(self, "decrement_enabled", True)
        state = "normal" if self.decrement_enabled else "disabled"
        for btn in self.dec_buttons.values():
            btn.configure(state=state)

    def _confirm_reset(self):
        if prompt_notification(f"Campo {self.instance} - Zerar", "Zerar marcador?", icon="❓"):
            for p in (self.casa_file, self.fora_file):
                self._write(p, 0)
            self.update_labels()
