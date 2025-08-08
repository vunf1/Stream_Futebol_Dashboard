# helpers/icons_provider.py
from pathlib import Path
from functools import lru_cache
from typing import Any, Dict
import sys

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

def _icons_dir() -> Path:
    """
    Locate the assets/icons directory in:
    - PyInstaller --onefile (MEIPASS temp dir),
    - PyInstaller --onedir (next to the executable),
    - Dev mode (../assets/icons relative to this file).
    """
    candidates = []

    if getattr(sys, "frozen", False):  # running a PyInstaller build
        # 1) onefile: extracted to a temp dir exposed as sys._MEIPASS
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / "assets" / "icons")
        # 2) onedir: files live next to the executable
        candidates.append(Path(sys.executable).parent / "assets" / "icons")

    # 3) dev: helpers/ → ../assets/icons
    candidates.append(Path(__file__).resolve().parent.parent / "assets" / "icons")

    for c in candidates:
        if c.exists():
            return c

    raise FileNotFoundError(
        "Could not find assets/icons. Looked in:\n" + "\n".join(str(c) for c in candidates)
    )

_ICON_DIR = _icons_dir()
_EXTS = {".ico", ".png", ".gif", ".jpg", ".jpeg"}

def _scan_icons(folder: Path) -> Dict[str, Path]:
    return {
        p.stem: p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in _EXTS
    }

_ICON_MAP = _scan_icons(_ICON_DIR)

@lru_cache(maxsize=32)
def get_icon(name: str, size: int = 24) -> CTkImage:
    try:
        path = _ICON_MAP[name]
    except KeyError:
        raise KeyError(f"No icon called {name!r} in {_ICON_DIR}")

    if _HAS_PIL and Image is not None and Resampling is not None:
        pil_img = Image.open(path).convert("RGBA").resize((size, size), Resampling.LANCZOS)
        return CTkImage(light_image=pil_img, dark_image=pil_img, size=(size, size))
    else:
        photo: Any = PhotoImage(file=str(path))
        return CTkImage(light_image=photo, dark_image=photo, size=(size, size))  # type: ignore

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