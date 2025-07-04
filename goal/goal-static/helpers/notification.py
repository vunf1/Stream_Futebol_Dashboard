import customtkinter as ctk
import tkinter as tk
from multiprocessing import Queue

# Initialized by bootstrap in each process
notification_queue: Queue = None

# Internal stack for active toasts (server only)
active_toasts = []


def init_notification_queue(q: Queue):
    """Assign the shared notification queue. Call once in each process before notify()."""
    global notification_queue
    notification_queue = q


def show_message_notification(title: str, message: str, duration: int = 5000,
           icon: str = "ℹ️", bg_color: str = None):
    """
    Enqueue a toast request from any ScoreApp instance (any process).
    """
    if notification_queue is None:
        raise RuntimeError("Notification queue not initialized")
    notification_queue.put((title, message, {
        'duration': duration,
        'icon': icon,
        'bg_color': bg_color,
    }))


def display_notification(title: str, message: str, duration: int = 5000,
                         icon: str = "ℹ️", bg_color: str = None):
    """
    Runs in the notification server process to actually show the toast.
    """
    toast = ctk.CTkToplevel()
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)
    toast.attributes("-alpha", 0.0)

    # Position stacked toasts bottom-right
    width, height, margin, gap = 300, 100, 20, 10
    toast.update_idletasks()
    screen_w, screen_h = toast.winfo_screenwidth(), toast.winfo_screenheight()
    y = screen_h - height - margin - sum((height + gap) for _ in active_toasts)
    x = screen_w - width - margin
    toast.geometry(f"{width}x{height}+{x}+{y}")
    active_toasts.append(toast)

    # Build content
    frame = ctk.CTkFrame(toast, corner_radius=10, fg_color=bg_color)
    frame.pack(fill="both", expand=True, padx=10, pady=10)
    ctk.CTkLabel(frame, text=icon, font=("Segoe UI", 24)).pack(side="left", padx=(5,10))
    txt = ctk.CTkFrame(frame, fg_color="transparent")
    txt.pack(side="left", fill="both", expand=True)
    ctk.CTkLabel(txt, text=title, font=("Segoe UI", 14, "bold")).pack(anchor="w")
    ctk.CTkLabel(txt, text=message, font=("Segoe UI", 12), wraplength=220).pack(anchor="w")

    # Simple fade in/out logic
    tasks = []

    def cancel_tasks():
        for t in tasks:
            try:
                toast.after_cancel(t)
            except:
                pass

    def fade_in(alpha=0.0):
        if not toast.winfo_exists(): return
        if alpha < 1.0:
            toast.attributes("-alpha", alpha)
            t = toast.after(20, lambda: fade_in(alpha + 0.1))
            tasks.append(t)
        else:
            toast.attributes("-alpha", 1.0)
            t = toast.after(duration, fade_out)
            tasks.append(t)

    def fade_out(alpha=1.0):
        if not toast.winfo_exists(): return
        if alpha > 0:
            toast.attributes("-alpha", alpha)
            t = toast.after(20, lambda: fade_out(alpha - 0.1))
            tasks.append(t)
        else:
            cancel_tasks()
            if toast in active_toasts:
                active_toasts.remove(toast)
            toast.destroy()

    toast.bind("<Destroy>", lambda e: cancel_tasks())
    fade_in()


def prompt_notification(title: str, message: str, icon: str = "ℹ️", bg_color: str = None) -> bool:
    """
    Displays a draggable, borderless Yes/No prompt.
    Returns True if the user clicks Yes, False otherwise.
    """
    # 1) Create borderless window
    prompt = ctk.CTkToplevel()
    prompt.overrideredirect(True)
    prompt.attributes("-topmost", True)
    prompt.configure(fg_color=bg_color or "black")

    # 2) Make draggable
    def start_move(e):
        prompt._drag_x = e.x
        prompt._drag_y = e.y
    def on_move(e):
        if hasattr(prompt, "_drag_x"):
            x = e.x_root - prompt._drag_x
            y = e.y_root - prompt._drag_y
            prompt.geometry(f"+{x}+{y}")

    prompt.bind("<Button-1>", start_move)
    prompt.bind("<B1-Motion>", on_move)

    # 3) Center on screen
    w, h = 200, 160
    prompt.update_idletasks()
    sw, sh = prompt.winfo_screenwidth(), prompt.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    prompt.geometry(f"{w}x{h}+{x}+{y}")

    # 4) Main content frame
    container = ctk.CTkFrame(prompt, corner_radius=12, fg_color=bg_color or "black")
    container.pack(fill="both", expand=True, padx=10, pady=10)

    # 5) Header (icon + title) aligned left
    header = ctk.CTkFrame(container, fg_color="transparent")
    header.pack(fill="x", pady=(0, 10))
    ctk.CTkLabel(header, text=icon, font=("Segoe UI", 24)).pack(side="left", padx=(0, 8))
    ctk.CTkLabel(header, text=title, font=("Segoe UI", 16, "bold")).pack(side="left")

    # 6) Message text, centered
    msg = ctk.CTkLabel(
        container,
        text=message,
        font=("Segoe UI", 12),
        wraplength=w - 40,
        justify="center"
    )
    msg.pack(fill="x", pady=(0, 20))

    # 7) Buttons row, centered
    result = {"value": False}
    btn_frame = ctk.CTkFrame(container, fg_color="transparent")
    btn_frame.pack()

    def on_yes():
        result["value"] = True
        prompt.destroy()
    def on_no():
        prompt.destroy()

    yes_btn = ctk.CTkButton(
        btn_frame,
        text="Yes",
        width=100,
        corner_radius=8,
        command=on_yes
    )
    no_btn = ctk.CTkButton(
        btn_frame,
        text="No",
        width=100,
        corner_radius=8,
        fg_color="#e40b0b",
        hover_color="#bbbbbb",
        command=on_no
    )
    yes_btn.pack(side="left", padx=10)
    no_btn.pack(side="left", padx=10)

    # 8) Modal grab and wait
    prompt.grab_set()
    prompt.wait_window()

    return result["value"]