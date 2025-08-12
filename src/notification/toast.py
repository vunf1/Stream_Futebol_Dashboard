# helpers/notification/toast.py
from __future__ import annotations
from dataclasses import dataclass
import time
from typing import Any, Optional, Tuple
import customtkinter as ctk
import tkinter as tk
from typing import Any, Dict, Optional, Union
import time
import threading
from queue import Queue

# Initialized per process via init_notification_queue()
notification_queue = None  # type: ignore

@dataclass
class ToastPayload:
    title: str
    message: str
    duration: int = 5000
    icon: str = "ℹ️"
    bg_color: Optional[str] = None
    # Anchor screen selection: (x, y) in global desktop coords
    anchor: Optional[Tuple[int, int]] = None
    # Optional grouping key (drop/replace future)
    group: Optional[str] = None

def init_notification_queue(q: Any):
    """Assign the shared notification queue. Call once in each process."""
    global notification_queue
    notification_queue = q

def prompt_notification(
    title: str,
    message: str,
    icon: str = "ℹ️",
    bg_color: Optional[str] = None,
    *,
    yes_text: str = "Yes",
    no_text: str = "No",
    parent: Optional[ctk.CTk] = None,
) -> bool:
    """
    Modal, borderless Yes/No prompt. Returns True if 'Yes' is clicked.
    Uses CustomTkinter only (no tk import). Does not use the queue/server.
    """
    # Window
    prompt = ctk.CTkToplevel(master=parent)
    prompt.overrideredirect(True)
    prompt.attributes("-topmost", True)
    prompt.attributes("-toolwindow", True)  # prevent taskbar icon
    prompt.configure(fg_color=bg_color or "black")
    # make_it_drag_and_drop(prompt) # Removed as per edit hint

    # Size & position (center on parent, else primary screen)
    w, h = 260, 170
    prompt.update_idletasks()
    if parent and parent.winfo_exists():
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
    else:
        sw, sh = prompt.winfo_screenwidth(), prompt.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
    prompt.geometry(f"{w}x{h}+{x}+{y}")

    # Content
    container = ctk.CTkFrame(prompt, corner_radius=12, fg_color=bg_color or "black")
    container.pack(fill="both", expand=True, padx=10, pady=10)

    header = ctk.CTkFrame(container, fg_color="transparent")
    header.pack(fill="x", pady=(0, 10))
    ctk.CTkLabel(header, text=icon, font=("Segoe UI", 24)).pack(side="left", padx=(0, 8))
    ctk.CTkLabel(header, text=title, font=("Segoe UI", 16, "bold")).pack(side="left")

    ctk.CTkLabel(
        container, text=message, font=("Segoe UI", 12),
        wraplength=w - 40, justify="center"
    ).pack(fill="x", pady=(0, 16))

    # Buttons
    result = {"value": False}

    def on_yes():
        result["value"] = True
        prompt.destroy()

    def on_no():
        prompt.destroy()

    btn_row = ctk.CTkFrame(container, fg_color="transparent")
    btn_row.pack()

    yes_btn = ctk.CTkButton(btn_row, text=yes_text, width=100, corner_radius=8, command=on_yes)
    no_btn  = ctk.CTkButton(btn_row, text=no_text,  width=100, corner_radius=8,
                            fg_color="#e40b0b", hover_color="#bbbbbb", command=on_no)
    yes_btn.pack(side="left", padx=8)
    no_btn.pack(side="left", padx=8)

    # UX niceties
    prompt.bind("<Return>", lambda e: on_yes())
    prompt.bind("<Escape>", lambda e: on_no())
    prompt.after(10, yes_btn.focus_set)

    # Modal
    prompt.grab_set()
    prompt.wait_window()

    return result["value"]

# notify("❗ Fecha a app", "Fecha o ficheiro goal_score.exe antes de continuar!",
#        icon="❌", duration=0, bg=COLOR_ERROR)

