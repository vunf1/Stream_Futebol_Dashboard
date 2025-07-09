import customtkinter as ctk
import tkinter as tk
from typing import Union

def make_it_drag_and_drop(window: Union[tk.Toplevel, ctk.CTkToplevel]) -> None:
    """
    Bind mouse events so that `window` can be dragged around by its client area.
    State is kept in the closure (no monkey-patching attributes on `window`).
    """
    drag_state = {"x": 0, "y": 0}

    def _start_drag(event: tk.Event) -> None:
        # record pointer location relative to window top-left
        drag_state["x"] = event.x
        drag_state["y"] = event.y

    def _on_drag(event: tk.Event) -> None:
        # compute new absolute window position
        new_x = event.x_root - drag_state["x"]
        new_y = event.y_root - drag_state["y"]
        window.geometry(f"+{new_x}+{new_y}")

    # Use `add="+"` so you don’t clobber other bindings
    window.bind("<Button-1>",   _start_drag, add="+")
    window.bind("<B1-Motion>",  _on_drag,    add="+")
