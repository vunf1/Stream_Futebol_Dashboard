import os
import re
import json
import time
import threading
from typing import Any, Dict

from ..config import AppConfig

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

# Global write buffer for batching operations
_write_buffer = {}
_write_buffer_lock = threading.Lock()
_write_timer = None
_write_timer_lock = threading.Lock()

def _schedule_write():
    """Schedule a delayed write to batch multiple operations"""
    global _write_timer
    
    with _write_timer_lock:
        if _write_timer:
            _write_timer.cancel()
        
        def delayed_write():
            _flush_write_buffer()
        
        _write_timer = threading.Timer(0.1, delayed_write)  # 100ms delay
        _write_timer.start()

def _flush_write_buffer():
    """Flush all pending writes to disk"""
    global _write_buffer
    
    with _write_buffer_lock:
        if not _write_buffer:
            return
        
        # Group writes by file path
        files_to_write = {}
        for (path, field_key, key), value in _write_buffer.items():
            if path not in files_to_write:
                files_to_write[path] = {}
            if field_key not in files_to_write[path]:
                files_to_write[path][field_key] = {}
            files_to_write[path][field_key][key] = value
        
        # Write each file
        for path, field_data in files_to_write.items():
            try:
                # Read current file
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if not isinstance(data, dict):
                        data = {}
                except Exception:
                    data = {}
                
                # Apply all changes for this file
                for field_key, changes in field_data.items():
                    if field_key not in data:
                        data[field_key] = {}
                    data[field_key].update(changes)
                
                # Atomic write
                tmp = path + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                os.replace(tmp, path)
                
            except Exception as e:
                print(f"Error flushing write buffer for {path}: {e}")
        
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

    def _log(self, *parts):
        if self.debug:
            print(f"[GameInfoStore:{self.field_key}]", *parts)
    # ----- disk helpers -----
    
    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)

    def _load_from_disk(self) -> Dict[str, Any]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                data = {}
        except Exception as e:
            self._log("load_from_disk error:", repr(e))
            data = {}
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
            self._atomic_write(self._data)
            self._log("seeded defaults")

        self._log("loaded", f"path={self.path}", f"keys={list(blk.keys())}")
        return self._data

    def _ensure_loaded(self):
        if not self._loaded:
            self._load_from_disk()

    def _atomic_write(self, data: Dict[str, Any]):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)
        self._log("write ->", self.path)

    # ----- public API -----
    def read_all_field(self) -> Dict[str, Any]:
        data = self._load_from_disk()
        blk = dict(data[self.field_key])
        self._log("read_all_field ->", blk)
        return blk

    def read_field_key(self, key: str, default: Any = None) -> Any:
        data = self._load_from_disk()
        val = data[self.field_key].get(key, DEFAULT_FIELD_STATE.get(key, default))
        self._log(f"read_field_key('{key}') ->", repr(val))
        return val

    def get(self, key: str, default: Any = None) -> Any:
        self._ensure_loaded()
        blk = self._data.get(self.field_key, {})
        val = blk.get(key, DEFAULT_FIELD_STATE.get(key, default))
        self._log(f"get('{key}') [cached] ->", repr(val))
        return val

    def set(self, key: str, value: Any, persist: bool = True) -> bool:
        if key not in ALLOWED_KEYS:
            self._log("set ignored (unknown key):", key)
            return False
        self._ensure_loaded()
        blk = self._data[self.field_key]
        if blk.get(key) == value:
            self._log(f"set('{key}') no-op (same value)")
            return False
        blk[key] = value
        self._log(f"set('{key}') =", repr(value))
        if persist:
            # Use buffered write for better performance
            with _write_buffer_lock:
                _write_buffer[(self.path, self.field_key, key)] = value
            _schedule_write()
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
        self._log("update", safe_patch)
        if persist:
            # Use buffered write for better performance
            with _write_buffer_lock:
                for key, value in safe_patch.items():
                    _write_buffer[(self.path, self.field_key, key)] = value
            _schedule_write()
        return True
    
    def _read_disk_raw(self) -> Dict[str, Any]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}
        return data
    
    def _file_lock(self, timeout=2.0, poll=0.02):
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

        with self._file_lock(): # type: ignore
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

            # Atomic write
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
            self._log("write ->", self.path)

            # Update cache to reflect on-disk snapshot
            self._data = data
            self._loaded = True
            return True
    
if __name__ == "__main__":
    # Simple demo (no CLI flags): operate on "field 1"
    store = GameInfoStore("field 1")

    print(f"gameinfo.json path: {GAMEINFO_PATH}")
    print(f"using block: {store.field_key}\n")

    # 1) Ensure defaults exist and show the whole field block
    print("1) read_all_field()")
    print(json.dumps(store.read_all_field(), ensure_ascii=False, indent=2), "\n")

    # 2) Fresh read of a single key (reloads file)
    print("2) read_field_key('half')  →", store.read_field_key("half"))
    print("   read_field_key('max')   →", store.read_field_key("max"), "\n")

    # 3) Cached get (no disk read)
    print("3) get('timer') (cached) →", store.get("timer"), "\n")

    # 4) set(): updates cache immediately and persists (merge-on-latest)
    print("4) set('home_name', 'AAA FC') + set('home_abbr', 'AAA')")
    store.set("home_name", "AAA FC")
    store.set("home_abbr", "AAA")
    print("   get('home_name') →", store.get("home_name"))
    print("   get('home_abbr') →", store.get("home_abbr"), "\n")

    # 5) Time helpers: parse/format then persist via set()
    print("5) Update 'max' via time helpers (_parse_time_to_seconds/_format_time)")
    secs = _parse_time_to_seconds("46:10") or 0
    store.set("max", _format_time(secs))
    print("   read_field_key('max') →", store.read_field_key("max"), "\n")

    # 6) update(): atomic multi-key write; cache stays in sync
    print("6) update({'timer':'00:10','extra':'00:00','home_score':1,'away_score':0})")
    store.update({"timer": "00:10", "extra": "00:00", "home_score": 1, "away_score": 0})
    print(json.dumps(store.read_all_field(), ensure_ascii=False, indent=2), "\n")

    # 7) Show another field block in the same file (no args, int is fine)
    print("7) Second field example (field_2)")
    store2 = GameInfoStore(2)
    store2.update({"home_name": "Team Two", "away_name": "Visitors", "timer": "00:12"})
    print(json.dumps(store2.read_all_field(), ensure_ascii=False, indent=2), "\n")

    print("✓ Done.")
