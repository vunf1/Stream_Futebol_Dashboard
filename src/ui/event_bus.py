import threading
from typing import Callable, Dict

from src.config.settings import AppConfig


class DebouncedEventBus:
    """Lightweight, per-event debounce.

    - subscribe(event, callback): register a single callback for an event name
    - publish(event): schedule the callback after delay_ms (resetting any pending one)

    Callbacks run on a background Timer thread. If they touch UI, they must
    enqueue to the Tk mainloop (e.g., root.after(0, ...)).
    """

    def __init__(self, delay_ms: int = 50):
        self._delay = max(0, int(delay_ms)) / 1000.0
        self._lock = threading.Lock()
        self._callbacks: Dict[str, Callable[[], None]] = {}
        self._timers: Dict[str, threading.Timer] = {}

    def subscribe(self, event: str, callback: Callable[[], None]) -> None:
        with self._lock:
            self._callbacks[event] = callback

    def publish(self, event: str) -> None:
        with self._lock:
            cb = self._callbacks.get(event)
            if not cb:
                return
            if event in self._timers:
                try:
                    self._timers[event].cancel()
                except Exception:
                    pass
            t = threading.Timer(self._delay, cb)
            self._timers[event] = t
            t.daemon = True
            t.start()


UI_EVENT_BUS = DebouncedEventBus(delay_ms=getattr(AppConfig, "UI_UPDATE_DEBOUNCE", 50))


