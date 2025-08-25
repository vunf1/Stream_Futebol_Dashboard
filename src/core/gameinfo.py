import os
import re
import json
import time
import threading
from typing import Any, Dict, Iterator
from contextlib import contextmanager

from ..config import AppConfig
from .logger import get_logger
from .file_cache import read_json_cached, write_json_async, write_json_sync, batch_write_json, invalidate_file_cache

log = get_logger(__name__)

# ───────────────── Base path & file ─────────────────
BASE_FOLDER_PATH = os.path.join(
    os.path.expanduser("~"),
    "Desktop",
    AppConfig.DESKTOP_FOLDER_NAME,
    AppConfig.SPECIAL_CONFIG_FOLDER,
    AppConfig.CONFIG_SUBFOLDER
)
GAMEINFO_PATH = os.path.join(BASE_FOLDER_PATH, AppConfig.GAMEINFO_FILENAME)

# MM:SS or MMM+:SS (>=100 min), with seconds 00–59
TIME_PATTERN = re.compile(r"^(?:\d{2}|[1-9]\d{2,}):[0-5]\d$")

# Default block for each field
DEFAULT_FIELD_STATE: Dict[str, Any] = AppConfig.DEFAULT_FIELD_STATE
ALLOWED_KEYS = set(DEFAULT_FIELD_STATE.keys())

# Legacy write buffer (kept for backward compatibility)
_write_buffer: Dict[tuple[str, str, str], Any] = {}
_write_buffer_lock = threading.Lock()
_write_timer = None
_write_timer_lock = threading.Lock()

def _schedule_write() -> None:
    """Schedule a delayed write to batch multiple operations"""
    global _write_timer
    
    with _write_timer_lock:
        if _write_timer:
            _write_timer.cancel()
        
        def delayed_write() -> None:
            _flush_write_buffer()
        
        # Reduced delay for more responsive writes with multiple timers
        _write_timer = threading.Timer(0.05, delayed_write)  # 50ms delay
        _write_timer.start()

def _flush_write_buffer() -> None:
    """Flush all pending writes to disk using new caching system"""
    global _write_buffer
    
    with _write_buffer_lock:
        if not _write_buffer:
            return
        
        # Group writes by file path
        files_to_write: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for (path, field_key, key), value in _write_buffer.items():
            if path not in files_to_write:
                files_to_write[path] = {}
            if field_key not in files_to_write[path]:
                files_to_write[path][field_key] = {}
            files_to_write[path][field_key][key] = value
        
        # Use new batch write system - combine all field updates into one call
        for path, field_data in files_to_write.items():
            # Combine all field updates into a single batch write
            all_updates = {}
            for field_key, changes in field_data.items():
                all_updates[field_key] = changes
            batch_write_json(path, all_updates)
        
        # Clear buffer
        _write_buffer.clear()


def _parse_time_to_seconds(text: str) -> int | None:
    t = text.strip()
    if not TIME_PATTERN.match(t):
        return None
    m, s = t.split(":")
    return int(m) * 60 + int(s)


def _format_time(total_seconds: int) -> str:
    m, s = divmod(max(0, int(total_seconds)), 60)
    return f"{m:02}:{s:02}"


def _normalize_field_key(field: int | str) -> str:
    if isinstance(field, int):
        return f"field_{field}"
    s = str(field).strip().lower()
    m = re.search(r"(\d+)", s)
    n = int(m.group(1)) if m else 1
    return f"field_{n}"
