from pathlib import Path
from functools import lru_cache
from typing import Any

from customtkinter import CTkImage
from tkinter import PhotoImage

# Optional Pillow for best‐quality resizing
try:
    from PIL import Image
    from PIL.Image import Resampling
    _HAS_PIL = True
except ImportError:
    Image = None  # type: ignore
    Resampling = None  # type: ignore
    _HAS_PIL = False

_ICON_DIR = Path(__file__).parent
_EXTS = {'.ico', '.png', '.gif', '.jpg', '.jpeg'}

_ICON_MAP = {
    p.stem: p for p in _ICON_DIR.iterdir()
    if p.suffix.lower() in _EXTS
}

@lru_cache(maxsize=32)
def get_icon(name: str, size: int = 24) -> CTkImage:
    """
    Return a CTkImage of "name" at the given square size.
    Prefers PIL for high-quality resizing; if PIL is absent,
    falls back to a raw PhotoImage (no resizing).
    """
    try:
        path = _ICON_MAP[name]
    except KeyError:
        raise KeyError(f"No icon called {name!r} in {_ICON_DIR}")

    if _HAS_PIL and Image is not None and Resampling is not None:
        # load + resize via Pillow
        pil_img = Image.open(path).convert("RGBA")
        pil_img = pil_img.resize((size, size), Resampling.LANCZOS)
        return CTkImage(light_image=pil_img, dark_image=pil_img, size=(size, size))
    else:
        # fallback: Tk's PhotoImage (size must match the file)
        photo: Any = PhotoImage(file=str(path))
        return CTkImage(light_image=photo, dark_image=photo, size=(size, size))  # type: ignore