# notify("✅ Fechado", "Executável antigo removido com sucesso!",
#        icon="✅", duration=2000, bg=COLOR_SUCCESS)
def notify(title, message, *, icon="ℹ️", duration=5000, bg=None, anchor=None, group=None):
    # treat duration==0 as sticky (~1 hour; user can click to dismiss)
    if duration == 0:
        duration = 60 * 60 * 1000
    show_message_notification(
        title=title, message=message, duration=duration,
        icon=icon, bg_color=bg, anchor=anchor, group=group
    )
    
def show_message_notification(
    title: str,
    message: str,
    duration: int = 5000,
    icon: str = "ℹ️",
    bg_color: Optional[str] = None,
    *,
    anchor: Optional[Tuple[int, int]] = None,
    group: Optional[str] = None,
):
    """
    Enqueue a toast request. If 'anchor' is None we’ll use current cursor
    position in the server process (i.e., the user's *current* screen).
    """
    if notification_queue is None:
        raise RuntimeError("Notification queue not initialized")

    payload = ToastPayload(
        title=title,
        message=message,
        duration=duration,
        icon=icon,
        bg_color=bg_color,
        anchor=anchor,
        group=group,
    )
    notification_queue.put(payload)

# Keep width shared with the server
TOAST_WIDTH = 320  # bump to 340–360 if you want fewer wraps


