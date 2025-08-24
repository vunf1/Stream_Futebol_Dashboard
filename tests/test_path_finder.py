from pathlib import Path

from src.core.path_finder import get_path_finder


def test_path_finder_resources_exist():
    pf = get_path_finder()
    root = pf.project_root()
    assert (root / 'src').exists(), f"project root missing src: {root}"
    icons = pf.resource('src', 'ui', 'icons')
    assert icons.exists(), f"icons dir not found: {icons}"


