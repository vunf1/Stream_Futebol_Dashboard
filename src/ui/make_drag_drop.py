import customtkinter as ctk
import tkinter as tk
from typing import Union

def make_it_drag_and_drop(window):
    """
    Bind mouse events so that `window` can be dragged around by sua client area,
    mantendo o ponteiro travado no mesmo offset dentro da janela.
    """
    drag_state = {"offset_x": 0, "offset_y": 0}

    def _start_drag(event):
        # calcula o offset entre ponteiro e canto superior esquerdo da janela
        drag_state["offset_x"] = event.x_root - window.winfo_x()
        drag_state["offset_y"] = event.y_root - window.winfo_y()

    def _on_drag(event):
        # nova posição da janela para manter o ponteiro no mesmo offset
        new_x = event.x_root - drag_state["offset_x"]
        new_y = event.y_root - drag_state["offset_y"]
        window.geometry(f"+{new_x}+{new_y}")

    window.bind("<Button-1>",  _start_drag, add="+")
    window.bind("<B1-Motion>", _on_drag,    add="+")

