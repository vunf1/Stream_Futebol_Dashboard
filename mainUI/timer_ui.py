import json
from typing import Any, Dict
from customtkinter import CTkFrame, CTkImage, CTkButton, CTkEntry, CTkLabel
from assets.colors import (
    COLOR_ACTIVE, COLOR_BORDER, COLOR_ERROR, COLOR_INFO,
    COLOR_PAUSE, COLOR_STOP, COLOR_SUCCESS, COLOR_WARNING,
)
from assets.icons.icons_provider import get_icon
from database.gameinfo import DEFAULT_FIELD_STATE, GameInfoStore, _format_time, _parse_time_to_seconds
from helpers.notification.toast import show_message_notification
from mainUI.score_ui import BUTTON_PAD


class TimerComponent(CTkFrame):
    def __init__(self, parent, instance_number: int):
        super().__init__(
            parent,
            fg_color=("transparent"),
            corner_radius=18,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.instance_number = instance_number
        
        self.configure(width=960, height=180)
        self.pack(side="top", fill="x", padx=12, pady=10)
        self.pack_propagate(False)

        # JSON store (shared gameinfo.json, per-field block)
        self.state = GameInfoStore(instance_number, debug=True)

        # UI refs
        self.max_entry: CTkEntry
        self.timer_entry: CTkEntry
        self.extra_entry: CTkEntry
        self.half_buttons: dict[str, CTkButton] = {}
        self._icon_refs: list[CTkImage] = []

        # runtime
        self.timer_seconds_main = 0
        self.timer_seconds_extra = 0
        self.timer_seconds_max = 0
        self.timer_running = False

        # Build UI, then hydrate from JSON after widgets exist
        self._build_ui()
        self.after(0, self._hydrate_from_json)

    # ---------- Half controls ----------
    def _read_half(self) -> str:
        # Fresh read from disk for accuracy at startup/external edits
        return self.state.read_field_key("half", "1ª Parte")

    def _write_half(self, part: str):
        self.state.set("half", part)

    def _build_half_controls(self, parent, start_col: int = 0):
        ICON_SIZE = 44
        FRAME_PAD = 6
        CORNER = 10
        self.half_buttons = {}

        for idx, (label, icon_name) in enumerate((("1ª Parte", "1half"), ("2ª Parte", "2half"))):
            icon = get_icon(icon_name, ICON_SIZE)
            self._icon_refs.append(icon)
            w, h = icon.cget("size")
            btn = CTkButton(
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
                padx=max(2, BUTTON_PAD["padx"] - 2),
                pady=max(2, BUTTON_PAD["pady"] - 2),
                sticky="nsew",
            )
            self.half_buttons[label] = btn

    def _highlight_half(self, selected: str):
        for part, btn in self.half_buttons.items():
            btn.configure(fg_color=COLOR_ACTIVE if part == selected else "transparent")

    def _on_half(self, part: str):
        self._write_half(part)
        self._highlight_half(part)
        show_message_notification(
            f"✅ Campo {self.instance_number}",
            f"Metade definida: {part}",
            icon="✅",
            bg_color=COLOR_SUCCESS,
        )

    # ---------- UI ----------
    def _build_ui(self):
        self.container = CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=12, pady=8)

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

    def _configure_grid(self, container, cols: int):
        # two rows: row 0 = entries/buttons, row 1 = labels
        container.grid_rowconfigure(0, weight=1, uniform="row", minsize=56)
        container.grid_rowconfigure(1, weight=0, minsize=20)
        for col in range(cols):
            # give each column some minimum width so entries don't collapse
            container.grid_columnconfigure(col, weight=1, uniform="col", minsize=90)


    def _build_save_button(self, col: int = 0):
        img = get_icon("save", 24)
        self._icon_refs.append(img)
        CTkButton(
            self.container,
            image=img,
            text="",
            fg_color="transparent",
            hover_color=COLOR_ACTIVE,
            command=self.save_timers_from_entries,
        ).grid(row=0, column=col, sticky="nsew", padx=5, pady=5)

    def _build_time_entries(self, start_col: int, specs: list[tuple]):
        for idx, (attr, ph, ph_col, text_col, bg) in enumerate(specs):
            col = start_col + idx
            entry = CTkEntry(
                self.container,
                width=140, height=44,           # <- keeps them from shrinking
                font=("Arial Bold", 18),
                justify="center",
                placeholder_text=ph,
                **({"placeholder_text_color": ph_col} if ph_col else {}),
                **({"text_color": text_col} if text_col else {}),
                fg_color=bg,
            )
            setattr(self, attr, entry)
            entry.grid(row=0, column=col, sticky="nsew", padx=6, pady=(6, 2))

            CTkLabel(
                self.container,
                text=ph,
                font=("Arial", 12),
                text_color="#EAEAEA",           # better contrast on dark bg
            ).grid(row=1, column=col, sticky="n", pady=(0, 6))


    def _build_controls(self, start_col: int, specs: list[tuple]):
        ICON_SIZE = 32
        for idx, (key, cmd, col) in enumerate(specs):
            img = get_icon(key, ICON_SIZE)
            self._icon_refs.append(img)
            CTkButton(
                self.container,
                image=img,
                text="",
                fg_color="transparent",
                hover_color=col,
                command=cmd,
            ).grid(row=0, column=start_col + idx, sticky="nsew", padx=5, pady=5)

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

        # ensure half highlight matches JSON
        self._highlight_half(self._read_half())

    def _set_entry_text(self, entry: CTkEntry, text: str) -> None:
        if entry.get() != text:
            entry.delete(0, "end")
            entry.insert(0, text)

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
                    f"❌ Campo {self.instance_number} - Erro",
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
            f"💾 Campo {self.instance_number} - Guardado",
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
            f"⏱️ Campo {self.instance_number} - Iniciado",
            "Cronómetro iniciado.",
            icon="⏳",
            bg_color=COLOR_INFO,
        )

    def _tick(self):
        if not self.timer_running:
            return

        if self.timer_seconds_main < self.timer_seconds_max:
            self.timer_seconds_main += 1
            t = _format_time(self.timer_seconds_main)
            self._set_entry_text(self.timer_entry, t)
            self.state.set("timer", t)

            if self.timer_seconds_main == self.timer_seconds_max:
                show_message_notification(
                    f"⏱️Campo {self.instance_number} - Tempo Extra",
                    "Tempo Extra iniciado.",
                    icon="⏳",
                    bg_color=COLOR_ERROR,
                )
                self.timer_seconds_extra = 0
                te = "00:00"
                self._set_entry_text(self.extra_entry, te)
                self.state.set("extra", te)
        else:
            self.timer_seconds_extra += 1
            te = _format_time(self.timer_seconds_extra)
            self._set_entry_text(self.extra_entry, te)
            self.state.set("extra", te)

        if self.timer_running:
            self.after(1000, self._tick)

    def pause_timer(self):
        if not self.timer_running:
            return
        self.timer_running = False
        show_message_notification(
            f"⏸️Campo {self.instance_number} - Pausado",
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

        show_message_notification(
            f"⏹️ Campo {self.instance_number} - Parado",
            "Cronómetro parado.",
            icon="🛑",
            bg_color=COLOR_STOP,
        )
