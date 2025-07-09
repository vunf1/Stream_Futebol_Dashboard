import os
import re
from tkinter import PhotoImage
from customtkinter import CTkFrame, CTkImage, CTkButton, CTkEntry
from assets.icons.icons_provider import get_icon
from helpers.notification.toast import show_message_notification
from assets.colors import COLOR_ACTIVE, COLOR_ERROR, COLOR_INFO, COLOR_PAUSE, COLOR_STOP, COLOR_SUCCESS, COLOR_WARNING

class TimerWidget(CTkFrame):
    def __init__(self, parent, field_folder, instance_number):
        super().__init__(parent,fg_color="transparent",corner_radius=0)
        self.field_folder = field_folder
        self.timer_running = False
        self.timer_seconds = 0
        self.instance_number = instance_number
        self._load_persisted_time()        
        self.pack(padx=10, pady=10, fill="x")
        self._icon_refs: list[CTkImage] = []
        self._build_ui()

    def _load_persisted_time(self):
        # ensure file exists, and load last value
        timer_path = os.path.join(self.field_folder, "timer.txt")
        os.makedirs(self.field_folder, exist_ok=True)
        if not os.path.exists(timer_path):
            with open(timer_path, "w", encoding="utf-8") as f:
                f.write("00:00")
        else:
            try:
                with open(timer_path, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                    mins, secs = map(int, text.split(":"))
                    self.timer_seconds = mins * 60 + secs
            except Exception:
                self.timer_seconds = 0

    def _build_ui(self):
        # Let this frame expand in both directions
        self.pack(fill="both", expand=True)

        # Create container that also fills and expands
        container = CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True)

        # Make row 0 and all five columns stretch
        container.grid_rowconfigure(0, weight=1)
        for col in range(5):
            container.grid_columnconfigure(col, weight=1)

        # — Save button —
        save_img = get_icon("save", 24)
        self._icon_refs.append(save_img)
        save_button = CTkButton(
            container,
            image=save_img,
            text="",
            fg_color="transparent",
            hover_color=COLOR_ACTIVE,
            command=self.save_timer_from_entry
        )
        save_button.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # — Timer entry —
        self.timer_entry = CTkEntry(
            container,
            font=("Segoe UI Emoji", 24),
            justify="center"
        )
        self.timer_entry.insert(0, self._format_time(self.timer_seconds))
        self.timer_entry.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # — Play / Pause / Stop buttons —
        ICON_SIZE = 32
        BUTTON_SPECS = [
            ("play",  self.start_timer,   COLOR_INFO),
            ("pause", self.pause_timer,   COLOR_WARNING),
            ("stop",  self.reset_timer,   COLOR_ERROR),
        ]

        for idx, (icon_key, cmd, hover_col) in enumerate(BUTTON_SPECS, start=2):
            img = get_icon(icon_key, ICON_SIZE)
            self._icon_refs.append(img)

            btn = CTkButton(
                container,
                image=img,
                text="",                   # icon only
                fg_color="transparent",    # no background
                hover_color=hover_col,     # dynamic hover color
                command=cmd
            )
            btn.grid(row=0, column=idx, sticky="nsew", padx=5, pady=5)

    def _format_time(self, total_seconds):        
        # Compute whole minutes and remaining seconds
        minutes, seconds = divmod(total_seconds, 60)
        # Format with two digits each, e.g.  3 → "03", 42 → "42"
        return f"{minutes:02}:{seconds:02}"

    def save_timer_from_entry(self):
        text = self.timer_entry.get().strip()
        # Accept only MM:SS or MMM:SS but reject MMM < 100
        if not re.match(r"^(?:\d{2}|[1-9]\d{2,}):\d{2}$", text):
            show_message_notification(f"❌Campo {self.instance_number} -  Erro",
                "Formato inválido. Usa 'MM:SS' ou 'MMM:SS' (>=100).",
                icon="❌", bg_color=COLOR_ERROR)
            return

        mins_str, secs_str = text.split(":")
        mins, secs = int(mins_str), int(secs_str)
        if len(mins_str)==3 and mins<100:
            show_message_notification(f"❌Campo {self.instance_number} -  Erro",
                "Minutos 3-dígitos devem ser ≥100.", icon="❌", bg_color=COLOR_ERROR)
            return
        if not (0 <= secs < 60):
            show_message_notification(f"❌Campo {self.instance_number} -  Erro",
                "Segundos fora do intervalo 00–59.", icon="❌", bg_color=COLOR_ERROR)
            return

        self.timer_seconds = mins*60 + secs
        timer_path = os.path.join(self.field_folder, "timer.txt")
        with open(timer_path, "w", encoding="utf-8") as f:
            f.write(f"{mins_str}:{secs:02}")

        show_message_notification(f"💾Campo {self.instance_number} - Guardado","Tempo guardado com sucesso.", icon="💾", bg_color=COLOR_SUCCESS)

    def update_timer(self):
        if self.timer_running:
            self.timer_seconds += 1
            t = self._format_time(self.timer_seconds)
            self.timer_entry.delete(0, "end") 
            self.timer_entry.insert(0, t)
            with open(os.path.join(self.field_folder, "timer.txt"), "w", encoding="utf-8") as f:
                f.write(t)
            self.after(1000, self.update_timer)

    def start_timer(self):
        if not self.timer_running:
            self.timer_running = True
            self.update_timer()
            show_message_notification(f"⏱️Campo {self.instance_number} - Timer Iniciado",
                "O cronómetro foi iniciado.", icon="⏳", bg_color=COLOR_INFO)

    def pause_timer(self):
        if self.timer_running:
            self.timer_running = False
            show_message_notification(f"⏸️Campo {self.instance_number} - Pausado",
                "O cronómetro foi pausado.", icon="⏸", bg_color=COLOR_PAUSE)

    def reset_timer(self):
        """
        Stop the timer, zero the display and the persisted file,
        and show a “Stopped” notification.
        """
        # Stop the running clock
        self.timer_running = False
        # Fire the notification
        show_message_notification(f"⏹️Campo {self.instance_number} - Parado ",f"O cronómetro foi parado - {self._format_time(self.timer_seconds)}.",icon="🛑",bg_color=COLOR_STOP)
        # Zero out internal counter
        self.timer_seconds = 0

        # Prepare zero string
        zero_str = "00:00"
        timer_path = os.path.join(self.field_folder, "timer.txt")

        # Write "00:00" to file
        try:
            os.makedirs(self.field_folder, exist_ok=True)
            with open(timer_path, "w", encoding="utf-8") as f:
                f.write(zero_str)
        except Exception as e:
            print(f"❌ Erro ao zerar timer.txt: {e}")

        # Update the entry widget
        if hasattr(self, "timer_entry"):
            self.timer_entry.delete(0, "end")
            self.timer_entry.insert(0, zero_str)


