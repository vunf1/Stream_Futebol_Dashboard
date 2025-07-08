
import customtkinter as ctk
from typing import Any, Callable

class Autocomplete(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        fetch_suggestions: Callable[[], dict[str,Any]],
        selection_callback: Callable[[str,Any],None],
        placeholder: str = "",
        max_visible: int = 6
    ):
        super().__init__(parent)
        self.fetch_suggestions = fetch_suggestions
        self.selection_callback = selection_callback
        self.max_visible = max_visible
        self.popup = None

        self.entry = ctk.CTkEntry(self, placeholder_text=placeholder)
        self.entry.pack(fill="x")
        self.entry.bind("<KeyRelease>", self._on_text_changed)

    def _on_text_changed(self, event):
        query = self.entry.get().strip().lower()
        if not query:
            return self._hide_popup()
        self._show_popup(query)

    def _show_popup(self, query: str):
        all_items = self.fetch_suggestions() # should return dict[str, Any]
        matches = [label for label in all_items if query in label.lower()]
        if not matches:
            return self._hide_popup()

        # remove old popup if present
        self._hide_popup()

        # create new floating window
        self.popup = ctk.CTkToplevel(self)
        self.popup.overrideredirect(True)
        self.popup.attributes("-topmost", True)

        # position & size
        self.entry.update_idletasks()
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        width = self.entry.winfo_width()
        item_height = 30
        visible_count = min(len(matches), self.max_visible)
        height = visible_count * item_height
        self.popup.geometry(f"{width}x{height}+{x}+{y}")

        # scrollable container
        suggestion_frame = ctk.CTkScrollableFrame(self.popup, corner_radius=6)
        suggestion_frame.pack(fill="both", expand=True)

        # anywhere you click outside should close it
        root = self.winfo_toplevel()
        root.bind_all("<Button-1>", self._on_global_click, "+")

        # add one label per suggestion
        for label in matches:
            value = all_items[label]
            item = ctk.CTkLabel(
                suggestion_frame,
                text=label,
                anchor="w",       # left‐align
                justify="left",
                fg_color="#333333",
                corner_radius=0,
                height=item_height - 4
            )
            item.pack(fill="x", padx=(8,2), pady=1)

            # click selects
            item.bind(
                "<Button-1>",
                lambda e, lbl=label, val=value: self._select(lbl, val)
            )
            # hover effect
            item.bind("<Enter>",  lambda e, w=item: w.configure(fg_color="#444444"))
            item.bind("<Leave>",  lambda e, w=item: w.configure(fg_color="#333333"))

    def _on_global_click(self, event):
        widget = event.widget
        # if click lands inside entry or popup, ignore
        if widget == self.entry or self._is_descendant(widget, self.popup):
            return
        self._hide_popup()

    def _is_descendant(self, widget, ancestor):
        while widget:
            if widget == ancestor:
                return True
            widget = getattr(widget, "master", None)
        return False

    def _hide_popup(self):
        if self.popup:
            # undo the global click binding
            self.winfo_toplevel().unbind_all("<Button-1>")
            self.popup.destroy()
            self.popup = None

    def _select(self, label: str, value: Any):
        # fill entry, notify caller, then hide
        self.entry.delete(0, "end")
        self.entry.insert(0, label)
        self.selection_callback(label, value)
        self._hide_popup()

    def get(self) -> str:
        return self.entry.get()

    def set(self, text: str):
        self.entry.delete(0, "end")
        self.entry.insert(0, text)