def _build_toast_window(
    title: str,
    message: str,
    icon: str,
    bg_color: Optional[str],
    duration: int,
    *,
    anim: str = "lift",        # "lift" | "slide" | "fade"
    show_progress: bool = True,
) -> ctk.CTkToplevel:
    """
    Build a compact toast window with:
      - Rounded corners (with true transparent corners on Windows)
      - Bottom-right placement (server sets _target_xy; we animate from there)
      - Click-to-dismiss anywhere
      - Footer hint ("Click to dismiss") + a lifetime progress bar (optional)
      - Smooth fade-in/fade-out animation
      - Progress bar timing synced to actual visible time (no 1px sliver)

    NOTE: The server is responsible for:
      - Measuring/clamping height for stacking
      - Setting `win._target_xy = (x, y)` and then calling `win._fade_in()`
    """
    import time  # local import keeps module side-effects minimal

    # ---------- Visual constants ----------
    RADIUS    = 12
    SURFACE   = bg_color or "#198754"  # your green by default
    TITLE_FONT= ("Segoe UI", 12, "bold")
    MSG_FONT  = ("Segoe UI", 10)
    ICON_FONT = ("Segoe UI", 16)
    WRAP      = TOAST_WIDTH - 86       # text wrap width, leaves room for icon
    INNER_PAD = 10
    FADE_IN_MS, FADE_OUT_MS = 220, 160

    # Track all `after()` callbacks so we can cancel them on manual dismiss
    timers: list[int] = []

    # ---------- Top-level window ----------
    toast = ctk.CTkToplevel()
    toast.overrideredirect(True)   # borderless
    toast.attributes("-topmost", True)
    toast.attributes("-alpha", 0.0)  # start fully transparent for fade-in
    toast.attributes("-toolwindow", True)  # prevent taskbar icon

    # True transparent corners via chroma key where supported (Windows/Tk 8.6+)
    CHROMA = "#010101"
    try:
        toast.configure(fg_color=CHROMA)
        toast.attributes("-transparentcolor", CHROMA)
    except Exception:
        # Fallback: just color the toplevel to match the card; corners still look clean
        toast.configure(fg_color=SURFACE)

    # ---------- Card container (rounded) ----------
    # We use GRID on the card so we can reserve bottom rows for footer + progress
    card = ctk.CTkFrame(
        toast, corner_radius=RADIUS, border_width=0, fg_color=SURFACE, cursor="hand2"
    )
    card.pack(fill="both", expand=True)

    # Layout: row0 = content (expands/shrinks), row1 = footer label, row2 = progress bar
    card.grid_columnconfigure(0, weight=1)
    card.grid_rowconfigure(0, weight=1)  # content shrinks first if height is clamped
    card.grid_rowconfigure(1, weight=0)
    card.grid_rowconfigure(2, weight=0)

    # ---------- CONTENT (row 0) ----------
    content = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
    content.grid(row=0, column=0, sticky="nsew", padx=INNER_PAD, pady=(INNER_PAD, 4))

    # Container uses pack; its children use GRID so we can center the icon vertically
    row = ctk.CTkFrame(content, fg_color="transparent", cursor="hand2")
    row.pack(fill="both", expand=True)

    # Two columns: [icon] [text], one row that stretches vertically
    row.grid_columnconfigure(0, weight=0)  # icon column
    row.grid_columnconfigure(1, weight=1)  # text column
    row.grid_rowconfigure(0, weight=1)     # row expands so icon can center vertically

    # Emoji-based icon. Placed in the single row, centered by letting the row expand.
    icon_lbl = ctk.CTkLabel(
        row, text=icon, font=ICON_FONT, text_color="white",
        fg_color="transparent", cursor="hand2"
    )
    # `sticky=""` keeps it centered inside the cell (no N/S/E/W pulling)
    icon_lbl.grid(row=0, column=0, padx=(0, 8), sticky="")

    # Text column: title + message
    text_col = ctk.CTkFrame(row, fg_color="transparent", cursor="hand2")
    text_col.grid(row=0, column=1, sticky="nsew")

    ctk.CTkLabel(
        text_col, text=(title or "").strip(), font=TITLE_FONT,
        text_color="white", fg_color="transparent",
        wraplength=WRAP, justify="left"
    ).pack(anchor="w")

    ctk.CTkLabel(
        text_col, text=(message or "").strip(), font=MSG_FONT,
        text_color="white", fg_color="transparent",
        wraplength=WRAP, justify="left"
    ).pack(anchor="w")

    # ---------- FOOTER LABEL (row 1) ----------
    footer_lbl = ctk.CTkLabel(
        card, text="Click to dismiss", font=("Segoe UI", 9),
        text_color="#eaeaea", fg_color="transparent", anchor="e"
    )
    # Pinned to bottom via grid; will always be visible even if content is clamped
    footer_lbl.grid(row=1, column=0, sticky="ew", padx=INNER_PAD, pady=(0, 2))

    # ---------- PROGRESS BAR (row 2) ----------
    prog_bar = None
    if show_progress and duration > 400:
        # Slightly lighter progress over a darker track for visibility
        prog_bar = ctk.CTkProgressBar(
            card, height=3, corner_radius=2,
            fg_color="#0e5d38", progress_color="#d6ffe9"
        )
        prog_bar.grid(row=2, column=0, sticky="ew", padx=INNER_PAD, pady=(0, INNER_PAD - 6))
        prog_bar.set(1.0)

    # ---------- Helpers / interactions ----------
    def _hide_progress_bar():
        """Snap the progress bar to 0 and remove it from layout to avoid a 1-px sliver."""
        if prog_bar is None:
            return
        try:
            prog_bar.set(0.0)  # value to zero
            # Blend the progress color into the track color to hide any theme repaint
            prog_bar.configure(progress_color=prog_bar.cget("fg_color"))
            toast.update_idletasks()
            # Remove from layout immediately
            mgr = prog_bar.winfo_manager()
            if mgr == "grid":
                prog_bar.grid_remove()
            elif mgr == "pack":
                prog_bar.pack_forget()
            else:
                prog_bar.place_forget()
        except Exception:
            pass

    def cancel_timers():
        """Cancel all scheduled after() callbacks (e.g., on click-to-dismiss)."""
        for t in timers[:]:
            try:
                toast.after_cancel(t) # type: ignore[no-untyped-call]
            except:
                pass
        timers.clear()

    def fade_out():
        """Smooth fade-out + slight drop, then destroy the window."""
        if not toast.winfo_exists():
            return
        cancel_timers()
        _hide_progress_bar()  # ensure the bar is fully gone before exit

        x, y = toast.winfo_x(), toast.winfo_y()
        y_end = y + 8  # small downward motion
        frames = max(1, FADE_OUT_MS // 16)

        def tick(i=0):
            if not toast.winfo_exists():
                return
            t = min(1.0, i / frames)
            a = 1.0 - (t ** 3)  # ease-in cubic for opacity
            toast.attributes("-alpha", max(0.0, a))
            yi = int(y + (y_end - y) * t)
            toast.geometry(f"+{toast.winfo_x()}+{yi}")
            if t < 1.0:
                timers.append(toast.after(12, lambda: tick(i + 1))) # type: ignore[no-untyped-call] # Faster (was 16ms, now 12ms)
            else:
                try:
                    toast.destroy()
                except:
                    pass

        tick()

    # Bind click anywhere (and Esc) to dismiss
    for w in (toast, card, content, row, text_col, footer_lbl, icon_lbl):
        try:
            w.bind("<Button-1>", lambda _e=None: fade_out())
        except Exception:
            pass
    toast.bind("<Escape>", lambda _e=None: fade_out())

    # ---------- Animations ----------
    def ease_out_cubic(t: float) -> float:
        """Easing used for fade-in movement/opacity (fast start, gentle end)."""
        return 1.0 - (1.0 - t) ** 3

    def start_progress_and_schedule_dismiss():
        """
        Start the lifetime bar AFTER fade-in, run for the exact visible time,
        and trigger fade_out() when finished. Also hides the bar to avoid a 1-px tail.
        """
        visible_ms = max(0, duration - FADE_IN_MS - FADE_OUT_MS)
        if prog_bar is None or visible_ms <= 0:
            # No bar: just schedule the fade-out
            timers.append(toast.after(visible_ms, fade_out)) # type: ignore[no-untyped-call]
            return

        # Single controller loop: progress + deadline = same heartbeat
        deadline = time.perf_counter() + (visible_ms / 1000.0)
        total_s = visible_ms / 1000.0

        def step():
            if not toast.winfo_exists():
                return
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                _hide_progress_bar()  # remove any residual sliver
                fade_out()
                return
            # Update bar (clamped 0..1)
            try:
                prog_bar.set(max(0.0, min(1.0, remaining / total_s))) # type: ignore[no-untyped-call]
            except Exception:
                pass
            timers.append(toast.after(12, step))# type: ignore # ~83 fps (was 16ms, now 12ms)

        timers.append(toast.after(12, step)) # type: ignore[no-untyped-call] # Faster (was 16ms, now 12ms)

    def fade_in():
        """Fade-in + optional small lift/slide from the server-placed target (bottom-right)."""
        if not toast.winfo_exists():
            return

        # The server recorded the final geometry for us to animate towards
        x_final, y_final = getattr(toast, "_target_xy", (toast.winfo_x(), toast.winfo_y()))

        # Choose a starting offset for a subtle motion
        if anim == "slide":
            x0, y0 = x_final + 14, y_final
        elif anim == "lift":
            x0, y0 = x_final, y_final + 12
        else:  # pure fade
            x0, y0 = x_final, y_final

        # Start from the offset position
        if (x0, y0) != (x_final, y_final):
            toast.geometry(f"+{x0}+{y0}")

        frames = max(1, FADE_IN_MS // 16)

        def tick(i=0):
            if not toast.winfo_exists():
                return
            t = min(1.0, i / frames)
            a = ease_out_cubic(t)
            toast.attributes("-alpha", a)
            if (x0, y0) != (x_final, y_final):
                xi = int(x0 + (x_final - x0) * a)
                yi = int(y0 + (y_final - y0) * a)
                toast.geometry(f"+{xi}+{yi}")
            if t < 1.0:
                timers.append(toast.after(12, lambda: tick(i + 1))) # type: ignore[no-untyped-call] # Faster (was 16ms, now 12ms)
            else:
                toast.attributes("-alpha", 1.0)
                # Only start the visible-time countdown after we’re fully in
                start_progress_and_schedule_dismiss()

        tick()

    # Expose hooks the server calls
    toast._fade_in = fade_in     # type: ignore[attr-defined]
    toast._fade_out = fade_out   # type: ignore[attr-defined]

    # Let the server read the real measured height for stacking/clamping
    toast.update_idletasks()
    try:
        toast._measured_height = max(1, toast.winfo_height())  # type: ignore[attr-defined]
    except Exception:
        pass

    return toast
