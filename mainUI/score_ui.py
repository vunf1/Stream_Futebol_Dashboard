import os
import customtkinter as ctk
from tkinter import messagebox
from assets.colors import COLOR_ACTIVE, COLOR_BORDER, COLOR_SUCCESS, COLOR_ERROR
from assets.icons.icons_provider import get_icon
from helpers.filenames import get_file_path, get_file_value
from helpers.helpers import save_teams_to_json
from helpers.notification.toast import prompt_notification, show_message_notification

BUTTON_PAD = dict(padx=5, pady=5)

class ScoreUI:
    def __init__(
        self,
        root: ctk.CTkBaseClass,
        instance: int,
        mongo_client,
    ):
        # Setup paths and storage
        self.instance = instance
        self.mongo = mongo_client
        self.paths = {
            key: get_file_path(self.instance, key)
            for key in (
                'home_score',
                'away_score',
                'home_name',
                'away_name',
                'home_abbr',
                'away_abbr',
            )
        }
        self.decrement_enabled = True
        self.buttons = {}

        # Read persistent texts

        # Root wrapper frame
        self.parent = ctk.CTkFrame(root, fg_color='transparent')
        self.parent.pack(fill='both', expand=True)
        self.parent.grid_columnconfigure((0, 1), weight=1)

        # Build UI rows
        self._build_score_display()
        self._build_score_controls()
        self._build_bottom_controls()
        
        # Load persisted files
    def _load_persisted_files(self):
        self.home_name = get_file_value(self.instance, 'home_name', 'Casa')
        self.away_name = get_file_value(self.instance, 'away_name', 'Fora')
        self.home_abbr = get_file_value(self.instance, 'home_abbr', 'Casa')
        self.away_abbr = get_file_value(self.instance, 'away_abbr', 'Fora')


    # -------------- Helper IO Methods --------------
    def _read_number(self, path):
        try:
            return max(0, int(open(path, 'r').read().strip()))
        except Exception:
            self._write_number(path, 0)
            return 0

    def _write_number(self, path, value):
        with open(path, 'w') as f:
            f.write(str(value))

    # -------------- UI Builders --------------
    def _build_score_display(self):
        frame = ctk.CTkFrame(self.parent, fg_color='transparent')
        frame.grid(row=1, column=0, columnspan=2, sticky='ew')
        frame.grid_columnconfigure((0,1), weight=1)

        self.home_label = ctk.CTkLabel(frame, text='', font=(None, 24))
        self.away_label = ctk.CTkLabel(frame, text='', font=(None, 24))
        self.home_label.grid(row=0, column=0)
        self.away_label.grid(row=0, column=1)

        self._update_labels()

    def _build_score_controls(self):
        frame = ctk.CTkFrame(self.parent, fg_color='transparent')
        frame.grid(row=2, column=0, columnspan=2, sticky='ew', **BUTTON_PAD)
        frame.grid_columnconfigure((0,1,2,3), weight=1)

        # Create plus/minus buttons for each side
        for i, side in enumerate(('home', 'away')):
            row_offset = 0
            icon_plus = get_icon('plusone', 24)
            icon_minus = get_icon('minusone', 24)
            score_path = self.paths[f'{side}_score']
            abbr = getattr(self, f'{side}_abbr')
            label = getattr(self, f'{side}_label')

            btn_plus = ctk.CTkButton(
                frame, image=icon_plus, text='', fg_color='transparent',
                command=lambda s=side: self._change_score(s, 1)
            )
            btn_minus = ctk.CTkButton(
                frame, image=icon_minus, text='', fg_color='transparent',
                command=lambda s=side: self._change_score(s, -1)
            )
            btn_plus.grid(row=row_offset, column=i*2, sticky='e', padx=5)
            btn_minus.grid(row=row_offset, column=i*2+1, sticky='w', padx=5)
            # Store decrement for toggle
            self.buttons[f'{side}_minus'] = btn_minus

    def _build_bottom_controls(self):
        frame = ctk.CTkFrame(self.parent, fg_color='transparent')
        frame.grid(row=3, column=0, columnspan=2, sticky='ew', padx=10, pady=10)
        # Configure three equally expanding columns
        for col in (0, 1, 2):
            frame.grid_columnconfigure(col, weight=1)

        # (icon_name, command, color)
        specs = [
            ('swap_score', self._swap_scores),
            ('lock',       self._toggle_decrement),
            ('score00',    self._confirm_reset),
        ]
        for idx, (icon_name, cmd) in enumerate(specs):
            icon = get_icon(icon_name, 70)
            btn = ctk.CTkButton(
                frame,
                image=icon,
                text='',
                fg_color='transparent',
                command=cmd
            )
            btn.grid(row=0, column=idx, sticky='nsew', padx=5, pady=5)
            # Preserve swap/reset button references
            if icon_name == 'swap_score':
                self.buttons['swap'] = btn
            elif icon_name == 'score00':
                self.buttons['reset'] = btn
    # -------------- UI Actions --------------
    def _toggle_decrement(self):
        self.decrement_enabled = not self.decrement_enabled
        state = 'normal' if self.decrement_enabled else 'disabled'
        for btn in self.buttons.values():
            btn.configure(state=state)

    def _update_labels(self):
        self._load_persisted_files()
        # Reload names/abbrs
        home_score = self._read_number(self.paths['home_score'])
        away_score = self._read_number(self.paths['away_score'])
        self.home_label.configure(text=f"{self.home_abbr}: {home_score}")
        self.away_label.configure(text=f"{self.away_abbr}: {away_score}")

    def _change_score(self, side: str, delta: int):
        path = self.paths[f'{side}_score']
        new_val = max(0, self._read_number(path) + delta)
        self._write_number(path, new_val)
        label = getattr(self, f'{side}_label')
        abbr = getattr(self, f'{side}_abbr')
        label.configure(text=f"{abbr}: {new_val}")

    def _swap_scores(self):
        try:
            h = self._read_number(self.paths['home_score'])
            a = self._read_number(self.paths['away_score'])
            self._write_number(self.paths['home_score'], a)
            self._write_number(self.paths['away_score'], h)
            self._update_labels()
            show_message_notification(
                f"✅ Campo {self.instance}",
                f"Casa←{a} | Fora←{h}", icon='🔄', bg_color=COLOR_SUCCESS
            )
        except Exception as e:
            print(f"❌ Erro ao trocar placares: {e}")



    def _confirm_reset(self):
        if prompt_notification(
            f"Campo {self.instance} - Zerar",
            "Zerar marcador?",
            icon='❓'
        ):
            for key in ('home_score', 'away_score'):
                self._write_number(self.paths[key], 0)
            self._update_labels()
