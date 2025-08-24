import sys
from pathlib import Path

from src.core.server_launcher import get_server_launcher


def test_server_path_resolves_dev():
    # In test environment, we are not frozen; path should resolve under project root
    sl = get_server_launcher()
    p = sl.get_server_path()
    # It may or may not exist in dev, but path object should be a Path
    assert isinstance(p, Path)


