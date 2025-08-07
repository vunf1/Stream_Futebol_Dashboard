import os
import re
import sys
from customtkinter import CTk, CTkFrame, CTkImage, CTkButton, CTkEntry, CTkLabel
from assets.colors import (
    COLOR_ACTIVE,
    COLOR_ERROR,
    COLOR_INFO,
    COLOR_PAUSE,
    COLOR_STOP,
    COLOR_SUCCESS,
    COLOR_WARNING,
)
from assets.icons.icons_provider import get_icon
from helpers.notification.toast import show_message_notification

# Padrão para validar tempo MM:SS ou MMM:SS (>=100 minutos)
TIME_PATTERN = re.compile(r"^(?:\d{2}|[1-9]\d{2,}):\d{2}$")

class TimerComponent(CTkFrame):
    def __init__(self, parent, field_folder, instance_number):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.field_folder = field_folder
        self.instance_number = instance_number

        # Declarações para o type checker
        self.max_entry: CTkEntry
        self.timer_entry: CTkEntry
        self.extra_entry: CTkEntry

        # Contadores internos
        self.timer_seconds_main = 0
        self.timer_seconds_extra = 0
        self.timer_seconds_max = 0
        self.timer_running = False

        # Persistência e UI
        self.pack(padx=10, pady=10, fill="x")
        self._icon_refs: list[CTkImage] = []
        self._load_persisted_time()
        self._build_ui()

    @staticmethod
    def _time_fields():
        # (entry_attr, filename, label, seconds_attr)
        return [
            ("max_entry",   "max.txt",   "Tempo Máximo",    "timer_seconds_max"),
            ("timer_entry", "timer.txt", "Tempo Principal", "timer_seconds_main"),
            ("extra_entry", "extra.txt", "Tempo Extra",     "timer_seconds_extra"),
        ]

    def _load_persisted_time(self):
        os.makedirs(self.field_folder, exist_ok=True)
        for entry_attr, filename, _, seconds_attr in self._time_fields():
            path = os.path.join(self.field_folder, filename)
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    f.write("00:00")
                setattr(self, seconds_attr, 0)
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                mins, secs = map(int, text.split(":"))
                setattr(self, seconds_attr, mins * 60 + secs)
            except Exception:
                setattr(self, seconds_attr, 0)

    def _build_ui(self):
        self.pack(fill="both", expand=True)
        self.container = CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        # compute counts
        num_save = 1
        time_fields = [
            ("max_entry",   "Máximo", None,    "black", "grey", "timer_seconds_max"),
            ("timer_entry", "Normal", None,    None,    "blue", "timer_seconds_main"),
            ("extra_entry", "Extra",  None,    None,    "red",  "timer_seconds_extra"),
        ]
        control_specs = [
            ("play",  self.start_timer,   COLOR_INFO),
            ("pause", self.pause_timer,   COLOR_WARNING),
            ("stop",  self.reset_timer,   COLOR_ERROR),
        ]
        # total columns, including save button and controls
        total_cols = num_save + len(time_fields) + len(control_specs)

        # configure grid uniformly
        self._configure_grid(self.container, cols=total_cols)

        # save button at col 0
        self._build_save_button()

        # time entries at cols 1..N
        self._build_time_entries(start_col=1, specs=time_fields)

        # controls at cols (1 + len(time_fields)) .. end
        self._build_controls(start_col=1 + len(time_fields), specs=control_specs)

    def _configure_grid(self, container, cols: int):
        container.grid_rowconfigure(0, weight=1, uniform="row")
        for col in range(cols):
            container.grid_columnconfigure(col, weight=1, uniform="col")

    def _build_save_button(self):
        img = get_icon("save", 24)
        self._icon_refs.append(img)
        btn = CTkButton(
            self.container,
            image=img,
            text="",
            fg_color="transparent",
            hover_color=COLOR_ACTIVE,
            command=self.save_timers_from_entries
        )
        btn.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    def _build_time_entries(self, start_col: int, specs: list):
        """
        Para cada spec, cria o Entry na row 0 e um Label com o nome (ph)
        logo abaixo, na row 1, mesmo column.
        """
        for idx, (attr, ph, ph_col, text_col, fg, sec_attr) in enumerate(specs):
            col = start_col + idx

            # 1) Entry
            entry = CTkEntry(
                self.container,
                font=("Arial Bold", 18),
                justify="center",
                placeholder_text=ph,
                **({"placeholder_text_color": ph_col} if ph_col else {}),
                **({"text_color": text_col} if text_col else {}),
                fg_color=fg,
            )
            setattr(self, attr, entry)
            curr = getattr(self, sec_attr, 0)
            entry.insert(0, self._format_time(curr))
            entry.grid(row=0, column=col, sticky="nsew", padx=5, pady=(5, 2))

            # 2) Label abaixo
            label = CTkLabel(
                self.container,
                text=ph,
                font=("Arial Bold", 12),
                text_color=text_col or "black"
            )
            # mesmo column, row 1
            label.grid(row=1, column=col, sticky="n", pady=(0, 5))


    def _build_controls(self, start_col: int, specs: list):
        ICON_SIZE = 32
        for idx, (key, cmd, col) in enumerate(specs):
            column = start_col + idx
            img = get_icon(key, ICON_SIZE)
            self._icon_refs.append(img)
            btn = CTkButton(
                self.container,
                image=img,
                text="",
                fg_color="transparent",
                hover_color=col,
                command=cmd
            )
            btn.grid(row=0, column=column, sticky="nsew", padx=5, pady=5)

    def _format_time(self, total_seconds: int) -> str:
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes:02}:{seconds:02}"

    def save_timers_from_entries(self):
        for entry_attr, filename, label, _ in self._time_fields():
            entry = getattr(self, entry_attr)
            text = entry.get().strip()
            if not TIME_PATTERN.match(text):
                show_message_notification(
                    f"❌ Campo {self.instance_number} - Erro",
                    f"{label}: formato inválido. Usa 'MM:SS' ou 'MMM:SS'.",
                    icon="❌", bg_color=COLOR_ERROR
                )
                return
            mins, secs = map(int, text.split(":"))
            if len(text.split(":")) == 3 and mins < 100:
                show_message_notification(
                    f"❌ Campo {self.instance_number} - Erro",
                    f"{label}: minutos 3 dígitos devem ser ≥100.",
                    icon="❌", bg_color=COLOR_ERROR
                )
                return
            if not (0 <= secs < 60):
                show_message_notification(
                    f"❌ Campo {self.instance_number} - Erro",
                    f"{label}: segundos fora do intervalo.",
                    icon="❌", bg_color=COLOR_ERROR
                )
                return
            total = mins * 60 + secs
            setattr(self, f"timer_seconds_{entry_attr.replace('_entry','')}", total)
            path = os.path.join(self.field_folder, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"{mins:02}:{secs:02}")
            show_message_notification(
                f"💾 Campo {self.instance_number} - Guardado",
                f"{label} guardado.",
                icon="💾", bg_color=COLOR_SUCCESS
            )

    def start_timer(self):
        if self.timer_running:
            return
        # lê valores atuais
        try:
            txt_main = self.timer_entry.get().strip()
            mn, sc = map(int, txt_main.split(":"))
            self.timer_seconds_main = mn*60 + sc
        except Exception:
            self.timer_seconds_main = 0
        try:
            txt_extra = self.extra_entry.get().strip()
            me, se = map(int, txt_extra.split(":"))
            self.timer_seconds_extra = me*60 + se
        except Exception:
            self.timer_seconds_extra = 0
        self.timer_running = True
        self.update_timer()
        show_message_notification(
            f"⏱️ Campo {self.instance_number} - Iniciado",
            "Cronómetro iniciado.", icon="⏳", bg_color=COLOR_INFO
        )

    def update_timer(self):
        if not self.timer_running:
            return
        if self.timer_seconds_main < self.timer_seconds_max:
            self.timer_seconds_main += 1
            tx = self._format_time(self.timer_seconds_main)
            self.timer_entry.delete(0, "end")
            self.timer_entry.insert(0, tx)
            with open(os.path.join(self.field_folder, "timer.txt"), "w", encoding="utf-8") as f:
                f.write(tx)
            if self.timer_seconds_main == self.timer_seconds_max:
                show_message_notification(
                    f"⏱️Campo {self.instance_number} - Tempo Extra",
                    "Tempo Extra iniciado.", icon="⏳", bg_color=COLOR_ERROR
                )
                self.timer_seconds_extra = 0
                self.extra_entry.delete(0, "end")
                self.extra_entry.insert(0, "00:00")
                with open(os.path.join(self.field_folder, "extra.txt"), "w", encoding="utf-8") as f:
                    f.write("00:00")
        else:
            self.timer_seconds_extra += 1
            txe = self._format_time(self.timer_seconds_extra)
            self.extra_entry.delete(0, "end")
            self.extra_entry.insert(0, txe)
            with open(os.path.join(self.field_folder, "extra.txt"), "w", encoding="utf-8") as f:
                f.write(txe)
        self.after(1000, self.update_timer)

    def pause_timer(self):
        if self.timer_running:
            self.timer_running = False
            show_message_notification(
                f"⏸️Campo {self.instance_number} - Pausado",
                "Cronómetro pausado.", icon="⏸", bg_color=COLOR_PAUSE
            )

    def reset_timer(self):
        self.timer_running = False
        zero_str = "00:00"
        os.makedirs(self.field_folder, exist_ok=True)
        for entry_attr, filename, label, seconds_attr in self._time_fields():
            if seconds_attr.endswith("max"):
                continue
            setattr(self, seconds_attr, 0)
            p = os.path.join(self.field_folder, filename)
            try:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(zero_str)
            except Exception as e:
                print(f"❌ Erro ao zerar '{filename}': {e}")
            w = getattr(self, entry_attr, None)
            if w:
                w.delete(0, "end")
                w.insert(0, zero_str)
        show_message_notification(
            f"⏹️ Campo {self.instance_number} - Parado",
            "Cronómetro parado.", icon="🛑", bg_color=COLOR_STOP
        )
