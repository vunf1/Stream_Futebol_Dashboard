import tempfile
from pathlib import Path

from src.core.config_manager import ConfigManager


def test_config_manager_forbids_admin_pin_and_allows_aliases():
    with tempfile.TemporaryDirectory() as td:
        cfg_path = Path(td) / "perf.json"
        cm = ConfigManager(config_file=str(cfg_path))

        # Forbidden keys should not be applied
        cm.update({"admin_pin": "1234", "PIN": "9999"})
        assert "admin_pin" not in cm.config
        # Aliased key should update the correct internal key
        cm.update({"UI_UPDATE_DEBOUNCE": 75})
        assert cm.config.get("ui_update_debounce") == 75


