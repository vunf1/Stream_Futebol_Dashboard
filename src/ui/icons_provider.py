# helpers/icons_provider.py
from pathlib import Path
from functools import lru_cache
from typing import Any, Dict
import sys
import threading

from customtkinter import CTkImage
from tkinter import PhotoImage

try:
    from PIL import Image
    from PIL.Image import Resampling
    _HAS_PIL = True
except ImportError:
    Image = None  # type: ignore
    Resampling = None  # type: ignore
    _HAS_PIL = False

from src.core.path_finder import get_path_finder
from src.config.settings import AppConfig

# Global icon cache for better performance (LRU bound applied externally)
_global_icon_cache = {}
_icon_cache_lock = threading.Lock()

def _icons_dir() -> Path:
    """
    Locate the icons directory in:
    - PyInstaller --onefile (MEIPASS temp dir),
    - PyInstaller --onedir (next to the executable),
    - Dev mode (./icons relative to this file).
    """
    pf = get_path_finder()
    candidates = [
        pf.resource("src", "ui", "icons"),
        Path(sys.executable).parent / "src" / "ui" / "icons" if getattr(sys, "frozen", False) else None,
        Path(__file__).resolve().parent / "icons",
    ]
    for c in candidates:
        if c and c.exists():
            return c
    raise FileNotFoundError("Could not find icons directory.")

_ICON_DIR = _icons_dir()
_EXTS = {".ico", ".png", ".gif", ".jpg", ".jpeg"}

def _scan_icons(folder: Path) -> Dict[str, Path]:
    return {
        p.stem: p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in _EXTS
    }

_ICON_MAP = _scan_icons(_ICON_DIR)

def get_icon(name: str, size: int = 24) -> CTkImage:
    """Get icon with global caching for better performance"""
    cache_key = f"{name}_{size}"
    
    with _icon_cache_lock:
        if cache_key in _global_icon_cache:
            return _global_icon_cache[cache_key]
    
    try:
        path = _ICON_MAP[name]
    except KeyError:
        raise KeyError(f"No icon called {name!r} in {_ICON_DIR}")

    if _HAS_PIL and Image is not None and Resampling is not None:
        pil_img = Image.open(path).convert("RGBA").resize((size, size), Resampling.LANCZOS)
        icon = CTkImage(light_image=pil_img, dark_image=pil_img, size=(size, size))
    else:
        photo: Any = PhotoImage(file=str(path))
        icon = CTkImage(light_image=photo, dark_image=photo, size=(size, size))  # type: ignore
    
    # Cache the icon (with LRU bound)
    with _icon_cache_lock:
        _global_icon_cache[cache_key] = icon
        # Enforce LRU capacity
        max_size = int(getattr(AppConfig, "ICON_CACHE_SIZE", 50) or 50)
        if len(_global_icon_cache) > max_size:
            # pop the oldest inserted item (Python 3.7+ dict preserves insertion order)
            # rebuild dict without the first item for clarity
            try:
                oldest_key = next(iter(_global_icon_cache))
                if oldest_key != cache_key:
                    _global_icon_cache.pop(oldest_key, None)
            except Exception:
                # As a fallback, drop arbitrary keys until size fits
                while len(_global_icon_cache) > max_size:
                    _global_icon_cache.pop(next(iter(_global_icon_cache)), None)
    
    return icon

def clear_icon_cache():
    """Clear the global icon cache to free memory"""
    global _global_icon_cache
    with _icon_cache_lock:
        _global_icon_cache.clear()

def get_icon_path(name: str) -> str:
    """
    Return the absolute path to an icon file by stem (e.g., 'dice').
    Useful for Tk's window.iconbitmap which requires a file path.
    """
    try:
        return str(_ICON_MAP[name])
    except KeyError:
        available = ", ".join(sorted(_ICON_MAP.keys()))
        raise KeyError(f"No icon called {name!r} in {_ICON_DIR}. Available: {available}")

def set_window_icon(win, name: str) -> None:
    """
    Cross-platform window icon setter.
    - On Windows with .ico: use iconbitmap (best fidelity).
    - Otherwise: fall back to iconphoto with PhotoImage (png/gif/jpg).
    Keeps a reference to avoid Tk garbage-collecting the image.
    """
    path = Path(get_icon_path(name))
    if path.suffix.lower() == ".ico" and sys.platform.startswith("win"):
        win.iconbitmap(default=str(path))
    else:
        photo = PhotoImage(file=str(path))
        win.iconphoto(True, photo)
        setattr(win, "_iconphoto_ref", photo)  # prevent GC