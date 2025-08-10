# helpers/notification/notification_server.py
from __future__ import annotations
from collections import deque, defaultdict
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional, Tuple

import customtkinter as ctk
from multiprocessing import Queue
from helpers.notification.toast import TOAST_WIDTH, ToastPayload, _build_toast_window

# -------- Windows multi-monitor helpers (with safe fallbacks) --------
def _get_cursor_pos() -> Tuple[int, int]:
    try:
        import ctypes
        from ctypes import wintypes
        pt = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return (pt.x, pt.y)
    except Exception:
        return (0, 0)

def _get_work_area_from_point(
    x: int,
    y: int,
    ct_root: Optional[ctk.CTk] = None
) -> Tuple[int, int, int, int]:
    try:
        import ctypes
        from ctypes import wintypes

        class RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                        ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

        class MONITORINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_ulong),
                        ("rcMonitor", RECT),
                        ("rcWork", RECT),
                        ("dwFlags", ctypes.c_ulong)]

        MonitorFromPoint = ctypes.windll.user32.MonitorFromPoint
        GetMonitorInfoW = ctypes.windll.user32.GetMonitorInfoW
        MonitorFromPoint.restype = wintypes.HMONITOR
        MONITOR_DEFAULTTONEAREST = 2

        hmon = MonitorFromPoint(wintypes.POINT(x, y), MONITOR_DEFAULTTONEAREST)
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        GetMonitorInfoW(hmon, ctypes.byref(mi))
        r = mi.rcWork
        return (r.left, r.top, r.right, r.bottom)

    except Exception:
        root = ct_root if (ct_root and ct_root.winfo_exists()) else None
        if root is None:
            tmp = ctk.CTk()
            try:
                tmp.withdraw()
                w, h = tmp.winfo_screenwidth(), tmp.winfo_screenheight()
            finally:
                try: tmp.destroy()
                except: pass
        else:
            w, h = root.winfo_screenwidth(), root.winfo_screenheight()
        return (0, 0, w, h)


# ------------------ Server state & layout policy ---------------------
TOAST_SIZE = (TOAST_WIDTH, 100)  # height is ignored; real height is measured
MARGIN = 16
GAP = 6
TARGET_MAX_VISIBLE = 10

@dataclass
class ActiveToast:
    win: ctk.CTkToplevel
    height: int = TOAST_SIZE[1]  # updated to real height after creation

