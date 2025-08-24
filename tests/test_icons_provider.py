import pytest

from src.ui.icons_provider import get_icon_path


def test_missing_icon_lists_available():
    with pytest.raises(KeyError) as exc:
        get_icon_path("_does_not_exist_")
    assert "Available:" in str(exc.value)


