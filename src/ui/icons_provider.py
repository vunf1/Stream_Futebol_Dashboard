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

# Global icon cache for better performance
_global_icon_cache = {}
_icon_cache_lock = threading.Lock()

def _icons_dir() -> Path:
    """
    Locate the icons directory in:
    - PyInstaller --onefile (MEIPASS temp dir),
    - PyInstaller --onedir (next to the executable),
    - Dev mode (./icons relative to this file).
    """
    candidates = []

    if getattr(sys, "frozen", False):  # running a PyInstaller build
        # 1) onefile: extracted to a temp dir exposed as sys._MEIPASS
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / "helpers" / "ui" / "icons")
        # 2) onedir: files live next to the executable
        candidates.append(Path(sys.executable).parent / "helpers" / "ui" / "icons")

    # 3) dev: helpers/ui/ → ./icons (same directory as this file)
    candidates.append(Path(__file__).resolve().parent / "icons")

    for c in candidates:
        if c.exists():
            return c

    raise FileNotFoundError(
        "Could not find icons directory. Looked in:\n" + "\n".join(str(c) for c in candidates)
    )

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
    
    # Cache the icon
    with _icon_cache_lock:
        _global_icon_cache[cache_key] = icon
    
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
        raise KeyError(f"No icon called {name!r} in {_ICON_DIR}")

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