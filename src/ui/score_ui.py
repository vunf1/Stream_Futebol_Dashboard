import customtkinter as ctk
from src.config.settings import AppConfig

# Color constants from AppConfig - using AppConfig directly
from src.ui import get_icon, get_icon_path
from src.core import GameInfoStore, DEFAULT_FIELD_STATE
from src.notification import show_message_notification, prompt_notification
import threading
import time

BUTTON_PAD = dict(padx=5, pady=5)

class ScoreUI:
    """
    Score control backed by GameInfoStore (gameinfo.json → field_<instance>).
    Shows 'ABBR: score' for home/away, with +/−, swap, lock, and reset.
    """
    def __init__(self, root: ctk.CTkBaseClass, instance: int, mongo_client, json: GameInfoStore):
        self.instance = instance
        self.mongo = mongo_client
        self.store = json
        self.decrement_enabled = True

        self.buttons: dict[str, ctk.CTkButton] = {}
        self._icon_refs = []
        
        # Pre-load lock icons to prevent flickering
        self.lock_icon = get_icon('lock', 70)
        self.unlock_icon = get_icon('unlock', 70)
        self._icon_refs += [self.lock_icon, self.unlock_icon]
        
        # Get theme colors for hover effects
        self.theme_bg = ctk.ThemeManager.theme["CTkFrame"]["fg_color"]
        
        # Performance optimizations
        self._update_pending = False
        self._update_timer = None
        self._last_home_score = None
        self._last_away_score = None
        self._last_home_abbr = None
        self._last_away_abbr = None

        # Root wrapper
        self.parent = ctk.CTkFrame(root, fg_color='transparent')
        self.parent.pack(fill='both', expand=True)
        self.parent.grid_columnconfigure((0, 1), weight=1)

        # Defer UI building for smooth loading
        self.parent.after(50, self._deferred_build_ui)  # Faster (was 100ms, now 50ms)

    def _deferred_build_ui(self):
        """Deferred UI building to ensure smooth loading"""
        try:
            # Build UI components
            self._build_score_display()
            self._build_score_controls()
            self._build_bottom_controls()
            
            # Hydrate UI from JSON after widgets exist
            self.parent.after(25, self._hydrate_from_json)  # Faster (was 50ms, now 25ms)
            
        except Exception as e:
            print(f"Error building ScoreUI: {e}")
            # Fallback: build UI immediately if there's an error
            self._build_score_display()
            self._build_score_controls()
            self._build_bottom_controls()
            self._hydrate_from_json()

    # -------------- Hydration / labels -------------- 
    def _hydrate_from_json(self):
        self._update_labels()

    def _schedule_label_update(self):
        """Debounce label updates to avoid excessive refreshes"""
        if self._update_pending:
            return
        
        self._update_pending = True
        
        def delayed_update():
            self._update_labels()
            self._update_pending = False
        
        # Cancel existing timer if any
        if self._update_timer:
            self.parent.after_cancel(self._update_timer)
        
        # Schedule update after 50ms delay
        self._update_timer = self.parent.after(50, delayed_update)

    def _update_labels(self):
        # Read from JSON (cached get is fine here)
        home_abbr = self.store.get('home_abbr', DEFAULT_FIELD_STATE['home_abbr']) or 'Casa'
        away_abbr = self.store.get('away_abbr', DEFAULT_FIELD_STATE['away_abbr']) or 'Fora'
        home_score = int(self.store.get('home_score', 0) or 0)
        away_score = int(self.store.get('away_score', 0) or 0)

        # Only update if values actually changed
        if (home_abbr != self._last_home_abbr or home_score != self._last_home_score):
            self.home_label.configure(text=f"{home_abbr}: {home_score}")
            self._last_home_abbr = home_abbr
            self._last_home_score = home_score

        if (away_abbr != self._last_away_abbr or away_score != self._last_away_score):
            self.away_label.configure(text=f"{away_abbr}: {away_score}")
            self._last_away_abbr = away_abbr
            self._last_away_score = away_score

    # -------------- UI Builders --------------
    def _build_score_display(self):
        frame = ctk.CTkFrame(self.parent, fg_color='transparent')
        frame.grid(row=1, column=0, columnspan=2, sticky='ew')
        frame.grid_columnconfigure((0, 1), weight=1)

        self.home_label = ctk.CTkLabel(frame, text='', font=(None, 24))
        self.away_label = ctk.CTkLabel(frame, text='', font=(None, 24))
        self.home_label.grid(row=0, column=0)
        self.away_label.grid(row=0, column=1)

    def _build_score_controls(self):
        frame = ctk.CTkFrame(self.parent, fg_color='transparent')
        frame.grid(row=2, column=0, columnspan=2, sticky='ew', **BUTTON_PAD)
        frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        for i, side in enumerate(('home', 'away')):
            icon_plus = get_icon('plusone', 24)
            icon_minus = get_icon('minusone', 24)
            self._icon_refs += [icon_plus, icon_minus]

            btn_plus = ctk.CTkButton(
                frame, image=icon_plus, text='', fg_color='transparent',
                hover_color=('gray75', 'gray25'),
                command=lambda s=side: self._change_score(s, +1)
            )
            btn_minus = ctk.CTkButton(
                frame, image=icon_minus, text='', fg_color='transparent',
                hover_color=('gray75', 'gray25'),
                command=lambda s=side: self._change_score(s, -1)
            )
            btn_plus.grid(row=0, column=i*2,   sticky='e', padx=5)
            btn_minus.grid(row=0, column=i*2+1, sticky='w', padx=5)

            # Track only minus buttons for lock toggle
            self.buttons[f'{side}_minus'] = btn_minus

    def _build_bottom_controls(self):
        frame = ctk.CTkFrame(self.parent, fg_color='transparent')
        frame.grid(row=3, column=0, columnspan=2, sticky='ew', padx=10, pady=10)
        for col in (0, 1, 2):
            frame.grid_columnconfigure(col, weight=1)

        specs = [
            ('swap_score', self._swap_scores),
            ('lock',       self._toggle_decrement),
            ('score00',    self._confirm_reset),
        ]
        for idx, (icon_key, cmd) in enumerate(specs):
            if icon_key == 'lock':
                # Use pre-loaded lock icon
                icon = self.unlock_icon if self.decrement_enabled else self.lock_icon
                # Lock button: use theme background color for hover
                btn = ctk.CTkButton(
                    frame, image=icon, text='', fg_color='transparent', 
                    hover_color=self.theme_bg, command=cmd
                )
            else:
                icon = get_icon(icon_key, 70)
                self._icon_refs.append(icon)
                # Other buttons: standard hover color
                btn = ctk.CTkButton(
                    frame, image=icon, text='', fg_color='transparent',
                    hover_color=('gray75', 'gray25'), command=cmd
                )
                
            btn.grid(row=0, column=idx, sticky='nsew', padx=5, pady=5)

            if icon_key == 'lock':
                self.buttons['lock'] = btn
            elif icon_key == 'swap_score':
                self.buttons['swap'] = btn
            elif icon_key == 'score00':
                self.buttons['reset'] = btn

    # -------------- Actions --------------
    def _toggle_decrement(self):
        self.decrement_enabled = not self.decrement_enabled
        
        # Batch all UI updates to prevent flickering
        def update_ui():
            # Update minus buttons appearance instead of state to prevent flickering
            for side in ('home', 'away'):
                btn = self.buttons[f'{side}_minus']
                if self.decrement_enabled:
                    # Enable: restore normal appearance with consistent hover color
                    btn.configure(fg_color='transparent', hover_color=('gray75', 'gray25'))
                else:
                    # Disable: visual indication without state change
                    btn.configure(fg_color=('gray90', 'gray30'), hover_color=('gray90', 'gray30'))
            
            # Update lock icon
            lock_btn = self.buttons['lock']
            new_icon = self.unlock_icon if self.decrement_enabled else self.lock_icon
            lock_btn.configure(image=new_icon)
        
        # Execute UI updates in a single batch
        self.parent.after_idle(update_ui)
        
        # Show notification after UI updates with a small delay
        def show_notification():
            show_message_notification(
                f"🔒Campo {self.instance}",
                f"Lock : {not self.decrement_enabled}",
                icon='🔒' if not self.decrement_enabled else '🔓',
                bg_color=AppConfig.COLOR_SUCCESS if self.decrement_enabled else AppConfig.COLOR_ERROR
            )
        
        # Delay notification to prevent interference with UI updates
        self.parent.after(100, show_notification)

    def _change_score(self, side: str, delta: int):
        # Check the flag instead of button state
        if delta < 0 and not self.decrement_enabled:
            return

        key = f'{side}_score'
        current = int(self.store.get(key, 0) or 0)
        new_val = max(0, current + delta)

        # Persist via JSON; UI will reflect immediately
        if self.store.set(key, new_val):
            # Use debounced update for better performance
            self._schedule_label_update()

    def _swap_scores(self):
        try:
            h = int(self.store.get('home_score', 0) or 0)
            a = int(self.store.get('away_score', 0) or 0)
            if self.store.update({'home_score': a, 'away_score': h}):
                self._update_labels()
                show_message_notification(
                    f"✅ Campo {self.instance}",
                    f"Casa←{a} | Fora←{h}", icon='🔄', bg_color=AppConfig.COLOR_SUCCESS
                )
        except Exception as e:
            print(f"❌ Erro ao trocar placares: {e}")

    def _confirm_reset(self):
        if prompt_notification(
            f"Campo {self.instance} - Zerar",
            "Zerar marcador?",
            icon='❓'
        ):
            if self.store.update({'home_score': 0, 'away_score': 0}):
                self._update_labels()
