import customtkinter as ctk
from typing import Any, Callable, Dict, List, Optional
from ...utils import create_popup_dialog

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
        self._binding_tag = f"autocomplete_{id(self)}"  # Unique binding tag
        self._monitoring = False  # Track if we're monitoring the popup
        self._click_binding_id: Optional[str] = None  # track root click binding id

        # Bindings
        self.entry.bind("<KeyRelease>", self._on_key)
        self.entry.bind("<Down>", self._nav_down)
        self.entry.bind("<Up>", self._nav_up)
        self.entry.bind("<Return>", self._nav_enter)
        self.entry.bind("<Escape>", self._restore_last_immediately)
        self.entry.bind("<FocusIn>", self._on_focus_in)
        # Ensure popup opens on mouse click inside the entry (even without key press)
        self.entry.bind("<Button-1>", self._on_entry_click, add=True)

    # ---------------- Events / Debounce ----------------
    def _on_key(self, event: Any):
        # Ignore nav keys here (handled separately)
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return
        
        # Clear matches if text is completely cleared
        current_text = (self.entry.get() or "").strip()
        if not current_text:
            self.matches.clear()
            self._selected_index = -1
            self._hide_popup()
            return
            
        if self._debounce_job:
            self.after_cancel(self._debounce_job)
        self._debounce_job = self.after(self.debounce_ms, self._query_and_show)

    def _query_and_show(self) -> None:
        self._debounce_job = None
        q = (self.entry.get() or "").strip()
        if not q:
            self._hide_popup()
            return

        # Always fetch fresh data to ensure consistency
        try:
            data = self.fetch_suggestions() or {}
        except Exception:
            return

        qcf = q.casefold()
        labels = list(data.keys())
        self.matches = [lbl for lbl in labels if qcf in lbl.casefold()]

        if not self.matches:
            self._hide_popup()
            return

        self._selected_index = -1
        try:
            popup = self._ensure_popup()
            self._position_popup(popup)
            self._populate_popup(data)
        except Exception:
            pass

    # ---------------- Popup helpers ----------------
    def _ensure_popup(self) -> ctk.CTkToplevel:
        popup = self.popup
        if popup is not None:
            try:
                if popup.winfo_exists():
                    return popup
            except Exception:
                pass
        
        # Create popup with custom configuration to allow proper focus handling
        try:
            parent_win = self.winfo_toplevel()
            # At runtime this is a CTk/CTkToplevel; cast to satisfy type checker
            from typing import cast
            import customtkinter as _ctk
            # Prefer CTkToplevel parent when possible; fall back to root cast
            parent_ctk = parent_win if isinstance(parent_win, (_ctk.CTk, _ctk.CTkToplevel)) else _ctk.CTk()
            popup = create_popup_dialog(
                cast(_ctk.CTk, parent_ctk),
                "Autocomplete", 
                200, 
                150,
                config={
                    "grab_set": False,
                    "transient": True,
                    "overrideredirect": True,
                    "topmost": True
                }
            )
            self.popup = popup

            self.container = ctk.CTkScrollableFrame(popup, corner_radius=6)
            self.container.pack(fill="both", expand=True)

            # Bind popup-specific events for better click outside detection
            # NOTE: Do not bind <FocusOut> on popup; it fires immediately because
            # the toplevel never gains focus when created via click, causing the
            # suggestions window to close instantaneously. Entry focus tracking
            # is sufficient for auto-closing behaviour.
            popup.bind("<Button-1>", self._on_popup_click)
            
            # Bind to the main window for click outside detection
            try:
                # No root-level click binding anymore; nothing to clean
                pass
            except Exception:
                pass
            
            # Background monitor disabled – focus-out logic already handles closure
            
            return popup
        except Exception as e:
            raise

    def _start_popup_monitor(self) -> None:
        """Start monitoring the popup to detect when it should be closed"""
        if self._monitoring:
            return  # Already monitoring
        
        self._monitoring = True
        
        def check_popup():
            if not self._monitoring:
                return  # Stop monitoring
            
            try:
                if self.popup and hasattr(self.popup, 'winfo_exists') and self.popup.winfo_exists():
                    # Check if the entry still has focus
                    if hasattr(self.entry, 'focus_get') and self.entry.focus_get() != self.entry:
                        # Entry lost focus, close popup
                        self._hide_popup()
                    else:
                        # Continue monitoring
                        self.after(100, check_popup)
                else:
                    # Popup closed, stop monitoring
                    self._monitoring = False
            except Exception:
                # If there's any error, stop monitoring and clean up
                self._monitoring = False
                try:
                    self._hide_popup()
                except Exception:
                    pass
        
        # Start the monitoring
        self.after(100, check_popup)

    def _position_popup(self, popup: ctk.CTkToplevel) -> None:
        try:
            self.entry.update_idletasks()
            x = self.entry.winfo_rootx()
            y = self.entry.winfo_rooty() + self.entry.winfo_height()
            width = self.entry.winfo_width()
            item_h = 30
            visible = min(len(self.matches), self.max_visible) or 1
            height = max(1, visible) * item_h
            popup.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            pass

    def _populate_popup(self, data: Dict[str, Any]) -> None:
        container = self.container
        if container is None:
            return
        # Clear previous
        for it in self.items:
            try:
                it.destroy()
            except Exception:
                pass
        self.items.clear()

        # 🚀 Build ALL items (scroll shows the rest)
        for label in self.matches:
            try:
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
                item.bind("<ButtonRelease-1>", lambda e, lbl=label, val=value: self._on_item_clicked(lbl, val))
                item.bind("<Enter>",    lambda e, w=item: w.configure(fg_color="#444444"))
                item.bind("<Leave>",    lambda e, w=item: w.configure(fg_color="#333333"))
                self.items.append(item)
            except Exception:
                pass

        self._highlight_selected()  # reset highlight

    def _hide_popup(self) -> None:
        popup = self.popup
        if popup is not None:
            try:
                # Check if the popup still exists and the application is still running
                if hasattr(popup, 'winfo_exists') and popup.winfo_exists():
                    # Unbind from main window
                    try:
                        # No root-level click binding anymore; nothing to clean
                        pass
                    except Exception:
                        pass
                    popup.destroy()
            except Exception:
                # If there's any error, just clear the reference
                pass
        
        self.popup = None
        self.container = None
        self.items.clear()
        # Clear matches when closing to prevent stale data
        self.matches.clear()
        self._selected_index = -1
        self._monitoring = False  # ensure monitor stops when popup closed

    def _on_popup_focus_out(self, event: Any):
        """Handle when popup loses focus"""
        # Small delay to allow click events to process first
        self.after(100, self._check_if_should_close)

    def _on_focus_in(self, event: Any):
        """Handle when entry gains focus - show suggestions for existing text"""
        current_text = (self.entry.get() or "").strip()
        if current_text and not self.popup:
            # There's text and no popup, show suggestions
            self.after(50, self._query_and_show)

    def _on_entry_click(self, event: Any):
        """Open suggestions immediately when the entry is clicked."""
        current_text = (self.entry.get() or "").strip()
        if current_text:
            # If popup already open, leave as is; otherwise trigger suggestions fast
            if not self.popup:
                self.after(10, self._query_and_show)
        # allow normal click processing to continue
        return None

    def _cleanup_state(self) -> None:
        """Clean up the autocomplete state to prevent corruption"""
        try:
            if self._debounce_job:
                self.after_cancel(self._debounce_job)
                self._debounce_job = None
            
            # Stop monitoring
            self._monitoring = False
            
            # Only try to hide popup if we're still in a valid state
            if hasattr(self, 'popup') and self.popup is not None:
                self._hide_popup()
            
            self.matches.clear()
            self._selected_index = -1
            self._last_text = ""
        except Exception:
            # If cleanup fails, just clear the basic state
            self._monitoring = False
            self._debounce_job = None
            self.popup = None
            self.container = None
            self.items = []
            self.matches = []
            self._selected_index = -1
            self._last_text = ""

    def _on_popup_click(self, event: Any):
        """Handle clicks within the popup"""
        # Prevent the popup from closing when clicking inside it
        return "break"

    def _on_main_window_click(self, event: Any):
        """Handle clicks on the main window"""
        # Deprecated: root click binding removed to avoid focus/grab conflicts.
        pass

    def reset(self) -> None:
        """Reset the autocomplete to a clean state - useful when it breaks"""
        self._cleanup_state()
        self.entry.delete(0, "end")
        self._last_text = ""

    def _check_if_should_close(self) -> None:
        """Check if popup should be closed based on focus"""
        try:
            if self.popup and hasattr(self.popup, 'winfo_exists') and self.popup.winfo_exists():
                # Check if the popup or any of its children still have focus
                if hasattr(self.popup, 'focus_get'):
                    focused_widget = self.popup.focus_get()
                    if focused_widget is None or not self._is_descendant(focused_widget, self.popup):
                        # Focus left the popup; if it's also not on the entry, close
                        if hasattr(self.entry, 'focus_get') and self.entry.focus_get() != self.entry:
                            self._hide_popup()
        except Exception:
            # If there's any error, just close the popup to be safe
            try:
                self._hide_popup()
            except Exception:
                pass

    @staticmethod
    def _is_descendant(widget: Any, ancestor: Any) -> bool:
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

    def _select(self, label: str, value: Any) -> None:
        self.entry.delete(0, "end")
        self.entry.insert(0, label)
        self._last_text = label  # remember it!
        self.selection_callback(label, value)
        # Return focus to the entry widget itself, not the container frame
        try:
            self.entry.focus_set()
        except Exception:
            pass
        # Move focus away from the entry so further typing does not reopen immediately
        try:
            self.master.focus_set()
        except Exception:
            pass
        self._hide_popup()

    def _restore_last_immediately(self, _e: Any):
        """ESC → restore last value and close popup."""
        if self._last_text:
            self.entry.delete(0, "end")
            self.entry.insert(0, self._last_text)
        self._hide_popup()
        return "break"

    def _nav_down(self, _e: Any):
        if not self.items:
            return "break"
        self._selected_index = (self._selected_index + 1) % len(self.items)
        self._highlight_selected()
        self._scroll_selected_into_view()
        return "break"

    def _nav_up(self, _e: Any):
        if not self.items:
            return "break"
        self._selected_index = (self._selected_index - 1) % len(self.items)
        self._highlight_selected()
        self._scroll_selected_into_view()
        return "break"

    def _nav_enter(self, _e: Any):
        if not self.items:
            return "break"
        idx = self._selected_index if self._selected_index >= 0 else 0
        label = self.items[idx].cget("text")
        data = self.fetch_suggestions() or {}
        self._select(label, data.get(label))
        return "break"

    def _highlight_selected(self):
        for i, item in enumerate(self.items):
            try:
                item.configure(fg_color="#555555" if i == self._selected_index else "#333333")
            except Exception:
                pass
        # keep the highlighted one visible
        self._scroll_selected_into_view()

    # ---------------- API ----------------
    def get(self) -> str:
        return str(self.entry.get())

    def set(self, text: str):
        self.entry.delete(0, "end")
        self.entry.insert(0, text or "")
        self._last_text = text or ""
        
    def show_suggestions(self):
        """Manually trigger showing suggestions for current text"""
        if self.entry.get().strip():
            self._query_and_show()
            
    def force_refresh(self):
        """Force refresh suggestions - useful when autocomplete seems broken"""
        self._cleanup_state()
        current_text = self.entry.get().strip()
        if current_text:
            self.after(100, self._query_and_show)
            
    def clear_state(self):
        """Clear the current autocomplete state"""
        self._cleanup_state()

    def _on_item_clicked(self, label: str, value: Any):
        """Handle click on a suggestion item and prevent event propagation."""
        self._select(label, value)
        return "break"
