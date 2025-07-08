import os
import customtkinter as ctk
import tkinter.messagebox as messagebox
from colors import COLOR_ERROR, COLOR_SUCCESS, COLOR_WARNING
from helpers.helpers import save_teams_to_json
from helpers.notification import prompt_notification, show_message_notification

BUTTON_PAD = dict(padx=5, pady=5)

class ScoreUI:
    def __init__(
        self,
        parent: ctk.CTkBaseClass,
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
        # register decrement buttons (if added later)
        self.dec_buttons = {}

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

        saved = self._load_half()
        if saved in self.half_buttons:
            self._highlight_half(saved)

    def _highlight_half(self, selected):
        self.selected_half = selected
        for part, btn in self.half_buttons.items():
            btn.configure(fg_color="green" if part == selected else "gray")

    def _load_half(self) -> str:
        try:
            with open(self.half_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return ""

    # ——— Score Section ——————————————————————————————————————————————————
    def _build_score_section(self):
        container = ctk.CTkFrame(self.parent, fg_color='transparent')
        # container itself has no extra padding
        container.pack(fill='both', expand=True, padx=0, pady=0)

        # Casa
        casa_frame = ctk.CTkFrame(container, fg_color='transparent')
        # no pad between casa and container
        casa_frame.pack(side='left', fill='both', expand=True, padx=0, pady=0)
        self.casa_name_lbl = ctk.CTkLabel(
            casa_frame, text=self.casa_name, font=('Segoe UI Emoji', 14, 'bold')
        )
        self.casa_name_lbl.pack(fill='x', pady=(0,5))
        self.casa_lbl = ctk.CTkLabel(
            casa_frame, text='', font=('Segoe UI Emoji', 24)
        )
        self.casa_lbl.pack(fill='x', pady=(0,10))

        plus_casa = ctk.CTkButton(
            casa_frame, text='+1', fg_color=COLOR_SUCCESS, width=80,
            command=lambda: self._change(self.casa_file, self.casa_lbl, self.casa_abbr, 1)
        )
        minus_casa = ctk.CTkButton(
            casa_frame, text='-1', fg_color=COLOR_ERROR, width=80,
            command=lambda: self._change(self.casa_file, self.casa_lbl, self.casa_abbr, -1)
        )
        plus_casa.pack(padx=0, pady=0)
        minus_casa.pack(padx=0, pady=0)
        self.dec_buttons['casa'] = minus_casa

        # Fora
        fora_frame = ctk.CTkFrame(container, fg_color='transparent')
        # no pad between casa_frame and fora_frame
        fora_frame.pack(side='left', fill='both', expand=True, padx=0, pady=0)
        self.fora_name_lbl = ctk.CTkLabel(
            fora_frame, text=self.fora_name, font=('Segoe UI Emoji', 14, 'bold')
        )
        self.fora_name_lbl.pack(fill='x', pady=(0,5))
        self.fora_lbl = ctk.CTkLabel(
            fora_frame, text='', font=('Segoe UI Emoji', 24)
        )
        self.fora_lbl.pack(fill='x', pady=(0,10))

        plus_fora = ctk.CTkButton(
            fora_frame, text='+1', fg_color=COLOR_SUCCESS, width=80,
            command=lambda: self._change(self.fora_file, self.fora_lbl, self.fora_abbr, 1)
        )
        minus_fora = ctk.CTkButton(
            fora_frame, text='-1', fg_color=COLOR_ERROR, width=80,
            command=lambda: self._change(self.fora_file, self.fora_lbl, self.fora_abbr, -1)
        )
        plus_fora.pack(padx=0, pady=0)
        minus_fora.pack(padx=0, pady=0)
        self.dec_buttons['fora'] = minus_fora

        self.update_labels()

    def update_labels(self):
        self.load_abbrevs()
        self.load_names()

        self.casa_lbl.configure(
            text=f"{self.casa_abbr}: {self._read(self.casa_file)}"
        )
        self.fora_lbl.configure(
            text=f"{self.fora_abbr}: {self._read(self.fora_file)}"
        )

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

    # ——— Swap Logic —————————————————————————————————————————————————————
    def _swap_scores(self):
        """Swap the home and away scores on disk and update the UI."""
        try:
            casa_score = self._read(self.casa_file)
            fora_score = self._read(self.fora_file)
            self._write(self.casa_file, fora_score)
            self._write(self.fora_file, casa_score)
            self.update_labels()
            show_message_notification(
                f"✅ Campo {self.instance} – Swap",
                f"Casa ← {fora_score} | Fora ← {casa_score}",
                icon="🔄", bg_color=COLOR_SUCCESS
            )
        except Exception as e:
            print(f"❌ Erro ao trocar placares: {e}")

    # ——— Bottom Controls ————————————————————————————————————————————————
    def _build_bottom_controls(self):
        frame = ctk.CTkFrame(self.parent, fg_color='transparent')
        frame.pack(fill='x', expand=True, padx=0, pady=0)
        buttons = [
            ('🔄 Swap',   'orange', self._swap_scores),
            ('🔒 Block',  'purple', self._toggle_decrement),
            ('♻️ Zerar',  'blue',   self._confirm_reset),
        ]

        # configure three equal-weight columns
        for i in range(3):
            frame.grid_columnconfigure(i, weight=1, uniform='btns')

        for idx, (text, color, cmd) in enumerate(buttons):
            btn = ctk.CTkButton(frame, text=text, fg_color=color, command=cmd)
            btn.grid(row=0, column=idx, sticky='nsew', padx=4, pady=0)
    # ─── Toggle Decrement Stub ────────────────────────────────────────────────────

    def _toggle_decrement(self):
        """Toggle disabling of the decrement (–) buttons."""
        self.decrement_enabled = not self.decrement_enabled
        state = 'normal' if self.decrement_enabled else 'disabled'
        for btn in self.dec_buttons.values():
            btn.configure(state=state)

    # ─── Reset Confirmation ───────────────────────────────────────────────────────
    def _confirm_reset(self):
        if prompt_notification(
            f"Campo {self.instance} - Zerar",
            "Zerar marcador?",
            icon="❓"
        ):
            for p in (self.casa_file, self.fora_file):
                self._write(p, 0)
            self.update_labels()
