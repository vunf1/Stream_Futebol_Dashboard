import os
import customtkinter as ctk
from tkinter import messagebox
from assets.colors import COLOR_ACTIVE, COLOR_BORDER, COLOR_SUCCESS, COLOR_ERROR
from assets.icons.icons_provider import get_icon
from helpers.helpers import save_teams_to_json
from helpers.notification.toast import prompt_notification, show_message_notification

BUTTON_PAD = dict(padx=5, pady=5)

class ScoreUI:
    def __init__(
        self,
        root: ctk.CTkBaseClass,
        instance: int,
        mongo_client,
        desktop_dir: str,
        field_dir: str,
    ):
        # Setup paths and storage
        self.instance = instance
        self.mongo = mongo_client
        os.makedirs(field_dir, exist_ok=True)
        self.paths = {
            'half': os.path.join(field_dir, 'parte.txt'),
            'home_score': os.path.join(field_dir, 'golo_casa.txt'),
            'away_score': os.path.join(field_dir, 'golo_fora.txt'),
            'home_name': os.path.join(field_dir, 'equipa_casa_nome.txt'),
            'away_name': os.path.join(field_dir, 'equipa_fora_nome.txt'),
            'home_abbr': os.path.join(field_dir, 'equipa_casa_abrev.txt'),
            'away_abbr': os.path.join(field_dir, 'equipa_fora_abrev.txt'),
        }
        self.desktop = desktop_dir
        self.decrement_enabled = True
        self.buttons = {}

        # Load teams and backup
        self._refresh_teams()
        # Read persistent texts
        self._load_texts()

        # Root wrapper frame
        self.parent = ctk.CTkFrame(root, fg_color='transparent')
        self.parent.pack(fill='both', expand=True)
        self.parent.grid_columnconfigure((0, 1), weight=1)

        # Build UI rows
        self._build_half_controls()
        self._build_score_display()
        self._build_score_controls()
        self._build_bottom_controls()

    # -------------- Data Loading and Backup --------------
    def _refresh_teams(self):
        try:
            teams = self.mongo.load_teams()
            save_teams_to_json(self.desktop, teams)
        except Exception as e:
            print(f"❌ Erro ao carregar equipas: {e}")

    def _load_texts(self):
        # Generic reader for name/abbr files
        def read_or_default(path, default):
            try:
                text = open(path, 'r', encoding='utf-8').read().strip()
                return text or default
            except FileNotFoundError:
                return default

        self.home_name = read_or_default(self.paths['home_name'], 'Casa')
        self.away_name = read_or_default(self.paths['away_name'], 'Fora')
        self.home_abbr = read_or_default(self.paths['home_abbr'], 'Casa')
        self.away_abbr = read_or_default(self.paths['away_abbr'], 'Fora')

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

    def _read_half(self):
        try:
            return open(self.paths['half'], 'r', encoding='utf-8').read().strip()
        except Exception:
            return ''

    def _write_half(self, part: str):
        with open(self.paths['half'], 'w', encoding='utf-8') as f:
            f.write(part)

    # -------------- UI Builders --------------
    def _build_half_controls(self):
        # Container for half-time buttons, two equal columns
        frame = ctk.CTkFrame(self.parent, fg_color='transparent')
        frame.grid(row=0, column=0, columnspan=2, sticky='ew', **BUTTON_PAD)
        # Ensure columns expand but buttons stay fixed size
        for col in (0, 1):
            frame.grid_columnconfigure(col, weight=1)

        self.half_buttons = {}
        # Use icons '1parte' and '2parte', sizing button to image
        for idx, icon_name in enumerate(('1parte', '2parte')):
            icon = get_icon(icon_name, 55)
            # Determine image dimensions
            img_width, img_height = icon.cget("size")
            btn = ctk.CTkButton(
                frame,
                image=icon,
                text='',
                fg_color='transparent',
                width=img_width,
                height=img_height,
                hover_color=COLOR_BORDER,
                corner_radius=img_width // 5,
                command=lambda name=icon_name: self._on_half(f"{name[0]}ª Parte")
            )
            # Center button in its expanding cell
            btn.grid(
                row=0,
                column=idx,
                padx=BUTTON_PAD['padx'],
                pady=BUTTON_PAD['pady']
            )
            label = '1ª Parte' if icon_name == '1parte' else '2ª Parte'
            self.half_buttons[label] = btn

        # Apply highlight to the saved half-time selection
        current = self._read_half()
        self._highlight_half(current)

    def _highlight_half(self, selected):
        # Highlight selected button, reset others to transparent
        for part, btn in self.half_buttons.items():
            btn.configure(
                fg_color=COLOR_ACTIVE if part == selected else 'transparent'
            )


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

    def _on_half(self, part: str):
        try:
            self._write_half(part)
            show_message_notification(
                f"✅ Campo {self.instance}",
                f"Metade definida: {part}",
                icon='✅', bg_color=COLOR_SUCCESS
            )
            self._highlight_half(part)
        except Exception as e:
            print(f"❌ Erro ao salvar metade: {e}")

    def _update_labels(self):
        # Reload names/abbrs
        self._load_texts()
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
