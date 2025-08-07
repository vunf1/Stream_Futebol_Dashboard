import customtkinter as ctk
from customtkinter import CTkToplevel


def top_centered_child_to_parent(win: CTkToplevel, parent: ctk.CTkBaseClass, child_w: int, child_h: int, y_offset: int = 20) -> None:
    """
    Configure stacking, focus and position of a child Toplevel window centered
    at the top of its parent.

    Args:
        win: The child CTkToplevel window.
        parent: The parent CTk window.
        child_w: Desired child window width.
        child_h: Desired child window height.
        y_offset: Vertical offset from the top of the parent.
    """
    win.transient(parent) # type: ignore
    win.lift(parent)
    win.focus_force()

    parent.update_idletasks()
    px = parent.winfo_x()
    py = parent.winfo_y()
    p_width = parent.winfo_width()
    pos_x = px + (p_width - child_w) // 2
    pos_y = py + y_offset
    win.geometry(f"{child_w}x{child_h}+{pos_x}+{pos_y}")
