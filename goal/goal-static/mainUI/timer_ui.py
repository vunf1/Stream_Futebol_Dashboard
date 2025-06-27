# timer_widget.py
import os
import re
import customtkinter as ctk
from helpers import show_message_notification
from colors import COLOR_ERROR, COLOR_INFO, COLOR_PAUSE, COLOR_STOP, COLOR_SUCCESS
import threading
import keyboard

class TimerWidget(ctk.CTkFrame):
    def __init__(self, parent, field_folder):
        super().__init__(parent)
        self.field_folder = field_folder
        self.timer_running = False
        self.timer_seconds = 0
        self._load_persisted_time()        
        self.pack(padx=10, pady=10, fill="x")
        #self._register_global_hotkeys()
        self._build_ui()

    # CAREFUL THIS WAY WILL TRIGGER ALL INSTANCES FIELD - NOT RELIABLE
    # def _register_global_hotkeys(self):
    #     """
    #     Use the `keyboard` library to register OS-level hotkeys:
    #      - 'i' → start
    #      - 'p' → pause
    #      - 'o' → stop
    #     Runs in its own thread so as not to block the UI.
    #     """
    #     try:
    #         import keyboard
    #     except ImportError:
    #         print("⚠️  keyboard module not found; global hotkeys disabled")
    #         return

    #     def _listen():
    #         # note: no need for a loop; keyboard.add_hotkey installs hooks globally
    #         keyboard.add_hotkey("i", self.start_timer)
    #         keyboard.add_hotkey("p", self.pause_timer)
    #         keyboard.add_hotkey("o", self.reset_timer)
    #         keyboard.wait()  # block here, keeping the listener thread alive

    #     # run in background daemon thread
    #     t = threading.Thread(target=_listen, daemon=True)
    #     t.start()

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
        # Make this frame fill horizontally (x) and add padding 
        self.pack(fill="x", padx=10, pady=10)

        # Create an internal container to grid all controls
        container = ctk.CTkFrame(self)
        container.pack(fill="x")
        # Configure 5 equally-weighted columns for centering
        for col in range(5):
            container.grid_columnconfigure(col, weight=1)

        save_button = ctk.CTkButton(
            container, text="💾", width=40, font=("Segoe UI Emoji Emoji", 18),
            command=self.save_timer_from_entry
        )
        save_button.grid(row=0, column=0, padx=5, pady=5)

        self.timer_entry = ctk.CTkEntry(
            container, width=90, font=("Segoe UI Emoji Emoji", 24), justify="center"
        )
        self.timer_entry.insert(0, self._format_time(self.timer_seconds))
        self.timer_entry.grid(row=0, column=1, padx=5, pady=5)

        # Friendly list of (label, callback, bg_color) for Start/Pause/Stop
        controls = [
            ("Start", self.start_timer, COLOR_INFO),
            ("Pause", self.pause_timer, COLOR_PAUSE),
            ("Stop",  self.reset_timer, COLOR_STOP),
        ]

        start_button = ctk.CTkButton(
            container, text=controls[0][0], width=70, height=30,
            font=("Segoe UI", 14), fg_color=controls[0][2],
            command=controls[0][1]
        )
        start_button.grid(row=0, column=2, padx=5, pady=5)

        pause_button = ctk.CTkButton(
            container, text=controls[1][0], width=70, height=30,
            font=("Segoe UI", 14), fg_color=controls[1][2],
            command=controls[1][1]
        )
        pause_button.grid(row=0, column=3, padx=5, pady=5)

        stop_button = ctk.CTkButton(
            container, text=controls[2][0], width=70, height=30,
            font=("Segoe UI", 14), fg_color=controls[2][2],
            command=controls[2][1]
        )
        stop_button.grid(row=0, column=4, padx=5, pady=5)


    def _format_time(self, total_seconds):        
        # Compute whole minutes and remaining seconds
        minutes, seconds = divmod(total_seconds, 60)
        # Format with two digits each, e.g.  3 → "03", 42 → "42"
        return f"{minutes:02}:{seconds:02}"

    def save_timer_from_entry(self):
        text = self.timer_entry.get().strip()
        # Accept only MM:SS or MMM:SS but reject MMM < 100
        if not re.match(r"^(?:\d{2}|[1-9]\d{2,}):\d{2}$", text):
            show_message_notification("❌ Erro",
                "Formato inválido. Usa 'MM:SS' ou 'MMM:SS' (>=100).",
                icon="❌", bg_color=COLOR_ERROR)
            return

        mins_str, secs_str = text.split(":")
        mins, secs = int(mins_str), int(secs_str)
        if len(mins_str)==3 and mins<100:
            show_message_notification("❌ Erro",
                "Minutos 3-dígitos devem ser ≥100.", icon="❌", bg_color=COLOR_ERROR)
            return
        if not (0 <= secs < 60):
            show_message_notification("❌ Erro",
                "Segundos fora do intervalo 00–59.", icon="❌", bg_color=COLOR_ERROR)
            return

        self.timer_seconds = mins*60 + secs
        timer_path = os.path.join(self.field_folder, "timer.txt")
        with open(timer_path, "w", encoding="utf-8") as f:
            f.write(f"{mins_str}:{secs:02}")
        show_message_notification("💾 Guardado",
            "Tempo guardado com sucesso.", icon="💾", bg_color=COLOR_SUCCESS)

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
            show_message_notification("⏱️ Timer Iniciado",
                "O cronómetro foi iniciado.", icon="⏳", bg_color=COLOR_INFO)

    def pause_timer(self):
        if self.timer_running:
            self.timer_running = False
            show_message_notification("⏸️ Pausado",
                "O cronómetro foi pausado.", icon="⏸", bg_color=COLOR_PAUSE)

    def reset_timer(self):
        """
        Stop the timer, zero the display and the persisted file,
        and show a “Stopped” notification.
        """
        # Stop the running clock
        self.timer_running = False
        # Fire the notification
        show_message_notification(
            "⏹️ Parado",
            f"O cronómetro foi parado em {self.timer_seconds}.",
            icon="🛑",
            bg_color=COLOR_STOP
        )
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