class ToastServer:
    def __init__(self, root: ctk.CTk, q: Queue):
        self.root = root
        self.q = q
        self.stacks: Dict[Tuple[int, int, int, int], List[ActiveToast]] = defaultdict(list)
        self.pending: Deque[Tuple[ToastPayload, Tuple[int, int, int, int]]] = deque()

    # ---------- capacity / geometry helpers ----------
    def _per_toast_cap(self, workarea: Tuple[int,int,int,int]) -> int:
        left, top, right, bottom = workarea
        available = (bottom - top) - (2 * MARGIN)  # vertical pixels we can use
        # ten toasts => 9 gaps between them
        cap = (available - GAP * (TARGET_MAX_VISIBLE - 1)) // TARGET_MAX_VISIBLE
        return max(28, int(cap))  # keep a sensible minimum

    def _can_fit_more(self, workarea: Tuple[int,int,int,int], next_height: int) -> bool:
        cap = self._per_toast_cap(workarea)
        next_h = min(next_height, cap)
        left, top, right, bottom = workarea
        stack = self.stacks[workarea]
        used = sum(min(t.height, cap) for t in stack) + (GAP * len(stack) if stack else 0)
        y_top_next = bottom - MARGIN - next_h - used
        return y_top_next >= (top + MARGIN)

    def _place_toast(self, workarea: Tuple[int,int,int,int], toast: ctk.CTkToplevel, next_height: int):
        cap = self._per_toast_cap(workarea)
        next_h = min(next_height, cap)

        left, top, right, bottom = workarea
        width = TOAST_SIZE[0]
        stack = self.stacks[workarea]
        used = sum(min(t.height, cap) for t in stack) + (GAP * len(stack) if stack else 0)
        y = bottom - MARGIN - next_h - used
        x = right - MARGIN - width
        toast.geometry(f"{width}x{next_h}+{x}+{y}")
        setattr(toast, "_target_xy", (x, y))

    def _reflow(self, workarea: Tuple[int,int,int,int]):
        cap = self._per_toast_cap(workarea)
        left, top, right, bottom = workarea
        width = TOAST_SIZE[0]
        x = right - MARGIN - width
        y = bottom - MARGIN
        new_stack: List[ActiveToast] = []
        for t in list(self.stacks[workarea]):
            if not t.win.winfo_exists():
                continue
            h = min(max(1, t.height), cap)
            y -= h
            t.win.geometry(f"{width}x{h}+{x}+{y}")
            # 👇 keep the target position up to date
            setattr(t.win, "_target_xy", (x, y))
            new_stack.append(ActiveToast(t.win, h))
            y -= GAP
        self.stacks[workarea] = new_stack


    def _attach_close_handlers(self, workarea, win: ctk.CTkToplevel):
        def on_destroy(_evt=None):
            stack = self.stacks[workarea]
            self.stacks[workarea] = [t for t in stack if (t.win.winfo_exists() and t.win != win)]
            self._reflow(workarea)
            self._try_flush_backlog(workarea)
        win.bind("<Destroy>", on_destroy)


    def _show_now(self, payload: ToastPayload, workarea):
        # Create with target size first, place, then measure real height and reflow
        win = self._build_and_maybe_show(payload, workarea)


    def _try_flush_backlog(self, workarea):
        while True:
            idx = next((i for i,(p,wa) in enumerate(self.pending) if wa == workarea), None)
            if idx is None:
                break
            payload, _ = self.pending[idx]
            if not self._build_and_maybe_show(payload, workarea):
                break
            del self.pending[idx]

    # -------------------- main dispatch --------------------
    def handle_payload(self, payload: ToastPayload):
        ax, ay = payload.anchor if payload.anchor is not None else _get_cursor_pos()
        workarea = _get_work_area_from_point(ax, ay, ct_root=self.root)
        if not self._build_and_maybe_show(payload, workarea):
            self.pending.append((payload, workarea))


            
    def _build_and_maybe_show(self, payload: ToastPayload, workarea) -> bool:
        win = _build_toast_window(
            payload.title, payload.message, payload.icon, payload.bg_color, payload.duration
        )
        # measure
        real_h = getattr(win, "_measured_height", None)
        if not isinstance(real_h, int) or real_h <= 0:
            win.update_idletasks()
            real_h = max(1, win.winfo_height())

        cap = self._per_toast_cap(workarea)
        real_h = min(real_h, cap)  # clamp so 10 can always fit

        if not self._can_fit_more(workarea, real_h):
            try: win.destroy()
            except: pass
            return False

        self._place_toast(workarea, win, real_h)
        self.stacks[workarea].append(ActiveToast(win, height=real_h))
        self._attach_close_handlers(workarea, win)
        self._reflow(workarea)
        self._reflow(workarea)
        win.update_idletasks()   # 👈 flush geometry so builder sees the recorded target
        win._fade_in()           # type: ignore[attr-defined]
        return True


def server_main(notification_queue: Queue):
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    root.withdraw()

    server = ToastServer(root, notification_queue)

    def poll():
        try:
            for _ in range(10):
                if notification_queue.empty():
                    break
                payload = notification_queue.get_nowait()
                if payload is None:
                    root.quit(); return
                if not isinstance(payload, ToastPayload):
                    title, message, opts = payload
                    payload = ToastPayload(
                        title=title, message=message,
                        duration=opts.get("duration", 5000),
                        icon=opts.get("icon", "ℹ️"),
                        bg_color=opts.get("bg_color"),
                        anchor=opts.get("anchor"),
                        group=opts.get("group"),
                    )
                server.handle_payload(payload)
        except Exception:
            pass
        finally:
            root.after(50, poll)  # Faster polling (was 80ms, now 50ms)

    poll()
    root.mainloop()

if __name__ == "__main__":
    from multiprocessing import Queue as Q
    q = Q()
    server_main(q)