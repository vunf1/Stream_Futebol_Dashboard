import customtkinter as ctk
from typing import Any, Dict, Optional
from src.ui.colors import (
    COLOR_ACTIVE, COLOR_BORDER, COLOR_SUCCESS, COLOR_ERROR,
    COLOR_PAUSE, COLOR_STOP, COLOR_WARNING, COLOR_INFO,
)
from src.ui import get_icon
from src.core import GameInfoStore, DEFAULT_FIELD_STATE
from src.notification import show_message_notification
from src.core import get_config
from src.performance import time_ui_update, time_json_operation
from src.ui import add_footer_label

# Constants
BUTTON_PAD = dict(padx=5, pady=5)

# Helper functions
def _parse_time_to_seconds(time_str: str) -> int:
    """Parse time string (MM:SS) to seconds"""
    try:
        if ':' in time_str:
            minutes, seconds = map(int, time_str.split(':'))
            return minutes * 60 + seconds
        else:
            return int(time_str)
    except (ValueError, TypeError):
        return 0

def _format_time(seconds: int) -> str:
    """Format seconds to MM:SS string"""
    if seconds < 0:
        seconds = 0
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


class TimerComponent(ctk.CTkFrame):
    def __init__(self, parent, instance_number: int, json: GameInfoStore):
        super().__init__(
            parent,
            fg_color=("transparent"),
            corner_radius=18,
            border_width=0,
            border_color=COLOR_BORDER,
        )
        self.instance_number = instance_number
        
        
        self.configure(width=960, height=80)
        self.pack(side="top", fill="x", padx=8, pady=5)
        self.pack_propagate(False)

        # JSON store (shared gameinfo.json, per-field block)
        self.state = json

        # Performance configuration
        self.ui_update_debounce = get_config("ui_update_debounce", 50)
        self.timer_update_interval = get_config("timer_update_interval", 1000)
        
        # UI refs
        self.max_entry: ctk.CTkEntry
        self.timer_entry: ctk.CTkEntry
        self.extra_entry: ctk.CTkEntry
        self.half_buttons: dict[str, ctk.CTkButton] = {}
        
        # Pre-load all icons for better performance
        self._icons = self._preload_icons()
        
        # runtime
        self.timer_seconds_main = 0
        self.timer_seconds_extra = 0
        self.timer_seconds_max = 0
        self.timer_running = False
        
        # Performance optimization: debounced updates
        self._update_pending = False
        self._update_timer = None
        self._last_values = {"timer": "", "extra": ""}
        


        # Build UI, then hydrate from JSON after widgets exist
        self._build_ui()
        self.after(0, self._hydrate_from_json)

    def _preload_icons(self) -> Dict[str, ctk.CTkImage]:
        """Pre-load all icons for better performance"""
        icons = {}
        icon_specs = [
            ("1half", 44), ("2half", 44), ("save", 24),
            ("play", 32), ("pause", 32), ("stop", 32)
        ]
        
        for name, size in icon_specs:
            try:
                icons[name] = get_icon(name, size)
            except Exception as e:
                print(f"Warning: Could not load icon {name}: {e}")
        
        return icons

    # ---------- Half controls ----------
    def _read_half(self) -> str:
        # Fresh read from disk for accuracy at startup/external edits
        return self.state.read_field_key("half", "1ª Parte")

    def _write_half(self, part: str):
        self.state.set("half", part)

    def _build_half_controls(self, parent, start_col: int = 0):
        ICON_SIZE = 44
        FRAME_PAD = 4
        CORNER = 8
        self.half_buttons = {}

        for idx, (label, icon_name) in enumerate((("1ª Parte", "1half"), ("2ª Parte", "2half"))):
            icon = self._icons.get(icon_name)
            if not icon:
                continue
                
            w, h = icon.cget("size")
            btn = ctk.CTkButton(
                parent,
                image=icon,
                text="",
                width=w + FRAME_PAD * 2,
                height=h + FRAME_PAD * 2,
                fg_color="transparent",
                hover_color=COLOR_BORDER,
                corner_radius=CORNER,
                command=lambda l=label: self._on_half(l),
            )
            btn.grid(
                row=0,
                column=start_col + idx,
                padx=max(1, BUTTON_PAD["padx"] - 3),  
                pady=max(1, BUTTON_PAD["pady"] - 3),  
                sticky="nsew",
            )
            self.half_buttons[label] = btn

        # Add label below 1half button
        ctk.CTkLabel(
            parent,
            text=f"Campo - {self.instance_number}",
            font=("Arial", 10),
            text_color="#EAEAEA",
        ).grid(row=1, column=start_col, sticky="n", pady=(0, 4))

    def _highlight_half(self, selected: str):
        for part, btn in self.half_buttons.items():
            btn.configure(fg_color=COLOR_ACTIVE if part == selected else "transparent")

    def _on_half(self, part: str):
        self._write_half(part)
        self._highlight_half(part)
        show_message_notification(
            f"Campo - {self.instance_number}",
            f"Metade definida: {part}",
            icon="✅",
            bg_color=COLOR_SUCCESS,
        )

    # ---------- UI ----------
    def _build_ui(self):
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=8, pady=4)  

        time_fields = [
            ("max_entry",   "Máximo", None,    "black", "grey"),
            ("timer_entry", "Normal", None,    None,    "blue"),
            ("extra_entry", "Extra",  None,    None,    "red"),
        ]
        controls = [
            ("play",  self.start_timer, COLOR_INFO),
            ("pause", self.pause_timer, COLOR_WARNING),
            ("stop",  self.reset_timer, COLOR_ERROR),
        ]

        # layout: [half1][half2] [save] [max][timer][extra] [play][pause][stop]
        HALF_COLS = 2
        SAVE_COL  = 2
        TIME_START_COL = 3
        CTRL_START_COL = TIME_START_COL + len(time_fields)
        total_cols = HALF_COLS + 1 + len(time_fields) + len(controls)

        self._configure_grid(self.container, cols=total_cols)
        self._build_half_controls(self.container, start_col=0)
        self._build_save_button(col=SAVE_COL)
        self._build_time_entries(start_col=TIME_START_COL, specs=time_fields)
        self._build_controls(start_col=CTRL_START_COL, specs=controls)
        
        # Add footer
        add_footer_label(self, f"Campo {self.instance_number}")

    def _configure_grid(self, container, cols: int):
        # two rows: row 0 = entries/buttons, row 1 = labels
        container.grid_rowconfigure(0, weight=1, uniform="row", minsize=48) 
        container.grid_rowconfigure(1, weight=0, minsize=16) 
        for col in range(cols):
            # give each column some minimum width so entries don't collapse
            container.grid_columnconfigure(col, weight=1, uniform="col", minsize=80)

    def _build_save_button(self, col: int = 0):
        img = self._icons.get("save")
        if img:
            ctk.CTkButton(
                self.container,
                image=img,
                text="",
                fg_color="transparent",
                hover_color=COLOR_ACTIVE,
                command=self.save_timers_from_entries,
            ).grid(row=0, column=col, sticky="nsew", padx=3, pady=3)

    def _build_time_entries(self, start_col: int, specs: list[tuple]):
        for idx, (attr, ph, ph_col, text_col, bg) in enumerate(specs):
            col = start_col + idx
            entry = ctk.CTkEntry(
                self.container,
                width=120, height=36,
                font=("Arial Bold", 16),
                justify="center",
                placeholder_text=ph,
                **({"placeholder_text_color": ph_col} if ph_col else {}),
                **({"text_color": text_col} if text_col else {}),
                fg_color=bg,
            )
            setattr(self, attr, entry)
            entry.grid(row=0, column=col, sticky="nsew", padx=4, pady=(4, 1))

            ctk.CTkLabel(
                self.container,
                text=ph,
                font=("Arial", 10),
                text_color="#EAEAEA",           # better contrast on dark bg
            ).grid(row=1, column=col, sticky="n", pady=(0, 4))

    def _build_controls(self, start_col: int, specs: list[tuple]):
        for idx, (key, cmd, col) in enumerate(specs):
            img = self._icons.get(key)
            if img:
                ctk.CTkButton(
                    self.container,
                    image=img,
                    text="",
                    fg_color="transparent",
                    hover_color=col,
                    command=cmd,
                ).grid(row=0, column=start_col + idx, sticky="nsew", padx=3, pady=3)
                
                # Add "X" label below stop button
                if key == "stop":
                    close_label = ctk.CTkLabel(
                        self.container,
                        text="X",
                        font=("Arial", 10),
                        text_color="#EAEAEA",
                        cursor="hand2",  # Show hand cursor on hover
                    )
                    close_label.grid(row=1, column=start_col + idx, sticky="ne", pady=(0, 4), padx=(0, 10))  # Align to right with right padding
                    
                    # Make the label clickable to close the component
                    close_label.bind("<Button-1>", lambda e: self._close_component())
                    
                    # Add hover effect
                    def on_enter(e):
                        close_label.configure(text_color="#FF6B6B")  # Red color on hover
                    
                    def on_leave(e):
                        close_label.configure(text_color="#EAEAEA")  # Original color
                    
                    close_label.bind("<Enter>", on_enter)
                    close_label.bind("<Leave>", on_leave)

    # ---------- Hydrate / save (JSON) ----------
    def _hydrate_from_json(self):
        # Fresh read from disk so launches always mirror file content
        max_txt   = self.state.read_field_key("max",   DEFAULT_FIELD_STATE["max"])
        timer_txt = self.state.read_field_key("timer", DEFAULT_FIELD_STATE["timer"])
        extra_txt = self.state.read_field_key("extra", DEFAULT_FIELD_STATE["extra"])
        
        print(f"[TimerComponent:{self.instance_number}] loaded from JSON → "
            f"max={max_txt} timer={timer_txt} extra={extra_txt} ")
        self.timer_seconds_max   = _parse_time_to_seconds(max_txt)   or 0
        self.timer_seconds_main  = _parse_time_to_seconds(timer_txt) or 0
        self.timer_seconds_extra = _parse_time_to_seconds(extra_txt) or 0

        self._set_entry_text(self.max_entry,   _format_time(self.timer_seconds_max))
        self._set_entry_text(self.timer_entry, _format_time(self.timer_seconds_main))
        self._set_entry_text(self.extra_entry, _format_time(self.timer_seconds_extra))

        # Update last values for change detection
        self._last_values["timer"] = _format_time(self.timer_seconds_main)
        self._last_values["extra"] = _format_time(self.timer_seconds_extra)

        # ensure half highlight matches JSON
        self._highlight_half(self._read_half())

    def _set_entry_text(self, entry: ctk.CTkEntry, text: str) -> None:
        """Optimized entry text setting - only update if different"""
        if entry.get() != text:
            entry.delete(0, "end")
            entry.insert(0, text)

    def _schedule_ui_update(self):
        """Debounced UI update to reduce unnecessary refreshes"""
        if self._update_pending:
            return
        
        self._update_pending = True
        self._update_timer = self.after(self.ui_update_debounce, self._perform_ui_update)

    @time_ui_update
    def _perform_ui_update(self):
        """Perform the actual UI update"""
        self._update_pending = False
        self._update_timer = None
        
        # Update entries only if values changed
        timer_text = _format_time(self.timer_seconds_main)
        extra_text = _format_time(self.timer_seconds_extra)
        
        if timer_text != self._last_values["timer"]:
            self._set_entry_text(self.timer_entry, timer_text)
            self._last_values["timer"] = timer_text
        
        if extra_text != self._last_values["extra"]:
            self._set_entry_text(self.extra_entry, extra_text)
            self._last_values["extra"] = extra_text

    @time_json_operation
    def save_timers_from_entries(self):
        fields = [
            ("Tempo Máximo",    "max_entry",   "max"),
            ("Tempo Principal", "timer_entry", "timer"),
            ("Tempo Extra",     "extra_entry", "extra"),
        ]

        patch: Dict[str, str] = {}
        for label, entry_attr, json_key in fields:
            entry = getattr(self, entry_attr)
            text = entry.get().strip()
            secs = _parse_time_to_seconds(text)
            if secs is None:
                show_message_notification(
                    f"Campo - {self.instance_number} - Erro",
                    f"{label}: formato inválido. Usa 'MM:SS' ou 'MMM:SS' (segundos 00–59).",
                    icon="❌",
                    bg_color=COLOR_ERROR,
                )
                return
            if json_key == "max":
                self.timer_seconds_max = secs
            elif json_key == "timer":
                self.timer_seconds_main = secs
            else:
                self.timer_seconds_extra = secs
            patch[json_key] = _format_time(secs)

        self.state.update(patch, persist=True)

        show_message_notification(
            f"Campo - {self.instance_number} - Guardado",
            "Tempos guardados.",
            icon="💾",
            bg_color=COLOR_SUCCESS,
        )

    # ---------- Run loop ----------
    def start_timer(self):
        if self.timer_running:
            return

        self.timer_seconds_max   = _parse_time_to_seconds(self.max_entry.get())   or 0
        self.timer_seconds_main  = _parse_time_to_seconds(self.timer_entry.get()) or 0
        self.timer_seconds_extra = _parse_time_to_seconds(self.extra_entry.get()) or 0

        # Sync immediate values to JSON so overlay sees them right away
        self.state.update({
            "max":   _format_time(self.timer_seconds_max),
            "timer": _format_time(self.timer_seconds_main),
            "extra": _format_time(self.timer_seconds_extra),
        }, persist=True)

        self.timer_running = True
        self._tick()
        show_message_notification(
            f"Campo - {self.instance_number} - Iniciado",
            "Cronómetro iniciado.",
            icon="⏳",
            bg_color=COLOR_INFO,
        )

    @time_ui_update
    def _tick(self):
        """Optimized timer tick with batched updates"""
        if not self.timer_running:
            return

        # Batch updates for better performance
        updates = {}
        needs_ui_update = False
        
        if self.timer_seconds_main < self.timer_seconds_max:
            self.timer_seconds_main += 1
            updates["timer"] = _format_time(self.timer_seconds_main)
            needs_ui_update = True

            if self.timer_seconds_main == self.timer_seconds_max:
                show_message_notification(
                    f"Campo - {self.instance_number} - Tempo Extra",
                    "Tempo Extra iniciado.",
                    icon="⏳",
                    bg_color=COLOR_ERROR,
                )
                self.timer_seconds_extra = 0
                updates["extra"] = "00:00"
                needs_ui_update = True
        else:
            self.timer_seconds_extra += 1
            updates["extra"] = _format_time(self.timer_seconds_extra)
            needs_ui_update = True

        # Batch persist updates
        if updates:
            self.state.update(updates, persist=True)

        # Schedule UI update if needed
        if needs_ui_update:
            self._schedule_ui_update()

        if self.timer_running:
            self.after(self.timer_update_interval, self._tick)

    def pause_timer(self):
        if not self.timer_running:
            return
        self.timer_running = False
        show_message_notification(
            f"Campo - {self.instance_number} - Pausado",
            "Cronómetro pausado.",
            icon="⏸",
            bg_color=COLOR_PAUSE,
        )

    def reset_timer(self):
        self.timer_running = False
        self.timer_seconds_main = 0
        self.timer_seconds_extra = 0

        zero = "00:00"
        self._set_entry_text(self.timer_entry, zero)
        self._set_entry_text(self.extra_entry, zero)
        self.state.update({"timer": zero, "extra": zero}, persist=True)

        # Update last values
        self._last_values["timer"] = zero
        self._last_values["extra"] = zero

        show_message_notification(
            f"Campo - {self.instance_number} - Parado",
            "Cronómetro parado.",
            icon="🛑",
            bg_color=COLOR_STOP,
        )

    def _close_component(self):
        """Close the timer component and its parent window"""
        # Find the parent window and close it
        current = self
        while hasattr(current, 'winfo_toplevel'):
            current = current.winfo_toplevel()
            if hasattr(current, 'destroy'):
                current.destroy()
                break

    def destroy(self):
        """Cleanup when component is destroyed"""
        if self._update_timer:
            self.after_cancel(self._update_timer)
        super().destroy()
