import os
import sys
from pathlib import Path
from typing import Optional

from .logger import get_logger

log = get_logger(__name__)


class PathFinder:
    """Locate packaged and development resources in a consistent way."""

    def __init__(self) -> None:
        self._frozen = getattr(sys, "frozen", False)
        self._meipass = getattr(sys, "_MEIPASS", None)
        self._root = Path(__file__).resolve().parents[2]

    def project_root(self) -> Path:
        return self._root

    def meipass_dir(self) -> Optional[Path]:
        try:
            return Path(self._meipass) if self._meipass else None
        except Exception:
            return None

    def resource(self, *relative: str | os.PathLike[str]) -> Path:
        """Return a path to a resource packaged with the app.

        Resolution order:
        - PyInstaller onefile/onedir: inside _MEIPASS if present
        - Dev: relative to project root
        """
        rel_path: Path = Path(*map(str, relative))
        if self._frozen and self._meipass:
            cand = Path(str(self._meipass)) / rel_path
            if cand.exists():
                return cand
        # Dev / fallback
        return self._root / rel_path

    def user_local_appdir(self, *relative: str | os.PathLike[str]) -> Path:
        base = Path(os.getenv("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local"))
        return base.joinpath(*map(str, relative))


_path_finder = PathFinder()


def get_path_finder() -> PathFinder:
    return _path_finder