# ───────────────── JSON store (shared file, per-field sections) ─────────────────
class GameInfoStore:
    """
    Shared JSON ('gameinfo.json') with one object per field:
      {
        "field_1": { ... keys ... },
        "field_2": { ... }
      }
    """
    def __init__(self, field: int | str, debug: bool = True):
        self.field_key = _normalize_field_key(field)
        self.path = GAMEINFO_PATH
        self._data: Dict[str, Any] = {}
        self._loaded = False
        self.debug = debug
        self._ensure_file()

    def _log(self, *parts: Any) -> None:
        if self.debug:
            log.debug("gameinfo_debug", extra={"field": self.field_key, "msg": " ".join(str(p) for p in parts)})
    # ----- disk helpers -----
    
    def _ensure_file(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)

    def _load_from_disk(self) -> Dict[str, Any]:
        # Use cached file reading
        data = read_json_cached(self.path, {})
        self._data = data
        self._loaded = True

        blk = self._data.get(self.field_key, {})
        if not isinstance(blk, dict):
            blk = {}
        changed = False
        for k, v in DEFAULT_FIELD_STATE.items():
            if k not in blk:
                blk[k] = v
                changed = True
        self._data[self.field_key] = blk
        if changed:
            # Use sync write for immediate persistence
            write_json_sync(self.path, self._data)
            log.info("gameinfo_seed_defaults", extra={"path": self.path, "field": self.field_key})

        log.debug("gameinfo_loaded", extra={"path": self.path, "field": self.field_key, "keys": list(blk.keys())})
        return self._data

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self._load_from_disk()

    def _atomic_write(self, data: Dict[str, Any]) -> None:
        # Use sync write to ensure immediate persistence and prevent blocking
        write_json_sync(self.path, data)
        log.debug("gameinfo_write_sync", extra={"path": self.path})

    # ----- public API -----
    def read_all_field(self) -> Dict[str, Any]:
        data = self._load_from_disk()
        blk = dict(data[self.field_key])
        log.debug("gameinfo_read_all_field", extra={"field": self.field_key})
        return blk

    def read_field_key(self, key: str, default: Any = None) -> Any:
        data = self._load_from_disk()
        val = data[self.field_key].get(key, DEFAULT_FIELD_STATE.get(key, default))
        log.debug("gameinfo_read_field_key", extra={"field": self.field_key, "key": key})
        return val

    def get(self, key: str, default: Any = None) -> Any:
        self._ensure_loaded()
        blk = self._data.get(self.field_key, {})
        val = blk.get(key, DEFAULT_FIELD_STATE.get(key, default))
        log.debug("gameinfo_get_cached", extra={"field": self.field_key, "key": key})
        return val

    def set(self, key: str, value: Any, persist: bool = True) -> bool:
        if key not in ALLOWED_KEYS:
            self._log("set ignored (unknown key):", key)
            return False
        self._ensure_loaded()
        blk = self._data[self.field_key]
        if blk.get(key) == value:
            log.debug("gameinfo_set_noop", extra={"field": self.field_key, "key": key})
            return False
        blk[key] = value
        log.info("gameinfo_set", extra={"field": self.field_key, "key": key})
        if persist:
            # Use batch write directly (single queue layer)
            try:
                batch_write_json(self.path, {self.field_key: {key: value}})
            except Exception:
                log.error("gameinfo_batch_write_error", extra={"path": self.path, "field": self.field_key}, exc_info=True)
        return True

    def update(self, patch: Dict[str, Any], persist: bool = True) -> bool:
        self._ensure_loaded()
        blk = self._data[self.field_key]
        safe_patch: Dict[str, Any] = {}
        for k, v in patch.items():
            if k in ALLOWED_KEYS and blk.get(k) != v:
                blk[k] = v
                safe_patch[k] = v
        if not safe_patch:
            self._log("update no-op")
            return False
        log.info("gameinfo_update", extra={"field": self.field_key, "keys": list(safe_patch.keys())})
        if persist:
            try:
                batch_write_json(self.path, {self.field_key: safe_patch})
            except Exception:
                log.error("gameinfo_batch_write_error", extra={"path": self.path, "field": self.field_key}, exc_info=True)
        return True
    
    def _read_disk_raw(self) -> Dict[str, Any]:
        # Use cached file reading
        return read_json_cached(self.path, {})
    
    @contextmanager
    def _file_lock(self, timeout: float = 2.0, poll: float = 0.02) -> Iterator[None]:
        lock = self.path + ".lock"
        start = time.time()
        while True:
            try:
                fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.close(fd)
                break
            except FileExistsError:
                if time.time() - start > timeout:
                    raise TimeoutError(f"Lock timeout: {lock}")
                time.sleep(poll)
        try:
            yield
        finally:
            try:
                os.remove(lock)
            except FileNotFoundError:
                pass
    
    def _merge_and_write(self, patch: Dict[str, Any]) -> bool:
        """
        Merge only the provided keys for this field into the freshest file,
        then write atomically. Does NOT call _load_from_disk() (avoids recursion).
        """
        if not patch:
            return False

        with self._file_lock():
            data = self._read_disk_raw()
            blk = data.get(self.field_key)
            if not isinstance(blk, dict):
                blk = {}

            changed = False
            for k, v in patch.items():
                if k in ALLOWED_KEYS and blk.get(k) != v:
                    blk[k] = v
                    changed = True
            if not changed:
                return False

            # Keep other fields intact, only replace this field's object
            data[self.field_key] = blk

            # Use sync write for immediate persistence
            write_json_sync(self.path, data)
            log.debug("gameinfo_write_sync", extra={"path": self.path})

            # Update cache to reflect on-disk snapshot
            self._data = data
            self._loaded = True
            return True
    
if __name__ == "__main__":
    # Demo replaced with structured logs
    store = GameInfoStore("field 1")
    log.info("gameinfo_demo_path", extra={"path": GAMEINFO_PATH, "field": store.field_key})
    log.info("gameinfo_demo_read_all", extra={"data_keys": list(store.read_all_field().keys())})
    log.info("gameinfo_demo_read_keys", extra={"half": store.read_field_key("half"), "max": store.read_field_key("max")})
    store.set("home_name", "AAA FC")
    store.set("home_abbr", "AAA")
    log.info("gameinfo_demo_after_set", extra={"home_name": store.get("home_name"), "home_abbr": store.get("home_abbr")})
    secs = _parse_time_to_seconds("46:10") or 0
    store.set("max", _format_time(secs))
    log.info("gameinfo_demo_after_time", extra={"max": store.read_field_key("max")})
    store.update({"timer": "00:10", "extra": "00:00", "home_score": 1, "away_score": 0})
    log.info("gameinfo_demo_after_update", extra={"data_keys": list(store.read_all_field().keys())})
    store2 = GameInfoStore(2)
    store2.update({"home_name": "Team Two", "away_name": "Visitors", "timer": "00:12"})
    log.info("gameinfo_demo_second_field", extra={"data_keys": list(store2.read_all_field().keys())})
    log.info("gameinfo_demo_done")
