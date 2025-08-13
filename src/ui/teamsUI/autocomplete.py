import customtkinter as ctk
from typing import Any, Callable, Dict, List, Optional
from ..window_utils import create_popup_dialog

class Autocomplete(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        fetch_suggestions: Callable[[], Dict[str, Any]],
        selection_callback: Callable[[str, Any], None],
        placeholder: str = "",
        max_visible: int = 6,
        debounce_ms: int = 120,
    ):
        super().__init__(parent, fg_color="transparent")
        self.fetch_suggestions = fetch_suggestions
        self.selection_callback = selection_callback
        self.max_visible = max_visible
        self.debounce_ms = debounce_ms

        self.entry = ctk.CTkEntry(self, placeholder_text=placeholder)
        self.entry.pack(fill="x")

        # Popup + state
        self.popup: Optional[ctk.CTkToplevel] = None
        self.container: Optional[ctk.CTkScrollableFrame] = None
        self.items: List[ctk.CTkLabel] = []
        self.matches: List[str] = []
        self._debounce_job: Optional[str] = None
        self._selected_index: int = -1
        self._last_text: str = ""  # for restore when empty

        # Bindings
        self.entry.bind("<KeyRelease>", self._on_key)
        self.entry.bind("<FocusOut>", self._on_focus_out, add=True)
        self.entry.bind("<Down>", self._nav_down)
        self.entry.bind("<Up>", self._nav_up)
        self.entry.bind("<Return>", self._nav_enter)
        self.entry.bind("<Escape>", self._restore_last_immediately)

    # ---------------- Events / Debounce ----------------
    def _on_key(self, event):
        # Ignore nav keys here (handled separately)
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return
        if self._debounce_job:
            self.after_cancel(self._debounce_job)
        self._debounce_job = self.after(self.debounce_ms, self._query_and_show)

    def _query_and_show(self):
        self._debounce_job = None
        q = (self.entry.get() or "").strip()
        if not q:
            self._hide_popup()
            return

        data = self.fetch_suggestions() or {}
        qcf = q.casefold()
        labels = list(data.keys())
        self.matches = [lbl for lbl in labels if qcf in lbl.casefold()]

        if not self.matches:
            self._hide_popup()
            return

        self._selected_index = -1
        popup = self._ensure_popup()
        self._position_popup(popup)
        self._populate_popup(data)

    # ---------------- Popup helpers ----------------
    def _ensure_popup(self) -> ctk.CTkToplevel:
        popup = self.popup
        if popup is not None and popup.winfo_exists():
            return popup
        
        # Create popup using window utilities
        popup = create_popup_dialog(self, "Autocomplete", 200, 150)
        self.popup = popup

        self.container = ctk.CTkScrollableFrame(popup, corner_radius=6)
        self.container.pack(fill="both", expand=True)

        # Global click to close
        self.winfo_toplevel().bind_all("<Button-1>", self._on_global_click, "+")
        return popup

    def _position_popup(self, popup: ctk.CTkToplevel) -> None:
        self.entry.update_idletasks()
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        width = self.entry.winfo_width()
        item_h = 30
        visible = min(len(self.matches), self.max_visible) or 1
        height = max(1, visible) * item_h
        popup.geometry(f"{width}x{height}+{x}+{y}")

    def _populate_popup(self, data: Dict[str, Any]) -> None:
        container = self.container
        if container is None:
            return
        # Clear previous
        for it in self.items:
            it.destroy()
        self.items.clear()

        # 🚀 Build ALL items (scroll shows the rest)
        for label in self.matches:
            value = data[label]
            item = ctk.CTkLabel(
                container,
                text=label,
                anchor="w",
                justify="left",
                fg_color="#333333",
                corner_radius=0,
                height=26,
            )
            item.pack(fill="x", padx=(8, 2), pady=1)
            item.bind("<Button-1>", lambda e, lbl=label, val=value: self._select(lbl, val))
            item.bind("<Enter>",    lambda e, w=item: w.configure(fg_color="#444444"))
            item.bind("<Leave>",    lambda e, w=item: w.configure(fg_color="#333333"))
            self.items.append(item)

        self._highlight_selected()  # reset highlight

    def _hide_popup(self):
        popup = self.popup
        if popup is not None and popup.winfo_exists():
            try:
                self.winfo_toplevel().unbind_all("<Button-1>")
            except Exception:
                pass
            popup.destroy()
        self.popup = None
        self.container = None
        self.items.clear()
        self.matches.clear()
        self._selected_index = -1

    def _on_global_click(self, event):
        w = event.widget
        if w == self.entry or (self.popup and self._is_descendant(w, self.popup)):
            return
        self._hide_popup()

    @staticmethod
    def _is_descendant(widget, ancestor) -> bool:
        if ancestor is None:
            return False
        while widget:
            if widget == ancestor:
                return True
            widget = getattr(widget, "master", None)
        return False

    # ---------------- Selection / Navigation ----------------
    def _scroll_selected_into_view(self) -> None:
        """Ensure the highlighted item is visible inside the scrollable frame."""
        cont = self.container
        if cont is None or not self.items or self._selected_index < 0:
            return
        # item geometry (relative to the inner frame)
        item = self.items[self._selected_index]
        try:
            canvas = cont._parent_canvas  # customtkinter internal canvas
        except Exception:
            return

        canvas.update_idletasks()

        item_y = item.winfo_y()
        item_h = item.winfo_height()

        top = canvas.canvasy(0)                  # current top of visible area (in inner-frame coords)
        view_h = canvas.winfo_height()
        bottom = top + view_h

        # compute the target top we want after scroll
        if item_y < top:
            target_top = item_y
        elif item_y + item_h > bottom:
            target_top = item_y + item_h - view_h
        else:
            return  # already fully visible

        # clamp fraction to [0,1] based on scrollregion height
        bbox = canvas.bbox("all")
        if not bbox:
            return
        total_h = max(1, bbox[3] - bbox[1])
        frac = max(0.0, min(1.0, target_top / total_h))
        canvas.yview_moveto(frac)

    def _select(self, label: str, value: Any):
        self.entry.delete(0, "end")
        self.entry.insert(0, label)
        self._last_text = label  # remember it!
        self.selection_callback(label, value)
        self.focus_set()
        self._hide_popup()

    def _on_focus_out(self, _e):
        # If user leaves it empty, restore last text
        if not (self.entry.get() or "").strip() and self._last_text:
            self.entry.delete(0, "end")
            self.entry.insert(0, self._last_text)

    def _restore_last_immediately(self, _e):
        """ESC → restore last value and close popup."""
        if self._last_text:
            self.entry.delete(0, "end")
            self.entry.insert(0, self._last_text)
        self._hide_popup()
        return "break"

    def _nav_down(self, _e):
        if not self.items:
            return "break"
        self._selected_index = (self._selected_index + 1) % len(self.items)
        self._highlight_selected()
        self._scroll_selected_into_view()
        return "break"

    def _nav_up(self, _e):
        if not self.items:
            return "break"
        self._selected_index = (self._selected_index - 1) % len(self.items)
        self._highlight_selected()
        self._scroll_selected_into_view()
        return "break"

    def _nav_enter(self, _e):
        if not self.items:
            return "break"
        idx = self._selected_index if self._selected_index >= 0 else 0
        label = self.items[idx].cget("text")
        data = self.fetch_suggestions() or {}
        self._select(label, data.get(label))
        return "break"

    def _highlight_selected(self):
        for i, item in enumerate(self.items):
            item.configure(fg_color="#555555" if i == self._selected_index else "#333333")
        # keep the highlighted one visible
        self._scroll_selected_into_view()
    # ---------------- API ----------------
    def get(self) -> str:
        return self.entry.get()

    def set(self, text: str):
        self.entry.delete(0, "end")
        self.entry.insert(0, text or "")
        self._last_text = text or ""
